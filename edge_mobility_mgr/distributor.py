import json
import logging
import ast
import signal
import sys

from webob import Response
from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER, CONFIG_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.app.wsgi import ControllerBase, WSGIApplication, route
from ryu.lib import dpid as dpid_lib
import ryu.lib.ovs.vsctl as ovs_vsctl
from ryu.exception import RyuException
from ryu.controller import dpset
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.ofproto import ether
from ryu.lib.packet import packet
from ryu.lib.packet import in_proto
from ryu.lib.packet import packet_base
from ryu.lib.packet import arp
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types
from ryu.lib.packet import icmp
from ryu.lib.packet import ipv4
from ryu.lib.packet import tcp
from ryu.lib.packet import udp
from ryu.lib import mac as mac_lib
from ryu.lib import hub
from threading import Timer
import array
from ofctl import *


LOG = logging.getLogger('ryu.app.distributor_ctrl')
spgw_instance_name = 'distributor_ctrl_api'

LOCAL_TENANT_MODE = False

DPID = 0

#ENDPOINTS DPID
dpids = {
  'dist': 1152921504606846976,
  'mec0': 1,
  'mec1': 2,
  'mec2': 3,
  'mec3': 4,
  'mec4': 5
}

dpids_mecs = {}

# ENDPOINTS PUBLIC IP
mec_endpoints = {
  'dist': '192.168.85.88',
  'mec0': '192.168.89.155',
  'mec1': '192.168.89.187',
  'mec2': '192.168.89.155',
  'mec3': '192.168.89.155',
  'mec4': '192.168.89.155'
}

# network specific variables

#CLIENT_IF = "client"
#CDN_IF = "cdn"

CLIENT_SIDE_IF = "client"
CDN_SIDE_IF = "cdn"
GRE_PORT = "gre0"
#LOCAL_IP_OUT = "10.0.4.14"
local_ip = {
  'dist': '10.0.2.2',
  'mec0': '10.0.2.33',
  'mec1': '10.0.2.18',
  'mec2': '10.0.2.5',
  'mec3': '10.0.2.6'
}
VIDEO_ORIGIN = "192.168.89.124"

GRE_TUNNEL_ID = 2

# Local Variables
IN_TABLE = 1
OUT_TABLE = 2

ports = {}
# ports stucture example:
# ports = {'dist': {'ens4': {'port_no': 2, 'hwaddr': 'fa:16:3e:55:10:73'}}}

mecs = {}
# mecs structure example:
# mecs = {'mec0': {'ipAddr': '10.0.2.3', 'hwaddr': 'fa:16:3e:55:10:73'}}

CURRENT_MEC = None

#-------------------------------------------------------------------------------------------------------
def command_method(method):
  def wrapper(self, req, *args, **kwargs):

    try:
      if req.body:
              # We use ast.literal_eval() to parse request json body
      # instead of json.loads().
      # Because we need to parse binary format body
  # in send_experimenter().
        body = ast.literal_eval(req.body.decode('utf-8'))
      else:
        body = {}
    except SyntaxError:
      LOG.exception('Invalid syntax: %s', req.body)
      return Response(status=400)

    # Invoke EDGEController method
    try:
      method(self, req, body, *args, **kwargs)
      return Response(status=200)
    except ValueError:
      LOG.exception('Invalid syntax: %s', req.body)
      return Response(status=400)

  return wrapper

