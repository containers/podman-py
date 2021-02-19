"""Specialized Transport Adapter for UNIX domain sockets."""

import socket
from typing import Any, Mapping, Optional, Union
from urllib.parse import unquote, urlparse

from requests.adapters import HTTPAdapter
from requests.packages.urllib3 import HTTPConnectionPool  # pylint: disable=import-error
from requests.packages.urllib3.connection import HTTPConnection  # pylint: disable=import-error
from requests.packages.urllib3.util import Timeout  # pylint: disable=import-error


class UDSConnection(HTTPConnection):
    """Provide an adapter for requests library to connect to UNIX domain sockets."""

    def __init__(
        self,
        host: str,
        timeout: Optional[Union[float, Timeout]] = None,
    ):
        """Instantiate connection to UNIX domain socket for HTTP client."""
        if isinstance(timeout, Timeout):
            try:
                timeout = float(timeout.total)
            except TypeError:
                timeout = None

        super().__init__('localhost', timeout=timeout)

        self.url = host
        self.sock: Optional[socket.socket] = None
        self.timeout = timeout

    def connect(self):
        """Returns socket for unix domain socket."""
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.settimeout(self.timeout)

        netloc = unquote(urlparse(self.url).netloc)
        sock.connect(netloc)
        self.sock = sock

    def __del__(self):
        """Cleanup connection."""
        if self.sock:
            self.sock.close()


class UDSConnectionPool(HTTPConnectionPool):
    """Specialization of urllib3 HTTPConnectionPool for UNIX domain sockets."""

    # pylint: disable=too-few-public-methods

    def __init__(
        self,
        host: str,
        timeout: Optional[Union[float, Timeout]] = None,
    ) -> None:
        if isinstance(timeout, float):
            timeout = Timeout.from_float(timeout)

        super().__init__('localhost', timeout=timeout, retries=10)
        self.host = host

    def _new_conn(self) -> UDSConnection:
        return UDSConnection(self.host, self.timeout)


class UDSAdapter(HTTPAdapter):
    """Specialization of requests transport adapter for unix domain sockets."""

    # Abstract methods (get_connection) are specialized and pylint cannot walk hierarchy.
    # pylint: disable=arguments-differ

    def __init__(self, *args, **kwargs):

        self.timeout = None
        if "timeout" in kwargs:
            self.timeout = kwargs.pop("timeout")

        super().__init__(*args, **kwargs)

    def get_connection(self, host, proxies: Mapping[str, Any] = None) -> UDSConnectionPool:
        if len(proxies) > 0:
            uri = urlparse(host)
            if uri.scheme in proxies:
                raise ValueError(f"{self.__class__.__name__} does not support proxies.")

        return UDSConnectionPool(host, timeout=self.timeout)
