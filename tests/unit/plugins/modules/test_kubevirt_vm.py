# -*- coding: utf-8 -*-
# Copyright 2023 Red Hat, Inc.
# Apache License 2.0 (see LICENSE or http://www.apache.org/licenses/LICENSE-2.0)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.kubernetes.core.plugins.module_utils.k8s import runner
from ansible_collections.kubevirt.core.plugins.modules import kubevirt_vm
from ansible_collections.kubevirt.core.tests.unit.utils.ansible_module_mock import (
    AnsibleFailJson,
    AnsibleExitJson,
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
    with pytest.raises(AnsibleFailJson), patch_module_args({}):
        kubevirt_vm.main()


VM_DEFINITION_CREATE = {
    "apiVersion": "kubevirt.io/v1",
    "kind": "VirtualMachine",
    "metadata": {
        "name": "testvm",
        "namespace": "default",
        "labels": {"environment": "staging", "service": "loadbalancer"},
    },
    "spec": {
        "running": True,
        "runStrategy": None,
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

VM_DEFINITION_RUNNING = {
    "apiVersion": "kubevirt.io/v1",
    "kind": "VirtualMachine",
    "metadata": {
        "name": "testvm",
        "namespace": "default",
    },
    "spec": {
        "running": True,
        "runStrategy": None,
        "template": {
            "spec": {
                "domain": {"devices": {}},
            },
        },
    },
}

VM_DEFINITION_STOPPED = {
    "apiVersion": "kubevirt.io/v1",
    "kind": "VirtualMachine",
    "metadata": {
        "name": "testvm",
        "namespace": "default",
    },
    "spec": {
        "running": False,
        "runStrategy": None,
        "template": {
            "spec": {
                "domain": {"devices": {}},
            },
        },
    },
}

VM_DEFINITION_HALTED = {
    "apiVersion": "kubevirt.io/v1",
    "kind": "VirtualMachine",
    "metadata": {
        "name": "testvm",
        "namespace": "default",
    },
    "spec": {
        "running": None,
        "runStrategy": "Halted",
        "template": {
            "spec": {
                "domain": {"devices": {}},
            },
        },
    },
}

MODULE_PARAMS_DEFAULT = {
    "api_version": "kubevirt.io/v1",
    "annotations": None,
    "labels": None,
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
    "grace_period_seconds": None,
}

MODULE_PARAMS_CREATE = MODULE_PARAMS_DEFAULT | {
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

MODULE_PARAMS_RUNNING = MODULE_PARAMS_DEFAULT | {
    "name": "testvm",
    "namespace": "default",
    "running": True,
}

MODULE_PARAMS_STOPPED = MODULE_PARAMS_DEFAULT | {
    "name": "testvm",
    "namespace": "default",
    "running": False,
}

MODULE_PARAMS_HALTED = MODULE_PARAMS_DEFAULT | {
    "name": "testvm",
    "namespace": "default",
    "run_strategy": "Halted",
}

MODULE_PARAMS_DELETE = MODULE_PARAMS_DEFAULT | {
    "name": "testvm",
    "namespace": "default",
    "state": "absent",
    "wait": True,
}

MODULE_PARAMS_HIDDEN_FIELDS = MODULE_PARAMS_DEFAULT | {
    "name": "testvm",
    "namespace": "default",
    "running": False,
    "hidden_fields": [
        "metadata.annotations[kubemacpool.io/transaction-timestamp]",
        "metadata.annotations[kubectl.kubernetes.io/last-applied-configuration]",
    ],
}

K8S_MODULE_PARAMS_CREATE = MODULE_PARAMS_CREATE | {
    "generate_name": None,
    "running": None,
    "run_strategy": None,
    "resource_definition": VM_DEFINITION_CREATE,
    "wait_condition": {"type": "Ready", "status": True},
    "hidden_fields": [
        "metadata.annotations[kubemacpool.io/transaction-timestamp]",
        "metadata.managedFields",
    ],
}

K8S_MODULE_PARAMS_RUNNING = MODULE_PARAMS_RUNNING | {
    "generate_name": None,
    "run_strategy": None,
    "resource_definition": VM_DEFINITION_RUNNING,
    "wait_condition": {"type": "Ready", "status": True},
    "hidden_fields": [
        "metadata.annotations[kubemacpool.io/transaction-timestamp]",
        "metadata.managedFields",
    ],
}

K8S_MODULE_PARAMS_STOPPED = MODULE_PARAMS_STOPPED | {
    "generate_name": None,
    "run_strategy": None,
    "resource_definition": VM_DEFINITION_STOPPED,
    "wait_condition": {"type": "Ready", "status": False, "reason": "VMINotExists"},
    "hidden_fields": [
        "metadata.annotations[kubemacpool.io/transaction-timestamp]",
        "metadata.managedFields",
    ],
}

K8S_MODULE_PARAMS_HALTED = MODULE_PARAMS_HALTED | {
    "generate_name": None,
    "running": None,
    "resource_definition": VM_DEFINITION_HALTED,
    "wait_condition": {"type": "Ready", "status": False, "reason": "VMINotExists"},
    "hidden_fields": [
        "metadata.annotations[kubemacpool.io/transaction-timestamp]",
        "metadata.managedFields",
    ],
}

K8S_MODULE_PARAMS_DELETE = MODULE_PARAMS_DELETE | {
    "generate_name": None,
    "running": None,
    "run_strategy": None,
    "resource_definition": VM_DEFINITION_RUNNING,
    "wait_condition": {"type": "Ready", "status": True},
    "hidden_fields": [
        "metadata.annotations[kubemacpool.io/transaction-timestamp]",
        "metadata.managedFields",
    ],
}

K8S_MODULE_PARAMS_HIDDEN_FIELDS = MODULE_PARAMS_HIDDEN_FIELDS | {
    "generate_name": None,
    "run_strategy": None,
    "resource_definition": VM_DEFINITION_STOPPED,
    "wait_condition": {"type": "Ready", "status": False, "reason": "VMINotExists"},
}


@pytest.mark.parametrize(
    "module_params,k8s_module_params,vm_definition,method",
    [
        (
            MODULE_PARAMS_CREATE,
            K8S_MODULE_PARAMS_CREATE,
            VM_DEFINITION_CREATE,
            "create",
        ),
        (
            MODULE_PARAMS_RUNNING,
            K8S_MODULE_PARAMS_RUNNING,
            VM_DEFINITION_RUNNING,
            "update",
        ),
        (
            MODULE_PARAMS_STOPPED,
            K8S_MODULE_PARAMS_STOPPED,
            VM_DEFINITION_STOPPED,
            "update",
        ),
        (
            MODULE_PARAMS_HALTED,
            K8S_MODULE_PARAMS_HALTED,
            VM_DEFINITION_HALTED,
            "update",
        ),
        (
            MODULE_PARAMS_DELETE,
            K8S_MODULE_PARAMS_DELETE,
            VM_DEFINITION_RUNNING,
            "delete",
        ),
        (
            MODULE_PARAMS_HIDDEN_FIELDS,
            K8S_MODULE_PARAMS_HIDDEN_FIELDS,
            VM_DEFINITION_STOPPED,
            "update",
        ),
    ],
)
def test_module(mocker, module_params, k8s_module_params, vm_definition, method):
    mocker.patch.object(AnsibleModule, "exit_json", exit_json)
    mocker.patch.object(runner, "get_api_client")

    mock_perform_action = mocker.patch.object(
        runner,
        "perform_action",
        return_value={
            "method": method,
            "changed": True,
            "result": "success",
        },
    )

    with pytest.raises(AnsibleExitJson), patch_module_args(module_params):
        kubevirt_vm.main()

    mock_perform_action.assert_called_once_with(
        mocker.ANY,
        vm_definition,
        k8s_module_params,
    )


CREATE_VM_PARAMS = {
    "api_version": "kubevirt.io/v1",
    "namespace": "default",
}

CREATE_VM_PARAMS_RUN_STRATEGY = {
    "api_version": "kubevirt.io/v1",
    "namespace": "default",
    "run_strategy": "Manual",
}

CREATE_VM_PARAMS_ANNOTATIONS = CREATE_VM_PARAMS | {
    "annotations": {"test": "test"},
}

CREATE_VM_PARAMS_LABELS = CREATE_VM_PARAMS | {
    "labels": {"test": "test"},
}

CREATE_VM_PARAMS_INSTANCETYPE = CREATE_VM_PARAMS | {
    "instancetype": {"name": "u1.medium"},
}

CREATE_VM_PARAMS_PREFERENCE = CREATE_VM_PARAMS | {
    "preference": {"name": "fedora"},
}

CREATE_VM_PARAMS_DATAVOLUMETEMPLATE = CREATE_VM_PARAMS | {
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
        },
    ],
}

CREATE_VM_PARAMS_NAME = CREATE_VM_PARAMS | {
    "name": "testvm",
}

CREATE_VM_PARAMS_GENERATE_NAME = CREATE_VM_PARAMS | {
    "generate_name": "testvm-1234",
}

CREATE_VM_PARAMS_SPECS = CREATE_VM_PARAMS | {
    "spec": {
        "domain": {
            "devices": {
                "cpu": {
                    "cores": 2,
                    "socket": 1,
                    "threads": 2,
                }
            }
        }
    }
}

CREATED_VM = {
    "apiVersion": "kubevirt.io/v1",
    "kind": "VirtualMachine",
    "metadata": {
        "namespace": "default",
    },
    "spec": {
        "running": True,
        "runStrategy": None,
        "template": {
            "spec": {
                "domain": {
                    "devices": {},
                },
            },
        },
    },
}

CREATED_VM_RUN_STRATEGY = {
    "apiVersion": "kubevirt.io/v1",
    "kind": "VirtualMachine",
    "metadata": {
        "namespace": "default",
    },
    "spec": {
        "running": None,
        "runStrategy": "Manual",
        "template": {
            "spec": {
                "domain": {
                    "devices": {},
                },
            },
        },
    },
}

CREATED_VM_LABELS = {
    "apiVersion": "kubevirt.io/v1",
    "kind": "VirtualMachine",
    "metadata": {
        "namespace": "default",
        "labels": {
            "test": "test",
        },
    },
    "spec": {
        "running": True,
        "runStrategy": None,
        "template": {
            "metadata": {
                "labels": {"test": "test"},
            },
            "spec": {
                "domain": {
                    "devices": {},
                },
            },
        },
    },
}

CREATED_VM_ANNOTATIONS = {
    "apiVersion": "kubevirt.io/v1",
    "kind": "VirtualMachine",
    "metadata": {
        "namespace": "default",
        "annotations": {
            "test": "test",
        },
    },
    "spec": {
        "running": True,
        "runStrategy": None,
        "template": {
            "metadata": {
                "annotations": {"test": "test"},
            },
            "spec": {
                "domain": {
                    "devices": {},
                },
            },
        },
    },
}

CREATED_VM_INSTANCETYPE = {
    "apiVersion": "kubevirt.io/v1",
    "kind": "VirtualMachine",
    "metadata": {
        "namespace": "default",
    },
    "spec": {
        "running": True,
        "runStrategy": None,
        "instancetype": {"name": "u1.medium"},
        "template": {
            "spec": {
                "domain": {
                    "devices": {},
                },
            },
        },
    },
}

CREATED_VM_PREFERENCE = {
    "apiVersion": "kubevirt.io/v1",
    "kind": "VirtualMachine",
    "metadata": {
        "namespace": "default",
    },
    "spec": {
        "running": True,
        "runStrategy": None,
        "preference": {"name": "fedora"},
        "template": {
            "spec": {
                "domain": {
                    "devices": {},
                },
            },
        },
    },
}

CREATED_VM_DATAVOLUMETEMPLATE = {
    "apiVersion": "kubevirt.io/v1",
    "kind": "VirtualMachine",
    "metadata": {
        "namespace": "default",
    },
    "spec": {
        "running": True,
        "runStrategy": None,
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
            },
        ],
        "template": {
            "spec": {
                "domain": {
                    "devices": {},
                },
            },
        },
    },
}

