"""Model and Manager for Volume resources."""
import logging
from typing import Any, Dict, List, Optional, Union

import requests

from podman import api
from podman.api import Literal
from podman.domain.manager import Manager, PodmanResource
from podman.errors import APIError

logger = logging.getLogger("podman.volumes")


class Volume(PodmanResource):
    """Details and configuration for an image managed by the Podman service."""

    @property
    def id(self):
        return self.name

    @property
    def name(self):
        """str: Returns the name of the volume."""
        return self.attrs.get("Name")

    def remove(self, force: Optional[bool] = None) -> None:
        """Delete this volume.

        Args:
            force: When true, force deletion of in-use volume

        Raises:
            APIError: when service reports an error
        """
        self.manager.remove(self.name, force=force)


class VolumesManager(Manager):
    """Specialized Manager for Volume resources."""

    @property
    def resource(self):
        """Type[Volume]: prepare_model() will create Volume classes."""
        return Volume

    def create(self, name: Optional[str] = None, **kwargs) -> Volume:
        """Create a Volume.

        Args:
            name: Name given to new volume

        Keyword Args:
            driver (str): Volume driver to use
            driver_opts (Dict[str, str]): Options to use with driver
            labels (Dict[str, str]): Labels to apply to volume

        Raises:
            APIError: when service reports error
        """
        data = {
            "Driver": kwargs.get("driver"),
            "Labels": kwargs.get("labels"),
            "Name": name,
            "Options": kwargs.get("driver_opts"),
        }
        response = self.client.post(
            "/volumes/create",
            data=api.prepare_body(data),
            headers={"Content-Type": "application/json"},
        )
        response.raise_for_status()
        return self.prepare_model(attrs=response.json())

    def exists(self, key: str) -> bool:
        response = self.client.get(f"/volumes/{key}/exists")
        return response.ok

    # pylint is flagging 'volume_id' here vs. 'key' parameter in super.get()
    def get(self, volume_id: str) -> Volume:  # pylint: disable=arguments-differ,arguments-renamed
        """Returns and volume by name or id.

        Args:
            volume_id: Volume id or name for which to search

        Raises:
            NotFound: when volume could not be found
            APIError: when service reports an error
        """
        response = self.client.get(f"/volumes/{volume_id}/json")
        response.raise_for_status()
        return self.prepare_model(attrs=response.json())

    def list(self, *_, **kwargs) -> List[Volume]:
        """Report on volumes.

        Keyword Args:
            filters (Dict[str, str]): criteria to filter Volume list

                - driver (str): filter volumes by their driver
                - label (Dict[str, str]): filter by label and/or value
                - name (str): filter by volume's name
        """
        filters = api.prepare_filters(kwargs.get("filters"))
        response = self.client.get("/volumes/json", params={"filters": filters})

        if response.status_code == requests.codes.not_found:
            return []
        response.raise_for_status()

        return [self.prepare_model(i) for i in response.json()]

    def prune(
        self, filters: Optional[Dict[str, str]] = None  # pylint: disable=unused-argument
    ) -> Dict[Literal["VolumesDeleted", "SpaceReclaimed"], Any]:
        """Delete unused volumes.

        Args:
            filters: Criteria for selecting volumes to delete. Ignored.

        Raises:
            APIError: when service reports error
        """
        response = self.client.post("/volumes/prune")
        data = response.json()
        response.raise_for_status()

        volumes: List[str] = []
        space_reclaimed = 0
        for item in data:
            if "Err" in item:
                raise APIError(
                    item["Err"],
                    response=response,
                    explanation=f"""Failed to prune volume '{item.get("Id")}'""",
                )
            volumes.append(item.get("Id"))
            space_reclaimed += item["Size"]

        return {"VolumesDeleted": volumes, "SpaceReclaimed": space_reclaimed}

    def remove(self, name: Union[Volume, str], force: Optional[bool] = None) -> None:
        """Delete a volume.

        Podman only.

        Args:
            name: Identifier for Volume to be deleted.
            force: When true, force deletion of in-use volume

        Raises:
            APIError: when service reports an error
        """
        if isinstance(name, Volume):
            name = name.name
        response = self.client.delete(f"/volumes/{name}", params={"force": force})
        response.raise_for_status()
