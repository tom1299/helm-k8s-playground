#!/bin/bash
rm example-4.com.key example-4.com.csr example-4.com.crt

openssl genrsa -out example-4.com.key 2048

openssl req -new -key example-4.com.key -out example-4.com.csr \
  -subj "/CN=example4.com"

openssl x509 -req -in example-4.com.csr -signkey example-4.com.key \
  -out example-4.com.crt -days 365

kubectl create secret tls example-4-tls-secret --key=example-4.com.key --cert=example-4.com.crt
