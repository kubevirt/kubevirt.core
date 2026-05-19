#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2023 Red Hat, Inc.
# Based on the kubernetes.core.k8s module
# Apache License 2.0 (see LICENSE or http://www.apache.org/licenses/LICENSE-2.0)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = """
module: kubevirt_vm

short_description: Manage KubeVirt VirtualMachines

author:
- "KubeVirt.io Project (!UNKNOWN)"

description:
- Use the Kubernetes Python client to perform create, delete, start, stop, or restart operations on KubeVirt VirtualMachines.
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
    - Mutually exclusive with O(run_strategy).
    - Defaults to O(running=yes) when O(running) and O(run_strategy) are not set.
    type: bool
  run_strategy:
    description:
    - Specify the C(RunStrategy) of the C(VirtualMachine).
    - Mutually exclusive with O(running).
    type: str
    choices:
    - Always
    - Halted
    - Manual
    - RerunOnFailure
    - Once
    version_added: 2.0.0
  grace_period_seconds:
    description:
    - Specify the grace period in seconds for stopping or restarting the C(VirtualMachine).
    - Only used when O(state=stopped) or O(state=restarted).
    - When used with O(state=restarted), the only supported values are V(null) (use the default grace period) and V(0) (force restart immediately).
    type: int
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
    - Determines if an object should be created, patched, deleted, started, stopped, or restarted.
    - When set to O(state=present), an object will be created, if it does not already exist.
    - If set to O(state=absent), an existing object will be deleted.
    - If set to O(state=present), an existing object will be patched, if its attributes differ from those specified.
    - If set to O(state=started), a stopped C(VirtualMachine) will be started.
    - If set to O(state=stopped), a running C(VirtualMachine) will be stopped.
    - If set to O(state=restarted), a running C(VirtualMachine) will be restarted.
    type: str
    default: present
    choices:
    - absent
    - present
    - restarted
    - started
    - stopped
  force:
    description:
    - If set to O(force=yes), and O(state=present) is set, an existing object will be replaced.
    type: bool
    default: no
  hidden_fields:
    description:
    - Hide fields matching this option in the result.
    - An example might be O(hidden_fields=[metadata.managedFields])
      or O(hidden_fields=[metadata.annotations[kubemacpool.io/transaction-timestamp]]).
    type: list
    elements: str
    default: ['metadata.annotations[kubemacpool.io/transaction-timestamp]', metadata.managedFields]
    version_added: 2.2.0

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

- name: Start a VirtualMachine
  kubevirt.core.kubevirt_vm:
    name: testvm
    namespace: default
    state: started
    wait: true

- name: Stop a VirtualMachine
  kubevirt.core.kubevirt_vm:
    name: testvm
    namespace: default
    state: stopped
    wait: true

- name: Restart a VirtualMachine
  kubevirt.core.kubevirt_vm:
    name: testvm
    namespace: default
    state: restarted
    wait: true

- name: Force restart a VirtualMachine
  kubevirt.core.kubevirt_vm:
    name: testvm
    namespace: default
    state: restarted
    grace_period_seconds: 0
    wait: true
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

# Monkey patch service.diff_objects to temporarily fix the changed logic
from ansible_collections.kubevirt.core.plugins.module_utils.diff import (
    _patch_diff_objects,
)

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
from ansible_collections.kubernetes.core.plugins.module_utils.k8s.client import (
    get_api_client,
    K8SClient,
)
from ansible_collections.kubernetes.core.plugins.module_utils.k8s.core import (
    AnsibleK8SModule,
)
from ansible_collections.kubernetes.core.plugins.module_utils.k8s.exceptions import (
    CoreException,
)
from ansible_collections.kubernetes.core.plugins.module_utils.k8s.service import (
    K8sService,
)

WAIT_CONDITION_READY = {"type": "Ready", "status": True}
WAIT_CONDITION_VMI_NOT_EXISTS = {
    "type": "Ready",
    "status": False,
    "reason": "VMINotExists",
}
SUBRESOURCE_API = "subresources.kubevirt.io/v1"
VM_IS_ALREADY_IN_DESIRED_STATE_ERROR_CODE = 409


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

    if (run_strategy := params.get("run_strategy")) is not None:
        vm["spec"]["runStrategy"] = run_strategy
        vm["spec"]["running"] = None
    else:
        vm["spec"]["runStrategy"] = None
        vm["spec"]["running"] = (
            running if (running := params.get("running")) is not None else True
        )
    if (instancetype := params.get("instancetype")) is not None:
        vm["spec"]["instancetype"] = instancetype
    if (preference := params.get("preference")) is not None:
        vm["spec"]["preference"] = preference
    if (data_volume_templates := params.get("data_volume_templates")) is not None:
        vm["spec"]["dataVolumeTemplates"] = data_volume_templates
    if (spec := params.get("spec")) is not None:
        vm["spec"]["template"]["spec"] = spec

    return vm


def set_wait_condition(module: AnsibleK8SModule) -> None:
    """
    set_wait_condition sets the wait_condition to allow waiting for the ready
    state of the VirtualMachine depending on the module parameters running
    and run_strategy.
    """
    if (
        module.params["running"] is False
        or (run_strategy := module.params["run_strategy"]) == "Halted"
    ):
        module.params["wait_condition"] = WAIT_CONDITION_VMI_NOT_EXISTS
    elif run_strategy != "Manual":
        module.params["wait_condition"] = WAIT_CONDITION_READY


def _vm_is_ready(client: K8SClient, module: AnsibleK8SModule) -> bool:
    svc = K8sService(client, module)
    result = svc.find(
        kind="VirtualMachine",
        api_version=module.params["api_version"],
        name=module.params["name"],
        namespace=module.params["namespace"],
    )
    resources = result.get("resources", [])
    if not resources:
        return False
    return resources[0].get("status", {}).get("ready", False)


