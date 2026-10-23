import json
import unittest

try:
    # Python >= 3.10
    from collections.abc import Iterator
except ImportError:
    # Python < 3.10
    from collections.abc import Iterator

from unittest.mock import DEFAULT, MagicMock, patch

import requests_mock

from podman import PodmanClient, tests
from podman.domain.containers import Container
from podman.domain.containers_create import CreateMixin
from podman.domain.containers_manager import ContainersManager
from podman.errors import APIError, NotFound

FIRST_CONTAINER = {
    "Id": "87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd",
    "Image": "quay.io/fedora:latest",
    "Name": "evil_ptolemy",
    "HostConfig": {"LogConfig": {"Type": "json-file"}},
}
SECOND_CONTAINER = {
    "Id": "6dc84cc0a46747da94e4c1571efcc01a756b4017261440b4b8985d37203c3c03",
    "Image": "quay.io/fedora:rc",
    "Name": "good_galileo",
}


class ContainersManagerTestCase(unittest.TestCase):
    """Test ContainersManager area of concern.

    Note:
        Mock responses need to be coded for libpod returns.  The python bindings are responsible
            for mapping to compatible output.
    """

    def setUp(self) -> None:
        super().setUp()

        self.client = PodmanClient(base_url=tests.BASE_SOCK)

    def tearDown(self) -> None:
        super().tearDown()

        self.client.close()

    def test_podmanclient(self):
        manager = self.client.containers
        self.assertIsInstance(manager, ContainersManager)

    @requests_mock.Mocker()
    def test_get(self, mock):
        mock.get(
            tests.LIBPOD_URL
            + "/containers/87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd/json",
            json=FIRST_CONTAINER,
        )

        actual = self.client.containers.get(
            "87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd"
        )
        self.assertEqual(
            actual.id,
            "87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd",
        )

    @requests_mock.Mocker()
    def test_get_404(self, mock):
        mock.get(
            tests.LIBPOD_URL
            + "/containers/87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd/json",
            json={
                "cause": "Container not found.",
                "message": "Container not found.",
                "response": 404,
            },
            status_code=404,
        )

        with self.assertRaises(NotFound):
            self.client.containers.get(
                "87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd"
            )

    @requests_mock.Mocker()
    def test_list_empty(self, mock):
        mock.get(
            tests.LIBPOD_URL + "/containers/json",
            text="[]",
        )
        actual = self.client.containers.list()
        self.assertListEqual(actual, [])

    @requests_mock.Mocker()
    def test_list(self, mock):
        mock.get(
            tests.LIBPOD_URL + "/containers/json",
            json=[FIRST_CONTAINER, SECOND_CONTAINER],
        )
        actual = self.client.containers.list()
        self.assertIsInstance(actual, list)

        self.assertEqual(
            actual[0].id,
            "87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd",
        )
        self.assertEqual(
            actual[1].id,
            "6dc84cc0a46747da94e4c1571efcc01a756b4017261440b4b8985d37203c3c03",
        )

    @requests_mock.Mocker()
    def test_list_filtered(self, mock):
        mock.get(
            tests.LIBPOD_URL + "/containers/json?"
            "all=True"
            "&filters=%7B"
            "%22before%22%3A"
            "+%5B%226dc84cc0a46747da94e4c1571efcc01a756b4017261440b4b8985d37203c3c03%22%5D%2C"
            "+%22since%22%3A"
            "+%5B%2287e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd%22%5D%2C"
            "+%22status%22%3A+%5B%22running%22%5D%7D",
            json=[FIRST_CONTAINER, SECOND_CONTAINER],
        )
        actual = self.client.containers.list(
            all=True,
            filters={"status": "running"},
            since="87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd",
            before="6dc84cc0a46747da94e4c1571efcc01a756b4017261440b4b8985d37203c3c03",
        )
        self.assertIsInstance(actual, list)

        self.assertEqual(
            actual[0].id,
            "87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd",
        )
        self.assertEqual(
            actual[1].id,
            "6dc84cc0a46747da94e4c1571efcc01a756b4017261440b4b8985d37203c3c03",
        )

    @requests_mock.Mocker()
    def test_list_multiple_labels(self, mock):
        filters = {"label": ["team=platform", "env=test"], "status": "running"}
        mock.get(tests.LIBPOD_URL + "/containers/json", json=[FIRST_CONTAINER])

        actual = self.client.containers.list(filters=filters)

        self.assertEqual([container.id for container in actual], [FIRST_CONTAINER["Id"]])
        self.assertEqual(
            json.loads(mock.last_request.qs["filters"][0]),
            {"label": ["team=platform", "env=test"], "status": ["running"]},
        )
        self.assertEqual(filters, {"label": ["team=platform", "env=test"], "status": "running"})

    @requests_mock.Mocker()
    def test_list_no_filters(self, mock):
        mock.get(
            tests.LIBPOD_URL + "/containers/json",
            json=[FIRST_CONTAINER, SECOND_CONTAINER],
        )
        actual = self.client.containers.list()
        self.assertIsInstance(actual, list)

        self.assertEqual(
            actual[0].id,
            "87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd",
        )
        self.assertEqual(
            actual[1].id,
            "6dc84cc0a46747da94e4c1571efcc01a756b4017261440b4b8985d37203c3c03",
        )

    @requests_mock.Mocker()
    def test_list_sparse_libpod_default(self, mock):
        mock.get(
            tests.LIBPOD_URL + "/containers/json",
            json=[FIRST_CONTAINER, SECOND_CONTAINER],
        )
        actual = self.client.containers.list()
        self.assertIsInstance(actual, list)

        self.assertEqual(
            actual[0].id, "87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd"
        )
        self.assertEqual(
            actual[1].id, "6dc84cc0a46747da94e4c1571efcc01a756b4017261440b4b8985d37203c3c03"
        )

        # Verify that no individual reload() calls were made for sparse=True (default)
        # Should be only 1 request for the list endpoint
        self.assertEqual(len(mock.request_history), 1)
        self.assertEqual(
            tests.normalized_url(mock.request_history[0].url),
            tests.normalized_url(tests.LIBPOD_URL + "/containers/json"),
        )

    @requests_mock.Mocker()
    def test_list_sparse_libpod_false(self, mock):
        mock.get(
            tests.LIBPOD_URL + "/containers/json",
            json=[FIRST_CONTAINER, SECOND_CONTAINER],
        )
        # Mock individual container detail endpoints for reload() calls
        # that are done for sparse=False
        mock.get(
            tests.LIBPOD_URL + f"/containers/{FIRST_CONTAINER['Id']}/json",
            json=FIRST_CONTAINER,
        )
        mock.get(
            tests.LIBPOD_URL + f"/containers/{SECOND_CONTAINER['Id']}/json",
            json=SECOND_CONTAINER,
        )
        actual = self.client.containers.list(sparse=False)
        self.assertIsInstance(actual, list)

        self.assertEqual(
            actual[0].id, "87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd"
        )
        self.assertEqual(
            actual[1].id, "6dc84cc0a46747da94e4c1571efcc01a756b4017261440b4b8985d37203c3c03"
        )

        # Verify that individual reload() calls were made for sparse=False
        # Should be 3 requests total: 1 for list + 2 for individual container details
        self.assertEqual(len(mock.request_history), 3)

        # Verify the list endpoint was called first
        self.assertEqual(
            tests.normalized_url(mock.request_history[0].url),
            tests.normalized_url(tests.LIBPOD_URL + "/containers/json"),
        )

        # Verify the individual container detail endpoints were called
        individual_urls = {tests.normalized_url(req.url) for req in mock.request_history[1:]}
        expected_urls = {
            tests.normalized_url(tests.LIBPOD_URL + f"/containers/{FIRST_CONTAINER['Id']}/json"),
            tests.normalized_url(tests.LIBPOD_URL + f"/containers/{SECOND_CONTAINER['Id']}/json"),
        }
        self.assertEqual(individual_urls, expected_urls)

    @requests_mock.Mocker()
    def test_list_sparse_compat_default(self, mock):
        mock.get(
            tests.COMPATIBLE_URL + "/containers/json",
            json=[FIRST_CONTAINER, SECOND_CONTAINER],
        )
        # Mock individual container detail endpoints for reload() calls
        # that are done for sparse=False
        mock.get(
            tests.COMPATIBLE_URL + f"/containers/{FIRST_CONTAINER['Id']}/json",
            json=FIRST_CONTAINER,
        )
        mock.get(
            tests.COMPATIBLE_URL + f"/containers/{SECOND_CONTAINER['Id']}/json",
            json=SECOND_CONTAINER,
        )
        actual = self.client.containers.list(compatible=True)
        self.assertIsInstance(actual, list)

        self.assertEqual(
            actual[0].id, "87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd"
        )
        self.assertEqual(
            actual[1].id, "6dc84cc0a46747da94e4c1571efcc01a756b4017261440b4b8985d37203c3c03"
        )

        # Verify that individual reload() calls were made for compat default (sparse=True)
        # Should be 3 requests total: 1 for list + 2 for individual container details
        self.assertEqual(len(mock.request_history), 3)
        self.assertEqual(
            tests.normalized_url(mock.request_history[0].url),
            tests.normalized_url(tests.COMPATIBLE_URL + "/containers/json"),
        )

        # Verify the individual container detail endpoints were called
        individual_urls = {tests.normalized_url(req.url) for req in mock.request_history[1:]}
        expected_urls = {
            tests.normalized_url(
                tests.COMPATIBLE_URL + f"/containers/{FIRST_CONTAINER['Id']}/json"
            ),
            tests.normalized_url(
                tests.COMPATIBLE_URL + f"/containers/{SECOND_CONTAINER['Id']}/json"
            ),
        }
        self.assertEqual(individual_urls, expected_urls)

    @requests_mock.Mocker()
    def test_list_sparse_compat_true(self, mock):
        mock.get(
            tests.COMPATIBLE_URL + "/containers/json",
            json=[FIRST_CONTAINER, SECOND_CONTAINER],
        )
        actual = self.client.containers.list(sparse=True, compatible=True)
        self.assertIsInstance(actual, list)

        self.assertEqual(
            actual[0].id, "87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd"
        )
        self.assertEqual(
            actual[1].id, "6dc84cc0a46747da94e4c1571efcc01a756b4017261440b4b8985d37203c3c03"
        )

        # Verify that no individual reload() calls were made for sparse=True
        # Should be only 1 request for the list endpoint
        self.assertEqual(len(mock.request_history), 1)
        self.assertEqual(
            tests.normalized_url(mock.request_history[0].url),
            tests.normalized_url(tests.COMPATIBLE_URL + "/containers/json"),
        )

    @requests_mock.Mocker()
    def test_prune(self, mock):
        mock.post(
            tests.LIBPOD_URL + "/containers/prune",
            json=[
                {
                    "Id": "87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd",
                    "Size": 1024,
                },
                {
                    "Id": "6dc84cc0a46747da94e4c1571efcc01a756b4017261440b4b8985d37203c3c03",
                    "Size": 1024,
                },
            ],
        )
        actual = self.client.containers.prune()
        self.assertDictEqual(
            actual,
            {
                "ContainersDeleted": [
                    "87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd",
                    "6dc84cc0a46747da94e4c1571efcc01a756b4017261440b4b8985d37203c3c03",
                ],
                "SpaceReclaimed": 2048,
            },
        )

    @requests_mock.Mocker()
    def test_create(self, mock):
        mock.post(
            tests.LIBPOD_URL + "/containers/create",
            status_code=201,
            json={
                "Id": "87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd",
                "Warnings": [],
            },
        )
        mock.get(
            tests.LIBPOD_URL
            + "/containers/87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd/json",
            json=FIRST_CONTAINER,
        )

        actual = self.client.containers.create("fedora", "/usr/bin/ls", cpu_count=9999)
        self.assertIsInstance(actual, Container)

    @requests_mock.Mocker()
    def test_create_404(self, mock):
        # mock the first POST to return 404,
        # then the second POST (after pulling the image) to return 201
        mock.post(
            tests.LIBPOD_URL + "/containers/create",
            [
                {
                    "status_code": 404,
                    "json": {
                        "cause": "Image not found",
                        "message": "Image not found",
                        "response": 404,
                    },
                },
                {
                    "status_code": 201,
                    "json": {
                        "Id": "87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd",
                        "Warnings": [],
                    },
                },
            ],
        )
        self.client.images.pull = MagicMock()
        mock.get(
            tests.LIBPOD_URL + f"/containers/{FIRST_CONTAINER['Id']}/json",
            json=FIRST_CONTAINER,
        )
        actual = self.client.containers.create("fedora", "/usr/bin/ls", cpu_count=9999)
        self.client.images.pull.assert_called_once_with(
            "fedora",
            all_tags=False,
            auth_config=None,
            decode=False,
            platform=None,
            policy="missing",
            progress_bar=False,
            stream=False,
            tls_verify=True,
        )
        self.assertIsInstance(actual, Container)
        self.assertEqual(actual.id, FIRST_CONTAINER['Id'])
        # 2 POSTs for create
        # 1 GET for container json
        self.assertEqual(mock.call_count, 3)

    @requests_mock.Mocker()
    def test_create_api_error(self, mock):
        # Any error other than 404 must surface as APIError, not as a KeyError on "Id".
        mock.post(
            tests.LIBPOD_URL + "/containers/create",
            status_code=500,
            json={
                "cause": "that name is already in use",
                "message": "creating container storage: the container name is already in use",
                "response": 500,
            },
        )
        self.client.images.pull = MagicMock()
        with self.assertRaises(APIError) as e:
            self.client.containers.create("fedora", "/usr/bin/ls", name="dup")
        self.assertEqual(e.exception.response.status_code, 500)
        self.assertIn("already in use", str(e.exception))
        self.client.images.pull.assert_not_called()

    @requests_mock.Mocker()
    def test_create_parse_host_port(self, mock):
        mock_response = MagicMock()
        mock_response.json = lambda: {
            "Id": "87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd",
            "Size": 1024,
        }
        self.client.containers.client.post = MagicMock(return_value=mock_response)
        mock.get(
            tests.LIBPOD_URL
            + "/containers/87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd/json",
            json=FIRST_CONTAINER,
        )

        port_str = {"2233": 3333}
        port_str_protocol = {"2244/tcp": 3344}
        port_int = {2255: 3355}
        ports = {**port_str, **port_str_protocol, **port_int}
        self.client.containers.create("fedora", "/usr/bin/ls", ports=ports)

        self.client.containers.client.post.assert_called()
        expected_ports = [
            {
                "container_port": 2233,
                "host_port": 3333,
                "protocol": "tcp",
            },
            {
                "container_port": 2244,
                "host_port": 3344,
                "protocol": "tcp",
            },
            {
                "container_port": 2255,
                "host_port": 3355,
                "protocol": "tcp",
            },
        ]
        actual_ports = json.loads(self.client.containers.client.post.call_args[1]["data"])[
            "portmappings"
        ]
        self.assertEqual(expected_ports, actual_ports)

    @requests_mock.Mocker()
    def test_create_userns_mode_simple(self, mock):
        mock_response = MagicMock()
        mock_response.json = lambda: {
            "Id": "87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd",
            "Size": 1024,
        }
        self.client.containers.client.post = MagicMock(return_value=mock_response)
        mock.get(
            tests.LIBPOD_URL
            + "/containers/87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd/json",
            json=FIRST_CONTAINER,
        )

        userns = "keep-id"
        self.client.containers.create("fedora", "/usr/bin/ls", userns_mode=userns)
        self.client.containers.client.post.assert_called()
        expected_userns = {"nsmode": userns}

        actual_userns = json.loads(self.client.containers.client.post.call_args[1]["data"])[
            "userns"
        ]
        self.assertEqual(expected_userns, actual_userns)

    @requests_mock.Mocker()
    def test_create_userns_mode_dict(self, mock):
        mock_response = MagicMock()
        mock_response.json = lambda: {
            "Id": "87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd",
            "Size": 1024,
        }
        self.client.containers.client.post = MagicMock(return_value=mock_response)
        mock.get(
            tests.LIBPOD_URL
            + "/containers/87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd/json",
            json=FIRST_CONTAINER,
        )

        userns = {"nsmode": "keep-id", "value": "uid=900"}
        self.client.containers.create("fedora", "/usr/bin/ls", userns_mode=userns)
        self.client.containers.client.post.assert_called()
        expected_userns = dict(**userns)

        actual_userns = json.loads(self.client.containers.client.post.call_args[1]["data"])[
            "userns"
        ]
        self.assertEqual(expected_userns, actual_userns)

    def test_create_nsmode_with_value(self):
        cases = [
            ("ipc_mode", "ipcns", "container:db", {"nsmode": "container", "value": "db"}),
            ("ipc_mode", "ipcns", "shareable", {"nsmode": "shareable"}),
            ("pid_mode", "pidns", "container:db", {"nsmode": "container", "value": "db"}),
            ("pid_mode", "pidns", "ns:/proc/9/ns", {"nsmode": "path", "value": "/proc/9/ns"}),
            ("uts_mode", "utsns", "host", {"nsmode": "host"}),
            ("userns_mode", "userns", "keep-id", {"nsmode": "keep-id"}),
            (
                "userns_mode",
                "userns",
                "keep-id:uid=1000,gid=1000",
                {"nsmode": "keep-id", "value": "uid=1000,gid=1000"},
            ),
            ("userns_mode", "userns", "auto:size=1024", {"nsmode": "auto", "value": "size=1024"}),
            ("network_mode", "netns", "container:db", {"nsmode": "container", "value": "db"}),
            ("network_mode", "netns", "ns:/run/ns/a", {"nsmode": "path", "value": "/run/ns/a"}),
            ("network_mode", "netns", "host", {"nsmode": "host"}),
            ("network_mode", "netns", "bridge", {"nsmode": "bridge"}),
        ]
        for kwarg, key, value, expected in cases:
            with self.subTest(kwarg=kwarg, value=value):
                params = CreateMixin._render_payload({"image": "fedora", kwarg: value})
                self.assertEqual(expected, params[key])

    def test_create_unsupported_key(self):
        with self.assertRaises(TypeError):
            self.client.containers.create("fedora", "/usr/bin/ls", blkio_weight=100.0)

    def test_create_security_opt(self):
        params = CreateMixin._render_payload(
            {
                "image": "fedora",
                "annotations": {"user": "kept"},
                "security_opt": [
                    "seccomp=unconfined",
                    "apparmor=unconfined",
                    "label=type:spc_t",
                    "label:level:s0:c1,c2",
                    "no-new-privileges",
                    "mask=/proc/acpi:/sys/firmware",
                    "unmask=/proc/kcore",
                    "proc-opts=subset=pid",
                ],
            }
        )
        self.assertEqual("unconfined", params["seccomp_profile_path"])
        self.assertEqual("unconfined", params["apparmor_profile"])
        self.assertEqual(["type:spc_t", "level:s0:c1,c2"], params["selinux_opts"])
        self.assertTrue(params["no_new_privileges"])
        self.assertEqual(["/proc/acpi", "/sys/firmware"], params["mask"])
        self.assertEqual(["/proc/kcore"], params["unmask"])
        self.assertEqual(["subset=pid"], params["procfs_opts"])
        self.assertEqual(
            {
                "user": "kept",
                "io.podman.annotations.seccomp": "unconfined",
                "io.podman.annotations.apparmor": "unconfined",
                "io.podman.annotations.label": "type:spc_t,label=level:s0:c1,c2",
            },
            params["annotations"],
        )

    def test_create_security_opt_values(self):
        cases = [
            (["label=disable"], "selinux_opts", ["disable"]),
            (["label=nested"], "label_nested", True),
            (["no-new-privileges=false"], "no_new_privileges", False),
            (["no-new-privileges:true"], "no_new_privileges", True),
            (["systempaths=unconfined"], "unmask", ["ALL"]),
            # Raw SELinux options keep working as before
            (["disable"], "selinux_opts", ["disable"]),
            (["type:spc_t", "level:s0"], "selinux_opts", ["type:spc_t", "level:s0"]),
        ]
        for security_opt, key, expected in cases:
            with self.subTest(security_opt=security_opt):
                params = CreateMixin._render_payload(
                    {"image": "fedora", "security_opt": security_opt}
                )
                self.assertEqual(expected, params[key])

        params = CreateMixin._render_payload({"image": "fedora", "security_opt": ["disable"]})
        self.assertIsNone(params["annotations"])

    def test_create_security_opt_invalid(self):
        for security_opt in (["no-new-privileges=maybe"], ["systempaths=confined"]):
            with self.subTest(security_opt=security_opt):
                with self.assertRaises(ValueError):
                    CreateMixin._render_payload({"image": "fedora", "security_opt": security_opt})

    def test_create_unknown_key(self):
        with self.assertRaises(TypeError):
            self.client.containers.create("fedora", "/usr/bin/ls", unknown_key=100.0)

    @requests_mock.Mocker()
    def test_create_convert_env_list_to_dict(self, mock):
        env_list1 = ["FOO=foo", "BAR=bar"]
        # Test valid list
        converted_dict1 = {"FOO": "foo", "BAR": "bar"}
        self.assertEqual(CreateMixin._convert_env_list_to_dict(env_list1), converted_dict1)

        # Test empty string
        env_list2 = ["FOO=foo", ""]
        self.assertRaises(ValueError, CreateMixin._convert_env_list_to_dict, env_list2)

        # Test non iterable
        env_list3 = ["FOO=foo", None]
        self.assertRaises(TypeError, CreateMixin._convert_env_list_to_dict, env_list3)

        # Test iterable with non string element
        env_list4 = ["FOO=foo", []]
        self.assertRaises(TypeError, CreateMixin._convert_env_list_to_dict, env_list4)

        # Test empty list
        env_list5 = []
        converted_dict5 = {}
        self.assertEqual(CreateMixin._convert_env_list_to_dict(env_list5), converted_dict5)

        # Test single valid environment variable
        env_list6 = ["SINGLE=value"]
        converted_dict6 = {"SINGLE": "value"}
        self.assertEqual(CreateMixin._convert_env_list_to_dict(env_list6), converted_dict6)

        # Test environment variable with empty value
        env_list7 = ["EMPTY="]
        converted_dict7 = {"EMPTY": ""}
        self.assertEqual(CreateMixin._convert_env_list_to_dict(env_list7), converted_dict7)

        # Test environment variable with multiple equals signs
        env_list8 = ["URL=https://example.com/path?param=value"]
        converted_dict8 = {"URL": "https://example.com/path?param=value"}
        self.assertEqual(CreateMixin._convert_env_list_to_dict(env_list8), converted_dict8)

        # Test environment variable with spaces in value
        env_list9 = ["MESSAGE=Hello World", "PATH=/usr/local/bin:/usr/bin"]
        converted_dict9 = {"MESSAGE": "Hello World", "PATH": "/usr/local/bin:/usr/bin"}
        self.assertEqual(CreateMixin._convert_env_list_to_dict(env_list9), converted_dict9)

        # Test environment variable with special characters
        env_list10 = ["SPECIAL=!@#$%^&*()_+-=[]{}|;':\",./<>?"]
        converted_dict10 = {"SPECIAL": "!@#$%^&*()_+-=[]{}|;':\",./<>?"}
        self.assertEqual(CreateMixin._convert_env_list_to_dict(env_list10), converted_dict10)

        # Test environment variable with numeric values
        env_list11 = ["PORT=8080", "TIMEOUT=30"]
        converted_dict11 = {"PORT": "8080", "TIMEOUT": "30"}
        self.assertEqual(CreateMixin._convert_env_list_to_dict(env_list11), converted_dict11)

        # Test environment variable with boolean-like values
        env_list12 = ["DEBUG=true", "VERBOSE=false", "ENABLED=1", "DISABLED=0"]
        converted_dict12 = {
            "DEBUG": "true",
            "VERBOSE": "false",
            "ENABLED": "1",
            "DISABLED": "0",
        }
        self.assertEqual(CreateMixin._convert_env_list_to_dict(env_list12), converted_dict12)

        # Test environment variable with whitespace in key (should preserve)
        env_list13 = [" SPACED_KEY =value", "KEY= spaced_value "]
        converted_dict13 = {" SPACED_KEY ": "value", "KEY": " spaced_value "}
        self.assertEqual(CreateMixin._convert_env_list_to_dict(env_list13), converted_dict13)

        # Test missing equals sign
        env_list14 = ["FOO=foo", "INVALID"]
        self.assertRaises(ValueError, CreateMixin._convert_env_list_to_dict, env_list14)

        # Test environment variable with only equals sign (empty key)
        env_list15 = ["FOO=foo", "=value"]
        self.assertRaises(ValueError, CreateMixin._convert_env_list_to_dict, env_list15)

        # Test environment variable with only whitespace key
        env_list16 = ["FOO=foo", "   =value"]
        self.assertRaises(ValueError, CreateMixin._convert_env_list_to_dict, env_list16)

        # Test whitespace-only string
        env_list17 = ["FOO=foo", "   "]
        self.assertRaises(ValueError, CreateMixin._convert_env_list_to_dict, env_list17)

        # Test various non-string types in list
        env_list18 = ["FOO=foo", 123]
        self.assertRaises(TypeError, CreateMixin._convert_env_list_to_dict, env_list18)

        env_list19 = ["FOO=foo", {"key": "value"}]
        self.assertRaises(TypeError, CreateMixin._convert_env_list_to_dict, env_list19)

        env_list20 = ["FOO=foo", True]
        self.assertRaises(TypeError, CreateMixin._convert_env_list_to_dict, env_list20)

        # Test duplicate keys (last one should win)
        env_list21 = ["KEY=first", "KEY=second", "OTHER=value"]
        converted_dict21 = {"KEY": "second", "OTHER": "value"}
        self.assertEqual(CreateMixin._convert_env_list_to_dict(env_list21), converted_dict21)

        # Test very long environment variable
        long_value = "x" * 1000
        env_list22 = [f"LONG_VAR={long_value}"]
        converted_dict22 = {"LONG_VAR": long_value}
        self.assertEqual(CreateMixin._convert_env_list_to_dict(env_list22), converted_dict22)

        # Test environment variable with newlines and tabs
        env_list23 = ["MULTILINE=line1\nline2\ttabbed"]
        converted_dict23 = {"MULTILINE": "line1\nline2\ttabbed"}
        self.assertEqual(CreateMixin._convert_env_list_to_dict(env_list23), converted_dict23)

        # Test environment variable with unicode characters
        env_list24 = ["UNICODE=こんにちは", "EMOJI=🚀🌟"]
        converted_dict24 = {"UNICODE": "こんにちは", "EMOJI": "🚀🌟"}
        self.assertEqual(CreateMixin._convert_env_list_to_dict(env_list24), converted_dict24)

        # Test case sensitivity
        env_list25 = ["path=/usr/bin", "PATH=/usr/local/bin"]
        converted_dict25 = {"path": "/usr/bin", "PATH": "/usr/local/bin"}
        self.assertEqual(CreateMixin._convert_env_list_to_dict(env_list25), converted_dict25)

    @requests_mock.Mocker()
    def test_run_detached(self, mock):
        mock.post(
            tests.LIBPOD_URL + "/containers/create",
            status_code=201,
            json={
                "Id": "87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd",
                "Warnings": [],
            },
        )
        mock.post(
            tests.LIBPOD_URL
            + "/containers/87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd/start",
            status_code=204,
        )
        mock.get(
            tests.LIBPOD_URL
            + "/containers/87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd/json",
            json=FIRST_CONTAINER,
        )

        with patch.multiple(Container, logs=DEFAULT, wait=DEFAULT, autospec=True) as mock_container:
            mock_container["logs"].return_value = []
            mock_container["wait"].return_value = {"StatusCode": 0}

            actual = self.client.containers.run("fedora", "/usr/bin/ls", detach=True)
            self.assertIsInstance(actual, Container)

    @requests_mock.Mocker()
    def test_run(self, mock):
        mock.post(
            tests.LIBPOD_URL + "/containers/create",
            status_code=201,
            json={
                "Id": "87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd",
                "Warnings": [],
            },
        )
        mock.post(
            tests.LIBPOD_URL
            + "/containers/87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd/start",
            status_code=204,
        )
        mock.get(
            tests.LIBPOD_URL
            + "/containers/87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd/json",
            json=FIRST_CONTAINER,
        )

        mock_logs = (
            b"This is a unittest - line 1",
            b"This is a unittest - line 2",
        )

        with patch.multiple(Container, logs=DEFAULT, wait=DEFAULT, autospec=True) as mock_container:
            mock_container["wait"].return_value = 0

            with self.subTest("Results not streamed"):
                mock_container["logs"].return_value = iter(mock_logs)

                actual = self.client.containers.run("fedora", "/usr/bin/ls")
                self.assertIsInstance(actual, bytes)
                self.assertEqual(actual, b"This is a unittest - line 1This is a unittest - line 2")

            # iter() cannot be reset so subtests used to create new instance
            with self.subTest("Stream results"):
                mock_container["logs"].return_value = iter(mock_logs)

                actual = self.client.containers.run("fedora", "/usr/bin/ls", stream=True)
                self.assertNotIsInstance(actual, bytes)
                self.assertIsInstance(actual, Iterator)
                self.assertEqual(next(actual), b"This is a unittest - line 1")
                self.assertEqual(next(actual), b"This is a unittest - line 2")

    @requests_mock.Mocker()
    def test_run_404(self, mock):
        mock.post(
            tests.LIBPOD_URL + "/containers/create",
            [
                {
                    "status_code": 404,
                    "json": {
                        "cause": "Image not found",
                        "message": "Image not found",
                        "response": 404,
                    },
                },
                {
                    "status_code": 201,
                    "json": {
                        "Id": "87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd",
                        "Warnings": [],
                    },
                },
            ],
        )
        self.client.images.pull = MagicMock()
        mock.post(
            tests.LIBPOD_URL
            + "/containers/87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd/start",
            status_code=204,
        )
        mock.get(
            tests.LIBPOD_URL + f"/containers/{FIRST_CONTAINER['Id']}/json",
            json=FIRST_CONTAINER,
        )

        mock_logs = (
            b"This is a unittest - line 1",
            b"This is a unittest - line 2",
        )

        with patch.multiple(Container, logs=DEFAULT, wait=DEFAULT, autospec=True) as mock_container:
            mock_container["wait"].return_value = 0
            mock_container["logs"].return_value = iter(mock_logs)

            actual = self.client.containers.run("fedora", "/usr/bin/ls")
            self.client.images.pull.assert_called_once_with(
                "fedora",
                auth_config=None,
                platform=None,
                policy="missing",
                progress_bar=False,
                tls_verify=True,
                decode=False,
                all_tags=False,
                stream=False,
            )
            self.assertIsInstance(actual, bytes)
            self.assertEqual(actual, b"This is a unittest - line 1This is a unittest - line 2")
            # 2 POSTs for create
            # 1 POST for start
            # 1 GET for container json
            # 1 GET for reload
            for r in mock.request_history:
                print(r)
            self.assertEqual(mock.call_count, 5)

    @requests_mock.Mocker()
    def test_create_healthcheck_nested_payload(self, mock):
        """Test that fine-grained health kwargs produce nested healthconfig/startupHealthConfig."""
        mock_response = MagicMock()
        mock_response.json = lambda: {
            "Id": "87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd",
            "Size": 1024,
        }
        self.client.containers.client.post = MagicMock(return_value=mock_response)
        mock.get(
            tests.LIBPOD_URL
            + "/containers/87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd/json",
            json=FIRST_CONTAINER,
        )

        self.client.containers.create(
            "fedora",
            "/usr/bin/ls",
            health_cmd="curl -f http://localhost:8080/health",
            health_interval="30s",
            health_timeout="10s",
            health_retries=3,
            health_start_period="1m",
        )

        actual_data = json.loads(self.client.containers.client.post.call_args[1]["data"])

        self.assertEqual(
            actual_data["healthconfig"],
            {
                "Test": ["CMD-SHELL", "curl -f http://localhost:8080/health"],
                "Interval": 30_000_000_000,
                "Timeout": 10_000_000_000,
                "Retries": 3,
                "StartPeriod": 60_000_000_000,
            },
        )

    @requests_mock.Mocker()
    def test_create_startup_healthcheck_nested_payload(self, mock):
        """Test that startup health kwargs produce nested startupHealthConfig."""
        mock_response = MagicMock()
        mock_response.json = lambda: {
            "Id": "87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd",
            "Size": 1024,
        }
        self.client.containers.client.post = MagicMock(return_value=mock_response)
        mock.get(
            tests.LIBPOD_URL
            + "/containers/87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd/json",
            json=FIRST_CONTAINER,
        )

        self.client.containers.create(
            "fedora",
            "/usr/bin/ls",
            health_startup_cmd="curl -f http://localhost:8080/ready",
            health_startup_interval="10s",
            health_startup_timeout="45s",
            health_startup_retries=5,
            health_startup_success=2,
        )

        actual_data = json.loads(self.client.containers.client.post.call_args[1]["data"])

        self.assertEqual(
            actual_data["startupHealthConfig"],
            {
                "Test": ["CMD-SHELL", "curl -f http://localhost:8080/ready"],
                "Interval": 10_000_000_000,
                "Timeout": 45_000_000_000,
                "Retries": 5,
                "Successes": 2,
            },
        )

    @requests_mock.Mocker()
    def test_create_health_scalar_fields(self, mock):
        """Test healthLogDestination, healthMaxLogCount, healthMaxLogSize mapping."""
        mock_response = MagicMock()
        mock_response.json = lambda: {
            "Id": "87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd",
            "Size": 1024,
        }
        self.client.containers.client.post = MagicMock(return_value=mock_response)
        mock.get(
            tests.LIBPOD_URL
            + "/containers/87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd/json",
            json=FIRST_CONTAINER,
        )

        self.client.containers.create(
            "fedora",
            "/usr/bin/ls",
            health_cmd="true",
            health_log_destination="events_logger",
            health_max_log_count=10,
            health_max_logs_size=1024,
        )

        actual_data = json.loads(self.client.containers.client.post.call_args[1]["data"])

        self.assertEqual(actual_data["healthLogDestination"], "events_logger")
        self.assertEqual(actual_data["healthMaxLogCount"], 10)
        self.assertEqual(actual_data["healthMaxLogSize"], 1024)

    @requests_mock.Mocker()
    def test_create_health_on_failure_mapping(self, mock):
        """Test health_on_failure string maps to health_check_on_failure_action int."""
        mock_response = MagicMock()
        mock_response.json = lambda: {
            "Id": "87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd",
            "Size": 1024,
        }
        self.client.containers.client.post = MagicMock(return_value=mock_response)
        mock.get(
            tests.LIBPOD_URL
            + "/containers/87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd/json",
            json=FIRST_CONTAINER,
        )

        self.client.containers.create(
            "fedora",
            "/usr/bin/ls",
            health_cmd="true",
            health_on_failure="restart",
        )

        actual_data = json.loads(self.client.containers.client.post.call_args[1]["data"])
        self.assertEqual(actual_data["health_check_on_failure_action"], 3)

    @requests_mock.Mocker()
    def test_create_no_healthcheck(self, mock):
        """Test no_healthcheck=True produces healthconfig with Test=NONE."""
        mock_response = MagicMock()
        mock_response.json = lambda: {
            "Id": "87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd",
            "Size": 1024,
        }
        self.client.containers.client.post = MagicMock(return_value=mock_response)
        mock.get(
            tests.LIBPOD_URL
            + "/containers/87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd/json",
            json=FIRST_CONTAINER,
        )

        self.client.containers.create("fedora", "/usr/bin/ls", no_healthcheck=True)

        actual_data = json.loads(self.client.containers.client.post.call_args[1]["data"])
        self.assertEqual(actual_data["healthconfig"], {"Test": ["NONE"]})

    def test_create_no_healthcheck_conflicts_with_health_kwargs(self):
        """Test that no_healthcheck=True + health kwargs raises ValueError."""
        with self.assertRaises(ValueError) as ctx:
            self.client.containers.create(
                "fedora", "/usr/bin/ls", no_healthcheck=True, health_cmd="true"
            )
        self.assertIn("no_healthcheck is True", str(ctx.exception))

    def test_create_healthcheck_dict_conflicts_with_health_kwargs(self):
        """Test that healthcheck dict + health_cmd raises ValueError."""
        with self.assertRaises(ValueError) as ctx:
            self.client.containers.create(
                "fedora",
                "/usr/bin/ls",
                healthcheck={"Test": ["CMD-SHELL", "true"]},
                health_cmd="curl localhost",
            )
        self.assertIn("Cannot combine", str(ctx.exception))

    def test_create_health_on_failure_conflicts_with_int(self):
        """Test that health_on_failure + health_check_on_failure_action raises ValueError."""
        with self.assertRaises(ValueError) as ctx:
            self.client.containers.create(
                "fedora",
                "/usr/bin/ls",
                health_cmd="true",
                health_on_failure="restart",
                health_check_on_failure_action=3,
            )
        self.assertIn("Cannot set both", str(ctx.exception))

    def test_create_health_on_failure_invalid_value(self):
        """Test that invalid health_on_failure value raises ValueError."""
        with self.assertRaises(ValueError) as ctx:
            self.client.containers.create(
                "fedora",
                "/usr/bin/ls",
                health_cmd="true",
                health_on_failure="invalid_action",
            )
        self.assertIn("Invalid health_on_failure value", str(ctx.exception))

    @requests_mock.Mocker()
    def test_create_health_duration_as_int(self, mock):
        """Test that int duration values are passed through as nanoseconds."""
        mock_response = MagicMock()
        mock_response.json = lambda: {
            "Id": "87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd",
            "Size": 1024,
        }
        self.client.containers.client.post = MagicMock(return_value=mock_response)
        mock.get(
            tests.LIBPOD_URL
            + "/containers/87e1325c82424e49a00abdd4de08009eb76c7de8d228426a9b8af9318ced5ecd/json",
            json=FIRST_CONTAINER,
        )

        self.client.containers.create(
            "fedora",
            "/usr/bin/ls",
            health_cmd="true",
            health_interval=5_000_000_000,
            health_timeout=2_000_000_000,
        )

        actual_data = json.loads(self.client.containers.client.post.call_args[1]["data"])
        self.assertEqual(actual_data["healthconfig"]["Interval"], 5_000_000_000)
        self.assertEqual(actual_data["healthconfig"]["Timeout"], 2_000_000_000)


if __name__ == "__main__":
    unittest.main()
