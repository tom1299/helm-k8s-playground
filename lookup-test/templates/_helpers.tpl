{{/*
Expand the name of the chart.
*/}}
{{- define "lookup-test.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "lookup-test.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "lookup-test.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "lookup-test.labels" -}}
helm.sh/chart: {{ include "lookup-test.chart" . }}
{{ include "lookup-test.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "lookup-test.selectorLabels" -}}
app.kubernetes.io/name: {{ include "lookup-test.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "lookup-test.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "lookup-test.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/* Get the exact name of a configmap starting with a specific prefix */}}
{{- define  "lookup-test.getConfigMapName" -}}
{{- $prefix := printf "%s-" .prefix -}}
{{- $namespace := .namespace -}}
{{- $configmapName := "" -}}
{{ range $index, $configmap := (lookup "v1" "ConfigMap" $namespace "").items }}
    # Get the name of the configmap
    {{- if hasPrefix $configmap.metadata.name $prefix }}
        {{- $configmapName = $configmap.metadata.name }}
        {{- break -}}
    {{- end }}
{{ end }}
{{- $configmapName -}}
{{- end }}


