"""Resolve the explicit project runtime for the G2 faction row probe.

This bootstrap uses only the standard library and never falls back to the
Python executable that happened to invoke it.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


REQUIRED_DISTRIBUTIONS = ("nvidia-cublas", "onnxruntime", "pywin32")


def runtime_candidates(
    *,
    requested: Path | None,
    workspace_root: Path | None,
    repo_root: Path,
    environment: dict[str, str],
) -> list[tuple[str, Path]]:
    candidates: list[tuple[str, Path]] = []
    if requested is not None:
        candidates.append(("--python", requested))
    elif environment.get("XAR_PYTHON"):
        candidates.append(("XAR_PYTHON", Path(environment["XAR_PYTHON"])))
    else:
        configured_root = workspace_root
        if configured_root is None and environment.get("XAR_WORKSPACE_ROOT"):
            configured_root = Path(environment["XAR_WORKSPACE_ROOT"])
        if configured_root is not None:
            candidates.append(
                (
                    "workspace-root",
                    configured_root / "tools" / ".venv" / "Scripts" / "python.exe",
                )
            )
        candidates.append(
            (
                "repo-local-runtime",
                repo_root / "tools" / ".venv" / "Scripts" / "python.exe",
            )
        )
    return [(source, path.expanduser().resolve()) for source, path in candidates]


def resolve_runtime_python(
    *,
    requested: Path | None,
    workspace_root: Path | None,
    repo_root: Path,
    environment: dict[str, str],
) -> tuple[str, Path]:
    candidates = runtime_candidates(
        requested=requested,
        workspace_root=workspace_root,
        repo_root=repo_root,
        environment=environment,
    )
    existing = [(source, path) for source, path in candidates if path.is_file()]
    if not existing:
        rendered = ", ".join(f"{source}={path}" for source, path in candidates)
        raise RuntimeError(
            "no explicit XAR project Python exists; set XAR_PYTHON, "
            "XAR_WORKSPACE_ROOT, --workspace-root, or --python; checked " + rendered
        )
    source, selected = existing[0]
    probe = (
        "import importlib.metadata as m;"
        f"names={REQUIRED_DISTRIBUTIONS!r};"
        "missing=[];"
        "\nfor name in names:\n"
        " try: m.version(name)\n"
        " except m.PackageNotFoundError: missing.append(name)\n"
        "\nif missing: raise SystemExit('missing distributions: '+','.join(missing))\n"
    )
    checked = subprocess.run(
        [str(selected), "-c", probe],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    if checked.returncode != 0:
        detail = (checked.stderr or checked.stdout).strip()
        raise RuntimeError(
            f"selected XAR project Python failed dependency preflight: {selected}; {detail}"
        )
    return source, selected


def _write_preflight(path: Path | None, payload: object) -> None:
    if path is None:
        return
    target = path.expanduser().resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--python", type=Path)
    parser.add_argument("--workspace-root", type=Path)
    parser.add_argument("--runtime-preflight-output", type=Path)
    parser.add_argument("runner_arguments", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    runner_arguments = list(args.runner_arguments)
    if runner_arguments and runner_arguments[0] == "--":
        runner_arguments.pop(0)
    if not runner_arguments:
        parser.error("runner arguments are required after --")

    repo_root = Path(__file__).resolve().parents[1]
    runner = (
        repo_root
        / "ck3_autonomous_player"
        / "native_bridge"
        / "research"
        / "run_faction_targeting_row_private_probe_live.py"
    )
    try:
        source, python = resolve_runtime_python(
            requested=args.python,
            workspace_root=args.workspace_root,
            repo_root=repo_root,
            environment=dict(os.environ),
        )
        payload: dict[str, object] = {
            "schema": "xar.ck3.g2_faction_targeting_row_runtime_preflight_v1",
            "status": "green",
            "ck3_launched": False,
            "selection_source": source,
            "python": str(python),
            "runner": str(runner),
        }
        _write_preflight(args.runtime_preflight_output, payload)
    except (OSError, RuntimeError, subprocess.SubprocessError) as error:
        payload = {
            "schema": "xar.ck3.g2_faction_targeting_row_runtime_preflight_v1",
            "status": "red",
            "ck3_launched": False,
            "reason": f"{type(error).__name__}: {error}",
        }
        _write_preflight(args.runtime_preflight_output, payload)
        print(json.dumps(payload, ensure_ascii=False), file=sys.stderr)
        return 2

    environment = dict(os.environ)
    source_root = repo_root / "ck3_autonomous_player" / "src"
    current_pythonpath = environment.get("PYTHONPATH")
    environment["PYTHONPATH"] = (
        str(source_root)
        if not current_pythonpath
        else str(source_root) + os.pathsep + current_pythonpath
    )
    completed = subprocess.run(
        [str(python), str(runner), *runner_arguments],
        cwd=repo_root,
        env=environment,
        check=False,
    )
    return int(completed.returncode)


if __name__ == "__main__":
    raise SystemExit(main())
