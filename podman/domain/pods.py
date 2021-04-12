"""Model and Manager for Pod resources.

Notes:
    See https://docs.podman.io/en/latest/_static/api.html#tag/pods
"""
import logging
from typing import Any, Dict, Tuple, Union, Optional

import requests

from podman.domain.manager import PodmanResource
from podman.errors import APIError, NotFound

_Timeout = Union[None, float, Tuple[float, float], Tuple[float, None]]

logger = logging.getLogger("podman.pods")


class Pod(PodmanResource):
    """Details and configuration for a pod managed by the Podman service."""

    @property
    def id(self) -> str:  # pylint: disable=invalid-name
        return self.attrs.get("ID", self.attrs.get("Id"))

    @property
    def name(self) -> str:
        """Returns name of pod."""
        return self.attrs.get("Name")

    def kill(self, signal: Union[str, int, None] = None) -> None:
        """Send signal to pod.

        Args:
            signal: To be sent to pod.

        Raises:
            NotFound when pod not found.
            APIError when service reports an error.
        """
        response = self.client.post(f"/pods/{self.id}/kill", params={"signal": signal})
        if response.status_code == requests.codes.okay:
            return

        body = response.json()
        if response.status_code == requests.codes.not_found:
            raise NotFound(body["cause"], response=response, explanation=body["message"])
        raise APIError(body["cause"], response=response, explanation=body["message"])

    def pause(self) -> None:
        """Pause pod.

        Raises:
            NotFound when pod not found.
            APIError when service reports an error.
        """
        response = self.client.post(f"/pods/{self.id}/pause")
        if response.status_code == requests.codes.okay:
            return

        body = response.json()
        if response.status_code == requests.codes.not_found:
            raise NotFound(body["cause"], response=response, explanation=body["message"])
        raise APIError(body["cause"], response=response, explanation=body["message"])

    def remove(self, force: Optional[bool] = None) -> None:
        """Delete pod.

        Args:
            force: When True, stop and delete all containers in pod before deleting pod.

        Raises:
            NotFound when pod not found.
            APIError when service reports an error.
        """
        response = self.client.delete(f"/pods/{self.id}", params={"force": force})
        if response.status_code == requests.codes.okay:
            return

        body = response.json()
        if response.status_code == requests.codes.not_found:
            raise NotFound(body["cause"], response=response, explanation=body["message"])
        raise APIError(body["cause"], response=response, explanation=body["message"])

    def restart(self):
        """Restart pod.

        Raises:
            NotFound when pod not found.
            APIError when service reports an error.
        """
        response = self.client.post(f"/pods/{self.id}/restart")
        if response.status_code == requests.codes.okay:
            return

        body = response.json()
        if response.status_code == requests.codes.not_found:
            raise NotFound(body["cause"], response=response, explanation=body["message"])
        raise APIError(body["cause"], response=response, explanation=body["message"])

    def start(self):
        """Start pod.

        Raises:
            NotFound when pod not found.
            APIError when service reports an error.
        """
        response = self.client.post(f"/pods/{self.id}/start")
        if response.status_code in (requests.codes.okay, requests.codes.not_modified):
            return

        body = response.json()
        if response.status_code == requests.codes.not_found:
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
        if response.status_code in (requests.codes.okay, requests.codes.not_modified):
            return

        body = response.json()
        if response.status_code == requests.codes.not_found:
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
        response = self.client.get(f"/pods/{self.id}/top", params=params)
        body = response.json()

        if response.status_code == requests.codes.okay:
            return body

        if response.status_code == requests.codes.not_found:
            raise NotFound(body["cause"], response=response, explanation=body["message"])
        raise APIError(body["cause"], response=response, explanation=body["message"])

    def unpause(self) -> None:
        """Unpause pod.

        Raises:
            NotFound when pod not found.
            APIError when service reports an error.
        """
        response = self.client.post(f"/pods/{self.id}/unpause")
        if response.status_code == requests.codes.okay:
            return

        body = response.json()
        if response.status_code == requests.codes.not_found:
            raise NotFound(body["cause"], response=response, explanation=body["message"])
        raise APIError(body["cause"], response=response, explanation=body["message"])
