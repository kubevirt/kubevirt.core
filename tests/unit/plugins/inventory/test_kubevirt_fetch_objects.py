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


@pytest.mark.parametrize(
    "opts,namespaces",
    [
        (
            InventoryOptions(),
            [DEFAULT_NAMESPACE],
        ),
        (
            InventoryOptions(namespaces=["test"]),
            ["test"],
        ),
        (
            InventoryOptions(namespaces=["test1", "test2"]),
            ["test1", "test2"],
        ),
    ],
)
def test_fetch_objects(mocker, inventory, opts, namespaces):
    get_available_namespaces = mocker.patch.object(
        inventory, "_get_available_namespaces", return_value=[DEFAULT_NAMESPACE]
    )
    get_vms_for_namespace = mocker.patch.object(
        inventory, "_get_vms_for_namespace", return_value=[{}]
    )
    get_vmis_for_namespace = mocker.patch.object(
        inventory, "_get_vmis_for_namespace", return_value=[{}]
    )
    get_services_for_namespace = mocker.patch.object(
        inventory, "_get_services_for_namespace", return_value=[]
    )
    get_default_hostname = mocker.patch.object(
        inventory, "_get_default_hostname", return_value="default-hostname"
    )
    get_cluster_domain = mocker.patch.object(
        inventory, "_get_cluster_domain", return_value="test.com"
    )

    inventory._fetch_objects(mocker.Mock(), opts)

    if opts.namespaces:
        get_available_namespaces.assert_not_called()
    else:
        get_available_namespaces.assert_called()

    get_vms_for_namespace.assert_has_calls(
        [mocker.call(mocker.ANY, namespace, opts) for namespace in namespaces]
    )
    get_vmis_for_namespace.assert_has_calls(
        [mocker.call(mocker.ANY, namespace, opts) for namespace in namespaces]
    )
    get_services_for_namespace.assert_has_calls(
        [mocker.call(mocker.ANY, namespace) for namespace in namespaces]
    )
    get_default_hostname.assert_called_once()
    get_cluster_domain.assert_called_once()


def test_fetch_objects_early_return(mocker, inventory):
    get_available_namespaces = mocker.patch.object(
        inventory, "_get_available_namespaces", return_value=[DEFAULT_NAMESPACE]
    )
    get_vms_for_namespace = mocker.patch.object(
        inventory, "_get_vms_for_namespace", return_value=[]
    )
    get_vmis_for_namespace = mocker.patch.object(
        inventory, "_get_vmis_for_namespace", return_value=[]
    )
    get_services_for_namespace = mocker.patch.object(
        inventory, "_get_services_for_namespace"
    )
    get_default_hostname = mocker.patch.object(
        inventory, "_get_default_hostname", return_value="default-hostname"
    )
    get_cluster_domain = mocker.patch.object(
        inventory, "_get_cluster_domain", return_value="test.com"
    )

    inventory._fetch_objects(mocker.Mock(), InventoryOptions())

    get_available_namespaces.assert_called_once()
    get_vms_for_namespace.assert_called_once_with(
        mocker.ANY, DEFAULT_NAMESPACE, InventoryOptions()
    )
    get_vmis_for_namespace.assert_called_once_with(
        mocker.ANY, DEFAULT_NAMESPACE, InventoryOptions()
    )
    get_services_for_namespace.assert_not_called()
    get_default_hostname.assert_called_once()
    get_cluster_domain.assert_called_once()
