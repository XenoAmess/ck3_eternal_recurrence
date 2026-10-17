"""Read-only source/shot/native/capture index. This module never plays CK3.

An intake is an editorial map to byte-bound native observations, not an
observation producer. A structurally complete chain is still only reported
evidence: callers must assess the experiment's actual field deltas separately.
"""
from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path

from xar_promo.adapters.ck3.capture import load_capture_bundle


def load(path: Path) -> dict:
    value = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object: {path}")
    return value


def binding(path: Path) -> dict:
    path = Path(path).resolve()
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return {"path": path.as_posix(), "bytes": path.stat().st_size,
            "sha256": digest.hexdigest()}


def verify_binding(record: dict, *, root: Path) -> Path:
    if not isinstance(record, dict) or set(record) != {"path", "bytes", "sha256"}:
        raise ValueError("Expected an exact path/bytes/sha256 file binding")
    path = Path(record["path"])
    path = (path if path.is_absolute() else root / path).resolve()
    actual = binding(path)
    if (actual["bytes"] != record["bytes"]
            or actual["sha256"] != str(record["sha256"]).lower()):
        raise ValueError(f"Evidence bytes changed: {path}")
    return path


def _text(value, label):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a nonempty string")
    return value


def _number(value, label):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{label} must be a finite number")
    return value


