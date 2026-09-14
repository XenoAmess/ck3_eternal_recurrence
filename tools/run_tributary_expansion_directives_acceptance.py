#!/usr/bin/env python3
"""Run one isolated CK3 live cell for Tributary Expansion Directives."""

from __future__ import annotations

import argparse
import os
import re
import shutil
import sys
import time
from pathlib import Path, PurePosixPath

DEFAULT_CK3_EXE = Path(
    r"C:\SteamLibrary\steamapps\common\Crusader Kings III\binaries\ck3.exe"
)
if "XAR_CK3_EXE" not in os.environ and DEFAULT_CK3_EXE.is_file():
    os.environ["XAR_CK3_EXE"] = str(DEFAULT_CK3_EXE)

import build_tributary_expansion_directives_release as release
import run_ox_here_acceptance as harness
import run_acceptance as acceptance
import run_vivhite_acceptance as isolated
import validate_tributary_expansion_directives_static as static_gate


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / release.PRODUCT_ID
FIXTURE_SOURCE = ROOT / "tools/fixtures/tributary_expansion_directives_acceptance"
PRODUCT_OUTER = "ted_acceptance.mod"
FIXTURE_OUTER = "tea_acceptance_fixture.mod"
REQUIRED_MARKERS = (
    "TEA: TEST BEGIN tributary_expansion_directives",
    "TEA: TEST PASS exact_build_song_emperor",
    "TEA: TEST PASS switched_to_supported_player",
    "TEA: TEST PASS tributary_context_constructed",
    "TEA: TEST PASS decline_response_preserved_send_cost_and_gold",
    "TEA: TEST PASS decline_effect_created_no_war",
    "TEA: TEST PASS subsidized_accept_spent_prestige_and_transferred_gold",
    "TEA: TEST PASS accept_effect_started_war",
    "TEA: TEST PASS switched_to_tributary_attacker",
    "TEA: TEST PASS war_attacker_defender_binding",
    "TEA: TEST GAP complete_war_outcomes_save_reload_and_tribute_not_executed",
    "TEA: TEST DONE tributary_expansion_directives",
)
REMOTE_FILE_ID_LINE = re.compile(
    r'(?m)^[ \t]*remote_file_id[ \t]*=[ \t]*"([0-9]+)"[ \t]*(?:\r?\n|$)'
)


class TeaMarkerStream:
    def __init__(self, path: Path):
        self.path = path
        self.offset = 0
        self.pending = b""
        self.lines: list[str] = []

    def pump(self, final: bool = False) -> None:
        try:
            with self.path.open("rb") as source:
                source.seek(0, 2)
                size = source.tell()
                if size < self.offset:
                    self.offset = 0
                    self.pending = b""
                source.seek(self.offset)
                data = source.read()
                self.offset = source.tell()
        except OSError as error:
            if final:
                raise acceptance.RunnerError(f"cannot finalize fixture log: {error}") from error
            data = b""
        payload = self.pending + data
        if final:
            complete, self.pending = payload, b""
        else:
            boundary = max(payload.rfind(b"\n"), payload.rfind(b"\r"))
            if boundary < 0:
                self.pending = payload
                return
            complete, self.pending = payload[: boundary + 1], payload[boundary + 1 :]
        for line in complete.decode("utf-8", errors="ignore").splitlines():
            if "TEA:" in line:
                stripped = line.strip()
                self.lines.append(stripped)
                log(stripped)
        failures = [line for line in self.lines if "TEA: TEST FAIL" in line]
        if failures:
            raise acceptance.RunnerError(f"fixture failure marker: {failures[-1]}")

    def wait(self, marker: str, timeout_s: float = 15) -> None:
        deadline = time.time() + timeout_s
        while time.time() < deadline:
            self.pump()
            if any(marker in line for line in self.lines):
                return
            time.sleep(acceptance.POLL_INTERVAL_S)
        raise acceptance.RunnerError(f"fixture marker timeout: {marker}")

    def validate(self, final: bool = False) -> None:
        self.pump(final=final)
        for marker in REQUIRED_MARKERS:
            count = sum(marker in line for line in self.lines)
            if count != 1:
                raise acceptance.RunnerError(
                    f"fixture marker count for {marker!r} is {count}, expected 1"
                )


def log(message: str) -> None:
    acceptance.log(f"tributary_expansion_directives: {message}")


