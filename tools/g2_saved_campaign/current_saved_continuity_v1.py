"""Continuity proof validation and explicit saved-checkpoint rollback transactions.

Read-only views never repair files. The dedicated rollback transaction uses the
original ledger writer and a single lock; no function submits a game request.
"""
from __future__ import annotations

from contextlib import AbstractContextManager
from copy import deepcopy
from dataclasses import dataclass
import hashlib
from pathlib import Path
from typing import Callable, Literal, Protocol, TypeAlias

from tools.g2_saved_campaign.current_saved_basis_v1 import (
    BasisReaderV1, PinnedCheckpointValidatorV1, ValidatedCurrentSavedBasisV1, CurrentSavedBasisV1, SavedFrameV1, ExactRefV1, JsonObject, canonical_json_v1, exact_read,
    integer, json_object, need, parse_json, parse_ref, record, rows, text, utc,
)
from tools.g2_saved_campaign.file_stat_identity_v1 import (
    SCHEMA as STAT_SCHEMA, FileStatIdentityV1, normalize_file_stat_identity_v1, parse_file_stat_identity_v1,
)

MAX_CONTINUITY_BYTES = 65536
MAX_CONTINUITY_EVENTS = 256
CONTINUITY_BINDING_SCHEMA = "xar.current-saved-continuity-binding/v1"
ContinuityReducerV1: TypeAlias = Callable[[object, str, JsonObject], JsonObject]


def continuity_digest_v1(value: object) -> str:
    return hashlib.sha256(canonical_json_v1(value)).hexdigest()


def _path(value: str) -> str:
    return str(Path(text(value)).resolve()).casefold()


def validate_continuity_source_identities_v1(
    sources: tuple[tuple[ExactRefV1, FileStatIdentityV1], ...], *,
    mutable_snapshot_ref: ExactRefV1, reader: BasisReaderV1,
) -> None:
    """Recheck immutable history; only the exact historical snapshot may move."""
    need(bool(sources) and len({_path(ref.path) for ref, _ in sources}) == len(sources),
         "unique captured continuity source identities")
    need(sum(ref == mutable_snapshot_ref for ref, _ in sources) == 1,
         "one exact mutable continuity snapshot exclusion")
    for reference, identity in sources:
        need(reference.bytes == identity.bytes, "captured continuity source length")
        if reference != mutable_snapshot_ref:
            need(reader.stat(reference.path) == identity,
                 "immutable continuity source identity changed")


@dataclass(frozen=True, slots=True)
class PinnedContinuityDocumentV1:
    reference: ExactRefV1
    identity: FileStatIdentityV1
    payload: bytes

    def value(self) -> JsonObject:
        need(self.reference.bytes == self.identity.bytes == len(self.payload)
             and self.reference.bytes <= MAX_CONTINUITY_BYTES
             and hashlib.sha256(self.payload).hexdigest() == self.reference.sha256,
             "exact bounded continuity document")
        return json_object(parse_json(self.payload))


class ContinuityReaderV1(Protocol):
    def probe(self, path: str, limit: int) -> PinnedContinuityDocumentV1 | None: ...


class LocalContinuityReaderV1:
    def probe(self, path: str, limit: int) -> PinnedContinuityDocumentV1 | None:
        integer(limit, 1, MAX_CONTINUITY_BYTES)
        candidate = Path(path)
        try:
            before = candidate.stat(follow_symlinks=False)
        except FileNotFoundError:
            return None
        need(not bool(getattr(before, "st_file_attributes", 0) & 0x400),
             "continuity reparse input denied")
        identity = normalize_file_stat_identity_v1(before)
        need(identity.bytes <= limit, "bounded continuity input")
        with candidate.open("rb") as stream:
            raw = stream.read(limit + 1)
        need(normalize_file_stat_identity_v1(candidate.stat(follow_symlinks=False)) == identity
             and len(raw) == identity.bytes, "continuity changed while reading")
        return PinnedContinuityDocumentV1(
            ExactRefV1(str(candidate.resolve()), len(raw), hashlib.sha256(raw).hexdigest()),
            identity, raw)


@dataclass(frozen=True, slots=True)
class ContinuitySourceIndexV1:
    reference: ExactRefV1
    sequence: int
    identity: str
    source_key: str


@dataclass(frozen=True, slots=True)
class ContinuityReadViewV1:
    machine_id: str
    canonical_path: str
    anchor_ref: ExactRefV1
    anchor_digest: str
    anchor_sequence: int
    snapshot_ref: ExactRefV1
    event_refs: tuple[ExactRefV1, ...]
    source_indexes: tuple[ContinuitySourceIndexV1, ...]
    head_state: JsonObject
    missing_source_indexes: tuple[str, ...]
    snapshot_needs_recovery: bool
    document_identities: tuple[tuple[ExactRefV1, FileStatIdentityV1], ...]

    @property
    def head_sequence(self) -> int:
        return integer(self.head_state.get("sequence"))

    @property
    def head_digest(self) -> str:
        return continuity_digest_v1(self.head_state)

    @property
    def ready(self) -> bool:
        return not self.missing_source_indexes and not self.snapshot_needs_recovery

    def to_wire(self) -> JsonObject:
        return {
            "schema": CONTINUITY_BINDING_SCHEMA, "machine_id": self.machine_id,
            "canonical_path": self.canonical_path, "anchor_ref": self.anchor_ref.to_wire(),
            "anchor_digest": self.anchor_digest, "anchor_sequence": self.anchor_sequence,
            "snapshot_ref": self.snapshot_ref.to_wire(),
            "event_refs": [ref.to_wire() for ref in self.event_refs],
            "source_index_refs": [item.reference.to_wire() for item in self.source_indexes],
            "head_sequence": self.head_sequence, "head_digest": self.head_digest,
            "missing_source_indexes": list(self.missing_source_indexes),
            "snapshot_needs_recovery": self.snapshot_needs_recovery,
            "ready": self.ready, "ledger_writes": 0,
            "source_identities": [{"reference": ref.to_wire(), "identity": json_object(identity.to_wire())}
                                  for ref, identity in self.document_identities],
        }


def _state(value: object, machine_id: str) -> JsonObject:
    state = json_object(value)
    need(state.get("schema") == "root.ck3.continuity-window/v1"
         and state.get("machine_id") == machine_id, "continuity schema/machine")
    integer(state.get("sequence"))
    integer(state.get("window_id"), 1)
    start = integer(state.get("start_date_raw"))
    end = integer(state.get("target_date_raw"))
    need(end - start == integer(state.get("target_days"), 1) * 24,
         "continuity original target")
    need(state.get("status") in ("running", "repair_required", "complete"),
         "continuity status")
    integer(state.get("last_settled_cycles"))
    integer(state.get("last_settled_date_raw"))
    return state


def _origin(state: JsonObject) -> tuple[int, int, int, int]:
    return (integer(state.get("window_id"), 1), integer(state.get("start_date_raw")),
            integer(state.get("target_date_raw")), integer(state.get("target_days"), 1))


def _required(reader: ContinuityReaderV1, path: Path) -> PinnedContinuityDocumentV1:
    result = reader.probe(str(path), MAX_CONTINUITY_BYTES)
    need(result is not None, "missing continuity document: " + str(path))
    if result is None:
        raise ValueError("missing continuity document")
    need(_path(result.reference.path) == _path(str(path)), "canonical continuity path")
    result.value()
    return result


