# -*- coding: utf-8 -*-
# Copyright 2024 Red Hat, Inc.
# Apache License 2.0 (see LICENSE or http://www.apache.org/licenses/LICENSE-2.0)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest

from addict import Dict


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
}

VM2 = {
    "metadata": {
        "name": "testvm2",
        "namespace": DEFAULT_NAMESPACE,
        "uid": "c2c68de5-b9d7-4c25-872f-462e7245b3e6",
    },
}

VMI1 = {
    "metadata": {
        "name": "testvm1",
        "namespace": DEFAULT_NAMESPACE,
        "uid": "a84319a9-db31-4a36-9b66-3e387578f871",
    },
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
    _vms = {vm["metadata"]["name"]: Dict(vm) for vm in vms}
    _vmis = {vmi["metadata"]["name"]: Dict(vmi) for vmi in vmis}
    opts = InventoryOptions()

    def format_hostname(obj):
        return opts.host_format.format(
            namespace=obj.metadata.namespace,
            name=obj.metadata.name,
            uid=obj.metadata.uid,
        )

    def add_host_call(obj):
        return mocker.call(
            obj,
            opts.host_format,
            f"namespace_{DEFAULT_NAMESPACE}",
        )

    add_host_side_effects = []
    add_host_calls = []
    set_vars_from_vm_calls = []
    set_vars_from_vmi_calls = []
    set_composable_vars_calls = []

    # For each VM add the expected calls
    # Also add expected calls for VMIs for which a VM exists
    for name, vm in _vms.items():
        hostname = format_hostname(vm)
        add_host_side_effects.append(hostname)
        add_host_calls.append(add_host_call(vm))
        set_vars_from_vm_calls.append(mocker.call(hostname, vm, opts))
        if name in _vmis.keys():
            set_vars_from_vmi_calls.append(mocker.call(hostname, _vmis[name], [], opts))
        set_composable_vars_calls.append(mocker.call(hostname))

    # For each VMI add the expected calls
    # Do not add for VMIs for which a VM exists
    for name, vmi in _vmis.items():
        if name not in _vms.keys():
            hostname = format_hostname(vmi)
            add_host_side_effects.append(hostname)
            add_host_calls.append(add_host_call(vmi))
            set_vars_from_vmi_calls.append(mocker.call(hostname, vmi, [], opts))
            set_composable_vars_calls.append(mocker.call(hostname))

    get_vms_for_namespace = mocker.patch.object(
        inventory, "get_vms_for_namespace", return_value=_vms.values()
    )
    get_vmis_for_namespace = mocker.patch.object(
        inventory, "get_vmis_for_namespace", return_value=_vmis.values()
    )
    get_ssh_services_for_namespace = mocker.patch.object(
        inventory, "get_ssh_services_for_namespace", return_value=[]
    )
    add_host = mocker.patch.object(
        inventory, "add_host", side_effect=add_host_side_effects
    )
    set_vars_from_vm = mocker.patch.object(inventory, "set_vars_from_vm")
    set_vars_from_vmi = mocker.patch.object(inventory, "set_vars_from_vmi")
    set_composable_vars = mocker.patch.object(inventory, "set_composable_vars")

    inventory.populate_inventory_from_namespace(None, "test", DEFAULT_NAMESPACE, opts)

    # These should always get called once
    get_vms_for_namespace.assert_called_once_with(None, DEFAULT_NAMESPACE, opts)
    get_vmis_for_namespace.assert_called_once_with(None, DEFAULT_NAMESPACE, opts)

    # Assert it tries to add the expected vars for all provided VMs/VMIs
    set_vars_from_vm.assert_has_calls(set_vars_from_vm_calls)
    set_vars_from_vmi.assert_has_calls(set_vars_from_vmi_calls)
    set_composable_vars.assert_has_calls(set_composable_vars_calls)

    # If no VMs or VMIs were provided the function should not add any groups
    if vms or vmis:
        get_ssh_services_for_namespace.assert_called_once_with(None, DEFAULT_NAMESPACE)
        assert list(groups.keys()) == ["test", f"namespace_{DEFAULT_NAMESPACE}"]
    else:
        get_ssh_services_for_namespace.assert_not_called()
        assert not list(groups.keys())

    # Assert the expected amount of hosts was added
    add_host.assert_has_calls(add_host_calls)
    assert len(add_host_calls) == expected
