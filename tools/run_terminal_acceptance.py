#!/usr/bin/env python3
"""Run non-debug observer/Ironman terminal acceptance in a disposable CK3 userdir."""

import argparse
import hashlib
import json
import os
import shutil
import tempfile
import time
import uuid
import winreg
import xml.etree.ElementTree as ET
from pathlib import Path

import run_acceptance as acceptance


REAL_PROFILE = acceptance.ORIGINAL_USER_DIR
STEAM_APP_ID = "1158310"
POSTFLIGHT_STABILITY_SECONDS = 5
HARNESS_FILES = (
    acceptance.ROOT / "tools" / "run_acceptance.py",
    acceptance.ROOT / "tools" / "run_terminal_acceptance.py",
    acceptance.ROOT / "tools" / "validate_static.py",
)


def file_digest(path):
    return {
        "size": path.stat().st_size,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }


def real_profile_snapshot():
    paths = [
        REAL_PROFILE / "tutorial.txt",
        REAL_PROFILE / "player" / "game_rules" / "presets.txt",
        REAL_PROFILE / "dlc_load.json",
        REAL_PROFILE / "pdx_settings.txt",
    ]
    save_dir = REAL_PROFILE / "save games"
    if save_dir.is_dir():
        paths.extend(sorted(path for path in save_dir.rglob("*.ck3") if path.is_file()))
    return {
        str(path.relative_to(REAL_PROFILE)).replace("\\", "/"): file_digest(path)
        for path in paths if path.is_file()
    }


