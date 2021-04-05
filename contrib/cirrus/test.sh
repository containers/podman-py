#!/bin/bash

set -eo pipefail

echo "Locate: $(which podman)"
podman --version
podman-remote --version

make
make tests
