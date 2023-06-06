#!/usr/bin/env bash

# This script handles any custom processing of the spec file generated using the `post-upstream-clone`
# action and gets used by the fix-spec-file action in .packit.yaml.

set -eo pipefail

# Name of the package
PACKAGE=python-podman
SPEC_FILE=rpm/$PACKAGE.spec

# Get Version from HEAD
VERSION=$(grep '^__version__' podman/version.py | cut -d\" -f2 | sed -e 's/-/~/')

# Generate source tarball from HEAD
git archive --prefix=$PACKAGE-$VERSION/ -o $PACKAGE-$VERSION.tar.gz HEAD

# RPM Spec modifications

# Update Version in spec with Version from podman/version.py
sed -i "s/^Version:.*/Version: $VERSION/" $SPEC_FILE

# Update Release in spec with Packit's release envvar
sed -i "s/^Release:.*/Release: $PACKIT_RPMSPEC_RELEASE%{?dist}/" $SPEC_FILE

# Update Source tarball name in spec
sed -i "s/^Source:.*.tar.gz/Source: $PACKAGE-$VERSION.tar.gz/" $SPEC_FILE
