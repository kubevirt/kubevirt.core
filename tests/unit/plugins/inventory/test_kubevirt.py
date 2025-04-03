# -*- coding: utf-8 -*-
# Copyright 2024 Red Hat, Inc.
# Apache License 2.0 (see LICENSE or http://www.apache.org/licenses/LICENSE-2.0)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest

from ansible_collections.kubevirt.core.plugins.inventory.kubevirt import (
    InventoryModule,
    InventoryOptions,
)

from ansible_collections.kubevirt.core.tests.unit.plugins.inventory.constants import (
    DEFAULT_BASE_DOMAIN,
)


@pytest.mark.parametrize(
    "host,expected",
    [
        ("https://example", "example"),
        ("http://example", "example"),
        ("example.com", "example-com"),
        ("https://example:8080", "example_8080"),
        ("https://example.com:8080", "example-com_8080"),
    ],
)
def test_get_default_hostname(host, expected):
    assert InventoryModule._get_default_hostname(host) == expected


@pytest.mark.parametrize(
    "name,expected",
    [
        ("lowercase", "lowercase"),
        ("ONLYUPPERCASE", "onlyuppercase"),
        ("snake_case", "snake_case"),
        ("snake_CASE", "snake_case"),
        ("TestNameOne", "test_name_one"),
        ("TestNameTWO", "test_name_two"),
    ],
)
def test_format_var_name(name, expected):
    assert InventoryModule._format_var_name(name) == expected


@pytest.mark.parametrize(
    "obj,expected",
    [
        ({}, False),
        ({"spec": {}}, False),
        ({"status": {}}, False),
        ({"metadata": {}}, False),
        ({"spec": {}, "status": {}}, False),
        ({"spec": {}, "metadata": {}}, False),
        ({"status": {}, "metadata": {}}, False),
        ({"spec": {}, "status": {}, "metadata": {}}, False),
        ({"spec": {}, "status": {}, "metadata": {}, "something": {}}, False),
        ({"spec": {}, "status": {}, "metadata": {"name": "test"}}, False),
        ({"spec": {}, "status": {}, "metadata": {"namespace": "test"}}, False),
        ({"spec": {}, "status": {}, "metadata": {"uid": "test"}}, False),
        (
            {
                "spec": {},
                "status": {},
                "metadata": {"name": "test", "namespace": "test"},
            },
            False,
        ),
        (
            {
                "spec": {},
                "status": {},
                "metadata": {"name": "test", "namespace": "test", "something": "test"},
            },
            False,
        ),
        (
            {"spec": {}, "status": {}, "metadata": {"name": "test", "uid": "test"}},
            False,
        ),
        (
            {
                "spec": {},
                "status": {},
                "metadata": {"name": "test", "namespace": "test", "uid": "test"},
            },
            True,
        ),
    ],
)
def test_obj_is_valid(obj, expected):
    assert InventoryModule._obj_is_valid(obj) == expected


@pytest.mark.parametrize(
    "services,target_port,expected",
    [
        ([], 1234, None),
        ([{"spec": {"something": "something"}}], 1234, None),
        ([{"spec": {"ports": []}}], 1234, None),
        ([{"spec": {"ports": [{"port": 1234}]}}], 1234, None),
        ([{"spec": {"ports": [{"targetPort": 2222}]}}], 1234, None),
        (
            [{"spec": {"ports": [{"targetPort": 1234}]}}],
            1234,
            {"spec": {"ports": [{"targetPort": 1234}]}},
        ),
        (
            [
                {
                    "metadata": {"name": "first"},
                    "spec": {"ports": [{"targetPort": 1234}]},
                },
                {
                    "metadata": {"name": "second"},
                    "spec": {"ports": [{"targetPort": 1234}]},
                },
            ],
            1234,
            {"metadata": {"name": "first"}, "spec": {"ports": [{"targetPort": 1234}]}},
        ),
        (
            [
                {
                    "metadata": {"name": "first"},
                    "spec": {"ports": [{"targetPort": 2222}]},
                },
                {
                    "metadata": {"name": "second"},
                    "spec": {"ports": [{"targetPort": 1234}]},
                },
            ],
            1234,
            {"metadata": {"name": "second"}, "spec": {"ports": [{"targetPort": 1234}]}},
        ),
    ],
)
def test_find_service_with_target_port(services, target_port, expected):
    assert (
        InventoryModule._find_service_with_target_port(services, target_port)
        == expected
    )


