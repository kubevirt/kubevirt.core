# -*- coding: utf-8 -*-
# Copyright 2024 Red Hat, Inc.
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest

from addict import Dict
import copy

from ansible_collections.kubevirt.core.plugins.inventory.kubevirt import (
    GetVmiOptions,
    InventoryModule,
    KubeVirtInventoryException,
)

from ansible_collections.kubevirt.core.tests.unit.utils.merge_dicts import (
    merge_dicts,
)

from ansible_collections.kubevirt.core.plugins.inventory import (
    kubevirt
)


DEFAULT_NAMESPACE = "default"
DEFAULT_BASE_DOMAIN = "example.com"

BASE_VMI = {
    "apiVersion": "kubevirt.io/v1",
    "kind": "VirtualMachineInstance",
    "metadata": {
        "name": "testvmi",
        "namespace": "default",
        "uid": "f8abae7c-d792-4b9b-af95-62d322ae5bc1",
        "labels": {"kubevirt.io/domain": "test-domain"},
    },
    "spec": {
        "domain": {"devices": {}},
    },
}
# Note, if "interfaces": [{}] or "interfaces": [{"ipAddress": {}}] the if on line 517, problem?
VMI_WITH_INTERFACE_NO_IPADDRESS = merge_dicts(
    BASE_VMI,
    {
        "status": {
            "interfaces": [{"ipAddress": None}]
        }
    }
)
BASIC_VMI = merge_dicts(
    BASE_VMI,
    {
        "status": {
            "interfaces": [{"ipAddress": "10.10.10.10"}],
        },
    }
)
WINDOWS_VMI_1 = merge_dicts(
    BASIC_VMI,
    {
        "status": {
            "guestOSInfo": {"id": "mswindows"},
        }
    },
)
WINDOWS_VMI_2 = merge_dicts(
    BASIC_VMI,
    {
        "metadata": {
            "annotations": {"kubevirt.io/cluster-preference-name": "windows.2k22"}
        },
    },
)
WINDOWS_VMI_3 = merge_dicts(
    BASIC_VMI,
    {
        "metadata": {"annotations": {"kubevirt.io/preference-name": "windows.2k22"}},
    },
)
WINDOWS_VMI_4 = merge_dicts(
    BASIC_VMI,
    {
        "metadata": {"annotations": {"vm.kubevirt.io/os": "windows2k22"}},
    },
)
COMPLETE_VMI = merge_dicts(
    BASIC_VMI,
    {
        "metadata": {
            # {"test-label": "test-label"} does not work
            "annotations": {"test-annotation": "test-annotation"},
            "clusterName": {"test-cluster"},
            "resourceVersion": {"42"},
        },
        "status": {
            "activePods": {"d5b85485-354b-40d3-b6a0-23e18b685310": "node01"},
            "conditions": [
                {
                    "status": True,
                    "type": "Ready",
                    "lastProbeTime": "null",
                    "lastTransitionTime": "null",
                },
            ],
            "guestOSInfo": {
                "id": "fedora",
                "version": "39",
            },
            "launcherContainerImageVersion": {"quay.io/kubevirt/virt-launcher:v1.1.0"},
            "migrationMethod": "BlockMigration",
            "migrationTransport": "Unix",
            "nodeName": "node01",
            "phase": "Running",
            "phaseTransitionTimestamps": [
                {
                    "phase": "Running",
                    "phaseTransitionTimestamp": "null",
                },
            ],
            "qosClass": "Burstable",
            "virtualMachineRevisionName": "revision-start-vm-12345",
            "volumeStatus": [
                {
                    "name": "cloudinit",
                    "size": 1048576,
                    "target": "vdb"
                },
                {
                    "name": "containerdisk",
                    "target": "vda",
                }
            ],
        }
    },
)

