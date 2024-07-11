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

from ansible_collections.kubevirt.core.plugins.inventory import kubevirt


@pytest.mark.parametrize(
    "config_data,expected",
    [
        (
            None,
            {
                "name": "default-hostname",
                "namespaces": [DEFAULT_NAMESPACE],
                "opts": InventoryOptions(),
            },
        ),
        (
            {
                "name": "test",
            },
            {
                "name": "test",
                "namespaces": [DEFAULT_NAMESPACE],
                "opts": InventoryOptions(),
            },
        ),
        (
            {"name": "test", "namespaces": ["test"]},
            {"name": "test", "namespaces": ["test"], "opts": InventoryOptions()},
        ),
        (
            {
                "name": "test",
                "namespaces": ["test"],
                "use_service": True,
                "create_groups": True,
                "append_base_domain": True,
                "base_domain": "test-domain",
            },
            {
                "name": "test",
                "namespaces": ["test"],
                "opts": InventoryOptions(
                    use_service=True,
                    create_groups=True,
                    append_base_domain=True,
                    base_domain="test-domain",
                ),
            },
        ),
        (
            {
                "name": "test",
                "namespaces": ["test"],
                "use_service": True,
                "create_groups": True,
                "append_base_domain": True,
                "base_domain": "test-domain",
                "network_name": "test-network",
            },
            {
                "name": "test",
                "namespaces": ["test"],
                "opts": InventoryOptions(
                    use_service=True,
                    create_groups=True,
                    append_base_domain=True,
                    base_domain="test-domain",
                    network_name="test-network",
                ),
            },
        ),
        (
            {
                "name": "test",
                "namespaces": ["test"],
                "use_service": True,
                "create_groups": True,
                "append_base_domain": True,
                "base_domain": "test-domain",
                "interface_name": "test-interface",
            },
            {
                "name": "test",
                "namespaces": ["test"],
                "opts": InventoryOptions(
                    use_service=True,
                    create_groups=True,
                    append_base_domain=True,
                    base_domain="test-domain",
                    network_name="test-interface",
                ),
            },
        ),
    ],
)
def test_fetch_objects(mocker, inventory, config_data, expected):
    mocker.patch.object(kubevirt, "get_api_client")
    mocker.patch.object(
        inventory, "get_default_host_name", return_value="default-hostname"
    )

    cluster_domain = "test.com"
    mocker.patch.object(inventory, "get_cluster_domain", return_value=cluster_domain)
    expected["opts"].base_domain = expected["opts"].base_domain or cluster_domain

    get_available_namespaces = mocker.patch.object(
        inventory, "get_available_namespaces", return_value=[DEFAULT_NAMESPACE]
    )
    populate_inventory_from_namespace = mocker.patch.object(
        inventory, "populate_inventory_from_namespace"
    )

    inventory.fetch_objects(config_data)

    if config_data and "namespaces" in config_data:
        get_available_namespaces.assert_not_called()
    else:
        get_available_namespaces.assert_called()

    populate_inventory_from_namespace.assert_has_calls(
        [
            mocker.call(mocker.ANY, expected["name"], namespace, expected["opts"])
            for namespace in expected["namespaces"]
        ]
    )
