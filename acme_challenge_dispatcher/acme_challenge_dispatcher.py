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

# Configuration constants
LABEL_SELECTOR = os.getenv('LABEL_SELECTOR', 'app=acme-challenge-dispatcher')
NAMESPACE = os.getenv('POD_NAMESPACE')
CHALLENGE_PORT = 8089
HEALTH_PORT = 8081
ACME_PATH_PREFIX = '/.well-known/acme-challenge/'
CACHE_TIMEOUT_SECONDS = 600
REQUEST_TIMEOUT_SECONDS = 1

logger = get_logger()
API_CLIENT = None

def get_api_client():
    global API_CLIENT
    if API_CLIENT is None:
        API_CLIENT = get_core_v1_client(logger)
    return API_CLIENT

def get_cert_manager_pods():
    try:
        v1 = get_api_client()
        pods = v1.list_namespaced_pod(namespace=NAMESPACE, label_selector=LABEL_SELECTOR)
        cert_manager_pods = []
        for pod in pods.items:
            if pod.status.pod_ip:
                cert_manager_pods.append(pod.status.pod_ip)
            else:
                logger.warning("Pod '%s' does not have an ip (yet)'", pod.metadata.name)
        return cert_manager_pods
    except Exception as e:
        logger.error("Failed to get cert manager pods: %s\n%s", str(e), traceback.format_exc())
        return []

class HTTPStatusCounter:
    """Class to track HTTP status code counts for metrics."""
    
    def __init__(self):
        self.counters = {200: 0, 400: 0, 404: 0, 500: 0}
    
    def increment(self, status_code):
        if status_code in self.counters:
            self.counters[status_code] += 1
    
    def get_metrics(self):
        metrics = "# HELP acme_service_dispatcher_requests_total Total number of scrapes by HTTP status code.\n"
        metrics += "# TYPE acme_service_dispatcher_requests_total counter\n"
        for code, count in self.counters.items():
            metrics += f'acme_service_dispatcher_requests_total{{code="{code}"}} {count}\n'
        return metrics.strip()

class BaseRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Base handler with common functionality."""
    
    def log_message(self, format, *args):
        logger.debug(format % args)
    
    def send_error_response(self, status_code, message=None):
        """Send an error response with given status code and message."""
        self.send_response(status_code)
        self.end_headers()
        if message is None:
            message = f"{status_code} Error"
        self.wfile.write(message.encode())
        return status_code

class HealthHandler(BaseRequestHandler):
    
    """Handler for health and metrics endpoints."""
    
    def __init__(self, request, client_address, server):
        if request is None:
            # For testing only
            self.path = None
            return
        super().__init__(request, client_address, server)
    
    status_counter = HTTPStatusCounter()
    
    def do_GET(self):
        if self.path == '/healthz':
            self.handle_health_request()
            return
        
        if self.path == '/metrics':
            self.handle_metrics_request()
            return
        
        logger.error("Invalid path: %s for health check", self.path)
        self.send_error_response(404, "404 Not Found")
        HealthHandler.status_counter.increment(404)
    
    def handle_health_request(self):
        try:
            cert_manager_pods = get_cert_manager_pods()
            if cert_manager_pods:  # Check if list is non-empty
                self.send_response(200)
                self.end_headers()
                logger.debug("Cluster connection is healthy, cert manager pods: %s", cert_manager_pods)
                return
            
            logger.error("Cluster connection is not healthy, no cert manager pods found")
            self.send_error_response(500, "500 Internal Server Error")
            HealthHandler.status_counter.increment(500)
        except Exception as e:
            logger.error("Cluster connection is not healthy: %s\n%s", str(e), traceback.format_exc())
            self.send_error_response(500, "500 Internal Server Error")
            HealthHandler.status_counter.increment(500)
    
    def handle_metrics_request(self):
        metrics = ChallengeHandler.status_counter.get_metrics()
        
        logger.debug("Serving metrics request with response: %s", metrics.encode())
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; version=0.0.4")
        self.end_headers()
        self.wfile.write(metrics.encode())

class TokenCache:
    """Class to manage token-to-pod mapping cache."""
    
    def __init__(self):
        self.cache = {}
        self.last_request_time = 0
    
    def get(self, token):
        """Get pod IP for token if in cache."""
        return self.cache.get(token)
    
    def set(self, token, pod_ip):
        """Set pod IP for token in cache."""
        self.cache[token] = pod_ip
        self.update_timestamp()
    
    def remove(self, token):
        """Remove token from cache."""
        if token in self.cache:
            self.cache.pop(token)
    
    def update_timestamp(self):
        """Update last request timestamp."""
        self.last_request_time = time.time()
    
    def clear_if_stale(self):
        """Clear cache if no requests for CACHE_TIMEOUT_SECONDS."""
        if time.time() - self.last_request_time > CACHE_TIMEOUT_SECONDS:
            self.cache.clear()
            logger.info(f"Cleared cache as no ACME challenge request was received in last {CACHE_TIMEOUT_SECONDS} seconds")

class ChallengeHandler(BaseRequestHandler):
    """Handler for ACME challenge requests."""
    
    token_cache = TokenCache()
    status_counter = HTTPStatusCounter()
    
    def __init__(self, request, client_address, server):
        if request is None:
            # For testing only
            self.path = None
            return
        super().__init__(request, client_address, server)
    
    @classmethod
    def create_without_server(cls):
        """Factory method for creating test instances."""
        return cls(None, None, None)
    
    def do_GET(self):
        logger.info("Received request: %s, Headers: %s", self.path, self.headers)
        
        if not self.path.startswith(ACME_PATH_PREFIX):
            logger.error("Invalid path: %s", self.path)
            self.send_error_response(404, "404 Not Found")
            ChallengeHandler.status_counter.increment(404)
            return
        
        token = self.extract_token()
        host = self.headers.get('Host')
        
        if not token or not host:
            logger.error("Token or host missing in request: %s, Headers: %s", self.path, self.headers)
            self.send_error_response(400, "400 Bad Request")
            ChallengeHandler.status_counter.increment(400)
            return
        
        logger.info("Current cache content: %s", ChallengeHandler.token_cache.cache)
        ChallengeHandler.token_cache.update_timestamp()
        ChallengeHandler.token_cache.clear_if_stale()
        
        pod_ip = ChallengeHandler.token_cache.get(token)
        if pod_ip:
            self.handle_cached_token(token, host, pod_ip)
        else:
            self.handle_new_token(token, host)
    
    def extract_token(self):
        """Extract the token from the request path."""
        if not self.path:
            logger.error("No path provided to extract token from")
            return ''
        return self.path.split('/')[-1]
    
    def handle_new_token(self, token, host):
        """Handle a token that is not in the cache."""
        logger.debug("Request for new token %s for host %s received", token, host)
        cert_manager_pods = get_cert_manager_pods()
        logger.info("Found %s cert manager pods: %s", len(cert_manager_pods), cert_manager_pods)
        
        for pod_ip in cert_manager_pods:
            try:
                response = self.send_request_to_pod(pod_ip, token, host)
                if response and response.status_code == 200:
                    logger.info("Cert manager pod %s returned 200 for token %s", pod_ip, token)
                    ChallengeHandler.token_cache.set(token, pod_ip)
                    return self.send_success_response(response, token, pod_ip)
            except Exception as e:
                logger.error("Error querying pod %s: %s", pod_ip, str(e))
        
        logger.error("None of the cert manager pods returned 200 for token %s. Returning 404", token)
        self.send_error_response(404, "404 Not Found")
        ChallengeHandler.status_counter.increment(404)
    
    def handle_cached_token(self, token, host, pod_ip):
        """Handle a token that is already in the cache."""
        logger.info("Found cert manager pod with IP %s in cache for token %s", pod_ip, token)
        try:
            response = self.send_request_to_pod(pod_ip, token, host)
            if response and response.status_code == 200:
                return self.send_success_response(response, token, pod_ip)
            
            # Remove from cache if response is not 200
            ChallengeHandler.token_cache.remove(token)
            logger.error(
                "Cert manager pod '%s' did not return 200 for token %s: %s. Removed from cache",
                pod_ip, token, response.status_code if response else 'No response'
            )
            self.send_error_response(404, "404 Not Found")
            ChallengeHandler.status_counter.increment(404)
        except Exception as e:
            logger.error("Error with cached pod %s: %s", pod_ip, str(e))
            ChallengeHandler.token_cache.remove(token)
            self.send_error_response(500, "500 Internal Server Error")
            ChallengeHandler.status_counter.increment(500)
    
    def send_request_to_pod(self, pod_ip, token, host):
        """Send a request to a cert manager pod."""
        url = f"http://{pod_ip}:{CHALLENGE_PORT}{ACME_PATH_PREFIX}{token}"
        headers = {'Host': host, 'User-Agent': 'acme-challenge-dispatcher'}
        try:
            response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT_SECONDS)
            return response
        except requests.exceptions.Timeout:
            logger.error("Timeout while sending request to ACME pod %s", pod_ip)
            return None
        except requests.RequestException as e:
            logger.error("Error while sending request to ACME pod %s: %s\n%s",
                     pod_ip, str(e), traceback.format_exc())
            ChallengeHandler.status_counter.increment(500)
            return None
    
    def send_success_response(self, response, token, pod_ip):
        """Send a successful response back to the client."""
        self.send_response(200)
        self.end_headers()
        self.wfile.write(response.content)
        logger.info("Successfully wrote response for token %s from cert manager pod %s", 
                 token, pod_ip)
        ChallengeHandler.status_counter.increment(200)

class ThreadingHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    """Threaded HTTP server for handling concurrent requests."""
    daemon_threads = True

def run_server():
    """Run the health and challenge servers."""
    logger.info("Serving health checks on port %d", HEALTH_PORT)
    health_server = ThreadingHTTPServer(("0.0.0.0", HEALTH_PORT), HealthHandler)
    
    logger.info("Serving acme challenges on port %d with label selector '%s'", 
               CHALLENGE_PORT, LABEL_SELECTOR)
    challenge_server = ThreadingHTTPServer(("0.0.0.0", CHALLENGE_PORT), ChallengeHandler)
    
    def gracefully_shutdown_hook(signum, frame):
        """Shutdown both servers gracefully."""
        logger.info("Received shutdown signal, shutting down servers...")
        health_server_thread = threading.Thread(target=health_server.shutdown)
        challenge_server_thread = threading.Thread(target=challenge_server.shutdown)
        
        health_server_thread.start()
        challenge_server_thread.start()
        
        # Wait for both shutdown threads to complete
        health_server_thread.join(timeout=5)
        challenge_server_thread.join(timeout=5)
        logger.info("Servers shut down successfully")
    
    signal.signal(signal.SIGTERM, gracefully_shutdown_hook)
    
    # Start both servers in their own threads
    health_thread = threading.Thread(target=health_server.serve_forever)
    challenge_thread = threading.Thread(target=challenge_server.serve_forever)
    
    health_thread.daemon = True
    challenge_thread.daemon = True
    
    health_thread.start()
    challenge_thread.start()
    
    # Keep the main thread alive
    while True:
        time.sleep(1)

if __name__ == '__main__':
    run_server()