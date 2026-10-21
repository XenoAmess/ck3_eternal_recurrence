"""Exact two R0176 keeper gzip carriers. No original deletion capability."""
from __future__ import annotations
import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import sys
from typing import BinaryIO, Literal
import zlib

ROOT = Path("C:/ck3-e04-resume-20261020-a01/r08-r176-keeper-lossless-2300-a01")
PAYLOAD = ROOT / "payload"
LOSS = Path("C:/ck3-e04-resume-20261020-a01/r08-r223-lossless-replacement-2200-a01")
RET = Path("C:/ck3-e04-resume-20261020-a01/r08-r223-exact-retention-2100-a01")
SUPPORT_SHA = "863849c61bae97e6d4a28ce6e7608d36ef06e8fcc453a625f70acb4a709808dd"
RET_SHA = "de1bb3c810fa361cf5f6cd63a9ba25aa5e89c614e6df1b1afc9373cf3af7a249"
if hashlib.sha256((LOSS / "lossless_exact5.py").read_bytes()).hexdigest() != SUPPORT_SHA:
    raise ValueError("Immutable byte-verifier support changed")
if hashlib.sha256((RET / "retire_exact_duplicates.py").read_bytes()).hexdigest() != RET_SHA:
    raise ValueError("Immutable identity support changed")
sys.path.insert(0, str(LOSS))
import lossless_exact5 as support

Json = support.Json
Identity = support.Identity
Pin = support.Pin
need = support.need
obj = support.shared.object_row
text = support.shared.text
integer = support.shared.integer
MACHINE = "desktop-3fevhd2-1c74096080"
CHUNK = 256 * 1024
PAYLOAD_LIMIT = 18 * 1024 * 1024
META_LIMIT = 2 * 1024 * 1024
DEADLINE = datetime(2026, 10, 20, 23, 0, tzinfo=timezone.utc)
PROTECTION_REVIEW = "2026-10-25T06:59:39.751702Z"
SOURCE_CARD = ROOT / "capacity/R176-KEEPER-LOSSLESS20-FINANCIAL-SOURCE.actual-a01.json"
SOURCE_CARD_SHA = "12334c049c52c93571548063304113d2c343199d4486c6a94d03fef1cee62b48"
PLAN = ROOT / "SOURCE-PLAN.actual-a01.json"
FREEZE = ROOT / "SOURCE-FROZEN.actual-a01.json"
BASE = Path("C:/ck3-war-episode04-research-20261004-a01/native-live-r0176-a01/responses")
R208 = Path("D:/workspace/ck3_native_war_ai_promo_work/storage-r208-response-copies-readonly-a01/TWO-RESPONSE-COPIES.plan.readonly.json")


def utc() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class Spec:
    kind: Literal["before", "after"]
    identity: Identity
    sha256: str
    gzip_bytes: int
    gzip_sha256: str

    @property
    def path(self) -> Path:
        return BASE / ("root-r0176-C-final-leg-eta-a01-" + self.kind + ".json")

    @property
    def carrier(self) -> Path:
        return PAYLOAD / (self.kind + ".json.gz")

    def to_json(self) -> dict[str, Json]:
        return {"kind": self.kind, "path": str(self.path), "identity": self.identity.to_json(),
                "sha256": self.sha256, "carrier": str(self.carrier),
                "gzip_level6_bytes": self.gzip_bytes, "gzip_level6_sha256": self.gzip_sha256}


SPECS: tuple[Spec, Spec] = (
    Spec("before", Identity("13886423844274364792", "1125899907708075", 193474721,
                           "1791245191768030400", "1791245191768030400"),
         "1d5dcdbad7e5d4e57f285b44c72d64833ce7ab8fe80c117d9174fab4cc1c174a", 8562240,
         "2ba59fe7638932c6b8e735b6f2b32c845e61fbeb908cf96dbe84d6689bef7e67"),
    Spec("after", Identity("13886423844274364792", "844424930997500", 193481991,
                          "1791245222909094600", "1791245222909094600"),
         "023552624e34dc32a28c6ae3dfcc06a82ade077ad4523eba7d52078cb545c286", 8563211,
         "87d7f2bbd533e9ee61dd54c2d9573a2ed0eab7e07ebb55418fcb97a75af91b4d"),
)


