# -*- coding: utf-8 -*-
# Copyright 2026 KubeVirt Project
# Apache License 2.0 (see LICENSE or http://www.apache.org/licenses/LICENSE-2.0)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from copy import deepcopy

import pytest

from ansible_collections.kubevirt.core.plugins.inventory.kubevirt import (
    InventoryOptions,
)


@pytest.mark.parametrize("service_type", ["NodePort", "LoadBalancer"])
@pytest.mark.parametrize("target_port", [22, 5985, 5986])
@pytest.mark.parametrize("management_port_first", [True, False])
def test_multiport_service_connection(
    inventory, hosts, client, mocker, service_type, target_port, management_port_first
):
    management_port = {"port": 2022, "targetPort": target_port, "nodePort": 30514}
    application_port = {"port": 443, "targetPort": 443, "nodePort": 32538}
    ports = [management_port, application_port]
    if not management_port_first:
        ports.reverse()
    service = {
        "metadata": {"name": "test-remote", "namespace": "default", "uid": "svc-uid"},
        "spec": {
            "type": service_type,
            "selector": {"kubevirt.io/domain": "test"},
            "ports": ports,
        },
        "status": {"loadBalancer": {"ingress": [{"ip": "192.168.1.100"}]}},
    }
    original_service = deepcopy(service)
    mocker.patch.object(inventory, "_get_resources", return_value=[service])
    services = inventory._get_services_for_namespace(client, "default")
    assert services == {"test": [service]}
    vmi = {
        "metadata": {
            "name": "test",
            "namespace": "default",
            "uid": "vmi-uid",
            "labels": {"kubevirt.io/domain": "test"},
        },
        "spec": {},
        "status": {
            "nodeName": "node.example.com",
            "interfaces": [{"ipAddress": "10.128.0.97"}],
        },
    }
    if target_port != 22:
        vmi["status"]["guestOSInfo"] = {"id": "mswindows"}
    inventory._populate_inventory(
        {
            "default_hostname": "testcluster",
            "cluster_domain": "example.com",
            "namespaces": {"default": {"vms": [], "vmis": [vmi], "services": services}},
        },
        InventoryOptions(use_service=True),
    )
    host = hosts["default-test"]
    assert host["ansible_host"] == (
        "node.example.com" if service_type == "NodePort" else "192.168.1.100"
    )
    assert host["ansible_port"] == (30514 if service_type == "NodePort" else 2022)
    assert service == original_service


def test_multiport_service_prefers_winrm_https(inventory, hosts, client, mocker):
    service = {
        "metadata": {"name": "remote", "namespace": "default", "uid": "svc-uid"},
        "spec": {
            "type": "NodePort",
            "selector": {"kubevirt.io/domain": "test"},
            "ports": [
                {"targetPort": 22, "nodePort": 30022},
                {"targetPort": 5985, "nodePort": 30585},
                {"targetPort": 5986, "nodePort": 30586},
            ],
        },
        "status": {},
    }
    mocker.patch.object(inventory, "_get_resources", return_value=[service])
    services = inventory._get_services_for_namespace(client, "default")
    vmi = {
        "metadata": {
            "name": "test",
            "namespace": "default",
            "uid": "vmi-uid",
            "labels": {"kubevirt.io/domain": "test"},
        },
        "spec": {},
        "status": {
            "nodeName": "node.example.com",
            "interfaces": [{"ipAddress": "10.128.0.97"}],
            "guestOSInfo": {"id": "mswindows"},
        },
    }
    inventory._populate_inventory(
        {
            "default_hostname": "testcluster",
            "cluster_domain": "example.com",
            "namespaces": {"default": {"vms": [], "vmis": [vmi], "services": services}},
        },
        InventoryOptions(use_service=True),
    )
    assert hosts["default-test"]["ansible_port"] == 30586
