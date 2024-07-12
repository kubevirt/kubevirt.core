# -*- coding: utf-8 -*-
# Copyright 2024 Red Hat, Inc.
# Apache License 2.0 (see LICENSE or http://www.apache.org/licenses/LICENSE-2.0)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from ansible_collections.kubevirt.core.plugins.inventory.kubevirt import (
    InventoryOptions,
)

VM1 = {
    "metadata": {
        "name": "testvm1",
        "namespace": "default",
        "uid": "940003aa-0160-4b7e-9e55-8ec3df72047f",
    },
    "spec": {"running": True},
    "status": {},
}

VM2 = {
    "metadata": {
        "name": "testvm2",
        "namespace": "default",
        "uid": "c2c68de5-b9d7-4c25-872f-462e7245b3e6",
    },
    "spec": {"running": False},
    "status": {},
}

VMI1 = {
    "metadata": {
        "name": "testvm1",
        "namespace": "default",
        "uid": "a84319a9-db31-4a36-9b66-3e387578f871",
    },
    "spec": {},
    "status": {
        "interfaces": [{"ipAddress": "10.10.10.10"}],
    },
}


def test_stopped_vm(inventory, hosts):
    inventory._populate_inventory(
        {
            "default_hostname": "test",
            "cluster_domain": "test.com",
            "namespaces": {
                "default": {"vms": [VM1, VM2], "vmis": [VMI1], "services": {}},
            },
        },
        InventoryOptions(),
    )

    # The running VM should be present with ansible_host or ansible_port
    assert "default-testvm1" in hosts
    assert "ansible_host" in hosts["default-testvm1"]
    assert "ansible_port" in hosts["default-testvm1"]

    # The stopped VM should be present without ansible_host or ansible_port
    assert "default-testvm2" in hosts
    assert "ansible_host" not in hosts["default-testvm2"]
    assert "ansible_port" not in hosts["default-testvm2"]
