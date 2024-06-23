import os
import re
import time
import logging
import sys
from uptime_kuma_api import UptimeKumaApi
from kubernetes import client, config
from kubernetes.client.rest import ApiException

# Logging configuration
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
UPTIME_KUMA_URL = os.getenv('UPTIME_KUMA_URL')
UPTIME_KUMA_USER = os.getenv('UPTIME_KUMA_USER')
UPTIME_KUMA_PASSWORD = os.getenv('UPTIME_KUMA_PASSWORD')

# Global variables for Kubernetes and Uptime Kuma
kuma = None
api_instance = None


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
            if monitor['name'] == name and monitor['url'] == url:
                logger.info(f"Monitor already exists for {name} with same URL. Skipping creation.")
                return
            elif monitor['name'] == name:
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


def extract_hosts(match):
    host_pattern = re.compile(r'Host\(`([^`]*)`\)')
    return host_pattern.findall(match)


def process_ingressroutes(item):
    metadata = item['metadata']
    annotations = metadata.get('annotations', {})

    name = metadata['name']
    namespace = metadata['namespace']
    spec = item['spec']
    routes = spec['routes']
    interval = int(annotations.get('uptime-kuma.autodiscovery.probe.interval', 60))
    monitor_name = annotations.get('uptime-kuma.autodiscovery.probe.name', f"{name}-{namespace}")
    enabled = annotations.get('uptime-kuma.autodiscovery.probe.enabled', 'true').lower() == 'true'
    probe_type = annotations.get('uptime-kuma.autodiscovery.probe.type', 'http')
    headers = annotations.get('uptime-kuma.autodiscovery.probe.headers')
    port = annotations.get('uptime-kuma.autodiscovery.probe.port')
    method = annotations.get('uptime-kuma.autodiscovery.probe.method', 'GET')

    if not enabled:
        logger.info(f"Monitoring for {name} is disabled via annotations.")
        return

    if len(routes) == 1:
        process_single_route(monitor_name, routes[0], interval, probe_type, headers, port, method)
    else:
        process_multiple_routes(monitor_name, routes, interval, probe_type, headers, port, method)


def process_single_route(monitor_name, route, interval, probe_type, headers, port, method):
    match = route.get('match')
    if match:
        hosts = extract_hosts(match)
        for host in hosts:
            url = f"https://{host}"
            if port:
                url = f"{url}:{port}"
            create_or_update_monitor(monitor_name, url, interval, probe_type, headers, method)


def process_multiple_routes(monitor_name, routes, interval, probe_type, headers, port, method):
    index = 1
    for route in routes:
        match = route.get('match')
        if match:
            hosts = extract_hosts(match)
            for host in hosts:
                url = f"https://{host}"
                if port:
                    url = f"{url}:{port}"
                monitor_name_with_index = f"{monitor_name}-{index}"
                index += 1
                create_or_update_monitor(monitor_name_with_index, url, interval, probe_type, headers, method)


def init_kubernetes_client():
    try:
        config.load_incluster_config()
        global api_instance
        api_instance = client.CustomObjectsApi()
    except Exception as e:
        logger.error(f"Failed to initialize Kubernetes client: {e}")
        sys.exit(1)


def get_ingressroutes(api_inst):
    try:
        return api_inst.list_cluster_custom_object(
            group="traefik.containo.us",
            version="v1alpha1",
            plural="ingressroutes"
        )
    except Exception as e:
        logger.error(f"Failed to get ingressroutes: {e}")
        return {'items': []}


def ingressroute_changed(old, new):
    return old != new


def watch_ingressroutes(interval=10):
    previous_ingressroutes = {}

    while True:
        current_ingressroutes = get_ingressroutes(api_instance)
        current_items = {item['metadata']['name']: item for item in current_ingressroutes['items']}
        current_names = set(current_items.keys())
        previous_names = set(previous_ingressroutes.keys())

        added = current_names - previous_names
        for name in added:
            logger.info(f"IngressRoute {name} added.")
            process_ingressroutes(current_items[name])

        deleted = previous_names - current_names
        for name in deleted:
            logger.info(f"IngressRoute {name} deleted.")
            delete_monitor(name)

        modified = current_names & previous_names
        for name in modified:
            if ingressroute_changed(previous_ingressroutes[name], current_items[name]):
                logger.info(f"IngressRoute {name} modified.")
                process_ingressroutes(current_items[name])

        previous_ingressroutes = current_items
        time.sleep(interval)


def main():
    check_config()
    init_kuma_api()
    init_kubernetes_client()
    watch_ingressroutes()


if __name__ == "__main__":
    main()
