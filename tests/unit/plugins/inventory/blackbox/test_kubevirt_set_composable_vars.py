# -*- coding: utf-8 -*-
# Copyright 2024 Red Hat, Inc.
# Apache License 2.0 (see LICENSE or http://www.apache.org/licenses/LICENSE-2.0)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from ansible_collections.kubevirt.core.plugins.inventory.kubevirt import (
    InventoryOptions,
)

from ansible_collections.kubevirt.core.tests.unit.plugins.inventory.constants import (
    DEFAULT_NAMESPACE,
)


VMI = {
    "metadata": {
        "name": "testvmi",
        "namespace": "default",
        "uid": "6ffdef43-6c39-4441-a088-82d319ea5c13",
    },
    "spec": {},
    "status": {
        "interfaces": [{"ipAddress": "10.10.10.10"}],
        "migrationMethod": "BlockMigration",
        "nodeName": "test-node",
        "guestOSInfo": {
            "id": "fedora",
            "versionId": "40",
        },
    },
}


def test_set_composable_vars(
    inventory,
    groups,
    hosts,
):
    inventory._options = {
        "compose": {"set_from_another_var": "vmi_node_name"},
        "groups": {"block_migratable_vmis": "vmi_migration_method == 'BlockMigration'"},
        "keyed_groups": [{"prefix": "fedora", "key": "vmi_guest_os_info.versionId"}],
        "strict": True,
    }
    inventory._populate_inventory(
        {
            "default_hostname": "test",
            "cluster_domain": "test.com",
            "namespaces": {
                "default": {"vms": [], "vmis": [VMI], "services": {}},
            },
        },
        InventoryOptions(),
    )

    host = f"{DEFAULT_NAMESPACE}-testvmi"
    assert hosts[host]["set_from_another_var"] == "test-node"
    assert "block_migratable_vmis" in groups
    assert host in groups["block_migratable_vmis"]["children"]
    assert "fedora_40" in groups
    assert host in groups["fedora_40"]["children"]
