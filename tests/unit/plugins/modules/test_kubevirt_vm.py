# -*- coding: utf-8 -*-
# Copyright: (c) 2021, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

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
def vm_definition():
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
def vm_manifest():
    return """apiVersion: kubevirt.io/v1
kind: VirtualMachine
metadata:
  name: "testvm"
  namespace: "default"
  labels:
    environment: staging
    service: loadbalancer
spec:
  running: True
  instancetype:
    name: u1.medium
  preference:
    name: fedora
  dataVolumeTemplates:
    - metadata:
        name: testdv
      spec:
        source:
          registry:
            url: docker://quay.io/containerdisks/fedora:latest
        storage:
          accessModes:
          - ReadWriteOnce
          resources:
            requests:
              storage: 5Gi
  template:
    metadata:
      labels:
        environment: staging
        service: loadbalancer
    spec:
      domain:
        devices: {}
      terminationGracePeriodSeconds: 180
"""


@pytest.fixture(scope="module")
def module_params_create():
    return {
        "name": "testvm",
        "namespace": "default",
        "state": "present",
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
def k8s_module_params_create(module_params_create, vm_manifest):
    return module_params_create | {
        "api_version": "kubevirt.io/v1",
        "running": True,
        "wait": False,
        "wait_sleep": 5,
        "wait_timeout": 120,
        "force": False,
        "generate_name": None,
        "annotations": None,
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
        "delete_options": None,
        "resource_definition": vm_manifest,
        "wait_condition": {"type": "Ready", "status": True},
    }


def test_module_fails_when_required_args_missing(monkeypatch):
    monkeypatch.setattr(AnsibleModule, "fail_json", fail_json)
    with pytest.raises(AnsibleFailJson):
        set_module_args({})
        kubevirt_vm.main()


def test_module_create(
    monkeypatch, mocker, module_params_create, k8s_module_params_create, vm_definition
):
    monkeypatch.setattr(AnsibleModule, "exit_json", exit_json)
    monkeypatch.setattr(runner, "get_api_client", lambda _: None)

    set_module_args(module_params_create)

    perform_action = mocker.patch.object(runner, "perform_action")
    perform_action.return_value = {
        "method": "create",
        "changed": True,
        "result": "success",
    }

    with pytest.raises(AnsibleExitJson):
        kubevirt_vm.main()
    perform_action.assert_called_once_with(
        mocker.ANY, vm_definition, k8s_module_params_create
    )