BASE_SERVICE = {
    "apiVersion": "v1",
    "kind": "Service",
    "metadata": {
        "name": "test-service"
    },
    "spec": {}
}
LOADBALANCER_SERVICE_WITHOUT_AND_SELECTOR_PORTS = merge_dicts(
    BASE_SERVICE,
    {
        "spec": {
            "type": "LoadBalancer"
        }
    }
)
LOADBALANCER_SERVICE_WITHOUT_SELECTOR_AND_SSH_PORT = merge_dicts(
    LOADBALANCER_SERVICE_WITHOUT_AND_SELECTOR_PORTS,
    {
        "spec": {
            "ports": [
                {
                    "protocol": "TCP",
                    "port": 80,
                    "targetPort": 80,
                },
            ],
            "type": "LoadBalancer",
        }
    }
)
LOADBALANCER_SERVICE_WITHOUT_SELECTOR = merge_dicts(
    LOADBALANCER_SERVICE_WITHOUT_AND_SELECTOR_PORTS,
    {
        "spec": {
            "ports": [
                {
                    "protocol": "TCP",
                    "port": 22,
                    "targetPort": 22,
                },
            ],
            "type": "LoadBalancer",
        }
    }
)
LOADBALANCER_SERVICE = {
    "apiVersion": "v1",
    "kind": "Service",
    "metadata": {
        "name": "test-service"
    },
    "spec": {
        "selector": {
            "kubevirt.io/domain": "test-domain"
        },
        "ports": [
            {
                "protocol": "TCP",
                "port": 22,
                "targetPort": 22
            }
        ],
        "type": "LoadBalancer"
    }
}
NODEPORT_SERVICE = merge_dicts(
    LOADBALANCER_SERVICE,
    {
        "spec": {
            "type": "NodePort",
        }
    }
)


@pytest.fixture(scope="function")
def inventory(mocker):
    inventory = InventoryModule()
    inventory.inventory = mocker.Mock()
    mocker.patch.object(inventory, "set_composable_vars")
    return inventory


@pytest.fixture(scope="function")
def host_vars(monkeypatch, inventory):
    host_vars = {}

    def set_variable(host, key, value):
        if host not in host_vars:
            host_vars[host] = {}
        host_vars[host][key] = value

    monkeypatch.setattr(inventory.inventory, "set_variable", set_variable)
    return host_vars


@pytest.fixture(scope="function")
def add_group(monkeypatch, inventory):
    groups = []

    def add_group(name):
        if name not in groups:
            groups.append(name)

    monkeypatch.setattr(inventory.inventory, "add_group", add_group)
    return groups


@pytest.fixture(scope="function")
def add_host(monkeypatch, inventory):
    hosts = []

    def add_host(name):
        if name not in hosts:
            hosts.append(name)

    monkeypatch.setattr(inventory.inventory, "add_host", add_host)
    return hosts


@pytest.fixture(scope="function")
def add_child(monkeypatch, inventory):
    children = {}

    def add_child(group, name):
        if group not in children:
            children[group] = []
        if name not in children[group]:
            children[group].append(name)

    monkeypatch.setattr(inventory.inventory, "add_child", add_child)
    return children


@pytest.fixture(scope="function")
def client(mocker, request):
    namespaces = mocker.Mock()
    namespaces.items = [
        Dict(item)
        for item in request.param.get(
            "namespaces", [{"metadata": {"name": DEFAULT_NAMESPACE}}]
        )
    ]
    vmis = mocker.Mock()
    vmis.items = [Dict(item) for item in request.param.get("vmis", [])]
    services = mocker.Mock()
    services.items = [Dict(item) for item in request.param.get("services", [])]
    dns = Dict(
        {"spec": {"baseDomain": request.param.get("base_domain", DEFAULT_BASE_DOMAIN)}}
    )

    namespace_client = mocker.Mock()
    namespace_client.get = mocker.Mock(return_value=namespaces)
    vmi_client = mocker.Mock()
    vmi_client.get = mocker.Mock(return_value=vmis)
    service_client = mocker.Mock()
    service_client.get = mocker.Mock(return_value=services)
    dns_client = mocker.Mock()
    dns_client.get = mocker.Mock(return_value=dns)

    def resources_get(api_version="", kind=""):
        if api_version.lower() == "v1":
            if kind.lower() == "namespace":
                return namespace_client
            elif kind.lower() == "service":
                return service_client
        elif api_version.lower() == "config.openshift.io/v1" and kind.lower() == "dns":
            return dns_client
        elif (
            "kubevirt.io/" in api_version.lower()
            and kind.lower() == "virtualmachineinstance"
        ):
            return vmi_client

        return None

    client = mocker.Mock()
    client.resources.get = resources_get
    return client


