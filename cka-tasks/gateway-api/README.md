# Gateway API CKA

## TODO
Gateway api:
- Do an example with header matching and default backend if not match could be found
- Do an example for migration from an ingress resource to a gateway api including tls termination and a default backend (?)
- Look at the RegularExpression type of the HTTPPathMatch.
- Define a HTTPRoute with no match but with a backendRef

## Difference ingress gateway
**TLS**:
> In Gateway API, TLS termination is a property of the Gateway listener, and similarly to the Ingress, a TLS certificate and key are also stored in a Secret.
**Rules**:
> The hostnames of an HTTPRoute must match the hostname of the Gateway listener.
Rules api reference: https://gateway-api.sigs.k8s.io/reference/spec/#httprouterule
Match rules: https://gateway-api.sigs.k8s.io/reference/spec/#httproutematch

## Miscelanous
Continue here https://docs.nginx.com/nginx-gateway-fabric/traffic-management/https-termination/

Try redirect and passthrough examples

openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout example.com.key \
  -out example.com.crt \
  -subj "/CN=example.com"


Problem:
https://docs.nginx.com/nginx-gateway-fabric/how-to/traffic-management/tls-passthrough/
To enable experimental features on NGINX Gateway Fabric:

Using Helm: Set nginxGateway.gwAPIExperimentalFeatures.enable to true. An example can be found in the Installation with Helm guide.

Using Kubernetes manifests: Add the --gateway-api-experimental-features command-line flag to the deployment manifest args. An example can be found in the Installation with Kubernetes manifests guide.

Try gateway-tls.yaml with tls passthrough enabled.

## Two identical gateways for 80
Error:
```
{"level":"error","ts":"2025-07-28T06:24:56Z","logger":"eventLoop.eventHandler","msg":"error from provisioner","batchID":17,"error":"error provisioning nginx resources: Service \"example-2-nginx\" is invalid: spec.ports[0].nodePort: Invalid value: 31437: provided port is already allocated","stacktrace":"github.com/nginx/nginx-gateway-fabric/internal/controller.(*eventHandlerImpl).sendNginxConfig.func1\n\t/home/runner/work/nginx-gateway-fabric/nginx-gateway-fabric/internal/controller/handler.go:192"}
{"level":"info","ts":"2025-07-28T06:24:57Z","logger":"eventHandler","msg":"NGINX configuration was successfully updated"}
{"level":"error","ts":"2025-07-28T06:25:02Z","logger":"eventHandler","msg":"error getting Gateway Service IP address","error":"error finding Service example-2-nginx for Gateway: context deadline exceeded","stacktrace":"github.com/nginx/nginx-gateway-fabric/internal/controller.(*eventHandlerImpl).updateStatuses\n\t/home/runner/work/nginx-gateway-fabric/nginx-gateway-fabric/internal/controller/handler.go:326\ngithub.com/nginx/nginx-gateway-fabric/internal/controller.(*eventHandlerImpl).waitForStatusUpdates\n\t/home/runner/work/nginx-gateway-fabric/nginx-gateway-fabric/internal/controller/handler.go:273"}
```
```yaml
kind: Gateway
metadata:
  name: example-1
spec:
  gatewayClassName: nginx
  listeners:
  - protocol: HTTP
    port: 80
    name: prod-web-gw
    allowedRoutes:
      namespaces:
        from: All
---
apiVersion: gateway.networking.k8s.io/v1
kind: Gateway
metadata:
  name: example-2
spec:
  gatewayClassName: nginx
  listeners:
  - protocol: HTTP
    port: 80
    name: prod-web-gw
    allowedRoutes:
      namespaces:
        from: All
---
Probably not possible to have two identical gateways for the same port.
This might not work with nodeport services. See install.sh and kind configuration.
