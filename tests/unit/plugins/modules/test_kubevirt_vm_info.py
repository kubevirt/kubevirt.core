# -*- coding: utf-8 -*-
# Copyright 2023 Red Hat, Inc.
# Apache License 2.0 (see LICENSE or http://www.apache.org/licenses/LICENSE-2.0)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.kubernetes.core.plugins.module_utils.k8s.service import (
    K8sService,
)
from ansible_collections.kubevirt.core.plugins.modules import (
    kubevirt_vm_info,
)
from ansible_collections.kubevirt.core.tests.unit.utils.ansible_module_mock import (
    AnsibleExitJson,
    AnsibleFailJson,
    exit_json,
    fail_json,
    set_module_args,
)


@pytest.fixture(scope="module")
def find_args_default():
    return {
        "kind": "VirtualMachine",
        "api_version": "kubevirt.io/v1",
        "name": None,
        "namespace": None,
        "label_selectors": [],
        "field_selectors": [],
        "wait": None,
        "wait_sleep": 5,
        "wait_timeout": 120,
        "condition": {"type": "Ready", "status": True},
    }


@pytest.fixture(scope="module")
def find_args_name_namespace(find_args_default):
    return find_args_default | {
        "name": "testvm",
        "namespace": "default",
    }


@pytest.fixture(scope="module")
def find_args_label_selector(find_args_default):
    return find_args_default | {
        "label_selectors": ["app=test"],
    }


@pytest.fixture(scope="module")
def find_args_field_selector(find_args_default):
    return find_args_default | {
        "field_selectors": ["app=test"],
    }


@pytest.fixture(scope="module")
def find_args_running(find_args_default):
    return find_args_default | {
        "wait": True,
        "condition": {"type": "Ready", "status": True},
    }


@pytest.fixture(scope="module")
def find_args_stopped(find_args_default):
    return find_args_default | {
        "wait": True,
        "condition": {"type": "Ready", "status": False, "reason": "VMINotExists"},
    }


@pytest.mark.parametrize(
    "module_args",
    [
        {"running": False},
    ],
)
def test_module_fails_when_required_args_missing(mocker, module_args):
    mocker.patch.object(AnsibleModule, "fail_json", fail_json)
    with pytest.raises(AnsibleFailJson):
        set_module_args(module_args)
        kubevirt_vm_info.main()


@pytest.mark.parametrize(
    "module_args,find_args",
    [
        ({}, "find_args_default"),
        ({"name": "testvm", "namespace": "default"}, "find_args_name_namespace"),
        ({"label_selectors": "app=test"}, "find_args_label_selector"),
        ({"field_selectors": "app=test"}, "find_args_field_selector"),
        ({"wait": True, "running": True}, "find_args_running"),
        ({"wait": True, "running": False}, "find_args_stopped"),
    ],
)
def test_module(request, mocker, module_args, find_args):
    mocker.patch.object(AnsibleModule, "exit_json", exit_json)
    mocker.patch.object(kubevirt_vm_info, "get_api_client")

    find = mocker.patch.object(
        K8sService,
        "find",
        return_value={
            "api_found": True,
            "failed": False,
            "resources": [],
        },
    )

    with pytest.raises(AnsibleExitJson):
        set_module_args(module_args)
        kubevirt_vm_info.main()

    find.assert_called_once_with(**request.getfixturevalue(find_args))
