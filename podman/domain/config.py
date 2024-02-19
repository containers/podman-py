"""Read containers.conf file."""

import sys
import urllib
from pathlib import Path
from typing import Dict, Optional
import json

import xdg.BaseDirectory

from podman.api import cached_property

if sys.version_info >= (3, 11):
    from tomllib import loads as toml_loads
else:
    try:
        from tomli import loads as toml_loads
    except ImportError:
        try:
            from toml import loads as toml_loads
        except ImportError:
            from pytoml import loads as toml_loads


class ServiceConnection:
    """ServiceConnection defines a connection to the Podman service."""

    def __init__(self, name: str, attrs: Dict[str, str]):
        """Create a Podman ServiceConnection."""
        self.name = name
        self.attrs = attrs

    def __repr__(self) -> str:
        return f"""<{self.__class__.__name__}: '{self.id}'>"""

    def __hash__(self) -> int:
        return hash(tuple(self.name))

    def __eq__(self, other) -> bool:
        if isinstance(other, ServiceConnection):
            return self.id == other.id and self.attrs == other.attrs
        return False

    @property
    def id(self):  # pylint: disable=invalid-name
        """str: Returns identifier for service connection."""
        return self.name

    @cached_property
    def url(self):
        """urllib.parse.ParseResult: Returns URL for service connection."""
        if self.attrs.get("uri"):
            return urllib.parse.urlparse(self.attrs.get("uri"))
        return urllib.parse.urlparse(self.attrs.get("URI"))

    @cached_property
    def identity(self):
        """Path: Returns Path to identity file for service connection."""
        if self.attrs.get("identity"):
            return Path(self.attrs.get("identity"))
        return Path(self.attrs.get("Identity"))


class PodmanConfig:
    """PodmanConfig provides a representation of the containers.conf file."""

    def __init__(self, path: Optional[str] = None):
        """Read Podman configuration from users XDG_CONFIG_HOME."""

        self.is_default = False
        if path is None:
            home = Path(xdg.BaseDirectory.xdg_config_home)
            self.path = home / "containers" / "podman-connections.json"
            old_toml_file = home / "containers" / "containers.conf"
            self.is_default = True
        # this elif is only for testing purposes
        elif "@@is_test@@" in path:
            test_path = path.replace("@@is_test@@", '')
            self.path = Path(test_path) / "podman-connections.json"
            old_toml_file = Path(test_path) / "containers.conf"
            self.is_default = True
        else:
            self.path = Path(path)

        self.attrs = {}
        if self.path.exists():
            try:
                with open(self.path, encoding='utf-8') as file:
                    self.attrs = json.load(file)
            except:  # pylint: disable=bare-except
                # if the user specifies a path, it can either be a JSON file
                # or a TOML file - so try TOML next
                try:
                    with self.path.open(encoding='utf-8') as file:
                        buffer = file.read()
                    loaded_toml = toml_loads(buffer)
                    self.attrs.update(loaded_toml)
                except Exception as e:
                    raise AttributeError(
                        "The path given is neither a JSON nor a TOML connections file"
                    ) from e

        # Read the old toml file configuration
        if self.is_default and old_toml_file.exists():
            with old_toml_file.open(encoding='utf-8') as file:
                buffer = file.read()
            loaded_toml = toml_loads(buffer)
            self.attrs.update(loaded_toml)

    def __hash__(self) -> int:
        return hash(tuple(self.path.name))

    def __eq__(self, other) -> bool:
        if isinstance(other, PodmanConfig):
            return self.id == other.id and self.attrs == other.attrs
        return False

    @property
    def id(self):  # pylint: disable=invalid-name
        """Path: Returns Path() of container.conf."""
        return self.path

    @cached_property
    def services(self):
        """Dict[str, ServiceConnection]: Returns list of service connections.

        Examples:
            podman_config = PodmanConfig()
            address = podman_config.services["testing"]
            print(f"Testing service address {address}")
        """
        services: Dict[str, ServiceConnection] = {}

        # read the keys of the toml file first
        engine = self.attrs.get("engine")
        if engine:
            destinations = engine.get("service_destinations")
            for key in destinations:
                connection = ServiceConnection(key, attrs=destinations[key])
                services[key] = connection

        # read the keys of the json file next
        # this will ensure that if the new json file and the old toml file
        # has a connection with the same name defined, we always pick the
        # json one
        connection = self.attrs.get("Connection")
        if connection:
            destinations = connection.get("Connections")
            for key in destinations:
                connection = ServiceConnection(key, attrs=destinations[key])
                services[key] = connection

        return services

    @cached_property
    def active_service(self):
        """Optional[ServiceConnection]: Returns active connection."""

        # read the new json file format
        connection = self.attrs.get("Connection")
        if connection:
            active = connection.get("Default")
            destinations = connection.get("Connections")
            return ServiceConnection(active, attrs=destinations[active])

        # if we are here, that means there was no default in the new json file
        engine = self.attrs.get("engine")
        if engine:
            active = engine.get("active_service")
            destinations = engine.get("service_destinations")
            return ServiceConnection(active, attrs=destinations[active])

        return None
