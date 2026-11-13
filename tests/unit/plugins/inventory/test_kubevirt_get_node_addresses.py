# -*- coding: utf-8 -*-
# Copyright 2026 KubeVirt Project
# Apache License 2.0 (see LICENSE or http://www.apache.org/licenses/LICENSE-2.0)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest
from pytest_mock import MockerFixture
from kubernetes.dynamic.exceptions import DynamicApiError, ResourceNotFoundError
from kubernetes.client.exceptions import ApiException

from ansible_collections.kubevirt.core.plugins.inventory.kubevirt import (
    InventoryModule,
    InventoryOptions,
    KubeVirtInventoryException,
)


@pytest.mark.parametrize("service_type", ["NodePort", "LoadBalancer"])
def test_get_node_addresses_only_associated_nodes_once(
    inventory: InventoryModule, mocker: MockerFixture, service_type: str
) -> None:
    client = mocker.Mock()
    addresses = [{"type": "InternalIP", "address": "192.168.1.60"}]
    client.resources.get.return_value.get.return_value.to_dict.return_value = {
        "status": {"addresses": addresses}
    }
    vmi = {
        "metadata": {"labels": {"kubevirt.io/domain": "test"}},
        "status": {"nodeName": "node.example.com"},
    }
    unassociated_vmi = {
        "metadata": {"labels": {"kubevirt.io/domain": "other"}},
        "status": {"nodeName": "other-node"},
    }
    data = {
        "vmis": [vmi, vmi, unassociated_vmi, {}],
        "services": {"test": [{"spec": {"type": service_type}}]},
    }
    result = inventory._get_node_addresses(
        client, {"namespace1": data, "namespace2": data}
    )
    if service_type == "NodePort":
        assert result == {"node.example.com": addresses}
        client.resources.get.assert_called_once_with(api_version="v1", kind="Node")
        client.resources.get.return_value.get.assert_called_once_with(
            name="node.example.com"
        )
    else:
        assert result == {}
        client.resources.get.assert_not_called()


@pytest.mark.parametrize("discovery_error", [False, True])
@pytest.mark.parametrize(
    "error",
    [
        DynamicApiError(ApiException(status=403, reason="Forbidden")),
        ResourceNotFoundError(),
    ],
)
def test_get_node_addresses_api_errors(
    inventory: InventoryModule,
    mocker: MockerFixture,
    discovery_error: bool,
    error: Exception,
) -> None:
    client = mocker.Mock()
    if discovery_error:
        client.resources.get.side_effect = error
    else:
        client.resources.get.return_value.get.side_effect = error
    namespaces = {
        "test": {
            "vmis": [
                {
                    "metadata": {"labels": {"kubevirt.io/domain": "test"}},
                    "status": {"nodeName": "node.example.com"},
                }
            ],
            "services": {"test": [{"spec": {"type": "NodePort"}}]},
        }
    }
    with pytest.raises(
        KubeVirtInventoryException,
        match="Unable to read Node 'node.example.com'.*get access",
    ):
        inventory._get_node_addresses(client, namespaces)


@pytest.mark.parametrize(
    "opts,expected",
    [
        (InventoryOptions(), False),
        (InventoryOptions(node_address_type="InternalIP"), True),
        (InventoryOptions(node_address_type="InternalIP", use_service=False), False),
        (
            InventoryOptions(node_address_type="InternalIP", network_name="secondary"),
            False,
        ),
    ],
)
def test_fetch_objects_node_addresses_opt_in(
    inventory: InventoryModule,
    mocker: MockerFixture,
    opts: InventoryOptions,
    expected: bool,
) -> None:
    mocker.patch.object(
        inventory, "_get_available_namespaces", return_value=["default"]
    )
    mocker.patch.object(inventory, "_get_vms_for_namespace", return_value=[])
    mocker.patch.object(inventory, "_get_vmis_for_namespace", return_value=[])
    mocker.patch.object(inventory, "_get_cluster_domain", return_value=None)
    read_nodes = mocker.patch.object(inventory, "_get_node_addresses", return_value={})
    result = inventory._fetch_objects(mocker.Mock(), opts)
    assert ("node_addresses" in result) == expected
    assert read_nodes.call_count == int(expected)


def test_inventory_options_invalid_node_address_type() -> None:
    with pytest.raises(
        KubeVirtInventoryException, match="Unsupported node_address_type"
    ):
        InventoryOptions(config_data={"node_address_type": "internalip"})
