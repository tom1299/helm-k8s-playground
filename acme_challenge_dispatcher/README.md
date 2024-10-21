# Acme challenge dispatcher
A simple web server that dispatches acme challenges to the correct acme client.
It receives acme challenges in the form of HTTP requests and forwards them to the correct acme client.

## Prerequisites
* The web server should be written in python
* It should be based on pythons simple http server
* Logging should be done in json format and should be cloud native
* All requests to acme clients should use a timeout of 1 second

## Detailed description
* The dispatcher listens for incoming HTTP requests on port 8080
* It will process get requests in the form of `http://<dispatcher-ip>:8080/.well-known/acme-challenge/<challenge-token>`
* If the path of the request does not start with `/.well-known/acme-challenge/`, the dispatcher will log the request and immediately return a 404
* The dispatcher will then extract the token from the request and the host header
* It will log the token and the host header
* Using the kubernetes API, the dispatcher will then look up all Pods that have the label `acme=enabled` and get their IP addresses
* For each IP the dispatcher will send a POST request to `http://<pod-ip>:8080/.well-known/acme-challenge/<challenge-token>` with the host header set to the host header from the original request
* The dispatcher will log the response from the acme client
* If the dispatcher receives a 200 response from any of the acme clients, it will log success and return the response to the original requestor.
* If the dispatcher receives a 200 response it will store the IP of the acme client in a dict with the token as the key
* It will then use this dict to forward any subsequent requests with the same token to the same acme client
* If the dispatcher receives a response code other than 200 from a client it will log the response and continue to the next client
* If all clients return a response code other than 200, the dispatcher will return a 404 error to the original requestor and log an error

## Implementation details
* The implementation of extracting the token and host header from the request should be in own functions
* The implementation of sending the request to the acme clients should be in own function
* The implementation of getting the acme clients from the kubernetes API should be in own function