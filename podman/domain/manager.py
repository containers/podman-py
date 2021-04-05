"""Base classes for PodmanResources and Manager's."""
from abc import ABC, abstractmethod
from typing import Any, ClassVar, Dict, List, Optional, Type, TypeVar, Union

from podman.api.client import APIClient

# Abstract methods use this Type when a sub-class of PodmanResource is expected.
PodmanResourceType = TypeVar("PodmanResourceType", bound="PodmanResource")


class PodmanResource(ABC):
    """Base class for representing resource of a Podman service.

    Attributes:
        attrs: Dictionary to carry attributes of resource from Podman service
    """

    def __init__(
        self,
        attrs: Optional[Dict[str, Any]] = None,
        client: Optional[APIClient] = None,
        collection: Optional["Manager"] = None,
    ):
        """Initialize base class for PodmanResource's.

        Args:
            attrs: Dictionary to carry attributes of resource from Podman service.
            client: Configured connection to a Podman service.
            collection: Manager of this category of resource
        """
        self.client = client

        # parameter named collection for compatibility
        self.manager = collection

        self.attrs = dict()
        if attrs is not None:
            self.attrs = attrs

    def __repr__(self):
        return f"<{self.__class__.__name__}: {self.short_id}>"

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.id == other.id

    def __hash__(self):
        return hash(f"{self.__class__.__name__}:{self.id}")

    @property
    def id(self) -> str:  # pylint: disable=invalid-name
        """Returns the identifier for the object."""
        return self.attrs.get("Id", None)

    @property
    def short_id(self) -> str:
        """Returns truncated identifier. 'sha256' preserved when included in the id.

        Notes:
            No attempt is made to ensure the returned value is
                semantically meaningful for all resources.
        """
        if self.id.startswith("sha256:"):
            return self.id[:17]
        return self.id[:10]

    def reload(self) -> None:
        """Refresh this object's data from the service."""
        latest = self.manager.get(self.id)
        self.attrs = latest.attrs


class Manager(ABC):
    """Base class for representing a Manager of resources for a Podman service.

    Attributes:
        resource: Subclass of PodmanResource this manager will operate upon.
    """

    resource: ClassVar[Type[PodmanResource]] = None

    @abstractmethod
    def exists(self, key: str) -> bool:
        """Returns True if resource exists.

        Note:
            This method does _not_ provide any mutex mechanism.
        """
        raise NotImplementedError()

    def __init__(self, client: APIClient = None) -> None:
        """Initialize Manager() object.

        Args:
            client: Podman client configured to connect to Podman service.
        """
        self.client = client

    @abstractmethod
    def get(self, key: str) -> PodmanResourceType:
        """Returns representation of resource."""
        raise NotImplementedError()

    @abstractmethod
    def list(self, **kwargs) -> List[PodmanResourceType]:
        """Returns list of resources."""
        raise NotImplementedError()

    def prepare_model(self, attrs: Union[PodmanResource, Dict[str, Any]]) -> PodmanResourceType:
        """ Create a model from a set of attributes. """
        if isinstance(attrs, PodmanResource):
            # Refresh existing PodmanResource.
            attrs.client = self.client
            attrs.collection = self
            return attrs

        if isinstance(attrs, dict):
            # Instantiate new PodmanResource from Dict[str, Any]
            # pylint: disable=not-callable
            return self.resource(attrs=attrs, client=self.client, collection=self)

        raise Exception("Can't create %s from %s" % (self.resource.__name__, attrs))
