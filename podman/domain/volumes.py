"""Model and Manager for Volume resources."""
from typing import List

from podman.api.client import APIClient
from podman.domain.manager import Manager, PodmanResource


class Volume(PodmanResource):
    """Details and configuration for an image managed by the Podman service."""


class VolumeManager(Manager):
    """Specialized Manager for Volume resources."""

    # Abstract methods (create,get,list) are specialized and pylint cannot walk hierarchy.
    # pylint: disable=arguments-differ

    resource = Volume

    def __init__(self, client: APIClient):
        """Initiate VolumeManager object.

        Args:
            client: Connection to Podman service.
        """
        super().__init__(client)

    def list(self) -> List[Volume]:
        """Report on volumes."""

    def get(self, volume_id: str) -> Volume:
        """Returns and volume by name or id.

        Args:
            volume_id: Volume id or name for which to search
        """
        _ = volume_id

    def create(self, *args, **kwargs) -> Volume:
        """Create an Volume."""

        _ = args
        _ = kwargs
