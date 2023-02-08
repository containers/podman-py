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
from typing import Optional, Union

from podman.domain.containers import Container
from podman.domain.containers_manager import ContainersManager
from podman.domain.manager import PodmanResource

logger = logging.getLogger("podman.networks")


class Network(PodmanResource):
    """Details and configuration for a networks managed by the Podman service.

    Attributes:
        attrs (Dict[str, Any]): Attributes of Network reported from Podman service
    """

    @property
    def id(self):  # pylint: disable=invalid-name
        """str: Returns the identifier of the network."""
        with suppress(KeyError):
            return self.attrs["Id"]

        with suppress(KeyError):
            sha256 = hashlib.sha256(self.attrs["name"].encode("ascii"))
            return sha256.hexdigest()

        return None

    @property
    def containers(self):
        """List[Container]: Returns list of Containers connected to network."""
        with suppress(KeyError):
            container_manager = ContainersManager(client=self.client)
            return [container_manager.get(ident) for ident in self.attrs["Containers"].keys()]
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
            aliases (List[str]): Aliases to add for this endpoint
            driver_opt (Dict[str, Any]): Options to provide to network driver
            ipv4_address (str): IPv4 address for given Container on this network
            ipv6_address (str): IPv6 address for given Container on this network
            link_local_ips (List[str]): list of link-local addresses
            links (List[Union[str, Containers]]): Ignored

        Raises:
            APIError: when Podman service reports an error
        """
        if isinstance(container, Container):
            container = container.id

        # TODO Talk with baude on which IPAddress field is needed...
        ipam = {
            "IPv4Address": kwargs.get('ipv4_address'),
            "IPv6Address": kwargs.get('ipv6_address'),
            "Links": kwargs.get("link_local_ips"),
        }
        ipam = {k: v for (k, v) in ipam.items() if not (v is None or len(v) == 0)}

        endpoint_config = {
            "Aliases": kwargs.get("aliases"),
            "DriverOpts": kwargs.get("driver_opt"),
            "IPAddress": kwargs.get("ipv4_address", kwargs.get("ipv6_address")),
            "IPAMConfig": ipam,
            "Links": kwargs.get("link_local_ips"),
            "NetworkID": self.id,
        }
        endpoint_config = {
            k: v for (k, v) in endpoint_config.items() if not (v is None or len(v) == 0)
        }

        data = {"Container": container, "EndpointConfig": endpoint_config}
        data = {k: v for (k, v) in data.items() if not (v is None or len(v) == 0)}

        response = self.client.post(
            f"/networks/{self.name}/connect",
            data=json.dumps(data),
            headers={"Content-type": "application/json"},
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
        response = self.client.post(f"/networks/{self.name}/disconnect", data=json.dumps(data))
        response.raise_for_status()

    def remove(self, force: Optional[bool] = None, **kwargs) -> None:
        """Remove this network.

        Args:
            force: Remove network and any associated containers

        Raises:
            APIError: when Podman service reports an error
        """
        self.manager.remove(self.name, force=force, **kwargs)
