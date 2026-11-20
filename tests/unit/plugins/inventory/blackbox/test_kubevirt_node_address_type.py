# -*- coding: utf-8 -*-
# Copyright 2026 KubeVirt Project
# Apache License 2.0 (see LICENSE or http://www.apache.org/licenses/LICENSE-2.0)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from copy import deepcopy
import json
from typing import Any, Dict, List, Optional

import pytest

from ansible_collections.kubevirt.core.plugins.inventory.kubevirt import (
    InventoryModule,
    InventoryOptions,
    KubeVirtInventoryException,
)

RESULTS = {
    "default_hostname": "testcluster",
    "cluster_domain": "example.com",
    "node_addresses": {
        "node.example.com": [
            {"type": "Hostname", "address": "node.example.com"},
            {"type": "InternalIP", "address": "192.168.1.60"},
            {"type": "ExternalIP", "address": "203.0.113.60"},
            {"type": "InternalDNS", "address": "internal.example.com"},
            {"type": "ExternalDNS", "address": "external.example.com"},
            {"type": "InternalIP", "address": "fd00::60"},
        ]
    },
    "namespaces": {
        "default": {
            "vms": [],
            "vmis": [
                {
                    "metadata": {
                        "name": "test",
                        "namespace": "default",
                        "uid": "vmi-uid",
                        "labels": {"kubevirt.io/domain": "test"},
                    },
                    "spec": {},
                    "status": {
                        "nodeName": "node.example.com",
                        "interfaces": [{"name": "default", "ipAddress": "10.128.0.97"}],
                    },
                }
            ],
            "services": {
                "test": [
                    {
                        "metadata": {
                            "name": "remote",
                            "namespace": "default",
                            "uid": "svc-uid",
                        },
                        "spec": {
                            "type": "NodePort",
                            "ports": [
                                {"targetPort": 22, "nodePort": 30514, "port": 2022}
                            ],
                        },
                        "status": {
                            "loadBalancer": {"ingress": [{"ip": "203.0.113.100"}]}
                        },
                    }
                ]
            },
        }
    },
}


@pytest.mark.parametrize(
    "address_type,expected",
    [
        (None, "node.example.com"),
        ("InternalIP", "192.168.1.60"),
        ("ExternalIP", "203.0.113.60"),
        ("Hostname", "node.example.com"),
        ("InternalDNS", "internal.example.com"),
        ("ExternalDNS", "external.example.com"),
    ],
)
def test_node_address_type_cached_inventory(
    inventory: InventoryModule,
    hosts: Dict[str, Dict[str, Any]],
    address_type: Optional[str],
    expected: str,
) -> None:
    results = json.loads(json.dumps(RESULTS))
    inventory._populate_inventory(
        results, InventoryOptions(node_address_type=address_type)
    )
    assert hosts["default-test"]["ansible_host"] == expected
    assert hosts["default-test"]["ansible_port"] == 30514
    assert results == RESULTS


@pytest.mark.parametrize(
    "addresses",
    [
        None,
        {},
        {"node.example.com": []},
        {"node.example.com": [{"type": "InternalIP", "address": ""}]},
    ],
)
def test_node_address_type_missing_fails(
    inventory: InventoryModule,
    hosts: Dict[str, Dict[str, Any]],
    addresses: Optional[Dict[str, List[Dict[str, str]]]],
) -> None:
    results = deepcopy(RESULTS)
    results["node_addresses"] = addresses
    with pytest.raises(
        KubeVirtInventoryException, match="no address of type 'InternalIP'"
    ):
        inventory._populate_inventory(
            results, InventoryOptions(node_address_type="InternalIP")
        )
    assert "ansible_host" not in hosts["default-test"]


@pytest.mark.parametrize("node_name", [None, "unknown-node"])
def test_node_address_type_missing_node_fails(
    inventory: InventoryModule,
    hosts: Dict[str, Dict[str, Any]],
    node_name: Optional[str],
) -> None:
    results = deepcopy(RESULTS)
    results["namespaces"]["default"]["vmis"][0]["status"]["nodeName"] = node_name
    with pytest.raises(KubeVirtInventoryException, match="no address of type"):
        inventory._populate_inventory(
            results, InventoryOptions(node_address_type="InternalIP")
        )


@pytest.mark.parametrize(
    "address_type,expected",
    [(None, "node.example.com.example.com"), ("InternalIP", "192.168.1.60")],
)
def test_node_address_type_append_domain(
    inventory: InventoryModule,
    hosts: Dict[str, Dict[str, Any]],
    address_type: Optional[str],
    expected: str,
) -> None:
    inventory._populate_inventory(
        deepcopy(RESULTS),
        InventoryOptions(node_address_type=address_type, append_base_domain=True),
    )
    assert hosts["default-test"]["ansible_host"] == expected


def test_node_address_type_ipv6_first(
    inventory: InventoryModule, hosts: Dict[str, Dict[str, Any]]
) -> None:
    results = deepcopy(RESULTS)
    results["node_addresses"]["node.example.com"].insert(
        0, {"type": "InternalIP", "address": "fd00::60"}
    )
    inventory._populate_inventory(
        results, InventoryOptions(node_address_type="InternalIP")
    )
    assert hosts["default-test"]["ansible_host"] == "fd00::60"


@pytest.mark.parametrize(
    "mode,expected,port",
    [
        ("loadbalancer", "203.0.113.100", 2022),
        ("disabled", "10.128.0.97", None),
        ("network", "10.128.0.97", None),
        ("no-service", "10.128.0.97", None),
    ],
)
def test_node_address_type_unrelated_connections(
    inventory: InventoryModule,
    hosts: Dict[str, Dict[str, Any]],
    mode: str,
    expected: str,
    port: Optional[int],
) -> None:
    results = deepcopy(RESULTS)
    results.pop("node_addresses")
    opts = InventoryOptions(node_address_type="InternalIP")
    if mode == "loadbalancer":
        results["namespaces"]["default"]["services"]["test"][0]["spec"][
            "type"
        ] = "LoadBalancer"
    elif mode == "disabled":
        opts.use_service = False
    elif mode == "network":
        opts.network_name = "default"
    else:
        results["namespaces"]["default"]["services"] = {}
    inventory._populate_inventory(results, opts)
    assert hosts["default-test"]["ansible_host"] == expected
    assert hosts["default-test"]["ansible_port"] == port
