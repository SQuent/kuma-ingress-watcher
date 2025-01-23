import unittest
from unittest.mock import patch
from kuma_ingress_watcher.controller import process_routes


class TestProcessRoutes(unittest.TestCase):
    @patch("kuma_ingress_watcher.controller.create_or_update_monitor")
    @patch("kuma_ingress_watcher.controller.extract_hosts")
    def test_process_routes_single_route(
        self, mock_extract_hosts, mock_create_or_update_monitor
    ):
        mock_extract_hosts.return_value = ["example.com"]

        process_routes(
            monitor_name="test-monitor",
            routes_or_rules=[{"match": "Host(`example.com`)"}],
            interval=60,
            probe_type="http",
            headers=None,
            hard_host=None,
            path=None,
            port="8080",
            method="GET",
            type_obj="IngressRoute",
        )

        mock_create_or_update_monitor.assert_called_once_with(
            "test-monitor", "https://example.com:8080", 60, "http", None, "GET"
        )

    @patch("kuma_ingress_watcher.controller.create_or_update_monitor")
    @patch("kuma_ingress_watcher.controller.extract_hosts")
    def test_process_routes_multiple_routes(
        self, mock_extract_hosts, mock_create_or_update_monitor
    ):
        mock_extract_hosts.side_effect = [["example.com"], ["example.org"]]

        process_routes(
            monitor_name="test-monitor",
            routes_or_rules=[
                {"match": "Host(`example.com`)"},
                {"match": "Host(`example.org`)"},
            ],
            interval=60,
            probe_type="http",
            headers=None,
            hard_host=None,
            path=None,
            port="8080",
            method="GET",
            type_obj="IngressRoute",
        )

        self.assertEqual(mock_create_or_update_monitor.call_count, 2)
        calls = [
            unittest.mock.call(
                "test-monitor-1", "https://example.com:8080", 60, "http", None, "GET"
            ),
            unittest.mock.call(
                "test-monitor-2", "https://example.org:8080", 60, "http", None, "GET"
            ),
        ]
        mock_create_or_update_monitor.assert_has_calls(calls)

    @patch("kuma_ingress_watcher.controller.create_or_update_monitor")
    @patch("kuma_ingress_watcher.controller.extract_hosts")
    def test_process_routes_no_hosts(
        self, mock_extract_hosts, mock_create_or_update_monitor
    ):
        mock_extract_hosts.return_value = []

        process_routes(
            monitor_name="test-monitor",
            routes_or_rules=[{"match": "Path(`/test`)"}],
            interval=60,
            probe_type="http",
            headers=None,
            hard_host=None,
            path=None,
            port="8080",
            method="GET",
            type_obj="IngressRoute",
        )

        mock_create_or_update_monitor.assert_not_called()

    @patch("kuma_ingress_watcher.controller.create_or_update_monitor")
    @patch("kuma_ingress_watcher.controller.extract_hosts")
    def test_process_routes_with_empty_port(
        self, mock_extract_hosts, mock_create_or_update_monitor
    ):
        mock_extract_hosts.return_value = ["example.com"]

        process_routes(
            monitor_name="test-monitor",
            routes_or_rules=[{"match": "Host(`example.com`)"}],
            interval=60,
            probe_type="http",
            headers=None,
            hard_host=None,
            path=None,
            port=None,
            method="GET",
            type_obj="IngressRoute",
        )

        mock_create_or_update_monitor.assert_called_once_with(
            "test-monitor", "https://example.com", 60, "http", None, "GET"
        )

    @patch("kuma_ingress_watcher.controller.create_or_update_monitor")
    @patch("kuma_ingress_watcher.controller.extract_hosts")
    def test_process_routes_with_path(
        self, mock_extract_hosts, mock_create_or_update_monitor
    ):
        mock_extract_hosts.return_value = ["example.com"]

        process_routes(
            monitor_name="test-monitor",
            routes_or_rules=[{"match": "Host(`example.com`)"}],
            interval=60,
            probe_type="http",
            headers=None,
            hard_host=None,
            path="/milou",
            port=None,
            method="GET",
            type_obj="IngressRoute",
        )

        mock_create_or_update_monitor.assert_called_once_with(
            "test-monitor", "https://example.com/milou", 60, "http", None, "GET"
        )

    @patch("kuma_ingress_watcher.controller.create_or_update_monitor")
    @patch("kuma_ingress_watcher.controller.extract_hosts")
    def test_process_routes_with_hard_host_and_path(
        self, mock_extract_hosts, mock_create_or_update_monitor
    ):
        mock_extract_hosts.return_value = ["example.com"]

        process_routes(
            monitor_name="test-monitor",
            routes_or_rules=[{"match": "Host(`example.com`)"}],
            interval=60,
            probe_type="http",
            headers=None,
            hard_host="tintin",
            path="/milou",
            port=None,
            method="GET",
            type_obj="IngressRoute",
        )

        mock_create_or_update_monitor.assert_called_once_with(
            "test-monitor", "https://tintin/milou", 60, "http", None, "GET"
        )

    @patch("kuma_ingress_watcher.controller.create_or_update_monitor")
    @patch("kuma_ingress_watcher.controller.extract_hosts")
    def test_process_routes_with_hard_host_and_path_and_port(
        self, mock_extract_hosts, mock_create_or_update_monitor
    ):
        mock_extract_hosts.return_value = ["example.com"]

        process_routes(
            monitor_name="test-monitor",
            routes_or_rules=[{"match": "Host(`example.com`)"}],
            interval=60,
            probe_type="http",
            headers=None,
            hard_host="tintin",
            path="/milou",
            port=8080,
            method="GET",
            type_obj="IngressRoute",
        )

        mock_create_or_update_monitor.assert_called_once_with(
            "test-monitor", "https://tintin/milou:8080", 60, "http", None, "GET"
        )

    @patch("kuma_ingress_watcher.controller.create_or_update_monitor")
    @patch("kuma_ingress_watcher.controller.extract_hosts")
    def test_process_routes_multiple_routes_with_hard_host_and_path_and_port(
        self, mock_extract_hosts, mock_create_or_update_monitor
    ):
        mock_extract_hosts.side_effect = [["example.com"], ["example.org"]]

        process_routes(
            monitor_name="test-monitor",
            routes_or_rules=[
                {"match": "Host(`example.com`)"},
                {"match": "Host(`example.org`)"},
            ],
            interval=60,
            probe_type="http",
            headers=None,
            hard_host="tintin",
            path="/milou",
            port=8080,
            method="GET",
            type_obj="IngressRoute",
        )

        self.assertEqual(mock_create_or_update_monitor.call_count, 2)
        calls = [
            unittest.mock.call(
                "test-monitor-1", "https://tintin/milou:8080", 60, "http", None, "GET"
            ),
            unittest.mock.call(
                "test-monitor-2", "https://tintin/milou:8080", 60, "http", None, "GET"
            ),
        ]
        mock_create_or_update_monitor.assert_has_calls(calls)


if __name__ == "__main__":
    unittest.main()
