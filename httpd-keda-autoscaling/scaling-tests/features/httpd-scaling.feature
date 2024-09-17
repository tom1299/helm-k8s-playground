@httpd-scaling
Feature: Scaling the Apache httpd with KEDA

  Background:
    Given I have a connection to the cluster
    And I can connect to the prometheus service
    And The namespace "httpd-autoscaling" exists
    And The value for the prometheus query "sum(rate(apache_accesses_total[1m]))" gets smaller than 1.0 within 120 seconds
    And The deployment "httpd" is installed
    And The deployment "httpd" has 1 replicas running within 120 seconds

  @basic
  Scenario: Simple scale up and down
    And I deploy the config map "load-test-config" with the content of the file "test-data/load-test-1.js" as the data item "load-test.js"
    And I create the pod "load-test" with the pod spec from the file "test-data/load-test-pod.yaml"
    Then The pod "load-test" should be running within 60 seconds
    And The deployment "httpd" should have 2 replicas running within 90 seconds
    Then The deployment "httpd" should have 1 replicas running within 90 seconds

  @advanced
  Scenario: Scale up and down with ramp up and down
    And I deploy the config map "load-test-config" with the content of the file "test-data/load-test-2.js" as the data item "load-test.js"
    And I create the pod "load-test" with the pod spec from the file "test-data/load-test-pod.yaml"
    Then The pod "load-test" should be running within 60 seconds
    And The deployment "httpd" should have 2 replicas running within 120 seconds
    And The deployment "httpd" should have 3 replicas running within 90 seconds
    And The deployment "httpd" should have 2 replicas running within 180 seconds
    And The deployment "httpd" should have 2 replicas running within 60 seconds