def snapshot_digest(snapshot):
    payload = json.dumps(
        snapshot, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def harness_digest():
    digest = hashlib.sha256()
    for path in HARNESS_FILES:
        relative = path.relative_to(acceptance.ROOT).as_posix().encode("utf-8")
        digest.update(len(relative).to_bytes(4, "big"))
        digest.update(relative)
        digest.update(path.read_bytes())
    return digest.hexdigest()


def steam_userdata_root():
    override = os.environ.get("XAR_STEAM_USERDATA_DIR")
    if override:
        root = Path(os.path.expandvars(override)).expanduser().resolve()
    else:
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam") as key:
                steam_path, _ = winreg.QueryValueEx(key, "SteamPath")
        except OSError as exc:
            raise acceptance.RunnerError(
                "Steam userdata root is unavailable; set XAR_STEAM_USERDATA_DIR") from exc
        root = (Path(steam_path) / "userdata").resolve()
    if not root.is_dir():
        raise acceptance.RunnerError(f"Steam userdata root does not exist: {root}")
    return root


def steam_cloud_app_dirs(root):
    app_dirs = sorted(
        path for path in root.glob(f"*/{STEAM_APP_ID}") if path.is_dir())
    if not app_dirs:
        raise acceptance.RunnerError(
            f"no local Steam userdata found for CK3 app {STEAM_APP_ID} under {root}")
    return app_dirs


def steam_cloud_snapshot(root):
    app_dirs = steam_cloud_app_dirs(root)
    return {
        str(path.relative_to(root)).replace("\\", "/"): file_digest(path)
        for app_dir in app_dirs
        for path in sorted(item for item in app_dir.rglob("*") if item.is_file())
    }


def verify_storage_stability(profile_before, steam_before, steam_root):
    """Require both protected stores to equal baseline for a bounded quiet period."""
    deadline = time.monotonic() + POSTFLIGHT_STABILITY_SECONDS
    profile_after = real_profile_snapshot()
    steam_after = steam_cloud_snapshot(steam_root)
    while True:
        if profile_after != profile_before or steam_after != steam_before:
            return profile_after, steam_after, False
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return profile_after, steam_after, True
        time.sleep(min(1, remaining))
        profile_after = real_profile_snapshot()
        steam_after = steam_cloud_snapshot(steam_root)


def render_presets(ironman):
    defaults = [setting for _, setting in acceptance.declared_vanilla_rule_defaults()]
    settings = defaults + ["xar_selftest", "xar_inherit_100", "xar_score_growth"]
    if len(settings) != len(set(settings)):
        raise acceptance.RunnerError("isolated game-rule profile contains duplicate settings")
    return (
        'game_rules_preset={\n'
        '\tname="LastAppliedRules"\n'
        f'\tsetting={{ {" ".join(settings)} }}\n'
        f'\tironman={"yes" if ironman else "no"}\n'
        '}\n'
    )


def render_settings():
    return '''"game"={
\t"promt_for_tutorial"={ version=0 enabled=no }
\t"cloud_save"={ version=0 enabled=no }
}
"Graphics"={
\t"display_mode"={ version=0 value="fullscreen" }
\t"display_index"={ version=0 value="0" }
\t"fullscreen_resolution"={ version=0 value="2560x1440" }
}
"System"={
\t"language"={ version=0 value="l_simp_chinese" }
}
'''


def bootstrap_userdir(userdir, ironman):
    target = userdir / "mod" / acceptance.build_release.WORKSHOP_ITEM_ID
    for path in (
            target, userdir / "logs", userdir / "save games",
            userdir / "player" / "game_rules"):
        path.mkdir(parents=True, exist_ok=True)
    descriptor = acceptance.MOD_ROOT / "descriptor.mod"
    shutil.copy2(descriptor, target / "descriptor.mod")
    outer = descriptor.read_text(encoding="utf-8-sig")
    outer += f'path="{target.as_posix()}"\n'
    (userdir / "mod" / "ugc_3784706360.mod").write_text(
        outer, encoding="utf-8-sig", newline="\n")
    (userdir / "tutorial.txt").write_text(
        'last_lesson_chain="reactive_advice"\ncompleted_lessons={\n}\n',
        encoding="utf-8", newline="\n")
    (userdir / "player" / "game_rules" / "presets.txt").write_text(
        render_presets(ironman), encoding="utf-8", newline="\n")
    (userdir / "dlc_load.json").write_text(
        json.dumps({
            "enabled_mods": ["mod/ugc_3784706360.mod"],
            "disabled_dlcs": [],
        }, separators=(",", ":")),
        encoding="utf-8", newline="\n")
    (userdir / "pdx_settings.txt").write_text(
        render_settings(), encoding="utf-8", newline="\n")
    return target


def mark_junit_failed(path, reason):
    tree = ET.parse(path)
    suite = tree.getroot()
    suite.set("failures", "1")
    case = suite.find("testcase")
    if case is None:
        raise acceptance.RunnerError(f"JUnit report lacks testcase: {path}")
    for failure in case.findall("failure"):
        case.remove(failure)
    ET.SubElement(case, "failure", {"message": reason})
    ET.indent(tree, space="  ")
    tree.write(path, encoding="utf-8", xml_declaration=True)


def update_report(artifacts, isolation, postflight_error=None):
    report_path = artifacts / "report.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    report.setdefault("scenario_evidence", {}).update(isolation)
    if postflight_error:
        previous = report.get("error_reason")
        report["result"] = "RED"
        report["error_reason"] = (
            f"{previous}; {postflight_error}" if previous else postflight_error)
        mark_junit_failed(artifacts / "report.xml", report["error_reason"])
    evidence_path = artifacts / "isolation_evidence.json"
    evidence_path.write_text(
        json.dumps(isolation, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report["artifacts"]["files"] = sorted(set(
        report["artifacts"]["files"] + ["isolation_evidence.json"]))
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main(mode, artifacts_dir=None, keep_userdir=False):
    if acceptance.ck3_is_running():
        raise acceptance.RunnerError(
            "isolated terminal acceptance refuses to run while ck3.exe is active")
    if artifacts_dir:
        artifacts = Path(artifacts_dir).expanduser().resolve()
    else:
        artifacts = Path(tempfile.gettempdir()) / (
            f"xar_terminal_{mode}_{uuid.uuid4().hex[:8]}")
    if artifacts.exists():
        raise acceptance.RunnerError(f"artifact directory already exists: {artifacts}")
    if not artifacts.parent.is_dir():
        raise acceptance.RunnerError(f"artifact parent does not exist: {artifacts.parent}")
    userdir = artifacts.with_name(artifacts.name + "_userdir")
    if userdir.exists():
        raise acceptance.RunnerError(f"isolated userdir already exists: {userdir}")

    steam_root = steam_userdata_root()
    steam_account_count = len(steam_cloud_app_dirs(steam_root))
    before = real_profile_snapshot()
    steam_before = steam_cloud_snapshot(steam_root)
    before_digest = snapshot_digest(before)
    steam_before_digest = snapshot_digest(steam_before)
    terminal_harness_sha256 = harness_digest()
    target = userdir / "mod" / acceptance.build_release.WORKSHOP_ITEM_ID
    acceptance.configure_isolated_userdir(userdir, target)
    userdir.mkdir()
    bootstrap_userdir(userdir, mode == "ironman")
    scenario = f"terminal-{mode}"
    exit_code = 1
    try:
        exit_code = acceptance.main(
            scenario=scenario, import_record=0, artifacts_dir=str(artifacts))
        postflight_errors = []
        try:
            after, steam_after, stable = verify_storage_stability(
                before, steam_before, steam_root)
            profile_untouched = before == after
            steam_untouched = steam_before == steam_after
        except Exception as exc:
            after = None
            steam_after = None
            stable = False
            profile_untouched = False
            steam_untouched = False
            postflight_errors.append(f"protected-storage postflight failed: {exc}")
        isolated_logs_created = any((userdir / "logs").glob("*.log"))
        if not profile_untouched and after is not None:
            postflight_errors.append(
                "protected real CK3 profile/save files changed during isolated acceptance")
        if not steam_untouched and steam_after is not None:
            postflight_errors.append(
                "local Steam Cloud CK3 backing store changed during isolated acceptance")
        removal_error = None
        if exit_code == 0 and not postflight_errors and not keep_userdir:
            try:
                shutil.rmtree(userdir)
            except OSError as exc:
                removal_error = str(exc)
                postflight_errors.append(f"isolated userdir removal failed: {exc}")
        userdir_removed = not userdir.exists()
        if (exit_code == 0 and not keep_userdir and not userdir_removed
                and removal_error is None):
            postflight_errors.append(f"isolated userdir still exists: {userdir}")
        isolation = {
            "real_profile_untouched": profile_untouched,
            "real_profile_file_count": len(before),
            "real_profile_before_sha256": before_digest,
            "real_profile_after_sha256": (
                snapshot_digest(after) if after is not None else None),
            "real_profile_scope": (
                "tutorial, game-rule presets, dlc_load, pdx_settings, all *.ck3 saves"),
            "steam_cloud_untouched": steam_untouched,
            "steam_cloud_file_count": len(steam_before),
            "steam_cloud_before_sha256": steam_before_digest,
            "steam_cloud_after_sha256": (
                snapshot_digest(steam_after) if steam_after is not None else None),
            "steam_cloud_app_id": STEAM_APP_ID,
            "steam_cloud_account_count": steam_account_count,
            "steam_cloud_scope": (
                "local Steam userdata backing store; remote service not queried"),
            "postflight_stable": stable,
            "postflight_stability_seconds": POSTFLIGHT_STABILITY_SECONDS,
            "terminal_harness_sha256": terminal_harness_sha256,
            "isolated_userdir": str(userdir),
            "isolated_logs_created": isolated_logs_created,
            "cloud_save_setting": False,
            "userdir_launch_argument": True,
            "userdir_removed_after_run": userdir_removed,
            "userdir_retained_by_request": keep_userdir,
        }
        if removal_error:
            isolation["userdir_removal_error"] = removal_error
        if postflight_errors:
            isolation["postflight_errors"] = postflight_errors
        postflight_error = "; ".join(postflight_errors) or None
        update_report(artifacts, isolation, postflight_error)
        if postflight_error:
            exit_code = 1
            acceptance.log(f"FATAL postflight: {postflight_error}")
            print("RESULT: RED")
    finally:
        if userdir.exists():
            acceptance.log(f"isolated userdir retained at {userdir}")
    return exit_code


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("observer", "ironman"), required=True)
    parser.add_argument("--artifacts-dir", help="create this exact artifact directory")
    parser.add_argument("--keep-userdir", action="store_true")
    args = parser.parse_args()
    raise SystemExit(main(args.mode, args.artifacts_dir, args.keep_userdir))
