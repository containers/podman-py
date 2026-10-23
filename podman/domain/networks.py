"""Model for Network resources.

Example:

    with PodmanClient(base_url="unix:///run/user/1000/podman/podman.sock") as client:
        net = client.networks.get("db_network")
            print(net.name, "\n")
"""

import hashlib
import json
import logging
from contextlib import suppress
from typing import Any, Optional, Union, TYPE_CHECKING

from podman import api
from podman.domain.containers import Container
from podman.domain.containers_manager import ContainersManager
from podman.domain.manager import PodmanResource

if TYPE_CHECKING:
    from podman.domain.networks_manager import NetworksManager

logger = logging.getLogger("podman.networks")


class Network(PodmanResource):
    """Details and configuration for a networks managed by the Podman service.

    Attributes:
        attrs (dict[str, Any]): Attributes of Network reported from Podman service
    """

    manager: "NetworksManager"

    @property
    def id(self):  # pylint: disable=invalid-name
        """str: Returns the identifier of the network."""
        if "Id" in self.attrs:
            return self.attrs["Id"]

        if "id" in self.attrs:
            return self.attrs["id"]

        with suppress(KeyError):
            sha256 = hashlib.sha256(self.attrs["name"].encode("ascii"))
            return sha256.hexdigest()

        return None

    @property
    def containers(self):
        """list[Container]: Returns list of Containers connected to network."""
        with suppress(KeyError):
            container_manager = ContainersManager(client=self.client)
            return [container_manager.get(ident) for ident in self.attrs["containers"].keys()]
        return []

    @property
    def name(self):
        """str: Returns the name of the network."""

        if "Name" in self.attrs:
            return self.attrs["Name"]

        if "name" in self.attrs:
            return self.attrs["name"]

        raise KeyError("Neither 'name' or 'Name' attribute found.")

    def reload(self):
        """Refresh this object's data from the service."""
        latest = self.manager.get(self.name)
        self.attrs = latest.attrs

    def connect(self, container: Union[str, Container], *_, **kwargs) -> None:
        """Connect given container to this network.

        Args:
            container: To add to this Network

        Keyword Args:
            aliases (list[str]): Aliases to add for this endpoint
            compatible (bool): Use the Docker compatible endpoint. Default: False
            driver_opt (dict[str, str]): Options to provide to network driver
            interface_name (str): Name of the interface inside the container (e.g. eth1).
                Podman only.
            ipv4_address (str): IPv4 address for given Container on this network
            ipv6_address (str): IPv6 address for given Container on this network
            link_local_ips (list[str]): list of link-local addresses. Only used when
                compatible=True.
            links (list[Union[str, Containers]]): Ignored
            mac_address (str): Static MAC address for given Container on this network.
                Podman only.

        Raises:
            APIError: when Podman service reports an error
        """
        if isinstance(container, Container):
            container = container.id

        data: dict[str, Any]
        if not kwargs.get("compatible"):
            # The libpod endpoint expects the container and libpod's per-network options at
            # the top level of the body, as podman's own bindings send them.
            data = {
                "container": container,
                "aliases": kwargs.get("aliases"),
                "interface_name": kwargs.get("interface_name"),
                "options": kwargs.get("driver_opt"),
                "static_ips": [kwargs.get("ipv4_address"), kwargs.get("ipv6_address")],
                "static_mac": kwargs.get("mac_address"),
            }
        else:
            # Static addresses are read from IPAMConfig by both Docker and podman's
            # compat handler.
            data = {
                "Container": container,
                "EndpointConfig": {
                    "Aliases": kwargs.get("aliases"),
                    "DriverOpts": kwargs.get("driver_opt"),
                    "IPAMConfig": {
                        "IPv4Address": kwargs.get("ipv4_address"),
                        "IPv6Address": kwargs.get("ipv6_address"),
                        "Links": kwargs.get("link_local_ips"),
                    },
                    "Links": kwargs.get("link_local_ips"),
                    "NetworkID": self.id,
                },
            }

        response = self.api.post(
            f"/networks/{self.name}/connect",
            data=api.prepare_body(data),
            headers={"Content-type": "application/json"},
            **kwargs,
        )
        response.raise_for_status()

    def disconnect(self, container: Union[str, Container], **kwargs) -> None:
        """Disconnect given container from this network.

        Args:
            container: To remove from this Network

        Keyword Args:
            force (bool): Force operation

        Raises:
            APIError: when Podman service reports an error
        """
        if isinstance(container, Container):
            container = container.id

        data = {"Container": container, "Force": kwargs.get("force")}
        response = self.api.post(f"/networks/{self.name}/disconnect", data=json.dumps(data))
        response.raise_for_status()

    def remove(self, force: Optional[bool] = None, **kwargs) -> None:
        """Remove this network.

        Args:
            force: Remove network and any associated containers

        Raises:
            APIError: when Podman service reports an error
        """
        self.manager.remove(self.name, force=force, **kwargs)
