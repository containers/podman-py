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
"""podman.system unit tests"""

import unittest

from unittest import mock
import podman.errors
import podman.system


class TestSystem(unittest.TestCase):
    """Test the system calls."""

    def setUp(self):
        super().setUp()
        self.request = mock.MagicMock()
        self.response = mock.MagicMock()
        self.request.return_value = self.response
        self.api = mock.MagicMock()
        self.api.get = self.request

    def test_version(self):
        """test version call"""
        self.response.status = 200
        mock_read = mock.MagicMock()
        mock_read.return_value = b'{"Version": "2.1.1"}'
        expected = {'Version': '2.1.1'}
        self.response.read = mock_read
        ret = podman.system.version(self.api)
        self.assertEqual(ret, expected)
        self.request.assert_called_once_with('/version')

    def test_version_not_ok(self):
        """test version call"""
        self.response.status = 404
        ret = podman.system.version(self.api)
        self.assertEqual(ret, {})

    def test_get_info(self):
        """test info call"""
        mock_read = mock.MagicMock()
        mock_read.return_value = b'{"ID":"a"}'
        self.response.read = mock_read
        ret = podman.system.get_info(self.api)
        self.assertEqual(ret, {'ID': 'a'})
        self.request.assert_called_once_with('/info')

    def test_get_info_fail(self):
        """test info call fails"""
        self.request.side_effect = podman.errors.NotFoundError('yikes')
        mock_raise = mock.MagicMock()
        mock_raise.side_effect = podman.errors.ImageNotFound('yikes')
        self.api.raise_image_not_found = mock_raise
        self.assertRaises(podman.errors.ImageNotFound,
                          podman.system.get_info,
                          self.api)

    def test_show_disk_usage(self):
        """test df call"""
        mock_read = mock.MagicMock()
        mock_read.return_value = b'{"LayersSize":0}'
        self.response.read = mock_read
        ret = podman.system.show_disk_usage(self.api)
        self.assertEqual(ret, {'LayersSize': 0})
        self.request.assert_called_once_with('/system/df')

    def test_show_disk_usage_fail(self):
        """test df call fails"""
        self.request.side_effect = podman.errors.NotFoundError('yikes')
        mock_raise = mock.MagicMock()
        mock_raise.side_effect = podman.errors.ImageNotFound('yikes')
        self.api.raise_image_not_found = mock_raise
        self.assertRaises(podman.errors.ImageNotFound,
                          podman.system.show_disk_usage,
                          self.api)
