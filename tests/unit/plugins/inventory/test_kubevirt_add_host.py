# -*- coding: utf-8 -*-
# Copyright 2024 Red Hat, Inc.
# Apache License 2.0 (see LICENSE or http://www.apache.org/licenses/LICENSE-2.0)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest

from ansible_collections.kubevirt.core.tests.unit.plugins.inventory.constants import (
    DEFAULT_NAMESPACE,
)


@pytest.mark.parametrize(
    "host_format,expected",
    [
        ("static", "static"),
        ("{name}", "testvm"),
        ("{name}-static", "testvm-static"),
        ("{namespace}", "default"),
        ("{uid}", "f8abae7c-d792-4b9b-af95-62d322ae5bc1"),
        ("{name}-{namespace}", "testvm-default"),
        ("{name}-{namespace}-static", "testvm-default-static"),
        ("{name}-{uid}", "testvm-f8abae7c-d792-4b9b-af95-62d322ae5bc1"),
        ("{namespace}-{name}", "default-testvm"),
        ("{namespace}-{uid}", "default-f8abae7c-d792-4b9b-af95-62d322ae5bc1"),
        ("{uid}-{name}", "f8abae7c-d792-4b9b-af95-62d322ae5bc1-testvm"),
        ("{uid}-{namespace}", "f8abae7c-d792-4b9b-af95-62d322ae5bc1-default"),
        (
            "{name}-{namespace}-{uid}",
            "testvm-default-f8abae7c-d792-4b9b-af95-62d322ae5bc1",
        ),
        (
            "{name}-{namespace}-{uid}-static",
            "testvm-default-f8abae7c-d792-4b9b-af95-62d322ae5bc1-static",
        ),
        (
            "{name}-{uid}-{namespace}",
            "testvm-f8abae7c-d792-4b9b-af95-62d322ae5bc1-default",
        ),
        (
            "{namespace}-{name}-{uid}",
            "default-testvm-f8abae7c-d792-4b9b-af95-62d322ae5bc1",
        ),
        (
            "{namespace}-{uid}-{name}",
            "default-f8abae7c-d792-4b9b-af95-62d322ae5bc1-testvm",
        ),
        (
            "{uid}-{namespace}-{name}",
            "f8abae7c-d792-4b9b-af95-62d322ae5bc1-default-testvm",
        ),
        (
            "{uid}-{name}-{namespace}",
            "f8abae7c-d792-4b9b-af95-62d322ae5bc1-testvm-default",
        ),
    ],
)
def test_add_host(inventory, groups, hosts, host_format, expected):
    namespace_group = "namespace_default"
    inventory.inventory.add_group(namespace_group)

    inventory._add_host(
        {
            "name": "testvm",
            "namespace": DEFAULT_NAMESPACE,
            "uid": "f8abae7c-d792-4b9b-af95-62d322ae5bc1",
        },
        host_format,
        namespace_group,
    )

    assert expected in hosts
    assert expected in groups[namespace_group]["children"]
