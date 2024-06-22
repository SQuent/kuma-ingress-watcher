import unittest
from unittest.mock import patch, MagicMock
from kuma_ingress_watcher.controller import process_single_route
import os

class TestProcessSingleRoute(unittest.TestCase):
    @patch.dict(os.environ, {
        'UPTIME_KUMA_URL': 'https://example.com',
        'UPTIME_KUMA_USER': 'user',
        'UPTIME_KUMA_PASSWORD': 'password'
    })
    @patch('kuma_ingress_watcher.controller.create_or_update_monitor')
    def test_process_single_route(self, mock_create_or_update_monitor):
        route = {'match': 'Host(`example.com`)'}
        process_single_route('test-monitor', route, 60, 'http', None, None, 'GET')
        mock_create_or_update_monitor.assert_called_once_with('test-monitor', 'https://example.com', 60, 'http', None, 'GET')

if __name__ == '__main__':
    unittest.main()
