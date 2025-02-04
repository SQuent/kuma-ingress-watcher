import unittest
from kuma_ingress_watcher.controller import extract_hosts_from_match


class TestExtractHostsFromMatch(unittest.TestCase):
    def test_extract_hosts_single(self):
        match = "Host(`example.com`)"
        hosts = extract_hosts_from_match(match)
        self.assertEqual(hosts, ["example.com"])

    def test_extract_hosts_multiple(self):
        match = "Host(`example.com`) && Host(`example.org`)"
        hosts = extract_hosts_from_match(match)
        self.assertEqual(hosts, ["example.com", "example.org"])

    def test_extract_hosts_none(self):
        match = "Path(`/test`)"
        hosts = extract_hosts_from_match(match)
        self.assertEqual(hosts, [])


if __name__ == "__main__":
    unittest.main()
