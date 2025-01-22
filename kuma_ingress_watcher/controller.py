import os
import re
import time
import logging
import sys
from uptime_kuma_api import UptimeKumaApi
from kubernetes import client, config


def str_to_bool(value):
    if isinstance(value, bool):
        return value
    return str(value).lower() in ['true', '1', 't', 'y', 'yes']


# Configuration
UPTIME_KUMA_URL = os.getenv('UPTIME_KUMA_URL')
UPTIME_KUMA_USER = os.getenv('UPTIME_KUMA_USER')
UPTIME_KUMA_PASSWORD = os.getenv('UPTIME_KUMA_PASSWORD')
WATCH_INTERVAL = int(os.getenv('WATCH_INTERVAL', '10') or 10)
WATCH_INGRESSROUTES = str_to_bool(os.getenv('WATCH_INGRESSROUTES', True))
WATCH_INGRESS = str_to_bool(os.getenv('WATCH_INGRESS', False))
USE_TRAEFIK_V3_CRD_GROUP = str_to_bool(os.getenv('USE_TRAEFIK_V3_CRD_GROUP', False))
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()

LOG_LEVELS = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL,
}

# Logging configuration
logging.basicConfig(
    level=LOG_LEVELS.get(LOG_LEVEL, 'INFO'),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global variables for Kubernetes and Uptime Kuma
kuma = None
custom_api_instance = None
networking_api_instance = None


def check_config():
    if not UPTIME_KUMA_URL or not UPTIME_KUMA_USER or not UPTIME_KUMA_PASSWORD:
        logger.error("Uptime Kuma configuration is not set properly.")
        sys.exit(1)


def init_kuma_api():
    try:
        global kuma
        kuma = UptimeKumaApi(UPTIME_KUMA_URL)
        kuma.login(UPTIME_KUMA_USER, UPTIME_KUMA_PASSWORD)
    except Exception as e:
        logger.error(f"Failed to connect to Uptime Kuma API: {e}")
        sys.exit(1)


def create_or_update_monitor(name, url, interval, probe_type, headers, method):
    try:
        monitors = kuma.get_monitors()
        for monitor in monitors:
            if monitor['name'] == name:
                logger.info(f"Updating monitor for {name} with URL: {url}")
                kuma.edit_monitor(monitor['id'], url=url, type=probe_type, headers=headers, method=method, interval=interval)
                return
        logger.info(f"Creating new monitor for {name} with URL: {url}")
        kuma.add_monitor(
            type=probe_type,
            name=name,
            url=url,
            interval=interval,
            headers=headers,
            method=method
        )
        logger.info(f"Successfully created monitor for {name}")
    except Exception as e:
        logger.error(f"Failed to create or update monitor for {name}: {e}")


def delete_monitor(name):
    try:
        monitors = kuma.get_monitors()
        for monitor in monitors:
            if monitor['name'] == name:
                kuma.delete_monitor(monitor['id'])
                logger.info(f"Successfully deleted monitor {name}")
                return
        logger.warning(f"No monitor found with name {name}")
    except Exception as e:
        logger.error(f"Failed to delete monitor {name}: {e}")


def extract_hosts_from_match(match):
    host_pattern = re.compile(r'Host\(`([^`]*)`\)')
    return host_pattern.findall(match)


def extract_hosts_from_ingress_rule(rule):
    hosts = []
    if 'host' in rule:
        hosts.append(rule['host'])
    return hosts


def extract_hosts(route_or_rule, type_obj):
    if type_obj == 'IngressRoute':
        match = route_or_rule.get('match')
        return extract_hosts_from_match(match) if match else []
    elif type_obj == 'Ingress':
        return extract_hosts_from_ingress_rule(route_or_rule)
    else:
        return []


def get_routes_or_rules(spec, type_obj):
    if type_obj == 'IngressRoute':
        return spec.get('routes', [])
    elif type_obj == 'Ingress':
        return spec.get('rules', [])
    else:
        return []


def process_routing_object(item, type_obj):
    metadata = item['metadata']
    annotations = metadata.get('annotations', {})

    name = metadata['name']
    namespace = metadata['namespace']
    spec = item['spec']
    routes_or_rules = get_routes_or_rules(spec, type_obj)
    interval = int(annotations.get('uptime-kuma.autodiscovery.probe.interval', 60))
    monitor_name = annotations.get('uptime-kuma.autodiscovery.probe.name', f"{name}-{namespace}")
    enabled = annotations.get('uptime-kuma.autodiscovery.probe.enabled', 'true').lower() == 'true'
    probe_type = annotations.get('uptime-kuma.autodiscovery.probe.type', 'http')
    headers = annotations.get('uptime-kuma.autodiscovery.probe.headers')
    port = annotations.get('uptime-kuma.autodiscovery.probe.port')
    path = annotations.get('uptime-kuma.autodiscovery.probe.path')
    hard_host = annotations.get('uptime-kuma.autodiscovery.probe.host')
    method = annotations.get('uptime-kuma.autodiscovery.probe.method', 'GET')

    if not enabled:
        logger.info(f"Monitoring for {name} is disabled via annotations.")
        delete_monitor(monitor_name)
        return

    process_routes(monitor_name, routes_or_rules, interval, probe_type, headers, port, path, hard_host, method, type_obj)


def process_routes(monitor_name, routes_or_rules, interval, probe_type, headers, port, path, hard_host, method, type_obj):
    index = 1
    for route_or_rule in routes_or_rules:
        hosts = extract_hosts(route_or_rule, type_obj)

        if hosts:
            for host in hosts:
                url = f"https://{host}"
                if hard_host:
                    url = f"https://{hard_host}"
                if path:
                    url = f"{url}{path}"
                if port:
                    url = f"{url}:{port}"

                monitor_name_with_index = f"{monitor_name}-{index}" if len(routes_or_rules) > 1 else monitor_name

                create_or_update_monitor(monitor_name_with_index, url, interval, probe_type, headers, method)
            index += 1


def init_kubernetes_client():
    try:
        config.load_incluster_config()
        if WATCH_INGRESS:
            global networking_api_instance
            networking_api_instance = client.NetworkingV1Api()

        if WATCH_INGRESSROUTES:
            global custom_api_instance
            custom_api_instance = client.CustomObjectsApi()
    except Exception as e:
        logger.error(f"Failed to initialize Kubernetes client: {e}")
        sys.exit(1)


def get_ingressroutes(custom_api_instance):
    if USE_TRAEFIK_V3_CRD_GROUP:
        group = "traefik.io"
    else:
        group = "traefik.containo.us"

    try:
        return custom_api_instance.list_cluster_custom_object(
            group=group,
            version="v1alpha1",
            plural="ingressroutes"
        )
    except Exception as e:
        logger.error(f"Failed to get ingressroutes: {e}")
        return {'items': []}


def get_ingress(networking_api_instance):
    try:
        ingress_list = networking_api_instance.list_ingress_for_all_namespaces()
        ingress_dict_list = [ingress.to_dict() for ingress in ingress_list.items]
        return {'items': ingress_dict_list}
    except Exception as e:
        logger.error(f"Failed to get Ingress: {e}")
        return {'items': []}


def handle_changes(previous_items, current_items, resource_type):
    current_names = set(current_items.keys())
    previous_names = set(previous_items.keys())

    added = current_names - previous_names
    for name in added:
        logger.info(f"{resource_type} {name} added.")
        process_routing_object(current_items[name], resource_type)

    deleted = previous_names - current_names
    for name in deleted:
        namespace = previous_items[name]['metadata']['namespace']
        monitor_name = f"{name}-{namespace}"
        logger.info(f"{resource_type} {name} deleted.")
        delete_monitor(monitor_name)

    modified = current_names & previous_names
    for name in modified:
        if ingressroute_changed(previous_items[name], current_items[name]):
            logger.info(f"{resource_type} {name} modified.")
            process_routing_object(current_items[name], resource_type)

    return current_items


def ingressroute_changed(old, new):
    return old != new


def watch_ingress_resources():
    if WATCH_INGRESSROUTES:
        logger.info("Start watching Traefik Ingress Routes")
        previous_ingressroutes = {}
    if WATCH_INGRESS:
        logger.info("Start watching Kubernetes Ingress Object")
        previous_ingress = {}

    while True:
        if WATCH_INGRESSROUTES:
            current_ingressroutes = get_ingressroutes(custom_api_instance)
            current_items = {item['metadata']['name']: item for item in current_ingressroutes['items']}
            previous_ingressroutes = handle_changes(previous_ingressroutes, current_items, "IngressRoute")

        if WATCH_INGRESS:
            current_ingress = get_ingress(networking_api_instance)
            current_items = {item['metadata']['name']: item for item in current_ingress['items']}
            previous_ingress = handle_changes(previous_ingress, current_items, "Ingress")

        time.sleep(WATCH_INTERVAL)


def main():
    check_config()
    init_kuma_api()
    init_kubernetes_client()
    watch_ingress_resources()


if __name__ == "__main__":
    main()