def read_continuity_view_v1(
    *, canonical_path: Path, anchor_ref: ExactRefV1, expected_machine_id: str,
    reader: ContinuityReaderV1,
) -> ContinuityReadViewV1:
    """Recover an in-memory head only; never call WindowLedger.load/_load."""
    machine = text(expected_machine_id)
    anchor_doc = _required(reader, Path(anchor_ref.path))
    need(anchor_doc.reference == anchor_ref, "exact trusted continuity anchor")
    snapshot_doc = _required(reader, canonical_path)
    anchor = _state(anchor_doc.value(), machine)
    snapshot = _state(snapshot_doc.value(), machine)
    initial_sequence = integer(anchor["sequence"])
    snapshot_sequence = integer(snapshot["sequence"])
    need(snapshot_sequence >= initial_sequence and _origin(snapshot) == _origin(anchor),
         "canonical snapshot cannot precede or reset anchor")
    events_dir = canonical_path.with_name("ROOT-CONTINUITY-WINDOW-EVENTS")
    state = anchor
    documents = [anchor_doc, snapshot_doc]
    event_refs: list[ExactRefV1] = []
    indexes: list[ContinuitySourceIndexV1] = []
    missing: list[str] = []
    identities: dict[str, str] = {}
    matched_snapshot = snapshot_sequence == initial_sequence
    if matched_snapshot:
        need(canonical_json_v1(snapshot) == canonical_json_v1(anchor),
             "same sequence snapshot differs")
    for _ in range(MAX_CONTINUITY_EVENTS):
        sequence = integer(state["sequence"]) + 1
        path = events_dir / f"{sequence:08d}.json"
        doc = reader.probe(str(path), MAX_CONTINUITY_BYTES)
        if doc is None:
            break
        need(_path(doc.reference.path) == _path(str(path)), "canonical event path")
        event = record(doc.value(), {"sequence", "at_utc", "kind", "details",
                                     "identity", "previous_sha256", "after"})
        need(integer(event["sequence"], 1) == sequence
             and event["previous_sha256"] == continuity_digest_v1(state),
             "continuity event gap or predecessor digest")
        utc(event["at_utc"])
        kind = text(event["kind"])
        details = json_object(event["details"])
        evidence_id = text(details.get("evidence_id"))
        need(bool(details.get("source")), "event exact source")
        identity = continuity_digest_v1({"kind": kind, "details": details})
        need(event["identity"] == identity, "event identity differs from actual contents")
        after = _state(event["after"], machine)
        need(integer(after["sequence"]) == sequence
             and after.get("last_event_identity") == identity
             and _origin(after) == _origin(anchor), "event changed sequence/origin")
        source_key = continuity_digest_v1({"kind": kind, "evidence_id": evidence_id})
        need(source_key not in identities, "committed evidence ID reused")
        identities[source_key] = identity
        index_path = events_dir / ("source-" + source_key + ".json")
        index_doc = reader.probe(str(index_path), MAX_CONTINUITY_BYTES)
        if index_doc is None:
            missing.append(str(index_path))
        else:
            need(_path(index_doc.reference.path) == _path(str(index_path)),
                 "canonical source index path")
            index = record(index_doc.value(), {"sequence", "identity"})
            need(integer(index["sequence"], 1) == sequence and index["identity"] == identity,
                 "source index conflicts with committed event")
            indexes.append(ContinuitySourceIndexV1(index_doc.reference, sequence, identity, source_key))
            documents.append(index_doc)
        event_refs.append(doc.reference)
        documents.append(doc)
        state = after
        if sequence == snapshot_sequence:
            need(canonical_json_v1(snapshot) == canonical_json_v1(state),
                 "snapshot differs from its committed event")
            matched_snapshot = True
    else:
        raise ValueError("continuity event chain exceeds finite bound")
    need(matched_snapshot, "snapshot has no exact committed lineage from anchor")
    next_path = events_dir / f"{integer(state['sequence']) + 1:08d}.json"
    need(reader.probe(str(next_path), MAX_CONTINUITY_BYTES) is None,
         "continuity head advanced during read")
    for original in documents:
        again = _required(reader, Path(original.reference.path))
        need(again.reference == original.reference and again.identity == original.identity,
             "continuity source changed during view")
    need(reader.probe(str(next_path), MAX_CONTINUITY_BYTES) is None,
         "continuity head advanced after source verification")
    return ContinuityReadViewV1(
        machine, str(canonical_path.resolve()), anchor_ref, continuity_digest_v1(anchor),
        initial_sequence, snapshot_doc.reference,
        tuple(event_refs), tuple(indexes), state, tuple(missing),
        integer(state["sequence"]) != snapshot_sequence,
        tuple((doc.reference, doc.identity) for doc in documents))


@dataclass(frozen=True, slots=True)
class ContinuityAttachmentV1:
    view: ContinuityReadViewV1
    kind: str
    details: JsonObject
    reducer_sources: tuple[ExactRefV1, ...]
    identity: str
    source_key: str
    reduced_state: JsonObject
    committed_state: JsonObject

    def to_wire(self) -> JsonObject:
        return {
            "schema": "xar.current-saved-continuity-attachment/v1",
            "view": self.view.to_wire(), "kind": self.kind,
            "details_digest": continuity_digest_v1(self.details),
            "predecessor_digest": self.view.head_digest, "identity": self.identity,
            "source_key": self.source_key,
            "reducer_sources": [ref.to_wire() for ref in self.reducer_sources],
            "reduced_digest": continuity_digest_v1(self.reduced_state),
            "after_digest": continuity_digest_v1(self.committed_state),
            "ledger_writes": 0,
        }


def dry_run_attachment_v1(
    view: ContinuityReadViewV1, *, kind: str, details: JsonObject,
    reducer: ContinuityReducerV1, reducer_sources: tuple[ExactRefV1, ...],
) -> ContinuityAttachmentV1:
    """Execute the caller's actual reducer, then the existing writer envelope."""
    need(view.ready, "continuity metadata recovery required before admission")
    need(bool(reducer_sources) and len({r.path for r in reducer_sources}) == len(reducer_sources),
         "exact reducer source chain")
    name = text(kind)
    supplied = json_object(details)
    need(supplied.get("machine_id", view.machine_id) == view.machine_id
         and bool(supplied.get("source")), "attachment machine/source")
    evidence_id = text(supplied.get("evidence_id"))
    identity = continuity_digest_v1({"kind": name, "details": supplied})
    source_key = continuity_digest_v1({"kind": name, "evidence_id": evidence_id})
    need(all(item.source_key != source_key for item in view.source_indexes),
         "attachment evidence already committed")
    previous = json_object(parse_json(canonical_json_v1(view.head_state)))
    original = canonical_json_v1(previous)
    reduced = json_object(reducer(previous, name, supplied))
    need(canonical_json_v1(previous) == original, "reducer mutated predecessor input")
    need(canonical_json_v1(reduced) != original, "attachment reducer produced no transition")
    need(_origin(reduced) == _origin(view.head_state)
         and reduced.get("machine_id") == view.machine_id, "attachment changed origin/machine")
    committed = json_object(reduced)
    committed.update(sequence=view.head_sequence + 1, last_event_identity=identity)
    return ContinuityAttachmentV1(view, name, supplied, reducer_sources, identity,
                                  source_key, reduced, committed)


def checked_attachment_reducer_v1(
    original: ContinuityReducerV1, *, attachment: ContinuityAttachmentV1,
    reader: ContinuityReaderV1,
) -> ContinuityReducerV1:
    """Recheck the real predecessor inside WindowLedger.apply's writer lock."""
    def reduce(previous: object, kind: str, details: JsonObject) -> JsonObject:
        if kind != attachment.kind:
            return original(previous, kind, details)
        current = read_continuity_view_v1(
            canonical_path=Path(attachment.view.canonical_path), anchor_ref=attachment.view.anchor_ref,
            expected_machine_id=attachment.view.machine_id, reader=reader)
        need(canonical_json_v1(current.to_wire()) == canonical_json_v1(attachment.view.to_wire()),
             "continuity source identities changed after qualification")
        need(canonical_json_v1(previous) == canonical_json_v1(attachment.view.head_state)
             and canonical_json_v1(details) == canonical_json_v1(attachment.details),
             "continuity attachment predecessor/details changed after qualification")
        result = json_object(original(previous, kind, details))
        need(canonical_json_v1(result) == canonical_json_v1(attachment.reduced_state),
             "actual reducer outcome changed after qualification")
        return result
    return reduce


def validate_continuity_binding_v1(
    value: object, *, expected_machine_id: str, reader: ContinuityReaderV1,
) -> ContinuityReadViewV1:
    row = record(value, {"schema", "machine_id", "canonical_path", "anchor_ref", "anchor_digest", "anchor_sequence", "snapshot_ref",
                         "event_refs", "source_index_refs", "head_sequence", "head_digest",
                         "missing_source_indexes", "snapshot_needs_recovery", "ready", "ledger_writes",
                         "source_identities"})
    need(row["schema"] == CONTINUITY_BINDING_SCHEMA
         and row["machine_id"] == expected_machine_id, "continuity binding schema/machine")
    view = read_continuity_view_v1(
        canonical_path=Path(text(row["canonical_path"])), anchor_ref=parse_ref(row["anchor_ref"]),
        expected_machine_id=expected_machine_id, reader=reader)
    # Canonical JSON distinguishes bool/float from the integer fields as well.
    need(canonical_json_v1(row) == canonical_json_v1(view.to_wire()),
         "continuity binding differs from actual read-only recovered view")
    return view



def reduce_saved_continuity_attachment_v1(
    previous: object, details: object, *, expected_details: JsonObject,
    expected_predecessor: JsonObject, basis_value: object,
    game: JsonObject, opening: JsonObject, progress: JsonObject,
) -> JsonObject:
    """The single saved-campaign binding reducer, shared by cold and forward."""
    old = json_object(previous)
    need(canonical_json_v1(old) == canonical_json_v1(expected_predecessor)
         and canonical_json_v1(details) == canonical_json_v1(expected_details),
         "exact frozen predecessor")
    basis = record(basis_value)
    origin = record(basis.get("origin"))
    frame = record(basis.get("frame"))
    need(integer(old.get("window_id"), 1) >= 1
         and old.get("status") in ("running", "complete", "repair_required")
         and old.get("machine_id") == basis.get("machine_id")
         and integer(old.get("start_date_raw")) == integer(origin.get("start_date_raw"))
         and integer(old.get("target_date_raw")) == integer(origin.get("target_date_raw"))
         and integer(old.get("last_settled_cycles")) == integer(progress.get("ledger_cycles"))
         and integer(old.get("last_settled_date_raw")) == integer(progress.get("ledger_date_raw")),
         "original continuity origin and exact predecessor coordinates")
    for name in ("new_ordinary_cycle_credit", "game_day_credit"):
        need(integer(expected_details.get(name)) == 0, "attachment grants no new credit")
    need(expected_details.get("original_actions_replayed") is False
         and expected_details.get("window_origin_reset") is False, "no replay or window reset")
    changed = json_object(old)
    completed = integer(basis.get("completed_cycles"))
    current_date = integer(frame.get("date_raw"))
    changed.update(
        status="complete" if current_date >= integer(origin.get("target_date_raw")) else "running",
        game_binding=game, latest_binding=opening,
        last_settled_cycles=completed, last_settled_date_raw=current_date,
        cold_handoff_count=integer(old.get("cold_handoff_count", 0)) + 1,
        last_current_saved_cold=expected_details,
        last_settled_source=json_object(record(basis.get("refs"))["settled_full_response"]),
        current_saved_reconciliation={
            "progress": progress,
            "already_settled_alignment_cycles": completed - integer(progress.get("ledger_cycles")),
            "already_settled_alignment_date_raw": current_date - integer(progress.get("ledger_date_raw")),
            "ordinary_cycle_credit": 0, "game_day_credit": 0, "original_actions_replayed": False})
    if "interruption" in old:
        changed["previous_interruption"] = old["interruption"]
    allowed = {"status", "game_binding", "latest_binding", "last_settled_cycles",
        "last_settled_date_raw", "cold_handoff_count", "last_current_saved_cold",
        "last_settled_source", "current_saved_reconciliation", "previous_interruption"}
    need(all(canonical_json_v1(changed.get(key)) == canonical_json_v1(value)
             for key, value in old.items() if key not in allowed),
         "origin/window/unknown history must remain exact")
    return changed


