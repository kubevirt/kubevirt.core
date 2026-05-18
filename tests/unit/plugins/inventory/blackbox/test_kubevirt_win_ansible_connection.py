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
        "labels": {"kubevirt.io/domain": "testdomain"},
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
SVC_LB_WINRM_HTTPS = {
    "apiVersion": "v1",
    "kind": "Service",
    "metadata": {
        "name": "test-lb-winrm-https",
        "namespace": "default",
        "uid": "22f20931-e47b-4074-a2a8-21fa59073dfd",
    },
    "spec": {
        "ports": [
            {
                "protocol": "TCP",
                "port": 12345,
                "targetPort": 5986,
            },
        ],
        "type": "LoadBalancer",
        "selector": {"kubevirt.io/domain": "testdomain"},
    },
    "status": {"loadBalancer": {"ingress": [{"ip": "192.168.1.100"}]}},
}
SVC_LB_SSH = merge_dicts(
    SVC_LB_WINRM_HTTPS,
    {
        "metadata": {
            "name": "test-lb-ssh",
            "uid": "33a31042-f58c-5044-cf78-ef211cedb1d4",
        },
        "spec": {
            "ports": [
                {
                    "protocol": "TCP",
                    "port": 12345,
                    "targetPort": 22,
                },
            ],
        },
    },
)


@pytest.mark.parametrize(
    "vmi,expected,use_service,default_win_ansible_connection,services",
    [
        (BASE_VMI, False, False, "winrm", [SVC_LB_WINRM_HTTPS]),
        (WINDOWS_VMI_1, True, True, "winrm", [SVC_LB_WINRM_HTTPS]),
        (WINDOWS_VMI_2, True, True, "winrm", [SVC_LB_WINRM_HTTPS]),
        (WINDOWS_VMI_3, True, True, "winrm", [SVC_LB_WINRM_HTTPS]),
        (WINDOWS_VMI_4, True, True, "winrm", [SVC_LB_WINRM_HTTPS]),
        (WINDOWS_VMI_1, True, False, "winrm", [SVC_LB_WINRM_HTTPS]),
        (WINDOWS_VMI_2, True, False, "winrm", [SVC_LB_WINRM_HTTPS]),
        (WINDOWS_VMI_3, True, False, "winrm", [SVC_LB_WINRM_HTTPS]),
        (WINDOWS_VMI_4, True, False, "winrm", [SVC_LB_WINRM_HTTPS]),
        (WINDOWS_VMI_1, True, True, "psrp", [SVC_LB_WINRM_HTTPS]),
        (WINDOWS_VMI_1, True, False, "psrp", [SVC_LB_WINRM_HTTPS]),
        (WINDOWS_VMI_2, True, True, "ansible.builtin.psrp", [SVC_LB_WINRM_HTTPS]),
        (WINDOWS_VMI_3, True, False, "ssh", [SVC_LB_SSH]),
        (WINDOWS_VMI_4, True, True, "ansible.builtin.ssh", [SVC_LB_SSH]),
    ],
)
def test_default_win_ansible_connection(
    inventory,
    hosts,
    vmi,
    expected,
    use_service,
    default_win_ansible_connection,
    services,
):
    inventory._populate_inventory(
        {
            "default_hostname": "test",
            "cluster_domain": "test.com",
            "namespaces": {
                "default": {
                    "vms": [],
                    "vmis": [vmi],
                    "services": {"testdomain": services},
                }
            },
        },
        InventoryOptions(
            use_service=use_service,
            default_win_ansible_connection=default_win_ansible_connection,
        ),
    )

    host = f"{DEFAULT_NAMESPACE}-{vmi['metadata']['name']}"
    if expected:
        assert hosts[host]["ansible_connection"] == default_win_ansible_connection
    else:
        assert "ansible_connection" not in hosts[host]
    if use_service:
        assert hosts[host]["ansible_host"] == "192.168.1.100"
        assert hosts[host]["ansible_port"] == 12345
    else:
        assert hosts[host]["ansible_host"] == "10.10.10.10"
        assert hosts[host]["ansible_port"] is None
