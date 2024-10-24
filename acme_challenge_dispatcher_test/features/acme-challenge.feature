@acme-challenge
Feature: Acme challenge processing

  Background:
    Given I have a connection to the cluster
    And the namespace "acme-challenge-test" exists
    And the service-account "acme-challenge-dispatcher" exists
    And I deploy the acme challenge dispatcher pod with the following parameters:
    | name | image |
    | acme-challenge-dispatcher-1 | localhost/acme-challenge-dispatcher:v18 |

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
    When I do 1 GET request to 8080 with the following parameters:
    | url | port | host |
    | /.well-known/acme-challenge/abc | 8080 | example.com |
    Then response number 1 should have return code 404 and content "404 Not Found"
    When I do 1 GET request to 8080 with the following parameters:
    | url | port | host |
    | /.well-known/acme-challenge/xxxxxxxxxx | 8080 | acme-challenge-dispatcher-1.com |
    Then response number 1 should have return code 404 and content "404 Not Found"
    And I stop forwarding the port 8080 of the pod "acme-challenge-dispatcher-1"
    And I delete the pods:
    | name |
    | acme-challenge-dispatcher-1 |
    | acme-solver-1 |

  Scenario: Two acme challenges running
    Given I deploy an acme solver pod with the following parameters:
    | name | port | token | key | domain |
    | acme-solver-1 | 8080 | abc | def | acme-challenge-dispatcher-1.com |
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

  Scenario: 6 acme challenges running
    Given I deploy an acme solver pod with the following parameters:
    | name | port | token | key | domain |
    | acme-solver-1 | 8080 | abc | def | acme-challenge-dispatcher-1.com |
    | acme-solver-2 | 8080 | ghi | jkl | acme-challenge-dispatcher-2.com |
    | acme-solver-3 | 8080 | mno | pqr | acme-challenge-dispatcher-3.com |
    | acme-solver-4 | 8080 | stu | vwx | acme-challenge-dispatcher-4.com |
    | acme-solver-5 | 8080 | yza | bcd | acme-challenge-dispatcher-5.com |
    | acme-solver-6 | 8080 | efg | hij | acme-challenge-dispatcher-6.com |
    And I forward the port 8080 of the pod "acme-challenge-dispatcher-1" to port 8080
    And I wait for 2 seconds
    When I do 10 GET request to 8080 with the following parameters:
    | url | port | host |
    | /.well-known/acme-challenge/abc | 8080 | acme-challenge-dispatcher-1.com |
    Then all responses should have return code 200 and content "def"
    When I do 2 GET request to 8080 with the following parameters:
    | url | port | host |
    | /.well-known/acme-challenge/yza | 8080 | acme-challenge-dispatcher-5.com |
    Then all responses should have return code 200 and content "bcd"
    And I stop forwarding the port 8080 of the pod "acme-challenge-dispatcher-1"
    And I delete the pods:
    | name |
    | acme-challenge-dispatcher-1 |
    | acme-solver-1 |
    | acme-solver-2 |
    | acme-solver-3 |
    | acme-solver-4 |
    | acme-solver-5 |
    | acme-solver-6 |

Scenario: No acme challenges running
    Given I forward the port 8080 of the pod "acme-challenge-dispatcher-1" to port 8080
    And I wait for 2 seconds
    When I do 1 GET request to 8080 with the following parameters:
    | url | port | host |
    | /.well-known/acme-challenge/abc | 8080 | acme-challenge-dispatcher-1.com |
    Then response number 1 should have return code 404 and content "404 Not Found"
    And I stop forwarding the port 8080 of the pod "acme-challenge-dispatcher-1"
    And I delete the pods:
    | name |
    | acme-challenge-dispatcher-1 |

Scenario: Acme solver pod is deleted while acme challenge is running
    Given I deploy an acme solver pod with the following parameters:
    | name | port | token | key | domain |
    | acme-solver-1 | 8080 | abc | def | acme-challenge-dispatcher-1.com |
    And I forward the port 8080 of the pod "acme-challenge-dispatcher-1" to port 8080
    And I wait for 2 seconds
    When I do 1 GET request to 8080 with the following parameters:
    | url | port | host |
    | /.well-known/acme-challenge/abc | 8080 | acme-challenge-dispatcher-1.com |
    Then response number 1 should have return code 200 and content "def"
    When I delete the pods:
    | name |
    | acme-solver-1 |
    And I do 1 GET request to 8080 with the following parameters:
    | url | port | host |
    | /.well-known/acme-challenge/abc | 8080 | acme-challenge-dispatcher-1.com |
    Then response number 1 should have return code 404 and content "404 Not Found"
    When I deploy an acme solver pod with the following parameters:
    | name | port | token | key | domain |
    | acme-solver-1 | 8080 | abc | def | acme-challenge-dispatcher-1.com |
    And I do 1 GET request to 8080 with the following parameters:
    | url | port | host |
    | /.well-known/acme-challenge/abc | 8080 | acme-challenge-dispatcher-1.com |
    Then response number 1 should have return code 200 and content "def"
    And I stop forwarding the port 8080 of the pod "acme-challenge-dispatcher-1"
    And I delete the pods:
    | name |
    | acme-challenge-dispatcher-1 |
    | acme-solver-1 |

Scenario: Diverse error cases
    Given I deploy an acme solver pod with the following parameters:
    | name | port | token | key | domain |
    | acme-solver-1 | 8080 | abc | def | acme-challenge-dispatcher-1.com |
    And I forward the port 8080 of the pod "acme-challenge-dispatcher-1" to port 8080
    And I wait for 2 seconds
    When I do 1 GET request to 8080 with the following parameters:
    | url | port | host |
    | /.well-known/acme-challenge/abc | 8080 | |
    Then response number 1 should have return code 400 and content "400 Bad Request"
    When I do 1 GET request to 8080 with the following parameters:
    | url | port | host |
    | /invalid/path | 8080 | acme-challenge-dispatcher-1.com |
    Then response number 1 should have return code 404 and content "404 Not Found"
    When I do 1 GET request to 8080 with the following parameters:
    | url | port | host |
    | /.well-known/acme-challenge/ | 8080 | acme-challenge-dispatcher-1.com |
    Then response number 1 should have return code 400 and content "400 Bad Request"
    And I stop forwarding the port 8080 of the pod "acme-challenge-dispatcher-1"
    And I delete the pods:
    | name |
    | acme-challenge-dispatcher-1 |
    | acme-solver-1 |
