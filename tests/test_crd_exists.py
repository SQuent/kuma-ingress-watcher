import unittest
from unittest.mock import patch, MagicMock
from kuma_ingress_watcher.controller import crd_exists
from kubernetes.client.rest import ApiException

class TestCrdExists(unittest.TestCase):
    @patch('kuma_ingress_watcher.controller.client.ApiextensionsV1Api')
    @patch('kuma_ingress_watcher.controller.logger')
    def test_crd_exists_true(self, mock_logger, MockApiExtensionsV1Api):
        mock_api_instance = MockApiExtensionsV1Api.return_value
        # Mocking successful read_custom_resource_definition
        mock_api_instance.read_custom_resource_definition.return_value = MagicMock()
        
        result = crd_exists('group', 'version', 'plural')
        
        self.assertTrue(result)
        mock_api_instance.read_custom_resource_definition.assert_called_once_with('plural.group')
        mock_logger.assert_not_called()  # No error should be logged

    @patch('kuma_ingress_watcher.controller.client.ApiextensionsV1Api')
    @patch('kuma_ingress_watcher.controller.logger')
    def test_crd_exists_false_not_found(self, mock_logger, MockApiExtensionsV1Api):
        mock_api_instance = MockApiExtensionsV1Api.return_value
        # Mocking ApiException with status 404
        mock_api_instance.read_custom_resource_definition.side_effect = ApiException(status=404)
        
        result = crd_exists('group', 'version', 'plural')
        
        self.assertFalse(result)
        mock_api_instance.read_custom_resource_definition.assert_called_once_with('plural.group')
        mock_logger.error.assert_not_called()  # No error should be logged for 404

    @patch('kuma_ingress_watcher.controller.client.ApiextensionsV1Api')
    @patch('kuma_ingress_watcher.controller.logger')
    def test_crd_exists_false_api_exception(self, mock_logger, MockApiExtensionsV1Api):
        mock_api_instance = MockApiExtensionsV1Api.return_value
        # Mocking ApiException with status 500 (or any other non-404 status)
        mock_api_instance.read_custom_resource_definition.side_effect = ApiException(status=500)
        
        result = crd_exists('group', 'version', 'plural')
        
        self.assertFalse(result)
        mock_api_instance.read_custom_resource_definition.assert_called_once_with('plural.group')
        mock_logger.error.assert_called_once()  # Error should be logged for other ApiException cases

if __name__ == '__main__':
    unittest.main()
