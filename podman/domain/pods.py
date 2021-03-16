"""Model and Manager for Pod resources.

Notes:
    See https://docs.podman.io/en/latest/_static/api.html#tag/pods
"""
from typing import Any, Dict, Tuple, Union

from podman.domain.manager import PodmanResource
from podman.errors import APIError, NotFound

_Timeout = Union[None, float, Tuple[float, float], Tuple[float, None]]


class Pod(PodmanResource):
    """Details and configuration for a pod managed by the Podman service."""

    @property
    def id(self):  # pylint: disable=invalid-name
        if "ID" in self.attrs:
            return self.attrs["ID"]

        if "Id" in self.attrs:
            return self.attrs["Id"]

        return None

    @property
    def name(self):
        """Returns name of pod."""
        if "Name" in self.attrs:
            return self.attrs["Name"]
        raise KeyError("'Name' attribute found.")

    def kill(self, signal: Union[str, int, None] = None) -> None:
        """Send signal to pod.

        Args:
            signal: To be sent to pod.

        Raises:
            NotFound when pod not found.
            APIError when service reports an error.
        """
        params = {"signal": signal}

        response = self.client.post(f"/pods/{self.id}/kill", params=params)
        if response.status_code == 200:
            return

        body = response.json()
        if response.status_code == 404:
            raise NotFound(body["cause"], response=response, explanation=body["message"])
        raise APIError(body["cause"], response=response, explanation=body["message"])

    def pause(self) -> None:
        """Pause pod.

        Raises:
            NotFound when pod not found.
            APIError when service reports an error.
        """
        response = self.client.post(f"/pods/{self.id}/pause")
        if response.status_code == 200:
            return

        body = response.json()
        if response.status_code == 404:
            raise NotFound(body["cause"], response=response, explanation=body["message"])
        raise APIError(body["cause"], response=response, explanation=body["message"])

    def remove(self, force=False) -> None:
        """Delete pod.

        Args:
            force: Stop and delete all containers in pod before deleting pod.

        Raises:
            NotFound when pod not found.
            APIError when service reports an error.
        """
        params = {"force": force}
        response = self.client.delete(f"/pods/{self.id}", params=params)
        if response.status_code == 200:
            return

        body = response.json()
        if response.status_code == 404:
            raise NotFound(body["cause"], response=response, explanation=body["message"])
        raise APIError(body["cause"], response=response, explanation=body["message"])

    def restart(self):
        """Restart pod.

        Raises:
            NotFound when pod not found.
            APIError when service reports an error.
        """
        response = self.client.post(f"/pods/{self.id}/restart")
        if response.status_code == 200:
            return

        body = response.json()
        if response.status_code == 404:
            raise NotFound(body["cause"], response=response, explanation=body["message"])
        raise APIError(body["cause"], response=response, explanation=body["message"])

    def start(self):
        """Start pod.

        Raises:
            NotFound when pod not found.
            APIError when service reports an error.
        """
        response = self.client.post(f"/pods/{self.id}/start")
        if response.status_code == 200:
            return

        body = response.json()
        if response.status_code == 404:
            raise NotFound(body["cause"], response=response, explanation=body["message"])
        raise APIError(body["cause"], response=response, explanation=body["message"])

    def stats(self, **kwargs) -> Dict[str, Any]:
        """Resource usage statistics for the containers in pods.

        Keyword Args:
            all (bool): Provide statistics for all running pods.
            name (Union[str, List[str]]): Pods to include in report.

        Raises:
            NotFound when pod not found.
            APIError when service reports an error.
        """
        params = dict() if kwargs is None else kwargs.copy()
        response = self.client.get("/pods/stats", params=params)
        body = response.json()

        if response.status_code == 200:
            return body

        if response.status_code == 404:
            raise NotFound(body["cause"], response=response, explanation=body["message"])
        raise APIError(body["cause"], response=response, explanation=body["message"])

    def stop(self, timeout: _Timeout = None) -> None:
        """Stop pod.

        Raises:
            NotFound when pod not found.
            APIError when service reports an error.
        """
        params = {"t": timeout}
        response = self.client.post(f"/pods/{self.id}/stop", params=params)
        body = response.json()

        if response.status_code == 200:
            return

        if response.status_code == 404:
            raise NotFound(body["cause"], response=response, explanation=body["message"])
        raise APIError(body["cause"], response=response, explanation=body["message"])

    def top(self, **kwargs) -> Dict[str, Any]:
        """Report on running processes in pod.

        Keyword Args:
            ps_args (str): Optional arguments passed to ps.

        Raises:
            NotFound when pod not found.
            APIError when service reports an error.
        """
        params = {
            "ps_args": kwargs.get("ps_args"),
            "stream": False,
        }
        response = self.client.get(f"/containers/{self.id}/top", params=params)
        body = response.json()

        if response.status_code == 200:
            return body

        if response.status_code == 404:
            raise NotFound(body["cause"], response=response, explanation=body["message"])
        raise APIError(body["cause"], response=response, explanation=body["message"])

    def unpause(self) -> None:
        """Unpause pod.

        Raises:
            NotFound when pod not found.
            APIError when service reports an error.
        """
        response = self.client.post(f"/pods/{self.id}/unpause")
        if response.status_code == 200:
            return

        body = response.json()
        if response.status_code == 404:
            raise NotFound(body["cause"], response=response, explanation=body["message"])
        raise APIError(body["cause"], response=response, explanation=body["message"])