@pytest.mark.parametrize(
    "file_name,expected",
    [
        ("inventory.kubevirt.yml", True),
        ("inventory.kubevirt.yaml", True),
        ("something.kubevirt.yml", True),
        ("something.kubevirt.yaml", True),
        ("inventory.somethingelse.yml", False),
        ("inventory.somethingelse.yaml", False),
        ("something.somethingelse.yml", False),
        ("something.somethingelse.yaml", False),
    ],
)
def test_verify_file(tmp_path, inventory, file_name, expected):
    file = tmp_path / file_name
    file.touch()
    assert inventory.verify_file(str(file)) is expected


@pytest.mark.parametrize(
    "file_name",
    [
        "inventory.kubevirt.yml",
        "inventory.kubevirt.yaml",
        "something.kubevirt.yml",
        "something.kubevirt.yaml",
        "inventory.somethingelse.yml",
        "inventory.somethingelse.yaml",
        "something.somethingelse.yml",
        "something.somethingelse.yaml",
    ],
)
def test_verify_file_bad_config(inventory, file_name):
    assert inventory.verify_file(file_name) is False


@pytest.mark.parametrize(
    "guest_os_info,annotations,expected",
    [
        ({"id": "mswindows"}, {}, True),
        ({}, {"kubevirt.io/preference-name": "windows.2k22"}, True),
        ({}, {"vm.kubevirt.io/os": "windows2k22"}, True),
        ({}, {}, False),
        ({"id": "fedora"}, {}, False),
        (
            {"id": "fedora"},
            {"kubevirt.io/cluster-preference-name": "windows.2k22"},
            False,
        ),
        ({"id": "fedora"}, {"kubevirt.io/preference-name": "windows.2k22"}, False),
        ({"id": "fedora"}, {"vm.kubevirt.io/os": "windows2k22"}, False),
        (
            {},
            {
                "kubevirt.io/cluster-preference-name": "fedora",
                "kubevirt.io/preference-name": "windows.2k22",
            },
            False,
        ),
        (
            {},
            {
                "kubevirt.io/cluster-preference-name": "fedora",
                "vm.kubevirt.io/os": "windows2k22",
            },
            False,
        ),
        (
            {},
            {
                "kubevirt.io/preference-name": "fedora",
                "vm.kubevirt.io/os": "windows2k22",
            },
            False,
        ),
    ],
)
def test_is_windows(inventory, guest_os_info, annotations, expected):
    assert inventory.is_windows(guest_os_info, annotations) is expected


@pytest.mark.parametrize(
    "client,vmi,expected",
    [
        ({"vmis": [BASIC_VMI]}, BASIC_VMI, False),
        ({"vmis": [WINDOWS_VMI_1]}, WINDOWS_VMI_1, True),
        ({"vmis": [WINDOWS_VMI_2]}, WINDOWS_VMI_2, True),
        ({"vmis": [WINDOWS_VMI_3]}, WINDOWS_VMI_3, True),
        ({"vmis": [WINDOWS_VMI_4]}, WINDOWS_VMI_4, True),
    ],
    indirect=["client"],
)
def test_ansible_connection_winrm(inventory, host_vars, client, vmi, expected):
    inventory.get_vmis_for_namespace(client, "", DEFAULT_NAMESPACE, GetVmiOptions())

    host = f"{DEFAULT_NAMESPACE}-{vmi['metadata']['name']}"
    if expected:
        assert host_vars[host]["ansible_connection"] == "winrm"
    else:
        assert "ansible_connection" not in host_vars[host]


