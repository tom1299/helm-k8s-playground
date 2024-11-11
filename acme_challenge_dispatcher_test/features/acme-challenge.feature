@acme-challenge
Feature: Acme challenge processing

  Background:
    Given I have a connection to the cluster
    And prometheus is running
    And the namespace "acme-challenge-test" exists
    And the service-account "acme-challenge-dispatcher" exists
    And I deploy the acme challenge dispatcher pod monitor
    And I deploy the acme challenge dispatcher pod with the following parameters
    | name | image |
    | acme-challenge-dispatcher-1 | localhost/acme-challenge-dispatcher:1.0.0 |

  Scenario: Single acme challenge running
    Given I deploy an acme solver pod with the following parameters
    | name | port | token | key | domain |
    | acme-solver-1 | 8089 | abc | def | acme-challenge-dispatcher-1.com |
    When I do 1 GET request to 8089 with the following parameters
    | url | port | host |
    | /.well-known/acme-challenge/abc | 8089 | acme-challenge-dispatcher-1.com |
    Then response number 1 should have return code 200 and content "def"
    When I do 1 GET request to 8089 with the following parameters
    | url | port | host |
    | /.well-known/acme-challenge/abc | 8089 | example.com |
    Then response number 1 should have return code 404 and content "404 Not Found"
    When I do 1 GET request to 8089 with the following parameters
    | url | port | host |
    | /.well-known/acme-challenge/xxxxxxxxxx | 8089 | acme-challenge-dispatcher-1.com |
    Then response number 1 should have return code 404 and content "404 Not Found"
    And I delete the pods
    | name |
    | acme-challenge-dispatcher-1 |
    | acme-solver-1 |

  Scenario: Two acme challenges running
    Given I deploy an acme solver pod with the following parameters
    | name | port | token | key | domain |
    | acme-solver-1 | 8089 | abc | def | acme-challenge-dispatcher-1.com |
    | acme-solver-2 | 8089 | ghi | jkl | acme-challenge-dispatcher-2.com |
    When I do 1 GET request to 8089 with the following parameters
    | url | port | host |
    | /.well-known/acme-challenge/abc | 8089 | acme-challenge-dispatcher-1.com |
    Then response number 1 should have return code 200 and content "def"
    When I do 1 GET request to 8089 with the following parameters
    | url | port | host |
    | /.well-known/acme-challenge/ghi | 8089 | acme-challenge-dispatcher-2.com |
    Then response number 1 should have return code 200 and content "jkl"
    And I delete the pods
    | name |
    | acme-challenge-dispatcher-1 |
    | acme-solver-1 |
    | acme-solver-2 |

  Scenario: 6 acme challenges running
    Given I deploy an acme solver pod with the following parameters
    | name | port | token | key | domain |
    | acme-solver-1 | 8089 | abc | def | acme-challenge-dispatcher-1.com |
    | acme-solver-2 | 8089 | ghi | jkl | acme-challenge-dispatcher-2.com |
    | acme-solver-3 | 8089 | mno | pqr | acme-challenge-dispatcher-3.com |
    | acme-solver-4 | 8089 | stu | vwx | acme-challenge-dispatcher-4.com |
    | acme-solver-5 | 8089 | yza | bcd | acme-challenge-dispatcher-5.com |
    | acme-solver-6 | 8089 | efg | hij | acme-challenge-dispatcher-6.com |
    When I do 10 GET request to 8089 with the following parameters
    | url | port | host |
    | /.well-known/acme-challenge/abc | 8089 | acme-challenge-dispatcher-1.com |
    Then all responses should have return code 200 and content "def"
    When I do 2 GET request to 8089 with the following parameters
    | url | port | host |
    | /.well-known/acme-challenge/yza | 8089 | acme-challenge-dispatcher-5.com |
    Then all responses should have return code 200 and content "bcd"
    And I delete the pods
    | name |
    | acme-challenge-dispatcher-1 |
    | acme-solver-1 |
    | acme-solver-2 |
    | acme-solver-3 |
    | acme-solver-4 |
    | acme-solver-5 |
    | acme-solver-6 |

