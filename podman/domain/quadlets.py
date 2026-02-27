"""Model and Manager for Quadlet resources."""

import builtins
import logging
from typing import Optional, Union

import requests

from podman import api
from podman.domain.manager import Manager, PodmanResource
from podman.errors import NotFound, PodmanError

logger = logging.getLogger("podman.quadlets")


class Quadlet(PodmanResource):
    """Details and configuration for a quadlet managed by the Podman service."""

    manager: "QuadletsManager"

    @property
    def name(self) -> str:
        """str: Returns the name of the quadlet file."""
        return self.attrs.get("Name", self.attrs.get("name", ""))

    @property
    def unit_name(self) -> str:
        """str: Returns the unit name of the quadlet."""
        return self.attrs.get("UnitName", self.attrs.get("unitName", ""))

    @property
    def path(self) -> str:
        """str: Returns the path of the quadlet file."""
        return self.attrs.get("Path", self.attrs.get("path", ""))

    @property
    def status(self) -> str:
        """str: Returns the status of the quadlet."""
        return self.attrs.get("Status", self.attrs.get("status", ""))

    @property
    def application(self) -> str:
        """str: Returns the application of the quadlet."""
        return self.attrs.get("App", self.attrs.get("app", ""))

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}: {self.name}>"

    def delete(self, **kwargs) -> builtins.list:
        """Remove this quadlet file. Can force removal of running
        quadlets and control systemd reload behavior.

        Keyword Args:
            force (bool): Remove running quadlet by stopping it first (default False)
            ignore (bool): Do not error if the quadlet does not exist (default False)
            reload_systemd (bool): Reload systemd after removing quadlets (default True)

        Returns:
            List of removed quadlet names.
        """
        return self.manager.delete(self.name, **kwargs)

    def get_contents(self) -> str:
        """Get the contents of this quadlet file.

        Returns:
            The complete quadlet file contents as a string.
        """
        return self.manager.get_contents(self.name)

    def print_contents(self) -> None:
        """Print the contents of this quadlet file.

        Raises:
            APIError: when service reports an error
        """
        self.manager.print_contents(self.name)


class QuadletsManager(Manager):
    """Specialized Manager for Quadlet resources."""

    @property
    def resource(self):
        """Type[Quadlet]: prepare_model() will create Quadlet classes."""
        return Quadlet

    def exists(self, key: str) -> bool:
        """Check if a quadlet exists.

        Args:
            key: Name of the quadlet to check.

        Returns:
            True if the quadlet exists, False otherwise.
        """
        response = self.client.get(f"/quadlets/{key}/exists")
        if response.status_code == 404:
            return False
        response.raise_for_status()
        return True

    def get(self, name: str) -> Quadlet:
        """Returns a quadlet by name.

        Args:
            name: Quadlet name for which to search.

        Raises:
            NotFound: when quadlet could not be found
            APIError: when service reports an error
        """
        response = self.client.get(
            "/quadlets/json",
            params={"filters": api.prepare_filters({"name": name})},
        )
        response.raise_for_status()
        data = response.json()
        if not data:
            raise NotFound(f"Quadlet {name} not found")
        return self.prepare_model(attrs=data[0])

    def list(self, *_, **kwargs) -> builtins.list[Quadlet]:
        """Report on quadlets.

        Keyword Args:
            filters (dict[str, str]): Criteria to filter quadlet list.
                - name (str): Filter by quadlet name (supports wildcards).

        Returns:
            List of Quadlet objects.
        """
        filters = api.prepare_filters(kwargs.get("filters"))
        params = {}
        if filters:
            params["filters"] = filters

        response = self.client.get("/quadlets/json", params=params)

        if response.status_code == requests.codes.not_found:
            return []
        response.raise_for_status()

        return [self.prepare_model(attrs=i) for i in response.json()]

    def get_contents(self, name: Union[Quadlet, str]) -> str:
        """Get the contents of a quadlet file.

        Args:
            name: Identifier for Quadlet to display.

        Returns:
            The complete quadlet file contents as a string.

        Raises:
            APIError: when service reports an error
        """
        if isinstance(name, Quadlet):
            name = name.name

        response = self.client.get(f"/quadlets/{name}/file")
        response.raise_for_status()
        return response.text

    def print_contents(self, name: Union[Quadlet, str]) -> None:
        """Print the contents of a quadlet file stripped
        of excess whitespace and newlines.

        Args:
            name: Identifier for Quadlet to display.

        Returns:
            None

        Raises:
            APIError: when service reports an error
        """
        if isinstance(name, Quadlet):
            name = name.name

        response = self.client.get(f"/quadlets/{name}/file")
        response.raise_for_status()
        print(response.text.strip())

    def delete(
        self, name: Optional[Union[Quadlet, str]] = None, *_, all: Optional[bool] = None, **kwargs
    ) -> builtins.list:
        """Remove a quadlet file by name. Can force
        removal of running quadlets and control systemd
        reload behavior

        Args:
            name: Identifier for Quadlet to remove
            all (bool): Remove all quadlets for the current user (default False)
                One between name and all should be provided.

        Keyword Args:
            force (bool): Remove running quadlet by stopping it first (default False)
            ignore (bool): Do not error if the quadlet does not exist (default  False)
            reload_systemd (bool): Reload systemd after removing quadlets. (default True)

        Returns:
            List of removed quadlet names.
        """

        if name is None and all is None:
            raise PodmanError("Quadlet name, or 'all=True' should be provided")

        if isinstance(name, Quadlet):
            name = name.name

        params = {
            "force": kwargs.get("force", False),
            "ignore": kwargs.get("ignore", False),
            "reload-systemd": kwargs.get("reload_systemd", True),
        }

        if all:
            params["all"] = True
            response = self.client.delete("/quadlets", params=params)
        else:
            response = self.client.delete(f"/quadlets/{name}", params=params)

        response.raise_for_status()
        return response.json()["Removed"]
