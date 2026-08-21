#!/usr/bin/env python3
"""Run isolated CK3 acceptance for Vivhite alone and both product load orders."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import html
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

import build_release
import build_vivhite_release
import run_acceptance as acceptance
import run_terminal_acceptance as terminal


ROOT = Path(__file__).resolve().parent.parent
FIXTURE_SOURCE = ROOT / "tools" / "fixtures" / "vivhite_acceptance"
STEAM_APP_ID = "1158310"
EXPECTED_GAME_VERSION = "1.19.0.6"
POSTFLIGHT_STABILITY_SECONDS = 5
BOOT_TIMEOUT_S = 300
DUAL_ONLY_BEGIN = "# ERVA_DUAL_ONLY_BEGIN"
DUAL_ONLY_END = "# ERVA_DUAL_ONLY_END"
PROJECT_TOKENS = (
    "ervc", "erva", "xar", "xa_", "vivhite", "eternal_recurrence_vivhite_courtier",
    "xenoamess_s_eternal_recurrence",
)
DUPLICATE_PATTERNS = (
    "there is more than one", "using most recent", "duplicate definition",
    "duplicate key", "already defined", "already registered",
)
ALLOWED_PROJECT_DIAGNOSTICS = (
    re.compile(
        r"Variable 'xa_curse_[ab]_rarity' is set but is never used\. "
        r"Note that use in localization doesn't count"
    ),
)


@dataclass(frozen=True)
class ProductSpec:
    key: str
    outer_name: str
    decision_title: str
    group_title: str
    modal_title: str
    confirm_label: str = "翻开典造契页"


@dataclass(frozen=True)
class ScenarioSpec:
    key: str
    product_order: tuple[str, ...]
    fixture_mode: str
    dual: bool


ORIGINAL = ProductSpec(
    key="original",
    outer_name="xar_original_acceptance.mod",
    decision_title="典造琉焰廷臣",
    group_title="琉焰卿的永恒轮回",
    modal_title="待价而塑的灵魂",
)
VIVHITE = ProductSpec(
    key="vivhite",
    outer_name="ervc_vivhite_acceptance.mod",
    decision_title="典造琉焰廷臣·白绮特供版",
    group_title="琉焰卿的永恒轮回：典造琉焰廷臣·白绮特供版",
    modal_title="待价而塑的灵魂",
)
PRODUCTS = {product.key: product for product in (ORIGINAL, VIVHITE)}
FIXTURE_OUTER_NAME = "erva_acceptance_fixture.mod"

SCENARIOS = {
    scenario.key: scenario
    for scenario in (
        ScenarioSpec(
            "vivhite-alone", ("vivhite",), "erva_acceptance_standalone", False),
        ScenarioSpec(
            "original-then-vivhite",
            ("original", "vivhite"),
            "erva_acceptance_dual",
            True,
        ),
        ScenarioSpec(
            "vivhite-then-original",
            ("vivhite", "original"),
            "erva_acceptance_dual",
            True,
        ),
    )
}

STANDALONE_MARKERS = (
    "ERVA: TEST BEGIN standalone",
    "ERVA: TEST PASS ai_fixture_ready",
    "ERVA: TEST PASS ai_guard",
    "ERVA: TEST PASS cancel_zero_side_effect",
    "ERVA: TEST PASS insufficient_119_blocked",
    "ERVA: TEST PASS default_120_one_delivery_one_charge",
    "ERVA: TEST PASS selected_faith_aluk",
    "ERVA: TEST PASS custom_348_ready",
    "ERVA: TEST PASS custom_configuration_retained",
    "ERVA: TEST PASS custom_configuration_reopened",
    "ERVA: TEST PASS custom_348_one_delivery_one_charge",
    "ERVA: TEST DONE standalone",
)
DUAL_MARKERS = (
    "ERVA: TEST BEGIN dual",
    "ERVA: TEST PASS ai_fixture_ready",
    "ERVA: TEST PASS ai_guard",
    "ERVA: TEST PASS ervc_custom_348_staged",
    "ERVA: TEST PASS ervc_configuration_retained",
    "ERVA: TEST PASS xar_default_isolated_from_ervc",
    "ERVA: TEST PASS xar_configuration_retained",
    "ERVA: TEST PASS ervc_state_retained_after_xar",
    "ERVA: TEST PASS ervc_348_one_delivery_one_charge",
    "ERVA: TEST PASS xar_state_retained_after_ervc",
    "ERVA: TEST PASS xar_120_one_delivery_one_charge",
    "ERVA: TEST DONE dual",
)


def log(message: str) -> None:
    acceptance.log(f"vivhite: {message}")


def write_text_atomic(path: Path, text: str, encoding: str = "utf-8") -> None:
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(text, encoding=encoding)
    os.replace(temporary, path)


def write_json_atomic(path: Path, payload: dict[str, object]) -> None:
    write_text_atomic(
        path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def tree_snapshot(root: Path) -> dict[str, dict[str, object]]:
    return {
        path.relative_to(root).as_posix(): {
            "size": path.stat().st_size,
            "sha256": sha256_file(path),
        }
        for path in sorted(item for item in root.rglob("*") if item.is_file())
    }


def snapshot_digest(snapshot: object) -> str:
    payload = json.dumps(
        snapshot, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("ascii")
    return hashlib.sha256(payload).hexdigest()


def is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def parse_descriptor_path(path: Path) -> Path:
    try:
        text = path.read_text(encoding="utf-8-sig")
    except OSError as error:
        raise acceptance.RunnerError(f"cannot read mod descriptor {path}: {error}") from error
    matches = re.findall(r'(?m)^\s*path\s*=\s*"([^"\r\n]+)"\s*$', text)
    if len(matches) != 1:
        raise acceptance.RunnerError(
            f"mod descriptor must contain exactly one path field: {path}"
        )
    target = Path(os.path.expandvars(matches[0])).expanduser()
    if not target.is_absolute():
        raise acceptance.RunnerError(
            f"mod descriptor path must be absolute: {path} -> {target}"
        )
    return target.resolve()


def steam_workshop_app_roots(steam_root: Path) -> list[Path]:
    steam_install = steam_root.resolve().parent
    library_file = steam_install / "steamapps" / "libraryfolders.vdf"
    try:
        text = library_file.read_text(encoding="utf-8-sig", errors="strict")
    except OSError as error:
        raise acceptance.RunnerError(
            f"cannot read Steam library registry {library_file}: {error}"
        ) from error
    libraries = [steam_install]
    for raw in re.findall(r'(?im)^\s*"path"\s+"([^"]+)"', text):
        libraries.append(Path(raw.replace("\\\\", "\\")).expanduser().resolve())
    roots = {
        (library / "steamapps" / "workshop" / "content" / STEAM_APP_ID).resolve()
        for library in libraries
    }
    return sorted(roots, key=lambda path: path.as_posix().casefold())


def validate_workshop_target(target: Path, app_roots: list[Path]) -> None:
    item_id = target.name
    if not item_id.isascii() or not item_id.isdigit() or item_id == "0":
        raise acceptance.RunnerError(f"invalid CK3 Workshop target item ID: {target}")
    if not any(target.parent == root for root in app_roots):
        raise acceptance.RunnerError(
            f"registered CK3 UGC target is outside Steam Workshop app roots: {target}"
        )


def registered_workshop_targets(app_roots: list[Path]) -> list[Path]:
    mod_dir = acceptance.ORIGINAL_USER_DIR / "mod"
    descriptors = sorted(mod_dir.glob("ugc_*.mod")) if mod_dir.is_dir() else []
    targets: list[Path] = []
    for descriptor in descriptors:
        if descriptor.is_file():
            target = parse_descriptor_path(descriptor)
            validate_workshop_target(target, app_roots)
            targets.append(target)
    return targets


def real_workshop_snapshot(steam_root: Path) -> dict[str, object]:
    mod_dir = acceptance.ORIGINAL_USER_DIR / "mod"
    descriptors = sorted(mod_dir.glob("ugc_*.mod")) if mod_dir.is_dir() else []
    files: dict[str, dict[str, object]] = {}
    targets: list[str] = []
    app_roots = steam_workshop_app_roots(steam_root)
    for descriptor in descriptors:
        if descriptor.is_file():
            files[f"descriptor:{descriptor.name}"] = terminal.file_digest(descriptor)
        target = parse_descriptor_path(descriptor)
        validate_workshop_target(target, app_roots)
        targets.append(str(target))
        if not target.is_dir():
            continue
        for item in sorted(path for path in target.rglob("*") if path.is_file()):
            relative = item.relative_to(target).as_posix()
            stat = item.stat()
            files[f"target:{descriptor.name}/{relative}"] = {
                "size": stat.st_size,
                "mtime_ns": stat.st_mtime_ns,
            }
    return {"registered_targets": targets, "files": files}


def ensure_test_paths_safe(
    paths: tuple[Path, ...], steam_root: Path, workshop_roots: list[Path]
) -> None:
    protected_roots = [
        ("repository", ROOT.resolve()),
        ("real CK3 profile", acceptance.ORIGINAL_USER_DIR.resolve()),
        ("Steam userdata", steam_root.resolve()),
    ]
    protected_roots.extend(
        ("Steam CK3 Workshop app root", root) for root in workshop_roots
    )
    for path in paths:
        candidate = path.resolve()
        for label, protected in protected_roots:
            if (
                candidate == protected
                or is_relative_to(candidate, protected)
                or is_relative_to(protected, candidate)
            ):
                raise acceptance.RunnerError(
                    f"acceptance path overlaps {label}: {candidate} <-> {protected}"
                )


def protected_snapshot(steam_root: Path) -> dict[str, object]:
    return {
        "real_profile": terminal.real_profile_snapshot(),
        "steam_cloud": terminal.steam_cloud_snapshot(steam_root),
        "workshop": real_workshop_snapshot(steam_root),
    }


def verify_protected_storage(
    baseline: dict[str, object], steam_root: Path, quiet_seconds: int = 0
) -> dict[str, object]:
    current = protected_snapshot(steam_root)
    if current != baseline:
        changed = [key for key in baseline if baseline[key] != current[key]]
        raise acceptance.RunnerError(
            "protected storage changed during Vivhite acceptance: "
            + ", ".join(changed)
        )
    if quiet_seconds <= 0:
        return current

    # Start the quiet interval only after a complete snapshot. A final complete
    # traversal then proves the baseline still holds after the full interval.
    time.sleep(quiet_seconds)
    current = protected_snapshot(steam_root)
    if current != baseline:
        changed = [key for key in baseline if baseline[key] != current[key]]
        raise acceptance.RunnerError(
            "protected storage changed during Vivhite acceptance postflight: "
            + ", ".join(changed)
        )
    return current


def render_presets(scenario: ScenarioSpec) -> str:
    settings = [setting for _, setting in acceptance.declared_vanilla_rule_defaults()]
    settings.append(scenario.fixture_mode)
    if scenario.dual:
        settings.extend(("xar_off", "xar_inherit_100", "xar_score_growth"))
    if len(settings) != len(set(settings)):
        raise acceptance.RunnerError(
            f"duplicate game-rule setting in {scenario.key}: {settings}"
        )
    return (
        'game_rules_preset={\n'
        '\tname="LastAppliedRules"\n'
        f'\tsetting={{ {" ".join(settings)} }}\n'
        '\tironman=no\n'
        '}\n'
    )


def write_outer_descriptor(inner: Path, outer: Path, target: Path) -> None:
    text = inner.read_text(encoding="utf-8-sig")
    if "remote_file_id" in text:
        raise acceptance.RunnerError(f"inner descriptor contains remote_file_id: {inner}")
    rendered = text.rstrip("\r\n") + f'\npath="{target.as_posix()}"\n'
    outer.write_bytes(rendered.encode("utf-8-sig"))


def render_fixture_tree(target: Path, include_dual: bool) -> None:
    if target.exists():
        shutil.rmtree(target)
    for source in sorted(path for path in FIXTURE_SOURCE.rglob("*") if path.is_file()):
        relative = source.relative_to(FIXTURE_SOURCE)
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        if source.suffix.lower() not in {".txt", ".gui", ".yml"}:
            shutil.copy2(source, destination)
            continue
        data = source.read_bytes()
        had_bom = data.startswith(b"\xef\xbb\xbf")
        text = data.decode("utf-8-sig")
        output: list[str] = []
        inside_dual = False
        begin_count = 0
        end_count = 0
        for line in text.splitlines(keepends=True):
            marker = line.strip()
            if marker == DUAL_ONLY_BEGIN:
                if inside_dual:
                    raise acceptance.RunnerError(
                        f"nested dual-only marker: {relative.as_posix()}"
                    )
                inside_dual = True
                begin_count += 1
                continue
            if marker == DUAL_ONLY_END:
                if not inside_dual:
                    raise acceptance.RunnerError(
                        f"unmatched dual-only end: {relative.as_posix()}"
                    )
                inside_dual = False
                end_count += 1
                continue
            if include_dual or not inside_dual:
                output.append(line)
        if inside_dual or begin_count != end_count:
            raise acceptance.RunnerError(
                f"unbalanced dual-only markers: {relative.as_posix()}"
            )
        rendered = "".join(output).encode("utf-8")
        destination.write_bytes((b"\xef\xbb\xbf" if had_bom else b"") + rendered)


def bootstrap_userdir(userdir: Path, scenario: ScenarioSpec) -> dict[str, object]:
    mod_dir = userdir / "mod"
    content_dir = userdir / "mod-content"
    for path in (
        mod_dir,
        content_dir,
        userdir / "logs",
        userdir / "save games",
        userdir / "player" / "game_rules",
    ):
        path.mkdir(parents=True, exist_ok=True)

    revision = build_vivhite_release.git_sha()
    if not revision:
        raise acceptance.RunnerError("Git revision unavailable")

    targets: dict[str, Path] = {}
    manifests: dict[str, dict[str, object]] = {}
    for key in scenario.product_order:
        target = content_dir / key
        if key == "vivhite":
            _, _, _, manifest = build_vivhite_release.build_release(
                build_vivhite_release.DEFAULT_SOURCE, target, revision=revision
            )
        else:
            _, _, _, manifest = build_release.build_release(
                build_release.DEFAULT_SOURCE, target, revision=revision
            )
        targets[key] = target
        manifests[key] = manifest

    fixture_target = content_dir / "fixture"
    render_fixture_tree(fixture_target, include_dual=scenario.dual)
    targets["fixture"] = fixture_target

    enabled_mods = []
    for key in scenario.product_order:
        product = PRODUCTS[key]
        outer = mod_dir / product.outer_name
        write_outer_descriptor(targets[key] / "descriptor.mod", outer, targets[key])
        enabled_mods.append(f"mod/{product.outer_name}")
    fixture_outer = mod_dir / FIXTURE_OUTER_NAME
    write_outer_descriptor(
        fixture_target / "descriptor.mod", fixture_outer, fixture_target
    )
    enabled_mods.append(f"mod/{FIXTURE_OUTER_NAME}")

    for outer_name in enabled_mods:
        target = parse_descriptor_path(userdir / outer_name)
        if target is None or not is_relative_to(target, userdir):
            raise acceptance.RunnerError(
                f"outer descriptor escapes disposable userdir: {outer_name} -> {target}"
            )

    (userdir / "tutorial.txt").write_text(
        'last_lesson_chain="reactive_advice"\ncompleted_lessons={\n}\n',
        encoding="utf-8",
        newline="\n",
    )
    (userdir / "player" / "game_rules" / "presets.txt").write_text(
        render_presets(scenario), encoding="utf-8", newline="\n"
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
        terminal.render_settings(), encoding="utf-8", newline="\n"
    )

    snapshots = {key: tree_snapshot(path) for key, path in targets.items()}
    return {
        "targets": targets,
        "tree_snapshots": snapshots,
        "tree_sha256": {
            key: snapshot_digest(snapshot) for key, snapshot in snapshots.items()
        },
        "enabled_mods": enabled_mods,
        "manifests": manifests,
    }


def verify_runtime_load_order(
    userdir: Path, scenario: ScenarioSpec, bootstrap: dict[str, object]
) -> list[str]:
    debug_log = userdir / "logs" / "debug.log"
    try:
        text = debug_log.read_text(encoding="utf-8", errors="ignore")
    except OSError as error:
        raise acceptance.RunnerError(
            f"cannot verify CK3 runtime load order: {error}"
        ) from error

    enabled = re.findall(r"(?m)^[^\r\n|]+\|(mod/[^\r\n|]+)\|Enabled\s*$", text)
    expected_enabled = list(bootstrap["enabled_mods"])
    if len(enabled) != len(expected_enabled) or set(enabled) != set(expected_enabled):
        raise acceptance.RunnerError(
            "CK3 enabled-mod inventory differs from the isolated profile: "
            f"actual={enabled}, expected={expected_enabled}"
        )

    content_root = (userdir / "mod-content").resolve()
    mounted: list[Path] = []
    for raw in re.findall(r"(?m)Mounted Data:\s*([^\r\n]+?)\s*$", text):
        path = Path(raw.strip()).resolve()
        if is_relative_to(path, content_root):
            mounted.append(path)
    expected_keys = (*scenario.product_order, "fixture")
    expected_mounts = [Path(bootstrap["targets"][key]).resolve() for key in expected_keys]
    if mounted != expected_mounts:
        raise acceptance.RunnerError(
            "CK3 mounted isolated products in the wrong order: "
            f"actual={[path.as_posix() for path in mounted]}, "
            f"expected={[path.as_posix() for path in expected_mounts]}"
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
                    f"cannot finalize fixture marker log {self.path}: {error}"
                ) from error
            data = b""

        payload = self.pending + data
        if final:
            complete = payload
            self.pending = b""
        else:
            boundary = max(payload.rfind(b"\n"), payload.rfind(b"\r"))
            if boundary < 0:
                self.pending = payload
                return
            complete = payload[:boundary + 1]
            self.pending = payload[boundary + 1:]
        text = complete.decode("utf-8", errors="ignore")
        for line in text.splitlines():
            if "ERVA:" in line:
                stripped = line.strip()
                self.lines.append(stripped)
                log(stripped)
        failures = [line for line in self.lines if "ERVA: TEST FAIL" in line]
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

    def validate(self, required: tuple[str, ...], final: bool = False) -> None:
        self.pump(final=final)
        for marker in required:
            count = sum(marker in line for line in self.lines)
            if count != 1:
                raise acceptance.RunnerError(
                    f"fixture marker count for {marker!r} is {count}, expected 1"
                )
        failures = [line for line in self.lines if "ERVA: TEST FAIL" in line]
        if failures:
            raise acceptance.RunnerError(
                f"fixture emitted {len(failures)} failure marker(s)"
            )


def diagnostic_lines(path: Path) -> tuple[list[str], list[str]]:
    try:
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except OSError:
        return [], []
    selected: list[str] = []
    for index, line in enumerate(lines):
        lowered = line.lower()
        context = " ".join(lines[max(0, index - 2):index + 3]).lower()
        attributed = any(token in lowered for token in PROJECT_TOKENS)
        duplicate = any(pattern in lowered for pattern in DUPLICATE_PATTERNS)
        if attributed or (duplicate and any(token in context for token in PROJECT_TOKENS)):
            selected.append(line.strip())
    selected = list(dict.fromkeys(line for line in selected if line))
    allowed = [
        line
        for line in selected
        if any(pattern.search(line) for pattern in ALLOWED_PROJECT_DIAGNOSTICS)
    ]
    blocking = [line for line in selected if line not in allowed]
    return blocking, allowed


def scan_project_logs(
    userdir: Path, artifacts: Path, stem: str
) -> tuple[list[str], list[str]]:
    diagnostics: list[str] = []
    allowed: list[str] = []
    for name in ("error.log", "gui_warnings.log", "database_conflicts.log"):
        path = userdir / "logs" / name
        blocking_lines, allowed_lines = diagnostic_lines(path)
        diagnostics.extend(f"{name}: {line}" for line in blocking_lines)
        allowed.extend(f"{name}: {line}" for line in allowed_lines)
        if path.is_file():
            shutil.copy2(path, artifacts / f"{stem}_{name}")
    return diagnostics, allowed


def collect_project_logs(
    userdir: Path,
    artifacts: Path,
    stem: str,
    diagnostics: list[str],
    allowed_diagnostics: list[str],
) -> None:
    blocking, allowed = scan_project_logs(userdir, artifacts, stem)
    diagnostics.extend(blocking)
    allowed_diagnostics.extend(allowed)
    if blocking:
        raise acceptance.RunnerError(
            f"{len(blocking)} project diagnostic(s) at {stem}: {blocking[-1]}"
        )


def dismiss_external_main_menu_popup(artifacts: Path) -> None:
    """Close OS/vendor notifications before lobby navigation takes focus."""
    region = (0.80, 0.58, 1.00, 0.96)
    dismissed = False
    for attempt in range(1, 4):
        image = acceptance.ImageGrab.grab()
        point = None
        for label in ("关闭", "忽略"):
            point = acceptance.find_ocr_text(image, label, region, contains=True)
            if point is not None:
                break
        if point is None:
            if not dismissed:
                return
            break
        image.save(artifacts / f"02_external_popup_{attempt}.png")
        acceptance.pyautogui.click(*point)
        dismissed = True
        log(f"dismissed external main-menu popup at {point}")
        time.sleep(2)
    image = acceptance.ImageGrab.grab()
    if any(
        acceptance.find_ocr_text(image, label, region, contains=True)
        for label in ("关闭", "忽略")
    ):
        raise acceptance.RunnerError("external main-menu popup remained after 3 closes")

    # The notification host can retain foreground briefly after its pixels vanish.
    width, height = acceptance.pyautogui.size()
    acceptance.pyautogui.click(int(width * 0.50), int(height * 0.15))
    time.sleep(0.8)
    acceptance.focus_ck3()


def wait_for_gameplay_hud(artifacts: Path, timeout_s: int = 180) -> None:
    deadline = time.time() + timeout_s
    last_image = None
    while time.time() < deadline:
        acceptance.focus_ck3()
        last_image = acceptance.ImageGrab.grab()
        if acceptance.read_hud_game_date(last_image) is not None:
            last_image.save(artifacts / "04_gameplay_hud.png")
            log("gameplay HUD and date are visible")
            return
        time.sleep(acceptance.POLL_INTERVAL_S)
    if last_image is not None:
        last_image.save(artifacts / "timeout_04_gameplay_hud.png")
    raise acceptance.RunnerError("gameplay HUD did not appear after lobby start")


def ensure_decisions_panel(artifacts: Path, stem: str) -> None:
    acceptance.focus_ck3()
    time.sleep(0.8)
    width, height = acceptance.pyautogui.size()
    image = acceptance.ImageGrab.grab()
    header_region = (0.55, 0.00, 0.90, 0.13)
    if acceptance.find_ocr_text(image, "决议", header_region, contains=True) is None:
        tab = (int(width * 0.987), int(height * 0.367))
        acceptance.pyautogui.moveTo(*tab, duration=0.2)
        acceptance.wait_for_ocr_text(
            "决议",
            acceptance.FULL_SCREEN_REGION,
            10,
            artifacts,
            f"{stem}_decisions_tooltip.png",
            contains=True,
            stable_hits=1,
        )
        acceptance.deliberate_click(tab, "native Decisions HUD tab")
    acceptance.pyautogui.moveTo(int(width * 0.90), int(height * 0.70))
    acceptance.pyautogui.scroll(20)
    time.sleep(0.6)


def open_decision_detail(
    title: str, confirm_label: str, artifacts: Path, stem: str, contains: bool = False
) -> tuple[int, int]:
    ensure_decisions_panel(artifacts, stem)
    row = acceptance.wait_for_ocr_text(
        title,
        acceptance.FULL_SCREEN_REGION,
        15,
        artifacts,
        f"{stem}_decision.png",
        contains=contains,
        stable_hits=1,
    )
    width, _ = acceptance.pyautogui.size()
    acceptance.deliberate_click(
        (int(width * 0.90), row[1]), f"native decision row {title}"
    )
    return acceptance.wait_for_ocr_text(
        confirm_label,
        acceptance.FULL_SCREEN_REGION,
        15,
        artifacts,
        f"{stem}_confirm.png",
        contains=True,
        stable_hits=1,
    )


def open_product_creator(product: ProductSpec, artifacts: Path, stem: str) -> None:
    confirm = open_decision_detail(
        product.decision_title,
        product.confirm_label,
        artifacts,
        stem,
        contains=False,
    )
    acceptance.click_until_ocr_appears(
        confirm,
        f"{product.key} creator decision",
        product.modal_title,
        acceptance.COURTIER_MODAL_REGION,
        artifacts,
        f"{stem}_modal.png",
        attempts=1,
        timeout_s=10,
    )


def initialize_fixture(
    scenario: ScenarioSpec, stream: MarkerStream, artifacts: Path
) -> None:
    confirm = open_decision_detail(
        "开始白绮独立版验收",
        "初始化验收",
        artifacts,
        "05_fixture_initialize",
    )
    acceptance.deliberate_click(confirm, "fixture initialization decision")
    stream.wait(f"ERVA: TEST BEGIN {'dual' if scenario.dual else 'standalone'}", 15)
    stream.wait("ERVA: TEST PASS ai_fixture_ready", 15)
    stream.wait("ERVA: TEST PASS ai_guard", 15)


def normalized(text: str) -> str:
    return re.sub(r"\s+", "", text).lower()


def assert_dual_decision_groups(artifacts: Path) -> None:
    ensure_decisions_panel(artifacts, "06_dual_groups")
    deadline = time.time() + 20
    last_items: list[dict[str, object]] = []
    while time.time() < deadline:
        image = acceptance.ImageGrab.grab()
        last_items = acceptance.ocr_box_results(image, acceptance.FULL_SCREEN_REGION)
        width, height = image.size
        panel_items = [
            item for item in last_items if int(item["center"][0]) > width * 0.65
        ]

        def unique_item(predicate):
            matches = [
                item
                for item in panel_items
                if predicate(normalized(str(item["text"])))
            ]
            return matches[0] if len(matches) == 1 else None

        original_group = unique_item(
            lambda text: text.startswith(normalized(ORIGINAL.group_title))
            and normalized("白绮特供版") not in text
        )
        vivhite_group = unique_item(
            lambda text: text.startswith(normalized(VIVHITE.group_title))
        )
        original_decision = unique_item(
            lambda text: text == normalized(ORIGINAL.decision_title)
        )
        vivhite_decision = unique_item(
            lambda text: text == normalized(VIVHITE.decision_title)
        )
        groups = [item for item in (original_group, vivhite_group) if item]

        def belongs_to(group, decision):
            if group is None or decision is None:
                return False
            group_y = int(group["center"][1])
            decision_y = int(decision["center"][1])
            if not 0 < decision_y - group_y < height * 0.08:
                return False
            return not any(
                group_y < int(other["center"][1]) < decision_y
                for other in groups
                if other is not group
            )

        if belongs_to(original_group, original_decision) and belongs_to(
            vivhite_group, vivhite_decision
        ):
            image.save(artifacts / "06_dual_groups.png")
            (artifacts / "06_dual_groups_ocr.json").write_text(
                json.dumps(last_items, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            log("PASS: both independent decision groups and creator rows rendered")
            return
        time.sleep(acceptance.POLL_INTERVAL_S)
    (artifacts / "timeout_06_dual_groups_ocr.json").write_text(
        json.dumps(last_items, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    raise acceptance.RunnerError("both product decision groups did not render together")


def modal_buttons(artifacts: Path, stem: str) -> tuple[tuple[int, int], tuple[int, int]]:
    cancel = acceptance.wait_for_ocr_text(
        "让此页继续空白",
        acceptance.COURTIER_MODAL_REGION,
        10,
        artifacts,
        f"{stem}_buttons.png",
        contains=True,
        stable_hits=1,
    )
    width, _ = acceptance.pyautogui.size()
    confirm = (cancel[0] + int(width * 0.125), cancel[1])
    return cancel, confirm


def click_and_wait(
    point: tuple[int, int], label: str, marker: str, stream: MarkerStream
) -> None:
    acceptance.deliberate_click(point, label)
    stream.wait(marker, 15)


def configure_ervc_custom(
    artifacts: Path, stem: str, verify_faith_tooltips: bool
) -> tuple[int, int]:
    acceptance.click_courtier_option("女性", artifacts, f"{stem}_female")
    width, height = acceptance.pyautogui.size()
    for x_ratio, y_ratio, label in (
        (0.533, 0.309, "age minus ten"),
        (0.805, 0.348, "diplomacy plus ten"),
        (0.805, 0.547, "prowess plus ten"),
    ):
        acceptance.deliberate_click(
            (int(width * x_ratio), int(height * y_ratio)),
            f"ERVC numeric {label}",
        )
        time.sleep(0.25)
    acceptance.wait_for_ocr_tokens(
        ("待价而塑的灵魂", "20", "16", "273"),
        ("ervc.cc", "xar.cc", "localize", "error"),
        acceptance.COURTIER_MODAL_REGION,
        12,
        artifacts,
        f"{stem}_numeric_profile",
    )

    acceptance.click_courtier_option("教育", artifacts, f"{stem}_education_tab")
    education = acceptance.wait_for_ocr_text(
        "阴谋家",
        acceptance.COURTIER_MODAL_REGION,
        12,
        artifacts,
        f"{stem}_education_grid.png",
        contains=True,
        stable_hits=1,
    )
    acceptance.deliberate_click(education, "ERVC education intrigue 1")
    acceptance.click_courtier_option("将才", artifacts, f"{stem}_commander_tab")
    acceptance.click_courtier_option("勤专家", artifacts, f"{stem}_logistician")
    acceptance.click_courtier_option(
        "军事工程师", artifacts, f"{stem}_military_engineer"
    )
    acceptance.click_courtier_option("血肉", artifacts, f"{stem}_physical_tab")
    acceptance.click_courtier_option("貌不扬", artifacts, f"{stem}_beauty_bad_1")
    acceptance.click_courtier_option("心性", artifacts, f"{stem}_personality_tab")
    acceptance.deliberate_click(
        (int(width * 0.215), int(height * 0.321)), "ERVC personality lustful"
    )
    time.sleep(0.35)
    acceptance.click_courtier_option("异质", artifacts, f"{stem}_other_tab")
    acceptance.deliberate_click(
        (int(width * 0.215), int(height * 0.321)), "ERVC other diplomat"
    )
    time.sleep(0.35)

    acceptance.deliberate_click(
        (int(width * 0.805), int(height * 0.215)), "ERVC origin tab"
    )
    time.sleep(0.5)
    acceptance.click_courtier_option(
        "归入我的宗族与家族", artifacts, f"{stem}_same_house", contains=False
    )
    selected_culture = acceptance.click_first_courtier_catalog_entry(
        (0.17, 0.42, 0.49, 0.72),
        artifacts,
        f"{stem}_culture",
        min_indent_px=50,
    )
    selected_faith = acceptance.click_first_courtier_catalog_entry(
        (0.51, 0.42, 0.84, 0.72),
        artifacts,
        f"{stem}_faith",
        click_x_ratio=0.52,
        click_y_offset=-20,
    )
    log(
        "selected ERVC origin rows: "
        f"culture={selected_culture!r}, faith={selected_faith!r}"
    )
    if "阿卢克古道" not in selected_faith:
        raise acceptance.RunnerError(
            f"selected faith must be Aluk for tooltip proof: {selected_faith!r}"
        )

    if verify_faith_tooltips:
        acceptance.click_courtier_option(
            "心性", artifacts, f"{stem}_selected_faith_personality"
        )
        diligent = acceptance.wait_for_ocr_text(
            "勤勉",
            acceptance.COURTIER_MODAL_REGION,
            12,
            artifacts,
            f"{stem}_diligent.png",
            contains=True,
            stable_hits=1,
        )
        acceptance.pyautogui.moveTo(diligent[0] - int(width * 0.025), diligent[1])
        time.sleep(1.8)
        acceptance.wait_for_ocr_tokens(
            ("阿卢克古道", "美德"),
            ("天主教", "ervc.cc", "xar.cc", "localize", "error"),
            acceptance.COURTIER_MODAL_REGION,
            12,
            artifacts,
            f"{stem}_selected_faith_virtue",
        )
        lazy = acceptance.wait_for_ocr_text(
            "懒惰",
            acceptance.COURTIER_MODAL_REGION,
            12,
            artifacts,
            f"{stem}_lazy.png",
            contains=True,
            stable_hits=1,
        )
        acceptance.pyautogui.moveTo(lazy[0] - int(width * 0.025), lazy[1])
        time.sleep(1.8)
        acceptance.wait_for_ocr_tokens(
            ("阿卢克古道", "罪恶"),
            ("天主教", "ervc.cc", "xar.cc", "localize", "error"),
            acceptance.COURTIER_MODAL_REGION,
            12,
            artifacts,
            f"{stem}_selected_faith_sin",
        )

    acceptance.deliberate_click(
        (int(width * 0.805), int(height * 0.215)), "ERVC return to origin tab"
    )
    acceptance.pyautogui.moveTo(int(width * 0.50), int(height * 0.255))
    time.sleep(0.5)
    acceptance.wait_for_ocr_tokens(
        ("待价而塑的灵魂", "348"),
        ("ervc.cc", "xar.cc", "localize", "error"),
        acceptance.COURTIER_MODAL_REGION,
        15,
        artifacts,
        f"{stem}_custom_render",
    )
    return modal_buttons(artifacts, stem)


def run_standalone(stream: MarkerStream, artifacts: Path) -> dict[str, object]:
    open_product_creator(VIVHITE, artifacts, "06_standalone_cancel")
    acceptance.wait_for_ocr_tokens(
        ("待价而塑的灵魂", "男性", "女性", "120", "1000"),
        ("ervc.cc", "xar.cc", "localize", "error"),
        acceptance.COURTIER_MODAL_REGION,
        15,
        artifacts,
        "06_standalone_initial_render",
    )
    cancel, _ = modal_buttons(artifacts, "06_standalone_cancel")
    click_and_wait(
        cancel,
        "ERVC initial cancel",
        "ERVA: TEST PASS cancel_zero_side_effect",
        stream,
    )

    open_product_creator(VIVHITE, artifacts, "07_standalone_poor")
    acceptance.wait_for_ocr_tokens(
        ("待价而塑的灵魂", "120", "119"),
        ("ervc.cc", "xar.cc", "localize", "error"),
        acceptance.COURTIER_MODAL_REGION,
        15,
        artifacts,
        "07_standalone_poor_render",
    )
    cancel, confirm = modal_buttons(artifacts, "07_standalone_poor")
    acceptance.deliberate_click(confirm, "disabled ERVC 119-gold confirm")
    acceptance.wait_for_ocr_text(
        "待价而塑的灵魂",
        acceptance.COURTIER_MODAL_REGION,
        4,
        artifacts,
        "07_standalone_poor_still_open.png",
        contains=True,
        stable_hits=1,
    )
    click_and_wait(
        cancel,
        "ERVC poor-gold cancel",
        "ERVA: TEST PASS insufficient_119_blocked",
        stream,
    )

    open_product_creator(VIVHITE, artifacts, "08_standalone_default")
    acceptance.wait_for_ocr_tokens(
        ("待价而塑的灵魂", "120", "1000"),
        ("ervc.cc", "xar.cc", "localize", "error"),
        acceptance.COURTIER_MODAL_REGION,
        15,
        artifacts,
        "08_standalone_default_render",
    )
    _, confirm = modal_buttons(artifacts, "08_standalone_default")
    click_and_wait(
        confirm,
        "ERVC default purchase",
        "ERVA: TEST PASS default_120_one_delivery_one_charge",
        stream,
    )

    open_product_creator(VIVHITE, artifacts, "09_standalone_custom")
    cancel, _ = configure_ervc_custom(
        artifacts, "09_standalone_custom", verify_faith_tooltips=True
    )
    click_and_wait(
        cancel,
        "ERVC configured cancel",
        "ERVA: TEST PASS custom_configuration_retained",
        stream,
    )
    stream.wait("ERVA: TEST PASS selected_faith_aluk", 5)
    stream.wait("ERVA: TEST PASS custom_348_ready", 5)

    open_product_creator(VIVHITE, artifacts, "10_standalone_reopen")
    stream.wait("ERVA: TEST PASS custom_configuration_reopened", 5)
    acceptance.wait_for_ocr_tokens(
        ("待价而塑的灵魂", "20", "16", "348"),
        ("ervc.cc", "xar.cc", "localize", "error"),
        acceptance.COURTIER_MODAL_REGION,
        15,
        artifacts,
        "10_standalone_reopen_render",
    )
    _, confirm = modal_buttons(artifacts, "10_standalone_reopen")
    click_and_wait(
        confirm,
        "ERVC custom purchase",
        "ERVA: TEST PASS custom_348_one_delivery_one_charge",
        stream,
    )
    stream.wait("ERVA: TEST DONE standalone", 5)
    stream.validate(STANDALONE_MARKERS)
    return {
        "cancel_zero_side_effect": True,
        "insufficient_119_blocked": True,
        "default_purchase_cost": 120,
        "custom_purchase_cost": 348,
        "selected_faith_context": "aluk",
        "ai_guard": True,
    }


def run_dual(stream: MarkerStream, artifacts: Path) -> dict[str, object]:
    assert_dual_decision_groups(artifacts)

    open_product_creator(VIVHITE, artifacts, "07_dual_ervc_stage")
    cancel, _ = configure_ervc_custom(
        artifacts, "07_dual_ervc_stage", verify_faith_tooltips=False
    )
    click_and_wait(
        cancel,
        "dual ERVC configured cancel",
        "ERVA: TEST PASS ervc_configuration_retained",
        stream,
    )
    stream.wait("ERVA: TEST PASS ervc_custom_348_staged", 5)

    open_product_creator(ORIGINAL, artifacts, "08_dual_xar_stage")
    stream.wait("ERVA: TEST PASS xar_default_isolated_from_ervc", 5)
    acceptance.wait_for_ocr_tokens(
        ("待价而塑的灵魂", "120", "1000"),
        ("xar.cc", "ervc.cc", "localize", "error"),
        acceptance.COURTIER_MODAL_REGION,
        15,
        artifacts,
        "08_dual_xar_default_render",
    )
    acceptance.click_courtier_option("女性", artifacts, "08_dual_xar_female")
    cancel, _ = modal_buttons(artifacts, "08_dual_xar_stage")
    click_and_wait(
        cancel,
        "dual XAR configured cancel",
        "ERVA: TEST PASS xar_configuration_retained",
        stream,
    )

    open_product_creator(VIVHITE, artifacts, "09_dual_ervc_purchase")
    stream.wait("ERVA: TEST PASS ervc_state_retained_after_xar", 5)
    acceptance.wait_for_ocr_tokens(
        ("待价而塑的灵魂", "20", "16", "348"),
        ("ervc.cc", "xar.cc", "localize", "error"),
        acceptance.COURTIER_MODAL_REGION,
        15,
        artifacts,
        "09_dual_ervc_retained_render",
    )
    _, confirm = modal_buttons(artifacts, "09_dual_ervc_purchase")
    click_and_wait(
        confirm,
        "dual ERVC 348 purchase",
        "ERVA: TEST PASS ervc_348_one_delivery_one_charge",
        stream,
    )

    open_product_creator(ORIGINAL, artifacts, "10_dual_xar_purchase")
    stream.wait("ERVA: TEST PASS xar_state_retained_after_ervc", 5)
    acceptance.wait_for_ocr_tokens(
        ("待价而塑的灵魂", "120"),
        ("xar.cc", "ervc.cc", "localize", "error"),
        acceptance.COURTIER_MODAL_REGION,
        15,
        artifacts,
        "10_dual_xar_retained_render",
    )
    _, confirm = modal_buttons(artifacts, "10_dual_xar_purchase")
    click_and_wait(
        confirm,
        "dual XAR 120 purchase",
        "ERVA: TEST PASS xar_120_one_delivery_one_charge",
        stream,
    )
    stream.wait("ERVA: TEST DONE dual", 5)
    stream.validate(DUAL_MARKERS)
    return {
        "both_decision_groups_rendered": True,
        "ervc_configuration_isolated": True,
        "xar_configuration_isolated": True,
        "ervc_purchase_cost": 348,
        "xar_purchase_cost": 120,
        "final_gold": 532,
        "delivery_count": 2,
    }


def copy_logs(userdir: Path, artifacts: Path) -> None:
    logs = userdir / "logs"
    if not logs.is_dir():
        return
    for path in sorted(item for item in logs.iterdir() if item.is_file()):
        shutil.copy2(path, artifacts / f"final_{path.name}")


def run_cell(
    scenario: ScenarioSpec,
    artifacts: Path,
    userdir: Path,
    keep_userdir: bool,
    expected_executable_sha256: str,
) -> dict[str, object]:
    started = time.perf_counter()
    started_at = datetime.now(timezone.utc).isoformat()
    artifacts.mkdir(parents=True)
    userdir.mkdir(parents=True)
    acceptance.configure_runtime_userdir(userdir)
    bootstrap = bootstrap_userdir(userdir, scenario)
    process = None
    result = "RED"
    error_reason = None
    evidence: dict[str, object] = {}
    diagnostics: list[str] = []
    allowed_diagnostics: list[str] = []
    verified_mount_order: list[str] = []
    game_version = None
    executable_before_sha256 = None
    executable_after_sha256 = None
    stream = MarkerStream(userdir / "logs" / "debug.log")
    pid_path = artifacts / "ck3.pid"
    watchdog_pid = None
    try:
        game_version = installed_game_version()
        if game_version != EXPECTED_GAME_VERSION:
            raise acceptance.RunnerError(
                f"CK3 version changed to {game_version} before {scenario.key}"
            )
        executable_before_sha256 = sha256_file(acceptance.CK3_EXE)
        if executable_before_sha256 != expected_executable_sha256:
            raise acceptance.RunnerError(
                f"CK3 executable changed before {scenario.key}"
            )
        watchdog_pid = acceptance.start_process_watchdog(pid_path)
        process = acceptance.launch_ck3_process(False)
        pid_path.write_text(str(process.pid), encoding="ascii")
        log(f"{scenario.key}: launched tracked CK3 PID {process.pid}")
        acceptance.wait_for_ocr_text(
            "新游戏",
            acceptance.MAIN_MENU_REGION,
            BOOT_TIMEOUT_S,
            artifacts,
            "01_main_menu_parser_ready.png",
            stable_hits=1,
        )
        verified_mount_order = verify_runtime_load_order(userdir, scenario, bootstrap)
        collect_project_logs(
            userdir,
            artifacts,
            "02_main_menu",
            diagnostics,
            allowed_diagnostics,
        )
        dismiss_external_main_menu_popup(artifacts)
        acceptance.navigate_lobby(artifacts)
        wait_for_gameplay_hud(artifacts)
        acceptance.ensure_game_paused(artifacts, "04_gameplay")
        initialize_fixture(scenario, stream, artifacts)
        evidence = (
            run_dual(stream, artifacts)
            if scenario.dual
            else run_standalone(stream, artifacts)
        )
        collect_project_logs(
            userdir, artifacts, "11_runtime", diagnostics, allowed_diagnostics
        )
        if process.poll() is not None:
            raise acceptance.RunnerError(
                f"CK3 PID {process.pid} exited before controlled shutdown"
            )
        result = "GREEN"
    except BaseException as exc:
        error_reason = str(exc) or type(exc).__name__
        log(f"{scenario.key}: FATAL {exc}")
        if isinstance(exc, Exception) and not isinstance(exc, acceptance.RunnerError):
            traceback.print_exc()
        try:
            acceptance.focus_ck3()
            acceptance.ImageGrab.grab().save(artifacts / "fatal_state.png")
        except Exception:
            pass
    finally:
        if process is not None:
            if result == "GREEN" and process.poll() is not None:
                result = "RED"
                error_reason = f"CK3 PID {process.pid} crashed before shutdown"
            try:
                acceptance.stop_ck3_process(
                    process, pid_path, require_running=result == "GREEN"
                )
            except Exception as exc:
                result = "RED"
                error_reason = (
                    f"{error_reason}; stop failed: {exc}"
                    if error_reason
                    else f"stop failed: {exc}"
                )
        try:
            if result == "GREEN":
                stream.validate(
                    DUAL_MARKERS if scenario.dual else STANDALONE_MARKERS,
                    final=True,
                )
            else:
                stream.pump(final=True)
        except BaseException as exc:
            result = "RED"
            reason = str(exc) or type(exc).__name__
            error_reason = f"{error_reason}; {reason}" if error_reason else reason
        try:
            version_after = installed_game_version()
            executable_after_sha256 = sha256_file(acceptance.CK3_EXE)
            if (
                version_after != game_version
                or version_after != EXPECTED_GAME_VERSION
                or executable_after_sha256 != expected_executable_sha256
            ):
                raise acceptance.RunnerError(
                    "CK3 installation changed during the acceptance cell"
                )
        except BaseException as exc:
            result = "RED"
            reason = str(exc) or type(exc).__name__
            error_reason = f"{error_reason}; {reason}" if error_reason else reason
        try:
            collect_project_logs(
                userdir,
                artifacts,
                "12_shutdown",
                diagnostics,
                allowed_diagnostics,
            )
        except BaseException as exc:
            result = "RED"
            reason = str(exc) or type(exc).__name__
            error_reason = f"{error_reason}; {reason}" if error_reason else reason
        try:
            copy_logs(userdir, artifacts)
        except Exception as exc:
            result = "RED"
            reason = f"final log copy failed: {exc}"
            error_reason = f"{error_reason}; {reason}" if error_reason else reason
        tree_unchanged = True
        tree_after_sha256: dict[str, str] = {}
        try:
            for key, target in bootstrap["targets"].items():
                after = tree_snapshot(target)
                tree_after_sha256[key] = snapshot_digest(after)
                if after != bootstrap["tree_snapshots"][key]:
                    tree_unchanged = False
        except Exception as exc:
            tree_unchanged = False
            reason = f"runtime tree postflight failed: {exc}"
            error_reason = f"{error_reason}; {reason}" if error_reason else reason
        if not tree_unchanged:
            result = "RED"
            reason = "CK3 rewrote a disposable runtime tree"
            error_reason = f"{error_reason}; {reason}" if error_reason else reason

    userdir_removed = False
    if result == "GREEN" and not keep_userdir:
        try:
            shutil.rmtree(userdir)
            userdir_removed = not userdir.exists()
            if not userdir_removed:
                raise OSError(f"userdir still exists after removal: {userdir}")
        except Exception as exc:
            result = "RED"
            reason = f"userdir cleanup failed: {exc}"
            error_reason = f"{error_reason}; {reason}" if error_reason else reason
    elif userdir.exists():
        log(f"{scenario.key}: retained userdir at {userdir}")

    duration = round(time.perf_counter() - started, 3)
    diagnostics = list(dict.fromkeys(diagnostics))
    allowed_diagnostics = list(dict.fromkeys(allowed_diagnostics))
    fixture_target = Path(bootstrap["targets"]["fixture"]).resolve().as_posix()
    report = {
        "schema_version": 2,
        "scenario": scenario.key,
        "result": result,
        "error_reason": error_reason,
        "started_at_utc": started_at,
        "duration_seconds": duration,
        "git_sha": build_vivhite_release.git_sha(),
        "game_version": game_version,
        "ck3_executable_before_sha256": executable_before_sha256,
        "ck3_executable_after_sha256": executable_after_sha256,
        "debug_mode": False,
        "isolated_userdir": True,
        "product_order": list(scenario.product_order),
        "enabled_mods": bootstrap["enabled_mods"],
        "verified_mount_order": verified_mount_order,
        "fixture_last": (
            bool(verified_mount_order) and verified_mount_order[-1] == fixture_target
        ),
        "runtime_tree_before_sha256": bootstrap["tree_sha256"],
        "runtime_tree_after_sha256": tree_after_sha256,
        "runtime_trees_unchanged": tree_unchanged,
        "fixture_markers": stream.lines,
        "project_diagnostics": diagnostics,
        "allowed_project_diagnostics": allowed_diagnostics,
        "scenario_evidence": evidence,
        "environment": {
            "platform": platform.platform(),
            "python": sys.version.split()[0],
            "desktop": (
                f"{acceptance.pyautogui.size().width}x"
                f"{acceptance.pyautogui.size().height}"
            ),
        },
        "isolated_userdir_path": str(userdir),
        "userdir_removed_after_run": userdir_removed,
        "process_watchdog_pid": watchdog_pid,
    }
    write_json_atomic(artifacts / "report.json", report)
    print(f"{scenario.key}: {result} ({duration}s)", flush=True)
    return report


def fixture_source_errors() -> list[str]:
    errors: list[str] = []
    if not FIXTURE_SOURCE.is_dir():
        return [f"fixture source missing: {FIXTURE_SOURCE}"]
    for path in sorted(item for item in FIXTURE_SOURCE.rglob("*") if item.is_file()):
        relative = path.relative_to(FIXTURE_SOURCE).as_posix()
        data = path.read_bytes()
        if relative != "descriptor.mod" and path.suffix.lower() in {
            ".txt", ".gui", ".yml",
        } and not data.startswith(b"\xef\xbb\xbf"):
            errors.append(f"fixture script lacks UTF-8 BOM: {relative}")
        text = data.decode("utf-8-sig", errors="replace")
        if (
            "remote_file_id" in text
            or build_vivhite_release.ORIGINAL_WORKSHOP_ITEM_ID in text
        ):
            errors.append(f"fixture contains Workshop identity: {relative}")
    return errors


def installed_game_version() -> str:
    settings = (
        acceptance.CK3_EXE.parent.parent / "launcher" / "launcher-settings.json"
    )
    try:
        payload = json.loads(settings.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as error:
        raise acceptance.RunnerError(
            f"cannot read installed CK3 version from {settings}: {error}"
        ) from error
    version = payload.get("rawVersion")
    if not isinstance(version, str) or not version:
        raise acceptance.RunnerError(
            f"launcher settings contain no rawVersion: {settings}"
        )
    raw_executable = payload.get("exePath")
    if not isinstance(raw_executable, str) or not raw_executable:
        raise acceptance.RunnerError(
            f"launcher settings contain no exePath: {settings}"
        )
    declared_executable = (settings.parent / raw_executable).resolve()
    if declared_executable != acceptance.CK3_EXE.resolve():
        raise acceptance.RunnerError(
            "launcher exePath does not match the configured CK3 executable: "
            f"{declared_executable} != {acceptance.CK3_EXE.resolve()}"
        )
    return version


def preflight() -> None:
    errors = fixture_source_errors()
    errors.extend(build_vivhite_release.release_source_errors(
        build_vivhite_release.DEFAULT_SOURCE
    ))
    errors.extend(build_release.release_source_errors(build_release.DEFAULT_SOURCE))
    if os.name != "nt":
        errors.append("Vivhite acceptance requires Windows")
    if os.environ.get("GITHUB_ACTIONS") == "true":
        errors.append("Vivhite CK3 acceptance is forbidden on official GitHub runners")
    if acceptance.ck3_is_running():
        errors.append("ck3.exe is already running")
    if not acceptance.CK3_EXE.is_file():
        errors.append(f"CK3 executable missing: {acceptance.CK3_EXE}")
    else:
        try:
            actual_version = installed_game_version()
            if actual_version != EXPECTED_GAME_VERSION:
                errors.append(
                    f"CK3 version is {actual_version}, expected {EXPECTED_GAME_VERSION}"
                )
        except acceptance.RunnerError as error:
            errors.append(str(error))
    if acceptance._ocr is None:
        errors.append("RapidOCR is unavailable; use tools/.venv")
    width, height = acceptance.pyautogui.size()
    if width < 1920 or height < 1080:
        errors.append(f"interactive desktop is too small: {width}x{height}")
    if errors:
        raise acceptance.RunnerError("preflight failed:\n  " + "\n  ".join(errors))
    log(
        f"preflight passed: exe={acceptance.CK3_EXE}, desktop={width}x{height}, "
        "production projections + external fixture"
    )


def write_matrix_report(
    artifacts: Path,
    reports: list[dict[str, object]],
    result: str,
    error_reason: str | None,
    protected_before: dict[str, object],
    protected_after: dict[str, object] | None,
    protected_unchanged: bool,
    quiet_period_completed: bool,
    started_at: str,
    duration: float,
) -> None:
    protected_counts = {
        "real_profile": len(protected_before["real_profile"]),
        "steam_cloud": len(protected_before["steam_cloud"]),
        "workshop_registered_targets": len(
            protected_before["workshop"]["registered_targets"]
        ),
        "workshop_files": len(protected_before["workshop"]["files"]),
    }
    report = {
        "schema_version": 2,
        "run_id": artifacts.name,
        "started_at_utc": started_at,
        "duration_seconds": round(duration, 3),
        "result": result,
        "error_reason": error_reason,
        "git_sha": build_vivhite_release.git_sha(),
        "product_id": build_vivhite_release.PRODUCT_ID,
        "mod_version": build_vivhite_release.descriptor_version(
            build_vivhite_release.DEFAULT_SOURCE
        ),
        "workshop_item_id": None,
        "debug_mode": False,
        "isolated_userdirs": True,
        "fixture_source": str(FIXTURE_SOURCE),
        "scenarios": reports,
        "protected_storage": {
            "unchanged": protected_unchanged,
            "required_quiet_period_seconds": POSTFLIGHT_STABILITY_SECONDS,
            "quiet_period_seconds": (
                POSTFLIGHT_STABILITY_SECONDS if quiet_period_completed else 0
            ),
            "before_sha256": snapshot_digest(protected_before),
            "after_sha256": (
                snapshot_digest(protected_after) if protected_after is not None else None
            ),
            "counts": protected_counts,
            "real_profile_scope": (
                "tutorial, game-rule presets, dlc_load, pdx_settings, all *.ck3 saves"
            ),
            "steam_cloud_scope": "local Steam userdata backing store for app 1158310",
            "workshop_scope": (
                "exact registered CK3 ugc_*.mod descriptors plus recursive target "
                "path/size/mtime metadata"
            ),
        },
    }
    failures = sum(item["result"] != "GREEN" for item in reports)
    cases = []
    for item in reports:
        failure = ""
        if item["result"] != "GREEN":
            failure = (
                f'<failure message="{html.escape(str(item.get("error_reason") or "failed"), quote=True)}" />'
            )
        cases.append(
            f'  <testcase classname="ervc.acceptance" name="{item["scenario"]}" '
            f'time="{item["duration_seconds"]}">{failure}</testcase>'
        )
    if result != "GREEN":
        failures += 1
        cases.append(
            '  <testcase classname="ervc.acceptance" name="matrix" '
            f'time="0"><failure message="{html.escape(error_reason or "matrix failed", quote=True)}" />'
            '</testcase>'
        )
    write_text_atomic(
        artifacts / "report.xml",
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<testsuite name="ervc.acceptance" tests="{len(cases)}" '
        f'failures="{failures}" time="{round(duration, 3)}">\n'
        + "\n".join(cases)
        + "\n</testsuite>\n",
    )
    # Publish JSON last; its presence marks the JSON/JUnit report pair complete.
    write_json_atomic(artifacts / "report.json", report)


def main(
    selected: str = "all",
    artifacts_dir: str | None = None,
    keep_userdirs: bool = False,
) -> int:
    preflight()
    if artifacts_dir:
        artifacts = Path(artifacts_dir).expanduser().resolve()
        if artifacts.exists():
            raise acceptance.RunnerError(f"artifact directory already exists: {artifacts}")
        if not artifacts.parent.is_dir():
            raise acceptance.RunnerError(
                f"artifact parent does not exist: {artifacts.parent}"
            )
    else:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        artifacts = Path(tempfile.gettempdir()) / (
            f"ervc_acceptance_{stamp}_{uuid.uuid4().hex[:8]}"
        )
    userdirs = artifacts.with_name(artifacts.name + "_userdirs")
    if userdirs.exists():
        raise acceptance.RunnerError(f"userdir root already exists: {userdirs}")

    steam_root = terminal.steam_userdata_root()
    workshop_roots = steam_workshop_app_roots(steam_root)
    registered_workshop_targets(workshop_roots)
    ensure_test_paths_safe((artifacts, userdirs), steam_root, workshop_roots)
    protected_before = protected_snapshot(steam_root)
    expected_executable_sha256 = sha256_file(acceptance.CK3_EXE)
    artifacts.mkdir()
    userdirs.mkdir()
    started = time.perf_counter()
    started_at = datetime.now(timezone.utc).isoformat()
    reports: list[dict[str, object]] = []
    result = "RED"
    error_reason = None
    protected_after: dict[str, object] | None = None
    protected_unchanged = False
    protected_violation = False
    quiet_period_completed = False
    chosen = list(SCENARIOS.values()) if selected == "all" else [SCENARIOS[selected]]
    try:
        for scenario in chosen:
            report = run_cell(
                scenario,
                artifacts / "cells" / scenario.key,
                userdirs / scenario.key,
                keep_userdirs,
                expected_executable_sha256,
            )
            reports.append(report)
            protected_after = verify_protected_storage(protected_before, steam_root)
            protected_unchanged = True
            if report["result"] != "GREEN":
                error_reason = f"{scenario.key}: {report['error_reason']}"
                break
        else:
            protected_after = verify_protected_storage(
                protected_before, steam_root, POSTFLIGHT_STABILITY_SECONDS
            )
            protected_unchanged = True
            quiet_period_completed = True
            result = "GREEN"
    except BaseException as exc:
        result = "RED"
        error_reason = str(exc) or type(exc).__name__
        if "protected storage changed" in error_reason:
            protected_violation = True
            protected_unchanged = False
        log(f"matrix FATAL {exc}")
        if isinstance(exc, Exception) and not isinstance(exc, acceptance.RunnerError):
            traceback.print_exc()
    finally:
        if result == "GREEN" and not keep_userdirs:
            try:
                shutil.rmtree(userdirs, ignore_errors=False)
                if userdirs.exists():
                    raise OSError(f"matrix userdir root still exists: {userdirs}")
            except Exception as exc:
                result = "RED"
                reason = f"matrix userdir cleanup failed: {exc}"
                error_reason = f"{error_reason}; {reason}" if error_reason else reason
        elif userdirs.exists():
            log(f"retained matrix userdirs at {userdirs}")
        try:
            current = verify_protected_storage(protected_before, steam_root)
            protected_after = current
            protected_unchanged = not protected_violation
        except BaseException as exc:
            result = "RED"
            protected_violation = True
            protected_unchanged = False
            reason = str(exc) or type(exc).__name__
            error_reason = f"{error_reason}; {reason}" if error_reason else reason
        duration = time.perf_counter() - started
        write_matrix_report(
            artifacts,
            reports,
            result,
            error_reason,
            protected_before,
            protected_after,
            protected_unchanged,
            quiet_period_completed,
            started_at,
            duration,
        )

    print("\n===== ERVC ACCEPTANCE MATRIX =====")
    for report in reports:
        print(f"{report['scenario']:<24} {report['result']}")
    print(f"protected storage       {'UNCHANGED' if result == 'GREEN' else 'UNPROVEN'}")
    print(f"artifacts               {artifacts}")
    print(f"RESULT: {result}")
    return 0 if result == "GREEN" else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--scenario", choices=("all", *SCENARIOS), default="all"
    )
    parser.add_argument("--artifacts-dir", help="create this exact artifact directory")
    parser.add_argument("--keep-userdirs", action="store_true")
    parser.add_argument(
        "--preflight", action="store_true", help="validate paths and fixture only"
    )
    args = parser.parse_args()
    if args.preflight:
        preflight()
        raise SystemExit(0)
    raise SystemExit(main(args.scenario, args.artifacts_dir, args.keep_userdirs))
