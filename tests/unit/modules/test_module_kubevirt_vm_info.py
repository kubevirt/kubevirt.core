# -*- coding: utf-8 -*-
# Copyright: (c) 2021, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from unittest import TestCase
from unittest.mock import patch

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
    fail_json,
    set_module_args,
    get_api_client,
)

FIXTURE1 = {
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

FIXTURE2 = {
    "kind": "VirtualMachine",
    "api_version": "kubevirt.io/v1",
    "name": "testvm",
    "namespace": "default",
    "label_selectors": [],
    "field_selectors": [],
    "wait": False,
    "wait_sleep": 5,
    "wait_timeout": 120,
    "condition": {"type": "Ready", "status": True},
}


class TestDescribeVM(TestCase):
    def setUp(self):
        self.mock_module_helper = patch.multiple(
            AnsibleModule, exit_json=exit_json, fail_json=fail_json
        )
        self.mock_module_helper.start()

        self.mock_main = patch.multiple(kubevirt_vm_info, get_api_client=get_api_client)
        self.mock_main.start()

        # Stop the patch after test execution
        # like tearDown but executed also when the setup failed
        self.addCleanup(self.mock_module_helper.stop)
        self.addCleanup(self.mock_main.stop)

    def run_module(self, fixture):
        with patch.object(K8sService, "find") as mock_find_command:
            mock_find_command.return_value = {
                "api_found": True,
                "failed": False,
                "resources": [],
            }  # successful execution
            with self.assertRaises(AnsibleExitJson):
                kubevirt_vm_info.main()
            mock_find_command.assert_called_once_with(
                **fixture,
            )

    def test_describe_without_args(self):
        set_module_args({})
        self.run_module(FIXTURE1)

    def test_describe_with_args(self):
        set_module_args(
            {
                "name": "testvm",
                "namespace": "default",
            }
        )
        self.run_module(FIXTURE2)
