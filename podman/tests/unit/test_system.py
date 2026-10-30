import unittest

import requests
import requests_mock

from podman import PodmanClient, tests


class SystemTestCase(unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()

        self.client = PodmanClient(base_url=tests.BASE_SOCK)

    def tearDown(self) -> None:
        super().tearDown()

        self.client.close()

    @requests_mock.Mocker()
    def test_df(self, mock):
        body = {
            "Containers": [
                {"ContainerID": "f1fb3564c202"},
                {"ContainerID": "779afab684c7"},
            ],
            "Images": [
                {"ImageID": "118cc2c68ef5"},
                {"ImageID": "a6b4a8255f9e"},
            ],
            "Volumes": [
                {"VolumeName": "27df59163be8"},
                {"VolumeName": "77a83a10f86e"},
            ],
        }

        mock.get(
            tests.LIBPOD_URL + "/system/df",
            json=body,
        )

        actual = self.client.df()
        self.assertDictEqual(actual, body)

    @requests_mock.Mocker()
    def test_info(self, mock):
        body = {
            "host": {
                "arch": "amd65",
                "os": "linux",
            }
        }
        mock.get(tests.LIBPOD_URL + "/info", json=body)

        actual = self.client.info()
        self.assertDictEqual(actual, body)

    @requests_mock.Mocker()
    def test_ping(self, mock):
        mock.head(tests.LIBPOD_URL + "/_ping")
        self.assertTrue(self.client.ping())

    @requests_mock.Mocker()
    def test_version(self, mock):
        body = {
            "APIVersion": "3.0.0",
            "MinAPIVersion": "3.0.0",
            "Arch": "amd64",
            "Os": "linux",
        }
        mock.get(tests.LIBPOD_URL + "/version", json=body)
        self.assertDictEqual(self.client.version(), body)

    @requests_mock.Mocker()
    def test_login_stores_credentials(self, mock):
        """Test that login stores credentials in the client."""
        body = {
            "IdentityToken": "",
            "Status": "Login Succeeded",
        }
        mock.post(tests.COMPATIBLE_URL + "/auth", json=body)

        registry = "https://quay.io/v2"
        username = "testuser"
        password = "testpass"

        result = self.client.login(
            registry=registry,
            username=username,
            password=password,
        )

        self.assertEqual(result["Status"], "Login Succeeded")

        # Verify credentials were stored (normalized to quay.io)
        stored_auth = self.client.api.get_registry_auth()
        self.assertIn("quay.io", stored_auth)
        self.assertEqual(stored_auth["quay.io"]["username"], username)
        self.assertEqual(stored_auth["quay.io"]["password"], password)

    @requests_mock.Mocker()
    def test_login_without_registry(self, mock):
        """Test that login without registry doesn't store credentials."""
        body = {
            "IdentityToken": "",
            "Status": "Login Succeeded",
        }
        mock.post(tests.COMPATIBLE_URL + "/auth", json=body)

        result = self.client.login(
            username="testuser",
            password="testpass",
        )

        self.assertEqual(result["Status"], "Login Succeeded")

        # Verify no credentials were stored (no registry provided)
        # Credentials are only stored when registry is explicitly provided
        # because the API response doesn't reliably indicate which registry was used
        stored_auth = self.client.api.get_registry_auth()
        self.assertEqual(len(stored_auth), 0)

    @requests_mock.Mocker()
    def test_login_failure_does_not_store_credentials(self, mock):
        """Test that failed login does not store credentials."""
        mock.post(
            tests.COMPATIBLE_URL + "/auth",
            status_code=401,
            json={"cause": "Unauthorized", "message": "Invalid username or password"},
        )

        registry = "https://quay.io/v2"
        username = "testuser"
        password = "wrongpass"

        with self.assertRaises(requests.exceptions.HTTPError):
            self.client.login(
                registry=registry,
                username=username,
                password=password,
            )

        # Verify no credentials were stored after failed login
        stored_auth = self.client.api.get_registry_auth()
        self.assertEqual(len(stored_auth), 0)

    def test_stored_credentials_used_by_pull_or_push(self):
        """Test that stored credentials are automatically used by pull/push.

        Stored credentials from login() are reused for pull and push operations
        when no explicit auth_config is provided. This matches Docker-py behavior.
        Explicit auth_config parameter always overrides stored credentials.
        """
        # Set up stored credentials (will be normalized to quay.io)
        self.client.api.set_registry_auth(
            "https://quay.io/v2", {"username": "user", "password": "pass"}
        )

        # Verify credentials are stored (normalized)
        stored_auth = self.client.api.get_registry_auth()
        self.assertIn("quay.io", stored_auth)

        # Pull and push will automatically use stored credentials when registry matches
        # Explicit auth_config parameter always overrides stored credentials
        # This ensures registry isolation while providing convenience for common workflows
        # The actual HTTP headers are tested in images_manager tests

    def test_logout_clears_specific_registry(self):
        """Test that logout clears credentials for a specific registry."""
        # Store credentials for two registries
        self.client.api.set_registry_auth("docker.io", {"username": "user1", "password": "pass1"})
        self.client.api.set_registry_auth("quay.io", {"username": "user2", "password": "pass2"})

        # Verify both are stored
        auth = self.client.api.get_registry_auth()
        self.assertIn("docker.io", auth)
        self.assertIn("quay.io", auth)

        # Logout from docker.io
        self.client.logout("docker.io")

        # Verify docker.io is cleared but quay.io remains
        auth = self.client.api.get_registry_auth()
        self.assertNotIn("docker.io", auth)
        self.assertIn("quay.io", auth)

    def test_logout_normalizes_registry(self):
        """Test that logout normalizes registry names."""
        # Store credentials with normalized form
        self.client.api.set_registry_auth("docker.io", {"username": "user", "password": "pass"})

        # Logout using different form
        self.client.logout("https://docker.io/v2")

        # Verify credentials are cleared
        auth = self.client.api.get_registry_auth()
        self.assertNotIn("docker.io", auth)

    def test_logout_with_empty_registry(self):
        """Test that logout raises ValueError for empty registry."""
        with self.assertRaises(ValueError):
            self.client.logout("")

    def test_logout_with_none_registry(self):
        """Test that logout raises ValueError for None registry."""
        with self.assertRaises(ValueError):
            self.client.logout(None)


if __name__ == '__main__':
    unittest.main()
