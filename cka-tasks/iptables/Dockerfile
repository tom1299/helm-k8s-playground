# Use the Alpine base image
FROM alpine:latest

# Install iptables and common networking tools
RUN apk add --no-cache \
    iptables \
    netcat-openbsd \
    socat \
    iproute2 \
    curl \
    wget \
    bash \
    inetutils-telnet

# Set a default command to keep the container running
CMD ["sh"]