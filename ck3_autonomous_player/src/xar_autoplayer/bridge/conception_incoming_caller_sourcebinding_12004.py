"""Bind retained native ReturnAddress records to already held exact-build source.

This module reads frozen metadata/source files only. It neither queries a game nor
discovers incoming calls. A pdata row is an address extent, not a monthly role.
"""
from __future__ import annotations

from bisect import bisect_right
from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Mapping

VERSION = "1.20.0.4"
EXE_SHA256 = "98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518"
METADATA_SHA256 = "7cff93c15aa9828c187f284d874b2c0815bbe2cb716fbc172650b47681f69f7d"
RUNTIME_SHA256 = "56e8abfd647eb96df034dd025491c3d3e1bd114da1c2787da9f41b648c398245"
ENTRY_RVA = 0x2929B40
IMAGE_SIZE = 102518784
U64_MAX = (1 << 64) - 1
HELD_ROOT = Path("Z:/ck3_mod_rewrite_process_assets/g2-background-20261007/upstream-build-migration")


def _integer(value: Any, *, maximum: int = U64_MAX) -> bool:
    return type(value) is int and 0 <= value <= maximum


def _json_no_duplicates(raw: bytes) -> Any:
    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in items:
            if key in result:
                raise ValueError(f"duplicate JSON key: {key}")
            result[key] = value
        return result
    return json.loads(raw.decode("utf-8-sig"), object_pairs_hook=pairs)


def _pinned_json(path: Path, digest: str) -> Any:
    raw = path.read_bytes()
    if sha256(raw).hexdigest() != digest:
        raise ValueError(f"held source pin mismatch: {path.name}")
    return _json_no_duplicates(raw)


def _verify_direct_call_boundary(body: bytes, owner: RuntimeFunctionRow, call_rva: int) -> None:
    """Mechanical byte validation; calling this does not admit native provenance."""
    if len(body) != owner.end_rva_exclusive - owner.begin_rva:
        raise ValueError("finite caller source must cover its admitted pdata row")
    from capstone import Cs, CS_ARCH_X86, CS_MODE_64
    cursor = owner.begin_rva
    found = False
    for instruction in Cs(CS_ARCH_X86, CS_MODE_64).disasm(body, cursor):
        if instruction.address != cursor:
            raise ValueError("caller source instruction-boundary gap")
        if cursor == call_rva:
            encoded = bytes(instruction.bytes)
            if instruction.mnemonic != "call" or len(encoded) != 5 or encoded[0] != 0xE8:
                raise ValueError("retained callsite is not a direct E8 CALL instruction")
            target = cursor + 5 + int.from_bytes(encoded[1:], "little", signed=True)
            if target != ENTRY_RVA:
                raise ValueError("retained CALL target differs from 2929B40")
            found = True
        cursor += instruction.size
    if cursor != owner.end_rva_exclusive or not found:
        raise ValueError("retained CALL is not on the frozen decoded instruction boundary")


@dataclass(frozen=True)
class ExactImage:
    version: str
    executable_sha256: str
    module_base: int


@dataclass(frozen=True)
class RuntimeFunctionRow:
    ordinal: int
    begin_rva: int
    end_rva_exclusive: int
    unwind_rva: int

    def wire(self) -> dict[str, int]:
        return {"ordinal": self.ordinal, "begin_rva": self.begin_rva,
                "end_rva_exclusive": self.end_rva_exclusive, "unwind_rva": self.unwind_rva}


