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
def test_cache_is_used(mocker, inventory, cache):
    connections = [{"test-conn": {}}]
    config_data = {"connections": connections}
    cache_key = "test-prefix"

    mocker.patch.dict(inventory._cache, {cache_key: {"test-key": "test-value"}})
    fetch_objects = mocker.patch.object(inventory, "fetch_objects")

    inventory.setup(config_data, cache, cache_key)

    if cache:
        fetch_objects.assert_not_called()
    else:
        fetch_objects.assert_called_once_with(connections)


@pytest.mark.parametrize(
    "present",
    [
        True,
        False,
    ],
)
def test_k8s_client_missing(mocker, inventory, present):
    mocker.patch.object(kubevirt, "HAS_K8S_MODULE_HELPER", present)
    fetch_objects = mocker.patch.object(inventory, "fetch_objects")

    if present:
        inventory.setup({}, False, "test")
        fetch_objects.assert_called_once()
    else:
        with pytest.raises(
            KubeVirtInventoryException,
            match="This module requires the Kubernetes Python client. Try `pip install kubernetes`. Detail: None",
        ):
            inventory.setup({}, False, "test")
        fetch_objects.assert_not_called()
