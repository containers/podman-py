#!/bin/bash

set -eo pipefail

systemctl enable podman.socket podman.service
systemctl start podman.socket

make
make tests
