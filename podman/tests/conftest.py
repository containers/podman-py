import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--pnext", action="store_true", default=False, help="run tests against podman_next copr"
    )


def pytest_configure(config):
    config.addinivalue_line("markers", "pnext: mark test as run against podman_next")


def pytest_collection_modifyitems(config, items):
    if config.getoption("--pnext"):
        # --pnext given in cli: run tests marked as pnext
        return
    podman_next = pytest.mark.skip(reason="need --pnext option to run")
    for item in items:
        if "pnext" in item.keywords:
            item.add_marker(podman_next)
