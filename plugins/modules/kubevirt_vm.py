#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2023 Red Hat, Inc.
# Based on the kubernetes.core.k8s module
# Apache License 2.0 (see LICENSE or http://www.apache.org/licenses/LICENSE-2.0)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = """
module: kubevirt_vm

short_description: Create or delete KubeVirt VirtualMachines

author:
- "KubeVirt.io Project (!UNKNOWN)"

description:
- Use the Kubernetes Python client to perform create or delete operations on KubeVirt VirtualMachines.
- Pass options to create the VirtualMachine as module arguments.
- Authenticate using either a config file, certificates, password or token.
- Supports check mode.

extends_documentation_fragment:
- kubevirt.core.kubevirt_auth_options

options:
  api_version:
    description:
    - Use this to set the API version of KubeVirt.
    type: str
    default: kubevirt.io/v1
  name:
    description:
    - Specify the name of the C(VirtualMachine).
    - This option is ignored when O(state=present) is not set.
    - Mutually exclusive with O(generate_name).
    type: str
  generate_name:
    description:
    - Specify the basis of the C(VirtualMachine) name and random characters will be added automatically on the cluster to
      generate a unique name.
    - Only used when O(state=present).
    - Mutually exclusive with O(name).
    type: str
  namespace:
    description:
    - Specify the namespace of the C(VirtualMachine).
    type: str
    required: yes
  annotations:
    description:
    - Specify annotations to set on the C(VirtualMachine).
    - Only used when O(state=present).
    type: dict
  labels:
    description:
    - Specify labels to set on the C(VirtualMachine).
    type: dict
  running:
    description:
    - Specify whether the C(VirtualMachine) should be running or not.
    type: bool
    default: yes
  instancetype:
    description:
    - Specify the C(Instancetype) matcher of the C(VirtualMachine).
    - Only used when O(state=present).
    type: dict
  preference:
    description:
    - Specify the C(Preference) matcher of the C(VirtualMachine).
    - Only used when O(state=present).
    type: dict
  data_volume_templates:
    description:
    - Specify the C(DataVolume) templates of the C(VirtualMachine).
    - See U(https://kubevirt.io/api-reference/main/definitions.html#_v1_datavolumetemplatespec)
    type: list
    elements: 'dict'
  spec:
    description:
    - Specify the template spec of the C(VirtualMachine).
    - See U(https://kubevirt.io/api-reference/main/definitions.html#_v1_virtualmachineinstancespec)
    type: dict
  wait:
    description:
    - Whether to wait for the C(VirtualMachine) to end up in the ready state.
    type: bool
    default: no
  wait_sleep:
    description:
    - Number of seconds to sleep between checks.
    - Ignored if O(wait) is not set.
    default: 5
    type: int
  wait_timeout:
    description:
    - How long in seconds to wait for the resource to end up in the ready state.
    - Ignored if O(wait) is not set.
    default: 120
    type: int
  delete_options:
    description:
    - Configure behavior when deleting an object.
    - Only used when O(state=absent).
    type: dict
    suboptions:
      propagationPolicy:
        description:
        - Use to control how dependent objects are deleted.
        - If not specified, the default policy for the object type will be used. This may vary across object types.
        type: str
        choices:
        - Foreground
        - Background
        - Orphan
      preconditions:
        description:
        - Specify condition that must be met for delete to proceed.
        type: dict
        suboptions:
          resourceVersion:
            description:
            - Specify the resource version of the target object.
            type: str
          uid:
            description:
            - Specify the C(UID) of the target object.
            type: str
  state:
    description:
    - Determines if an object should be created, patched, or deleted.
    - When set to O(state=present), an object will be created, if it does not already exist.
    - If set to O(state=absent), an existing object will be deleted.
    - If set to O(state=present), an existing object will be patched, if its attributes differ from those specified.
    type: str
    default: present
    choices:
    - absent
    - present
  force:
    description:
    - If set to O(force=yes), and O(state=present) is set, an existing object will be replaced.
    type: bool
    default: no

requirements:
- "python >= 3.9"
- "kubernetes >= 28.1.0"
- "PyYAML >= 3.11"
- "jsonpatch"
"""

EXAMPLES = """
- name: Create a VirtualMachine
  kubevirt.core.kubevirt_vm:
    state: present
    name: testvm
    namespace: default
    labels:
      app: test
    instancetype:
      name: u1.medium
    preference:
      name: fedora
    spec:
      domain:
        devices:
          interfaces:
            - name: default
              masquerade: {}
            - name: bridge-network
              bridge: {}
      networks:
        - name: default
          pod: {}
        - name: bridge-network
          multus:
            networkName: kindexgw
      volumes:
        - containerDisk:
            image: quay.io/containerdisks/fedora:latest
          name: containerdisk
        - cloudInitNoCloud:
            userData: |-
              #cloud-config
              # The default username is: fedora
              ssh_authorized_keys:
                - ssh-ed25519 AAAA...
          name: cloudinit

- name: Create a VirtualMachine with a DataVolume template
  kubevirt.core.kubevirt_vm:
    state: present
    name: testvm-with-dv
    namespace: default
    labels:
      app: test
    instancetype:
      name: u1.medium
    preference:
      name: fedora
    data_volume_templates:
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
    spec:
      domain:
        devices: {}
      volumes:
        - dataVolume:
            name: testdv
          name: datavolume
        - cloudInitNoCloud:
            userData: |-
              #cloud-config
              # The default username is: fedora
              ssh_authorized_keys:
                - ssh-ed25519 AAAA...
          name: cloudinit
    wait: true

- name: Delete a VirtualMachine
  kubevirt.core.kubevirt_vm:
    name: testvm
    namespace: default
    state: absent
"""

RETURN = """
result:
  description:
  - The created object. Will be empty in the case of a deletion.
  type: complex
  returned: success
  contains:
    changed:
      description: Whether the C(VirtualMachine) was changed or not.
      type: bool
      sample: True
    duration:
      description: Elapsed time of the task in seconds.
      returned: When O(wait=true).
      type: int
      sample: 48
    method:
      description: Method executed on the Kubernetes API.
      returned: success
      type: str
"""

from copy import deepcopy
from typing import Dict

from ansible_collections.kubernetes.core.plugins.module_utils.ansiblemodule import (
    AnsibleModule,
)
from ansible_collections.kubernetes.core.plugins.module_utils.args_common import (
    AUTH_ARG_SPEC,
    COMMON_ARG_SPEC,
)
from ansible_collections.kubernetes.core.plugins.module_utils.k8s import (
    runner,
)
from ansible_collections.kubernetes.core.plugins.module_utils.k8s.core import (
    AnsibleK8SModule,
)
from ansible_collections.kubernetes.core.plugins.module_utils.k8s.exceptions import (
    CoreException,
)


def create_vm(params: Dict) -> Dict:
    """
    create_vm constructs a VM from the module parameters.
    """
    vm = {
        "apiVersion": params["api_version"],
        "kind": "VirtualMachine",
        "metadata": {
            "namespace": params["namespace"],
        },
        "spec": {
            "running": params["running"],
            "template": {"spec": {"domain": {"devices": {}}}},
        },
    }

    if (name := params.get("name")) is not None:
        vm["metadata"]["name"] = name
    if (generate_name := params.get("generate_name")) is not None:
        vm["metadata"]["generateName"] = generate_name

    template_metadata = {}
    if (annotations := params.get("annotations")) is not None:
        vm["metadata"]["annotations"] = annotations
        template_metadata["annotations"] = annotations
    if (labels := params.get("labels")) is not None:
        vm["metadata"]["labels"] = labels
        template_metadata["labels"] = labels
    if template_metadata:
        vm["spec"]["template"]["metadata"] = template_metadata

    if (instancetype := params.get("instancetype")) is not None:
        vm["spec"]["instancetype"] = instancetype
    if (preference := params.get("preference")) is not None:
        vm["spec"]["preference"] = preference
    if (data_volume_templates := params.get("data_volume_templates")) is not None:
        vm["spec"]["dataVolumeTemplates"] = data_volume_templates
    if (spec := params.get("spec")) is not None:
        vm["spec"]["template"]["spec"] = spec

    return vm


def arg_spec() -> Dict:
    """
    arg_spec defines the argument spec of this module.
    """
    spec = {
        "api_version": {"default": "kubevirt.io/v1"},
        "name": {},
        "generate_name": {},
        "namespace": {"required": True},
        "annotations": {"type": "dict"},
        "labels": {"type": "dict"},
        "running": {"type": "bool", "default": True},
        "instancetype": {"type": "dict"},
        "preference": {"type": "dict"},
        "data_volume_templates": {"type": "list", "elements": "dict"},
        "spec": {"type": "dict"},
        "wait": {"type": "bool", "default": False},
        "wait_sleep": {"type": "int", "default": 5},
        "wait_timeout": {"type": "int", "default": 120},
        "delete_options": {
            "type": "dict",
            "default": None,
            "options": {
                "propagationPolicy": {
                    "choices": ["Foreground", "Background", "Orphan"]
                },
                "preconditions": {
                    "type": "dict",
                    "options": {
                        "resourceVersion": {"type": "str"},
                        "uid": {"type": "str"},
                    },
                },
            },
        },
    }
    spec.update(deepcopy(AUTH_ARG_SPEC))
    spec.update(deepcopy(COMMON_ARG_SPEC))

    return spec


def main() -> None:
    """
    main instantiates the AnsibleK8SModule, creates the resource
    definition and runs the module.
    """
    module = AnsibleK8SModule(
        module_class=AnsibleModule,
        argument_spec=arg_spec(),
        mutually_exclusive=[
            ("name", "generate_name"),
        ],
        required_one_of=[
            ("name", "generate_name"),
        ],
        supports_check_mode=True,
    )

    # Set resource_definition to our constructed VM
    module.params["resource_definition"] = create_vm(module.params)

    # Set wait_condition to allow waiting for the ready state of the VirtualMachine
    if module.params["running"]:
        module.params["wait_condition"] = {"type": "Ready", "status": True}
    else:
        module.params["wait_condition"] = {
            "type": "Ready",
            "status": False,
            "reason": "VMINotExists",
        }

    try:
        runner.run_module(module)
    except CoreException as exc:
        module.fail_from_exception(exc)


if __name__ == "__main__":
    main()
