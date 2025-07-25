# Use kube-proxy in iptables mode
See [kube-proxy-ipvs](../kube-proxy-ipvs/README.md) for details on what to achieve. Here we will use iptables mode instead of ipvs.

## Findings
- Seems to not be round robin.
Output from iptables on the workder node:
```
# iptables -t nat -L KUBE-SERVICES
Chain KUBE-SERVICES (2 references)
target     prot opt source               destination         
KUBE-SVC-NPX46M4PTMTKRN6Y  tcp  --  anywhere             10.96.0.1            /* default/kubernetes:https cluster IP */ tcp dpt:https
KUBE-SVC-ERIFXISQEP7F7OF4  tcp  --  anywhere             10.96.0.10           /* kube-system/kube-dns:dns-tcp cluster IP */ tcp dpt:domain
KUBE-SVC-JD5MR3NA4I4DYORP  tcp  --  anywhere             10.96.0.10           /* kube-system/kube-dns:metrics cluster IP */ tcp dpt:9153
KUBE-SVC-TCOU7JCQXEZGVUNU  udp  --  anywhere             10.96.0.10           /* kube-system/kube-dns:dns cluster IP */ udp dpt:domain
KUBE-SVC-YQMDS3LBFU4OPAM7  udp  --  anywhere             10.96.149.213        /* default/udp-server cluster IP */ udp dpt:8080
```
where `10.96.149.213` is the cluster IP for the `udp-server` service:
```
$ kubectl get service -owide
NAME         TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)    AGE   SELECTOR
kubernetes   ClusterIP   10.96.0.1       <none>        443/TCP    40m   <none>
udp-server   ClusterIP   10.96.149.213   <none>        8080/UDP   33m   app=udp-server
```
Details of the rule:
```
# iptables -t nat -L KUBE-SVC-YQMDS3LBFU4OPAM7
Chain KUBE-SVC-YQMDS3LBFU4OPAM7 (1 references)
target     prot opt source               destination         
KUBE-MARK-MASQ  udp  -- !10.244.0.0/16        10.96.149.213        /* default/udp-server cluster IP */ udp dpt:8080
KUBE-SEP-MIPKEHYKJ46QT3KB  all  --  anywhere             anywhere             /* default/udp-server -> 10.244.1.2:8080 */ statistic mode random probability 0.50000000000
KUBE-SEP-VLKTSMKO2POLEIZ2  all  --  anywhere             anywhere             /* default/udp-server -> 10.244.1.3:8080 */
```
Where `10.244.1.2` and `10.244.1.3` are the IPs of the pods backing the `udp-server` service.
Explanation of the rules see https://stackoverflow.com/a/54870905

## TODO
- Look at the iptables rules on the node.