import os
import http.server
import socketserver
import logging
import json
import traceback

import requests

from k8s_utils import get_core_v1_client

PORT = 8080
LABEL_SELECTOR = os.getenv('LABEL_SELECTOR', 'app=acme-challenge-dispatcher')
NAMESPACE = os.getenv('POD_NAMESPACE')

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            'message': record.getMessage(),
            'level': record.levelname,
            'time': self.formatTime(record, self.datefmt),
            'filename': record.filename,
            'function': record.funcName,
            'line': record.lineno
        }
        return json.dumps(log_record)

handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logger.propagate = False
logger.addHandler(handler)

class AcmeChallengeDispatcher(http.server.SimpleHTTPRequestHandler):

    acme_clients_cache = {}

    api_client = None

    def __init__(self):
        pass

    def __init__(self, request, client_address, server):
        if request is None:
            return
        super().__init__(request, client_address, server)

    @classmethod
    def create_without_server(cls):
        return AcmeChallengeDispatcher(None, None, None)

    def do_GET(self):
        logger.info(f"Received request: {self.path}, Headers: {self.headers}")

        if self.path == '/healthz':
            self.handle_health_request()
            return
        elif not self.path.startswith('/.well-known/acme-challenge/'):
            self.handle_non_challenge_request()
            return

        token = self.extract_token(self.path)
        host = self.headers.get('Host')
        logger.info(f"Token: {token}, Host: {host}")

        if not token or not host:
            self.handle_missing_token_or_host()
            return

        if token in self.acme_clients_cache:
            self.handle_cached_token(host, token)
        else:
            self.handle_new_token(host, token)

    def handle_new_token(self, host, token):
        logger.debug(f"Request of new token {token} for host {host} received")
        acme_clients = self.get_acme_clients()
        for client_ip in acme_clients:
            logger.debug(f"Trying ACME client with ip {client_ip} and token {token}")
            response = self.send_request_to_acme_client(client_ip, token, host)
            if response and response.status_code == 200:
                logger.debug(f"ACME client {client_ip} returned 200 and response {response.content} for token {token}. Adding {client_ip} to cache")
                self.api_clients_cache[token] = client_ip
                self.send_success(response, token, client_ip)
                logger.info(
                    f"Successfully returned response for token {token} from ACME client {client_ip}. Added {client_ip} to cache")
                return

        logger.error(f"None of the ACME clients returned 200 for token {token}. Returning 404")
        self.send_404()

    def handle_cached_token(self, host, token):
        client_ip = self.acme_clients_cache[token]
        logger.info(f"Found ACME client with IP {client_ip} in cache for token {token}")
        response = self.send_request_to_acme_client(client_ip, token, host)
        if response and response.status_code == 200:
            self.send_success(response, token, client_ip)
            logger.info(f"Successfully returned response for token {token} from ACME client {client_ip}")
        else:
            self.acme_clients_cache.pop(token)
            error_message = f"ACME client '{client_ip}' did not return 200 for token {token}: {response.status_code if response else 'No response'}. Removed {client_ip} from cache"
            logger.error(error_message)
            self.send_404()

    def send_404(self):
        self.send_response(404)
        self.end_headers()
        error_message = "404 Not Found"
        self.wfile.write(error_message.encode())

    def handle_missing_token_or_host(self):
        self.send_response(400)
        self.end_headers()
        error_message = "400 Bad Request: Token and host are required"
        logger.error("Token and / or host missing")
        self.wfile.write(error_message.encode())

    def handle_non_challenge_request(self):
        self.send_response(404)
        self.end_headers()
        error_message = f"404 Not Found: Invalid path '{self.path}'"
        logger.error(f"Invalid path: {self.path}")
        self.wfile.write(error_message.encode())

    def extract_token(self, path):
        if not path:
            logger.error("No path provided to extract token from")
            return ''
        return path.split('/')[-1]

    def send_request_to_acme_client(self, client_ip, token, host):
        url = f'http://{client_ip}:8080/.well-known/acme-challenge/{token}'
        headers = {'Host': host}
        try:
            response = requests.get(url, headers=headers, timeout=1)
            return response
        except requests.RequestException as e:
            logger.error(f"Error while sending request to ACME client {client_ip}: {str(e)}\n{traceback.format_exc()}")
            return None

    def get_acme_clients(self):
        v1 = self.get_api_client()
        pods = v1.list_namespaced_pod(namespace=NAMESPACE, label_selector=LABEL_SELECTOR)
        if not pods:
            logger.info(f"No pods found with label selector '{LABEL_SELECTOR}'")
            return []
        logger.info(f"Found {len(pods.items)} pods with label selector '{LABEL_SELECTOR}'")
        return [pod.status.pod_ip for pod in pods.items]

    def send_success(self, response, token, client_ip):
        self.acme_clients_cache[token] = client_ip
        self.send_response(200)
        self.end_headers()
        self.wfile.write(response.content)
        logger.info(f"Successfully wrote response {response.content} for token {token} from ACME client {client_ip}")

    def get_api_client(self):
        if AcmeChallengeDispatcher.api_client is None:
            AcmeChallengeDispatcher.api_client = get_core_v1_client(logger)
        return AcmeChallengeDispatcher.api_client

    def handle_health_request(self):
        try:
            acme_clients = self.get_acme_clients()
            if acme_clients is not None:
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"Connection to api server is healthy")
                logger.info(f"Cluster connection is healthy, ACME clients: {acme_clients}")
            else:
                raise Exception("No ACME clients found")
        except Exception as e:
            logger.error(f"Cluster connection is not healthy: {str(e)}\n{traceback.format_exc()}")
            self.send_response(500)
            self.end_headers()
            error_message = f"Connection to api server is not healthy: {str(e)}"
            self.wfile.write(error_message.encode())

if __name__ == '__main__':
    with socketserver.TCPServer(("", PORT), AcmeChallengeDispatcher) as httpd:
        logger.info(f"Serving on port {PORT} with label selector '{LABEL_SELECTOR}'")
        httpd.serve_forever()