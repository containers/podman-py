"""Specialized Transport Adapter for remote Podman access via ssh tunnel.

See Podman go bindings for more details.
"""

import collections
import functools
import logging
import pathlib
import random
import select
import socket
import subprocess
import urllib.parse
from contextlib import suppress
from typing import Optional, Union

import time

import urllib3
import urllib3.connection

from requests.adapters import DEFAULT_POOLBLOCK, DEFAULT_RETRIES, HTTPAdapter
from podman.api.path_utils import get_runtime_dir

from .adapter_utils import _key_normalizer

logger = logging.getLogger("podman.ssh_adapter")


def _identity_args(identity: Optional[str]) -> list[str]:
    if identity is None:
        return []
    path = pathlib.Path(identity).expanduser()
    return ["-i", str(path)]


def _runtime_forward_path() -> pathlib.Path:
    runtime_dir = pathlib.Path(get_runtime_dir()) / "podman"
    runtime_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
    return runtime_dir / f"podman-forward-{random.getrandbits(80):x}.sock"


def _ssh_forward_target(uri: urllib.parse.ParseResult) -> str:
    """Remote target for ssh -L (unix socket path or host:port)."""
    query = urllib.parse.parse_qs(uri.query)
    if "tcp_port" in query:
        return f"127.0.0.1:{query['tcp_port'][0]}"
    if uri.path:
        return uri.path
    raise ValueError(f"SSH URI must include a socket path or tcp_port query: {uri.geturl()}")


class SSHSocket(socket.socket):
    """Specialization of socket.socket to forward a Podman service via SSH."""

    def __init__(self, uri: str, identity: Optional[str] = None):
        """Initialize SSHSocket.

        Args:
            uri: Full address of a Podman service. The SSH forward target is taken from the
                URL path (remote Unix socket) or from the ``tcp_port`` query parameter (remote
                ``127.0.0.1:<port>`` TCP service, for environments where stream-local forwarding
                to a test socket is unreliable).
            identity: Path to file containing SSH key for authorization.

        Examples:
            SSHSocket("http+ssh://alice@api.example:2222/run/user/1000/podman/podman.sock",
                      "~alice/.ssh/api_ed25519")
            SSHSocket("http+ssh://root@localhost:22?tcp_port=8889", "/root/.ssh/id_ecdsa")
        """
        super().__init__(socket.AF_UNIX, socket.SOCK_STREAM)
        self.uri = uri
        self.identity = identity
        self._proc: Optional[subprocess.Popen] = None
        self.local_sock = _runtime_forward_path()

    def connect(self, **kwargs):  # pylint: disable=unused-argument
        """Returns socket for SSH tunneled access to the Podman service.

        Raises:
            OSError: when the SSH channel cannot be established.
            subprocess.TimeoutExpired: when SSH client fails to create local socket.
        """
        uri = urllib.parse.urlparse(self.uri)
        remote_target = _ssh_forward_target(uri)
        command = [
            "ssh",
            "-N",
            "-o",
            "StrictHostKeyChecking no",
            "-L",
            f"{self.local_sock}:{remote_target}",
            *_identity_args(self.identity),
            f"ssh://{uri.netloc}",
        ]
        cmd = " ".join(command)
        expiration = time.monotonic() + 30

        while time.monotonic() < expiration:
            if self._proc is None or self._proc.poll() is not None:
                with suppress(FileNotFoundError):
                    self.local_sock.unlink()
                self._proc = subprocess.Popen(  # pylint: disable=consider-using-with
                    command,
                    shell=False,
                    stdout=subprocess.DEVNULL,
                    stdin=subprocess.DEVNULL,
                    stderr=subprocess.PIPE,
                )

            while not self.local_sock.exists():
                if time.monotonic() > expiration:
                    raise subprocess.TimeoutExpired(cmd, expiration)
                if self._proc.poll() is not None:
                    break
                logger.debug("Waiting on %s", self.local_sock)
                time.sleep(0.2)
            else:
                try:
                    super().connect(str(self.local_sock))
                except OSError as exc:
                    logger.debug("Forward socket not ready: %s", exc)
                    time.sleep(0.2)
                    continue

                # Socket connected — verify the remote channel actually works.
                time.sleep(0.1)
                if self._forward_channel_failed():
                    logger.debug("SSH forward channel refused, retrying")
                    self._reset_forward()
                    time.sleep(0.2)
                    continue
                return

            time.sleep(0.2)

        raise subprocess.TimeoutExpired(cmd, expiration)

    def _reset_forward(self) -> None:
        with suppress(OSError):
            super().close()
        if self._proc:
            if self._proc.stderr:
                with suppress(OSError):
                    self._proc.stderr.close()
            self._proc.terminate()
            try:
                self._proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._proc.kill()
            self._proc = None
        with suppress(FileNotFoundError):
            self.local_sock.unlink()
        self.local_sock = _runtime_forward_path()
        socket.socket.__init__(self, socket.AF_UNIX, socket.SOCK_STREAM)

    def _forward_channel_failed(self) -> bool:
        if not self._proc or not self._proc.stderr:
            return False
        while True:
            ready, _, _ = select.select([self._proc.stderr], [], [], 0.0)
            if not ready:
                break
            line = self._proc.stderr.readline()
            if not line:
                break
            text = line.decode(errors="replace")
            if "open failed" in text.lower():
                logger.debug("SSH forward stderr: %s", text.strip())
                return True
        return False

    def close(self):
        self._reset_forward()


class SSHConnection(urllib3.connection.HTTPConnection):
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

    ConnectionCls = SSHConnection  # pylint: disable=invalid-name


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
    ):  # pylint: disable=too-many-positional-arguments
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
