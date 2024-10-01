# Script for revoking certificates

## Problem statement
Revoking certificates installed in a kubernetes cluster using certbot can only be done by extracting the
private key and public certificate from the corresponding secret and then using `certbot revoke` with these files.

## Solution
The goal of this task is to produce a script using AI assistant tools to automate the certificate revocation.

### Boundary conditions
* The script should be bash
* Only kubectl and certbot commands should be used
* The revocation is restricted to certificates in a single namespace

## Prerequisites
* certbot has already been registered with the certificate provider (e.g. let's encrypt)
* Parameters to the script are:
  * The name of the issuer to be used to select the certificates (see)
  * The namespace
  * The server to use with certbot
* certbot config-dir, work-dir and log-dir should default to `~/.certbot/config`, `~/.certbot/work` and `~/.certbot/logs` but can be overridden using appropriately named environment variables
* The script should be easy to understand
* The script should abort if any error occurs
* The script should contain detailed log statements especially in case of an error

## Preliminary process description
* Use kubectl to select the names of the secrets from the certificates that match a certain `spec.issuerRef.name` in a specific namespace and store the names of the certificates in a list
* For each secret extract the private key and public certificate in files with the secret name as a prefix. E.g: `mywebsite-tls-secret.key` and `mywebsite-tls-secret.pem` in a temporary folder that is created by the script
* Use the `certbot revoke` command with the reason `superseded` to revoke the certificate stored in the files
* Example invocation: `./revoke-certs.sh my-issuer my-namspace https://letsencrytp/v2/my-id/directory`