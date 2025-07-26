# iptables
From [here](https://www.howtogeek.com/177621/the-beginners-guide-to-iptables-the-linux-firewall/).
iptables is a command-line firewall utility that uses policy chains to allow or block traffic.

## Chains
Rules can be appended or inserted into a chain.
- **INPUT**: This chain is used for incoming connections.
- **OUTPUT**: This chain is used for outgoing connections.
- **FORWARD**: This chain is used for connections that are being routed through the host
There can be more chains. To view the chains:
```bash
iptables -L -v
```
When using iptables to lock down your system, remember that a lot of protocols will require two-way communication, so both the input and output chains will need to be configured properly.

## Connection state
Gives you the capability you'd need to allow two way communication but only allow one way connections to be established.

## Relation to kube-proxy and Kubernetes
- How does iptables relate to external and internal traffic policies in Kubernetes? iptables can be used to drop packages as is the case when the traffic policy for a service is set to `local`. Look at the rules created by kube-proxy when creating a service with local and cluster traffic policy.