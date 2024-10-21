@httpd-scaling
Feature: Scaling the Apache httpd with KEDA

  Scenario: Simple scale up and down
    Given I have a connection to the cluster
    And the namespace "acme-challenge-test" exists
