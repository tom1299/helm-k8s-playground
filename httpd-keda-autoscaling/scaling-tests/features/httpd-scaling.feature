Feature: Certificates

  Background:
    Given I have a connection to the cluster
    And The namespace "httpd-autoscaling" exists

#  Scenario: Simple scale up and down
#    Given The deployment "httpd" is installed having 1 replica running
#    And I deploy the config map "load-test-config" with the content of the file "test-data/load-test-1.js" as the data item "load-test.js"
#    And I create the pod "load-test" with the pod spec from the file "test-data/load-test-pod.yaml"
#    Then The pod "load-test" should be running within 60 seconds
#    And The deployment "httpd" should have 2 replicas running within 70 seconds
#    Then The deployment "httpd" should have 1 replicas running within 60 seconds

  Scenario: Scale up and down with ramp up and down
    Given The deployment "httpd" is installed having 1 replica running
    And I deploy the config map "load-test-config" with the content of the file "test-data/load-test-2.js" as the data item "load-test.js"
    And I create the pod "load-test" with the pod spec from the file "test-data/load-test-pod.yaml"
    Then The pod "load-test" should be running within 60 seconds
    And The deployment "httpd" should have 2 replicas running within 120 seconds
    And The deployment "httpd" should have 3 replicas running within 90 seconds
    And The deployment "httpd" should have 2 replicas running within 180 seconds
    And The deployment "httpd" should have 2 replicas running within 60 seconds