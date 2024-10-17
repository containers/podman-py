"""Read containers.conf file and create Podman containers with network options."""

import sys
import urllib
from pathlib import Path
from typing import Dict, Optional
import json
import logging

from podman.api import cached_property
from podman.api.path_utils import get_xdg_config_home
from podman import PodmanClient
from podman.errors import PodmanError

if sys.version_info >= (3, 11):
    from tomllib import loads as toml_loads
else:
    try:
        from tomli import loads as toml_loads
    except ImportError:
        try:
            from toml import loads as toml_loads
        except ImportError:
            from pytoml import loads as toml_loads


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
    def id(self):  # pylint: disable=invalid-name
        """str: Returns identifier for service connection."""
        return self.name

    @cached_property
    def url(self):
        """urllib.parse.ParseResult: Returns URL for service connection."""
        if self.attrs.get("uri"):
            return urllib.parse.urlparse(self.attrs.get("uri"))
        return urllib.parse.urlparse(self.attrs.get("URI"))

    @cached_property
    def identity(self):
        """Path: Returns Path to identity file for service connection."""
        if self.attrs.get("identity"):
            return Path(self.attrs.get("identity"))
        return Path(self.attrs.get("Identity"))


class PodmanConfig:
    """PodmanConfig provides a representation of the containers.conf file."""

    def __init__(self, path: Optional[str] = None):
        """Read Podman configuration from users XDG_CONFIG_HOME."""
        self.is_default = False
        if path is None:
            home = Path(get_xdg_config_home())
            self.path = home / "containers" / "podman-connections.json"
            old_toml_file = home / "containers" / "containers.conf"
            self.is_default = True
        # this elif is only for testing purposes
        elif "@@is_test@@" in path:
            test_path = path.replace("@@is_test@@", '')
            self.path = Path(test_path) / "podman-connections.json"
            old_toml_file = Path(test_path) / "containers.conf"
            self.is_default = True
        else:
            self.path = Path(path)
            old_toml_file = None

        self.attrs = {}
        if self.path.exists():
            try:
                with open(self.path, encoding='utf-8') as file:
                    self.attrs = json.load(file)
            except:  # pylint: disable=bare-except
                # if the user specifies a path, it can either be a JSON file
                # or a TOML file - so try TOML next
                try:
                    with self.path.open(encoding='utf-8') as file:
                        buffer = file.read()
                    loaded_toml = toml_loads(buffer)
                    self.attrs.update(loaded_toml)
                except Exception as e:
                    raise AttributeError(
                        "The path given is neither a JSON nor a TOML connections file"
                    ) from e

        # Read the old toml file configuration
        if self.is_default and old_toml_file and old_toml_file.exists():
            with old_toml_file.open(encoding='utf-8') as file:
                buffer = file.read()
            loaded_toml = toml_loads(buffer)
            self.attrs.update(loaded_toml)

    def __hash__(self) -> int:
        return hash(tuple(self.path.name))

    def __eq__(self, other) -> bool:
        if isinstance(other, PodmanConfig):
            return self.id == other.id and self.attrs == other.attrs
        return False

    @property
    def id(self):  # pylint: disable=invalid-name
        """Path: Returns Path() of container.conf."""
        return self.path

    @cached_property
    def services(self):
        """Dict[str, ServiceConnection]: Returns list of service connections.

            Examples:
                podman_config = PodmanConfig()
                address = podman_config.services["testing"]
                print(f"Testing service address {address}")
            """
        services: Dict[str, ServiceConnection] = {}

        # read the keys of the toml file first
        engine = self.attrs.get("engine")
        if engine:
            destinations = engine.get("service_destinations", {})
            for key in destinations:
                connection = ServiceConnection(key, attrs=destinations[key])
                services[key] = connection

        # read the keys of the json file next
        # this will ensure that if the new json file and the old toml file
        # has a connection with the same name defined, we always pick the
        # json one
        connection = self.attrs.get("Connection")
        if connection:
            destinations = connection.get("Connections", {})
            for key in destinations:
                connection = ServiceConnection(key, attrs=destinations[key])
                services[key] = connection

        return services

    @cached_property
    def active_service(self):
        """Optional[ServiceConnection]: Returns active connection."""
        # read the new json file format
        connection = self.attrs.get("Connection")
        if connection:
            active = connection.get("Default")
            destinations = connection.get("Connections", {})
            if active in destinations:
                return ServiceConnection(active, attrs=destinations[active])

        # if we are here, that means there was no default in the new json file
        engine = self.attrs.get("engine")
        if engine:
            active = engine.get("active_service")
            destinations = engine.get("service_destinations", {})
            if active in destinations:
                return ServiceConnection(active, attrs=destinations[active])

        return None

    @cached_property
    def network_options(self) -> Dict[str, list]:
        """
        Retrieves network options for all configured networks.

        Returns:
            Dict[str, list]: A dictionary where keys are network names and values are lists of options.
        """
        network_opts = {}
        network_config = self.attrs.get("network", {})
        for network_name, config in network_config.items():
            # Assuming network options are stored as 'pasta_options', 'bridge_options', etc.
            options_key = f"{network_name}_options"
            if options_key in network_config:
                network_opts[network_name] = network_config[options_key]
        return network_opts


