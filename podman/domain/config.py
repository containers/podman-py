"""Read containers.conf file."""
import sys
import urllib
from pathlib import Path
from typing import Dict, Optional

import xdg.BaseDirectory

from podman.api import cached_property

if sys.version_info >= (3, 11):
    from tomllib import loads as toml_loads
else:
    try:
        from tomli import loads as toml_loads
    except ImportError:
        from toml import loads as toml_loads


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
        return urllib.parse.urlparse(self.attrs.get("uri"))

    @cached_property
    def identity(self):
        """Path: Returns Path to identity file for service connection."""
        return Path(self.attrs.get("identity"))


class PodmanConfig:
    """PodmanConfig provides a representation of the containers.conf file."""

    def __init__(self, path: Optional[str] = None):
        """Read Podman configuration from users XDG_CONFIG_HOME."""

        if path is None:
            home = Path(xdg.BaseDirectory.xdg_config_home)
            self.path = home / "containers" / "containers.conf"
        else:
            self.path = Path(path)

        self.attrs = {}
        if self.path.exists():
            with self.path.open(encoding='utf-8') as file:
                buffer = file.read()
            self.attrs = toml_loads(buffer)

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

        engine = self.attrs.get("engine")
        if engine:
            destinations = engine.get("service_destinations")
            for key in destinations:
                connection = ServiceConnection(key, attrs=destinations[key])
                services[key] = connection

        return services

    @cached_property
    def active_service(self):
        """Optional[ServiceConnection]: Returns active connection."""

        engine = self.attrs.get("engine")
        if engine:
            active = engine.get("active_service")
            destinations = engine.get("service_destinations")
            for key in destinations:
                if key == active:
                    return ServiceConnection(key, attrs=destinations[key])
        return None
