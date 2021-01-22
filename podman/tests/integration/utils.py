#   Copyright 2020 Red Hat, Inc.
#
#   Licensed under the Apache License, Version 2.0 (the "License"); you may
#   not use this file except in compliance with the License. You may obtain
#   a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#   WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#   License for the specific language governing permissions and limitations
#   under the License.
#
"""Integration Test Utils"""

import shutil
import subprocess
import time
import os
import podman.tests.errors as errors


class PodmanLauncher:
    """Podman service launcher"""

    def __init__(self, socket_uri, podman_path=None, timeout=0, privileged=False):
        """create a launcher and build podman command"""
        self.podman_exe = podman_path
        if not self.podman_exe:
            self.podman_exe = shutil.which('podman')
        if self.podman_exe is None:
            raise errors.PodmanNotInstalled()
        self.socket_file = socket_uri.replace('unix://', '')
        self.proc = None
        self.cmd = []
        if privileged:
            self.cmd.append('sudo')
        self.cmd = self.cmd + [
            self.podman_exe,
            "system",
            "service",
            "--time",
            str(timeout),
            socket_uri,
        ]

    def start(self):
        """start podman service"""
        print("Launching {}".format(" ".join(self.cmd)))
        self.proc = subprocess.Popen(self.cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        # wait for socket to be created
        while not os.path.exists(self.socket_file):
            time.sleep(0.2)

    def stop(self):
        """stop podman service"""
        if not self.proc:
            return (None, None)
        self.proc.terminate()
        try:
            out, errs = self.proc.communicate(timeout=15)
        except subprocess.TimeoutExpired:
            self.proc.kill()
            out, errs = self.proc.communicate()
        self.proc = None
        if errs:
            print(errs)
        return (out, errs)
