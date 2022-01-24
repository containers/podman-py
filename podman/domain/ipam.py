"""Classes to support Internet Protocol Address Management.

Provided for compatibility
"""
from typing import Any, List, Mapping, Optional


class IPAMPool(dict):
    """Collect IP Network configuration."""

    def __init__(
        self,
        subnet: Optional[str] = None,
        iprange: Optional[str] = None,
        gateway: Optional[str] = None,
        aux_addresses: Optional[Mapping[str, str]] = None,
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
        driver: Optional[str] = "default",
        pool_configs: Optional[List[IPAMPool]] = None,
        options: Optional[Mapping[str, Any]] = None,
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
