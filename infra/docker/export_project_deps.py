"""Export ``project.dependencies`` from ``pyproject.toml`` as a requirements file."""

from __future__ import annotations

import sys
import tomllib
from pathlib import Path


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print("usage: export_project_deps.py <pyproject.toml> <requirements.txt>", file=sys.stderr)
        return 2

    pyproject_path = Path(argv[1])
    requirements_path = Path(argv[2])

    project = tomllib.loads(pyproject_path.read_text(encoding="utf-8")).get("project", {})
    dependencies = project.get("dependencies")
    if not isinstance(dependencies, list) or not all(isinstance(dep, str) for dep in dependencies):
        print("pyproject.toml is missing a valid project.dependencies list", file=sys.stderr)
        return 1

    requirements_path.write_text(
        "".join(f"{dependency}\n" for dependency in dependencies), encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
