"""Generate a Python launcher that preserves a manifest's pipe verbatim."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


PIPE_PREFIX = "\\\\.\\pipe\\"
_SAFE_PIPE_SUFFIX = re.compile(r"[A-Za-z0-9._-]+\Z")
_ROUND = re.compile(r"R[1-9][0-9]*\Z")
_SHA256 = re.compile(r"[0-9A-Fa-f]{64}\Z")
_REVISION = re.compile(r"[0-9A-Fa-f]{40}\Z")


def validate_named_pipe(value: object) -> str:
    if not isinstance(value, str) or not value.startswith(PIPE_PREFIX):
        raise ValueError(f"pipe name must start with {PIPE_PREFIX!r}")
    suffix = value[len(PIPE_PREFIX) :]
    if not _SAFE_PIPE_SUFFIX.fullmatch(suffix):
        raise ValueError("pipe suffix must contain only ASCII letters, digits, ._- ")
    return value


def _relative(value: str, name: str) -> str:
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"{name} must stay below the candidate root")
    return path.as_posix()


def _required_match(pattern: re.Pattern[str], value: str, name: str) -> str:
    if not pattern.fullmatch(value):
        raise ValueError(f"invalid {name}: {value!r}")
    return value


def render_wrapper(
    *,
    manifest_relative: str,
    bootstrap_relative: str,
    save_relative: str,
    dll_relative: str,
    injector_relative: str,
    save_name: str,
    expected_save_sha256: str,
    expected_dll_sha256: str,
    expected_injector_sha256: str,
    expected_game_exe_sha256: str,
    expected_character_id: int,
    old_round: str,
    new_round: str,
    candidate_revision: str,
    publish_timeout: int,
) -> str:
    manifest_relative = _relative(manifest_relative, "manifest path")
    bootstrap_relative = _relative(bootstrap_relative, "bootstrap path")
    save_relative = _relative(save_relative, "save path")
    dll_relative = _relative(dll_relative, "DLL path")
    injector_relative = _relative(injector_relative, "injector path")
    for name, value in (
        ("save SHA-256", expected_save_sha256),
        ("DLL SHA-256", expected_dll_sha256),
        ("injector SHA-256", expected_injector_sha256),
        ("game EXE SHA-256", expected_game_exe_sha256),
    ):
        _required_match(_SHA256, value, name)
    _required_match(_ROUND, old_round, "old round")
    _required_match(_ROUND, new_round, "new round")
    _required_match(_REVISION, candidate_revision, "candidate revision")
    if expected_character_id <= 0 or publish_timeout <= 0:
        raise ValueError("character id and publish timeout must be positive")

    constants = {
        "MANIFEST_RELATIVE": manifest_relative,
        "BOOTSTRAP_RELATIVE": bootstrap_relative,
        "SAVE_RELATIVE": save_relative,
        "DLL_RELATIVE": dll_relative,
        "INJECTOR_RELATIVE": injector_relative,
        "SAVE_NAME": save_name,
        "SAVE_SHA": expected_save_sha256.upper(),
        "DLL_SHA": expected_dll_sha256.upper(),
        "INJECTOR_SHA": expected_injector_sha256.upper(),
        "EXE_SHA": expected_game_exe_sha256.upper(),
        "EXPECTED_CHARACTER": expected_character_id,
        "OLD_ROUND": old_round,
        "NEW_ROUND": new_round,
        "CANDIDATE_REVISION": candidate_revision.lower(),
        "PUBLISH_TIMEOUT": publish_timeout,
    }
    constants_source = "\n".join(
        f"{name} = {value!r}" for name, value in constants.items()
    )
    return f'''#!/usr/bin/env python3
"""Generated bounded private-probe launcher; do not edit."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess


