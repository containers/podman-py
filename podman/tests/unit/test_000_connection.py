import unittest

import podman
from podman import ApiConnection


class TestConnection(unittest.TestCase):
    """Test the ApiConnection() object."""

    def test_000_ctor(self):
        with podman.ApiConnection("unix:///") as api:
            pass

    def test_001_ctor(self):
        self.assertRaises(ValueError, podman.ApiConnection, "")

    def test_001_ctor(self):
        self.assertRaises(ValueError, podman.ApiConnection,
                          "tcp://localhost//")

    def test_000_join(self):
        with podman.ApiConnection("unix:///") as api:
            path = api.join("/unittest")
            self.assertEqual("{}/unittest".format(api.base), path)

    def test_001_join(self):
        with podman.ApiConnection("unix:///") as api:
            path = api.join("/unittest", {"q": "p"})
            self.assertEqual("{}/unittest?q=p".format(api.base), path)