"""PodmanResource manager subclassed for Networks."""
import json
import logging
from typing import Any, Dict, List, Optional, Union

from podman import api
from podman.domain.manager import Manager
from podman.domain.pods import Pod
from podman.errors import APIError

logger = logging.getLogger("podman.pods")


class PodsManager(Manager):
    """Specialized Manager for Pod resources."""

    @property
    def resource(self):
        """Type[Pod]: prepare_model() will create Pod classes."""
        return Pod

    def create(self, name: str, **kwargs) -> Pod:
        """Create a Pod.

        Keyword Args:
            See (API documentation)[
                https://docs.podman.io/en/latest/_static/api.html#operation/CreatePod] for
                complete list of keywords.
        """
        data = {} if kwargs is None else kwargs.copy()
        data["name"] = name

        response = self.client.post("/pods/create", data=json.dumps(data))
        response.raise_for_status()

        body = response.json()
        return self.get(body["Id"])

    def exists(self, key: str) -> bool:
        """Returns True, when pod exists."""
        response = self.client.get(f"/pods/{key}/exists")
        return response.ok

    # pylint is flagging 'pod_id' here vs. 'key' parameter in super.get()
    def get(self, pod_id: str) -> Pod:  # pylint: disable=arguments-differ,arguments-renamed
        """Return information for Pod by name or id.

        Args:
            pod_id: Pod name or id.

        Raises:
            NotFound: when network does not exist
            APIError: when error returned by service
        """
        response = self.client.get(f"/pods/{pod_id}/json")
        response.raise_for_status()
        return self.prepare_model(attrs=response.json())

    def list(self, **kwargs) -> List[Pod]:
        """Report on pods.

        Keyword Args:
            filters (Mapping[str, str]): Criteria for listing pods. Available filters:

                - ctr-ids (List[str]): List of container ids to filter by.
                - ctr-names (List[str]): List of container names to filter by.
                - ctr-number (List[int]): list pods with given number of containers.
                - ctr-status (List[str]): List pods with containers in given state.
                  Legal values are: "created", "running", "paused", "stopped",
                  "exited", or "unknown"
                - id (str) - List pod with this id.
                - name (str) - List pod with this name.
                - status (List[str]): List pods in given state. Legal values are:
                  "created", "running", "paused", "stopped", "exited", or "unknown"
                - label (List[str]): List pods with given labels.
                - network (List[str]): List pods associated with given Network Ids (not Names).

        Raises:
            APIError: when an error returned by service
        """
        params = {"filters": api.prepare_filters(kwargs.get("filters"))}
        response = self.client.get("/pods/json", params=params)
        response.raise_for_status()
        return [self.prepare_model(attrs=i) for i in response.json()]

    def prune(self, filters: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Delete unused Pods.

        Returns:
            Dictionary Keys:
                - PodsDeleted (List[str]): List of pod ids deleted.
                - SpaceReclaimed (int): Always zero.

        Raises:
            APIError: when service reports error
        """
        response = self.client.post("/pods/prune", params={"filters": api.prepare_filters(filters)})
        response.raise_for_status()

        deleted: List[str] = []
        for item in response.json():
            if item["Err"] is not None:
                raise APIError(
                    item["Err"],
                    response=response,
                    explanation=f"""Failed to prune network '{item["Id"]}'""",
                )
            deleted.append(item["Id"])
        return {"PodsDeleted": deleted, "SpaceReclaimed": 0}

    def remove(self, pod_id: Union[Pod, str], force: Optional[bool] = None) -> None:
        """Delete pod.

        Args:
            pod_id: Identifier of Pod to delete.
            force: When True, stop and delete all containers in pod before deleting pod.

        Raises:
            NotFound: when pod not found
            APIError: when service reports an error

        Notes:
            Podman only.
        """
        if isinstance(pod_id, Pod):
            pod_id = pod_id.id

        response = self.client.delete(f"/pods/{pod_id}", params={"force": force})
        response.raise_for_status()

    def stats(self, **kwargs) -> Dict[str, Any]:
        """Resource usage statistics for the containers in pods.

        Keyword Args:
            all (bool): Provide statistics for all running pods.
            name (Union[str, List[str]]): Pods to include in report.

        Raises:
            NotFound: when pod not found
            APIError: when service reports an error
        """
        if "all" in kwargs and "name" in kwargs:
            raise ValueError("Keywords 'all' and 'name' are mutually exclusive.")

        params = {
            "all": kwargs.get("all"),
            "namesOrIDs": kwargs.get("name"),
        }
        response = self.client.get("/pods/stats", params=params)
        response.raise_for_status()
        return response.json()
