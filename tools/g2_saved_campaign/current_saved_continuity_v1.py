"""Read-only continuity recovery and previews of the actual ledger reducer.

This module never acquires a writer lock, repairs a snapshot/index, or submits
a game request. File pins and canonical state digests have different meanings.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path
from typing import Callable, Protocol, TypeAlias

from tools.g2_saved_campaign.current_saved_basis_v1 import (
    BasisReaderV1, ExactRefV1, JsonObject, canonical_json_v1, exact_read,
    integer, json_object, need, parse_json, parse_ref, record, rows, text, utc,
)
from tools.g2_saved_campaign.file_stat_identity_v1 import (
    FileStatIdentityV1, normalize_file_stat_identity_v1,
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

