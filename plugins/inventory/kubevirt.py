# -*- coding: utf-8 -*-
# Copyright 2023 Red Hat, Inc.
# Based on the kubernetes.core.k8s inventory
# Apache License 2.0 (see LICENSE or http://www.apache.org/licenses/LICENSE-2.0)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = """
name: kubevirt

short_description: Inventory source for KubeVirt VirtualMachines and VirtualMachineInstances

author:
- "KubeVirt.io Project (!UNKNOWN)"

description:
- Fetch virtual machines from one or more namespaces with an optional label selector.
- Groups by cluster name, namespace and labels.
- Uses the M(kubernetes.core.kubectl) connection plugin to access the Kubernetes cluster.
- Uses V(*.kubevirt.[yml|yaml]) YAML configuration file to set parameter values.

extends_documentation_fragment:
- inventory_cache
- constructed

options:
  plugin:
    description: Token that ensures this is a source file for the P(kubevirt.core.kubevirt#inventory) plugin.
    required: True
    choices: ["kubevirt", "kubevirt.core.kubevirt"]
  host_format:
    description:
    - 'Specify the format of the host in the inventory group. Available specifiers: V(name), V(namespace) and V(uid).'
    default: "{namespace}-{name}"
  connections:
    description:
    - Optional list of cluster connection settings. If no connections are provided, the default
      I(~/.kube/config) and active context will be used, and objects will be returned for all namespaces
      the active user is authorized to access.
    - This parameter is deprecated. Split your connections into multiple configuration files and move
      parameters of each connection to the configuration top level.
    - Deprecated in version C(1.5.0), will be removed in version C(3.0.0).
    type: list
    elements: dict
    suboptions:
      name:
        description:
        - Optional name to assign to the cluster. If not provided, a name is constructed from the server
          and port.
      kubeconfig:
        description:
        - Path to an existing Kubernetes config file. If not provided, and no other connection
          options are provided, the Kubernetes client will attempt to load the default
          configuration file from I(~/.kube/config). Can also be specified via E(K8S_AUTH_KUBECONFIG)
          environment variable.
      context:
        description:
        - The name of a context found in the config file. Can also be specified via E(K8S_AUTH_CONTEXT) environment
          variable.
      host:
        description:
        - Provide a URL for accessing the API. Can also be specified via E(K8S_AUTH_HOST) environment variable.
      api_key:
        description:
        - Token used to authenticate with the API. Can also be specified via E(K8S_AUTH_API_KEY) environment
          variable.
      username:
        description:
        - Provide a username for authenticating with the API. Can also be specified via E(K8S_AUTH_USERNAME)
          environment variable.
      password:
        description:
        - Provide a password for authenticating with the API. Can also be specified via E(K8S_AUTH_PASSWORD)
          environment variable.
      client_cert:
        description:
        - Path to a certificate used to authenticate with the API. Can also be specified via E(K8S_AUTH_CERT_FILE)
          environment variable.
        aliases: [ cert_file ]
      client_key:
        description:
        - Path to a key file used to authenticate with the API. Can also be specified via E(K8S_AUTH_KEY_FILE)
          environment variable.
        aliases: [ key_file ]
      ca_cert:
        description:
        - Path to a CA certificate used to authenticate with the API. Can also be specified via
          E(K8S_AUTH_SSL_CA_CERT) environment variable.
        aliases: [ ssl_ca_cert ]
      validate_certs:
        description:
        - Whether or not to verify the API server's SSL certificates. Can also be specified via
          E(K8S_AUTH_VERIFY_SSL) environment variable.
        type: bool
        aliases: [ verify_ssl ]
      namespaces:
        description:
        - List of namespaces. If not specified, will fetch virtual machines from all namespaces
          the user is authorized to access.
      label_selector:
        description:
        - Define a label selector to select a subset of the fetched virtual machines.
      network_name:
        description:
        - In case multiple networks are attached to a virtual machine, define which interface should
          be returned as primary IP address.
        aliases: [ interface_name ]
      kube_secondary_dns:
        description:
        - Enable C(kubesecondarydns) derived host names when using a secondary network interface.
        type: bool
        default: False
      use_service:
        description:
        - Enable the use of C(Services) to establish an SSH connection to a virtual machine.
        - Services are only used if no O(connections.network_name) was provided.
        type: bool
        default: True
      create_groups:
        description:
        - Enable the creation of groups from labels on C(VirtualMachines) and C(VirtualMachineInstances).
        type: bool
        default: False
      base_domain:
        description:
        - Override the base domain used to construct host names. Used in case of
          C(kubesecondarydns) or C(Services) of type C(NodePort) if O(connections.append_base_domain) is set.
      append_base_domain:
        description:
        - Append the base domain of the cluster to host names constructed from SSH C(Services) of type C(NodePort).
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

- name: Authenticate with token and return all virtual machines from all accessible namespaces
  plugin: kubevirt.core.kubevirt
  connections:
    - host: https://192.168.64.4:8443
      api_key: xxxxxxxxxxxxxxxx
      validate_certs: false

- name: Use default ~/.kube/config and return virtual machines from namespace testing connected to network bridge-network
  plugin: kubevirt.core.kubevirt
  connections:
    - namespaces:
        - testing
      network_name: bridge-network

- name: Use default ~/.kube/config and return virtual machines from namespace testing with label app=test
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
from re import compile as re_compile
from typing import (
    Any,
    Dict,
    List,
    Optional,
)

# Handle import errors of python kubernetes client.
# Set HAS_K8S_MODULE_HELPER and k8s_import exception accordingly to
# potentially print a warning to the user if the client is missing.
try:
    from kubernetes.dynamic.exceptions import DynamicApiError
    from kubernetes.dynamic.resource import ResourceField

    HAS_K8S_MODULE_HELPER = True
    K8S_IMPORT_EXCEPTION = None
except ImportError as e:

    class DynamicApiError(Exception):
        """
        Dummy class, mainly used for ansible-test sanity.
        """

    class ResourceField:
        """
        Dummy class, mainly used for ansible-test sanity.
        """

    HAS_K8S_MODULE_HELPER = False
    K8S_IMPORT_EXCEPTION = e

from ansible.plugins.inventory import BaseInventoryPlugin, Constructable, Cacheable


from ansible_collections.kubernetes.core.plugins.module_utils.k8s.client import (
    get_api_client,
    K8SClient,
)

ANNOTATION_KUBEVIRT_IO_CLUSTER_PREFERENCE_NAME = "kubevirt.io/cluster-preference-name"
ANNOTATION_KUBEVIRT_IO_PREFERENCE_NAME = "kubevirt.io/preference-name"
ANNOTATION_VM_KUBEVIRT_IO_OS = "vm.kubevirt.io/os"
LABEL_KUBEVIRT_IO_DOMAIN = "kubevirt.io/domain"
TYPE_LOADBALANCER = "LoadBalancer"
TYPE_NODEPORT = "NodePort"
ID_MSWINDOWS = "mswindows"


class KubeVirtInventoryException(Exception):
    """
    This class is used for exceptions raised by this inventory.
    """


@dataclass
class InventoryOptions:
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
    append_base_domain: Optional[bool] = None
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
        if self.append_base_domain is None:
            self.append_base_domain = False
        if self.host_format is None:
            self.host_format = "{namespace}-{name}"


class InventoryModule(BaseInventoryPlugin, Constructable, Cacheable):
    """
    This class implements the actual inventory module.
    """

    NAME = "kubevirt.core.kubevirt"

    # Used to convert camel case variable names into snake case
    snake_case_pattern = re_compile(r"(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])")

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
    def format_var_name(name: str) -> str:
        """
        format_var_name formats a CamelCase variable name into a snake_case name
        suitable for use as a inventory variable name.
        """
        return InventoryModule.snake_case_pattern.sub("_", name).lower()

    @staticmethod
    def get_host_from_service(service: Dict, node_name: Optional[str]) -> Optional[str]:
        """
        get_host_from_service extracts the hostname to be used from the
        passed in service.
        """
        service_type = service.get("spec", {}).get("type")
        if service_type == TYPE_LOADBALANCER:
            # LoadBalancer services can return a hostname or an IP address
            ingress = service.get("status", {}).get("loadBalancer", {}).get("ingress")
            if ingress is not None and len(ingress) > 0:
                hostname = ingress[0].get("hostname")
                ip_address = ingress[0].get("ip")
                return hostname if hostname is not None else ip_address
        elif service_type == TYPE_NODEPORT:
            # NodePort services use the node name as host
            return node_name

        return None

    @staticmethod
    def get_port_from_service(service: Dict) -> Optional[str]:
        """
        get_port_from_service extracts the port to be used from the
        passed in service.
        """
        ports = service.get("spec", {}).get("ports", [])
        if not ports:
            return None

        service_type = service.get("spec", {}).get("type")
        if service_type == TYPE_LOADBALANCER:
            # LoadBalancer services use the port attribute
            return ports[0].get("port")
        if service_type == TYPE_NODEPORT:
            # NodePort services use the nodePort attribute
            return ports[0].get("nodePort")

        return None

    @staticmethod
    def is_windows(guest_os_info: Optional[Dict], annotations: Optional[Dict]) -> bool:
        """
        is_windows checkes whether a given VM is running a Windows guest
        by checking its GuestOSInfo and annotations.
        """
        if guest_os_info and "id" in guest_os_info:
            return guest_os_info["id"] == ID_MSWINDOWS

        if not annotations:
            return False

        if ANNOTATION_KUBEVIRT_IO_CLUSTER_PREFERENCE_NAME in annotations:
            return annotations[
                ANNOTATION_KUBEVIRT_IO_CLUSTER_PREFERENCE_NAME
            ].startswith("windows")

        if ANNOTATION_KUBEVIRT_IO_PREFERENCE_NAME in annotations:
            return annotations[ANNOTATION_KUBEVIRT_IO_PREFERENCE_NAME].startswith(
                "windows"
            )

        if ANNOTATION_VM_KUBEVIRT_IO_OS in annotations:
            return annotations[ANNOTATION_VM_KUBEVIRT_IO_OS].startswith("windows")

        return False

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
        if not HAS_K8S_MODULE_HELPER:
            raise KubeVirtInventoryException(
                "This module requires the Kubernetes Python client. "
                + f"Try `pip install kubernetes`. Detail: {K8S_IMPORT_EXCEPTION}"
            )

        source_data = None
        if cache and cache_key in self._cache:
            try:
                source_data = self._cache[cache_key]
            except KeyError:
                pass

        if not source_data:
            self.fetch_objects(config_data.get("connections"))

    def fetch_objects(self, connections: Optional[List[Dict]]) -> None:
        """
        fetch_objects populates the inventory with every configured connection.
        """
        if connections:
            self.display.deprecated(
                msg="The 'connections' parameter is deprecated and starting with version 2.0.0 of kubevirt.core supports only a single entry.",
                version="3.0.0",
                collection_name="kubevirt.core",
            )

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

                opts = InventoryOptions(
                    connection.get("api_version"),
                    connection.get("label_selector"),
                    connection.get("network_name", connection.get("interface_name")),
                    connection.get("kube_secondary_dns"),
                    connection.get("use_service"),
                    connection.get("create_groups"),
                    connection.get("base_domain", self.get_cluster_domain(client)),
                    connection.get("append_base_domain"),
                    self.host_format,
                )
                for namespace in namespaces:
                    self.populate_inventory_from_namespace(
                        client, name, namespace, opts
                    )
        else:
            client = get_api_client()
            name = self.get_default_host_name(client.configuration.host)
            namespaces = self.get_available_namespaces(client)
            opts = InventoryOptions(
                host_format=self.host_format,
                base_domain=self.get_cluster_domain(client),
            )
            for namespace in namespaces:
                self.populate_inventory_from_namespace(client, name, namespace, opts)

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

    def get_resources(
        self, client: K8SClient, api_version: str, kind: str, **kwargs
    ) -> List[ResourceField]:
        """
        get_resources uses a dynamic K8SClient to fetch resources from the K8S API.
        """
        client = client.resources.get(api_version=api_version, kind=kind)
        try:
            result = client.get(**kwargs)
        except DynamicApiError as exc:
            self.display.debug(exc)
            raise KubeVirtInventoryException(
                f"Error fetching {kind} list: {self.format_dynamic_api_exc(exc)}"
            ) from exc

        return result.items

    def get_available_namespaces(self, client: K8SClient) -> List[str]:
        """
        get_available_namespaces lists all namespaces accessible with the
        configured credentials and returns them.
        """
        return [
            namespace.metadata.name
            for namespace in self.get_resources(client, "v1", "Namespace")
        ]

    def get_vms_for_namespace(
        self, client: K8SClient, namespace: str, opts: InventoryOptions
    ) -> List[ResourceField]:
        """
        get_vms_for_namespace returns a list of all VirtualMachines in a namespace.
        """
        return self.get_resources(
            client,
            opts.api_version,
            "VirtualMachine",
            namespace=namespace,
            label_selector=opts.label_selector,
        )

    def get_vmis_for_namespace(
        self, client: K8SClient, namespace: str, opts: InventoryOptions
    ) -> List[ResourceField]:
        """
        get_vmis_for_namespace returns a list of all VirtualMachineInstances in a namespace.
        """
        return self.get_resources(
            client,
            opts.api_version,
            "VirtualMachineInstance",
            namespace=namespace,
            label_selector=opts.label_selector,
        )

    def get_ssh_services_for_namespace(self, client: K8SClient, namespace: str) -> Dict:
        """
        get_ssh_services_for_namespace retrieves all services of a namespace exposing port 22/ssh.
        The services are mapped to the name of the corresponding domain.
        """
        service_list = self.get_resources(
            client,
            "v1",
            "Service",
            namespace=namespace,
        )

        services = {}
        for service in service_list:
            # Continue if service is not of type LoadBalancer or NodePort
            if service.get("spec") is None:
                continue

            if service["spec"].get("type") not in (
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

    def populate_inventory_from_namespace(
        self, client: K8SClient, name: str, namespace: str, opts: InventoryOptions
    ) -> None:
        """
        populate_inventory_from_namespace adds groups and hosts from a
        namespace to the inventory.
        """
        vms = {
            vm.metadata.name: vm
            for vm in self.get_vms_for_namespace(client, namespace, opts)
        }
        vmis = {
            vmi.metadata.name: vmi
            for vmi in self.get_vmis_for_namespace(client, namespace, opts)
        }

        if not vms and not vmis:
            # Return early if no VMs and VMIs were found to avoid adding empty groups.
            return

        services = self.get_ssh_services_for_namespace(client, namespace)

        name = self._sanitize_group_name(name)
        namespace_group = self._sanitize_group_name(f"namespace_{namespace}")

        self.inventory.add_group(name)
        self.inventory.add_group(namespace_group)
        self.inventory.add_child(name, namespace_group)

        # Add found VMs and optionally enhance with VMI data
        for name, vm in vms.items():
            hostname = self.add_host(vm, opts.host_format, namespace_group)
            self.set_vars_from_vm(hostname, vm, opts)
            if name in vmis:
                self.set_vars_from_vmi(hostname, vmis[name], services, opts)
            self.set_composable_vars(hostname)

        # Add remaining VMIs without VM
        for name, vmi in vmis.items():
            if name in vms:
                continue
            hostname = self.add_host(vmi, opts.host_format, namespace_group)
            self.set_vars_from_vmi(hostname, vmi, services, opts)
            self.set_composable_vars(hostname)

    def add_host(
        self, obj: ResourceField, host_format: str, namespace_group: str
    ) -> str:
        """
        add_hosts adds a host to the inventory.
        """
        hostname = host_format.format(
            namespace=obj.metadata.namespace,
            name=obj.metadata.name,
            uid=obj.metadata.uid,
        )
        self.inventory.add_host(hostname)
        self.inventory.add_child(namespace_group, hostname)

        return hostname

    def set_vars_from_vm(
        self, hostname: str, vm: ResourceField, opts: InventoryOptions
    ) -> None:
        """
        set_vars_from_vm sets inventory variables from a VM prefixed with vm_.
        """
        self.set_common_vars(hostname, "vm", vm, opts)

    def set_vars_from_vmi(
        self, hostname: str, vmi: ResourceField, services: Dict, opts: InventoryOptions
    ) -> None:
        """
        set_vars_from_vmi sets inventory variables from a VMI prefixed with vmi_ and
        looks up the interface to set ansible_host and ansible_port.
        """
        self.set_common_vars(hostname, "vmi", vmi, opts)

        if opts.network_name is None:
            # Use first interface
            interface = vmi.status.interfaces[0] if vmi.status.interfaces else None
        else:
            # Find interface by its name
            interface = next(
                (i for i in vmi.status.interfaces if i.name == opts.network_name),
                None,
            )

        # If interface is not found or IP address is not reported skip this VMI
        if interface is None or interface.ipAddress is None:
            return

        # Set up the connection
        service = None
        if self.is_windows(
            {} if not vmi.status.guestOSInfo else vmi.status.guestOSInfo.to_dict(),
            {} if not vmi.metadata.annotations else vmi.metadata.annotations.to_dict(),
        ):
            self.inventory.set_variable(hostname, "ansible_connection", "winrm")
        else:
            service = services.get(vmi.metadata.labels.get(LABEL_KUBEVIRT_IO_DOMAIN))
        self.set_ansible_host_and_port(
            vmi,
            hostname,
            interface.ipAddress,
            service,
            opts,
        )

    def set_common_vars(
        self, hostname: str, prefix: str, obj: ResourceField, opts: InventoryOptions
    ):
        """
        set_common_vars sets common inventory variables from VMs or VMIs.
        """
        # Add hostvars from metadata
        if metadata := obj.metadata:
            if metadata.annotations:
                self.inventory.set_variable(
                    hostname, f"{prefix}_annotations", metadata.annotations.to_dict()
                )
            if metadata.labels:
                self.inventory.set_variable(
                    hostname, f"{prefix}_labels", metadata.labels.to_dict()
                )
                # Create label groups and add vm to it if enabled
                if opts.create_groups:
                    self.set_groups_from_labels(hostname, metadata.labels)
            if metadata.resourceVersion:
                self.inventory.set_variable(
                    hostname, f"{prefix}_resource_version", metadata.resourceVersion
                )
            if metadata.uid:
                self.inventory.set_variable(hostname, f"{prefix}_uid", metadata.uid)

        # Add hostvars from status
        if obj.status:
            for key, value in obj.status.to_dict().items():
                name = self.format_var_name(key)
                self.inventory.set_variable(hostname, f"{prefix}_{name}", value)

    def set_groups_from_labels(self, hostname: str, labels: ResourceField) -> None:
        """
        set_groups_from_labels adds groups for each label of a VM or VMI and
        adds the host to each group.
        """
        groups = []
        for key, value in labels.to_dict().items():
            group_name = self._sanitize_group_name(f"label_{key}_{value}")
            if group_name not in groups:
                groups.append(group_name)
        # Add host to each label_value group
        for group in groups:
            self.inventory.add_group(group)
            self.inventory.add_child(group, hostname)

    def set_ansible_host_and_port(
        self,
        vmi: ResourceField,
        hostname: str,
        ip_address: str,
        service: Optional[Dict],
        opts: InventoryOptions,
    ) -> None:
        """
        set_ansible_host_and_port sets the ansible_host and possibly the ansible_port var.
        Secondary interfaces have priority over a service exposing SSH
        """
        ansible_host = None
        ansible_port = None
        if opts.kube_secondary_dns and opts.network_name:
            # Set ansible_host to the kubesecondarydns derived host name if enabled
            # See https://github.com/kubevirt/kubesecondarydns#parameters
            ansible_host = (
                f"{opts.network_name}.{vmi.metadata.name}.{vmi.metadata.namespace}.vm"
            )
            if opts.base_domain:
                ansible_host += f".{opts.base_domain}"
        elif opts.use_service and service and not opts.network_name:
            # Set ansible_host and ansible_port to the host and port from the LoadBalancer
            # or NodePort service exposing SSH
            node_name = vmi.status.nodeName
            if node_name and opts.append_base_domain and opts.base_domain:
                node_name += f".{opts.base_domain}"
            host = self.get_host_from_service(service, node_name)
            port = self.get_port_from_service(service)
            if host is not None and port is not None:
                ansible_host = host
                ansible_port = port

        # Default to the IP address of the interface if ansible_host was not set prior
        if ansible_host is None:
            ansible_host = ip_address

        self.inventory.set_variable(hostname, "ansible_host", ansible_host)
        self.inventory.set_variable(hostname, "ansible_port", ansible_port)

    def set_composable_vars(self, hostname: str) -> None:
        """
        set_composable_vars sets vars per
        https://docs.ansible.com/ansible/latest/dev_guide/developing_inventory.html
        """
        hostvars = self.inventory.get_host(hostname).get_vars()
        strict = self.get_option("strict")
        self._set_composite_vars(
            self.get_option("compose"), hostvars, hostname, strict=True
        )
        self._add_host_to_composed_groups(
            self.get_option("groups"), hostvars, hostname, strict=strict
        )
        self._add_host_to_keyed_groups(
            self.get_option("keyed_groups"), hostvars, hostname, strict=strict
        )
