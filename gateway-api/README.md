Continue here https://docs.nginx.com/nginx-gateway-fabric/traffic-management/https-termination/

Try redirect and passthrough examples

openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout example.com.key \
  -out example.com.crt \
  -subj "/CN=example.com"