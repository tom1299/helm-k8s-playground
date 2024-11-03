import os
import http.server
import signal
import socketserver
import threading
import time
import traceback

import requests

from k8s_functions import get_core_v1_client
from log_functions import get_logger

LABEL_SELECTOR = os.getenv('LABEL_SELECTOR', 'app=acme-challenge-dispatcher')
NAMESPACE = os.getenv('POD_NAMESPACE')
API_CLIENT = None

logger = get_logger()

def get_api_client():
    global API_CLIENT
    if API_CLIENT is None:
        API_CLIENT = get_core_v1_client(logger)
    return API_CLIENT

def get_acme_clients():
    v1 = get_api_client()
    pods = v1.list_namespaced_pod(namespace=NAMESPACE, label_selector=LABEL_SELECTOR)
    if not pods:
        return []
    acme_clients = []
    for pod in pods.items:
        if pod.status.pod_ip:
            acme_clients.append(pod.status.pod_ip)
        else:
            logger.warning("Pod '%s' does not have an ip (yet)'", pod.metadata.name)
    return acme_clients


class HealthHandler(http.server.SimpleHTTPRequestHandler):

    def log_message(self, format, *args):
        logger.debug(format % args)

    def do_GET(self):

        if self.path == '/healthz':
            self.handle_health_request()
            return

        if self.path == '/metrics':
            self.handle_metrics_request()
            return

        logger.error("Invalid path: %s for health check", self.path)
        self.send_response(404)
        self.end_headers()
        ChallengeHandler.counter_404 += 1

    def handle_health_request(self):
        try:
            acme_clients = get_acme_clients()
            if acme_clients is not None:
                self.send_response(200)
                self.end_headers()
                logger.debug("Cluster connection is healthy, ACME clients: %s", acme_clients)
                ChallengeHandler.counter_200 += 1
            else:
                logger.error("Cluster connection is not healthy, no ACME clients found")
                self.send_response(500)
                self.end_headers()
                ChallengeHandler.counter_500 += 1
        except Exception as e: # pylint: disable=broad-except
            logger.error("Cluster connection is not healthy: %s\n%s", str(e), traceback.format_exc())
            self.send_response(500)
            self.end_headers()
            ChallengeHandler.counter_500 += 1

    def handle_metrics_request(self):
        metrics = (
            "# HELP acme_service_dispatcher_requests_total Total number of scrapes by HTTP status code.\n"
            "# TYPE acme_service_dispatcher_requests_total counter\n"
            f"acme_service_dispatcher_requests_total{{code=\"200\"}} {ChallengeHandler.counter_200}\n"
            f"acme_service_dispatcher_requests_total{{code=\"400\"}} {ChallengeHandler.counter_400}\n"
            f"acme_service_dispatcher_requests_total{{code=\"404\"}} {ChallengeHandler.counter_404}\n"
            f"acme_service_dispatcher_requests_total{{code=\"500\"}} {ChallengeHandler.counter_500}\n"
        )
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; version=0.0.4")
        self.end_headers()
        self.wfile.write(metrics.encode())