def fixture_source_errors() -> list[str]:
    if not FIXTURE_SOURCE.is_dir():
        return [f"fixture source missing: {FIXTURE_SOURCE}"]
    errors: list[str] = []
    for path in sorted(item for item in FIXTURE_SOURCE.rglob("*") if item.is_file()):
        relative = path.relative_to(FIXTURE_SOURCE).as_posix()
        data = path.read_bytes()
        if path.suffix.lower() in {".txt", ".gui", ".yml"} and not data.startswith(
            b"\xef\xbb\xbf"
        ):
            errors.append(f"fixture text lacks UTF-8 BOM: {relative}")
        text = data.decode("utf-8-sig", errors="replace")
        if "remote_file_id" in text:
            errors.append(f"fixture contains Workshop identity: {relative}")
        if path.suffix.lower() in {".txt", ".gui"} and not static_gate.balanced_braces(text):
            errors.append(f"fixture has unbalanced braces: {relative}")
    effects = FIXTURE_SOURCE / "common/scripted_effects/tea_effects.txt"
    if effects.is_file():
        text = effects.read_text(encoding="utf-8-sig")
        for token in (
            "start_tributary_interaction_effect",
            "add_prestige = -150",
            "ted_decline_expansion_directive_effect = yes",
            "ted_accept_expansion_directive_effect = { SUBSIDIZED = yes }",
            "using_cb = ted_directed_county_expansion_cb",
            "add_character_flag = tea_verify_attacker_completed",
        ):
            if token not in text:
                errors.append(f"fixture contract missing {token}")
    return errors


def product_source_errors() -> list[str]:
    source = Path(harness.SOURCE)
    if not source.is_dir():
        return [f"product source missing: {source}"]
    errors: list[str] = []
    actual = {
        path.relative_to(source).as_posix()
        for path in source.rglob("*")
        if path.is_file()
    }
    missing = sorted(release.RUNTIME_FILES - actual)
    if missing:
        errors.append("product runtime files missing: " + ", ".join(missing))
    if source != DEFAULT_SOURCE.resolve():
        extras = sorted(actual - release.RUNTIME_FILES)
        if extras:
            errors.append("external runtime contains extra files: " + ", ".join(extras))
    for relative in sorted(release.RUNTIME_FILES):
        path = source / PurePosixPath(relative)
        if not path.is_file():
            continue
        data = path.read_bytes()
        if path.suffix.lower() in {".txt", ".gui", ".yml"} and not data.startswith(
            b"\xef\xbb\xbf"
        ):
            errors.append(f"product runtime text lacks UTF-8 BOM: {relative}")
    descriptor = source / "descriptor.mod"
    if descriptor.is_file():
        value = descriptor.read_text(encoding="utf-8-sig")
        ids = REMOTE_FILE_ID_LINE.findall(value)
        if len(ids) > 1:
            errors.append("descriptor contains multiple remote_file_id values")
        sanitized = REMOTE_FILE_ID_LINE.sub("", value)
        for token in (
            'version="1.0.0"',
            'name="Tributary Expansion Directives — 驱策朝贡国"',
            'supported_version="1.19.0.6"',
        ):
            if token not in sanitized:
                errors.append(f"product descriptor missing {token}")
    if source == DEFAULT_SOURCE.resolve():
        errors.extend(static_gate.validate())
    return list(dict.fromkeys(errors))


def _write_product_outer_descriptor(inner: Path, outer: Path, target: Path) -> str | None:
    text = inner.read_text(encoding="utf-8-sig")
    ids = REMOTE_FILE_ID_LINE.findall(text)
    if len(ids) > 1:
        raise acceptance.RunnerError("runtime descriptor contains multiple remote_file_id values")
    sanitized = REMOTE_FILE_ID_LINE.sub("", text)
    inner.write_bytes(sanitized.encode("utf-8"))
    rendered = sanitized.rstrip("\r\n") + f'\npath="{target.as_posix()}"\n'
    outer.write_bytes(rendered.encode("utf-8-sig"))
    return ids[0] if ids else None


def render_presets() -> str:
    rules = DEFAULT_CK3_EXE.parent.parent / "game/common/game_rules/00_game_rules.txt"
    settings = [
        setting for _, setting in acceptance.declared_vanilla_rule_defaults(rules)
    ]
    if len(settings) != len(set(settings)):
        raise acceptance.RunnerError("duplicate vanilla game-rule default")
    return (
        "game_rules_preset={\n"
        '\tname="LastAppliedRules"\n'
        f"\tsetting={{ {' '.join(settings)} }}\n"
        "\tironman=no\n"
        "}\n"
    )


