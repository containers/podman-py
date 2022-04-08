"""PodmanResource manager subclassed for Network resources.

Classes and methods for manipulating network resources via Podman API service.

Example:

    with PodmanClient(base_url="unix:///run/user/1000/podman/podman.sock") as client:
        for net in client.networks.list():
            print(net.id, "\n")
"""
import ipaddress
import logging
import sys
from contextlib import suppress
from typing import Any, Dict, List, Optional

from podman import api
from podman.api import http_utils
from podman.domain.manager import Manager
from podman.domain.networks import Network
from podman.errors import APIError

logger = logging.getLogger("podman.networks")


class NetworksManager(Manager):
    """Specialized Manager for Network resources."""

    @property
    def resource(self):
        """Type[Network]: prepare_model() will create Network classes."""
        return Network

    def create(self, name: str, **kwargs) -> Network:
        """Create a Network resource.

        Args:
            name: Name of network to be created

        Keyword Args:
            attachable (bool): Ignored, always False.
            check_duplicate (bool): Ignored, always False.
            dns_enabled (bool): When True, do not provision DNS for this network.
            driver (str): Which network driver to use when creating network.
            enable_ipv6 (bool): Enable IPv6 on the network.
            ingress (bool): Ignored, always False.
            internal (bool): Restrict external access to the network.
            ipam (IPAMConfig): Optional custom IP scheme for the network.
            labels (Dict[str, str]):  Map of labels to set on the network.
            options (Dict[str, Any]): Driver options.
            scope (str): Ignored, always "local".

        Raises:
            APIError: when Podman service reports an error
        """
        data = {
            "name": name,
            "driver": kwargs.get("driver"),
            "dns_enabled": kwargs.get("dns_enabled"),
            "subnets": kwargs.get("subnets"),
            "ipv6_enabled": kwargs.get("enable_ipv6"),
            "internal": kwargs.get("internal"),
            "labels": kwargs.get("labels"),
            "options": kwargs.get("options"),
        }

        with suppress(KeyError):
            self._prepare_ipam(data, kwargs["ipam"])

        response = self.client.post(
            "/networks/create",
            data=http_utils.prepare_body(data),
            headers={"Content-Type": "application/json"},
        )
        response.raise_for_status()
        sys.stderr.write(str(response.json()))
        return self.prepare_model(attrs=response.json())

    def _prepare_ipam(self, data: Dict[str, Any], ipam: Dict[str, Any]):
        if "Config" not in ipam:
            return

        data["subnets"] = []
        for cfg in ipam["Config"]:
            subnet = {
                "gateway": cfg.get("Gateway"),
                "subnet": cfg.get("Subnet"),
            }

            with suppress(KeyError):
                net = ipaddress.ip_network(cfg["IPRange"])
                subnet["lease_range"] = {
                    "start_ip": str(net[1]),
                    "end_ip": str(net[-2]),
                }

            data["subnets"].append(subnet)

    def exists(self, key: str) -> bool:
        response = self.client.get(f"/networks/{key}/exists")
        return response.ok

    def get(self, key: str) -> Network:
        """Return information for the network_id.

        Args:
            key: Network name or id.

        Raises:
            NotFound: when Network does not exist
            APIError: when error returned by service
        """
        response = self.client.get(f"/networks/{key}")
        response.raise_for_status()

        return self.prepare_model(attrs=response.json())

    def list(self, **kwargs) -> List[Network]:
        """Report on networks.

        Keyword Args:
            names (List[str]): List of names to filter by.
            ids (List[str]): List of identifiers to filter by.
            filters (Mapping[str,str]): Criteria for listing networks. Available filters:

                - driver="bridge": Matches a network's driver. Only "bridge" is supported.
                - label=(Union[str, List[str]]): format either "key", "key=value"
                  or a list of such.
                - type=(str): Filters networks by type, legal values are:

                    - "custom"
                    - "builtin"

                - plugin=(List[str]]): Matches CNI plugins included in a network, legal
                  values are (Podman only):

                        - bridge
                        - portmap
                        - firewall
                        - tuning
                        - dnsname
                        - macvlan

            greedy (bool): Fetch more details for each network individually.
                You might want this to get the containers attached to them. Ignored.

        Raises:
            APIError: when error returned by service
        """
        filters = kwargs.get("filters", {})
        filters["name"] = kwargs.get("names")
        filters["id"] = kwargs.get("ids")
        filters = api.prepare_filters(filters)

        params = {"filters": filters}
        response = self.client.get("/networks/json", params=params)
        response.raise_for_status()

        return [self.prepare_model(i) for i in response.json()]

    def prune(
        self, filters: Optional[Dict[str, Any]] = None
    ) -> Dict[api.Literal["NetworksDeleted", "SpaceReclaimed"], Any]:
        """Delete unused Networks.

        SpaceReclaimed always reported as 0

        Args:
            filters: Criteria for selecting volumes to delete. Ignored.

        Raises:
            APIError: when service reports error
        """
        response = self.client.post("/networks/prune", filters=api.prepare_filters(filters))
        response.raise_for_status()

        deleted: List[str] = []
        for item in response.json():
            if item["Error"] is not None:
                raise APIError(
                    item["Error"],
                    response=response,
                    explanation=f"""Failed to prune network '{item["Name"]}'""",
                )
            deleted.append(item["Name"])

        return {"NetworksDeleted": deleted, "SpaceReclaimed": 0}

    def remove(self, name: [Network, str], force: Optional[bool] = None) -> None:
        """Remove Network resource.

        Args:
            name: Identifier of Network to delete.
            force: Remove network and any associated containers

        Raises:
            APIError: when Podman service reports an error
        """
        if isinstance(name, Network):
            name = name.name

        response = self.client.delete(f"/networks/{name}", params={"force": force})
        response.raise_for_status()
