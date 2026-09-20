#!/usr/bin/env python3
"""Run one isolated CK3 live cell for Celestial Commerce & Corruption."""

from __future__ import annotations

import argparse
import os
import re
import sys
import time
from pathlib import Path, PurePosixPath

DEFAULT_CK3_EXE = Path(
    r"C:\SteamLibrary\steamapps\common\Crusader Kings III\binaries\ck3.exe"
)
if "XAR_CK3_EXE" not in os.environ and DEFAULT_CK3_EXE.is_file():
    os.environ["XAR_CK3_EXE"] = str(DEFAULT_CK3_EXE)

import build_celestial_commerce_corruption_release as release
import run_acceptance as acceptance
import run_ox_here_acceptance as harness
import run_tributary_expansion_directives_acceptance as reusable
import run_vivhite_acceptance as isolated
import validate_celestial_commerce_corruption_static as static_gate


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / release.PRODUCT_ID
FIXTURE_SOURCE = ROOT / "tools/fixtures/celestial_commerce_corruption_acceptance"
PRODUCT_OUTER = "xccc_acceptance.mod"
FIXTURE_OUTER = "xca_acceptance_fixture.mod"
REQUIRED_MARKERS = (
    "XCA: TEST BEGIN celestial_commerce_corruption",
    "XCA: TEST PASS celestial_government_allows_barter",
    "XCA: TEST PASS switched_to_song_emperor",
    "XCA: TEST PASS switched_to_celestial_official",
    "XCA: TEST PASS corruption_tier_four_applied",
    "XCA: TEST PASS tier_four_tax_rate_is_fifty_percent",
    "XCA: TEST PASS production_decision_event_round_trip",
    "XCA: TEST DONE celestial_commerce_corruption",
)
REMOTE_FILE_ID_LINE = re.compile(
    r'(?m)^[ \t]*remote_file_id[ \t]*=[ \t]*"([0-9]+)"[ \t]*(?:\r?\n|$)'
)


def log(message: str) -> None:
    acceptance.log(f"celestial_commerce_corruption: {message}")


class XcaMarkerStream(reusable.TeaMarkerStream):
    """The shared stream implementation, scoped to this fixture's marker prefix."""

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
                raise acceptance.RunnerError(
                    f"cannot finalize fixture log: {error}"
                ) from error
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
            if "XCA:" in line:
                stripped = line.strip()
                self.lines.append(stripped)
                log(stripped)
        failures = [line for line in self.lines if "XCA: TEST FAIL" in line]
        if failures:
            raise acceptance.RunnerError(f"fixture failure marker: {failures[-1]}")


def fixture_source_errors() -> list[str]:
    if not FIXTURE_SOURCE.is_dir():
        return [f"fixture source missing: {FIXTURE_SOURCE}"]
    errors: list[str] = []
    for path in sorted(item for item in FIXTURE_SOURCE.rglob("*") if item.is_file()):
        relative = path.relative_to(FIXTURE_SOURCE).as_posix()
        data = path.read_bytes()
        if relative != "descriptor.mod" and path.suffix.lower() in {
            ".txt",
            ".gui",
            ".yml",
        } and not data.startswith(b"\xef\xbb\xbf"):
            errors.append(f"fixture text lacks UTF-8 BOM: {relative}")
        value = data.decode("utf-8-sig", errors="replace")
        if "remote_file_id" in value:
            errors.append(f"fixture contains Workshop identity: {relative}")
        if path.suffix.lower() in {".txt", ".gui"} and not static_gate.balanced_braces(
            value
        ):
            errors.append(f"fixture has unbalanced braces: {relative}")
    effects = FIXTURE_SOURCE / "common/scripted_effects/xca_effects.txt"
    if effects.is_file():
        value = effects.read_text(encoding="utf-8-sig")
        for token in (
            "character:han_8052",
            "government_allows = barter",
            "has_trait = xccc_corruption_4",
            "value = xccc_celestial_tax_default",
            "subtract = xccc_corruption_4_tax_deduction",
            "var:xca_tax_after_tier_four = 0.50",
        ):
            if token not in value:
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
        if not path.is_file() or path.name == "descriptor.mod":
            continue
        if path.suffix.lower() in {".txt", ".gui", ".yml"} and not path.read_bytes().startswith(
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
            'name="天朝制允许经商&贪腐框架（XenoAmess维护版）"',
            'supported_version="1.19.0.6"',
        ):
            if token not in sanitized:
                errors.append(f"product descriptor missing {token}")
    if source == DEFAULT_SOURCE.resolve():
        errors.extend(static_gate.validate())
    return list(dict.fromkeys(errors))


