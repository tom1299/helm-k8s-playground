Used to reproduce the issue:

https://github.com/kubernetes/kubernetes/issues/67250

based on documentation:

https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/#forced-rollback

Can be solved by setting the podManagementPolicy to Parallel:

https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/#parallel-pod-management

Drawback: It might be that no pods are available after a faulty update.

### Test
* Rolling update strategy with podManagementPolicy set to OrderedReady
* Expected: Pods are updated one by one, waiting for the previous pod to be ready

### Test 2:
* Set image to a non-existing image
* Expected: The pod last created is updated first but fails to start, the previous pod is not updated and the rollout is stopped leaving the last pod in a failed state

```
NAME    READY   STATUS             RESTARTS   AGE
web-2   1/1     Running            0          2m13s
web-1   1/1     Running            0          2m1s
web-0   1/1     Running            0          109s
web-3   0/1     ImagePullBackOff   0          84s
```

### Test 3:
* Set image back to the correct image
* Expected: The statefulset gets updated but not the pods because of the above-mentioned issue

### Test 4:
* Delete the pod being stuck
* Expected: The pod gets recreated with the correct image and the other pods are updated as well

### Test 5:
* Set podManagementPolicy to Parallel
* Expected: When doing Tests 2 to 4, it should not be necessary to delete the pod being stuck
* Pods are created in parallel
* After setting the wrong image the last pod is stuck but the other are still running
* Changing the image back to the correct one, the last pod is updated and running, the other pods are updated as well

### Conclusion
* The issue is caused by the podManagementPolicy set to OrderedReady
* The issue can be solved by setting the podManagementPolicy to Parallel
* The issue can be solved by deleting the pod being stuck


## Probes:
The kubelet uses startup probes to know when a container application has started. If such a probe is configured, liveness and readiness probes do not start until it succeeds, making sure those probes don't interfere with the application startup.
This means that for an initial delay of 5 seconds, the liveness and readiness probes will only start after 5 seconds.
So if the startup probe and the readiness probe are both configured with an initial delay of 5 seconds, and both immediately return true, the pod will be ready after 10 seconds.

## Notes
This document was created with the assistance of the GitHub Copilot.
The Copilot failed to provide the correct information in some cases, so the information was corrected manually.
It seems like the Copilot is not able to provide the correct information for cases where the information is not directly available in the code and which are not common knowledge.
It seems to draw a lot of information from the context because after I manually corrected the information, the Copilot was able to provide the correct information for the next cases.