#-------------------------------------------------------------------------------------------------------$
class Distributor_Ctrl(app_manager.RyuApp):
  OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

  _CONTEXTS = {
          'dpset': dpset.DPSet,
          'wsgi': WSGIApplication
  }

  def __init__(self, *args, **kwargs):
    super(Distributor_Ctrl, self).__init__(*args, **kwargs)
    self.dpset = kwargs['dpset']
    wsgi = kwargs['wsgi']
    self.data = {}
    self.data['dpset'] = self.dpset
    mapper = wsgi.mapper
    LOG.error('## INITIALIZING DISTRIBUTOR CONTROLLER ##')

    for key in dpids:
      dpids_mecs[dpids[key]] = key

    LOG.error('DPIDs: %s', dpids_mecs)

    wsgi.registory['DistributorController'] = self.data

    url = '/handover/{mecId}'
    mapper.connect('mec_handover', url, controller=DistributorController,
                    action='mec_handover', conditions=dict(method=['HEAD']))

    url = '/report-node-ip'
    mapper.connect('report_node_ip', url, controller=DistributorController,
                    action='report_node_ip', conditions=dict(method=['POST']))

  #-----------------------------------------------------------------------------------------
  @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
  def switch_features_handler(self, ev):
    self.dp = ev.msg.datapath
    datapath = ev.msg.datapath
    dpid = datapath.id
    global DPID
    DPID = dpid
    parser = datapath.ofproto_parser
    ofproto = datapath.ofproto

    if dpid in dpids_mecs.keys():
      LOG.error('Connected dpid: %s', dpids_mecs[dpid])
    else:
      LOG.error('Unrecognized dpid %d', dpid)

    req = parser.OFPPortDescStatsRequest(datapath, 0)
    datapath.send_msg(req)

  #-----------------------------------------------------------------------------------------
  @set_ev_cls(ofp_event.EventOFPPortDescStatsReply, MAIN_DISPATCHER)
  def port_desc_stats_reply_handler(self, ev):
    self.dp = ev.msg.datapath
    datapath = ev.msg.datapath
    dpid = datapath.id
    parser = datapath.ofproto_parser
    ofproto = datapath.ofproto

    ofctl = Ofctl(datapath)

    dp_name = dpids_mecs[dpid]

    # EXTRACT RELEVANT INFO
    port_info = {}

    for p in ev.msg.body:
      port_name = p.name.decode("utf-8")
      port_info[port_name] = {'port_no': p.port_no, 'hwaddr': p.hw_addr}

    # GET CLIENT SIDE
    if CLIENT_SIDE_IF in port_info.keys():
      hw_addr = port_info[CLIENT_SIDE_IF]['hwaddr']
      del port_info[CLIENT_SIDE_IF]
      for port in port_info.keys():
        if port_info[port]['hwaddr'] == hw_addr:
          if dp_name in ports.keys():
            ports[dp_name][CLIENT_SIDE_IF] = {'port_no': port_info[port]['port_no'], 'hwaddr': hw_addr}
          else:
            ports[dp_name] = {CLIENT_SIDE_IF: {'port_no': port_info[port]['port_no'], 'hwaddr': hw_addr}}

    if CDN_SIDE_IF in port_info.keys():
      hw_addr = port_info[CDN_SIDE_IF]['hwaddr']
      del port_info[CDN_SIDE_IF]
      for port in port_info.keys():
        if port_info[port]['hwaddr'] == hw_addr:
          if dp_name in ports.keys():
            ports[dp_name][CDN_SIDE_IF] = {'port_no': port_info[port]['port_no'], 'hwaddr': hw_addr}
          else:
            ports[dp_name] = {CDN_SIDE_IF: {'port_no': port_info[port]['port_no'], 'hwaddr': hw_addr}}


    if GRE_PORT in port_info.keys():
      if dp_name in ports.keys():
        ports[dp_name][GRE_PORT] = {'port_no': port_info[GRE_PORT]['port_no'], 'hwaddr': port_info[GRE_PORT]['hwaddr']}
      else:
        ports[dp_name] = {GRE_PORT: {'port_no': port_info[GRE_PORT]['port_no'], 'hwaddr': port_info[GRE_PORT]['hwaddr']}}

    LOG.error('Available Ports: %s', ports)

    LOG.error('Install Default Flows')
    # DEFAULT FLOWS:

    # NORMAL
    match = parser.OFPMatch()
    actions = [parser.OFPActionOutput(ofproto.OFPP_NORMAL, 0)]
    inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
    ofctl.add_flow(priority=0, match=match, inst=inst)

    if dp_name == 'dist':
      # SEND INSIDE PACKETS TO INSIDE ARP TABLE
      match = parser.OFPMatch(eth_type=ether_types.ETH_TYPE_IP, in_port=ports[dp_name][CLIENT_SIDE_IF]['port_no'])
      inst = [parser.OFPInstructionGotoTable(IN_TABLE)]
      ofctl.add_flow(priority=1, match=match, inst=inst)

      # SEND UNKNOWN ADDRESSES TO THE CONTROLLER
      match = parser.OFPMatch(eth_type=ether_types.ETH_TYPE_IP)
      actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER)]
      inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
      ofctl.add_flow(priority=0, table_id=IN_TABLE, match=match, inst=inst)

      # SEND ARP RESPONSES RECEIVED IN THE EXT PORT TO THE CONTROLLER
      if LOCAL_TENANT_MODE:
        match = parser.OFPMatch(eth_type=ether_types.ETH_TYPE_ARP, in_port=ports[dp_name][CDN_SIDE_IF]['port_no'], arp_op=arp.ARP_REPLY, arp_tpa=LOCAL_IP_OUT)
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER)]
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        ofctl.add_flow(priority=1, match=match, inst=inst)
      else:
        match = parser.OFPMatch(in_port=ports[dp_name][GRE_PORT]['port_no'], eth_type=ether_types.ETH_TYPE_IP)
        inst = [parser.OFPInstructionGotoTable(IN_TABLE)]
        ofctl.add_flow(priority=1, match=match, inst=inst)
    else:
      match = parser.OFPMatch(in_port=ports[dp_name][CDN_SIDE_IF]['port_no'], eth_type=ether_types.ETH_TYPE_IP)
      actions = [parser.OFPActionSetField(tun_ipv4_dst=mec_endpoints['dist']), parser.OFPActionSetField(tunnel_id=GRE_TUNNEL_ID),parser.OFPActionOutput(ports[dp_name][GRE_PORT]['port_no'])]
      inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
      ofctl.add_flow(priority=1, match=match, inst=inst)

      match = parser.OFPMatch(eth_type=ether_types.ETH_TYPE_ARP, in_port=ports[dp_name][CDN_SIDE_IF]['port_no'], arp_op=arp.ARP_REPLY, arp_tpa=local_ip[dp_name])
      actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER)]
      inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
      ofctl.add_flow(priority=1, match=match, inst=inst)

  #-----------------------------------------------------------------------------------------
  @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
  def packet_in_handler(self, ev):
    #LOG.error('PACKET IN HANDLER')
    msg = ev.msg
    datapath = msg.datapath
    ofproto = datapath.ofproto
    parser = datapath.ofproto_parser
    dpid = datapath.id

    ofctl = Ofctl(datapath)
    dp_name = dpids_mecs[dpid]

    pkt = packet.Packet(array.array('B', msg.data))
    if pkt.protocols[0].ethertype == ether_types.ETH_TYPE_IP:
      # TABLE 1 UPLINK
      match = parser.OFPMatch(eth_type=ether_types.ETH_TYPE_IP, ipv4_src=pkt.protocols[1].src)
      inst = [parser.OFPInstructionGotoTable(OUT_TABLE)]
      ofctl.add_flow(priority=2, table_id=IN_TABLE, match=match, inst=inst)

      # TABLE 2 UPLINK (ADDED AFTER HANDOVER MESSAGE)

      # TABLE 0 DOWNLINK (ADDED AFTER HANDOVER MESSAGE)

      # TABLE 1 DOWNLINK
      match = parser.OFPMatch(eth_type=ether_types.ETH_TYPE_IP, ipv4_dst=pkt.protocols[1].src)
      actions = [parser.OFPActionSetField(eth_dst=pkt.protocols[0].src), parser.OFPActionOutput(ports[dp_name][CLIENT_SIDE_IF]['port_no'])]
      inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
      ofctl.add_flow(priority=2, table_id=IN_TABLE, match=match, inst=inst)

      # PACKET OUT
      actions = [parser.OFPActionOutput(ports[dp_name][CDN_SIDE_IF]['port_no'])]
      if pkt.protocols[1].dst == VIDEO_ORIGIN:
        if CURRENT_MEC is not None:
          actions = [parser.OFPActionSetField(eth_src=ports[dp_name][CDN_SIDE_IF]['hwaddr']), parser.OFPActionSetField(eth_dst=mecs[CURRENT_MEC]['hwaddr']), parser.OFPActionSetField(ipv4_dst=mecs[CURRENT_MEC]['ipAddr']), parser.OFPActionOutput(ports[dp_name][CDN_SIDE_IF]['port_no'])]


      out = parser.OFPPacketOut(
          datapath=datapath, buffer_id=msg.buffer_id, in_port=ofproto.OFPP_CONTROLLER, actions=actions, data=msg.data)
      datapath.send_msg(out)

    elif pkt.protocols[0].ethertype == ether_types.ETH_TYPE_ARP:
      if pkt.protocols[1].opcode == arp.ARP_REPLY and pkt.protocols[1].dst_ip == local_ip[dp_name]:
        LOG.error('RECEIVED ARP RESPONSE FROM %s', pkt.protocols[1].src_ip)
        LOG.error("mecs before: %s", mecs)
        for mec in mecs:
          if mecs[mec]['ipAddr'] ==  pkt.protocols[1].src_ip:
            mecs[mec]['hwaddr'] = pkt.protocols[1].src_mac
        LOG.error("mecs after: %s", mecs)

