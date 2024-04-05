# ingress-test
## Purpose
Test how an nginx ingress controller deals with ingresses having duplicate host names / and or pathes

## Setup
* 2-x ingresses with different configurations
* nginx ingress controller
* two services that just print the request to stdout `podman run -p 8080:8080 -p 8443:8443 --rm -t mendhak/http-https-echo`

## Questions to answer
* How does the nginx ingress controller work with similar ingress configurations
* Configure an nginx ingress to set the `X-FORWARDE-FOR` header

## Deployment
### Test
`helm template --debug -f ingress-test/test-values.yaml ingress-test ingress-test/`
