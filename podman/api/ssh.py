"""Specialized Transport Adapter for remote Podman access via ssh tunnel.

See Podman go bindings for more details.
"""
import collections
import functools
import http.client
import logging
import pathlib
import random
import socket
import subprocess
import urllib.parse
from contextlib import suppress
from typing import Optional, Union

import time
import xdg.BaseDirectory

try:
    import urllib3
except ImportError:
    from requests.packages import urllib3

from requests.adapters import DEFAULT_POOLBLOCK, DEFAULT_RETRIES, HTTPAdapter

from .adapter_utils import _key_normalizer

logger = logging.getLogger("podman.ssh_adapter")


class SSHSocket(socket.socket):
    """Specialization of socket.socket to forward a UNIX domain socket via SSH."""

    def __init__(self, uri: str, identity: Optional[str] = None):
        """Initialize SSHSocket.

        Args:
            uri: Full address of a Podman service including path to remote socket.
            identity: path to file containing SSH key for authorization

        Examples:
            SSHSocket("http+ssh://alice@api.example:2222/run/user/1000/podman/podman.sock",
                      "~alice/.ssh/api_ed25519")
        """
        super().__init__(socket.AF_UNIX, socket.SOCK_STREAM)
        self.uri = uri
        self.identity = identity
        self._proc: Optional[subprocess.Popen] = None

        runtime_dir = pathlib.Path(xdg.BaseDirectory.get_runtime_dir(strict=False)) / "podman"
        runtime_dir.mkdir(mode=0o700, parents=True, exist_ok=True)

        self.local_sock = runtime_dir / f"podman-forward-{random.getrandbits(80):x}.sock"

    def connect(self, **kwargs):  # pylint: disable=unused-argument
        """Returns socket for SSH tunneled UNIX domain socket.

        Raises:
            subprocess.TimeoutExpired: when SSH client fails to create local socket
        """
        uri = urllib.parse.urlparse(self.uri)

        command = [
            "ssh",
            "-N",
            "-o",
            "StrictHostKeyChecking no",
            "-L",
            f"{self.local_sock}:{uri.path}",
        ]

        if self.identity is not None:
            path = pathlib.Path(self.identity).expanduser()
            command += ["-i", str(path)]

        command += [f"ssh://{uri.netloc}"]
        self._proc = subprocess.Popen(  # pylint: disable=consider-using-with
            command,
            shell=False,
            stdout=subprocess.PIPE,
            stdin=subprocess.PIPE,
        )

        expiration = time.monotonic() + 300
        while not self.local_sock.exists():
            if time.monotonic() > expiration:
                cmd = " ".join(command)
                raise subprocess.TimeoutExpired(cmd, expiration)

            logger.debug("Waiting on %s", self.local_sock)
            time.sleep(0.2)

        super().connect(str(self.local_sock))

    def send(self, data: bytes, flags=None) -> int:  # pylint: disable=unused-argument
        """Write data to SSH forwarded UNIX domain socket.

        Args:
            data: Data to write.
            flags: Ignored.

        Returns:
            The number of bytes written.

        Raises:
            RuntimeError: When socket has not been connected.
        """
        if not self._proc or self._proc.stdin.closed:
            raise RuntimeError(f"SSHSocket({self.uri}) not connected.")

        count = self._proc.stdin.write(data)
        self._proc.stdin.flush()
        return count

    def recv(self, buffersize, flags=None) -> bytes:  # pylint: disable=unused-argument
        """Read data from SSH forwarded UNIX domain socket.

        Args:
            buffersize: Maximum number of bytes to read.
            flags: Ignored.

        Raises:
            RuntimeError: When socket has not been connected.
        """
        if not self._proc:
            raise RuntimeError(f"SSHSocket({self.uri}) not connected.")
        return self._proc.stdout.read(buffersize)

    def close(self):
        """Release resources held by SSHSocket.

        The SSH client is first sent SIGTERM, then a SIGKILL 20 seconds later if needed.
        """
        if not self._proc or self._proc.stdin.closed:
            return

        with suppress(BrokenPipeError):
            self._proc.stdin.close()
        self._proc.stdout.close()

        self._proc.terminate()
        try:
            self._proc.wait(timeout=20)
        except subprocess.TimeoutExpired:
            logger.debug("SIGKILL required to stop SSH client.")
            self._proc.kill()

        self.local_sock.unlink()
        self._proc = None
        super().close()


