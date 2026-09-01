#!/usr/bin/env python3
"""Run fresh-process CK3 localization smoke cells for all Ox Here languages.

The live matrix copies either the canonical source or an exact Workshop cache
leaf into a disposable ``-userdir``.  It never loads or edits the supplied
Workshop tree in place.  A tiny external fixture contributes a locale-specific
ASCII row locator and observes the production warrior after delivery; it does not
replace the production decision or event.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import json
import os
import platform
import re
import shutil
import sys
import tempfile
import time
import traceback
import uuid
from pathlib import Path

from PIL import Image, ImageChops

import build_ox_here_release
import run_acceptance as acceptance
import run_terminal_acceptance as terminal
import run_vivhite_acceptance as isolated


ROOT = Path(__file__).resolve().parent.parent
CANONICAL_SOURCE = ROOT / "ox_here"
FIXTURE_SOURCE = ROOT / "tools" / "fixtures" / "ox_here_loc_smoke"
EXPECTED_GAME_VERSION = "1.19.0.6"
STEAM_APP_ID = "1158310"
POSTFLIGHT_STABILITY_SECONDS = 5
BOOT_TIMEOUT_S = 300
DECISIONS_OPEN_ATTEMPTS = 3
DECISIONS_OPEN_TIMEOUT_S = 8
GAMEPLAY_TIMEOUT_S = 240
# Polish adds a separate community-localization version row and moves CK3's
# own version line above the single-row position used by the other locales.
FRONTEND_VERSION_REGION = (0.72, 0.88, 1.00, 1.00)
OPTION_RESPONSE_REGION = (0.30, 0.34, 0.62, 0.60)
OPTION_RESPONSE_MIN_CHANGED_FRACTION = 0.001
PRODUCT_OUTER = "ox_here_loc_smoke.mod"
FIXTURE_OUTER = "oxls_fixture.mod"
READY_MARKER = "OXLS: TEST READY gameplay"
DELIVERY_MARKER = "OXLS: TEST PASS production_delivery"
PROJECT_TOKENS = ("ox_here", "oxls_", "oxls.", "oxls:")
DUPLICATE_PATTERNS = (
    "there is more than one",
    "using most recent",
    "duplicate definition",
    "duplicate key",
    "already defined",
    "already registered",
)
EXPECTED_LOC_KEYS = frozenset(
    {
        "decision_group_type_ox_here",
        "ox_here_decision",
        "ox_here_decision_desc",
        "ox_here_decision_tooltip",
        "ox_here_decision_option_recruit",
        "ox_here_decision_option_recruit_desc",
        "ox_here_recruit_tooltip",
        "ox_here_decision_option_decline",
        "ox_here_decision_option_decline_desc",
        "ox_here_decline_tooltip",
        "ox_here_decision_confirm",
        "ox_here_secret_affair",
        "ox_here_secret_affair_corresponding",
        "ox_here_arrival_event_title",
        "ox_here_arrival_event_desc",
        "ox_here_arrival_event_desc_champion",
        "ox_here_arrival_event_option",
        "ox_here_blond_kanuri",
        "ox_here_blond_kanuri_collective_noun",
        "ox_here_blond_kanuri_prefix",
    }
)

OPEN_KAISHEK_PREFLIGHT_RESULT: dict[str, object] | None = None


@dataclass(frozen=True)
class LanguageSpec:
    key: str
    folder: str
    suffix: str
    anchor: str

    @property
    def localization_path(self) -> Path:
        return (
            Path("localization")
            / self.folder
            / f"ox_here_l_{self.suffix}.yml"
        )

    @property
    def fixture_localization_path(self) -> Path:
        return (
            Path("localization")
            / self.folder
            / f"oxls_l_{self.suffix}.yml"
        )


LANGUAGES = (
    LanguageSpec("l_english", "english", "english", "LOC SMOKE ENGLISH"),
    LanguageSpec("l_french", "french", "french", "LOC SMOKE FRENCH"),
    LanguageSpec("l_german", "german", "german", "LOC SMOKE GERMAN"),
    LanguageSpec("l_polish", "polish", "polish", "LOC SMOKE POLISH"),
    LanguageSpec("l_japanese", "japanese", "japanese", "LOC SMOKE JAPANESE"),
    LanguageSpec("l_spanish", "spanish", "spanish", "LOC SMOKE SPANISH"),
    LanguageSpec(
        "l_simp_chinese",
        "simp_chinese",
        "simp_chinese",
        "LOC SMOKE CHINESE",
    ),
    LanguageSpec("l_russian", "russian", "russian", "LOC SMOKE RUSSIAN"),
    LanguageSpec("l_korean", "korean", "korean", "LOC SMOKE KOREAN"),
)
LANGUAGE_BY_KEY = {spec.key: spec for spec in LANGUAGES}
EXPECTED_FIXTURE_LOC_KEYS = frozenset(
    {
        "oxls_anchor_decision",
        "oxls_anchor_decision_confirm",
        "oxls_anchor_decision_desc",
        "oxls_anchor_decision_tooltip",
    }
)
LOC_LINE = re.compile(
    r'^\s*([A-Za-z0-9_.-]+):(?:\d+)?\s+"((?:[^"\\]|\\.)*)"\s*$'
)
REMOTE_LINE = re.compile(rb'^\s*remote_file_id="([1-9][0-9]*)"\s*$')


def log(message: str) -> None:
    acceptance.log(f"ox_here_loc: {message}")


def write_json(path: Path, payload: object) -> None:
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def parse_localization(path: Path, expected_header: str) -> dict[str, str]:
    data = Path(path).read_bytes()
    if not data.startswith(b"\xef\xbb\xbf"):
        raise acceptance.RunnerError(f"localization lacks UTF-8 BOM: {path}")
    text = data.decode("utf-8-sig")
    lines = [line for line in text.splitlines() if line.strip()]
    if not lines or lines[0].strip() != f"{expected_header}:":
        raise acceptance.RunnerError(
            f"localization header mismatch: {path} != {expected_header}:"
        )
    values: dict[str, str] = {}
    for line_number, line in enumerate(lines[1:], 2):
        if line.lstrip().startswith("#"):
            continue
        match = LOC_LINE.fullmatch(line)
        if match is None:
            raise acceptance.RunnerError(
                f"unsupported localization line: {path}:{line_number}"
            )
        key, value = match.groups()
        if key in values:
            raise acceptance.RunnerError(
                f"duplicate localization key: {path}:{line_number}: {key}"
            )
        values[key] = value
    return values


def localization_matrix(source: Path) -> dict[str, dict[str, str]]:
    return {
        spec.key: parse_localization(source / spec.localization_path, spec.key)
        for spec in LANGUAGES
    }


def localization_errors(source: Path) -> list[str]:
    errors: list[str] = []
    try:
        matrix = localization_matrix(source)
    except (OSError, UnicodeError, acceptance.RunnerError) as error:
        return [str(error)]
    english = matrix["l_english"]
    for language, values in matrix.items():
        keys = frozenset(values)
        if keys != EXPECTED_LOC_KEYS:
            missing = sorted(EXPECTED_LOC_KEYS - keys)
            extra = sorted(keys - EXPECTED_LOC_KEYS)
            errors.append(
                f"{language} localization key mismatch: missing={missing}, extra={extra}"
            )
        for key, value in values.items():
            if not value.strip():
                errors.append(f"{language} localization is empty: {key}")
            rendered_literal = re.sub(r"\[[^\]]+\]", "", value)
            if re.search(
                r"\box_here(?:[_.][a-z0-9_]+)", rendered_literal.lower()
            ):
                errors.append(f"{language} localization exposes a raw key in {key}")
        for key in ("ox_here_arrival_event_desc", "ox_here_arrival_event_desc_champion"):
            if values.get(key, "").count("[ox_here_warrior.GetShortUIName|U]") != 1:
                errors.append(f"{language} does not preserve the warrior token in {key}")
        if language != "l_english":
            unchanged = sorted(
                key for key in EXPECTED_LOC_KEYS if values.get(key) == english.get(key)
            )
            if unchanged:
                errors.append(
                    f"{language} still contains English placeholder values: {unchanged}"
                )
    return errors


def fixture_source_errors() -> list[str]:
    if not FIXTURE_SOURCE.is_dir():
        return [f"fixture source missing: {FIXTURE_SOURCE}"]
    errors: list[str] = []
    for path in sorted(item for item in FIXTURE_SOURCE.rglob("*") if item.is_file()):
        relative = path.relative_to(FIXTURE_SOURCE).as_posix()
        data = path.read_bytes()
        if path.suffix.lower() in {".mod", ".txt", ".gui", ".yml"} and not data.startswith(
            b"\xef\xbb\xbf"
        ):
            errors.append(f"fixture text lacks UTF-8 BOM: {relative}")
        text = data.decode("utf-8-sig", errors="replace")
        if "remote_file_id" in text:
            errors.append(f"fixture contains Workshop identity: {relative}")
        depth = 0
        for line_number, line in enumerate(text.splitlines(), 1):
            body = line.split("#", 1)[0]
            depth += body.count("{") - body.count("}")
            if depth < 0:
                errors.append(
                    f"fixture has an unexpected closing brace: {relative}:{line_number}"
                )
                break
        if depth > 0:
            errors.append(f"fixture has {depth} unclosed brace(s): {relative}")
    loc_folders = {
        path.parent.name
        for path in (FIXTURE_SOURCE / "localization").glob("*/*.yml")
    }
    expected_folders = {spec.folder for spec in LANGUAGES}
    if loc_folders != expected_folders:
        errors.append(
            f"fixture localization folders mismatch: {sorted(loc_folders)}"
        )
    registry = (
        FIXTURE_SOURCE
        / "gui"
        / "scripted_widgets"
        / "oxls_scripted_widgets.txt"
    )
    try:
        registry_text = registry.read_text(encoding="utf-8-sig").strip()
    except (OSError, UnicodeError) as error:
        errors.append(f"cannot read fixture scripted-widget registry: {error}")
    else:
        if registry_text != "gui/oxls_bridge.gui = oxls_bridge_window":
            errors.append(
                "fixture scripted-widget registry must bind the GUI file to "
                "oxls_bridge_window"
            )
    anchors = [spec.anchor for spec in LANGUAGES]
    if len(anchors) != len(set(anchors)):
        errors.append("LanguageSpec OCR anchors are not unique")
    for spec in LANGUAGES:
        if re.fullmatch(r"LOC SMOKE [A-Z]+", spec.anchor, flags=re.ASCII) is None:
            errors.append(
                f"LanguageSpec anchor is not OCR-safe ASCII: {spec.key}: {spec.anchor!r}"
            )
        path = FIXTURE_SOURCE / spec.fixture_localization_path
        try:
            values = parse_localization(path, spec.key)
        except (OSError, UnicodeError, acceptance.RunnerError) as error:
            errors.append(str(error))
            continue
        if frozenset(values) != EXPECTED_FIXTURE_LOC_KEYS:
            errors.append(
                f"fixture localization key mismatch for {spec.key}: "
                f"{sorted(values)}"
            )
        actual_anchor = values.get("oxls_anchor_decision")
        if actual_anchor != spec.anchor:
            errors.append(
                f"fixture active-language anchor mismatch for {spec.key}: "
                f"{actual_anchor!r} != {spec.anchor!r}"
            )
    return errors


def normalized_descriptor_bytes(data: bytes, workshop_item_id: str | None) -> bytes:
    lines = data.splitlines(keepends=True)
    remote = [
        (index, REMOTE_LINE.fullmatch(line.rstrip(b"\r\n")))
        for index, line in enumerate(lines)
        if b"remote_file_id" in line
    ]
    if workshop_item_id is None:
        if remote:
            raise acceptance.RunnerError(
                "canonical product descriptor unexpectedly contains remote_file_id"
            )
        return data
    if len(remote) != 1 or remote[0][0] != len(lines) - 1 or remote[0][1] is None:
        raise acceptance.RunnerError(
            "Workshop descriptor must end with exactly one canonical remote_file_id"
        )
    actual = remote[0][1].group(1).decode("ascii")
    if actual != workshop_item_id:
        raise acceptance.RunnerError(
            f"Workshop descriptor item ID {actual} != cache leaf {workshop_item_id}"
        )
    return b"".join(lines[:-1])


def product_source_errors(source: Path, workshop_item_id: str | None) -> list[str]:
    if not source.is_dir():
        return [f"product source missing: {source}"]
    allowed = set(build_ox_here_release.RUNTIME_FILES)
    if workshop_item_id is None and source.resolve() == CANONICAL_SOURCE.resolve():
        allowed.update(build_ox_here_release.SOURCE_ONLY_FILES)
    actual = {
        path.relative_to(source).as_posix()
        for path in source.rglob("*")
        if path.is_file()
    }
    errors: list[str] = []
    errors.extend(f"required runtime file missing: {name}" for name in sorted(
        build_ox_here_release.RUNTIME_FILES - actual
    ))
    errors.extend(f"file outside localization smoke allowlist: {name}" for name in sorted(
        actual - allowed
    ))
    for path in sorted(source.rglob("*"), key=lambda item: item.as_posix()):
        if path.is_symlink():
            errors.append(
                f"symlink is forbidden: {path.relative_to(source).as_posix()}"
            )
    descriptor = source / "descriptor.mod"
    if descriptor.is_file():
        try:
            normalized_descriptor_bytes(descriptor.read_bytes(), workshop_item_id)
        except acceptance.RunnerError as error:
            errors.append(str(error))
    for relative in sorted(actual & set(build_ox_here_release.RUNTIME_FILES)):
        path = source / relative
        if path.suffix.lower() not in {".mod", ".txt", ".gui", ".yml"}:
            continue
        try:
            text = path.read_text(encoding="utf-8-sig")
        except UnicodeError as error:
            errors.append(f"runtime text is not UTF-8: {relative}: {error}")
            continue
        if relative != "descriptor.mod" and "remote_file_id" in text:
            errors.append(f"runtime file contains Workshop identity: {relative}")
    errors.extend(localization_errors(source))
    return errors


def validate_workshop_source(source: Path, steam_root: Path) -> str:
    source = source.resolve()
    roots = isolated.steam_workshop_app_roots(steam_root)
    if source.parent not in roots:
        raise acceptance.RunnerError(
            f"Workshop cache must be an exact CK3 item leaf: {source}"
        )
    try:
        item_id = build_ox_here_release.normalize_workshop_item_id(source.name)
    except ValueError as error:
        raise acceptance.RunnerError(str(error)) from error
    assert item_id is not None
    return item_id


def validate_mode_arguments(
    workshop_cache: str | None, manifest_path: str | None
) -> None:
    if workshop_cache and not manifest_path:
        raise acceptance.RunnerError(
            "--workshop-cache requires --manifest for release-level verification"
        )
    if manifest_path and not workshop_cache:
        raise acceptance.RunnerError("--manifest requires --workshop-cache")


def render_settings(language: str) -> str:
    if language not in LANGUAGE_BY_KEY:
        raise ValueError(f"unsupported CK3 language: {language}")
    return f'''"game"={{
\t"promt_for_tutorial"={{ version=0 enabled=no }}
\t"prompt_for_china_tutorial"={{ version=0 enabled=no }}
\t"cloud_save"={{ version=0 enabled=no }}
}}
"Graphics"={{
\t"display_mode"={{ version=0 value="fullscreen" }}
\t"display_index"={{ version=0 value="0" }}
\t"fullscreen_resolution"={{ version=0 value="2560x1440" }}
}}
"System"={{
\t"language"={{ version=0 value="{language}" }}
}}
'''


def render_presets() -> str:
    settings = [setting for _, setting in acceptance.declared_vanilla_rule_defaults()]
    if len(settings) != len(set(settings)):
        raise acceptance.RunnerError("duplicate vanilla game-rule default")
    return (
        "game_rules_preset={\n"
        '\tname="LastAppliedRules"\n'
        f"\tsetting={{ {' '.join(settings)} }}\n"
        "\tironman=no\n"
        "}\n"
    )


def copy_product_runtime(
    source: Path,
    destination: Path,
    workshop_item_id: str | None,
) -> list[str]:
    files: list[str] = []
    for relative in sorted(build_ox_here_release.RUNTIME_FILES):
        source_path = source / relative
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if relative == "descriptor.mod":
            target.write_bytes(
                normalized_descriptor_bytes(
                    source_path.read_bytes(), workshop_item_id
                )
            )
        else:
            shutil.copy2(source_path, target)
        files.append(relative)
    return files


def bootstrap_userdir(
    userdir: Path,
    source: Path,
    workshop_item_id: str | None,
    language: str,
) -> dict[str, object]:
    for path in (
        userdir / "mod",
        userdir / "mod-content",
        userdir / "logs",
        userdir / "save games",
        userdir / "player" / "game_rules",
    ):
        path.mkdir(parents=True, exist_ok=True)

    product = userdir / "mod-content" / "ox_here"
    product_files = copy_product_runtime(source, product, workshop_item_id)
    fixture = userdir / "mod-content" / "fixture"
    shutil.copytree(FIXTURE_SOURCE, fixture)
    isolated.write_outer_descriptor(
        product / "descriptor.mod", userdir / "mod" / PRODUCT_OUTER, product
    )
    isolated.write_outer_descriptor(
        fixture / "descriptor.mod", userdir / "mod" / FIXTURE_OUTER, fixture
    )
    enabled_mods = [f"mod/{PRODUCT_OUTER}", f"mod/{FIXTURE_OUTER}"]
    (userdir / "tutorial.txt").write_text(
        'last_lesson_chain="reactive_advice"\ncompleted_lessons={\n}\n',
        encoding="utf-8",
        newline="\n",
    )
    (userdir / "player" / "game_rules" / "presets.txt").write_text(
        render_presets(), encoding="utf-8", newline="\n"
    )
    (userdir / "dlc_load.json").write_text(
        json.dumps(
            {"enabled_mods": enabled_mods, "disabled_dlcs": []},
            separators=(",", ":"),
        ),
        encoding="utf-8",
        newline="\n",
    )
    (userdir / "pdx_settings.txt").write_text(
        render_settings(language), encoding="utf-8", newline="\n"
    )
    targets = {"product": product, "fixture": fixture}
    snapshots = {key: isolated.tree_snapshot(path) for key, path in targets.items()}
    return {
        "targets": targets,
        "tree_snapshots": snapshots,
        "tree_sha256": {
            key: isolated.snapshot_digest(snapshot)
            for key, snapshot in snapshots.items()
        },
        "enabled_mods": enabled_mods,
        "product_files": product_files,
    }


def verify_runtime_load_order(
    userdir: Path, bootstrap: dict[str, object]
) -> list[str]:
    debug_log = userdir / "logs" / "debug.log"
    try:
        text = debug_log.read_text(encoding="utf-8", errors="ignore")
    except OSError as error:
        raise acceptance.RunnerError(
            f"cannot read runtime mod inventory: {error}"
        ) from error
    enabled = re.findall(r"(?m)^[^\r\n|]+\|(mod/[^\r\n|]+)\|Enabled\s*$", text)
    expected_enabled = list(bootstrap["enabled_mods"])
    if len(enabled) != len(expected_enabled) or set(enabled) != set(expected_enabled):
        raise acceptance.RunnerError(
            f"isolated enabled-mod inventory drifted: {enabled} != {expected_enabled}"
        )
    content_root = (userdir / "mod-content").resolve()
    mounted: list[Path] = []
    for raw in re.findall(r"(?m)Mounted Data:\s*([^\r\n]+?)\s*$", text):
        path = Path(raw.strip()).resolve()
        if isolated.is_relative_to(path, content_root):
            mounted.append(path)
    expected = [
        Path(bootstrap["targets"][key]).resolve()
        for key in ("product", "fixture")
    ]
    if mounted != expected:
        raise acceptance.RunnerError(
            "isolated mount order drifted: "
            f"{[path.as_posix() for path in mounted]} != "
            f"{[path.as_posix() for path in expected]}"
        )
    return [path.as_posix() for path in mounted]


class MarkerStream:
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
            if "OXLS:" in line:
                stripped = line.strip()
                self.lines.append(stripped)
                log(stripped)
        failures = [line for line in self.lines if "OXLS: TEST FAIL" in line]
        if failures:
            raise acceptance.RunnerError(f"fixture failure marker: {failures[-1]}")

    def wait(self, marker: str, timeout_s: float) -> None:
        deadline = time.monotonic() + timeout_s
        while time.monotonic() < deadline:
            self.pump()
            if any(marker in line for line in self.lines):
                return
            time.sleep(acceptance.POLL_INTERVAL_S)
        raise acceptance.RunnerError(f"fixture marker timeout: {marker}")

    def validate(self, final: bool = False) -> None:
        self.pump(final=final)
        for marker in (READY_MARKER, DELIVERY_MARKER):
            count = sum(marker in line for line in self.lines)
            if count != 1:
                raise acceptance.RunnerError(
                    f"fixture marker count for {marker!r} is {count}, expected 1"
                )


def wait_for_debug_text(path: Path, target: str, timeout_s: float) -> None:
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        try:
            if target in path.read_text(encoding="utf-8", errors="ignore"):
                return
        except OSError:
            pass
        time.sleep(acceptance.POLL_INTERVAL_S)
    raise acceptance.RunnerError(f"debug log timeout: {target}")


def project_diagnostics(userdir: Path, artifacts: Path, stem: str) -> list[str]:
    blocking: list[str] = []
    for name in ("error.log", "gui_warnings.log", "database_conflicts.log"):
        path = userdir / "logs" / name
        if not path.is_file():
            continue
        shutil.copy2(path, artifacts / f"{stem}_{name}")
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        for index, line in enumerate(lines):
            lowered = line.lower()
            context = " ".join(lines[max(0, index - 2) : index + 3]).lower()
            attributed = any(token in lowered for token in PROJECT_TOKENS)
            duplicate = any(pattern in lowered for pattern in DUPLICATE_PATTERNS)
            if attributed or (
                duplicate and any(token in context for token in PROJECT_TOKENS)
            ):
                if duplicate and "champion_total_salary_value" in lowered:
                    continue
                blocking.append(f"{name}: {line.strip()}")
    return list(dict.fromkeys(line for line in blocking if line.strip()))


def compact_ocr_text(text: str) -> str:
    return re.sub(r"\s+", "", text).lower()


def unresolved_product_keys(texts: list[str]) -> list[str]:
    compact = "".join(compact_ocr_text(text) for text in texts)
    hits = sorted(
        {
            match.group(0)
            for match in re.finditer(
                r"ox_here(?:[_.][a-z0-9_]+)", compact, flags=re.ASCII
            )
        }
    )
    hits.extend(
        key for key in sorted(EXPECTED_LOC_KEYS) if key.lower() in compact
    )
    return list(dict.fromkeys(hits))


def capture_surface(
    path: Path,
    language: str,
    surface: str,
) -> tuple[Image.Image, list[dict[str, object]]]:
    acceptance.focus_ck3()
    image = acceptance.ImageGrab.grab()
    image.save(path)
    rows = [
        {
            "text": text,
            "score": float(score),
            "center": [int(center[0]), int(center[1])],
            "top": float(top),
        }
        for text, score, center, top in acceptance.ocr_results(
            image, acceptance.FULL_SCREEN_REGION
        )
    ]
    write_json(
        path.with_suffix(".ocr.json"),
        {"language": language, "surface": surface, "rows": rows},
    )
    hits = unresolved_product_keys([str(row["text"]) for row in rows])
    if hits:
        raise acceptance.RunnerError(
            f"{language} {surface} exposes raw product key(s): {hits}"
        )
    return image, rows


def normalized_text(value: str) -> str:
    return re.sub(r"[^\w]+", "", value, flags=re.UNICODE).casefold()


def find_ocr_row(
    rows: list[dict[str, object]], target: str
) -> tuple[int, int] | None:
    expected = normalized_text(target)
    if not expected:
        return None
    normalized_rows = [
        (normalized_text(str(row["text"])), row) for row in rows
    ]
    for actual, row in normalized_rows:
        if actual == expected:
            center = row["center"]
            return int(center[0]), int(center[1])
    for actual, row in normalized_rows:
        if len(expected) >= 6 and expected in actual:
            center = row["center"]
            return int(center[0]), int(center[1])
    return None


def prove_active_language_anchor(
    rows: list[dict[str, object]], language: LanguageSpec
) -> dict[str, object]:
    expected = compact_ocr_text(language.anchor)
    observed: list[tuple[str, list[int]]] = []
    for row in rows:
        text = str(row["text"])
        if compact_ocr_text(text) == expected:
            center = [int(row["center"][0]), int(row["center"][1])]
            observed.append((text, center))
    wrong = sorted(
        spec.anchor
        for spec in LANGUAGES
        if spec != language
        and any(
            compact_ocr_text(str(row["text"]))
            == compact_ocr_text(spec.anchor)
            for row in rows
        )
    )
    if len(observed) != 1 or wrong:
        raise acceptance.RunnerError(
            f"active-language anchor proof failed for {language.key}: "
            f"expected_count={len(observed)}, wrong_anchors={wrong}"
        )
    text, center = observed[0]
    return {
        "language": language.key,
        "expected_anchor": language.anchor,
        "observed_ocr": text,
        "center": center,
        "wrong_language_anchors": wrong,
        "proof": "exact_unique_ascii_anchor",
    }


def changed_pixel_fraction(
    first: Image.Image,
    second: Image.Image,
    region: tuple[float, float, float, float] | None = None,
) -> float:
    if first.size != second.size:
        return 1.0
    width, height = first.size
    relative = region or (0.20, 0.08, 0.78, 0.92)
    box = (
        int(width * relative[0]),
        int(height * relative[1]),
        int(width * relative[2]),
        int(height * relative[3]),
    )
    if box[0] >= box[2] or box[1] >= box[3]:
        raise ValueError(f"invalid changed-pixel region: {relative}")
    difference = ImageChops.difference(first.crop(box), second.crop(box)).convert("L")
    histogram = difference.histogram()
    changed = sum(histogram[20:])
    return changed / max(1, difference.width * difference.height)


def navigate_lobby_fixed(artifacts: Path, debug_log: Path) -> None:
    # CK3 can render a fully interactive frontend without emitting the optional
    # Frontend-idler debug line.  The exact-build version token is visible on
    # every localized main menu and is therefore the stronger readiness gate.
    acceptance.wait_for_ocr_text(
        EXPECTED_GAME_VERSION,
        FRONTEND_VERSION_REGION,
        BOOT_TIMEOUT_S,
        artifacts,
        "01_main_menu_parser_ready.png",
        contains=True,
        stable_hits=2,
    )
    time.sleep(2)
    capture_surface(artifacts / "01_main_menu.png", "frontend", "main_menu")
    width, height = acceptance.pyautogui.size()
    new_game = (int(width * (600 / 2560)), int(height * (557 / 1440)))
    robert_portrait = (int(width * (1561 / 2560)), int(height * (1081 / 1440)))
    start = (int(width * (2257 / 2560)), int(height * (1245 / 1440)))
    last_error: BaseException | None = None
    for attempt in range(1, 4):
        acceptance.deliberate_click(new_game, f"localized New Game geometry ({attempt})")
        time.sleep(5)
        capture_surface(
            artifacts / f"02_bookmark_attempt_{attempt}.png",
            "frontend",
            "bookmark",
        )
        acceptance.deliberate_click(
            robert_portrait, f"1066 Robert portrait geometry ({attempt})"
        )
        time.sleep(1)
        acceptance.deliberate_click(start, f"localized Start geometry ({attempt})")
        try:
            wait_for_debug_text(
                debug_log,
                "Setting idler 'Bookmark' with init options",
                20,
            )
            return
        except acceptance.RunnerError as error:
            last_error = error
    raise acceptance.RunnerError(
        f"fixed multilingual lobby route was not accepted: {last_error}"
    )


def exercise_product_surfaces(
    language: LanguageSpec,
    localizations: dict[str, str],
    stream: MarkerStream,
    artifacts: Path,
) -> dict[str, object]:
    width, height = acceptance.pyautogui.size()
    decisions_tab = (int(width * 0.987), int(height * 0.367))
    anchor: tuple[int, int] | None = None
    last_error: BaseException | None = None
    for attempt in range(1, DECISIONS_OPEN_ATTEMPTS + 1):
        acceptance.deliberate_click(
            decisions_tab,
            f"native Decisions HUD tab ({attempt})",
        )
        acceptance.pyautogui.moveTo(int(width * 0.90), int(height * 0.70))
        acceptance.pyautogui.scroll(20)
        try:
            anchor = acceptance.wait_for_ocr_text(
                language.anchor,
                acceptance.FULL_SCREEN_REGION,
                DECISIONS_OPEN_TIMEOUT_S,
                artifacts,
                f"03_decisions_anchor_attempt_{attempt}_timeout.png",
                contains=False,
                stable_hits=1,
            )
            break
        except acceptance.RunnerError as error:
            last_error = error
    if anchor is None:
        raise acceptance.RunnerError(
            "native Decisions panel did not expose the locale anchor after "
            f"{DECISIONS_OPEN_ATTEMPTS} attempts: {last_error}"
        )
    panel, panel_rows = capture_surface(
        artifacts / "03_native_decisions.png", language.key, "native_decisions"
    )
    active_language_proof = prove_active_language_anchor(panel_rows, language)
    localized_row = find_ocr_row(panel_rows, localizations["ox_here_decision"])
    if localized_row is not None and localized_row[1] > anchor[1] + 20:
        product_y = localized_row[1]
        locator = "localized_title_ocr"
    else:
        product_y = anchor[1] + int(height * (78 / 1440))
        locator = "fixture_anchor_geometry"
    if not int(height * 0.10) < product_y < int(height * 0.90):
        raise acceptance.RunnerError(
            f"derived production decision row is out of bounds: {product_y}"
        )
    acceptance.deliberate_click(
        (int(width * 0.90), product_y),
        f"production Ox Here decision row via {locator}",
    )
    time.sleep(1)
    acceptance.pyautogui.moveTo(int(width * 0.05), int(height * 0.50))
    time.sleep(0.7)
    modal, modal_rows = capture_surface(
        artifacts / "04_native_decision_detail.png",
        language.key,
        "native_decision_detail",
    )
    panel_to_modal = changed_pixel_fraction(panel, modal)
    if panel_to_modal < 0.025:
        raise acceptance.RunnerError(
            f"decision detail did not materially replace the panel: {panel_to_modal:.6f}"
        )
    recruit = (int(width * (1127 / 2560)), int(height * (689 / 1440)))
    decline = (int(width * (1127 / 2560)), int(height * (775 / 1440)))
    option_confirm = (int(width * (1306 / 2560)), int(height * (1232 / 1440)))
    final_confirm = (int(width * (1428 / 2560)), int(height * (1232 / 1440)))
    acceptance.deliberate_click(decline, "production decline option geometry")
    time.sleep(0.7)
    decline_selected, decline_selected_rows = capture_surface(
        artifacts / "05_native_decision_decline_selected.png",
        language.key,
        "native_decision_decline_selected",
    )
    acceptance.deliberate_click(recruit, "production recruit option geometry")
    time.sleep(0.7)
    recruit_selected, selected_rows = capture_surface(
        artifacts / "05_native_decision_selected.png",
        language.key,
        "native_decision_selected",
    )
    decline_response = changed_pixel_fraction(
        modal, decline_selected, OPTION_RESPONSE_REGION
    )
    recruit_response = changed_pixel_fraction(
        modal, recruit_selected, OPTION_RESPONSE_REGION
    )
    decline_to_recruit = changed_pixel_fraction(
        decline_selected, recruit_selected, OPTION_RESPONSE_REGION
    )
    for label, fraction in (
        ("decline option", decline_response),
        ("recruit option", recruit_response),
        ("decline-to-recruit transition", decline_to_recruit),
    ):
        if fraction < OPTION_RESPONSE_MIN_CHANGED_FRACTION:
            raise acceptance.RunnerError(
                f"{label} did not materially change the option/tooltip ROI: "
                f"{fraction:.6f}"
            )
    acceptance.deliberate_click(
        option_confirm, "production decision option confirm geometry"
    )
    time.sleep(0.8)
    confirmation, confirmation_rows = capture_surface(
        artifacts / "06_native_decision_confirmation.png",
        language.key,
        "native_decision_confirmation",
    )
    recruit_to_confirmation = changed_pixel_fraction(
        recruit_selected, confirmation
    )
    if recruit_to_confirmation < 0.025:
        raise acceptance.RunnerError(
            "decision option confirm did not open the native confirmation step: "
            f"{recruit_to_confirmation:.6f}"
        )
    acceptance.deliberate_click(
        final_confirm, "production decision final confirm geometry"
    )
    time.sleep(1.2)
    event, event_rows = capture_surface(
        artifacts / "07_native_arrival_event.png",
        language.key,
        "native_arrival_event",
    )
    confirmation_to_event = changed_pixel_fraction(confirmation, event)
    if confirmation_to_event < 0.025:
        raise acceptance.RunnerError(
            "arrival event did not materially replace decision confirmation: "
            f"{confirmation_to_event:.6f}"
        )
    stream.wait(DELIVERY_MARKER, 40)
    return {
        "decision_locator": locator,
        "active_language_proof": active_language_proof,
        "product_row_y": product_y,
        "anchor_y": anchor[1],
        "panel_to_modal_changed_pixel_fraction": round(panel_to_modal, 6),
        "modal_to_decline_option_roi_changed_pixel_fraction": round(
            decline_response, 6
        ),
        "modal_to_recruit_option_roi_changed_pixel_fraction": round(
            recruit_response, 6
        ),
        "decline_to_recruit_changed_pixel_fraction": round(
            decline_to_recruit, 6
        ),
        "recruit_to_confirmation_changed_pixel_fraction": round(
            recruit_to_confirmation, 6
        ),
        "confirmation_to_event_changed_pixel_fraction": round(
            confirmation_to_event, 6
        ),
        "positive_ocr": {
            "decision_title": find_ocr_row(
                modal_rows, localizations["ox_here_decision"]
            )
            is not None,
            "recruit_option": find_ocr_row(
                selected_rows, localizations["ox_here_decision_option_recruit"]
            )
            is not None,
            "recruit_tooltip": find_ocr_row(
                selected_rows, localizations["ox_here_recruit_tooltip"]
            )
            is not None,
            "decline_option": find_ocr_row(
                decline_selected_rows,
                localizations["ox_here_decision_option_decline"],
            )
            is not None,
            "decline_tooltip": find_ocr_row(
                decline_selected_rows, localizations["ox_here_decline_tooltip"]
            )
            is not None,
            "confirmation_button": find_ocr_row(
                confirmation_rows, localizations["ox_here_decision_confirm"]
            )
            is not None,
            "arrival_title": find_ocr_row(
                event_rows, localizations["ox_here_arrival_event_title"]
            )
            is not None,
            "arrival_option": find_ocr_row(
                event_rows, localizations["ox_here_arrival_event_option"]
            )
            is not None,
        },
        "runtime_assertion_boundary": (
            "raw ox_here_ keys are automatically rejected in every captured surface; "
            "positive multilingual text is screenshot/model-review evidence because the "
            "bundled OCR model is not a reliable positive oracle for every CK3 script"
        ),
    }


def copy_logs(userdir: Path, artifacts: Path) -> None:
    logs = userdir / "logs"
    if not logs.is_dir():
        return
    for path in sorted(item for item in logs.iterdir() if item.is_file()):
        shutil.copy2(path, artifacts / f"final_{path.name}")


def configured_language_from_text(text: str) -> str | None:
    matches = re.findall(
        r'"language"\s*=\s*\{[^{}]*\bvalue\s*=\s*"([^"]+)"[^{}]*\}',
        text,
    )
    return matches[-1] if matches else None


def configured_language(path: Path) -> str | None:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return None
    return configured_language_from_text(text)


def run_cell(
    language: LanguageSpec,
    localizations: dict[str, str],
    artifacts: Path,
    userdir: Path,
    source: Path,
    workshop_item_id: str | None,
    keep_userdir: bool,
) -> dict[str, object]:
    started = time.perf_counter()
    started_at = datetime.now(timezone.utc).isoformat()
    artifacts.mkdir(parents=True)
    userdir.mkdir(parents=True)
    source_before = isolated.tree_snapshot(source)
    acceptance.configure_runtime_userdir(userdir)
    bootstrap = bootstrap_userdir(
        userdir, source, workshop_item_id, language.key
    )
    process = None
    result = "RED"
    error_reason = None
    evidence: dict[str, object] = {}
    diagnostics: list[str] = []
    mount_order: list[str] = []
    game_version = isolated.installed_game_version()
    executable_before = isolated.sha256_file(acceptance.CK3_EXE)
    executable_after = None
    runtime_after: dict[str, str] = {}
    runtime_unchanged = False
    source_unchanged = False
    stream = MarkerStream(userdir / "logs" / "debug.log")
    pid_path = artifacts / "ck3.pid"
    watchdog_pid = None
    try:
        watchdog_pid = acceptance.start_process_watchdog(pid_path)
        process = acceptance.launch_ck3_process(False)
        pid_path.write_text(str(process.pid), encoding="ascii")
        log(f"{language.key}: launched tracked CK3 PID {process.pid}")
        navigate_lobby_fixed(artifacts, userdir / "logs" / "debug.log")
        stream.wait(READY_MARKER, GAMEPLAY_TIMEOUT_S)
        mount_order = verify_runtime_load_order(userdir, bootstrap)
        diagnostics.extend(project_diagnostics(userdir, artifacts, "02_gameplay"))
        if diagnostics:
            raise acceptance.RunnerError(diagnostics[-1])
        evidence = exercise_product_surfaces(
            language, localizations, stream, artifacts
        )
        diagnostics.extend(project_diagnostics(userdir, artifacts, "07_runtime"))
        if diagnostics:
            raise acceptance.RunnerError(diagnostics[-1])
        if process.poll() is not None:
            raise acceptance.RunnerError(
                f"CK3 PID {process.pid} exited before controlled shutdown"
            )
        result = "GREEN"
    except BaseException as error:
        error_reason = str(error) or type(error).__name__
        log(f"{language.key}: FATAL {error}")
        if isinstance(error, Exception) and not isinstance(
            error, acceptance.RunnerError
        ):
            traceback.print_exc()
        try:
            acceptance.focus_ck3()
            acceptance.ImageGrab.grab().save(artifacts / "fatal_state.png")
        except Exception:
            pass
    finally:
        if process is not None:
            try:
                acceptance.stop_ck3_process(
                    process, pid_path, require_running=result == "GREEN"
                )
            except Exception as error:
                result = "RED"
                reason = f"controlled stop failed: {error}"
                error_reason = f"{error_reason}; {reason}" if error_reason else reason
        try:
            if result == "GREEN":
                stream.validate(final=True)
            else:
                stream.pump(final=True)
        except BaseException as error:
            result = "RED"
            reason = str(error) or type(error).__name__
            error_reason = f"{error_reason}; {reason}" if error_reason else reason
        try:
            version_after = isolated.installed_game_version()
            executable_after = isolated.sha256_file(acceptance.CK3_EXE)
            if (
                version_after != EXPECTED_GAME_VERSION
                or game_version != EXPECTED_GAME_VERSION
                or executable_after != executable_before
            ):
                raise acceptance.RunnerError(
                    "CK3 installation changed during localization smoke"
                )
        except BaseException as error:
            result = "RED"
            reason = str(error) or type(error).__name__
            error_reason = f"{error_reason}; {reason}" if error_reason else reason
        try:
            diagnostics.extend(project_diagnostics(userdir, artifacts, "08_shutdown"))
            copy_logs(userdir, artifacts)
            if diagnostics:
                raise acceptance.RunnerError(diagnostics[-1])
        except BaseException as error:
            result = "RED"
            reason = str(error) or type(error).__name__
            error_reason = f"{error_reason}; {reason}" if error_reason else reason
        try:
            runtime_unchanged = True
            for key, target in bootstrap["targets"].items():
                snapshot = isolated.tree_snapshot(target)
                runtime_after[key] = isolated.snapshot_digest(snapshot)
                if snapshot != bootstrap["tree_snapshots"][key]:
                    runtime_unchanged = False
            source_unchanged = isolated.tree_snapshot(source) == source_before
            if not runtime_unchanged or not source_unchanged:
                raise acceptance.RunnerError(
                    "CK3 rewrote a runtime tree or the supplied source"
                )
        except BaseException as error:
            result = "RED"
            reason = str(error) or type(error).__name__
            error_reason = f"{error_reason}; {reason}" if error_reason else reason

    actual_language = configured_language(userdir / "pdx_settings.txt")
    if actual_language != language.key:
        result = "RED"
        reason = (
            f"CK3 settings language drifted: {actual_language!r} != {language.key!r}"
        )
        error_reason = f"{error_reason}; {reason}" if error_reason else reason

    userdir_removed = False
    if result == "GREEN" and not keep_userdir:
        try:
            shutil.rmtree(userdir)
            userdir_removed = not userdir.exists()
            if not userdir_removed:
                raise OSError(f"userdir still exists: {userdir}")
        except Exception as error:
            result = "RED"
            reason = f"userdir cleanup failed: {error}"
            error_reason = f"{error_reason}; {reason}" if error_reason else reason
    elif userdir.exists():
        log(f"{language.key}: retained userdir at {userdir}")

    report = {
        "schema_version": 1,
        "language": language.key,
        "result": result,
        "error_reason": error_reason,
        "started_at_utc": started_at,
        "duration_seconds": round(time.perf_counter() - started, 3),
        "game_version": game_version,
        "ck3_executable_before_sha256": executable_before,
        "ck3_executable_after_sha256": executable_after,
        "debug_mode": False,
        "fresh_process": True,
        "isolated_userdir": True,
        "configured_language_after_run": actual_language,
        "enabled_mods": bootstrap["enabled_mods"],
        "verified_mount_order": mount_order,
        "runtime_tree_before_sha256": bootstrap["tree_sha256"],
        "runtime_tree_after_sha256": runtime_after,
        "runtime_trees_unchanged": runtime_unchanged,
        "source_tree_unchanged": source_unchanged,
        "fixture_markers": stream.lines,
        "project_diagnostics": list(dict.fromkeys(diagnostics)),
        "surface_evidence": evidence,
        "open_kaishek_preflight": OPEN_KAISHEK_PREFLIGHT_RESULT,
        "isolated_userdir_path": str(userdir),
        "userdir_removed_after_run": userdir_removed,
        "process_watchdog_pid": watchdog_pid,
        "environment": {
            "platform": platform.platform(),
            "python": sys.version.split()[0],
            "desktop": (
                f"{acceptance.pyautogui.size().width}x"
                f"{acceptance.pyautogui.size().height}"
            ),
        },
    }
    write_json(artifacts / "report.json", report)
    return report


def preflight(
    source: Path,
    workshop_item_id: str | None,
    manifest: Path | None,
) -> dict[str, dict[str, str]]:
    global OPEN_KAISHEK_PREFLIGHT_RESULT
    # The checked-in fixture is the smallest deterministic parser slice for
    # this localization runner.  Run it before desktop inspection or CK3
    # launch; an absent/unsupported accelerator remains advisory.
    OPEN_KAISHEK_PREFLIGHT_RESULT = acceptance.run_open_kaishek_preflight(
        root=FIXTURE_SOURCE,
        profile="ck3-1.19.0.6",
        fixture="none",
        scope="run_ox_here_loc_smoke.fixture",
    )
    log(
        "open_kaishek preflight: "
        f"{OPEN_KAISHEK_PREFLIGHT_RESULT.get('result', 'FAILED')} "
        f"({OPEN_KAISHEK_PREFLIGHT_RESULT.get('reason', 'unknown')})"
    )
    errors = fixture_source_errors()
    errors.extend(product_source_errors(source, workshop_item_id))
    if os.name != "nt":
        errors.append("Ox Here localization smoke requires Windows")
    if os.environ.get("GITHUB_ACTIONS") == "true":
        errors.append("CK3 live localization smoke is forbidden on GitHub runners")
    if acceptance.ck3_is_running():
        errors.append("ck3.exe is already running")
    if not acceptance.CK3_EXE.is_file():
        errors.append(f"CK3 executable missing: {acceptance.CK3_EXE}")
    else:
        try:
            version = isolated.installed_game_version()
            if version != EXPECTED_GAME_VERSION:
                errors.append(
                    f"CK3 version is {version}, expected {EXPECTED_GAME_VERSION}"
                )
        except acceptance.RunnerError as error:
            errors.append(str(error))
    if acceptance._ocr is None:
        errors.append("RapidOCR is unavailable; use tools/.venv")
    width, height = acceptance.pyautogui.size()
    if (width, height) != (2560, 1440):
        errors.append(
            f"localization smoke geometry requires 2560x1440: {width}x{height}"
        )
    if workshop_item_id is not None and manifest is None:
        errors.append(
            "Workshop localization smoke requires a verified formal manifest"
        )
    if manifest is not None:
        if workshop_item_id is None:
            errors.append("--manifest is only valid with --workshop-cache")
        else:
            try:
                build_ox_here_release.verify_manifest(
                    source, manifest, workshop_cache=True
                )
            except (OSError, ValueError) as error:
                errors.append(f"Workshop manifest verification failed: {error}")
    if errors:
        raise acceptance.RunnerError(
            "localization smoke preflight failed:\n  " + "\n  ".join(errors)
        )
    matrix = localization_matrix(source)
    log(
        f"preflight passed: source={source}, CK3={EXPECTED_GAME_VERSION}, "
        f"desktop={width}x{height}, languages={len(matrix)}"
    )
    return matrix


def main(
    workshop_cache: str | None = None,
    manifest_path: str | None = None,
    selected_language: str = "all",
    artifacts_dir: str | None = None,
    keep_userdirs: bool = False,
    preflight_only: bool = False,
) -> int:
    global OPEN_KAISHEK_PREFLIGHT_RESULT
    OPEN_KAISHEK_PREFLIGHT_RESULT = None
    validate_mode_arguments(workshop_cache, manifest_path)
    steam_root = terminal.steam_userdata_root()
    source = (
        Path(workshop_cache).expanduser().resolve()
        if workshop_cache
        else CANONICAL_SOURCE.resolve()
    )
    workshop_item_id = (
        validate_workshop_source(source, steam_root) if workshop_cache else None
    )
    manifest = (
        Path(manifest_path).expanduser().resolve() if manifest_path else None
    )
    localizations = preflight(source, workshop_item_id, manifest)
    if preflight_only:
        print("OX HERE LOCALIZATION SMOKE PREFLIGHT: GREEN")
        return 0
    if selected_language != "all" and selected_language not in LANGUAGE_BY_KEY:
        raise acceptance.RunnerError(
            f"unsupported language selection: {selected_language}"
        )
    if artifacts_dir:
        artifacts = Path(artifacts_dir).expanduser().resolve()
        if artifacts.exists():
            raise acceptance.RunnerError(
                f"artifact directory already exists: {artifacts}"
            )
        if not artifacts.parent.is_dir():
            raise acceptance.RunnerError(
                f"artifact parent does not exist: {artifacts.parent}"
            )
    else:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        artifacts = Path(tempfile.gettempdir()) / (
            f"oxls_{stamp}_{uuid.uuid4().hex[:8]}"
        )
    userdirs = artifacts.with_name(artifacts.name + "_userdirs")
    workshop_roots = isolated.steam_workshop_app_roots(steam_root)
    isolated.registered_workshop_targets(workshop_roots)
    isolated.ensure_test_paths_safe(
        (artifacts, userdirs), steam_root, workshop_roots
    )
    protected_before = isolated.protected_snapshot(steam_root)
    source_before = isolated.tree_snapshot(source)
    artifacts.mkdir()
    userdirs.mkdir()
    chosen = (
        LANGUAGES
        if selected_language == "all"
        else (LANGUAGE_BY_KEY[selected_language],)
    )
    reports: list[dict[str, object]] = []
    result = "RED"
    error_reason = None
    protected_unchanged = False
    quiet_period_completed = False
    started = time.perf_counter()
    started_at = datetime.now(timezone.utc).isoformat()
    try:
        for spec in chosen:
            report = run_cell(
                spec,
                localizations[spec.key],
                artifacts / "cells" / spec.key,
                userdirs / spec.key,
                source,
                workshop_item_id,
                keep_userdirs,
            )
            reports.append(report)
            isolated.verify_protected_storage(
                protected_before, steam_root, quiet_seconds=0
            )
            if report["result"] != "GREEN":
                error_reason = f"{spec.key}: {report['error_reason']}"
                break
        else:
            isolated.verify_protected_storage(
                protected_before,
                steam_root,
                quiet_seconds=POSTFLIGHT_STABILITY_SECONDS,
            )
            protected_unchanged = True
            quiet_period_completed = True
            if isolated.tree_snapshot(source) != source_before:
                raise acceptance.RunnerError(
                    "supplied product source changed during the matrix"
                )
            result = "GREEN"
    except BaseException as error:
        error_reason = str(error) or type(error).__name__
        log(f"matrix FATAL {error}")
        if isinstance(error, Exception) and not isinstance(
            error, acceptance.RunnerError
        ):
            traceback.print_exc()
    finally:
        try:
            isolated.verify_protected_storage(
                protected_before, steam_root, quiet_seconds=0
            )
            protected_unchanged = True
        except BaseException as error:
            result = "RED"
            protected_unchanged = False
            reason = str(error) or type(error).__name__
            error_reason = f"{error_reason}; {reason}" if error_reason else reason
        if result == "GREEN" and not keep_userdirs:
            try:
                shutil.rmtree(userdirs)
            except OSError as error:
                result = "RED"
                reason = f"userdir root cleanup failed: {error}"
                error_reason = f"{error_reason}; {reason}" if error_reason else reason

    report = {
        "schema_version": 1,
        "result": result,
        "error_reason": error_reason,
        "started_at_utc": started_at,
        "duration_seconds": round(time.perf_counter() - started, 3),
        "product_source": str(source),
        "source_kind": (
            "verified_workshop_cache" if workshop_cache else "canonical_source"
        ),
        "workshop_item_id": workshop_item_id,
        "manifest": str(manifest) if manifest else None,
        "manifest_sha256": (
            isolated.sha256_file(manifest) if manifest is not None else None
        ),
        "manifest_verified": bool(workshop_cache and manifest is not None),
        "selected_language": selected_language,
        "expected_languages": [spec.key for spec in chosen],
        "cells": reports,
        "open_kaishek_preflight": OPEN_KAISHEK_PREFLIGHT_RESULT,
        "fresh_process_per_language": True,
        "protected_storage_unchanged": protected_unchanged,
        "postflight_quiet_seconds": (
            POSTFLIGHT_STABILITY_SECONDS if quiet_period_completed else 0
        ),
        "source_tree_unchanged": isolated.tree_snapshot(source) == source_before,
    }
    write_json(artifacts / "report.json", report)
    print("\n===== OX HERE LOCALIZATION SMOKE =====")
    for cell in reports:
        print(f"{cell['language']:<20} {cell['result']}")
    print(
        "protected storage    "
        + ("UNCHANGED" if protected_unchanged else "UNPROVEN")
    )
    print(f"artifacts            {artifacts}")
    print(f"RESULT: {result}")
    return 0 if result == "GREEN" else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--workshop-cache",
        help=(
            "exact numeric CK3 Workshop item leaf; copied and descriptor-normalized "
            "inside each disposable cell"
        ),
    )
    parser.add_argument(
        "--manifest",
        help="required formal manifest used to verify --workshop-cache",
    )
    parser.add_argument(
        "--language",
        choices=("all", *LANGUAGE_BY_KEY),
        default="all",
    )
    parser.add_argument("--artifacts-dir")
    parser.add_argument("--keep-userdirs", action="store_true")
    parser.add_argument("--preflight", action="store_true", help="do not launch CK3")
    return parser


if __name__ == "__main__":
    arguments = build_parser().parse_args()
    try:
        raise SystemExit(
            main(
                workshop_cache=arguments.workshop_cache,
                manifest_path=arguments.manifest,
                selected_language=arguments.language,
                artifacts_dir=arguments.artifacts_dir,
                keep_userdirs=arguments.keep_userdirs,
                preflight_only=arguments.preflight,
            )
        )
    except acceptance.RunnerError as error:
        print(f"OX HERE LOCALIZATION SMOKE FAILED: {error}", file=sys.stderr)
        raise SystemExit(1)
