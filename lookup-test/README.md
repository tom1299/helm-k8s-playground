## Commands
```shell
$ kubectl apply -n test -f kustomize/configmap.yaml
$ helm upgrade -n test lookup-test .
$ kubectl get configmaps -n test lookup-test -o yaml
$ kubectl get configmaps -n test lookup-test -o yaml
apiVersion: v1
data:
  lookupValue: lookup-test-123456
  myvalue: Hello World
kind: ConfigMap
metadata:
  annotations:
    meta.helm.sh/release-name: lookup-test
    meta.helm.sh/release-namespace: test
  creationTimestamp: "2024-04-06T05:47:25Z"
  labels:
    app.kubernetes.io/managed-by: Helm
  name: lookup-test
  namespace: test
  resourceVersion: "7155"
  uid: 4eababa8-234e-4f62-b0b0-dc8de296ddcc
```