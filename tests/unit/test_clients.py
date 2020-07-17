import unittest
from unittest.mock import MagicMock
from unittest.mock import Mock
from unittest.mock import patch
# from podman.clients import Podman
from podman.clients.lib import Client


class ClientTestCase(unittest.TestCase):
    """Test the ApiConnection() object."""

    @patch('podman.clients.lib.HTTPConnectionSocket', new=Mock())
    def test_http_call_sequence(self):
        c = Client('unix://localhost/foo/bar')
        c.request("GET", "/some/path", None, {})
        c.http.request.assert_called_once()
        c.http.getresponse.assert_called_once()
