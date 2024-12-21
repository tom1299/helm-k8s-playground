#!/bin/bash

if [ -z "$1" ]; then
  NEW_VALUE=$(date +%s)
else
  NEW_VALUE=$1
fi

CONFIGMAPS=$(kubectl get configmaps -o json | jq -r '.items[] | select(.metadata.name | startswith("echo-values-cm-")) | .metadata.name')

if [ -z "$CONFIGMAPS" ]; then
  echo "No matching ConfigMaps found"
  exit 1
fi

for CONFIGMAP in $CONFIGMAPS; do
  PATCH_OUTPUT=$(kubectl patch configmap $CONFIGMAP -p "{\"data\":{\"value\":\"$NEW_VALUE\"}}")
  if [ $? -ne 0 ]; then
    echo "Failed to update ConfigMap $CONFIGMAP"
    echo $PATCH_OUTPUT
    exit 1
  else
    echo "Succeeded to update ConfigMap $CONFIGMAP": "$PATCH_OUTPUT"
  fi
done

echo "Updated data.value field in all matching ConfigMaps to $NEW_VALUE"
