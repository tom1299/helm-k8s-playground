#!/bin/bash

set -e

# Create the cluster if it doesn't exist
if ! kind get clusters | grep -q '^kind$'; then
  if [[ ! -d /tmp/mysql ]]; then
    mkdir -p /tmp/mysql
  fi
  kind create cluster --config kind/kind.yaml
else
  echo "Cluster already exists"
fi

# Wait until all pods in the namespace kube-system are running
echo "Waiting for all pods in the namespace kube-system to be running..."
kubectl wait --for=condition=Ready pods --all --namespace kube-system --timeout=120s

# Apply PersistentVolume resources if they don't exist
if ! kubectl get pv prometheus &>/dev/null; then
  kubectl apply -f kind/pvs.yaml
else
  echo "PersistentVolumes already exist"
fi

# Wait until the pvs are in the state available
echo "Waiting for all PersistentVolumes to be available..."
timeout=120
interval=5
elapsed=0

# Get the number of persistent volumes
persistent_volume_count=$(kubectl get pv --no-headers | wc -l)
echo "Number of PersistentVolumes to be available: $persistent_volume_count"

while [[ $(kubectl get pv -o jsonpath='{.items[*].status.phase}' | grep -o 'Available' | wc -l) -ne persistent_volume_count ]]; do
  if [[ $elapsed -ge $timeout ]]; then
    echo "Timeout waiting for PersistentVolumes to be available"
    exit 1
  fi
  echo "Waiting for PersistentVolumes to be available..."
  sleep $interval
  elapsed=$((elapsed + interval))
done

# Apply KEDA resources if they don't exist
if ! kubectl get ns keda &>/dev/null; then
  kubectl apply --server-side -f https://github.com/kedacore/keda/releases/download/v2.14.1/keda-2.14.1.yaml
else
  echo "KEDA resources already exist"
fi

# Wait until all pods in the namespace keda are running
echo "Waiting for all pods in the namespace keda to be running..."
kubectl wait --for=condition=Ready pods --all --namespace keda --timeout=120s

# Apply monitoring namespace if it doesn't exist
if ! kubectl get ns monitoring &>/dev/null; then
  kubectl apply -f monitoring-namespace.yaml
else
  echo "Monitoring namespace already exists"
fi

# Install Prometheus operator if it doesn't exist
if ! helm list -n monitoring | grep -q 'prometheus-operator'; then
  helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
  helm repo update
  helm install prometheus-operator prometheus-community/kube-prometheus-stack -n monitoring -f prometheus-installation/values.yaml
else
  echo "Prometheus operator already installed"
fi

# Wait until all pods in the monitoring namespace are running
echo "Waiting for all pods in the namespace monitoring to be running..."
kubectl wait --for=condition=Ready pods --all --namespace monitoring --timeout=120s

# Apply httpd namespace if it doesn't exist
if ! kubectl get ns httpd-autoscaling &>/dev/null; then
  kubectl apply -f httpd/httpd-namespace.yaml
else
  echo "httpd namespace already exists"
fi

# Apply httpd resources
kubectl apply -k ./httpd

# Wait until all pods in the namespace httpd-autoscaling are running
echo "Waiting for all pods in the namespace httpd-autoscaling to be running..."
kubectl wait --for=condition=Ready pods --all --namespace httpd-autoscaling --timeout=120s

echo "All commands executed successfully."