# -*- coding: utf-8 -*-
# Copyright 2024 Red Hat, Inc.
# Apache License 2.0 (see LICENSE or http://www.apache.org/licenses/LICENSE-2.0)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest

from ansible.errors import AnsibleError

from ansible_collections.kubevirt.core.plugins.inventory.kubevirt import (
    KubeVirtInventoryException,
)


def test_config_data_without_connections_ignored(inventory):
    config_data = {
        "name": "connection-1",
        "namespaces": ["default"],
        "network_name": "bridge-network",
        "label_selector": "app=test",
    }

    inventory._connections_compatibility(config_data)

    assert config_data["name"] == "connection-1"
    assert config_data["namespaces"] == ["default"]
    assert config_data["network_name"] == "bridge-network"
    assert config_data["label_selector"] == "app=test"


def test_single_connection_supported(inventory):
    config_data = {
        "connections": [
            {
                "name": "connection-1",
                "namespaces": ["default"],
                "network_name": "bridge-network",
                "label_selector": "app=test",
            }
        ],
        "namespaces": ["something"],
        "network_name": "some-network",
        "label_selector": "app=something",
    }

    inventory._connections_compatibility(config_data)

    assert config_data["name"] == "connection-1"
    assert config_data["namespaces"] == ["default"]
    assert config_data["network_name"] == "bridge-network"
    assert config_data["label_selector"] == "app=test"


def test_multiple_connections_not_supported(inventory):
    with pytest.raises(
        AnsibleError, match="Split your connections into multiple configuration files."
    ):
        inventory._connections_compatibility(
            {
                "connections": [
                    {
                        "name": "connection-1",
                    },
                    {
                        "name": "connection-2",
                    },
                ],
            }
        )


@pytest.mark.parametrize(
    "config_data,expected",
    [
        ({"connections": "test"}, "Expecting connections to be a list."),
        (
            {"connections": [["test", "test"]]},
            "Expecting connection to be a dictionary.",
        ),
    ],
)
def test_connections_exceptions(inventory, config_data, expected):
    with pytest.raises(KubeVirtInventoryException, match=expected):
        inventory._connections_compatibility(config_data)
