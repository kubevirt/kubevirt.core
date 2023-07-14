#!/usr/bin/env python
from __future__ import absolute_import, division, print_function

__metaclass__ = type

import json
import os
from http import HTTPStatus
from http.server import HTTPServer
from http.server import SimpleHTTPRequestHandler
from threading import Thread
from urllib.parse import urlparse


class TestHandler(SimpleHTTPRequestHandler):
    # Path handlers:
    handlers = {}

    def log_message(self, format, *args):
        """
        Empty method, so we don't mix output of HTTP server with tests
        """

    def do_GET(self):
        params = urlparse(self.path)

        if params.path in self.handlers:
            self.handlers[params.path](self)
        else:
            SimpleHTTPRequestHandler.do_GET(self)

    def do_POST(self):
        params = urlparse(self.path)

        if params.path in self.handlers:
            self.handlers[params.path](self)
        else:
            self.send_error(HTTPStatus.NOT_FOUND)


class TestServer:
    # The host and port and path used by the embedded tests web server:
    PORT = None

    # The embedded web server:
    _httpd = None
    # Thread for http server:
    _thread = None

    def set_json_response(self, path, code, body):
        def _handle_request(handler):
            handler.send_response(code)
            handler.send_header("Content-Type", "application/json")
            handler.end_headers()

            data = json.dumps(body, ensure_ascii=False).encode("utf-8")
            handler.wfile.write(data)

        TestHandler.handlers[path] = _handle_request

    def start_server(self, host="localhost"):
        self._httpd = HTTPServer((host, 12345), TestHandler)
        self._thread = Thread(target=self._httpd.serve_forever)
        self._thread.start()

    def stop_server(self):
        self._httpd.shutdown()
        self._thread.join()


