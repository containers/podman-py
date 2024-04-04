import unittest
import urllib.parse
import json
import os
import tempfile
from pathlib import Path
from unittest import mock
from unittest.mock import MagicMock
from podman.domain.config import PodmanConfig


class PodmanConfigTestCaseDefault(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

        # Data to be written to the JSON file
        self.data_json = """
{
  "Connection": {
    "Default": "testing_json",
    "Connections": {
      "testing_json": {
        "URI": "ssh://qe@localhost:2222/run/podman/podman.sock",
        "Identity": "/home/qe/.ssh/id_rsa"
      },
      "production": {
        "URI": "ssh://root@localhost:22/run/podman/podman.sock",
        "Identity": "/home/root/.ssh/id_rsajson"
      }
    }
  },
  "Farm": {}
}
"""

        # Data to be written to the TOML file
        self.data_toml = """
[containers]
  log_size_max = -1
  pids_limit = 2048
  userns_size = 65536

[engine]
  num_locks = 2048
  active_service = "testing"
  stop_timeout = 10
  [engine.service_destinations]
    [engine.service_destinations.production]
      uri = "ssh://root@localhost:22/run/podman/podman.sock"
      identity = "/home/root/.ssh/id_rsa"
    [engine.service_destinations.testing]
      uri = "ssh://qe@localhost:2222/run/podman/podman.sock"
      identity = "/home/qe/.ssh/id_rsa"

[network]
"""

        # Define the file path
        self.path_json = os.path.join(self.temp_dir, 'podman-connections.json')
        self.path_toml = os.path.join(self.temp_dir, 'containers.conf')

        # Write data to the JSON file
        j_data = json.loads(self.data_json)
        with open(self.path_json, 'w+') as file_json:
            json.dump(j_data, file_json)

        # Write data to the TOML file
        with open(self.path_toml, 'w+') as file_toml:
            # toml.dump(self.data_toml, file_toml)
            file_toml.write(self.data_toml)

    def test_connections(self):
        config = PodmanConfig("@@is_test@@" + self.temp_dir)

        self.assertEqual(config.active_service.id, "testing_json")

        expected = urllib.parse.urlparse("ssh://qe@localhost:2222/run/podman/podman.sock")
        self.assertEqual(config.active_service.url, expected)
        self.assertEqual(config.services["production"].identity, Path("/home/root/.ssh/id_rsajson"))


class PodmanConfigTestCaseTOML(unittest.TestCase):
    opener = mock.mock_open(
        read_data="""
[containers]
  log_size_max = -1
  pids_limit = 2048
  userns_size = 65536

[engine]
  num_locks = 2048
  active_service = "testing"
  stop_timeout = 10
  [engine.service_destinations]
    [engine.service_destinations.production]
      uri = "ssh://root@localhost:22/run/podman/podman.sock"
      identity = "/home/root/.ssh/id_rsa"
    [engine.service_destinations.testing]
      uri = "ssh://qe@localhost:2222/run/podman/podman.sock"
      identity = "/home/qe/.ssh/id_rsa"

[network]
"""
    )

    def setUp(self) -> None:
        super().setUp()

        def mocked_open(self, *args, **kwargs):
            return PodmanConfigTestCaseTOML.opener(self, *args, **kwargs)

        self.mocked_open = mocked_open

    def test_connections(self):
        with mock.patch.multiple(Path, open=self.mocked_open, exists=MagicMock(return_value=True)):
            config = PodmanConfig("/home/developer/containers.conf")

            self.assertEqual(config.active_service.id, "testing")

            expected = urllib.parse.urlparse("ssh://qe@localhost:2222/run/podman/podman.sock")
            self.assertEqual(config.active_service.url, expected)
            self.assertEqual(config.services["production"].identity, Path("/home/root/.ssh/id_rsa"))

            PodmanConfigTestCaseTOML.opener.assert_called_with(
                Path("/home/developer/containers.conf"), encoding='utf-8'
            )


class PodmanConfigTestCaseJSON(unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()

        self.temp_dir = tempfile.mkdtemp()
        self.data = """
{
  "Connection": {
    "Default": "testing",
    "Connections": {
      "testing": {
        "URI": "ssh://qe@localhost:2222/run/podman/podman.sock",
        "Identity": "/home/qe/.ssh/id_rsa"
      },
      "production": {
        "URI": "ssh://root@localhost:22/run/podman/podman.sock",
        "Identity": "/home/root/.ssh/id_rsa"
      }
    }
  },
  "Farm": {}
}
"""

        self.path = os.path.join(self.temp_dir, 'podman-connections.json')
        # Write data to the JSON file
        data = json.loads(self.data)
        with open(self.path, 'w+') as file:
            json.dump(data, file)

    def test_connections(self):
        config = PodmanConfig(self.path)

        self.assertEqual(config.active_service.id, "testing")

        expected = urllib.parse.urlparse("ssh://qe@localhost:2222/run/podman/podman.sock")
        self.assertEqual(config.active_service.url, expected)
        self.assertEqual(config.services["production"].identity, Path("/home/root/.ssh/id_rsa"))


if __name__ == '__main__':
    unittest.main()
