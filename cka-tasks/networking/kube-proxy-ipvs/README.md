# Use kube-proxy in ipvs mode
Configure kind to use ipvs: https://kind.sigs.k8s.io/docs/user/configuration/#kube-proxy-mode
and extra port mapping for node port services:
https://kind.sigs.k8s.io/docs/user/configuration/#nodeport-with-port-mappings

## Questions:
- Are there any other configuration options for kube-proxy available in kind? Especially regarding load balancing with ipvs (https://kubernetes.io/docs/reference/config-api/kube-proxy-config.v1alpha1/).
