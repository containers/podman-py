"""PodmanResource manager subclassed for Networks.

Notes:
    See https://docs.podman.io/en/latest/_static/api.html#tag/pods
"""
import json
from typing import Dict, List, Optional

from podman import api
from podman.api import APIClient
from podman.domain.manager import Manager
from podman.domain.pods import Pod
from podman.errors import APIError, NotFound


class PodsManager(Manager):
    """Specialized Manager for Pod resources."""

    resource = Pod

    def __init__(self, client: APIClient):
        """Initiate PodManager object.

        Args:
            client: Connection to Podman service.
        """
        super().__init__(client)

    def create(self, name: str, **kwargs) -> Pod:
        """Create a Pod.

        Keyword Args:
            See (API documentation)[
                https://docs.podman.io/en/latest/_static/api.html#operation/CreatePod] for
                complete list of keywords.
        """
        data = dict() if kwargs is None else kwargs.copy()
        data["name"] = name

        response = self.client.post("/pods/create", data=json.dumps(data))
        body = response.json()

        if response.status_code != 200:
            raise APIError(body["cause"], response=response, explanation=body["message"])

        return self.prepare_model(self.get(body["Id"]))

    # pylint is flagging 'pod_id' here vs. 'key' parameter in super.get()
    def get(self, pod_id: str) -> Pod:  # pylint: disable=arguments-differ
        """Return information for Pod by name or id.

        Args:
            pod_id: Pod name or id.

        Raises:
            NotFound: Network does not exist.
            APIError: Error returned by service.
        """
        response = self.client.get(f"/pods/{pod_id}/json")
        body = response.json()

        if response.status_code == 200:
            return self.prepare_model(body)

        if response.status_code == 404:
            raise NotFound(body["cause"], response=response, explanation=body["message"])
        raise APIError(body["cause"], response=response, explanation=body["message"])

    def list(self, **kwargs) -> List[Pod]:
        """Report on pods.

        Keyword Args:
            filters (Mapping[str, str]): Criteria for listing pods. Available filters:
                - ctr-ids (List[str]): List of container ids to filter by.
                - ctr-names (List[str]): List of container names to filter by.
                - ctr-number (List[int]): list pods with given number of containers.
                - ctr-status (List[str]): List pods with containers in given state.
                    Legal values are: "created", "running", "paused",
                    "stopped", "exited", "unknown"
                - id (str) - List pod with this id.
                - name (str) - List pod with this name.
                - status (List[str]): List pods in given state. Legal values are: "created",
                    "running", "paused", "stopped", "exited", "unknown"
                - label (List[str]): List pods with given labels.
                - network (List[str]): List pods associated with given Network Ids (not Names).

        Raises:
            APIError: Error returned by service.
        """
        params = {"filters": kwargs.get("filters")}
        response = self.client.get("/pods/json", params=api.prepare_filters(params))
        body = response.json()

        if response.status_code != 200:
            raise APIError(body["cause"], response=response, explanation=body["message"])

        pods: List[Pod] = list()
        for item in body:
            pods.append(self.prepare_model(item))
        return pods

    def prune(self, filters: Optional[Dict[str, str]] = None):
        """Delete unused Pods.

        Raises:
            APIError when service reports error

        Notes:
            SpaceReclaimed always reported as 0
        """
        response = self.client.post("/pods/prune", params={"filters": api.prepare_filters(filters)})
        body = response.json()

        if response.status_code != 200:
            raise APIError(body["cause"], response=response, explanation=body["message"])

        deleted = list()
        for item in body:
            if item["Err"] is not None:
                raise APIError(
                    item["Err"],
                    response=response,
                    explanation=f"""Failed to prune network '{item["Id"]}'""",
                )
            deleted.append(item["Id"])
        return {"PodsDeleted": deleted, "SpaceReclaimed": 0}
