"""Validate this product's source and exact-installed CK3 selector contract."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

from product import LANGUAGES, REPO, SOURCE, TARGETS, UPSTREAM_ITEM_ID, runtime_files, spec

sys.path.insert(0, str(REPO / "tools"))
from ck3_text_projection import blocks, masked
from independent_mod_release import source_errors
from translate_localization_minimax import parse_ck3_localization


def block_body(source: str, key: str) -> str:
    clean = masked(source)
    found = [block for block in blocks(source) if block.key == key
             and clean[:block.start].count("{") == clean[:block.start].count("}")]
    if len(found) != 1:
        raise ValueError(f"expected one {key} block, found {len(found)}")
    return source[found[0].opening + 1:found[0].end - 1]


def validate(game_root: Path | None, release_localization: bool = False) -> dict:
    errors: list[str] = source_errors(spec(release_localization))
    hashes = []
    texts = {}
    runtime = runtime_files(release_localization)
    for relative in sorted(runtime):
        path = SOURCE / relative
        if not path.is_file():
            errors.append(f"missing runtime file: {relative}")
            continue
        data = path.read_bytes()
        hashes.append({"path": relative, "size": len(data), "sha256": hashlib.sha256(data).hexdigest()})
        if path.suffix in {".txt", ".yml", ".gui"} and not data.startswith(b"\xef\xbb\xbf"):
            errors.append(f"missing UTF-8 BOM: {relative}")
        if path.suffix in {".txt", ".gui", ".yml", ".mod"}:
            try:
                text = data.decode("utf-8-sig")
                texts[relative] = text
                if path.suffix != ".yml":
                    blocks(text)
                if "remote_file_id" in text or UPSTREAM_ITEM_ID in text:
                    errors.append(f"Workshop identity leaked into runtime: {relative}")
                if "CHTT:" in text or "chtt." in text:
                    errors.append(f"fixture leaked into runtime: {relative}")
            except (UnicodeError, ValueError) as error:
                errors.append(f"invalid runtime text: {relative}: {error}")
    decisions = texts.get("common/decisions/00_convert_holdings_decisions.txt", "")
    effects = texts.get("common/scripted_effects/cht_conversion_effects.txt", "")
    triggers = texts.get("common/scripted_triggers/00_convert_holdings_scripted_triggers.txt", "")
    gui = texts.get("gui/decision_view_widgets/decision_view_widget_ch_convert_holding.gui", "")
    descriptor = texts.get("descriptor.mod", "")
    if 'supported_version="1.20.*"' not in descriptor or 'version="1.0.0"' not in descriptor:
        errors.append("descriptor does not match reviewed 1.0.0 / CK3 1.20 contract")
    selector_methods = sorted(set(re.findall(r"DecisionViewWidget\w+\.\w+", "\n".join(line for line in gui.splitlines() if not line.lstrip().startswith("#")))))
    for old in ["DecisionViewWidgetCreateHolyOrder", "HasCurrentCapital", "GetCurrentCapital", "HasValidBaronies", "barony_valid"]:
        if old in gui or old in decisions:
            errors.append(f"obsolete selector API: {old}")
    try:
        base = block_body(triggers, "cht_barony_is_convertible_trigger")
        for expected in ["tier = tier_barony", "holder = $CHARACTER$", "$CHARACTER$ = { is_ai = no }", "is_leased_out = no", "has_holding = yes", "has_ongoing_construction = no"]:
            if expected not in base:
                errors.append(f"base title predicate lacks {expected}")
        for kind, holding, _ in TARGETS:
            decision = block_body(decisions, f"ch_convert_holding_to_{kind}_decision")
            shown = block_body(decision, "is_shown")
            valid = block_body(decision, "is_valid")
            widget = block_body(decision, "widget")
            effect = block_body(effects, f"cht_convert_to_{kind}_effect")
            if "is_ai = no" not in shown or "is_ai = no" not in valid or "ai_check_interval = 0" not in decision:
                errors.append(f"{kind}: player-only decision gate missing")
            if "controller = create_holy_order" not in widget or "title_valid" not in widget:
                errors.append(f"{kind}: current native selector contract missing")
            if "CHARACTER = scope:ruler" not in widget or "scope:ruler" in valid:
                errors.append(f"{kind}: actor scope wrong in selector/decision")
            if "gold = main_building_tier_1_cost" not in decision:
                errors.append(f"{kind}: reviewed upstream cost changed")
            if f"cht_convert_to_{kind}_effect = yes" not in block_body(decision, "effect"):
                errors.append(f"{kind}: decision bypasses production effect")
            if f"set_holding_type = {holding}" not in effect or "is_ai = no" not in effect or "exists = scope:barony" not in effect:
                errors.append(f"{kind}: production effect or guards incorrect")
    except ValueError as error:
        errors.append(str(error))
    locs = {}
    for language in (LANGUAGES if release_localization else LANGUAGES[:2]):
        text = texts.get(f"localization/{language}/00_convert_holdings_l_{language}.yml", "")
        if not text.splitlines() or text.splitlines()[0] != f"l_{language}:":
            errors.append(f"wrong localization header: {language}")
        try:
            parsed = parse_ck3_localization(SOURCE / f"localization/{language}/00_convert_holdings_l_{language}.yml")
            keys = list(parsed)
        except (OSError, ValueError) as error:
            errors.append(f"invalid localization: {language}: {error}")
            keys = []
        if len(keys) != len(set(keys)):
            errors.append(f"duplicate localization keys: {language}")
        locs[language] = set(keys)
        for kind, _, _ in TARGETS:
            for suffix in ["", "_desc", "_tooltip", "_confirm"]:
                if f"ch_convert_holding_to_{kind}_decision{suffix}" not in keys:
                    errors.append(f"missing {language} decision key for {kind}{suffix}")
        if "CHT_BUILDING_LOSS_WARNING" not in keys:
            errors.append(f"missing building loss warning: {language}")
    for language, keys in locs.items():
        if keys != locs.get("english"):
            errors.append(f"localization key inventories differ: {language}")
    vanilla = []
    if game_root is not None:
        native_files = ["common/holdings/00_holdings.txt", "common/decisions/00_holy_order_decisions.txt", "gui/decision_view_widgets/decision_view_widget_create_holy_order.gui", "common/script_values/00_building_values.txt", "common/culture/innovations/00_tribal_innovations.txt"]
        native = {}
        for relative in native_files:
            path = game_root / relative
            data = path.read_bytes()
            native[relative] = data.decode("utf-8-sig")
            vanilla.append({"path": relative, "size": len(data), "sha256": hashlib.sha256(data).hexdigest()})
        holdings = masked(native[native_files[0]])
        for _, holding, main in TARGETS:
            if not re.search(r"\b" + holding + r"\s*=\s*\{", holdings) or not re.search(r"\bprimary_building\s*=\s*" + main + r"\b", holdings):
                errors.append(f"target holding absent in installed game: {holding}")
        if "title_valid" not in native[native_files[1]]:
            errors.append("installed holy-order decision no longer uses title_valid")
        if not re.search(r"(?m)^main_building_tier_1_cost\s*=", native[native_files[3]]):
            errors.append("upstream cost script value is absent in installed game")
        for innovation in ["innovation_motte", "innovation_city_planning"]:
            if not re.search(r"(?m)^" + innovation + r"\s*=\s*\{", native[native_files[4]]):
                errors.append(f"upstream innovation absent in installed game: {innovation}")
        current_gui = native[native_files[2]]
        for method in selector_methods:
            if method not in current_gui:
                errors.append(f"GUI method absent from installed native widget: {method}")
    revision = subprocess.run(["git", "-C", str(REPO), "rev-parse", "HEAD"], check=True, capture_output=True, text=True).stdout.strip()
    executable = game_root.parent / "binaries/ck3.exe" if game_root else None
    exe_sha = hashlib.sha256(executable.read_bytes()).hexdigest() if executable and executable.is_file() else None
    return {"schema": "cht.static-validation.v1", "status": "RED" if errors else "GREEN", "errors": errors, "git_sha": revision, "runtime_file_count": len(runtime), "source_files": hashes, "selector_methods": selector_methods, "vanilla_files": vanilla, "game_root": str(game_root) if game_root else None, "ck3_exe_sha256": exe_sha, "release_localization": release_localization, "evidence_layer": "static-structure-and-installed-source", "ck3_started": False}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game-root", type=Path)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--release-localization", action="store_true")
    args = parser.parse_args()
    try:
        report = validate(args.game_root, args.release_localization)
        if args.report.exists():
            raise ValueError("report already exists; use a new attempt path")
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(json.dumps({"status": report["status"], "runtime_file_count": report["runtime_file_count"], "errors": report["errors"], "report": str(args.report)}, ensure_ascii=False))
        return 0 if not report["errors"] else 1
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        parser.exit(1, f"CHT STATIC FAILED: {error}\n")


if __name__ == "__main__":
    raise SystemExit(main())
