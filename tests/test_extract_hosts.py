import unittest
from kuma_ingress_watcher.controller import extract_hosts


class TestExtractHosts(unittest.TestCase):
    def test_extract_hosts_ingressroute(self):
        route_or_rule = {"match": "Host(`example.com`) && Host(`example.org`)"}
        hosts = extract_hosts(route_or_rule, "IngressRoute")
        self.assertEqual(hosts, ["example.com", "example.org"])

    def test_extract_hosts_ingress(self):
        route_or_rule = {"host": "example.com"}
        hosts = extract_hosts(route_or_rule, "Ingress")
        self.assertEqual(hosts, ["example.com"])

    def test_extract_hosts_none(self):
        route_or_rule = {"path": "/test"}
        hosts = extract_hosts(route_or_rule, "IngressRoute")
        self.assertEqual(hosts, [])


if __name__ == "__main__":
    unittest.main()
