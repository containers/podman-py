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
"""podman.manifests unit tests"""

import unittest
import urllib.parse
from unittest import mock

import podman.errors
import podman.manifests


class TestManifests(unittest.TestCase):
    """Test the manifest calls."""

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

    def test_add(self):
        """test add call"""
        manifest = {'all': False, 'annotation': {'prop1': 'string', 'prop2': 'string'}}
        self.response.status = 200
        self.assertTrue(podman.manifests.add(self.api, 'foo', manifest))

    def test_add_missing(self):
        """test add call missing manifest"""
        self.request.side_effect = podman.errors.NotFoundError('yikes')
        mock_raise = mock.MagicMock()
        mock_raise.side_effect = podman.errors.ManifestNotFound('yikes')
        self.api.raise_not_found = mock_raise
        self.assertRaises(podman.errors.ManifestNotFound, podman.manifests.add, self.api, 'foo', {})

    def test_create(self):
        """test create call"""
        self.response.status = 200
        self.assertTrue(podman.manifests.create(self.api, 'test', 'image', True))
        self.request.assert_called_once_with(
            '/manifests/create', params={'name': 'test', 'image': 'image', 'all': True}
        )

    def test_create_fail(self):
        """test create call with an error"""
        self.response.status = 400
        self.request.side_effect = podman.errors.RequestError('meh', self.response)
        self.assertRaises(podman.errors.RequestError, podman.manifests.create, self.api, 'test')

    def test_create_missing(self):
        """test create call with missing manifest"""
        self.request.side_effect = podman.errors.NotFoundError('yikes')
        mock_raise = mock.MagicMock()
        mock_raise.side_effect = podman.errors.ManifestNotFound('yikes')
        self.api.raise_not_found = mock_raise
        self.assertRaises(podman.errors.ManifestNotFound, podman.manifests.create, self.api, 'test')

    def test_inspect(self):
        """test manifests inspect call"""
        mock_read = mock.MagicMock()
        mock_read.return_value = b'[{"Instances":["podman"]}]'
        self.response.read = mock_read
        ret = podman.manifests.inspect(self.api, 'podman')
        self.assertEqual(ret, [{'Instances': ['podman']}])
        self.request.assert_called_once_with('/manifests/podman/json')

    def test_inspect_missing(self):
        """test inspect missing pod"""
        self.request.side_effect = podman.errors.NotFoundError('yikes')
        mock_raise = mock.MagicMock()
        mock_raise.side_effect = podman.errors.ManifestNotFound('yikes')
        self.api.raise_not_found = mock_raise
        self.assertRaises(
            podman.errors.ManifestNotFound, podman.manifests.inspect, self.api, 'podman'
        )

    def test_push(self):
        """test manifest push call"""
        self.response.status = 200
        self.assertTrue(podman.manifests.push(self.api, 'foo', 'dest', True))
        self.api.post.assert_called_once_with(
            '/manifests/foo/push', params={'destination': 'dest', 'all': True}
        )

    def test_push_fail(self):
        """test manifest push fails"""
        self.request.side_effect = podman.errors.NotFoundError('yikes')
        mock_raise = mock.MagicMock()
        mock_raise.side_effect = podman.errors.ManifestNotFound('yikes')
        self.api.raise_not_found = mock_raise
        self.assertRaises(
            podman.errors.ManifestNotFound, podman.manifests.push, self.api, 'podman', 'dest'
        )

    def test_remove(self):
        """test remove call"""
        self.response.status = 200
        self.assertTrue(podman.manifests.remove(self.api, 'foo', 'bar'))
        self.api.delete.assert_called_once_with('/manifests/foo', {'digest': 'bar'})

    def test_remove_missing(self):
        """test remove call with missing pod"""
        mock_raise = mock.MagicMock()
        mock_raise.side_effect = podman.errors.ManifestNotFound('yikes')
        self.api.raise_not_found = mock_raise
        self.request.side_effect = podman.errors.NotFoundError('nope')
        self.assertRaises(podman.errors.ManifestNotFound, podman.manifests.remove, self.api, 'foo')
