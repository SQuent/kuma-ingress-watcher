# Kubernetes Ingress Monitor Controller

## Overview

Kuma ingress watcher is a kubernetes controller designed to automatically monitor Traefik Ingress routes in a Kubernetes cluster and create corresponding monitors in Uptime Kuma. It provides seamless integration between Kubernetes ingress resources and Uptime Kuma monitoring, allowing for easy and efficient monitoring of web services deployed on Kubernetes.

## Features

- Automatically creates, updates and deletes monitors in Uptime Kuma for Kubernetes Ingress routes.
- Supports both single and multiple routes per Ingress resource.
- Customizable monitors by annotate ingressroutes.

## Installation

### Requirements

- Python 3.6+
- Kubernetes cluster
- Uptime Kuma instance


## Configuration

### Environment variables
Before running the controller, make sure to configure the following environment variables:

- `UPTIME_KUMA_URL`: The URL of your Uptime Kuma instance.
- `UPTIME_KUMA_USER`: The username for authenticating with Uptime Kuma.
- `UPTIME_KUMA_PASSWORD`: The password for authenticating with Uptime Kuma.

### Annotations for Uptime Kuma Autodiscovery

The following annotations can be used to configure automatic discovery of monitors by Uptime Kuma from Kubernetes Ingress Resources:

1. **`uptime-kuma.autodiscovery.probe.interval`**
   - Sets the probing interval in seconds for the monitor.
   - **Type:** Integer
   - **Default:** `60`
   - **Example:** `uptime-kuma.autodiscovery.probe.interval: 60`

2. **`uptime-kuma.autodiscovery.probe.name`**
   - Name of the monitor in Uptime Kuma.
   - **Type:** String
   - **Default:** `${name}-${namespace}`
   - **Example:** `uptime-kuma.autodiscovery.probe.name: my-monitor`

3. **`uptime-kuma.autodiscovery.probe.enabled`**
   - Enables or disables monitoring for this resource.
   - **Type:** Boolean (accepted values: 'true' or 'false')
   - **Default:** `true`
   - **Example:** `uptime-kuma.autodiscovery.probe.enabled: true`

4. **`uptime-kuma.autodiscovery.probe.type`**
   - Probe type for the monitor (e.g., HTTP, TCP, etc.).
   - **Type:** String
   - **Default:** `http`
   - **Example:** `uptime-kuma.autodiscovery.probe.type: http`

5. **`uptime-kuma.autodiscovery.probe.headers`**
   - Optional HTTP headers to include in the probe request.
   - **Type:** String (HTTP headers format)
   - **Default:** `null` (no headers)
   - **Example:** `uptime-kuma.autodiscovery.probe.headers: {"Authorization": "Bearer token"}`

6. **`uptime-kuma.autodiscovery.probe.port`**
   - Port to use for the probe.
   - **Type:** Integer
   - **Default:** `null` (default port for the protocol)
   - **Example:** `uptime-kuma.autodiscovery.probe.port: 8080`

7. **`uptime-kuma.autodiscovery.probe.method`**
   - HTTP method to use for the probe (GET, POST, etc.).
   - **Type:** String
   - **Default:** `GET`
   - **Example:** `uptime-kuma.autodiscovery.probe.method: GET`

### Complete Example

Here's an example of annotations configured in a Kubernetes Ingress Resource:

```yaml
apiVersion: traefik.containo.us/v1alpha1
kind: IngressRoute
metadata:
  name: example-ingressroute
  namespace: my-namespace
  annotations:
    uptime-kuma.autodiscovery.probe.interval: 120
    uptime-kuma.autodiscovery.probe.name: my-monitor
    uptime-kuma.autodiscovery.probe.enabled: true
    uptime-kuma.autodiscovery.probe.type: http
    uptime-kuma.autodiscovery.probe.headers: '{"Authorization": "Bearer token"}'
    uptime-kuma.autodiscovery.probe.port: 8080
    uptime-kuma.autodiscovery.probe.method: GET
spec:
  # Your Ingress route specification here
```


## Usage

Once the controller is running, it will automatically monitor any changes to Ingress resources in your Kubernetes cluster and create/update corresponding monitors in Uptime Kuma. Simply deploy your applications using Kubernetes Ingress, and the controller will take care of the rest!

## Important Notes

### Tag Addition Limitation

Currently, the addition of tags to monitors is not supported due to limitations in the Uptime Kuma API. Attempting to add tags through the controller may result in unexpected behavior or errors. Please refer to the Uptime Kuma documentation for updates on tag management capabilities.

### Custom Watcher for IngressRoutes

The Kubernetes event watcher (`watch`) does not provide specific details on creation, modification, or deletion events for IngressRoutes. To overcome this limitation, this controller implements a custom watcher mechanism that continuously monitors IngressRoutes and triggers appropriate actions based on changes detected. This custom solution ensures accurate monitoring and synchronization with Uptime Kuma configurations.


## Contributing

Contributions are welcome! If you have any ideas, suggestions, or bug reports, please open an issue or submit a pull request on GitHub.

## Running Unit Tests

To run unit tests for this project:

### Prerequisites

- Python 3.12 or higher installed.
- Poetry installed.

````
poetry install
poetry run pytest
````

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.