def validate_closed_continuity_frontier_v1(
    basis_value: object, binding: ContinuityReadViewV1,
) -> None:
    """Validate business/origin alignment without pretending that warm exists."""
    basis = record(basis_value)
    need(binding.ready, "continuity metadata recovery required before closed preparation")
    origin = record(basis.get("origin"))
    need(basis.get("machine_id") == binding.machine_id
         and integer(origin.get("start_date_raw")) == integer(binding.head_state["start_date_raw"])
         and integer(origin.get("target_date_raw")) == integer(binding.head_state["target_date_raw"])
         and integer(origin.get("target_days"), 1) == integer(binding.head_state["target_days"], 1),
         "closed basis continuity origin")
    frame = record(basis.get("frame"))
    progress = record(basis.get("progress"))
    refs = record(basis.get("refs"))
    need(parse_ref(refs.get("ledger")) == binding.anchor_ref
         and binding.anchor_digest == binding.head_digest
         and integer(progress.get("ledger_cycles")) == integer(binding.head_state["last_settled_cycles"])
         and integer(progress.get("ledger_date_raw")) == integer(binding.head_state["last_settled_date_raw"]),
         "closed basis still binds a stale continuity predecessor")
    need(integer(basis.get("completed_cycles")) == integer(binding.head_state["last_settled_cycles"])
         and integer(frame.get("date_raw")) == integer(binding.head_state["last_settled_date_raw"]),
         "closed basis and continuity settled frontier differ")



class OriginalResponseReaderV1(BasisReaderV1, Protocol):
    def read_response(self, reference: ExactRefV1, limit: int) -> bytes: ...

COMPLETED_UNSAVED_TAIL_SCHEMA_V1 = "xar.current-saved-completed-unsaved-tail/v1"
SAVED_ROLLBACK_HISTORY_KIND_V1: Literal["completed_unsaved_tail_recorded_v1"] = "completed_unsaved_tail_recorded_v1"
SAVED_ROLLBACK_KIND_V1: Literal["saved_checkpoint_rollback_verified_v1"] = "saved_checkpoint_rollback_verified_v1"

@dataclass(frozen=True, slots=True, kw_only=True)
class CompletedUnsavedTailSourcesV1:
    prior_basis: ExactRefV1
    prior_validation: ExactRefV1
    successful_full_responses: tuple[ExactRefV1, ...]
    raw_state: ExactRefV1
    raw_governance: ExactRefV1
    interruption: ExactRefV1
    inventory: ExactRefV1
    abnormal_closed_epoch: ExactRefV1
    current_driver_review: ExactRefV1
    actual_next: ExactRefV1
    canonical_checkpoint_qualification: ExactRefV1
    continuity_frontier: ExactRefV1

    def to_wire(self) -> JsonObject:
        return {"prior_basis": self.prior_basis.to_wire(),
            "prior_validation": self.prior_validation.to_wire(),
            "successful_full_responses": [r.to_wire() for r in self.successful_full_responses],
            "raw_state": self.raw_state.to_wire(), "raw_governance": self.raw_governance.to_wire(),
            "interruption": self.interruption.to_wire(), "inventory": self.inventory.to_wire(),
            "abnormal_closed_epoch": self.abnormal_closed_epoch.to_wire(),
            "current_driver_review": self.current_driver_review.to_wire(),
            "actual_next": self.actual_next.to_wire(),
            "canonical_checkpoint_qualification": self.canonical_checkpoint_qualification.to_wire(),
            "continuity_frontier": self.continuity_frontier.to_wire()}

@dataclass(frozen=True, slots=True, kw_only=True)
class CompletedUnsavedTailV1:
    machine_id: str
    observed_at_utc: str
    runtime_root: str
    sources: CompletedUnsavedTailSourcesV1

    def to_wire(self) -> JsonObject:
        return {"schema": COMPLETED_UNSAVED_TAIL_SCHEMA_V1,
            "status": "CLOSED_COMPLETED_UNSAVED_TAIL", "machine_id": self.machine_id,
            "observed_at_utc": self.observed_at_utc, "runtime_root": self.runtime_root,
            "sources": self.sources.to_wire(), "new_ordinary_cycle_credit": 0,
            "new_game_day_credit": 0, "original_actions_replayed": False,
            "Driver_history_truncated": False}

def parse_completed_unsaved_tail_v1(
    value: object, *, expected_machine_id: str,
) -> CompletedUnsavedTailV1:
    row = record(value, {"schema", "status", "machine_id", "observed_at_utc",
        "runtime_root", "sources", "new_ordinary_cycle_credit", "new_game_day_credit",
        "original_actions_replayed", "Driver_history_truncated"})
    need(row["schema"] == COMPLETED_UNSAVED_TAIL_SCHEMA_V1
        and row["status"] == "CLOSED_COMPLETED_UNSAVED_TAIL"
        and row["machine_id"] == text(expected_machine_id), "completed unsaved-tail source identity")
    integer(row["new_ordinary_cycle_credit"], 0, 0)
    integer(row["new_game_day_credit"], 0, 0)
    need(row["original_actions_replayed"] is False and row["Driver_history_truncated"] is False,
         "saved recovery never replays actions or truncates Driver")
    source = record(row["sources"], {"prior_basis", "prior_validation",
        "successful_full_responses", "raw_state", "raw_governance", "interruption",
        "inventory", "abnormal_closed_epoch", "current_driver_review", "actual_next",
        "canonical_checkpoint_qualification", "continuity_frontier"})
    full = tuple(parse_ref(item) for item in rows(source["successful_full_responses"]))
    need(0 < len(full) <= 256 and len({r.path for r in full}) == len(full),
         "finite unique original successful FULL chain")
    root = Path(text(row["runtime_root"]))
    need(root.is_absolute(), "absolute closed runtime")
    return CompletedUnsavedTailV1(machine_id=text(row["machine_id"]),
        observed_at_utc=utc(row["observed_at_utc"]), runtime_root=str(root.resolve()),
        sources=CompletedUnsavedTailSourcesV1(
            prior_basis=parse_ref(source["prior_basis"]),
            prior_validation=parse_ref(source["prior_validation"]),
            successful_full_responses=full, raw_state=parse_ref(source["raw_state"]),
            raw_governance=parse_ref(source["raw_governance"]),
            interruption=parse_ref(source["interruption"]), inventory=parse_ref(source["inventory"]),
            abnormal_closed_epoch=parse_ref(source["abnormal_closed_epoch"]),
            current_driver_review=parse_ref(source["current_driver_review"]),
            actual_next=parse_ref(source["actual_next"]),
            canonical_checkpoint_qualification=parse_ref(source["canonical_checkpoint_qualification"]),
            continuity_frontier=parse_ref(source["continuity_frontier"])))

@dataclass(frozen=True, slots=True, kw_only=True)
class ValidatedCompletedUnsavedTailV1:
    evidence_ref: ExactRefV1
    evidence: CompletedUnsavedTailV1
    saved_basis: CurrentSavedBasisV1
    current_cycles: int
    current_frame: SavedFrameV1
    actual_next_sequence: int
    driver_ref: ExactRefV1
    driver_identity: FileStatIdentityV1
    save_ref: ExactRefV1
    save_identity: FileStatIdentityV1
    history_rows: int

    @property
    def discarded_cycles(self) -> int:
        return self.current_cycles - self.saved_basis.completed_cycles

    @property
    def discarded_date_raw(self) -> int:
        return self.current_frame.date_raw - self.saved_basis.frame.date_raw