CREATED_VM_NAME = {
    "apiVersion": "kubevirt.io/v1",
    "kind": "VirtualMachine",
    "metadata": {
        "name": "testvm",
        "namespace": "default",
    },
    "spec": {
        "running": True,
        "runStrategy": None,
        "template": {
            "spec": {
                "domain": {
                    "devices": {},
                },
            },
        },
    },
}

CREATED_VM_GENERATE_NAME = {
    "apiVersion": "kubevirt.io/v1",
    "kind": "VirtualMachine",
    "metadata": {
        "generateName": "testvm-1234",
        "namespace": "default",
    },
    "spec": {
        "running": True,
        "runStrategy": None,
        "template": {
            "spec": {
                "domain": {
                    "devices": {},
                },
            },
        },
    },
}

CREATED_VM_SPECS = {
    "apiVersion": "kubevirt.io/v1",
    "kind": "VirtualMachine",
    "metadata": {
        "namespace": "default",
    },
    "spec": {
        "running": True,
        "runStrategy": None,
        "template": {
            "spec": {
                "domain": {
                    "devices": {
                        "cpu": {
                            "cores": 2,
                            "socket": 1,
                            "threads": 2,
                        }
                    },
                },
            },
        },
    },
}


@pytest.mark.parametrize(
    "params,expected",
    [
        (CREATE_VM_PARAMS, CREATED_VM),
        (CREATE_VM_PARAMS_RUN_STRATEGY, CREATED_VM_RUN_STRATEGY),
        (CREATE_VM_PARAMS_ANNOTATIONS, CREATED_VM_ANNOTATIONS),
        (CREATE_VM_PARAMS_LABELS, CREATED_VM_LABELS),
        (CREATE_VM_PARAMS_INSTANCETYPE, CREATED_VM_INSTANCETYPE),
        (CREATE_VM_PARAMS_PREFERENCE, CREATED_VM_PREFERENCE),
        (CREATE_VM_PARAMS_DATAVOLUMETEMPLATE, CREATED_VM_DATAVOLUMETEMPLATE),
        (CREATE_VM_PARAMS_NAME, CREATED_VM_NAME),
        (CREATE_VM_PARAMS_GENERATE_NAME, CREATED_VM_GENERATE_NAME),
        (CREATE_VM_PARAMS_SPECS, CREATED_VM_SPECS),
    ],
)
def test_create_vm(params, expected):
    assert kubevirt_vm.create_vm(params) == expected


