#!/bin/bash

timeout 1 docker exec client sh -c 'echo "Hello from client" | nc -t -w0 192.168.1.1 27018'
sleep 0.1

if ! docker logs backend2 | grep -q "Hello from client"; then
    echo "FAILED: Message not found"
    exit 1
fi
