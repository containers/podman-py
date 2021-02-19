"""Place holder for future adapter to allow remote access via ssh tunnel.

See Podman go bindings for more details.
"""
from typing import Any, Mapping, Optional, Union
from urllib.parse import urlparse

from requests.adapters import HTTPAdapter
from requests.packages.urllib3 import HTTPConnectionPool  # pylint: disable=import-error
from requests.packages.urllib3.connection import HTTPConnection  # pylint: disable=import-error
from requests.packages.urllib3.util import Timeout  # pylint: disable=import-error


class SSHConnection(HTTPConnection):
    """Specialization of HTTPConnection to use a ssh tunnel."""

    def __init__(
        self,
        host: str,
        timeout: Optional[Union[float, Timeout]] = None,
    ):
        """Instantiate connection to ssh tunnel for Podman service for HTTP client."""
        _ = host
        _ = timeout
        raise NotImplementedError

    def connect(self):
        """Returns socket for ssh tunnel."""
        raise NotImplementedError

    def __del__(self):
        """Cleanup connection."""
        raise NotImplementedError


class SSHConnectionPool(HTTPConnectionPool):
    """Specialization of urllib3 HTTPConnectionPool for ssh tunnels."""

    # pylint: disable=too-few-public-methods

    def __init__(
        self,
        host: str,
        timeout: Optional[Union[float, Timeout]] = None,
    ) -> None:
        if isinstance(timeout, float):
            timeout = Timeout.from_float(timeout)
        _ = host

    def _new_conn(self) -> SSHConnection:
        return SSHConnection(self.host, self.timeout)


class SSHAdapter(HTTPAdapter):
    """Specialization of requests transport adapter for ssh tunnels."""

    # Abstract methods (get_connection) are specialized and pylint cannot walk hierarchy.
    # pylint: disable=arguments-differ
    # pylint: disable=too-few-public-methods

    def __init__(self, *args, **kwargs):
        self.timeout = None
        if "timeout" in kwargs:
            self.timeout = kwargs.pop("timeout")

        super().__init__(*args, **kwargs)

    def get_connection(self, host, proxies: Mapping[str, Any] = None) -> SSHConnectionPool:
        """Returns ssh tunneled connection to Podman service."""
        if len(proxies) > 0:
            uri = urlparse(host)
            if uri.scheme in proxies:
                raise ValueError(f"{self.__class__.__name__} does not support proxies.")

        return SSHConnectionPool(host, timeout=self.timeout)
