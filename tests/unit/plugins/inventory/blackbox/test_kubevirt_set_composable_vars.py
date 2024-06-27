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
)


VMI = {
    "metadata": {
        "name": "testvmi",
        "namespace": "default",
    },
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


@pytest.mark.parametrize(
    "client",
    [{"vmis": [VMI]}],
    indirect=["client"],
)
def test_set_composable_vars(
    inventory,
    groups,
    hosts,
    client,
):
    inventory._options = {
        "compose": {"set_from_another_var": "vmi_node_name"},
        "groups": {"block_migratable_vmis": "vmi_migration_method == 'BlockMigration'"},
        "keyed_groups": [{"prefix": "fedora", "key": "vmi_guest_os_info.versionId"}],
        "strict": True,
    }
    inventory.populate_inventory_from_namespace(
        client, "", DEFAULT_NAMESPACE, InventoryOptions()
    )

    host = f"{DEFAULT_NAMESPACE}-testvmi"
    assert hosts[host]["set_from_another_var"] == "test-node"
    assert "block_migratable_vmis" in groups
    assert host in groups["block_migratable_vmis"]["children"]
    assert "fedora_40" in groups
    assert host in groups["fedora_40"]["children"]
