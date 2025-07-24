# Use kube-proxy in ipvs mode
Configure kind to use ipvs: https://kind.sigs.k8s.io/docs/user/configuration/#kube-proxy-mode
and extra port mapping for node port services:
https://kind.sigs.k8s.io/docs/user/configuration/#nodeport-with-port-mappings

## Questions:
- Are there any other configuration options for kube-proxy available in k^ind? Especially regarding load balancing with ipvs (https://kubernetes.io/docs/reference/config-api/kube-proxy-config.v1alpha1/).
- How does kubernetes work without kube-proxy?

## Findings
- In kind kube-proxy is a daemonset
- Configuration is done [here](https://github.com/kubernetes-sigs/kind/blob/5d59e3be91212cd98737be6bf38230dbf20819dc/pkg/cluster/internal/kubeadm/config.go#L299)
- Kube proxy can only be configured for the whole cluster using the `kubeadmConfigPatches` in the kind config file.
- Running kube-proxy in ipvs mode requires the `ipvs` kernel module permissions. Using rootless podman results in the following error:
```
E0724 05:58:59.052824       1 proxier.go:596] "Can't read the ipvs" err="could not get IPVS services: operation not permitted"
E0724 05:58:59.052847       1 server.go:136] "Error running ProxyServer" err="can't use the IPVS proxier: could not get IPVS services: operation not permitted"
```

## Conclusion
- Configuration of the kube-proxy could be done using [Kubeadm Config Patches](https://kind.sigs.k8s.io/docs/user/configuration/#kubeadm-config-patches).
- IPVS load balancing configuration, see here: https://kubernetes.io/blog/2018/07/09/ipvs-based-in-cluster-load-balancing-deep-dive/#ipvs-based-kube-proxy
- Scheduler can be set here: https://kubernetes.io/docs/reference/config-api/kube-proxy-config.v1alpha1/#kubeproxy-config-k8s-io-v1alpha1-KubeProxyIPVSConfiguration

## TODO
Find to understand this paragraph:
https://kind.sigs.k8s.io/docs/user/configuration/#kubeadm-config-patches
Especially the last part