def _utc(value, label):
    parsed = datetime.fromisoformat(_text(value, label).replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset().total_seconds() != 0:
        raise ValueError(f"{label} must have an explicit UTC offset")
    return parsed.astimezone(timezone.utc)


def _pointer(value, pointer):
    if not isinstance(pointer, str) or (pointer and not pointer.startswith("/")):
        raise ValueError("json_pointer must be empty or start with /")
    for component in pointer.split("/")[1:]:
        key = component.replace("~1", "/").replace("~0", "~")
        value = value[int(key)] if isinstance(value, list) else value[key]
    if not isinstance(value, dict) or not value:
        raise ValueError("Native evidence pointer must select a nonempty JSON object")
    return value


def _native_chain(document: dict, *, root: Path, identity: dict, phases: list) -> dict:
    references = document.get("native_chain", {})
    if set(references) != set(phases):
        raise ValueError("Intake needs exactly before/legality/decision/action/acknowledgement/after")
    observations, files = {}, {}
    for phase in phases:
        reference = references[phase]
        path = verify_binding(reference["file"], root=root)
        row = _pointer(load(path), reference["json_pointer"])
        for key in ("machine_id", "episode_id", "actor_id", "faith_id", "holy_site_instance_id"):
            if row.get(key) != identity[key]:
                raise ValueError(f"Native {phase}.{key} does not match the intake identity")
        _utc(row.get("observed_at_utc"), f"{phase}.observed_at_utc")
        _text(row.get("evidence_source"), f"{phase}.evidence_source")
        _number(row.get("frame"), f"{phase}.frame")
        if row.get("scene_revision") is None:
            raise ValueError(f"{phase}.scene_revision is required")
        observations[phase], files[phase] = row, reference
    before, legality, decision, action, ack, after = (observations[name] for name in phases)
    if legality.get("legal") is not True or not legality.get("requirements"):
        raise ValueError("One action chain needs actual legal=true and its full observed requirements")
    operation_id = _text(action.get("operation_id"), "action.operation_id")
    if action.get("submission_count") != 1 or isinstance(action.get("submission_count"), bool):
        raise ValueError("A chain must record exactly one native action submission")
    if any(row.get("operation_id") != operation_id for row in (decision, ack)):
        raise ValueError("Decision/action/ACK operation identities differ")
    if ack.get("status") not in {"accepted", "rejected", "unknown"}:
        raise ValueError("ACK status must explicitly be accepted/rejected/unknown")
    before_query = _text(before.get("query_id"), "before.query_id")
    after_query = _text(after.get("query_id"), "after.query_id")
    if after_query in {before_query, operation_id} or after.get("independent_readback") is not True:
        raise ValueError("Post-state needs a separate native query, independent of the action ACK")
    if not isinstance(before.get("state"), dict) or not isinstance(after.get("state"), dict):
        raise ValueError("Before and after must expose their actual state objects")
    if before["frame"] > action["frame"] or action["frame"] > after["frame"]:
        raise ValueError("Before/action/after frame order is inconsistent")
    if (_utc(before["observed_at_utc"], "before.UTC") > _utc(action["observed_at_utc"], "action.UTC")
            or _utc(action["observed_at_utc"], "action.UTC") > _utc(after["observed_at_utc"], "after.UTC")):
        raise ValueError("Before/action/after UTC order is inconsistent")
    return {"references": files, "reported_observations": observations,
            "operation_id": operation_id, "ack_status": ack["status"],
            "business_result_verified": False}


def build_evidence_index(plan_path: Path, intake_paths=(), *, observer: dict) -> dict:
    """Return a source-only index or verify supplied real capture intakes.

    No directories, media, run ledgers, game processes or approvals are written.
    Existing clean capture files are verified by xar-promo's CK3 adapter. Native
    snapshots are independently byte-checked and identity/order checked here.
    Those checks establish traceability, not the truth of a religious rule.
    """
    _text(observer.get("machine_id"), "observer.machine_id")
    _utc(observer.get("observed_at_utc"), "observer.observed_at_utc")
    _text(observer.get("evidence_source"), "observer.evidence_source")
    plan_path = Path(plan_path).resolve()
    plan = load(plan_path)
    if plan.get("schema") != "ck3-faith-power-pilot-plan-v1":
        raise ValueError("Unknown pilot plan schema")
    source_path = plan_path.parent / plan["source_lock"]
    source_lock = load(source_path)
    baseline = source_lock["same_version_source"]
    if baseline["commit"] != plan["source_baseline_commit"]:
        raise ValueError("Pilot plan and source lock commits differ")
    hashes = {row["path"]: row["baseline_sha256"] for row in baseline["file_results"]}
    claims = {}
    for claim in plan["claims"]:
        if claim["id"] in claims:
            raise ValueError("Duplicate claim ID")
        sources = []
        for source in claim["sources"]:
            start, end = source["lines"]
            if not isinstance(start, int) or not isinstance(end, int) or not 1 <= start <= end:
                raise ValueError("Invalid pinned source line range")
            sources.append({**source, "commit": baseline["commit"],
                            "version": baseline["declared_version"],
                            "sha256": hashes[source["path"]]})
        claims[claim["id"]] = {**claim, "sources": sources}
    pilots = {row["id"]: row for row in plan["pilots"]}
    if len(pilots) != len(plan["pilots"]):
        raise ValueError("Duplicate pilot ID")
    entries = []
    for pilot in pilots.values():
        if not set(pilot["claim_ids"]).issubset(claims):
            raise ValueError("Pilot references an unknown claim")
        entries.append({"pilot_id": pilot["id"], "shot_ids": pilot["shot_ids"],
                        "claim_ids": pilot["claim_ids"], "status": "pending-capture",
                        "native_chain": None, "raw": None, "raw_timecodes": None,
                        "final_timecodes": None, "business_result_verified": False})
    chains, seen = [], set()
    for supplied in intake_paths:
        path = Path(supplied).resolve()
        document = load(path)
        if document.get("schema") != "ck3-faith-power-capture-intake-v1":
            raise ValueError("Unknown capture intake schema")
        pilot = pilots[document["pilot_id"]]
        step_id = _text(document.get("step_id"), "step_id")
        chain_id = f"{pilot['id']}.{step_id}"
        if chain_id in seen:
            raise ValueError(f"Duplicate experiment step: {chain_id}")
        seen.add(chain_id)
        identity = document.get("identity", {})
        missing = [key for key in plan["required_identity_fields"] if identity.get(key) is None]
        if missing:
            raise ValueError(f"Missing capture identity fields: {missing}")
        if identity["machine_id"] == "unknown":
            raise ValueError("New religious experiment intakes need a verified machine identity")
        if identity["case_label"] not in plan["policy"]["case_labels"]:
            raise ValueError("Unknown case label")
        if identity["game_version"] != baseline["declared_version"]:
            raise ValueError("Capture patch differs from the source lock; create a version-bound plan first")
        native = _native_chain(document, root=path.parent, identity=identity,
                               phases=plan["required_native_chain"])
        span_ids = document.get("clean_span_ids", [])
        if not span_ids:
            raise ValueError("A production candidate needs explicit existing clean span IDs")
        capture_root = Path(document["capture_root"])
        if not capture_root.is_absolute():
            capture_root = (path.parent / capture_root).resolve()
        bundle = load_capture_bundle(capture_root, required_span_ids=span_ids)
        raw_start = _number(document.get("raw_start_seconds"), "raw_start_seconds")
        raw_end = _number(document.get("raw_end_seconds"), "raw_end_seconds")
        if not 0 <= raw_start < raw_end:
            raise ValueError("Raw selection must be a positive 1x interval")
        selected_spans = [bundle.clean_span(span_id) for span_id in span_ids]
        if not any(span.begin_seconds <= raw_start and raw_end <= span.end_seconds for span in selected_spans):
            raise ValueError("The continuous experiment selection must fit a single verified clean span")
        phase_pts = document.get("phase_raw_seconds", {})
        if set(phase_pts) != set(plan["required_native_chain"]):
            raise ValueError("Each native phase needs an original-recording timecode")
        times = [_number(phase_pts[name], f"phase_raw_seconds.{name}") for name in plan["required_native_chain"]]
        if times != sorted(times) or not all(raw_start <= point <= raw_end for point in times):
            raise ValueError("Native phase timecodes must be ordered inside the raw selection")
        chains.append({"chain_id": chain_id, "pilot_id": pilot["id"], "identity": identity,
                       "intake": binding(path), "shot_ids": pilot["shot_ids"],
                       "claim_ids": pilot["claim_ids"], "native_chain": native,
                       "capture_report": binding(bundle.report.path),
                       "capture_timeline": binding(bundle.timeline.path),
                       "capture_evidence_index": binding(bundle.evidence_index.path),
                       "raw": binding(bundle.raw_capture.path), "clean_span_ids": span_ids,
                       "raw_timecodes": {"start_seconds": raw_start, "end_seconds": raw_end,
                                         "phases": phase_pts},
                       "status": "traceable-candidate; business-interpretation-unverified",
                       "final_timecodes": None, "business_result_verified": False})
        for entry in entries:
            if entry["pilot_id"] == pilot["id"]:
                entry["status"] = "has-traceable-candidates; coverage-and-effects-unverified"
    return {"schema": "ck3-faith-power-evidence-index-v1",
            "observer": observer, "project_id": plan["project_id"], "plan": binding(plan_path),
            "source_lock": binding(source_path), "source_machine_id": source_lock.get("machine_id", "unknown"),
            "source_observed_at_utc": source_lock.get("observed_at_utc"),
            "source_machine_record_scope": "historical source provenance only; no target-machine runtime credit",
            "claims": list(claims.values()), "pilots": entries, "chains": chains,
            "render_ready": False, "human_1x_review_performed": False,
            "evidence_limit": "Structural/byte integrity and producer-reported chain, not independent religious effect validation."}
