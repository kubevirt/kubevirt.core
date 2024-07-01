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
    merge_dicts,
)

BASE_VMI = {
    "metadata": {
        "name": "testvmi",
        "namespace": "default",
    },
    "status": {
        "interfaces": [{"ipAddress": "10.10.10.10"}],
    },
}
WINDOWS_VMI_1 = merge_dicts(
    BASE_VMI,
    {
        "status": {
            "guestOSInfo": {"id": "mswindows"},
        }
    },
)
WINDOWS_VMI_2 = merge_dicts(
    BASE_VMI,
    {
        "metadata": {
            "annotations": {"kubevirt.io/cluster-preference-name": "windows.2k22"}
        },
    },
)
WINDOWS_VMI_3 = merge_dicts(
    BASE_VMI,
    {
        "metadata": {"annotations": {"kubevirt.io/preference-name": "windows.2k22"}},
    },
)
WINDOWS_VMI_4 = merge_dicts(
    BASE_VMI,
    {
        "metadata": {"annotations": {"vm.kubevirt.io/os": "windows2k22"}},
    },
)


@pytest.mark.parametrize(
    "client,vmi,expected",
    [
        ({"vmis": [BASE_VMI]}, BASE_VMI, False),
        ({"vmis": [WINDOWS_VMI_1]}, WINDOWS_VMI_1, True),
        ({"vmis": [WINDOWS_VMI_2]}, WINDOWS_VMI_2, True),
        ({"vmis": [WINDOWS_VMI_3]}, WINDOWS_VMI_3, True),
        ({"vmis": [WINDOWS_VMI_4]}, WINDOWS_VMI_4, True),
    ],
    indirect=["client"],
)
def test_ansible_connection_winrm(inventory, hosts, client, vmi, expected):
    inventory.populate_inventory_from_namespace(
        client, "", DEFAULT_NAMESPACE, InventoryOptions()
    )

    host = f"{DEFAULT_NAMESPACE}-{vmi['metadata']['name']}"
    if expected:
        assert hosts[host]["ansible_connection"] == "winrm"
    else:
        assert "ansible_connection" not in hosts[host]
