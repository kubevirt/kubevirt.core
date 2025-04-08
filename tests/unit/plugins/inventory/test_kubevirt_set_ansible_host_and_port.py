# -*- coding: utf-8 -*-
# Copyright 2024 Red Hat, Inc.
# Apache License 2.0 (see LICENSE or http://www.apache.org/licenses/LICENSE-2.0)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest

from ansible_collections.kubevirt.core.plugins.inventory.kubevirt import (
    InventoryOptions,
)


@pytest.mark.parametrize(
    "opts",
    [
        InventoryOptions(),
        InventoryOptions(kube_secondary_dns=True),  # needs network_name
        InventoryOptions(use_service=True),  # needs service
    ],
)
def test_use_ip_address_by_default(mocker, inventory, opts):
    set_variable = mocker.patch.object(inventory.inventory, "set_variable")

    hostname = "default-testvm"
    ip_address = "1.1.1.1"

    inventory._set_ansible_host_and_port({}, hostname, ip_address, None, opts)

    set_variable.assert_has_calls(
        [
            mocker.call(hostname, "ansible_host", ip_address),
            mocker.call(hostname, "ansible_port", None),
        ]
    )


@pytest.mark.parametrize(
    "base_domain",
    [
        True,
        False,
    ],
)
def test_kube_secondary_dns(mocker, inventory, base_domain):
    set_variable = mocker.patch.object(inventory.inventory, "set_variable")

    hostname = "default-testvm"
    vmi = {
        "metadata": {"name": "testvm", "namespace": "default"},
        "status": {"interfaces": [{"name": "awesome"}]},
    }

    inventory._set_ansible_host_and_port(
        vmi,
        hostname,
        "1.1.1.1",
        None,
        InventoryOptions(
            kube_secondary_dns=True,
            network_name="awesome",
            base_domain="example.com" if base_domain else None,
        ),
    )

    ansible_host = "awesome.testvm.default.vm"
    if base_domain:
        ansible_host += ".example.com"

    set_variable.assert_has_calls(
        [
            mocker.call(hostname, "ansible_host", ansible_host),
            mocker.call(hostname, "ansible_port", None),
        ]
    )


def test_kube_secondary_dns_precedence_over_service(mocker, inventory):
    set_variable = mocker.patch.object(inventory.inventory, "set_variable")

    hostname = "default-testvm"
    vmi = {
        "metadata": {"name": "testvm", "namespace": "default"},
        "status": {"interfaces": [{"name": "awesome"}]},
    }

    inventory._set_ansible_host_and_port(
        vmi,
        hostname,
        "1.1.1.1",
        {"metadata": {"name": "testsvc"}},
        InventoryOptions(
            kube_secondary_dns=True, network_name="awesome", use_service=True
        ),
    )

    set_variable.assert_has_calls(
        [
            mocker.call(hostname, "ansible_host", "awesome.testvm.default.vm"),
            mocker.call(hostname, "ansible_port", None),
        ]
    )


@pytest.mark.parametrize(
    "service,expected_host,expected_port",
    [
        (
            {
                "spec": {
                    "type": "LoadBalancer",
                    "ports": [{"port": 22}],
                },
                "status": {
                    "loadBalancer": {"ingress": [{"hostname": "testhost.example.com"}]}
                },
            },
            "testhost.example.com",
            22,
        ),
        (
            {
                "spec": {
                    "type": "LoadBalancer",
                    "ports": [{"port": 23}],
                },
                "status": {
                    "loadBalancer": {
                        "ingress": [
                            {"hostname": "testhost.example.com", "ip": "2.2.2.2"}
                        ]
                    }
                },
            },
            "testhost.example.com",
            23,
        ),
        (
            {
                "spec": {
                    "type": "LoadBalancer",
                    "ports": [{"port": 24}],
                },
                "status": {"loadBalancer": {"ingress": [{"ip": "2.2.2.2"}]}},
            },
            "2.2.2.2",
            24,
        ),
        (
            {
                "spec": {
                    "type": "NodePort",
                    "ports": [{"nodePort": 25}],
                },
            },
            "testnode.example.com",
            25,
        ),
    ],
)
def test_service(mocker, inventory, service, expected_host, expected_port):
    set_variable = mocker.patch.object(inventory.inventory, "set_variable")

    hostname = "default-testvm"
    vmi = {
        "status": {
            "nodeName": "testnode.example.com",
        },
    }

    inventory._set_ansible_host_and_port(
        vmi,
        hostname,
        "1.1.1.1",
        service,
        InventoryOptions(use_service=True),
    )

    set_variable.assert_has_calls(
        [
            mocker.call(hostname, "ansible_host", expected_host),
            mocker.call(hostname, "ansible_port", expected_port),
        ]
    )


def test_service_append_base_domain(mocker, inventory):
    set_variable = mocker.patch.object(inventory.inventory, "set_variable")

    hostname = "default-testvm"
    vmi = {
        "status": {
            "nodeName": "testnode",
        },
    }
    service = {
        "spec": {
            "type": "NodePort",
            "ports": [{"nodePort": 25}],
        },
    }
    inventory._set_ansible_host_and_port(
        vmi,
        hostname,
        "1.1.1.1",
        service,
        InventoryOptions(
            use_service=True, append_base_domain=True, base_domain="awesome.com"
        ),
    )

    set_variable.assert_has_calls(
        [
            mocker.call(hostname, "ansible_host", "testnode.awesome.com"),
            mocker.call(hostname, "ansible_port", 25),
        ]
    )


@pytest.mark.parametrize(
    "host,port",
    [
        ("testhost.com", None),
        (None, 22),
        (None, None),
    ],
)
def test_service_fallback(mocker, inventory, host, port):
    set_variable = mocker.patch.object(inventory.inventory, "set_variable")
    mocker.patch.object(inventory, "_get_host_from_service", return_value=host)
    mocker.patch.object(inventory, "_get_port_from_service", return_value=port)

    hostname = "default-testvm"
    vmi = {
        "status": {
            "nodeName": "testnode",
        },
    }
    inventory._set_ansible_host_and_port(
        vmi,
        hostname,
        "1.1.1.1",
        {"something": "something"},
        InventoryOptions(use_service=True),
    )

    set_variable.assert_has_calls(
        [
            mocker.call(hostname, "ansible_host", "1.1.1.1"),
            mocker.call(hostname, "ansible_port", None),
        ]
    )


def test_no_service_if_network_name(mocker, inventory):
    set_variable = mocker.patch.object(inventory.inventory, "set_variable")

    hostname = "default-testvm"
    inventory._set_ansible_host_and_port(
        {},
        hostname,
        "1.2.3.4",
        {"something": "something"},
        InventoryOptions(use_service=True, network_name="awesome"),
    )

    set_variable.assert_has_calls(
        [
            mocker.call(hostname, "ansible_host", "1.2.3.4"),
            mocker.call(hostname, "ansible_port", None),
        ]
    )


@pytest.mark.parametrize(
    "opts,expected",
    [
        (InventoryOptions(), True),
        (InventoryOptions(unset_ansible_port=True), True),
        (InventoryOptions(unset_ansible_port=False), False),
    ],
)
def test_unset_ansible_port(mocker, inventory, opts, expected):
    set_variable = mocker.patch.object(inventory.inventory, "set_variable")

    hostname = "default-testvm"
    ip_address = "1.1.1.1"

    inventory._set_ansible_host_and_port({}, hostname, ip_address, None, opts)

    calls = [mocker.call(hostname, "ansible_host", ip_address)]
    if expected:
        calls.append(mocker.call(hostname, "ansible_port", None))
    set_variable.assert_has_calls(calls)
