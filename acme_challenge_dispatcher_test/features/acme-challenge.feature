@acme-challenge
Feature: Acme challenge processing

  Scenario: Single acme challenge running
    Given I have a connection to the cluster
    And the namespace "acme-challenge-test" exists
    And the service-account "acme-challenge-dispatcher" exists
    And I deploy the acme challenge dispatcher pod with the following parameters:
    | name | image |
    | acme-challenge-dispatcher-1 | localhost/acme-challenge-dispatcher:v10 |
    And I deploy an acme solver pod with the following parameters:
    | name | port | token | key | domain |
    | acme-solver-1 | 8080 | abc | def | acme-challenge-dispatcher-1.com |
    And I forward the port 8080 of the pod "acme-challenge-dispatcher-1" to port 8080
    # TODO: Replace this step whith something like: And I wait until I can access port 8080
    And I wait for 10 seconds
    When I do a GET request to 8080 with the following parameters:
    | url | port | host |
    | /.well-known/acme-challenge/abc | 8080 | acme-challenge-dispatcher-1.com |
    Then the response should be "def"
    And I stop forwarding the port 8080 of the pod "acme-challenge-dispatcher-1"
    # TODO: Add delete steps. Use force and grace periond 0 to speed up the deletion

# Scenario: 10 acme challenges running
# Scenario: No acme challenge running
# Scenario: 1 acme challenge running, pod deleted => Cache should be updated