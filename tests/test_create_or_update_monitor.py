import unittest
from unittest.mock import patch
from kuma_ingress_watcher.controller import create_or_update_monitor


class TestCreateOrUpdateMonitor(unittest.TestCase):
    @patch("kuma_ingress_watcher.controller.kuma")
    @patch("kuma_ingress_watcher.controller.logger")
    def test_create_or_update_monitor_update(self, mock_logger, mock_kuma):
        mock_kuma.get_monitors.return_value = [
            {"name": "test", "url": "http://oldurl.com", "id": 1}
        ]

        create_or_update_monitor("test", "http://newurl.com", 60, "http", None, "GET", "testgroup", ["200-299"])

        mock_logger.info.assert_called_with(
            "Updating monitor for test with URL: http://newurl.com"
        )
        mock_kuma.edit_monitor.assert_called_once_with(
            1,
            url="http://newurl.com",
            interval=60,
            type="http",
            headers=None,
            method="GET",
            parent=None,
            accepted_statuscodes=["200-299"],
        )

    @patch("kuma_ingress_watcher.controller.kuma")
    @patch("kuma_ingress_watcher.controller.logger")
    def test_create_or_update_monitor_create(self, mock_logger, mock_kuma):
        mock_kuma.get_monitors.return_value = []

        create_or_update_monitor("test", "http://newurl.com", 60, "http", None, "GET", None, ["200-299"])

        mock_logger.info.assert_any_call(
            "Creating new monitor for test with URL: http://newurl.com"
        )
        mock_logger.info.assert_any_call("Successfully created monitor for test")
        mock_kuma.add_monitor.assert_called_once_with(
            type="http",
            name="test",
            url="http://newurl.com",
            interval=60,
            headers=None,
            method="GET",
            parent=None,
            accepted_statuscodes=["200-299"],
        )

    @patch("kuma_ingress_watcher.controller.kuma")
    @patch("kuma_ingress_watcher.controller.logger")
    def test_create_or_update_monitor_create_and_find_group(self, mock_logger, mock_kuma):
        mock_kuma.get_monitors.return_value = [
            {"name": "testgroup", "type": "group", "id": 1}
        ]

        create_or_update_monitor("test", "http://newurl.com", 60, "http", None, "GET", "testgroup")

        mock_logger.info.assert_any_call(
            "Creating new monitor for test with URL: http://newurl.com"
        )
        mock_logger.info.assert_any_call("Successfully created monitor for test")
        mock_kuma.add_monitor.assert_called_once_with(
            type="http",
            name="test",
            url="http://newurl.com",
            interval=60,
            headers=None,
            method="GET",
            parent=1,
            accepted_statuscodes=None,
        )

    @patch("kuma_ingress_watcher.controller.kuma")
    @patch("kuma_ingress_watcher.controller.logger")
    def test_create_or_update_monitor_error(self, mock_logger, mock_kuma):
        mock_kuma.get_monitors.side_effect = Exception("API error")

        create_or_update_monitor("test", "http://newurl.com", 60, "http", None, "GET")

        mock_logger.error.assert_called_once_with(
            "Failed to create or update monitor for test: API error"
        )


if __name__ == "__main__":
    unittest.main()
