# -*- coding: utf-8 -*-
# Copyright 2024 Red Hat, Inc.
# Apache License 2.0 (see LICENSE or http://www.apache.org/licenses/LICENSE-2.0)

# This file allows to run modules in unit tests.
# It was taken from:
# https://docs.ansible.com/ansible/latest/dev_guide/testing_units_modules.html#module-argument-processing

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from contextlib import contextmanager
from json import dumps
from typing import (
    Any,
    Dict,
)
from unittest import mock

from ansible.module_utils import basic
from ansible.module_utils.common.text.converters import to_bytes


@contextmanager
def patch_module_args(args: Dict[str, Any] | None = None):
    """prepare arguments so that they will be picked up during module creation"""
    args = dumps({"ANSIBLE_MODULE_ARGS": args})
    with mock.patch.object(basic, "_ANSIBLE_ARGS", to_bytes(args)):
        yield


class AnsibleExitJson(Exception):
    """Exception class to be raised by module.exit_json and caught by the test case"""

    pass


class AnsibleFailJson(Exception):
    """Exception class to be raised by module.fail_json and caught by the test case"""

    pass


def exit_json(*args, **kwargs):
    """function to patch over exit_json; package return data into an exception"""
    if "changed" not in kwargs:
        kwargs["changed"] = False
    raise AnsibleExitJson(kwargs)


def fail_json(*args, **kwargs):
    """function to patch over fail_json; package return data into an exception"""
    kwargs["failed"] = True
    raise AnsibleFailJson(kwargs)
