# -*- coding: utf-8 -*-
# Copyright 2024 Red Hat, Inc.
# Apache License 2.0 (see LICENSE or http://www.apache.org/licenses/LICENSE-2.0)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest

from ansible_collections.kubevirt.core.tests.unit.plugins.inventory.constants import (
    DEFAULT_NAMESPACE,
)

SVC_LB_SSH = {
    "apiVersion": "v1",
    "kind": "Service",
    "metadata": {"name": "test-lb-ssh"},
    "spec": {
        "ports": [
            {
                "protocol": "TCP",
                "port": 22,
                "targetPort": 22,
            },
        ],
        "type": "LoadBalancer",
        "selector": {"kubevirt.io/domain": "test-lb-ssh"},
    },
}

SVC_NP_SSH = {
    "apiVersion": "v1",
    "kind": "Service",
    "metadata": {"name": "test-np-ssh"},
    "spec": {
        "ports": [
            {
                "protocol": "TCP",
                "port": 22,
                "targetPort": 22,
            },
        ],
        "type": "NodePort",
        "selector": {"kubevirt.io/domain": "test-np-ssh"},
    },
}

SVC_LB_WINRM_HTTP = {
    "apiVersion": "v1",
    "kind": "Service",
    "metadata": {"name": "test-lb-winrm-http"},
    "spec": {
        "ports": [
            {
                "protocol": "TCP",
                "port": 5985,
                "targetPort": 5985,
            },
        ],
        "type": "LoadBalancer",
        "selector": {"kubevirt.io/domain": "test-lb-winrm-http"},
    },
}

SVC_NP_WINRM_HTTP = {
    "apiVersion": "v1",
    "kind": "Service",
    "metadata": {"name": "test-np-winrm-http"},
    "spec": {
        "ports": [
            {
                "protocol": "TCP",
                "port": 5985,
                "targetPort": 5985,
            },
        ],
        "type": "NodePort",
        "selector": {"kubevirt.io/domain": "test-np-winrm-http"},
    },
}

SVC_LB_WINRM_HTTPS = {
    "apiVersion": "v1",
    "kind": "Service",
    "metadata": {"name": "test-lb-winrm-https"},
    "spec": {
        "ports": [
            {
                "protocol": "TCP",
                "port": 5986,
                "targetPort": 5986,
            },
        ],
        "type": "LoadBalancer",
        "selector": {"kubevirt.io/domain": "test-lb-winrm-https"},
    },
}

SVC_NP_WINRM_HTTPS = {
    "apiVersion": "v1",
    "kind": "Service",
    "metadata": {"name": "test-np-winrm-https"},
    "spec": {
        "ports": [
            {
                "protocol": "TCP",
                "port": 5986,
                "targetPort": 5986,
            },
        ],
        "type": "NodePort",
        "selector": {"kubevirt.io/domain": "test-np-winrm-https"},
    },
}


@pytest.mark.parametrize(
    "client",
    [
        {
            "services": [
                SVC_LB_SSH,
                SVC_NP_SSH,
                SVC_LB_WINRM_HTTP,
                SVC_NP_WINRM_HTTP,
                SVC_LB_WINRM_HTTPS,
                SVC_NP_WINRM_HTTPS,
            ],
        },
    ],
    indirect=["client"],
)
def test_get_services_for_namespace(inventory, client):
    assert inventory._get_services_for_namespace(client, DEFAULT_NAMESPACE) == {
        "test-lb-ssh": [SVC_LB_SSH],
        "test-np-ssh": [SVC_NP_SSH],
        "test-lb-winrm-http": [SVC_LB_WINRM_HTTP],
        "test-np-winrm-http": [SVC_NP_WINRM_HTTP],
        "test-lb-winrm-https": [SVC_LB_WINRM_HTTPS],
        "test-np-winrm-https": [SVC_NP_WINRM_HTTPS],
    }


SVC_CLUSTERIP = {
    "apiVersion": "v1",
    "kind": "Service",
    "metadata": {"name": "test-clusterip"},
    "spec": {
        "ports": [
            {
                "protocol": "TCP",
                "port": 22,
                "targetPort": 22,
            },
        ],
        "type": "ClusterIP",
        "selector": {"kubevirt.io/domain": "test-clusterip"},
    },
}


SVC_HTTP = {
    "apiVersion": "v1",
    "kind": "Service",
    "metadata": {"name": "test-http"},
    "spec": {
        "ports": [
            {
                "protocol": "TCP",
                "port": 80,
                "targetPort": 80,
            },
        ],
        "type": "LoadBalancer",
        "selector": {"kubevirt.io/domain": "test-http"},
    },
}


SVC_NO_SPEC = {
    "apiVersion": "v1",
    "kind": "Service",
    "metadata": {"name": "test-no-spec"},
}

SVC_NO_TYPE = {
    "apiVersion": "v1",
    "kind": "Service",
    "metadata": {"name": "test-no-type"},
    "spec": {
        "ports": [
            {
                "protocol": "TCP",
                "port": 22,
                "targetPort": 22,
            },
        ],
        "selector": {"kubevirt.io/domain": "test-no-type"},
    },
}

SVC_NO_PORTS = {
    "apiVersion": "v1",
    "kind": "Service",
    "metadata": {"name": "test-no-ports"},
    "spec": {
        "type": "LoadBalancer",
        "selector": {"kubevirt.io/domain": "test-no-ports"},
    },
}

SVC_NO_SELECTOR = {
    "apiVersion": "v1",
    "kind": "Service",
    "metadata": {"name": "test-no-selector"},
    "spec": {
        "ports": [
            {
                "protocol": "TCP",
                "port": 22,
                "targetPort": 22,
            },
        ],
        "type": "LoadBalancer",
    },
}


@pytest.mark.parametrize(
    "client",
    [
        {
            "services": [
                SVC_HTTP,
                SVC_CLUSTERIP,
                SVC_NO_SPEC,
                SVC_NO_TYPE,
                SVC_NO_PORTS,
                SVC_NO_SELECTOR,
            ],
        },
    ],
    indirect=["client"],
)
def test_ignore_unwanted_services(inventory, client):
    assert not inventory._get_services_for_namespace(client, DEFAULT_NAMESPACE)
