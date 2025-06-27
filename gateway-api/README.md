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