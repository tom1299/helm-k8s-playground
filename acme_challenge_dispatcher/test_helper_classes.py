import unittest
import time
from unittest.mock import MagicMock
from acme_challenge_dispatcher import TokenCache, HTTPStatusCounter, CACHE_TIMEOUT_SECONDS

class TestTokenCache(unittest.TestCase):
    
    def setUp(self):
        self.cache = TokenCache()
    
    def test_get_nonexistent_token(self):
        """Test getting a token that doesn't exist in the cache."""
        self.assertIsNone(self.cache.get("nonexistent_token"))
    
    def test_set_and_get_token(self):
        """Test setting and getting a token."""
        self.cache.set("test_token", "192.168.1.1")
        self.assertEqual(self.cache.get("test_token"), "192.168.1.1")
    
    def test_update_timestamp(self):
        """Test that update_timestamp updates the last_request_time."""
        old_time = self.cache.last_request_time
        time.sleep(0.001)  # Ensure time has changed
        self.cache.update_timestamp()
        self.assertGreater(self.cache.last_request_time, old_time)
    
    def test_set_updates_timestamp(self):
        """Test that set() also updates the timestamp."""
        old_time = self.cache.last_request_time
        time.sleep(0.001)  # Ensure time has changed
        self.cache.set("test_token", "192.168.1.1")
        self.assertGreater(self.cache.last_request_time, old_time)
    
    def test_remove_token(self):
        """Test removing a token from the cache."""
        self.cache.set("test_token", "192.168.1.1")
        self.assertEqual(self.cache.get("test_token"), "192.168.1.1")
        
        self.cache.remove("test_token")
        self.assertIsNone(self.cache.get("test_token"))
    
    def test_remove_nonexistent_token(self):
        """Test removing a token that doesn't exist."""
        # Should not raise an exception
        self.cache.remove("nonexistent_token")
    
    def test_clear_if_stale_when_stale(self):
        """Test that clear_if_stale clears the cache when it's stale."""
        self.cache.set("test_token", "192.168.1.1")
        
        # Manually set last_request_time to be older than the timeout
        self.cache.last_request_time = time.time() - (CACHE_TIMEOUT_SECONDS + 1)
        
        self.cache.clear_if_stale()
        self.assertIsNone(self.cache.get("test_token"))
        self.assertEqual(len(self.cache.cache), 0)
    
    def test_clear_if_stale_when_fresh(self):
        """Test that clear_if_stale doesn't clear the cache when it's fresh."""
        self.cache.set("test_token", "192.168.1.1")
        
        # Last request time is recent, so cache should not be cleared
        self.cache.clear_if_stale()
        self.assertEqual(self.cache.get("test_token"), "192.168.1.1")
        self.assertEqual(len(self.cache.cache), 1)

class TestHTTPStatusCounter(unittest.TestCase):
    
    def setUp(self):
        self.counter = HTTPStatusCounter()
    
    def test_initial_counters(self):
        """Test that counters are initialized with zeros."""
        expected = {200: 0, 400: 0, 404: 0, 500: 0}
        self.assertEqual(self.counter.counters, expected)
    
    def test_increment_existing_status(self):
        """Test incrementing existing status codes."""
        self.counter.increment(200)
        self.assertEqual(self.counter.counters[200], 1)
        
        self.counter.increment(200)
        self.assertEqual(self.counter.counters[200], 2)
        
        self.counter.increment(404)
        self.assertEqual(self.counter.counters[404], 1)
    
    def test_increment_nonexistent_status(self):
        """Test incrementing a status code that isn't tracked."""
        # Should not affect counters
        self.counter.increment(302)
        expected = {200: 0, 400: 0, 404: 0, 500: 0}
        self.assertEqual(self.counter.counters, expected)
    
    def test_get_metrics_format(self):
        """Test the metrics formatting."""
        self.counter.counters = {200: 5, 400: 2, 404: 10, 500: 1}
        metrics = self.counter.get_metrics()
        
        # Check that metrics contains the expected lines
        self.assertIn('acme_service_dispatcher_requests_total{code="200"} 5', metrics)
        self.assertIn('acme_service_dispatcher_requests_total{code="400"} 2', metrics)
        self.assertIn('acme_service_dispatcher_requests_total{code="404"} 10', metrics)
        self.assertIn('acme_service_dispatcher_requests_total{code="500"} 1', metrics)
        
        # Check that the HELP and TYPE comments are included
        self.assertIn('# HELP acme_service_dispatcher_requests_total', metrics)
        self.assertIn('# TYPE acme_service_dispatcher_requests_total counter', metrics)

class TestBaseRequestHandler(unittest.TestCase):
    
    def setUp(self):
        from acme_challenge_dispatcher import BaseRequestHandler
        
        # Create a test instance that inherits from BaseRequestHandler
        class TestHandler(BaseRequestHandler):
            def __init__(self):
                self.response_code = None
                self.headers_sent = False
                self.response_body = None
                self.wfile = MagicMock()
            
            def send_response(self, code):
                self.response_code = code
            
            def end_headers(self):
                self.headers_sent = True
        
        self.handler = TestHandler()
    
    def test_send_error_response_with_custom_message(self):
        """Test sending an error response with a custom message."""
        self.handler.send_error_response(404, "Custom Not Found")
        
        self.assertEqual(self.handler.response_code, 404)
        self.assertTrue(self.handler.headers_sent)
        self.handler.wfile.write.assert_called_once_with(b"Custom Not Found")
    
    def test_send_error_response_with_default_message(self):
        """Test sending an error response with the default message."""
        self.handler.send_error_response(500)
        
        self.assertEqual(self.handler.response_code, 500)
        self.assertTrue(self.handler.headers_sent)
        self.handler.wfile.write.assert_called_once_with(b"500 Error")

if __name__ == '__main__':
    unittest.main()