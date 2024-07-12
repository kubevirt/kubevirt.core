# -*- coding: utf-8 -*-
# Copyright 2024 Red Hat, Inc.
# Apache License 2.0 (see LICENSE or http://www.apache.org/licenses/LICENSE-2.0)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from json import dumps

import pytest

from kubernetes.dynamic.exceptions import DynamicApiError

from ansible_collections.kubevirt.core.plugins.inventory.kubevirt import (
    InventoryModule,
)


@pytest.fixture(scope="function")
def body_error(mocker):
    error = DynamicApiError(e=mocker.Mock())
    error.headers = None
    error.body = "This is a test error"
    return error


@pytest.fixture(scope="function")
def message_error(mocker):
    error = DynamicApiError(e=mocker.Mock())
    error.headers = {"Content-Type": "application/json"}
    error.body = dumps({"message": "This is a test error"}).encode("utf-8")
    return error


@pytest.fixture(scope="function")
def status_reason_error(mocker):
    error = DynamicApiError(e=mocker.Mock())
    error.body = None
    error.status = 404
    error.reason = "This is a test error"
    return error


@pytest.mark.parametrize(
    "exc,expected",
    [
        ("body_error", "This is a test error"),
        ("message_error", "This is a test error"),
        ("status_reason_error", "404 Reason: This is a test error"),
    ],
)
def test_format_dynamic_api_exc(request, exc, expected):
    assert (
        InventoryModule._format_dynamic_api_exc(request.getfixturevalue(exc))
        == expected
    )
