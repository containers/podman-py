"""Classes to support Internet Protocol Address Management.

Provided for compatibility
"""

from typing import Any
from collections.abc import Mapping


class IPAMPool(dict):
    """Collect IP Network configuration."""

    def __init__(
        self,
        subnet: str | None = None,
        iprange: str | None = None,
        gateway: str | None = None,
        aux_addresses: Mapping[str, str] | None = None,
    ):
        """Create IPAMPool.

        Args:
            subnet: IP subnet in CIDR format for this network.
            iprange: IP range in CIDR format for endpoints on this network.
            gateway: IP gateway address for this network.
            aux_addresses: Ignored.
        """
        super().__init__()
        self.update(
            {
                "AuxiliaryAddresses": aux_addresses,
                "Gateway": gateway,
                "IPRange": iprange,
                "Subnet": subnet,
            }
        )


class IPAMConfig(dict):
    """Collect IP Address configuration."""

    def __init__(
        self,
        driver: str | None = "host-local",
        pool_configs: list[IPAMPool] | None = None,
        options: Mapping[str, Any] | None = None,
    ):
        """Create IPAMConfig.

        Args:
            driver: Network driver to use with this network.
            pool_configs: Network and endpoint information. Podman only supports one pool.
            options: Options to provide to the Network driver.
        """
        super().__init__()
        self.update(
            {
                "Config": pool_configs or [],
                "Driver": driver,
                "Options": options or {},
            }
        )
