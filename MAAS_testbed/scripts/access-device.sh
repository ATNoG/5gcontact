#!/bin/bash

echo "Trying to access network"
sudo ip link set wlp3s0 up				#Wireless device interface up
start=`date +%s`						#Start measuring the time
var2="Not connected." >> /dev/null  			#Compare string


while true; do
status=$(sudo iw dev wlp3s0 link) >> /dev/null		#Check the wireless interface status
sudo iw dev wlp3s0 connect -w apu_app >> /dev/null		#Tries to connect to the SSID "apu_app"

if [[ "$status" != "$var2" ]]; then			#If success perform a DHCP request
echo "DHCP"						# if not, check status and tries again
sudo dhclient wlp3s0
break
fi
done

end=`date +%s`						#Stops measuring time

echo "Took `expr $end - $start` seconds."