def bootstrap_userdir(userdir: Path) -> dict[str, object]:
    for path in (
        userdir / "mod",
        userdir / "mod-content",
        userdir / "logs",
        userdir / "save games",
        userdir / "player/game_rules",
    ):
        path.mkdir(parents=True, exist_ok=True)
    product = userdir / "mod-content/product"
    for relative in sorted(release.RUNTIME_FILES):
        source = Path(harness.SOURCE) / PurePosixPath(relative)
        destination = product / PurePosixPath(relative)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
    fixture = userdir / "mod-content/fixture"
    shutil.copytree(FIXTURE_SOURCE, fixture)
    workshop_item_id = _write_product_outer_descriptor(
        product / "descriptor.mod", userdir / "mod" / PRODUCT_OUTER, product
    )
    isolated.write_outer_descriptor(
        fixture / "descriptor.mod", userdir / "mod" / FIXTURE_OUTER, fixture
    )
    enabled_mods = [f"mod/{PRODUCT_OUTER}", f"mod/{FIXTURE_OUTER}"]
    (userdir / "tutorial.txt").write_text(
        'last_lesson_chain="reactive_advice"\ncompleted_lessons={\n}\n', encoding="utf-8"
    )
    (userdir / "player/game_rules/presets.txt").write_text(
        render_presets(), encoding="utf-8"
    )
    (userdir / "dlc_load.json").write_text(
        '{"enabled_mods":["mod/'
        + PRODUCT_OUTER
        + '","mod/'
        + FIXTURE_OUTER
        + '"],"disabled_dlcs":[]}',
        encoding="utf-8",
    )
    (userdir / "pdx_settings.txt").write_text(
        harness.terminal.render_settings(), encoding="utf-8"
    )
    targets = {"product": product, "fixture": fixture}
    snapshots = {key: isolated.tree_snapshot(path) for key, path in targets.items()}
    return {
        "targets": targets,
        "tree_snapshots": snapshots,
        "tree_sha256": {
            key: isolated.snapshot_digest(snapshot) for key, snapshot in snapshots.items()
        },
        "enabled_mods": enabled_mods,
        "workshop_item_id": workshop_item_id,
        "manifest": {
            "projection": "exact-release-allowlist",
            "files": sorted(release.RUNTIME_FILES),
            "tree_sha256": isolated.snapshot_digest(snapshots["product"]),
        },
    }


def run_scenario(stream: TeaMarkerStream, artifacts: Path) -> dict[str, object]:
    confirm = isolated.open_decision_detail(
        "开始朝贡扩张指令实机验收",
        "建立朝贡关系并执行分支",
        artifacts,
        "05_initialize",
        contains=False,
    )
    acceptance.click_until_text_disappears(
        confirm,
        "建立朝贡关系并执行分支",
        acceptance.FULL_SCREEN_REGION,
        artifacts,
        attempts=2,
    )
    stream.wait("TEA: TEST PASS switched_to_supported_player", 30)
    isolated.wait_for_gameplay_hud(artifacts)
    stream.wait("TEA: TEST DONE tributary_expansion_directives", 60)
    stream.validate()
    acceptance.ImageGrab.grab().save(artifacts / "07_directed_war_live.png")
    return {
        "direct_tributary_constructed": True,
        "valid_decline_prestige_delta": -150,
        "valid_decline_gold_delta": 0,
        "valid_decline_war_count": 0,
        "subsidized_accept_prestige_delta": -150,
        "subsidized_accept_gold_transfer": "exact ted_war_subsidy_value",
        "dedicated_war_started": True,
        "primary_attacker": "tributary",
        "primary_defender": "selected neighboring independent ruler",
        "remaining_live_gaps": [
            "production interaction selector UI",
            "invalidated-response cooldown refund",
            "victory, white-peace, and defeat outcomes",
            "save/reload and post-war tribute amount",
        ],
    }


def configure_harness(source: Path) -> None:
    harness.SOURCE = source
    harness.FIXTURE_SOURCE = FIXTURE_SOURCE
    harness.BOOT_TIMEOUT_S = 30 * 60
    harness.PRODUCT_OUTER = PRODUCT_OUTER
    harness.FIXTURE_OUTER = FIXTURE_OUTER
    harness.PROJECT_TOKENS = (
        "mod_tributary_expansion_directives",
        "tributary expansion directives",
        "ted_",
        "ted.",
        "tea_",
        "tea.",
    )
    harness.REQUIRED_MARKERS = REQUIRED_MARKERS
    harness.MarkerStream = TeaMarkerStream
    harness.log = log
    harness.fixture_source_errors = fixture_source_errors
    harness.product_source_errors = product_source_errors
    harness.render_presets = render_presets
    harness.bootstrap_userdir = bootstrap_userdir
    harness.run_scenario = run_scenario


def main(args: argparse.Namespace) -> int:
    source = Path(args.source).expanduser().resolve() if args.source else DEFAULT_SOURCE.resolve()
    configure_harness(source)
    return harness.main(
        artifacts_dir=args.artifacts_dir,
        keep_userdir=args.keep_userdir,
        preflight_only=args.preflight,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifacts-dir")
    parser.add_argument("--source", help="canonical source or strict-verified Workshop cache")
    parser.add_argument("--keep-userdir", action="store_true")
    parser.add_argument("--preflight", action="store_true")
    try:
        raise SystemExit(main(parser.parse_args()))
    except acceptance.RunnerError as error:
        print(f"TRIBUTARY EXPANSION ACCEPTANCE FAILED: {error}", file=sys.stderr)
        raise SystemExit(1)
