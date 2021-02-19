"""Base classes for PodmanResources and Manager's."""
from abc import ABC, abstractmethod
from typing import Any, ClassVar, Dict, List, Type, Union

from podman.api.client import APIClient


class PodmanResource(ABC):
    """Base class for representing resource of a Podman service."""

    def __init__(self, attrs: dict = None, client: APIClient = None, collection: 'Manager' = None):
        self.client = client

        # parameter named collection for compatibility
        self.manager = collection

        self.attrs = {}
        if attrs is not None:
            self.attrs = attrs

    def __repr__(self):
        return f"<{self.__class__.__name__}: {self.short_id}>"

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.id == other.id

    def __hash__(self):
        return hash(f"{self.__class__.__name__}:{self.id}")

    @property
    def id(self):  # pylint: disable=invalid-name
        """The ID of the object."""
        return self.attrs.get("Id")

    @property
    def short_id(self):
        """The ID of the object, truncated to 10 characters."""
        return self.id[:10]

    def reload(self):
        """Refresh this object's data from the service."""
        latest = self.manager.get(self.id)
        self.attrs = latest.attrs


class Manager(ABC):
    """Base class for representing a Manager of resources for a Podman service."""

    resource: ClassVar[Type[PodmanResource]] = None
    model = resource

    def __init__(self, client: APIClient = None) -> None:
        """Initialize Manager() object.
        Args:
            client: Podman client configured to connect to Podman service.
        """
        self.client = client

    @abstractmethod
    def list(self) -> List[PodmanResource]:
        """Returns list of resources."""
        raise NotImplementedError()

    @abstractmethod
    def get(self, key: str) -> PodmanResource:
        """Returns representation of resource."""
        raise NotImplementedError()

    @abstractmethod
    def create(self, *args, **kwargs) -> PodmanResource:
        """Creates resource via Podman service and return representation.

        Notes:
            TODO method signature should use Annotated[] requires 3.9
        """
        raise NotImplementedError()

    def prepare_model(
        self, attrs: Union[PodmanResource, Dict[str, Any]]
    ) -> Union[None, PodmanResource, List[PodmanResource], bytes]:
        """ Create a model from a set of attributes. """
        if isinstance(attrs, PodmanResource):
            # Refresh existing PodmanResource.
            attrs.client = self.client
            attrs.collection = self
            return attrs

        if isinstance(attrs, dict):
            # Instantiate PodmanResource from Dict[str, Any]
            # pylint: disable=not-callable
            return self.resource(attrs=attrs, client=self.client, collection=self)

        raise Exception("Can't create %s from %s" % (self.resource.__name__, attrs))
