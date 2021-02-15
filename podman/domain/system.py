from typing import Any, Dict, List

from podman.api.client import APIClient
from podman.domain.manager import Manager, PodmanResource
from podman.errors import APIError


class SystemManager(Manager):
    def list(self) -> List[PodmanResource]:
        raise NotImplementedError()

    def get(self, key: str) -> PodmanResource:
        raise NotImplementedError()

    def create(self, **kwargs) -> PodmanResource:
        raise NotImplementedError()

    resource = None

    def __init__(self, client: APIClient) -> None:
        """Initiate SystemManager object.

        Args:
            client: Connection to Podman service.
        """
        self.client = client

    def df(self) -> Dict[str, Any]:
        """Resource usage of Podman service.

        Returns:
            dict: Keyed by resource categories and their data usage.
        """
        pass

    def info(self, *args, **kwargs):
        pass

    def login(self, *args, **kwargs):
        pass

    def ping(self) -> bool:
        """Returns True if service responded with OK."""

        try:
            response = self.client.head("/_ping")
            if response.status_code == 200:
                return True
        except OSError as e:
            raise APIError("Ping failed.", response=response)
        return False

    def version(self, *args, **kwargs) -> Dict[str, Any]:
        """Get version information from service.

        Keyword Args:
            api_version (bool): Ignored.
        """

        try:
            response = self.client.get("/version")
            if response.status_code == 200:
                return response.json()
        except OSError as e:
            raise APIError("/version") from e
        raise APIError(
            response.url, response=response, explanation="Failed to retrieve version information."
        )
