"""Model and Manager for Secrets resources."""
from contextlib import suppress
from typing import Any, List, Mapping, Optional, Union

from podman.api import APIClient
from podman.domain.manager import Manager, PodmanResource


class Secret(PodmanResource):
    """Details and configuration for a secret registered with the Podman service."""

    def __repr__(self):
        return f"<{self.__class__.__name__}: {self.name}>"

    @property
    def id(self):  # pylint: disable=invalid-name
        return self.attrs.get("ID")

    @property
    def name(self):
        """str: name of the secret."""
        with suppress(KeyError):
            return self.attrs['Spec']['Name']
        return ""

    def remove(
        self,
        all: Optional[bool] = None,  # pylint: disable=redefined-builtin
    ):
        """Delete secret.

        Args:
            all: When True, delete all secrets.

        Raises:
            NotFound: when Secret does not exist
            APIError: when error returned by service
        """
        self.manager.remove(self.id, all=all)


class SecretsManager(Manager):
    """Specialized Manager for Secret resources."""

    @property
    def resource(self):
        """Type[Secret]: prepare_model() will create Secret classes."""
        return Secret

    def __init__(self, client: APIClient):
        """Initialize SecretsManager object.

        Args:
            client: Connection to Podman service.
        """
        super().__init__(client)

    def exists(self, key: str) -> bool:
        response = self.client.get(f"/secrets/{key}/json")
        return response.ok

    # pylint is flagging 'secret_id' here vs. 'key' parameter in super.get()
    def get(self, secret_id: str) -> Secret:  # pylint: disable=arguments-differ,arguments-renamed
        """Return information for Secret by name or id.

        Args:
            secret_id: Secret name or id.

        Raises:
            NotFound: when Secret does not exist
            APIError: when error returned by service
        """
        response = self.client.get(f"/secrets/{secret_id}/json")
        response.raise_for_status()
        return self.prepare_model(attrs=response.json())

    def list(self, **kwargs) -> List[Secret]:
        """Report on Secrets.

        Keyword Args:
            filters (Dict[str, Any]): Ignored.

        Raises:
            APIError: when error returned by service
        """
        response = self.client.get("/secrets/json")
        response.raise_for_status()
        return [self.prepare_model(attrs=item) for item in response.json()]

    def create(
        self,
        name: str,
        data: bytes,
        labels: Optional[Mapping[str, Any]] = None,  # pylint: disable=unused-argument
        driver: Optional[str] = None,
    ) -> Secret:
        """Create a Secret.

        Args:
            name: User-defined name of the secret.
            data: Secret to be registered with Podman service.
            labels: Ignored.
            driver: Secret driver.

        Raises:
            APIError: when service returns an error
        """
        params = {
            "name": name,
            "driver": driver,
        }
        response = self.client.post("/secrets/create", params=params, data=data)
        response.raise_for_status()

        body = response.json()
        return self.get(body["ID"])

    def remove(
        self,
        secret_id: Union[Secret, str],
        all: Optional[bool] = None,  # pylint: disable=redefined-builtin
    ):
        """Delete secret.

        Podman only

        Args:
            secret_id: Identifier of Secret to delete.
            all: When True, delete all secrets.

        Raises:
            NotFound: when Secret does not exist
            APIError: when an error returned by service
        """
        if isinstance(secret_id, Secret):
            secret_id = secret_id.id

        response = self.client.delete(f"/secrets/{secret_id}", params={"all": all})
        response.raise_for_status()
