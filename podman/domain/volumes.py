"""Model and Manager for Volume resources."""
import json
from typing import Dict, List, Optional

from podman.api.client import APIClient
from podman.domain.manager import Manager, PodmanResource
from podman.errors import APIError


class Volume(PodmanResource):
    """Details and configuration for an image managed by the Podman service."""

    @property
    def id(self):
        """Returns the identifier of the volume."""
        return self.name

    @property
    def name(self):
        """Returns the name of the volume."""
        return self.attrs["Name"]

    def remove(self, force: bool = False):
        """Delete this volume.

        Args:
            force: When true, force deletion of volume

        Raises:
            APIError when service reports an error
        """


class VolumeManager(Manager):
    """Specialized Manager for Volume resources."""

    resource = Volume

    def __init__(self, client: APIClient):
        """Initiate VolumeManager object.

        Args:
            client: Connection to Podman service.
        """
        super().__init__(client)

    def create(self, name: Optional[str] = None, **kwargs) -> Volume:
        """Create an Volume.

        Args:
            name: Name given to new volume

        Keyword Args:
            driver (str): Volume driver to use
            driver_opts (Dict[str, str]): Options to use with driver
            labels (Dict[str, str]): Labels to apply to volume

        Raises:
            APIError when service reports error
        """
        body = {
            "Driver": kwargs.get("driver", None),
            "Label": kwargs.get("label", None),
            "Name": name,
            "Options": kwargs.get("driver_opts"),
        }
        # Strip out any keys without a value
        body = {k: v for (k, v) in body.items() if v is not None}
        contents = json.dumps(body)

        response = self.client.post(
            "/volumes/create",
            data=contents,
            headers={"Content-Type": "application/json"},
        )
        body = response.json()

        if response.status_code != 201:
            raise APIError(body["cause"], response=response, explanation=body["message"])

        return self.get(volume_id=body["Name"])

    # pylint is flagging 'volume_id' here vs. 'key' parameter in super.get()
    def get(self, volume_id: str) -> Volume:  # pylint: disable=arguments-differ
        """Returns and volume by name or id.

        Args:
            volume_id: Volume id or name for which to search

        Raises:
            NotFound if volume could not be found
            APIError when service reports an error
        """
        _ = volume_id

    def list(self, *_, **kwargs) -> List[Volume]:
        """Report on volumes.

        Keyword Args:
            filters (Dict[str, str]): criteria to filter Volume list
        """

    def prune(self, filters: Optional[Dict[str, str]] = None) -> None:
        """Delete unused volumes.

        Args:
            filters: Criteria for selecting volumes to delete

        Raises:
            APIError when service reports error
        """
