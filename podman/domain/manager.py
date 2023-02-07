"""Base classes for PodmanResources and Manager's."""
from abc import ABC, abstractmethod
from collections import abc
from typing import Any, List, Mapping, Optional, TypeVar, Union

from podman.api.client import APIClient

# Methods use this Type when a subclass of PodmanResource is expected.
PodmanResourceType: TypeVar = TypeVar("PodmanResourceType", bound="PodmanResource")


class PodmanResource(ABC):
    """Base class for representing resource of a Podman service.

    Attributes:
        attrs: Mapping of attributes for resource from Podman service
    """

    def __init__(
        self,
        attrs: Optional[Mapping[str, Any]] = None,
        client: Optional[APIClient] = None,
        collection: Optional["Manager"] = None,
    ):
        """Initialize base class for PodmanResource's.

        Args:
            attrs: Mapping of attributes for resource from Podman service.
            client: Configured connection to a Podman service.
            collection: Manager of this category of resource, named `collection` for compatibility
        """
        super().__init__()
        self.client = client
        self.manager = collection

        self.attrs = {}
        if attrs is not None:
            self.attrs.update(attrs)

    def __repr__(self):
        return f"<{self.__class__.__name__}: {self.short_id}>"

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.id == other.id

    def __hash__(self):
        return hash(f"{self.__class__.__name__}:{self.id}")

    @property
    def id(self):  # pylint: disable=invalid-name
        """str: Returns the identifier for the object."""
        return self.attrs.get("Id")

    @property
    def short_id(self):
        """str: Returns truncated identifier. 'sha256' preserved when included in the id.

        No attempt is made to ensure the returned value is semantically meaningful
        for all resources.
        """
        if self.id.startswith("sha256:"):
            return self.id[:17]
        return self.id[:10]

    def reload(self) -> None:
        """Refresh this object's data from the service."""
        latest = self.manager.get(self.id)
        self.attrs = latest.attrs


class Manager(ABC):
    """Base class for representing a Manager of resources for a Podman service."""

    @property
    @abstractmethod
    def resource(self):
        """Type[PodmanResource]: Class which the factory method prepare_model() will use."""

    def __init__(self, client: APIClient = None) -> None:
        """Initialize Manager() object.

        Args:
            client: APIClient() configured to connect to Podman service.
        """
        super().__init__()
        self.client = client

    @abstractmethod
    def exists(self, key: str) -> bool:
        """Returns True if resource exists.

        Podman only.

        Notes:
            This method does _not_ provide any mutex mechanism.
        """

    @abstractmethod
    def get(self, key: str) -> PodmanResourceType:
        """Returns representation of resource."""

    @abstractmethod
    def list(self, **kwargs) -> List[PodmanResourceType]:
        """Returns list of resources."""

    def prepare_model(self, attrs: Union[PodmanResource, Mapping[str, Any]]) -> PodmanResourceType:
        """Create a model from a set of attributes."""

        # Refresh existing PodmanResource.
        if isinstance(attrs, PodmanResource):
            attrs.client = self.client
            attrs.collection = self
            return attrs

        # Instantiate new PodmanResource from Mapping[str, Any]
        if isinstance(attrs, abc.Mapping):
            # TODO Determine why pylint is reporting typing.Type not callable
            # pylint: disable=not-callable
            return self.resource(attrs=attrs, client=self.client, collection=self)

        # pylint: disable=broad-exception-raised
        raise Exception(f"Can't create {self.resource.__name__} from {attrs}")
