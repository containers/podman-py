#!/bin/bash

set -euo pipefail

VERSION="${1:-}"

if [[ -z "$VERSION" ]]; then
    echo "Error: Version argument is required"
    echo "Usage: $0 <version>"
    echo "Example: $0 5.8.0"
    exit 1
fi

# Update:
# - podman/version.py (single source of truth for package version)
# - podman/tests/__init__.py (URL contains /vX.Y.Z/libpod)
# - plans/main.fmf (ref: "vX.Y.Z")
#
# pyproject.toml, setup.cfg, and Makefile derive the version dynamically
# from podman/version.py and do not need manual updates.

sed -i "s/__version__ = \".*\"/__version__ = \"$VERSION\"/" podman/version.py
echo "  - Updated podman/version.py"

sed -i "s|/v[0-9.]*[0-9]/libpod|/v$VERSION/libpod|" podman/tests/__init__.py
echo "  - Updated podman/tests/__init__.py"