class SSHConnection(http.client.HTTPConnection):
    """Specialization of HTTPConnection to use a SSH forwarded socket."""

    def __init__(
        self,
        host: str,
        port: int,
        timeout: Union[float, urllib3.Timeout, None] = None,
        strict=False,
        **kwargs,  # pylint: disable=unused-argument
    ) -> None:
        """Initialize connection to SSHSocket for HTTP client.

        Args:
            host: Ignored.
            port: Ignored.
            timeout: Time to allow for operation.
            strict: Ignored.

        Keyword Args:
            uri: Full address of a Podman service including path to remote socket. Required.
            identity: path to file containing SSH key for authorization.
        """
        self.sock: Optional[socket.socket] = None

        connection_kwargs = kwargs.copy()
        connection_kwargs["port"] = port

        if timeout is not None:
            if isinstance(timeout, urllib3.Timeout):
                try:
                    connection_kwargs["timeout"] = float(timeout.total)
                except TypeError:
                    pass
            connection_kwargs["timeout"] = timeout

        self.uri = connection_kwargs.pop("uri")
        self.identity = connection_kwargs.pop("identity", None)

        super().__init__(host, **connection_kwargs)
        if logger.getEffectiveLevel() == logging.DEBUG:
            self.set_debuglevel(1)

    def connect(self) -> None:
        """Connect to Podman service via SSHSocket."""
        sock = SSHSocket(self.uri, self.identity)
        sock.settimeout(self.timeout)
        sock.connect()
        self.sock = sock


class SSHConnectionPool(urllib3.HTTPConnectionPool):
    """Specialized HTTPConnectionPool for holding SSH connections."""

    ConnectionCls = SSHConnection


class SSHPoolManager(urllib3.PoolManager):
    """Specialized PoolManager for tracking SSH connections."""

    # pylint's special handling for namedtuple does not cover this usage
    # pylint: disable=invalid-name
    _PoolKey = collections.namedtuple(
        "_PoolKey", urllib3.poolmanager.PoolKey._fields + ("key_uri", "key_identity")
    )

    # Map supported schemes to Pool Classes
    _pool_classes_by_scheme = {
        "http": SSHConnectionPool,
        "http+ssh": SSHConnectionPool,
    }

    # Map supported schemes to Pool Key index generator
    _key_fn_by_scheme = {
        "http": functools.partial(_key_normalizer, _PoolKey),
        "http+ssh": functools.partial(_key_normalizer, _PoolKey),
    }

    def __init__(self, num_pools=10, headers=None, **kwargs):
        """Initialize SSHPoolManager.

        Args:
            num_pools: Number of SSH Connection pools to maintain.
            headers: Additional headers to add to operations.
        """
        super().__init__(num_pools, headers, **kwargs)
        self.pool_classes_by_scheme = SSHPoolManager._pool_classes_by_scheme
        self.key_fn_by_scheme = SSHPoolManager._key_fn_by_scheme


class SSHAdapter(HTTPAdapter):
    """Specialization of requests transport adapter for SSH forwarded UNIX domain sockets."""

    def __init__(
        self,
        uri: str,
        pool_connections: int = 9,
        pool_maxsize: int = 10,
        max_retries: int = DEFAULT_RETRIES,
        pool_block: int = DEFAULT_POOLBLOCK,
        **kwargs,
    ):
        """Initialize SSHAdapter.

        Args:
            uri: Full address of a Podman service including path to remote socket.
                Format, ssh://<user>@<host>[:port]/run/podman/podman.sock?secure=True
            pool_connections: The number of connection pools to cache. Should be at least one less
                than pool_maxsize.
            pool_maxsize: The maximum number of connections to save in the pool.
                OpenSSH default is 10.
            max_retries: The maximum number of retries each connection should attempt.
            pool_block: Whether the connection pool should block for connections.

        Keyword Args:
            timeout (float):
            identity (str): Optional path to ssh identity key
        """
        self.poolmanager: Optional[SSHPoolManager] = None

        # Parsed for fail-fast side effects
        _ = urllib.parse.urlparse(uri)
        self._pool_kwargs = {"uri": uri}

        if "identity" in kwargs:
            path = pathlib.Path(kwargs.get("identity"))
            if not path.exists():
                raise FileNotFoundError(f"Identity file '{path}' does not exist.")
            self._pool_kwargs["identity"] = str(path)

        if "timeout" in kwargs:
            self._pool_kwargs["timeout"] = kwargs.get("timeout")

        super().__init__(pool_connections, pool_maxsize, max_retries, pool_block)

    def init_poolmanager(self, connections, maxsize, block=DEFAULT_POOLBLOCK, **kwargs):
        """Initialize SSHPoolManager to be used by SSHAdapter.

        Args:
            connections: The number of urllib3 connection pools to cache.
            maxsize: The maximum number of connections to save in the pool.
            block: Block when no free connections are available.
        """
        pool_kwargs = kwargs.copy()
        pool_kwargs.update(self._pool_kwargs)
        self.poolmanager = SSHPoolManager(
            num_pools=connections, maxsize=maxsize, block=block, **pool_kwargs
        )
