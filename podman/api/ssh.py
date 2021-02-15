"""Place holder for future adapter to allow remote access via ssh tunnel.

See Podman go bindings for more details.
"""
from typing import Any, Mapping, Optional, Union
from urllib.parse import urlparse

from requests.adapters import HTTPAdapter
from requests.packages.urllib3 import HTTPConnectionPool
from requests.packages.urllib3.connection import HTTPConnection
from requests.packages.urllib3.util import Timeout


class SSHConnection(HTTPConnection):
    """Provide an adapter for requests library to connect to ssh tunnel."""

    def __init__(
        self,
        host: str,
        timeout: Optional[Union[float, Timeout]] = None,
    ):
        """Instantiate connection to ssh proxy service for HTTP client."""
        raise NotImplementedError

    def connect(self):
        raise NotImplementedError

    def __del__(self):
        raise NotImplementedError


class SSHConnectionPool(HTTPConnectionPool):
    def __init__(
        self,
        host: str,
        timeout: Optional[Union[float, Timeout]] = None,
    ) -> None:
        if isinstance(timeout, float):
            timeout = Timeout.from_float(timeout)

    def _new_conn(self) -> SSHConnection:
        return SSHConnection(self.host, self.timeout)


class SSHAdapter(HTTPAdapter):
    def __init__(self, *args, **kwargs):

        self.timeout = None
        if "timeout" in kwargs:
            self.timeout = kwargs.pop("timeout")

        super().__init__(*args, **kwargs)

    def get_connection(self, host, proxies: Mapping[str, Any] = None) -> SSHConnectionPool:
        if len(proxies) > 0:
            uri = urlparse(host)
            if uri.scheme in proxies:
                raise ValueError(f"{self.__class__.__name__} does not support proxies.")

        return SSHConnectionPool(host, timeout=self.timeout)