@pytest.mark.parametrize(
    "url,host_name",
    [
        ("https://example", "example"),
        ("http://example", "example"),
        ("example.com", "example-com"),
        ("https://example:8080", "example_8080"),
        ("https://example.com:8080", "example-com_8080"),
    ],

)
def test_get_default_host_name(inventory, url, host_name):
    result = inventory.get_default_host_name(url)
    assert result == host_name


@pytest.fixture(scope="module")
def load_balancer_ingress_ip():
    return {
        "spec": {
            "type": "LoadBalancer",
        },
        "status": {
            "loadBalancer": {
                "ingress": [{"ip": "192.168.1.100"}]
            },
        }
    }


@pytest.fixture(scope="module")
def load_balancer_ingress_hostname():
    return {
        "spec": {
            "type": "LoadBalancer",
        },
        "status": {
            "loadBalancer": {
                "ingress": [{"hostname": "test-hostname"}]
            },
        }
    }


@pytest.fixture(scope="module")
def node_port():
    return {
        "spec": {
            "type": "NodePort"
        }
    }


@pytest.fixture(scope="module")
def service_other():
    return {
        "spec": {
            "type": "ClusterIP"
        }
    }


@pytest.mark.parametrize(
    "service,node_name,expected",
    [
        ("service_other", None, None),
        ("load_balancer_ingress_ip", None, "192.168.1.100"),
        ("load_balancer_ingress_hostname", None, "test-hostname"),
        ("node_port", "test-nodename", "test-nodename"),
    ],
)
def test_get_host_from_service(request, inventory, service, node_name, expected):
    result = inventory.get_host_from_service(request.getfixturevalue(service), node_name)
    assert result == expected


@pytest.fixture(scope="module")
def load_balancer_port():
    return {
        "spec": {
            "type": "LoadBalancer",
            "ports": [{"port": "80"}],
        },
    }


@pytest.fixture(scope="module")
def node_port_port():
    return {
        "spec": {
            "type": "NodePort",
            "ports": [{"nodePort": "8080"}],
        }
    }


@pytest.mark.parametrize(
    "service,port",
    [
        ("service_other", None),
        ("load_balancer_port", "80"),
        ("node_port_port", "8080"),
    ],
)
def test_port_from_service(request, inventory, service, port):
    assert port == inventory.get_port_from_service(request.getfixturevalue(service))


def test_parse(monkeypatch, inventory):
    monkeypatch.setattr(inventory, "_read_config_data", lambda path: {"host_format": "default-test"})
    monkeypatch.setattr(inventory, "_get_cache_prefix", lambda _: None)
    monkeypatch.setattr(inventory, "setup", lambda a, b, c: None)

    inventory.parse(inventory, None, "test")
    assert inventory.host_format == "default-test"


@pytest.fixture(scope="module")
def connection_none():
    return None


@pytest.fixture(scope="module")
def connection_not_list():
    return "test"


@pytest.fixture(scope="module")
def connection_list_not_dict():
    return [
        "test",
        "test"
    ]


@pytest.fixture(scope="module")
def connection_list():
    return [
        {
            "name": "test",
        },
    ]


@pytest.fixture(scope="module")
def connection_list_namespace():
    return [
        {
            "name": "test",
            "namespaces": ["test"]
        },
    ]


@pytest.fixture(scope="module")
def connection_with_base_values():
    return [
        {
            "name": "test",
            "namespaces": ["test"],
            "use_service": True,
            "create_groups": True,
            "append_base_domain": True,
            "base_domain": "test-domain"
        },
    ]


@pytest.fixture(scope="module")
def connection_with_network():
    return [
        {
            "name": "test",
            "namespaces": ["test"],
            "use_service": True,
            "create_groups": True,
            "append_base_domain": True,
            "base_domain": "test-domain",
            "network_name": "test-network"
        },
    ]


@pytest.fixture(scope="module")
def connection_with_interface():
    return [
        {
            "name": "test",
            "namespaces": ["test"],
            "use_service": True,
            "create_groups": True,
            "append_base_domain": True,
            "base_domain": "test-domain",
            "interface_name": "test-interface"
        },
    ]


