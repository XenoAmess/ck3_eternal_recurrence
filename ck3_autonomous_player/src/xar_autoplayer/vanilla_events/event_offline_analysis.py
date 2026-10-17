"""Completed vanilla event source review and durable user-first-option knowledge.

This is source knowledge, never a fabricated accepted timeline contract or a
claim that script effects occurred. Only native event-card evidence is handled.
"""
from __future__ import annotations

import argparse
import copy
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import re
import subprocess

from ..interaction_offline_analysis import block, read_json, write_immutable
from .builds import event_context_build, SUPPORTED_CK3_EXE_SHA256
from .source_index import load_vanilla_event_source_index


SCHEMA = "xar.vanilla-event-offline-source-known/v1"


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _fingerprint(binding):
    return _sha(json.dumps(binding, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def _blocks(text, wanted):
    """Extract direct child brace blocks while respecting comments and strings."""
    tokens = [(match.group(), match.start(), match.end()) for match in re.finditer(
        r'#[^\r\n]*|"(?:\\.|[^"\\])*"|[^\s={}#"]+|[={}"]', text)
        if not match.group().startswith("#")]
    depth, found = 0, []
    for index, (value, start, end) in enumerate(tokens):
        if value == "{":
            depth += 1
        elif value == "}":
            depth -= 1
            if depth < 0:
                raise ValueError("unbalanced event source")
        elif (depth == 1 and value == wanted and index + 2 < len(tokens)
              and tokens[index + 1][0] == "=" and tokens[index + 2][0] == "{"):
            level = 1
            for closing in range(index + 3, len(tokens)):
                level += (tokens[closing][0] == "{") - (tokens[closing][0] == "}")
                if level == 0:
                    found.append(text[start:tokens[closing][2]])
                    break
            else:
                raise ValueError("unterminated event source block")
    if depth != 0:
        raise ValueError("unbalanced event source")
    return found


def _scalars(text, wanted):
    tokens = [match.group() for match in re.finditer(
        r'#[^\r\n]*|"(?:\\.|[^"\\])*"|[^\s={}#"]+|[={}"]', text)
        if not match.group().startswith("#")]
    depth, found = 0, []
    for index, value in enumerate(tokens):
        if value == "{":
            depth += 1
        elif value == "}":
            depth -= 1
        elif (depth == 1 and value == wanted and index + 2 < len(tokens)
              and tokens[index + 1] == "=" and tokens[index + 2] != "{"):
            found.append(tokens[index + 2].strip('"'))
    return found


@lru_cache(maxsize=4)
def _index(build):
    return load_vanilla_event_source_index(build=build)


def _native_binding(capture):
    context = capture.get("window_context")
    if not isinstance(context, dict) or context.get("schema") != "current-event-window-context-v1":
        raise ValueError("not a native vanilla event-card context")
    key, calculated = context.get("event_definition_key"), context.get("calculated_event_id")
    build = event_context_build(context, default="")
    backend = context.get("provenance", {}).get("backend_id")
    if (not isinstance(key, str) or re.fullmatch(r"[A-Za-z0-9_]+\.[0-9]+", key) is None
            or key != capture.get("event_definition_key")
            or type(calculated) is not int or calculated <= 0
            or build not in SUPPORTED_CK3_EXE_SHA256
            or backend != f"ck3-{build}-native-event-window-v1"):
        raise ValueError("event/build/native provider identity unavailable")
    count = capture.get("snapshot_option_count")
    shown = [row for row in context.get("options", []) if isinstance(row, dict) and row.get("shown") is True]
    if (type(count) is not int or count <= 0 or not shown
            or any(type(row.get("native_option_index")) is not int
                   or not 0 <= row["native_option_index"] < count for row in shown)):
        raise ValueError("native event option identity incomplete")
    return {"ck3_build": build, "required_ck3_exe_sha256": SUPPORTED_CK3_EXE_SHA256[build],
            "native_backend_id": backend, "event_definition_key": key,
            "calculated_event_id": calculated, "native_option_count": count}


def _source(game_root, binding):
    key, build = binding["event_definition_key"], binding["ck3_build"]
    indexed = _index(build)["events"].get(key)
    expected = None
    if indexed is not None:
        record = indexed["definition"]
        path, expected = game_root / record["relative_path"], record["file_sha256"].lower()
    else:
        query = subprocess.run(["rg", "-l", "--glob", "*.txt", "--",
            r"^\s*" + re.escape(key) + r"\s*=\s*\{", str(game_root / "events")],
            capture_output=True, text=True, encoding="utf-8", check=False)
        if query.returncode not in (0, 1):
            raise ValueError("vanilla event source scan failed")
        paths = [Path(line) for line in query.stdout.splitlines() if line]
        if len(paths) != 1:
            raise ValueError("vanilla event definition missing or ambiguous")
        path = paths[0]
    raw = path.read_bytes()
    if len(raw) > 2 * 1024 * 1024 or expected is not None and _sha(raw) != expected:
        raise ValueError("exact vanilla source file bound/hash differs")
    definition = block(raw.decode("utf-8-sig"), key)
    if definition is None:
        raise ValueError("exact source event block absent")
    options = _blocks(definition, "option")
    if len(options) != binding["native_option_count"]:
        raise ValueError("source/native option-count mapping not established")
    reviewed = []
    for index, option in enumerate(options):
        names, name_blocks = _scalars(option, "name"), _blocks(option, "name")
        for name_block in name_blocks:
            names.extend(match.strip('"') for match in re.findall(
                r'\b(?:text|desc)\s*=\s*("[^"\r\n]+"|[A-Za-z0-9_.]+)', name_block))
        if not names:
            raise ValueError("source option name identity cannot be parsed")
        # Preserve every condition and scope. Direct effect statements are an
        # index into source bodies, not evaluated/flattened material predictions.
        effect_assignments = re.findall(r"(?m)^\s*((?:(?:add_|remove_|set_|change_|trigger_|start_|end_|save_)[A-Za-z0-9_]+)|(?:[A-Za-z0-9_]+_effect))\s*=\s*([^\r\n]+)", option)
        reviewed.append({"native_option_index": index, "source_name_keys": sorted(set(names)),
                         "conditional_name_source": name_blocks,
                         "source_option": option, "trigger": block(option, "trigger"),
                         "direct_effect_statements": [{"effect": k, "source_value": v} for k, v in effect_assignments]})
    return path, raw, definition, reviewed


def analyze_event_batch(manifest, game_root, output_dir, *, publish_state_dir=None):
    batch, batch_raw = read_json(manifest)
    game_root, output_dir = Path(game_root), Path(output_dir)
    entries, unresolved, already_known = [], [], []
    for item in batch.get("new_incidents", []):
        if item.get("kind") == "pending_character_interaction" or not item.get("event_definition_key"):
            continue
        try:
            before, raw = read_json(item["before"])
            if (_sha(raw) != item["before_sha256"] or before.get("incident_id") != item["incident_id"]
                    or before.get("schema") != "xar.unhandled-event-first-rendered/v1"):
                raise ValueError("event incident source SHA/identity differs")
            if item.get("after"):
                after, after_raw = read_json(item["after"])
                if (_sha(after_raw) != item["after_sha256"] or after.get("incident_id") != item["incident_id"]):
                    raise ValueError("event after source SHA/identity differs")
            binding = _native_binding(before)
            if (publish_state_dir is not None and before.get("registry_known") is True
                    and before.get("offline_followup_required") is False):
                known, audit = load_source_reviewed_event_v1(publish_state_dir, before)
                if known is not None:
                    already_known.append({"incident_id": item["incident_id"],
                        "event_definition_key": binding["event_definition_key"],
                        "fingerprint": known["fingerprint"], "status": "source_reviewed_known",
                        "offline_followup_required": False})
                    continue
            source, source_raw, definition, options = _source(game_root, binding)
            binding["source_sha256"] = _sha(source_raw)
            binding["option_catalogue_sha256"] = _fingerprint(options)
            fingerprint = _fingerprint(binding)
            facts = {"schema": "xar.vanilla-event-offline-source-facts/v1", "fingerprint": fingerprint,
                "binding": binding, "source_path": str(source.resolve()),
                "source_relative": source.relative_to(game_root).as_posix(), "definition": definition,
                "options": options, "immediate": block(definition, "immediate"), "after": block(definition, "after"),
                "analysis": "All native-indexed source options reviewed as exact script bodies with trigger/scope/effect statements preserved. Conditions and scripted-effect callees are not evaluated. User policy chooses first rendered option, without claiming optimality or native AI equivalence.",
                "material_effects_verified": False, "registry_contract_accepted": False}
            local = write_immutable(output_dir / (fingerprint + ".source-facts.json"), facts)
            canonical = None
            if publish_state_dir is not None:
                canonical = write_immutable(Path(publish_state_dir) / "evidence/event-source-registry/facts"
                                            / (fingerprint + ".json"), facts)
            entry = {"schema": SCHEMA, "fingerprint": fingerprint, "binding": binding,
                     "source_path": facts["source_path"], "source_facts": canonical or local,
                     "classification": "offline-source-reviewed-user-first-rendered-policy",
                     "registry_contract_accepted": False, "material_effects_verified": False}
            candidate = write_immutable(output_dir / (fingerprint + ".registry-entry.json"), entry)
            published = None
            if publish_state_dir is not None:
                published = write_immutable(Path(publish_state_dir) / "evidence/event-source-registry"
                                            / (fingerprint + ".json"), entry)
            entries.append({"incident_id": item["incident_id"], "event_definition_key": binding["event_definition_key"],
                            "fingerprint": fingerprint, "source_facts": local, "canonical_source_facts": canonical,
                            "candidate": candidate, "published": published})
        except (OSError, ValueError, KeyError, TypeError) as error:
            unresolved.append({"incident_id": item.get("incident_id"), "event_definition_key": item.get("event_definition_key"),
                               "status": "unknown_unable_to_source_review", "reason": str(error)})
    report = {"schema": "xar.vanilla-event-offline-source-batch/v1",
              "completed_control_sequence": batch["completed_control_sequence"],
              "manifest": {"path": str(Path(manifest).resolve()), "sha256": _sha(batch_raw)},
              "entries": entries, "already_known": already_known,
              "unresolved": unresolved, "Game_MCP_OBS_calls": 0}
    write_immutable(output_dir / "EVENT-SOURCE-REVIEW.json", report)
    return report


@lru_cache(maxsize=128)
def _validated(entry_raw, source_stamp, facts_stamp):
    entry = json.loads(entry_raw)
    binding = entry["binding"]
    facts, facts_raw = read_json(entry["source_facts"]["path"])
    path = Path(entry["source_path"])
    raw = path.read_bytes()
    if (len(raw) > 2 * 1024 * 1024 or _sha(raw) != binding["source_sha256"]
            or _sha(facts_raw) != entry["source_facts"]["sha256"]
            or facts.get("binding") != binding or facts.get("fingerprint") != entry["fingerprint"]
            or _fingerprint(binding) != entry["fingerprint"]
            or _fingerprint(facts["options"]) != binding["option_catalogue_sha256"]
            or entry.get("classification") != "offline-source-reviewed-user-first-rendered-policy"):
        raise ValueError("durable event source review changed")
    return entry


def _stamp(path):
    stat = Path(path).stat()
    return stat.st_size, stat.st_mtime_ns


_SOURCE_REBIND_IDENTITY_KEYS = (
    "ck3_build", "required_ck3_exe_sha256", "native_backend_id",
    "event_definition_key", "native_option_count",
)


def _source_rebind_root_shape(capture, facts, current, *, source_event_type="character_event"):
    """Admit only a fresh, bound character-event root and source option shape.

    Old source facts do not contain an earlier root-scope snapshot. The event
    script's declared type is therefore the independent shape authority.
    Other event types remain unknown until they get their own exact binding.
    """
    context = capture.get("window_context")
    frame = capture.get("binding")
    if not isinstance(context, dict) or not isinstance(frame, dict):
        raise ValueError("fresh event/frame binding unavailable")
    instance = context.get("current_event_instance_id")
    if (type(instance) is not int or instance <= 0
            or capture.get("current_event_instance_id") != instance
            or type(context.get("snapshot_revision")) is not int
            or context.get("snapshot_revision") != frame.get("native_revision")
            or type(context.get("date_raw")) is not int
            or context.get("date_raw") != frame.get("date_raw")):
        raise ValueError("fresh event instance or semantic frame differs")
    readiness = context.get("readiness")
    if (context.get("status") != "available" or not isinstance(readiness, dict)
            or any(readiness.get(key) is not True for key in (
                "event_definition_identity_ready", "root_scope_ready",
                "saved_scopes_ready", "option_presentation_ready"))):
        raise ValueError("fresh event context is not fully bound")
    definition = facts.get("definition")
    if not isinstance(definition, str) or _scalars(definition, "type") != [source_event_type]:
        raise ValueError("source-declared event root differs")
    root = context.get("root_scope")
    identity = root.get("typed_identity") if isinstance(root, dict) else None
    actor = frame.get("actor_character_id")
    if (not isinstance(root, dict) or root.get("status") != "available"
            or type(root.get("raw_type_index")) is not int
            or root.get("raw_type_index") != 4 or root.get("type_key") != "character"
            or type(root.get("subtype")) is not int or root.get("subtype") != 0
            or not isinstance(identity, dict)
            or identity.get("status") != "available" or identity.get("kind") != "character"
            or type(actor) is not int or actor <= 0 or identity.get("character_id") != actor):
        raise ValueError("fresh native root scope shape or actor differs")
    source_options = facts.get("options")
    native_options = context.get("options")
    if (not isinstance(source_options, list)
            or len(source_options) != current["native_option_count"]
            or not isinstance(native_options, list) or not native_options
            or [row.get("native_option_index") for row in source_options]
               != list(range(current["native_option_count"]))):
        raise ValueError("source/native option catalogue shape differs")
    indexes = [row.get("native_option_index") for row in native_options
               if isinstance(row, dict)]
    if (len(indexes) != len(native_options) or len(set(indexes)) != len(indexes)
            or any(type(index) is not int or not 0 <= index < len(source_options)
                   for index in indexes)):
        raise ValueError("fresh native option indexes are not unique source indexes")
    shown = [row for row in native_options if row.get("shown") is True]
    if (not shown or any(type(row.get("rendered_index")) is not int
                         or row["rendered_index"] < 0 for row in shown)
            or len({row["rendered_index"] for row in shown}) != len(shown)):
        raise ValueError("fresh shown option order is unavailable")
    enabled_shown = [row for row in shown if row.get("enabled") is True]
    first = min(enabled_shown or shown, key=lambda row: row["rendered_index"])
    selection = capture.get("selection")
    if (not isinstance(selection, dict)
            or selection.get("native_option_index") != first["native_option_index"]
            or selection.get("rendered_index") != first["rendered_index"]
            or selection.get("option_number") != first["native_option_index"] + 1
            or selection.get("enabled") is not first.get("enabled")):
        raise ValueError("first shown enabled option is not the bound native option")
    return {"source_event_type": source_event_type, "raw_type_index": 4,
            "type_key": "character", "subtype": 0,
            "typed_identity_kind": "character", "actor_character_id": actor}


def _populist1001_source_rebind_shape(capture, facts, current):
    """Reuse only the already reviewed .4 populist letter after a cold reload.

    The current native definition ID is observed, never predicted from the old
    load. All other letter events retain the generic character-only boundary.
    """
    from .faction_demand1001_context import recognize_faction_demand1001_projection_v1
    from .populist1001_known_refusal_v1 import (
        BACKEND, EVENT_KEY, OPTION_CATALOGUE_SHA256, SOURCE_REBIND_POLICY,
        SOURCE_SHA256, _scope_id,
    )

    source_binding = facts.get("binding", {})
    if (current.get("ck3_build") != "1.20.0.4"
            or current.get("event_definition_key") != EVENT_KEY
            or current.get("native_backend_id") != BACKEND
            or current.get("native_option_count") != 4
            or source_binding.get("source_sha256") != SOURCE_SHA256
            or source_binding.get("option_catalogue_sha256") != OPTION_CATALOGUE_SHA256):
        raise ValueError("reviewed populist letter source/catalogue differs")
    shape = _source_rebind_root_shape(
        capture, facts, current, source_event_type="letter_event")
    context, frame = capture["window_context"], capture["binding"]
    if (frame.get("paused") is not True or frame.get("map_ready") is not True
            or frame.get("snapshot_id") != "native:" + str(frame.get("native_revision"))
            or any(type(frame.get(key)) is not int or frame[key] <= 0
                   for key in ("bridge_pid", "connection_generation"))
            or not isinstance(frame.get("episode_run_id"), str)
            or not frame["episode_run_id"] or context.get("window_match_count") != 1
            or recognize_faction_demand1001_projection_v1(context,
                played_character_id=frame.get("actor_character_id"),
                snapshot_option_count=capture.get("snapshot_option_count"))["status"] != "recognized"):
        raise ValueError("fresh populist letter frame/roles unavailable")
    by_native = {row["native_option_index"]: row for row in context["options"]}
    if (by_native[2].get("rendered_index") != 0
            or by_native[3].get("rendered_index") != 1):
        raise ValueError("reviewed populist letter rendered layout differs")
    roles = {row["name"]: row for row in context["saved_scopes"]}
    required = (("faction", "faction", "faction", "faction_id"),
                ("target_title", "landed_title", "landed_title", "title_id"),
                ("peasant_leader", "character", "character", "character_id"),
                ("peasant_county", "landed_title", "landed_title", "title_id"))
    if any(_scope_id(roles[name], kind, type_key, field) is None
           for name, kind, type_key, field in required):
        raise ValueError("fresh populist letter native scope identity unavailable")
    return {**shape, "source_rebind_policy": SOURCE_REBIND_POLICY}


def load_source_reviewed_event_v1(state_dir, capture):
    try:
        current = _native_binding(capture)
    except (ValueError, TypeError, KeyError) as error:
        return None, {"status": "unknown", "reason": str(error)}
    rejected = []
    source_rebind_entries = []
    exact_entry_seen = False
    for path in sorted((Path(state_dir) / "evidence/event-source-registry").glob("*.json")):
        try:
            entry, raw = read_json(path, 64 * 1024)
            binding = entry.get("binding", {})
            if binding.get("event_definition_key") != current["event_definition_key"]:
                continue
            exact = all(binding.get(k) == v for k, v in current.items())
            exact_entry_seen |= exact
            if (entry.get("schema") != SCHEMA or entry.get("fingerprint") != path.stem):
                raise ValueError("event source registry schema/fingerprint differs")
            if exact:
                known = _validated(raw, _stamp(entry["source_path"]), _stamp(entry["source_facts"]["path"]))
                return known, {"status": "offline-source-reviewed", "binding_mode": "exact",
                               "fingerprint": path.stem, "entry_path": str(path), "entry_sha256": _sha(raw),
                               "material_effects_verified": False, "registry_contract_accepted": False}
            if any(binding.get(k) != current[k] for k in _SOURCE_REBIND_IDENTITY_KEYS):
                # A valid old entry from another build/option shape is not a
                # source-rebind candidate for this native observation.
                continue
            known = _validated(raw, _stamp(entry["source_path"]), _stamp(entry["source_facts"]["path"]))
            source_rebind_entries.append((path, raw, known))
        except (OSError, ValueError, KeyError, TypeError) as error:
            if len(rejected) < 8:
                rejected.append({"entry": path.name, "reason": str(error)})
    if exact_entry_seen:
        return None, {"status": "unknown", "reason": "exact event binding failed validation",
                      "rejected_entries": rejected}
    if source_rebind_entries and not rejected:
        source_pairs = {(entry["binding"]["source_sha256"],
                         entry["binding"]["option_catalogue_sha256"])
                        for _, _, entry in source_rebind_entries}
        if len(source_pairs) == 1:
            path, raw, known = source_rebind_entries[0]
            try:
                facts, _ = read_json(known["source_facts"]["path"])
                populist_letter = current["event_definition_key"] == "faction_demand.1001"
                shape = (_populist1001_source_rebind_shape(capture, facts, current)
                         if populist_letter else _source_rebind_root_shape(capture, facts, current))
                old_binding = known["binding"]
                fresh_binding = {**current,
                                 "source_sha256": old_binding["source_sha256"],
                                 "option_catalogue_sha256": old_binding["option_catalogue_sha256"]}
                return known, {"status": "offline-source-reviewed",
                    "binding_mode": ("populist1001_source_rebound" if populist_letter else "source_rebound"),
                    "fingerprint": path.stem,
                    "entry_path": str(path), "entry_sha256": _sha(raw),
                    "fresh_binding": fresh_binding,
                    "fresh_binding_fingerprint": _fingerprint(fresh_binding),
                    "adapted_from": {"fingerprint": path.stem,
                                     "calculated_event_id": old_binding["calculated_event_id"],
                                     "entry_sha256": _sha(raw)},
                    "equivalent_source_fingerprints": [p.stem for p, _, _ in source_rebind_entries],
                    "root_scope_shape": shape,
                    **({"source_rebind_policy": shape["source_rebind_policy"]} if populist_letter else {}),
                    "material_effects_verified": False, "registry_contract_accepted": False}
            except (OSError, ValueError, KeyError, TypeError) as error:
                rejected.append({"entry": path.name, "reason": str(error)})
        else:
            rejected.append({"reason": "conflicting source or option catalogue bindings"})
    return None, {"status": "unknown", "rejected_entries": rejected}


def annotate_source_reviewed_event_plan_v1(plan, state_dir):
    capture = plan.get("unhandled_event_fallback")
    if not isinstance(capture, dict) or state_dir is None:
        return plan
    known, audit = load_source_reviewed_event_v1(state_dir, capture)
    result = copy.deepcopy(plan)
    result["unhandled_event_fallback"].update(registry_known=known is not None,
        offline_followup_required=known is None, source_knowledge=audit)
    result["event_decision"].update(source_registry_known=known is not None,
        source_classification=known["classification"] if known is not None else None,
        registry_contract_accepted=False, material_effects_verified=False)
    result["active_event"]["source_registry_known"] = known is not None
    result["active_event"]["source_knowledge_status"] = "source_reviewed_known" if known is not None else "unknown"
    if known is not None:
        result["event_decision"].update(status="source_reviewed_known", registry_known=True,
                                       classification=known["classification"])
        result["phase"] = result["phase"].replace("active_event_unhandled_", "active_event_source_reviewed_")
        if result.get("selected_step") is None:
            result["reason"] = ("Source-reviewed event: no shown native option is enabled."
                if capture["selection"]["enabled"] is not True
                else "Source-reviewed event: its first shown enabled option lacks an advertised native selection step.")
    if known is not None and result.get("selected_step") is not None:
        result["phase"] = "active_event_source_reviewed_first_rendered_option"
        result["reason"] = "Source-reviewed event: choose its current first shown enabled option under the owner's policy; material effects remain unverified."
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--game-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--publish-state-dir", type=Path)
    args = parser.parse_args()
    result = analyze_event_batch(args.manifest, args.game_root, args.output_dir,
                                 publish_state_dir=args.publish_state_dir)
    print(json.dumps({"reviewed": len(result["entries"]), "unknown": len(result["unresolved"])}))


if __name__ == "__main__":
    main()