@pytest.mark.parametrize(
    "params,expected",
    [
        ({"running": None, "run_strategy": "Manual"}, {}),
        (
            {"running": None, "run_strategy": None},
            {"wait_condition": kubevirt_vm.WAIT_CONDITION_READY},
        ),
        (
            {"running": True, "run_strategy": None},
            {"wait_condition": kubevirt_vm.WAIT_CONDITION_READY},
        ),
        (
            {"running": None, "run_strategy": "Always"},
            {"wait_condition": kubevirt_vm.WAIT_CONDITION_READY},
        ),
        (
            {"running": None, "run_strategy": "RerunOnFailure"},
            {"wait_condition": kubevirt_vm.WAIT_CONDITION_READY},
        ),
        (
            {"running": None, "run_strategy": "Once"},
            {"wait_condition": kubevirt_vm.WAIT_CONDITION_READY},
        ),
        (
            {"running": False, "run_strategy": None},
            {"wait_condition": kubevirt_vm.WAIT_CONDITION_VMI_NOT_EXISTS},
        ),
        (
            {"running": None, "run_strategy": "Halted"},
            {"wait_condition": kubevirt_vm.WAIT_CONDITION_VMI_NOT_EXISTS},
        ),
    ],
)
def test_set_wait_condition(mocker, params, expected):
    module = mocker.Mock()
    module.params = params

    kubevirt_vm.set_wait_condition(module)

    assert module.params == params | expected


