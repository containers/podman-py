# AI Agent Guide for podman-py Development

![PODMAN logo](https://raw.githubusercontent.com/containers/common/main/logos/podman-logo-full-vert.png)

Unless noted otherwise, paths below are relative to the root of a [podman-py](https://github.com/containers/podman-py) source checkout. You can keep this file as `AGENTS.podman-py.md` in a parent workspace, or name it `AGENTS.md` at the root of a clone. When in doubt, treat [CONTRIBUTING.md](CONTRIBUTING.md) and the checked-in [Makefile](Makefile) / [tox.ini](tox.ini) / [pyproject.toml](pyproject.toml) as the authority.

## Persona

This guide is for AI coding assistants (for example Claude, ChatGPT, Copilot). Use it for layout, test workflow, and upstream expectations when helping **contributors to [containers/podman-py](https://github.com/containers/podman-py)**—patches, tests, docs, and pull requests for the **Python** bindings to [Podman](https://github.com/containers/podman)’s **REST API**.

Source material: [README.md](https://github.com/containers/podman-py/blob/main/README.md), [CONTRIBUTING.md](https://github.com/containers/podman-py/blob/main/CONTRIBUTING.md), [CODE-OF-CONDUCT.md](https://github.com/containers/podman-py/blob/main/CODE-OF-CONDUCT.md), [SECURITY.md](https://github.com/containers/podman-py/blob/main/SECURITY.md).

- **Audience**: **Upstream podman-py contributors** (or aspiring). This repository is *not* the [Podman](https://github.com/containers/podman) **Go** tree: changes here target `podman/` and tests under `podman/tests` as configured in [pyproject.toml](pyproject.toml). For engine behavior, socket paths, or the HTTP API *protocol*, defer to the Podman project and the [libpod API reference](https://docs.podman.io/en/latest/_static/api.html).
- **Mental model**: The published package is **`podman` on PyPI** ([pyproject.toml](https://github.com/containers/podman-py/blob/main/pyproject.toml) name `podman`); it calls **Podman’s libpod service** over the HTTP API. Clients use **`PodmanClient`**, transport lives under **`podman.api`**, and high-level managers live under **`podman.domain`**. Distinguish this from the **Go** [stable bindings](https://github.com/containers/podman/tree/main/pkg/bindings) in the `podman` repository when suggesting imports or file paths.
- **Upstream contract**: The library must follow the same HTTP contract as the daemon. Wrong paths, query parameters, or response handling here surface as bugs in **podman-py** even when the daemon is correct. Cross-check [libpod / Podman API](https://docs.podman.io/en/latest/_static/api.html) and the [Podman Reference](https://podman.readthedocs.io/en/latest/Reference.html).
- **Quality bar**: [CONTRIBUTING.md](CONTRIBUTING.md) — **Python >= 3.9**; **ruff** and [CONTRIBUTING’s **pylint**](https://github.com/containers/podman-py/blob/main/CONTRIBUTING.md) (exceptions need a case); `make lint` and **pre-commit** are **ruff** + **mypy**—add **pylint** if reviewers or CI need it. **Coverage**: CONTRIBUTING says **≥ 85%** to merge; [tox.ini `testenv:coverage`](https://github.com/containers/podman-py/blob/main/tox.ini) currently uses `coverage report --fail-under=80`—**prefer the 85% rule** when the two differ. **integration** tests for large changes. **DCO** **Signed-off-by** (`git commit -s`). **Security**: [SECURITY.md](SECURITY.md) and the [Containers security policy](https://github.com/containers/common/blob/main/SECURITY.md).
- **Community**: [CODE-OF-CONDUCT.md](CODE-OF-CONDUCT.md). Coordination: GitHub [issues/PRs](https://github.com/containers/podman-py); [CONTRIBUTING](https://github.com/containers/podman-py/blob/main/CONTRIBUTING.md) also notes IRC **#podman** on irc.libera.chat.

## Project overview

**podman-py** is a Python package (`pip install podman`) that uses the [Podman (libpod) HTTP API](https://docs.podman.io/en/latest/_static/api.html). Many high-level ideas overlap with the [Docker Engine HTTP API](https://docs.docker.com/engine/api/latest/); the **source of truth** for this project is still **libpod** / Podman ([static API](https://docs.podman.io/en/latest/_static/api.html)). Published docs: [readthedocs](https://podman-py.readthedocs.io/en/latest/).

- **Language / runtime**: Python **3.9+** (`requires-python` in [pyproject.toml](pyproject.toml))
- **Build / packaging**: setuptools, [pyproject.toml](pyproject.toml) + [setup.py](setup.py) / [setup.cfg](setup.cfg) as applicable in-tree
- **Tests**: The default story is **pytest**; `testpaths` is set under **`pyproject.toml` → `[tool.pytest.ini_options]`** (see directory `podman/tests`), usually driven by **tox** ([tox.ini](tox.ini)). The [Makefile](Makefile) also provides **`make unittest` / `make integration`**, which use Python’s [unittest](https://docs.python.org/3/library/unittest.html#test-discovery) with **coverage** (see `--fail-under` / `--omit` in the Makefile; same **80%** report threshold as [tox.ini `testenv:coverage`](https://github.com/containers/podman-py/blob/main/tox.ini) today—**CONTRIBUTING** still states **85%** for merge).
- **Coverage / quality**: [coverage.py](https://coverage.readthedocs.io/); report config in [`.coveragerc`](.coveragerc) and **[tool.coverage.report](https://github.com/containers/podman-py/blob/main/pyproject.toml)** in [pyproject.toml](https://github.com/containers/podman-py/blob/main/pyproject.toml); [coverage configuration](https://coverage.readthedocs.io/en/latest/config.html); [ruff](https://docs.astral.sh/ruff/) (lint + format); [mypy](https://mypy-lang.org/) (selective: many modules still have `ignore_errors` in [pyproject.toml](https://github.com/containers/podman-py/blob/main/pyproject.toml); **new** code should add sensible **type hints** where feasible); [pylint](https://pypi.org/project/pylint/) (`.pylintrc`); **Sphinx** for API docs; optional [pre-commit](https://pre-commit.com/) ([.pre-commit-config.yaml](.pre-commit-config.yaml))

## Quick start

```bash
git clone https://github.com/containers/podman-py.git
cd podman-py
pip install -e ".[test]"
pip install tox
tox -e coverage
# or: make tests
```

**More setup (optional):**

- Optional extras: `pip install -e ".[progress_bar,docs,test]"`
- Install `tox` and OS Python versions the way the maintainers expect: `make tox` (see [Makefile](Makefile); uses `dnf` vs `brew` as available)
- Isolated dev venv from tox: `tox --devenv venv` (see [tox devenv](https://tox.readthedocs.io/en/latest/examples/devenv.html))

[CONTRIBUTING.md](CONTRIBUTING.md) has the canonical `tox` invocations, including `tox -e py -- ...` and pytest options **after** `--`.

## Build, test, and quality (Make + tox)

[CONTRIBUTING.md](CONTRIBUTING.md) documents `tox` in detail; the repo’s [Makefile](Makefile) provides the same work through targets—use **either** pattern, and prefer **tox** when the Makefile does not cover a scenario (e.g. `tox -e py312 -- podman/tests/...` with pytest options after `--`). In [tox.ini](tox.ini), `envlist` is `coverage,py39,py310,py311,py312,py313`—use those names (or `tox list` / `tox -av` in a clone). Some **CONTRIBUTING** examples say `tox -e py` or `tox -e py12`; align with the **env names actually in [tox.ini](tox.ini)** if a command errors.

| Area | Make target | Notes |
|------|-------------|--------|
| Test with coverage + multiple Pythons | `make tests` | Runs `tox -e coverage,py39,…,py313` (see Makefile) |
| Unit tests only (unittest) | `make unittest` | `unittest discover` + coverage; `fail-under=80` in Makefile for this path |
| Integration only | `make integration` | `unittest` on `podman/tests/integration` |
| pnext / podman-next | (see Makefile) | e.g. `make tests-ci-base-python-podman-next` |
| Lint (format, lint, mypy via tox) | `make lint` | |
| DCO + lint | `make validate` | requires **git-validation** in PATH for `.gitvalidation` |
| Docs (Sphinx) | `make docs` | Matches readthedocs flow (see comments in Makefile) |
| Build sdist/wheel | `make podman` or `python -m build` | |
| Tox on PATH; optional OS Python install | `make tox` | Platform-specific (dnf vs brew) |

`make unittest` / `make integration` and `tox -e coverage` all use **`coverage report` with `--fail-under=80`** in the [Makefile](https://github.com/containers/podman-py/blob/main/Makefile) and [tox.ini](https://github.com/containers/podman-py/blob/main/tox.ini) on current `main`. [CONTRIBUTING.md](CONTRIBUTING.md) still says **85%** for merge—satisfy the **documented 85%** when preparing a PR, and be aware the automated `coverage` env may be stricter or looser until the two are aligned.

**Environment for tests (common):**

- **`PODMAN_BINARY`** – path to the `podman` binary under test
- **`PODMAN_LOG_LEVEL`**, **`DEBUG`** – as used in the suite / debugging (see tests and [CONTRIBUTING.md](CONTRIBUTING.md))
- **SSH to localhost** – the integration path may wait on forwarded sockets; ensure `ssh localhost exit` works (see "Common test issues" in [CONTRIBUTING.md](CONTRIBUTING.md))

### Rootful vs rootless testing

The client connects to a **running Podman** via a **base URL** (for example a **rootless** socket `unix:///run/user/$UID/podman/podman.sock` vs a **rootful** socket or TCP). The same test file can behave differently depending on which daemon and URI you use. When reproducing or writing tests (especially **integration**), state explicitly: **rootless** (user service, typical dev) **vs** **root** (e.g. `/run/podman/podman.sock` with appropriate rights). Match **PODMAN_BINARY** and the socket/URI to the same policy you intend to support; if a failure only appears in one mode, it is often permissions, subuid/subgid, or networking—mirroring real [Podman rootless](https://github.com/containers/podman/blob/main/rootless.md) constraints.

## Packit, tmt, and CI plans

The tree includes **[Packit](https://packit.dev/)** ([.packit.yaml](.packit.yaml)), **[tmt](https://tmt.readthedocs.io/)** metadata (for example [`.fmf`](.fmf), [`plans/`](plans/)), and [gating.yml](gating.yml) for **downstream / Fedora-style** gating. These define **automation and plan-based** runs, not the default loop for a laptop (that remains **tox** / **make** and a local **podman**). If you are debugging CI-only failures, look at **tmt** plans and Packit config in addition to `tox.ini` and [GitHub Actions](.github) if present.

## Codebase structure

```text
podman-py/
├── podman/                   # main import package
│   ├── api/                  # HTTP, UDS, SSH, adapters (see "Security" below)
│   ├── client.py
│   ├── domain/
│   ├── errors/
│   └── tests/                # unit/ and integration/; pytest `testpaths`
├── plans/                    # tmt plans (downstream/CI)
├── docs/                     # Sphinx; HTML under docs/.../ _build/ when built
├── contrib/                  # auxiliary
├── .fmf/                     # tmt metadata
├── .github/                  # CI
├── .packit.yaml, gating.yml
├── pyproject.toml            # deps, pytest, ruff, mypy, coverage, setuptools
├── setup.py, setup.cfg, MANIFEST.in
├── tox.ini
├── Makefile
├── .readthedocs.yaml         # Read the Docs: Sphinx, see docs/source/
├── .pylintrc
├── .pre-commit-config.yaml
└── .coveragerc
```

### Key files (at a glance)

| File | Role |
|------|------|
| [Makefile](Makefile) | `make tests`, `make lint`, `make docs`, `make validate`, `make podman` (package build), release/RPM-style targets |
| [tox.ini](tox.ini) | `tox` envs, factors, commands |
| [pyproject.toml](pyproject.toml) | Dependencies, tool configs (pytest, ruff, mypy, coverage) |
| [.pre-commit-config.yaml](.pre-commit-config.yaml) | Commit-time hooks (ruff, mypy, tmt-lint, …) |
| [.readthedocs.yaml](.readthedocs.yaml) / [docs/source/conf.py](docs/source/conf.py) / [Makefile `docs`](https://github.com/containers/podman-py/blob/main/Makefile) | **Sphinx** HTML and RTD |

**Generated or local-only paths** (do not treat as hand-edited source: `build/`, `dist/`, `*.egg-info/`, `.tox/`, `.venv/` / `venv/`, `__pycache__/`, `docs/**/_build/`, `.pytest_cache/`, `.mypy_cache/`, `.coverage`). Favor [CONTRIBUTING](https://github.com/containers/podman-py/blob/main/CONTRIBUTING.md) and the **IDE and ignore files** section below over duplicating huge ignore lists.

## Development patterns

### High-level client

```python
from podman import PodmanClient

uri = "unix:///run/user/1000/podman/podman.sock"  # rootless example; rootful uses different path
with PodmanClient(base_url=uri) as client:
    client.version()
    for c in client.containers.list():
        c.reload()
        print(c.id, c.status)
```

Feature work usually touches **domain** and **api**, with **unit** tests in `podman/tests/unit/`, and **integration** in `podman/tests/integration/` for larger behavior ([CONTRIBUTING.md](CONTRIBUTING.md)).

## Testing (detail)

- **Tox** – primary way to run what CI and CONTRIBUTING describe: `tox -e coverage`, `tox -e py312 -- podman/tests/...` (or another env from [tox.ini `envlist`](https://github.com/containers/podman-py/blob/main/tox.ini)), pytest options **after** `--` ([CONTRIBUTING](https://github.com/containers/podman-py/blob/main/CONTRIBUTING.md)).
- **Pnext** – `@pytest.mark.pnext` and `--pnext` for not-yet-stable daemon features; use sparingly ([CONTRIBUTING.md](CONTRIBUTING.md), `make tests-ci-base-python-podman-next`).
- **Version / OS** – `PODMAN_VERSION`, `OS_RELEASE` from `podman.tests.utils` for `skipif` patterns in [CONTRIBUTING.md](CONTRIBUTING.md).
- **Structure** – [pyproject.toml](pyproject.toml) `testpaths` → `podman/tests`; `unit` vs `integration` subpackages match **Makefile** `make unittest` / `make integration`.
- **Coverage** – [CONTRIBUTING](https://github.com/containers/podman-py/blob/main/CONTRIBUTING.md) requires **not below 85%** for merge. The `tox -e coverage` command in [tox.ini](tox.ini) currently runs `coverage report --fail-under=80`; [pyproject.toml](https://github.com/containers/podman-py/blob/main/pyproject.toml) has `[tool.coverage.report]` extras ([coverage config](https://coverage.readthedocs.io/en/latest/config.html)).

**Example patterns** (illustrative; [CONTRIBUTING](https://github.com/containers/podman-py/blob/main/CONTRIBUTING.md) is canonical):

```python
import pytest
from podman.tests.utils import OS_RELEASE, PODMAN_VERSION

@pytest.mark.skipif(
    PODMAN_VERSION < (5, 6, 0),
    reason="Feature introduced in Podman 5.6.0",
)
@pytest.mark.skipif(
    OS_RELEASE["ID"] == "fedora" and int(OS_RELEASE["VERSION_ID"]) < 42,
    reason="Patched in Fedora 42+",
)
def test_feature():
    pass

@pytest.mark.pnext
def test_future_feature():
    pass
```

## Code standards

- **Ruff** ([formatter](https://docs.astral.sh/ruff/formatter/) + [linter](https://docs.astral.sh/ruff/linter/)): configured in [pyproject.toml](https://github.com/containers/podman-py/blob/main/pyproject.toml) `[tool.ruff]`. Line length **100**; `quote-style = "preserve"`. The `exclude` list in `[tool.ruff]` applies to both linting and formatting (`.history`, `_build`, `build`, `dist`, etc.); the `[tool.ruff.format]` section inherits it—avoid duplicating excludes in the format subsection. The enabled rule set includes, among others, **Pyflakes (F)**, **pycodestyle (E, W)**, **pep8-naming (N)**, **pyupgrade (UP)**, **bugbear (B)**, **builtins (A)**, **YTT**, and **Pylint convention/error/warning (PLC, PLE, PLW)**; see the file for `select` / `ignore` and the full [rule list](https://docs.astral.sh/ruff/rules/). Quick local edits: `ruff format` / `ruff check --fix` (CI still expects **pylint** to pass as in CONTRIBUTING).
- **Mypy**: strictness varies; many `podman` modules are still under per-module `ignore_errors`. Note: `PodmanResource` and `Manager` base classes declare `self.client` as `Optional[APIClient]`; domain subclasses should use the `self.api` property (defined on both base classes) for API calls—it returns a narrowed `APIClient` and raises `AttributeError` if the client is not configured, avoiding `union-attr` errors without type-ignore pragmas.
- **Pylint** – [CONTRIBUTING](https://github.com/containers/podman-py/blob/main/CONTRIBUTING.md) still requires it when applicable; it is not part of the default [Makefile `lint`](https://github.com/containers/podman-py/blob/main/Makefile) target (`tox -e format,lint,mypy`) or the **ruff/mypy** [pre-commit](https://github.com/containers/podman-py/blob/main/.pre-commit-config.yaml) set—run **pylint** explicitly if CI or reviewers expect it.
- **Docstrings** – **Google** style, kwargs in a **Keyword Arguments** section per project convention ([CONTRIBUTING](https://github.com/containers/podman-py/blob/main/CONTRIBUTING.md)); **spaces**, not tabs.
- **Type hints** – add them for new code when mypy is not already ignoring the module, to reduce the legacy `ignore_errors` footprint.
- **Pre-commit** ([.pre-commit-config.yaml](https://github.com/containers/podman-py/blob/main/.pre-commit-config.yaml)): ruff, mypy, **tmt** lint, YAML checks, and more—`pre-commit install` / `pre-commit run -a` (Ruff **rev** in pre-commit may differ from the **ruff==** pin in [tox.ini](https://github.com/containers/podman-py/blob/main/tox.ini) for `lint`/`format`).

## Security and SSH in `podman.api`

**SSH and TLS** in `podman.api` affect trust boundaries. Treat changes with **extra review**: preserve **host key verification** where appropriate, avoid “disable all checks” patterns for real deployments, and use **tight file permissions** on identity material (e.g. **0600**), valid paths, and the usual SSH hygiene. If you change connection or verification behavior, get **maintainer** sign-off. Follow [SECURITY.md](SECURITY.md) and the [Containers security process](https://github.com/containers/common/blob/main/SECURITY.md) for non-public issues.

## Key dependencies and tools

- **requests** / **urllib3** – HTTP client stack ([pyproject.toml](pyproject.toml) `dependencies`)
- **Pytest** / **coverage** / **tox** / **requests-mock** – test extra
- **ruff**, **mypy**, **.pylintrc** – static analysis

## Version, release, and cleanup

- **Version**: driven from the package (see [pyproject.toml](https://github.com/containers/podman-py/blob/main/pyproject.toml) `dynamic` / `podman.version.__version__`); do not hand-edit a random “version=” in this file without following project practice.
- **Releases (maintainers)**: [Makefile](Makefile) has targets such as `make test-release` (TestPyPI), `make release` (PyPI), and `make rpm` / packaging helpers—read that file and maintainer docs before use.
- **Clean**: `make clean`, `make clobber` (aggressive, includes uninstall) as defined in the Makefile.

## Common local issues

- **Tox state** – if environments are broken or stale, `tox --recreate` (or equivalent) before debugging further.
- **`make validate` / DCO** – the **validate** target runs [git-validation](https://github.com/vbatts/git-validation) for DCO, subject length, and related checks; the binary must be on **PATH** or the step fails.
- **SSH and integration tests** – if logs show repeated `Waiting on ... podman-forward-...sock` lines, re-check that **`ssh localhost exit`** works (see [CONTRIBUTING](https://github.com/containers/podman-py/blob/main/CONTRIBUTING.md) “Common test issues”).

## IDE and ignore files

[**.gitignore**](https://git-scm.com/docs/gitignore) is the main place to exclude build artifacts, virtualenvs, and caches from version control. Editor- or tool-specific ignore lists should **not** repeat the same large rule sets unless a path truly must be excluded from that tool and **not** from git; in that case, prefer extending **`.gitignore`** first so the whole project benefits.

## Common pitfalls for AI agents

1. **Wrong repository** – `pkg/api` / `pkg/bindings` in **Go** [podman](https://github.com/containers/podman) are not this project; the PyPI name **`podman`** is **this** library.
2. **Only `make` or only `tox` dogma** – The **Makefile** calls **tox**; [CONTRIBUTING.md](https://github.com/containers/podman-py/blob/main/CONTRIBUTING.md) is written around **tox**. Use the pair consistently with the table above.
3. **80% in Makefile/tox vs 85% in CONTRIBUTING** – [tox.ini `testenv:coverage`](https://github.com/containers/podman-py/blob/main/tox.ini) and **make unittest**/**integration** use **`--fail-under=80`**; [CONTRIBUTING](https://github.com/containers/podman-py/blob/main/CONTRIBUTING.md) still says **85%** for merge—use the text policy when in doubt.
4. **API drift** – Client paths and payloads must match the live **libpod** API docs.
5. **SSH** – Failing or hanging tests: often `ssh localhost` (see [CONTRIBUTING.md](CONTRIBUTING.md) “Common test issues”); not always a Python bug.
6. **Rootful vs rootless** – A test can pass in one **daemon mode** and not the other; do not over-generalize.
7. **Redundant ignore files** – Avoid duplicating **`.gitignore`** rules in editor-only or tool-only ignore config; see **IDE and ignore files** above.

## Essential commands

```bash
# List Makefile targets
grep -E '^[a-z].*:' Makefile   # or read Makefile (no dedicated `make help` in-tree)

# Lint and format
make lint
ruff check .
ruff format .

# Tests (tox is canonical; see CONTRIBUTING)
tox -e coverage
make tests
tox -e py312 -- podman/tests/integration/ -k pattern   # pick env from tox.ini envlist
tox -e py312 -- --pnext -m pnext podman/tests/...      # pnext, when applicable

# Broken tox env
tox --recreate

# DCO + lint
make validate   # needs git-validation on PATH

# Docs
make docs        # apidoc + Sphinx; see Makefile for readthedocs-matching command

# Release (maintainers only; see Makefile)
# make test-release, make release, make rpm
```

## Documentation

- [CONTRIBUTING.md](CONTRIBUTING.md) (authoritative for tests, signing, and workflow)
- [CODE-OF-CONDUCT.md](CODE-OF-CONDUCT.md), [SECURITY.md](SECURITY.md)
- [podman-py on Read the Docs](https://podman-py.readthedocs.io/en/latest/)
- [Podman (libpod) API](https://docs.podman.io/en/latest/_static/api.html) (this library’s **contract** with the daemon)
- [Podman Reference](https://podman.readthedocs.io/en/latest/Reference.html) (CLI, useful when mapping user reports to API behavior)
- [Docker Engine API](https://docs.docker.com/engine/api/latest/) (**reference only** for readers from Docker; libpod remains canonical for Podman)
- [containers/podman](https://github.com/containers/podman) (daemon and **Go** `pkg/bindings`)

If this guide disagrees with **CONTRIBUTING.md** or the **main** [Makefile](https://github.com/containers/podman-py/blob/main/Makefile) / [tox.ini](https://github.com/containers/podman-py/blob/main/tox.ini) / [pyproject.toml](https://github.com/containers/podman-py/blob/main/pyproject.toml), the repository files win.
