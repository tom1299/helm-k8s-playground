Feature: Certificates

  Background:
    Given I have a connection to the cluster
    And The namespace "httpd-autoscaling" exists

  Scenario: Test
    Given The deployment "httpd" is installed having 1 replica running
    And I deploy the config map "load-test-config" with the content of the file "test-data/load-test-1.js" as the data item "load-test.js"
    And I create the pod "load-test" with the pod spec from the file "test-data/load-test-pod.yaml"
    Then The pod "load-test" should be running within 60 seconds
    And The deployment "httpd" should have 2 replicas running within 60 seconds
    Given I delete the pod "load-test"
    Then The deployment "httpd" should have 1 replicas running within 60 seconds