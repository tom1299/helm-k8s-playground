# Node port service
Example demonstrating that node port services are accessible by
the ips of all nodes. And show the corresponding iptables rules.
More comprehensive manual of iptables can be found [here](https://linux.die.net/man/8/iptables).

## Create the node port service
```bash
kubectl create service nodeport my-nodeport-service --tcp=8080:80
```

## Additional iptables rules
```bash
# iptables -L | grep -i my-nodeport-service -B 1
target     prot opt source               destination         
REJECT     tcp  --  anywhere             anywhere             /* default/my-nodeport-service:80-8080 has no endpoints */ ADDRTYPE match dst-type LOCAL tcp dpt:31736 reject-with icmp-port-unreachable
--
target     prot opt source               destination         
REJECT     tcp  --  anywhere             10.96.16.42          /* default/my-nodeport-service:80-8080 has no endpoints */ tcp dpt:http reject-with icmp-port-unreachable
```
The service has no endpoints, so the iptables rules reject the traffic.

## After adding a pod as endpoint
`kubectl run nginx --labels="app=my-nodeport-service" --image=nginx`
The two rules have disappeared.

## TODO
- Examine the iptables rules created by kube-proxy for the node port service on the two worker nodes. These rules should be
different since the pod ins only running on one node.

## Curl for each node ip
`kubectl get service my-nodeport-service -o jsonpath='{.spec.ports[?(@.name=="8080-80")].nodePort}'`
Get the ips for the nodes:
`kubectl get nodes -o jsonpath='{.items[*].status.addresses[?(@.type=="InternalIP")].address}'`
Then curl each node ip:
```bash
curl <node-ip>:<node-port>
```