def validate_completed_unsaved_tail_evidence_v1(
    evidence_ref: ExactRefV1, *, expected_machine_id: str, reader: OriginalResponseReaderV1,
) -> ValidatedCompletedUnsavedTailV1:
    # Fixed production validator; no callback or hand-entered GREEN is accepted.
    from tools.g2_saved_campaign.current_saved_basis_v1 import (
        decode_current_saved_basis_v1, evidence, original_response_evidence_v1, parse_frame,
    )
    from tools.g2_saved_campaign.root_current_saved_campaign_cold_owner_v1 import (
        _validated_immutable_inputs_v1,
        validate_completed_unsaved_tail_epoch_evidence_v1,
        validate_completed_unsaved_tail_inventory_v1,
    )
    proof = parse_completed_unsaved_tail_v1(evidence(reader, evidence_ref, 32768),
                                           expected_machine_id=expected_machine_id)
    sources = proof.sources
    prior_basis = decode_current_saved_basis_v1(exact_read(reader, sources.prior_basis, 65536),
                                              expected_machine_id=expected_machine_id)
    prior = _validated_immutable_inputs_v1(prior_basis, basis_ref=sources.prior_basis,
        validation_ref=sources.prior_validation, reader=reader)
    raw = evidence(reader, sources.raw_state, 262144)
    governance = evidence(reader, sources.raw_governance, 262144)
    for name in ("pending_cycle", "pending_checkpoint"):
        need(name in raw and raw[name] is None, "no unsettled Native call may be discarded as completed")
    count = integer(raw.get("completed_cycles"))
    current = parse_frame(raw.get("before"))
    need(count > prior_basis.completed_cycles and current.date_raw >= prior_basis.frame.date_raw,
         "positive completed but unsaved cycle tail")
    need(current.actor_character_id == prior_basis.frame.actor_character_id
         and current.episode_run_id == prior_basis.frame.episode_run_id,
         "v1 saved rollback requires the unchanged canonical checkpoint actor/episode")
    need(canonical_json_v1(raw.get("actual_saved_checkpoint")) == canonical_json_v1(prior.checkpoint)
         and canonical_json_v1(raw.get("campaign_goal_anchor")) ==
             canonical_json_v1(prior_basis.campaign_goal_anchor)
         and integer(raw.get("start_date_raw")) == prior_basis.origin.start_date_raw,
         "tail did not create a new saved frontier or origin")
    need(integer(governance.get("completed_cycles")) == count
         and "pending_cycle" in governance and governance["pending_cycle"] is None,
         "actual terminal governance frontier")
    before_count = prior_basis.completed_cycles
    before_date = prior_basis.frame.date_raw
    sequence = prior_basis.next_sequence - 1
    for full_ref in sources.successful_full_responses:
        full = original_response_evidence_v1(reader, full_ref)
        request = record(full.get("request")); result = record(full.get("result"))
        body = record(result.get("structured_content"))
        next_count = integer(body.get("cumulative_cycles"))
        after = parse_frame(body.get("actual_end_frame"))
        need(request.get("command") == "full_loop" and full.get("client_error") is None
             and result.get("is_error") is False
             and body.get("status") == "bounded_loop_finished" and body.get("replay_allowed") is False
             and integer(request.get("sequence"), 1) > sequence
             and next_count > before_count and after.date_raw >= before_date
             and integer(body.get("actual_end_date_raw")) == after.date_raw,
             "original successful FULL sequence and frontier")
        # The original producer records actual_turns, not a synthetic starting counter.
        turns = integer(body.get("actual_turns"), 1)
        need(next_count - before_count == turns
             and turns <= integer(record(request.get("arguments")).get("max_turns"), 1),
             "complete contiguous FULL tail, not a selected suffix")
        rpc = record(body.get("full_rpc_rows_v1"))
        tools = record(rpc.get("tools"))
        for label in ("AUTO", "MET"):
            tool = record(tools.get(label))
            need(integer(tool.get("count")) == turns
                 and integer(tool.get("error_count"), 0, 0) == 0
                 and integer(tool.get("client_error_count"), 0, 0) == 0,
                 "successful original AUTO/MET rows")
        need(integer(record(tools.get("SAVE")).get("count"), 0, 0) == 0,
             "no newer SAVE exists in the discarded tail")
        before_count, before_date, sequence = next_count, after.date_raw, integer(request["sequence"], 1)
    need(before_count == count and before_date == current.date_raw,
         "all discarded progress is explained by the retained successful FULL chain")
    next_row = evidence(reader, sources.actual_next, 16384)
    actual_next = integer(next_row.get("next_sequence"), 1)
    need(actual_next > sequence, "actual unused sequence is never rolled back")
    validate_completed_unsaved_tail_inventory_v1(proof, prior=prior,
        reader=reader, actual_next_sequence=actual_next)
    closed = validate_completed_unsaved_tail_epoch_evidence_v1(proof, prior=prior, reader=reader)
    need(closed.save_ref == prior_basis.refs.save
         and closed.save_identity == prior_basis.save_identity,
         "current original Driver and unchanged canonical SAVE identities")
    canonical = parse_recovery_checkpoint_qualification_v1(
        evidence(reader, sources.canonical_checkpoint_qualification, 32768), expected_machine_id=expected_machine_id)
    need(canonical.driver_ref == closed.driver_ref and canonical.driver_identity == closed.driver_identity
         and canonical.save_ref == closed.save_ref and canonical.save_identity == closed.save_identity
         and canonical.validator_source_ref == prior_basis.refs.checkpoint_validator
         and canonical_json_v1(canonical.checkpoint) == canonical_json_v1(prior.checkpoint),
         "actual measured canonical qualification binds the exact closed checkpoint")
    return ValidatedCompletedUnsavedTailV1(evidence_ref=evidence_ref, evidence=proof,
        saved_basis=prior_basis, current_cycles=count, current_frame=current,
        actual_next_sequence=actual_next, driver_ref=closed.driver_ref,
        driver_identity=closed.driver_identity, save_ref=closed.save_ref,
        save_identity=closed.save_identity, history_rows=closed.history_rows)

def reduce_completed_unsaved_tail_history_v1(
    previous: object, validated: ValidatedCompletedUnsavedTailV1,
) -> JsonObject:
    old = _state(previous, validated.saved_basis.machine_id)
    need(integer(old.get("last_settled_cycles")) == validated.current_cycles
         and integer(old.get("last_settled_date_raw")) == validated.current_frame.date_raw,
         "rollback requires the actual completed current head")
    origin = validated.saved_basis.origin
    need(integer(old.get("start_date_raw")) == origin.start_date_raw
         and integer(old.get("target_date_raw")) == origin.target_date_raw
         and integer(old.get("target_days"), 1) == origin.target_days,
         "rollback never changes the original campaign window")
    after = json_object(old)
    after["status"] = "repair_required"
    after["unsaved_tail_recovery"] = {
        "evidence_ref": validated.evidence_ref.to_wire(), "phase": "historical_tail_recorded",
        "saved_cycles": validated.saved_basis.completed_cycles,
        "saved_date_raw": validated.saved_basis.frame.date_raw,
        "historical_cycles": validated.current_cycles, "historical_date_raw": validated.current_frame.date_raw,
        "rolled_back_cycles": validated.discarded_cycles,
        "rolled_back_date_raw": validated.discarded_date_raw,
        "ordinary_cycle_credit": 0, "game_day_credit": 0,
        "original_actions_replayed": False, "Driver_history_truncated": False}
    return after

def reduce_saved_checkpoint_rollback_v1(
    previous: object, validated: ValidatedCompletedUnsavedTailV1,
) -> JsonObject:
    old = _state(previous, validated.saved_basis.machine_id)
    recovery = record(old.get("unsaved_tail_recovery"))
    need(recovery.get("phase") == "historical_tail_recorded"
         and parse_ref(recovery.get("evidence_ref")) == validated.evidence_ref
         and integer(old.get("last_settled_cycles")) == validated.current_cycles
         and integer(old.get("last_settled_date_raw")) == validated.current_frame.date_raw,
         "rollback only follows its exact retained historical-tail event")
    after = json_object(old)
    after["last_settled_cycles"] = validated.saved_basis.completed_cycles
    after["last_settled_date_raw"] = validated.saved_basis.frame.date_raw
    after["status"] = "repair_required"
    after["last_settled_source"] = validated.saved_basis.refs.settled_full_response.to_wire()
    after["unsaved_tail_recovery"] = {**json_object(recovery), "phase": "saved_frontier_restored",
        "saved_target_frame": validated.saved_basis.frame.to_wire(),
        "requires_new_cold_binding": True}
    allowed = {"last_settled_cycles", "last_settled_date_raw",
               "status", "last_settled_source", "unsaved_tail_recovery"}
    need(all(canonical_json_v1(after.get(k)) == canonical_json_v1(v)
             for k, v in old.items() if k not in allowed),
         "window/origin/unknown and all other history fields remain exact")
    return after


RECOVERY_CHECKPOINT_QUALIFICATION_SCHEMA_V1 = "xar.current-saved-recovery-checkpoint-qualification/v1"

@dataclass(frozen=True, slots=True, kw_only=True)
class RecoveryCheckpointQualificationV1:
    machine_id: str
    observed_at_utc: str
    validator_source_ref: ExactRefV1
    driver_ref: ExactRefV1
    driver_identity: FileStatIdentityV1
    save_ref: ExactRefV1
    save_identity: FileStatIdentityV1
    checkpoint: JsonObject
    pipe_name: str

    def to_wire(self) -> JsonObject:
        return {"schema": RECOVERY_CHECKPOINT_QUALIFICATION_SCHEMA_V1,
            "status": "ORIGINAL_SDK_SAVED_CHECKPOINT_QUALIFIED",
            "machine_id": self.machine_id, "observed_at_utc": self.observed_at_utc,
            "validator_source_ref": self.validator_source_ref.to_wire(),
            "driver_ref": self.driver_ref.to_wire(),
            "driver_identity_before": json_object(self.driver_identity.to_wire()),
            "driver_identity_after": json_object(self.driver_identity.to_wire()),
            "save_ref": self.save_ref.to_wire(),
            "save_identity_before": json_object(self.save_identity.to_wire()),
            "save_identity_after": json_object(self.save_identity.to_wire()),
            "checkpoint": self.checkpoint, "pipe_name": self.pipe_name,
            "driver_physical_body_reads": 1, "driver_payload_reader_calls": 1,
            "driver_physical_read_scope": "entire_operation_including_caller_reference_measurement",
            "driver_payload_reader_scope": "pinned_reader_or_caller_premeasured_RAM",
            "original_validator_calls": 1,
            "save_sha256_calls": 1, "driver_body_rewritten": False,
            "ledger_write_already_performed": False, "game_or_RPC_calls": 0}

