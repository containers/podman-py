#   Copyright 2020 Red Hat, Inc.
#
#   Licensed under the Apache License, Version 2.0 (the "License"); you may
#   not use this file except in compliance with the License. You may obtain
#   a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#   WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#   License for the specific language governing permissions and limitations
#   under the License.
#
"""podman.pods unit tests"""

import json
import unittest
import urllib.parse
from unittest import mock

import podman.errors
import podman.pods


class TestNetwork(unittest.TestCase):
    """Test the pod calls."""

    def setUp(self):
        super().setUp()
        self.request = mock.MagicMock()
        self.response = mock.MagicMock()
        self.request.return_value = self.response
        self.api = mock.MagicMock()
        self.api.get = self.request
        self.api.delete = self.request
        self.api.post = self.request
        self.api.quote = urllib.parse.quote

    def test_create(self):
        """test create call"""
        pod = {
            'name': 'foo',
        }
        mock_read = mock.MagicMock()
        mock_read.return_value = b'{"Id":"string"}'
        self.response.read = mock_read
        ret = podman.pods.create(self.api, 'test', pod)
        self.assertEqual(ret, {'Id': 'string'})
        self.request.assert_called_once_with(
            '/pods/create?name=test',
            headers={'content-type': 'application/json'},
            params='{"name": "foo"}',
        )

    def test_create_fail(self):
        """test create call with an error"""
        pod = {
            'name': 'foo',
        }
        self.response.status = 400
        self.request.side_effect = podman.errors.RequestError('meh', self.response)
        self.assertRaises(
            podman.errors.RequestError,
            podman.pods.create,
            self.api,
            'test',
            json.dumps(pod),
        )

    def test_exists(self):
        """test pods exists call"""
        self.assertTrue(podman.pods.exists(self.api, 'test'))

    def test_exists_missing(self):
        """test pods exists call returns false for missing pod"""
        self.request.side_effect = podman.errors.NotFoundError('yikes')
        self.assertFalse(podman.pods.exists(self.api, 'test'))

    def test_inspect(self):
        """test pods inspect call"""
        mock_read = mock.MagicMock()
        mock_read.return_value = b'[{"Name":"podman"}]'
        self.response.read = mock_read
        ret = podman.pods.inspect(self.api, 'podman')
        self.assertEqual(ret, [{'Name': 'podman'}])
        self.request.assert_called_once_with('/pods/podman/json')

    def test_inspect_missing(self):
        """test inspect missing pod"""
        self.request.side_effect = podman.errors.NotFoundError('yikes')
        mock_raise = mock.MagicMock()
        mock_raise.side_effect = podman.errors.PodNotFound('yikes')
        self.api.raise_not_found = mock_raise
        self.assertRaises(podman.errors.PodNotFound, podman.pods.inspect, self.api, 'podman')

    def test_kill(self):
        """test pods kill call"""
        mock_read = mock.MagicMock()
        mock_read.return_value = b'{"Id":"string"}'
        self.response.read = mock_read
        ret = podman.pods.kill(self.api, 'test', 'foo')
        self.assertEqual(ret, {'Id': 'string'})
        self.request.assert_called_once_with(
            '/pods/test/kill',
            {"signal": "foo"},
        )

    def test_kill_fail(self):
        """test pods kill call failure"""
        self.request.side_effect = podman.errors.NotFoundError('yikes')
        mock_raise = mock.MagicMock()
        mock_raise.side_effect = podman.errors.PodNotFound('yikes')
        self.api.raise_not_found = mock_raise
        self.assertRaises(podman.errors.PodNotFound, podman.pods.kill, self.api, 'podman')

    def test_list_pods(self):
        """test pods list call"""
        mock_read = mock.MagicMock()
        mock_read.return_value = b'[{"Name":"podman"}]'
        self.response.read = mock_read
        ret = podman.pods.list_pods(self.api)
        self.assertEqual(ret, [{'Name': 'podman'}])
        self.request.assert_called_once_with('/pods/json', {})

    def test_list_pods_filter(self):
        """test pods list call with a filter"""
        mock_read = mock.MagicMock()
        mock_read.return_value = b'[{"Name":"podman"}]'
        self.response.read = mock_read
        ret = podman.pods.list_pods(self.api, 'name=podman')
        self.assertEqual(ret, [{'Name': 'podman'}])
        self.request.assert_called_once_with('/pods/json', {'filter': 'name=podman'})

    def test_list_processes(self):
        """test pods list processes"""
        mock_read = mock.MagicMock()
        mock_read.return_value = b'{"Processes": [[]], "Titles": []}'
        self.response.read = mock_read
        ret = podman.pods.list_processes(self.api, 'podman')
        self.assertEqual(ret, {'Processes': [[]], 'Titles': []})
        self.request.assert_called_once_with('/pods/podman/top', {})

    def test_list_processes_with_options(self):
        """test pods list processes"""
        mock_read = mock.MagicMock()
        mock_read.return_value = b'{"Processes": [[]], "Titles": []}'
        self.response.read = mock_read
        ret = podman.pods.list_processes(self.api, 'podman', True, '-a')
        self.assertEqual(ret, {'Processes': [[]], 'Titles': []})
        self.request.assert_called_once_with('/pods/podman/top', {'stream': True, 'ps_args': '-a'})

    def test_pause(self):
        """test pods pause call"""
        mock_read = mock.MagicMock()
        mock_read.return_value = b'{"Id": "string"}'
        self.response.read = mock_read
        ret = podman.pods.pause(self.api, 'podman')
        self.assertEqual(ret, {'Id': "string"})
        self.request.assert_called_once_with('/pods/podman/pause')

    def test_pause_fail(self):
        """test pods pause fails"""
        self.request.side_effect = podman.errors.NotFoundError('yikes')
        mock_raise = mock.MagicMock()
        mock_raise.side_effect = podman.errors.PodNotFound('yikes')
        self.api.raise_not_found = mock_raise
        self.assertRaises(podman.errors.PodNotFound, podman.pods.pause, self.api, 'podman')

    def test_prune(self):
        """test pods prune call"""
        mock_read = mock.MagicMock()
        mock_read.return_value = b'{"Id": "string"}'
        self.response.read = mock_read
        ret = podman.pods.prune(self.api)
        self.assertEqual(ret, {'Id': "string"})
        self.request.assert_called_once_with('/pods/prune')

    def test_prune_fail(self):
        """test prune call with an error"""
        self.response.status = 400
        self.request.side_effect = podman.errors.RequestError('meh', self.response)
        self.assertRaises(podman.errors.RequestError, podman.pods.prune, self.api)

    def test_remove(self):
        """test remove call"""
        mock_read = mock.MagicMock()
        mock_read.return_value = b'[{"deleted": "str","untagged": ["str"]}]'
        self.response.status = 200
        self.response.read = mock_read
        expected = [{'deleted': 'str', 'untagged': ['str']}]
        ret = podman.pods.remove(self.api, 'foo')
        self.assertEqual(ret, expected)
        self.api.delete.assert_called_once_with('/pods/foo', {})

    def test_remove_force(self):
        """test remove call with force"""
        mock_read = mock.MagicMock()
        mock_read.return_value = b'[{"deleted": "str","untagged": ["str"]}]'
        self.response.status = 200
        self.response.read = mock_read
        expected = [{'deleted': 'str', 'untagged': ['str']}]
        ret = podman.pods.remove(self.api, 'foo', True)
        self.assertEqual(ret, expected)
        self.api.delete.assert_called_once_with('/pods/foo', {'force': True})

    def test_remove_missing(self):
        """test remove call with missing pod"""
        mock_raise = mock.MagicMock()
        mock_raise.side_effect = podman.errors.PodNotFound('yikes')
        self.api.raise_not_found = mock_raise
        self.request.side_effect = podman.errors.NotFoundError('nope')
        self.assertRaises(podman.errors.PodNotFound, podman.pods.remove, self.api, 'foo')

    def test_restart(self):
        """test pods restart call"""
        mock_read = mock.MagicMock()
        mock_read.return_value = b'{"Id": "string"}'
        self.response.read = mock_read
        ret = podman.pods.restart(self.api, 'podman')
        self.assertEqual(ret, {'Id': "string"})
        self.request.assert_called_once_with('/pods/podman/restart')

    def test_restart_fail(self):
        """test pods restart fail"""
        self.request.side_effect = podman.errors.NotFoundError('yikes')
        mock_raise = mock.MagicMock()
        mock_raise.side_effect = podman.errors.PodNotFound('yikes')
        self.api.raise_not_found = mock_raise
        self.assertRaises(podman.errors.PodNotFound, podman.pods.restart, self.api, 'podman')

    def test_start(self):
        """test pods start call"""
        mock_read = mock.MagicMock()
        mock_read.return_value = b'{"Id": "string"}'
        self.response.read = mock_read
        ret = podman.pods.start(self.api, 'podman')
        self.assertEqual(ret, {'Id': "string"})
        self.request.assert_called_once_with('/pods/podman/start')

    def test_start_fail(self):
        """test pods start fail"""
        self.request.side_effect = podman.errors.NotFoundError('yikes')
        mock_raise = mock.MagicMock()
        mock_raise.side_effect = podman.errors.PodNotFound('yikes')
        self.api.raise_not_found = mock_raise
        self.assertRaises(podman.errors.PodNotFound, podman.pods.start, self.api, 'podman')

    def test_stats(self):
        """test pods stats call"""
        mock_read = mock.MagicMock()
        mock_read.return_value = b'{"Processes": [[]], "Titles": []}'
        self.response.read = mock_read
        ret = podman.pods.stats(self.api)
        self.assertEqual(ret, {'Processes': [[]], 'Titles': []})
        self.request.assert_called_once_with('/pods/stats', {'all': True})

    def test_stats_with_names(self):
        """test pods stats call"""
        mock_read = mock.MagicMock()
        mock_read.return_value = b'{"Processes": [[]], "Titles": []}'
        self.response.read = mock_read
        ret = podman.pods.stats(self.api, False, ['test'])
        self.assertEqual(ret, {'Processes': [[]], 'Titles': []})
        self.request.assert_called_once_with('/pods/stats', {'all': False, 'namesOrIDs': ['test']})

    def test_stats_fail(self):
        """test pods stats fails"""
        self.request.side_effect = podman.errors.NotFoundError('yikes')
        mock_raise = mock.MagicMock()
        mock_raise.side_effect = podman.errors.PodNotFound('yikes')
        self.api.raise_not_found = mock_raise
        self.assertRaises(podman.errors.PodNotFound, podman.pods.stats, self.api, 'podman')

    def test_stop(self):
        """test pods stop call"""
        mock_read = mock.MagicMock()
        mock_read.return_value = b'{"Id": "string"}'
        self.response.read = mock_read
        ret = podman.pods.stop(self.api, 'podman')
        self.assertEqual(ret, {'Id': "string"})
        self.request.assert_called_once_with('/pods/podman/stop')

    def test_stop_fail(self):
        """test pods stop fail"""
        self.request.side_effect = podman.errors.NotFoundError('yikes')
        mock_raise = mock.MagicMock()
        mock_raise.side_effect = podman.errors.PodNotFound('yikes')
        self.api.raise_not_found = mock_raise
        self.assertRaises(podman.errors.PodNotFound, podman.pods.stop, self.api, 'podman')

    def test_unpause(self):
        """test pods unpause call"""
        mock_read = mock.MagicMock()
        mock_read.return_value = b'{"Id": "string"}'
        self.response.read = mock_read
        ret = podman.pods.unpause(self.api, 'podman')
        self.assertEqual(ret, {'Id': "string"})
        self.request.assert_called_once_with('/pods/podman/unpause')

    def test_unpause_fail(self):
        """test pods unpause fails"""
        self.request.side_effect = podman.errors.NotFoundError('yikes')
        mock_raise = mock.MagicMock()
        mock_raise.side_effect = podman.errors.PodNotFound('yikes')
        self.api.raise_not_found = mock_raise
        self.assertRaises(podman.errors.PodNotFound, podman.pods.unpause, self.api, 'podman')
