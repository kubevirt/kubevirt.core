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
        "uid": "e86c603c-fb13-4933-bf67-de100bdba0c3",
    },
    "spec": {},
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
    "vmi,expected",
    [
        (BASE_VMI, False),
        (WINDOWS_VMI_1, True),
        (WINDOWS_VMI_2, True),
        (WINDOWS_VMI_3, True),
        (WINDOWS_VMI_4, True),
    ],
)
def test_ansible_connection_winrm(inventory, hosts, vmi, expected):
    inventory._populate_inventory(
        {
            "default_hostname": "test",
            "cluster_domain": "test.com",
            "namespaces": {
                "default": {"vms": [], "vmis": [vmi], "services": {}},
            },
        },
        InventoryOptions(),
    )

    host = f"{DEFAULT_NAMESPACE}-{vmi['metadata']['name']}"
    if expected:
        assert hosts[host]["ansible_connection"] == "winrm"
    else:
        assert "ansible_connection" not in hosts[host]
