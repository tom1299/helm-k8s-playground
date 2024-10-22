import requests
import unittest
from acme_challenge_dispatcher import AcmeChallengeDispatcher

from unittest.mock import MagicMock, patch

class TestAcmeChallengeDispatcher(unittest.TestCase):

    def setUp(self):
        self.dispatcher = AcmeChallengeDispatcher.create_without_server()
        AcmeChallengeDispatcher.api_client = None
        AcmeChallengeDispatcher.acme_clients_cache = {}

    def test_extract_token_valid_path(self):
        path = '/.well-known/acme-challenge/JHb54aT_KTXBWQOzGYkt9A'
        expected_token = 'JHb54aT_KTXBWQOzGYkt9A'
        token = self.dispatcher.extract_token(path)
        self.assertEqual(token, expected_token)

    def test_extract_token_empty_path(self):
        path = ''
        expected_token = ''
        token = self.dispatcher.extract_token(path)
        self.assertEqual(token, expected_token)

    def test_extract_token_no_token(self):
        path = '/.well-known/acme-challenge/'
        expected_token = ''
        token = self.dispatcher.extract_token(path)
        self.assertEqual(token, expected_token)

    def test_extract_token_no_acme_challenge(self):
        path = '/some/other/path'
        expected_token = 'path'
        token = self.dispatcher.extract_token(path)
        self.assertEqual(token, expected_token)

    def test_extract_token_special_characters(self):
        path = '/.well-known/acme-challenge/token-with-special-characters-!@#$%^&*()'
        expected_token = 'token-with-special-characters-!@#$%^&*()'
        token = self.dispatcher.extract_token(path)
        self.assertEqual(token, expected_token)

    def test_extract_token_none_path(self):
        path = None
        expected_token = ''
        token = self.dispatcher.extract_token(path)
        self.assertEqual(token, expected_token)

    @patch('requests.get')
    def test_send_request_to_acme_client_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b'valid response'
        mock_get.return_value = mock_response

        client_ip = '192.168.1.1'
        token = 'JHb54aT_KTXBWQOzGYkt9A'
        host = 'example.com'
        response = self.dispatcher.send_request_to_acme_client(client_ip, token, host)

        self.assertIsNotNone(response)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'valid response')

    @patch('requests.get')
    def test_send_request_to_acme_client_failure(self, mock_get):
        mock_get.side_effect = requests.RequestException("Request failed")

        client_ip = '192.168.1.1'
        token = 'JHb54aT_KTXBWQOzGYkt9A'
        host = 'example.com'
        response = self.dispatcher.send_request_to_acme_client(client_ip, token, host)

        self.assertIsNone(response)

    @patch('acme_challenge_dispatcher.get_api_client')
    def test_get_acme_clients_with_pods(self, mock_get_api_client):
        mock_v1 = MagicMock()
        mock_get_api_client.return_value = mock_v1
        mock_v1.list_namespaced_pod.return_value.items = [
            MagicMock(status=MagicMock(pod_ip='192.168.1.1')),
            MagicMock(status=MagicMock(pod_ip='192.168.1.2'))
        ]

        acme_clients = self.dispatcher.get_acme_clients()
        self.assertEqual(acme_clients, ['192.168.1.1', '192.168.1.2'])

    @patch('acme_challenge_dispatcher.get_api_client')
    def test_get_acme_clients_with_no_pods(self, mock_get_api_client):
        mock_v1 = MagicMock()
        mock_get_api_client.return_value = mock_v1
        mock_v1.list_namespaced_pod.return_value.items = []

        acme_clients = self.dispatcher.get_acme_clients()
        self.assertEqual(acme_clients, [])

    @patch('acme_challenge_dispatcher.get_api_client')
    def test_get_acme_clients_with_none(self, mock_get_api_client):
        mock_v1 = MagicMock()
        mock_get_api_client.return_value = mock_v1
        mock_v1.list_namespaced_pod.return_value = None

        acme_clients = self.dispatcher.get_acme_clients()
        self.assertEqual(acme_clients, [])

if __name__ == '__main__':
    unittest.main()