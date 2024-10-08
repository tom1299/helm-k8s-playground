# Troubleshooting ServiceMonitor not working

## Verify whether httpd's metrics are being scraped by prometheus
* Check the logs of the prometheus Pod to see if the ServiceMonitor is being picked up / scraped
* Using curl and wget to verify that the metrics are being exposed by the Pod and the service
* Check the log files of the httpd Pod to see if the metrics are being scraped by the curl/wget requests
Both tasks are first done in the httpd Pod itself using `kubectl exec` and then in the prometheus Pod using `kubectl debug`

## Some first googleing
Well, I have to admit that my first attempts to google the issue were a little bit superficial. The only thing I found was the
Prometheus Operator per default should only pick up ServieMonitors from its own namespace. So I put the ServiceMonitor in the
namespace `monitoring` where the Prometheus Operator is running. But without success.

## Trying out the sample app
Trying out a simple from the Prometheus Operator's documentation seemed to be a good idea, since one would expect that this should work.

## Adding annotations to the namespace

## Compare non working ServiceMonitor to working ServiceMonitor
Since some ServiceMonitors were indeed working and others were not, I decided to compare the ServiceMonitor of the api server
with my non working ServiceMonitor for the httpd service.
Comapring the two service monitors revealed that the service monitor for the httpd service monitor's specification seemed alright.

_Spoiler alert_: The issue was with the label `release: prometheus-operator` which was missing in the non working ServiceMonitor which I did not notice at first:
```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: prometheus-operator-kube-p-operator
  namespace: monitoring
  labels:
    release: prometheus-operator
```

## Googleing the issue THOUROUGHLY (stupid me for not doing this first ;-)

## Assesment of the troubleshooting steps
Actually the steps of trying to first verify that the metrics are being exposed and accessible followed by a comparison between working and non working ServiceMonitors was a good approach. As I think it always is a good idea to first verify that the basic are working.
Me not spotting the missing label in the ServiceMonitor was not really a mistake since the service generated by deploying the Prometheus Operator had nearly a dozen labels and I did not know which one to look for.
Searching with a more specific search term and taking more time to got through the results would have spared me some time, since the GitHub issue that utlimately helped me was already in the list of search results for the first search.