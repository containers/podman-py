#!/bin/bash

set -eo pipefail

echo "Locate: $(type -P podman)"
podman --version
podman-remote --version

make
make tests
