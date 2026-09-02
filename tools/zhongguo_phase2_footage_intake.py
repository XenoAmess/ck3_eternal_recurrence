#!/usr/bin/env python3
"""Strict no-media intake for one ZhongGuo phase-two capture bundle.

This is a media-entry contract, not a native observer schema.  It only reads
and hashes existing files.  It never launches CK3, invokes FFmpeg, or repairs a
partial capture.  Any absent or incomplete real bundle remains typed
``footage_pending``.  A schema-v2 span-session contract may aggregate clean
spans across managed CK3 restarts, while preserving one canonical seed/save
lineage and exact source/game/mod-mount identity.  The legacy one-session
runner envelope remains accepted without weakening its original checks.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from pathlib import Path, PurePosixPath

from zhongguo_phase2_capture_choreography import PHASE2_CAPTURE_SCENARIOS
from zhongguo_phase2_promo_producer import (
    PHASE2_PROMO_CAPTURE_CONTRACT_VERSION,
    PHASE2_PROMO_CAPTURE_MODE,
    canonical_phase2_capture_contract,
)


KIND = "zg361_phase2_footage_intake"
REPORT_RELATIVE = "report.json"
TIMELINE_RELATIVE = "cell/promo/capture-timeline.json"
INDEX_RELATIVE = "evidence-index.json"
LOADED_SEED_RELATIVE = "cell/04_phase2_seed_loaded.json"
_SHA = re.compile(r"^[0-9A-Fa-f]{64}$")
_GIT_SHA = re.compile(r"^[0-9A-Fa-f]{40}$")
SPAN_SESSION_CONTRACT_VERSION = 2
PHASE2_GAME_VERSION = "1.19.0.6"


def final_promo_execution_dag() -> dict[str, list[str]]:
    """Return the shared production dependency graph as a fresh mapping."""

    return {
        "fetch_and_verify_promo_origin_main": [],
        "fresh_promo_tool_receipt": ["fetch_and_verify_promo_origin_main"],
        "verified_eight_span_footage": ["fresh_promo_tool_receipt"],
        "source_footage_review_1x": ["verified_eight_span_footage"],
        "promoted_bilingual_authoring": ["source_footage_review_1x"],
        "xiaoxiao_tts": [
            "verified_eight_span_footage",
            "promoted_bilingual_authoring",
        ],
        "zh_cn_en_subtitle_layout_safe_zone": ["xiaoxiao_tts"],
        "composition": ["zh_cn_en_subtitle_layout_safe_zone"],
        "claims_audit": ["composition"],
        "final_video_review_1x": ["claims_audit"],
        "approved_signoff": ["final_video_review_1x"],
        "export": ["approved_signoff"],
        "publish_target_authority": ["explicit_operator_action"],
        "publish": ["export", "publish_target_authority"],
    }


def _positive_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _revision(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _nonempty(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _sha(value: object) -> bool:
    return isinstance(value, str) and _SHA.fullmatch(value) is not None


def _canonical_lineage(value: object) -> bool:
    if not isinstance(value, Mapping):
        return False
    source = value.get("source") if isinstance(value.get("source"), Mapping) else {}
    game = value.get("game") if isinstance(value.get("game"), Mapping) else {}
    mount = value.get("mod_mount") if isinstance(value.get("mod_mount"), Mapping) else {}
    return (
        value.get("schema_version") == 1
        and value.get("phase") == "zhongguo_phase2"
        and value.get("evidence_class") == "real_ck3"
        and value.get("fixture_used") is False
        and value.get("prior_phase_footage_used") is False
        and _nonempty(value.get("seed_lineage_id"))
        and _sha(value.get("canonical_seed_save_sha256"))
        and isinstance(source.get("git_commit"), str)
        and _GIT_SHA.fullmatch(str(source["git_commit"])) is not None
        and _sha(source.get("tree_sha256"))
        and game.get("version") == PHASE2_GAME_VERSION
        and _sha(game.get("exe_sha256"))
        and mount.get("kind") == "product-only"
        and _sha(mount.get("tree_sha256"))
    )


def _sha256(path: Path) -> dict[str, object]:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return {
        "path": str(path.resolve()),
        "bytes": path.stat().st_size,
        "sha256": digest.hexdigest().upper(),
    }


def _read(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON root is not an object: {path}")
    return value


def _relative(root: Path, raw: object) -> str | None:
    if not isinstance(raw, str) or not Path(raw).is_absolute():
        return None
    try:
        return Path(raw).expanduser().resolve().relative_to(root).as_posix()
    except ValueError:
        return None


def validate_footage_intake(capture_root: Path | None) -> dict[str, object]:
    """Return a typed, deterministic report without writing any input."""

    root = None if capture_root is None else capture_root.expanduser().resolve()
    report: dict[str, object] = {
        "schema_version": 1,
        "kind": KIND,
        "scope": "phase2_media_entry_only_no_native_observer_schema",
        "result": "RED",
        "reason_code": "footage_pending",
        "capture_root": None if root is None else str(root),
        "checks": {},
        "files": {},
        "session_binding": None,
        "reuse_policy": {
            "immutable_source_bundle": True,
            "independent_edit_projects_may_reuse_verified_spans": True,
            "source_copy_or_regeneration_required": False,
            "each_candidate_must_bind_same_verified_hashes": True,
        },
        "spans": [],
        "errors": [],
        "execution_attestation": {
            "ck3_started": False,
            "ffmpeg_started": False,
            "media_generated": False,
        },
    }
    errors: list[str] = []
    checks: dict[str, bool] = {}

    if root is None or not root.is_dir():
        report["errors"] = ["capture_root_missing"]
        report["checks"] = {"capture_root_exists": False}
        return report

    paths = {
        "report": root / REPORT_RELATIVE,
        "timeline": root / Path(*PurePosixPath(TIMELINE_RELATIVE).parts),
        "evidence_index": root / INDEX_RELATIVE,
        "loaded_seed_v2": root / Path(*PurePosixPath(LOADED_SEED_RELATIVE).parts),
    }
    checks["capture_root_exists"] = True
    checks["core_files_present"] = all(path.is_file() for path in paths.values())
    report["files"] = {
        name: None if not path.is_file() else _sha256(path)
        for name, path in paths.items()
    }
    if not checks["core_files_present"]:
        report["checks"] = checks
        report["errors"] = [
            "missing_core_files:"
            + ",".join(name for name, path in paths.items() if not path.is_file())
        ]
        return report

    try:
        outer = _read(paths["report"])
        timeline = _read(paths["timeline"])
        index = _read(paths["evidence_index"])
        loaded = _read(paths["loaded_seed_v2"])
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
        report["checks"] = checks
        report["errors"] = [f"core_json_invalid:{type(error).__name__}:{error}"]
        return report

    raw_rows = index.get("files")
    indexed: dict[str, Mapping[str, object]] = {}
    if isinstance(raw_rows, list):
        for row in raw_rows:
            if isinstance(row, Mapping) and isinstance(row.get("path"), str):
                indexed[str(row["path"]).replace("\\", "/")] = row
    checks["index_header_green"] = (
        index.get("schema_version") == 1
        and index.get("result") == "GREEN"
        and isinstance(index.get("artifact_root"), str)
        and Path(str(index["artifact_root"])).expanduser().resolve() == root
    )

    verified_records: dict[str, dict[str, object]] = {}

    def verify_indexed(relative: str, label: str) -> bool:
        row = indexed.get(relative)
        path = root / Path(*PurePosixPath(relative).parts)
        if not isinstance(row, Mapping) or not path.is_file():
            errors.append(f"{label}_not_indexed")
            return False
        record = _sha256(path)
        valid = (
            isinstance(row.get("bytes"), int)
            and not isinstance(row.get("bytes"), bool)
            and row.get("bytes") == record["bytes"]
            and isinstance(row.get("sha256"), str)
            and _SHA.fullmatch(str(row["sha256"])) is not None
            and str(row["sha256"]).upper() == record["sha256"]
        )
        if valid:
            verified_records[label] = record
        else:
            errors.append(f"{label}_hash_mismatch")
        return valid

    core_indexed = all(
        verify_indexed(relative, label)
        for relative, label in (
            (REPORT_RELATIVE, "report"),
            (TIMELINE_RELATIVE, "timeline"),
            (LOADED_SEED_RELATIVE, "loaded_seed_v2"),
        )
    )
    checks["core_files_hash_bound"] = core_indexed
    cell = outer.get("cell") if isinstance(outer.get("cell"), Mapping) else {}
    scenario = cell.get("scenario_evidence") if isinstance(cell, Mapping) and isinstance(cell.get("scenario_evidence"), Mapping) else {}
    reported_timeline = cell.get("promo_capture") if isinstance(cell, Mapping) else None
    checks["report_green_phase2_capture"] = (
        outer.get("schema_version") == 1
        and outer.get("result") == "GREEN"
        and isinstance(cell, Mapping)
        and cell.get("schema_version") == 1
        and cell.get("result") == "GREEN"
        and cell.get("phase2_promo_capture") is True
        and cell.get("phase2_promo_capture_complete") is True
        and cell.get("gameplay_green_claimed") is True
        and cell.get("native_launch_sequence") == "managed_native_session_supervisor"
    )
    checks["report_exactly_binds_timeline"] = reported_timeline == timeline
    expected_span_ids = [item.span_id for item in PHASE2_CAPTURE_SCENARIOS]
    contract = timeline.get("capture_contract")
    checks["timeline_phase2_contract"] = (
        timeline.get("schema") == 2
        and timeline.get("capture_mode") == PHASE2_PROMO_CAPTURE_MODE
        and timeline.get("capture_contract_version")
        == PHASE2_PROMO_CAPTURE_CONTRACT_VERSION
        and contract == canonical_phase2_capture_contract()
        and timeline.get("clean_capture_complete") is True
        and timeline.get("missing_clean_spans") == []
        and timeline.get("exclude_ck3_loading") is True
        and isinstance(timeline.get("source_kind"), str)
        and "real ck3" in str(timeline["source_kind"]).casefold()
        and isinstance(timeline.get("real_character_provenance"), Mapping)
    )

    raw_relative = _relative(root, timeline.get("raw_path"))
    raw_ok = False
    if raw_relative is not None and verify_indexed(raw_relative, "raw_recording"):
        raw_record = verified_records["raw_recording"]
        raw_ok = (
            raw_record["bytes"] == timeline.get("raw_bytes")
            and raw_record["sha256"] == str(timeline.get("raw_sha256", "")).upper()
            and int(raw_record["bytes"]) > 0
        )
    checks["raw_recording_hash_bound"] = raw_ok
    files = report["files"]
    assert isinstance(files, dict)
    files["raw_recording"] = verified_records.get("raw_recording")

    marks_value = timeline.get("marks")
    marks = marks_value if isinstance(marks_value, list) else []
    mark_map = {
        row.get("label"): row.get("seconds")
        for row in marks
        if isinstance(row, Mapping)
        and isinstance(row.get("label"), str)
        and isinstance(row.get("seconds"), (int, float))
        and not isinstance(row.get("seconds"), bool)
    }
    mark_labels = [
        row.get("label") for row in marks if isinstance(row, Mapping)
    ]
    expected_mark_labels = ["recording_started_after_gameplay_hud"]
    for span_id in expected_span_ids:
        expected_mark_labels.extend(
            [f"{span_id}_clean_begin", f"{span_id}_clean_end"]
        )
    expected_mark_labels.append("recording_stop_requested")
    checks["capture_marks_exact_and_ordered"] = (
        mark_labels == expected_mark_labels
        and all(
            isinstance(row, Mapping)
            and isinstance(row.get("seconds"), (int, float))
            and not isinstance(row.get("seconds"), bool)
            and float(row["seconds"]) >= 0
            for row in marks
        )
        and all(
            float(marks[index]["seconds"]) <= float(marks[index + 1]["seconds"])
            for index in range(len(marks) - 1)
        )
    )
    gates_value = timeline.get("clean_frame_gates")
    gates = gates_value if isinstance(gates_value, list) else []
    gate_ids = [row.get("span_id") for row in gates if isinstance(row, Mapping)]
    gate_evidence_ok = gate_ids == expected_span_ids
    for gate in gates:
        if not isinstance(gate, Mapping):
            gate_evidence_ok = False
            continue
        span_id = gate.get("span_id")
        begin = f"{span_id}_clean_begin"
        end = f"{span_id}_clean_end"
        frames = gate.get("frames")
        if not (
            gate.get("result") == "GREEN"
            and gate.get("begin_mark") == begin
            and gate.get("end_mark") == end
            and isinstance(mark_map.get(begin), (int, float))
            and isinstance(mark_map.get(end), (int, float))
            and float(mark_map[end]) > float(mark_map[begin])
            and isinstance(frames, list)
            and len(frames) == 2
        ):
            gate_evidence_ok = False
            continue
        for frame in frames:
            if not isinstance(frame, Mapping):
                gate_evidence_ok = False
                continue
            for key in ("image", "gate"):
                record = frame.get(key)
                relative = _relative(root, record.get("path") if isinstance(record, Mapping) else None)
                if relative is None or not verify_indexed(relative, f"{span_id}_{frame.get('phase')}_{key}"):
                    gate_evidence_ok = False
            image = frame.get("image") if isinstance(frame, Mapping) else None
            gate_record = frame.get("gate") if isinstance(frame, Mapping) else None
            gate_relative = _relative(
                root,
                gate_record.get("path") if isinstance(gate_record, Mapping) else None,
            )
            if gate_relative is None:
                gate_evidence_ok = False
                continue
            try:
                gate_payload = _read(
                    root / Path(*PurePosixPath(gate_relative).parts)
                )
            except (OSError, UnicodeError, json.JSONDecodeError, ValueError):
                gate_evidence_ok = False
                continue
            if not (
                frame.get("span") == span_id
                and frame.get("phase") in {"begin", "end"}
                and isinstance(image, Mapping)
                and gate_payload
                == {key: value for key, value in frame.items() if key != "gate"}
                and gate_payload.get("result") == "GREEN"
                and gate_payload.get("span") == span_id
            ):
                gate_evidence_ok = False
    checks["eight_clean_spans_hash_bound"] = gate_evidence_ok

    expected_definitions = [
        {"span_id": item.span_id, "producer_key": item.producer_key, "handler": item.handler, "postcondition": item.postcondition}
        for item in PHASE2_CAPTURE_SCENARIOS
    ]
    definitions_value = scenario.get("scenario_definitions") if isinstance(scenario, Mapping) else None
    definitions = definitions_value if isinstance(definitions_value, list) else []
    observed_definitions = [
        {key: row.get(key) for key in ("span_id", "producer_key", "handler", "postcondition")}
        for row in definitions
        if isinstance(row, Mapping)
    ]
    completed_value = scenario.get("completed_spans") if isinstance(scenario, Mapping) else None
    completed = completed_value if isinstance(completed_value, list) else []
    completed_ids = [row.get("span_id") for row in completed if isinstance(row, Mapping)]

    def collect_named(value: object, name: str) -> list[object]:
        found: list[object] = []
        if isinstance(value, Mapping):
            for key, item in value.items():
                if key == name:
                    found.append(item)
                found.extend(collect_named(item, name))
        elif isinstance(value, list):
            for item in value:
                found.extend(collect_named(item, name))
        return found

    postconditions_green = completed_ids == expected_span_ids and all(
        isinstance(row, Mapping)
        and row.get("result") == "GREEN"
        and row.get("surface_visible") is True
        and row.get("postcondition_green") is True
        and isinstance(row.get("postcondition_evidence"), Mapping)
        and row["postcondition_evidence"].get("result") == "GREEN"
        and row["postcondition_evidence"].get("surface_visible") is True
        and row["postcondition_evidence"].get("postcondition_green") is True
        for row in completed
    )
    checks["eight_span_postconditions_green"] = (
        scenario.get("result") == "GREEN"
        and scenario.get("capture_mode") == PHASE2_PROMO_CAPTURE_MODE
        and scenario.get("capture_contract_version")
        == PHASE2_PROMO_CAPTURE_CONTRACT_VERSION
        and scenario.get("capture_contract")
        == canonical_phase2_capture_contract()
        and observed_definitions == expected_definitions
        and postconditions_green
    )
    report["spans"] = [
        {
            "span_id": expected.span_id,
            "producer_key": expected.producer_key,
            "postcondition": expected.postcondition,
            "clean_gate_green": expected.span_id in gate_ids,
            "postcondition_green": expected.span_id in completed_ids
            and next(
                (row.get("postcondition_green") for row in completed if isinstance(row, Mapping) and row.get("span_id") == expected.span_id),
                False,
            )
            is True,
        }
        for expected in PHASE2_CAPTURE_SCENARIOS
    ]

    startup_value = cell.get("phase2_native_session") if isinstance(cell, Mapping) else None
    native = startup_value if isinstance(startup_value, Mapping) else {}
    startup = native.get("startup") if isinstance(native.get("startup"), Mapping) else {}
    final_binding = (
        native.get("final_binding")
        if isinstance(native.get("final_binding"), Mapping)
        else {}
    )
    cleanup = native.get("cleanup") if isinstance(native.get("cleanup"), Mapping) else {}
    observed = loaded.get("observed") if isinstance(loaded.get("observed"), Mapping) else {}
    tracked_pid = cell.get("tracked_full_acceptance_pid") if isinstance(cell, Mapping) else None
    pid_lineage = native.get("pid_lineage")
    generation_lineage = native.get("connection_generation_lineage")
    completed_pids = collect_named(completed, "bridge_pid")
    completed_generations = collect_named(completed, "connection_generation")
    completed_revisions = collect_named(completed, "revision")
    completed_native_revisions = collect_named(completed, "native_revision")

    # Compatibility is intentionally one-way: an old runner bundle must still
    # satisfy the original single-session contract.  As soon as any v2
    # span-session field is present, the complete new contract is mandatory and
    # cannot silently fall back to the legacy checks.
    span_session_rows = [
        row.get("session_evidence")
        for row in completed
        if isinstance(row, Mapping) and "session_evidence" in row
    ]
    multi_session_contract = (
        scenario.get("span_session_contract_version") is not None
        or timeline.get("capture_lineage") is not None
        or cell.get("seed_generation_loaded_chain") is not None
        or bool(span_session_rows)
    )

    if not multi_session_contract:
        legacy_binding_ok = (
            _positive_int(tracked_pid)
            and startup.get("bridge_pid") == tracked_pid
            and _positive_int(startup.get("connection_generation"))
            and loaded.get("schema_version") == 2
            and loaded.get("result") == "GREEN"
            and observed.get("bridge_pid") == tracked_pid
            and observed.get("connection_generation") == startup.get("connection_generation")
            and final_binding.get("connected") is True
            and final_binding.get("bridge_pid") == tracked_pid
            and final_binding.get("connection_generation")
            == startup.get("connection_generation")
            and isinstance(observed.get("snapshot_id"), str)
            and bool(observed.get("snapshot_id"))
            and _revision(observed.get("revision"))
            and _positive_int(observed.get("native_revision"))
            and isinstance(pid_lineage, list)
            and pid_lineage == [tracked_pid]
            and isinstance(generation_lineage, list)
            and generation_lineage == [startup.get("connection_generation")]
            and native.get("restart_count") == 0
            and cleanup.get("result") == "GREEN"
            and bool(completed_pids)
            and all(value == tracked_pid for value in completed_pids)
            and bool(completed_generations)
            and all(
                value == startup.get("connection_generation")
                for value in completed_generations
            )
            and bool(completed_revisions)
            and all(_revision(value) for value in completed_revisions)
            and bool(completed_native_revisions)
            and all(_positive_int(value) for value in completed_native_revisions)
        )
        checks["legacy_single_session_contract"] = legacy_binding_ok
        report["session_binding"] = {
            "mode": "legacy-single-session-v1",
            "tracked_ck3_pid": tracked_pid,
            "connection_generation": startup.get("connection_generation"),
            "snapshot_id": observed.get("snapshot_id"),
            "revision": observed.get("revision"),
            "native_revision": observed.get("native_revision"),
        }
    else:
        lineage_value = timeline.get("capture_lineage")
        lineage = lineage_value if isinstance(lineage_value, Mapping) else {}
        source = lineage.get("source") if isinstance(lineage.get("source"), Mapping) else {}
        checks["canonical_phase2_seed_source_game_mount_lineage"] = (
            scenario.get("span_session_contract_version")
            == SPAN_SESSION_CONTRACT_VERSION
            and _canonical_lineage(lineage)
            and timeline.get("source_git_commit") == source.get("git_commit")
            and timeline.get("source_clean_tree_sha256") == source.get("tree_sha256")
        )

        def verify_declared_record(value: object, label: str) -> bool:
            if not isinstance(value, Mapping):
                errors.append(f"{label}_record_missing")
                return False
            relative = _relative(root, value.get("path"))
            if relative is None or not verify_indexed(relative, label):
                return False
            actual = verified_records[label]
            valid = (
                value.get("bytes") == actual["bytes"]
                and isinstance(value.get("sha256"), str)
                and str(value["sha256"]).upper() == actual["sha256"]
                and int(actual["bytes"]) > 0
            )
            if not valid:
                errors.append(f"{label}_declared_record_mismatch")
            return valid

        seed_value = cell.get("seed_generation_loaded_chain")
        seed_chain = seed_value if isinstance(seed_value, Mapping) else {}
        generated = (
            seed_chain.get("generated")
            if isinstance(seed_chain.get("generated"), Mapping)
            else {}
        )
        loaded_chain = (
            seed_chain.get("loaded")
            if isinstance(seed_chain.get("loaded"), Mapping)
            else {}
        )
        seed_pid = seed_chain.get("bridge_pid")
        seed_generation = seed_chain.get("connection_generation")
        generated_save_ok = verify_declared_record(
            generated.get("save"), "canonical_seed_generated_save"
        )
        loaded_save_ok = verify_declared_record(
            loaded_chain.get("save"), "canonical_seed_loaded_save"
        )
        canonical_seed_sha = str(lineage.get("canonical_seed_save_sha256", "")).upper()
        generated_save = generated.get("save") if isinstance(generated.get("save"), Mapping) else {}
        loaded_save = loaded_chain.get("save") if isinstance(loaded_chain.get("save"), Mapping) else {}
        checks["seed_generation_to_loaded_proof_continuous"] = (
            seed_chain.get("schema_version") == 1
            and seed_chain.get("result") == "GREEN"
            and _nonempty(seed_chain.get("session_id"))
            and _positive_int(seed_pid)
            and _positive_int(seed_generation)
            and generated.get("session_id") == seed_chain.get("session_id")
            and loaded_chain.get("session_id") == seed_chain.get("session_id")
            and generated.get("bridge_pid") == seed_pid
            and loaded_chain.get("bridge_pid") == seed_pid
            and generated.get("connection_generation") == seed_generation
            and loaded_chain.get("connection_generation") == seed_generation
            and _revision(generated.get("revision"))
            and _revision(loaded_chain.get("revision"))
            and int(loaded_chain.get("revision", -1))
            >= int(generated.get("revision", 0))
            and _positive_int(generated.get("native_revision"))
            and _positive_int(loaded_chain.get("native_revision"))
            and int(loaded_chain.get("native_revision", 0))
            >= int(generated.get("native_revision", 1))
            and generated_save_ok
            and loaded_save_ok
            and str(generated_save.get("sha256", "")).upper() == canonical_seed_sha
            and str(loaded_save.get("sha256", "")).upper() == canonical_seed_sha
            and loaded.get("schema_version") == 2
            and loaded.get("result") == "GREEN"
            and observed.get("bridge_pid") == seed_pid
            and observed.get("connection_generation") == seed_generation
            and observed.get("revision") == loaded_chain.get("revision")
            and observed.get("native_revision") == loaded_chain.get("native_revision")
            and str(observed.get("save_sha256", "")).upper() == canonical_seed_sha
        )

        per_span_ok = len(span_session_rows) == len(expected_span_ids)
        exact_lineage_ok = per_span_ok
        phase2_source_only = per_span_ok
        session_summaries: list[dict[str, object]] = []
        for expected, row in zip(PHASE2_CAPTURE_SCENARIOS, completed):
            session = (
                row.get("session_evidence")
                if isinstance(row, Mapping)
                and isinstance(row.get("session_evidence"), Mapping)
                else {}
            )
            pre = session.get("pre") if isinstance(session.get("pre"), Mapping) else {}
            action = (
                session.get("action")
                if isinstance(session.get("action"), Mapping)
                else {}
            )
            post = session.get("post") if isinstance(session.get("post"), Mapping) else {}
            span_cleanup = (
                session.get("cleanup")
                if isinstance(session.get("cleanup"), Mapping)
                else {}
            )
            session_id = session.get("session_id")
            pid = session.get("bridge_pid")
            generation = session.get("connection_generation")
            start_checkpoint_ok = verify_declared_record(
                session.get("start_checkpoint"),
                f"{expected.span_id}_start_checkpoint",
            )
            end_checkpoint_ok = verify_declared_record(
                session.get("end_checkpoint"),
                f"{expected.span_id}_end_checkpoint",
            )
            start_checkpoint = (
                session.get("start_checkpoint")
                if isinstance(session.get("start_checkpoint"), Mapping)
                else {}
            )
            end_checkpoint = (
                session.get("end_checkpoint")
                if isinstance(session.get("end_checkpoint"), Mapping)
                else {}
            )
            stage_identity_ok = all(
                stage.get("session_id") == session_id
                and stage.get("bridge_pid") == pid
                and stage.get("connection_generation") == generation
                for stage in (pre, action, post)
            )
            revision_chain_ok = (
                _revision(pre.get("revision"))
                and _positive_int(pre.get("native_revision"))
                and action.get("pre_revision") == pre.get("revision")
                and action.get("pre_native_revision") == pre.get("native_revision")
                and _revision(action.get("post_revision"))
                and _positive_int(action.get("post_native_revision"))
                and post.get("revision") == action.get("post_revision")
                and post.get("native_revision") == action.get("post_native_revision")
                and int(post.get("revision", -1)) >= int(pre.get("revision", 0))
                and int(post.get("native_revision", 0))
                >= int(pre.get("native_revision", 1))
            )
            checkpoint_chain_ok = (
                start_checkpoint_ok
                and end_checkpoint_ok
                and start_checkpoint.get("save_lineage_id")
                == lineage.get("seed_lineage_id")
                and end_checkpoint.get("save_lineage_id")
                == lineage.get("seed_lineage_id")
                and str(pre.get("checkpoint_sha256", "")).upper()
                == str(start_checkpoint.get("sha256", "")).upper()
                and str(post.get("checkpoint_sha256", "")).upper()
                == str(end_checkpoint.get("sha256", "")).upper()
            )
            binding = (
                row.get("postcondition_evidence", {}).get("binding", {})
                if isinstance(row, Mapping)
                and isinstance(row.get("postcondition_evidence"), Mapping)
                and isinstance(row["postcondition_evidence"].get("binding"), Mapping)
                else {}
            )
            postcondition_bound = (
                binding.get("bridge_pid") == pid
                and binding.get("connection_generation") == generation
                and binding.get("revision") == post.get("revision")
                and binding.get("native_revision") == post.get("native_revision")
            )
            row_ok = (
                session.get("schema_version") == 1
                and session.get("result") == "GREEN"
                and session.get("span_id") == expected.span_id
                and _nonempty(session_id)
                and _positive_int(pid)
                and _positive_int(generation)
                and stage_identity_ok
                and revision_chain_ok
                and checkpoint_chain_ok
                and postcondition_bound
                and span_cleanup.get("result") == "GREEN"
                and span_cleanup.get("process_tree_gone") is True
                and span_cleanup.get("driver_closed") is True
            )
            per_span_ok = per_span_ok and row_ok
            lineage_binding = session.get("lineage_binding")
            exact_lineage_ok = exact_lineage_ok and lineage_binding == lineage
            if isinstance(lineage_binding, Mapping):
                phase2_source_only = phase2_source_only and (
                    lineage_binding.get("phase") == "zhongguo_phase2"
                    and lineage_binding.get("evidence_class") == "real_ck3"
                    and lineage_binding.get("fixture_used") is False
                    and lineage_binding.get("prior_phase_footage_used") is False
                )
            else:
                phase2_source_only = False
            session_summaries.append(
                {
                    "span_id": expected.span_id,
                    "session_id": session_id,
                    "bridge_pid": pid,
                    "connection_generation": generation,
                    "start_checkpoint_sha256": start_checkpoint.get("sha256"),
                    "end_checkpoint_sha256": end_checkpoint.get("sha256"),
                    "cleanup_green": span_cleanup.get("result") == "GREEN",
                }
            )
        checks["each_span_pre_action_post_session_continuous"] = per_span_ok
        checks["cross_span_canonical_lineage_exact"] = exact_lineage_ok
        checks["phase2_real_source_only"] = phase2_source_only
        report["session_binding"] = {
            "mode": "lineage-bound-span-sessions-v2",
            "seed_lineage_id": lineage.get("seed_lineage_id"),
            "canonical_seed_save_sha256": lineage.get(
                "canonical_seed_save_sha256"
            ),
            "source": dict(source),
            "game": dict(lineage.get("game", {}))
            if isinstance(lineage.get("game"), Mapping)
            else {},
            "mod_mount": dict(lineage.get("mod_mount", {}))
            if isinstance(lineage.get("mod_mount"), Mapping)
            else {},
            "span_sessions": session_summaries,
        }
    requirements = loaded.get("span_requirements")
    checks["loaded_seed_v2_eight_rows_green"] = (
        isinstance(requirements, list)
        and [row.get("span_id") for row in requirements if isinstance(row, Mapping)]
        == expected_span_ids
        and all(isinstance(row, Mapping) and row.get("loaded_feature_seed_ready") is True for row in requirements)
    )

    failed = [name for name, value in checks.items() if value is not True]
    report["checks"] = checks
    report["errors"] = list(dict.fromkeys([*errors, *failed]))
    if not report["errors"]:
        report["result"] = "GREEN"
        report["reason_code"] = None
    return report


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    output = args.output.expanduser().resolve()
    if output.exists():
        parser.error(f"refusing to overwrite typed intake report: {output}")
    if not output.parent.is_dir():
        parser.error(f"output parent does not exist: {output.parent}")
    report = validate_footage_intake(args.capture_root)
    output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(f"FOOTAGE INTAKE: {report['result']} [{report['reason_code']}]")
    print(f"report={output}")
    print(f"report_sha256={_sha256(output)['sha256']}")
    return 0 if report["result"] == "GREEN" else 2


if __name__ == "__main__":
    raise SystemExit(main())
