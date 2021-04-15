import setuptools

import fnmatch
from setuptools import find_packages
from setuptools.command.build_py import build_py as build_py_orig

excluded = [
    "podman/api_connection.py",
    "podman/containers/*",
    "podman/images/*",
    "podman/manifests/*",
    "podman/networks/*",
    "podman/pods/*",
    "podman/system/*",
    "podman/system/*",
    "podman/tests/*",
]


class build_py(build_py_orig):
    def find_package_modules(self, package, package_dir):
        modules = super().find_package_modules(package, package_dir)
        return [
            (pkg, mod, file)
            for (pkg, mod, file) in modules
            if not any(fnmatch.fnmatchcase(file, pat=pattern) for pattern in excluded)
        ]


setuptools.setup(
    packages=find_packages(),
    cmdclass={"build_py": build_py},
)
