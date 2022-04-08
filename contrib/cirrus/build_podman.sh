#!/bin/bash

set -xeo pipefail

systemctl stop podman.socket || :

dnf erase podman -y
dnf copr enable rhcontainerbot/podman-next -y
dnf install podman -y

