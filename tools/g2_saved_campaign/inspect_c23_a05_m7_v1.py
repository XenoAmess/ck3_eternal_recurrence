"""Stream one closed, bounded WAL; preserve original same-query root and H.

No Game, RPC, state mutation, provider issuer, directory scan or base-state read.
The input is driver-state.wal-v1.json, not JSONL. Each <=256 KiB canonical
delta is decoded separately. The <=8 MiB original extent is hashed once and
never copied. Output is a readout, not M7 or loaded-provider qualification.

CLI: --manifest small.json [--output create-only.json]; without --output only
the byte quote and digest are printed. Reserve the quoted output before using
--output. A manifest contains machine_id, closed_extent=true, wal stat identity
(path/bytes/file_id/device/mtime_ns), and expected Game/DLL/owner epoch. Those
expected values must come from the actual launch/SEM/custody evidence retained
by Root; this reader cannot turn client JSON into authority.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys

MACHINE = "xenoamess-full-tower-eb9d2c1186"
CAMPAIGN = "native-31254-6271ac8cd441"
EPISODE = "native-40526-1bec95182886"
ACTOR, FOUNDER, FIXED_D0 = 40526, 31254, 174
EXE = "98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518"
GETTER = "632f01555310ab57b65743a686d5653b87a08ada14ebcb7d849371027ae27660"
WAL_SCHEMA = "xar.ck3.driver-state-wal/v1"
PROJECTION = "player_heir_fixed_dynasty_projection_v1"
COMPONENT = "player_heir_candidate_v1"
MAX_WAL, MAX_DELTA, MAX_OUTPUT = 8 * 1024**2, 256 * 1024, 128 * 1024
META = {"format_version", "pipe_name", "bridge_pid", "episode_character_id",
        "episode_run_id", "last_checkpoint", "rollback_war_failure",
        "managed_restore_transaction", "succession_expectation",
        "succession_lifecycle", "campaign_goal"}
ROOT_FIELDS = ("status", "snapshot_revision", "date_raw", "local_player_id",
               "player_character_id", "player_character_alive", "provenance", COMPONENT)
H_BASE = {"status", "reason", "fixed_dynasty_id_raw", "candidate_character_id",
          "candidate_same_fixed_dynasty", "positive_same_dynasty_legal_witness",
          "k", "b", "H_interval", "complete_backup_domain", "scope"}
H_BOUND = {"machine_id", "game_identity", "native_provider_sha256", "owner_source_epoch",
           "query_id", "native_query_sequence", "capture_epoch_basis",
           "queried_snapshot_id", "queried_revision", "queried_native_revision"}


def require(value, reason):
    if not value:
        raise ValueError("M7 readout denied: " + reason)


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def hex64(value):
    return isinstance(value, str) and re.fullmatch("[0-9a-f]{64}", value) is not None


def object_pairs(pairs):
    value = {}
    for key, item in pairs:
        require(key not in value, "duplicate JSON key")
        value[key] = item
    return value


def decode(raw):
    return json.loads(raw, object_pairs_hook=object_pairs,
                      parse_constant=lambda v: require(False, "nonfinite JSON"))


class Stream:
    """Fixed extent with bounded token buffers and whole-extent digest."""
    def __init__(self, source, size):
        require(type(size) is int and 0 < size <= MAX_WAL, "WAL must be 1..8 MiB")
        self.source, self.size = source, size
        self.buffer, self.index, self.position, self.loaded = b"", 0, 0, 0
        self.digest = hashlib.sha256()

    def peek(self):
        if self.index == len(self.buffer):
            if self.loaded == self.size:
                return None
            self.buffer = self.source.read(min(65536, self.size - self.loaded))
            require(bool(self.buffer), "closed WAL extent truncated")
            self.digest.update(self.buffer)
            self.loaded += len(self.buffer)
            self.index = 0
        return self.buffer[self.index]

    def pop(self):
        value = self.peek()
        require(value is not None, "unexpected JSON end")
        self.index += 1
        self.position += 1
        return value

    def ws(self):
        while self.peek() in (9, 10, 13, 32):
            self.pop()

    def expect(self, byte):
        self.ws()
        require(self.pop() == byte, "unexpected JSON delimiter")

    def raw(self, limit):
        self.ws()
        start, first, out = self.position, self.peek(), bytearray()
        require(first is not None, "missing JSON value")
        stack, quoted, escaped = [], False, False
        composite = first in (91, 123)
        string_only = first == 34
        while True:
            value = self.peek()
            if value is None:
                require(not stack and not quoted and out, "truncated JSON value")
                break
            if out and not composite and not string_only and value in (9, 10, 13, 32, 44, 93, 125):
                break
            value = self.pop()
            out.append(value)
            require(len(out) <= limit, "one bounded JSON value exceeded limit")
            if quoted:
                if escaped:
                    escaped = False
                elif value == 92:
                    escaped = True
                elif value == 34:
                    quoted = False
                    if string_only:
                        break
            elif value == 34:
                quoted = True
            elif value in (91, 123):
                stack.append(93 if value == 91 else 125)
            elif value in (93, 125):
                require(stack and stack.pop() == value, "JSON nesting mismatch")
                if composite and not stack:
                    break
        return bytes(out), start, self.position


def validate_expected(expected):
    require(isinstance(expected, dict) and expected.get("machine_id") == MACHINE,
            "expected machine binding")
    require(expected.get("actor_character_id") == ACTOR and type(expected["actor_character_id"]) is int
            and expected.get("episode_run_id") == EPISODE
            and expected.get("campaign_id") == CAMPAIGN
            and expected.get("founder_character_id") == FOUNDER
            and expected.get("fixed_dynasty_id_raw") == FIXED_D0,
            "original founder/current episode/fixed D0 binding")
    game = expected.get("game_identity")
    require(isinstance(game, dict) and set(game) == {"pid", "creation_date", "executable"}
            and type(game.get("pid")) is int and game["pid"] > 0
            and all(isinstance(game.get(k), str) and game[k] for k in ("creation_date", "executable")),
            "actual exact Game identity required")
    require(hex64(expected.get("native_provider_sha256"))
            and expected["native_provider_sha256"] != GETTER
            and hex64(expected.get("owner_source_epoch")), "actual DLL and owner epoch required")


def same_actor_state(fields, expected):
    goal = fields.get("campaign_goal")
    return (fields.get("bridge_pid") == expected["game_identity"]["pid"]
            and fields.get("episode_character_id") == ACTOR
            and fields.get("episode_run_id") == EPISODE
            and isinstance(goal, dict) and goal.get("format_version") == 1
            and goal.get("goal_key") == "dynasty_continuity"
            and goal.get("campaign_id") == CAMPAIGN
            and goal.get("origin_character_id") == FOUNDER
            and goal.get("current_character_id") == ACTOR)


def inspect_result(result, *, fields, expected):
    """Conservative independently checked payload; no provider qualification."""
    root = result.get("campaign_root_context")
    require(isinstance(root, dict) and root.get("player_character_id") == ACTOR
            and root.get("player_character_alive") is True and same_actor_state(fields, expected),
            "root and same-entry episode/goal differ")
    require(type(root.get("date_raw")) is int and root["date_raw"] >= 53274624,
            "pre-A05 original frame")
    query = result.get("query_sequence")
    native = result.get("queried_native_revision")
    require(type(query) is int and query > 0 and type(native) is int and native > 0
            and type(root.get("snapshot_revision")) is int and root["snapshot_revision"] == native
            and type(result.get("snapshot_revision")) is int and result["snapshot_revision"] == native
            and type(result.get("queried_revision")) is int
            and isinstance(result.get("queried_snapshot_id"), str)
            and result["queried_snapshot_id"], "one root query frame required")
    provenance = root.get("provenance")
    require(isinstance(provenance, dict)
            and str(provenance.get("executable_sha256", "")).lower() == EXE,
            "actual exact EXE provenance required")
    frame = {k: result[k] for k in ("query_sequence", "snapshot_revision", "queried_snapshot_id",
                                   "queried_revision", "queried_native_revision")}
    projected = {"frame": frame, "root": {k: root[k] for k in ROOT_FIELDS if k in root},
                 "root_is_selected_original_fields": True, "omitted_root_fields": sorted(set(root) - set(ROOT_FIELDS)),
                 "projection": result.get(PROJECTION), "H_observation": "unknown"}
    value = result.get(PROJECTION)
    if value is None:
        projected["reason"] = "optional_projection_not_observed"
        return projected
    require(isinstance(value, dict) and set(value) in (H_BASE, H_BASE | H_BOUND), "H DTO key set")
    require(value.get("fixed_dynasty_id_raw") == FIXED_D0 and type(value["fixed_dynasty_id_raw"]) is int
            and value.get("b") is None and value.get("complete_backup_domain") is False
            and value.get("scope") == "pure_current_candidate_projection", "H fixed D0/domain semantics")
    require(isinstance(value.get("reason"), str) and 0 < len(value["reason"]) <= 1024, "H reason")
    if value.get("status") == "unknown":
        require(value.get("k") is None and value.get("candidate_same_fixed_dynasty") is not True
                and value.get("positive_same_dynasty_legal_witness") is False
                and value.get("H_interval") == [0, 100], "unknown H semantics")
        projected["reason"] = value["reason"]
    else:
        require(value.get("status") == "positive_witness" and set(value) == H_BASE | H_BOUND
                and value.get("reason") == "one_living_native_player_heir_in_fixed_D0"
                and type(value.get("k")) is int and value["k"] == 1
                and value.get("candidate_same_fixed_dynasty") is True
                and value.get("positive_same_dynasty_legal_witness") is True
                and value.get("H_interval") == [70, 100], "positive H semantics")
        component = root.get(COMPONENT)
        require(root.get("status") == "available" and isinstance(component, dict)
                and set(component) == {"schema_version", "snapshot_revision", "query_kind", "executable_sha256",
                                       "getter_rva", "parent_frame_bound", "observation"}
                and type(component.get("schema_version")) is int and component["schema_version"] == 1
                and component.get("query_kind") == "campaign_root_context_v1"
                and component.get("getter_rva") == "0x289DCC0"
                and component.get("parent_frame_bound") is True
                and component.get("snapshot_revision") == native
                and str(component.get("executable_sha256", "")).lower() == EXE,
                "native component and root frame binding")
        observation = component.get("observation")
        require(isinstance(observation, dict) and observation.get("source_fixture") is False
                and all(observation.get(k) is True for k in (
                    "available", "original_getter_source_bound", "getter_observed", "candidate_present",
                    "candidate_alive", "identity_and_frame_stable", "lineage_available"))
                and observation.get("unavailable_reason") in (None, "")
                and observation.get("lineage_unavailable_reason") in (None, ""), "native positive observation")
        core = observation.get("before")
        require(isinstance(core, dict) and core == observation.get("after")
                and set(core) == {"date_raw", "paused", "speed", "local_player_id", "map_ready",
                                  "has_played_character", "played_character_id", "played_character_alive"}
                and all(type(core.get(k)) is int and core[k] >= 0 for k in ("date_raw", "speed", "local_player_id"))
                and core.get("date_raw") == root["date_raw"]
                and core.get("local_player_id") == root.get("local_player_id")
                and core.get("played_character_id") == ACTOR
                and all(core.get(k) is True for k in (
                    "paused", "map_ready", "has_played_character", "played_character_alive")),
                "native Core bookend and parent alive binding")
        lineage = observation.get("candidate_lineage")
        candidate = value.get("candidate_character_id")
        require(type(candidate) is int and -(2**31) <= candidate < 2**31 and candidate not in (-1, ACTOR)
                and observation.get("actor_character_id") == ACTOR
                and observation.get("candidate_character_id") == candidate
                and isinstance(lineage, dict) and set(lineage) == {"house_id", "dynasty_id"}
                and type(lineage.get("house_id")) is int and -(2**31) <= lineage["house_id"] < 2**31
                and lineage["house_id"] != -1 and type(lineage.get("dynasty_id")) is int
                and lineage["dynasty_id"] == FIXED_D0,
                "full candidate/House/fixed dynasty binding")
        projected["H_observation"] = "positive_same_frame_payload_requires_Root_evidence_review"
    if set(value) == H_BASE | H_BOUND:
        require(value["machine_id"] == expected["machine_id"]
                and value["game_identity"] == expected["game_identity"]
                and value["native_provider_sha256"] == expected["native_provider_sha256"]
                and value["owner_source_epoch"] == expected["owner_source_epoch"]
                and value["capture_epoch_basis"] == "original_root_query_sequence"
                and type(value["native_query_sequence"]) is int and value["native_query_sequence"] == query
                and isinstance(value["query_id"], str) and value["query_id"], "Game/DLL/epoch/query binding")
        for key in ("queried_snapshot_id", "queried_revision", "queried_native_revision"):
            require(type(value[key]) is type(result[key]) and value[key] == result[key], "H crossed root frame")
    return projected


def inspect_stream(source, size, expected, *, max_matches=4):
    validate_expected(expected)
    require(type(max_matches) is int and 1 <= max_matches <= 16, "bounded match count")
    stream = Stream(source, size)
    stream.expect(123)
    header, matches, issues = {}, [], []
    count, history_index, previous, root_rows, eligible_rows = 0, None, None, 0, 0
    first = True
    while True:
        stream.ws()
        if stream.peek() == 125:
            stream.pop()
            break
        if not first:
            stream.expect(44)
        first = False
        key = decode(stream.raw(1024)[0])
        require(isinstance(key, str) and key not in header, "WAL duplicate/header key")
        stream.expect(58)
        if key != "entries":
            header[key] = decode(stream.raw(4096)[0])
            continue
        # The actual writer canonicalizes keys, so base fields precede entries.
        require(type(header.get("base_history_rows")) is int and header["base_history_rows"] >= 0
                and hex64(header.get("base_sha256")), "original canonical WAL header order")
        history_index, previous = header["base_history_rows"] + 1, header["base_sha256"]
        header[key] = "streamed"
        stream.expect(91)
        entry_first = True
        while True:
            stream.ws()
            if stream.peek() == 93:
                stream.pop()
                break
            if not entry_first:
                stream.expect(44)
            entry_first = False
            raw, start, end = stream.raw(MAX_DELTA + 1024)
            entry = decode(raw)
            require(isinstance(entry, dict) and set(entry) == {
                "sequence", "previous_sha256", "history_rows", "state_fields", "sha256"}, "WAL entry keys")
            count += 1
            require(type(entry["sequence"]) is int and entry["sequence"] == count
                    and entry["previous_sha256"] == previous and hex64(entry["sha256"]), "WAL chain order")
            body = canonical({k: v for k, v in entry.items() if k != "sha256"})
            require(len(body) <= MAX_DELTA and sha(body) == entry["sha256"], "WAL canonical delta bound/checksum")
            fields, rows = entry["state_fields"], entry["history_rows"]
            require(isinstance(fields, dict) and set(fields) in (META, META | {"rollback_war_failures"})
                    and fields.get("format_version") == 2 and isinstance(rows, list) and rows, "original WAL scalar schema")
            for offset, row in enumerate(rows):
                require(isinstance(row, dict) and type(row.get("index")) is int
                        and row["index"] == history_index, "WAL history index gap")
                history_index += 1
                if row.get("command") != "query-campaign-root-context-v1" or row.get("ok") is not True:
                    continue
                root_rows += 1
                pointer = "/entries/" + str(count - 1) + "/history_rows/" + str(offset) + "/result"
                try:
                    require(isinstance(row.get("result"), dict), "root result absent")
                    selected = inspect_result(row["result"], fields=fields, expected=expected)
                except (ValueError, KeyError, TypeError) as error:
                    if len(issues) < 32:
                        issues.append({"pointer": pointer, "reason": str(error)[:1024]})
                    continue
                eligible_rows += 1
                if len(matches) == max_matches:
                    matches.pop(0)
                matches.append({"pointer": pointer, "history_index": row["index"],
                    "entry_extent": {"start": start, "end": end, "sha256": sha(raw)},
                    "entry_chain_sha256": entry["sha256"], "query_result_canonical_sha256": sha(canonical(row["result"])),
                    "same_entry_actor_episode_goal": {k: fields[k] for k in (
                        "bridge_pid", "episode_character_id", "episode_run_id", "campaign_goal")}, **selected})
            previous = entry["sha256"]
    stream.ws()
    require(stream.peek() is None and stream.position == size, "trailing/incomplete WAL extent")
    require(set(header) == {"schema", "base_sha256", "base_history_rows", "entries", "consolidated_sha256"}
            and header.get("schema") == WAL_SCHEMA
            and (header.get("consolidated_sha256") is None or hex64(header["consolidated_sha256"])), "WAL full header")
    return {"schema": "xar.c23-a05.m7-WAL-readout/v1", "machine_id": MACHINE,
        "observed_at_utc": datetime.now(timezone.utc).isoformat(), "expected": expected,
        "WAL_extent": {"start": 0, "end": size, "bytes": size, "sha256": stream.digest.hexdigest()},
        "WAL_header": header, "verified_entries": count, "last_history_index": history_index - 1,
        "root_rows_observed": root_rows, "eligible_root_rows": eligible_rows,
        "selection": "latest matching original root results in this complete WAL extent",
        "omitted_earlier_eligible_rows": eligible_rows - len(matches), "matches": matches, "issues": issues,
        "H_observation": "unknown" if not matches else "see_each_original_same_query_payload",
        "G2_M7_credit_awarded": False, "breadth_credit_awarded": False, "actual_loaded_provider_qualification": False,
        "Game_RPC_SDK_calls": 0, "base_Driver_SAVE_body_reads": 0,
        "boundary": "Checks retained same-query facts only; expected bindings are not a provider issuer. Root must review actual launch/custody/source evidence. A positive payload is neither complete backup coverage nor broad M7."}


def stat_identity(stat):
    return {"bytes": stat.st_size, "file_id": str(stat.st_ino), "device": str(stat.st_dev), "mtime_ns": stat.st_mtime_ns}


def inspect_manifest(manifest):
    require(manifest.get("schema") == "xar.c23-a05.m7-WAL-inspection-manifest/v1"
            and manifest.get("machine_id") == MACHINE and manifest.get("closed_extent") is True,
            "explicit closed extent manifest required")
    reference = manifest["wal"]
    path = Path(reference["path"])
    require(path.name == "driver-state.wal-v1.json" and not path.is_symlink(), "one actual named WAL required")
    before = stat_identity(path.stat())
    require(all(reference.get(k) == value for k, value in before.items()), "fixed WAL fileID/mtime/size differs")
    with path.open("rb") as source:
        require(stat_identity(os.fstat(source.fileno())) == before, "opened WAL identity differs")
        result = inspect_stream(source, before["bytes"], manifest["expected"], max_matches=manifest.get("max_matches", 4))
        require(stat_identity(os.fstat(source.fileno())) == before, "opened WAL changed during streaming")
    require(stat_identity(path.stat()) == before, "WAL path atomically replaced during streaming")
    if "sha256" in reference:
        require(reference["sha256"] == result["WAL_extent"]["sha256"], "frozen WAL SHA differs")
    result["WAL_source"] = {"path": str(path.resolve()), **before}
    result["source_pins"] = manifest.get("source_pins", [])
    return result


def self_test():
    expected = {"machine_id": MACHINE, "actor_character_id": ACTOR, "episode_run_id": EPISODE,
        "campaign_id": CAMPAIGN, "founder_character_id": FOUNDER, "fixed_dynasty_id_raw": FIXED_D0,
        "game_identity": {"pid": 123, "creation_date": "synthetic-only", "executable": "synthetic/ck3.exe"},
        "native_provider_sha256": "a" * 64, "owner_source_epoch": "b" * 64}
    root = {"status": "available", "snapshot_revision": 7, "date_raw": 53274624, "local_player_id": 0,
        "player_character_id": ACTOR, "player_character_alive": True, "provenance": {"executable_sha256": EXE}}
    result = {"campaign_root_context": root, "query_sequence": 11, "snapshot_revision": 7,
        "queried_snapshot_id": "synthetic:7", "queried_revision": 8, "queried_native_revision": 7}
    fields = dict.fromkeys(META)
    fields.update(format_version=2, bridge_pid=123, episode_character_id=ACTOR, episode_run_id=EPISODE,
        campaign_goal={"format_version": 1, "goal_key": "dynasty_continuity", "campaign_id": CAMPAIGN,
                       "origin_character_id": FOUNDER, "current_character_id": ACTOR})

    def journal(payload=result):
        body = {"sequence": 1, "previous_sha256": "c" * 64, "history_rows": [
            {"index": 101, "command": "query-campaign-root-context-v1", "ok": True, "result": payload}], "state_fields": fields}
        return {"schema": WAL_SCHEMA, "base_sha256": "c" * 64, "base_history_rows": 100,
                "entries": [{**body, "sha256": sha(canonical(body))}], "consolidated_sha256": None}

    checks = []
    def run(doc, exp=expected):
        data = canonical(doc)
        return inspect_stream(io.BytesIO(data), len(data), exp)

    good = run(journal())
    require(len(good["matches"]) == 1 and good["matches"][0]["reason"] == "optional_projection_not_observed", "selftest missing H")
    checks.append("missing_H_retains_unknown_without_RPC")
    unknown = dict(status="unknown", reason="trusted_loaded_Native_DLL_custody_unavailable", fixed_dynasty_id_raw=174,
        candidate_character_id=None, candidate_same_fixed_dynasty=None, positive_same_dynasty_legal_witness=False,
        k=None, b=None, H_interval=[0, 100], complete_backup_domain=False, scope="pure_current_candidate_projection")
    require(run(journal({**result, PROJECTION: unknown}))["matches"][0]["projection"] == unknown, "selftest unknown unchanged")
    checks.append("unknown_original_DTO_preserved")
    core = {"date_raw": 53274624, "paused": True, "speed": 5, "local_player_id": 0, "map_ready": True,
            "has_played_character": True, "played_character_id": ACTOR, "played_character_alive": True}
    observation = {k: True for k in ("available", "original_getter_source_bound", "getter_observed", "candidate_present",
                  "candidate_alive", "identity_and_frame_stable", "lineage_available")}
    observation.update(source_fixture=False, unavailable_reason=None, lineage_unavailable_reason=None,
        before=core, after=deepcopy(core), actor_character_id=ACTOR, candidate_character_id=45678,
        candidate_lineage={"house_id": 500, "dynasty_id": 174})
    component = {"schema_version": 1, "snapshot_revision": 7, "query_kind": "campaign_root_context_v1",
        "executable_sha256": EXE, "getter_rva": "0x289DCC0", "parent_frame_bound": True, "observation": observation}
    positive = {**unknown, "status": "positive_witness", "reason": "one_living_native_player_heir_in_fixed_D0",
        "candidate_character_id": 45678, "candidate_same_fixed_dynasty": True, "positive_same_dynasty_legal_witness": True,
        "k": 1, "H_interval": [70, 100], "machine_id": MACHINE, "game_identity": expected["game_identity"],
        "native_provider_sha256": "a" * 64, "owner_source_epoch": "b" * 64, "query_id": "synthetic-step",
        "native_query_sequence": 11, "capture_epoch_basis": "original_root_query_sequence",
        "queried_snapshot_id": "synthetic:7", "queried_revision": 8, "queried_native_revision": 7}
    payload = {**result, "campaign_root_context": {**root, COMPONENT: component}, PROJECTION: positive}
    require(len(run(journal(payload))["matches"]) == 1, "selftest positive")
    checks.append("same_frame_positive_payload_only_no_credit")
    for label, mutate in (
        ("stale_revision", lambda p: p[PROJECTION].update(queried_revision=9)),
        ("wrong_Game_birth", lambda p: p[PROJECTION]["game_identity"].update(creation_date="other")),
        ("wrong_DLL", lambda p: p[PROJECTION].update(native_provider_sha256="d" * 64)),
        ("wrong_owner_epoch", lambda p: p[PROJECTION].update(owner_source_epoch="e" * 64)),
        ("dead_parent", lambda p: p["campaign_root_context"].update(player_character_alive=False)),
        ("invalid_House", lambda p: p["campaign_root_context"][COMPONENT]["observation"]["candidate_lineage"].update(house_id=-1)),
        ("foreign_dynasty", lambda p: p["campaign_root_context"][COMPONENT]["observation"]["candidate_lineage"].update(dynasty_id=175)),
        ("fixture", lambda p: p["campaign_root_context"][COMPONENT]["observation"].update(source_fixture=True)),
    ):
        changed = deepcopy(payload)
        mutate(changed)
        require(not run(journal(changed))["matches"], "selftest accepted " + label)
        checks.append("reject_" + label)
    bad = journal()
    bad["entries"][0]["history_rows"][0]["index"] = 999
    try:
        run(bad)
    except ValueError:
        checks.append("reject_tampered_entry_chain")
    else:
        raise AssertionError("tampered journal accepted")
    raw = canonical(journal())
    try:
        inspect_stream(io.BytesIO(raw[:-1]), len(raw), expected)
    except ValueError:
        checks.append("reject_truncated_fixed_extent")
    else:
        raise AssertionError("truncated journal accepted")
    changed = deepcopy(fields)
    fields["episode_run_id"] = "different-episode"
    require(not run(journal())["matches"], "selftest cross episode accepted")
    fields.update(changed)
    checks.append("reject_same_actor_cross_episode")
    # Exercise string escapes and multibyte data across the 64 KiB refill.
    padded = {**payload, "unrelated_result_padding": ('\\\"}[' + chr(233)) * 20000}
    require(len(run(journal(padded))["matches"]) == 1, "selftest chunk boundary")
    checks.append("stream_refill_nested_string_escapes")
    many = journal(payload)
    first = deepcopy(many["entries"][0])
    for index in range(1, 6):
        body = {k: deepcopy(v) for k, v in first.items() if k != "sha256"}
        body.update(sequence=index + 1, previous_sha256=many["entries"][-1]["sha256"])
        body["history_rows"][0]["index"] = 101 + index
        many["entries"].append({**body, "sha256": sha(canonical(body))})
    selected = run(many)
    require(selected["eligible_root_rows"] == 6 and len(selected["matches"]) == 4
            and selected["matches"][0]["history_index"] == 103
            and selected["omitted_earlier_eligible_rows"] == 2, "selftest bounded latest selection")
    checks.append("complete_chain_latest_selection_without_cross_frame_merge")
    return {"schema": "xar.c23-a05.m7-inspector-synthetic-qualification/v1", "status": "PASS_SOURCE_ONLY",
        "checks": checks, "all_Game_and_provider_inputs": "synthetic", "actual_H": "NOTRUN",
        "M7": "in_progress", "G2": "6/8", "Game_RPC_SDK_calls": 0, "source26_frozen_leaf_writes": 0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.self_test:
        require(args.manifest is None and args.output is None, "selftest uses RAM only")
        print(json.dumps(self_test(), ensure_ascii=False))
        return
    require(args.manifest is not None and args.manifest.stat().st_size <= 32768, "small explicit manifest required")
    actual_machine = subprocess.check_output([sys.executable, "-B", str(Path(__file__).resolve().parents[1] / "ck3_live_run_id.py"), "machine"], text=True).strip()
    require(actual_machine == MACHINE, "actual machine differs")
    manifest_raw = args.manifest.read_bytes()
    result = inspect_manifest(decode(manifest_raw))
    result["manifest"] = {"path": str(args.manifest.resolve()), "bytes": len(manifest_raw), "sha256": sha(manifest_raw)}
    raw = canonical(result) + b"\n"
    require(len(raw) <= MAX_OUTPUT, "small M7 output budget exceeded; reduce max_matches")
    if args.output is not None:
        with args.output.open("xb") as output:
            output.write(raw)
            output.flush()
            os.fsync(output.fileno())
    print(json.dumps({"machine_id": MACHINE, "quote_bytes": len(raw), "sha256": sha(raw),
        "output": str(args.output) if args.output else None, "matches": len(result["matches"]),
        "H_observation": result["H_observation"], "M7_credit_awarded": False, "Game_RPC_SDK_calls": 0}))


if __name__ == "__main__":
    main()