def small_pin(path: Path) -> Pin:
    return support.shared.small_pin(path)


def sizes() -> tuple[int, int]:
    payload_bytes = meta_bytes = 0
    for path in ROOT.rglob("*"):
        if path.is_file():
            need(not (path.lstat().st_file_attributes & 0x400), "Unexpected reparse output")
            if path.is_relative_to(PAYLOAD):
                payload_bytes += path.stat().st_size
            else:
                meta_bytes += path.stat().st_size
    return payload_bytes, meta_bytes


def budget(extra: int = 0, *, payload: bool = False) -> None:
    need(type(extra) is int and 0 <= extra <= PAYLOAD_LIMIT, "Exact bounded new bytes required")
    p, m = sizes()
    need(p + (extra if payload else 0) <= PAYLOAD_LIMIT and
         m + (0 if payload else extra) <= META_LIMIT, "Component budget would overflow")
    need(p + m + extra <= PAYLOAD_LIMIT + META_LIMIT, "Aggregate budget would overflow")


def write_meta(name: str, value: dict[str, Json]) -> Pin:
    path = ROOT / name
    need(path.parent == ROOT and path.suffix == ".json", "Exact metadata basename required")
    raw = (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")
    need(len(raw) <= 65536, "Small metadata bound")
    budget(len(raw))
    with path.open("xb") as stream:
        need(stream.write(raw) == len(raw), "Short metadata write")
        stream.flush()
        os.fsync(stream.fileno())
    return small_pin(path)


def source_grant() -> None:
    need(small_pin(SOURCE_CARD).sha256 == SOURCE_CARD_SHA, "Actual source capacity pin changed")
    row = support.shared.read_json(SOURCE_CARD)
    need(row.get("schema") == "xar.capacity.r176-keeper.lossless20.financial-source.v1" and
         row.get("machine_id") == MACHINE and row.get("admitted") is True and
         row.get("source_implementation_and_checks_execution_admitted") is True and
         row.get("lossless_produce_execution_admitted") is False and
         row.get("retirement_or_delete_execution_admitted") is False, "Source-only phase grant differs")
    need(Path(text(row["aggregate_root"])) == ROOT and
         row["hard_deadline_utc"] == "2026-10-20T23:00:00Z" and
         row["keeper_protection_deadline_utc"] == PROTECTION_REVIEW and
         integer(row["aggregate_ceiling_bytes"]) == PAYLOAD_LIMIT + META_LIMIT,
         "Source root/deadline/protection/budget differs")
    support.shared.checked_pin(row["quota_exception"])
    support.shared.checked_pin(row["quota_exception_scope_addendum"])
    plan = support.shared.read_json(PLAN)
    source_rows: list[Json] = [spec.to_json() for spec in SPECS]
    need(plan.get("schema") == "xar.r176-keeper.exact-two-source-plan.v1" and
         plan.get("execution_machine_id") == MACHINE and plan.get("origin_machine_id") == "unknown" and
         plan.get("sources") == source_rows and plan.get("raw_retirement_admitted") is False and
         plan.get("keeper_protection_deadline_utc") == PROTECTION_REVIEW,
         "Exact two source plan differs")
    need(support.shared.checked_pin(plan["R208_keeper_contract"]) == small_pin(R208),
         "Prior keeper contract changed")


def frozen_checks() -> None:
    source_grant()
    row = support.shared.read_json(FREEZE)
    need(row.get("schema") == "xar.r176-keeper.lossless-source-frozen.v1" and
         row.get("fixtures_passed") is True and integer(row["actual_mypy_returncode"]) == 0,
         "Actual frozen checks missing")
    for key, path in (("source_helper", ROOT / "keeper_lossless2.py"), ("source_plan", PLAN)):
        need(support.shared.parse_pin(row[key]) == small_pin(path), "Frozen source/plan changed")
    for key in ("checks_wait", "checks_output"):
        support.shared.checked_pin(row[key])
    budget()


@dataclass(frozen=True)
class Admission:
    pin: Pin
    quota_exception: Pin | None


def admit(path: Path) -> Admission:
    need(path.is_absolute() and path.parent == ROOT / "capacity", "New exact produce card under new root required")
    pin = small_pin(path)
    row = support.shared.read_json(path)
    need(row.get("schema") == "xar.capacity.r176-keeper.lossless20.produce.v1" and
         row.get("phase") == "produce_two" and row.get("machine_id") == MACHINE and
         row.get("admitted") is True and row.get("budget_status") == "GREEN" and
         row.get("lossless_produce_execution_admitted") is True and
         row.get("retirement_or_delete_execution_admitted") is False,
         "Separate produce grant required; no deletion authority")
    need(Path(text(row["aggregate_root"])) == ROOT and
         row["hard_deadline_utc"] == "2026-10-20T23:00:00Z", "Produce root/deadline differs")
    for key, expected in (("source_helper", ROOT / "keeper_lossless2.py"), ("source_plan", PLAN),
                          ("source_frozen", FREEZE), ("source_financial_admission", SOURCE_CARD)):
        need(support.shared.checked_pin(row[key]) == small_pin(expected), "Produce source binding differs")
    exception_value = row["quota_exception"]
    exception: Pin | None
    if exception_value is None:
        base = obj(row["base_budget"])
        integer(base["C_quota_margin_bytes"])
        exception = None
    else:
        exception = support.shared.checked_pin(exception_value)
        ledger = support.shared.read_json(Path("D:/workspace/.codex-task-bus/e04-capacity-reservations.json"),
                                          maximum=1024*1024)
        active = obj(ledger["active_finite_quota_exception"])
        need(support.shared.parse_pin(active["exception"]) == exception and
             datetime.now(timezone.utc) < datetime.fromisoformat(text(active["hard_deadline_utc"]).replace("Z", "+00:00")),
             "Finite quota exception absent/expired")
    need(datetime.now(timezone.utc) < DEADLINE, "Hard deadline passed")
    return Admission(pin, exception)


def tick(admission: Admission) -> None:
    need(datetime.now(timezone.utc) < DEADLINE, "Hard deadline passed; stop payload")
    need(small_pin(admission.pin.path) == admission.pin, "Produce card changed")
    budget()


def verify_gzip(stream: BinaryIO, *, expected_bytes: int, expected_sha: str,
                expected_crc: str) -> dict[str, Json]:
    try:
        return support.verify_gzip(stream, expected_bytes=expected_bytes,
                                   expected_sha=expected_sha, expected_crc=expected_crc)
    except zlib.error as error:
        raise ValueError("Gzip integrity failure: " + str(error)) from error


def source_hash(held: support.Held) -> tuple[str, str]:
    before = support.shared.stat_identity(os.fstat(held.fd))
    need(before == held.identity, "Source hash generation differs")
    os.lseek(held.fd, 0, os.SEEK_SET)
    digest = hashlib.sha256()
    crc = size = 0
    while block := os.read(held.fd, CHUNK):
        digest.update(block)
        crc = zlib.crc32(block, crc)
        size += len(block)
    need(size == held.identity.bytes and support.shared.stat_identity(os.fstat(held.fd)) == before,
         "Source second hash changed")
    return digest.hexdigest(), format(crc, "08x")


def produce(path: Path) -> int:
    frozen_checks()
    need(support.shared.machine_now() == MACHINE, "Current storage machine differs")
    admission = admit(path)
    need((DEADLINE - datetime.now(timezone.utc)).total_seconds() >= 30, "Insufficient time for bounded once")
    write_meta("PRODUCE-ONCE.actual.json",
               {"schema": "xar.r176-keeper.lossless-produce-once.v1", "execution_machine_id": MACHINE,
                "origin_machine_id": "unknown", "observed_at_utc": utc(), "admission": admission.pin.to_json(),
                "raw_retirement_admitted": False, "source_count": 2})
    PAYLOAD.mkdir(exist_ok=True)
    need(PAYLOAD.resolve(strict=True) == PAYLOAD and not any(PAYLOAD.iterdir()), "Payload root not new empty directory")
    for parent in (PAYLOAD, *PAYLOAD.parents):
        need(not (parent.lstat().st_file_attributes & 0x400), "Reparse output ancestor")
    api = support.Handles()
    held_sources: list[support.Held] = []
    held_carriers: list[support.Held] = []
    records: list[dict[str, Json]] = []
    free_before = api.free()
    error: str | None = None
    try:
        for spec in SPECS:
            held_sources.append(api.open_exact(spec.path, spec.identity))
        for spec, original in zip(SPECS, held_sources, strict=True):
            tick(admission)
            raw_sha = hashlib.sha256()
            gzip_sha = hashlib.sha256()
            compressor = zlib.compressobj(6, zlib.DEFLATED, 31)
            raw_size = gzip_size = crc = 0
            os.lseek(original.fd, 0, os.SEEK_SET)
            with spec.carrier.open("xb", buffering=0) as target:
                while block := os.read(original.fd, CHUNK):
                    tick(admission)
                    raw_sha.update(block)
                    crc = zlib.crc32(block, crc)
                    raw_size += len(block)
                    need(raw_size <= spec.identity.bytes, "Source size overflow")
                    compressed = compressor.compress(block)
                    budget(len(compressed), payload=True)
                    need(target.write(compressed) == len(compressed), "Short carrier write")
                    gzip_sha.update(compressed)
                    gzip_size += len(compressed)
                compressed = compressor.flush()
                budget(len(compressed), payload=True)
                need(target.write(compressed) == len(compressed), "Short carrier flush")
                gzip_sha.update(compressed)
                gzip_size += len(compressed)
                target.flush()
                os.fsync(target.fileno())
            need(raw_size == spec.identity.bytes and raw_sha.hexdigest() == spec.sha256 and
                 gzip_size == spec.gzip_bytes and gzip_sha.hexdigest() == spec.gzip_sha256,
                 "Source or deterministic prior RAM carrier bytes/SHA differ")
            api.check(original)
            carrier = api.open_exact(spec.carrier)
            held_carriers.append(carrier)
            os.lseek(carrier.fd, 0, os.SEEK_SET)
            with os.fdopen(os.dup(carrier.fd), "rb") as stream:
                verified = verify_gzip(stream, expected_bytes=spec.identity.bytes,
                                       expected_sha=spec.sha256, expected_crc=format(crc, "08x"))
            need(verified["compressed_bytes"] == spec.gzip_bytes and
                 verified["compressed_sha256"] == spec.gzip_sha256, "Readback carrier differs")
            second_sha, second_crc = source_hash(original)
            need(second_sha == spec.sha256 and second_crc == format(crc, "08x"), "Second original hash differs")
            allocation = api.check(carrier)
            api.check(original)
            records.append({"kind": spec.kind, "original_path": str(spec.path),
                            "original_bytes": raw_size, "original_sha256": raw_sha.hexdigest(),
                            "original_second_sha256": second_sha, "original_identity": original.identity.to_json(),
                            "original_after_identity": support.shared.stat_identity(os.fstat(original.fd)).to_json(),
                            "gzip_path": str(spec.carrier), "gzip_bytes": gzip_size,
                            "gzip_sha256": gzip_sha.hexdigest(), "gzip_identity": carrier.identity.to_json(),
                            "gzip_allocation_bytes": allocation, "readback": verified,
                            "original_still_available": True, "gzip_available_and_verified": True,
                            "raw_retired": False})
            print(json.dumps({"kind": spec.kind, "status": "GZIP_FULLY_VERIFIED", "gzip_bytes": gzip_size}), flush=True)
        for held in held_sources + held_carriers:
            api.check(held)
        tick(admission)
    except Exception as exc:
        error = type(exc).__name__ + ": " + str(exc)
    finally:
        for held in reversed(held_carriers + held_sources):
            held.close()
    free_after = api.free()
    complete = error is None and len(records) == 2
    json_records: list[Json] = [row for row in records]
    final = write_meta("PRODUCE-FINAL.actual.json",
              {"schema": "xar.r176-keeper.lossless-produce-final.v1", "execution_machine_id": MACHINE,
               "origin_machine_id": "unknown", "observed_at_utc": utc(),
               "status": "BOTH_CARRIERS_COMPLETE_AND_VERIFIED" if complete else "PARTIAL_OR_FAILED_KEEP_ALL_ORIGINALS",
               "records": json_records, "error": error, "source_plan": small_pin(PLAN).to_json(),
               "source_frozen": small_pin(FREEZE).to_json(), "admission": admission.pin.to_json(),
               "source_original_total_bytes": sum(spec.identity.bytes for spec in SPECS),
               "verified_gzip_total_bytes": sum(integer(row["gzip_bytes"]) for row in records),
               "raw_protection_deadline_utc": PROTECTION_REVIEW, "R208_contract_unchanged": True,
               "all_originals_still_available": all(spec.path.is_file() for spec in SPECS),
               "source_handles_closed": True, "carrier_handles_closed": True,
               "large_uncompressed_copy_files": 0, "raw_mutations_or_deletions": 0,
               "physical_cleanup_credit_bytes": 0, "raw_retirement_admitted": False,
               "free_before": free_before, "free_after": free_after,
               "whole_volume_free_delta_not_exclusive_attribution": True,
               "actual_payload_and_metadata_bytes": list(sizes()),
               "source_chunk_max_bytes": CHUNK, "decoded_verification_chunk_max_bytes": 1024*1024,
               "prior_RAM_method_matched": "zlib gzip wbits31 level6; no filename or timestamp",
               "future_payload_writers_after_this_final": 0})
    print(json.dumps({"final": final.to_json(), "error": error, "complete": complete}), flush=True)
    return 0 if complete else 1


def self_test() -> int:
    plain = b'{"id64":"18446744073709551615","name":"keeper"}\n' + bytes([0, 255, 254])
    compressor = zlib.compressobj(6, zlib.DEFLATED, 31)
    carrier = compressor.compress(plain) + compressor.flush()
    digest, crc = hashlib.sha256(plain).hexdigest(), format(zlib.crc32(plain), "08x")
    good = verify_gzip(io.BytesIO(carrier), expected_bytes=len(plain), expected_sha=digest, expected_crc=crc)
    need(good["compressed_sha256"] == hashlib.sha256(carrier).hexdigest() and
         good["decompressed_sha256"] == digest, "Binary producer-to-consumer roundtrip failed")
    damaged = bytearray(carrier)
    damaged[-8] ^= 1
    bad: tuple[tuple[str, bytes, str], ...] = (
        ("truncated member", carrier[:-1], digest), ("CRC corruption", bytes(damaged), digest),
        ("concatenated members", carrier + carrier, digest), ("wrong source SHA", carrier, "0"*64))
    cases: list[Json] = ["binary/source64string->gzip->CRC/fullSHA roundtrip"]
    for name, data, expected in bad:
        rejected = False
        try:
            verify_gzip(io.BytesIO(data), expected_bytes=len(plain), expected_sha=expected, expected_crc=crc)
        except ValueError:
            rejected = True
        need(rejected, "Invalid carrier accepted: " + name)
        cases.append(name + " rejected")
    print(json.dumps({"schema": "xar.r176-keeper.lossless-fixtures.v1", "status": "PASS",
                      "origin_machine_id": "synthetic", "cases": cases, "case_count": len(cases),
                      "real_source_body_reads": 0}), flush=True)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--produce-cap", type=Path)
    args = parser.parse_args()
    if args.self_test:
        need(args.produce_cap is None, "Fixture and production phases differ")
        return self_test()
    need(args.produce_cap is not None, "Separate exact produce cap required")
    return produce(args.produce_cap)


if __name__ == "__main__":
    raise SystemExit(main())
