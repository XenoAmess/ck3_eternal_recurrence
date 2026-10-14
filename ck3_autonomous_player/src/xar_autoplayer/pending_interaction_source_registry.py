"""Read immutable offline source reviews without reconnecting the active SDK."""
from __future__ import annotations

from functools import lru_cache
import hashlib
import json
from pathlib import Path
import re


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _read(path, limit):
    data = Path(path).read_bytes()
    if len(data) > limit:
        raise ValueError("offline registry source exceeds bounded input")
    return data


def _file_stamp(path):
    value = Path(path).stat()
    return value.st_size, value.st_mtime_ns


@lru_cache(maxsize=128)
def _validate_fingerprint(entry_digest, entry_raw, source_stamp, gui_stamp, facts_stamp):
    """Cache only a fully source-checked immutable fingerprint and file stamps."""
    entry = json.loads(entry_raw)
    facts_raw = _read(entry["source_facts"]["path"], 1024 * 1024)
    facts = json.loads(facts_raw)
    fields = ("build", "canonical_key", "deterministic_key_hash", "source_sha256", "gui_sha256")
    binding = {field: entry[field] for field in fields}
    fingerprint = _sha(json.dumps(binding, sort_keys=True, separators=(",", ":")).encode("utf-8"))
    if (entry.get("schema") != "xar.interaction-offline-reviewed-entry/v1"
            or entry.get("fingerprint") != fingerprint
            or facts.get("schema") != "xar.interaction-offline-source-facts/v1"
            or facts.get("fingerprint") != fingerprint
            or any(facts.get(field) != binding[field] for field in fields)
            or entry.get("classification") != "offline-source-reviewed-user-left-policy"
            or entry.get("preferred_action") != "reject"
            or _sha(facts_raw) != entry["source_facts"]["sha256"]
            or _sha(_read(entry["source_path"], 2 * 1024 * 1024)) != entry["source_sha256"]
            or _sha(_read(entry["gui_path"], 2 * 1024 * 1024)) != entry["gui_sha256"]
            or _file_stamp(entry["source_path"]) != source_stamp
            or _file_stamp(entry["gui_path"]) != gui_stamp
            or _file_stamp(entry["source_facts"]["path"]) != facts_stamp):
        raise ValueError("offline registry fingerprint/source binding changed")
    return entry


def load_source_reviewed_interaction_v1(state_dir, context, gui_binding):
    """Failure remains unknown and still uses the authorized left fallback."""
    directory = Path(state_dir) / "evidence/interaction-source-registry"
    definition, build = context.get("definition"), context.get("build")
    if (not isinstance(definition, dict) or not isinstance(build, dict)
            or type(definition.get("deterministic_key_hash")) is not int):
        return None, {"status": "unknown", "reason": "native_definition_or_build_missing"}
    rejected = []
    for path in sorted(directory.glob("*.json")):
        if re.fullmatch(r"[0-9a-f]{64}\.json", path.name) is None:
            continue
        try:
            raw = _read(path, 64 * 1024)
            entry = json.loads(raw)
            if entry.get("canonical_key") != definition.get("canonical_key"):
                continue
            if (entry.get("deterministic_key_hash") != definition["deterministic_key_hash"]
                    or type(entry.get("deterministic_key_hash")) is not int
                    or entry.get("build") != build
                    or entry.get("gui_sha256") != gui_binding["sha256"]
                    or entry.get("fingerprint") != path.stem):
                raise ValueError("offline registry current build/key/hash/GUI mismatch")
            reviewed = _validate_fingerprint(
                _sha(raw), raw, _file_stamp(entry["source_path"]), _file_stamp(entry["gui_path"]),
                _file_stamp(entry["source_facts"]["path"]))
            return reviewed, {"status": "offline-source-reviewed", "fingerprint": path.stem,
                              "entry_path": str(path), "entry_sha256": _sha(raw),
                              "source_sha256": reviewed["source_sha256"],
                              "gui_sha256": reviewed["gui_sha256"],
                              "material_effects_verified": False}
        except (OSError, ValueError, TypeError, KeyError) as error:
            if len(rejected) < 8:
                rejected.append({"entry": path.name, "reason": str(error)})
    return None, {"status": "unknown", "rejected_entries": rejected}