def vmi_options_base_values():
    return GetVmiOptions(use_service=True,
                         create_groups=True,
                         append_base_domain=True,
                         base_domain="test-domain"
                         )


def vmi_options_with_network():
    return GetVmiOptions(use_service=True,
                         create_groups=True,
                         append_base_domain=True,
                         base_domain="test-domain",
                         network_name="test-network"
                         )


def vmi_options_with_interface():
    return GetVmiOptions(use_service=True,
                         create_groups=True,
                         append_base_domain=True,
                         base_domain="test-domain",
                         network_name="test-interface"
                         )


@pytest.mark.parametrize(
    "connections,result,default_namespace",
    [

        ("connection_list", {"name": "test", "namespace": DEFAULT_NAMESPACE, "opts": GetVmiOptions()}, True),
        ("connection_list_namespace", {"name": "test", "namespace": "test", "opts": GetVmiOptions()}, False),
        ("connection_with_base_values", {"name": "test", "namespace": "test", "opts": vmi_options_base_values()}, False),
        ("connection_with_network", {"name": "test", "namespace": "test", "opts": vmi_options_with_network()}, False),
        ("connection_with_interface", {"name": "test", "namespace": "test", "opts": vmi_options_with_interface()}, False),
        ("connection_none", {"name": "default-hostname", "namespace": DEFAULT_NAMESPACE, "opts": GetVmiOptions()}, True),
    ],
)
def test_fetch_objects(request, mocker, monkeypatch, inventory, connections, result, default_namespace):
    monkeypatch.setattr(kubevirt, "get_api_client", lambda **_: mocker.Mock())
    monkeypatch.setattr(inventory, "get_default_host_name", lambda _: "default-hostname")
    monkeypatch.setattr(inventory, "get_cluster_domain", lambda _: None)

    get_vmis_for_namespace = mocker.patch.object(inventory, "get_vmis_for_namespace")
    get_available_namespaces = mocker.patch.object(inventory, "get_available_namespaces")

    if default_namespace:
        get_available_namespaces.return_value = [DEFAULT_NAMESPACE]
        inventory.fetch_objects(request.getfixturevalue(connections))
        get_available_namespaces.assert_called_once_with(mocker.ANY)
    else:
        inventory.fetch_objects(request.getfixturevalue(connections))
        get_available_namespaces.assert_not_called()

    get_vmis_for_namespace.assert_called_once_with(mocker.ANY,
                                                   result["name"],
                                                   result["namespace"],
                                                   result["opts"])


@pytest.mark.parametrize(
    "connections,result",
    [
        ("connection_not_list", "Expecting connections to be a list."),
        ("connection_list_not_dict", "Expecting connection to be a dictionary."),
    ],
)
def test_fetch_objects_exceptions(request, inventory, connections, result):
    with pytest.raises(KubeVirtInventoryException, match=result):
        inventory.fetch_objects(request.getfixturevalue(connections))


# Exceptions?
@pytest.mark.parametrize(
    "client,result",
    [
        ({"namespaces": [{"metadata": {"name": DEFAULT_NAMESPACE}}]}, DEFAULT_BASE_DOMAIN)

    ],
    indirect=["client"],
)
def test_get_cluster_domain(inventory, client, result):
    assert result == inventory.get_cluster_domain(client)


@pytest.fixture(scope="module")
def get_default_namespace_list():
    return [
        DEFAULT_NAMESPACE
    ]


@pytest.fixture(scope="module")
def get_multiple_namespace_list():
    return [
        DEFAULT_NAMESPACE,
        "test"
    ]


# Exceptions?
@pytest.mark.parametrize(
    "client,result",
    [
        ({"namespaces": [{"metadata": {"name": DEFAULT_NAMESPACE}}]}, "get_default_namespace_list"),
        ({"namespaces": [{"metadata": {"name": DEFAULT_NAMESPACE}}, {"metadata": {"name": "test"}}]}, "get_multiple_namespace_list")
    ],
    indirect=["client"],
)
def test_get_available_namespaces(request, inventory, client, result):
    assert request.getfixturevalue(result) == inventory.get_available_namespaces(client)


