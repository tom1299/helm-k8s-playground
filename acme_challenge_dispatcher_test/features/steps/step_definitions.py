import json
import logging
import os
import subprocess
from time import sleep

import yaml

from acme_challenge_dispatcher.k8s_utils import get_api_client
from behave import step
from kubernetes import client

logger = logging.getLogger(__name__)

@step('I have a connection to the cluster')
def step_impl(context):
    api_client = get_api_client(logger)
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