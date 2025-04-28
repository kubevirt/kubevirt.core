# -*- coding: utf-8 -*-
# Copyright 2024 Red Hat, Inc.
# Apache License 2.0 (see LICENSE or http://www.apache.org/licenses/LICENSE-2.0)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest

from ansible_collections.kubevirt.core.plugins.inventory.kubevirt import (
    InventoryOptions,
)

from ansible_collections.kubevirt.core.tests.unit.plugins.inventory.constants import (
    DEFAULT_NAMESPACE,
    DEFAULT_BASE_DOMAIN,
)


@pytest.mark.parametrize(
    "client",
    [
        {
            "vms": [{"metadata": {"name": "testvm"}}],
            "vmis": [{"metadata": {"name": "testvmi"}}],
            "services": [{"metadata": {"name": "testsvc"}}],
        },
    ],
    indirect=["client"],
)
def test_get_resources(inventory, client):
    assert inventory._get_resources(client, "v1", "Namespace") == [
        {"metadata": {"name": DEFAULT_NAMESPACE}}
    ]
    assert inventory._get_resources(client, "v1", "Service") == [
        {"metadata": {"name": "testsvc"}}
    ]
    assert inventory._get_resources(client, "config.openshift.io/v1", "DNS") == [
        {"spec": {"baseDomain": DEFAULT_BASE_DOMAIN}}
    ]
    assert inventory._get_resources(client, "kubevirt.io/v1", "VirtualMachine") == [
        {"metadata": {"name": "testvm"}}
    ]
    assert inventory._get_resources(
        client, "kubevirt.io/v1", "VirtualMachineInstance"
    ) == [{"metadata": {"name": "testvmi"}}]


@pytest.mark.parametrize(
    "client,expected",
    [
        (
            {},
            [DEFAULT_NAMESPACE],
        ),
        (
            {
                "namespaces": [
                    {"metadata": {"name": DEFAULT_NAMESPACE}},
                    {"metadata": {"name": "test"}},
                ]
            },
            [DEFAULT_NAMESPACE, "test"],
        ),
        (
            {
                "projects": [
                    {"metadata": {"name": DEFAULT_NAMESPACE}},
                    {"metadata": {"name": "testproject"}},
                ]
            },
            [DEFAULT_NAMESPACE, "testproject"],
        ),
        (
            {
                "namespaces": [
                    {"metadata": {"name": DEFAULT_NAMESPACE}},
                    {"metadata": {"name": "test"}},
                ],
                "projects": [
                    {"metadata": {"name": "testproject"}},
                ],
            },
            ["testproject"],
        ),
    ],
    indirect=["client"],
)
def test_get_available_namespaces(inventory, client, expected):
    assert inventory._get_available_namespaces(client) == expected


@pytest.mark.parametrize(
    "client",
    [
        {
            "vms": [
                {"metadata": {"name": "testvm1"}},
                {"metadata": {"name": "testvm2"}},
            ],
        },
    ],
    indirect=["client"],
)
def test_get_vms_for_namespace(inventory, client):
    assert inventory._get_vms_for_namespace(
        client, DEFAULT_NAMESPACE, InventoryOptions()
    ) == [{"metadata": {"name": "testvm1"}}, {"metadata": {"name": "testvm2"}}]


@pytest.mark.parametrize(
    "client",
    [
        {
            "vmis": [
                {"metadata": {"name": "testvmi1"}},
                {"metadata": {"name": "testvmi2"}},
            ],
        },
    ],
    indirect=["client"],
)
def test_get_vmis_for_namespace(inventory, client):
    assert inventory._get_vmis_for_namespace(
        client, DEFAULT_NAMESPACE, InventoryOptions()
    ) == [{"metadata": {"name": "testvmi1"}}, {"metadata": {"name": "testvmi2"}}]
