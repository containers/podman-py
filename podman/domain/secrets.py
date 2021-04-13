"""Model and Manager for Secrets resources.

Notes:
    See https://docs.podman.io/en/latest/_static/api.html#tag/secrets
"""
from typing import List, Optional, Mapping, Any

import requests

from podman.api import APIClient
from podman.domain.manager import PodmanResource, Manager
from podman.errors.exceptions import APIError, NotFound


class Secret(PodmanResource):
    """Details and configuration for a secret registered with the Podman service."""

    def __repr__(self):
        return f"<{self.__class__.__name__}: {self.name}>"

    @property
    def id(self) -> str:  # pylint: disable=invalid-name
        """Returns the identifier for the object."""
        return self.attrs.get("ID")

    @property
    def name(self) -> str:
        try:
            return self.attrs['Spec']['Name']
        except KeyError:
            return ""

    def remove(self, all: Optional[bool] = None):  # pylint: disable=redefined-builtin
        """Delete secret.

        Args:
            all: When True, delete all secrets.

        Raises:
            NotFound: Secret does not exist.
            APIError: Error returned by service.
        """
        response = self.client.delete(f"/secrets/{self.id}", params={"all": all})

        if response.status_code == requests.codes.no_content:
            return

        body = response.json()
        raise APIError(body["cause"], response=response, explanation=body["message"])


class SecretsManager(Manager):
    """Specialized Manager for Secret resources."""

    resource = Secret

    def __init__(self, client: APIClient):
        """Initiate SecretsManager object.

        Args:
            client: Connection to Podman service.
        """
        super().__init__(client)

    def exists(self, key: str) -> bool:
        response = self.client.get(f"/secrets/{key}/json")
        return response.status_code == requests.codes.okay

    # pylint is flagging 'secret_id' here vs. 'key' parameter in super.get()
    def get(self, secret_id: str) -> Secret:  # pylint: disable=arguments-differ
        """Return information for Secret by name or id.

        Args:
            secret_id: Secret name or id.

        Raises:
            NotFound: Secret does not exist.
            APIError: Error returned by service.
        """
        response = self.client.get(f"/secrets/{secret_id}/json")
        body = response.json()

        if response.status_code == requests.codes.okay:
            return self.prepare_model(attrs=body)

        if response.status_code == 404:
            raise NotFound(body["cause"], response=response, explanation=body["message"])
        raise APIError(body["cause"], response=response, explanation=body["message"])

    def list(self, **kwargs) -> List[Secret]:
        """Report on Secrets.

        Keyword Args:
            filters (Dict[str, Any]): Ignored.

        Raises:
            APIError: When error returned by service.
        """
        response = self.client.get("/secrets/json")
        body = response.json()

        if response.status_code == requests.codes.okay:
            return [self.prepare_model(attrs=item) for item in body]
        raise APIError(body["cause"], response=response, explanation=body["message"])

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
            APIError when service returns an error.
        """
        params = {
            "name": name,
            "driver": driver,
        }
        response = self.client.post("/secrets/create", params=params, data=data)
        body = response.json()

        if response.status_code == requests.codes.okay:
            return self.get(body["ID"])
        raise APIError(body["cause"], response=response, explanation=body["message"])
