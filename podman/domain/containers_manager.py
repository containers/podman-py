"""PodmanResource manager subclassed for Containers."""
import logging
import urllib
from typing import Any, Dict, List, Mapping, Type

import requests

from podman import api
from podman.domain.containers import Container
from podman.domain.containers_create import CreateMixin
from podman.domain.containers_run import RunMixin
from podman.domain.manager import Manager, PodmanResource
from podman.errors import APIError, NotFound

logger = logging.getLogger("podman.containers")


class ContainersManager(RunMixin, CreateMixin, Manager):
    """Specialized Manager for Container resources."""

    @property
    def resource(self) -> Type[PodmanResource]:
        return Container

    def exists(self, key: str) -> bool:
        response = self.client.get(f"/containers/{key}/exists")
        return response.status_code == requests.codes.no_content

    # pylint is flagging 'container_id' here vs. 'key' parameter in super.get()
    def get(self, container_id: str) -> Container:  # pylint: disable=arguments-differ
        """Get container by name or id.

        Args:
            container_id: Container name or id.

        Raises:
            NotFound: Container does not exist.
            APIError: Error return by service.
        """
        container_id = urllib.parse.quote_plus(container_id)
        response = self.client.get(f"/containers/{container_id}/json")
        body = response.json()

        if response.status_code == requests.codes.okay:
            return self.prepare_model(attrs=body)

        if response.status_code == requests.codes.not_found:
            raise NotFound(body["cause"], response=response, explanation=body["message"])
        raise APIError(body["cause"], response=response, explanation=body["message"])

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
            APIError: If service returns an error.
        """
        params = {
            "all": kwargs.get("all"),
            "filters": kwargs.get("filters", dict()),
            "limit": kwargs.get("limit"),
        }
        if "before" in kwargs:
            params["filters"]["before"] = kwargs.get("before")
        if "since" in kwargs:
            params["filters"]["since"] = kwargs.get("since")

        # filters formatted last because some kwargs may need to be mapped into filters
        params["filters"] = api.prepare_filters(params["filters"])

        response = self.client.get("/containers/json", params=params)
        body = response.json()

        if response.status_code != requests.codes.okay:
            raise APIError(body["cause"], response=response, explanation=body["message"])

        return [self.prepare_model(attrs=i) for i in body]

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
            APIError: If service reports an error
        """
        params = {"filters": api.prepare_filters(filters)}
        response = self.client.post("/containers/prune", params=params)
        body = response.json()

        if response.status_code != requests.codes.okay:
            raise APIError(body["cause"], response=response, explanation=body["message"])

        results = {"ContainersDeleted": list(), "SpaceReclaimed": 0}
        for entry in body:
            if entry.get("error", None) is not None:
                raise APIError(entry["error"], response=response, explanation=entry["error"])

            results["ContainersDeleted"].append(entry["Id"])
            results["SpaceReclaimed"] += entry["Size"]
        return results
