# -*- coding: utf-8 -*-
# Copyright 2024 Red Hat, Inc.
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest

from ansible_collections.kubevirt.core.plugins.inventory.kubevirt import InventoryModule


@pytest.fixture
def inventory():
    return InventoryModule()


@pytest.mark.parametrize(
    "file_name,expected",
    [
        ("inventory.kubevirt.yml", True),
        ("inventory.kubevirt.yaml", True),
        ("something.kubevirt.yml", True),
        ("something.kubevirt.yaml", True),
        ("inventory.somethingelse.yml", False),
        ("inventory.somethingelse.yaml", False),
        ("something.somethingelse.yml", False),
        ("something.somethingelse.yaml", False),
    ],
)
def test_verify_file(tmp_path, inventory, file_name, expected):
    file = tmp_path / file_name
    file.touch()
    assert inventory.verify_file(str(file)) is expected


@pytest.mark.parametrize(
    "file_name",
    [
        "inventory.kubevirt.yml",
        "inventory.kubevirt.yaml",
        "something.kubevirt.yml",
        "something.kubevirt.yaml",
        "inventory.somethingelse.yml",
        "inventory.somethingelse.yaml",
        "something.somethingelse.yml",
        "something.somethingelse.yaml",
    ],
)
def test_verify_file_bad_config(inventory, file_name):
    assert inventory.verify_file(file_name) is False
