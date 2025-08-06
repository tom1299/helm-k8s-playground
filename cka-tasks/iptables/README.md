# Example of load balancing with iptables

## Commands
### Udp client to backend server
```bash
Allow udp to backend server 10.0.0.2
```bash
iptables -A PREROUTING -t nat -p udp -d 192.168.1.1 --dport 27017 -j DNAT --to-destination 10.0.0.2:1234
```
Test udp from client:
```bash
echo "Hello from client" | nc -u 192.168.1.1 27017
```
### tcp client to backend server
Allow tcp to backend server 10.0.0.3
```bash
iptables -A PREROUTING -t nat -p tcp -d 192.168.1.1 --dport 27018 -j DNAT --to-destination 10.0.0.3:1234
iptables -A POSTROUTING -t nat -p tcp -d 10.0.0.3 --dport 1234  -j SNAT  --to-source 10.0.0.1 # Only needed for tcp because connection oriented
```
Test tcp from client:
```bash
echo "Hello from client" | nc -t 192.168.1.3 27018
```

## All ip tables commands
```bash
# udp
iptables -A PREROUTING -t nat -p udp -d 192.168.1.1 --dport 27017 -j DNAT --to-destination 10.0.0.2:1234
# tcp
iptables -A PREROUTING -t nat -p tcp -d 192.168.1.1 --dport 27018 -j DNAT --to-destination 10.0.0.2:5678
iptables -A POSTROUTING -t nat -p tcp -d 10.0.0.2 --dport 5678  -j SNAT  --to-source 10.0.0.1
```