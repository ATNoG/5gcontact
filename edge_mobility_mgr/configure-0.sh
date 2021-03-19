CLIENT_SIDE_IF='ens4'
CDN_SIDE_IF='ens7'
DATAPATH_ID='0000000000000001'

HOST=$(hostname)
echo 127.0.1.1 $HOST >> /etc/hosts
apt-get update
apt-get upgrade -y
apt-get install openvswitch-switch python3-ryu -y
dhclient ens4 ens5

ovs-vsctl add-br br0
ovs-vsctl set bridge br0 other-config:datapath-id=$DATAPATH_ID
ovs-vsctl set bridge br0 protocols=OpenFlow13
ovs-vsctl set-controller br0 "tcp:127.0.0.1:6653"
ovs-vsctl add-port br0 client -- set interface client type=internal
ovs-vsctl add-port br0 cdn -- set interface cdn type=internal
ovs-vsctl add-port br0 $CLIENT_SIDE_IF
ovs-vsctl add-port br0 $CDN_SIDE_IF
ovs-vsctl add-port br0 gre0 -- set interface gre0 type=gre options:remote_ip=flow options:in_key=flow options:out_key=flow
