"""Bind the four actor trigger closures to the existing zero-mod run's files.

Pure filesystem read. No Game, Driver, SDK, registry or desktop calls. The
result is a future-cold source admission input; actual successor same-frame
shadow and rechecking these inputs before launch remain necessary.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from audit_declaration_actor_candidates_12004 import audit, tokens

EXPECTED_EXE_SHA = "98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518"
EXPECTED_NATIVE25_SHA = "a1448baa860a88826cbb9ae50ab67c93506560f2772c0515e4ef51e934002f40"


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def pin(path: Path) -> dict:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return {"path": str(path.resolve()), "bytes": path.stat().st_size, "sha256": h.hexdigest()}


def definitions_of_interest(tree: list[str], names: set[str]) -> list[str]:
    depth, found = 0, []
    for index, token in enumerate(tree):
        if depth == 0 and token in names and tree[index + 1:index + 3] == ["=", "{"]:
            found.append(token)
        depth += (token == "{") - (token == "}")
        if depth < 0:
            raise ValueError("unbalanced source brace")
    if depth:
        raise ValueError("unclosed source brace")
    return found


def main() -> None:
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--game-root", type=Path, required=True)
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--actor-source-audit", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("audit output is create-only")
    machine = subprocess.check_output([sys.executable, str(ROOT / "tools/ck3_live_run_id.py"), "machine"], text=True).strip()
    absence_path = args.runtime_root / "ROOT-CLEAN-CAMPAIGN-MOD-ABSENCE-ACTUAL.json"
    launch_path = args.runtime_root / "ROOT-ACTUAL-GAME-LAUNCH.json"
    absence, launch = (json.loads(path.read_text(encoding="utf-8-sig")) for path in (absence_path, launch_path))
    if absence.get("machine_id") != machine or launch.get("machine_id") != machine:
        raise ValueError("zero-mod/run evidence belongs to another or unknown machine")
    if not (absence.get("enabled_mods_known") and absence.get("loaded_mods_known") and
            absence.get("startup_log_reviewed") and absence.get("enabled_mods") == [] and
            absence.get("loaded_mods") == [] and launch.get("enabled_mods") == []):
        raise ValueError("zero-mod loaded-source admission is unavailable")
    if absence["game_pid"] != launch["pid"] or absence["game_creation_filetime"] != launch["creation_filetime"]:
        raise ValueError("zero-mod/run tuples differ")
    if launch["dll_sha256"] != EXPECTED_NATIVE25_SHA:
        raise ValueError("run is not the qualified Native25 baseline")
    profile_settings = Path(absence["profile_enabled_mods"]["path"])
    profile_pin = pin(profile_settings)
    if profile_pin["sha256"] != absence["profile_enabled_mods"]["sha256"]:
        raise ValueError("current small profile mod settings changed")
    settings = json.loads(profile_settings.read_text(encoding="utf-8-sig"))
    if settings.get("enabled_mods") != []:
        raise ValueError("current profile enables mods")
    executable = pin(args.game_root / "binaries/ck3.exe")
    if executable["sha256"] != EXPECTED_EXE_SHA:
        raise ValueError("installed exact .4 executable changed")
    common = args.game_root / "game/common"
    old_audit = json.loads(args.actor_source_audit.read_text(encoding="utf-8-sig"))
    fresh = audit(common)
    if fresh["rules_sha256"] != old_audit["rules_sha256"] or fresh["rules"] != old_audit["rules"]:
        raise ValueError("source-reviewed actor closure changed")
    cb_names = {row["key"] for row in fresh["rules"]}
    trigger_names = {row["name"] for closure in fresh["closure"].values() for row in closure
                     if "/allowed_for_character" not in row["name"]}
    scanned, definitions = [], {name: [] for name in cb_names | trigger_names}
    for folder, wanted in (("casus_belli_types", cb_names), ("scripted_triggers", trigger_names)):
        for path in sorted((common / folder).rglob("*.txt")):
            scanned.append(pin(path))
            for name in definitions_of_interest(tokens(path.read_text(encoding="utf-8-sig")), wanted):
                definitions[name].append(str(path.relative_to(common)))
    expected = {}
    for key, closure in fresh["closure"].items():
        for row in closure:
            name = key if row["name"].endswith("/allowed_for_character") else row["name"]
            expected.setdefault(name, row["relative_path"].replace("/", "\\"))
    for name, sources in definitions.items():
        if sources != [expected[name]]:
            raise ValueError(f"actor definition duplicate/override/missing: {name}: {sources}")
    dlc = args.game_root / "game/dlc"
    dlc_files, archives, override_files, descriptors = [], [], [], []
    for directory, names, files in os.walk(dlc):
        names.sort()
        for filename in sorted(files):
            path = Path(directory) / filename
            relative = path.relative_to(dlc).as_posix()
            dlc_files.append({"relative": relative, "bytes": path.stat().st_size})
            lower = relative.lower()
            if lower.endswith((".zip", ".7z", ".rar", ".pak")):
                archives.append(relative)
            if "/common/casus_belli_types/" in "/" + lower or "/common/scripted_triggers/" in "/" + lower:
                override_files.append(relative)
            if lower.endswith(".dlc"):
                descriptors.append(pin(path))
                body = path.read_text(encoding="utf-8-sig")
                if any(line.lstrip().startswith(("archive", "replace_path")) for line in body.splitlines()):
                    archives.append(relative + " (descriptor archive/replace_path)")
            if len(dlc_files) > 100000:
                raise ValueError("unexpected DLC metadata enumeration expansion")
    if archives or override_files:
        raise ValueError("DLC source resolution requires explicit archive/override review: " + repr(archives + override_files))
    result = {
        "schema": "xar.native26-actor-zero-mod-source-admission/v1", "machine_id": machine,
        "observed_at_utc": datetime.now(timezone.utc).isoformat(), "producer": pin(Path(__file__)),
        "status": "CURRENT_ZERO_MOD_INSTALLATION_CLOSURE_VERIFIED_FUTURE_COLD_RECHECK_REQUIRED",
        "current_run": {"game_pid": launch["pid"], "creation_filetime": launch["creation_filetime"],
                        "absence": pin(absence_path), "launch": pin(launch_path)},
        "executable": executable, "profile_settings": profile_pin,
        "enabled_mods": [], "loaded_mods": [], "settings": settings,
        "actor_source_audit": pin(args.actor_source_audit), "actor_rules_sha256": fresh["rules_sha256"],
        "rules": fresh["rules"], "effective_definition_sources": definitions,
        "scanned_common_source_files": scanned,
        "dlc_root": str(dlc.resolve()), "dlc_metadata_file_count": len(dlc_files),
        "dlc_metadata_inventory_sha256": sha(json.dumps(dlc_files, sort_keys=True, separators=(",", ":")).encode()),
        "dlc_descriptors": descriptors, "dlc_archives": archives, "dlc_cb_or_trigger_overrides": override_files,
        "Game_or_Driver_or_native_or_desktop_calls": 0,
        "current_Native25_changed": False, "runtime_actor_gate_enabled": False,
        "successor_adoption": "Before future cold launch re-read profile/source identity and resolve overrides again; bind the proof SHA in ACTOR_SOURCE_MANIFEST_SHA256 only for that admitted tuple, then actual same-frame shadow. No runtime ABI/business credit from this file audit.",
        "missing_machine06_original": "Retained as machine_id unknown; not used as this admission's identity source.",
    }
    raw = (json.dumps(result, ensure_ascii=True, indent=2) + "\n").encode()
    if len(raw) > 256 * 1024:
        raise ValueError("small loaded-source admission exceeds256KiB")
    args.output.write_bytes(raw)
    print(json.dumps({"output": str(args.output), "bytes": len(raw), "sha256": sha(raw),
                      "common_sources": len(scanned), "dlc_files": len(dlc_files), "definitions": len(definitions)}))


if __name__ == "__main__":
    main()