def click_decision(
    title: str, confirm_label: str, artifacts: Path, stem: str
) -> None:
    confirm = isolated.open_decision_detail(
        title, confirm_label, artifacts, stem, contains=False
    )
    acceptance.click_until_text_disappears(
        confirm,
        confirm_label,
        acceptance.FULL_SCREEN_REGION,
        artifacts,
        attempts=2,
    )


def choose_event_option(label: str, artifacts: Path, stem: str) -> None:
    point = acceptance.wait_for_ocr_text(
        label,
        acceptance.FULL_SCREEN_REGION,
        30,
        artifacts,
        f"{stem}.png",
        contains=True,
        stable_hits=1,
    )
    acceptance.click_until_text_disappears(
        point,
        label,
        acceptance.FULL_SCREEN_REGION,
        artifacts,
        attempts=2,
    )


def run_scenario(stream: reusable.TeaMarkerStream, artifacts: Path) -> dict[str, object]:
    click_decision(
        "开始天朝经商贪腐实机验收",
        "切换至验收官员",
        artifacts,
        "05_initialize",
    )
    stream.wait("XCA: TEST PASS switched_to_celestial_official", 45)
    isolated.wait_for_gameplay_hud(artifacts)
    acceptance.ensure_game_paused(artifacts, "05_celestial_official")
    click_decision(
        "定夺贪墨之策",
        "翻开账册",
        artifacts,
        "06_production_decision",
    )
    choose_event_option(
        "榨尽这官位所能承受的一切",
        artifacts,
        "07_production_event_tier_four",
    )
    stream.wait("XCA: TEST DONE celestial_commerce_corruption", 30)
    stream.validate()
    acceptance.ImageGrab.grab().save(artifacts / "08_policy_applied_live.png")
    return {
        "installed_build": "1.19.0.6",
        "celestial_government_allows_barter": True,
        "production_decision_rendered_and_confirmed": True,
        "production_event_tier_four_selected": True,
        "corruption_trait_applied": "xccc_corruption_4",
        "tier_four_tax_rate": 0.50,
        "stale_feast_override_absent": True,
        "stale_county_gui_override_absent": True,
        "remaining_gap": (
            "the engine does not expose a direct scripted trigger for the final "
            "subject-contract tax transfer amount; the live constant calculation and "
            "production contract wiring are proven separately"
        ),
    }


def configure_reusable(source: Path) -> None:
    reusable.release = release
    reusable.static_gate = static_gate
    reusable.DEFAULT_SOURCE = DEFAULT_SOURCE
    reusable.FIXTURE_SOURCE = FIXTURE_SOURCE
    reusable.PRODUCT_OUTER = PRODUCT_OUTER
    reusable.FIXTURE_OUTER = FIXTURE_OUTER
    reusable.REQUIRED_MARKERS = REQUIRED_MARKERS
    reusable.REMOTE_FILE_ID_LINE = REMOTE_FILE_ID_LINE
    reusable.log = log
    reusable.fixture_source_errors = fixture_source_errors
    reusable.product_source_errors = product_source_errors
    reusable.run_scenario = run_scenario
    reusable.configure_harness(source)
    harness.MarkerStream = XcaMarkerStream
    harness.BOOT_TIMEOUT_S = 30 * 60
    harness.ACCEPTANCE_LABEL = "CELESTIAL COMMERCE & CORRUPTION"
    harness.ARTIFACT_PREFIX = "xcca"
    harness.USERDIR_PREFIX = "xccu"
    harness.PROJECT_TOKENS = (
        "mod_celestial_commerce_corruption",
        "celestial commerce",
        "xccc_",
        "xccc.",
        "xca_",
        "xca.",
    )


def main(args: argparse.Namespace) -> int:
    source = (
        Path(args.source).expanduser().resolve()
        if args.source
        else DEFAULT_SOURCE.resolve()
    )
    configure_reusable(source)
    return harness.main(
        artifacts_dir=args.artifacts_dir,
        keep_userdir=args.keep_userdir,
        preflight_only=args.preflight,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifacts-dir")
    parser.add_argument("--source", help="canonical source or strict Workshop cache")
    parser.add_argument("--keep-userdir", action="store_true")
    parser.add_argument("--preflight", action="store_true")
    try:
        raise SystemExit(main(parser.parse_args()))
    except acceptance.RunnerError as error:
        print(f"CELESTIAL COMMERCE ACCEPTANCE FAILED: {error}", file=sys.stderr)
        raise SystemExit(1)
