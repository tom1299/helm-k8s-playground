import json
import logging
import os
import requests
from time import sleep, time

from kubernetes import utils

import yaml

from acme_challenge_dispatcher.k8s_functions import get_core_v1_client, get_api_client

from behave import step
from kubernetes import client

logger = logging.getLogger(__name__)

@step('I have a connection to the cluster')
def step_impl(context):
    api_client = get_api_client(logger)
    context.api_client = api_client
    v1_client = get_core_v1_client(logger)
    v1_client.list_namespace()
    context.v1_client = v1_client

@step('The namespace "{namespace}" exists')
def check_namespace_exists(context, namespace):
    v1 = context.v1_client
    namespaces = v1.list_namespace()
    namespace_names = [ns.metadata.name for ns in namespaces.items]

    if namespace not in namespace_names:
        v1.create_namespace(client.V1Namespace(metadata=client.V1ObjectMeta(name=namespace)))

    context.namespace = namespace


@step('I deploy an acme solver pod with the following parameters')
def deploy_acme_solver_pod(context):
    script_dir = os.path.dirname(__file__)
    full_file_path = os.path.join(script_dir, "test-data", "acme-solver-pod-template.yaml")

    for row in context.table:
        name = row['name']
        port = int(row['port'])
        token = row['token']
        key = row['key']
        domain = row['domain']

        if not does_object_exist(context.v1_client, name, context.namespace, "pod"):
            with open(full_file_path) as f:
                pod_template = yaml.safe_load(f)

            pod_template['metadata']['name'] = name

            # Update the container args and port
            container = pod_template['spec']['containers'][0]
            container['args'] = [
                f'--listen-port={port}',
                f'--domain={domain}',
                f'--token={token}',
                f'--key={key}'
            ]
            container['ports'][0]['containerPort'] = port

            v1 = context.v1_client
            delete_pod_if_exists(v1, name, context.namespace)
            v1.create_namespaced_pod(namespace=context.namespace, body=pod_template)

            assert is_pod_running_and_ready(v1, context.namespace, name)

@step('the service-account "{service_account_name}" exists')
def step_impl(context, service_account_name):
    namespace = context.namespace
    rbac_file_path = os.path.join(os.path.dirname(__file__), 'test-data', 'rbac.yaml')

    try:
        v1 = context.v1_client
        v1.read_namespaced_service_account(name=service_account_name, namespace=namespace)
        logger.info(f"Service account '{service_account_name}' already exists in namespace '{namespace}'")
    except client.exceptions.ApiException as e:
        if e.status == 404:
            logger.info(f"Service account '{service_account_name}' does not exist in namespace '{namespace}', applying rbac.yaml...")
            # TODO: Use client from context
            utils.create_from_yaml(get_api_client(logger), rbac_file_path, namespace=namespace)
            logger.info(f"Service account '{service_account_name}' and associated RBAC resources created in namespace '{namespace}'")
        else:
            raise

@step('I deploy the acme challenge dispatcher pod with the following parameters')
def deploy_acme_challenge_dispatcher_pod(context):
    namespace = context.namespace
    table = context.table

    if not does_object_exist(context.v1_client, table[0]['name'], namespace, "pod"):

        pod_template_path = os.path.join(os.path.dirname(__file__), 'test-data', 'acme-challenge-dispatcher-pod-template.yaml')
        with open(pod_template_path) as f:
            pod_template = yaml.safe_load(f)

        pod_template['metadata']['name'] = table[0]['name']
        pod_template['spec']['containers'][0]['image'] = table[0]['image']

        # Create the pod in the specified namespace
        v1 = context.v1_client
        v1.create_namespaced_pod(namespace=namespace, body=pod_template)
        print(f"Pod '{table[0]['name']}' with image '{table[0]['image']}' created in namespace '{namespace}'")

        assert is_pod_running_and_ready(v1, namespace, pod_template['metadata']['name'])

    if not does_object_exist(context.v1_client, "acme-challenge-dispatcher-service", namespace, "service"):
        service_template_path = os.path.join(os.path.dirname(__file__), 'test-data', 'acme-challenge-dispatcher-service.yaml')
        with open(service_template_path) as f:
            service_template = yaml.safe_load(f)

        v1 = context.v1_client
        v1.create_namespaced_service(namespace=namespace, body=service_template)
        print(f"Service '{table[0]['name']}' created in namespace '{namespace}'")

        start_time = time()
        while time() - start_time < 60:
            endpoints = v1.read_namespaced_endpoints(name="acme-challenge-dispatcher-service", namespace=namespace)
            if endpoints.subsets:
                break
            sleep(1)
        else:
            raise Exception("Service did not get any endpoints after one minute")


@step('I do {num_requests:d} GET request to {port:d} with the following parameters')
def do_get_request(context, num_requests, port):
    params = context.table[0]
    url = f"http://localhost:{port}{params['url']}"
    headers = {'Host': params['host']}

    context.requests = []

    for _ in range(num_requests):
        response = requests.get(url, headers=headers)
        context.requests.append(response)

@step('response number {response_number:d} should have return code {expected_code:d} and content "{expected_content}"')
@step('all responses should have return code {expected_code:d} and content "{expected_content}"')
def check_response(context, response_number=None, expected_code=None, expected_content=None):
    if response_number is not None:
        response = context.requests[response_number - 1]  # Adjust for 0-based index
        assert response.status_code == expected_code, f"Expected status code {expected_code}, but got {response.status_code}"
        assert response.text == expected_content, f"Expected content '{expected_content}', but got '{response.text}'"
    else:
        for response in context.requests:
            assert response.status_code == expected_code, f"Expected status code {expected_code}, but got {response.status_code}"
            assert response.text == expected_content, f"Expected content '{expected_content}', but got '{response.text}'"

@step('I delete the pods')
def delete_pods(context):
    namespace = context.namespace
    v1 = context.v1_client

    for row in context.table:
        pod_name = row['name']
        delete_pod_if_exists(v1, pod_name, namespace)
        print(f"Pod '{pod_name}' deleted in namespace '{namespace}'")

def delete_pod(v1, pod_name, namespace):
    return v1.delete_namespaced_pod(name=pod_name, namespace=namespace)

def delete_pod_if_exists(v1, pod_name, namespace):
    def run():
        delete_pod(v1, pod_name, namespace)

    while True:
        try:
            run()
            sleep(0.5)
        except client.rest.ApiException as e:
            has_deleted = json.loads(e.body)['code'] == 404
            if has_deleted:
                return

def does_object_exist(v1, name, namespace, type):
    try:
        if type == "pod":
            v1.read_namespaced_pod(name=name, namespace=namespace)
        elif type == "service":
            v1.read_namespaced_service(name=name, namespace=namespace)
        return True
    except client.exceptions.ApiException as e:
        if e.status == 404:
            return False
        else:
            raise

def is_pod_running_and_ready(v1, namespace, pod_name, timeout=60):
    start_time = time()

    while time() - start_time < timeout:
        try:
            pod = v1.read_namespaced_pod(name=pod_name, namespace=namespace)
            if pod.status.phase == "Running":
                if all(container_status.ready for container_status in pod.status.container_statuses):
                    return True
        except client.exceptions.ApiException as e:
            if e.status == 404:
                print(f"Pod '{pod_name}' not found in namespace '{namespace}'")
                return False
            else:
                print(f"Error occurred: {e}")

        sleep(1)

    return False