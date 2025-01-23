import unittest
from unittest.mock import patch
from kuma_ingress_watcher.controller import delete_monitor


class TestDeleteMonitor(unittest.TestCase):
    @patch("kuma_ingress_watcher.controller.kuma")
    @patch("kuma_ingress_watcher.controller.logger")
    def test_delete_monitor_exists(self, mock_logger, mock_kuma):
        mock_kuma.get_monitors.return_value = [{"name": "test", "id": 1}]

        delete_monitor("test")

        mock_logger.info.assert_called_with("Successfully deleted monitor test")
        mock_kuma.delete_monitor.assert_called_once_with(1)

    @patch("kuma_ingress_watcher.controller.kuma")
    @patch("kuma_ingress_watcher.controller.logger")
    def test_delete_monitor_not_found(self, mock_logger, mock_kuma):
        mock_kuma.get_monitors.return_value = []

        delete_monitor("test")

        mock_logger.warning.assert_called_with("No monitor found with name test")
        mock_kuma.delete_monitor.assert_not_called()


if __name__ == "__main__":
    unittest.main()