MODULE_PARAMS_START = MODULE_PARAMS_DEFAULT | {
    "name": "testvm",
    "namespace": "default",
    "state": "started",
}

MODULE_PARAMS_STOP = MODULE_PARAMS_DEFAULT | {
    "name": "testvm",
    "namespace": "default",
    "state": "stopped",
}

MODULE_PARAMS_STOP_FORCE = MODULE_PARAMS_DEFAULT | {
    "name": "testvm",
    "namespace": "default",
    "state": "stopped",
    "grace_period_seconds": 0,
}

MODULE_PARAMS_RESTART = MODULE_PARAMS_DEFAULT | {
    "name": "testvm",
    "namespace": "default",
    "state": "restarted",
}

MODULE_PARAMS_RESTART_FORCE = MODULE_PARAMS_DEFAULT | {
    "name": "testvm",
    "namespace": "default",
    "state": "restarted",
    "grace_period_seconds": 0,
}

SUBRESOURCE_BASE_PATH = (
    f"/apis/{kubevirt_vm.SUBRESOURCE_API}/namespaces/default/virtualmachines/testvm"
)


@pytest.mark.parametrize(
    "module_params,action,expected_body,vm_ready",
    [
        (MODULE_PARAMS_START, "start", None, False),
        (MODULE_PARAMS_STOP, "stop", None, True),
        (MODULE_PARAMS_STOP_FORCE, "stop", {"gracePeriod": 0}, True),
        (MODULE_PARAMS_RESTART, "restart", None, None),
        (MODULE_PARAMS_RESTART_FORCE, "restart", {"gracePeriodSeconds": 0}, None),
    ],
)
def test_subresource_action(mocker, module_params, action, expected_body, vm_ready):
    mocker.patch.object(AnsibleModule, "exit_json", exit_json)
    mocker.patch.object(
        kubevirt_vm, "_apply_definition", return_value={"changed": False}
    )
    mock_client = mocker.Mock()
    mocker.patch.object(kubevirt_vm, "get_api_client", return_value=mock_client)

    if vm_ready is not None:
        mocker.patch.object(kubevirt_vm, "_vm_is_ready", return_value=vm_ready)

    with pytest.raises(AnsibleExitJson) as exc, patch_module_args(module_params):
        kubevirt_vm.main()

    mock_client.client.request.assert_called_once_with(
        "put",
        f"{SUBRESOURCE_BASE_PATH}/{action}",
        body=expected_body,
        header_params={"Accept": "*/*"},
    )
    assert exc.value.args[0]["changed"] is True


