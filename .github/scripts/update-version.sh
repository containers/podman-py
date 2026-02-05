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
# - podman/version.py
# - pyproject.toml
# - setup.cfg
# - Makefile
# - podman/tests/__init__.py (URL contains /vX.Y.Z/libpod)
# - plans/main.fmf (ref: "vX.Y.Z")

sed -i "s/__version__ = \".*\"/__version__ = \"$VERSION\"/" podman/version.py
echo "  - Updated podman/version.py"

sed -i "s/^version = \".*\"/version = \"$VERSION\"/" pyproject.toml
echo "  - Updated pyproject.toml"

sed -i "s/^version = .*/version = $VERSION/" setup.cfg
echo "  - Updated setup.cfg"

sed -i "s/export PODMAN_VERSION ?= \".*\"/export PODMAN_VERSION ?= \"$VERSION\"/" Makefile
echo "  - Updated Makefile"

sed -i "s|/v[0-9.]*[0-9]/libpod|/v$VERSION/libpod|" podman/tests/__init__.py
echo "  - Updated podman/tests/__init__.py"

sed -i "s/ref: \"v[0-9.]*[0-9]\"/ref: \"v$VERSION\"/" plans/main.fmf
echo "  - Updated plans/main.fmf"
