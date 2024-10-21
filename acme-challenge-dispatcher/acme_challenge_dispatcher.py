import os
import http.server
import socketserver
import logging
import json
import traceback

import requests
from kubernetes import client, config

PORT = 8080
LABEL_SELECTOR = os.getenv('LABEL_SELECTOR', 'app=acme-challenge-dispatcher')

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger()
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
logger.addHandler(handler)

class AcmeChallengeDispatcher(http.server.SimpleHTTPRequestHandler):

    acme_clients_cache = {}

    api_client = None

    def do_GET(self):
        if self.path == '/healthz':
            self.is_healthy()
            return
        elif not self.path.startswith('/.well-known/acme-challenge/'):
            self.send_response(404)
            self.end_headers()
            error_message = f"404 Not Found: Invalid path '{self.path}'"
            logger.info(f"Invalid path: {self.path}")
            self.wfile.write(error_message.encode())
            return

        token = self.extract_token(self.path)
        host = self.headers.get('Host')
        logger.info(f"Token: {token}, Host: {host}")

        if token in self.acme_clients_cache:
            client_ip = self.acme_clients_cache[token]
            logger.info(f"Found ACME client with IP {client_ip} in cache for token {token}")
            response = self.send_request_to_acme_client(client_ip, token, host)
            if response and response.status_code == 200:
                self.handle_successful_response(response, token, client_ip)
                logger.info(f"Successfully returned response for token {token} from ACME client {client_ip}")
                return
            else:
                self.acme_clients_cache.pop(token)
                error_message = f"ACME client '{client_ip}' did not return 200 for token {token}: {response.status_code if response else 'No response'}. Removed {client_ip} from cache"
                logger.error(error_message)

        acme_clients = self.get_acme_clients()
        for client_ip in acme_clients:
            response = self.send_request_to_acme_client(client_ip, token, host)
            if response and response.status_code == 200:
                self.handle_successful_response(response, token, client_ip)
                return
            else:
                logger.info(f"Client IP: {client_ip}, Response Code: {response.status_code if response else 'No response'}")

        self.send_response(404)
        self.end_headers()
        error_message = "404 Not Found: No ACME matching client found"
        logger.error(f"No ACME client returned 200 for token {token} and host {host}")
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
        pods = v1.list_namespaced_pod(namespace='wlan', label_selector=LABEL_SELECTOR)
        return [pod.status.pod_ip for pod in pods.items]

    def handle_successful_response(self, response, token, client_ip):
        self.acme_clients_cache[token] = client_ip
        self.send_response(200)
        self.end_headers()
        self.wfile.write(response.content)
        logger.info(f"Successfully wrote response {response.content} for token {token} from ACME client {client_ip}")

    def get_api_client(self):
        if not self.api_client:
            if os.path.exists('/var/run/secrets/kubernetes.io/serviceaccount/token'):
                logger.info("Using in-cluster configuration with service account token to access the API server")
                config.load_incluster_config()
                self.api_client = client.CoreV1Api()
            else:
                kubeconfig_path = os.getenv('KUBECONFIG')
                logger.info(f"Using configuration from kubeconfig file at '{kubeconfig_path}'")

                config.load_kube_config(config_file=kubeconfig_path)

                username = os.getenv('K8S_USER')
                password = os.getenv('K8S_USER_PASSWORD')
                client.Configuration().username = username
                client.Configuration().password = password

                self.api_client = client.CoreV1Api()
        return self.api_client

    def is_healthy(self):
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
    with socketserver.TCPServer(("0.0.0.0", PORT), AcmeChallengeDispatcher) as httpd:
        logger.info(f"Serving on port {PORT} with label selector '{LABEL_SELECTOR}'")
        httpd.serve_forever()