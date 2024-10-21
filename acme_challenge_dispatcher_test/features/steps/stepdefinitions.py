import logging

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