@pytest.fixture(scope="module")
def inventory_empty():
    return []


@pytest.fixture(scope="module")
def inventory_groups():
    return [
        "test",
        "namespace_default",
    ]


@pytest.fixture(scope="module")
def inventory_vmi_group():
    return ["default-testvmi"]


@pytest.fixture(scope="module")
def children_group_without_vmi():
    return {
        "test": [
            "namespace_default"
        ],
    }


@pytest.fixture(scope="module")
def children_group_with_vmi(children_group_without_vmi):
    return children_group_without_vmi | {
        "namespace_default": [
            "default-testvmi"
        ]
    }


@pytest.fixture(scope="module")
def children_group_with_vmi_create_groups_option(children_group_with_vmi):
    return children_group_with_vmi | {
        "label_kubevirt_io_domain_test_domain": [
            "default-testvmi"
        ]
    }


@pytest.fixture(scope="function")
def inventory_groups_create_groups_option(inventory_groups):
    inv = copy.deepcopy(inventory_groups)
    inv.append("label_kubevirt_io_domain_test_domain")
    return inv


@pytest.fixture(scope="module")
def base_vmi_host_vars():
    return {}


@pytest.fixture(scope="module")
def basic_vmi_host_vars():
    return {
        "default-testvmi": {
            "object_type": "vmi",
            "labels": {'kubevirt.io/domain': 'test-domain'},
            "annotations": {},
            "cluster_name": {},
            "resource_version": {},
            "uid": "f8abae7c-d792-4b9b-af95-62d322ae5bc1",
            "vmi_active_pods": {},
            "vmi_conditions": [],
            "vmi_guest_os_info": {},
            "vmi_interfaces": [{"ipAddress": "10.10.10.10"}],
            "vmi_launcher_container_image_version": {},
            "vmi_migration_method": {},
            "vmi_migration_transport": {},
            "vmi_node_name": {},
            "vmi_phase": {},
            "vmi_phase_transition_timestamps": [],
            "vmi_qos_class": {},
            "vmi_virtual_machine_revision_name": {},
            "vmi_volume_status": [],
        }
    }


@pytest.fixture(scope="module")
def complete_vmi_host_vars(basic_vmi_host_vars):
    vmi = basic_vmi_host_vars["default-testvmi"] | {

        "labels": {"kubevirt.io/domain": "test-domain"},
        "annotations": {"test-annotation": "test-annotation"},
        "cluster_name": {"test-cluster"},
        "resource_version": {"42"},
        "vmi_active_pods": {"d5b85485-354b-40d3-b6a0-23e18b685310": "node01"},
        "vmi_conditions": [
            {
                "status": True,
                "type": "Ready",
                "lastProbeTime": "null",
                "lastTransitionTime": "null",
            },
        ],
        "vmi_guest_os_info": {"id": "fedora", "version": "39"},
        "vmi_launcher_container_image_version": {"quay.io/kubevirt/virt-launcher:v1.1.0"},
        "vmi_migration_method": "BlockMigration",
        "vmi_migration_transport": "Unix",
        "vmi_node_name": "node01",
        "vmi_phase": "Running",
        "vmi_phase_transition_timestamps": [
            {
                "phase": "Running",
                "phaseTransitionTimestamp": "null",
            },
        ],
        "vmi_qos_class": "Burstable",
        "vmi_virtual_machine_revision_name": "revision-start-vm-12345",
        "vmi_volume_status": [
            {
                "name": "cloudinit",
                "size": 1048576,
                "target": "vdb"
            },
            {
                "name": "containerdisk",
                "target": "vda"
            },
        ],
    }
    vmi = {
        "default-testvmi": vmi
    }
    return vmi


@pytest.fixture(scope="module")
def windows_vmi_host_vars(basic_vmi_host_vars):
    vmi = basic_vmi_host_vars["default-testvmi"] | {
        "ansible_connection": "winrm",
        "vmi_guest_os_info": {"id": "mswindows"},
    }
    vmi = {
        "default-testvmi": vmi
    }
    return vmi


