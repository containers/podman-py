"""SystemManager to provide system level information from Podman service."""
from typing import Any, Dict, List, Optional

from podman.api.client import APIClient
from podman.domain.manager import Manager, PodmanResource
from podman.errors import APIError


class SystemManager(Manager):
    """SystemManager to provide system level information from Podman service."""

    # Abstract methods (create,get,list) are specialized and pylint cannot walk hierarchy.
    # pylint: disable=arguments-differ

    resource = None

    def __init__(self, client: APIClient) -> None:
        """Initiate SystemManager object.

        Args:
            client: Connection to Podman service.
        """
        super().__init__(client)

    def list(self) -> List[PodmanResource]:
        """NotImplementedError."""
        raise NotImplementedError()

    def get(self, key: str) -> PodmanResource:
        """NotImplementedError."""
        _ = key
        raise NotImplementedError()

    def create(self, **kwargs) -> PodmanResource:
        """NotImplementedError."""
        _ = kwargs

        raise NotImplementedError()

    def df(self) -> Dict[str, Any]:  # pylint: disable=invalid-name
        """Disk usage by Podman resources.

        Returns:
            dict: Keyed by resource categories and their data usage.
        """
        response = self.client.get("/system/df")
        body = response.json()

        if response.status_code == 200:
            return body

        raise APIError(body["cause"], response=response, explanation=body["message"])

    def info(self, *_, **__) -> Dict[str, Any]:
        """Returns information on Podman service."""
        response = self.client.get("/system/info")
        body = response.json()

        if response.status_code == 200:
            return body

        raise APIError(body["cause"], response=response, explanation=body["message"])

    def login(
        self,
        username: str,
        password: Optional[str] = None,
        email: Optional[str] = None,
        registry: Optional[str] = None,
        reauth: bool = False,
        dockercfg_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Log into Podman service.

        Args:
            username: Registry username
            password: Registry plaintext password
            email: Registry account email address
            registry: URL for registry access. For example,
                https://quay.io/v2
            reauth: If True, refresh existing authentication. Default: False
            dockercfg_path: Path to custom configuration file.
                Default: $HOME/.config/containers/config.json
        """

    def ping(self) -> bool:
        """Returns True if service responded with OK."""
        response = self.client.head("/_ping")
        if response.status_code == 200:
            return True
        return False

    def version(self, *_, **kwargs) -> Dict[str, Any]:
        """Get version information from service.

        Keyword Args:
            api_version (bool): When True include API version
        """
        response = self.client.get("/version")
        body = response.json()

        if response.status_code == 200:
            if not kwargs.get("api_version", True):
                del body["APIVersion"]
            return body

        raise APIError(body["cause"], response=response, explanation=body["message"])
