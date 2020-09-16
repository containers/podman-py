import unittest

import podman
from podman import ApiConnection, system


class TestSystem(unittest.TestCase):
    def test_000_version(self):
        with ApiConnection("ssh://localhost//") as api:
            self.assertRaises(NotImplementedError, system.version, api)