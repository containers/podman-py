#   Copyright 2019 Red Hat, Inc.
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
"""podman.ApiConnection unit tests"""

import unittest
import socket

from unittest import mock
from podman import ApiConnection
import podman.errors


class TestApiConnection(unittest.TestCase):
    """Test the ApiConnection() object."""

    def setUp(self):
        super().setUp()
        self.conn = ApiConnection('unix:///', base='/test')

    def test_missing_url(self):
        """test missing url to constructor"""
        self.assertRaises(ValueError,
                          ApiConnection,
                          None)

    def test_invalid_scheme(self):
        """test invalid scheme to constructor"""
        self.assertRaises(ValueError,
                          ApiConnection,
                          "tcp://localhost//")

    @mock.patch('socket.socket')
    def test_connect(self, mock_sock):
        """test connect for unix"""
        mock_sock_obj = mock.MagicMock()
        mock_sock.return_value = mock_sock_obj
        self.conn.connect()
        mock_sock.assert_called_once_with(socket.AF_UNIX, socket.SOCK_STREAM)

    def test_connect_fail(self):
        """test connect not implemented"""
        conn = ApiConnection('ssh:///')
        self.assertRaises(NotImplementedError,
                          conn.connect)

    def test_join(self):
        """test join call"""
        path = '/foo'
        self.assertEqual(self.conn.join(path), '/test/foo')

    def test_join_params(self):
        """test join call with params"""
        path = '/foo'
        params = {'a': '"b"'}
        self.assertEqual(self.conn.join(path, params),
                         '/test/foo?a=%22b%22')

    def test_delete(self):
        """test delete wrapper"""
        mock_req = mock.MagicMock()
        self.conn.request = mock_req

        self.conn.delete('/baz')
        self.conn.delete('/foo', params={'a': 'b'})
        self.conn.delete('/bar', params={'a': 'b', 'c': 'd'})
        calls = [
            mock.call('DELETE', '/test/baz'),
            mock.call('DELETE', '/test/foo?a=b'),
            mock.call('DELETE', '/test/bar?a=b&c=d')
        ]
        mock_req.assert_has_calls(calls)

    def test_get(self):
        """test get wrapper"""
        mock_req = mock.MagicMock()
        self.conn.request = mock_req

        self.conn.get('/baz')
        self.conn.get('/foo', params={'a': 'b'})
        self.conn.get('/bar', params={'a': 'b', 'c': 'd'})
        calls = [
            mock.call('GET', '/test/baz'),
            mock.call('GET', '/test/foo?a=b'),
            mock.call('GET', '/test/bar?a=b&c=d')
        ]
        mock_req.assert_has_calls(calls)

    def test_post(self):
        """test post wrapper"""
        mock_req = mock.MagicMock()
        self.conn.request = mock_req

        self.conn.post('/baz')
        self.conn.post('/foo', params={'a': 'b'})
        self.conn.post('/bar', params={'a': 'b', 'c': 'd'}, headers={'x': 'y'})
        calls = [
            mock.call('POST', '/test/baz', body=None, headers={}),
            mock.call('POST', '/test/foo', body='a=b',
                      headers={
                          'content-type': 'application/x-www-form-urlencoded'
                      }),
            mock.call('POST', '/test/bar', body='a=b&c=d',
                      headers={
                          'x': 'y',
                          'content-type': 'application/x-www-form-urlencoded'
                      }),

        ]
        mock_req.assert_has_calls(calls)

    @mock.patch('http.client.HTTPConnection.getresponse')
    @mock.patch('http.client.HTTPConnection.request')
    def test_request(self, mock_request, mock_response):
        """test request"""
        mock_resp = mock.MagicMock()
        mock_resp.status = 200
        mock_response.return_value = mock_resp
        ret = self.conn.request('GET', 'unix://foo')
        mock_request.assert_called_once_with('GET', 'unix://foo', None, {},
                                             encode_chunked=False)
        mock_response.assert_called_once_with()
        self.assertEqual(ret, mock_resp)

    @mock.patch('http.client.HTTPConnection.getresponse')
    @mock.patch('http.client.HTTPConnection.request')
    def test_request_not_found(self, mock_request, mock_response):
        """test request with not found response"""
        mock_resp = mock.MagicMock()
        mock_resp.status = 404
        mock_response.return_value = mock_resp
        self.assertRaises(podman.errors.NotFoundError,
                          self.conn.request,
                          'GET', 'unix://foo')
        mock_request.assert_called_once_with('GET', 'unix://foo', None, {},
                                             encode_chunked=False)
        mock_response.assert_called_once_with()

    @mock.patch('http.client.HTTPConnection.getresponse')
    @mock.patch('http.client.HTTPConnection.request')
    def test_request_server_error(self, mock_request, mock_response):
        """test request with server error response"""
        mock_resp = mock.MagicMock()
        mock_resp.status = 500
        mock_response.return_value = mock_resp
        self.assertRaises(podman.errors.InternalServerError,
                          self.conn.request,
                          'GET', 'unix://foo')
        mock_request.assert_called_once_with('GET', 'unix://foo', None, {},
                                             encode_chunked=False)
        mock_response.assert_called_once_with()

    def test_quote(self):
        """test quote"""
        ret = self.conn.quote('"')
        self.assertEqual(ret, '%22')

    @mock.patch('json.loads')
    def test_raise_image_not_found(self, mock_json):
        """test raise image not found function"""
        exc = Exception('meh')
        mock_resp = mock.MagicMock()
        mock_json.return_value = {'cause': 'c', 'message': 'msg'}
        # pylint: disable=protected-access
        self.assertRaises(podman.errors.ImageNotFound,
                          self.conn.raise_image_not_found,
                          exc,
                          mock_resp)
        mock_json.assert_called_once()
