#!/bin/bash

for i in {1..10}; do
  POD_NAME="pod-$i"
  SERVICE_NAME="service-$i"
  if kubectl get pod $POD_NAME >/dev/null 2>&1; then
    kubectl delete pod $POD_NAME
    kubectl wait --for=delete pod/$POD_NAME --timeout=60s
  fi
  if kubectl get service $SERVICE_NAME >/dev/null 2>&1; then
    kubectl delete service $SERVICE_NAME
  fi
  cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: $POD_NAME
  labels:
    app: $POD_NAME
spec:
  containers:
  - name: nginx
    image: nginx:alpine
    ports:
    - containerPort: 80
    command: ["/bin/sh"]
    args: ["-c", "echo 'Hello from pod $i' > /usr/share/nginx/html/index.html && nginx -g 'daemon off;'"]
---
apiVersion: v1
kind: Service
metadata:
  name: $SERVICE_NAME
spec:
  selector:
    app: $POD_NAME
  ports:
  - port: 8080
    targetPort: 80
    protocol: TCP
  type: ClusterIP
EOF
done

for i in {1..10}; do
  POD_NAME="pod-$i"
  SERVICE_NAME="service-$i"
  kubectl wait --for=condition=ready pod/$POD_NAME --timeout=60s
  kubectl wait --for=jsonpath='{.endpoints[0].targetRef.name}'=$POD_NAME endpointslices -l kubernetes.io/service-name=$SERVICE_NAME --timeout=60s
done