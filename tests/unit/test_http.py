import unittest
from podman.http import HTTPConnectionSocket
from podman.exceptions.http import SocketFileNotFound
from podman.exceptions.http import SchemaNotSupported


class HTTPConnectionSocketTestCase(unittest.TestCase):
    """Test the ApiConnection() object."""

    def test_uri_cannot_be_blank(self):
        with self.assertRaises(TypeError):
            HTTPConnectionSocket(None)

    def test_schema_not_supported(self):
        with self.assertRaises(SchemaNotSupported):
            HTTPConnectionSocket('http://foo/bar')\
                .connect()

    def test_uri_does_not_exist(self):
        with self.assertRaises(SocketFileNotFound):
            HTTPConnectionSocket('unix://foo/bar')\
                .connect()
