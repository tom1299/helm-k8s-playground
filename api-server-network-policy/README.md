# Template function description
Abstract: The function creates a network policy that allows egress traffic for the tcp protocol to the api server pods.
It will do so by looking up the endpoint of the kubernetes service and add each ip as an ip block to the network policy.
The endpoint yaml looks like this:
```yaml
apiVersion: v1
kind: Endpoints
metadata:
  labels:
    endpointslice.kubernetes.io/skip-mirror: "true"
  name: kubernetes
  namespace: default
subsets:
- addresses:
  - ip: 10.108.166.221
  - ip: 10.108.166.222
  - ip: 10.108.166.223
  ports:
  - name: https
    port: 6443
    protocol: TCP
```
* Name: "egress2apiserver"
* Abstract: The function creates a network policy that allows egress traffic for the tcp protocol to the api server pods.
* Parameters: The name of the Pod as a string to which the network policy applies to
* The function does the following:
  1. Use the helm template function to lookup the endpoint named kubernetes in the default namespace
  2. It will create an egress configuration as follows:
     1. From the resulting dictionary the function will do the following:
     2. For the port in `ports` it will add an IP for each `addresses.ip` to allow egress
  3. It will add an annotation with the current time at which the network policy was created
  5. It will return the network policy yaml as a string