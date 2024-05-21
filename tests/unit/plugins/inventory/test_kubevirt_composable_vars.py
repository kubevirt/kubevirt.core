# -*- coding: utf-8 -*-
# Copyright 2024 Red Hat, Inc.
# Apache License 2.0 (see LICENSE or http://www.apache.org/licenses/LICENSE-2.0)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest

from ansible_collections.kubevirt.core.plugins.inventory.kubevirt import (
    InventoryModule,
)

from ansible.template import Templar


@pytest.fixture(scope="function")
def inventory_composable_vars(mocker):
    inventory = InventoryModule()

    inventory.templar = Templar(loader=None)

    inventory._options = {
        "compose": {"block_migratable_vmis": "vmi_migration_method"},
        "strict": True,
        "groups": {"vmi_node_groups": "cluster_name"},
        "keyed_groups": [{"prefix": "fedora", "key": "vmi_guest_os_info.version"}],
    }

    inventory.inventory = mocker.Mock()

    return inventory


@pytest.fixture(scope="function")
def host_vars(monkeypatch, inventory_composable_vars):
    host_vars = {}

    def set_variable(host, key, value):
        if host not in host_vars:
            host_vars[host] = {}
        host_vars[host][key] = value

    monkeypatch.setattr(
        inventory_composable_vars.inventory, "set_variable", set_variable
    )
    return host_vars


@pytest.fixture(scope="function")
def add_group(monkeypatch, inventory_composable_vars):
    groups = []

    def add_group(name):
        if name not in groups:
            groups.append(name)
        return name

    monkeypatch.setattr(inventory_composable_vars.inventory, "add_group", add_group)
    return groups


@pytest.fixture(scope="function")
def add_host(monkeypatch, inventory_composable_vars):
    hosts = []

    def add_host(name, group=None):
        if name not in hosts:
            hosts.append(name)
        if group is not None and group not in hosts:
            hosts.append(group)

    monkeypatch.setattr(inventory_composable_vars.inventory, "add_host", add_host)
    return hosts


@pytest.fixture(scope="function")
def add_child(monkeypatch, inventory_composable_vars):
    children = {}

    def add_child(group, name):
        if group not in children:
            children[group] = []
        if name not in children[group]:
            children[group].append(name)

    monkeypatch.setattr(inventory_composable_vars.inventory, "add_child", add_child)
    return children


@pytest.fixture(scope="module")
def vmi_host_vars():
    return {
        "vmi_migration_method": "BlockMigration",
        "vmi_guest_os_info": {"id": "fedora", "version": "39"},
        "cluster_name": {"test-cluster"},
    }


def test_set_composable_vars(
    inventory_composable_vars,
    mocker,
    host_vars,
    add_group,
    add_child,
    add_host,
    vmi_host_vars,
):
    get_vars = mocker.patch.object(
        inventory_composable_vars.inventory.get_host(), "get_vars"
    )
    get_vars.return_value = vmi_host_vars
    inventory_composable_vars.set_composable_vars("testvmi")

    assert {"testvmi": {"block_migratable_vmis": "BlockMigration"}} == host_vars
    assert ["vmi_node_groups", "fedora_39"] == add_group
    assert {"vmi_node_groups": ["testvmi"]} == add_child
    assert ["testvmi", "fedora_39"] == add_host
