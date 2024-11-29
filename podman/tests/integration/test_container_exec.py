import podman.tests.integration.base as base
from podman import PodmanClient

# @unittest.skipIf(os.geteuid() != 0, 'Skipping, not running as root')


class ContainersExecIntegrationTests(base.IntegrationTest):
    """Containers integration tests for exec"""

    def setUp(self):
        super().setUp()

        self.client = PodmanClient(base_url=self.socket_uri)
        self.addCleanup(self.client.close)

        self.alpine_image = self.client.images.pull("quay.io/libpod/alpine", tag="latest")
        self.containers = []

    def tearDown(self):
        for container in self.containers:
            container.remove(force=True)

    def test_container_exec_run(self):
        """Test any command that will return code 0 and no output"""
        container = self.client.containers.create(self.alpine_image, command=["top"], detach=True)
        container.start()
        error_code, stdout = container.exec_run("echo hello")

        self.assertEqual(error_code, 0)
        self.assertEqual(stdout, b'\x01\x00\x00\x00\x00\x00\x00\x06hello\n')

    def test_container_exec_run_errorcode(self):
        """Test a failing command with stdout and stderr in a single bytestring"""
        container = self.client.containers.create(self.alpine_image, command=["top"], detach=True)
        container.start()
        error_code, output = container.exec_run("ls nonexistent")

        self.assertEqual(error_code, 1)
        self.assertEqual(
            output, b"\x02\x00\x00\x00\x00\x00\x00+ls: nonexistent: No such file or directory\n"
        )

    def test_container_exec_run_demux(self):
        """Test a failing command with stdout and stderr in a bytestring tuple"""
        container = self.client.containers.create(self.alpine_image, command=["top"], detach=True)
        container.start()
        error_code, output = container.exec_run("ls nonexistent", demux=True)

        self.assertEqual(error_code, 1)
        self.assertEqual(output[0], None)
        self.assertEqual(output[1], b"ls: nonexistent: No such file or directory\n")

    def test_container_exec_run_stream(self):
        """Test streaming the output from a long running command."""
        container = self.client.containers.create(self.alpine_image, command=["top"], detach=True)
        container.start()

        command = [
            '/bin/sh',
            '-c',
            'echo 0 ; sleep .1 ; echo 1 ; sleep .1 ; echo 2 ; sleep .1 ;',
        ]
        error_code, output = container.exec_run(command, stream=True)

        self.assertEqual(error_code, None)
        self.assertEqual(
            list(output),
            [
                b'0\n',
                b'1\n',
                b'2\n',
            ],
        )

    def test_container_exec_run_stream_demux(self):
        """Test streaming the output from a long running command with demux enabled."""
        container = self.client.containers.create(self.alpine_image, command=["top"], detach=True)
        container.start()

        command = [
            '/bin/sh',
            '-c',
            'echo 0 ; >&2 echo 1 ; sleep .1 ; '
            + 'echo 2 ; >&2 echo 3 ; sleep .1 ; '
            + 'echo 4 ; >&2 echo 5 ; sleep .1 ;',
        ]
        error_code, output = container.exec_run(command, stream=True, demux=True)

        self.assertEqual(error_code, None)
        self.assertEqual(
            list(output),
            [
                (b'0\n', None),
                (None, b'1\n'),
                (b'2\n', None),
                (None, b'3\n'),
                (b'4\n', None),
                (None, b'5\n'),
            ],
        )

    def test_container_exec_run_stream_detach(self):
        """Test streaming the output from a long running command with detach enabled."""
        container = self.client.containers.create(self.alpine_image, command=["top"], detach=True)
        container.start()

        command = [
            '/bin/sh',
            '-c',
            'echo 0 ; sleep .1 ; echo 1 ; sleep .1 ; echo 2 ; sleep .1 ;',
        ]
        error_code, output = container.exec_run(command, stream=True, detach=True)

        # Detach should make the ``exec_run`` ignore the ``stream`` flag so we will assert against the standard,
        # non-streaming behavior.
        self.assertEqual(error_code, 0)
        # The endpoint should return immediately, before we are able to actually get any of the output.
        self.assertEqual(
            output,
            b'\n',
        )
