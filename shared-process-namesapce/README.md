Context: k8s, apache httpd, sidecar, configmap watcher

## Implement the following Pod and ConfigMap:

General Pod requirements:
* The Pod should have two containers: the main container and a sidecar container.
* The main container should be an Apache HTTPD server that serves a single static HTML page.
* The content of the HTML page should be configurable via the ConfigMap named `html-content`.
* The sidecar container should watch for changes to the ConfigMap and signal the main container to reload using the kill command.
* The Pod should be configured whit "shareProcessNamespace" in order for the sidecar container to be able to communicate with the main container.
* Both containers should have the following securityContext:
  ```
    securityContext:
      allowPrivilegeEscalation: false
      capabilities:
        drop:
        - ALL
        - CAP_NET_RAW
      readOnlyRootFilesystem: true
      runAsNonRoot: true
  ```
* The Pod should have the following securityContext:
  ```
  securityContext:
    fsGroup: 3000
    runAsGroup: 10000
    runAsUser: 10003
    seccompProfile:
      type: RuntimeDefault
  ```
* The Pod should not automount the default service account token.

Main container:
* The main container should be an Apache HTTPD server that serves a single static HTML page.
* The content of the HTML page should be configurable via the ConfigMap named `html-content`.
 
Sidecar container:
* The sidecar container should watch for changes to the ConfigMap and update the main container with the new content.
* The sidecar container should use the `inotifywait` command to watch for changes to the ConfigMap.
* On a change of the ConfigMap, the sidecar should signal the main container to reload using the command `kill -s SIGUSR1 1`.
