# Goal
Deploy three replicas of a deployment to the node with class critical.
Each pod should get the exact same amount of cpu.

# Resources
https://kubernetes.io/docs/tasks/administer-cluster/cpu-management-policies/
https://kubernetes.io/docs/concepts/policy/node-resource-managers/

# Reducing the number of cpus for a node in kind
* Get the number of allocatable CPUs in the cluster
    ```bash
    kubectl get node critical-workload-node -o jsonpath='{.status.allocatable.cpu}'
    ```
* Adjust the number of CPUs in the kind cluster
    ```yaml
    - role: worker
    labels:
        class: critical
    extraMounts:
    kubeadmConfigPatches:
    - |
        kind: JoinConfiguration
        nodeRegistration:
        name: critical-workload-node
        kubeletExtraArgs:
            system-reserved: "cpu=10,memory=2Gi"
            kube-reserved: "cpu=8,memory=2Gi"
    ```
* In the example above, the node has 10 CPUs and 2Gi of memory reserved for system processes and 8 CPUs and 2Gi of memory reserved for kubelet processes. Given that the node has 20 CPUs, the maximum number of CPUs available for pods is 20 - 10 - 8 = 2 CPUs.

# Trying to deploy a pod with more than 2 CPUs
```bash
kubectl run --image nginx:latest --dry-run=client -oyaml nginx | kubectl set resources --requests=cpu=3 --local -oyaml -f - | kubectl apply -f -
```
Result:
```
kubectl describe pod nginx
...
Events:
  Type     Reason            Age                 From               Message
  ----     ------            ----                ----               -------
  Warning  FailedScheduling  59s (x14 over 66m)  default-scheduler  0/2 nodes are available: 1 Insufficient cpu, 1 node(s) had untolerated taint {node-role.kubernetes.io/control-plane: }. preemption: 0/2 nodes are available: 1 No preemption victims found for incoming pod, 1 Preemption is not helpful for scheduling.
```
The event shows that:
* There are 2 nodes in the cluster.
* One node has insufficient CPU resources (worker node).
* The other node has a taint that prevents the pod from being scheduled on it (control-plane node).

# 3 replicas of a deployment each getting the same amount of CPU
From k8s documentation:
> a Pod can consume as much CPU and memory as is allowed by the ResourceQuotas that apply to that namespace. As a cluster operator, or as a namespace-level administrator, you might also be concerned about making sure that a single object cannot monopolize all available resources within a namespace.

```bash
kubectl create namespace quota
kubectl apply -f limit-range.yaml -n quota
kubectl create quota my-quota --hard=cpu=2,pods=3,resourcequotas=1 -n quota
kubectl create deployment --image nginx:latest --replicas 3 -n quota nginx
```
This will only work if the limit range is set to allow 630m of CPU per pod which has enough headroom for the 3 replicas to be scheduled on the node with class critical.

