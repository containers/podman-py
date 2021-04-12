"""PodmanResource manager subclassed for Networks.

Notes:
    See https://docs.podman.io/en/latest/_static/api.html#tag/pods
"""
import json
import logging
from typing import Dict, List, Optional, Type, ClassVar, Any

import requests

from podman import api
from podman.domain.manager import Manager
from podman.domain.pods import Pod
from podman.errors import APIError, NotFound

logger = logging.getLogger("podman.pods")


class PodsManager(Manager):
    """Specialized Manager for Pod resources.

    Attributes:
        resource: Pod subclass of PodmanResource, factory method `prepare_model` will create these.
    """

    resource: ClassVar[Type[Pod]] = Pod

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

        if response.status_code == requests.codes.created:
            return self.get(body["Id"])

        raise APIError(body["cause"], response=response, explanation=body["message"])

    def exists(self, key: str) -> bool:
        """Returns True, when pod exists."""
        response = self.client.get(f"/pods/{key}/exists")
        return response.status_code == requests.codes.no_content

    # pylint is flagging 'pod_id' here vs. 'key' parameter in super.get()
    def get(self, pod_id: str) -> Pod:  # pylint: disable=arguments-differ
        """Return information for Pod by name or id.

        Args:
            pod_id: Pod name or id.

        Raises:
            NotFound: When network does not exist.
            APIError: When error returned by service.
        """
        response = self.client.get(f"/pods/{pod_id}/json")
        body = response.json()

        if response.status_code == requests.codes.okay:
            return self.prepare_model(attrs=body)

        if response.status_code == requests.codes.not_found:
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
        params = {"filters": api.prepare_filters(kwargs.get("filters"))}
        response = self.client.get("/pods/json", params=params)
        body = response.json()

        if response.status_code != requests.codes.okay:
            raise APIError(body["cause"], response=response, explanation=body["message"])

        pods: List[Pod] = list()
        for item in body:
            pods.append(self.prepare_model(attrs=item))
        return pods

    def prune(self, filters: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Delete unused Pods.

        Returns:
            Dictionary Keys:
                - PodsDeleted (List[str]): List of pod ids deleted.
                - SpaceReclaimed (int): Always zero.

        Raises:
            APIError when service reports error
        """
        response = self.client.post("/pods/prune", params={"filters": api.prepare_filters(filters)})
        body = response.json()

        if response.status_code != requests.codes.okay:
            raise APIError(body["cause"], response=response, explanation=body["message"])

        deleted: List[str] = list()
        for item in body:
            if item["Err"] is not None:
                raise APIError(
                    item["Err"],
                    response=response,
                    explanation=f"""Failed to prune network '{item["Id"]}'""",
                )
            deleted.append(item["Id"])
        return {"PodsDeleted": deleted, "SpaceReclaimed": 0}

    def stats(self, **kwargs) -> Dict[str, Any]:
        """Resource usage statistics for the containers in pods.

        Keyword Args:
            all (bool): Provide statistics for all running pods.
            name (Union[str, List[str]]): Pods to include in report.

        Raises:
            NotFound when pod not found.
            APIError when service reports an error.
        """
        if "all" in kwargs and "name" in kwargs:
            raise ValueError("Keywords 'all' and 'name' are mutually exclusive.")

        params = {
            "all": kwargs.get("all"),
            "namesOrIDs": kwargs.get("name"),
        }
        response = self.client.get("/pods/stats", params=params)
        body = response.json()

        if response.status_code == requests.codes.okay:
            return body

        if response.status_code == requests.codes.not_found:
            raise NotFound(body["cause"], response=response, explanation=body["message"])
        raise APIError(body["cause"], response=response, explanation=body["message"])
