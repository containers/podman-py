"""Model and Manager for Volume resources."""
import json
from typing import Any, Dict, List, Optional

from podman import api
from podman.api.client import APIClient
from podman.domain.manager import Manager, PodmanResource
from podman.errors import APIError, NotFound


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

    def remove(self, force: bool = None):
        """Delete this volume.

        Args:
            force: When true, force deletion of volume

        Raises:
            APIError when service reports an error
        """
        params = {"force": force}
        response = self.client.delete(f"/volumes/{self.name}", params=params)

        if response.status_code == 204:
            return

        data = response.json()
        if response.status_code == 404:
            raise NotFound(data["cause"], response=response, explanation=data["message"])

        raise APIError(data["cause"], response=response, explanation=data["message"])


class VolumesManager(Manager):
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
        data = {
            "Driver": kwargs.get("driver", None),
            "Labels": kwargs.get("labels", None),
            "Name": name,
            "Options": kwargs.get("driver_opts"),
        }
        # Strip out any keys without a value
        data = {k: v for (k, v) in data.items() if v is not None}
        contents = json.dumps(data)

        response = self.client.post(
            "/volumes/create",
            data=contents,
            headers={"Content-Type": "application/json"},
        )
        data = response.json()

        if response.status_code == 201:
            return self.prepare_model(data)

        raise APIError(data["cause"], response=response, explanation=data["message"])

    # pylint is flagging 'volume_id' here vs. 'key' parameter in super.get()
    def get(self, volume_id: str) -> Volume:  # pylint: disable=arguments-differ
        """Returns and volume by name or id.

        Args:
            volume_id: Volume id or name for which to search

        Raises:
            NotFound if volume could not be found
            APIError when service reports an error
        """
        response = self.client.get(f"/volumes/{volume_id}")

        if response.status_code == 404:
            raise NotFound(
                response.text, response=response, explanation=f"Failed to find volume '{volume_id}'"
            )

        data = response.json()
        if response.status_code == 200:
            return self.prepare_model(data)

        raise APIError(data["cause"], response=response, explanation=data["message"])

    def list(self, *_, **kwargs) -> List[Volume]:
        """Report on volumes.

        Keyword Args:
            filters (Dict[str, str]): criteria to filter Volume list
                - driver (str): filter volumes by their driver
                - label (Dict[str, str]): filter by label and/or value
                - name (str): filter by volume's name
        """
        filters = api.prepare_filters(kwargs.get("filters"))
        response = self.client.get("/volumes", params={"filters": filters})

        if response.status_code == 404:
            return []

        data = response.json()
        if response.status_code == 200:
            volumes: List[Volume] = list()
            for item in data:
                volumes.append(self.prepare_model(item))
            return volumes

        raise APIError(data["cause"], response=response, explanation=data["message"])

    def prune(
        self, filters: Optional[Dict[str, str]] = None  # pylint: disable=unused-argument
    ) -> Dict[str, Any]:
        """Delete unused volumes.

        Args:
            filters: Criteria for selecting volumes to delete. Ignored.

        Raises:
            APIError when service reports error
        """
        response = self.client.post("/volumes/prune")
        data = response.json()

        if response.status_code != 200:
            raise APIError(data["cause"], response=response, explanation=data["message"])

        volumes: List[str] = list()
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
