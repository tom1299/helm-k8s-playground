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