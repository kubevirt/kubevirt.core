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
    KubeVirtInventoryException,
)


@pytest.mark.parametrize(
    "cache",
    [
        True,
        False,
    ],
)
def test_parse(mocker, inventory, cache):
    path = "/testpath"
    cache_prefix = "test-prefix"
    config_data = {"host_format": "test-format"}

    mocker.patch.dict(inventory._cache, {cache_prefix: {"test-key": "test-value"}})
    get_cache_prefix = mocker.patch.object(
        inventory, "_get_cache_prefix", return_value=cache_prefix
    )
    read_config_data = mocker.patch.object(
        inventory, "_read_config_data", return_value=config_data
    )
    fetch_objects = mocker.patch.object(inventory, "fetch_objects")

    inventory.parse(None, None, path, cache)

    get_cache_prefix.assert_called_once_with(path)
    read_config_data.assert_called_once_with(path)
    if cache:
        fetch_objects.assert_not_called()
    else:
        fetch_objects.assert_called_once_with(config_data)


@pytest.mark.parametrize(
    "present",
    [
        True,
        False,
    ],
)
def test_k8s_client_missing(mocker, inventory, present):
    mocker.patch.object(kubevirt, "HAS_K8S_MODULE_HELPER", present)
    mocker.patch.object(inventory, "_get_cache_prefix")
    mocker.patch.object(inventory, "_read_config_data")
    fetch_objects = mocker.patch.object(inventory, "fetch_objects")

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
