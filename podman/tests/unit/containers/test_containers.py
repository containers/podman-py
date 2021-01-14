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

    def test_checkpoint(self):
        """test checkpoint call"""
        mock_read = mock.MagicMock()
        mock_read.return_value = b''
        self.response.status = 200
        self.response.read = mock_read
        expected = b''
        ret = podman.containers.checkpoint(self.api, 'foo')
        self.assertEqual(ret, expected)
        self.request.assert_called_once_with(
            "/containers/foo/checkpoint", params={}, headers={'content-type': 'application/json'}
        )

    def test_checkpoint_options(self):
        """test checkpoint call with options"""
        mock_read = mock.MagicMock()
        mock_read.return_value = b''
        self.response.status = 200
        self.response.read = mock_read
        expected = b''
        ret = podman.containers.checkpoint(self.api, 'foo', False, False, False, False, False)
        self.assertEqual(ret, expected)
        params = {
            'export': False,
            'ignoreRootFS': False,
            'keep': False,
            'leaveRunning': False,
            'tcpEstablished': False,
        }
        self.request.assert_called_once_with(
            "/containers/foo/checkpoint",
            params=params,
            headers={'content-type': 'application/json'},
        )

    def test_copy(self):
        """test copy call"""
        mock_read = mock.MagicMock()
        self.response.status = 200
        self.response.read = mock_read
        ret = podman.containers.copy(self.api, 'foo', '/foo.tar', False)
        self.assertTrue(ret)
        params = {'path': '/foo.tar', 'pause': False}
        self.request.assert_called_once_with(
            "/containers/foo/copy", params=params, headers={'content-type': 'application/json'}
        )

    def test_container_exists(self):
        """test checkpoint call"""
        self.request.side_effect = [mock.MagicMock(), podman.errors.NotFoundError('')]
        ret = podman.containers.container_exists(self.api, 'foo')
        self.assertTrue(ret)
        ret = podman.containers.container_exists(self.api, 'foo')
        self.assertFalse(ret)
        calls = [
            mock.call('/containers/foo/exists'),
            mock.call('/containers/foo/exists'),
        ]
        self.request.assert_has_calls(calls)

    def test_create(self):
        """test create call"""
        self.response.status = 201
        ret = podman.containers.create(self.api, {'container': 'data'})
        self.assertTrue(ret)
        params = {'container': 'data'}
        self.request.assert_called_once_with(
            "/containers/create", params=params, headers={'content-type': 'application/json'}
        )

    def test_export(self):
        """test export call"""
        mock_read = mock.MagicMock()
        mock_read.return_value = b''
        self.response.status = 200
        self.response.read = mock_read
        ret = podman.containers.export(self.api, 'foo')
        self.assertEqual(ret, b'')
        self.request.assert_called_once_with("/containers/foo/export")

    def test_healthcheck(self):
        """test healthcheck call"""
        mock_read = mock.MagicMock()
        mock_read.return_value = b'{"data": "stuff"}'
        self.response.status = 200
        self.response.read = mock_read
        ret = podman.containers.healthcheck(self.api, 'foo')
        self.assertEqual(ret, {'data': 'stuff'})
        self.request.assert_called_once_with("/containers/foo/healthcheck")

    def test_init(self):
        """test init call"""
        self.response.status = 204
        ret = podman.containers.init(self.api, 'foo')
        self.assertTrue(ret)
        self.request.assert_called_once_with("/containers/foo/init")

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

    def test_logs(self):
        """test logs call"""
        self.assertRaises(NotImplementedError, podman.containers.logs, self.api, 'foo')

    def test_mount(self):
        """test mount call"""
        mock_read = mock.MagicMock()
        mock_read.return_value = b'"/stuff"'
        self.response.status = 200
        self.response.read = mock_read
        ret = podman.containers.mount(self.api, 'foo')
        self.assertEqual(ret, '/stuff')
        self.request.assert_called_once_with(
            "/containers/foo/mount", headers={'content-type': 'application/json'}
        )

    def test_pause(self):
        """test pause call"""
        mock_read = mock.MagicMock()
        mock_read.return_value = b''
        self.response.status = 204
        self.response.read = mock_read
        ret = podman.containers.pause(self.api, 'foo')
        self.assertTrue(ret)
        self.request.assert_called_once_with(
            "/containers/foo/pause", headers={'content-type': 'application/json'}
        )

    def test_prune(self):
        """test prune call"""
        mock_read = mock.MagicMock()
        mock_read.return_value = b'[{"Id": "foo"}]'
        self.response.status = 200
        self.response.read = mock_read
        ret = podman.containers.prune(self.api, 'foo')
        self.assertEqual(ret, [{"Id": "foo"}])
        self.request.assert_called_once_with(
            "/containers/foo/prune", params={}, headers={'content-type': 'application/json'}
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

    def test_resize(self):
        """test resize call"""
        mock_read = mock.MagicMock()
        mock_read.return_value = b'{}'
        self.response.status = 200
        self.response.read = mock_read
        ret = podman.containers.resize(self.api, 'foo', 80, 80)
        self.assertEqual(ret, {})
        self.request.assert_called_once_with(
            "/containers/foo/resize",
            params={'h': 80, 'w': 80},
            headers={'content-type': 'application/json'},
        )

    def test_restart(self):
        """test restart call"""
        mock_read = mock.MagicMock()
        mock_read.return_value = b''
        self.response.status = 204
        self.response.read = mock_read
        ret = podman.containers.restart(self.api, 'foo')
        self.assertTrue(ret)
        self.request.assert_called_once_with(
            "/containers/foo/restart", params={}, headers={'content-type': 'application/json'}
        )

    def test_restore(self):
        """test restore call"""
        mock_read = mock.MagicMock()
        mock_read.return_value = b''
        self.response.status = 204
        self.response.read = mock_read
        ret = podman.containers.restore(self.api, 'foo')
        self.assertEqual(ret, b'')
        self.request.assert_called_once_with(
            "/containers/foo/restore", params={}, headers={'content-type': 'application/json'}
        )

    def test_show_mounted(self):
        """test show mounted call"""
        mock_read = mock.MagicMock()
        mock_read.return_value = b'{"Id": "foo"}'
        self.response.status = 200
        self.response.read = mock_read
        ret = podman.containers.show_mounted(self.api)
        self.assertEqual(ret, {"Id": "foo"})
        self.request.assert_called_once_with("/containers/showmounted")

    def test_start(self):
        """test start call"""
        mock_read = mock.MagicMock()
        mock_read.return_value = b''
        self.response.status = 204
        self.response.read = mock_read
        ret = podman.containers.start(self.api, 'foo')
        self.assertTrue(ret)
        self.request.assert_called_once_with(
            "/containers/foo/start", params={}, headers={'content-type': 'application/json'}
        )

    def test_stats(self):
        """test stats call"""
        mock_read = mock.MagicMock()
        mock_read.return_value = b'""'
        self.response.status = 200
        self.response.read = mock_read
        ret = podman.containers.stats(self.api, stream=False)
        self.assertEqual(ret, '')
        params = {'stream': False}
        self.request.assert_called_once_with("/containers/stats", params=params)

    def test_stats_stream(self):
        """test stream call with stream"""
        mock_read = mock.MagicMock()
        mock_read.return_value = b''
        self.response.status = 200
        self.response.read = mock_read
        ret = podman.containers.stats(self.api, 'foo', True)
        self.assertEqual(ret, self.response)
        params = {'stream': True, 'containers': 'foo'}
        self.request.assert_called_once_with("/containers/stats", params=params)

    def test_stop(self):
        """test stop call"""
        mock_read = mock.MagicMock()
        mock_read.return_value = b''
        self.response.status = 204
        self.response.read = mock_read
        ret = podman.containers.stop(self.api, 'foo')
        self.assertTrue(ret)
        self.request.assert_called_once_with(
            "/containers/foo/stop", params={}, headers={'content-type': 'application/json'}
        )

    def test_top(self):
        """test top call"""
        mock_read = mock.MagicMock()
        mock_read.return_value = b'""'
        self.response.status = 200
        self.response.read = mock_read
        ret = podman.containers.top(self.api, 'foo', stream=False)
        self.assertEqual(ret, '')
        params = {'stream': False}
        self.request.assert_called_once_with("/containers/foo/top", params=params)

    def test_top_stream(self):
        """test top call with stream"""
        mock_read = mock.MagicMock()
        mock_read.return_value = b'""'
        self.response.status = 200
        self.response.read = mock_read
        ret = podman.containers.top(self.api, 'foo', '-a')
        self.assertEqual(ret, self.response)
        params = {'stream': True, 'ps_args': '-a'}
        self.request.assert_called_once_with("/containers/foo/top", params=params)

    def test_unmount(self):
        """test unmount call"""
        mock_read = mock.MagicMock()
        mock_read.return_value = b''
        self.response.status = 204
        self.response.read = mock_read
        ret = podman.containers.unmount(self.api, 'foo')
        self.assertTrue(ret)
        self.request.assert_called_once_with(
            "/containers/foo/unmount", headers={'content-type': 'application/json'}
        )

    def test_unpause(self):
        """test unpause call"""
        mock_read = mock.MagicMock()
        mock_read.return_value = b''
        self.response.status = 204
        self.response.read = mock_read
        ret = podman.containers.unpause(self.api, 'foo')
        self.assertTrue(ret)
        self.request.assert_called_once_with(
            "/containers/foo/unpause", headers={'content-type': 'application/json'}
        )

    def test_wait(self):
        """test wait call"""
        mock_read = mock.MagicMock()
        mock_read.return_value = b'{"StatusCode": 0}'
        self.response.status = 200
        self.response.read = mock_read
        ret = podman.containers.wait(self.api, 'foo')
        self.assertEqual(ret, {"StatusCode": 0})
        self.request.assert_called_once_with(
            "/containers/foo/wait", params={}, headers={'content-type': 'application/json'}
        )
