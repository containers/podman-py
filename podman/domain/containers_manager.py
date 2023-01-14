"""PodmanResource manager subclassed for Containers."""
import logging
import urllib
from typing import Any, Dict, List, Mapping, Union

from podman import api
from podman.domain.containers import Container
from podman.domain.containers_create import CreateMixin
from podman.domain.containers_run import RunMixin
from podman.domain.manager import Manager
from podman.errors import APIError

logger = logging.getLogger("podman.containers")


class ContainersManager(RunMixin, CreateMixin, Manager):
    """Specialized Manager for Container resources."""

    @property
    def resource(self):
        """Type[Container]: prepare_model() will create Container classes."""
        return Container

    def exists(self, key: str) -> bool:
        response = self.client.get(f"/containers/{key}/exists")
        return response.ok

    def get(self, key: str) -> Container:
        """Get container by name or id.

        Args:
            container_id: Container name or id.

        Returns:
            A `Container` object corresponding to `key`.

        Raises:
            NotFound: when Container does not exist
            APIError: when an error return by service
        """
        container_id = urllib.parse.quote_plus(key)
        response = self.client.get(f"/containers/{container_id}/json")
        response.raise_for_status()
        return self.prepare_model(attrs=response.json())

    def list(self, **kwargs) -> List[Container]:
        """Report on containers.

        Keyword Args:
            all: If False, only show running containers. Default: False.
            since: Show containers created after container name or id given.
            before: Show containers created before container name or id given.
            limit: Show last N created containers.
            filters: Filter container reported.
                Available filters:

                - exited (int): Only containers with specified exit code
                - status (str): One of restarting, running, paused, exited
                - label (Union[str, List[str]]): Format either "key", "key=value" or a list of such.
                - id (str): The id of the container.
                - name (str): The name of the container.
                - ancestor (str): Filter by container ancestor. Format of
                    <image-name>[:tag], <image-id>, or <image@digest>.
                - before (str): Only containers created before a particular container.
                    Give the container name or id.
                - since (str): Only containers created after a particular container.
                    Give container name or id.
            sparse: Ignored
            ignore_removed: If True, ignore failures due to missing containers.

        Raises:
            APIError: when service returns an error
        """
        params = {
            "all": kwargs.get("all"),
            "filters": kwargs.get("filters", {}),
            "limit": kwargs.get("limit"),
        }
        if "before" in kwargs:
            params["filters"]["before"] = kwargs.get("before")
        if "since" in kwargs:
            params["filters"]["since"] = kwargs.get("since")

        # filters formatted last because some kwargs may need to be mapped into filters
        params["filters"] = api.prepare_filters(params["filters"])

        response = self.client.get("/containers/json", params=params)
        response.raise_for_status()

        return [self.prepare_model(attrs=i) for i in response.json()]

    def prune(self, filters: Mapping[str, str] = None) -> Dict[str, Any]:
        """Delete stopped containers.

        Args:
            filters: Criteria for determining containers to remove. Available keys are:
                - until (str): Delete containers before this time
                - label (List[str]): Labels associated with containers

        Returns:
            Keys:
                - ContainersDeleted (List[str]): Identifiers of deleted containers.
                - SpaceReclaimed (int): Amount of disk space reclaimed in bytes.

        Raises:
            APIError: when service reports an error
        """
        params = {"filters": api.prepare_filters(filters)}
        response = self.client.post("/containers/prune", params=params)
        response.raise_for_status()

        results = {"ContainersDeleted": [], "SpaceReclaimed": 0}
        for entry in response.json():
            if entry.get("error") is not None:
                raise APIError(entry["error"], response=response, explanation=entry["error"])

            results["ContainersDeleted"].append(entry["Id"])
            results["SpaceReclaimed"] += entry["Size"]
        return results

    def remove(self, container_id: Union[Container, str], **kwargs):
        """Delete container.

        Podman only

        Args:
            container_id: identifier of Container to delete.

        Keyword Args:
            v (bool): Delete associated volumes as well.
            link (bool): Ignored.
            force (bool): Kill a running container before deleting.
        """
        if isinstance(container_id, Container):
            container_id = container_id.id

        params = {
            "v": kwargs.get("v"),
            "force": kwargs.get("force"),
        }

        response = self.client.delete(f"/containers/{container_id}", params=params)
        response.raise_for_status()
