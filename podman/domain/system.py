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
                https://quay.io/v2. When explicitly provided, successful
                credentials are stored in the client-side credential store
                for use in subsequent build operations (via X-Registry-Config)
                and pull/push operations (via X-Registry-Auth). When omitted,
                the Podman service defaults to Docker Hub, but the client
                cannot reliably determine which registry was used from the
                API response, so credentials are not persisted for client-side
                reuse.
            reauth: Ignored: If True, refresh existing authentication. Default: False
            dockercfg_path: Ignored: Path to custom configuration file.
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

        # Store credentials for use in subsequent operations (e.g., build)
        # Only store credentials when registry is explicitly provided.
        # When registry is omitted, the Podman service defaults to Docker Hub,
        # but the client cannot reliably determine which registry was used
        # from the API response. Users should provide the registry explicitly
        # to enable credential persistence for build operations.
        if registry:
            auth_config = {
                "username": username,
                "password": password,
                "email": email,
                "auth": auth,
                "identitytoken": identitytoken,
                "registrytoken": registrytoken,
            }
            # Filter out None values
            auth_config = {k: v for k, v in auth_config.items() if v is not None}
            # Registry is normalized to canonical form for consistent lookup
            self.client.set_registry_auth(registry, auth_config)

        return response.json()

    def logout(self, registry: str) -> None:
        """Log out from a container registry by clearing stored credentials.

        This removes client-side in-memory credentials for the specified registry.
        Note: This does not affect Podman's auth.json file or any credential helpers
        configured on the Podman service side. It only clears credentials stored
        by the Python client's login() method for subsequent operations.

        Args:
            registry: Registry URL to log out from (e.g., "docker.io", "https://quay.io/v2").
                      The registry is normalized to canonical form before lookup.

        Raises:
            ValueError: If registry is None or empty
        """
        if not registry:
            raise ValueError("Registry must be provided for logout")

        self.client.clear_registry_auth(registry)

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
