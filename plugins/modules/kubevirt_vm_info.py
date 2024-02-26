#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2023 Red Hat, Inc.
# Based on the kubernetes.core.k8s_info module
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = """
module: kubevirt_vm_info

short_description: Describe VirtualMachines on Kubernetes

author:
- "KubeVirt.io Project (!UNKNOWN)"

description:
  - Use the Kubernetes Python client to perform read operations on KubeVirt VirtualMachines.
  - Pass options to find VirtualMachines as module arguments.
  - Authenticate using either a config file, certificates, password or token.
  - Supports check mode.

options:
  api_version:
    description:
    - Use this to set the API version of KubeVirt.
    type: str
    default: kubevirt.io/v1
  name:
    description:
    - Specify the name of the VirtualMachine.
    type: str
  namespace:
    description:
    - Specify the namespace of VirtualMachines.
    type: str
  label_selectors:
    description: List of label selectors to use to filter results
    type: list
    elements: str
    default: []
  field_selectors:
    description: List of field selectors to use to filter results
    type: list
    elements: str
    default: []
  wait:
    description:
    - Whether to wait for the VirtualMachine to end up in the ready state.
    type: bool
    default: no
  wait_sleep:
    description:
    - Number of seconds to sleep between checks.
    - Ignored if C(wait) is not set.
    default: 5
    type: int
  wait_timeout:
    description:
    - How long in seconds to wait for the resource to end up in the desired state.
    - Ignored if C(wait) is not set.
    default: 120
    type: int

extends_documentation_fragment:
  - kubernetes.core.k8s_auth_options

requirements:
  - "python >= 3.6"
  - "kubernetes >= 12.0.0"
"""

EXAMPLES = """
- name: Get an existing VirtualMachine
  kubevirt.core.kubevirt_vm_info:
    name: testvm
    namespace: default
  register: default_testvm

- name: Get a list of all VirtualMachines
  kubevirt.core.kubevirt_vm_info:
    namespace: default
  register: vm_list

- name: Get a list of all VirtualMachines from any namespace
  kubevirt.core.kubevirt_vm_info:
  register: vm_list

- name: Search for all VirtualMachines labelled app=test
  kubevirt.core.kubevirt_vm_info:
    label_selectors:
      - app=test

- name: Wait until the VirtualMachine is Ready
  kubevirt.core.kubevirt_vm_info:
    name: testvm
    namespace: default
    wait: true
"""

RETURN = """
api_found:
  description:
  - Whether the specified api_version and VirtualMachine kind were successfully mapped to an existing API on the targeted cluster.
  returned: always
  type: bool
resources:
  description:
  - The VirtualMachine(s) that exists
  returned: success
  type: complex
  contains:
    api_version:
      description: The versioned schema of this representation of an object.
      returned: success
      type: str
    kind:
      description: Represents the REST resource this object represents.
      returned: success
      type: str
    metadata:
      description: Standard object metadata. Includes name, namespace, annotations, labels, etc.
      returned: success
      type: dict
    spec:
      description: Specific attributes of the VirtualMachine. Can vary based on the I(api_version).
      returned: success
      type: dict
    status:
      description: Current status details for the VirtualMachine.
      returned: success
      type: dict
"""

from copy import deepcopy

from ansible_collections.kubernetes.core.plugins.module_utils.ansiblemodule import (
    AnsibleModule,
)
from ansible_collections.kubernetes.core.plugins.module_utils.args_common import (
    AUTH_ARG_SPEC,
)
from ansible_collections.kubernetes.core.plugins.module_utils.k8s.core import (
    AnsibleK8SModule,
)
from ansible_collections.kubernetes.core.plugins.module_utils.k8s.client import (
    get_api_client,
)
from ansible_collections.kubernetes.core.plugins.module_utils.k8s.exceptions import (
    CoreException,
)
from ansible_collections.kubernetes.core.plugins.module_utils.k8s.service import (
    K8sService,
)


def execute_module(module, svc):
    """
    execute_module defines the kind and wait_condition and runs the lookup
    of resources.
    """
    # Set kind to query for VirtualMachines
    KIND = "VirtualMachine"

    # Set wait_condition to allow waiting for the ready state of the VirtualMachine
    WAIT_CONDITION = {"type": "Ready", "status": True}

    facts = svc.find(
        kind=KIND,
        api_version=module.params["api_version"],
        name=module.params["name"],
        namespace=module.params["namespace"],
        label_selectors=module.params["label_selectors"],
        field_selectors=module.params["field_selectors"],
        wait=module.params["wait"],
        wait_sleep=module.params["wait_sleep"],
        wait_timeout=module.params["wait_timeout"],
        condition=WAIT_CONDITION,
    )

    module.exit_json(changed=False, **facts)


def arg_spec():
    """
    arg_spec defines the argument spec of this module.
    """
    spec = {
        "api_version": {"default": "kubevirt.io/v1"},
        "name": {},
        "namespace": {},
        "label_selectors": {"type": "list", "elements": "str", "default": []},
        "field_selectors": {"type": "list", "elements": "str", "default": []},
        "wait": {"type": "bool", "default": False},
        "wait_sleep": {"type": "int", "default": 5},
        "wait_timeout": {"type": "int", "default": 120},
    }
    spec.update(deepcopy(AUTH_ARG_SPEC))

    return spec


def main():
    """
    main instantiates the AnsibleK8SModule and runs the module.
    """
    module = AnsibleK8SModule(
        module_class=AnsibleModule, argument_spec=arg_spec(), supports_check_mode=True
    )

    try:
        client = get_api_client(module)
        svc = K8sService(client, module)
        execute_module(module, svc)
    except CoreException as exc:
        module.fail_from_exception(exc)


if __name__ == "__main__":
    main()