class ChallengeHandler(http.server.SimpleHTTPRequestHandler):

    acme_clients_cache = {}
    last_acme_challenge_request_time = 0

    # Counters for HTTP status codes
    counter_200 = 0
    counter_400 = 0
    counter_404 = 0
    counter_500 = 0

    def __init__(self, request, client_address, server):
        if request is None:
            return
        super().__init__(request, client_address, server)

    @classmethod
    def create_without_server(cls):
        return ChallengeHandler(None, None, None)

    def log_message(self, format, *args):
        logger.debug(format % args)

    def do_GET(self):
        logger.info("Received request: %s, Headers: %s", self.path, self.headers)

        if not self.path.startswith('/.well-known/acme-challenge/'):
            self.handle_non_challenge_request()
            return

        token = self.extract_token()
        host = self.headers.get('Host')

        if not token or not host:
            self.handle_missing_token_or_host()
            return

        logger.info("Current cache content: %s", ChallengeHandler.acme_clients_cache)
        ChallengeHandler.last_acme_challenge_request_time = time.time()
        self.clear_cache_if_needed()

        if token in ChallengeHandler.acme_clients_cache:
            self.handle_cached_token(host, token)
        else:
            self.handle_new_token(host, token)

    def clear_cache_if_needed(self):
        if time.time() - ChallengeHandler.last_acme_challenge_request_time > 600:
            ChallengeHandler.acme_clients_cache.clear()
            logger.info("Cleared cache as no ACME challenge request was received in last 600 seconds")

    def handle_new_token(self, host, token):
        logger.debug("Request for new token %s for host %s received", token, host)
        acme_clients = get_acme_clients()
        logger.info("Found %s ACME clients: %s", len(acme_clients), acme_clients)
        for client_ip in acme_clients:
            logger.debug("Trying ACME client with ip %s and token %s", client_ip, token)
            response = self.send_request_to_acme_client(client_ip, token, host)
            if response and response.status_code == 200:
                logger.info("ACME client %s returned 200 and response %s for token %s. Adding %s to cache",
                             client_ip, response.content, token, client_ip)
                ChallengeHandler.acme_clients_cache[token] = client_ip
                self.send_success(response, token, client_ip)
                return

        logger.error("None of the ACME clients returned 200 for token %s. Returning 404", token)
        self.send_404()

    def handle_cached_token(self, host, token):
        client_ip = ChallengeHandler.acme_clients_cache[token]
        logger.info("Found ACME client with IP %s in cache for token %s", client_ip, token)
        response = self.send_request_to_acme_client(client_ip, token, host)
        if response and response.status_code == 200:
            self.send_success(response, token, client_ip)
        else:
            ChallengeHandler.acme_clients_cache.pop(token)
            logger.error("ACME client '%s' did not return 200 for token %s: %s. Removed %s from cache",
                         client_ip, token, response.status_code if response else 'No response', client_ip)
            self.send_404()

    def send_404(self):
        self.send_response(404)
        self.end_headers()
        error_message = "404 Not Found"
        self.wfile.write(error_message.encode())
        ChallengeHandler.counter_404 += 1

    def handle_missing_token_or_host(self):
        logger.error("Token or host missing in request: %s, Headers: %s", self.path, self.headers)
        self.send_response(400)
        self.end_headers()
        error_message = "400 Bad Request"
        self.wfile.write(error_message.encode())
        ChallengeHandler.counter_400 += 1

    def handle_non_challenge_request(self):
        self.send_response(404)
        self.end_headers()
        error_message = "404 Not Found"
        logger.error("Invalid path: %s", self.path)
        self.wfile.write(error_message.encode())
        ChallengeHandler.counter_404 += 1

    def extract_token(self):
        if not self.path:
            logger.error("No path provided to extract token from")
            return ''
        return self.path.split('/')[-1]

    def send_request_to_acme_client(self, client_ip, token, host):
        url = f"http://{client_ip}:8089/.well-known/acme-challenge/{token}"
        headers = {'Host': host, 'User-Agent': 'acme-challenge-dispatcher'}
        try:
            response = requests.get(url, headers=headers, timeout=1)
            return response
        except requests.RequestException as e:
            logger.error("Error while sending request to ACME client %s: %s\n%s",
                         client_ip, str(e), traceback.format_exc())
            ChallengeHandler.counter_500 += 1
            return None

    def send_success(self, response, token, client_ip):
        ChallengeHandler.acme_clients_cache[token] = client_ip
        self.send_response(200)
        self.end_headers()
        self.wfile.write(response.content)
        logger.info("Successfully wrote response %s for token %s from ACME client %s", response.content,
                    token, client_ip)
        ChallengeHandler.counter_200 += 1

class ThreadingHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True

def run_server():
    logger.info("Serving health checks on port 8081")
    health_server = ThreadingHTTPServer(("0.0.0.0", 8081), HealthHandler)

    logger.info("Serving acme challenges on port 8080 with label selector '%s'", LABEL_SELECTOR)
    challenge_server = ThreadingHTTPServer(("0.0.0.0", 8089), ChallengeHandler)

    def gracefully_shutdown_hook(signum, frame): # pylint: disable=unused-argument
        thread = threading.Thread(target=health_server.shutdown)
        thread.start()
        thread = threading.Thread(target=challenge_server.shutdown)
        thread.start()

    signal.signal(signal.SIGTERM, gracefully_shutdown_hook)

    threading.Thread(target=health_server.serve_forever).start()
    threading.Thread(target=challenge_server.serve_forever).start()


if __name__ == '__main__':
    run_server()