@pytest.mark.parametrize(
    "client,vmi,groups,vmi_group,child_group,create_groups,expected_host_vars,call_functions,windows",
    [
        (
            {"vmis": [BASE_VMI]},
            BASE_VMI,
            "inventory_groups",
            "inventory_empty",
            "children_group_without_vmi",
            False, "base_vmi_host_vars",
            False,
            False,
        ),
        (
            {"vmis": [VMI_WITH_INTERFACE_NO_IPADDRESS]},
            BASE_VMI,
            "inventory_groups",
            "inventory_empty",
            "children_group_without_vmi",
            False,
            "base_vmi_host_vars",
            False,
            False,
        ),
        (
            {"vmis": [BASIC_VMI], "services": [LOADBALANCER_SERVICE]},
            BASIC_VMI,
            "inventory_groups",
            "inventory_vmi_group",
            "children_group_with_vmi",
            False,
            "basic_vmi_host_vars",
            True,
            False,
        ),
        (
            {"vmis": [COMPLETE_VMI], "services": [LOADBALANCER_SERVICE]},
            COMPLETE_VMI,
            "inventory_groups",
            "inventory_vmi_group",
            "children_group_with_vmi",
            False,
            "complete_vmi_host_vars",
            True,
            False,
        ),
        (
            {"vmis": [COMPLETE_VMI], "services": [LOADBALANCER_SERVICE]},
            COMPLETE_VMI,
            "inventory_groups_create_groups_option",
            "inventory_vmi_group",
            "children_group_with_vmi_create_groups_option",
            True,
            "complete_vmi_host_vars",
            True,
            False,
        ),
        (
            {"vmis": [WINDOWS_VMI_1]},
            WINDOWS_VMI_1,
            "inventory_groups",
            "inventory_vmi_group",
            "children_group_with_vmi",
            False,
            "windows_vmi_host_vars",
            True,
            True,
        ),
    ],
    indirect=["client"],
)
def test_get_vmis_for_namespace(mocker,
                                request,
                                inventory,
                                vmi,
                                host_vars,
                                add_group,
                                add_host,
                                add_child,
                                client,
                                groups,
                                vmi_group,
                                child_group,
                                create_groups,
                                expected_host_vars,
                                call_functions,
                                windows,
                                ):
    set_ansible_host_and_port = mocker.patch.object(inventory, "set_ansible_host_and_port")
    set_composable_vars = mocker.patch.object(inventory, "set_composable_vars")

    inventory.get_vmis_for_namespace(client, "test", DEFAULT_NAMESPACE, GetVmiOptions(create_groups=create_groups))

    assert request.getfixturevalue(groups) == add_group
    assert request.getfixturevalue(vmi_group) == add_host
    assert request.getfixturevalue(child_group) == add_child
    assert request.getfixturevalue(expected_host_vars) == host_vars

    if call_functions:
        vmi_name = f"{DEFAULT_NAMESPACE}-{vmi['metadata']['name']}"
        service = (
            None
            if windows
            else LOADBALANCER_SERVICE
        )
        set_ansible_host_and_port.assert_called_once_with(vmi,
                                                          vmi_name,
                                                          vmi["status"]["interfaces"][0]["ipAddress"],
                                                          service,
                                                          GetVmiOptions(create_groups=create_groups)
                                                          )
        set_composable_vars.assert_called_once_with(vmi_name)


@pytest.fixture(scope="module")
def loadbalancer():
    return {
        "test-domain": {
            "apiVersion": "v1",
            "kind": "Service",
            "metadata": {
                "name": "test-service",
            },
            "spec": {
                "selector": {
                    "kubevirt.io/domain": "test-domain",
                },
                "ports": [
                    {
                        "protocol": "TCP",
                        "port": 22,
                        "targetPort": 22
                    }
                ],
                "type": "LoadBalancer"
            },
        },
    }