@pytest.mark.parametrize(
    "state,vm_ready",
    [
        ("started", False),
        ("stopped", True),
        ("restarted", None),
    ],
)
def test_subresource_action_check_mode(mocker, state, vm_ready):
    mocker.patch.object(AnsibleModule, "exit_json", exit_json)
    mocker.patch.object(
        kubevirt_vm, "_apply_definition", return_value={"changed": False}
    )
    mock_client = mocker.Mock()
    mocker.patch.object(kubevirt_vm, "get_api_client", return_value=mock_client)

    if vm_ready is not None:
        mocker.patch.object(kubevirt_vm, "_vm_is_ready", return_value=vm_ready)

    params = MODULE_PARAMS_DEFAULT | {
        "name": "testvm",
        "namespace": "default",
        "state": state,
        "_ansible_check_mode": True,
    }
    with pytest.raises(AnsibleExitJson) as exc, patch_module_args(params):
        kubevirt_vm.main()

    mock_client.client.request.assert_not_called()
    assert exc.value.args[0]["changed"] is True


@pytest.mark.parametrize("state", ["started", "stopped", "restarted"])
def test_subresource_action_fails_without_name(mocker, state):
    mocker.patch.object(AnsibleModule, "fail_json", fail_json)

    params = MODULE_PARAMS_DEFAULT | {
        "namespace": "default",
        "state": state,
        "generate_name": "testvm-",
    }
    with pytest.raises(AnsibleFailJson), patch_module_args(params):
        kubevirt_vm.main()


@pytest.mark.parametrize(
    "state,action,vm_ready",
    [
        ("started", "start", False),
        ("stopped", "stop", True),
        ("restarted", "restart", None),
    ],
)
def test_subresource_action_api_error(mocker, state, action, vm_ready):
    mocker.patch.object(AnsibleModule, "exit_json", exit_json)
    mocker.patch.object(AnsibleModule, "fail_json", fail_json)
    mocker.patch.object(
        kubevirt_vm, "_apply_definition", return_value={"changed": False}
    )

    mock_client = mocker.Mock()
    mock_client.client.request.side_effect = Exception("API error")
    mocker.patch.object(kubevirt_vm, "get_api_client", return_value=mock_client)

    if vm_ready is not None:
        mocker.patch.object(kubevirt_vm, "_vm_is_ready", return_value=vm_ready)

    params = MODULE_PARAMS_DEFAULT | {
        "name": "testvm",
        "namespace": "default",
        "state": state,
    }
    with pytest.raises(AnsibleFailJson) as exc, patch_module_args(params):
        kubevirt_vm.main()

    assert f"Failed to {action} VirtualMachine" in exc.value.args[0]["msg"]


