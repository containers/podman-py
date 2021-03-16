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
"""podman.networks unit tests"""

import json
import unittest
import urllib.parse
from unittest import mock

import podman.errors
import podman.networks


class TestNetwork(unittest.TestCase):
    """Test the network calls."""

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
        network = {
            'DisableDNS': False,
        }
        mock_read = mock.MagicMock()
        mock_read.return_value = b'{"Filename":"string"}'
        self.response.read = mock_read
        ret = podman.networks.create(self.api, 'test', network)
        self.assertEqual(ret, {'Filename': 'string'})
        self.request.assert_called_once_with(
            '/networks/create?name=test',
            headers={'content-type': 'application/json'},
            params='{"DisableDNS": false}',
        )

    def test_create_with_string(self):
        """test create call with string"""
        network = {
            'DisableDNS': False,
        }
        mock_read = mock.MagicMock()
        mock_read.return_value = b'{"Filename":"string"}'
        self.response.read = mock_read
        ret = podman.networks.create(self.api, 'test', json.dumps(network))
        self.assertEqual(ret, {'Filename': 'string'})
        self.request.assert_called_once_with(
            '/networks/create?name=test',
            headers={'content-type': 'application/json'},
            params='{"DisableDNS": false}',
        )

    def test_create_fail(self):
        """test create call with an error"""
        network = {
            'DisableDNS': False,
        }
        self.response.status = 400
        self.request.side_effect = podman.errors.RequestError('meh', self.response)
        self.assertRaises(
            podman.errors.RequestError,
            podman.networks.create,
            self.api,
            'test',
            json.dumps(network),
        )

    def test_inspect(self):
        """test inspect call"""
        mock_read = mock.MagicMock()
        mock_read.return_value = b'[{"Name":"podman"}]'
        self.response.read = mock_read
        ret = podman.networks.inspect(self.api, 'podman')
        self.assertEqual(ret, [{'Name': 'podman'}])
        self.request.assert_called_once_with('/networks/podman/json')

    def test_inspect_missing(self):
        """test inspect missing network"""
        self.request.side_effect = podman.errors.NotFoundError('yikes')
        mock_raise = mock.MagicMock()
        mock_raise.side_effect = podman.errors.NetworkNotFound('yikes')
        self.api.raise_not_found = mock_raise
        self.assertRaises(
            podman.errors.NetworkNotFound, podman.networks.inspect, self.api, 'podman'
        )

    def test_list_networks(self):
        """test networks list call"""
        mock_read = mock.MagicMock()
        mock_read.return_value = b'[{"Name":"podman"}]'
        self.response.read = mock_read
        ret = podman.networks.list_networks(self.api)
        self.assertEqual(ret, [{'Name': 'podman'}])
        self.request.assert_called_once_with('/networks/json', {})

    def test_list_networks_filter(self):
        """test networks list call with a filter"""
        mock_read = mock.MagicMock()
        mock_read.return_value = b'[{"Name":"podman"}]'
        self.response.read = mock_read
        ret = podman.networks.list_networks(self.api, 'name=podman')
        self.assertEqual(ret, [{'Name': 'podman'}])
        self.request.assert_called_once_with('/networks/json', {'filter': 'name=podman'})

    def test_remove(self):
        """test remove call"""
        mock_read = mock.MagicMock()
        mock_read.return_value = b'[{"deleted": "str","untagged": ["str"]}]'
        self.response.status = 200
        self.response.read = mock_read
        expected = [{'deleted': 'str', 'untagged': ['str']}]
        ret = podman.networks.remove(self.api, 'foo')
        self.assertEqual(ret, expected)
        self.api.delete.assert_called_once_with('/networks/foo', {})

    def test_remove_force(self):
        """test remove call with force"""
        mock_read = mock.MagicMock()
        mock_read.return_value = b'[{"deleted": "str","untagged": ["str"]}]'
        self.response.status = 200
        self.response.read = mock_read
        expected = [{'deleted': 'str', 'untagged': ['str']}]
        ret = podman.networks.remove(self.api, 'foo', True)
        self.assertEqual(ret, expected)
        self.api.delete.assert_called_once_with('/networks/foo', {'force': True})

    def test_remove_missing(self):
        """test remove call with missing network"""
        mock_raise = mock.MagicMock()
        mock_raise.side_effect = podman.errors.NetworkNotFound('yikes')
        self.api.raise_not_found = mock_raise
        self.request.side_effect = podman.errors.NotFoundError('nope')
        self.assertRaises(podman.errors.NetworkNotFound, podman.networks.remove, self.api, 'foo')

    def test_prune(self):
        """test prune call"""
        mock_read = mock.MagicMock()
        mock_read.return_value = b'[{"Name": "net1"}, {"Name": "net2"}]'
        self.response.read = mock_read
        ret = podman.networks.prune(self.api)
        expected = [{'Name': 'net1'}, {"Name": "net2"}]
        self.assertEqual(ret, expected)
        self.request.assert_called_once_with(
            '/networks/prune',
            headers={'content-type': 'application/json'},
        )
