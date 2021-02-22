"""Model and Manager for Image resources."""
from typing import List

from podman.api.client import APIClient
from podman.domain.manager import Manager, PodmanResource


class Image(PodmanResource):
    """Details and configuration for an image managed by the Podman service."""


class ImageManager(Manager):
    """Specialized Manager for Image resources."""

    # Abstract methods (create,get,list) are specialized and pylint cannot walk hierarchy.
    # pylint: disable=arguments-differ

    resource = Image

    def __init__(self, client: APIClient):
        """Initiate ImageManager object.

        Args:
            client: Connection to Podman service.
        """
        super().__init__(client)

    def list(self) -> List[Image]:
        """Report on images."""

    def get(self, image_id: str) -> Image:
        """Returns and image by name or id.

        Args:
            image_id: Image id or name for which to search
        """
        _ = image_id

    def create(self, *args, **kwargs) -> Image:
        """Create an Image."""
