import unittest
from unittest.mock import MagicMock
from unittest.mock import Mock
from unittest.mock import patch
from podman.endpoints.lib import Endpoint


class EndpointTestCase(unittest.TestCase):
    """Test the ApiConnection() object."""

    def test_domain_format(self):
        class FooEndpoint(Endpoint):
            domain = '/foo'
            api_ver = '1.0'
        c = Mock()
        e = TestEndpoint(c)
        self.assertTrue(e.get_domain(), '/1.0/foo')

    def test_domain_is_none(self):
        class FooEndpoint(Endpoint):
            api_ver = '1.0'
        c = Mock()
        e = TestEndpoint(c)
        with self.assertRaises(TypeError):
            e.get_domain()

    def test_api_ver_is_none(self):
        class FooEndpoint(Endpoint):
            domain = '/foo'
        c = Mock()
        e = TestEndpoint(c)
        with self.assertRaises(TypeError):
            e.get_domain()

    def test_path_format(self):
        class FooEndpoint(Endpoint):
            domain = '/foo'
            api_ver = '1.0'
        class BarEndpoint(FooEndpoint):
            path = '/bar'
        c = Mock()
        e = BarEndpoint(c)
        self.assertTrue(e.get_path(), '/1.0/foo/bar')
