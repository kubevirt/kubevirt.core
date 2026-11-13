# -*- coding: utf-8 -*-
# Copyright 2026 KubeVirt Project
# Apache License 2.0 (see LICENSE or http://www.apache.org/licenses/LICENSE-2.0)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from urllib.parse import parse_qs, urlparse

import pytest
import requests
from ansible.plugins.inventory import Cacheable

from ansible_collections.kubevirt.core.plugins.inventory import kubevirt
from ansible_collections.kubevirt.core.plugins.module_utils import openshift_auth


def test_openshift_oauth_token_flow(mocker):
    discovery_response = mocker.Mock(status_code=200)
    discovery_response.json.return_value = {
        "authorization_endpoint": "https://oauth.example.test/authorize",
        "token_endpoint": "https://oauth.example.test/token",
    }
    authorization_response = mocker.Mock(status_code=302)
    token_response = mocker.Mock(status_code=200)
    token_response.json.return_value = {"access_token": "temporary-token"}

    def get_response(url, **kwargs):
        if url.endswith("/.well-known/oauth-authorization-server"):
            return discovery_response
        state = parse_qs(urlparse(url).query)["state"][0]
        authorization_response.headers = {
            "Location": f"https://oauth.example.test/callback?code=one-time-code&state={state}"
        }
        authorization_response.request_args = kwargs
        authorization_response.request_url = url
        return authorization_response

    get = mocker.patch.object(openshift_auth.requests, "get", side_effect=get_response)
    post = mocker.patch.object(
        openshift_auth.requests, "post", return_value=token_response
    )

    token = openshift_auth.get_openshift_oauth_token(
        "https://api.example.test:6443", "user", "password", False
    )

    assert token == "temporary-token"
    assert get.call_count == 2
    assert authorization_response.request_args["auth"] == ("user", "password")
    assert authorization_response.request_args["verify"] is False
    assert authorization_response.request_args["allow_redirects"] is False
    assert (
        authorization_response.request_args["headers"]["X-Csrf-Token"]
        == parse_qs(urlparse(authorization_response.request_url).query)["state"][0]
    )
    assert post.call_args.kwargs["auth"] == (
        "openshift-challenging-client",
        "",
    )
    assert post.call_args.kwargs["data"]["grant_type"] == "authorization_code"
    assert post.call_args.kwargs["data"]["code"] == "one-time-code"
    assert post.call_args.kwargs["data"]["code_verifier"]


@pytest.mark.parametrize(
    "status_code, expected_message",
    [
        (401, "authorization failed"),
        (500, "authorization failed"),
    ],
)
def test_openshift_oauth_authorization_error(mocker, status_code, expected_message):
    discovery_response = mocker.Mock(status_code=200)
    discovery_response.json.return_value = {
        "authorization_endpoint": "https://oauth.example.test/authorize",
        "token_endpoint": "https://oauth.example.test/token",
    }
    authorization_response = mocker.Mock(status_code=status_code)
    mocker.patch.object(
        openshift_auth.requests,
        "get",
        side_effect=[discovery_response, authorization_response],
    )

    with pytest.raises(openshift_auth.OpenShiftOAuthError, match=expected_message):
        openshift_auth.get_openshift_oauth_token(
            "https://api.example.test:6443", "user", "password", True
        )


def test_revoke_openshift_oauth_token(mocker):
    response = mocker.Mock(status_code=204)
    delete = mocker.patch.object(
        openshift_auth.requests, "delete", return_value=response
    )

    assert openshift_auth.revoke_openshift_oauth_token(
        "https://api.example.test:6443", "temporary-token", False
    )
    assert delete.call_args.kwargs["headers"] == {
        "Authorization": "Bearer temporary-token"
    }
    assert delete.call_args.kwargs["verify"] is False
    assert (
        "/apis/oauth.openshift.io/v1/useroauthaccesstokens/sha256~"
        in delete.call_args.args[0]
    )


