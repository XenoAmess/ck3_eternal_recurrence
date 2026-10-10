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
FILE_DIGEST_LOCK_RETRY_SECONDS = 30
FILE_DIGEST_LOCK_RETRY_INTERVAL_SECONDS = 0.25
HARNESS_FILES = (
    acceptance.ROOT / "tools" / "run_acceptance.py",
    acceptance.ROOT / "tools" / "run_terminal_acceptance.py",
    acceptance.ROOT / "tools" / "validate_static.py",
)


def file_digest(path, retry_seconds=FILE_DIGEST_LOCK_RETRY_SECONDS):
    """Hash a protected file after bounded retries for transient Windows locks.

    Steam can briefly open ``remotecache.vdf`` without sharing read access while
    a game process is shutting down.  A missing or persistently unreadable file
    must still fail the protected-storage gate; only ``PermissionError`` is
    retried, and the digest is always computed from bytes that were actually
    read.
    """
    deadline = time.monotonic() + retry_seconds
    while True:
        try:
            payload = path.read_bytes()
            return {
                "size": len(payload),
                "sha256": hashlib.sha256(payload).hexdigest(),
            }
        except PermissionError:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise
            time.sleep(min(FILE_DIGEST_LOCK_RETRY_INTERVAL_SECONDS, remaining))


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
\t"prompt_for_china_tutorial"={ version=0 enabled=no }
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
    print('Legacy direct CK3 acceptance launch is disabled. Use tools/ck3_mod_acceptance.py plan / prepare / allocate / preflight / run / verify with the selected common runtime manifest.', file=sys.stderr)
    return 2


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("observer", "ironman"), required=True)
    parser.add_argument("--artifacts-dir", help="create this exact artifact directory")
    parser.add_argument("--keep-userdir", action="store_true")
    args = parser.parse_args()
    raise SystemExit(main(args.mode, args.artifacts_dir, args.keep_userdir))
