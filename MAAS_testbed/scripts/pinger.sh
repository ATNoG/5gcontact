#!/bin/bash
count=1
echo "Starting"
echo "Enter IP"
read ping_ip
echo "Starting Ping Requests"
start=`date +%s`
while ping -q -c 1 $last_ip >/dev/null
do
echo -ne "$count  "
((count++))
sleep 1
done
end=`date +%s`
echo "Ping Error"
echo Execution time was `expr $end - $start` seconds.
