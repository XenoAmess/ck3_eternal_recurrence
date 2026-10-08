"""Offline conjunction of actual managed-host rows; never controls CK3 or grants source PASS."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

VERSION = "1.20.0.4"
EXE_SHA = "98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518"
LAW = "single_heir_succession_law"
FAMILIES = {
    "d3": [("TEST", "later_dynasty_single_heir_law_and_heir_ready")],
    "predeath": [],
    "postdeath": [
        ("PROBE", "phase3_succession_title"),
        ("TEST", "phase3_later_dynasty_realm_and_ministry_inherited"),
    ],
}


class AdmissionError(ValueError):
    pass


def require(value: bool, reason: str) -> None:
    if not value:
        raise AdmissionError(reason)


def uint32(value: object) -> bool:
    return type(value) is int and 0 < value < 0xFFFFFFFF


def integer(value: object, minimum: int = 0) -> bool:
    return type(value) is int and value >= minimum


def frame(snapshot: dict) -> tuple:
    require(isinstance(snapshot, dict), "actual after_snapshot missing")
    require(snapshot.get("backend_id") == "native-headless", "backend is not native")
    require(snapshot.get("source") == "injected-dll-named-pipe", "snapshot source differs")
    require(snapshot.get("episode_projection") == "native_campaign", "campaign projection differs")
    require(snapshot.get("paused") is True and snapshot.get("map_ready") is True, "not paused on map")
    require("active_event" in snapshot and snapshot["active_event"] is None, "event boundary unresolved")
    actor = snapshot.get("played_character", {})
    require(uint32(actor.get("character_id")) and actor.get("alive") is True,
            "current actor is not a living full-ID character")
    require(actor.get("source") == "native", "actor provenance differs")
    diagnostic = snapshot.get("diagnostics", {})
    hello = diagnostic.get("hello", {})
    require(diagnostic.get("connected") is True, "native bridge is not connected")
    require(integer(diagnostic.get("bridge_pid"), 1) and integer(diagnostic.get("connection_generation"), 1),
            "native process/generation identity missing")
    require(hello.get("expected_ck3_version") == VERSION
            and str(hello.get("expected_ck3_sha256", "")).lower() == EXE_SHA, "snapshot build differs")
    native = snapshot.get("native_revision")
    public = snapshot.get("revision")
    date = snapshot.get("date_raw")
    require(integer(native, 1) and integer(public) and integer(date, 1), "frame revisions/date invalid")
    require(snapshot.get("snapshot_id") == f"native:{native}", "snapshot ID/native revision mismatch")
    return (diagnostic["bridge_pid"], diagnostic["connection_generation"],
            actor["character_id"], date, native, public, snapshot["snapshot_id"])


def row(record: dict, tool: str) -> tuple[dict, tuple]:
    require(isinstance(record, dict) and record.get("ok") is True and not record.get("error"),
            "actual managed row is unsuccessful")
    require(record.get("plan", {}).get("tool") == tool, "managed row tool differs")
    require(isinstance(record.get("result"), dict), "actual managed result missing")
    return record["result"], frame(record.get("after_snapshot"))


def exact_query_binding(result: dict, f: tuple) -> None:
    require(result.get("queried_snapshot_id") == f[6]
            and result.get("queried_native_revision") == f[4]
            and result.get("queried_revision") == f[5], "query is not bound to actual current frame")
    require(result.get("snapshot_revision") == f[4] and result.get("date_raw") == f[3],
            "query date/native revision differs")


def count(log: dict, literal: str) -> int:
    matches = [item for item in log.get("matches", []) if item.get("literal") == literal]
    require(len(matches) == 1, "missing/duplicate log literal row: " + literal)
    value = matches[0].get("line_count")
    require(integer(value), "invalid literal line count")
    samples = matches[0].get("samples")
    require(isinstance(samples, list), "log samples missing")
    if value == 1:
        require(len(samples) == 1 and integer(samples[0].get("line_number"), 1)
                and literal in samples[0].get("text", ""), "actual one-line witness missing")
    elif value == 0:
        require(samples == [], "zero-count literal has samples")
    return value


def boolean(log: dict, name: str) -> bool:
    yes, no = count(log, name + "=TRUE"), count(log, name + "=FALSE")
    require((yes, no) in {(1, 0), (0, 1)}, "script Boolean is missing/repeated/conflicting: " + name)
    return yes == 1


def phase_literals(phase: str) -> dict[str, list[str]]:
    if phase == "d3":
        names = ["RQA_STAGE_DIAG_V3 same_current_primary",
                 "RQA_STAGE_DIAG_V3 actual_title_holder_is_root",
                 "RQA_STAGE_DIAG_V2 later_dynasty_single_heir_law",
                 "RQA_STAGE_DIAG_V3 holder_realm_has_single_heir"]
    else:
        names = [f"RQA_EFFECTIVE_LAW {phase} title_identity",
                 f"RQA_EFFECTIVE_LAW {phase} script_own_single_heir",
                 f"RQA_EFFECTIVE_LAW {phase} holder_realm_single_heir"]
    literals = [name + "=" + value for name in names for value in ("TRUE", "FALSE")]
    for kind, family in FAMILIES[phase]:
        literals += [f"RQA: {kind} PENDING_PHYSICAL {family}",
                     f"RQA: {kind} FAIL {family}", f"RQA: {kind} PASS {family}"]
    return {"literals": literals}


def evaluate_phase(evidence: dict) -> dict:
    phase = evidence.get("phase")
    require(phase in FAMILIES, "unknown observation phase")
    root, current = row(evidence.get("root_record"), "ck3_query_campaign_root_context_v1")
    physical, own_frame = row(evidence.get("physical_record"), "ck3_query_title_own_laws_v1")
    script, script_frame = row(evidence.get("script_record"), "ck3_query_engine_log_literals_v1")
    require(current == own_frame == script_frame, "owner/date/native/public frame changed between witnesses")
    require(root.get("accepted") is True and root.get("status") == "available"
            and root.get("campaign_root_context_ready") is True, "independent campaign root unavailable")
    exact_query_binding(root, current)
    build = root.get("build", {})
    require(build.get("version") == VERSION and str(build.get("exe_sha256", "")).lower() == EXE_SHA,
            "campaign-root exact build differs")
    ctx = root.get("campaign_root_context", {})
    require(ctx.get("status") == "available" and ctx.get("snapshot_revision") == current[4]
            and ctx.get("date_raw") == current[3] and ctx.get("player_character_id") == current[2]
            and ctx.get("player_character_alive") is True and ctx.get("independent") is True,
            "campaign-root current holder identity unavailable")
    title = ctx.get("primary_title", {})
    title_id = title.get("title_id")
    require(uint32(title_id) and title.get("tier_key") == "hegemony", "actual primary hegemony full ID missing")
    primary_rows = [entry for entry in ctx.get("held_title_partition", []) if entry.get("primary") is True]
    require(len(primary_rows) == 1 and primary_rows[0].get("title", {}).get("title_id") == title_id,
            "primary title is not an independent held title")
    heir = primary_rows[0].get("first_heir_character_id")
    if phase != "postdeath":
        require(uint32(heir) and heir != current[2], "original current-heir requirement not met")
    require(physical.get("accepted") is True and physical.get("read_only") is True
            and physical.get("status") == "available", "physical query unavailable")
    exact_query_binding(physical, current)
    own = physical.get("title_own_laws", {})
    require(own.get("schema") == "xar.ck3.title-own-laws.v1" and own.get("schema_version") == 1,
            "physical schema differs")
    require(own.get("available") is True and own.get("status") == "available"
            and own.get("unavailable_reason") is None, "physical full array unavailable")
    require(own.get("game_version") == VERSION and str(own.get("executable_sha256", "")).lower() == EXE_SHA,
            "physical exact build differs")
    require(own.get("actor_character_id") == current[2] and own.get("title_id") == title_id
            and physical.get("title_id") == title_id and own.get("snapshot_revision") == current[4]
            and own.get("date_raw") == current[3], "physical owner/title/frame differs")
    laws = own.get("laws")
    native_count = own.get("native_law_count")
    require(isinstance(laws, list) and integer(native_count) and native_count == len(laws),
            "physical count is not the complete ordered array")
    require(all(isinstance(law, dict) and set(law) == {"native_definition_id", "key"}
                and integer(law["native_definition_id"]) and law["native_definition_id"] < 0xFFFFFFFF
                and isinstance(law["key"], str)
                and law["key"] for law in laws), "invalid physical law row")
    require(script.get("schema") == "xar.ck3.engine-log-literals/v1"
            and script.get("read_only") is True and script.get("exists") is True
            and script.get("case_sensitive") is True and script.get("log_name") == "debug.log",
            "actual independent script witnesses unavailable")
    if phase == "d3":
        require(boolean(script, "RQA_STAGE_DIAG_V3 same_current_primary")
                and boolean(script, "RQA_STAGE_DIAG_V3 actual_title_holder_is_root"),
                "script title/holder differs from current root")
        script_own = boolean(script, "RQA_STAGE_DIAG_V2 later_dynasty_single_heir_law")
        realm = boolean(script, "RQA_STAGE_DIAG_V3 holder_realm_has_single_heir")
    else:
        require(boolean(script, f"RQA_EFFECTIVE_LAW {phase} title_identity"), "script title/holder differs")
        script_own = boolean(script, f"RQA_EFFECTIVE_LAW {phase} script_own_single_heir")
        realm = boolean(script, f"RQA_EFFECTIVE_LAW {phase} holder_realm_single_heir")
    for kind, family in FAMILIES[phase]:
        require(count(script, f"RQA: {kind} PENDING_PHYSICAL {family}") == 1
                and count(script, f"RQA: {kind} FAIL {family}") == 0
                and count(script, f"RQA: {kind} PASS {family}") == 0,
                "original non-law AND was not observed exactly once as pending")
    if native_count == 0:
        require(laws == [] and own.get("single_heir_member") is False and not script_own and realm,
                "empty-array realm-baseline evidence is incomplete/conflicting")
        representation = "realm_baseline_no_override"
    else:
        # Additional own laws have no qualified policy-compatibility proof here.
        require(native_count == 1 and laws[0]["key"] == LAW
                and own.get("single_heir_member") is True and script_own,
                "nonempty own array is conflicting/unknown or script does not agree")
        representation = "own_override"
    return {"phase": phase, "effective_single_heir_qualified": True,
            "representation": representation, "frame": list(current), "title_id": title_id,
            "actor_character_id": current[2], "date_raw": current[3], "engine_first_heir_id": heir,
            "script_own_single_heir": script_own, "holder_realm_single_heir": realm,
            "native_law_count": native_count, "laws": laws,
            "qualified_law_families": [family for _, family in FAMILIES[phase]],
            "source_pass": False, "business_pass": False}


def evaluate_bundle(evidence: dict) -> dict:
    require(evidence.get("schema") == "rmtm-effective-single-heir-actual-rows-v1", "bundle schema differs")
    phases = evidence.get("phases")
    require(isinstance(phases, list) and len(phases) == 3
            and [item.get("phase") for item in phases] == ["d3", "predeath", "postdeath"],
            "D3, fresh predeath and fresh postdeath observations are all required")
    d3, pre, post = (evaluate_phase(item) for item in phases)
    require(d3["title_id"] == pre["title_id"] == post["title_id"], "Later title identity changed")
    require(d3["actor_character_id"] == pre["actor_character_id"], "predeath current owner changed")
    require(pre["engine_first_heir_id"] == post["actor_character_id"], "actual successor differs from pre-read engine heir")
    require(d3["frame"][:2] == pre["frame"][:2] == post["frame"][:2], "same-live PID/generation changed")
    require(d3["date_raw"] <= pre["date_raw"] < post["date_raw"], "postdeath frame is not fresh")
    return {"schema": "rmtm-effective-single-heir-qualified-laws-v1", "observations": [d3, pre, post],
            "three_law_families_qualified": True, "source_pass": False, "business_pass": False,
            "remaining_original_contract": "actual predecessor death; original 36 families including personal land, loyal subtree, nine incumbents, same-title next-day recovery; original UI/14-day/threshold cells"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    data = args.evidence.read_bytes()
    try:
        evidence = json.loads(data.decode("utf-8-sig"))
        if evidence.get("schema") == "rmtm-effective-single-heir-phase-actual-rows-v1":
            result = evaluate_phase(evidence)
        else:
            result = evaluate_bundle(evidence)
        code = 0
    except (AdmissionError, KeyError, TypeError, AttributeError, ValueError) as error:
        result = {"schema": "rmtm-effective-single-heir-qualified-laws-v1", "error": str(error),
                  "three_law_families_qualified": False, "source_pass": False, "business_pass": False}
        code = 1
    result["input"] = {"path": str(args.evidence.resolve()), "bytes": len(data),
                       "sha256": hashlib.sha256(data).hexdigest()}
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