def parse_recovery_checkpoint_qualification_v1(
    value: object, *, expected_machine_id: str,
) -> RecoveryCheckpointQualificationV1:
    row = record(value, {"schema", "status", "machine_id", "observed_at_utc",
        "validator_source_ref", "driver_ref", "driver_identity_before", "driver_identity_after",
        "save_ref", "save_identity_before", "save_identity_after", "checkpoint", "pipe_name",
        "driver_physical_body_reads", "driver_payload_reader_calls",
        "driver_physical_read_scope", "driver_payload_reader_scope",
        "original_validator_calls", "save_sha256_calls",
        "driver_body_rewritten", "ledger_write_already_performed", "game_or_RPC_calls"})
    need(row["schema"] == RECOVERY_CHECKPOINT_QUALIFICATION_SCHEMA_V1
         and row["status"] == "ORIGINAL_SDK_SAVED_CHECKPOINT_QUALIFIED"
         and row["machine_id"] == expected_machine_id,
         "distinct measured canonical checkpoint qualification")
    for key in ("driver_physical_body_reads", "driver_payload_reader_calls", "original_validator_calls", "save_sha256_calls"):
        integer(row[key], 1, 1)
    need(row["driver_physical_read_scope"] == "entire_operation_including_caller_reference_measurement"
         and row["driver_payload_reader_scope"] == "pinned_reader_or_caller_premeasured_RAM",
         "physical and RAM payload reads have distinct scopes")
    integer(row["game_or_RPC_calls"], 0, 0)
    need(row["driver_body_rewritten"] is False and row["ledger_write_already_performed"] is False,
         "original canonical read must precede any ledger mutation")
    driver = parse_file_stat_identity_v1(row["driver_identity_before"], schema=STAT_SCHEMA)
    saved = parse_file_stat_identity_v1(row["save_identity_before"], schema=STAT_SCHEMA)
    need(driver == parse_file_stat_identity_v1(row["driver_identity_after"], schema=STAT_SCHEMA)
         and saved == parse_file_stat_identity_v1(row["save_identity_after"], schema=STAT_SCHEMA),
         "one measured stable Driver/SAVE pair")
    driver_ref, save_ref = parse_ref(row["driver_ref"]), parse_ref(row["save_ref"])
    need(driver.bytes == driver_ref.bytes and saved.bytes == save_ref.bytes,
         "actual measured file sizes")
    return RecoveryCheckpointQualificationV1(machine_id=text(row["machine_id"]),
        observed_at_utc=utc(row["observed_at_utc"]),
        validator_source_ref=parse_ref(row["validator_source_ref"]),
        driver_ref=driver_ref, driver_identity=driver,
        save_ref=save_ref, save_identity=saved, checkpoint=json_object(row["checkpoint"]),
        pipe_name=text(row["pipe_name"]))



def validate_completed_unsaved_tail_v1(
    evidence_ref: ExactRefV1, *, expected_machine_id: str, reader: OriginalResponseReaderV1,
) -> ValidatedCompletedUnsavedTailV1:
    """Current closed gate; historical readers use the evidence-only API."""
    from tools.g2_saved_campaign.current_saved_basis_v1 import evidence
    proof = parse_completed_unsaved_tail_v1(evidence(reader, evidence_ref, 32768),
                                            expected_machine_id=expected_machine_id)
    review = record(evidence(reader, proof.sources.current_driver_review, 262144))
    driver, saved = record(review.get("Driver")), record(review.get("SAVE"))
    driver_ref, save_ref = parse_ref(driver.get("ref")), parse_ref(saved.get("ref"))
    driver_identity = parse_file_stat_identity_v1(driver.get("identity"), schema=STAT_SCHEMA)
    save_identity = parse_file_stat_identity_v1(saved.get("identity"), schema=STAT_SCHEMA)
    need(reader.stat(driver_ref.path) == driver_identity and reader.stat(save_ref.path) == save_identity,
         "current closed identities before recovery evidence")
    checked = validate_completed_unsaved_tail_evidence_v1(evidence_ref,
        expected_machine_id=expected_machine_id, reader=reader)
    need(checked.driver_ref == driver_ref and checked.driver_identity == driver_identity
         and checked.save_ref == save_ref and checked.save_identity == save_identity
         and reader.stat(driver_ref.path) == driver_identity and reader.stat(save_ref.path) == save_identity,
         "current closed identities after recovery evidence")
    return checked

def _rollback_same_v1(left: object, right: object) -> bool:
    return canonical_json_v1(left) == canonical_json_v1(right)

class _OriginalViewV1(Protocol):
    @property
    def head_state(self) -> JsonObject: ...
    @property
    def head_sequence(self) -> int: ...
    @property
    def head_digest(self) -> str: ...
    @property
    def machine_id(self) -> str: ...
    @property
    def canonical_path(self) -> str: ...
    @property
    def ready(self) -> bool: ...
    def to_wire(self) -> JsonObject: ...
@dataclass(frozen=True)
class RollbackEventPlanV1:
    kind: Literal["completed_unsaved_tail_recorded_v1", "saved_checkpoint_rollback_verified_v1"]
    details: JsonObject
    reduced_state: JsonObject
    committed_state: JsonObject
@dataclass(frozen=True)
class RollbackPairPlanV1:
    proof_ref: ExactRefV1
    original_view: _OriginalViewV1
    first: RollbackEventPlanV1
    second: RollbackEventPlanV1
    transaction_id: str
class _RollbackPlanRevalidatorV1(Protocol):
    def __call__(self, proof_ref: ExactRefV1) -> RollbackPairPlanV1: ...
class RollbackPairStoreV1(Protocol):
    @property
    def canonical_path(self) -> str: ...
    def locked(self) -> AbstractContextManager[None]: ...
    def read_head(self) -> JsonObject: ...
    def read_snapshot(self) -> JsonObject: ...
    def read_event(self, sequence: int) -> JsonObject | None: ...
    def read_index(self, source_key: str) -> JsonObject | None: ...
    def create_event(self, sequence: int, event: JsonObject) -> None: ...
    def replace_snapshot(self, state: JsonObject) -> None: ...
    def create_index(self, source_key: str, index: JsonObject) -> None: ...
@dataclass(frozen=True)
class RollbackPairCommitV1:
    phase: Literal["RollbackPairCommitted"]
    transaction_id: str
    previous_sequence: int
    committed_sequence: int
    committed_digest: str
    recovered_after_first_event: bool
    writes: int
    created_events: int
@dataclass(frozen=True)
class _OperationV1:
    kind: Literal["event", "snapshot", "index"]
    sequence: int
    source_key: str
    payload: JsonObject
def _ref_wire(ref: ExactRefV1) -> JsonObject:
    path = text(ref.path)
    count = integer(ref.bytes)
    digest = text(ref.sha256)
    need(0 < count <= MAX_CONTINUITY_BYTES and len(digest) == 64 and
          all(c in "0123456789abcdef" for c in digest), "proof exact ref")
    return {"path": path, "bytes": count, "sha256": digest}
def _event_plan_wire(event: RollbackEventPlanV1) -> JsonObject:
    return {"kind": event.kind, "details": event.details,
            "reduced_state": event.reduced_state, "committed_state": event.committed_state}
def _plan_wire(plan: RollbackPairPlanV1) -> JsonObject:
    return {"proof_ref": _ref_wire(plan.proof_ref),
            "original_view": plan.original_view.to_wire(),
            "first": _event_plan_wire(plan.first), "second": _event_plan_wire(plan.second),
            "transaction_id": text(plan.transaction_id)}
def _identity(item: RollbackEventPlanV1) -> str:
    return continuity_digest_v1({"kind": item.kind, "details": item.details})
def _source_key(item: RollbackEventPlanV1) -> str:
    return continuity_digest_v1({"kind": item.kind, "evidence_id": text(item.details.get("evidence_id"))})
def _preserved(before: JsonObject, after: JsonObject) -> None:
    for key in ("schema", "machine_id", "window_id", "start_date_raw",
                "target_date_raw", "target_days", "target_years", "calendar_year_days",
                "manual_repair_count", "automatic_recovery_count", "binding_lineage_count",
                "game", "game_binding", "latest_binding"):
        need((key in before) == (key in after), "preserved field presence: " + key)
        if key in before:
            need(_rollback_same_v1(before[key], after[key]), "origin/credit/binding changed: " + key)
