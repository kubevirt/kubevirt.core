# -*- coding: utf-8 -*-
# Copyright 2024 Red Hat, Inc.
# Apache License 2.0 (see LICENSE or http://www.apache.org/licenses/LICENSE-2.0)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest

from ansible_collections.kubevirt.core.plugins.inventory.kubevirt import (
    InventoryOptions,
    LABEL_KUBEVIRT_IO_DOMAIN,
)


def test_ignore_vmi_without_interface(mocker, inventory):
    mocker.patch.object(inventory, "_set_common_vars")
    set_ansible_host_and_port = mocker.patch.object(
        inventory, "_set_ansible_host_and_port"
    )

    vmi = {"status": {}}
    inventory._set_vars_from_vmi("default-testvm", vmi, {}, InventoryOptions())

    set_ansible_host_and_port.assert_not_called()


def test_use_first_interface_by_default(mocker, inventory):
    mocker.patch.object(inventory, "_set_common_vars")
    set_ansible_host_and_port = mocker.patch.object(
        inventory, "_set_ansible_host_and_port"
    )

    hostname = "default-testvm"
    vmi = {
        "metadata": {},
        "status": {"interfaces": [{"ipAddress": "1.1.1.1"}, {"ipAddress": "2.2.2.2"}]},
    }
    opts = InventoryOptions()
    inventory._set_vars_from_vmi(hostname, vmi, {}, opts)

    set_ansible_host_and_port.assert_called_once_with(
        vmi, hostname, "1.1.1.1", None, opts
    )


def test_use_named_interface(mocker, inventory):
    mocker.patch.object(inventory, "_set_common_vars")
    set_ansible_host_and_port = mocker.patch.object(
        inventory, "_set_ansible_host_and_port"
    )

    hostname = "default-testvm"
    vmi = {
        "metadata": {},
        "status": {
            "interfaces": [
                {"name": "first", "ipAddress": "1.1.1.1"},
                {"name": "second", "ipAddress": "2.2.2.2"},
            ]
        },
    }
    opts = InventoryOptions(network_name="second")
    inventory._set_vars_from_vmi(hostname, vmi, {}, opts)

    set_ansible_host_and_port.assert_called_once_with(
        vmi, hostname, "2.2.2.2", None, opts
    )


def test_ignore_vmi_without_named_interface(mocker, inventory):
    mocker.patch.object(inventory, "_set_common_vars")
    set_ansible_host_and_port = mocker.patch.object(
        inventory, "_set_ansible_host_and_port"
    )

    vmi = {
        "metadata": {},
        "status": {"interfaces": [{"name": "somename", "ipAddress": "1.1.1.1"}]},
    }
    inventory._set_vars_from_vmi(
        "default-testvm", vmi, {}, InventoryOptions(network_name="awesome")
    )

    set_ansible_host_and_port.assert_not_called()


def test_set_winrm_if_windows(mocker, inventory):
    mocker.patch.object(inventory, "_set_common_vars")
    mocker.patch.object(inventory, "_is_windows", return_value=True)
    mocker.patch.object(inventory, "_set_ansible_host_and_port")
    set_variable = mocker.patch.object(inventory.inventory, "set_variable")

    hostname = "default-testvm"
    vmi = {"metadata": {}, "status": {"interfaces": [{"ipAddress": "1.1.1.1"}]}}
    inventory._set_vars_from_vmi(hostname, vmi, {}, InventoryOptions())

    set_variable.assert_called_once_with(hostname, "ansible_connection", "winrm")


@pytest.mark.parametrize(
    "is_windows,target_port",
    [
        (False, 22),
        (True, 5985),
        (True, 5986),
    ],
)
def test_service_lookup(mocker, inventory, is_windows, target_port):
    mocker.patch.object(inventory, "_set_common_vars")
    mocker.patch.object(inventory, "_is_windows", return_value=is_windows)
    set_ansible_host_and_port = mocker.patch.object(
        inventory, "_set_ansible_host_and_port"
    )

    hostname = "default-testvm"
    vmi = {
        "metadata": {"labels": {LABEL_KUBEVIRT_IO_DOMAIN: "testdomain"}},
        "status": {"interfaces": [{"ipAddress": "1.1.1.1"}]},
    }
    opts = InventoryOptions()
    service = {
        "metadata": {"name": "testsvc"},
        "spec": {"ports": [{"targetPort": target_port}]},
    }
    inventory._set_vars_from_vmi(hostname, vmi, {"testdomain": [service]}, opts)

    set_ansible_host_and_port.assert_called_once_with(
        vmi, hostname, "1.1.1.1", service, opts
    )


@pytest.mark.parametrize(
    "is_windows,target_port",
    [
        (True, 22),
        (False, 5985),
        (False, 5986),
    ],
)
def test_service_ignore_not_matching_connection(
    mocker, inventory, is_windows, target_port
):
    mocker.patch.object(inventory, "_set_common_vars")
    mocker.patch.object(inventory, "_is_windows", return_value=is_windows)
    set_ansible_host_and_port = mocker.patch.object(
        inventory, "_set_ansible_host_and_port"
    )

    hostname = "default-testvm"
    vmi = {
        "metadata": {"labels": {LABEL_KUBEVIRT_IO_DOMAIN: "testdomain"}},
        "status": {"interfaces": [{"ipAddress": "1.1.1.1"}]},
    }
    opts = InventoryOptions()
    service = {
        "metadata": {"name": "testsvc"},
        "spec": {"ports": [{"targetPort": target_port}]},
    }
    inventory._set_vars_from_vmi(hostname, vmi, {"testdomain": [service]}, opts)

    set_ansible_host_and_port.assert_called_once_with(
        vmi, hostname, "1.1.1.1", None, opts
    )


def test_service_prefer_winrm_https(mocker, inventory):
    mocker.patch.object(inventory, "_set_common_vars")
    mocker.patch.object(inventory, "_is_windows", return_value=True)
    set_ansible_host_and_port = mocker.patch.object(
        inventory, "_set_ansible_host_and_port"
    )

    hostname = "default-testvm"
    vmi = {
        "metadata": {"labels": {LABEL_KUBEVIRT_IO_DOMAIN: "testdomain"}},
        "status": {"interfaces": [{"ipAddress": "1.1.1.1"}]},
    }
    opts = InventoryOptions()
    service_winrm_http = {
        "metadata": {"name": "svc_winrm_http"},
        "spec": {"ports": [{"targetPort": 5985}]},
    }
    service_winrm_https = {
        "metadata": {"name": "svc_winrm_https"},
        "spec": {"ports": [{"targetPort": 5986}]},
    }
    inventory._set_vars_from_vmi(
        hostname, vmi, {"testdomain": [service_winrm_http, service_winrm_https]}, opts
    )

    set_ansible_host_and_port.assert_called_once_with(
        vmi, hostname, "1.1.1.1", service_winrm_https, opts
    )
