## UDP Server using socat
`socat -dd STDIO UDP4-LISTEN:8080,reuseaddr,fork`
`-dd` enables more verbose logging.

## UDP Client using socat
`echo "Message1" | socat - UDP:127.0.0.1:8080`
This takes a long time, set not to wait for a response and the command will run quicker:
`echo "Message1" | socat -t 0 - UDP-SENDTO:127.0.0.1:8080`

### UDP Client using netcat
`echo "Hello World" | nc -u -w1 127.0.0.1 8080`
Quicker than above

## Deployment
`kubectl create deployment udp-server --image=alpine/socat --port=8080 -- socat -dd STDIO UDP4-LISTEN:8080,reuseaddr,fork`

## Additional information
https://gist.github.com/jdimpson/6ae2f91ec133da8453b0198f9be05bd5

See here for specifying source port and other things:
https://superuser.com/questions/1473729/send-udp-packet-and-listen-for-replies