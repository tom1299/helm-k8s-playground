#!/bin/bash
kubectl delete pods --grace-period=0 --force --ignore-not-found --selector=app=networking-test
kubectl run pod-worker1-1 --image=nicolaka/netshoot --labels="app=networking-test" -oyaml --dry-run=client --command -- sleep infinity |  kubectl patch -f - --patch '{"spec":{"nodeName": "kind-worker"}}' --dry-run=client -oyaml | kubectl apply -f -
kubectl run pod-worker1-2 --image=nicolaka/netshoot --labels="app=networking-test" -oyaml --dry-run=client --command -- sleep infinity |  kubectl patch -f - --patch '{"spec":{"nodeName": "kind-worker"}}' --dry-run=client -oyaml | kubectl apply -f -
kubectl run pod-worker2 --image=nicolaka/netshoot --labels="app=networking-test" -oyaml --dry-run=client --command -- sleep infinity |  kubectl patch -f - --patch '{"spec":{"nodeName": "kind-worker2"}}' --dry-run=client -oyaml | kubectl apply -f -

POD_WORKER1_1_IP=$(kubectl get pod -o jsonpath='{.items[?(@.metadata.name=="pod-worker1-1")].status.podIP}')
# 10.122.1.6
# The IP address of pod-worker1-1
kubectl wait --for=condition=Ready pod/pod-worker1-1 --timeout=60s


POD_WORKER1_2_IP=$(kubectl get pod -o jsonpath='{.items[?(@.metadata.name=="pod-worker1-2")].status.podIP}')
POD_WORKER2_IP=$(kubectl get pod -o jsonpath='{.items[?(@.metadata.name=="pod-worker2")].status.podIP}')

podman exec -ti kind-worker ip address
# Example output:
#
# 7: vethda4630db@if2: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue state UP group default qlen 1000
#    link/ether 5a:e9:d8:9c:f6:ac brd ff:ff:ff:ff:ff:ff link-netns cni-c9ba3e83-3079-05ca-d20d-5e6bd5be287c
#    inet 10.122.1.1/32 scope global vethda4630db
#       valid_lft forever preferred_lft forever
#    inet6 fe80::d069:fdff:fece:17fd/64 scope link
#       valid_lft forever preferred_lft forever
# 8: veth1b333ef3@if2: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue state UP group default qlen 1000
#    link/ether b2:77:44:f0:5b:cb brd ff:ff:ff:ff:ff:ff link-netns cni-9f0ea51a-2f59-8e19-0df1-fafb0bfe3135
#    inet 10.122.1.1/32 scope global veth1b333ef3
#       valid_lft forever preferred_lft forever
#    inet6 fe80::b077:44ff:fef0:5bcb/64 scope link
#       valid_lft forever preferred_lft forever
#
# Explanation of the output:
# For each pod on the worker node, there is a veth interface created with the ip address

kubectl exec pod-worker1-1 -- ip route
# Example output:
# dev = device name
#
# default via 10.122.1.1 dev eth0
# 10.122.1.0/24 via 10.122.1.1 dev eth0 src 10.122.1.6
# 10.122.1.1 dev eth0 scope link src 10.122.1.6
#
# Explanation of the output:
#
# default via 10.122.1.1 dev eth0
# All traffic to destinations not in the routing table goes to the gateway 10.122.1.1 (node) via interface eth0.
#
# 10.122.1.0/24 via 10.122.1.1 dev eth0 src 10.122.1.6
# Traffic to the subnet 10.122.1.0/24 is routed through 10.122.1.1 (node) using eth0, with source IP 10.122.1.6 (pod id).
#
# 10.122.1.1 dev eth0 scope link src 10.122.1.6
# Directly reachable IP 10.122.1.1 on eth0, with source IP 10.122.1.6.
# This extra line for 10.122.1.1 (node ip) indicates that 10.122.1.1 is
# directly reachable on the local network (no gateway needed),
# while the other line (10.122.1.0/24 via 10.122.1.1 ...) defines
# routing for the whole subnet through 10.122.1.1 as a gateway.
# The dedicated line ensures the pod can communicate directly with the gateway IP for ARP and local traffic.
#
# "scope link" restricts the route to addresses reachable on the local link (i.e., the same Layer 2 network segment)

podman exec -ti kind-worker ip route
# Example output:
#
# default via 10.89.0.1 dev eth0 proto static metric 100
# 10.122.0.0/24 via 10.89.0.9 dev eth0
# 10.122.1.6 dev veth0b88a07e scope host  # This is the IP of pod-worker1-1
# 10.122.1.7 dev vethfc4ed760 scope host   # This is the IP of pod-worker1-2
# 10.122.2.0/24 via 10.89.0.11 dev eth0
#
# In kind each worker gets its own ip range, so that routes are not overlapping:
#
# $ kubectl get pod -o jsonpath='{.items[?(@.metadata.name=="pod-test-worker")].status.podIP}'
# 10.122.3.2  # Running on test-worker node (added later)
# $ kubectl get pod -o jsonpath='{.items[?(@.metadata.name=="pod-worker1-1")].status.podIP}'
# 10.122.1.2  # Running on kind-worker node (first)
# $ kubectl get pod -o jsonpath='{.items[?(@.metadata.name=="pod-worker2")].status.podIP}'
# 10.122.2.2  # Running on kind-worker2 node (second)
#
# When a new worker is added, it gets a new range, so the routes do not overlap.
# Confirmaation:
#
# kubectl get nodes -o jsonpath="{range .items[*]}{.metadata.name}{'\t'}{.spec.podCIDR}{'\n'}{end}"
# kind-control-plane	10.122.0.0/24
# kind-worker	10.122.1.0/24
# kind-worker2	10.122.2.0/24
# test-worker	10.122.3.0/24

