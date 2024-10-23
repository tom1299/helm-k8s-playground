@acme-challenge
Feature: Acme challenge processing

  Background:
    Given I have a connection to the cluster
    And the namespace "acme-challenge-test" exists
    And the service-account "acme-challenge-dispatcher" exists
    And I deploy the acme challenge dispatcher pod with the following parameters:
    | name | image |
    | acme-challenge-dispatcher-1 | localhost/acme-challenge-dispatcher:v11 |

  Scenario: Single acme challenge running
    Given I deploy an acme solver pod with the following parameters:
    | name | port | token | key | domain |
    | acme-solver-1 | 8080 | abc | def | acme-challenge-dispatcher-1.com |
    And I forward the port 8080 of the pod "acme-challenge-dispatcher-1" to port 8080
    # TODO: Replace this step whith something like: And I wait until I can access port 8080
    And I wait for 2 seconds
    When I do 1 GET request to 8080 with the following parameters:
    | url | port | host |
    | /.well-known/acme-challenge/abc | 8080 | acme-challenge-dispatcher-1.com |
    Then response number 1 should have return code 200 and content "def"
    And I stop forwarding the port 8080 of the pod "acme-challenge-dispatcher-1"
    And I delete the pods:
    | name |
    | acme-challenge-dispatcher-1 |
    | acme-solver-1 |

  Scenario: Two acme challenges running
    Given I deploy an acme solver pod with the following parameters:
    | name | port | token | key | domain |
    | acme-solver-1 | 8080 | abc | def | acme-challenge-dispatcher-1.com |
    And I deploy an acme solver pod with the following parameters:
    | name | port | token | key | domain |
    | acme-solver-2 | 8080 | ghi | jkl | acme-challenge-dispatcher-2.com |
    And I forward the port 8080 of the pod "acme-challenge-dispatcher-1" to port 8080
    And I wait for 2 seconds
    When I do 1 GET request to 8080 with the following parameters:
    | url | port | host |
    | /.well-known/acme-challenge/abc | 8080 | acme-challenge-dispatcher-1.com |
    Then response number 1 should have return code 200 and content "def"
    When I do 1 GET request to 8080 with the following parameters:
    | url | port | host |
    | /.well-known/acme-challenge/ghi | 8080 | acme-challenge-dispatcher-2.com |
    Then response number 1 should have return code 200 and content "jkl"
    And I stop forwarding the port 8080 of the pod "acme-challenge-dispatcher-1"
    And I delete the pods:
    | name |
    | acme-challenge-dispatcher-1 |
    | acme-solver-1 |
    | acme-solver-2 |

# Scenario: 10 acme challenges running
# Scenario: No acme challenge running
# Scenario: 1 acme challenge running, pod deleted => Cache should be updated