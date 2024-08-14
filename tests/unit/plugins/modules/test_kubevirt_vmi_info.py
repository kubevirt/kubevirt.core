# -*- coding: utf-8 -*-
# Copyright 2024 Red Hat, Inc.
# Apache License 2.0 (see LICENSE or http://www.apache.org/licenses/LICENSE-2.0)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.kubernetes.core.plugins.module_utils.k8s.service import (
    K8sService,
)
from ansible_collections.kubevirt.core.plugins.modules import (
    kubevirt_vmi_info,
)
from ansible_collections.kubevirt.core.plugins.module_utils import (
    info,
)
from ansible_collections.kubevirt.core.tests.unit.utils.ansible_module_mock import (
    AnsibleExitJson,
    exit_json,
    set_module_args,
)

FIND_ARGS_DEFAULT = {
    "kind": "VirtualMachineInstance",
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

FIND_ARGS_NAME_NAMESPACE = FIND_ARGS_DEFAULT | {
    "name": "testvm",
    "namespace": "default",
}

FIND_ARGS_LABEL_SELECTOR = FIND_ARGS_DEFAULT | {
    "label_selectors": ["app=test"],
}

FIND_ARGS_FIELD_SELECTOR = FIND_ARGS_DEFAULT | {
    "field_selectors": ["app=test"],
}


@pytest.mark.parametrize(
    "module_args,find_args",
    [
        ({}, FIND_ARGS_DEFAULT),
        ({"name": "testvm", "namespace": "default"}, FIND_ARGS_NAME_NAMESPACE),
        ({"label_selectors": "app=test"}, FIND_ARGS_LABEL_SELECTOR),
        ({"field_selectors": "app=test"}, FIND_ARGS_FIELD_SELECTOR),
    ],
)
def test_module(mocker, module_args, find_args):
    mocker.patch.object(AnsibleModule, "exit_json", exit_json)
    mocker.patch.object(info, "get_api_client")

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
        kubevirt_vmi_info.main()

    find.assert_called_once_with(**find_args)
