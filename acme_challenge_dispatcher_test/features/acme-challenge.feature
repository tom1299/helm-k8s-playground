@httpd-scaling
Feature: Scaling the Apache httpd with KEDA

  Scenario: Simple scale up and down
    Given I have a connection to the cluster
    And the namespace "acme-challenge-test" exists
    And I deploy an acme solver pod with the following parameters:
    | name | port | token | key |
    | acme-solver-1 | 8080 | abc | def |
    And I forward the port 8080 of the pod "acme-solver-1" to port 8080
