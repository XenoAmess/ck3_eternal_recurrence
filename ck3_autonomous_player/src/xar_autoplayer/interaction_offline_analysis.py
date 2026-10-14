"""Offline source catalogue after a completed batch. Never calls Game/MCP.

Publishes immutable, source-pinned entries in the managed state directory for
the optional P08 registry reader. The only reply policy remains authored left.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read_json(path, limit=1024 * 1024):
    data = Path(path).read_bytes()
    if len(data) > limit:
        raise ValueError("offline incident/source receipt exceeds its bounded JSON input")
    return json.loads(data), data


def block(text, key):
    """Extract a CK3 named brace block, ignoring strings and line comments."""
    pattern = re.compile(r"(?m)^\s*" + re.escape(key) + r"\s*=\s*\{")
    match = pattern.search(text)
    if match is None:
        return None
    start = match.start()
    depth, quoted, comment, escaped = 1, False, False, False
    for index in range(match.end(), len(text)):
        char = text[index]
        if comment:
            if char in "\r\n":
                comment = False
        elif quoted:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                quoted = False
        elif char == "#":
            comment = True
        elif char == '"':
            quoted = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start:index + 1]
    raise ValueError("unterminated original interaction definition")


def write_immutable(path, value):
    data = (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != data:
            raise ValueError("immutable offline source receipt already differs")
    else:
        # Publish only a complete fsynced inode; the live reader never observes
        # a partly written JSON. Hard-link creation refuses an existing name.
        import os
        import uuid
        temporary = path.with_name(path.name + ".tmp-" + uuid.uuid4().hex)
        try:
            with temporary.open("xb") as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
            try:
                os.link(temporary, path)
            except FileExistsError:
                if path.read_bytes() != data:
                    raise ValueError("immutable offline source receipt already differs")
        finally:
            temporary.unlink(missing_ok=True)
    return {"path": str(path.resolve()), "sha256": sha(data)}


def analyze_batch(manifest, game_root, output_dir, *, publish_state_dir=None):
    """Mechanically catalogue source effects; never claim outcome optimality."""
    batch, manifest_data = read_json(manifest)
    game_root, output_dir = Path(game_root), Path(output_dir)
    entries, unresolved = [], []
    for incident in batch.get("new_incidents", []):
        if incident.get("kind") != "pending_character_interaction":
            continue
        before, raw = read_json(incident["before"])
        after, after_raw = read_json(incident["after"])
        if (sha(raw) != incident["before_sha256"] or sha(after_raw) != incident["after_sha256"]
                or before.get("incident_id") != incident["incident_id"]
                or after.get("incident_id") != incident["incident_id"]):
            raise ValueError("completed batch incident source SHA/identity mismatch")
        context = before["context"]
        key = context["definition"]["canonical_key"]
        key_hash = context["definition"]["deterministic_key_hash"]
        gui = before["gui_binding"]
        if (not isinstance(key, str) or re.fullmatch(r"[A-Za-z0-9_]+", key) is None
                or type(key_hash) is not int):
            raise ValueError("noncanonical native interaction definition")
        search_root = game_root / "common/character_interactions"
        found = subprocess.run(["rg", "-l", "--glob", "*.txt", "--",
                                r"^\s*" + re.escape(key) + r"\s*=\s*\{", str(search_root)],
                               capture_output=True, text=True, encoding="utf-8", check=False)
        if found.returncode not in (0, 1):
            raise ValueError("original interaction definition source scan failed")
        paths = [Path(line) for line in found.stdout.splitlines() if line]
        if len(paths) != 1:
            unresolved.append({"incident_id": incident["incident_id"], "canonical_key": key,
                               "status": "unknown", "reason": "original_definition_missing_or_ambiguous"})
            continue
        source = paths[0]
        source_raw = source.read_bytes()
        if len(source_raw) > 2 * 1024 * 1024:
            raise ValueError("interaction source exceeds bounded offline source input")
        definition = block(source_raw.decode("utf-8-sig"), key)
        gui_path = game_root / gui["source"]
        if sha(gui_path.read_bytes()) != gui["sha256"]:
            raise ValueError("captured original GUI source SHA changed")
        if before["selection"].get("action") not in ("reject", "acknowledge"):
            raise ValueError("offline source catalogue cannot introduce a different reply policy")
        binding = {"build": context["build"], "canonical_key": key,
                   "deterministic_key_hash": key_hash, "source_sha256": sha(source_raw),
                   "gui_sha256": gui["sha256"]}
        fingerprint = sha(json.dumps(binding, sort_keys=True, separators=(",", ":")).encode("utf-8"))
        facts = {"schema": "xar.interaction-offline-source-facts/v1", "fingerprint": fingerprint,
                 **binding, "source_path": str(source.resolve()), "gui_path": str(gui_path.resolve()),
                 "source_relative": source.relative_to(game_root).as_posix(),
                 "category": re.findall(r"(?m)^\s*category\s*=\s*([A-Za-z0-9_]+)", definition),
                 "definition": definition, "on_accept": block(definition, "on_accept"),
                 "on_decline": block(definition, "on_decline"),
                 "analysis": "Exact source bodies retained including conditional scopes and costs; no branch is assumed executed. User policy chooses authored left, not a claimed optimal or native-AI decision.",
                 "material_effects_verified": False}
        facts_receipt = write_immutable(output_dir / (fingerprint + ".source-facts.json"), facts)
        canonical_facts = None
        if publish_state_dir is not None:
            canonical_facts = write_immutable(
                Path(publish_state_dir) / "evidence/interaction-source-registry/facts"
                / (fingerprint + ".json"), facts)
        entry = {"schema": "xar.interaction-offline-reviewed-entry/v1", "fingerprint": fingerprint,
                 **binding, "classification": "offline-source-reviewed-user-left-policy",
                 "preferred_action": "reject", "source_path": facts["source_path"],
                 "gui_path": facts["gui_path"], "source_facts": canonical_facts or facts_receipt,
                 "reason": "Source-catalogued interaction; use the user's authored-left reply policy. Exact on_accept/on_decline effects are retained offline; reply ACK does not prove those effects."}
        receipt = write_immutable(output_dir / (fingerprint + ".registry-entry.json"), entry)
        published = None
        if publish_state_dir is not None:
            published = write_immutable(Path(publish_state_dir) / "evidence/interaction-source-registry"
                                        / (fingerprint + ".json"), entry)
        entries.append({"canonical_key": key, "fingerprint": fingerprint, "source_facts": facts_receipt,
                        "canonical_source_facts": canonical_facts,
                        "candidate": receipt, "published": published, "known_next_same_key": published is not None})
    report = {"schema": "xar.interaction-offline-source-batch-review/v1",
              "completed_control_sequence": batch["completed_control_sequence"],
              "manifest": {"path": str(Path(manifest).resolve()), "sha256": sha(manifest_data)},
              "entries": entries, "unresolved": unresolved,
              "Game_MCP_OBS_calls": 0, "runtime_source_edits": 0}
    write_immutable(output_dir / "SOURCE-REVIEW.json", report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--game-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--publish-state-dir", type=Path)
    args = parser.parse_args()
    report = analyze_batch(args.manifest, args.game_root, args.output_dir,
                           publish_state_dir=args.publish_state_dir)
    print(json.dumps({"reviewed": len(report["entries"]), "unknown": len(report["unresolved"])}))


if __name__ == "__main__":
    main()
