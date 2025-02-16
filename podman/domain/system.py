"""SystemManager to provide system level information from Podman service."""

import logging
from typing import Any, Optional, Union

from podman.api.client import APIClient
from podman import api

logger = logging.getLogger("podman.system")


class SystemManager:
    """SystemManager to provide system level information from Podman service."""

    def __init__(self, client: APIClient) -> None:
        """Initialize SystemManager object.

        Args:
            client: Connection to Podman service.
        """
        self.client = client

    def df(self) -> dict[str, Any]:  # pylint: disable=invalid-name
        """Disk usage by Podman resources.

        Returns:
            dict: Keyed by resource categories and their data usage.
        """
        response = self.client.get("/system/df")
        response.raise_for_status()
        return response.json()

    def info(self, *_, **__) -> dict[str, Any]:
        """Returns information on Podman service."""
        response = self.client.get("/info")
        response.raise_for_status()
        return response.json()

    def login(  # pylint: disable=too-many-arguments,too-many-positional-arguments,unused-argument
        self,
        username: str,
        password: Optional[str] = None,
        email: Optional[str] = None,
        registry: Optional[str] = None,
        reauth: Optional[bool] = False,
        dockercfg_path: Optional[str] = None,
        auth: Optional[str] = None,
        identitytoken: Optional[str] = None,
        registrytoken: Optional[str] = None,
        tls_verify: Optional[Union[bool, str]] = None,
    ) -> dict[str, Any]:
        """Log into Podman service.

        Args:
            username: Registry username
            password: Registry plaintext password
            email: Registry account email address
            registry: URL for registry access. For example,
            reauth: Ignored: If True, refresh existing authentication. Default: False
            dockercfg_path: Ignored: Path to custom configuration file.
                https://quay.io/v2
            auth: TODO: Add description based on the source code of Podman.
            identitytoken: IdentityToken is used to authenticate the user and
                           get an access token for the registry.
            registrytoken: RegistryToken is a bearer token to be sent to a registry
            tls_verify: Whether to verify TLS certificates.
        """

        payload = {
            "username": username,
            "password": password,
            "email": email,
            "serveraddress": registry,
            "auth": auth,
            "identitytoken": identitytoken,
            "registrytoken": registrytoken,
        }
        payload = api.prepare_body(payload)
        response = self.client.post(
            path="/auth",
            headers={"Content-type": "application/json"},
            data=payload,
            compatible=True,
            verify=tls_verify,  # Pass tls_verify to the client
        )
        response.raise_for_status()
        return response.json()

    def ping(self) -> bool:
        """Returns True if service responded with OK."""
        response = self.client.head("/_ping")
        return response.ok

    def version(self, **kwargs) -> dict[str, Any]:
        """Get version information from service.

        Keyword Args:
            api_version (bool): When True include API version
        """
        response = self.client.get("/version")
        response.raise_for_status()

        body = response.json()
        if not kwargs.get("api_version", True):
            del body["APIVersion"]
        return body
