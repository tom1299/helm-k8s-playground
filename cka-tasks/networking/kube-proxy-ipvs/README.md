# Use kube-proxy in ipvs mode
Configure kind to use ipvs: https://kind.sigs.k8s.io/docs/user/configuration/#kube-proxy-mode
and extra port mapping for node port services:
https://kind.sigs.k8s.io/docs/user/configuration/#nodeport-with-port-mappings

## Questions:
- Are there any other configuration options for kube-proxy available in kind? Especially regarding load balancing with ipvs (https://kubernetes.io/docs/reference/config-api/kube-proxy-config.v1alpha1/).

## Findings
- In kind kube-proxy is a daemonset
- Configuration is done [here](https://github.com/kubernetes-sigs/kind/blob/5d59e3be91212cd98737be6bf38230dbf20819dc/pkg/cluster/internal/kubeadm/config.go#L299)

## Conclusion
- Configuration of the kube-proxy could be done using [Kubeadm Config Patches](https://kind.sigs.k8s.io/docs/user/configuration/#kubeadm-config-patches).
