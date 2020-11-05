"""podman.containers unit tests"""

import unittest
import urllib.parse
from unittest import mock

import podman.containers
import podman.errors
import podman.system


class TestContainers(unittest.TestCase):
    """Test the containers calls."""

    def setUp(self):
        super().setUp()
        self.request = mock.MagicMock()
        self.response = mock.MagicMock()
        self.request.return_value = self.response
        self.api = mock.MagicMock()
        self.api.get = self.request
        self.api.post = self.request
        self.api.delete = self.request
        self.api.quote = urllib.parse.quote

    def test_list_containers(self):
        """test list call"""
        mock_read = mock.MagicMock()
        mock_read.return_value = b'[{"Id": "foo"}]'
        self.response.status = 200
        self.response.read = mock_read
        expected = [{"Id": "foo"}]
        ret = podman.containers.list_containers(self.api)
        self.assertEqual(ret, expected)
        self.request.assert_called_once_with("/containers/json", {})

    def test_list_containers_all(self):
        """test list call"""
        mock_read = mock.MagicMock()
        mock_read.return_value = b'[{"Id": "foo"}]'
        self.response.status = 200
        self.response.read = mock_read
        expected = [{"Id": "foo"}]
        ret = podman.containers.list_containers(self.api, True)
        self.assertEqual(ret, expected)
        self.request.assert_called_once_with("/containers/json", {"all": True})
