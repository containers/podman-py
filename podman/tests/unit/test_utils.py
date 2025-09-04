import unittest

from unittest.mock import patch, MagicMock

from podman.tests import utils


class TestPodmanVersion(unittest.TestCase):
    @patch('podman.tests.utils.subprocess.Popen')
    def test_podman_version(self, mock_popen):
        mock_proc = MagicMock()
        mock_proc.stdout.read.return_value = b'5.6.0'
        mock_popen.return_value.__enter__.return_value = mock_proc
        self.assertEqual(utils.podman_version(), (5, 6, 0))

    @patch('podman.tests.utils.subprocess.Popen')
    def test_podman_version_dev(self, mock_popen):
        mock_proc = MagicMock()
        mock_proc.stdout.read.return_value = b'5.6.0-dev'
        mock_popen.return_value.__enter__.return_value = mock_proc
        self.assertEqual(utils.podman_version(), (5, 6, 0))

    @patch('podman.tests.utils.subprocess.Popen')
    def test_podman_version_four_digits(self, mock_popen):
        mock_proc = MagicMock()
        mock_proc.stdout.read.return_value = b'5.6.0.1'
        mock_popen.return_value.__enter__.return_value = mock_proc
        self.assertEqual(utils.podman_version(), (5, 6, 0))

    @patch('podman.tests.utils.subprocess.Popen')
    def test_podman_version_release_candidate(self, mock_popen):
        mock_proc = MagicMock()
        mock_proc.stdout.read.return_value = b'5.6.0-rc1'
        mock_popen.return_value.__enter__.return_value = mock_proc
        self.assertEqual(utils.podman_version(), (5, 6, 0))

    @patch('podman.tests.utils.subprocess.Popen')
    def test_podman_version_none(self, mock_popen):
        mock_proc = MagicMock()
        mock_proc.stdout.read.return_value = b''
        mock_popen.return_value.__enter__.return_value = mock_proc
        with self.assertRaises(RuntimeError) as context:
            utils.podman_version()
        self.assertEqual(str(context.exception), "Unable to detect podman version. Got \"\"")
