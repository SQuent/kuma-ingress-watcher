import unittest
from unittest.mock import patch
from kuma_ingress_watcher.controller import process_routing_object


class TestProcessRoutingObject(unittest.TestCase):
    @patch("kuma_ingress_watcher.controller.create_or_update_monitor")
    @patch("kuma_ingress_watcher.controller.delete_monitor")
    def test_process_routing_object_single_route(
        self, mock_delete_monitor, mock_create_or_update_monitor
    ):
        # Define the test item with a single route
        item = {
            "metadata": {"name": "test", "namespace": "default", "annotations": {}},
            "spec": {"routes": [{"match": "Host(`example.com`)"}]},
        }
        type_obj = "IngressRoute"

        # Call the function under test
        process_routing_object(item, type_obj)

        # Check that create_or_update_monitor was called
        mock_create_or_update_monitor.assert_called()
        self.assertEqual(mock_create_or_update_monitor.call_count, 1)
        # Verify that delete_monitor was not called
        mock_delete_monitor.assert_not_called()

    @patch("kuma_ingress_watcher.controller.create_or_update_monitor")
    @patch("kuma_ingress_watcher.controller.delete_monitor")
    def test_process_routing_object_multiple_routes(
        self, mock_delete_monitor, mock_create_or_update_monitor
    ):
        # Define the test item with multiple routes
        item = {
            "metadata": {"name": "test", "namespace": "default", "annotations": {}},
            "spec": {
                "routes": [
                    {"match": "Host(`example.com`)"},
                    {"match": "Host(`example.org`)"},
                ]
            },
        }
        type_obj = "IngressRoute"

        # Call the function under test
        process_routing_object(item, type_obj)

        # Check that create_or_update_monitor was called for each route
        self.assertEqual(mock_create_or_update_monitor.call_count, 2)
        # Verify that delete_monitor was not called
        mock_delete_monitor.assert_not_called()

    @patch("kuma_ingress_watcher.controller.create_or_update_monitor")
    @patch("kuma_ingress_watcher.controller.delete_monitor")
    def test_process_routing_object_empty(
        self, mock_delete_monitor, mock_create_or_update_monitor
    ):
        # Define the test item with no routes
        item = {
            "metadata": {"name": "test", "namespace": "default", "annotations": {}},
            "spec": {"routes": []},
        }
        type_obj = "IngressRoute"

        # Call the function under test
        process_routing_object(item, type_obj)

        # Verify that create_or_update_monitor was not called
        mock_create_or_update_monitor.assert_not_called()
        # Verify that delete_monitor was not called
        mock_delete_monitor.assert_not_called()


if __name__ == "__main__":
    unittest.main()
