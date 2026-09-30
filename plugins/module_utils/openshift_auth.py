# -*- coding: utf-8 -*-
# Copyright 2026 KubeVirt Project
# Apache License 2.0 (see LICENSE or http://www.apache.org/licenses/LICENSE-2.0)

"""Helpers for authenticating to OpenShift using its OAuth challenging-client flow."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import base64
import hashlib
import secrets
from typing import Any, Dict
from urllib.parse import parse_qs, quote, urlencode, urljoin, urlparse

try:
    import requests
    from requests import RequestException

    REQUESTS_IMPORT_EXCEPTION = None
except ImportError as exc:
    requests = None
    REQUESTS_IMPORT_EXCEPTION = exc

    class RequestException(Exception):
        """Fallback request exception used when the requests dependency is unavailable."""


OAUTH_CLIENT_ID = "openshift-challenging-client"
OAUTH_TIMEOUT = 15


class OpenShiftOAuthError(Exception):
    """Raised when OpenShift OAuth discovery or authentication fails."""


def _url_with_query(url: str, params: Dict[str, str]) -> str:
    """Append query parameters while preserving any already present on the URL."""
    separator = "&" if urlparse(url).query else "?"
    return f"{url}{separator}{urlencode(params)}"


def get_openshift_oauth_token(
    host: str, username: str, password: str, verify: Any
) -> str:
    """Exchange username/password credentials for a temporary OpenShift OAuth token."""
    if requests is None:
        raise OpenShiftOAuthError(
            "OpenShift OAuth authentication requires the Python requests package. "
            f"Try `pip install requests`. Detail: {REQUESTS_IMPORT_EXCEPTION}"
        )

    base_url = host.rstrip("/") + "/"
    try:
        discovery = requests.get(
            urljoin(base_url, ".well-known/oauth-authorization-server"),
            verify=verify,
            timeout=OAUTH_TIMEOUT,
        )
        if discovery.status_code != 200:
            raise OpenShiftOAuthError(
                "OpenShift OAuth discovery failed with HTTP "
                f"{discovery.status_code}. Check the API host and TLS settings."
            )
        oauth_info = discovery.json()
        authorization_endpoint = oauth_info["authorization_endpoint"]
        token_endpoint = oauth_info["token_endpoint"]
    except OpenShiftOAuthError:
        raise
    except (RequestException, ValueError, KeyError, TypeError) as exc:
        raise OpenShiftOAuthError(
            "Unable to discover the OpenShift OAuth endpoints "
            f"({type(exc).__name__}). Check the API host and TLS settings."
        ) from exc

    state = secrets.token_urlsafe(32)
    verifier = secrets.token_urlsafe(64)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest())
    challenge = challenge.rstrip(b"=").decode("ascii")
    authorization_url = _url_with_query(
        authorization_endpoint,
        {
            "client_id": OAUTH_CLIENT_ID,
            "response_type": "code",
            "state": state,
            "code_challenge": challenge,
            "code_challenge_method": "S256",
        },
    )

    try:
        authorization = requests.get(
            authorization_url,
            auth=(username, password),
            headers={"X-Csrf-Token": state},
            verify=verify,
            allow_redirects=False,
            timeout=OAUTH_TIMEOUT,
        )
        if authorization.status_code not in (302, 303):
            raise OpenShiftOAuthError(
                "OpenShift OAuth authorization failed with HTTP "
                f"{authorization.status_code}. Verify the username and password."
            )
        location = authorization.headers.get("Location")
        if not location:
            raise OpenShiftOAuthError(
                "OpenShift OAuth authorization response had no redirect."
            )
        redirect_params = parse_qs(urlparse(location).query)
        if redirect_params.get("state", [None])[0] != state:
            raise OpenShiftOAuthError(
                "OpenShift OAuth authorization returned an invalid state."
            )
        code = redirect_params.get("code", [None])[0]
        if not code:
            raise OpenShiftOAuthError(
                "OpenShift OAuth authorization response contained no code."
            )

        token_response = requests.post(
            token_endpoint,
            auth=(OAUTH_CLIENT_ID, ""),
            headers={"Accept": "application/json"},
            data={
                "grant_type": "authorization_code",
                "code": code,
                "state": state,
                "code_verifier": verifier,
            },
            verify=verify,
            timeout=OAUTH_TIMEOUT,
        )
        if token_response.status_code != 200:
            raise OpenShiftOAuthError(
                "OpenShift OAuth token exchange failed with HTTP "
                f"{token_response.status_code}."
            )
        token = token_response.json().get("access_token")
        if not token:
            raise OpenShiftOAuthError(
                "OpenShift OAuth token response contained no access token."
            )
        return token
    except OpenShiftOAuthError:
        raise
    except (RequestException, ValueError, KeyError, TypeError) as exc:
        raise OpenShiftOAuthError(
            "OpenShift OAuth authentication failed "
            f"({type(exc).__name__}). Check the API host, TLS settings, and credentials."
        ) from exc


def revoke_openshift_oauth_token(host: str, token: str, verify: Any) -> bool:
    """Revoke a temporary OpenShift token, returning whether the API accepted it."""
    if requests is None:
        return False
    content = token[len("sha256~") :] if token.startswith("sha256~") else token
    digest = base64.urlsafe_b64encode(hashlib.sha256(content.encode()).digest())
    digest = digest.rstrip(b"=").decode("ascii")
    object_name = quote(f"sha256~{digest}", safe="~")
    url = (
        f"{host.rstrip('/')}/apis/oauth.openshift.io/v1/"
        f"useroauthaccesstokens/{object_name}"
    )
    try:
        response = requests.delete(
            url,
            json={
                "apiVersion": "oauth.openshift.io/v1",
                "kind": "DeleteOptions",
                "gracePeriodSeconds": 0,
            },
            headers={"Authorization": f"Bearer {token}"},
            verify=verify,
            timeout=OAUTH_TIMEOUT,
        )
        return response.status_code in (200, 202, 204)
    except RequestException:
        return False
