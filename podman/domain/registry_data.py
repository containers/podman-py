"""Module for tracking registry metadata."""
import logging
from typing import Any, Mapping, Optional, Union

from podman import api
from podman.domain.images import Image
from podman.domain.manager import PodmanResource
from podman.errors import InvalidArgument

logger = logging.getLogger("podman.images")


class RegistryData(PodmanResource):
    """Registry metadata about Image."""

    def __init__(self, image_name: str, *args, **kwargs) -> None:
        """Initialize RegistryData object.

        Args:
            image_name: Name of Image.

        Keyword Args:
            client (APIClient): Configured connection to a Podman service.
            collection (Manager): Manager of this category of resource,
                named `collection` for compatibility

        """
        super().__init__(*args, **kwargs)
        self.image_name = image_name

        self.attrs = kwargs.get("attrs")
        if self.attrs is None:
            self.attrs = self.manager.get(image_name).attrs

    def pull(self, platform: Optional[str] = None) -> Image:
        """Returns Image pulled by identifier.

        Args:
            platform: Platform for which to pull Image. Default: None (all platforms.)
        """
        repository = api.parse_repository(self.image_name)
        return self.manager.pull(repository, tag=self.id, platform=platform)

    def has_platform(self, platform: Union[str, Mapping[str, Any]]) -> bool:
        """Returns True if platform is available for Image.

        Podman API does not support "variant" therefore it is ignored.

        Args:
            platform: Name as os[/arch[/variant]] or Mapping[str,Any]

        Returns:
            True if platform is available

        Raises:
            InvalidArgument: when platform value is not valid
            APIError: when service reports an error
        """
        invalid_platform = InvalidArgument(f"'{platform}' is not a valid platform descriptor.")

        if platform is None:
            platform = {}

        if isinstance(platform, dict):
            if not {"os", "architecture"} <= platform.keys():
                version = self.client.version()
                platform["os"] = platform.get("os", version["Os"])
                platform["architecture"] = platform.get("architecture", version["Arch"])
        elif isinstance(platform, str):
            elements = platform.split("/")
            if 1 < len(elements) > 3:
                raise invalid_platform

            platform = {"os": elements[0]}
            if len(elements) > 2:
                platform["variant"] = elements[2]
            if len(elements) > 1:
                platform["architecture"] = elements[1]
        else:
            raise invalid_platform

        return (
            # Variant not carried in libpod attrs
            platform["os"] == self.attrs["Os"]
            and platform["architecture"] == self.attrs["Architecture"]
        )
