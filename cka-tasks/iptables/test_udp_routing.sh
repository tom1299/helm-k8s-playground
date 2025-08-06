#!/bin/bash

timeout 1 docker exec client sh -c 'echo "Hello from client via udp" | nc -u -w0 192.168.1.1 27017'
sleep 0.1

if ! docker logs backend | grep -q "Hello from client via udp"; then
    echo "FAILED: Message not found"
    exit 1
fi
