# Kube proxy examples

## Kube proxy in ipvs mode
An example showing the different load balancing algorythms 

## Traiif policies
Shows how the different internal and external traffic policies work.
Inclduing an example where packages are dropped.

## kind kube-proxy configuration
Find out how to confire kube-proxy for kind.
Runs as pod with a (generated ?) configuraiton:
```bash
$ kubectl exec -ti -n kube-system kube-proxy-t8c4k -- cat /var/lib/kube-proxy/config.conf
apiVersion: kubeproxy.config.k8s.io/v1alpha1
bindAddress: 0.0.0.0
bindAddressHardFail: false
clientConnection:
  acceptContentTypes: ""
  burst: 0
  contentType: ""
  kubeconfig: /var/lib/kube-proxy/kubeconfig.conf
  qps: 0
clusterCIDR: 10.244.0.0/16
```
