"""Model and Manager for Network resources."""
from typing import List

from podman.api.client import APIClient
from podman.domain.manager import Manager, PodmanResource


class Network(PodmanResource):
    """Details and configuration for a networks managed by the Podman service."""


class NetworkManager(Manager):
    """Specialized Manager for Network resources."""

    # Abstract methods (create,get,list) are specialized and pylint cannot walk hierarchy.
    # pylint: disable=arguments-differ

    resource = Network

    def __init__(self, client: APIClient):
        """Instantiate """
        super().__init__(client)

    def list(self, *args, **kwargs) -> List[Network]:
        """Report on networks.

        Keyword Args:
            names (List[str]): List of names to filter by.
            ids (List[str]): List of ids to filter by.
            filters (Mapping[str,str]): Filters to be processed on the network list.
                Available filters:
                - ``driver=[<driver-name>]`` Matches a network's driver.
                - `label` (Union[str, List[str]]): format either ``"key"``, ``"key=value"``
                    or a list of such.
                - ``type=["custom"|"builtin"]`` Filters networks by type.
            greedy (bool): Fetch more details for each network individually.
                You might want this to get the containers attached to them.
        """
        _ = args
        _ = kwargs

    def get(self, network_id: str, *args, **kwargs) -> Network:
        """Return information for network network_id.

        Args:
            network_id: Network name or id.

        Raises:
            NotFound: Network does not exist.
            APIError: Error returned by service.
        """
        _ = network_id
        _ = args
        _ = kwargs

    def create(self, name: str, *args, **kwargs) -> Network:
        """Create a Network."""
        _ = name
        _ = args
        _ = kwargs
