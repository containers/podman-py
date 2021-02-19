"""Model and Manager for Pod resources."""
from typing import List

from podman.api.client import APIClient
from podman.domain.manager import Manager, PodmanResource


class Pod(PodmanResource):
    """Details and configuration for a pod managed by the Podman service."""


class PodManager(Manager):
    """Specialized Manager for Pod resources."""

    # Abstract methods (create,get,list) are specialized and pylint cannot walk hierarchy.
    # pylint: disable=arguments-differ

    resource = Pod

    def __init__(self, client: APIClient):
        """Initiate PodManager object.

        Args:
            client: Connection to Podman service.
        """
        super().__init__(client)

    def list(self) -> List[Pod]:
        """Report on pods."""

    def get(self, pod_id: str) -> Pod:
        """Returns and image by name or id.

        Args:
            pod_id: Image id or name for which to search
        """
        _ = pod_id

    def create(self, *args, **kwargs) -> PodmanResource:
        """Create a Pod."""
