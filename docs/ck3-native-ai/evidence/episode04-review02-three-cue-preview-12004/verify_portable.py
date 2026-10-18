"""Read-only small-copy and selection smoke; not a render, native audit, or QA."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import zipfile

def need(condition, message):
    if not condition:
        raise ValueError(message)

def digest(path):
    body = path.read_bytes()
    return len(body), hashlib.sha256(body).hexdigest()

def within(root, rel):
    path = (root / rel).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError(f"escaped package path: {rel}")
    return path

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[4])
    parser.add_argument("--package-root", type=Path, help="external candidate root, only before canonical copy")
    parser.add_argument("--require-integrated-composer", action="store_true")
    args = parser.parse_args()
    repo = args.repo_root.resolve()
    package = (args.package_root or repo).resolve()
    evidence = within(package, "docs/ck3-native-ai/evidence/episode04-review02-three-cue-preview-12004")
    index = json.loads((evidence / "source-index.json").read_text(encoding="utf-8"))
    selection = json.loads(within(package, "promo/ck3_native_war_ai/episode-04-march-logistics/review02/three-cue-preview-a01/preview-selection.json").read_text(encoding="utf-8"))
    need(index["schema"] == "xar.e04.review02-three-cue-small-source-index.v1", "wrong source-index schema")
    need(selection["schema"] == "xar.e04.review02-three-cue-portable-selection.v1", "wrong selection schema")
    need(index["machine_id"] == "desktop-3fevhd2-1c74096080", "wrong source machine")
    need(index["source_commit"] == selection["source_commit_of_actual_preview"], "source commit mismatch")
    checked = 0
    for name, item in index["original_and_copy_pins"].items():
        copy = item["portable_copy"]
        p = within(package, copy["repo_relative"])
        size, sha = digest(p)
        need((size, sha) == (copy["bytes"], copy["sha256"]), f"portable copy mismatch: {name}")
        need((size, sha) == (item["machine_original"]["bytes"], item["machine_original"]["sha256"]), f"original pin mismatch: {name}")
        checked += 1
    need(checked == 12, "small original copy count mismatch")
    cues = selection["visual_sources"]
    ids = [x["cue_id"] for x in cues]
    need(ids == selection["render"]["preview_cue_ids"] == ["C01-01", "C02-09", "C03-08"], "preview cue ids/order mismatch")
    need(sum(x["cue_frames"] for x in cues) == 2512 == index["frame_count"], "preview frame count mismatch")
    need(all(x["source_frame_interval"][1] - x["source_frame_interval"][0] + x["explicit_tail_hold_frames"] == x["cue_frames"] for x in cues), "source/hold frame math mismatch")
    need([x["explicit_tail_hold_frames"] for x in cues] == [27, 0, 0], "tail holds mismatch")
    need(index["full_human_1x"] is False and index["signoff"] is False and index["formal_dynamic_credit"] == 0, "review status overstated")
    need(index["deliverable"]["sha256"] == "5d5f04f89afe1619d90fbcc8ad0cc950fde44aee8a4d03129816f2dca7c4d811", "deliverable pin mismatch")
    config = selection["base_project_config"]
    archive = within(repo, "promo/ck3_native_war_ai/episode-04-march-logistics/review02/production-inputs-a03/review02-bilingual-inputs-a03.zip")
    with zipfile.ZipFile(archive) as z:
        body = z.read(config["archive_member"])
    need(len(body) == config["bytes"] and hashlib.sha256(body).hexdigest() == config["sha256"], "base ProjectConfig member mismatch")
    patch = within(package, selection["composer"]["required_patch_repo_relative"])
    patch_text = patch.read_text(encoding="utf-8")
    need("tail_hold_frames" in patch_text and "tpad=stop_mode=clone" in patch_text and "filter_complex_threads" in patch_text and "raw_render_windows" in patch_text, "multiwindow composer patch markers missing")
    need(digest(patch) == (4841, "f7de2531e4818825db7a9fc03ef9ed2fdad9232db3f827a2b777de09e77754c3"), "postbuild composer patch changed")
    original_patch = within(package, selection["composer"]["actual_preview_patch_repo_relative"])
    need(digest(original_patch) == (4641, "359035bcad1269cd782be639bc47559552cdcf0307dd26ad093b1487fa9c556b"), "actual preview patch changed")
    need(selection["composer"]["postbuild_candidate_only"] is True, "postbuild candidate boundary absent")
    regression = json.loads((evidence / "MULTIWINDOW-HOLD0-CHECK.actual.json").read_text(encoding="utf-8"))
    need(regression["status"] == "PASS_FOCUSED_NO_PROCESS_PLANNER_CHECK" and regression["same_raw_different_length_hold0_preserved"] is True, "focused multiwindow branch not passed")
    need(regression["candidate_composer"]["sha256"] == "65caaef16a78e41959f7e45c55251b1784b4dae08af96052d3a0306c965a6735", "candidate composer pin changed")
    need(regression["native_CLI_run"] is False and regression["FFmpeg_executed"] is False, "focused check exceeded offline scope")
    if args.require_integrated_composer:
        composer = within(repo, selection["composer"]["repo_relative"])
        code = composer.read_text(encoding="utf-8")
        need("tail_hold_frames" in code and "tpad=stop_mode=clone" in code and "filter_complex_threads" in code and "raw_render_windows" in code, "integrated multiwindow composer markers missing")
    machine_cmd = [sys.executable, str(repo / "tools/ck3_live_run_id.py"), "machine"]
    machine = subprocess.run(machine_cmd, capture_output=True, text=True, check=True).stdout.strip()
    need(bool(machine), "machine ID readback empty")
    return {"status": "PASS_PORTABLE_SMALL_COPY_AND_SELECTION_ONLY",
            "verified_at_utc": datetime.now(timezone.utc).isoformat(),
            "verification_machine_id": machine, "source_machine_id": index["machine_id"],
            "package_root": str(package), "repo_root": str(repo),
            "small_original_copies_checked": checked,
            "project_config_archive_member_checked": True,
            "cue_frame_math_checked": True,
            "composer_patch_text_checked": True,
            "actual_preview_patch_separate_from_postbuild_candidate": True,
            "focused_hold0_multiwindow_check_read": True,
            "integrated_composer_static_check": args.require_integrated_composer,
            "media_body_read": False, "native_cli_run": False,
            "native_build_or_validate": False, "media_QA_or_human_review": False}

if __name__ == "__main__":
    print(json.dumps(main(), ensure_ascii=False, separators=(",", ":")))
