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


def load_source_reviewed_event_v1(state_dir, capture):
    try:
        current = _native_binding(capture)
    except (ValueError, TypeError, KeyError) as error:
        return None, {"status": "unknown", "reason": str(error)}
    rejected = []
    for path in sorted((Path(state_dir) / "evidence/event-source-registry").glob("*.json")):
        try:
            entry, raw = read_json(path, 64 * 1024)
            binding = entry.get("binding", {})
            if binding.get("event_definition_key") != current["event_definition_key"]:
                continue
            if (entry.get("schema") != SCHEMA or entry.get("fingerprint") != path.stem
                    or any(binding.get(k) != v for k, v in current.items())):
                raise ValueError("current event/source option/build identity differs")
            known = _validated(raw, _stamp(entry["source_path"]), _stamp(entry["source_facts"]["path"]))
            return known, {"status": "offline-source-reviewed", "fingerprint": path.stem,
                           "entry_path": str(path), "entry_sha256": _sha(raw),
                           "material_effects_verified": False, "registry_contract_accepted": False}
        except (OSError, ValueError, KeyError, TypeError) as error:
            if len(rejected) < 8:
                rejected.append({"entry": path.name, "reason": str(error)})
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
            result["reason"] = ("Source-reviewed event: its first rendered option is disabled; do not substitute another option."
                if capture["selection"]["enabled"] is not True
                else "Source-reviewed event: its first rendered option lacks an advertised native selection step.")
    if known is not None and result.get("selected_step") is not None:
        result["phase"] = "active_event_source_reviewed_first_rendered_option"
        result["reason"] = "Source-reviewed event: choose its current first rendered option under the owner's policy; material effects remain unverified."
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
