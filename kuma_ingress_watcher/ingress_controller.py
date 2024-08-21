import os
import re
import time
import logging
import sys
from uptime_kuma_api import UptimeKumaApi
from kubernetes import client, config


# Configuration
UPTIME_KUMA_URL = os.getenv('UPTIME_KUMA_URL')
UPTIME_KUMA_USER = os.getenv('UPTIME_KUMA_USER')
UPTIME_KUMA_PASSWORD = os.getenv('UPTIME_KUMA_PASSWORD')
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
    level=LOG_LEVELS.get(LOG_LEVEL, logging.DEBUG),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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

def extract_ingress_objects_hosts(ingress_objects):
    hosts = []
    for ingress in ingress_objects.get('items', []):
        if 'spec' in ingress and 'rules' in ingress['spec']:
            for rule in ingress['spec']['rules']:
                if 'host' in rule:
                    hosts.append(rule['host'])
    return hosts


def process_ingress_objects(item):
    metadata = item['metadata']
    annotations = metadata.get('annotations', {})

    name = metadata['name']
    namespace = metadata['namespace']
    spec = item['spec']
    rules = spec['rules']
    interval = int(annotations.get('uptime-kuma.autodiscovery.probe.interval', 60))
    monitor_name = annotations.get('uptime-kuma.autodiscovery.probe.name', f"{name}-{namespace}")
    enabled = annotations.get('uptime-kuma.autodiscovery.probe.enabled', 'true').lower() == 'true'
    probe_type = annotations.get('uptime-kuma.autodiscovery.probe.type', 'http')
    headers = annotations.get('uptime-kuma.autodiscovery.probe.headers')
    port = annotations.get('uptime-kuma.autodiscovery.probe.port')
    method = annotations.get('uptime-kuma.autodiscovery.probe.method', 'GET')

    if not enabled:
        logger.info(f"Monitoring for {name} is disabled via annotations.")
        delete_monitor(monitor_name)
        return

    if len(rules) == 1:
        process_single_ingress(monitor_name, rules[0]["host"], interval, probe_type, headers, port, method)
    else:
        process_multiple_ingress(monitor_name, rules, interval, probe_type, headers, port, method)

def process_single_ingress(monitor_name, host, interval, probe_type, headers, port, method):    
    
    url = f"https://{host}"
    if port:
        url = f"{url}:{port}"
    create_or_update_monitor(monitor_name, url, interval, probe_type, headers, method)

def process_multiple_ingress(monitor_name, routes, interval, probe_type, headers, port, method):
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

def load_kubernetes_config():
    try:
        config.load_incluster_config()
        logger.info("Loaded in-cluster configuration.")
    except config.ConfigException:

        logger.warning(f"In-cluster configuration not found. Attempting to use service account token.")

        try:
            kubernetes_host = os.getenv('KUBERNETES_HOST')
            token = os.getenv('KUBERNETES_TOKEN')

            configuration = client.Configuration()
            configuration.host = kubernetes_host
            configuration.verify_ssl = False  # Set this to True if you want to verify SSL certificates
            configuration.api_key = {"authorization": "Bearer " + token}

            client.Configuration.set_default(configuration)
            logger.info("Kubernetes client configured using service account token.")
        except Exception as ex:
            logger.error(f"Failed to configure Kubernetes client with service account token: {ex}")
            sys.exit(1)

def init_kubernetes_client():
    load_kubernetes_config()
    global api_instance
    global networking_v1_api
    api_instance = client.CustomObjectsApi() # used for ingress routes
    networking_v1_api = client.NetworkingV1Api()
    logger.info("Kubernetes client initialized.")

def get_ingress_objects(api_inst):
    try:
        return api_inst.list_ingress_for_all_namespaces().to_dict()
    except Exception as e:
        logger.error(f"Failed to get ingress_objects: {e}")
        return {'items': []}

def watch_ingress_objects(interval=10):
    previous_ingress_objects = {}

    while True:
        previous_ingress_objects = get_ingress_objects(networking_v1_api)
        current_items = {item['metadata']['name']: item for item in previous_ingress_objects['items']}        
        current_names = set(current_items.keys())
        previous_names = set(previous_ingress_objects.keys())

        added = current_names - previous_names
        for name in added:
            logger.info(f"Ingress {name} added.")
            process_ingress_objects(current_items[name])

        deleted = previous_names - current_names
        for name in deleted:
            namespace = previous_ingressroutes[name]['metadata']['namespace']
            monitor_name = f"{name}-{namespace}"
            logger.info(f"IngressRoute {name} deleted.")
            delete_monitor(monitor_name)

        modified = current_names & previous_names
        for name in modified:
            if ingress_changed(previous_ingressroutes[name], current_items[name]):
                logger.info(f"IngressRoute {name} modified.")
                process_ingress_objects(current_items[name])

        previous_ingressroutes = current_items
        time.sleep(interval)

def ingress_changed(old, new):
    return old != new


def main():
    check_config()
    init_kuma_api()
    init_kubernetes_client()
    watch_ingress_objects()


if __name__ == "__main__":
    main()