def _check_plan(plan: RollbackPairPlanV1) -> tuple[JsonObject, JsonObject, JsonObject]:
    view = plan.original_view
    need(type(view.ready) is bool and view.ready, "original view must be fully qualified")
    before = deepcopy(view.head_state)
    sequence = integer(before.get("sequence"))
    need(sequence == integer(view.head_sequence) and continuity_digest_v1(before) == view.head_digest,
          "original view sequence/digest")
    machine = text(view.machine_id)
    need(before.get("machine_id") == machine, "original machine")
    need(plan.first.kind == SAVED_ROLLBACK_HISTORY_KIND_V1 and plan.second.kind == SAVED_ROLLBACK_KIND_V1, "ordered rollback kinds")
    predecessor = before
    for offset, item in enumerate((plan.first, plan.second), 1):
        need(item.details.get("machine_id") == machine, "event machine")
        text(item.details.get("evidence_id"))
        text(item.details.get("source"))
        for key in ("ordinary_cycle_credit", "game_day_credit"):
            need(integer(item.details.get(key)) == 0, "zero credit required")
        need(item.details.get("original_actions_replayed") is False and
              item.details.get("window_origin_reset") is False, "no replay/origin reset")
        _preserved(before, item.reduced_state)
        need(item.reduced_state.get("status") == "repair_required", "repair status required")
        need(integer(item.reduced_state.get("sequence")) == sequence + offset - 1,
              "reducer sequence must remain predecessor")
        expected = deepcopy(item.reduced_state)
        expected.update(sequence=sequence + offset, last_event_identity=_identity(item))
        need(_rollback_same_v1(expected, item.committed_state), "committed state exact reducer projection")
        need(not _rollback_same_v1(predecessor, item.reduced_state), "event must make a real transition")
        need(integer(item.committed_state.get("sequence")) == sequence + offset, "sequence")
        predecessor = item.committed_state
    for key in ("last_settled_date_raw", "last_settled_cycles"):
        original = integer(before.get(key))
        need(integer(plan.first.committed_state.get(key)) == original,
              "first event must retain actual business head")
        need(integer(plan.second.committed_state.get(key)) <= original,
              "rollback cannot manufacture forward progress")
    need(_source_key(plan.first) != _source_key(plan.second), "distinct source keys")
    return before, deepcopy(plan.first.committed_state), deepcopy(plan.second.committed_state)
def _check_existing_event(actual: JsonObject, expected: JsonObject) -> None:
    need(set(actual) == {"sequence", "at_utc", "kind", "details", "identity",
                          "previous_sha256", "after"}, "event exact fields")
    utc(text(actual.get("at_utc")))
    for key in ("sequence", "kind", "details", "identity", "previous_sha256", "after"):
        need(_rollback_same_v1(actual.get(key), expected.get(key)), "event conflict: " + key)
def _commit_saved_rollback_pair_v1(
    store: RollbackPairStoreV1,
    plan: RollbackPairPlanV1,
    *,
    revalidate: _RollbackPlanRevalidatorV1,
    now_utc: str,
) -> RollbackPairCommitV1:
    utc(now_utc)
    with store.locked():
        head = deepcopy(store.read_head())
        submitted = canonical_json_v1(_plan_wire(plan))
        checked = revalidate(plan.proof_ref)
        need(submitted == canonical_json_v1(_plan_wire(checked)), "stale/forged rollback plan")
        need(store.canonical_path == checked.original_view.canonical_path, "ledger path binding")
        before, first, second = _check_plan(checked)
        states = (before, first, second)
        stage = -1
        for candidate_stage, candidate in enumerate(states):
            if _rollback_same_v1(head, candidate):
                stage = candidate_stage
        need(stage >= 0, "head sequence/digest CAS drift")
        need(integer(head.get("sequence")) == integer(states[stage].get("sequence")) and
              continuity_digest_v1(head) == continuity_digest_v1(states[stage]), "head CAS")
        snapshot = deepcopy(store.read_snapshot())
        snapshot_stage = -1
        for candidate_stage, candidate in enumerate(states):
            if _rollback_same_v1(snapshot, candidate):
                snapshot_stage = candidate_stage
        need(0 <= snapshot_stage <= stage, "snapshot outside exact transaction lineage")
        sequence = integer(before.get("sequence"))
        operations: list[_OperationV1] = []
        current_snapshot_stage = snapshot_stage
        for offset, item in enumerate((checked.first, checked.second), 1):
            event_sequence = sequence + offset
            event: JsonObject = {
                "sequence": event_sequence, "at_utc": now_utc, "kind": item.kind,
                "details": deepcopy(item.details), "identity": _identity(item),
                "previous_sha256": continuity_digest_v1(states[offset - 1]),
                "after": deepcopy(item.committed_state),
            }
            need(len(canonical_json_v1(event)) + 1 <= MAX_CONTINUITY_BYTES, "event receipt exceeds original cap")
            existing = store.read_event(event_sequence)
            need((existing is not None) == (offset <= stage), "head/event existence mismatch")
            if existing is not None:
                _check_existing_event(existing, event)
            source_key = _source_key(item)
            index: JsonObject = {"sequence": event_sequence, "identity": _identity(item)}
            existing_index = store.read_index(source_key)
            if existing_index is not None:
                need(existing is not None and _rollback_same_v1(existing_index, index),
                      "same evidence ID changed content/orphan source index")
            if existing is None:
                operations.append(_OperationV1("event", event_sequence, "", event))
            if current_snapshot_stage < offset:
                need(len(canonical_json_v1(item.committed_state)) + 1 <= MAX_CONTINUITY_BYTES, "snapshot cap")
                operations.append(_OperationV1("snapshot", event_sequence, "",
                                               deepcopy(item.committed_state)))
                current_snapshot_stage = offset
            if existing_index is None:
                operations.append(_OperationV1("index", event_sequence, source_key, index))
        created_events = 0
        for operation in operations:
            if operation.kind == "event":
                store.create_event(operation.sequence, deepcopy(operation.payload))
                created_events += 1
            elif operation.kind == "snapshot":
                store.replace_snapshot(deepcopy(operation.payload))
            else:
                store.create_index(operation.source_key, deepcopy(operation.payload))
        return RollbackPairCommitV1(
            phase="RollbackPairCommitted", transaction_id=checked.transaction_id,
            previous_sequence=sequence, committed_sequence=sequence + 2,
            committed_digest=continuity_digest_v1(second), recovered_after_first_event=stage > 0,
            writes=len(operations), created_events=created_events)


@dataclass(frozen=True, slots=True, kw_only=True)
class HistoricalRollbackFrontierV1:
    machine_id: str
    canonical_path: str
    anchor_ref: ExactRefV1
    head_event_ref: ExactRefV1
    writer_source_ref: ExactRefV1
    head_state: JsonObject

    @property
    def head_sequence(self) -> int:
        return integer(self.head_state.get("sequence"), 1)

    @property
    def head_digest(self) -> str:
        return continuity_digest_v1(self.head_state)

    @property
    def ready(self) -> bool:
        # Construction is private to the actual-chain validator below.
        return True

    def to_wire(self) -> JsonObject:
        return {"schema": "xar.current-saved-historical-rollback-frontier/v1",
            "machine_id": self.machine_id, "canonical_path": self.canonical_path,
            "anchor_ref": self.anchor_ref.to_wire(),
            "head_event_ref": self.head_event_ref.to_wire(),
            "writer_source_ref": self.writer_source_ref.to_wire(),
            "head_sequence": self.head_sequence, "head_digest": self.head_digest}

def validate_saved_rollback_frontier_v1(
    reference: ExactRefV1, *, validated: ValidatedCompletedUnsavedTailV1,
    reader: BasisReaderV1, continuity_reader: ContinuityReaderV1,
) -> HistoricalRollbackFrontierV1:
    from tools.g2_saved_campaign.current_saved_basis_v1 import digest, evidence
    row = record(evidence(reader, reference, 32768), {
        "schema", "machine_id", "observed_at_utc", "canonical_path",
        "anchor_ref", "head_event_ref", "writer_source_ref", "head_sequence", "head_digest"})
    need(row["schema"] == "xar.current-saved-historical-rollback-frontier/v1"
         and row["machine_id"] == validated.saved_basis.machine_id,
         "typed current saved-recovery frontier")
    utc(row["observed_at_utc"])
    canonical = Path(text(row["canonical_path"]))
    need(canonical.is_absolute(), "actual canonical ledger path")
    anchor = parse_ref(row["anchor_ref"])
    need(anchor == validated.saved_basis.refs.ledger,
         "qualified saved business ledger remains the immutable continuity anchor")
    source = parse_ref(row["writer_source_ref"])
    need(_path(source.path) == _path(str(Path(validated.evidence.runtime_root) /
                                       "root_continuity_window_c23_100.py")),
         "original frozen continuity writer source")
    exact_read(reader, source, 131072)
    current = read_continuity_view_v1(canonical_path=canonical, anchor_ref=anchor,
        expected_machine_id=validated.saved_basis.machine_id, reader=continuity_reader)
    previous_sequence = integer(row["head_sequence"], 1)
    old_event = parse_ref(row["head_event_ref"])
    need(previous_sequence > current.anchor_sequence
         and previous_sequence <= current.head_sequence
         and old_event in current.event_refs,
         "actual original event prefix and finite transaction suffix")
    event = record(evidence(reader, old_event, MAX_CONTINUITY_BYTES))
    state = _state(event.get("after"), validated.saved_basis.machine_id)
    need(integer(event.get("sequence"), 1) == previous_sequence
         and integer(state.get("sequence"), 1) == previous_sequence
         and continuity_digest_v1(state) == digest(row["head_digest"])
         and event.get("identity") == state.get("last_event_identity"),
         "captured historical predecessor has its original immutable event")
    need(integer(state.get("last_settled_cycles")) == validated.current_cycles
         and integer(state.get("last_settled_date_raw")) == validated.current_frame.date_raw,
         "current completed tail matches its actual ledger predecessor")
    # The read-only reader already validates every event digest and source index.
    # Later transaction indexes may be absent after a crash; historical indexes may not.
    expected_indexes = previous_sequence - current.anchor_sequence
    need(len([item for item in current.source_indexes
              if item.sequence <= previous_sequence]) == expected_indexes,
         "original predecessor source-index prefix must be fully committed")
    return HistoricalRollbackFrontierV1(machine_id=validated.saved_basis.machine_id,
        canonical_path=str(canonical.resolve()), anchor_ref=anchor,
        head_event_ref=old_event, writer_source_ref=source, head_state=state)

