import unittest
from unittest.mock import patch, MagicMock
from kuma_ingress_watcher.controller import process_multiple_routes
import os 
class TestProcessMultipleRoutes(unittest.TestCase):
    @patch.dict(os.environ, {
        'UPTIME_KUMA_URL': 'https://example.com',
        'UPTIME_KUMA_USER': 'user',
        'UPTIME_KUMA_PASSWORD': 'password'
    })
    @patch('kuma_ingress_watcher.controller.create_or_update_monitor')
    def test_process_multiple_routes(self, mock_create_or_update_monitor):
        routes = [{'match': 'Host(`example.com`)'}, {'match': 'Host(`example.org`)'}]
        process_multiple_routes('test-monitor', routes, 60, 'http', None, None, 'GET')
        
        self.assertEqual(mock_create_or_update_monitor.call_count, 2)
        
        mock_create_or_update_monitor.assert_any_call('test-monitor-1', 'https://example.com', 60, 'http', None, 'GET')
        
        mock_create_or_update_monitor.assert_any_call('test-monitor-2', 'https://example.org', 60, 'http', None, 'GET')

if __name__ == '__main__':
    unittest.main()
