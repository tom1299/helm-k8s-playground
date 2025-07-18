# Useful commands for node troubleshooting
Get the list of services managed by systemd without systemctl:
```bash
root@kind-worker2:/# ls -la /etc/systemd/system
total 36
drwxr-xr-x. 1 root root  608 May 21 00:56 .
drwxr-xr-x. 1 root root   26 Jul 17 12:37 ..
-rw-r--r--. 1 root root 1014 Oct 17  2024 10-kubeadm.conf
-rw-r--r--. 1 root root  791 Oct 17  2024 11-kind.conf
-rw-r--r--. 1 root root  299 Oct 17  2024 containerd-fuse-overlayfs.service
-rw-r--r--. 1 root root  754 Oct 17  2024 containerd.service
drwxr-xr-x. 1 root root    0 May 21 00:56 getty.target.wants
lrwxrwxrwx. 1 root root   38 May 21 00:55 iscsi.service -> /lib/systemd/system/open-iscsi.service
-rw-r--r--. 1 root root  878 Oct 17  2024 kubelet.service
drw-r--r--. 1 root root   54 May 21 00:55 kubelet.service.d
-rw-r--r--. 1 root root  129 Oct 17  2024 kubelet.slice
drwxr-xr-x. 1 root root  114 May 21 00:56 multi-user.target.wants
drwxr-xr-x. 1 root root    0 May 21 00:56 remote-fs.target.wants
drwxr-xr-x. 1 root root    0 May 21 00:56 sockets.target.wants
drwxr-xr-x. 1 root root    0 May 21 00:56 sysinit.target.wants
lrwxrwxrwx. 1 root root    9 May 21 00:56 systemd-binfmt.service -> /dev/null
drwxr-xr-x. 1 root root    0 May 21 00:56 timers.target.wants
-rw-r--r--. 1 root root  205 Oct 17  2024 undo-mount-hacks.service
```

## kube-proxy
In kind kube-proxy is running as a critcl container. To check the status of kube-proxy:
- Exec into the node
- Exec into the container
- Look at the configuration: `/var/lib/kube-proxy/config.conf`
- Also contains the mode: `mode: iptables`
- iptables commands can be run inside the container
- Logs can be viewed by `crictl logs 6513ba4d0df1b`