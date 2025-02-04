import unittest
from unittest.mock import patch, MagicMock
from kuma_ingress_watcher.controller import get_ingress


class TestGetIngress(unittest.TestCase):
    @patch("kuma_ingress_watcher.controller.logger", spec=True)
    @patch("kuma_ingress_watcher.controller.networking_api_instance")
    def test_get_ingress_success(self, mock_api_instance, mock_logger):
        # Mock an ingress object with a 'to_dict' method
        mock_ingress = MagicMock()
        mock_ingress.to_dict.return_value = {"metadata": {"name": "test-ingress"}}

        # Set the mocked 'items' list to contain the mocked ingress object
        mock_api_instance.list_ingress_for_all_namespaces.return_value.items = [
            mock_ingress
        ]

        # Call the function
        result = get_ingress(mock_api_instance)

        # Expected result after calling 'to_dict' on the ingress object
        expected_result = {"items": [{"metadata": {"name": "test-ingress"}}]}

        # Assert the function's result matches the expected result
        self.assertEqual(result, expected_result)
        mock_logger.error.assert_not_called()

    @patch("kuma_ingress_watcher.controller.logger", spec=True)
    @patch("kuma_ingress_watcher.controller.networking_api_instance")
    def test_get_ingress_failure(self, mock_api_instance, mock_logger):
        # Simulate an exception when calling list_ingress_for_all_namespaces
        mock_api_instance.list_ingress_for_all_namespaces.side_effect = Exception(
            "Failed to get Ingress"
        )

        result = get_ingress(mock_api_instance)

        # Verify that in case of an exception, an empty list is returned
        self.assertEqual(result, {"items": []})
        mock_logger.error.assert_called_once_with(
            "Failed to get Ingress: Failed to get Ingress"
        )


if __name__ == "__main__":
    unittest.main()
