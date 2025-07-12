# Play around with sysctls and SELinux

https://kubernetes.io/docs/tasks/configure-pod-container/security-context/#assign-selinux-labels-to-a-container

```bash
$ kubectl apply -f pod.yaml -n restricted 
Error from server (Forbidden): error when creating "pod.yaml": pods "sysctlpod" is forbidden: violates PodSecurity "restricted:v1.32": seLinuxOptions (pod set forbidden securityContext.seLinuxOptions: user may not be set; role may not be set), forbidden sysctls (net.core.somaxconn, kernel.msgmax), allowPrivilegeEscalation != false (container "my-pod" must set securityContext.allowPrivilegeEscalation=false), unrestricted capabilities (container "my-pod" must set securityContext.capabilities.drop=["ALL"]), runAsNonRoot != true (pod or container "my-pod" must set securityContext.runAsNonRoot=true), seccompProfile (pod or container "my-pod" must set securityContext.seccompProfile.type to "RuntimeDefault" or "Localhost")
```