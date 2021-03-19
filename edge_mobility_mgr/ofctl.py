#---------------------------------------------------------------#
#            Ofctl Class: Used to add or remove flows           #
# Author: Rui Silva (ruimiguelsilva@av.it.pt)                   #
#---------------------------------------------------------------#

from ryu.lib.packet import ether_types

#-----------------------------------------------------------------------------------------------------------------------------
class Ofctl():
  def __init__(self, dp):
    self.datapath = dp

  #-----------------------------------------------------------------------------------------
  def add_flow(self, priority, match, inst, cookie=0, table_id=0, idle_timeout=0, flags=None, buffer_id=None):
    ofproto = self.datapath.ofproto
    parser = self.datapath.ofproto_parser

    if buffer_id:
      if flags:
        mod = parser.OFPFlowMod(datapath=self.datapath, cookie=cookie, table_id=table_id, idle_timeout=idle_timeout, buffer_id=buffer_id,
                                priority=priority, flags=flags, match=match, instructions=inst)
      else:
        mod = parser.OFPFlowMod(datapath=self.datapath, cookie=cookie, table_id=table_id, idle_timeout=idle_timeout, buffer_id=buffer_id,
                                priority=priority, match=match, instructions=inst)
    else:
      if flags:
        mod = parser.OFPFlowMod(datapath=self.datapath, cookie=cookie, table_id=table_id, idle_timeout=idle_timeout,
                                priority=priority, flags=flags, match=match, instructions=inst)
      else:
        mod = parser.OFPFlowMod(datapath=self.datapath, cookie=cookie, table_id=table_id, idle_timeout=idle_timeout,
                                priority=priority, match=match, instructions=inst)
  
    self.datapath.send_msg(mod)

  #-----------------------------------------------------------------------------------------
  def del_flow(self, match, table_id=0, buffer_id=None):
    ofproto = self.datapath.ofproto
    parser = self.datapath.ofproto_parser
    inst = []

    if buffer_id:
      mod = parser.OFPFlowMod(datapath=self.datapath, table_id=table_id, buffer_id=buffer_id, match=match, instructions=inst,
                              command=ofproto.OFPFC_DELETE, out_port=ofproto.OFPP_ANY, out_group=ofproto.OFPG_ANY)
    else:
      mod = parser.OFPFlowMod(datapath=self.datapath, table_id=table_id, match=match, instructions=inst,
                              command=ofproto.OFPFC_DELETE, out_port=ofproto.OFPP_ANY, out_group=ofproto.OFPG_ANY)

    self.datapath.send_msg(mod)
