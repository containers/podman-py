import unittest

from podman.domain.pods_manager import PodsManager


class ManagerTestCase(unittest.TestCase):
    def test_prepare_model(self):
        with self.assertRaisesRegex(Exception, "^Can't create Pod from .*$"):
            PodsManager().prepare_model(attrs=("Sets", "Not", "supported"))


if __name__ == '__main__':
    unittest.main()
