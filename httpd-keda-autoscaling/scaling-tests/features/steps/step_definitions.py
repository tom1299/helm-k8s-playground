from behave import given, step
from kubernetes import client, config
from kubernetes.client.rest import ApiException
import logging
import os
import time
import yaml

# Create a logger
logger = logging.getLogger()
logger.setLevel(logging.WARNING)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.WARNING)

formatter = logging.Formatter('\x1b[33;20m    %(message)s\x1b[0m')

console_handler.setFormatter(formatter)

logger.addHandler(console_handler)


@step('I have a connection to the cluster')
def establish_cluster_connection(context):
    if not hasattr(context, 'api_client'):
        if os.path.exists('/var/run/secrets/kubernetes.io/serviceaccount/token'):
            config.load_incluster_config()
            context.api_client = client.ApiClient()
        elif not hasattr(context, 'api_client'):
            kubeconfig_path = os.getenv('KUBECONFIG')

            config.load_kube_config(config_file=kubeconfig_path)

            username = os.getenv('K8S_USER')
            password = os.getenv('K8S_USER_PASSWORD')
            client.Configuration().username = username
            client.Configuration().password = password

            api_client = client.ApiClient()

            version_api = client.VersionApi(api_client)
            version_info = version_api.get_code()
            print(f"Kubernetes version: {version_info.git_version}")

            context.api_client = api_client

    # Set the namespace in the context
    context.namespace = "httpd-autoscaling"


@step('The namespace "{namespace}" exists')
def check_namespace_exists(context, namespace):
    v1 = client.CoreV1Api(context.api_client)
    namespaces = v1.list_namespace()
    namespace_names = [ns.metadata.name for ns in namespaces.items]

    if namespace not in namespace_names:
        raise Exception(f"Namespace {namespace} does not exist")

    # Update the context namespace
    context.namespace = namespace


@step('The deployment "{deployment_name}" is installed having {replica_count:d} replica running')
def check_deployment_replicas(context, deployment_name, replica_count):
    v1_apps = client.AppsV1Api(context.api_client)
    namespace = context.namespace

    try:
        deployment = v1_apps.read_namespaced_deployment(deployment_name, namespace)
        actual_replicas = deployment.status.ready_replicas

        if actual_replicas != replica_count:
            raise Exception(
                f"Deployment {deployment_name} has {actual_replicas} replicas running, expected {replica_count}")
    except client.exceptions.ApiException as e:
        raise Exception(f"Exception when calling AppsV1Api->read_namespaced_deployment: {e}")


@step(
    'I deploy the config map "{config_map_name}" with the content of the file "{file_path}" as the data item "{data_item}"')
def deploy_config_map(context, config_map_name, file_path, data_item):
    v1 = client.CoreV1Api(context.api_client)
    namespace = context.namespace

    script_dir = os.path.dirname(__file__)
    full_file_path = os.path.join(script_dir, "../", file_path)

    with open(full_file_path, 'r') as file:
        file_content = file.read()

    config_map = client.V1ConfigMap(
        metadata=client.V1ObjectMeta(name=config_map_name),
        data={data_item: file_content}
    )

    try:
        v1.delete_namespaced_config_map(name=config_map_name, namespace=namespace)
        print(f"ConfigMap {config_map_name} deleted successfully in namespace {namespace}")
    except ApiException as e:
        if e.status != 404:
            raise Exception(f"Exception when deleting ConfigMap: {e}")

    try:
        v1.create_namespaced_config_map(namespace=namespace, body=config_map)
        print(f"ConfigMap {config_map_name} created successfully in namespace {namespace}")
    except ApiException as e:
        raise Exception(f"Exception when creating ConfigMap: {e}")


@step('I create the pod "{pod_name}" with the pod spec from the file "{file_path}"')
def create_pod_with_spec(context, pod_name, file_path):
    v1 = client.CoreV1Api(context.api_client)
    namespace = context.namespace

    script_dir = os.path.dirname(__file__)
    full_file_path = os.path.join(script_dir, "../", file_path)

    with open(full_file_path, 'r') as file:
        pod_spec = yaml.safe_load(file)

    pod_spec['metadata']['name'] = pod_name

    delete_pod(context, pod_name)

    try:
        # Create the pod
        v1.create_namespaced_pod(namespace=namespace, body=pod_spec)
        print(f"Pod {pod_name} created successfully in namespace {namespace}")
    except client.exceptions.ApiException as e:
        raise Exception(f"Exception when creating Pod: {e}")


@step('The pod "{pod_name}" should be running within {timeout:d} seconds')
def check_pod_running(context, pod_name, timeout):
    v1 = client.CoreV1Api(context.api_client)
    namespace = context.namespace
    end_time = time.time() + timeout

    while time.time() < end_time:
        try:
            pod = v1.read_namespaced_pod(name=pod_name, namespace=namespace)
            if pod.status.phase == "Running":
                print(f"Pod {pod_name} is running in namespace {namespace}")
                return
        except client.exceptions.ApiException as e:
            if e.status != 404:
                raise Exception(f"Exception when reading Pod: {e}")

        time.sleep(5)

    raise Exception(f"Pod {pod_name} is not running in namespace {namespace} within {timeout} seconds")


@step('The deployment "{deployment_name}" should have {replica_count:d} replicas running within {timeout:d} seconds')
def check_deployment_replicas_within_timeout(context, deployment_name, replica_count, timeout):
    v1_apps = client.AppsV1Api(context.api_client)
    namespace = context.namespace
    start_time = time.time()
    end_time = start_time + timeout

    while time.time() < end_time:
        try:
            deployment = v1_apps.read_namespaced_deployment(deployment_name, namespace)
            if deployment.status.ready_replicas == replica_count:
                print(f"Deployment {deployment_name} has {replica_count} replicas running in namespace {namespace}, within {time.time() - start_time} seconds")
                return
        except client.exceptions.ApiException as e:
            raise Exception(f"Exception when reading Deployment: {e}")

        time.sleep(5)

    raise Exception(f"Deployment {deployment_name} does not have {replica_count} replicas running in namespace {namespace} within {timeout} seconds")


@step('I delete the pod "{pod_name}"')
def delete_pod(context, pod_name):
    v1 = client.CoreV1Api(context.api_client)
    namespace = context.namespace

    try:
        v1.delete_namespaced_pod(name=pod_name, namespace=namespace)
        print(f"Pod {pod_name} deleted successfully in namespace {namespace}")
    except client.exceptions.ApiException as e:
        if e.status != 404:
            raise Exception(f"Exception when deleting Pod: {e}")