@pytest.mark.parametrize(
    "state,expected_condition,vm_ready",
    [
        ("started", kubevirt_vm.WAIT_CONDITION_READY, False),
        ("stopped", kubevirt_vm.WAIT_CONDITION_VMI_NOT_EXISTS, True),
        ("restarted", kubevirt_vm.WAIT_CONDITION_READY, None),
    ],
)
def test_subresource_action_wait(mocker, state, expected_condition, vm_ready):
    mocker.patch.object(AnsibleModule, "exit_json", exit_json)
    mocker.patch.object(
        kubevirt_vm, "_apply_definition", return_value={"changed": False}
    )
    mock_client = mocker.Mock()
    mocker.patch.object(kubevirt_vm, "get_api_client", return_value=mock_client)

    if vm_ready is not None:
        mocker.patch.object(kubevirt_vm, "_vm_is_ready", return_value=vm_ready)

    mock_svc = mocker.Mock()
    mock_svc.find.return_value = {"resources": [], "api_found": True}
    mocker.patch.object(kubevirt_vm, "K8sService", return_value=mock_svc)

    params = MODULE_PARAMS_DEFAULT | {
        "name": "testvm",
        "namespace": "default",
        "state": state,
        "wait": True,
    }
    with pytest.raises(AnsibleExitJson) as exc, patch_module_args(params):
        kubevirt_vm.main()

    mock_svc.find.assert_called_once_with(
        kind="VirtualMachine",
        api_version="kubevirt.io/v1",
        name="testvm",
        namespace="default",
        wait=True,
        wait_sleep=5,
        wait_timeout=5,
        condition=expected_condition,
    )
    assert exc.value.args[0]["changed"] is True


@pytest.mark.parametrize(
    "state,vm_ready",
    [
        ("started", True),
        ("stopped", False),
    ],
)
def test_subresource_action_idempotent(mocker, state, vm_ready):
    mocker.patch.object(AnsibleModule, "exit_json", exit_json)
    mocker.patch.object(
        kubevirt_vm, "_apply_definition", return_value={"changed": False}
    )
    mock_client = mocker.Mock()
    mocker.patch.object(kubevirt_vm, "get_api_client", return_value=mock_client)
    mocker.patch.object(kubevirt_vm, "_vm_is_ready", return_value=vm_ready)

    params = MODULE_PARAMS_DEFAULT | {
        "name": "testvm",
        "namespace": "default",
        "state": state,
    }
    with pytest.raises(AnsibleExitJson) as exc, patch_module_args(params):
        kubevirt_vm.main()

    mock_client.client.request.assert_not_called()
    assert exc.value.args[0]["changed"] is False


@pytest.mark.parametrize(
    "state,action,vm_ready,definition_changed",
    [
        ("started", "start", False, True),
        ("started", "start", True, True),
        ("stopped", "stop", True, True),
        ("stopped", "stop", False, True),
        ("restarted", "restart", None, True),
        ("started", "start", False, False),
        ("stopped", "stop", True, False),
        ("restarted", "restart", None, False),
    ],
)
def test_subresource_action_with_definition(
    mocker, state, action, vm_ready, definition_changed
):
    mocker.patch.object(AnsibleModule, "exit_json", exit_json)

    mock_client = mocker.Mock()
    mocker.patch.object(kubevirt_vm, "get_api_client", return_value=mock_client)

    def fake_run_module(module):
        module.exit_json(changed=definition_changed, method="update", result={})

    mocker.patch.object(runner, "run_module", side_effect=fake_run_module)

    if vm_ready is not None:
        mocker.patch.object(kubevirt_vm, "_vm_is_ready", return_value=vm_ready)

    params = MODULE_PARAMS_DEFAULT | {
        "name": "testvm",
        "namespace": "default",
        "state": state,
        "labels": {"app": "test"},
    }
    with pytest.raises(AnsibleExitJson) as exc, patch_module_args(params):
        kubevirt_vm.main()

    runner.run_module.assert_called_once()

    already_in_desired_state = (action == "start" and vm_ready) or (
        action == "stop" and not vm_ready
    )
    if already_in_desired_state:
        mock_client.client.request.assert_not_called()
    else:
        mock_client.client.request.assert_called_once_with(
            "put",
            f"{SUBRESOURCE_BASE_PATH}/{action}",
            body=None,
            header_params={"Accept": "*/*"},
        )

    assert exc.value.args[0]["changed"] is (
        definition_changed or not already_in_desired_state
    )
