## Commands
```shell
$ kubectl apply -k ./lookup-test/kustomize/
$ helm upgrade -n test lookup-test .
$ helm upgrade -n test lookup-test ./lookup-test/
$ $ kubectl get configmaps -n test lookup-test -o yaml
apiVersion: v1
data:
  spring-jpa-configmap-name: spring-jpa-config-df9d9mfhfb
  spring-jpa-secret-name: spring-jpa-secret-5259dtkthk
kind: ConfigMap
metadata:
  annotations:
    meta.helm.sh/release-name: lookup-test
    meta.helm.sh/release-namespace: test
  creationTimestamp: "2024-04-07T05:50:25Z"
  labels:
    app.kubernetes.io/managed-by: Helm
  name: lookup-test
  namespace: test
  resourceVersion: "8814"
  uid: cc707148-5c7c-40df-baf4-5afe66276fbc
```