# -*- coding: utf-8 -*-
# Copyright 2024 Red Hat, Inc.
# Apache License 2.0 (see LICENSE or http://www.apache.org/licenses/LICENSE-2.0)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from random import choice
from string import ascii_lowercase

import pytest

from addict import Dict

from ansible_collections.kubevirt.core.plugins.inventory.kubevirt import (
    InventoryOptions,
)


@pytest.mark.parametrize(
    "obj,expected",
    [
        (
            {
                "metadata": {
                    "something": "idontcare",
                },
            },
            {},
        ),
        (
            {
                "metadata": {
                    "annotations": {"testanno": "testval"},
                },
            },
            {"annotations": {"testanno": "testval"}},
        ),
        (
            {
                "metadata": {
                    "labels": {"testlabel": "testval"},
                },
            },
            {"labels": {"testlabel": "testval"}},
        ),
        (
            {
                "metadata": {
                    "resourceVersion": "123",
                },
            },
            {"resource_version": "123"},
        ),
        (
            {
                "metadata": {
                    "uid": "48e6ed2c-d8a2-4172-844d-0fe7056aa180",
                },
            },
            {"uid": "48e6ed2c-d8a2-4172-844d-0fe7056aa180"},
        ),
        (
            {
                "status": {
                    "interfaces": [{"ipAddress": "10.10.10.10"}],
                },
            },
            {"interfaces": [{"ipAddress": "10.10.10.10"}]},
        ),
    ],
)
def test_set_common_vars(inventory, hosts, obj, expected):
    hostname = "default-testvm"
    prefix = "".join(choice(ascii_lowercase) for i in range(5))
    inventory.inventory.add_host(hostname)
    inventory.set_common_vars(hostname, prefix, Dict(obj), InventoryOptions())

    for key, value in expected.items():
        prefixed_key = f"{prefix}_{key}"
        assert prefixed_key in hosts[hostname]
        assert hosts[hostname][prefixed_key] == value


@pytest.mark.parametrize(
    "create_groups",
    [
        True,
        False,
    ],
)
def test_set_common_vars_create_groups(mocker, inventory, create_groups):
    mocker.patch.object(inventory.inventory, "set_variable")
    set_groups_from_labels = mocker.patch.object(inventory, "set_groups_from_labels")

    hostname = "default-testvm"
    labels = {"testkey": "testval"}
    opts = InventoryOptions(create_groups=create_groups)

    inventory.set_common_vars(
        hostname, "prefix", Dict({"metadata": {"labels": labels}}), opts
    )

    if create_groups:
        set_groups_from_labels.assert_called_once_with(hostname, labels)
    else:
        set_groups_from_labels.assert_not_called()


def test_called_by_set_vars_from(mocker, inventory):
    hostname = "default-testvm"
    opts = InventoryOptions()

    set_common_vars = mocker.patch.object(inventory, "set_common_vars")

    inventory.set_vars_from_vm(hostname, Dict(), opts)
    inventory.set_vars_from_vmi(hostname, Dict(), {}, opts)

    set_common_vars.assert_has_calls(
        [mocker.call(hostname, "vm", {}, opts), mocker.call(hostname, "vmi", {}, opts)]
    )
