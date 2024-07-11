# -*- coding: utf-8 -*-
# Copyright 2024 Red Hat, Inc.
# Apache License 2.0 (see LICENSE or http://www.apache.org/licenses/LICENSE-2.0)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from random import choice
from string import ascii_lowercase

import pytest

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
                "spec": {},
                "status": {},
            },
            {},
        ),
        (
            {
                "metadata": {
                    "annotations": {"testanno": "testval"},
                },
                "spec": {},
                "status": {},
            },
            {"annotations": {"testanno": "testval"}},
        ),
        (
            {
                "metadata": {
                    "labels": {"testlabel": "testval"},
                },
                "spec": {},
                "status": {},
            },
            {"labels": {"testlabel": "testval"}},
        ),
        (
            {
                "metadata": {
                    "resourceVersion": "123",
                },
                "spec": {},
                "status": {},
            },
            {"resource_version": "123"},
        ),
        (
            {
                "metadata": {
                    "uid": "48e6ed2c-d8a2-4172-844d-0fe7056aa180",
                },
                "spec": {},
                "status": {},
            },
            {"uid": "48e6ed2c-d8a2-4172-844d-0fe7056aa180"},
        ),
        (
            {
                "metadata": {},
                "spec": {},
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
    inventory._set_common_vars(hostname, prefix, obj, InventoryOptions())

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
    set_groups_from_labels = mocker.patch.object(inventory, "_set_groups_from_labels")

    hostname = "default-testvm"
    labels = {"testkey": "testval"}
    opts = InventoryOptions(create_groups=create_groups)

    inventory._set_common_vars(
        hostname, "prefix", {"metadata": {"labels": labels}, "status": {}}, opts
    )

    if create_groups:
        set_groups_from_labels.assert_called_once_with(hostname, labels)
    else:
        set_groups_from_labels.assert_not_called()


def test_called_by_set_vars_from(mocker, inventory):
    hostname = "default-testvm"
    opts = InventoryOptions()
    obj = {"status": {}}

    set_common_vars = mocker.patch.object(inventory, "_set_common_vars")

    inventory._set_vars_from_vm(hostname, obj, opts)
    inventory._set_vars_from_vmi(hostname, obj, {}, opts)

    set_common_vars.assert_has_calls(
        [
            mocker.call(hostname, "vm", obj, opts),
            mocker.call(hostname, "vmi", obj, opts),
        ]
    )