@dataclass(frozen=True)
class FrozenLiteralCallProof:
    """Admitted finite held source, supplied by the source owner, never by a wire event.

    A manually reviewed source contract binds the bytes and the reached callsite.
    Factory decoding checks its direct instruction boundary and target. The source
    contract still cannot assign a monthly role without separate upstream source.
    """
    proof_id: str
    owner: RuntimeFunctionRow
    call_rva: int
    return_rva: int
    source_sha256: str
    source_contract_sha256: str
    provenance: str

    @classmethod
    def from_frozen_files(cls, *, proof_id: str, owner: RuntimeFunctionRow,
                          call_rva: int, source_path: Path, source_sha256: str,
                          contract_path: Path, contract_sha256: str) -> FrozenLiteralCallProof:
        if source_path.stat().st_size > 8192:
            raise ValueError("finite caller source exceeds the 8192-byte admitted batch")
        body = source_path.read_bytes()
        if sha256(body).hexdigest() != source_sha256:
            raise ValueError("finite caller source pin mismatch")
        contract = _pinned_json(contract_path, contract_sha256)
        if (contract.get("schema") != "xar.finite-incoming-call-sourceproof.v1"
                or contract.get("executable_sha256", "").lower() != EXE_SHA256
                or contract.get("runtime_metadata_sha256") != RUNTIME_SHA256
                or contract.get("source_sha256") != source_sha256
                or contract.get("owner") != owner.wire()
                or contract.get("call_rva") != call_rva
                or contract.get("target_rva") != ENTRY_RVA
                or contract.get("manual_reached_call_review") is not True
                or contract.get("provenance") != "finite-actual-held-native-source"):
            raise ValueError("caller source contract is not admitted exact native source")
        _verify_direct_call_boundary(body, owner, call_rva)
        return cls(proof_id, owner, call_rva, call_rva + 5, source_sha256,
                   contract_sha256, "finite-actual-held-native-source")