def create_container_with_pasta(network_name: str, port_mapping: str, image: str, container_name: str, **kwargs):
    """
    Creates and starts a Podman container with specified Pasta network options.

    Args:
        network_name (str): The name of the network (e.g., 'pasta').
        port_mapping (str): The port mapping in 'host_port:container_port' format (e.g., '3128:3128').
        image (str): The container image to use.
        container_name (str): The name for the container.
        **kwargs: Additional keyword arguments for container creation.

    Returns:
        podman.containers.Container: The created and started container instance.
    """
    try:
        # Initialize Podman client
        podman_client = PodmanClient(base_url="unix://run/podman/io.podman")
        logging.debug("Podman client initialized.")

        # Read Podman configuration
        podman_config = PodmanConfig()
        logging.debug("Podman configuration loaded.")

        # Extract network options for the specified network
        network_opts = podman_config.network_options.get(network_name, [])
        logging.debug(f"Original network options for '{network_name}': {network_opts}")

        # Append the port mapping using '-T' flag
        network_opts += ["-T", port_mapping]
        logging.debug(f"Updated network options for '{network_name}': {network_opts}")

        # Create the container with network options
        logging.info(f"Creating container '{container_name}' with image '{image}' on network '{network_name}' with options {network_opts}")

        container = podman_client.containers.create(
            image=image,
            name=container_name,
            networks={network_name: {}},
            network_options={network_name: network_opts},
            **kwargs  # Include other parameters like environment variables, volumes, etc.
        )
        logging.info(f"Container '{container_name}' created successfully.")

        # Start the container
        container.start()
        logging.info(f"Container '{container_name}' started successfully.")

        return container

    except PodmanError as pe:
        logging.error(f"Podman error occurred: {pe}")
        raise
    except PermissionError as pe:
        logging.error(f"Permission error: {pe}")
        raise
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        raise


if __name__ == "__main__":
    try:
        # Define container parameters
        network_name = "pasta"              # Replace with your network name if different
        port_mapping = "3128:3128"          # Host port : Container port
        image = "your-image"                 # Replace with your actual image
        container_name = "your-container"    # Replace with your desired container name

        # Additional parameters (if any)
        additional_kwargs = {
            # Example: Environment variables
            # "environment": {"ENV_VAR": "value"},
            # Example: Volume mounts
            # "volumes": {"/host/path": {"bind": "/container/path", "mode": "rw"}},
        }

        # Create and start the container
        container = create_container_with_pasta(
            network_name=network_name,
            port_mapping=port_mapping,
            image=image,
            container_name=container_name,
            **additional_kwargs
        )

        print(f"Container '{container.name}' is running with TCP namespace forwarding from host port {port_mapping.split(':')[0]} to container port {port_mapping.split(':')[1]}.")

    except Exception as e:
        print(f"Failed to create and start container: {e}")
