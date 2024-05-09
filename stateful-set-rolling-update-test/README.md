Used to reproduce the issue:

https://github.com/kubernetes/kubernetes/issues/67250

based on documentation:

https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/#forced-rollback

Can be solved by setting the podManagementPolicy to Parallel:

https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/#parallel-pod-management

Drawback: It might be that no pods are available after a faulty update.
