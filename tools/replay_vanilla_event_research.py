"""Replay frozen JSON through existing event policy/outcome functions, offline.

Required input fields: context, played_character_id, snapshot_option_count,
ck3_build, ck3_exe_sha256. The two build fields may instead be declared in
context; every declared copy must agree with the production registry.
Optional snapshot and event_selection are passed to the production outcome
functions. No game, bridge service, command runner, or planner is instantiated.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = REPOSITORY_ROOT / "ck3_autonomous_player" / "src"
sys.path.insert(0, str(PACKAGE_ROOT))

from xar_autoplayer.vanilla_events import outcome, policy, registry  # noqa: E402


class ReplayInputError(ValueError):
    """The supplied frozen input cannot be interpreted without assumptions."""


def _object_pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ReplayInputError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _invalid_constant(value: str) -> None:
    raise ReplayInputError(f"non-finite JSON number: {value}")


def _is_integer(value: object, *, minimum: int = 0) -> bool:
    return type(value) is int and value >= minimum


def _not_evaluated(reason: str, **details: object) -> dict[str, object]:
    return {"status": "not_evaluated", "reason": reason, **details}


def _check_build(bundle: dict[str, object], context: dict[str, object]) -> dict:
    sources = [("input", bundle), ("context", context)]
    for name in ("snapshot", "event_selection"):
        if name in bundle:
            value = bundle[name]
            if not isinstance(value, dict):
                raise ReplayInputError(f"{name} must be an object when supplied")
            sources.append((name, value))
    provenance = context.get("provenance")
    if isinstance(provenance, dict):
        sources.append(("context.provenance", provenance))
    declarations: dict[str, list[str]] = {}
    for field, expected in (
        ("ck3_build", registry.EXACT_CK3_BUILD),
        ("ck3_exe_sha256", registry.EXACT_CK3_EXE_SHA256),
    ):
        declared_by = []
        for name, value in sources:
            if field not in value:
                continue
            actual = value[field]
            if field.endswith("sha256") and isinstance(actual, str):
                actual = actual.upper()
            if actual != expected:
                raise ReplayInputError(f"{name}.{field} differs from the frozen production build")
            declared_by.append(name)
        if not any(name in declared_by for name in ("input", "context", "context.provenance")):
            raise ReplayInputError(f"missing explicit {field} in input or context")
        declarations[field] = declared_by
    return {
        "ck3_build": registry.EXACT_CK3_BUILD,
        "ck3_exe_sha256": registry.EXACT_CK3_EXE_SHA256,
        "declarations": declarations,
        "verification": "input_declaration_matches_registry; executable_not_read",
    }


def _snapshot_issue(bundle: dict, context: dict) -> dict | None:
    snapshot = bundle.get("snapshot")
    if snapshot is None:
        return _not_evaluated("snapshot_not_supplied")
    required = ("snapshot_id", "revision", "played_character")
    missing = [key for key in required if key not in snapshot]
    if missing:
        return _not_evaluated("snapshot_binding_incomplete", missing_fields=missing)
    if not isinstance(snapshot["snapshot_id"], str) or not snapshot["snapshot_id"]:
        raise ReplayInputError("snapshot.snapshot_id must be a nonempty string")
    if not _is_integer(snapshot["revision"]):
        raise ReplayInputError("snapshot.revision must be a nonnegative integer")
    character = snapshot["played_character"]
    if not isinstance(character, dict):
        raise ReplayInputError("snapshot.played_character must be an object")
    if "character_id" not in character:
        return _not_evaluated("snapshot_binding_incomplete", missing_fields=["played_character.character_id"])
    if type(character["character_id"]) is not int or character["character_id"] != bundle["played_character_id"]:
        raise ReplayInputError("snapshot player identity differs from played_character_id")
    for context_key, snapshot_key in (("snapshot_revision", "native_revision"), ("date_raw", "date_raw")):
        if context_key not in context:
            continue
        if snapshot_key not in snapshot:
            return _not_evaluated("snapshot_binding_incomplete", missing_fields=[snapshot_key])
        if type(context[context_key]) is not int or type(snapshot[snapshot_key]) is not int or context[context_key] != snapshot[snapshot_key]:
            raise ReplayInputError(f"context.{context_key} differs from snapshot.{snapshot_key}")
    active_event = snapshot.get("active_event", snapshot.get("current_event"))
    if "current_event_instance_id" in context:
        if not isinstance(active_event, dict) or "instance_id" not in active_event:
            return _not_evaluated("snapshot_binding_incomplete", missing_fields=["active_event.instance_id"])
        if type(active_event["instance_id"]) is not int or active_event["instance_id"] != context["current_event_instance_id"]:
            raise ReplayInputError("context and snapshot event instance differ")
    if isinstance(active_event, dict) and "option_count" in active_event:
        if type(active_event["option_count"]) is not int or active_event["option_count"] != bundle["snapshot_option_count"]:
            raise ReplayInputError("snapshot event option count differs from snapshot_option_count")
    return None


def _production_fingerprint() -> dict[str, object]:
    """Bind the policy, outcome, registry and their checked-in Python records."""
    package = Path(policy.__file__).resolve().parent
    files = {
        path.relative_to(package).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(package.rglob("*.py"))
    }
    encoded = json.dumps(files, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return {
        "package": "xar_autoplayer.vanilla_events",
        "python_sources_sha256": hashlib.sha256(encoded).hexdigest(),
        "files_sha256": files,
        "policy": policy.VANILLA_EVENT_REGISTRY_CHOICE_POLICY,
    }


def replay_bytes(data: bytes) -> dict[str, object]:
    """Return an offline computation report; never submit the returned choice."""
    bundle = json.loads(data.decode("utf-8-sig"), object_pairs_hook=_object_pairs, parse_constant=_invalid_constant)
    if not isinstance(bundle, dict):
        raise ReplayInputError("input must be a JSON object")
    context = bundle.get("context")
    if not isinstance(context, dict):
        raise ReplayInputError("context must be an explicit JSON object")
    if not _is_integer(bundle.get("played_character_id"), minimum=1):
        raise ReplayInputError("played_character_id must be a positive integer")
    if not _is_integer(bundle.get("snapshot_option_count")):
        raise ReplayInputError("snapshot_option_count must be a nonnegative integer")
    build = _check_build(bundle, context)
    snapshot_issue = _snapshot_issue(bundle, context)
    decision = policy.recommend_registered_vanilla_event_option_v1(
        context,
        played_character_id=bundle["played_character_id"],
        snapshot_option_count=bundle["snapshot_option_count"],
    )
    material_plan = snapshot_issue or _not_evaluated("policy_did_not_recommend")
    material_evaluation = _not_evaluated("material_plan_not_ready")
    if snapshot_issue is None and decision.get("status") == "recommended":
        snapshot = bundle["snapshot"]
        planned = outcome.plan_registered_event_material_postcondition_v1(
            decision,
            snapshot["played_character"],
            played_character_gold=snapshot.get("played_character_gold"),
            played_character_prestige=snapshot.get("played_character_prestige"),
            snapshot_id=snapshot["snapshot_id"],
            revision=snapshot["revision"],
        )
        if planned is None:
            material_plan = _not_evaluated("material_postcondition_not_supported")
        elif planned.get("status") != "ready":
            material_plan = _not_evaluated(
                "production_material_plan_unavailable", production_result=planned
            )
        else:
            material_plan = planned
    if material_plan.get("status") == "ready":
        if "event_selection" not in bundle:
            material_evaluation = _not_evaluated("event_selection_not_supplied")
        else:
            selection = bundle["event_selection"]
            for field in ("event_definition_key", "selected_native_option_index"):
                if field in selection and selection[field] != decision.get(field):
                    raise ReplayInputError(f"event_selection.{field} differs from the replayed decision")
            material_evaluation = outcome.evaluate_registered_event_material_postcondition_v1(material_plan, selection)
    return {
        "schema": "xar.ck3.vanilla-event-research-replay",
        "schema_version": 1,
        "status": "replayed",
        "execution_mode": "offline-replay",
        "game_started": False,
        "gameplay_commands_submitted": 0,
        "new_live_evidence": False,
        "receipt_boundary": "supplied receipt replay only; authenticity and new game effects are not established",
        "input": {"sha256": hashlib.sha256(data).hexdigest(), "size_bytes": len(data)},
        "build": build,
        "production": _production_fingerprint(),
        "policy": decision,
        "material_plan": material_plan,
        "material_evaluation": material_evaluation,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="explicit frozen JSON bundle")
    parser.add_argument("--output", type=Path, help="new report file; default stdout; existing files are rejected")
    args = parser.parse_args(argv)
    try:
        if args.output is not None and args.output.exists():
            raise FileExistsError(f"refusing to overwrite {args.output}")
        report = replay_bytes(args.input.read_bytes())
        rendered = json.dumps(report, ensure_ascii=True, indent=2, sort_keys=True) + "\n"
        if args.output is None:
            sys.stdout.write(rendered)
        else:
            with args.output.open("x", encoding="utf-8", newline="\n") as handle:
                handle.write(rendered)
    except (OSError, ValueError) as error:
        print(f"offline replay input/output error: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
