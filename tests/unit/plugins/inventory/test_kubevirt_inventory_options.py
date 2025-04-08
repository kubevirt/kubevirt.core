# -*- coding: utf-8 -*-
# Copyright 2024 Red Hat, Inc.
# Apache License 2.0 (see LICENSE or http://www.apache.org/licenses/LICENSE-2.0)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from ansible_collections.kubevirt.core.plugins.inventory.kubevirt import (
    InventoryOptions,
)


def test_inventory_options_defaults():
    opts = InventoryOptions()
    assert opts.api_version == "kubevirt.io/v1"
    assert opts.label_selector is None
    assert opts.network_name is None
    assert opts.kube_secondary_dns is False
    assert opts.use_service is True
    assert opts.unset_ansible_port is True
    assert opts.create_groups is False
    assert opts.base_domain is None
    assert opts.append_base_domain is False
    assert opts.host_format == "{namespace}-{name}"


def test_inventory_options_override_defaults():
    api_version = "test/v1"
    label_selector = "test-selector"
    network_name = "test-network"
    kube_secondary_dns = True
    use_service = False
    unset_ansible_port = False
    create_groups = True
    base_domain = "test-domain.com"
    append_base_domain = True
    host_format = "{name}-testhost"

    opts = InventoryOptions(
        api_version=api_version,
        label_selector=label_selector,
        network_name=network_name,
        kube_secondary_dns=kube_secondary_dns,
        use_service=use_service,
        unset_ansible_port=unset_ansible_port,
        create_groups=create_groups,
        base_domain=base_domain,
        append_base_domain=append_base_domain,
        host_format=host_format,
    )
    assert opts.api_version == api_version
    assert opts.label_selector == label_selector
    assert opts.network_name == network_name
    assert opts.kube_secondary_dns == kube_secondary_dns
    assert opts.use_service == use_service
    assert opts.unset_ansible_port == unset_ansible_port
    assert opts.create_groups == create_groups
    assert opts.base_domain == base_domain
    assert opts.append_base_domain == append_base_domain
    assert opts.host_format == host_format
