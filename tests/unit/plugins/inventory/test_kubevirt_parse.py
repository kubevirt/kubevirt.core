# -*- coding: utf-8 -*-
# Copyright 2024 Red Hat, Inc.
# Apache License 2.0 (see LICENSE or http://www.apache.org/licenses/LICENSE-2.0)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest

from ansible_collections.kubevirt.core.plugins.inventory import (
    kubevirt,
)

from ansible_collections.kubevirt.core.plugins.inventory.kubevirt import (
    InventoryOptions,
    KubeVirtInventoryException,
)

from ansible.plugins.inventory import Cacheable


@pytest.mark.parametrize(
    "config_data,expected",
    [
        (
            {},
            InventoryOptions(),
        ),
        (
            {
                "name": "test",
            },
            InventoryOptions(name="test"),
        ),
        (
            {"name": "test", "namespaces": ["test"]},
            InventoryOptions(name="test", namespaces=["test"]),
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
            InventoryOptions(
                use_service=True,
                create_groups=True,
                append_base_domain=True,
                base_domain="test-domain",
                name="test",
                namespaces=["test"],
            ),
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
            InventoryOptions(
                use_service=True,
                create_groups=True,
                append_base_domain=True,
                base_domain="test-domain",
                network_name="test-network",
                name="test",
                namespaces=["test"],
            ),
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
            InventoryOptions(
                use_service=True,
                create_groups=True,
                append_base_domain=True,
                base_domain="test-domain",
                network_name="test-interface",
                name="test",
                namespaces=["test"],
            ),
        ),
    ],
)
def test_config_data_to_opts(mocker, inventory, config_data, expected):
    mocker.patch.object(Cacheable, "cache", new_callable=mocker.PropertyMock)
    mocker.patch.object(inventory, "_read_config_data", return_value=config_data)
    mocker.patch.object(inventory, "get_cache_key")
    mocker.patch.object(inventory, "get_option")
    mocker.patch.object(kubevirt, "get_api_client")
    mocker.patch.object(inventory, "_fetch_objects")
    populate_inventory = mocker.patch.object(inventory, "_populate_inventory")

    inventory.parse(None, None, "", False)

    populate_inventory.assert_called_once_with(mocker.ANY, expected)


@pytest.mark.parametrize(
    "cache_parse,cache_option,cache_data,expected",
    [
        (True, True, {"test-key": {"something": "something"}}, True),
        (None, True, {"test-key": {"something": "something"}}, True),
        (False, True, {"test-key": {"something": "something"}}, False),
        (True, False, {"test-key": {"something": "something"}}, False),
        (None, False, {"test-key": {"something": "something"}}, False),
        (False, False, {"test-key": {"something": "something"}}, False),
        (True, True, {"test-key2": {"something": "something"}}, False),
        (None, True, {"test-key2": {"something": "something"}}, False),
    ],
)
def test_use_of_cache(
    mocker, inventory, cache_parse, cache_option, cache_data, expected
):
    path = "/testpath"
    config_data = {"host_format": "test-format"}

    mocker.patch.object(
        Cacheable, "cache", new_callable=mocker.PropertyMock, return_value=cache_data
    )

    read_config_data = mocker.patch.object(
        inventory, "_read_config_data", return_value=config_data
    )
    get_cache_key = mocker.patch.object(
        inventory, "get_cache_key", return_value="test-key"
    )
    get_option = mocker.patch.object(inventory, "get_option", return_value=cache_option)
    get_api_client = mocker.patch.object(kubevirt, "get_api_client")
    fetch_objects = mocker.patch.object(inventory, "_fetch_objects")
    populate_inventory = mocker.patch.object(inventory, "_populate_inventory")

    if cache_parse is None:
        inventory.parse(None, None, path)
    else:
        inventory.parse(None, None, path, cache_parse)

    opts = InventoryOptions(config_data=config_data)
    get_cache_key.assert_called_once_with(path)
    get_option.assert_called_once_with("cache")
    read_config_data.assert_called_once_with(path)
    if expected:
        get_api_client.assert_not_called()
        fetch_objects.assert_not_called()
    else:
        get_api_client.assert_called_once_with(**config_data)
        fetch_objects.assert_called_once_with(mocker.ANY, opts)
    populate_inventory.assert_called_once_with(mocker.ANY, opts)


@pytest.mark.parametrize(
    "present",
    [
        True,
        False,
    ],
)
def test_k8s_client_missing(mocker, inventory, present):
    mocker.patch.object(Cacheable, "cache", new_callable=mocker.PropertyMock)
    mocker.patch.object(kubevirt, "HAS_K8S_MODULE_HELPER", present)
    mocker.patch.object(kubevirt, "get_api_client")
    mocker.patch.object(inventory, "_read_config_data", return_value={})
    mocker.patch.object(inventory, "get_cache_key")
    mocker.patch.object(inventory, "get_option")
    fetch_objects = mocker.patch.object(inventory, "_fetch_objects")

    if present:
        inventory.parse(None, None, "", False)
        fetch_objects.assert_called_once()
    else:
        with pytest.raises(
            KubeVirtInventoryException,
            match="This module requires the Kubernetes Python client. Try `pip install kubernetes`. Detail: None",
        ):
            inventory.parse(None, None, "", False)
        fetch_objects.assert_not_called()