Scenario: No acme challenges running
    When I do 1 GET request to 8089 with the following parameters
    | url | port | host |
    | /.well-known/acme-challenge/abc | 8089 | acme-challenge-dispatcher-1.com |
    Then response number 1 should have return code 404 and content "404 Not Found"
    And I delete the pods
    | name |
    | acme-challenge-dispatcher-1 |

Scenario: Acme solver pod is deleted while acme challenge is running
    Given I deploy an acme solver pod with the following parameters
    | name | port | token | key | domain |
    | acme-solver-1 | 8089 | abc | def | acme-challenge-dispatcher-1.com |
    When I do 1 GET request to 8089 with the following parameters
    | url | port | host |
    | /.well-known/acme-challenge/abc | 8089 | acme-challenge-dispatcher-1.com |
    Then response number 1 should have return code 200 and content "def"
    When I delete the pods
    | name |
    | acme-solver-1 |
    And I do 1 GET request to 8089 with the following parameters
    | url | port | host |
    | /.well-known/acme-challenge/abc | 8089 | acme-challenge-dispatcher-1.com |
    Then response number 1 should have return code 404 and content "404 Not Found"
    When I deploy an acme solver pod with the following parameters
    | name | port | token | key | domain |
    | acme-solver-1 | 8089 | abc | def | acme-challenge-dispatcher-1.com |
    And I do 1 GET request to 8089 with the following parameters
    | url | port | host |
    | /.well-known/acme-challenge/abc | 8089 | acme-challenge-dispatcher-1.com |
    Then response number 1 should have return code 200 and content "def"
    And I delete the pods
    | name |
    | acme-challenge-dispatcher-1 |
    | acme-solver-1 |

Scenario: Diverse error cases
    Given I deploy an acme solver pod with the following parameters
    | name | port | token | key | domain |
    | acme-solver-1 | 8089 | abc | def | acme-challenge-dispatcher-1.com |
    When I do 1 GET request to 8089 with the following parameters
    | url | port | host |
    | /.well-known/acme-challenge/abc | 8089 | |
    Then response number 1 should have return code 400 and content "400 Bad Request"
    When I do 1 GET request to 8089 with the following parameters
    | url | port | host |
    | /invalid/path | 8089 | acme-challenge-dispatcher-1.com |
    Then response number 1 should have return code 404 and content "404 Not Found"
    When I do 1 GET request to 8089 with the following parameters
    | url | port | host |
    | /.well-known/acme-challenge/ | 8089 | acme-challenge-dispatcher-1.com |
    Then response number 1 should have return code 400 and content "400 Bad Request"
    And I delete the pods
    | name |
    | acme-challenge-dispatcher-1 |
    | acme-solver-1 |

Scenario: Test health and metrics endpoint
    When I do 1 GET request to 8081 with the following parameters
    | url | port | host |
    | /healthz | 8081 | acme-challenge-dispatcher-1.com |
    Then response number 1 should have return code 200 and no content
    When I do 1 GET request to 8081 with the following parameters
    | url | port | host |
    | /invalid-path | 8081 | acme-challenge-dispatcher-1.com |
    Then response number 1 should have return code 404 and no content
    When I do 1 GET request to 8081 with the following parameters
    | url | port | host |
    | /metrics | 8081 | acme-challenge-dispatcher-1.com |
    Then response number 1 should have return code 200 and content
    """
    # HELP acme_service_dispatcher_requests_total Total number of scrapes by HTTP status code.
    # TYPE acme_service_dispatcher_requests_total counter
    acme_service_dispatcher_requests_total{code="200"} 0
    acme_service_dispatcher_requests_total{code="400"} 0
    acme_service_dispatcher_requests_total{code="404"} 0
    acme_service_dispatcher_requests_total{code="500"} 0
    """
    And I delete the pods
    | name |
    | acme-challenge-dispatcher-1 |
    | acme-solver-1 |