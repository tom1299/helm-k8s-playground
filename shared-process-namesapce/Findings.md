Main problem:
* GitHub Copilot created a snippet that is not a valid:
```yaml
    volumeMounts:
    - name: html-content
      mountPath: /usr/local/apache2/htdocs/
      subPath: index.html
```
You can not mount a single file to a directory. Troubleshooting this problem took longer
than actually writing the snippet myself => Big problem because this questions to whole usefulness of GitHub Copilot.