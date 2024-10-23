import os
import http.server
import logging
import json
import signal
import threading
import traceback

import requests

from k8s_utils import get_core_v1_client

PORT = 8080
LABEL_SELECTOR = os.getenv('LABEL_SELECTOR', 'app=acme-challenge-dispatcher')
NAMESPACE = os.getenv('POD_NAMESPACE')

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(os.getenv('LOG_LEVEL', 'INFO'))

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

logging.getLogger("urllib3").setLevel(logging.WARNING)


class AcmeChallengeDispatcher(http.server.SimpleHTTPRequestHandler):

    acme_clients_cache = {}

    api_client = None

    def __init__(self, request, client_address, server):
        if request is None:
            return
        super().__init__(request, client_address, server)

    @classmethod
    def create_without_server(cls):
        return AcmeChallengeDispatcher(None, None, None)

    def do_GET(self):
        logger.info("Received request: %s, Headers: %s", self.path, self.headers)

        if self.path == '/healthz':
            self.handle_health_request()
            return

        if not self.path.startswith('/.well-known/acme-challenge/'):
            self.handle_non_challenge_request()
            return

        token = self.extract_token()
        host = self.headers.get('Host')

        logger.info("Current cache content: %s", AcmeChallengeDispatcher.acme_clients_cache)

        if not token or not host:
            self.handle_missing_token_or_host()
            return

        if token in AcmeChallengeDispatcher.acme_clients_cache:
            self.handle_cached_token(host, token)
        else:
            self.handle_new_token(host, token)

    def handle_new_token(self, host, token):
        logger.debug("Request for new token %s for host %s received", token, host)
        acme_clients = self.get_acme_clients()
        for client_ip in acme_clients:
            logger.debug("Trying ACME client with ip %s and token %s", client_ip, token)
            response = self.send_request_to_acme_client(client_ip, token, host)
            if response and response.status_code == 200:
                logger.debug("ACME client %s returned 200 and response %s for token %s. Adding %s to cache",
                             client_ip, response.content, token, client_ip)
                AcmeChallengeDispatcher.acme_clients_cache[token] = client_ip
                self.send_success(response, token, client_ip)
                logger.info("Successfully returned response for token %s from ACME client %s. Added %s to cache",
                            token, client_ip, client_ip)
                return

        logger.error("None of the ACME clients returned 200 for token %s. Returning 404", token)
        self.send_404()

    def handle_cached_token(self, host, token):
        client_ip = AcmeChallengeDispatcher.acme_clients_cache[token]
        logger.info("Found ACME client with IP %s in cache for token %s", client_ip, token)
        response = self.send_request_to_acme_client(client_ip, token, host)
        if response and response.status_code == 200:
            self.send_success(response, token, client_ip)
            logger.info("Successfully returned response for token %s from ACME client %s", token, client_ip)
        else:
            AcmeChallengeDispatcher.acme_clients_cache.pop(token)
            logger.error("ACME client '%s' did not return 200 for token %s: %s. Removed %s from cache",
                         client_ip, token, response.status_code if response else 'No response', client_ip)
            self.send_404()

    def send_404(self):
        self.send_response(404)
        self.end_headers()
        error_message = "404 Not Found"
        self.wfile.write(error_message.encode())

    def handle_missing_token_or_host(self):
        logger.error("Token or host missing in request: %s, Headers: %s", self.path, self.headers)
        self.send_response(400)
        self.end_headers()
        error_message = "400 Bad Request"
        self.wfile.write(error_message.encode())

    def handle_non_challenge_request(self):
        self.send_response(404)
        self.end_headers()
        error_message = "404 Not Found"
        logger.error("Invalid path: %s", self.path)
        self.wfile.write(error_message.encode())

    def extract_token(self):
        if not self.path:
            logger.error("No path provided to extract token from")
            return ''
        return self.path.split('/')[-1]

    def send_request_to_acme_client(self, client_ip, token, host):
        url = f"http://{client_ip}:8080/.well-known/acme-challenge/{token}"
        headers = {'Host': host}
        try:
            response = requests.get(url, headers=headers, timeout=1)
            return response
        except requests.RequestException as e:
            logger.error("Error while sending request to ACME client %s: %s\n%s",
                         client_ip, str(e), traceback.format_exc())
            return None

    def get_acme_clients(self):
        v1 = self.get_api_client()
        pods = v1.list_namespaced_pod(namespace=NAMESPACE, label_selector=LABEL_SELECTOR)
        if not pods:
            logger.info("No pods found with label selector '%s'", LABEL_SELECTOR)
            return []
        logger.info("Found %d pods with label selector '%s'", len(pods.items), LABEL_SELECTOR)
        return [pod.status.pod_ip for pod in pods.items]

    def send_success(self, response, token, client_ip):
        AcmeChallengeDispatcher.acme_clients_cache[token] = client_ip
        self.send_response(200)
        self.end_headers()
        self.wfile.write(response.content)
        logger.info("Successfully wrote response %s for token %s from ACME client %s", response.content,
                    token, client_ip)

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
                logger.debug("Cluster connection is healthy, ACME clients: %s", acme_clients)
            else:
                logger.error("Cluster connection is not healthy, no ACME clients found")
                self.send_response(500)
                self.end_headers()
        except Exception as e: # pylint: disable=broad-except
            logger.error("Cluster connection is not healthy: %s\n%s", str(e), traceback.format_exc())
            self.send_response(500)
            self.end_headers()

def run_server():
    server_address = ('', PORT)
    httpd = http.server.HTTPServer(server_address, AcmeChallengeDispatcher)
    logger.info("Serving on port %s with label selector '%s'", PORT, LABEL_SELECTOR)

    def gracefully_shutdown_hook(signum, frame): # pylint: disable=unused-argument
        thread = threading.Thread(target=httpd.shutdown)
        thread.start()

    signal.signal(signal.SIGTERM, gracefully_shutdown_hook)

    httpd.serve_forever()


if __name__ == '__main__':
    run_server()
