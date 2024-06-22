import unittest
from unittest.mock import patch, MagicMock
from kuma_ingress_watcher.controller import process_ingressroutes

class TestProcessIngressroutes(unittest.TestCase):
    @patch('kuma_ingress_watcher.controller.process_single_route')
    def test_process_ingressroutes_single_route(self, mock_process_single_route):
        item = {
            'metadata': {'name': 'test', 'namespace': 'default', 'annotations': {}},
            'spec': {'routes': [{'match': 'Host(`example.com`)'}]}
        }
        process_ingressroutes(item)
        mock_process_single_route.assert_called_once()

    @patch('kuma_ingress_watcher.controller.process_multiple_routes')
    def test_process_ingressroutes_multiple_routes(self, mock_process_multiple_routes):
        item = {
            'metadata': {'name': 'test', 'namespace': 'default', 'annotations': {}},
            'spec': {'routes': [{'match': 'Host(`example.com`)'}, {'match': 'Host(`example.org`)'}]}
        }
        process_ingressroutes(item)
        mock_process_multiple_routes.assert_called_once()

if __name__ == '__main__':
    unittest.main()