if __name__ == "__main__":
    print(os.getpid())
    server = TestServer()
    server.start_server()
    server.set_json_response(path="/version", code=200, body={})
    server.set_json_response(
        path="/api",
        code=200,
        body={
            "kind": "APIVersions",
            "versions": ["v1"],
            "serverAddressByClientCIDRs": [
                {"clientCIDR": "0.0.0.0/0", "serverAddress": "localhost:12345"}
            ],
        },
    )
    server.set_json_response(
        path="/api/v1",
        code=200,
        body={
            "kind": "APIResourceList",
            "groupVersion": "v1",
            "resources": [
                {
                    "name": "services",
                    "singularName": "service",
                    "namespaced": True,
                    "kind": "Service",
                    "verbs": [
                        "create",
                        "delete",
                        "deletecollection",
                        "get",
                        "list",
                        "patch",
                        "update",
                        "watch",
                    ],
                    "shortNames": ["svc"],
                }
            ],
        },
    )
    server.set_json_response(
        path="/api/v1/namespaces/default/services",
        code=200,
        body={
            "kind": "ServiceList",
            "groupVersion": "v1",
            "items": [],
        },
    )
    server.set_json_response(
        path="/apis",
        code=200,
        body={
            "kind": "APIGroupList",
            "apiVersion": "v1",
            "groups": [
                {
                    "name": "kubevirt.io",
                    "versions": [{"groupVersion": "kubevirt.io/v1", "version": "v1"}],
                    "preferredVersion": {
                        "groupVersion": "kubevirt.io/v1",
                        "version": "v1",
                    },
                }
            ],
        },
    )
    server.set_json_response(
        path="/apis/kubevirt.io/v1",
        code=200,
        body={
            "kind": "APIResourceList",
            "apiVersion": "v1",
            "groupVersion": "kubevirt.io/v1",
            "resources": [
                {
                    "name": "virtualmachineinstances",
                    "singularName": "virtualmachineinstance",
                    "namespaced": True,
                    "kind": "VirtualMachineInstance",
                    "verbs": [
                        "delete",
                        "deletecollection",
                        "get",
                        "list",
                        "patch",
                        "create",
                        "update",
                        "watch",
                    ],
                    "shortNames": ["vmi", "vmis"],
                }
            ],
        },
    )
    server.set_json_response(
        path="/apis/kubevirt.io/v1/namespaces/default/virtualmachineinstances",
        code=200,
        body={
            "apiVersion": "v1",
            "items": [
                {
                    "apiVersion": "kubevirt.io/v1",
                    "kind": "VirtualMachineInstance",
                    "metadata": {
                        "annotations": {
                            "kubevirt.io/latest-observed-api-version": "v1",
                            "kubevirt.io/storage-observed-api-version": "v1alpha3",
                        },
                        "creationTimestamp": "2022-09-14T13:43:36Z",
                        "finalizers": [
                            "kubevirt.io/virtualMachineControllerFinalize",
                            "foregroundDeleteVirtualMachine",
                        ],
                        "generation": 9,
                        "labels": {
                            "kubevirt.io/nodeName": "node01",
                            "kubevirt.io/vm": "vm-cirros",
                        },
                        "name": "vm-cirros",
                        "namespace": "default",
                        "ownerReferences": [
                            {
                                "apiVersion": "kubevirt.io/v1",
                                "blockOwnerDeletion": True,
                                "controller": True,
                                "kind": "VirtualMachine",
                                "name": "vm-cirros",
                                "uid": "4d1b1438-91ba-4c75-a211-566fc50a06f5",
                            }
                        ],
                        "resourceVersion": "5387",
                        "uid": "7b3a8d94-bd7e-4c14-818a-89228172e4f1",
                    },
                    "spec": {
                        "domain": {
                            "cpu": {
                                "cores": 1,
                                "model": "host-model",
                                "sockets": 1,
                                "threads": 1,
                            },
                            "devices": {
                                "disks": [
                                    {
                                        "disk": {"bus": "virtio"},
                                        "name": "containerdisk",
                                    },
                                    {
                                        "disk": {"bus": "virtio"},
                                        "name": "cloudinitdisk",
                                    },
                                ],
                                "interfaces": [{"bridge": {}, "name": "default"}],
                            },
                            "features": {"acpi": {"enabled": True}},
                            "firmware": {
                                "uuid": "0d2a2043-41c0-59c3-9b17-025022203668"
                            },
                            "machine": {"type": "q35"},
                            "resources": {"requests": {"memory": "128Mi"}},
                        },
                        "networks": [{"name": "default", "pod": {}}],
                        "terminationGracePeriodSeconds": 0,
                        "volumes": [
                            {
                                "containerDisk": {
                                    "image": "registry:5000/kubevirt/cirros-container-disk-demo:devel",
                                    "imagePullPolicy": "IfNotPresent",
                                },
                                "name": "containerdisk",
                            },
                            {
                                "cloudInitNoCloud": {
                                    "userData": "#!/bin/sh\n\necho 'printed from cloud-init userdata'\n"
                                },
                                "name": "cloudinitdisk",
                            },
                        ],
                    },
                    "status": {
                        "activePods": {
                            "a9a6c31b-8574-46f9-8bec-70ff091c3d97": "node01"
                        },
                        "conditions": [
                            {
                                "lastProbeTime": None,
                                "lastTransitionTime": "2022-09-14T13:43:39Z",
                                "status": "True",
                                "type": "Ready",
                            },
                            {
                                "lastProbeTime": None,
                                "lastTransitionTime": None,
                                "message": "cannot migrate VMI which does not use masquerade to connect to the pod network",
                                "reason": "InterfaceNotLiveMigratable",
                                "status": "False",
                                "type": "LiveMigratable",
                            },
                        ],
                        "guestOSInfo": {},
                        "interfaces": [
                            {
                                "infoSource": "domain",
                                "ipAddress": "10.244.196.152",
                                "ipAddresses": ["10.244.196.152", "fd10:244::c497"],
                                "mac": "96:13:92:4f:05:d3",
                                "name": "default",
                                "queueCount": 1,
                            }
                        ],
                        "launcherContainerImageVersion":
                            "registry:5000/kubevirt/virt-launcher@sha256:5c1474d240488c9a8e6e6e48b2ad446113744353b4cd2464baee3550e6b1829d",
                        "migrationMethod": "BlockMigration",
                        "migrationTransport": "Unix",
                        "nodeName": "node01",
                        "phase": "Running",
                        "phaseTransitionTimestamps": [
                            {
                                "phase": "Pending",
                                "phaseTransitionTimestamp": "2022-09-14T13:43:36Z",
                            },
                            {
                                "phase": "Scheduling",
                                "phaseTransitionTimestamp": "2022-09-14T13:43:36Z",
                            },
                            {
                                "phase": "Scheduled",
                                "phaseTransitionTimestamp": "2022-09-14T13:43:39Z",
                            },
                            {
                                "phase": "Running",
                                "phaseTransitionTimestamp": "2022-09-14T13:43:40Z",
                            },
                        ],
                        "qosClass": "Burstable",
                        "runtimeUser": 0,
                        "virtualMachineRevisionName": "revision-start-vm-4d1b1438-91ba-4c75-a211-566fc50a06f5-9",
                        "volumeStatus": [
                            {"name": "cloudinitdisk", "size": 1048576, "target": "vdb"},
                            {"name": "containerdisk", "target": "vda"},
                        ],
                    },
                }
            ],
            "kind": "List",
            "metadata": {"resourceVersion": "", "selfLink": ""},
        },
    )
