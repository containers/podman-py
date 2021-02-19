"""Holds TLS configuration."""


class TLSConfig:
    """TLS configuration.

    Args:
        client_cert (tuple of str): Path to client cert, path to client key.
        ca_cert (str): Path to CA cert file.
        verify (bool or str): This can be ``False`` or a path to a CA cert
            file.
        ssl_version (int): A valid `SSL version`_.
        assert_hostname (bool): Verify the hostname of the server.

    .. _`SSL version`:
        https://docs.python.org/3.5/library/ssl.html#ssl.PROTOCOL_TLSv1
    """

    # pylint: disable=too-few-public-methods

    def __init__(self, **kwargs):
        _ = kwargs

    def configure_client(self, client) -> None:
        """Add TLS configuration to the client."""
        _ = client
