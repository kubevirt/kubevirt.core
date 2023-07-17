# -*- coding: utf-8 -*-
# Copyright: (c) 2021, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import unittest

from unittest.mock import patch, ANY

from ansible.module_utils import basic
from ansible_collections.kubernetes.core.plugins.module_utils.k8s import runner
from ansible_collections.kubernetes.kubevirt.plugins.modules import kubevirt_vm
from ansible_collections.kubernetes.kubevirt.tests.unit.utils.ansible_module_mock import (
    AnsibleFailJson,
    AnsibleExitJson,
    exit_json,
    fail_json,
    set_module_args,
    get_api_client
)

FIXTURE1 = {
    "apiVersion": "kubevirt.io/v1",
    "kind": "VirtualMachine",
    "metadata": {
        "name": "testvm",
        "namespace": "default",
        "labels": {
            "environment": "staging",
            "service": "loadbalancer"
        }
    },
    "spec": {
        "running": True,
        "template": {
            "metadata": {
                "labels": {
                    "environment": "staging",
                    "service": "loadbalancer"
                }
            },
            "spec": {
                "domain": {
                    "devices": {}
                },
                "terminationGracePeriodSeconds": 180
            }
        }
    }
}

METADATA = '''apiVersion: kubevirt.io/v1
kind: VirtualMachine
metadata:
  name: "testvm"
  namespace: "default"
  labels:
    environment: staging
    service: loadbalancer
spec:
  running: True
  template:
    metadata:
      labels:
        environment: staging
        service: loadbalancer
    spec:
      domain:
        devices: {}
      terminationGracePeriodSeconds: 180'''

FIXTURE2 = {
    'name': 'testvm',
    'namespace': 'default',
    'state': 'present',
    'labels': {
        'service': 'loadbalancer',
        'environment': 'staging'
    },
    'api_version': 'kubevirt.io/v1', 'running': True, 'termination_grace_period': 180, 'wait': False, 'wait_sleep': 5, 'wait_timeout': 120, 'force': False,
    'generate_name': None, 'annotations': None, 'instancetype': None, 'preference': None, 'infer_from_volume': None, 'clear_revision_name': None,
    'interfaces': None, 'networks': None, 'volumes': None, 'kubeconfig': None, 'context': None, 'host': None, 'api_key': None, 'username': None,
    'password': None, 'validate_certs': None, 'ca_cert': None, 'client_cert': None, 'client_key': None, 'proxy': None, 'no_proxy': None, 'proxy_headers': None,
    'persist_config': None, 'impersonate_user': None, 'impersonate_groups': None, 'delete_options': None,
    'resource_definition': METADATA,
    'wait_condition': {
        'type': 'Ready',
        'status': True
    }
}


class TestCreateVM(unittest.TestCase):
    def setUp(self):
        self.mock_module_helper = patch.multiple(
            basic.AnsibleModule,
            exit_json=exit_json,
            fail_json=fail_json
        )
        self.mock_module_helper.start()

        self.mock_runner = patch.multiple(
            runner,
            get_api_client=get_api_client
        )
        self.mock_runner.start()

        # Stop the patch after test execution
        # like tearDown but executed also when the setup failed
        self.addCleanup(self.mock_module_helper.stop)
        self.addCleanup(self.mock_runner.stop)

    def test_module_fail_when_required_args_missing(self):
        with self.assertRaises(AnsibleFailJson):
            set_module_args({})
            kubevirt_vm.main()

    def test_create(self):
        set_module_args(
            {
                "name": "testvm",
                "namespace": "default",
                "state": "present",
                "labels": {
                    "service": "loadbalancer",
                    "environment": "staging"
                }
            }
        )
        with patch.object(runner, "perform_action") as mock_run_command:
            mock_run_command.return_value = (
                {
                    "method": "create",
                    "changed": True,
                    "result": "success"
                }
            )  # successful execution
            with self.assertRaises(AnsibleExitJson) as result:
                kubevirt_vm.main()
            mock_run_command.assert_called_once_with(
                ANY,
                FIXTURE1,
                FIXTURE2,
            )
