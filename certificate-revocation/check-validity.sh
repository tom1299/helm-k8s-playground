#!/bin/bash

# Function to log messages
log() {
  echo "$(date +'%Y-%m-%d %H:%M:%S') - $1"
}

# Function to handle errors
error_log() {
  log "ERROR: $1"
}

# Check if the correct number of arguments is provided
if [ "$#" -ne 2 ]; then
  error_log "Usage: $0 <namespace> <secret_name>"
  exit 1
fi

NAMESPACE=$1
SECRET_NAME=$2

# Extract the certificate from the Kubernetes secret
log "Extracting certificate from secret '$SECRET_NAME' in namespace '$NAMESPACE'..."
CERT_DATA=$(kubectl get secret "$SECRET_NAME" -n "$NAMESPACE" -o jsonpath="{.data['tls\.crt']}")

if [ -z "$CERT_DATA" ]; then
  error_log "Failed to extract certificate from secret '$SECRET_NAME'"
  exit 1
fi

# Decode the certificate
CERT=$(echo "$CERT_DATA" | base64 --decode)

# Get the expiry date of the certificate
EXPIRY_DATE=$(echo "$CERT" | openssl x509 -noout -enddate | cut -d= -f2)
EXPIRY_DATE_EPOCH=$(date -d "$EXPIRY_DATE" +%s)
CURRENT_DATE_EPOCH=$(date +%s)

# Calculate the hours until expiration
HOURS_UNTIL_EXPIRY=$(( (EXPIRY_DATE_EPOCH - CURRENT_DATE_EPOCH) / 3600 ))

# Display the expiry date and hours until expiration
log "Certificate expiry date: $EXPIRY_DATE"
log "Hours until expiry: $HOURS_UNTIL_EXPIRY"