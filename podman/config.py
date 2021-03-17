"""Read containers.conf file."""
import os
import pathlib
import urllib.parse
from functools import lru_cache
from pathlib import Path
from typing import Dict, Optional

try:
    import toml
except ImportError:
    import pytoml as toml


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
    def id(self) -> str:  # pylint: disable=invalid-name
        """Returns identifier for service connection."""
        return self.name

    @property
    @lru_cache(1)
    def url(self) -> urllib.parse.ParseResult:
        """Returns URL for service connection."""
        return urllib.parse.urlparse(self.attrs.get("uri"))

    @property
    @lru_cache(1)
    def identity(self) -> Path:
        """Returns Path to identity file for service connection."""
        return pathlib.Path(self.attrs.get("identity"))


class PodmanConfig:
    """PodmanConfig provides a representation of the containers.conf file."""

    def __init__(self, path: str = None):
        """Read Podman configuration from users XDG_CONFIG_HOME."""

        if path is None:
            home = Path(os.environ.get("XDG_CONFIG_HOME", Path.home()))
            self.path = home / ".config" / "containers" / "containers.conf"
        else:
            self.path = pathlib.Path(path)

        self.attrs = dict()
        if self.path.exists():
            with self.path.open() as file:
                buffer = file.read()
            self.attrs = toml.loads(buffer)

    def __hash__(self) -> int:
        return hash(tuple(self.path.name))

    def __eq__(self, other) -> bool:
        if isinstance(other, PodmanConfig):
            return self.id == other.id and self.attrs == other.attrs
        return False

    @property
    def id(self):  # pylint: disable=invalid-name
        """Returns Path() of container.conf."""
        return self.path

    @property
    @lru_cache(1)
    def services(self) -> Dict[str, ServiceConnection]:
        """Returns list of service connections."""
        services: Dict[str, ServiceConnection] = dict()

        engine = self.attrs.get("engine")
        if engine:
            destinations = engine.get("service_destinations")
            for key in destinations:
                connection = ServiceConnection(key, attrs=destinations[key])
                services[key] = connection

        return services

    @property
    @lru_cache(1)
    def active_service(self) -> Optional[ServiceConnection]:
        """Returns active connection."""

        engine = self.attrs.get("engine")
        if engine:
            active = engine.get("active_service")
            destinations = engine.get("service_destinations")
            for key in destinations:
                if key == active:
                    return ServiceConnection(key, attrs=destinations[key])
        return None
