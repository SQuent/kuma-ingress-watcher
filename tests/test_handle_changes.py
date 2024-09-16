import unittest
from unittest.mock import patch
from kuma_ingress_watcher.controller import handle_changes


class TestHandleChanges(unittest.TestCase):

    @patch('kuma_ingress_watcher.controller.process_routing_object')
    @patch('kuma_ingress_watcher.controller.delete_monitor')
    @patch('kuma_ingress_watcher.controller.ingressroute_changed')
    @patch('kuma_ingress_watcher.controller.logger', spec=True)
    def test_handle_changes(self, mock_logger, mock_ingressroute_changed, mock_delete_monitor, mock_process_routing_object):
        # Define previous and current items
        previous_items = {
            'test1': {'metadata': {'name': 'test1', 'namespace': 'default'}},
            'test2': {'metadata': {'name': 'test2', 'namespace': 'default'}}
        }
        current_items = {
            'test1': {'metadata': {'name': 'test1', 'namespace': 'default'}},
            'test3': {'metadata': {'name': 'test3', 'namespace': 'default'}}
        }

        # Simulate that the items have changed
        mock_ingressroute_changed.return_value = True

        # Call the function under test without storing the result
        handle_changes(previous_items, current_items, "Ingress")

        # Verify that process_routing_object was called for the added item
        mock_process_routing_object.assert_any_call(current_items['test3'], "Ingress")

        # Verify that process_routing_object was called for the modified item
        mock_process_routing_object.assert_any_call(current_items['test1'], "Ingress")

        # Verify that delete_monitor was called for the deleted item
        mock_delete_monitor.assert_called_once_with('test2-default')


if __name__ == '__main__':
    unittest.main()