def _apply_definition(module: AnsibleK8SModule) -> Dict:
    definition = create_vm(module.params)

    original_state = module.params["state"]
    original_wait = module.params.get("wait")
    if original_state not in ("present", "absent"):
        module.params["state"] = "present"
        # Don't wait during the CRUD step for subresource states;
        # the subresource action handles the final wait.
        module.params["wait"] = False
        # Don't override running/runStrategy unless the user explicitly set
        # them, so the CRUD step won't unintentionally change the VM's
        # lifecycle state before the subresource action runs.
        if (
            module.params.get("running") is None
            and module.params.get("run_strategy") is None
        ):
            definition["spec"].pop("running", None)
            definition["spec"].pop("runStrategy", None)

    module.params["resource_definition"] = definition

    set_wait_condition(module)

    captured = {}
    original_exit_json = module.exit_json
    module.exit_json = lambda **kwargs: captured.update(kwargs)
    try:
        runner.run_module(module)
    except CoreException as exc:
        module.exit_json = original_exit_json
        module.fail_from_exception(exc)
    finally:
        module.exit_json = original_exit_json
        module.params["state"] = original_state
        module.params["wait"] = original_wait

    return captured


def _call_subresource(
    client: K8SClient,
    module: AnsibleK8SModule,
    action: str,
    body: Dict,
    wait_condition: Dict,
    ignore_conflict: bool = False,
) -> Dict:
    name = module.params["name"]
    namespace = module.params["namespace"]

    path = (
        f"/apis/{SUBRESOURCE_API}"
        f"/namespaces/{namespace}"
        f"/virtualmachines/{name}/{action}"
    )

    try:
        client.client.request("put", path, body=body, header_params={"Accept": "*/*"})
    except Exception as exc:
        # 409 Conflict means the VM is already in the desired state or
        # its RunStrategy does not support manual start requests.
        if (
            ignore_conflict
            and hasattr(exc, "status")
            and exc.status == VM_IS_ALREADY_IN_DESIRED_STATE_ERROR_CODE
        ):
            return {"changed": False}
        module.fail_json(
            msg=f"Failed to {action} VirtualMachine '{name}': {exc}",
        )

    result = {"changed": True}

    if module.params.get("wait"):
        try:
            svc = K8sService(client, module)
            wait_result = svc.find(
                kind="VirtualMachine",
                api_version=module.params["api_version"],
                name=name,
                namespace=namespace,
                wait=True,
                wait_sleep=module.params["wait_sleep"],
                wait_timeout=module.params["wait_timeout"],
                condition=wait_condition,
            )
            result.update(wait_result)
        except CoreException as exc:
            module.fail_from_exception(exc)

    return result


def start_vm(client: K8SClient, module: AnsibleK8SModule) -> Dict:
    if _vm_is_ready(client, module):
        return {"changed": False}
    if module.check_mode:
        return {"changed": True}

    return _call_subresource(
        client, module, "start", None, WAIT_CONDITION_READY, ignore_conflict=True
    )


def stop_vm(client: K8SClient, module: AnsibleK8SModule) -> Dict:
    if not _vm_is_ready(client, module):
        return {"changed": False}
    if module.check_mode:
        return {"changed": True}

    grace_period_seconds = module.params.get("grace_period_seconds")
    body = None
    if grace_period_seconds is not None:
        body = {"gracePeriod": grace_period_seconds}
    return _call_subresource(
        client,
        module,
        "stop",
        body,
        WAIT_CONDITION_VMI_NOT_EXISTS,
        ignore_conflict=True,
    )


def restart_vm(client: K8SClient, module: AnsibleK8SModule) -> Dict:
    if module.check_mode:
        return {"changed": True}

    grace_period_seconds = module.params.get("grace_period_seconds")
    body = None
    if grace_period_seconds is not None:
        body = {"gracePeriodSeconds": grace_period_seconds}
    return _call_subresource(client, module, "restart", body, WAIT_CONDITION_READY)


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
        "running": {"type": "bool"},
        "run_strategy": {
            "choices": ["Always", "Halted", "Manual", "RerunOnFailure", "Once"]
        },
        "grace_period_seconds": {"type": "int"},
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
        "hidden_fields": {
            "type": "list",
            "elements": "str",
            "default": [
                "metadata.annotations[kubemacpool.io/transaction-timestamp]",
                "metadata.managedFields",
            ],
        },
    }
    spec.update(deepcopy(AUTH_ARG_SPEC))
    spec.update(deepcopy(COMMON_ARG_SPEC))

    # Override state choices from COMMON_ARG_SPEC which only defines
    # ["present", "absent"], adding our subresource action states.
    spec["state"] = {
        "default": "present",
        "choices": ["absent", "present", "restarted", "started", "stopped"],
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
            ("running", "run_strategy"),
        ],
        required_one_of=[
            ("name", "generate_name"),
        ],
        required_if=[
            ("state", "started", ("name",)),
            ("state", "stopped", ("name",)),
            ("state", "restarted", ("name",)),
        ],
        supports_check_mode=True,
    )

    result = _apply_definition(module)

    subresource_actions = {
        "started": start_vm,
        "stopped": stop_vm,
        "restarted": restart_vm,
    }
    if (action := subresource_actions.get(module.params["state"])) is not None:
        client = get_api_client(module)
        action_result = action(client, module)
        result["changed"] = result["changed"] or action_result.get("changed", False)

    module.exit_json(**result)


if __name__ == "__main__":
    _patch_diff_objects()
    main()
