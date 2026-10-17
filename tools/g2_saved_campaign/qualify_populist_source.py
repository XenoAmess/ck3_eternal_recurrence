"""Verify carried populist knowledge with the selected SDK's offline loader/policy.

This replays the frozen P43 event window, never starts a service, and submits no
gameplay command. Namespace preparation can call it after carrying durable
source-registry knowledge into its actual state directory.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys


REPO = Path(__file__).resolve().parents[2]
FIXTURE_SHA256 = "96f1e075797c4d1ff76c815b44d48715a663e4900523e50f1cb4dfb779bae3e9"
EXPECTED_FINGERPRINT = "14b787d272428d83ecbf6e7e9e13389b6b3857688c4e0e7fb007a851cd61b17f"


def pin(path: Path) -> dict:
    raw = path.read_bytes()
    return {"path": str(path.resolve()), "bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest()}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package-root", type=Path, required=True)
    parser.add_argument("--state-dir", type=Path, required=True)
    parser.add_argument("--fixture", type=Path, default=REPO / "ck3_autonomous_player/tests/unit/fixtures/p43_populist_actual193_projection.json")
    parser.add_argument("--verify-cold-id-rebind", action="store_true",
                        help="also require the reviewed source to bind a synthetic changed cold-load definition ID")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.output.exists():
        parser.error("output must be new; retain prior qualification receipts")
    sys.dont_write_bytecode = True
    package = args.package_root.resolve(strict=True)
    sys.path.insert(0, str(package))
    from xar_autoplayer.vanilla_events import event_offline_analysis as loader
    from xar_autoplayer.vanilla_events import populist1001_known_refusal_v1 as policy

    if not all(Path(module.__file__).resolve().is_relative_to(package) for module in (loader, policy)):
        raise ValueError("imported source differs from the selected SDK package root")
    fixture_pin = pin(args.fixture)
    if fixture_pin["sha256"] != FIXTURE_SHA256:
        raise ValueError("P43 replay fixture bytes differ")
    fixture = json.loads(args.fixture.read_text(encoding="utf-8"))
    original = deepcopy(fixture["plan"])
    original["phase"] = "active_event_unhandled_first_rendered_option"
    original["unhandled_event_fallback"].update(
        registry_known=False, source_knowledge={"status": "unknown"})
    original["event_decision"]["status"] = "unhandled"
    if args.verify_cold_id_rebind:
        original["unhandled_event_fallback"]["window_context"]["calculated_event_id"] += 10000
    annotated = loader.annotate_source_reviewed_event_plan_v1(original, args.state_dir)
    chosen = policy.choose_source_reviewed_populist_refusal_v1(
        annotated, snapshot=fixture["snapshot"],
        action_steps=("select-event-option-3", "select-event-option-4"))
    knowledge = chosen["unhandled_event_fallback"]["source_knowledge"]
    expected_mode = "populist1001_source_rebound" if args.verify_cold_id_rebind else "exact"
    passed = (knowledge.get("status") == "offline-source-reviewed"
              and knowledge.get("binding_mode") == expected_mode
              and knowledge.get("fingerprint") == EXPECTED_FINGERPRINT
              and chosen.get("phase") == "active_event_source_reviewed_populist_refusal"
              and chosen.get("selected_step") == "select-event-option-4")
    machine = subprocess.check_output(
        [sys.executable, "-X", "utf8", str(REPO / "tools/ck3_live_run_id.py"), "machine"],
        text=True, encoding="utf-8").strip()
    report = {
        "schema": "xar.g2.populist-source-carry-qualification/v1",
        "machine_id": machine, "observed_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PASS" if passed else "FAIL",
        "package_root": str(package), "state_dir": str(args.state_dir.resolve()),
        "fixture": fixture_pin,
        "production_sources": {module.__name__: pin(Path(module.__file__)) for module in (loader, policy)},
        "source_knowledge": knowledge, "selected_step": chosen.get("selected_step"),
        "phase": chosen.get("phase"), "frozen_original_unknown_step": original["selected_step"],
        "cold_id_rebind_required": args.verify_cold_id_rebind,
        "calculated_event_id_mutation_is_synthetic": args.verify_cold_id_rebind,
        "Game_MCP_OBS_calls": 0, "gameplay_commands_submitted": 0,
        "current_game_observed": False, "new_live_evidence": False,
        "business_success_inferred": False, "title_retention_verified": False,
        "boundary": "Frozen P43 input and actual carried source files only; no current game, future event ID, war outcome or policy optimality qualification.",
    }
    with args.output.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    print(json.dumps({"status": report["status"], "receipt": pin(args.output)}, ensure_ascii=False))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
