```
kubectl apply -f httpd-config.yaml
kubectl apply -f httpd-deployment.yaml
kubectl apply -f httpd-service.yaml
kubectl apply -f httpd-metrics-exporter-service.yaml  
```

```sh
kubectl port-forward service/httpd 8888:8888 -n httpd-autoscaling
kubectl port-forward service/httpd-metrics-exporter 9117:9117 -n httpd-autoscaling

curl localhost:8888
curl localhost:9117/metrics
```

https://github.com/Lusitaniae/apache_exporter
https://keda.sh/docs/2.15/scalers/metrics-api/

Command for debugging the keda-operator:
```
kubectl debug -n keda keda-operator-<pod-id> -ti --image=nicolaka/netshoot --target=keda-operator --custom=partial_container.yaml -- bash
```

**Next**
* Create scaled object with url: `httpd-metrics-exporter.httpd-autoscaling:9117/metrics`
* Use metric `apache_sent_kilobytes_total` just for the sake ot testing

**Conclusion**
* As expected this does not work.

**Next**
* Try prometheus

**Prometheus operator installation**
```
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm install prometheus-operator prometheus-community/kube-prometheus-stack -n monitoring -f prometheus-installation/values.yaml
```
Use port-forwarding to access the prometheus dashboard:
```sh
kubectl port-forward svc/prometheus-operator-kube-p-prometheus -n monitoring 9090:9090
```

```sh
http://localhost:9090/service-discovery?search=
```

**Solution for the issue**
https://github.com/prometheus-operator/kube-prometheus/issues/1392#issuecomment-1411719953

**Next**
* Create a service monitor for the httpd service in tht httpd-autoscaling namespace
* Create the prometheus query for scaling
* Create the scaled object
* Test the scaling

Also make this change:
```
https://github.com/prometheus-operator/prometheus-operator/blob/main/Documentation/user-guides/getting-started.md
By default, Prometheus will only pick up ServiceMonitors from the current namespace. To select ServiceMonitors from other namespaces, you can update the spec.serviceMonitorNamespaceSelector field of the Prometheus resource.
```

rate(apache_accesses_total[30s])
Start scaling at 20 requests per second and scale up to 50 requests per second

kubectl port-forward svc/httpd -n httpd-autoscaling 8888:8888


https://keda.sh/docs/2.15/reference/scaledobject-spec/

Next:
* Containerize the scaling test