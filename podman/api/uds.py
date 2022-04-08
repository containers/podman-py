"""Specialized Transport Adapter for UNIX domain sockets."""
import collections
import functools
import http.client
import logging
import socket
from typing import Optional, Union
from urllib.parse import unquote, urlparse

try:
    import urllib3
except ImportError:
    from requests.packages import urllib3

from requests.adapters import DEFAULT_POOLBLOCK, DEFAULT_POOLSIZE, DEFAULT_RETRIES, HTTPAdapter

from ..errors import APIError

from .adapter_utils import _key_normalizer

logger = logging.getLogger("podman.uds_adapter")


class UDSSocket(socket.socket):
    """Specialization of socket.socket for a UNIX domain socket."""

    def __init__(self, uds: str):
        """Initialize UDSSocket.

        Args:
            uds: Full address of a Podman service UNIX domain socket.

        Examples:
            UDSSocket("http+unix:///run/podman/podman.sock")
        """
        super().__init__(socket.AF_UNIX, socket.SOCK_STREAM)
        self.uds = uds

    def connect(self, **kwargs):  # pylint: disable=unused-argument
        """Returns socket for UNIX domain socket."""
        netloc = unquote(urlparse(self.uds).netloc)
        try:
            super().connect(netloc)
        except Exception as e:
            raise APIError(f"Unable to make connection to UDS '{netloc}'") from e


class UDSConnection(http.client.HTTPConnection):
    """Specialization of HTTPConnection to use a UNIX domain sockets."""

    def __init__(
        self,
        host: str,
        port: int,
        timeout: Union[float, urllib3.Timeout, None] = None,
        strict=False,
        **kwargs,  # pylint: disable=unused-argument
    ):
        """Initialize connection to UNIX domain socket for HTTP client.

        Args:
            host: Ignored.
            port: Ignored.
            timeout: Time to allow for operation.
            strict: Ignored.

        Keyword Args:
            uds: Full address of a Podman service UNIX domain socket. Required.
        """
        connection_kwargs = kwargs.copy()
        self.sock: Optional[socket.socket] = None

        if timeout is not None:
            if isinstance(timeout, urllib3.Timeout):
                try:
                    connection_kwargs["timeout"] = float(timeout.total)
                except TypeError:
                    pass
            connection_kwargs["timeout"] = timeout

        self.uds = connection_kwargs.pop("uds")
        super().__init__(host, **connection_kwargs)

    def connect(self) -> None:
        """Connect to Podman service via UNIX domain socket."""
        sock = UDSSocket(self.uds)
        sock.settimeout(self.timeout)
        sock.connect()
        self.sock = sock


class UDSConnectionPool(urllib3.HTTPConnectionPool):
    """Specialization of HTTPConnectionPool for holding UNIX domain sockets."""

    ConnectionCls = UDSConnection


class UDSPoolManager(urllib3.PoolManager):
    """Specialized PoolManager for tracking UNIX domain socket connections."""

    # pylint's special handling for namedtuple does not cover this usage
    # pylint: disable=invalid-name
    _PoolKey = collections.namedtuple(
        "_PoolKey", urllib3.poolmanager.PoolKey._fields + ("key_uds",)
    )

    # Map supported schemes to Pool Classes
    _pool_classes_by_scheme = {
        "http": UDSConnectionPool,
        "http+ssh": UDSConnectionPool,
    }

    # Map supported schemes to Pool Key index generator
    _key_fn_by_scheme = {
        "http": functools.partial(_key_normalizer, _PoolKey),
        "http+ssh": functools.partial(_key_normalizer, _PoolKey),
    }

    def __init__(self, num_pools=10, headers=None, **kwargs):
        """Initialize UDSPoolManager.

        Args:
            num_pools: Number of UDS Connection pools to maintain.
            headers: Additional headers to add to operations.
        """
        super().__init__(num_pools, headers, **kwargs)
        self.pool_classes_by_scheme = UDSPoolManager._pool_classes_by_scheme
        self.key_fn_by_scheme = UDSPoolManager._key_fn_by_scheme


class UDSAdapter(HTTPAdapter):
    """Specialization of requests transport adapter for UNIX domain sockets."""

    def __init__(
        self,
        uds: str,
        pool_connections=DEFAULT_POOLSIZE,
        pool_maxsize=DEFAULT_POOLSIZE,
        max_retries=DEFAULT_RETRIES,
        pool_block=DEFAULT_POOLBLOCK,
        **kwargs,
    ):
        """Initialize UDSAdapter.

        Args:
            uds: Full address of a Podman service UNIX domain socket.
                Format, http+unix:///run/podman/podman.sock
            max_retries: The maximum number of retries each connection should attempt.
            pool_block: Whether the connection pool should block for connections.
            pool_connections: The number of connection pools to cache.
            pool_maxsize: The maximum number of connections to save in the pool.

        Keyword Args:
            timeout (float): Time in seconds to wait for response

        Examples:
            requests.Session.mount(
                "http://", UDSAdapater("http+unix:///run/user/1000/podman/podman.sock"))
        """
        self.poolmanager: Optional[UDSPoolManager] = None

        self._pool_kwargs = {"uds": uds}

        if "timeout" in kwargs:
            self._pool_kwargs["timeout"] = kwargs.get("timeout")

        super().__init__(pool_connections, pool_maxsize, max_retries, pool_block)

    def init_poolmanager(self, connections, maxsize, block=DEFAULT_POOLBLOCK, **kwargs):
        """Initialize UDS Pool Manager.

        Args:
            connections: The number of urllib3 connection pools to cache.
            maxsize: The maximum number of connections to save in the pool.
            block: Block when no free connections are available.
        """
        pool_kwargs = kwargs.copy()
        pool_kwargs.update(self._pool_kwargs)
        self.poolmanager = UDSPoolManager(
            num_pools=connections, maxsize=maxsize, block=block, **pool_kwargs
        )
