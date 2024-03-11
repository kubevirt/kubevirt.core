# -*- coding: utf-8 -*-
# Copyright 2023 Red Hat, Inc.
# Based on the kubernetes.core.k8s inventory
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = """
name: kubevirt

short_description: Inventory source for KubeVirt VirtualMachines

author:
- "KubeVirt.io Project (!UNKNOWN)"

description:
- Fetch running VirtualMachineInstances for one or more namespaces with an optional label selector.
- Groups by namespace, namespace_vmis and labels.
- Uses the kubectl connection plugin to access the Kubernetes cluster.
- Uses *.kubevirt.(yml|yaml) YAML configuration file to set parameter values.

extends_documentation_fragment:
- inventory_cache
- constructed

options:
  plugin:
    description: Token that ensures this is a source file for the "kubevirt" plugin.
    required: True
    choices: ["kubevirt", "kubevirt.core.kubevirt"]
  host_format:
    description:
    - 'Specify the format of the host in the inventory group. Available specifiers: name, namespace, uid.'
    default: "{namespace}-{name}"
  connections:
    description:
    - Optional list of cluster connection settings. If no connections are provided, the default
      I(~/.kube/config) and active context will be used, and objects will be returned for all namespaces
      the active user is authorized to access.
    suboptions:
      name:
        description:
        - Optional name to assign to the cluster. If not provided, a name is constructed from the server
          and port.
      kubeconfig:
        description:
        - Path to an existing Kubernetes config file. If not provided, and no other connection
          options are provided, the Kubernetes client will attempt to load the default
          configuration file from I(~/.kube/config). Can also be specified via K8S_AUTH_KUBECONFIG
          environment variable.
      context:
        description:
        - The name of a context found in the config file. Can also be specified via K8S_AUTH_CONTEXT environment
          variable.
      host:
        description:
        - Provide a URL for accessing the API. Can also be specified via K8S_AUTH_HOST environment variable.
      api_key:
        description:
        - Token used to authenticate with the API. Can also be specified via K8S_AUTH_API_KEY environment
          variable.
      username:
        description:
        - Provide a username for authenticating with the API. Can also be specified via K8S_AUTH_USERNAME
          environment variable.
      password:
        description:
        - Provide a password for authenticating with the API. Can also be specified via K8S_AUTH_PASSWORD
          environment variable.
      client_cert:
        description:
        - Path to a certificate used to authenticate with the API. Can also be specified via K8S_AUTH_CERT_FILE
          environment variable.
        aliases: [ cert_file ]
      client_key:
        description:
        - Path to a key file used to authenticate with the API. Can also be specified via K8S_AUTH_KEY_FILE
          environment variable.
        aliases: [ key_file ]
      ca_cert:
        description:
        - Path to a CA certificate used to authenticate with the API. Can also be specified via
          K8S_AUTH_SSL_CA_CERT environment variable.
        aliases: [ ssl_ca_cert ]
      validate_certs:
        description:
        - Whether or not to verify the API server's SSL certificates. Can also be specified via
          K8S_AUTH_VERIFY_SSL environment variable.
        type: bool
        aliases: [ verify_ssl ]
      namespaces:
        description:
        - List of namespaces. If not specified, will fetch all VirtualMachineInstances for all namespaces
          the user is authorized to access.
      label_selector:
        description:
        - Define a label selector to select a subset of the fetched VirtualMachineInstances.
      network_name:
        description:
        - In case multiple networks are attached to a VirtualMachineInstance, define which interface should
          be returned as primary IP address.
        aliases: [ interface_name ]
      kube_secondary_dns:
        description:
        - Enable kubesecondarydns derived host names when using a secondary network interface.
        type: bool
        default: False
      use_service:
        description:
        - Enable the use of services to establish an SSH connection to the VirtualMachine.
        type: bool
        default: True
      create_groups:
        description:
        - Enable the creation of groups from labels on VirtualMachines.
        type: bool
        default: False
      api_version:
        description:
        - Specify the used KubeVirt API version.
        default: "kubevirt.io/v1"

requirements:
- "python >= 3.9"
- "kubernetes >= 28.1.0"
- "PyYAML >= 3.11"
"""

