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
from ansible_collections.kubevirt.core.plugins.module_utils import (
    info,
)
from ansible_collections.kubevirt.core.tests.unit.utils.ansible_module_mock import (
    AnsibleExitJson,
    AnsibleFailJson,
    exit_json,
    fail_json,
)

# Handle import errors of patch_module_args.
# It is only available on ansible-core >=2.19.
try:
    from ansible.module_utils.testing import patch_module_args
except ImportError as e:
    from ansible_collections.kubevirt.core.tests.unit.utils.ansible_module_mock import (
        patch_module_args,
    )


def test_module_fails_when_required_args_missing(mocker):
    mocker.patch.object(AnsibleModule, "fail_json", fail_json)
    with pytest.raises(AnsibleFailJson), patch_module_args({"running": False}):
        kubevirt_vm_info.main()


FIND_ARGS_DEFAULT = {
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
    "hidden_fields": [
        "metadata.annotations[kubemacpool.io/transaction-timestamp]",
        "metadata.managedFields",
    ],
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

FIND_ARGS_RUNNING = FIND_ARGS_DEFAULT | {
    "wait": True,
    "condition": {"type": "Ready", "status": True},
}

FIND_ARGS_STOPPED = FIND_ARGS_DEFAULT | {
    "wait": True,
    "condition": {"type": "Ready", "status": False, "reason": "VMINotExists"},
}

FIND_ARGS_HIDDEN_FIELDS = FIND_ARGS_DEFAULT | {
    "hidden_fields": [
        "metadata.annotations[kubemacpool.io/transaction-timestamp]",
        "metadata.annotations[kubectl.kubernetes.io/last-applied-configuration]",
    ],
}


@pytest.mark.parametrize(
    "module_args,find_args",
    [
        ({}, FIND_ARGS_DEFAULT),
        ({"name": "testvm", "namespace": "default"}, FIND_ARGS_NAME_NAMESPACE),
        ({"label_selectors": "app=test"}, FIND_ARGS_LABEL_SELECTOR),
        ({"field_selectors": "app=test"}, FIND_ARGS_FIELD_SELECTOR),
        ({"wait": True, "running": True}, FIND_ARGS_RUNNING),
        ({"wait": True, "running": False}, FIND_ARGS_STOPPED),
        (
            {
                "hidden_fields": [
                    "metadata.annotations[kubemacpool.io/transaction-timestamp]",
                    "metadata.annotations[kubectl.kubernetes.io/last-applied-configuration]",
                ]
            },
            FIND_ARGS_HIDDEN_FIELDS,
        ),
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

    with pytest.raises(AnsibleExitJson), patch_module_args(module_args):
        kubevirt_vm_info.main()

    find.assert_called_once_with(**find_args)
