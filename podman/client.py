"""Client for connecting to Podman service."""
import os
import ssl
from typing import Any, Dict, Mapping, Optional, Union

from podman.api.client import APIClient
from podman.domain.containers import ContainerManager
from podman.domain.events import EventManager
from podman.domain.images import ImageManager
from podman.domain.networks import NetworkManager
from podman.domain.pods import PodManager
from podman.domain.system import SystemManager
from podman.domain.volumes import VolumeManager
from podman.tlsconfig import TLSConfig


class PodmanClient:
    """Create client connection to Podman service"""

    def __init__(
        self,
        base_url: str = None,
        version: str = None,
        timeout: int = 60,
        tls: Union[bool, TLSConfig] = False,
        user_agent: str = None,
        credstore_env: Optional[Mapping[str, str]] = None,
        use_ssh_client: bool = False,
        max_pool_size: int = 5,
    ) -> None:
        """Instantiate PodmanClient object

        Args:
            base_url: URL to Podman service.
            version: API version to use. Default: auto, use version from server
            timeout: Timeout for API calls, in seconds. Default: 60
            tls: Enable TLS connection to service. True uses default options which
                may be overridden using a TLSConfig object
            user_agent: User agent for service connections. Default: PodmanPy/<Code Version>
            credstore_env: Dict containing environment for credential store
            use_ssh_client: Use system ssh agent rather than ssh module. Default:False
            max_pool_size: Number of connections to save in pool
        """
        # FIXME Should parameters be *args, **kwargs and resolved before calling APIClient()?

        if not base_url:
            uid = os.geteuid()
            if uid == 0:
                elements = ["http+unix://", "run", "podman", "podman.sock"]
            else:
                elements = ["http+unix://", "run", "user", str(uid), "podman", "podman.sock"]
            base_url = "%2F".join(elements)
        self.base_url = base_url

        _ = use_ssh_client

        self.client = APIClient(
            base_url=base_url,
            version=version,
            timeout=timeout,
            tls=tls,
            user_agent=user_agent,
            num_pools=max_pool_size,
            credstore_env=credstore_env,
        )

    @classmethod
    def from_env(
        cls,
        version: str = "auto",
        timeout: int = -1,
        max_pool_size: int = 60,
        ssl_version: int = None,
        assert_hostname: bool = False,
        environment: dict = None,
        credstore_env: dict = None,
        use_ssh_client: bool = False,
    ) -> 'PodmanClient':
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
            use_ssh_client: Use system ssh agent rather than ssh module. Default:False

        Returns:
            PodmanClient: used to communicate with Podman service
        """
        # FIXME Should parameters be *args, **kwargs and resolved before calling PodmanClient()?

        env = os.environ
        if environment is not None:
            env = environment

        if credstore_env is None:
            credstore_env = {}

        if version == "auto":
            version = None

        tls = False
        tls_verify = env.get("CONTAINER_TLS_VERIFY") or env.get("DOCKER_TLS_VERIFY")
        if tls_verify or ssl_version or assert_hostname:
            cert_path = (
                env.get("CONTAINER_CERT_PATH")
                or env.get("DOCKER_CERT_PATH")
                or os.path.join(os.path.expanduser('~'), ".config/containers/certs.d")
            )

            tls = TLSConfig(
                client_cert=(
                    os.path.join(cert_path, 'cert.pem'),
                    os.path.join(cert_path, 'key.pem'),
                ),
                ca_cert=os.path.join(cert_path, 'ca.pem'),
                verify=tls_verify,
                ssl_version=ssl_version or ssl.PROTOCOL_TLSv1_2,
                assert_hostname=assert_hostname,
            )

        host = env.get("CONTAINER_HOST") or env.get("DOCKER_HOST") or None

        return PodmanClient(
            base_url=host,
            version=version,
            timeout=timeout,
            tls=tls,
            user_agent="Podman/3.0.0",
            credstore_env=credstore_env,
            use_ssh_client=use_ssh_client,
            max_pool_size=max_pool_size,
        )

    @property
    def configs(self):
        """Returns object for managing configuration of the Podman service.

        Raises:
            NotImplementError:
        """
        raise NotImplementedError()

    @property
    def containers(self) -> ContainerManager:
        """Returns object for managing containers running via the Podman service.

        Returns:
            ContainerManager:
        """
        return ContainerManager(client=self.client)

    @property
    def images(self) -> ImageManager:
        """Returns object for managing images stored via the Podman service.

        Returns:
            ImageManager:
        """
        return ImageManager(client=self.client)

    @property
    def networks(self) -> NetworkManager:
        """Returns object for managing networks created via the Podman service.

        Returns:
            NetworkManager:
        """
        return NetworkManager(client=self.client)

    @property
    def volumes(self) -> VolumeManager:
        """Returns object for managing volumes maintained via the Podman service.

        Returns:
            VolumeManager:
        """
        return VolumeManager(client=self.client)

    @property
    def pods(self) -> PodManager:
        """Returns object for managing pods created via the Podman service.

        Returns:
            PodManager:
        """
        return PodManager(client=self.client)

    @property
    def nodes(self):
        """Swarm not supported.

        Raises:
            NotImplemented:
        """
        raise NotImplementedError("Swarm not supported.")

    @property
    def secrets(self):
        """TBD."""
        raise NotImplementedError()

    @property
    def services(self):
        """Swarm not supported.

        Raises:
            NotImplemented:
        """
        raise NotImplementedError("Swarm not supported.")

    @property
    def swarm(self):
        """Swarm not supported.

        Raises:
            NotImplemented:
        """
        raise NotImplementedError("Swarm not supported.")

    def df(self) -> Dict[str, Any]:  # pylint: disable=missing-function-docstring,invalid-name
        return SystemManager(client=self.client).df()

    df.__doc__ = SystemManager.df.__doc__

    def events(self, *args, **kwargs):  # pylint: disable=missing-function-docstring
        return EventManager(client=self.client).apply(*args, **kwargs)

    events.__doc__ = EventManager.apply.__doc__

    def info(self, *args, **kwargs):  # pylint: disable=missing-function-docstring
        return SystemManager(client=self.client).info(*args, **kwargs)

    info.__doc__ = SystemManager.info.__doc__

    def login(self, *args, **kwargs):  # pylint: disable=missing-function-docstring
        return SystemManager(client=self.client).login(*args, **kwargs)

    login.__doc__ = SystemManager.login.__doc__

    def ping(self) -> bool:  # pylint: disable=missing-function-docstring
        return SystemManager(client=self.client).ping()

    ping.__doc__ = SystemManager.ping.__doc__

    def version(self, *args, **kwargs):  # pylint: disable=missing-function-docstring
        return SystemManager(client=self.client).version(*args, **kwargs)

    ping.__doc__ = SystemManager.version.__doc__

    def close(self):  # pylint: disable=missing-function-docstring
        """Close connection to service."""
        return self.client.close()

    close.__doc__ = APIClient.close.__doc__


DockerClient = PodmanClient
from_env = PodmanClient.from_env
