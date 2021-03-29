"""PodmanResource manager subclassed for Networks.


Note:
    By default, most methods in this module uses the Podman compatible API rather than the
        libpod API as the results are so different.  To use the libpod API add the keyword argument
        compatible=False to any method call.
"""
import ipaddress
from contextlib import suppress
from typing import Any, Dict, List, Optional

import requests

import podman.api.http_utils
from podman import api
from podman.api import APIClient
from podman.domain.manager import Manager
from podman.domain.networks import Network
from podman.errors import APIError, NotFound


class NetworksManager(Manager):
    """Specialized Manager for Network resources."""

    resource = Network

    def __init__(self, client: APIClient):
        """Create NetworkManager.

        Args:
            client: Podman service client.
        """
        super().__init__(client)

    def list(self, **kwargs) -> List[Network]:
        """Report on networks.

        Keyword Args:
            names (List[str]): List of names to filter by.
            ids (List[str]): List of ids to filter by.
            filters (Mapping[str,str]): Criteria for listing networks.
                Available filters:
                - driver="bridge": Matches a network's driver. Only "bridge" is supported.
                - label=(Union[str, List[str]]): format either "key", "key=value"
                    or a list of such.
                - type=(str): Filters networks by type, legal values are:
                    - "custom"
                    - "builtin"
                - plugin=(List[str]]): Matches CNI plugins included in a network,
                    legal values are (Podman only):
                        - bridge
                        - portmap
                        - firewall
                        - tuning
                        - dnsname
                        - macvlan
            greedy (bool): Fetch more details for each network individually.
                You might want this to get the containers attached to them. (ignored)

        Raises:
            APIError: Error returned by service.
        """
        compatible = kwargs.get("compatible", True)

        filters = kwargs.get("filters", dict())
        filters["name"] = kwargs.get("names", None)
        filters["id"] = kwargs.get("ids", None)
        filters = api.prepare_filters(filters)

        params = {"filters": filters}
        path = f"/networks{'' if compatible else '/json'}"

        response = self.client.get(path, params=params, compatible=compatible)
        body = response.json()

        if response.status_code != 200:
            raise APIError(body["cause"], response=response, explanation=body["message"])

        nets: List[Network] = list()
        for item in body:
            nets.append(self.prepare_model(item))
        return nets

    # pylint is flagging 'network_id' here vs. 'key' parameter in super.get()
    def get(self, network_id: str, *_, **kwargs) -> Network:  # pylint: disable=arguments-differ
        """Return information for network network_id.

        Args:
            network_id: Network name or id.

        Keyword Args:
            compatible (bool): Should compatible API be used. Default: True

        Raises:
            NotFound: Network does not exist.
            APIError: Error returned by service.

        Note:
            The compatible API is used, this allows the server to provide dynamic fields.
                id is the most important example.
        """
        compatible = kwargs.get("compatible", True)

        path = f"/networks/{network_id}" + ("" if compatible else "/json")

        response = self.client.get(path, compatible=compatible)
        body = response.json()

        if response.status_code != 200:
            if response.status_code == 404:
                raise NotFound(body["cause"], response=response, explanation=body["message"])
            raise APIError(body["cause"], response=response, explanation=body["message"])

        if not compatible:
            body = body[0]

        return self.prepare_model(body)

    def create(self, name: str, **kwargs) -> Network:
        """Create a Network.

        Args:
            name: Name of network to be created

        Keyword Args:
            attachable (bool): Ignored, always False.
            check_duplicate (bool): Ignored, always False.
            disabled_dns (bool): When True, do not provision DNS for this network.
            driver (str): Which network driver to use when creating network.
            enable_ipv6 (bool): Enable IPv6 on the network.
            ingress (bool): Ignored, always False.
            internal (bool): Restrict external access to the network.
            ipam (IPAMConfig): Optional custom IP scheme for the network.
            labels (Dict[str, str]):  Map of labels to set on the network.
            macvlan (str):
            options (Dict[str, Any]): Driver options.
            scope (str): Ignored, always "local".

        Raises:
            APIError when Podman service reports an error
        """
        data = {
            "DisabledDNS": kwargs.get("disabled_dns"),
            "Driver": kwargs.get("driver"),
            "Internal": kwargs.get("internal"),
            "IPv6": kwargs.get("enable_ipv6"),
            "Labels": kwargs.get("labels"),
            "MacVLAN": kwargs.get("macvlan"),
            "Options": kwargs.get("options"),
        }

        with suppress(KeyError):
            ipam = kwargs["ipam"]
            if len(ipam["Config"]) > 0:

                if len(ipam["Config"]) > 1:
                    raise ValueError("Podman service only supports one IPAM config.")

                ip_config = ipam["Config"][0]
                data["Gateway"] = ip_config.get("Gateway")

                if "IPRange" in ip_config:
                    iprange = ipaddress.ip_network(ip_config["IPRange"])
                    iprange, mask = api.prepare_cidr(iprange)
                    data["Range"] = {
                        "IP": iprange,
                        "Mask": mask,
                    }

                if "Subnet" in ip_config:
                    subnet = ipaddress.ip_network(ip_config["Subnet"])
                    subnet, mask = api.prepare_cidr(subnet)
                    data["Subnet"] = {
                        "IP": subnet,
                        "Mask": mask,
                    }

        response = self.client.post(
            "/networks/create",
            params={"name": name},
            data=podman.api.http_utils.prepare_body(data),
            headers={"Content-Type": "application/json"},
        )
        data = response.json()

        if response.status_code != requests.codes.okay:
            raise APIError(data["cause"], response=response, explanation=data["message"])

        return self.get(network_id=name, **kwargs)

    def prune(self, filters: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
        """Delete unused Networks.

        Args:
            filters: Criteria for selecting volumes to delete. Ignored.


        Keyword Args:
            compatible (bool): Should compatible API be used. Default: True

        Raises:
            APIError when service reports error

        Notes:
            SpaceReclaimed always reported as 0
        """
        compatible = kwargs.get("compatible", True)

        response = self.client.post(
            "/networks/prune", filters=api.prepare_filters(filters), compatible=compatible
        )
        body = response.json()

        if response.status_code != 200:
            raise APIError(body["cause"], response=response, explanation=body["message"])

        if compatible:
            return body

        deleted = list()
        for item in body:
            if item["Error"] is not None:
                raise APIError(
                    item["Error"],
                    response=response,
                    explanation=f"""Failed to prune network '{item["Name"]}'""",
                )
            deleted.append(item["Name"])

        return {"NetworksDeleted": deleted, "SpaceReclaimed": 0}
