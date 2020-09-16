"""Connection unit tests"""
import unittest
from podman import ApiConnection


class TestConnection(unittest.TestCase):
    """Test the ApiConnection() object."""

    def test_000_ctor(self):
        """test unix socket"""
        with ApiConnection("unix:///") as _:
            pass

    def test_001_ctor(self):
        """test failed no connection"""
        self.assertRaises(ValueError, ApiConnection, "")

    def test_002_ctor(self):
        """test failed tcp connection"""
        self.assertRaises(ValueError, ApiConnection,
                          "tcp://localhost//")

    def test_000_join(self):
        """test api join"""
        with ApiConnection("unix:///") as api:
            path = api.join("/unittest")
            self.assertEqual("{}/unittest".format(api.base), path)

    def test_001_join(self):
        """test api join with params"""
        with ApiConnection("unix:///") as api:
            path = api.join("/unittest", {"q": "p"})
            self.assertEqual("{}/unittest?q=p".format(api.base), path)
