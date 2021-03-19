CLIENT_SIDE_IF='ens4'
CDN_SIDE_IF='ens7'
VIDEO_ORIGIN_IP='192.168.89.124'

dhclient $CLIENT_SIDE_IF $CDN_SIDE_IF

sleep 1

CLIENT_PORT_IP=$(ifconfig $CLIENT_SIDE_IF | grep -m1 "inet" | cut -d ' ' -f 10)
CLIENT_PORT_HW=$(ifconfig $CLIENT_SIDE_IF | grep "ether" | cut -d ' ' -f 10)
CDN_PORT_IP=$(ifconfig $CDN_SIDE_IF | grep -m1 "inet" | cut -d ' ' -f 10)
CDN_PORT_HW=$(ifconfig $CDN_SIDE_IF | grep "ether" | cut -d ' ' -f 10)

sed -i "s/#CDN_SIDE_IF/CDN_SIDE_IF = \"${CDN_SIDE_IF}\"/g" distributor.py
sed -i "s/#CLIENT_SIDE_IF/CLIENT_SIDE_IF = \"${CLIENT_SIDE_IF}\"/g" distributor.py
sed -i "s/#VIDEO_ORIGIN/VIDEO_ORIGIN = \"${VIDEO_ORIGIN_IP}\"/g" distributor.py
sed -i "s/#LOCAL_IP_OUT/LOCAL_IP_OUT = \"${CDN_PORT_IP}\"/g" distributor.py

ifconfig -a $CLIENT_SIDE_IF 0
ifconfig -a client hw ether $CLIENT_PORT_HW
ifconfig -a client $CLIENT_PORT_IP/24 up

ifconfig -a $CDN_SIDE_IF 0
ifconfig -a cdn hw ether $CDN_PORT_HW
ifconfig -a cdn $CDN_PORT_IP/24 up

