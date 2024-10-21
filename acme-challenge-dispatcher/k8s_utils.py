import os
from kubernetes import client, config

def get_api_client(logger):

    if os.path.exists('/var/run/secrets/kubernetes.io/serviceaccount/token'):
        logger.info("Using in-cluster configuration with service account token to access the API server")
        config.load_incluster_config()
        api_client = client.CoreV1Api()
    else:
        kubeconfig_path = os.getenv('KUBECONFIG')
        logger.info(f"Using configuration from kubeconfig file at '{kubeconfig_path}'")

        config.load_kube_config(config_file=kubeconfig_path)

        username = os.getenv('K8S_USER')
        password = os.getenv('K8S_USER_PASSWORD')
        client.Configuration().username = username
        client.Configuration().password = password

        api_client = client.CoreV1Api()

    return api_client