EXAMPLES = """
# Filename must end with kubevirt.[yml|yaml]

- name: Authenticate with token and return all VirtualMachineInstances for all accessible namespaces
  plugin: kubevirt.core.kubevirt
  connections:
    - host: https://192.168.64.4:8443
      api_key: xxxxxxxxxxxxxxxx
      validate_certs: false

- name: Use default ~/.kube/config and return VirtualMachineInstances from namespace testing connected to network bridge-network
  plugin: kubevirt.core.kubevirt
  connections:
    - namespaces:
        - testing
      network_name: bridge-network

- name: Use default ~/.kube/config and return VirtualMachineInstances from namespace testing with label app=test
  plugin: kubevirt.core.kubevirt
  connections:
    - namespaces:
        - testing
      label_selector: app=test

- name: Use a custom config file and a specific context
  plugin: kubevirt.core.kubevirt
  connections:
    - kubeconfig: /path/to/config
      context: 'awx/192-168-64-4:8443/developer'
"""

from dataclasses import dataclass
from json import loads
from typing import (
    Any,
    Dict,
    List,
    Optional,
)


# Handle import errors of python kubernetes client.
# HAS_K8S_MODULE_HELPER imported below will print a warning to the user if the client is missing.
try:
    from kubernetes.dynamic.exceptions import DynamicApiError
except ImportError:

    class DynamicApiError(Exception):
        pass


from ansible.plugins.inventory import BaseInventoryPlugin, Constructable, Cacheable

from ansible_collections.kubernetes.core.plugins.module_utils.common import (
    HAS_K8S_MODULE_HELPER,
    k8s_import_exception,
)


from ansible_collections.kubernetes.core.plugins.module_utils.k8s.client import (
    get_api_client,
    K8SClient,
)


LABEL_KUBEVIRT_IO_DOMAIN = "kubevirt.io/domain"
TYPE_LOADBALANCER = "LoadBalancer"
TYPE_NODEPORT = "NodePort"


class KubeVirtInventoryException(Exception):
    pass


@dataclass
class GetVmiOptions:
    """
    This class holds the options defined by the user.
    """

    api_version: Optional[str] = None
    label_selector: Optional[str] = None
    network_name: Optional[str] = None
    kube_secondary_dns: Optional[bool] = None
    use_service: Optional[bool] = None
    create_groups: Optional[bool] = None
    base_domain: Optional[str] = None
    host_format: Optional[str] = None

    def __post_init__(self):
        # Set defaults in __post_init__ to allow instatiating class with None values
        if self.api_version is None:
            self.api_version = "kubevirt.io/v1"
        if self.kube_secondary_dns is None:
            self.kube_secondary_dns = False
        if self.use_service is None:
            self.use_service = True
        if self.create_groups is None:
            self.create_groups = False
        if self.host_format is None:
            self.host_format = "{namespace}-{name}"