@pytest.mark.parametrize(
    "service,node_name,expected",
    [
        ({}, None, None),
        ({"spec": {"something": "something"}}, None, None),
        ({"spec": {"type": "ClusterIP"}}, None, None),
        ({"spec": {"type": "LoadBalancer"}}, None, None),
        ({"spec": {"type": "LoadBalancer"}, "status": {}}, None, None),
        (
            {"spec": {"type": "LoadBalancer"}, "status": {"loadBalancer": {}}},
            None,
            None,
        ),
        (
            {
                "spec": {
                    "type": "LoadBalancer",
                },
                "status": {"loadBalancer": {"ingress": [{"ip": "192.168.1.100"}]}},
            },
            None,
            "192.168.1.100",
        ),
        (
            {
                "spec": {
                    "type": "LoadBalancer",
                },
                "status": {
                    "loadBalancer": {"ingress": [{"hostname": "test-hostname"}]},
                },
            },
            None,
            "test-hostname",
        ),
        (
            {
                "spec": {
                    "type": "LoadBalancer",
                },
                "status": {
                    "loadBalancer": {
                        "ingress": [
                            {"hostname": "test-hostname", "ip": "192.168.1.100"}
                        ]
                    },
                },
            },
            None,
            "test-hostname",
        ),
        ({"spec": {"type": "NodePort"}}, "test-nodename", "test-nodename"),
    ],
)
def test_get_host_from_service(service, node_name, expected):
    assert InventoryModule._get_host_from_service(service, node_name) == expected


@pytest.mark.parametrize(
    "service,expected",
    [
        ({}, None),
        ({"spec": {"type": "LoadBalancer", "ports": []}}, None),
        ({"spec": {"type": "ClusterIP"}}, None),
        (
            {
                "spec": {
                    "type": "LoadBalancer",
                    "ports": [{"garbage": "80"}],
                },
            },
            None,
        ),
        (
            {
                "spec": {
                    "type": "NodePort",
                    "ports": [{"garbage": "8080"}],
                }
            },
            None,
        ),
        (
            {
                "spec": {
                    "type": "LoadBalancer",
                    "ports": [{"port": "80"}],
                },
            },
            "80",
        ),
        (
            {
                "spec": {
                    "type": "NodePort",
                    "ports": [{"nodePort": "8080"}],
                }
            },
            "8080",
        ),
    ],
)
def test_port_from_service(service, expected):
    assert InventoryModule._get_port_from_service(service) == expected


@pytest.mark.parametrize(
    "guest_os_info,annotations,expected",
    [
        (None, None, False),
        ({}, {}, False),
        ({"id": "mswindows"}, None, True),
        ({"id": "mswindows"}, {}, True),
        (None, {"kubevirt.io/preference-name": "windows.2k22"}, True),
        ({}, {"kubevirt.io/preference-name": "windows.2k22"}, True),
        (None, {"kubevirt.io/cluster-preference-name": "windows.2k22"}, True),
        ({}, {"kubevirt.io/cluster-preference-name": "windows.2k22"}, True),
        (None, {"vm.kubevirt.io/os": "windows2k22"}, True),
        ({}, {"vm.kubevirt.io/os": "windows2k22"}, True),
        ({"id": "fedora"}, None, False),
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
def test_is_windows(guest_os_info, annotations, expected):
    assert InventoryModule._is_windows(guest_os_info, annotations) == expected


def test_get_cluster_domain(inventory, client):
    assert inventory._get_cluster_domain(client) == DEFAULT_BASE_DOMAIN


@pytest.mark.parametrize(
    "results,expected",
    [
        (
            {
                "cluster_domain": "example.com",
                "default_hostname": "test",
                "namespaces": {},
            },
            0,
        ),
        (
            {
                "cluster_domain": "example.com",
                "default_hostname": "test",
                "namespaces": {"test": {"vms": [], "vmis": [], "services": {}}},
            },
            1,
        ),
        (
            {
                "cluster_domain": "example.com",
                "default_hostname": "test",
                "namespaces": {
                    "test": {"vms": [], "vmis": [], "services": {}},
                    "test2": {"vms": [], "vmis": [], "services": {}},
                },
            },
            2,
        ),
    ],
)
def test_populate_inventory(mocker, inventory, results, expected):
    populate_inventory_from_namespace = mocker.patch.object(
        inventory, "_populate_inventory_from_namespace"
    )

    inventory._populate_inventory(results, InventoryOptions())

    opts = InventoryOptions(
        base_domain=results["cluster_domain"], name=results["default_hostname"]
    )
    calls = [
        mocker.call(namespace, data, opts)
        for namespace, data in results["namespaces"].items()
    ]
    populate_inventory_from_namespace.assert_has_calls(calls)
    assert len(calls) == expected


@pytest.mark.parametrize(
    "labels,expected",
    [
        ({}, []),
        ({"testkey": "testval"}, ["label_testkey_testval"]),
        (
            {"testkey1": "testval", "testkey2": "testval"},
            ["label_testkey1_testval", "label_testkey2_testval"],
        ),
    ],
)
def test_set_groups_from_labels(inventory, groups, labels, expected):
    hostname = "default-testvm"
    inventory._set_groups_from_labels(hostname, labels)
    for group in expected:
        assert group in groups
        assert hostname in groups[group]["children"]
