import datetime
import os
import unittest
import tempfile
from unittest import mock

from podman import api


class PathUtilsTestCase(unittest.TestCase):
    def setUp(self):
        self.xdg_runtime_dir = os.getenv('XDG_RUNTIME_DIR')
        print('XDG_RUNTIME_DIR', self.xdg_runtime_dir)

    @mock.patch.dict(os.environ, clear=True)
    def test_get_runtime_dir_env_var_set(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            os.environ['XDG_RUNTIME_DIR'] = str(tmpdir)
            self.assertEqual(str(tmpdir), api.path_utils.get_runtime_dir())

    @unittest.skipUnless(os.getenv('XDG_RUNTIME_DIR'), 'XDG_RUNTIME_DIR must be set')
    @mock.patch.dict(os.environ, clear=True)
    def test_get_runtime_dir_env_var_not_set(self):
        self.assertNotEqual(self.xdg_runtime_dir, api.path_utils.get_runtime_dir())


if __name__ == '__main__':
    unittest.main()
