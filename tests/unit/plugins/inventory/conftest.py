# -*- coding: utf-8 -*-
# Copyright 2024 Red Hat, Inc.
# Apache License 2.0 (see LICENSE or http://www.apache.org/licenses/LICENSE-2.0)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest

from kubernetes.dynamic.exceptions import ResourceNotFoundError
from kubernetes.dynamic.resource import ResourceField

from ansible.template import Templar

from ansible_collections.kubevirt.core.plugins.inventory.kubevirt import (
    InventoryModule,
)

from ansible_collections.kubevirt.core.tests.unit.plugins.inventory.constants import (
    DEFAULT_BASE_DOMAIN,
    DEFAULT_NAMESPACE,
)


@pytest.fixture(scope="function")
def inventory(mocker):
    inventory = InventoryModule()
    inventory.inventory = mocker.Mock()
    inventory.templar = Templar(loader=None)
    inventory._options = {
        "compose": {},
        "groups": {},
        "keyed_groups": [],
        "strict": True,
    }
    return inventory


@pytest.fixture(scope="function")
def inventory_data(mocker, inventory):
    groups = {}
    hosts = {}

    def add_group(group):
        if group not in groups:
            groups[group] = {"children": [], "vars": {}}
        return group

    def add_child(group, name):
        if name not in groups[group]["children"]:
            groups[group]["children"].append(name)

    def add_host(host, group=None):
        if host not in hosts:
            hosts[host] = {}
        if group is not None:
            add_child(group, host)

    def get_host(hostname):
        host = mocker.Mock()
        host.get_vars = mocker.Mock(return_value=hosts[hostname])
        return host

    def set_variable(name, key, value):
        if name in groups:
            groups[name]["vars"][key] = value
        else:
            hosts[name][key] = value

    mocker.patch.object(inventory.inventory, "add_group", add_group)
    mocker.patch.object(inventory.inventory, "add_child", add_child)
    mocker.patch.object(inventory.inventory, "add_host", add_host)
    mocker.patch.object(inventory.inventory, "get_host", get_host)
    mocker.patch.object(inventory.inventory, "set_variable", set_variable)
    return groups, hosts


@pytest.fixture(scope="function")
def groups(inventory_data):
    return inventory_data[0]


@pytest.fixture(scope="function")
def hosts(inventory_data):
    return inventory_data[1]


@pytest.fixture(scope="function")
def client(mocker, request):
    param = {}
    if hasattr(request, "param"):
        param = request.param

    namespaces = mocker.Mock()
    if "namespaces" in param:
        items = param["namespaces"]
    else:
        items = [{"metadata": {"name": DEFAULT_NAMESPACE}}]
    namespaces.items = [ResourceField(item) for item in items]

    vms = mocker.Mock()
    vms.items = [ResourceField(item) for item in param.get("vms", [])]
    vmis = mocker.Mock()
    vmis.items = [ResourceField(item) for item in param.get("vmis", [])]
    services = mocker.Mock()
    services.items = [ResourceField(item) for item in param.get("services", [])]

    dns = mocker.Mock()
    if "base_domain" in param:
        base_domain = param["base_domain"]
    else:
        base_domain = DEFAULT_BASE_DOMAIN
    dns_obj = ResourceField({"spec": {"baseDomain": base_domain}})
    dns.items = [dns_obj]

    projects = mocker.Mock()
    projects.items = [ResourceField(item) for item in param.get("projects", [])]

    namespace_client = mocker.Mock()
    namespace_client.get = mocker.Mock(return_value=namespaces)
    vm_client = mocker.Mock()
    vm_client.get = mocker.Mock(return_value=vms)
    vmi_client = mocker.Mock()
    vmi_client.get = mocker.Mock(return_value=vmis)
    service_client = mocker.Mock()
    service_client.get = mocker.Mock(return_value=services)

    def dns_client_get(**kwargs):
        if "name" in kwargs:
            return dns_obj
        return dns

    dns_client = mocker.Mock()
    dns_client.get = dns_client_get

    def project_client_get():
        if not projects.items:
            raise ResourceNotFoundError
        return projects

    project_client = mocker.Mock()
    project_client.get = project_client_get

    def resources_get(api_version="", kind=""):
        if api_version.lower() == "v1":
            if kind.lower() == "namespace":
                return namespace_client
            if kind.lower() == "service":
                return service_client
        elif api_version.lower() == "config.openshift.io/v1" and kind.lower() == "dns":
            return dns_client
        elif (
            api_version.lower() == "project.openshift.io/v1"
            and kind.lower() == "project"
        ):
            return project_client
        elif "kubevirt.io/" in api_version.lower():
            if kind.lower() == "virtualmachine":
                return vm_client
            if kind.lower() == "virtualmachineinstance":
                return vmi_client

        return None

    client = mocker.Mock()
    client.resources.get = resources_get
    return client
