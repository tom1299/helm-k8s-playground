#!/bin/bash

# Send multiple messages to test load balancing
for i in {1..6}; do
    timeout 1 docker exec client sh -c "echo \"Udp load balance message $i\" | nc -u -w0 192.168.1.1 27019"
done

sleep 0.2

# Check if messages were distributed across backends
BACKEND1_COUNT=$(docker logs backend | grep -c "Udp load balance message")
BACKEND2_COUNT=$(docker logs backend2 | grep -c "Udp load balance message") 
BACKEND3_COUNT=$(docker logs backend3 | grep -c "Udp load balance message")

echo "Backend1 received: $BACKEND1_COUNT messages"
echo "Backend2 received: $BACKEND2_COUNT messages"  
echo "Backend3 received: $BACKEND3_COUNT messages"

# Verify each backend received exactly 2 messages
if [ "$BACKEND1_COUNT" -ne 2 ] || [ "$BACKEND2_COUNT" -ne 2 ] || [ "$BACKEND3_COUNT" -ne 2 ]; then
    echo "FAILED: Expected 2 messages per backend"
    exit 1
fi

echo "SUCCESS: Perfect load balancing - each backend received 2 messages"
