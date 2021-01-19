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

    def test_inspect(self):
        """test inspect call"""
        mock_read = mock.MagicMock()
        mock_read.return_value = b'{"Id": "foo"}'
        self.response.status = 200
        self.response.read = mock_read
        expected = {"Id": "foo"}
        ret = podman.containers.inspect(self.api, 'foo')
        self.assertEqual(ret, expected)
        self.request.assert_called_once_with("/containers/foo/json")

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

    def test_kill(self):
        """test kill call"""
        mock_read = mock.MagicMock()
        mock_read.return_value = b''
        self.response.status = 204
        self.response.read = mock_read
        ret = podman.containers.kill(self.api, 'foo')
        self.assertTrue(ret)
        self.request.assert_called_once_with(
            "/containers/foo/kill", params={}, headers={'content-type': 'application/json'}
        )

    def test_kill_signal(self):
        """test kill call with signal"""
        mock_read = mock.MagicMock()
        mock_read.return_value = b''
        self.response.status = 200
        self.response.read = mock_read
        ret = podman.containers.kill(self.api, 'foo', 'HUP')
        self.assertTrue(ret)
        self.request.assert_called_once_with(
            "/containers/foo/kill",
            params={'signal': 'HUP'},
            headers={'content-type': 'application/json'},
        )

    def test_remove(self):
        """test remove call"""
        mock_read = mock.MagicMock()
        mock_read.return_value = b''
        self.response.status = 204
        self.response.read = mock_read
        ret = podman.containers.remove(self.api, 'foo')
        self.assertTrue(ret)
        self.request.assert_called_once_with("/containers/foo", {})

    def test_remove_options(self):
        """test remove call with options"""
        mock_read = mock.MagicMock()
        mock_read.return_value = b''
        self.response.status = 204
        self.response.read = mock_read
        ret = podman.containers.remove(self.api, 'foo', True, True)
        self.assertTrue(ret)
        self.request.assert_called_once_with("/containers/foo", {'force': True, 'v': True})
