# Process trivy scan results in GitLab
## Basic idea
* Scan a docker image with the trivy-operator
* Use the gitlab format for the report
* Upload the report to the gitlab package registry
* Upload triggers a pipeline to process the report, e.g adds the file to the vulnerability dashboard:
```yaml
  artifacts:
    when:                          always
    reports:
      container_scanning:          gl-container-scanning-report.json
```


## Upload a file to a package registry
The token used is a deploy token for the project:
```shell
curl --request PUT \
  --user "gitlab+deploy-token-xxx:gldt-xxx" \
  --header "Content-Type: multipart/form-data" \
  --form "file=@Dockerfile" \
  "https://gitlab.com/api/v4/projects/325747/packages/generic/test-report-1/1.0.0/Dockerfile"
```

## Using the gitlab template for the trivy-operator
See [here](https://trivy.dev/v0.29.2/docs/integrations/gitlab-ci/)
```shell
--format template --template "@/contrib/gitlab.tpl
```
The tpl can be found [here](https://github.com/aquasecurity/trivy/blob/main/contrib/gitlab.tpl)

## Converting
Use `trivy convert` to convert the report in conjunction with `--template "@/contrib/gitlab.tpl`

```shell
trivy convert --debug --format template --template "@./contrib/gitlab.tpl" --output trivy-operator-sample-report-gitlab.json  trivy-operator-sample-report.json
```
```
trivy convert --debug --format table --output trivy-operator-sample-report-gitlab.txt  trivy-operator-sample-report.json
```