#!/bin/bash
kind create cluster --config ./cluster-config.yaml --name gateway-api-demo

kubectl kustomize "https://github.com/nginx/nginx-gateway-fabric/config/crd/gateway-api/experimental?ref=v2.0.1" | kubectl apply -f -
 
helm install ngf oci://ghcr.io/nginx/charts/nginx-gateway-fabric --create-namespace -n nginx-gateway --set nginx.service.type=NodePort --set nginxGateway.gwAPIExperimentalFeatures.enable=true --set-json 'nginx.service.nodePorts=[{"port":31437,"listenerPort":80},{"port":30916,"listenerPort":443}]'

kubectl wait --for=condition=Ready pod -l app.kubernetes.io/name=nginx-gateway-fabric -n nginx-gateway --timeout=300s

# kubectl create namespace demo

# kubectl config set-context --current --namespace=demo

# certs/create-certs.sh

# kubectl create secret tls internal-cafe-secret \
#   --cert=./certs/ssl.internal.cafe.example.com.crt \
#   --key=./certs/ssl.internal.cafe.example.com.key \
#   --namespace=demo

# kubectl apply -f ./application.yaml

# kubectl wait --for=condition=Ready pod -l app=coffee --timeout=300s

# kubectl wait --for=condition=Ready pod -l app=tea --timeout=300s

# kubectl wait --for=condition=Ready pod -l app=secure-coffee --timeout=300s

# kubectl apply -f ./gateway.yaml

# kubectl wait --for=condition=Ready pod -l app.kubernetes.io/name=gateway-nginx --timeout=300s

# kubectl apply -f ./route.yaml

# for i in {1..10}; do
#     echo "Attempt $i: Testing cafe.example.com/tea endpoint..."
#     if curl --resolve cafe.example.com:8080:127.0.0.1 http://cafe.example.com:8080/tea; then
#         echo "Success on attempt $i!"
#         break
#     else
#         echo "Failed attempt $i. Waiting 10 seconds before trying again..."
#         if [ $i -lt 10 ]; then
#             sleep 10
#         else
#             echo "All attempts failed."
#         fi
#     fi
# done

# kubectl apply -f ./cert.yaml

# kubectl apply -f ./gateway-tls.yaml

# kubectl wait --for=condition=Ready pod -l gateway.networking.k8s.io/gateway-name=cafe-tls --timeout=300s

# for i in {1..10}; do
#     echo "Attempt $i: Testing ssl.cafe.example.com/coffee endpoint..."
#     if curl --insecure --resolve ssl.cafe.example.com:8443:127.0.0.1 https://ssl.cafe.example.com:8443/coffee; then
#         echo "Success on attempt $i!"
#         break
#     else
#         echo "Failed attempt $i. Waiting 10 seconds before trying again..."
#         if [ $i -lt 10 ]; then
#             sleep 10
#         else
#             echo "All attempts failed."
#         fi
#     fi
# done

# kubectl apply -f ./gateway-tls-passthrough.yaml