"""Model and Manager for Pod resources."""
import logging
from typing import Any, Dict, Optional, Tuple, Union

from podman.domain.manager import PodmanResource

_Timeout = Union[None, float, Tuple[float, float], Tuple[float, None]]

logger = logging.getLogger("podman.pods")


class Pod(PodmanResource):
    """Details and configuration for a pod managed by the Podman service."""

    @property
    def id(self):  # pylint: disable=invalid-name
        return self.attrs.get("ID", self.attrs.get("Id"))

    @property
    def name(self):
        """str: Returns name of pod."""
        return self.attrs.get("Name")

    def kill(self, signal: Union[str, int, None] = None) -> None:
        """Send signal to pod.

        Args:
            signal: To be sent to pod.

        Raises:
            NotFound: when pod not found
            APIError: when service reports an error
        """
        response = self.client.post(f"/pods/{self.id}/kill", params={"signal": signal})
        response.raise_for_status()

    def pause(self) -> None:
        """Pause pod.

        Raises:
            NotFound: when pod not found
            APIError: when service reports an error
        """
        response = self.client.post(f"/pods/{self.id}/pause")
        response.raise_for_status()

    def remove(self, force: Optional[bool] = None) -> None:
        """Delete pod.

        Args:
            force: When True, stop and delete all containers in pod before deleting pod.

        Raises:
            NotFound: when pod not found
            APIError: when service reports an error
        """
        self.manager.remove(self.id, force=force)

    def restart(self) -> None:
        """Restart pod.

        Raises:
            NotFound: when pod not found
            APIError: when service reports an error
        """
        response = self.client.post(f"/pods/{self.id}/restart")
        response.raise_for_status()

    def start(self) -> None:
        """Start pod.

        Raises:
            NotFound: when pod not found
            APIError: when service reports an error
        """
        response = self.client.post(f"/pods/{self.id}/start")
        response.raise_for_status()

    def stop(self, timeout: _Timeout = None) -> None:
        """Stop pod.

        Raises:
            NotFound: when pod not found
            APIError: when service reports an error
        """
        params = {"t": timeout}
        response = self.client.post(f"/pods/{self.id}/stop", params=params)
        response.raise_for_status()

    def top(self, **kwargs) -> Dict[str, Any]:
        """Report on running processes in pod.

        Keyword Args:
            ps_args (str): Optional arguments passed to ps.

        Raises:
            NotFound: when pod not found
            APIError: when service reports an error
        """
        params = {
            "ps_args": kwargs.get("ps_args"),
            "stream": False,
        }
        response = self.client.get(f"/pods/{self.id}/top", params=params)
        response.raise_for_status()

        if len(response.text) == 0:
            return {"Processes": [], "Titles": []}
        return response.json()

    def unpause(self) -> None:
        """Unpause pod.

        Raises:
            NotFound: when pod not found
            APIError: when service reports an error
        """
        response = self.client.post(f"/pods/{self.id}/unpause")
        response.raise_for_status()