def test_revoke_openshift_oauth_token_network_error(mocker):
    mocker.patch.object(
        openshift_auth.requests,
        "delete",
        side_effect=requests.ConnectionError("unreachable"),
    )

    assert not openshift_auth.revoke_openshift_oauth_token(
        "https://api.example.test:6443", "temporary-token", True
    )


@pytest.mark.parametrize(
    "config, expected_verify",
    [
        ({"validate_certs": False}, False),
        ({"ca_cert": "/tmp/ca.crt", "validate_certs": True}, "/tmp/ca.crt"),
        ({"ca_cert": "/tmp/ca.crt", "validate_certs": False}, False),
    ],
)
def test_openshift_auth_config_builds_token_client(
    mocker, inventory, config, expected_verify
):
    token = mocker.patch.object(
        kubevirt, "get_openshift_oauth_token", return_value="temporary-token"
    )
    client = mocker.patch.object(kubevirt, "get_api_client", return_value="client")
    mocker.patch.object(kubevirt, "revoke_openshift_oauth_token")
    config_data = {
        "auth_type": "openshift_oauth",
        "host": "https://api.example.test:6443",
        "username": "user",
        "password": "password",
        **config,
    }

    api_client, generated_token, host, verify = inventory._get_api_client(config_data)

    assert api_client == "client"
    assert generated_token == "temporary-token"
    assert host == config_data["host"]
    assert verify == expected_verify
    token.assert_called_once_with(
        config_data["host"], "user", "password", expected_verify
    )
    expected_config = {
        key: value
        for key, value in config_data.items()
        if key not in ("auth_type", "username", "password")
    }
    expected_config["api_key"] = "temporary-token"
    client.assert_called_once_with(**expected_config)


def test_openshift_auth_uses_auth_environment(mocker, inventory):
    mocker.patch.dict(
        "os.environ",
        {
            "K8S_AUTH_HOST": "https://api.example.test:6443",
            "K8S_AUTH_USERNAME": "user",
            "K8S_AUTH_PASSWORD": "password",
            "K8S_AUTH_VERIFY_SSL": "false",
        },
    )
    token = mocker.patch.object(
        kubevirt, "get_openshift_oauth_token", return_value="temporary-token"
    )
    client = mocker.patch.object(kubevirt, "get_api_client", return_value="client")
    mocker.patch.object(kubevirt, "revoke_openshift_oauth_token")

    api_client, generated_token, host, verify = inventory._get_api_client(
        {"auth_type": "openshift_oauth"}
    )

    assert api_client == "client"
    assert generated_token == "temporary-token"
    assert host == "https://api.example.test:6443"
    assert verify is False
    token.assert_called_once_with(
        "https://api.example.test:6443", "user", "password", False
    )
    client.assert_called_once_with(
        api_key="temporary-token", host="https://api.example.test:6443"
    )


@pytest.mark.parametrize("fetch_error", [None, RuntimeError("fetch failed")])
def test_parse_revokes_openshift_token_after_fetch(mocker, inventory, fetch_error):
    mocker.patch.object(Cacheable, "cache", new_callable=mocker.PropertyMock)
    mocker.patch.object(
        inventory, "_read_config_data", return_value={"auth_type": "openshift_oauth"}
    )
    mocker.patch.object(inventory, "get_cache_key", return_value="cache-key")
    mocker.patch.object(inventory, "get_option", return_value=False)
    mocker.patch.object(
        inventory,
        "_get_api_client",
        return_value=("client", "temporary-token", "https://api.example.test", False),
    )
    fetch = mocker.patch.object(inventory, "_fetch_objects", return_value={})
    if fetch_error:
        fetch.side_effect = fetch_error
    mocker.patch.object(inventory, "_populate_inventory")
    revoke = mocker.patch.object(kubevirt, "revoke_openshift_oauth_token")

    if fetch_error:
        with pytest.raises(RuntimeError, match="fetch failed"):
            inventory.parse(None, None, "inventory.kubevirt.yml", False)
    else:
        inventory.parse(None, None, "inventory.kubevirt.yml", False)

    revoke.assert_called_once_with("https://api.example.test", "temporary-token", False)
