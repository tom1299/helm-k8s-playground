@httpd-scaling
Feature: Scaling Jobs with KEDA

  Background:
    Given I have a connection to the cluster
    And The namespace "job-autoscaling" exists
    And The deployment "mysql" is installed
    And The database "jobs" exists
    And There are 5 records in the "jobs" table in the "jobs" database
    And I delete all pods except for mysql

  @basic
  Scenario: Spawn three jobs
    Given I run the following sql script in the database "jobs"
      """
      USE jobs;
      INSERT INTO jobs (name) VALUES ('test-job-1'),('test-job-2'),('test-job-3');
      """
    Then There should be 3 pods with status "Succeeded" within 120 seconds