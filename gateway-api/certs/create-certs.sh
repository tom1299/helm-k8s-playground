#!/bin/bash
rm ssl.internal.cafe.example.com.key ssl.internal.cafe.example.com.csr ssl.internal.cafe.example.com.crt

openssl genrsa -out ssl.internal.cafe.example.com.key 2048

openssl req -new -key ssl.internal.cafe.example.com.key -out ssl.internal.cafe.example.com.csr \
  -subj "/CN=example.com"

openssl x509 -req -in ssl.internal.cafe.example.com.csr -signkey ssl.internal.cafe.example.com.key \
  -out ssl.internal.cafe.example.com.crt -days 365
