"""Holds TLS configuration."""


class TLSConfig:
    """TLS configuration.

    Provided for compatibility, currently ignored.
    """

    # pylint: disable=too-few-public-methods

    def __init__(self, *args, **kwargs):
        """Initialize TLSConfig.

        Keywords may be delegated to the SSH client configuration.

        Keyword Args:
                client_cert (tuple of str): Path to client cert, path to client key.
                ca_cert (str): Path to CA cert file.
                verify (bool or str): This can be False, or a path to a CA cert file.
                ssl_version (int): Ignored.
                assert_hostname (bool): Verify the hostname of the server.
        """

    @staticmethod
    def configure_client(client) -> None:
        """Add TLS configuration to the client."""
        # TODO Somehow work this into SSHAdapter(), if/when someone complains.
