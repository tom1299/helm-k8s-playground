# Taints and tolerations

## Questions
Why is it possible to add multiple taints wit the same key but different effects to a node?
```bash
kubectl taint nodes mission-critical-node mission-critical:PreferNoSchedule
kubectl taint nodes mission-critical-node mission-critical:NoExecute
```
```yaml
spec:
  podCIDR: 10.244.1.0/24
  podCIDRs:
  - 10.244.1.0/24
  providerID: kind://docker/kind/kind-worker
  taints:
  - effect: PreferNoSchedule
    key: mission-critical
  - effect: NoExecute
    key: mission-critical
  - effect: NoSchedule
    key: mission-critical
```
Reason: Allows fine-grained control over pod scheduling since tolerations are a combination of key and effect.

## TODO
Look at https://kubernetes.io/docs/concepts/scheduling-eviction/taint-and-toleration/#concepts.
Verify the description with the help of the kubectl taint command.

## Possible bug in help of kubectl taint
```bash
Examples:
  # Update node 'foo' with a taint with key 'dedicated' and value 'special-user' and effect 'NoSchedule'
  # If a taint with that key and effect already exists, its value is replaced as specified
  kubectl taint nodes foo dedicated=special-user:NoSchedule
```
Trying this example:
```bash
$ kubectl taint nodes mission-critical-node dedicated=special-user:NoSchedule
node/mission-critical-node tainted
$ kubectl taint nodes mission-critical-node dedicated=special-user2:NoSchedule
error: node mission-critical-node already has dedicated taint(s) with same effect(s) and --overwrite is false
$ kubectl taint nodes mission-critical-node dedicated=special-user2:NoSchedule --overwrite=true
node/mission-critical-node modified
```

Needs option `--overwrite` to replace existing taint with the same key and effect:
```bash
kubectl taint nodes foo dedicated=special-user:NoSchedule --overwrite=true
```