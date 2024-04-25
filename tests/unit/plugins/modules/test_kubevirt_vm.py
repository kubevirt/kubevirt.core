# -*- coding: utf-8 -*-
# Copyright: (c) 2021, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest

from yaml import dump

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.kubernetes.core.plugins.module_utils.k8s import runner
from ansible_collections.kubevirt.core.plugins.modules import kubevirt_vm
from ansible_collections.kubevirt.core.tests.unit.utils.ansible_module_mock import (
    AnsibleFailJson,
    AnsibleExitJson,
    exit_json,
    fail_json,
    set_module_args,
)


@pytest.fixture(scope="module")
def vm_definition_create():
    return {
        "apiVersion": "kubevirt.io/v1",
        "kind": "VirtualMachine",
        "metadata": {
            "name": "testvm",
            "namespace": "default",
            "labels": {"environment": "staging", "service": "loadbalancer"},
        },
        "spec": {
            "running": True,
            "instancetype": {"name": "u1.medium"},
            "preference": {"name": "fedora"},
            "dataVolumeTemplates": [
                {
                    "metadata": {"name": "testdv"},
                    "spec": {
                        "source": {
                            "registry": {
                                "url": "docker://quay.io/containerdisks/fedora:latest"
                            },
                        },
                        "storage": {
                            "accessModes": ["ReadWriteOnce"],
                            "resources": {"requests": {"storage": "5Gi"}},
                        },
                    },
                }
            ],
            "template": {
                "metadata": {
                    "labels": {"environment": "staging", "service": "loadbalancer"}
                },
                "spec": {
                    "domain": {"devices": {}},
                    "terminationGracePeriodSeconds": 180,
                },
            },
        },
    }


@pytest.fixture(scope="module")
def vm_definition_running():
    return {
        "apiVersion": "kubevirt.io/v1",
        "kind": "VirtualMachine",
        "metadata": {
            "name": "testvm",
            "namespace": "default",
        },
        "spec": {
            "running": True,
            "template": {
                "spec": {
                    "domain": {"devices": {}},
                },
            },
        },
    }


@pytest.fixture(scope="module")
def vm_definition_stopped():
    return {
        "apiVersion": "kubevirt.io/v1",
        "kind": "VirtualMachine",
        "metadata": {
            "name": "testvm",
            "namespace": "default",
        },
        "spec": {
            "running": False,
            "template": {
                "spec": {
                    "domain": {"devices": {}},
                },
            },
        },
    }


@pytest.fixture(scope="module")
def module_params_default():
    return {
        "api_version": "kubevirt.io/v1",
        "annotations": None,
        "labels": None,
        "running": True,
        "instancetype": None,
        "preference": None,
        "data_volume_templates": None,
        "spec": None,
        "wait": False,
        "wait_sleep": 5,
        "wait_timeout": 5,
        "kubeconfig": None,
        "context": None,
        "host": None,
        "api_key": None,
        "username": None,
        "password": None,
        "validate_certs": None,
        "ca_cert": None,
        "client_cert": None,
        "client_key": None,
        "proxy": None,
        "no_proxy": None,
        "proxy_headers": None,
        "persist_config": None,
        "impersonate_user": None,
        "impersonate_groups": None,
        "state": "present",
        "force": False,
        "delete_options": None,
    }


@pytest.fixture(scope="module")
def module_params_create(module_params_default):
    return module_params_default | {
        "name": "testvm",
        "namespace": "default",
        "labels": {"service": "loadbalancer", "environment": "staging"},
        "instancetype": {"name": "u1.medium"},
        "preference": {"name": "fedora"},
        "data_volume_templates": [
            {
                "metadata": {"name": "testdv"},
                "spec": {
                    "source": {
                        "registry": {
                            "url": "docker://quay.io/containerdisks/fedora:latest"
                        },
                    },
                    "storage": {
                        "accessModes": ["ReadWriteOnce"],
                        "resources": {"requests": {"storage": "5Gi"}},
                    },
                },
            }
        ],
        "spec": {
            "domain": {"devices": {}},
            "terminationGracePeriodSeconds": 180,
        },
    }


@pytest.fixture(scope="module")
def module_params_running(module_params_default):
    return module_params_default | {
        "name": "testvm",
        "namespace": "default",
        "running": True,
    }


@pytest.fixture(scope="module")
def module_params_stopped(module_params_default):
    return module_params_default | {
        "name": "testvm",
        "namespace": "default",
        "running": False,
    }


@pytest.fixture(scope="module")
def module_params_delete(module_params_default):
    return module_params_default | {
        "name": "testvm",
        "namespace": "default",
        "state": "absent",
        "wait": True,
    }


@pytest.fixture(scope="module")
def k8s_module_params_create(module_params_create, vm_definition_create):
    return module_params_create | {
        "generate_name": None,
        "resource_definition": dump(vm_definition_create, sort_keys=False),
        "wait_condition": {"type": "Ready", "status": True},
    }


@pytest.fixture(scope="module")
def k8s_module_params_running(module_params_running, vm_definition_running):
    return module_params_running | {
        "generate_name": None,
        "resource_definition": dump(vm_definition_running, sort_keys=False),
        "wait_condition": {"type": "Ready", "status": True},
    }


@pytest.fixture(scope="module")
def k8s_module_params_stopped(module_params_stopped, vm_definition_stopped):
    return module_params_stopped | {
        "generate_name": None,
        "resource_definition": dump(vm_definition_stopped, sort_keys=False),
        "wait_condition": {"type": "Ready", "status": False, "reason": "VMINotExists"},
    }


@pytest.fixture(scope="module")
def k8s_module_params_delete(module_params_delete, vm_definition_running):
    return module_params_delete | {
        "generate_name": None,
        "resource_definition": dump(vm_definition_running, sort_keys=False),
        "wait_condition": {"type": "Ready", "status": True},
    }


def test_module_fails_when_required_args_missing(monkeypatch):
    monkeypatch.setattr(AnsibleModule, "fail_json", fail_json)
    with pytest.raises(AnsibleFailJson):
        set_module_args({})
        kubevirt_vm.main()


@pytest.mark.parametrize(
    "module_params,k8s_module_params,vm_definition,method",
    [
        (
            "module_params_create",
            "k8s_module_params_create",
            "vm_definition_create",
            "create",
        ),
        (
            "module_params_running",
            "k8s_module_params_running",
            "vm_definition_running",
            "update",
        ),
        (
            "module_params_stopped",
            "k8s_module_params_stopped",
            "vm_definition_stopped",
            "update",
        ),
        (
            "module_params_delete",
            "k8s_module_params_delete",
            "vm_definition_running",
            "delete",
        ),
    ],
)
def test_module(
    request,
    monkeypatch,
    mocker,
    module_params,
    k8s_module_params,
    vm_definition,
    method,
):
    monkeypatch.setattr(AnsibleModule, "exit_json", exit_json)
    monkeypatch.setattr(runner, "get_api_client", lambda _: None)

    set_module_args(request.getfixturevalue(module_params))

    perform_action = mocker.patch.object(runner, "perform_action")
    perform_action.return_value = {
        "method": method,
        "changed": True,
        "result": "success",
    }

    with pytest.raises(AnsibleExitJson):
        kubevirt_vm.main()
    perform_action.assert_called_once_with(
        mocker.ANY,
        request.getfixturevalue(vm_definition),
        request.getfixturevalue(k8s_module_params),
    )
