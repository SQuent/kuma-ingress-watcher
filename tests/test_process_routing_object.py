import unittest
from unittest.mock import patch, call
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

    @patch("kuma_ingress_watcher.controller.create_or_update_monitor")
    @patch("kuma_ingress_watcher.controller.delete_monitor")
    def test_process_routing_object_disabled_deletes_all_suffixed_monitors(
        self, mock_delete_monitor, mock_create_or_update_monitor
    ):
        # An object with multiple routes/hosts that gets disabled via
        # annotation must clean up every suffixed monitor it previously
        # created (name-namespace-1, name-namespace-2, ...), not just the
        # unsuffixed base name. See
        # https://github.com/SQuent/kuma-ingress-watcher/issues/60
        item = {
            "metadata": {
                "name": "test",
                "namespace": "default",
                "annotations": {
                    "uptime-kuma.autodiscovery.probe.enabled": "false"
                },
            },
            "spec": {
                "routes": [
                    {"match": "Host(`example.com`)"},
                    {"match": "Host(`example.org`)"},
                ]
            },
        }
        type_obj = "IngressRoute"

        process_routing_object(item, type_obj)

        mock_create_or_update_monitor.assert_not_called()
        mock_delete_monitor.assert_has_calls(
            [call("test-default-1"), call("test-default-2")], any_order=True
        )
        self.assertEqual(mock_delete_monitor.call_count, 2)


if __name__ == "__main__":
    unittest.main()
