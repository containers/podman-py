"""Client for connecting to Podman service."""
import logging
import os
import ssl
from contextlib import AbstractContextManager
from typing import Any, Dict, Optional

from podman.api.client import APIClient
from podman.domain.containers_manager import ContainersManager
from podman.domain.events import EventsManager
from podman.domain.images_manager import ImagesManager
from podman.domain.manifests import ManifestsManager
from podman.domain.networks_manager import NetworksManager
from podman.domain.pods_manager import PodsManager
from podman.domain.secrets import SecretsManager
from podman.domain.system import SystemManager
from podman.domain.volumes import VolumesManager
from podman.tlsconfig import TLSConfig
from podman.api import cached_property

logger = logging.getLogger("podman")


class PodmanClient(AbstractContextManager):
    """Create client to Podman service.

    Examples:
        Format, ssh://<user>@<host>[:port]/run/podman/podman.sock?secure=True

    """

    def __init__(self, *args, **kwargs) -> None:
        """Instantiate PodmanClient object

        Keyword Args:
            base_url: Full URL to Podman service. Formats:
                    - http+ssh://<user>@<host>[:port]</run/podman/podman.sock>[?secure=True]
                    - http+unix://</run/podman/podman.sock>
                    - tcp://<localhost>[:<port>]
            version: API version to use. Default: auto, use version from server
            timeout: Timeout for API calls, in seconds. Default: socket._GLOBAL_DEFAULT_TIMEOUT.
            tls: Enable TLS connection to service. True uses default options which
                may be overridden using a TLSConfig object
            user_agent: User agent for service connections. Default: PodmanPy/<Code Version>
            credstore_env: Dict containing environment for credential store
            use_ssh_client: Use system ssh agent rather than ssh module. Always True.
            max_pool_size: Number of connections to save in pool
        """
        super().__init__()
        api_kwargs = kwargs.copy()

        if "base_url" not in api_kwargs:
            uid = os.geteuid()
            if uid == 0:
                elements = ["http+unix://", "run", "podman", "podman.sock"]
            else:
                elements = ["http+unix://", "run", "user", str(uid), "podman", "podman.sock"]
            api_kwargs["base_url"] = os.path.join(elements)  # os.path.join() is correct here...

        self.api = APIClient(*args, **api_kwargs)

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
        ssl_version: int = None,
        assert_hostname: bool = False,
        environment: dict = None,
        credstore_env: dict = None,
        use_ssh_client: bool = True,
    ) -> "PodmanClient":
        """Returns connection to service using environment variables and parameters.

        Environment variables:
            DOCKER_HOST, CONTAINER_HOST: URL to Podman service
            DOCKER_TLS_VERIFY, CONTAINER_TLS_VERIFY: Verify host against CA certificate
            DOCKER_CERT_PATH, CONTAINER_CERT_PATH: Path to TLS certificates for host connection

        Args:
            version: API version to use. Default: auto, use version from server
            timeout: Timeout for API calls, in seconds. Default: 60
            max_pool_size: Number of connections to save in pool.
            ssl_version: Valid SSL version from ssl module
            assert_hostname: Verify hostname of service
            environment: Dict containing input environment. Default: os.environ
            credstore_env: Dict containing environment for credential store
            use_ssh_client: Use system ssh agent rather than ssh module. Always, True.

        Returns:
            PodmanClient: used to communicate with Podman service
        """
        # FIXME Should parameters be *args, **kwargs and resolved before calling PodmanClient()?

        environment = environment or os.environ
        credstore_env = credstore_env or dict()

        if version == "auto":
            version = None

        tls = False
        tls_verify = environment.get("CONTAINER_TLS_VERIFY") or environment.get("DOCKER_TLS_VERIFY")
        if tls_verify or ssl_version or assert_hostname:
            cert_path = (
                environment.get("CONTAINER_CERT_PATH")
                or environment.get("DOCKER_CERT_PATH")
                or os.path.join(os.path.expanduser("~"), ".config/containers/certs.d")
            )

            tls = TLSConfig(
                client_cert=(
                    os.path.join(cert_path, "cert.pem"),
                    os.path.join(cert_path, "key.pem"),
                ),
                ca_cert=os.path.join(cert_path, "ca.pem"),
                verify=tls_verify,
                ssl_version=ssl_version or ssl.PROTOCOL_TLSv1_2,
                assert_hostname=assert_hostname,
            )

        host = environment.get("CONTAINER_HOST") or environment.get("DOCKER_HOST") or None

        return PodmanClient(
            base_url=host,
            version=version,
            timeout=timeout,
            tls=tls,
            credstore_env=credstore_env,
            use_ssh_client=use_ssh_client,
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
            NotImplemented:
        """
        raise NotImplementedError("Swarm operations are not supported by Podman service.")

    services = swarm
    configs = swarm
    nodes = swarm


DockerClient = PodmanClient
from_env = PodmanClient.from_env