def build_saved_rollback_pair_plan_v1(
    validated: ValidatedCompletedUnsavedTailV1,
    frontier: HistoricalRollbackFrontierV1,
) -> RollbackPairPlanV1:
    before = frontier.head_state
    need(frontier.machine_id == validated.saved_basis.machine_id
         and integer(before.get("last_settled_cycles")) == validated.current_cycles
         and integer(before.get("last_settled_date_raw")) == validated.current_frame.date_raw,
         "qualified proof and exact ledger frontier")
    common: JsonObject = {"machine_id": frontier.machine_id,
        "source": validated.evidence_ref.path, "proof_ref": validated.evidence_ref.to_wire(),
        "ordinary_cycle_credit": 0, "game_day_credit": 0,
        "original_actions_replayed": False, "window_origin_reset": False}
    first_details = {**common, "evidence_id":
        "unsaved-tail-history:" + validated.evidence_ref.sha256}
    first_reduced = reduce_completed_unsaved_tail_history_v1(before, validated)
    first_identity = continuity_digest_v1({"kind": SAVED_ROLLBACK_HISTORY_KIND_V1,
                                          "details": first_details})
    first_committed = json_object(first_reduced)
    first_committed.update(sequence=frontier.head_sequence + 1, last_event_identity=first_identity)
    second_details = {**common, "evidence_id":
        "saved-checkpoint-rollback:" + validated.evidence_ref.sha256}
    second_reduced = reduce_saved_checkpoint_rollback_v1(first_committed, validated)
    second_identity = continuity_digest_v1({"kind": SAVED_ROLLBACK_KIND_V1,
                                           "details": second_details})
    second_committed = json_object(second_reduced)
    second_committed.update(sequence=frontier.head_sequence + 2, last_event_identity=second_identity)
    transaction_id = continuity_digest_v1({
        "proof_ref": validated.evidence_ref.to_wire(),
        "original_sequence": frontier.head_sequence, "original_digest": frontier.head_digest})
    return RollbackPairPlanV1(proof_ref=validated.evidence_ref, original_view=frontier,
        first=RollbackEventPlanV1(kind=SAVED_ROLLBACK_HISTORY_KIND_V1, details=first_details,
            reduced_state=first_reduced, committed_state=first_committed),
        second=RollbackEventPlanV1(kind=SAVED_ROLLBACK_KIND_V1, details=second_details,
            reduced_state=second_reduced, committed_state=second_committed),
        transaction_id=transaction_id)

# The public transaction constructs this adapter from an exact original writer.
# Callers cannot supply a reducer or a hand-entered acceptance result.
class OriginalWindowLedgerV1(Protocol):
    path: Path
    events: Path
    def locked(self) -> AbstractContextManager[None]: ...

class OriginalWindowAtomicV1(Protocol):
    def __call__(self, path: Path, value: JsonObject, replace: bool = False) -> None: ...

class _OriginalRollbackPairStoreV1:
    def __init__(self, *, canonical_path: Path, anchor_ref: ExactRefV1,
                 machine_id: str, reader: ContinuityReaderV1,
                 ledger: OriginalWindowLedgerV1, atomic: OriginalWindowAtomicV1) -> None:
        self.path = canonical_path.resolve(strict=True)
        self.anchor_ref, self.machine_id, self.reader = anchor_ref, machine_id, reader
        self.ledger, self.atomic = ledger, atomic
        need(_path(str(ledger.path)) == _path(str(self.path))
             and _path(str(ledger.events)) == _path(str(self.path.with_name("ROOT-CONTINUITY-WINDOW-EVENTS"))),
             "original ledger adapter paths")
        need(self.path.with_suffix(".lock").is_file() and ledger.events.is_dir(),
             "explicit recovery requires the original lock and event directory")
    @property
    def canonical_path(self) -> str:
        return str(self.path)
    def locked(self) -> AbstractContextManager[None]:
        return self.ledger.locked()
    def read_head(self) -> JsonObject:
        return read_continuity_view_v1(canonical_path=self.path, anchor_ref=self.anchor_ref,
            expected_machine_id=self.machine_id, reader=self.reader).head_state
    def read_snapshot(self) -> JsonObject:
        return _required(self.reader, self.path).value()
    def read_event(self, sequence: int) -> JsonObject | None:
        integer(sequence, 1)
        doc = self.reader.probe(str(self.ledger.events / f"{sequence:08d}.json"), MAX_CONTINUITY_BYTES)
        return None if doc is None else doc.value()
    def read_index(self, source_key: str) -> JsonObject | None:
        from tools.g2_saved_campaign.current_saved_basis_v1 import digest
        key = digest(source_key)
        doc = self.reader.probe(str(self.ledger.events / ("source-" + key + ".json")), MAX_CONTINUITY_BYTES)
        return None if doc is None else doc.value()
    def create_event(self, sequence: int, event: JsonObject) -> None:
        self.atomic(self.ledger.events / f"{integer(sequence,1):08d}.json", event)
    def replace_snapshot(self, state: JsonObject) -> None:
        self.atomic(self.path, state, replace=True)
    def create_index(self, source_key: str, index: JsonObject) -> None:
        from tools.g2_saved_campaign.current_saved_basis_v1 import digest
        self.atomic(self.ledger.events / ("source-" + digest(source_key) + ".json"), index)

@dataclass(frozen=True, slots=True)
class _MeasuredRecoveryCheckpointV1:
    receipt: RecoveryCheckpointQualificationV1
    driver_bytes: bytes
    payload_digest: str
    anchor: JsonObject
    validator: PinnedCheckpointValidatorV1
    token: object

_MEASURED_RECOVERY_ISSUED: dict[object, tuple[_MeasuredRecoveryCheckpointV1, str, str]] = {}

def _native_payload_digest_v1(value: object) -> str:
    # Driver history is a Python-only wire domain and can contain exact int64.
    import json
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
        separators=(",", ":"), allow_nan=False).encode("utf-8")).hexdigest()

def measure_saved_recovery_checkpoint_v1(
    *, driver_ref: ExactRefV1, driver_identity: FileStatIdentityV1,
    save_ref: ExactRefV1, save_identity: FileStatIdentityV1,
    checkpoint_validator: PinnedCheckpointValidatorV1, pipe_name: str, expected_machine_id: str,
    observed_at_utc: str, reader: BasisReaderV1,
) -> _MeasuredRecoveryCheckpointV1:
    """Execute the original SDK validator once, before any ledger write.

    The whole operation measures one physical Driver read and one SDK SAVE hash.
    reader.read may reuse the caller RAM payload already read to obtain its ExactRef.
    Physical and RAM reads are counted at their actual source, never conflated.
    The caller must hold an independent explicit storage/read authorization.
    """
    from tools.ck3_live_run_id import current_machine_id
    from tools.g2_saved_campaign.current_saved_basis_v1 import PinnedCheckpointValidatorV1
    import json
    need(expected_machine_id == current_machine_id(), "actual execution machine for canonical recovery")
    need(type(checkpoint_validator) is PinnedCheckpointValidatorV1,
         "original concrete SDK pinned validator required for measurement")
    if not isinstance(checkpoint_validator, PinnedCheckpointValidatorV1):
        raise ValueError("original pinned validator")
    exact_read(reader, checkpoint_validator.source_ref, 65536)
    need(driver_ref.bytes == driver_identity.bytes and save_ref.bytes == save_identity.bytes
         and reader.stat(driver_ref.path) == driver_identity
         and reader.stat(save_ref.path) == save_identity, "stable original files before canonical read")
    raw = reader.read(driver_ref, 268435456)
    need(type(raw) is bytes and len(raw) == driver_ref.bytes
         and hashlib.sha256(raw).hexdigest() == driver_ref.sha256,
         "one exact physical Driver payload")
    payload = record(json.loads(raw))
    raw_checkpoint = json_object(payload.get("last_checkpoint"))
    need(integer(raw_checkpoint.get("size"),1) == save_ref.bytes
         and raw_checkpoint.get("sha256") == save_ref.sha256, "original saved checkpoint bytes")
    anchor = checkpoint_validator.validate(payload,
        profile_dir=Path(save_ref.path).parent.parent, pipe_name=text(pipe_name))
    need(reader.stat(driver_ref.path) == driver_identity and reader.stat(save_ref.path) == save_identity,
         "original files unchanged after SDK canonical validation")
    receipt = RecoveryCheckpointQualificationV1(machine_id=expected_machine_id,
        observed_at_utc=utc(observed_at_utc), validator_source_ref=checkpoint_validator.source_ref,
        driver_ref=driver_ref, driver_identity=driver_identity,
        save_ref=save_ref, save_identity=save_identity, checkpoint=raw_checkpoint,
        pipe_name=text(pipe_name))
    token = object()
    measured = _MeasuredRecoveryCheckpointV1(receipt=receipt, driver_bytes=raw,
        payload_digest=_native_payload_digest_v1(payload), anchor=anchor,
        validator=checkpoint_validator, token=token)
    _MEASURED_RECOVERY_ISSUED[token] = (measured,
        _native_payload_digest_v1(receipt.to_wire()), _native_payload_digest_v1(anchor))
    return measured