class CallerSourceResolver:
    def __init__(self, *, rows: tuple[RuntimeFunctionRow, ...],
                 executable_extents: tuple[tuple[int, int], ...],
                 proofs: tuple[FrozenLiteralCallProof, ...] = (),
                 metadata_provenance: str = "exact-held-12004-metadata"):
        if not rows or any(a.begin_rva >= b.begin_rva or a.end_rva_exclusive > b.begin_rva
                           for a, b in zip(rows, rows[1:])):
            raise ValueError("runtime rows must be sorted and nonoverlapping")
        for row in rows:
            if (not _integer(row.ordinal) or not _integer(row.begin_rva, maximum=IMAGE_SIZE)
                    or not _integer(row.end_rva_exclusive, maximum=IMAGE_SIZE)
                    or not _integer(row.unwind_rva, maximum=IMAGE_SIZE - 1)
                    or row.begin_rva >= row.end_rva_exclusive):
                raise ValueError("invalid runtime row")
        if any(not (0 <= begin < end <= IMAGE_SIZE) for begin, end in executable_extents):
            raise ValueError("invalid executable metadata extent")
        self._rows = rows
        self._begins = tuple(row.begin_rva for row in rows)
        self._extents = executable_extents
        self._provenance = metadata_provenance
        self._proofs: dict[int, FrozenLiteralCallProof] = {}
        for proof in proofs:
            if (proof.return_rva in self._proofs or proof.return_rva != proof.call_rva + 5
                    or self.owner_at(proof.return_rva - 1) != proof.owner
                    or proof.provenance != "finite-actual-held-native-source"):
                raise ValueError("literal proof is not bound to the held runtime row")
            self._proofs[proof.return_rva] = proof

    @classmethod
    def from_held_metadata(cls, metadata_path: Path | None = None,
                           runtime_path: Path | None = None,
                           proofs: tuple[FrozenLiteralCallProof, ...] = ()) -> CallerSourceResolver:
        metadata = _pinned_json(metadata_path or HELD_ROOT / "global-pe-diff/NEW-PE-METADATA.json",
                                METADATA_SHA256)
        runtime = _pinned_json(runtime_path or HELD_ROOT / "function-match-core/NEW-RUNTIME-FUNCTIONS.json",
                               RUNTIME_SHA256)
        versions = metadata["embedded_versions"]["native_1_20_version_candidates"]
        if (metadata["optional_header"]["SizeOfImage"] != IMAGE_SIZE
                or not any(row["value"] == VERSION for row in versions)
                or runtime["schema"] != "ck3.runtime-function-table.v1"
                or runtime["row_fields"] != ["begin_rva", "end_rva_exclusive", "unwind_rva"]):
            raise ValueError("held metadata contract changed")
        rows = tuple(RuntimeFunctionRow(i, *row) for i, row in enumerate(runtime["rows"]))
        extents = tuple((section["rva_start"], section["rva_virtual_end_exclusive"])
                        for section in metadata["sections"] if section["Characteristics"] & 0x20000000)
        return cls(rows=rows, executable_extents=extents, proofs=proofs)

    def owner_at(self, rva: int) -> RuntimeFunctionRow | None:
        index = bisect_right(self._begins, rva) - 1
        if index >= 0 and rva < self._rows[index].end_rva_exclusive:
            return self._rows[index]
        return None

    def bind(self, image: ExactImage, caller_return_pc: Any,
             caller_return_rva: Any = None) -> dict[str, Any]:
        result: dict[str, Any] = {
            "schema": "xar.conception-incoming-caller-sourcebinding.v1",
            "target_entry_rva": ENTRY_RVA, "binding_status": "unavailable",
            "reason": "exact-image-not-admitted", "normalized_return_rva": None,
            "runtime_function_row": None, "metadata_provenance": self._provenance,
            "metadata_sha256": METADATA_SHA256, "runtime_metadata_sha256": RUNTIME_SHA256,
            "literal_call_status": "unknown", "literal_call_proof": None,
            "caller_function_role": "unknown", "monthly_or_stage_role": "unknown",
            "natural_observation_verified_by_this_consumer": False,
        }
        if (image.version != VERSION or not isinstance(image.executable_sha256, str)
                or image.executable_sha256.lower() != EXE_SHA256
                or not _integer(image.module_base) or image.module_base == 0
                or image.module_base > U64_MAX - IMAGE_SIZE):
            return result
        if not _integer(caller_return_pc) or not image.module_base < caller_return_pc <= image.module_base + IMAGE_SIZE:
            result["reason"] = "return-address-outside-admitted-image"
            return result
        rva = caller_return_pc - image.module_base
        if caller_return_rva is not None and (not _integer(caller_return_rva) or caller_return_rva != rva):
            result["reason"] = "retained-rva-disagrees-with-raw-return-address"
            return result
        result["normalized_return_rva"] = rva
        if not any(begin <= rva - 1 < end for begin, end in self._extents):
            result["reason"] = "preceding-return-address-byte-is-not-executable"
            return result
        owner = self.owner_at(rva - 1)
        if owner is None:
            result["binding_status"] = "unknown-source"
            result["reason"] = "no-held-runtime-function-row-for-preceding-return-address-byte"
            return result
        result["runtime_function_row"] = owner.wire()
        result["binding_status"] = "metadata-bound-source-unknown"
        result["reason"] = "no-held-finite-incoming-call-sourceproof"
        proof = self._proofs.get(rva)
        if proof is not None:
            result["binding_status"] = "literal-call-source-bound"
            result["reason"] = "exact-held-literal-call-to-2929B40"
            result["literal_call_status"] = "confirmed-finite-native-source"
            result["literal_call_proof"] = {
                "proof_id": proof.proof_id, "call_rva": proof.call_rva,
                "return_rva": proof.return_rva, "target_rva": ENTRY_RVA,
                "source_sha256": proof.source_sha256,
                "source_contract_sha256": proof.source_contract_sha256,
                "provenance": proof.provenance,
            }
        return result


def bind_owned_record(record: Mapping[str, Any], *, image: ExactImage,
                      resolver: CallerSourceResolver,
                      identity: Mapping[str, Any]) -> dict[str, Any]:
    """Pure adapter. Caller passes retained record and its own immutable journal key.

    The result carries only supplied event identity and source binding. It makes no
    assertion that a caller-supplied record is a natural hit; the journal owner is
    responsible for that provenance. Input record and nested identity are unchanged.
    """
    from copy import deepcopy
    binding = resolver.bind(image, record.get("caller_return_pc"), record.get("caller_return_rva"))
    return {"schema": "xar.conception-owned-caller-sourcebinding.v1",
            "event_identity": deepcopy(dict(identity)), "caller_source_binding": binding}


