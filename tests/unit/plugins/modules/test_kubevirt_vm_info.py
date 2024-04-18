# -*- coding: utf-8 -*-
# Copyright: (c) 2021, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

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
    exit_json,
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
        "wait": False,
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


@pytest.mark.parametrize(
    "module_args,find_args",
    [
        ({}, "find_args_default"),
        ({"name": "testvm", "namespace": "default"}, "find_args_name_namespace"),
        ({"label_selectors": "app=test"}, "find_args_label_selector"),
        ({"field_selectors": "app=test"}, "find_args_field_selector"),
    ],
)
def test_module(request, monkeypatch, mocker, module_args, find_args):
    monkeypatch.setattr(AnsibleModule, "exit_json", exit_json)
    monkeypatch.setattr(kubevirt_vm_info, "get_api_client", lambda _: None)

    set_module_args(module_args)

    find = mocker.patch.object(K8sService, "find")
    find.return_value = {
        "api_found": True,
        "failed": False,
        "resources": [],
    }

    with pytest.raises(AnsibleExitJson):
        kubevirt_vm_info.main()
    find.assert_called_once_with(**request.getfixturevalue(find_args))
