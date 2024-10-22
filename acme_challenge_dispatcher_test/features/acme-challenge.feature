@acme-challenge
Feature: Acme challenge processing

  Scenario: Simple scale up and down
    Given I have a connection to the cluster
    And the namespace "acme-challenge-test" exists
    And the service-account "acme-challenge-dispatcher" exists
    And I deploy the acme challenge dispatcher pod with the following parameters:
    | name | image |
    | acme-challenge-dispatcher-1 | localhost/acme-challenge-dispatcher:v7 |
    And I deploy an acme solver pod with the following parameters:
    | name | port | token | key | domain |
    | acme-solver-1 | 8080 | abc | def | acme-challenge-dispatcher-1.com |
    And I forward the port 8080 of the pod "acme-challenge-dispatcher-1" to port 8080
    And I wait for 10 seconds
    When I do a GET request to 8080 with the following parameters:
    | url | port | host |
    | /.well-known/acme-challenge/abc | 8080 | acme-challenge-dispatcher-1.com |
    Then the response should be "def"
    And I stop forwarding the port 8080 of the pod "acme-challenge-dispatcher-1"