#-------------------------------------------------------------------------------------------------------$
class DistributorController(ControllerBase):
  def __init__(self, req, link, data, **config):
    super(DistributorController, self).__init__(req, link, data, **config)
    self.dpset = data['dpset']

  #-----------------------------------------------------------------------------------------
  @command_method
  def mec_handover(self, req, body, *args, **kwargs):
    datapath = self.get_datapath(DPID)
    parser = datapath.ofproto_parser
    ofproto = datapath.ofproto
    ofctl = Ofctl(datapath)
    global CURRENT_MEC

    mecId = kwargs['mecId']
    CURRENT_MEC = mecId

    LOG.error("Handover: mecId: %s, CURRENT_MEC: %s, mecs: %s", mecId, CURRENT_MEC, mecs)
    if mecId in mecs.keys():
      if LOCAL_TENANT_MODE:
        ipAddr = mecs[mecId]['ipAddr']
        mac = mecs[mecId]['hwaddr']
        LOG.error('Clients are being handed over to %s at %s', mecId, ipAddr)
        # TABLE 2 UPLINK
        match = parser.OFPMatch(eth_type=ether_types.ETH_TYPE_IP, ipv4_dst=VIDEO_ORIGIN)
        actions = [parser.OFPActionSetField(eth_src=ports[CLIENT_SIDE_IF]['hwaddr']), parser.OFPActionSetField(eth_dst=mac), parser.OFPActionSetField(ipv4_dst=ipAddr), parser.OFPActionOutput(ports[CDN_SIDE_IF]['port_no'])]
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        ofctl.add_flow(priority=2, table_id=OUT_TABLE, match=match, inst=inst)

        # TABLE 0 DOWNLINK
        match = parser.OFPMatch(eth_type=ether_types.ETH_TYPE_IP, ipv4_src=ipAddr)
        actions = [parser.OFPActionSetField(eth_src=ports[CLIENT_SIDE_IF]['hwaddr']),parser.OFPActionSetField(ipv4_src=VIDEO_ORIGIN)]
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions), parser.OFPInstructionGotoTable(IN_TABLE)]
        ofctl.add_flow(priority=2, match=match, inst=inst)
      else:
        # TO DIST
        dpid = dpids['dist']
        datapath = self.get_datapath(dpid)
        parser = datapath.ofproto_parser
        ofproto = datapath.ofproto
        ofctl = Ofctl(datapath)

        match = parser.OFPMatch(eth_type=ether_types.ETH_TYPE_IP, ipv4_dst=VIDEO_ORIGIN)
        actions = [parser.OFPActionSetField(tun_ipv4_dst=mec_endpoints[mecId]), parser.OFPActionSetField(tunnel_id=GRE_TUNNEL_ID), parser.OFPActionOutput(ports['dist'][GRE_PORT]['port_no'])]
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        ofctl.add_flow(priority=2, table_id=OUT_TABLE, match=match, inst=inst)

        # TO MECX
        dpid = dpids[mecId]
        datapath = self.get_datapath(dpid)
        parser = datapath.ofproto_parser
        ofproto = datapath.ofproto
        ofctl = Ofctl(datapath)

        match = parser.OFPMatch(eth_type=ether_types.ETH_TYPE_IP, ipv4_dst=VIDEO_ORIGIN)
        actions = [parser.OFPActionSetField(eth_src=ports[mecId][CDN_SIDE_IF]['hwaddr']), parser.OFPActionSetField(eth_dst=mecs[mecId]['hwaddr']), parser.OFPActionSetField(ipv4_dst=mecs[mecId]['ipAddr']), parser.OFPActionOutput(ports[mecId][CDN_SIDE_IF]['port_no'])]
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        ofctl.add_flow(priority=2, match=match, inst=inst)

        match = parser.OFPMatch(eth_type=ether_types.ETH_TYPE_IP, ipv4_src=mecs[mecId]['ipAddr'])
        actions = [parser.OFPActionSetField(ipv4_src=VIDEO_ORIGIN), parser.OFPActionSetField(tun_ipv4_dst=mec_endpoints['dist']), parser.OFPActionSetField(tunnel_id=GRE_TUNNEL_ID), parser.OFPActionOutput(ports[mecId][GRE_PORT]['port_no'])]
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        ofctl.add_flow(priority=2, match=match, inst=inst)
    else:
      LOG.error('ERROR: %s IP Address was not received', mecId)

  #-----------------------------------------------------------------------------------------
  @command_method
  def report_node_ip(self, req, body, *args, **kwargs):
    mecId = body['mecId']

    if LOCAL_TENANT_MODE:
      endpoint_id = 'dist'
    else:
      endpoint_id = mecId

    dpid = dpids[endpoint_id]
    datapath = self.get_datapath(dpid)
    parser = datapath.ofproto_parser
    ofproto = datapath.ofproto
    ofctl = Ofctl(datapath)

    # SAVE RECEIVED PARAMETERS
    ipAddr = body['nodeIP']
    if mecId not in mecs.keys():
      mecs[mecId] = {'ipAddr': ipAddr}

    LOG.error('Report Node IP: %s, MEC: %s, mecs: %s', mecId, ipAddr, mecs)
    # BUILD ARP PACKET

    e = ethernet.ethernet(dst = 'ff:ff:ff:ff:ff:ff',
                          src = ports[endpoint_id][CDN_SIDE_IF]['hwaddr'],
                          ethertype=ether.ETH_TYPE_ARP)

    a = arp.arp(hwtype=1, proto=0x0800, hlen=6, plen=4, opcode=arp.ARP_REQUEST,
                src_mac=ports[endpoint_id][CDN_SIDE_IF]['hwaddr'], src_ip=local_ip[endpoint_id],
                dst_mac='00:00:00:00:00:00', dst_ip=ipAddr)

    p = packet.Packet()
    p.add_protocol(e)
    p.add_protocol(a)
    p.serialize()

      # PACKET OUT
    actions = [parser.OFPActionOutput(ports[endpoint_id][CDN_SIDE_IF]['port_no'])]
    out = parser.OFPPacketOut(
        datapath=datapath, buffer_id=ofproto.OFP_NO_BUFFER, in_port=ofproto.OFPP_CONTROLLER, actions=actions, data=p)
    datapath.send_msg(out)


  #-----------------------------------------------------------------------------------------
  def get_datapath(self, dpid):
    try:
      dp = self.dpset.get(int(str(dpid), 0))
    except ValueError:
      LOG.exception('Invalid dpid: %s', dpid)
    if dp is None:
      LOG.error('No such Datapath: %s', dpid)
    return dp

