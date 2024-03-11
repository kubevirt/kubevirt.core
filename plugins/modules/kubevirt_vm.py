#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2023 Red Hat, Inc.
# Based on the kubernetes.core.k8s module
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

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
- kubevirt.core.k8s_auth_options
- kubevirt.core.k8s_state_options
- kubevirt.core.k8s_delete_options

options:
  api_version:
    description:
    - Use this to set the API version of KubeVirt.
    type: str
    default: kubevirt.io/v1
  name:
    description:
    - Specify the name of the VirtualMachine.
    - This option is ignored when I(state) is not set to C(present).
    - mutually exclusive with C(generate_name).
    type: str
  generate_name:
    description:
    - Specify the basis of the VirtualMachine name and random characters will be added automatically on server to
      generate a unique name.
    - Only used when I(state=present).
    - mutually exclusive with C(name).
    type: str
  namespace:
    description:
    - Specify the namespace of the VirtualMachine.
    type: str
    required: yes
  annotations:
    description:
    - Specify annotations to set on the VirtualMachine.
    - Only used when I(state=present).
    type: dict
  labels:
    description:
    - Specify labels to set on the VirtualMachine.
    type: dict
  running:
    description:
    - Specify whether the VirtualMachine should be running.
    type: bool
    default: yes
  instancetype:
    description:
    - Specify the instancetype matcher of the VirtualMachine.
    - Only used when I(state=present).
    type: dict
  preference:
    description:
    - Specify the preference matcher of the VirtualMachine.
    - Only used when I(state=present).
    type: dict
  data_volume_templates:
    description:
    - Specify the DataVolume templates of the VirtualMachine.
    - 'See: https://kubevirt.io/api-reference/main/definitions.html#_v1_datavolumetemplatespec'
    type: list
    elements: 'dict'
  spec:
    description:
    - Specify the template spec of the VirtualMachine.
    - 'See: https://kubevirt.io/api-reference/main/definitions.html#_v1_virtualmachineinstancespec'
    type: dict
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

requirements:
- "python >= 3.9"
- "kubernetes >= 28.1.0"
- "PyYAML >= 3.11"
- "jsonpatch"
- "jinja2"
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
      description: Whether the VirtualMachine was changed
      type: bool
      sample: True
    duration:
      description: elapsed time of task in seconds
      returned: when C(wait) is true
      type: int
      sample: 48
    method:
      description: Method executed on the Kubernetes API.
      returned: success
      type: str
"""

from copy import deepcopy
from typing import Dict
import traceback

from ansible_collections.kubernetes.core.plugins.module_utils.ansiblemodule import (
    AnsibleModule,
)
from ansible_collections.kubernetes.core.plugins.module_utils.args_common import (
    AUTH_ARG_SPEC,
    COMMON_ARG_SPEC,
    DELETE_OPTS_ARG_SPEC,
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

try:
    import yaml
except ImportError:
    HAS_YAML = False
    YAML_IMPORT_ERROR = traceback.format_exc()
else:
    HAS_YAML = True
    YAML_IMPORT_ERROR = None

try:
    from jinja2 import Environment
except ImportError:
    HAS_JINJA = False
    JINJA_IMPORT_ERROR = traceback.format_exc()
else:
    HAS_JINJA = True
    JINJA_IMPORT_ERROR = None


VM_TEMPLATE = """
apiVersion: {{ api_version }}
kind: VirtualMachine
metadata:
  {% if name %}
  name: "{{ name }}"
  {% endif %}
  {% if generate_name %}
  generateName: "{{ generate_name }}"
  {% endif %}
  namespace: "{{ namespace }}"
  {% if annotations %}
  annotations:
    {{ annotations | to_yaml | indent(4) }}
  {%- endif %}
  {% if labels %}
  labels:
    {{ labels | to_yaml | indent(4) }}
  {%- endif %}
spec:
  running: {{ running }}
  {% if instancetype %}
  instancetype:
    {{ instancetype | to_yaml | indent(4) }}
  {%- endif %}
  {% if preference %}
  preference:
    {{ preference | to_yaml | indent(4) }}
  {%- endif %}
  {% if data_volume_templates %}
  dataVolumeTemplates:
    {{ data_volume_templates | to_yaml | indent(4) }}
  {%- endif %}
  template:
    {% if annotations or labels %}
    metadata:
      {% if annotations %}
      annotations:
        {{ annotations | to_yaml | indent(8) }}
      {%- endif %}
      {% if labels %}
      labels:
        {{ labels | to_yaml | indent(8) }}
      {%- endif %}
    {% endif %}
    spec:
    {% if spec %}
      {{ spec | to_yaml | indent (6) }}
    {%- else %}
      domain:
        devices: {}
    {% endif %}
"""


def render_template(params: Dict) -> str:
    """
    render_template uses Jinja2 to render the VM_TEMPLATE into a string.
    """
    env = Environment(autoescape=False, trim_blocks=True, lstrip_blocks=True)
    env.filters["to_yaml"] = lambda data, *_, **kw: yaml.dump(
        data, allow_unicode=True, default_flow_style=False, **kw
    )

    template = env.from_string(VM_TEMPLATE.strip())
    return template.render(params)


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
    }
    spec.update(deepcopy(AUTH_ARG_SPEC))
    spec.update(deepcopy(COMMON_ARG_SPEC))
    spec["delete_options"] = {
        "type": "dict",
        "default": None,
        "options": deepcopy(DELETE_OPTS_ARG_SPEC),
    }

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

    # Set resource_definition to our rendered template
    module.params["resource_definition"] = render_template(module.params)

    # Set wait_condition to allow waiting for the ready state of the VirtualMachine
    module.params["wait_condition"] = {"type": "Ready", "status": True}

    try:
        runner.run_module(module)
    except CoreException as exc:
        module.fail_from_exception(exc)


if __name__ == "__main__":
    main()
