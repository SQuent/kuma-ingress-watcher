import unittest
from unittest.mock import patch, MagicMock
import yaml
from kuma_ingress_watcher.controller import process_monitor_file


class TestProcessFileIngress(unittest.TestCase):
    @patch("kuma_ingress_watcher.controller.logger", spec=True)
    @patch("kuma_ingress_watcher.controller.open", new_callable=MagicMock)
    def test_process_monitor_file_empty_file(self, mock_open, mock_logger):
        mock_file_content = ""
        mock_open.return_value.__enter__.return_value.read.return_value = (
            mock_file_content
        )

        process_monitor_file("empty_file.yaml")

        mock_logger.info.assert_called_once_with(
            "The file empty_file.yaml is empty or contains only whitespace."
        )

    @patch("kuma_ingress_watcher.controller.logger", spec=True)
    @patch("kuma_ingress_watcher.controller.open", new_callable=MagicMock)
    def test_process_monitor_file_invalid_yaml(self, mock_open, mock_logger):
        mock_file_content = """
        - name: test-ingress
          url: http://example.com
          interval: 60
          type: http
        - name: invalid-ingress
          url example.com  # Erreur dans le YAML
        """
        mock_open.return_value.__enter__.return_value.read.return_value = (
            mock_file_content
        )

        with patch("yaml.safe_load", side_effect=yaml.YAMLError("Invalid YAML")):
            process_monitor_file("mock_file.yaml")

        mock_logger.error.assert_called_once_with(
            "Failed to process file mock_file.yaml: Invalid YAML format (Invalid YAML)"
        )

    @patch("kuma_ingress_watcher.controller.logger", spec=True)
    @patch("kuma_ingress_watcher.controller.open", new_callable=MagicMock)
    def test_process_monitor_file_invalid_statuscodes(self, mock_open, mock_logger):
        mock_file_content = """
        - name: test-ingress
          url: http://example.com
          accepted-statuscodes: not_a_list
        """
        mock_open.return_value.__enter__.return_value.read.return_value = (
            mock_file_content
        )

        process_monitor_file("mock_file.yaml")

        mock_logger.warning.assert_called_once()

    @patch("kuma_ingress_watcher.controller.logger", spec=True)
    @patch("kuma_ingress_watcher.controller.open", new_callable=MagicMock)
    @patch("kuma_ingress_watcher.controller.create_or_update_monitor", spec=True)
    def test_process_monitor_file_valid_entries(
        self, mock_create_or_update_monitor, mock_open, mock_logger
    ):
        mock_file_content = """
        - name: test-ingress
          url: http://example.com
          interval: 30
          type: http
          headers: {"Authorization": "Bearer token"}
          method: POST
          parent: test-parent
          accepted-statuscodes:
            - 200-299
        """
        mock_open.return_value.__enter__.return_value.read.return_value = (
            mock_file_content
        )

        process_monitor_file("mock_file.yaml")

        mock_create_or_update_monitor.assert_called_once_with(
            "test-ingress",
            "http://example.com",
            30,
            "http",
            {"Authorization": "Bearer token"},
            "POST",
            "test-parent",
            ["200-299"]
        )

    @patch("kuma_ingress_watcher.controller.logger", spec=True)
    @patch("kuma_ingress_watcher.controller.open", new_callable=MagicMock)
    def test_process_monitor_file_file_not_found(self, mock_open, mock_logger):
        mock_open.side_effect = FileNotFoundError

        process_monitor_file("nonexistent_file.yaml")

        mock_logger.error.assert_called_once_with(
            "File nonexistent_file.yaml not found."
        )

    @patch("kuma_ingress_watcher.controller.logger", spec=True)
    @patch("kuma_ingress_watcher.controller.open", new_callable=MagicMock)
    def test_process_monitor_file_unexpected_exception(self, mock_open, mock_logger):
        mock_open.side_effect = Exception("Unexpected error")

        process_monitor_file("error_file.yaml")

        mock_logger.error.assert_called_once_with(
            "An unexpected error occurred while processing file error_file.yaml: Unexpected error"
        )

    @patch("kuma_ingress_watcher.controller.logger", spec=True)
    @patch("kuma_ingress_watcher.controller.open", new_callable=MagicMock)
    def test_process_monitor_file_invalid_entry_format(self, mock_open, mock_logger):
        mock_file_content = """
        - not_a_dict
        """
        mock_open.return_value.__enter__.return_value.read.return_value = (
            mock_file_content
        )

        process_monitor_file("mock_file.yaml")

        mock_logger.warning.assert_called_once_with(
            "Skipping invalid entry: not_a_dict (Invalid entry format: not_a_dict)"
        )

    @patch("kuma_ingress_watcher.controller.logger", spec=True)
    @patch("kuma_ingress_watcher.controller.open", new_callable=MagicMock)
    @patch("kuma_ingress_watcher.controller.create_or_update_monitor", spec=True)
    def test_process_monitor_file_multiple_valid_entries_with_non_default_values(
        self, mock_create_or_update_monitor, mock_open, mock_logger
    ):
        # Contenu simulé du fichier avec plusieurs entrées valides et des valeurs personnalisées
        mock_file_content = """
        - name: ingress1
          url: http://example1.com
          interval: 30
          type: https
          probe_type: http
          headers:
            Authorization: "Bearer token1"
          method: POST
        - name: ingress2
          url: http://example2.com
        - name: ingress3
          url: http://example3.com
          type: http
          probe_type: http
          headers:
            Authorization: "Bearer token3"
          method: GET
        - name: ingress1
          url: http://example1.com
          interval: 30
          probe_type: http
          headers:
            Authorization: "Bearer token1"
          method: POST
        - name: ingress2
          url: http://example2.com
          interval: 45
          type: http
          headers:
            Authorization: "Bearer token2"
          method: PUT
        - name: ingress3
          url: http://example3.com
          interval: 60
          type: http
          probe_type: http
          method: GET
        - name: ingress3
          url: http://example3.com
          interval: 60
          type: http
          probe_type: http
        """
        mock_open.return_value.__enter__.return_value.read.return_value = (
            mock_file_content
        )

        process_monitor_file("mock_file.yaml")

        mock_logger.warning.assert_not_called()

        assert mock_create_or_update_monitor.call_count == 7


if __name__ == "__main__":
    unittest.main()
