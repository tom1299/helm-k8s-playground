{{- define "api-server-network-policy.egress2apiserver" -}}
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: {{ . }}-apiserver-egress-network-policy
  annotations:
    createdAt: {{ now | date "2006-01-02 15:04:05" }} by helm function egress2apiserver
spec:
  podSelector:
    matchLabels:
      kubernetes.io/metadata.name: {{ . }}
  policyTypes:
  - Egress
  egress:
  {{- $endpoints := (lookup "v1" "Endpoints" "default" "kubernetes") }}
  {{- if $endpoints }}
  {{- range $endpoints.subsets }}
  - to:
      {{- range .addresses }}
      - ipBlock:
          cidr: {{ .ip }}/32
      {{- end }}
    ports:
      {{- range .ports }}
      - protocol: {{ .protocol }}
        port: {{ .port }}
      {{- end }}
  {{- end }}
  {{- else }}
  - to:
    - ipBlock:
        cidr: 0.0.0.0/0
    ports:
    - protocol: TCP
      port: 6443
  {{- end }}
{{- end }}