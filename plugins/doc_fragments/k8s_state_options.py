# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Red Hat | Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Options for specifying object state

# DO NOT CHANGE THIS FILE
# Direct copy of:
# https://github.com/ansible-collections/kubernetes.core/blob/23e94b60c1202e67d35903d8f6d298fbb15f35cc/plugins/doc_fragments/k8s_state_options.py
# Because it is not possible to refer to doc_fragments of dependency collections we need this copy.

from __future__ import absolute_import, division, print_function

__metaclass__ = type


class ModuleDocFragment(object):
    DOCUMENTATION = r"""
options:
  state:
    description:
    - Determines if an object should be created, patched, or deleted. When set to C(present), an object will be
      created, if it does not already exist. If set to C(absent), an existing object will be deleted. If set to
      C(present), an existing object will be patched, if its attributes differ from those specified using
      I(resource_definition) or I(src).
    type: str
    default: present
    choices: [ absent, present ]
  force:
    description:
    - If set to C(yes), and I(state) is C(present), an existing object will be replaced.
    type: bool
    default: no
"""
