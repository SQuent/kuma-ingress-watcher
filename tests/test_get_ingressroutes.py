import unittest
from unittest.mock import patch, MagicMock
from kuma_ingress_watcher.controller import get_ingressroutes


class TestGetIngressroutes(unittest.TestCase):
    @patch('kuma_ingress_watcher.controller.logger', spec=True)
    @patch('kuma_ingress_watcher.controller.custom_api_instance')
    def test_get_ingressroutes_success(self, mock_api_instance, mock_logger):
        # Mock an ingressroute object with a 'to_dict' method
        mock_ingressroute = MagicMock()
        mock_ingressroute.to_dict.return_value = {'metadata': {'name': 'test-ingressroute'}}

        # Mock the API response to include the mocked ingressroute
        mock_api_instance.list_cluster_custom_object.return_value = {
            'items': [mock_ingressroute.to_dict()]
        }

        # Call the function
        result = get_ingressroutes(mock_api_instance)

        # Assert we call list_cluster_custom_object with expected group
        mock_api_instance.list_cluster_custom_object.assert_called_with(group='traefik.containo.us',
                                                                        version='v1alpha1',
                                                                        plural='ingressroutes')

        # Expected result after calling 'to_dict' on the ingressroute object
        expected_result = {'items': [{'metadata': {'name': 'test-ingressroute'}}]}

        # Assert the function's result matches the expected result
        self.assertEqual(result, expected_result)
        mock_logger.error.assert_not_called()

    @patch('kuma_ingress_watcher.controller.logger', spec=True)
    @patch('kuma_ingress_watcher.controller.custom_api_instance')
    def test_get_ingressroutes_failure(self, mock_api_instance, mock_logger):
        # Simulate an exception when calling list_cluster_custom_object
        mock_api_instance.list_cluster_custom_object.side_effect = Exception('Failed to get ingressroutes')

        result = get_ingressroutes(mock_api_instance)

        # Verify that in case of an exception, an empty list is returned
        self.assertEqual(result, {'items': []})
        mock_logger.error.assert_called_once_with('Failed to get ingressroutes: Failed to get ingressroutes')

    @patch('kuma_ingress_watcher.controller.logger', spec=True)
    @patch('kuma_ingress_watcher.controller.custom_api_instance')
    def test_get_ingressroutes_empty(self, mock_api_instance, mock_logger):
        # Simulate an empty response from the API
        mock_api_instance.list_cluster_custom_object.return_value = {'items': []}

        result = get_ingressroutes(mock_api_instance)

        # Verify that an empty list is returned when there are no ingressroutes
        self.assertEqual(result, {'items': []})
        mock_logger.error.assert_not_called()

    @patch('kuma_ingress_watcher.controller.custom_api_instance')
    @patch('kuma_ingress_watcher.controller.USE_TRAEFIK_V3_CRD_GROUP', True)
    def test_get_ingressroutes_traefik_v3_crd(self, mock_api_instance):
        mock_ingressroute = MagicMock()
        mock_ingressroute.to_dict.return_value = {'metadata': {'name': 'test-ingressroute'}}

        # Mock the API response to include the mocked ingressroute
        mock_api_instance.list_cluster_custom_object.return_value = {
            'items': [mock_ingressroute.to_dict()]
        }

        get_ingressroutes(mock_api_instance)

        # Assert we call list_cluster_custom_object with expected group
        mock_api_instance.list_cluster_custom_object.assert_called_with(group='traefik.io',
                                                                        version='v1alpha1',
                                                                        plural='ingressroutes')


if __name__ == '__main__':
    unittest.main()
