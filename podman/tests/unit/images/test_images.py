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
"""podman.images unit tests"""

import unittest
import urllib.parse
from unittest import mock

import podman.errors
import podman.system


class TestImages(unittest.TestCase):
    """Test the images calls."""

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

    def test_list_images(self):
        """test list call"""
        mock_read = mock.MagicMock()
        mock_read.return_value = b'[{"Id": "foo"}]'
        self.response.status = 200
        self.response.read = mock_read
        expected = [{"Id": "foo"}]
        ret = podman.images.list_images(self.api)
        self.assertEqual(ret, expected)
        self.request.assert_called_once_with("/images/json")

    def test_inspect(self):
        """test inspect call"""
        mock_read = mock.MagicMock()
        mock_read.return_value = b'{"Id": "foo"}'
        self.response.status = 200
        self.response.read = mock_read
        expected = {"Id": "foo"}
        ret = podman.images.inspect(self.api, "foo")
        self.assertEqual(ret, expected)
        self.request.assert_called_once_with("/images/foo/json")

    def test_image_exists(self):
        """test exists call"""
        self.response.status = 204
        self.assertTrue(podman.images.image_exists(self.api, "foo"))
        self.request.assert_called_once_with("/images/foo/exists")

    def test_image_exists_missing(self):
        """test exists call with missing image"""
        self.request.side_effect = podman.errors.NotFoundError("nope")
        self.assertFalse(podman.images.image_exists(self.api, "foo"))

    def test_remove(self):
        """test remove call"""
        mock_read = mock.MagicMock()
        mock_read.return_value = b'[{"deleted": "str","untagged": ["str"]}]'
        self.response.status = 200
        self.response.read = mock_read
        expected = [{"deleted": "str", "untagged": ["str"]}]
        ret = podman.images.remove(self.api, "foo")
        self.assertEqual(ret, expected)
        self.api.delete.assert_called_once_with("/images/foo", {})

    def test_remove_force(self):
        """test remove call with force"""
        mock_read = mock.MagicMock()
        mock_read.return_value = b'[{"deleted": "str","untagged": ["str"]}]'
        self.response.status = 200
        self.response.read = mock_read
        expected = [{"deleted": "str", "untagged": ["str"]}]
        ret = podman.images.remove(self.api, "foo", True)
        self.assertEqual(ret, expected)
        self.api.delete.assert_called_once_with("/images/foo", {"force": True})

    def test_remove_missing(self):
        """test remove call with missing image"""
        mock_raise = mock.MagicMock()
        mock_raise.side_effect = podman.errors.ImageNotFound("yikes")
        self.api.raise_not_found = mock_raise
        self.request.side_effect = podman.errors.NotFoundError("nope")
        self.assertRaises(
            podman.errors.ImageNotFound, podman.images.remove, self.api, "foo"
        )

    def test_tag_image(self):
        """test tag image"""
        self.response.status = 201
        self.assertTrue(podman.images.tag_image(self.api, "foo", "bar", "baz"))

    def test_tag_image_fail(self):
        """test remove call with missing image"""
        mock_raise = mock.MagicMock()
        mock_raise.side_effect = podman.errors.ImageNotFound("yikes")
        self.api.raise_image_not_found = mock_raise
        self.request.side_effect = podman.errors.NotFoundError("nope")
        self.assertRaises(
            podman.errors.ImageNotFound,
            podman.images.tag_image,
            self.api,
            "foo",
            "bar",
            "baz",
        )

    def test_history(self):
        """test image history"""
        mock_read = mock.MagicMock()
        mock_read.return_value = b'{"Id": "a"}'
        self.response.status = 200
        self.response.read = mock_read
        expected = {"Id": "a"}
        ret = podman.images.history(self.api, "foo")
        self.assertEqual(ret, expected)
        self.api.delete.assert_called_once_with("/images/foo/history")

    def test_history_missing_image(self):
        """test history with missing image"""
        mock_raise = mock.MagicMock()
        mock_raise.side_effect = podman.errors.ImageNotFound("yikes")
        self.api.raise_image_not_found = mock_raise
        self.request.side_effect = podman.errors.NotFoundError("nope")
        self.assertRaises(
            podman.errors.ImageNotFound, podman.images.history, self.api, "foo"
        )
