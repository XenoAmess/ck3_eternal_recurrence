"""Extract bounded, owner-frozen M6 observations without game calls or writes.

Input is an explicit pinned manifest, never a directory or live ledger. JSONL
inputs require a frozen byte extent; the rest of a large trace is never read.
Output is a review packet, not G2 credit. Missing frame/episode/Game provenance
stays missing; an old named gain is never attached to a new action UUID.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import sys

SCHEMA = "xar.c23-a05.m6-inspection-manifest/v1"
SMALL = 256 * 1024
EXTENT = 8 * 1024 * 1024
LINE = 2 * 1024 * 1024
OUTPUT = 256 * 1024
IDENTITY = ("action_id", "actor_character_id", "target_character_id",
            "scheme_instance_id", "scheme_instance_generation")
STAGES = ("material_intervention", "first_named_gain_intervention",
          "terminal_intervention", "latest_instance_observation")
FACTS = (*IDENTITY, "exact_ck3_build", "exe_sha256", "source_native_revision",
         "source_date_raw", "completion_source_native_revision",
         "baseline_source_native_revision", "baseline_source_date_raw",
         "scheme_sway_opinion", "previous_scheme_sway_opinion",
         "sway_blocker_opinion", "tracked_instance_active",
         "incremental_named_gain_observed", "dedicated_benefit_observed",
         "instance_terminal_outcome_observed", "native_status_key",
         "terminal_cause_observed", "terminal_cause", "next_turn_consumed",
         "following_native_revision", "following_date_raw", "native_observation",
         "common_native_end_observation", "causal_observation")
RUNTIME = ("machine_id", "campaign_id", "Game_pid", "Game_creation_filetime")


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                     separators=(",", ":")).encode()).hexdigest()


def pointer(document, path):
    if path == "":
        return document
    if not isinstance(path, str) or not path.startswith("/"):
        raise ValueError("explicit JSON pointer required")
    for part in path[1:].split("/"):
        if re.search(r"~(?![01])", part):
            raise ValueError("invalid JSON pointer escape")
        part = part.replace("~1", "/").replace("~0", "~")
        if isinstance(document, dict):
            if part not in document:
                raise ValueError("JSON pointer not found: " + path)
            document = document[part]
        elif isinstance(document, list) and part.isascii() and part.isdecimal() and part == str(int(part)):
            document = document[int(part)]
        else:
            raise ValueError("JSON pointer not found: " + path)
    return document


def _positive(value):
    return type(value) is int and value > 0


def _sha(value):
    return isinstance(value, str) and re.fullmatch("[0-9a-f]{64}", value) is not None


def _time(value):
    if not isinstance(value, str):
        raise ValueError("freeze time required")
    stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if stamp.tzinfo is None:
        raise ValueError("freeze time requires explicit UTC offset")


def _read_pin(pin, wanted_lines):
    """Keep only selected rows; SHA covers exactly the declared closed extent."""
    if not isinstance(pin, dict) or not isinstance(pin.get("path"), str) or not _sha(pin.get("sha256")):
        raise ValueError("source path and lowercase SHA-256 required")
    _time(pin.get("frozen_at_utc"))
    path = Path(pin["path"])
    if pin.get("format") == "json":
        if pin.get("closed") is not True or not _positive(pin.get("bytes")) or pin["bytes"] > SMALL:
            raise ValueError("small JSON must be explicitly closed and at most 256 KiB")
        before = path.stat()
        if before.st_size != pin["bytes"]:
            raise ValueError("closed JSON size differs")
        with path.open("rb") as stream:
            raw = stream.read(SMALL + 1)
        after = path.stat()
        if (len(raw) != pin["bytes"] or hashlib.sha256(raw).hexdigest() != pin["sha256"]
                or (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
                != (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)):
            raise ValueError("closed JSON changed")
        return {None: json.loads(raw)}, {"bytes_read": len(raw), "sha256_verified": True}
    if pin.get("format") != "jsonl" or pin.get("closed_extent") is not True:
        raise ValueError("JSONL requires an owner-frozen extent")
    offset, length = pin.get("offset"), pin.get("length")
    if type(offset) is not int or offset < 0 or not _positive(length) or length > EXTENT:
        raise ValueError("explicit JSONL offset and length <= 8 MiB required")
    before = path.stat()
    if before.st_size < offset + length:
        raise ValueError("frozen extent no longer present")
    selected, checksum, count = {}, hashlib.sha256(), 0
    with path.open("rb") as stream:
        if offset:
            stream.seek(offset - 1)
            if stream.read(1) != b"\n":
                raise ValueError("extent offset is not a line boundary")
        stream.seek(offset)
        remaining = length
        while remaining:
            raw = stream.readline(min(remaining, LINE + 1))
            if not raw or len(raw) > LINE or not raw.endswith(b"\n"):
                raise ValueError("extent contains a partial or oversized JSONL row")
            remaining -= len(raw)
            checksum.update(raw)
            count += 1
            if count in wanted_lines:
                selected[count] = json.loads(raw)
        if checksum.hexdigest() != pin["sha256"]:
            raise ValueError("frozen extent SHA-256 differs")
    after = path.stat()
    if (before.st_dev, before.st_ino) != (after.st_dev, after.st_ino) or after.st_size < offset + length:
        raise ValueError("extent file identity changed")
    if set(selected) != wanted_lines:
        raise ValueError("selected JSONL row is outside the frozen extent")
    return selected, {"bytes_read": length + int(offset > 0), "rows_in_extent": count,
                      "selected_rows": sorted(selected), "sha256_verified": True,
                      "suffix_read": False}


def _identity(row):
    receipt = row.get("native_receipt") or row.get("recovered_instance_observation")
    receipt = receipt if isinstance(receipt, dict) else {}
    identity = {key: row.get(key, receipt.get(key)) for key in IDENTITY}
    full_id, generation = identity[IDENTITY[3]], identity[IDENTITY[4]]
    if (not isinstance(identity["action_id"], str) or not identity["action_id"]
            or any(not _positive(identity[key]) for key in IDENTITY[1:3])
            or not _positive(full_id) or full_id >= 0xFFFFFFFF
            or type(generation) is not int or generation != full_id >> 24):
        return None
    return identity


def _frame(frame):
    if not isinstance(frame, dict):
        return {}
    diagnostics = frame.get("diagnostics", {})
    played = frame.get("played_character", {})
    return {"snapshot_id": frame.get("snapshot_id"), "revision": frame.get("revision"),
            "native_revision": frame.get("native_revision"), "date_raw": frame.get("date_raw"),
            "actor_character_id": frame.get("actor_character_id", played.get("character_id") if isinstance(played, dict) else None),
            "episode_run_id": frame.get("episode_run_id"),
            "bridge_pid": frame.get("bridge_pid", diagnostics.get("bridge_pid") if isinstance(diagnostics, dict) else None),
            "connection_generation": frame.get("connection_generation", diagnostics.get("connection_generation") if isinstance(diagnostics, dict) else None)}


def _extract(row, *, locator, ordinary, frame, root, runtime):
    identity = _identity(row)
    if identity is None:
        return {"source": locator, "state": "instance_identity_not_observed"}
    frame = _frame(frame)
    receipt = row.get("native_receipt") or row.get("retained_native_applied_receipt")
    receipt_source = row.get("native_receipt_source") or row.get("retained_native_receipt_source")
    runtime = runtime if isinstance(runtime, dict) else {}
    gaps = []
    if (any(not isinstance(runtime.get(key), str) or not runtime[key]
            for key in ("machine_id", "campaign_id"))
            or any(not _positive(runtime.get(key)) for key in ("Game_pid", "Game_creation_filetime"))):
        gaps.append("machine_campaign_Game_pid_birth_binding_missing")
    if (not isinstance(frame.get("episode_run_id"), str) or not frame["episode_run_id"]
            or any(not _positive(frame.get(key)) for key in (
                "actor_character_id", "bridge_pid", "connection_generation", "native_revision"))
            or type(frame.get("date_raw")) is not int):
        gaps.append("complete_current_frame_not_observed")
    if frame.get("actor_character_id") != identity["actor_character_id"]:
        gaps.append("current_frame_actor_mismatch_or_missing")
    if runtime.get("Game_pid") != frame.get("bridge_pid"):
        gaps.append("Game_pid_current_frame_mismatch_or_missing")
    if not isinstance(receipt_source, dict):
        gaps.append("original_receipt_source_frame_missing")
    else:
        if receipt_source.get("schema") != "xar.ck3.sway-receipt-source-frame.v1":
            gaps.append("original_receipt_source_schema_missing")
        source_frames = [receipt_source.get(key) for key in ("before", "after")]
        for item in source_frames:
            if (not isinstance(item, dict)
                    or any(item.get(key) != frame.get(key) for key in (
                        "actor_character_id", "episode_run_id"))
                    or any(not _positive(item.get(key)) for key in (
                        "actor_character_id", "bridge_pid", "connection_generation"))
                    or type(item.get("date_raw")) is not int):
                gaps.append("original_receipt_actor_episode_mismatch_or_missing")
                break
    if not isinstance(root, dict):
        gaps.append("same_frame_root_not_observed")
    elif (root.get("status") != "available"
          or root.get("player_character_id") != identity["actor_character_id"]
          or root.get("player_character_alive") is not True
          or root.get("snapshot_revision") != frame.get("native_revision")
          or root.get("date_raw") != frame.get("date_raw")):
        gaps.append("root_current_frame_mismatch")
    if runtime.get("machine_id") is None:
        gaps.append("source_machine_not_observed")
    records = []
    for kind in STAGES:
        record = row.get(kind)
        if not isinstance(record, dict):
            continue
        exact = all(type(record.get(key)) is type(value) and record[key] == value
                    for key, value in identity.items())
        if not exact:
            records.append({"kind": kind, "state": "record_identity_mismatch", "sha256": digest(record)})
            continue
        facts = {key: record[key] for key in FACTS if key in record}
        source_revision, source_date = record.get("source_native_revision"), record.get("source_date_raw")
        following_revision, following_date = record.get("following_native_revision"), record.get("following_date_raw")
        # Old consumption fields can survive later reads. They are evidence only
        # when both coordinates are later and the ordinary returned occurrence
        # carries that very following frame. Revision ordering is session-local.
        following_matches_frame = (
            ordinary is not None and ordinary.get("status") == "executed"
            and record.get("next_turn_consumed") is True
            and _positive(source_revision) and type(source_date) is int
            and _positive(following_revision) and type(following_date) is int
            and following_revision > source_revision and following_date > source_date
            and following_revision == frame.get("native_revision")
            and following_date == frame.get("date_raw"))
        native = record.get("native_observation")
        natural = (record.get("instance_terminal_outcome_observed") is True
                   and isinstance(native, dict)
                   and all(native.get(key) == identity[key] for key in IDENTITY[1:])
                   and native.get("snapshot_revision") == source_revision
                   and native.get("date_raw") == source_date
                   and native.get("storage_slot_reused") is False
                   and all(native.get(key) is True for key in (
                       "instance_source_observed", "instance_present", "exact_instance_join_ready",
                       "native_status_observed", "native_terminal_state_observed"))
                   and type(native.get("native_status_raw")) is int
                   and native["native_status_raw"] == 1)
        records.append({"kind": kind, "facts": facts, "sha256": digest(record),
                        "later_ordinary_frame_candidate": following_matches_frame,
                        "independent_native_terminal_candidate": natural,
                        "same_measurement_frame": source_revision == frame.get("native_revision")
                        and source_date == frame.get("date_raw"),
                        "natural_cause_and_useful_outcome_review": "not_evaluated"})
    return {"source": locator, "identity": identity,
            "current_frame": frame, "runtime_binding": runtime, "ordinary_auto": ordinary,
            "root_frame": root, "native_receipt": receipt,
            "native_receipt_source": receipt_source,
            "applied_instance_observation": row.get("applied_instance_observation"),
            "recovered_instance_observation": row.get("recovered_instance_observation"),
            "binding_gaps": sorted(set(gaps)), "records": records,
            "cross_observation_join_performed": False}


def inspect_manifest(manifest, *, collector_machine_id):
    if (manifest.get("schema") != SCHEMA or not isinstance(manifest.get("machine_id"), str)
            or not manifest["machine_id"]):
        raise ValueError("manifest schema and source machine_id required")
    sources, selections = manifest.get("sources"), manifest.get("selections")
    if not isinstance(sources, list) or not 1 <= len(sources) <= 32 or not isinstance(selections, list) or len(selections) > 64:
        raise ValueError("at most 32 sources and 64 selections")
    wanted = [set() for _ in sources]

    def register(ref):
        if not isinstance(ref, dict) or type(ref.get("source")) is not int or not 0 <= ref["source"] < len(sources):
            raise ValueError("explicit source index required")
        index = ref["source"]
        if sources[index].get("format") == "jsonl":
            if not _positive(ref.get("line")):
                raise ValueError("JSONL line is relative to the extent and starts at 1")
            wanted[index].add(ref["line"])
        if not isinstance(ref.get("pointer"), str):
            raise ValueError("explicit pointer required, empty string selects document")

    for selection in selections:
        register(selection)
        for key in ("frame", "root", "runtime"):
            if key in selection:
                reference = selection[key]
                if key == "runtime" and isinstance(reference, dict) and "fields" in reference:
                    fields = reference["fields"]
                    if not isinstance(fields, dict) or set(fields) != set(RUNTIME):
                        raise ValueError("runtime fields must explicitly map machine/campaign/Game PID/birth")
                    for field_ref in fields.values():
                        register(field_ref)
                else:
                    register(reference)
    docs, reads = [], []
    for index, pin in enumerate(sources):
        value, summary = _read_pin(pin, wanted[index])
        docs.append(value)
        reads.append({"pin": pin, **summary})

    def get(ref):
        line = ref.get("line") if sources[ref["source"]].get("format") == "jsonl" else None
        return pointer(docs[ref["source"]][line], ref["pointer"])

    observations = []
    for selection in selections:
        value = get(selection)
        frame = get(selection["frame"]) if "frame" in selection else None
        root = get(selection["root"]) if "root" in selection else None
        runtime_ref = selection.get("runtime")
        runtime = ({key: get(ref) for key, ref in runtime_ref["fields"].items()}
                   if isinstance(runtime_ref, dict) and "fields" in runtime_ref
                   else get(runtime_ref) if runtime_ref is not None else None)
        ordinary = None
        if selection.get("kind") == "ordinary_auto":
            if not isinstance(value, dict):
                raise ValueError("ordinary_auto must select returned body")
            ordinary = {key: value.get(key) for key in ("status", "selected_step", "planning_source_frame")}
            if frame is None:
                frame = value.get("planning_source_frame")
            rows = [("/sway_following_turn", value.get("sway_following_turn"))]
            if value.get("selected_step") == "ordinary-sway-opportunity-v1":
                rows.append(("/result", value.get("result")))
        elif selection.get("kind") == "ledger_episode":
            rows = [("", value)]
        else:
            raise ValueError("kind must be ordinary_auto or ledger_episode")
        for suffix, row in rows:
            if not isinstance(row, dict):
                continue
            candidates = [(suffix, row)]
            previous = row.get("previous_interventions", [])
            if not isinstance(previous, list) or len(previous) > 64:
                raise ValueError("previous interventions must be bounded")
            candidates.extend((suffix + "/previous_interventions/" + str(i), item)
                              for i, item in enumerate(previous) if isinstance(item, dict))
            for tail, item in candidates:
                locator = {key: selection[key] for key in ("source", "line", "pointer") if key in selection}
                locator["pointer"] += tail
                observation = _extract(item, locator=locator, ordinary=ordinary,
                                       frame=frame, root=root, runtime=runtime)
                if (isinstance(runtime, dict) and runtime.get("machine_id") is not None
                        and runtime["machine_id"] != manifest["machine_id"]):
                    observation.setdefault("binding_gaps", []).append("manifest_runtime_source_machine_mismatch")
                if (manifest.get("campaign_id") is not None and isinstance(runtime, dict)
                        and runtime.get("campaign_id") != manifest["campaign_id"]):
                    observation.setdefault("binding_gaps", []).append("manifest_runtime_campaign_mismatch")
                observation["context_sources"] = {key: selection[key] for key in ("frame", "root", "runtime")
                                                  if key in selection}
                observations.append(observation)
    result = {"schema": "xar.c23-a05.m6-inspection/v1",
              "collector_machine_id": collector_machine_id, "source_machine_id": manifest["machine_id"],
              "observed_at_utc": datetime.now(timezone.utc).isoformat(), "sources": reads,
              "observations": observations, "Game_MCP_SDK_calls": 0,
              "G2_M6_credit_awarded": False, "M6_complete": False,
              "boundary": "Pinned producer observations only; no cross-episode/Game join, natural cause, useful outcome or completion inferred"}
    if len(json.dumps(result, ensure_ascii=False).encode()) > OUTPUT:
        raise ValueError("review packet exceeds 256 KiB; select fewer observations")
    return result


def self_check():
    """RAM-only adversarial checks of the new observation surface."""
    identity = dict(zip(IDENTITY, ("new-uuid", 40526, 34973, 83887164, 5)))
    frame = {"native_revision": 30, "date_raw": 300, "actor_character_id": 40526,
             "episode_run_id": "new-episode", "bridge_pid": 7, "connection_generation": 2}
    runtime = {"machine_id": "synthetic", "campaign_id": "c", "Game_pid": 7, "Game_creation_filetime": 99}
    record = {**identity, "source_native_revision": 20, "source_date_raw": 200,
              "next_turn_consumed": True, "following_native_revision": 30, "following_date_raw": 300,
              "instance_terminal_outcome_observed": False,
              "native_observation": {"storage_slot_reused": True, "native_terminal_state_observed": False}}
    row = {**identity, "native_receipt": identity, "terminal_intervention": record}
    def extract(candidate):
        return _extract(candidate, locator={}, ordinary={"status": "executed"}, frame=frame,
                        root=None, runtime=runtime)
    result = extract(row)
    assert result["records"][0]["later_ordinary_frame_candidate"] is True
    assert result["records"][0]["independent_native_terminal_candidate"] is False
    assert "original_receipt_source_frame_missing" in result["binding_gaps"]
    stale = {**record, "following_date_raw": 100, "following_native_revision": 10}
    assert extract({**row, "terminal_intervention": stale})["records"][0]["later_ordinary_frame_candidate"] is False
    old_gain = {**record, "action_id": "old-uuid"}
    assert extract({**row, "first_named_gain_intervention": old_gain})["records"][0]["state"] == "record_identity_mismatch"
    source = {"before": {"actor_character_id": 40526, "episode_run_id": "old-episode"},
              "after": {"actor_character_id": 40526, "episode_run_id": "old-episode"}}
    assert "original_receipt_actor_episode_mismatch_or_missing" in extract({**row, "native_receipt_source": source})["binding_gaps"]
    wrong = _extract(row, locator={}, ordinary={}, frame=frame, root=None,
                     runtime={**runtime, "Game_pid": 8})
    assert "Game_pid_current_frame_mismatch_or_missing" in wrong["binding_gaps"]
    assert pointer({"a/b": [{"~": 3}]}, "/a~1b/0/~0") == 3
    # Exercise the real extent reader against an in-memory file, including a
    # deliberately invalid suffix. No scratch file or trace copy is created.
    class Tracked(io.BytesIO):
        maximum_position = 0

        def readline(self, limit=-1):
            value = super().readline(limit)
            self.maximum_position = max(self.maximum_position, self.tell())
            return value

    class MemoryPath:
        def __init__(self, raw):
            self.raw, self.stream = raw, None

        def stat(self):
            from types import SimpleNamespace
            return SimpleNamespace(st_dev=1, st_ino=2, st_size=len(self.raw), st_mtime_ns=3)

        def open(self, mode):
            assert mode == "rb"
            self.stream = Tracked(self.raw)
            return self.stream

    prefix, extent = b"prefix\n", b'{"x":1}\n{"x":2}\n'
    memory = MemoryPath(prefix + extent + b"invalid-unread-suffix")
    pin = {"path": "RAM", "format": "jsonl", "closed_extent": True,
           "frozen_at_utc": "2026-10-20T00:00:00Z", "offset": len(prefix), "length": len(extent),
           "sha256": hashlib.sha256(extent).hexdigest()}
    original_path = globals()["Path"]
    globals()["Path"] = lambda unused: memory
    try:
        selected, read = _read_pin(pin, {2})
        assert selected == {2: {"x": 2}} and read["suffix_read"] is False
        assert memory.stream.maximum_position == len(prefix) + len(extent)
        for changed in ({"sha256": "0" * 64}, {"length": len(extent) - 1}):
            try:
                _read_pin({**pin, **changed}, {2})
            except ValueError:
                pass
            else:
                raise AssertionError("changed or partial extent accepted")
        source_frame = {key: frame[key] for key in (
            "actor_character_id", "episode_run_id", "bridge_pid", "connection_generation", "date_raw")}
        receipt_source = {"schema": "xar.ck3.sway-receipt-source-frame.v1",
                          "before": source_frame, "after": source_frame}
        document = {"episode": {**row, "native_receipt_source": receipt_source}, "frame": frame,
                    "root": {"status": "available", "player_character_id": 40526,
                             "player_character_alive": True, "snapshot_revision": 30, "date_raw": 300},
                    "metadata": runtime}
        manifest = {"schema": SCHEMA, "machine_id": "synthetic", "sources": [],
                    "selections": [{"source": 0, "pointer": "/episode", "kind": "ledger_episode",
                                    "frame": {"source": 0, "pointer": "/frame"},
                                    "root": {"source": 0, "pointer": "/root"},
                                    "runtime": {"fields": {key: {"source": 0, "pointer": "/metadata/" + key}
                                                            for key in RUNTIME}}}]}
        def inspect_ram():
            nonlocal memory
            raw = json.dumps(document).encode()
            memory = MemoryPath(raw)
            manifest["sources"] = [{"path": "RAM", "format": "json", "closed": True,
                                     "frozen_at_utc": pin["frozen_at_utc"], "bytes": len(raw),
                                     "sha256": hashlib.sha256(raw).hexdigest()}]
            return inspect_manifest(manifest, collector_machine_id="synthetic")["observations"][0]
        assert inspect_ram()["binding_gaps"] == []
        document["root"]["date_raw"] = 299
        assert "root_current_frame_mismatch" in inspect_ram()["binding_gaps"]
    finally:
        globals()["Path"] = original_path
    return {"status": "PASS", "checks": 13, "synthetic_only": True,
            "Game_MCP_SDK_calls": 0, "G2_M6_credit_awarded": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args()
    if args.self_check:
        print(json.dumps(self_check(), indent=2))
        return
    if args.manifest is None or not 0 < args.manifest.stat().st_size <= SMALL:
        parser.error("--manifest must name a small explicit JSON manifest")
    raw = args.manifest.read_bytes()
    machine = subprocess.run([sys.executable, "-B", str(Path(__file__).resolve().parents[1] / "ck3_live_run_id.py"),
                              "machine"], capture_output=True, text=True, check=True).stdout.strip()
    result = inspect_manifest(json.loads(raw), collector_machine_id=machine)
    result["manifest"] = {"path": str(args.manifest), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
