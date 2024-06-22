import unittest
from unittest.mock import patch, MagicMock
from kuma_ingress_watcher.controller import get_ingressroutes

class TestGetIngressroutes(unittest.TestCase):
    @patch('kuma_ingress_watcher.controller.logger', spec=True)
    @patch('kuma_ingress_watcher.controller.api_instance')
    def test_get_ingressroutes_success(self, mock_api_instance, mock_logger):
        mock_api_instance.list_cluster_custom_object.return_value = {'items': [{'metadata': {'name': 'test'}}]}
        
        result = get_ingressroutes(mock_api_instance)
        
        self.assertEqual(result, {'items': [{'metadata': {'name': 'test'}}]})
        mock_logger.error.assert_not_called()

    @patch('kuma_ingress_watcher.controller.logger', spec=True)
    @patch('kuma_ingress_watcher.controller.api_instance')
    def test_get_ingressroutes_failure(self, mock_api_instance, mock_logger):
        mock_api_instance.list_cluster_custom_object.side_effect = Exception('Failed to get ingressroutes')
        
        result = get_ingressroutes(mock_api_instance)
        
        self.assertEqual(result, {'items': []})
        mock_logger.error.assert_called_once_with('Failed to get ingressroutes: Failed to get ingressroutes')

if __name__ == '__main__':
    unittest.main()
