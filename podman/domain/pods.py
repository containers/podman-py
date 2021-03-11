"""Model and Manager for Pod resources."""
from typing import Any, Dict, List, Optional, Tuple, Union

from podman import api
from podman.api.client import APIClient
from podman.domain.manager import Manager, PodmanResource
from podman.errors import APIError

_Timeout = Union[None, float, Tuple[float, float], Tuple[float, None]]


class Pod(PodmanResource):
    """Details and configuration for a pod managed by the Podman service."""

    def kill(self, signal: Union[str, int, None] = None):
        """Send signal to pod.

        Args:
            signal: to be sent to pod
        """
        params = dict()
        if signal is not None:
            params["signal"] = signal

    def pause(self):
        """Pause pod."""

    def remove(self, force=False) -> None:
        """Delete pod.

        Args:
            force: Stop and delete all containers in pod before deleting pod

        """

    def restart(self):
        """Restart pod."""

    def start(self):
        """Start pod."""

    def stats(self):
        """Resource usage statistics for the containers in pods."""

    def stop(self, timeout: _Timeout = None):
        """Stop pod"""

    def top(self, **kwargs) -> Dict[str, Any]:
        """Report on running processes in pod.

        Keyword Args:
            ps_args (str): Optional arguments passed to ps
        """

    def unpause(self):
        """Unpause pod."""


class PodsManager(Manager):
    """Specialized Manager for Pod resources."""

    resource = Pod

    def __init__(self, client: APIClient):
        """Initiate PodManager object.

        Args:
            client: Connection to Podman service.
        """
        super().__init__(client)

    def create(self, name: str, *args, **kwargs) -> Pod:
        """Create a Pod."""

    # pylint is flagging 'pod_id' here vs. 'key' parameter in super.get()
    def get(self, pod_id: str) -> Pod:  # pylint: disable=arguments-differ
        """Returns and image by name or id.

        Args:
            pod_id: Image id or name for which to search
        """
        _ = pod_id
        self.prepare_model(dict())

    def list(self, **kwargs) -> List[Pod]:
        """Report on pods."""

    def prune(self, filters: Optional[Dict[str, str]] = None):
        """Delete unused Pods."""
        response = self.client.post("/pods/prune", params={"filters": api.format_filters(filters)})
        if response.status_code == 200:
            return

        body = response.json()
        raise APIError(body["cause"], response=response, explanation=body["message"])
