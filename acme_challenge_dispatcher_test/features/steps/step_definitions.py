import json
import logging
import os
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
    with open(full_file_path) as f:
         pod_template = yaml.safe_load(f)

    table = context.table
    name = table[0]['name']
    port = int(table[0]['port'])
    token = table[0]['token']
    key = table[0]['key']

    # Update the pod name
    pod_template['metadata']['name'] = name

    # Update the container args and port
    container = pod_template['spec']['containers'][0]
    container['args'] = [
        f'--listen-port={port}',
        '--domain=example.com',
        f'--token={token}',
        f'--key={key}'
    ]
    container['ports'][0]['containerPort'] = port

    v1 = context.api_client
    delete_pod_if_exists(v1, name, context.namespace)
    v1.create_namespaced_pod(namespace=context.namespace, body=pod_template)

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


@step('I wait for 1 minute')
def wait_for_one_minute(context):
    sleep(60)

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
    parameters = context.table

    # Read the pod template
    pod_template_path = os.path.join(os.path.dirname(__file__), 'test-data', 'acme-challenge-dispatcher-pod-template.yaml')
    with open(pod_template_path) as f:
        pod_template = yaml.safe_load(f)

    for row in parameters:
        pod_template['metadata']['name'] = row['name']
        pod_template['spec']['containers'][0]['image'] = row['image']

        # Create the pod in the specified namespace
        v1 = context.api_client
        v1.create_namespaced_pod(namespace=namespace, body=pod_template)
        print(f"Pod '{row['name']}' with image '{row['image']}' created in namespace '{namespace}'")

    is_pod_running_and_ready(v1, namespace, pod_template['metadata']['name'])

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