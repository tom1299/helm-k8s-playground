```sh
kubectl port-forward service/httpd 8888:8888 -n httpd-autoscaling
kubectl port-forward service/httpd-metrics-exporter 9117:9117 -n httpd-autoscaling

curl localhost:8888
curl localhost:9117/metrics
```

https://github.com/Lusitaniae/apache_exporter
https://keda.sh/docs/2.15/scalers/metrics-api/