#!/bin/bash

# Delay added to give time to validate connection and the block of packets.
valid=true
count=1
while [ $valid ]
do
echo -ne "$count "
if [ $count -eq 50 ];
then
break
fi
sleep 1
((count++))
done


# Iptables command to block incoming pings from the APU-1
sudo iptables -A INPUT -p icmp --icmp-type echo-request -s 10.10.10.38 -j REJECT
