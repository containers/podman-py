import unittest
from unittest.mock import mock_open
from podman import ApiConnection, system
import json

from unittest.mock import patch


class TestSystem(unittest.TestCase):

    def mock_bytes_response_from_api(self, module):
        """Simulates the response of a bytes object from the API"""
        my_dict = {"key": "value"}
        bytes = json.dumps(my_dict).encode('utf-8')
        with patch('podman.ApiConnection.request', mock_open(read_data=bytes), create=True):
            response = module(ApiConnection('unix:/junkuri'))
            return response

    def test_000_get_info(self):
        info = self.mock_bytes_response_from_api(system.get_info)
        self.assertTrue(type(info) == dict)

    def test_000_show_disk_usage(self):
        disk_usage = self.mock_bytes_response_from_api(system.show_disk_usage)
        self.assertTrue(type(disk_usage) == dict)

    def test_000_get_events(self):
        disk_usage = self.mock_bytes_response_from_api(system.get_events)
        self.assertTrue(type(disk_usage) == dict)

    def test_000_version(self):
        version = self.mock_bytes_response_from_api(system.version)
        self.assertTrue(type(version) == dict)

    def test_000_prune_unused_data(self):
        pruned_data = self.mock_bytes_response_from_api(system.prune_unused_data)
        self.assertTrue(type(pruned_data) == dict)