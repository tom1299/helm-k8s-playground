import unittest
from unittest.mock import MagicMock, patch, call
import time
import threading

from acme_challenge_dispatcher import (
    HealthHandler, 
    run_server, 
    ThreadingHTTPServer,
    HEALTH_PORT,
    CHALLENGE_PORT
)

class TestThreadingHTTPServer(unittest.TestCase):
    
    def test_daemon_threads(self):
        """Test that daemon_threads is set to True."""
        self.assertTrue(ThreadingHTTPServer.daemon_threads)

class TestRunServer(unittest.TestCase):
    
    @patch('acme_challenge_dispatcher.ThreadingHTTPServer')
    @patch('acme_challenge_dispatcher.threading.Thread')
    @patch('acme_challenge_dispatcher.signal.signal')
    @patch('acme_challenge_dispatcher.time.sleep')
    def test_run_server_initialization(self, mock_sleep, mock_signal, mock_thread, mock_server):
        """Test server initialization and thread creation."""
        # Mock time.sleep to raise an exception after first call to break the infinite loop
        mock_sleep.side_effect = [None, KeyboardInterrupt]
        
        # Create mock servers
        mock_health_server = MagicMock()
        mock_challenge_server = MagicMock()
        mock_server.side_effect = [mock_health_server, mock_challenge_server]
        
        # Create mock threads
        mock_health_thread = MagicMock()
        mock_challenge_thread = MagicMock()
        mock_thread.side_effect = [mock_health_thread, mock_challenge_thread]
        
        # Run the server function and catch the expected KeyboardInterrupt
        try:
            run_server()
        except KeyboardInterrupt:
            pass
        
        # Assert ThreadingHTTPServer was initialized properly
        self.assertEqual(mock_server.call_count, 2)
        mock_server.assert_has_calls([
            call(("0.0.0.0", HEALTH_PORT), HealthHandler),
            call(("0.0.0.0", CHALLENGE_PORT), unittest.mock.ANY)  # Challenge handler
        ])
        
        # Assert threads were created and started
        self.assertEqual(mock_thread.call_count, 2)
        mock_thread.assert_has_calls([
            call(target=mock_health_server.serve_forever),
            call(target=mock_challenge_server.serve_forever)
        ])
        
        # Assert both threads were started
        mock_health_thread.daemon = True
        mock_challenge_thread.daemon = True
        mock_health_thread.start.assert_called_once()
        mock_challenge_thread.start.assert_called_once()
        
        # Assert signal was registered
        mock_signal.assert_called_once()

    @patch('acme_challenge_dispatcher.ThreadingHTTPServer')
    @patch('acme_challenge_dispatcher.threading.Thread')
    @patch('acme_challenge_dispatcher.signal.signal')
    def test_graceful_shutdown(self, mock_signal, mock_thread, mock_server):
        """Test the graceful shutdown hook."""
        # Create mock servers
        mock_health_server = MagicMock()
        mock_challenge_server = MagicMock()
        mock_server.side_effect = [mock_health_server, mock_challenge_server]
        
        # Capture the shutdown hook
        shutdown_hook = None
        def capture_hook(sig, hook):
            nonlocal shutdown_hook
            shutdown_hook = hook
        mock_signal.side_effect = capture_hook
        
        # Run the server initialization (but don't actually run the infinite loop)
        with patch('acme_challenge_dispatcher.time.sleep', side_effect=KeyboardInterrupt):
            try:
                run_server()
            except KeyboardInterrupt:
                pass
        
        # Reset the mocks for our test
        mock_thread.reset_mock()
        
        # Create mock threads for shutdown
        mock_health_thread = MagicMock()
        mock_challenge_thread = MagicMock()
        mock_thread.side_effect = [mock_health_thread, mock_challenge_thread]
        
        # Call the shutdown hook
        self.assertIsNotNone(shutdown_hook)
        shutdown_hook(None, None)
        
        # Assert shutdown threads were created and started
        self.assertEqual(mock_thread.call_count, 2)
        mock_thread.assert_has_calls([
            call(target=mock_health_server.shutdown),
            call(target=mock_challenge_server.shutdown)
        ])
        
        # Assert join was called on both threads
        mock_health_thread.start.assert_called_once()
        mock_challenge_thread.start.assert_called_once()
        mock_health_thread.join.assert_called_once()
        mock_challenge_thread.join.assert_called_once()

class TestHealthHandler(unittest.TestCase):
    
    def setUp(self):
        # Create a test instance that doesn't call super().__init__
        self.handler = HealthHandler(None, None, None)
        self.handler.send_response = MagicMock()
        self.handler.end_headers = MagicMock()
        self.handler.send_header = MagicMock()
        self.handler.wfile = MagicMock()
        self.handler.send_error_response = MagicMock()
    
    def test_do_GET_invalid_path(self):
        """Test invalid path handling."""
        self.handler.path = '/invalid'
        self.handler.do_GET()
        self.handler.send_error_response.assert_called_once()
    
    @patch('acme_challenge_dispatcher.get_cert_manager_pods')
    def test_health_request_healthy(self, mock_get_pods):
        """Test health request when system is healthy."""
        mock_get_pods.return_value = ['192.168.1.1']
        self.handler.path = '/healthz'
        self.handler.do_GET()
        self.handler.send_response.assert_called_with(200)
        self.handler.send_error_response.assert_not_called()
    
    @patch('acme_challenge_dispatcher.get_cert_manager_pods')
    def test_health_request_unhealthy_no_pods(self, mock_get_pods):
        """Test health request when no pods are found."""
        mock_get_pods.return_value = []
        self.handler.path = '/healthz'
        self.handler.do_GET()
        self.handler.send_error_response.assert_called_once()
    
    @patch('acme_challenge_dispatcher.get_cert_manager_pods')
    def test_health_request_exception(self, mock_get_pods):
        """Test health request when an exception occurs."""
        mock_get_pods.side_effect = Exception("Test exception")
        self.handler.path = '/healthz'
        self.handler.do_GET()
        self.handler.send_error_response.assert_called_once()
    
    @patch('acme_challenge_dispatcher.ChallengeHandler.status_counter.get_metrics')
    def test_metrics_request(self, mock_get_metrics):
        """Test metrics request."""
        mock_get_metrics.return_value = "metrics_data"
        self.handler.path = '/metrics'
        self.handler.do_GET()
        self.handler.send_response.assert_called_with(200)
        self.handler.send_header.assert_called_with("Content-Type", "text/plain; version=0.0.4")
        self.handler.wfile.write.assert_called_once()

if __name__ == '__main__':
    unittest.main()