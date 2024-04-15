# -*- coding: utf-8 -*-
# Copyright 2024 Red Hat, Inc.
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest

from addict import Dict

from ansible_collections.kubevirt.core.plugins.inventory.kubevirt import (
    GetVmiOptions,
    InventoryModule,
)

from ansible_collections.kubevirt.core.tests.unit.utils.merge_dicts import (
    merge_dicts,
)

DEFAULT_NAMESPACE = "default"
DEFAULT_BASE_DOMAIN = "example.com"

BASE_VMI = {
    "apiVersion": "kubevirt.io/v1",
    "kind": "VirtualMachineInstance",
    "metadata": {
        "name": "testvmi",
        "namespace": "default",
        "uid": "f8abae7c-d792-4b9b-af95-62d322ae5bc1",
    },
    "spec": {
        "domain": {"devices": {}},
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


@pytest.fixture(scope="function")
def inventory(mocker):
    inventory = InventoryModule()
    inventory.inventory = mocker.Mock()
    mocker.patch.object(inventory, "set_composable_vars")
    return inventory


@pytest.fixture(scope="function")
def host_vars(monkeypatch, inventory):
    host_vars = {}

    def set_variable(host, key, value):
        if host not in host_vars:
            host_vars[host] = {}
        host_vars[host][key] = value

    monkeypatch.setattr(inventory.inventory, "set_variable", set_variable)
    return host_vars


@pytest.fixture(scope="function")
def client(mocker, request):
    namespaces = mocker.Mock()
    namespaces.items = [
        Dict(item)
        for item in request.param.get(
            "namespaces", [{"metadata": {"name": DEFAULT_NAMESPACE}}]
        )
    ]
    vmis = mocker.Mock()
    vmis.items = [Dict(item) for item in request.param.get("vmis", [])]
    services = mocker.Mock()
    services.items = [Dict(item) for item in request.param.get("services", [])]
    dns = Dict(
        {"spec": {"baseDomain": request.param.get("base_domain", DEFAULT_BASE_DOMAIN)}}
    )

    namespace_client = mocker.Mock()
    namespace_client.get = mocker.Mock(return_value=namespaces)
    vmi_client = mocker.Mock()
    vmi_client.get = mocker.Mock(return_value=vmis)
    service_client = mocker.Mock()
    service_client.get = mocker.Mock(return_value=services)
    dns_client = mocker.Mock()
    dns_client.get = mocker.Mock(return_value=dns)

    def resources_get(api_version="", kind=""):
        if api_version.lower() == "v1":
            if kind.lower() == "namespace":
                return namespace_client
            elif kind.lower() == "service":
                return service_client
        elif api_version.lower() == "config.openshift.io/v1" and kind.lower() == "dns":
            return dns_client
        elif (
            "kubevirt.io/" in api_version.lower()
            and kind.lower() == "virtualmachineinstance"
        ):
            return vmi_client

        return None

    client = mocker.Mock()
    client.resources.get = resources_get
    return client


@pytest.mark.parametrize(
    "file_name,expected",
    [
        ("inventory.kubevirt.yml", True),
        ("inventory.kubevirt.yaml", True),
        ("something.kubevirt.yml", True),
        ("something.kubevirt.yaml", True),
        ("inventory.somethingelse.yml", False),
        ("inventory.somethingelse.yaml", False),
        ("something.somethingelse.yml", False),
        ("something.somethingelse.yaml", False),
    ],
)
def test_verify_file(tmp_path, inventory, file_name, expected):
    file = tmp_path / file_name
    file.touch()
    assert inventory.verify_file(str(file)) is expected


@pytest.mark.parametrize(
    "file_name",
    [
        "inventory.kubevirt.yml",
        "inventory.kubevirt.yaml",
        "something.kubevirt.yml",
        "something.kubevirt.yaml",
        "inventory.somethingelse.yml",
        "inventory.somethingelse.yaml",
        "something.somethingelse.yml",
        "something.somethingelse.yaml",
    ],
)
def test_verify_file_bad_config(inventory, file_name):
    assert inventory.verify_file(file_name) is False


@pytest.mark.parametrize(
    "guest_os_info,annotations,expected",
    [
        ({"id": "mswindows"}, {}, True),
        ({}, {"kubevirt.io/preference-name": "windows.2k22"}, True),
        ({}, {"vm.kubevirt.io/os": "windows2k22"}, True),
        ({}, {}, False),
        ({"id": "fedora"}, {}, False),
        (
            {"id": "fedora"},
            {"kubevirt.io/cluster-preference-name": "windows.2k22"},
            False,
        ),
        ({"id": "fedora"}, {"kubevirt.io/preference-name": "windows.2k22"}, False),
        ({"id": "fedora"}, {"vm.kubevirt.io/os": "windows2k22"}, False),
        (
            {},
            {
                "kubevirt.io/cluster-preference-name": "fedora",
                "kubevirt.io/preference-name": "windows.2k22",
            },
            False,
        ),
        (
            {},
            {
                "kubevirt.io/cluster-preference-name": "fedora",
                "vm.kubevirt.io/os": "windows2k22",
            },
            False,
        ),
        (
            {},
            {
                "kubevirt.io/preference-name": "fedora",
                "vm.kubevirt.io/os": "windows2k22",
            },
            False,
        ),
    ],
)
def test_is_windows(inventory, guest_os_info, annotations, expected):
    assert inventory.is_windows(guest_os_info, annotations) is expected


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
def test_ansible_connection_winrm(inventory, host_vars, client, vmi, expected):
    inventory.get_vmis_for_namespace(client, "", DEFAULT_NAMESPACE, GetVmiOptions())

    host = f"{DEFAULT_NAMESPACE}-{vmi['metadata']['name']}"
    if expected:
        assert host_vars[host]["ansible_connection"] == "winrm"
    else:
        assert "ansible_connection" not in host_vars[host]
