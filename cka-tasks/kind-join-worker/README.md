# Join a worker node to an existing Kind cluster

## Podman command
```bash
export NODE_NAME=kind-worker-X
podman run --restart on-failure --cpus="2" -v /lib/modules:/lib/modules:ro --privileged -h $NODE_NAME -d --network kind --network-alias $NODE_NAME --tmpfs /run --tmpfs /tmp --security-opt seccomp=unconfined --security-opt apparmor=unconfined --security-opt label=disable -v /var --name $NODE_NAME --label io.x-k8s.kind.cluster=kind --label io.x-k8s.kind.role=worker --env KIND_EXPERIMENTAL_CONTAINERD_SNAPSHOTTER docker.io/kindest/node:v1.33.1
```
## Joining
After running kubeadm token create --print-join-command on the control plane node has the following error:
```bash
CGROUPS_CPU: enabled
CGROUPS_CPUSET: missing
CGROUPS_DEVICES: enabled
CGROUPS_FREEZER: enabled
CGROUPS_MEMORY: enabled
CGROUPS_PIDS: enabled
CGROUPS_HUGETLB: missing
CGROUPS_IO: enabled
	[WARNING SystemVerification]: missing optional cgroups: hugetlb
error execution phase preflight: [preflight] Some fatal errors occurred:
	[ERROR SystemVerification]: missing required cgroups: cpuset
[preflight] If you know what you are doing, you can make a check non-fatal with `--ignore-preflight-errors=...`
To see the stack trace of this error execute with --v=5 or higher
```
Ignore the error and run the join command with the following options:
```bash
kubeadm join ... --ignore-preflight-errors=SystemVerification
```

# TODO
- Find out why the cgroup cpuset is missing and fix it. Edit: Seems really to be related to Podman rootless as the same command works yields
  the same error on the control plane node:
    ```bash
    kubeadm init phase preflight
    ``` 
- Find out whether it is possible to ignore specific errors instead of all SystemVerification errors.
