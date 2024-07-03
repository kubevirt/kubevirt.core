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
        "resource_definition": vm_definition_create,
        "wait_condition": {"type": "Ready", "status": True},
    }


@pytest.fixture(scope="module")
def k8s_module_params_running(module_params_running, vm_definition_running):
    return module_params_running | {
        "generate_name": None,
        "resource_definition": vm_definition_running,
        "wait_condition": {"type": "Ready", "status": True},
    }


@pytest.fixture(scope="module")
def k8s_module_params_stopped(module_params_stopped, vm_definition_stopped):
    return module_params_stopped | {
        "generate_name": None,
        "resource_definition": vm_definition_stopped,
        "wait_condition": {"type": "Ready", "status": False, "reason": "VMINotExists"},
    }


@pytest.fixture(scope="module")
def k8s_module_params_delete(module_params_delete, vm_definition_running):
    return module_params_delete | {
        "generate_name": None,
        "resource_definition": vm_definition_running,
        "wait_condition": {"type": "Ready", "status": True},
    }


def test_module_fails_when_required_args_missing(mocker):
    mocker.patch.object(AnsibleModule, "fail_json", fail_json)
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
    mocker,
    module_params,
    k8s_module_params,
    vm_definition,
    method,
):
    mocker.patch.object(AnsibleModule, "exit_json", exit_json)
    mocker.patch.object(runner, "get_api_client")

    perform_action = mocker.patch.object(
        runner,
        "perform_action",
        return_value={
            "method": method,
            "changed": True,
            "result": "success",
        },
    )

    with pytest.raises(AnsibleExitJson):
        set_module_args(request.getfixturevalue(module_params))
        kubevirt_vm.main()

    perform_action.assert_called_once_with(
        mocker.ANY,
        request.getfixturevalue(vm_definition),
        request.getfixturevalue(k8s_module_params),
    )


@pytest.fixture(scope="module")
def create_vm_params():
    return {
        "api_version": "kubevirt.io/v1",
        "running": True,
        "namespace": "default",
    }


@pytest.fixture(scope="module")
def create_vm_params_annotations(create_vm_params):
    return create_vm_params | {
        "annotations": {"test": "test"},
    }


@pytest.fixture(scope="module")
def create_vm_params_labels(create_vm_params):
    return create_vm_params | {
        "labels": {"test": "test"},
    }


@pytest.fixture(scope="module")
def create_vm_params_instancetype(create_vm_params):
    return create_vm_params | {
        "instancetype": {"name": "u1.medium"},
    }


@pytest.fixture(scope="module")
def create_vm_params_preference(create_vm_params):
    return create_vm_params | {
        "preference": {"name": "fedora"},
    }


@pytest.fixture(scope="module")
def create_vm_params_datavolumetemplate(create_vm_params):
    return create_vm_params | {
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


@pytest.fixture(scope="module")
def create_vm_params_name(create_vm_params):
    return create_vm_params | {
        "name": "testvm",
    }


@pytest.fixture(scope="module")
def create_vm_params_generate_name(create_vm_params):
    return create_vm_params | {
        "generate_name": "testvm-1234",
    }


@pytest.fixture(scope="module")
def create_vm_params_specs(create_vm_params):
    return create_vm_params | {
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


@pytest.fixture(scope="module")
def created_vm():
    return {
        "apiVersion": "kubevirt.io/v1",
        "kind": "VirtualMachine",
        "metadata": {
            "namespace": "default",
        },
        "spec": {
            "running": True,
            "template": {
                "spec": {
                    "domain": {
                        "devices": {},
                    },
                },
            },
        },
    }


@pytest.fixture(scope="module")
def created_vm_labels():
    return {
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


@pytest.fixture(scope="module")
def created_vm_annotations():
    return {
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


@pytest.fixture(scope="module")
def created_vm_instancetype():
    return {
        "apiVersion": "kubevirt.io/v1",
        "kind": "VirtualMachine",
        "metadata": {
            "namespace": "default",
        },
        "spec": {
            "running": True,
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


@pytest.fixture(scope="module")
def created_vm_preference():
    return {
        "apiVersion": "kubevirt.io/v1",
        "kind": "VirtualMachine",
        "metadata": {
            "namespace": "default",
        },
        "spec": {
            "running": True,
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


@pytest.fixture(scope="module")
def created_vm_datavolumetemplate():
    return {
        "apiVersion": "kubevirt.io/v1",
        "kind": "VirtualMachine",
        "metadata": {
            "namespace": "default",
        },
        "spec": {
            "running": True,
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


@pytest.fixture(scope="module")
def created_vm_name():
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
                    "domain": {
                        "devices": {},
                    },
                },
            },
        },
    }


@pytest.fixture(scope="module")
def created_vm_generate_name():
    return {
        "apiVersion": "kubevirt.io/v1",
        "kind": "VirtualMachine",
        "metadata": {
            "generateName": "testvm-1234",
            "namespace": "default",
        },
        "spec": {
            "running": True,
            "template": {
                "spec": {
                    "domain": {
                        "devices": {},
                    },
                },
            },
        },
    }


@pytest.fixture(scope="module")
def created_vm_specs():
    return {
        "apiVersion": "kubevirt.io/v1",
        "kind": "VirtualMachine",
        "metadata": {
            "namespace": "default",
        },
        "spec": {
            "running": True,
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
        ("create_vm_params", "created_vm"),
        ("create_vm_params_annotations", "created_vm_annotations"),
        ("create_vm_params_labels", "created_vm_labels"),
        ("create_vm_params_instancetype", "created_vm_instancetype"),
        ("create_vm_params_preference", "created_vm_preference"),
        ("create_vm_params_datavolumetemplate", "created_vm_datavolumetemplate"),
        ("create_vm_params_name", "created_vm_name"),
        ("create_vm_params_generate_name", "created_vm_generate_name"),
        ("create_vm_params_specs", "created_vm_specs"),
    ],
)
def test_create_vm(request, params, expected):
    assert kubevirt_vm.create_vm(
        request.getfixturevalue(params)
    ) == request.getfixturevalue(expected)
