import unittest
from unittest.mock import patch, call
from kuma_ingress_watcher.controller import handle_changes


class TestHandleChanges(unittest.TestCase):
    @patch("kuma_ingress_watcher.controller.process_routing_object")
    @patch("kuma_ingress_watcher.controller.delete_monitor")
    @patch("kuma_ingress_watcher.controller.ingressroute_changed")
    @patch("kuma_ingress_watcher.controller.logger", spec=True)
    def test_handle_changes(
        self,
        mock_logger,
        mock_ingressroute_changed,
        mock_delete_monitor,
        mock_process_routing_object,
    ):
        # Define previous and current items. test2 has a single rule/host, so it
        # is expected to produce a single, unsuffixed monitor name.
        previous_items = {
            "test1": {
                "metadata": {"name": "test1", "namespace": "default"},
                "spec": {"rules": [{"host": "test1.example.com"}]},
            },
            "test2": {
                "metadata": {"name": "test2", "namespace": "default"},
                "spec": {"rules": [{"host": "test2.example.com"}]},
            },
        }
        current_items = {
            "test1": {
                "metadata": {"name": "test1", "namespace": "default"},
                "spec": {"rules": [{"host": "test1.example.com"}]},
            },
            "test3": {
                "metadata": {"name": "test3", "namespace": "default"},
                "spec": {"rules": [{"host": "test3.example.com"}]},
            },
        }

        # Simulate that the items have changed
        mock_ingressroute_changed.return_value = True

        # Call the function under test without storing the result
        handle_changes(previous_items, current_items, "Ingress")

        # Verify that process_routing_object was called for the added item
        mock_process_routing_object.assert_any_call(current_items["test3"], "Ingress")

        # Verify that process_routing_object was called for the modified item
        mock_process_routing_object.assert_any_call(current_items["test1"], "Ingress")

        # Verify that delete_monitor was called for the deleted item
        mock_delete_monitor.assert_called_once_with("test2-default")

    @patch("kuma_ingress_watcher.controller.process_routing_object")
    @patch("kuma_ingress_watcher.controller.delete_monitor")
    @patch("kuma_ingress_watcher.controller.ingressroute_changed")
    @patch("kuma_ingress_watcher.controller.logger", spec=True)
    def test_handle_changes_deletes_all_monitors_for_multi_host_ingress(
        self,
        mock_logger,
        mock_ingressroute_changed,
        mock_delete_monitor,
        mock_process_routing_object,
    ):
        # A deleted Ingress with two rules/hosts previously produced two
        # suffixed monitors (name-namespace-1, name-namespace-2). Regression
        # test for https://github.com/SQuent/kuma-ingress-watcher/issues/60 -
        # deletion must clean up every suffixed monitor, not just the
        # unsuffixed base name.
        previous_items = {
            "multi": {
                "metadata": {"name": "multi", "namespace": "default"},
                "spec": {
                    "rules": [
                        {"host": "multi.local.example.com"},
                        {"host": "multi.example.com"},
                    ]
                },
            },
        }
        current_items = {}

        handle_changes(previous_items, current_items, "Ingress")

        mock_process_routing_object.assert_not_called()
        mock_delete_monitor.assert_has_calls(
            [call("multi-default-1"), call("multi-default-2")], any_order=True
        )
        self.assertEqual(mock_delete_monitor.call_count, 2)


if __name__ == "__main__":
    unittest.main()
