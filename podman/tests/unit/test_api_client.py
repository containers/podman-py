"""Unit tests for APIClient credential storage."""

import unittest

from podman.api.client import APIClient


class TestAPIClientCredentials(unittest.TestCase):
    """Test APIClient registry credential storage and retrieval."""

    def setUp(self):
        self.client = APIClient(base_url="http+unix:///run/podman/podman.sock")

    def test_set_and_get_registry_auth(self):
        """Test setting and retrieving registry credentials."""
        auth_config = {
            "username": "testuser",
            "password": "testpass",
        }
        registry = "https://quay.io/v2"

        self.client.set_registry_auth(registry, auth_config)
        retrieved = self.client.get_registry_auth()

        self.assertEqual(retrieved[registry], auth_config)

    def test_set_multiple_registries(self):
        """Test storing credentials for multiple registries."""
        auth1 = {"username": "user1", "password": "pass1"}
        auth2 = {"username": "user2", "password": "pass2"}

        self.client.set_registry_auth("https://quay.io/v2", auth1)
        self.client.set_registry_auth("docker.io", auth2)

        retrieved = self.client.get_registry_auth()
        self.assertEqual(len(retrieved), 2)
        self.assertEqual(retrieved["https://quay.io/v2"], auth1)
        self.assertEqual(retrieved["docker.io"], auth2)

    def test_clear_specific_registry(self):
        """Test clearing credentials for a specific registry."""
        auth_config = {"username": "user", "password": "pass"}
        registry = "https://quay.io/v2"

        self.client.set_registry_auth(registry, auth_config)
        self.client.clear_registry_auth(registry)

        retrieved = self.client.get_registry_auth()
        self.assertNotIn(registry, retrieved)

    def test_clear_all_registries(self):
        """Test clearing all registry credentials."""
        self.client.set_registry_auth(
            "https://quay.io/v2", {"username": "user1", "password": "pass1"}
        )
        self.client.set_registry_auth("docker.io", {"username": "user2", "password": "pass2"})

        self.client.clear_registry_auth()

        retrieved = self.client.get_registry_auth()
        self.assertEqual(len(retrieved), 0)

    def test_get_returns_copy(self):
        """Test that get_registry_auth returns a copy, not the internal dict."""
        auth_config = {"username": "user", "password": "pass"}
        self.client.set_registry_auth("https://quay.io/v2", auth_config)

        retrieved = self.client.get_registry_auth()
        retrieved["new_registry"] = {"username": "newuser", "password": "newpass"}

        # Verify the internal dict wasn't modified
        internal = self.client._registry_auth
        self.assertNotIn("new_registry", internal)


if __name__ == '__main__':
    unittest.main()