PIPE_PREFIX = {PIPE_PREFIX!r}
{constants_source}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--python", required=True)
    parser.add_argument("--game-dir", type=Path, required=True)
    parser.add_argument("--artifact-dir", type=Path, required=True)
    parser.add_argument("--state-dir", type=Path, required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    root = Path(__file__).resolve().parent
    manifest = root / MANIFEST_RELATIVE
    bootstrap = root / BOOTSTRAP_RELATIVE
    save = root / SAVE_RELATIVE
    dll = root / DLL_RELATIVE
    injector = root / INJECTOR_RELATIVE
    game_exe = args.game_dir.resolve() / "binaries" / "ck3.exe"
    manifest_object = json.loads(manifest.read_text(encoding="utf-8-sig"))
    manifest_pipe = manifest_object.get("next_live", {{}}).get("unique_pipe")
    if not isinstance(manifest_pipe, str) or not manifest_pipe.startswith(PIPE_PREFIX):
        raise RuntimeError("manifest pipe lacks the canonical named-pipe prefix")
    if re.fullmatch(r"[A-Za-z0-9._-]+", manifest_pipe[len(PIPE_PREFIX):]) is None:
        raise RuntimeError("manifest pipe has a non-canonical suffix")
    for input_path in (manifest, bootstrap, save, dll, injector, game_exe):
        if not input_path.is_file():
            raise RuntimeError(f"required input is missing: {{input_path}}")
    for path, expected in (
        (save, SAVE_SHA),
        (dll, DLL_SHA),
        (injector, INJECTOR_SHA),
        (game_exe, EXE_SHA),
    ):
        if sha256(path) != expected:
            raise RuntimeError(f"SHA-256 mismatch: {{path}}")
    manifest_sha = sha256(manifest)
    runner_arguments = [
        "--artifact-dir", str(args.artifact_dir.resolve()),
        "--state-dir", str(args.state_dir.resolve()),
        "--game-dir", str(args.game_dir.resolve()),
        "--source-save", str(save),
        "--save-name", SAVE_NAME,
        "--expected-save-sha256", SAVE_SHA,
        "--candidate-manifest", str(manifest),
        "--expected-candidate-manifest-sha256", manifest_sha,
        "--bridge-dll", str(dll),
        "--expected-bridge-dll-sha256", DLL_SHA,
        "--bridge-injector", str(injector),
        "--expected-bridge-injector-sha256", INJECTOR_SHA,
        "--expected-game-exe-sha256", EXE_SHA,
        "--expected-character-id", str(EXPECTED_CHARACTER),
        "--pipe", manifest_pipe,
        "--old-round", OLD_ROUND,
        "--new-round", NEW_ROUND,
        "--candidate-revision", CANDIDATE_REVISION,
        "--publish-timeout", str(PUBLISH_TIMEOUT),
    ]
    argument_pipe = runner_arguments[runner_arguments.index("--pipe") + 1]
    if argument_pipe != manifest_pipe:
        raise RuntimeError("runner pipe argument differs from candidate manifest")
    if args.dry_run:
        print(json.dumps({{
            "schema": "xar.ck3.bounded_private_probe_wrapper_dry_run_v1",
            "status": "green",
            "ck3_launched": False,
            "manifest_pipe": manifest_pipe,
            "argument_pipe": argument_pipe,
            "argument_pipe_utf16": [ord(value) for value in argument_pipe],
            "manifest_sha256": manifest_sha,
        }}, ensure_ascii=False, indent=2))
        return 0
    completed = subprocess.run([
        args.python,
        str(bootstrap),
        "--python", args.python,
        "--runtime-preflight-output", str(args.artifact_dir / "runtime-preflight.json"),
        "--",
        *runner_arguments,
    ], check=False)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
'''


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate-root", type=Path, required=True)
    parser.add_argument("--manifest-relative", default="candidate-manifest.json")
    parser.add_argument("--output-relative", default="run-bounded-private-probe.py")
    parser.add_argument("--bootstrap-relative", required=True)
    parser.add_argument("--save-relative", required=True)
    parser.add_argument("--dll-relative", required=True)
    parser.add_argument("--injector-relative", required=True)
    parser.add_argument("--save-name", required=True)
    parser.add_argument("--expected-save-sha256", required=True)
    parser.add_argument("--expected-dll-sha256", required=True)
    parser.add_argument("--expected-injector-sha256", required=True)
    parser.add_argument("--expected-game-exe-sha256", required=True)
    parser.add_argument("--expected-character-id", type=int, required=True)
    parser.add_argument("--old-round", required=True)
    parser.add_argument("--new-round", required=True)
    parser.add_argument("--candidate-revision", required=True)
    parser.add_argument("--publish-timeout", type=int, required=True)
    args = parser.parse_args(argv)

    root = args.candidate_root.resolve()
    manifest_relative = _relative(args.manifest_relative, "manifest path")
    output_relative = _relative(args.output_relative, "output path")
    manifest = json.loads((root / manifest_relative).read_text(encoding="utf-8-sig"))
    validate_named_pipe(manifest.get("next_live", {}).get("unique_pipe"))
    output = root / output_relative
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        render_wrapper(
            manifest_relative=manifest_relative,
            bootstrap_relative=args.bootstrap_relative,
            save_relative=args.save_relative,
            dll_relative=args.dll_relative,
            injector_relative=args.injector_relative,
            save_name=args.save_name,
            expected_save_sha256=args.expected_save_sha256,
            expected_dll_sha256=args.expected_dll_sha256,
            expected_injector_sha256=args.expected_injector_sha256,
            expected_game_exe_sha256=args.expected_game_exe_sha256,
            expected_character_id=args.expected_character_id,
            old_round=args.old_round,
            new_round=args.new_round,
            candidate_revision=args.candidate_revision,
            publish_timeout=args.publish_timeout,
        ),
        encoding="utf-8",
        newline="\n",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
