import unittest
from kuma_ingress_watcher.controller import get_routes_or_rules


class TestGetRoutesOrRules(unittest.TestCase):
    def test_get_routes_ingressroute(self):
        spec = {
            "routes": [
                {"match": "Host(`example.com`)"},
                {"match": "Host(`example.org`)"},
            ]
        }
        type_obj = "IngressRoute"
        result = get_routes_or_rules(spec, type_obj)
        expected = [{"match": "Host(`example.com`)"}, {"match": "Host(`example.org`)"}]
        self.assertEqual(result, expected)

    def test_get_routes_ingress(self):
        spec = {"rules": [{"host": "example.com"}, {"host": "example.org"}]}
        type_obj = "Ingress"
        result = get_routes_or_rules(spec, type_obj)
        expected = [{"host": "example.com"}, {"host": "example.org"}]
        self.assertEqual(result, expected)

    def test_get_routes_empty(self):
        spec = {}
        type_obj = "IngressRoute"
        result = get_routes_or_rules(spec, type_obj)
        self.assertEqual(result, [])

    def test_get_routes_invalid_type(self):
        spec = {
            "routes": [{"match": "Host(`example.com`)"}],
            "rules": [{"host": "example.org"}],
        }
        type_obj = "InvalidType"
        result = get_routes_or_rules(spec, type_obj)
        self.assertEqual(result, [])


if __name__ == "__main__":
    unittest.main()