class InventoryModule(BaseInventoryPlugin, Constructable, Cacheable):
    """
    This class implements the actual inventory module.
    """

    NAME = "kubevirt.core.kubevirt"

    connection_plugin = "kubernetes.core.kubectl"
    transport = "kubectl"

    @staticmethod
    def get_default_host_name(host: str) -> str:
        """
        get_default_host_name strips URL schemes from the host name and
        replaces invalid characters.
        """
        return (
            host.replace("https://", "")
            .replace("http://", "")
            .replace(".", "-")
            .replace(":", "_")
        )

    @staticmethod
    def format_dynamic_api_exc(exc: DynamicApiError) -> str:
        """
        format_dynamic_api_exc tries to extract the message from the JSON body
        of a DynamicApiError.
        """
        if exc.body:
            if exc.headers and exc.headers.get("Content-Type") == "application/json":
                message = loads(exc.body).get("message")
                if message:
                    return message
            return exc.body

        return f"{exc.status} Reason: {exc.reason}"

    @staticmethod
    def get_host_from_service(service: Dict, node_name: str) -> Optional[str]:
        """
        get_host_from_service extracts the hostname to be used from the
        passed in service.
        """
        # LoadBalancer services can return a hostname or an IP address
        if service["spec"]["type"] == TYPE_LOADBALANCER:
            ingress = service["status"]["loadBalancer"].get("ingress")
            if ingress is not None and len(ingress) > 0:
                hostname = ingress[0].get("hostname")
                ip_address = ingress[0].get("ip")
                return hostname if hostname is not None else ip_address

        # NodePort services use the node name as host
        if service["spec"]["type"] == TYPE_NODEPORT:
            return node_name

        return None

    @staticmethod
    def get_port_from_service(service: Dict) -> Optional[str]:
        """
        get_port_from_service extracts the port to be used from the
        passed in service.
        """
        # LoadBalancer services use the port attribute
        if service["spec"]["type"] == TYPE_LOADBALANCER:
            return service["spec"]["ports"][0]["port"]

        # LoadBalancer services use the nodePort attribute
        if service["spec"]["type"] == TYPE_NODEPORT:
            return service["spec"]["ports"][0]["nodePort"]

        return None

    def __init__(self) -> None:
        super().__init__()
        self.host_format = None

    def verify_file(self, path: str) -> None:
        """
        verify_file ensures the inventory file is compatible with this plugin.
        """
        return super().verify_file(path) and path.endswith(
            ("kubevirt.yml", "kubevirt.yaml")
        )

    def parse(self, inventory: Any, loader: Any, path: str, cache: bool = True) -> None:
        """
        parse runs basic setup of the inventory.
        """
        super().parse(inventory, loader, path)
        cache_key = self._get_cache_prefix(path)
        config_data = self._read_config_data(path)
        self.host_format = config_data.get("host_format")
        self.setup(config_data, cache, cache_key)

    def setup(self, config_data: Dict, cache: bool, cache_key: str) -> None:
        """
        setup checks for availability of the Kubernetes Python client,
        gets the configured connections and runs fetch_objects on them.
        If there is a cache it is returned instead.
        """
        connections = config_data.get("connections")

        if not HAS_K8S_MODULE_HELPER:
            raise KubeVirtInventoryException(
                "This module requires the Kubernetes Python client. "
                + f"Try `pip install kubernetes`. Detail: {k8s_import_exception}"
            )

        source_data = None
        if cache and cache_key in self._cache:
            try:
                source_data = self._cache[cache_key]
            except KeyError:
                pass

        if not source_data:
            self.fetch_objects(connections)

    def fetch_objects(self, connections: Dict) -> None:
        """
        fetch_objects populates the inventory with every configured connection.
        """
        if connections:
            if not isinstance(connections, list):
                raise KubeVirtInventoryException("Expecting connections to be a list.")

            for connection in connections:
                if not isinstance(connection, dict):
                    raise KubeVirtInventoryException(
                        "Expecting connection to be a dictionary."
                    )
                client = get_api_client(**connection)
                name = connection.get(
                    "name", self.get_default_host_name(client.configuration.host)
                )
                if connection.get("namespaces"):
                    namespaces = connection["namespaces"]
                else:
                    namespaces = self.get_available_namespaces(client)

                opts = GetVmiOptions(
                    connection.get("api_version"),
                    connection.get("label_selector"),
                    connection.get("network_name", connection.get("interface_name")),
                    connection.get("kube_secondary_dns"),
                    connection.get("use_service"),
                    connection.get("create_groups"),
                    connection.get("base_domain", self.get_cluster_domain(client)),
                    self.host_format,
                )
                for namespace in namespaces:
                    self.get_vmis_for_namespace(client, name, namespace, opts)
        else:
            client = get_api_client()
            name = self.get_default_host_name(client.configuration.host)
            namespaces = self.get_available_namespaces(client)
            opts = GetVmiOptions(host_format=self.host_format)
            for namespace in namespaces:
                self.get_vmis_for_namespace(client, name, namespace, opts)

    def get_cluster_domain(self, client: K8SClient) -> Optional[str]:
        """
        get_cluster_domain tries to get the base domain of an OpenShift cluster.
        """
        try:
            v1_dns = client.resources.get(
                api_version="config.openshift.io/v1", kind="DNS"
            )
        except Exception:
            # If resource not found return None
            return None
        try:
            obj = v1_dns.get(name="cluster")
        except DynamicApiError as exc:
            self.display.debug(
                f"Failed to fetch cluster DNS config: {self.format_dynamic_api_exc(exc)}"
            )
            return None
        return obj.get("spec", {}).get("baseDomain")

    def get_available_namespaces(self, client: K8SClient) -> List:
        """
        get_available_namespaces lists all namespaces accessible with the
        configured credentials and returns them.
        """
        v1_namespace = client.resources.get(api_version="v1", kind="Namespace")
        try:
            obj = v1_namespace.get()
        except DynamicApiError as exc:
            self.display.debug(exc)
            raise KubeVirtInventoryException(
                f"Error fetching Namespace list: {self.format_dynamic_api_exc(exc)}"
            ) from exc
        return [namespace.metadata.name for namespace in obj.items]

    def get_vmis_for_namespace(
        self, client: K8SClient, name: str, namespace: str, opts: GetVmiOptions
    ) -> None:
        """
        get_vmis_for_namespace lists all VirtualMachineInstances in a namespace
        and adds groups and hosts to the inventory.
        """
        vmi_client = client.resources.get(
            api_version=opts.api_version, kind="VirtualMachineInstance"
        )
        try:
            vmi_list = vmi_client.get(
                namespace=namespace, label_selector=opts.label_selector
            )
        except DynamicApiError as exc:
            self.display.debug(exc)
            raise KubeVirtInventoryException(
                f"Error fetching VirtualMachineInstance list: {self.format_dynamic_api_exc(exc)}"
            ) from exc

        services = self.get_ssh_services_for_namespace(client, namespace)

        name = self._sanitize_group_name(name)
        namespace_group = self._sanitize_group_name(f"namespace_{namespace}")

        self.inventory.add_group(name)
        self.inventory.add_group(namespace_group)
        self.inventory.add_child(name, namespace_group)

        for vmi in vmi_list.items:
            if not (vmi.status and vmi.status.interfaces):
                continue

            # Find interface by its name:
            if opts.network_name is None:
                interface = vmi.status.interfaces[0]
            else:
                interface = next(
                    (i for i in vmi.status.interfaces if i.name == opts.network_name),
                    None,
                )

            # If interface is not found or IP address is not reported skip this VM:
            if interface is None or interface.ipAddress is None:
                continue

            vmi_name = opts.host_format.format(
                namespace=vmi.metadata.namespace,
                name=vmi.metadata.name,
                uid=vmi.metadata.uid,
            )
            vmi_annotations = (
                {}
                if not vmi.metadata.annotations
                else vmi.metadata.annotations.to_dict()
            )
            vmi_labels = (
                {} if not vmi.metadata.labels else vmi.metadata.labels.to_dict()
            )

            # Add vmi to the namespace group
            self.inventory.add_host(vmi_name)
            self.inventory.add_child(namespace_group, vmi_name)

            # Create label groups and add vmi to it if enabled
            if vmi.metadata.labels and opts.create_groups:
                # Create a group for each label_value
                vmi_groups = []
                for key, value in vmi.metadata.labels:
                    group_name = self._sanitize_group_name(f"label_{key}_{value}")
                    if group_name not in vmi_groups:
                        vmi_groups.append(group_name)
                # Add vmi to each label_value group
                for group in vmi_groups:
                    self.inventory.add_group(group)
                    self.inventory.add_child(group, vmi_name)

            # Set up the connection
            self.inventory.set_variable(vmi_name, "ansible_connection", "ssh")
            self.set_ansible_host_and_port(
                vmi,
                vmi_name,
                interface.ipAddress,
                services.get(vmi.metadata.labels.get(LABEL_KUBEVIRT_IO_DOMAIN)),
                opts,
            )

            # Add hostvars from metadata
            self.inventory.set_variable(vmi_name, "object_type", "vmi")
            self.inventory.set_variable(vmi_name, "labels", vmi_labels)
            self.inventory.set_variable(vmi_name, "annotations", vmi_annotations)
            self.inventory.set_variable(
                vmi_name, "cluster_name", vmi.metadata.clusterName
            )
            self.inventory.set_variable(
                vmi_name, "resource_version", vmi.metadata.resourceVersion
            )
            self.inventory.set_variable(vmi_name, "uid", vmi.metadata.uid)

            # Add hostvars from status
            vmi_active_pods = (
                {} if not vmi.status.activePods else vmi.status.activePods.to_dict()
            )
            self.inventory.set_variable(vmi_name, "vmi_active_pods", vmi_active_pods)
            vmi_conditions = (
                []
                if not vmi.status.conditions
                else [c.to_dict() for c in vmi.status.conditions]
            )
            self.inventory.set_variable(vmi_name, "vmi_conditions", vmi_conditions)
            vmi_guest_os_info = (
                {} if not vmi.status.guestOSInfo else vmi.status.guestOSInfo.to_dict()
            )
            self.inventory.set_variable(
                vmi_name, "vmi_guest_os_info", vmi_guest_os_info
            )
            vmi_interfaces = (
                []
                if not vmi.status.interfaces
                else [i.to_dict() for i in vmi.status.interfaces]
            )
            self.inventory.set_variable(vmi_name, "vmi_interfaces", vmi_interfaces)
            self.inventory.set_variable(
                vmi_name,
                "vmi_launcher_container_image_version",
                vmi.status.launcherContainerImageVersion,
            )
            self.inventory.set_variable(
                vmi_name, "vmi_migration_method", vmi.status.migrationMethod
            )
            self.inventory.set_variable(
                vmi_name, "vmi_migration_transport", vmi.status.migrationTransport
            )
            self.inventory.set_variable(vmi_name, "vmi_node_name", vmi.status.nodeName)
            self.inventory.set_variable(vmi_name, "vmi_phase", vmi.status.phase)
            vmi_phase_transition_timestamps = (
                []
                if not vmi.status.phaseTransitionTimestamps
                else [p.to_dict() for p in vmi.status.phaseTransitionTimestamps]
            )
            self.inventory.set_variable(
                vmi_name,
                "vmi_phase_transition_timestamps",
                vmi_phase_transition_timestamps,
            )
            self.inventory.set_variable(vmi_name, "vmi_qos_class", vmi.status.qosClass)
            self.inventory.set_variable(
                vmi_name,
                "vmi_virtual_machine_revision_name",
                vmi.status.virtualMachineRevisionName,
            )
            vmi_volume_status = (
                []
                if not vmi.status.volumeStatus
                else [v.to_dict() for v in vmi.status.volumeStatus]
            )
            self.inventory.set_variable(
                vmi_name, "vmi_volume_status", vmi_volume_status
            )

    def get_ssh_services_for_namespace(self, client: K8SClient, namespace: str) -> Dict:
        """
        get_ssh_services_for_namespace retrieves all services of a namespace exposing port 22/ssh.
        The services are mapped to the name of the corresponding domain.
        """
        v1_service = client.resources.get(api_version="v1", kind="Service")
        try:
            service_list = v1_service.get(
                namespace=namespace,
            )
        except DynamicApiError as exc:
            self.display.debug(exc)
            raise KubeVirtInventoryException(
                f"Error fetching Service list: {self.format_dynamic_api_exc(exc)}"
            ) from exc

        services = {}
        for service in service_list.items:
            # Continue if service is not of type LoadBalancer or NodePort
            if service.get("spec", {}).get("type") not in (
                TYPE_LOADBALANCER,
                TYPE_NODEPORT,
            ):
                continue

            # Continue if ports are not defined, there are more than one port mapping
            # or the target port is not port 22/ssh
            ports = service["spec"].get("ports")
            if ports is None or len(ports) != 1 or ports[0].get("targetPort") != 22:
                continue

            # Only add the service to the dict if the domain selector is present
            domain = service["spec"].get("selector", {}).get(LABEL_KUBEVIRT_IO_DOMAIN)
            if domain is not None:
                services[domain] = service

        return services

    def set_ansible_host_and_port(
        self,
        vmi: Dict,
        vmi_name: str,
        ip_address: str,
        service: Optional[Dict],
        opts: GetVmiOptions,
    ) -> None:
        """
        set_ansible_host_and_port sets the ansible_host and possibly the ansible_port var.
        Secondary interfaces have priority over a service exposing SSH
        """
        ansible_host = None
        if opts.kube_secondary_dns and opts.network_name is not None:
            # Set ansible_host to the kubesecondarydns derived host name if enabled
            # See https://github.com/kubevirt/kubesecondarydns#parameters
            ansible_host = (
                f"{opts.network_name}.{vmi.metadata.name}.{vmi.metadata.namespace}.vm"
            )
            if opts.base_domain is not None:
                ansible_host += f".{opts.base_domain}"
        elif opts.use_service and service is not None:
            # Set ansible_host and ansible_port to the host and port from the LoadBalancer
            # or NodePort service exposing SSH
            host = self.get_host_from_service(service, vmi.status.nodeName)
            port = self.get_port_from_service(service)
            if host is not None and port is not None:
                ansible_host = host
                self.inventory.set_variable(vmi_name, "ansible_port", port)

        # Default to the IP address of the interface if ansible_host was not set prior
        if ansible_host is None:
            ansible_host = ip_address

        self.inventory.set_variable(vmi_name, "ansible_host", ansible_host)
