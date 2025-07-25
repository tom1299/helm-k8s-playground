## UDP Server using socat
`socat -dd STDIO UDP4-LISTEN:8080,reuseaddr,fork`
`-dd` enables more verbose logging.
Alternative command:
`socat -dd STDIO UDP4-RECV:8080,reuseaddr`

## UDP Client using socat
`echo "Message1" | socat - UDP:127.0.0.1:8080`
This takes a long time, set not to wait for a response and the command will run quicker:
`echo "Message1" | socat -t 0 - UDP-SENDTO:127.0.0.1:8080`
Or as a pod:
`kubectl run udp-client --image=alpine/socat --restart=Never --command -- sh -c 'echo "Message1" | socat -t 0 - UDP-SENDTO:udp-server:8080'`

### UDP Client using netcat
`echo "Hello World" | nc -u -w1 127.0.0.1 8080`

## Deployment
`kubectl create deployment udp-server --replicas=2 --image=alpine/socat --port=8080 -- socat -u -dd UDP4-LISTEN:8080,reuseaddr,fork STDIO`

## Service
`kubectl expose deployment udp-server --port=8080 --target-port=8080 --protocol=UDP`

## Additional information
https://gist.github.com/jdimpson/6ae2f91ec133da8453b0198f9be05bd5

See here for specifying source port and other things:
https://superuser.com/questions/1473729/send-udp-packet-and-listen-for-replies

## TODOs
- How to use `create deplyoyment` when only providing args ?
- Which socat udp command to use (LISTEN or RECV) ?
- Write tests that verify the `rr` behaviour.
- Test the other load balancing algorithms.

## Findings
### Deployment
`kubectl create deployment udp-server --image=alpine/socat --port=8080 -- socat -u -dd UDP4-LISTEN:8080,reuseaddr,fork STDIO`
### Service
`kubectl expose deployment udp-server --port=8080 --target-port=8080 --protocol=UDP`
### Client
`kubectl run udp-client --image=alpine/socat --restart=Never --command -- sh -c 'echo "Message1" | socat -t 0 - UDP-SENDTO:udp-server:8080'`
or in order to send requests interactively:
`kubectl run udp-client --image=alpine/socat --restart=Never --command -- sleep infinity`

## Conclusion
Using round robin with udp works. UDP requests are load balanced evenly across the available pods. Even as new replicas are added.