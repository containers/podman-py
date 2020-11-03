"""system unit tests"""
import unittest

from podman import ApiConnection, system


class TestSystem(unittest.TestCase):
    """Test the system calls"""

    def test_000_version(self):
        """test version call"""
        with ApiConnection("ssh://localhost//") as api:
            self.assertRaises(NotImplementedError, system.version, api)
