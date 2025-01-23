import unittest
from kuma_ingress_watcher.controller import extract_hosts_from_ingress_rule


class TestExtractHostsFromIngressRule(unittest.TestCase):
    def test_extract_hosts_single(self):
        rule = {"host": "example.com"}
        hosts = extract_hosts_from_ingress_rule(rule)
        self.assertEqual(hosts, ["example.com"])

    def test_extract_hosts_none(self):
        rule = {"path": "/test"}
        hosts = extract_hosts_from_ingress_rule(rule)
        self.assertEqual(hosts, [])


if __name__ == "__main__":
    unittest.main()
