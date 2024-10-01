#!/bin/bash

# Function to log messages
log() {
  echo "$(date +'%Y-%m-%d %H:%M:%S') - $1"
}

# Function to handle errors
error_exit() {
  log "ERROR: $1"
  exit 1
}

# Check if the correct number of arguments is provided
if [ "$#" -ne 3 ]; then
  error_exit "Usage: $0 <issuer-name> <namespace> <certbot-server>"
fi

ISSUER_NAME=$1
NAMESPACE=$2
CERTBOT_SERVER=$3

# Set default directories for certbot
CERTBOT_CONFIG_DIR=${CERTBOT_CONFIG_DIR:-~/.certbot/config}
CERTBOT_WORK_DIR=${CERTBOT_WORK_DIR:-~/.certbot/work}
CERTBOT_LOG_DIR=${CERTBOT_LOG_DIR:-~/.certbot/logs}

# Create a temporary directory for storing key and cert files
TEMP_DIR=$(mktemp -d)
if [ ! -d "$TEMP_DIR" ]; then
  error_exit "Failed to create temporary directory"
fi
log "Created temporary directory: $TEMP_DIR"

# Get the list of secrets with the specified issuer name
log "Fetching secrets with issuer name '$ISSUER_NAME' in namespace '$NAMESPACE'..."
SECRETS=$(kubectl get secrets -n "$NAMESPACE" -o jsonpath="{.items[?(@.metadata.annotations['cert-manager.io/issuer-name']=='$ISSUER_NAME')].metadata.name}")

if [ -z "$SECRETS" ]; then
  error_exit "No secrets found with issuer name '$ISSUER_NAME' in namespace '$NAMESPACE'"
fi

# Loop through each secret and revoke the certificate
for SECRET in $SECRETS; do
  log "Processing secret '$SECRET'..."

  # Extract the private key and certificate
  kubectl get secret "$SECRET" -n "$NAMESPACE" -o jsonpath="{.data['tls\.key']}" | base64 --decode > "$TEMP_DIR/${SECRET}.key" || error_exit "Failed to extract private key from secret '$SECRET'"
  kubectl get secret "$SECRET" -n "$NAMESPACE" -o jsonpath="{.data['tls\.crt']}" | base64 --decode > "$TEMP_DIR/${SECRET}.pem" || error_exit "Failed to extract certificate from secret '$SECRET'"

  # Revoke the certificate using certbot
  log "Revoking certificate for secret '$SECRET'..."
  certbot revoke --cert-path "$TEMP_DIR/${SECRET}.pem" --key-path "$TEMP_DIR/${SECRET}.key" --reason superseded --server "$CERTBOT_SERVER" --config-dir "$CERTBOT_CONFIG_DIR" --work-dir "$CERTBOT_WORK_DIR" --logs-dir "$CERTBOT_LOG_DIR" || error_exit "Failed to revoke certificate for secret '$SECRET'"

  log "Certificate for secret '$SECRET' revoked successfully."
done

# Clean up the temporary directory
rm -rf "$TEMP_DIR"
log "Temporary directory $TEMP_DIR removed."

log "All certificates revoked successfully."