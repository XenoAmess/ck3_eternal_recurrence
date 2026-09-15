"""Verify the sealed R694 query candidate without launching CK3."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import sys
from pathlib import Path

EXPECTED_SCHEMA = "xar.ck3.g2_m4_council_r694_query_sealed_prep_v1"
EXPECTED_EXE = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
EXPECTED_SAVE = "9104CCB8AE9D5776166FBBAEDA9B43BD08CBAA2CB5C057332EB8B7A1A212CC63"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def verify(root: Path) -> dict[str, object]:
    root = root.resolve()
    manifest_path = root / "sealed-prep-manifest.json"
    checksum = (root / "sealed-prep-manifest.sha256").read_text(encoding="ascii").split()[0]
    if sha256(manifest_path) != checksum.upper():
        raise RuntimeError("sealed manifest checksum differs")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("schema") != EXPECTED_SCHEMA or manifest.get("status") != "sealed-no-launch":
        raise RuntimeError("sealed manifest identity/status differs")
    rows = manifest.get("files")
    if not isinstance(rows, list) or len(rows) != manifest.get("file_count"):
        raise RuntimeError("sealed manifest file count differs")
    for row in rows:
        relative = row.get("path") if isinstance(row, dict) else None
        if not isinstance(relative, str):
            raise RuntimeError("sealed manifest row lacks a path")
        path = (root / relative).resolve()
        if not path.is_relative_to(root) or not path.is_file():
            raise RuntimeError(f"sealed file absent or outside root: {relative}")
        if path.stat().st_size != row.get("size_bytes") or sha256(path) != row.get("sha256"):
            raise RuntimeError(f"sealed file differs: {relative}")
    operator = json.loads((root / "operator-runtime.json").read_text(encoding="utf-8"))
    if operator.get("schema") != "xar.ck3.g2_m4_council_r694_query_operator_v1":
        raise RuntimeError("operator config schema differs")
    if (operator.get("old_round"), operator.get("new_round")) != ("R693", "R694"):
        raise RuntimeError("round identity differs")
    if (operator.get("readiness_timeout_seconds"), operator.get("query_timeout_seconds"),
            operator.get("overall_window_seconds")) != (300, 60, 480):
        raise RuntimeError("bounded timeout differs")
    if operator.get("pipe") != r"\\.\pipe\xar_ck3_bridge_g2_m4_council_r694_query_76a3da26":
        raise RuntimeError("unique pipe differs")
    python = Path(str(operator["python"])).resolve()
    game = Path(str(operator["game_dir"])).resolve()
    if not python.is_file() or sha256(python) != manifest.get("python_exe_sha256"):
        raise RuntimeError("operator Python differs")
    exe = game / "binaries" / "ck3.exe"
    if not exe.is_file() or sha256(exe) != EXPECTED_EXE:
        raise RuntimeError("exact CK3 EXE differs")
    source = root / "source-save" / "dev3b_r639.ck3"
    target = root / "fresh-profile-state" / "profile" / "save games" / "dev3b_r639.ck3"
    if sha256(source) != EXPECTED_SAVE or sha256(target) != EXPECTED_SAVE:
        raise RuntimeError("source/target save differs")
    descriptor = root / "fresh-profile-state" / "profile" / "mod" / "xar_autoplayer.mod"
    expected_mod = (root / "fresh-profile-state" / "profile" / "mod-content" / "xar-production").as_posix()
    if f'path="{expected_mod}"' not in descriptor.read_text(encoding="utf-8-sig"):
        raise RuntimeError("private profile mod path differs")
    dlc_load = root / "fresh-profile-state" / "profile" / "dlc_load.json"
    if not isinstance(json.loads(dlc_load.read_text(encoding="utf-8-sig")), dict):
        raise RuntimeError("frozen DLC/mod load configuration is unreadable")
    source_src = root / "source-repo" / "ck3_autonomous_player" / "src"
    source_tools = root / "source-repo" / "tools"
    sys.path[:0] = [str(source_src), str(source_tools)]
    import build_release
    import xar_autoplayer.bridge.native_driver as native_driver
    import xar_autoplayer.environment as environment
    import xar_autoplayer.runtime as runtime
    for module in (build_release, native_driver, environment, runtime):
        if not Path(str(module.__file__)).resolve().is_relative_to(root / "source-repo"):
            raise RuntimeError(f"Python import escaped candidate: {module.__name__}")
    dependencies = {name: importlib.metadata.version(name)
                    for name in ("nvidia-cublas", "onnxruntime", "pywin32")}
    return {
        "status": "green-no-launch",
        "source_commit": manifest["source_commit"],
        "game_exe_sha256": EXPECTED_EXE,
        "bridge_dll_sha256": manifest["bridge_dll_sha256"],
        "source_save_sha256": EXPECTED_SAVE,
        "file_count": len(rows),
        "pipe": operator["pipe"],
        "timeouts_seconds": [300, 60, 480],
        "dependencies": dependencies,
        "ck3_launched": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-root", type=Path, default=Path(__file__).parent)
    args = parser.parse_args()
    print(json.dumps(verify(args.artifact_root), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
