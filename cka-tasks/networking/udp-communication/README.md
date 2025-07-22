## UDP Server using socat
`socat STDIO UDP4-LISTEN:8080,reuseaddr,fork`

## UDP Client
`echo "Message1" | socat - UDP:127.0.0.1:8080`