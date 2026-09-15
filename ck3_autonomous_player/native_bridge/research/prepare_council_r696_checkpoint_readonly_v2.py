"""Seal a gate-only cold-restore candidate from the R696 material checkpoint."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from prepare_council_r696_controlled_candidate import (
    EXPECTED_EXE_SHA256, EXPECTED_SAVE_SHA256, copy_file, git, sha256, write_json,
)

CHECKPOINT_SHA = "599B9EEE2E2C78A2AA341567FE5C52C36A1292AE1C5F8F00A231E2D7DCA27F64"
R696_REPORT_SHA = "AAFDA2C3346A5A4F4E6966E77BD0C7CD15F4947CDD7C599CD64029D34C9950FB"
R695_DLL_SHA = "77515453226DEE89E24044BB4B173F795258FCAFE44F3C5EA1CE5E75159ECA8D"
R695_INJECTOR_SHA = "09E35E9E86FF714CBA8D716223C951EAC271DBDEFA8C6C638B0765D265A99D51"
NATIVE_SOURCE_COMMIT = "72882e69c11a8b77e4926dfa22ae52998b0e1a61"
ACTION_SOURCE_COMMIT = "245dcf4995f0f18aa5e88468f1303357f6162a0b"


def prepare(r695: Path, r696: Path, game: Path, python: Path, output: Path) -> dict[str, object]:
    r695, r696, game, python, output = (path.resolve() for path in
                                        (r695, r696, game, python, output))
    if output.exists():
        raise RuntimeError(f"sealed output already exists: {output}")
    r695_manifest_path = r695 / "sealed-prep-manifest.json"
    old = json.loads(r695_manifest_path.read_text(encoding="utf-8"))
    if (old.get("schema") != "xar.ck3.g2_m4_council_r695_gate_sealed_prep_v1" or
            old.get("source_commit") != NATIVE_SOURCE_COMMIT or
            old.get("bridge_dll_sha256") != R695_DLL_SHA or
            old.get("injector_sha256") != R695_INJECTOR_SHA or
            old.get("source_save_sha256") != EXPECTED_SAVE_SHA256):
        raise RuntimeError("R695 gate-only frozen source differs")
    r696_report_path = r696 / "live-r696" / "report.json"
    if sha256(r696_report_path) != R696_REPORT_SHA:
        raise RuntimeError("R696 RED report changed")
    report = json.loads(r696_report_path.read_text(encoding="utf-8"))
    checkpoint_result = json.loads((r696 / "live-r696" / "typed-checkpoint-result.json")
                                   .read_text(encoding="utf-8"))
    source_checkpoint = (r696 / "fresh-profile-state" / "profile" / "save games"
                         / "xar_checkpoint.ck3")
    if (report.get("status") != "red" or
            report.get("material_incumbent_observed") != 33433 or
            report.get("pending_ack", {}).get("action_request_id") != "r696-replace-33433" or
            report.get("postflight", {}).get("checkpoint_sha256") != CHECKPOINT_SHA or
            checkpoint_result.get("checkpoint", {}).get("sha256", "").upper() != CHECKPOINT_SHA or
            not source_checkpoint.is_file() or sha256(source_checkpoint) != CHECKPOINT_SHA or
            source_checkpoint.open("rb").read(7) != b"SAV0101"):
        raise RuntimeError("R696 material/typed checkpoint source differs")
    exe = game / "binaries" / "ck3.exe"
    if not exe.is_file() or sha256(exe) != EXPECTED_EXE_SHA256 or not python.is_file():
        raise RuntimeError("exact CK3 EXE or operator Python differs")
    output.mkdir(parents=True)
    prefixes = ("fresh-profile-state/profile/", "source-repo/", "candidate-bin/")
    selected = [row for row in old["files"] if str(row["path"]).startswith(prefixes)]
    for row in selected:
        relative = str(row["path"])
        source = r695 / relative
        if (not source.is_file() or source.stat().st_size != row["size_bytes"] or
                sha256(source) != row["sha256"]):
            raise RuntimeError(f"R695 sealed prelaunch row changed: {relative}")
        copy_file(source, output / relative)
    descriptor = output / "fresh-profile-state" / "profile" / "mod" / "xar_autoplayer.mod"
    old_mod = (r695 / "fresh-profile-state" / "profile" / "mod-content"
               / "xar-production").as_posix()
    new_mod = (output / "fresh-profile-state" / "profile" / "mod-content"
               / "xar-production").as_posix()
    text = descriptor.read_text(encoding="utf-8-sig")
    if f'path="{old_mod}"' not in text:
        raise RuntimeError("R695 outer mod descriptor path differs")
    descriptor.write_text(text.replace(old_mod, new_mod), encoding="utf-8")
    copy_file(source_checkpoint, output / "source-checkpoint" / "xar_checkpoint.ck3")
    copy_file(source_checkpoint, output / "fresh-profile-state" / "profile"
              / "save games" / "xar_checkpoint.ck3")
    runner = Path(__file__).resolve().parent
    copy_file(runner / "run_council_r696_checkpoint_readonly_v2.py",
              output / "run_council_r696_checkpoint_readonly_v2.py")
    copy_file(runner / "council_r696_checkpoint_readonly_v2.template.json",
              output / "council_r696_checkpoint_readonly_v2.template.json")
    operator = {
        "schema": "xar.ck3.g2_m4_council_r696_checkpoint_readonly_operator_v2",
        "python": str(python), "game_dir": str(game),
        "pipe": r"\\.\pipe\xar_ck3_bridge_g2_m4_council_r696_restore_72882e69",
        "last_completed_council_round": "R696",
        "round_allocated": False,
        "readiness_timeout_seconds": 300, "query_timeout_seconds": 60,
        "overall_window_seconds": 480,
    }
    write_json(output / "operator-runtime.json", operator)
    files = [{"path": path.relative_to(output).as_posix(),
              "size_bytes": path.stat().st_size, "sha256": sha256(path)}
             for path in sorted(output.rglob("*")) if path.is_file() and
             path.name not in {"sealed-prep-manifest.json", "sealed-prep-manifest.sha256"}]
    manifest: dict[str, object] = {
        "schema": "xar.ck3.g2_m4_council_r696_checkpoint_readonly_sealed_v2",
        "status": "sealed-no-launch",
        "runner_commit": git(runner.parents[2], "rev-parse", "HEAD"),
        "native_source_commit": NATIVE_SOURCE_COMMIT,
        "r696_action_source_commit": ACTION_SOURCE_COMMIT,
        "game_version": "1.19.0.6", "game_exe_sha256": EXPECTED_EXE_SHA256,
        "python_exe_sha256": sha256(python),
        "r695_gate_prep_sha256": sha256(r695_manifest_path),
        "r696_red_report_sha256": R696_REPORT_SHA,
        "r696_pending_action_request_id": "r696-replace-33433",
        "checkpoint_sha256": CHECKPOINT_SHA,
        "checkpoint_size_bytes": source_checkpoint.stat().st_size,
        "bridge_dll_sha256": R695_DLL_SHA,
        "injector_sha256": R695_INJECTOR_SHA,
        "cmake_options": {
            "XAR_CK3_ENABLE_G2_COUNCIL_APPLICATION_MAIN_PRIVATE_ROUTE_V1": "ON",
            "XAR_CK3_ENABLE_G2_COUNCIL_FINAL_GATE_PRIVATE_QUERY_V1": "ON",
            "XAR_CK3_ENABLE_G2_COUNCIL_ASSIGN_PRIVATE_ACTION_GATE_V1": "OFF",
        },
        "public_council_advertised": False,
        "private_assign_admitted": False,
        "read_only": True,
        "formal_goal_cold_restore": "unverified_private_action_not_in_driver_state",
        "typed_receipt_across_process": "unavailable_pending_ack_was_process_local",
        "expected_owner_character_id": 29829,
        "expected_incumbent_character_id": 33433,
        "expected_date_raw": 53178264,
        "file_count": len(files), "files": files,
    }
    path = output / "sealed-prep-manifest.json"
    write_json(path, manifest)
    (output / "sealed-prep-manifest.sha256").write_text(
        sha256(path) + "  sealed-prep-manifest.json\n", encoding="ascii")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("r695_candidate", "r696_candidate", "game_dir", "python", "output"):
        parser.add_argument("--" + name.replace("_", "-"), type=Path, required=True)
    args = parser.parse_args()
    result = prepare(args.r695_candidate, args.r696_candidate, args.game_dir,
                     args.python, args.output)
    print(json.dumps({"status": result["status"], "file_count": result["file_count"],
                      "output": str(args.output.resolve())}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
