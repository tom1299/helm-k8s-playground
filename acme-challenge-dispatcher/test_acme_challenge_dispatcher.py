import requests
import unittest
import acme_challenge_dispatcher

from unittest.mock import MagicMock, patch

class TestAcmeChallengeDispatcher(unittest.TestCase):

    def setUp(self):
        self.dispatcher = acme_challenge_dispatcher.AcmeChallengeDispatcher

    def test_extract_token_valid_path(self):
        path = '/.well-known/acme-challenge/JHb54aT_KTXBWQOzGYkt9A'
        expected_token = 'JHb54aT_KTXBWQOzGYkt9A'
        token = self.dispatcher.extract_token(self.dispatcher, path)
        self.assertEqual(token, expected_token)

    def test_extract_token_empty_path(self):
        path = ''
        expected_token = ''
        token = self.dispatcher.extract_token(self.dispatcher, path)
        self.assertEqual(token, expected_token)

    def test_extract_token_no_token(self):
        path = '/.well-known/acme-challenge/'
        expected_token = ''
        token = self.dispatcher.extract_token(self.dispatcher, path)
        self.assertEqual(token, expected_token)

    def test_extract_token_no_acme_challenge(self):
        path = '/some/other/path'
        expected_token = 'path'
        token = self.dispatcher.extract_token(self.dispatcher, path)
        self.assertEqual(token, expected_token)

    def test_extract_token_special_characters(self):
        path = '/.well-known/acme-challenge/token-with-special-characters-!@#$%^&*()'
        expected_token = 'token-with-special-characters-!@#$%^&*()'
        token = self.dispatcher.extract_token(self.dispatcher, path)
        self.assertEqual(token, expected_token)

    def test_extract_token_none_path(self):
        path = None
        expected_token = ''
        token = self.dispatcher.extract_token(self.dispatcher, path)
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
        response = self.dispatcher.send_request_to_acme_client(self.dispatcher, client_ip, token, host)

        self.assertIsNotNone(response)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'valid response')

    @patch('requests.get')
    def test_send_request_to_acme_client_failure(self, mock_get):
        mock_get.side_effect = requests.RequestException("Request failed")

        client_ip = '192.168.1.1'
        token = 'JHb54aT_KTXBWQOzGYkt9A'
        host = 'example.com'
        response = self.dispatcher.send_request_to_acme_client(self.dispatcher, client_ip, token, host)

        self.assertIsNone(response)

if __name__ == '__main__':
    unittest.main()