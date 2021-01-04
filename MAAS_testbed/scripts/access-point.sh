#!/bin/bash

# Install hostapd
sudo apt install hostapd -y

# hostadp config file create
mkdir ~/conf
cd ~/conf
cat > hostapd.conf << EOF
interface=wlp1s0
driver=nl80211
ssid=apu_app
hw_mode=g
channel=1
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
#wpa=3				# ignore wpa
#wpa_passphrase=12345678	# doesn't need password
#wpa_key_mgmt=WPA-PSK
#wpa_pairwise=TKIP
rsn_pairwise=CCMP
EOF
cd ~

# install isc-dhcp-server
sudo apt install -y isc-dhcp-server
sudo service isc-dhcp-server stop

# add wireless interface to default isc-dhcp-server config file
sudo sed -i 's/INTERFACESv4=""/INTERFACESv4="wlp1s0"/' /etc/default/isc-dhcp-server
sudo sed -i 's/INTERFACESv6=""/INTERFACESv6="wlp1s0"/' /etc/default/isc-dhcp-server

# comment unnecessary lines on /etc/dhcp/dhcpd.conf
sudo sed -i '10,14 s/^/#/' /etc/dhcp/dhcpd.conf
sudo sed -i '20,21 s/^/#/' /etc/dhcp/dhcpd.conf

# configure subnet
sudo tee -a /etc/dhcp/dhcpd.conf > /dev/null <<EOT
subnet 10.10.0.0 netmask 255.255.255.0 {
        range 10.10.0.2 10.10.0.16;
        option domain-name-servers 8.8.8.8, 8.8.4.4;
        option routers 10.10.0.1;
}
EOT

# configure wireless interface -> wlp1s0
sudo ip addr add 10.10.0.1/24 dev wlp1s0
sudo ip link set wlp1s0 up

# start hostapd deamon && isc-dhcp-server
sudo service isc-dhcp-server start
sudo hostapd -B ~/conf/hostapd.conf
sudo service isc-dhcp-server restart