def bind_owned_journal(journal: Mapping[str, Any], *, image: ExactImage,
                       resolver: CallerSourceResolver) -> dict[str, Any]:
    """Consume 19b SerializeConceptionPairPassiveJournal12004's retained events.

    Instantiate the resolver once, then attach this separate immutable result to
    the already obtained parent query. A current-session guard is supplied by the
    journal owner; this consumer does not read clocks or establish live freshness.
    """
    from copy import deepcopy
    records = journal.get("events")
    guards = {name: deepcopy(journal.get(name)) for name in (
        "observer_installed", "current_session_guard", "clock_identity",
        "oldest_available_sequence", "latest_sequence", "overwritten_events",
        "unattributed_identity_events")}
    result: dict[str, Any] = {"schema": "xar.conception-owned-journal-sourcebinding.v1",
                             "journal_guards": guards, "records": [],
                             "status": "unavailable", "reason": "owned-journal-guard-unavailable",
                             "monthly_or_stage_role": "unknown"}
    if (journal.get("schema") != "xar.ck3.conception-pair-passive-12004.v1"
            or journal.get("source") != "natural_2929B40_original_once"
            or journal.get("build_version") != image.version
            or not isinstance(journal.get("source_pin"), str)
            or journal["source_pin"].lower() != EXE_SHA256
            or not _integer(journal.get("image_base"))
            or journal["image_base"] != image.module_base):
        result["reason"] = "owned-journal-exact-image-mismatch"
        return result
    if journal.get("observer_installed") is not True or journal.get("current_session_guard") is not True:
        return result
    if not isinstance(records, list) or not all(isinstance(record, Mapping) for record in records):
        result["reason"] = "owned-journal-events-unavailable"
        return result
    if not _integer(journal.get("event_count")) or journal["event_count"] != len(records):
        result["reason"] = "owned-journal-event-count-mismatch"
        return result
    result["status"] = "retained-records-bound"
    result["reason"] = "metadata-and-sourceproof-states-are-independent-from-natural-scheduling"
    for record in records:
        identity = {name: deepcopy(record.get(name)) for name in (
            "source_pin", "journal_sequence", "process_id", "thread_id", "before_event", "completed_event",
            "fixture_origin", "original_called_once", "original_returned",
            "generation_unchanged", "event_clock_and_thread_match")}
        bound = bind_owned_record(record, image=image, resolver=resolver, identity=identity)
        if not isinstance(record.get("source_pin"), str) or record["source_pin"].lower() != EXE_SHA256:
            binding = bound["caller_source_binding"]
            binding.update(binding_status="unavailable", reason="owned-event-source-pin-mismatch",
                           normalized_return_rva=None, runtime_function_row=None,
                           literal_call_status="unknown", literal_call_proof=None)
        result["records"].append(bound)
    return result


def main() -> int:
    """Offline retained-wire entry. Exact image facts must be supplied explicitly."""
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--journal", type=Path, required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--exe-sha256", required=True)
    parser.add_argument("--module-base", type=lambda value: int(value, 0), required=True)
    parser.add_argument("--metadata", type=Path)
    parser.add_argument("--runtime-functions", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    raw = args.journal.read_bytes()
    journal = _json_no_duplicates(raw)
    if not isinstance(journal, Mapping):
        raise ValueError("retained journal must be an object")
    resolver = CallerSourceResolver.from_held_metadata(args.metadata, args.runtime_functions)
    result = bind_owned_journal(journal, image=ExactImage(args.version, args.exe_sha256, args.module_base),
                                resolver=resolver)
    result["retained_input_sha256"] = sha256(raw).hexdigest()
    result["literal_call_registry_entries"] = 0
    with args.output.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(result, handle, indent=2)
        handle.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
