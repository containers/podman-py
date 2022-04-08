"""Utility functions for working with tarballs."""
import pathlib
import random
import shutil
import tarfile
import tempfile
from fnmatch import fnmatch
from typing import BinaryIO, List, Optional

import sys


def prepare_containerignore(anchor: str) -> List[str]:
    """Return the list of patterns for filenames to exclude.

    .containerignore takes precedence over .dockerignore.
    """
    for filename in (".containerignore", ".dockerignore"):
        ignore = pathlib.Path(anchor) / filename
        if not ignore.exists():
            continue

        with ignore.open(encoding='utf-8') as file:
            return list(
                filter(
                    lambda l: l and not l.startswith("#"),
                    (line.strip() for line in file.readlines()),
                )
            )
    return []


def prepare_containerfile(anchor: str, dockerfile: str) -> str:
    """Ensure that Containerfile, or a proxy Containerfile is in context_dir.

    Args:
        anchor: Build context directory
        dockerfile: Path to Dockerfile/Containerfile

    Returns:
        path to Dockerfile/Containerfile in root of context directory
    """
    anchor_path = pathlib.Path(anchor)
    dockerfile_path = pathlib.Path(dockerfile)

    if dockerfile_path.parent.samefile(anchor_path):
        return dockerfile_path.name

    proxy_path = anchor_path / f".containerfile.{random.getrandbits(160):x}"
    shutil.copy2(dockerfile_path, proxy_path, follow_symlinks=False)
    return proxy_path.name


def create_tar(
    anchor: str, name: str = None, exclude: List[str] = None, gzip: bool = False
) -> BinaryIO:
    """Create a tarfile from context_dir to send to Podman service.

    Args:
        anchor: Directory to use as root of tar file.
        name: Name of tar file.
        exclude: List of patterns for files to exclude from tar file.
        gzip: When True, gzip compress tar file.
    """

    def add_filter(info: tarfile.TarInfo) -> Optional[tarfile.TarInfo]:
        """Filter files targeted to be added to tarfile.

        Args:
            info: Information on the file targeted to be added

        Returns:
            None: if file is not to be added
            TarInfo: when file is to be added. Modified as needed.

        Notes:
            exclude is captured from parent
        """

        if not (info.isfile() or info.isdir() or info.issym()):
            return None

        if _exclude_matcher(info.name, exclude):
            return None

        # Workaround https://bugs.python.org/issue32713. Fixed in Python 3.7
        if info.mtime < 0 or info.mtime > 8**11 - 1:
            info.mtime = int(info.mtime)

        # do not leak client information to service
        info.uid = 0
        info.uname = info.gname = "root"

        if sys.platform == "win32":
            info.mode = info.mode & 0o755 | 0o111

        return info

    if name is None:
        # pylint: disable=consider-using-with
        name = tempfile.NamedTemporaryFile(prefix="podman_context", suffix=".tar")
    else:
        name = pathlib.Path(name)

    if exclude is None:
        exclude = []
    else:
        exclude = exclude.copy()

    # FIXME caller needs to add this...
    # exclude.append(".dockerignore")
    exclude.append(name.name)

    mode = "w:gz" if gzip else "w"
    with tarfile.open(name.name, mode) as tar:
        tar.add(anchor, arcname="", recursive=True, filter=add_filter)

    return open(name.name, "rb")  # pylint: disable=consider-using-with


def _exclude_matcher(path: str, exclude: List[str]) -> bool:
    """Returns True if path matches an entry in exclude.

    Note:
        FIXME Not compatible, support !, **, etc
    """
    if not exclude:
        return False

    for pattern in exclude:
        if fnmatch(path, pattern):
            return True
    return False
