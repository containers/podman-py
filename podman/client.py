"""Client for connecting to Podman service."""
import logging
import os
from contextlib import AbstractContextManager
from pathlib import Path
from typing import Any, Dict, Optional

import xdg.BaseDirectory

from podman.api import cached_property
from podman.api.client import APIClient
from podman.domain.config import PodmanConfig
from podman.domain.containers_manager import ContainersManager
from podman.domain.events import EventsManager
from podman.domain.images_manager import ImagesManager
from podman.domain.manifests import ManifestsManager
from podman.domain.networks_manager import NetworksManager
from podman.domain.pods_manager import PodsManager
from podman.domain.secrets import SecretsManager
from podman.domain.system import SystemManager
from podman.domain.volumes import VolumesManager

logger = logging.getLogger("podman")


class PodmanClient(AbstractContextManager):
    """Client to connect to a Podman service.

    Examples:

        with PodmanClient(base_url="ssh://root@api.example:22/run/podman/podman.sock?secure=True",
            identity="~alice/.ssh/api_ed25519")
    """

    def __init__(self, **kwargs) -> None:
        """Initialize PodmanClient.

        Keyword Args:
            base_url (str): Full URL to Podman service. See examples.
            version (str): API version to use. Default: auto, use version from server
            timeout (int): Timeout for API calls, in seconds.
                Default: socket._GLOBAL_DEFAULT_TIMEOUT.
            tls: Ignored. SSH connection configuration delegated to SSH Host configuration.
            user_agent (str): User agent for service connections. Default: PodmanPy/<Code Version>
            credstore_env (Mapping[str, str]): Dict containing environment for credential store
            use_ssh_client (True): Always shell out to SSH client for
                SSH Podman service connections.
            max_pool_size (int): Number of connections to save in pool
            connection (str): Identifier of connection to use from
                XDG_CONFIG_HOME/containers/containers.conf
            identity (str): Provide SSH key to authenticate SSH connection.

        Examples:
            base_url:

                - http+ssh://<user>@<host>[:port]</run/podman/podman.sock>[?secure=True]
                - http+unix://</run/podman/podman.sock>
                - tcp://<localhost>[:<port>]
        """
        super().__init__()
        config = PodmanConfig()

        api_kwargs = kwargs.copy()

        if "connection" in api_kwargs:
            connection = config.services[api_kwargs.get("connection")]
            api_kwargs["base_url"] = connection.url.geturl()

            # Override configured identity, if provided in arguments
            api_kwargs["identity"] = kwargs.get("identity", str(connection.identity))
        elif "base_url" not in api_kwargs:
            path = str(
                Path(xdg.BaseDirectory.get_runtime_dir(strict=False)) / "podman" / "podman.sock"
            )
            api_kwargs["base_url"] = "http+unix://" + path
        self.api = APIClient(**api_kwargs)

    def __enter__(self) -> "PodmanClient":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()

    @classmethod
    def from_env(
        cls,
        version: str = "auto",
        timeout: Optional[int] = None,
        max_pool_size: Optional[int] = None,
        ssl_version: Optional[int] = None,  # pylint: disable=unused-argument
        assert_hostname: bool = False,  # pylint: disable=unused-argument
        environment: Optional[Dict[str, str]] = None,
        credstore_env: Optional[Dict[str, str]] = None,
        use_ssh_client: bool = True,  # pylint: disable=unused-argument
    ) -> "PodmanClient":
        """Returns connection to service using environment variables and parameters.

        Environment variables:

            - DOCKER_HOST, CONTAINER_HOST: URL to Podman service
            - DOCKER_TLS_VERIFY, CONTAINER_TLS_VERIFY: Verify host against CA certificate
            - DOCKER_CERT_PATH, CONTAINER_CERT_PATH: Path to TLS certificates for host connection

        Args:
            version: API version to use. Default: auto, use version from server
            timeout: Timeout for API calls, in seconds.
            max_pool_size: Number of connections to save in pool.
            ssl_version: SSH configuration delegated to SSH client configuration. Ignored.
            assert_hostname: Ignored.
            environment: Dict containing input environment. Default: os.environ
            credstore_env: Dict containing environment for credential store
            use_ssh_client: Use system ssh client rather than ssh module. Always, True.

        Returns:
            Client used to communicate with a Podman service.
        """
        environment = environment or os.environ
        credstore_env = credstore_env or {}

        if version == "auto":
            version = None

        host = environment.get("CONTAINER_HOST") or environment.get("DOCKER_HOST") or None

        return PodmanClient(
            base_url=host,
            version=version,
            timeout=timeout,
            tls=False,
            credstore_env=credstore_env,
            max_pool_size=max_pool_size,
        )

    @cached_property
    def containers(self) -> ContainersManager:
        """Returns Manager for operations on containers stored by a Podman service."""
        return ContainersManager(client=self.api)

    @cached_property
    def images(self) -> ImagesManager:
        """Returns Manager for operations on images stored by a Podman service."""
        return ImagesManager(client=self.api)

    @cached_property
    def manifests(self) -> ManifestsManager:
        """Returns Manager for operations on manifests maintained by a Podman service."""
        return ManifestsManager(client=self.api)

    @cached_property
    def networks(self) -> NetworksManager:
        """Returns Manager for operations on networks maintained by a Podman service."""
        return NetworksManager(client=self.api)

    @cached_property
    def volumes(self) -> VolumesManager:
        """Returns Manager for operations on volumes maintained by a Podman service."""
        return VolumesManager(client=self.api)

    @cached_property
    def pods(self) -> PodsManager:
        """Returns Manager for operations on pods maintained by a Podman service."""
        return PodsManager(client=self.api)

    @cached_property
    def secrets(self):
        """Returns Manager for operations on secrets maintained by a Podman service."""
        return SecretsManager(client=self.api)

    @cached_property
    def system(self):
        return SystemManager(client=self.api)

    def df(self) -> Dict[str, Any]:  # pylint: disable=missing-function-docstring,invalid-name
        return self.system.df()

    df.__doc__ = SystemManager.df.__doc__

    def events(self, *args, **kwargs):  # pylint: disable=missing-function-docstring
        return EventsManager(client=self.api).list(*args, **kwargs)

    events.__doc__ = EventsManager.list.__doc__

    def info(self, *args, **kwargs):  # pylint: disable=missing-function-docstring
        return self.system.info(*args, **kwargs)

    info.__doc__ = SystemManager.info.__doc__

    def login(self, *args, **kwargs):  # pylint: disable=missing-function-docstring
        return self.system.login(*args, **kwargs)

    login.__doc__ = SystemManager.login.__doc__

    def ping(self) -> bool:  # pylint: disable=missing-function-docstring
        return self.system.ping()

    ping.__doc__ = SystemManager.ping.__doc__

    def version(self, *args, **kwargs):  # pylint: disable=missing-function-docstring
        _ = args
        return self.system.version(**kwargs)

    version.__doc__ = SystemManager.version.__doc__

    def close(self):
        """Release PodmanClient Resources."""
        return self.api.close()

    @property
    def swarm(self):
        """Swarm not supported.

        Raises:
            NotImplemented: Swarm not supported by Podman service
        """
        raise NotImplementedError("Swarm operations are not supported by Podman service.")

    # Aliases to cover all swarm methods
    services = swarm
    configs = swarm
    nodes = swarm


# Aliases to minimize effort to port to PodmanPy
DockerClient = PodmanClient
from_env = PodmanClient.from_env
