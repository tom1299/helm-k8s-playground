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

