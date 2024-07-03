# -*- coding: utf-8 -*-
# Copyright 2024 Red Hat, Inc.
# Apache License 2.0 (see LICENSE or http://www.apache.org/licenses/LICENSE-2.0)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest

from addict import Dict

from ansible_collections.kubevirt.core.plugins.inventory.kubevirt import (
    InventoryModule,
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
def test_get_default_host_name(host, expected):
    assert InventoryModule.get_default_host_name(host) == expected


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
    assert InventoryModule.format_var_name(name) == expected


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
    assert InventoryModule.get_host_from_service(service, node_name) == expected


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
    assert InventoryModule.get_port_from_service(service) == expected


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
    assert InventoryModule.is_windows(guest_os_info, annotations) == expected


def test_parse(mocker, inventory):
    path = "/testpath"
    cache_prefix = "test-prefix"
    host_format = "test-format"
    config_data = {"host_format": host_format}
    cache = True

    get_cache_prefix = mocker.patch.object(
        inventory, "_get_cache_prefix", return_value=cache_prefix
    )
    read_config_data = mocker.patch.object(
        inventory, "_read_config_data", return_value=config_data
    )
    setup = mocker.patch.object(inventory, "setup")

    inventory.parse(None, None, path, cache)

    get_cache_prefix.assert_called_once_with(path)
    read_config_data.assert_called_once_with(path)
    setup.assert_called_once_with(config_data, cache, cache_prefix)
    assert inventory.host_format == host_format


def test_get_cluster_domain(inventory, client):
    assert inventory.get_cluster_domain(client) == DEFAULT_BASE_DOMAIN


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
    inventory.set_groups_from_labels(hostname, Dict(labels))
    for group in expected:
        assert group in groups
        assert hostname in groups[group]["children"]
