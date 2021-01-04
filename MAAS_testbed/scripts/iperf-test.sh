#|/bin/bash

for i in {1..10}
do
echo "IPERF $i"
iperf3 -i 10 -w 1M -t 60 -c 10.10.0.1  | tee ~/iperf_tests/results/t3/tcp_client$i.txt
echo ""
echo "IPERF $i done"
echo ""
done
