import unittest
import urllib.parse
from pathlib import Path
from unittest import mock
from unittest.mock import MagicMock

from podman.domain.config import PodmanConfig


class PodmanConfigTestCase(unittest.TestCase):
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
            return PodmanConfigTestCase.opener(self, *args, **kwargs)

        self.mocked_open = mocked_open

    def test_connections(self):
        with mock.patch.multiple(Path, open=self.mocked_open, exists=MagicMock(return_value=True)):
            config = PodmanConfig("/home/developer/containers.conf")

            self.assertEqual(config.active_service.id, "testing")

            expected = urllib.parse.urlparse("ssh://qe@localhost:2222/run/podman/podman.sock")
            self.assertEqual(config.active_service.url, expected)
            self.assertEqual(config.services["production"].identity, Path("/home/root/.ssh/id_rsa"))

            PodmanConfigTestCase.opener.assert_called_with(
                Path("/home/developer/containers.conf"), encoding='utf-8'
            )


if __name__ == '__main__':
    unittest.main()
