import json
import logging
import os
import requests
import subprocess
from time import sleep, time

from kubernetes import utils

import yaml

from acme_challenge_dispatcher.k8s_utils import get_core_v1_client, get_api_client

from behave import step
from kubernetes import client

logger = logging.getLogger(__name__)

@step('I have a connection to the cluster')
def step_impl(context):
    api_client = get_core_v1_client(logger)
    api_client.list_namespace()
    context.api_client = api_client

@step('The namespace "{namespace}" exists')
def check_namespace_exists(context, namespace):
    v1 = context.api_client
    namespaces = v1.list_namespace()
    namespace_names = [ns.metadata.name for ns in namespaces.items]

    if namespace not in namespace_names:
        v1.create_namespace(client.V1Namespace(metadata=client.V1ObjectMeta(name=namespace)))

    context.namespace = namespace


@step('I deploy an acme solver pod with the following parameters')
def deploy_acme_solver_pod(context):
    script_dir = os.path.dirname(__file__)
    full_file_path = script_dir + "/test-data/acme-solver-pod-template.yaml"

    table = context.table
    name = table[0]['name']
    port = int(table[0]['port'])
    token = table[0]['token']
    key = table[0]['key']
    domain = table[0]['domain']

    if not does_pod_exist(context.api_client, name, context.namespace):
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

        v1 = context.api_client
        delete_pod_if_exists(v1, name, context.namespace)
        v1.create_namespaced_pod(namespace=context.namespace, body=pod_template)

        is_pod_running_and_ready(v1, context.namespace, name)

@step('I forward the port {pod_port:d} of the pod "{pod_name}" to port {host_port:d}')
def forward_port(context, pod_port, pod_name, host_port):
    namespace = context.namespace

    # Ensure the port_forward_processes list exists in the context
    if not hasattr(context, 'port_forward_processes'):
        context.port_forward_processes = []

    # Run a loop until the pod is in the state Running
    v1 = context.api_client
    while True:
        pod = v1.read_namespaced_pod(name=pod_name, namespace=namespace)
        if pod.status.phase == "Running":
            break
        sleep(1)

    try:
        process = subprocess.Popen(
            ["kubectl", "port-forward", f"pod/{pod_name}", f"{host_port}:{pod_port}", "-n", namespace])
        context.port_forward_processes.append({'pod_name': pod_name, 'pid': process.pid})
    except subprocess.CalledProcessError as e:
        print(f"Failed to forward port: {e}")


@step('I wait for {seconds:d} seconds')
def wait_for_seconds(context, seconds):
    sleep(seconds)

@step('the service-account "{service_account_name}" exists')
def step_impl(context, service_account_name):
    namespace = context.namespace
    rbac_file_path = os.path.join(os.path.dirname(__file__), 'test-data', 'rbac.yaml')

    try:
        v1 = context.api_client
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

    if not does_pod_exist(context.api_client, table[0]['name'], namespace):

        pod_template_path = os.path.join(os.path.dirname(__file__), 'test-data', 'acme-challenge-dispatcher-pod-template.yaml')
        with open(pod_template_path) as f:
            pod_template = yaml.safe_load(f)

        pod_template['metadata']['name'] = table[0]['name']
        pod_template['spec']['containers'][0]['image'] = table[0]['image']

        # Create the pod in the specified namespace
        v1 = context.api_client
        v1.create_namespaced_pod(namespace=namespace, body=pod_template)
        print(f"Pod '{table[0]['name']}' with image '{table[0]['image']}' created in namespace '{namespace}'")

        is_pod_running_and_ready(v1, namespace, pod_template['metadata']['name'])

@step('I stop forwarding the port {pod_port:d} of the pod "{pod_name}"')
def stop_forwarding_port(context, pod_port, pod_name):
    if not hasattr(context, 'port_forward_processes'):
        print("No port forwarding processes found in context")
        return

    for process_info in context.port_forward_processes:
        if process_info['pod_name'] == pod_name:
            try:
                subprocess.run(["kill", str(process_info['pid'])], check=True)
                print(f"Stopped port forwarding for pod '{pod_name}' on port {pod_port}")
            except subprocess.CalledProcessError as e:
                print(f"Failed to stop port forwarding: {e}")
            context.port_forward_processes.remove(process_info)
            break
    else:
        print(f"No port forwarding process found for pod '{pod_name}' on port {pod_port}")

@step('I do a GET request to {port:d} with the following parameters')
def do_get_request(context, port):
    params = context.table[0]
    url = f"http://localhost:{port}{params['url']}"
    headers = {'Host': params['host']}

    response = requests.get(url, headers=headers)
    context.response = response

@step('the response should be "{expected_response}"')
def check_response(context, expected_response):
    assert context.response.text == expected_response, f"Expected '{expected_response}', but got '{context.response.text}'"

def delete_pod(v1, pod_name, namespace):
    return v1.delete_namespaced_pod(name=pod_name, namespace=namespace)

def delete_pod_if_exists(v1, pod_name, namespace):
    def run():
        delete_pod(v1, pod_name, namespace)

    while True:
        try:
            run()
            sleep(0.2)
        except client.rest.ApiException as e:
            has_deleted = json.loads(e.body)['code'] == 404
            if has_deleted:
                return

def does_pod_exist(v1, pod_name, namespace):
    try:
        v1.read_namespaced_pod(name=pod_name, namespace=namespace)
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