@pytest.fixture(scope="module")
def nodeport(loadbalancer):
    np = copy.deepcopy(loadbalancer)
    np["test-domain"]["spec"]["type"] = "NodePort"
    return np


@pytest.fixture(scope="module")
def empty_service():
    return {}


@pytest.mark.parametrize(
    "client,result",
    [
        (
            {"services": [LOADBALANCER_SERVICE], "namespaces": [{"metadata": {"name": DEFAULT_NAMESPACE}}]},
            "loadbalancer",
        ),
        (
            {"services": [NODEPORT_SERVICE], "namespaces": [{"metadata": {"name": DEFAULT_NAMESPACE}}]},
            "nodeport",
        ),
        (
            {"services": [BASE_SERVICE], "namespaces": [{"metadata": {"name": DEFAULT_NAMESPACE}}]},
            "empty_service",
        ),
        (
            {"services": [LOADBALANCER_SERVICE_WITHOUT_AND_SELECTOR_PORTS], "namespaces": [{"metadata": {"name": DEFAULT_NAMESPACE}}]},
            "empty_service",
        ),
        (
            {"services": [LOADBALANCER_SERVICE_WITHOUT_SELECTOR_AND_SSH_PORT], "namespaces": [{"metadata": {"name": DEFAULT_NAMESPACE}}]},
            "empty_service",
        ),
        (
            {"services": [LOADBALANCER_SERVICE_WITHOUT_SELECTOR], "namespaces": [{"metadata": {"name": DEFAULT_NAMESPACE}}]},
            "empty_service",
        ),
    ],
    indirect=["client"]
)
def test_get_ssh_services_for_namespace(request, inventory, client, result):
    assert request.getfixturevalue(result) == inventory.get_ssh_services_for_namespace(client, DEFAULT_NAMESPACE)


@pytest.fixture(scope="module")
def ansible_host_and_port_network():
    return {
        "default-testvmi": {
            "ansible_host": "test-network.testvmi.default.vm",
            "ansible_port": None,
        }
    }


@pytest.fixture(scope="module")
def ansible_host_and_port_network_with_base_domain():
    return {
        "default-testvmi": {
            "ansible_host": "test-network.testvmi.default.vm.example.com",
            "ansible_port": None,
        }
    }


@pytest.fixture(scope="module")
def ansible_host_and_port_service():
    return {
        "default-testvmi": {
            "ansible_host": "test-host",
            "ansible_port": "8080",
        }
    }


@pytest.fixture(scope="module")
def ansible_host_and_port_service_ip():
    return {
        "default-testvmi": {
            "ansible_host": "10.10.10.10",
            "ansible_port": None,
        }
    }


@pytest.mark.parametrize(
    "vmi,use_service,opts,result",
    [
        (
            BASIC_VMI,
            None,
            GetVmiOptions(kube_secondary_dns=True, network_name="test-network"),
            "ansible_host_and_port_network",
        ),
        (
            BASIC_VMI,
            None,
            GetVmiOptions(kube_secondary_dns=True, network_name="test-network", base_domain=DEFAULT_BASE_DOMAIN),
            "ansible_host_and_port_network_with_base_domain",
        ),
        (
            BASIC_VMI,
            {"host": "test-host", "port": "8080"}, GetVmiOptions(use_service=True),
            "ansible_host_and_port_service",
        ),
        (
            BASIC_VMI,
            {"host": None, "port": None}, GetVmiOptions(use_service=True),
            "ansible_host_and_port_service_ip",
        ),
    ],
)
def test_set_ansible_host_and_port(monkeypatch, request, inventory, host_vars, vmi, use_service, opts, result):
    vmi_name = f"{DEFAULT_NAMESPACE}-{vmi['metadata']['name']}"
    service = {}
    if use_service is not None:
        monkeypatch.setattr(inventory, "get_host_from_service", lambda a, b: use_service["host"])
        monkeypatch.setattr(inventory, "get_port_from_service", lambda _: use_service["port"])

    inventory.set_ansible_host_and_port(Dict(vmi), vmi_name, "10.10.10.10", service, opts)

    assert request.getfixturevalue(result) == host_vars