def _check_measured_recovery_v1(
    measured: _MeasuredRecoveryCheckpointV1, validated: ValidatedCompletedUnsavedTailV1,
    *, reader: BasisReaderV1,
) -> None:
    from tools.g2_saved_campaign.current_saved_basis_v1 import evidence
    issued = _MEASURED_RECOVERY_ISSUED.get(measured.token)
    need(issued is not None, "same-process measured canonical result required")
    if issued is None:
        raise ValueError("unissued canonical cache")
    need(issued[0] is measured
         and issued[1] == _native_payload_digest_v1(measured.receipt.to_wire())
         and issued[2] == _native_payload_digest_v1(measured.anchor),
         "exact issued canonical cache and immutable receipt/anchor contents")
    receipt = parse_recovery_checkpoint_qualification_v1(evidence(reader,
        validated.evidence.sources.canonical_checkpoint_qualification,32768),
        expected_machine_id=validated.saved_basis.machine_id)
    original_wire, fresh_wire = receipt.to_wire(), measured.receipt.to_wire()
    original_wire.pop("observed_at_utc"); fresh_wire.pop("observed_at_utc")
    from datetime import datetime
    need(datetime.fromisoformat(measured.receipt.observed_at_utc.replace("Z","+00:00")) >=
         datetime.fromisoformat(receipt.observed_at_utc.replace("Z","+00:00")),
         "retry retains original proof and its real later canonical observation")
    need(canonical_json_v1(original_wire) == canonical_json_v1(fresh_wire)
         and receipt.driver_ref == validated.driver_ref
         and receipt.driver_identity == validated.driver_identity
         and receipt.save_ref == validated.save_ref and receipt.save_identity == validated.save_identity,
         "proof binds the actual measured canonical result")
    need(reader.stat(receipt.driver_ref.path) == receipt.driver_identity
         and reader.stat(receipt.save_ref.path) == receipt.save_identity,
         "measured original files still current")

def _original_rollback_store_v1(
    frontier: HistoricalRollbackFrontierV1, *, reader: BasisReaderV1,
    continuity_reader: ContinuityReaderV1,
) -> _OriginalRollbackPairStoreV1:
    from types import FunctionType
    from typing import runtime_checkable

    @runtime_checkable
    class LedgerShape(Protocol):
        path: Path
        events: Path
        def locked(self) -> AbstractContextManager[None]: ...
    @runtime_checkable
    class AtomicShape(Protocol):
        def __call__(self, path: Path, value: JsonObject, replace: bool = False) -> None: ...

    raw = exact_read(reader, frontier.writer_source_ref,131072)
    namespace: dict[str,object] = {"__name__":"_saved_recovery_original_writer",
                                  "__file__":frontier.writer_source_ref.path}
    exec(compile(raw,frontier.writer_source_ref.path,"exec"),namespace)
    ledger_type, atomic = namespace.get("WindowLedger"), namespace.get("_atomic")
    need(isinstance(ledger_type,type) and isinstance(atomic,FunctionType), "actual original ledger module")
    if not isinstance(ledger_type,type) or not isinstance(atomic,FunctionType):
        raise ValueError("original ledger exports")
    need(_path(atomic.__code__.co_filename) == _path(frontier.writer_source_ref.path),
         "original atomic writer exact source origin")
    instance: object = ledger_type(Path(frontier.canonical_path))
    if not isinstance(instance,LedgerShape) or not isinstance(atomic,AtomicShape):
        raise ValueError("original ledger writer interfaces")
    initializer: object = vars(ledger_type).get("__init__")
    if not isinstance(initializer,FunctionType):
        raise ValueError("original ledger initializer")
    need(_path(initializer.__code__.co_filename) == _path(frontier.writer_source_ref.path),
         "actual original ledger class source origin")
    return _OriginalRollbackPairStoreV1(canonical_path=Path(frontier.canonical_path),
        anchor_ref=frontier.anchor_ref, machine_id=frontier.machine_id,
        reader=continuity_reader, ledger=instance, atomic=atomic)

def commit_completed_unsaved_tail_recovery_v1(
    evidence_ref: ExactRefV1, *, measurement: _MeasuredRecoveryCheckpointV1,
    expected_machine_id: str, observed_at_utc: str,
    reader: OriginalResponseReaderV1, continuity_reader: ContinuityReaderV1,
) -> RollbackPairCommitV1:
    """Only the fixed validator and original writer can authorize this pair."""
    from tools.ck3_live_run_id import current_machine_id
    need(expected_machine_id == current_machine_id(), "actual recovery execution machine")
    checked = validate_completed_unsaved_tail_v1(evidence_ref,
        expected_machine_id=expected_machine_id,reader=reader)
    _check_measured_recovery_v1(measurement,checked,reader=reader)
    frontier = validate_saved_rollback_frontier_v1(checked.evidence.sources.continuity_frontier,
        validated=checked,reader=reader,continuity_reader=continuity_reader)
    plan = build_saved_rollback_pair_plan_v1(checked,frontier)
    store = _original_rollback_store_v1(frontier,reader=reader,continuity_reader=continuity_reader)

    def revalidate(proof_ref: ExactRefV1) -> RollbackPairPlanV1:
        need(proof_ref == evidence_ref,"one exact rollback proof")
        again = validate_completed_unsaved_tail_v1(proof_ref,
            expected_machine_id=expected_machine_id,reader=reader)
        _check_measured_recovery_v1(measurement,again,reader=reader)
        actual = validate_saved_rollback_frontier_v1(again.evidence.sources.continuity_frontier,
            validated=again,reader=reader,continuity_reader=continuity_reader)
        return build_saved_rollback_pair_plan_v1(again,actual)

    return _commit_saved_rollback_pair_v1(store,plan,revalidate=revalidate,
                                         now_utc=utc(observed_at_utc))

def qualify_saved_recovery_basis_v1(
    evidence_ref: ExactRefV1, *, ledger_ref: ExactRefV1,
    measurement: _MeasuredRecoveryCheckpointV1, expected_machine_id: str,
    observed_at_utc: str, reader: OriginalResponseReaderV1,
    continuity_reader: ContinuityReaderV1,
) -> ValidatedCurrentSavedBasisV1:
    """Finalize only after the real two-event head is committed and read back."""
    from dataclasses import replace
    from tools.g2_saved_campaign.current_saved_basis_v1 import (
        CurrentSavedBasisInputsV1, PinnedCheckpointValidatorV1,
        qualify_current_saved_basis_v1, evidence, record,
    )
    checked = validate_completed_unsaved_tail_v1(evidence_ref,
        expected_machine_id=expected_machine_id,reader=reader)
    _check_measured_recovery_v1(measurement,checked,reader=reader)
    frontier = validate_saved_rollback_frontier_v1(checked.evidence.sources.continuity_frontier,
        validated=checked,reader=reader,continuity_reader=continuity_reader)
    plan = build_saved_rollback_pair_plan_v1(checked,frontier)
    actual = read_continuity_view_v1(canonical_path=Path(frontier.canonical_path),
        anchor_ref=frontier.anchor_ref,expected_machine_id=expected_machine_id,reader=continuity_reader)
    need(actual.ready and actual.head_sequence == frontier.head_sequence + 2
         and actual.head_digest == continuity_digest_v1(plan.second.committed_state)
         and canonical_json_v1(evidence(reader,ledger_ref,65536)) ==
             canonical_json_v1(plan.second.committed_state),
         "actual committed rollback head before final basis qualification")
    original = measurement.validator
    if not isinstance(original,PinnedCheckpointValidatorV1):
        raise ValueError("measured original SDK validator retained")

    class MeasuredValidator(PinnedCheckpointValidatorV1):
        def validate(self,payload:object,*,profile_dir:Path,pipe_name:str)->JsonObject:
            need(_native_payload_digest_v1(payload) == measurement.payload_digest
                 and _path(str(profile_dir)) == _path(str(Path(checked.save_ref.path).parent.parent))
                 and pipe_name == measurement.receipt.pipe_name,
                 "same measured payload/profile/pipe for original qualifier")
            _check_measured_recovery_v1(measurement,checked,reader=reader)
            return json_object(measurement.anchor)

    class MeasuredReader:
        def read(self,reference:ExactRefV1,limit:int)->bytes:
            if reference == checked.driver_ref:
                need(reference.bytes <= limit and reader.stat(reference.path) == checked.driver_identity,
                     "same already measured Driver payload")
                return measurement.driver_bytes
            return reader.read(reference,limit)
        def stat(self,path:str)->FileStatIdentityV1:
            return reader.stat(path)
        def read_response(self,reference:ExactRefV1,limit:int)->bytes:
            return reader.read_response(reference,limit)

    prior = checked.saved_basis
    refs = replace(prior.refs,driver=checked.driver_ref,
        driver_close=checked.evidence.sources.current_driver_review,
        closure=evidence_ref,next=checked.evidence.sources.actual_next,ledger=ledger_ref)
    inputs = CurrentSavedBasisInputsV1(machine_id=expected_machine_id,
        observed_at_utc=utc(observed_at_utc),origin=prior.origin,refs=refs,
        driver_identity=checked.driver_identity,save_identity=checked.save_identity,
        unknown_requests=prior.unknown_requests,sidecars=prior.sidecars)
    validator = MeasuredValidator(source_ref=original.source_ref,function=original.function)
    return qualify_current_saved_basis_v1(inputs,reader=MeasuredReader(),checkpoint_validator=validator)
