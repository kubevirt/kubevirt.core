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

VM1 = {
    "metadata": {
        "name": "testvm1",
        "namespace": DEFAULT_NAMESPACE,
        "uid": "940003aa-0160-4b7e-9e55-8ec3df72047f",
    },
    "spec": {},
    "status": {},
}

VM2 = {
    "metadata": {
        "name": "testvm2",
        "namespace": DEFAULT_NAMESPACE,
        "uid": "c2c68de5-b9d7-4c25-872f-462e7245b3e6",
    },
    "spec": {},
    "status": {},
}

VMI1 = {
    "metadata": {
        "name": "testvm1",
        "namespace": DEFAULT_NAMESPACE,
        "uid": "a84319a9-db31-4a36-9b66-3e387578f871",
    },
    "spec": {},
    "status": {
        "interfaces": [{"ipAddress": "10.10.10.10"}],
    },
}

VMI2 = {
    "metadata": {
        "name": "testvm2",
        "namespace": DEFAULT_NAMESPACE,
        "uid": "fd35700a-9cbe-488b-8f32-7adbe57eadc2",
    },
    "spec": {},
    "status": {
        "interfaces": [{"ipAddress": "10.10.10.10"}],
    },
}


@pytest.mark.parametrize(
    "vms,vmis,expected",
    [
        ([], [], 0),
        ([VM1], [], 1),
        ([VM1, VM2], [], 2),
        ([VM1], [VMI1], 1),
        ([VM2], [VMI2], 1),
        ([VM1], [VMI2], 2),
        ([VM2], [VMI1], 2),
        ([VM1], [VMI1, VMI2], 2),
        ([VM2], [VMI1, VMI2], 2),
        ([VM1, VM2], [VMI1, VMI2], 2),
        ([], [VMI1], 1),
        ([], [VMI1, VMI2], 2),
    ],
)
def test_populate_inventory_from_namespace(
    mocker, inventory, groups, vms, vmis, expected
):
    _vms = {vm["metadata"]["name"]: vm for vm in vms}
    _vmis = {vmi["metadata"]["name"]: vmi for vmi in vmis}
    opts = InventoryOptions(name="test")

    def format_hostname(obj):
        return opts.host_format.format(
            namespace=obj["metadata"]["namespace"],
            name=obj["metadata"]["name"],
            uid=obj["metadata"]["uid"],
        )

    def add_host_call(obj):
        return mocker.call(
            obj["metadata"],
            opts.host_format,
            f"namespace_{DEFAULT_NAMESPACE}",
        )

    obj_is_valid_calls = []
    add_host_side_effects = []
    add_host_calls = []
    set_vars_from_vm_calls = []
    set_vars_from_vmi_calls = []
    set_composable_vars_calls = []

    # For each VM add the expected calls
    # Also add expected calls for VMIs for which a VM exists
    for name, vm in _vms.items():
        obj_is_valid_calls.append(mocker.call(vm))
        hostname = format_hostname(vm)
        add_host_side_effects.append(hostname)
        add_host_calls.append(add_host_call(vm))
        set_vars_from_vm_calls.append(mocker.call(hostname, vm, opts))
        if name in _vmis.keys():
            set_vars_from_vmi_calls.append(mocker.call(hostname, _vmis[name], {}, opts))
        set_composable_vars_calls.append(mocker.call(hostname))

    # For each VMI add the expected calls
    # Do not add for VMIs for which a VM exists
    for name, vmi in _vmis.items():
        obj_is_valid_calls.append(mocker.call(vmi))
        if name not in _vms.keys():
            hostname = format_hostname(vmi)
            add_host_side_effects.append(hostname)
            add_host_calls.append(add_host_call(vmi))
            set_vars_from_vmi_calls.append(mocker.call(hostname, vmi, {}, opts))
            set_composable_vars_calls.append(mocker.call(hostname))

    obj_is_valid = mocker.patch.object(inventory, "_obj_is_valid", return_value=True)
    add_host = mocker.patch.object(
        inventory, "_add_host", side_effect=add_host_side_effects
    )
    set_vars_from_vm = mocker.patch.object(inventory, "_set_vars_from_vm")
    set_vars_from_vmi = mocker.patch.object(inventory, "_set_vars_from_vmi")
    set_composable_vars = mocker.patch.object(inventory, "_set_composable_vars")

    inventory._populate_inventory_from_namespace(
        DEFAULT_NAMESPACE, {"vms": vms, "vmis": vmis, "services": {}}, opts
    )

    # Assert it tries to add the expected vars for all provided VMs/VMIs
    obj_is_valid.assert_has_calls(obj_is_valid_calls)
    set_vars_from_vm.assert_has_calls(set_vars_from_vm_calls)
    set_vars_from_vmi.assert_has_calls(set_vars_from_vmi_calls)
    set_composable_vars.assert_has_calls(set_composable_vars_calls)

    # If no VMs or VMIs were provided the function should not add any groups
    if vms or vmis:
        assert list(groups.keys()) == ["test", f"namespace_{DEFAULT_NAMESPACE}"]
    else:
        assert not list(groups.keys())

    # Assert the expected amount of hosts was added
    add_host.assert_has_calls(add_host_calls)
    assert len(add_host_calls) == expected
