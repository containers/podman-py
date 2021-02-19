"""Model and Manager for Event resources."""
from typing import List

from podman.api.client import APIClient
from podman.domain.manager import Manager, PodmanResource


class Event(PodmanResource):
    """Details and configuration for a event managed by the Podman service."""


class EventManager(Manager):
    """Specialized Manager for Event resources."""

    # Abstract methods (create,get,list) are specialized and pylint cannot walk hierarchy.
    # pylint: disable=arguments-differ

    resource = Event

    def __init__(self, client: APIClient) -> None:
        """Initiate EventManager object.

        Args:
            client: Connection to Podman service.
        """
        super().__init__(client)

    def list(self) -> List[Event]:
        """Report on networks."""

    def get(self, event_id: str) -> Event:
        """Get event by name or id.

        Args:
            event_id: Event name or id.

        Raises:
            NotFound: Event does not exist.
            APIError: Error return by service.
        """
        _ = event_id

    def create(self, *args, **kwargs) -> Event:
        """Create an Event."""

    def apply(self, *args, **kwargs) -> object:
        """TBD."""
