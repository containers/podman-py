#!/usr/bin/env python3
"""Sync Python floor and test matrix after a new Python minor ships.

Called by Renovate postUpgradeTasks when the tracker file is bumped.
Fetches the EOL schedule from endoflife.date, computes the floor as
oldest-non-EOL + 1, and updates every file that carries a Python
version list or constraint.

Usage:
    python3 contrib/renovate/sync_python_versions.py --apply
    python3 contrib/renovate/sync_python_versions.py --dry-run
"""

from __future__ import annotations

import argparse
import difflib
import json
import re
import sys
from datetime import date
from pathlib import Path
from urllib.request import urlopen

EOL_API = "https://endoflife.date/api/python.json"


def fetch_python_versions() -> tuple[int, list[int]]:
    """Return (oldest_non_eol_minor, [released_minors]) for Python 3.x."""
    with urlopen(EOL_API, timeout=60) as resp:
        releases = json.load(resp)
    today = date.today()
    released: list[int] = []
    oldest_non_eol: int | None = None
    for entry in releases:
        cycle = entry.get("cycle", "")
        if not cycle.startswith("3."):
            continue
        minor = int(cycle.split(".")[1])
        if date.fromisoformat(entry["releaseDate"]) <= today:
            released.append(minor)
        eol = entry.get("eol")
        if isinstance(eol, str) and date.fromisoformat(eol) > today:
            if oldest_non_eol is None or minor < oldest_non_eol:
                oldest_non_eol = minor
    if oldest_non_eol is None:
        raise RuntimeError("no non-EOL Python 3.x versions found")
    return oldest_non_eol, sorted(released)


def compute_policy(
    oldest_non_eol: int,
    released: list[int],
) -> tuple[int, list[tuple[int, int]]]:
    """Return (floor_minor, [(3, m), ...]) where floor is oldest_non_eol + 1."""
    floor = oldest_non_eol + 1
    matrix = [(3, m) for m in released if m >= floor]
    if not matrix:
        raise RuntimeError(f"no released Python >= 3.{floor}")
    return floor, matrix


# ---- file updaters ----
# All share the signature (text, floor, matrix) -> str.
# Callers decide whether to write or diff.


def _sub(text: str, pattern: str, repl, **kw) -> str:
    return re.sub(pattern, repl, text, **kw)


def update_pyproject(text: str, floor: int, matrix: list[tuple[int, int]]) -> str:
    text = _sub(text, r'requires-python\s*=\s*">=\d+\.\d+"', f'requires-python = ">=3.{floor}"')
    text = _sub(
        text,
        r'([ ]+"Programming Language :: Python :: 3 :: Only",\n)'
        r'(?:[ ]+"Programming Language :: Python :: 3\.\d+",\n)+',
        lambda m: (
            m.group(1)
            + "".join(f'    "Programming Language :: Python :: {a}.{b}",\n' for a, b in matrix)
        ),
    )
    return text


def update_setup_cfg(text: str, floor: int, matrix: list[tuple[int, int]]) -> str:
    text = _sub(
        text,
        r'^python_requires\s*=\s*.+$',
        f'python_requires = >=3.{floor}',
        count=1,
        flags=re.MULTILINE,
    )
    text = _sub(
        text,
        r'([ ]+Programming Language :: Python :: 3 :: Only\n)'
        r'(?:[ ]+Programming Language :: Python :: 3\.\d+\n)+',
        lambda m: (
            m.group(1)
            + "".join(f'    Programming Language :: Python :: {a}.{b}\n' for a, b in matrix)
        ),
    )
    return text


def update_tox(text: str, floor: int, matrix: list[tuple[int, int]]) -> str:
    envlist = "coverage," + ",".join(f"py{a}{b}" for a, b in matrix)
    return _sub(text, r'^envlist\s*=\s*.+$', f'envlist = {envlist}', count=1, flags=re.MULTILINE)


def update_makefile(text: str, floor: int, matrix: list[tuple[int, int]]) -> str:
    envlist = "coverage," + ",".join(f"py{a}{b}" for a, b in matrix)
    text = _sub(text, r'(-m tox -e )coverage(?:,py\d+)+', rf'\1{envlist}')
    text = _sub(
        text,
        r'brew install python@[^\n]+',
        'brew install ' + ' '.join(f'python@{a}.{b}' for a, b in matrix),
    )
    text = _sub(
        text,
        r'-dnf install -y python3[^\n]+',
        '-dnf install -y python3 ' + ' '.join(f'python{a}.{b}' for a, b in matrix),
    )
    return text


def update_precommit_ci(text: str, floor: int, matrix: list[tuple[int, int]]) -> str:
    return _sub(
        text,
        r'([ ]+python-version: \|\n)(?:[ ]+[0-9x.]+\n)+',
        lambda m: m.group(1) + f'          3.{floor}\n          3.x\n',
        count=1,
    )


def update_fmf(text: str, floor: int, matrix: list[tuple[int, int]]) -> str:
    def repl(m: re.Match[str]) -> str:
        indent, dash = m.group("indent"), m.group("dash")
        return f"{indent}package:\n" + "".join(f"{dash}- python{a}.{b}\n" for a, b in matrix)

    return _sub(
        text,
        r'(?P<indent>[ ]+)package:\n(?P<dash>[ ]+)- python3\.\d+\n(?:(?P=dash)- python3\.\d+\n)*',
        repl,
    )


TARGETS: list[tuple[str, callable]] = [
    ("pyproject.toml", update_pyproject),
    ("setup.cfg", update_setup_cfg),
    ("tox.ini", update_tox),
    ("Makefile", update_makefile),
    (".github/workflows/pre-commit.yml", update_precommit_ci),
    ("plans/main.fmf", update_fmf),
]


def process_all(
    repo: Path,
    floor: int,
    matrix: list[tuple[int, int]],
    *,
    write: bool,
) -> list[str]:
    """Update (or diff) all target files. Returns unified diff lines."""
    diffs: list[str] = []
    for relpath, updater in TARGETS:
        path = repo / relpath
        old = path.read_text()
        new = updater(old, floor, matrix)
        if old != new:
            diffs.extend(
                difflib.unified_diff(
                    old.splitlines(keepends=True),
                    new.splitlines(keepends=True),
                    fromfile=f"a/{relpath}",
                    tofile=f"b/{relpath}",
                )
            )
            if write:
                path.write_text(new)
    return diffs


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--apply", action="store_true", help="Rewrite files in-place")
    group.add_argument("--dry-run", action="store_true", help="Show diffs without writing")
    args = parser.parse_args(argv)

    try:
        oldest_non_eol, released = fetch_python_versions()
        floor, matrix = compute_policy(oldest_non_eol, released)
    except (OSError, RuntimeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    vers = ", ".join(f"{a}.{b}" for a, b in matrix)
    print(f"Oldest non-EOL: 3.{oldest_non_eol}  Floor: >=3.{floor}  Matrix: [{vers}]")

    diffs = process_all(args.repo_root, floor, matrix, write=args.apply)

    if diffs:
        sys.stdout.writelines(diffs)
        if args.apply:
            print("Files updated.")
    else:
        print("No changes needed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
