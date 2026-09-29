"""Durable, append-only record of quoted war cash awaiting reconciliation.

This ledger covers actions submitted by one owned driver. It never certifies
that *all* game-side or other-writer war commitments have been observed, so it
must not directly fill the M5 ``pending_war_cash_raw`` field. An absent or
empty ledger is unknown, never proof of zero.
"""

from __future__ import annotations

from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
from typing import Iterator, Mapping


SCHEMA = "xar.ck3.war-cash-pending-ledger.v1"
_ZERO_SHA = "0" * 64
_FRAME_KEYS = frozenset({
    "played_character_id", "native_revision", "date_raw", "snapshot_id",
    "revision", "episode_run_id",
})


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def _bounded_file_sha256(path: Path, *, max_bytes: int) -> str:
    if not isinstance(path, Path) or not path.is_file():
        raise ValueError("pending source checkpoint file is missing")
    size = path.stat().st_size
    if not 0 < size <= max_bytes:
        raise ValueError("pending source checkpoint exceeds bounded read")
    digest = hashlib.sha256()
    count = 0
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            count += len(chunk)
            if count > max_bytes:
                raise ValueError("pending source checkpoint grew during read")
            digest.update(chunk)
    if count != size:
        raise ValueError("pending source checkpoint changed during read")
    return digest.hexdigest().upper()


def _bounded_read_bytes(path: Path, *, max_bytes: int) -> bytes:
    if not isinstance(path, Path) or not path.is_file():
        raise ValueError("pending source file is missing")
    size = path.stat().st_size
    if not 0 < size <= max_bytes:
        raise ValueError("pending source file exceeds bounded read")
    with path.open("rb") as source:
        data = source.read(max_bytes + 1)
    if len(data) != size:
        raise ValueError("pending source file changed during bounded read")
    return data


def _canonical(value: object) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _sha(value: object) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(
        character in "0123456789ABCDEF" for character in value
    )


def _positive(value: object) -> bool:
    return type(value) is int and value > 0


def _nonnegative(value: object) -> bool:
    return type(value) is int and value >= 0


def _frame(value: object) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != _FRAME_KEYS or not (
        _positive(value["played_character_id"])
        and _positive(value["native_revision"])
        and _nonnegative(value["date_raw"])
        and isinstance(value["snapshot_id"], str)
        and value["snapshot_id"]
        and _positive(value["revision"])
        and isinstance(value["episode_run_id"], str)
        and value["episode_run_id"]
    ):
        raise ValueError("war cash ledger requires an exact paused source frame")
    return dict(value)


def _action(value: object) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != {
        "selected_step", "command_kind", "typed_arguments", "route_sha256",
    }:
        raise ValueError("war cash action identity is incomplete")
    if not (
        isinstance(value["selected_step"], str) and value["selected_step"]
        and isinstance(value["command_kind"], str) and value["command_kind"]
        and isinstance(value["typed_arguments"], dict)
        and all(isinstance(key, str) and key for key in value["typed_arguments"])
        and (value["route_sha256"] is None or _sha(value["route_sha256"]))
    ):
        raise ValueError("war cash action identity has invalid values")
    # Canonical encoding rejects non-JSON values before they enter the ledger.
    _canonical(value)
    return dict(value)


def _quote(value: object, *, episode_run_id: str, war_id: int) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != {
        "source_frame", "war_id", "priced_action", "raw", "scale",
        "price_source_kind", "price_evidence_sha256",
    }:
        raise ValueError("war cash quote shape is incomplete")
    source_frame = _frame(value["source_frame"])
    action = _action(value["priced_action"])
    if (
        source_frame["episode_run_id"] != episode_run_id
        or type(value["war_id"]) is not int
        or value["war_id"] != war_id
        or not _nonnegative(value["raw"])
        or value["scale"] != 100_000
        or value["price_source_kind"] not in {
            "native_exact_q100000", "proved_zero_native_command",
        }
        or not _sha(value["price_evidence_sha256"])
    ):
        raise ValueError("war cash quote lacks same-episode typed price evidence")
    if (value["raw"] == 0) != (value["price_source_kind"] == "proved_zero_native_command"):
        raise ValueError("zero war cash quote needs a proved-zero source")
    return {**value, "source_frame": source_frame, "priced_action": action}


def ledger_path(state_dir: Path, *, episode_run_id: str, war_id: int) -> Path:
    if not isinstance(episode_run_id, str) or not episode_run_id or not _positive(war_id):
        raise ValueError("war cash ledger scope identity is invalid")
    key = _digest(_canonical({"episode_run_id": episode_run_id, "war_id": war_id}))[:24]
    return Path(state_dir) / "native-session" / "war-cash" / f"{key}.jsonl"


def _no_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    value: dict[str, object] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("war cash ledger has duplicate JSON keys")
        value[key] = item
    return value


def _records(path: Path, *, frozen_data: bytes | None = None) -> list[dict[str, object]]:
    if frozen_data is None and not path.exists():
        return []
    data = path.read_bytes() if frozen_data is None else frozen_data
    if not data:
        return []
    if not data.endswith(b"\n"):
        raise ValueError("war cash ledger has an incomplete final record")
    records: list[dict[str, object]] = []
    previous = _ZERO_SHA
    try:
        lines = data.decode("utf-8").splitlines()
        for expected_seq, line in enumerate(lines, 1):
            row = json.loads(line, object_pairs_hook=_no_duplicate_keys)
            if not isinstance(row, dict) or set(row) != {
                "seq", "prev_sha256", "event", "sha256",
            }:
                raise ValueError("war cash ledger record shape changed")
            body = {key: row[key] for key in ("seq", "prev_sha256", "event")}
            if (
                type(row["seq"]) is not int or row["seq"] != expected_seq
                or row["prev_sha256"] != previous
                or not _sha(row["sha256"])
                or _digest(_canonical(body)) != row["sha256"]
            ):
                raise ValueError("war cash ledger hash chain changed")
            records.append(row)
            previous = row["sha256"]
    except (UnicodeError, json.JSONDecodeError) as error:
        raise ValueError("war cash ledger is not valid UTF-8 JSONL") from error
    return records


@contextmanager
def _locked(path: Path) -> Iterator[None]:
    path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = path.with_suffix(".lock")
    with lock_path.open("a+b") as handle:
        if os.name == "nt":
            import msvcrt

            handle.seek(0, os.SEEK_END)
            if handle.tell() == 0:
                handle.write(b"\0")
                handle.flush()
            handle.seek(0)
            try:
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            except OSError as error:
                raise ValueError("war cash ledger is owned by another writer") from error
            try:
                yield
            finally:
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            try:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as error:
                raise ValueError("war cash ledger is owned by another writer") from error
            try:
                yield
            finally:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _append(path: Path, event: dict[str, object], *, expected_sha256: str) -> None:
    with _locked(path):
        prior = _records(path)
        if not prior or prior[-1]["sha256"] != expected_sha256:
            raise ValueError("war cash ledger changed before append; reload scope")
        body = {
            "seq": len(prior) + 1,
            "prev_sha256": prior[-1]["sha256"] if prior else _ZERO_SHA,
            "event": event,
        }
        record = {**body, "sha256": _digest(_canonical(body))}
        with path.open("ab") as handle:
            handle.write(_canonical(record) + b"\n")
            handle.flush()
            os.fsync(handle.fileno())


def open_war_cash_scope_v1(
    state_dir: Path, *, episode_run_id: str, war_id: int,
    owner_id: str, source_checkpoint_sha256: str,
) -> Path:
    """Create one scoped journal; this alone proves no cash coverage."""
    path = ledger_path(state_dir, episode_run_id=episode_run_id, war_id=war_id)
    if not isinstance(owner_id, str) or not owner_id or not _sha(source_checkpoint_sha256):
        raise ValueError("war cash scope lacks owner/checkpoint identity")
    with _locked(path):
        if path.exists():
            raise ValueError("war cash scope already exists")
        body = {"seq": 1, "prev_sha256": _ZERO_SHA, "event": {
            "kind": "scope_open", "schema": SCHEMA,
            "episode_run_id": episode_run_id, "war_id": war_id,
            "owner_id": owner_id, "source_checkpoint_sha256": source_checkpoint_sha256,
        }}
        record = {**body, "sha256": _digest(_canonical(body))}
        with path.open("ab") as handle:
            handle.write(_canonical(record) + b"\n")
            handle.flush()
            os.fsync(handle.fileno())
    return path


def _replay(
    path: Path, *, episode_run_id: str, war_id: int,
    frozen_data: bytes | None = None,
) -> dict[str, object] | None:
    records = _records(path, frozen_data=frozen_data)
    if not records:
        return None
    first = records[0]["event"]
    if not isinstance(first, dict) or set(first) != {
        "kind", "schema", "episode_run_id", "war_id", "owner_id",
        "source_checkpoint_sha256",
    } or first.get("kind") != "scope_open" or first.get("schema") != SCHEMA or (
        first.get("episode_run_id"), first.get("war_id")
    ) != (episode_run_id, war_id) or type(first.get("war_id")) is not int or not isinstance(first.get("owner_id"), str) or not first["owner_id"] or not _sha(first.get("source_checkpoint_sha256")):
        raise ValueError("war cash ledger scope identity changed")
    pending: dict[str, dict[str, object]] = {}
    pending_checkpoint_sha256: dict[str, str] = {}
    resolved: set[str] = set()
    acknowledged: set[str] = set()
    for record in records[1:]:
        event = record["event"]
        if not isinstance(event, dict):
            raise ValueError("war cash ledger event is malformed")
        kind = event.get("kind")
        request_id = event.get("request_id")
        if not isinstance(request_id, str) or not request_id:
            raise ValueError("war cash ledger request identity is missing")
        if kind == "reserve":
            if set(event) != {"kind", "request_id", "quote", "source_checkpoint_sha256"} or request_id in pending or request_id in resolved or not _sha(event["source_checkpoint_sha256"]):
                raise ValueError("war cash ledger reservation is duplicated or malformed")
            pending[request_id] = _quote(event["quote"], episode_run_id=episode_run_id, war_id=war_id)
            pending_checkpoint_sha256[request_id] = event["source_checkpoint_sha256"]
        elif kind == "ack":
            if set(event) != {"kind", "request_id", "action_sha256", "ack_status"} or request_id not in pending or request_id in acknowledged or event["ack_status"] != "submitted_verification_pending" or event["action_sha256"] != _digest(_canonical(pending[request_id]["priced_action"])):
                raise ValueError("war cash ledger ACK does not match a pending action")
            acknowledged.add(request_id)
        elif kind == "resolve":
            receipt = event.get("independent_receipt")
            if set(event) != {"kind", "request_id", "action_sha256", "independent_receipt"} or request_id not in pending or not isinstance(receipt, dict) or set(receipt) != {
                "request_id", "action_sha256", "episode_run_id", "war_id",
                "postcondition_verified", "status", "charged_raw",
                "source_sha256", "post_frame",
            }:
                raise ValueError("war cash resolution lacks an independent receipt")
            action_sha = _digest(_canonical(pending[request_id]["priced_action"]))
            post_frame = _frame(receipt["post_frame"])
            if (
                event["action_sha256"] != action_sha
                or receipt["request_id"] != request_id
                or receipt["action_sha256"] != action_sha
                or receipt["episode_run_id"] != episode_run_id
                or type(receipt["war_id"]) is not int
                or receipt["war_id"] != war_id
                or receipt["postcondition_verified"] is not True
                or receipt["status"] not in {"charged", "not_applied"}
                or not _nonnegative(receipt["charged_raw"])
                or receipt["charged_raw"] != (
                    pending[request_id]["raw"] if receipt["status"] == "charged" else 0
                )
                or not _sha(receipt["source_sha256"])
                or post_frame["episode_run_id"] != episode_run_id
                or post_frame["played_character_id"] != pending[request_id]["source_frame"]["played_character_id"]
            ):
                raise ValueError("war cash resolution disagrees with its quote")
            del pending[request_id]
            del pending_checkpoint_sha256[request_id]
            resolved.add(request_id)
        else:
            raise ValueError("war cash ledger event kind is unknown")
    return {"scope": first, "pending": pending,
            "pending_checkpoint_sha256": pending_checkpoint_sha256,
            "resolved": resolved,
            "acknowledged": acknowledged, "event_count": len(records),
            "last_sha256": records[-1]["sha256"]}


def reserve_war_cash_action_v1(
    state_dir: Path, *, episode_run_id: str, war_id: int,
    request_id: str, quote: Mapping[str, object],
    source_checkpoint_sha256: str, current_frame: Mapping[str, object],
) -> None:
    path = ledger_path(state_dir, episode_run_id=episode_run_id, war_id=war_id)
    state = _replay(path, episode_run_id=episode_run_id, war_id=war_id)
    if state is None or not isinstance(request_id, str) or not request_id or request_id in state["pending"] or request_id in state["resolved"] or not _sha(source_checkpoint_sha256):
        raise ValueError("war cash reserve requires a unique owned scope/action")
    normalized = _quote(dict(quote), episode_run_id=episode_run_id, war_id=war_id)
    if normalized["source_frame"] != _frame(dict(current_frame)):
        raise ValueError("war cash reserve quote is not from the current paused frame")
    _append(path, {"kind": "reserve", "request_id": request_id,
                   "quote": normalized,
                   "source_checkpoint_sha256": source_checkpoint_sha256},
            expected_sha256=state["last_sha256"])


def record_war_cash_ack_v1(
    state_dir: Path, *, episode_run_id: str, war_id: int,
    request_id: str, priced_action: Mapping[str, object],
) -> None:
    path = ledger_path(state_dir, episode_run_id=episode_run_id, war_id=war_id)
    state = _replay(path, episode_run_id=episode_run_id, war_id=war_id)
    action = _action(dict(priced_action))
    if state is None or request_id not in state["pending"] or request_id in state["acknowledged"] or state["pending"][request_id]["priced_action"] != action:
        raise ValueError("war cash ACK needs the unresolved priced action")
    _append(path, {"kind": "ack", "request_id": request_id,
                   "action_sha256": _digest(_canonical(action)),
                   "ack_status": "submitted_verification_pending"},
            expected_sha256=state["last_sha256"])


def resolve_war_cash_action_v1(
    state_dir: Path, *, episode_run_id: str, war_id: int,
    request_id: str, independent_receipt: Mapping[str, object],
) -> None:
    path = ledger_path(state_dir, episode_run_id=episode_run_id, war_id=war_id)
    state = _replay(path, episode_run_id=episode_run_id, war_id=war_id)
    if state is None or request_id not in state["pending"]:
        raise ValueError("war cash resolution has no unresolved action")
    action_sha = _digest(_canonical(state["pending"][request_id]["priced_action"]))
    event = {"kind": "resolve", "request_id": request_id,
             "action_sha256": action_sha,
             "independent_receipt": dict(independent_receipt)}
    # Validate the entire candidate before appending; a bad receipt must not
    # poison the immutable journal.
    receipt = event["independent_receipt"]
    if not isinstance(receipt, dict) or receipt.get("request_id") != request_id or receipt.get("action_sha256") != action_sha or receipt.get("episode_run_id") != episode_run_id or type(receipt.get("war_id")) is not int or receipt.get("war_id") != war_id or receipt.get("postcondition_verified") is not True or receipt.get("status") not in {"charged", "not_applied"} or not _nonnegative(receipt.get("charged_raw")) or receipt.get("charged_raw") != (state["pending"][request_id]["raw"] if receipt.get("status") == "charged" else 0) or not _sha(receipt.get("source_sha256")) or _frame(receipt.get("post_frame"))["episode_run_id"] != episode_run_id or receipt["post_frame"]["played_character_id"] != state["pending"][request_id]["source_frame"]["played_character_id"]:
        raise ValueError("war cash independent receipt is not matching")
    if set(receipt) != {"request_id", "action_sha256", "episode_run_id", "war_id", "postcondition_verified", "status", "charged_raw", "source_sha256", "post_frame"}:
        raise ValueError("war cash independent receipt shape is incomplete")
    _append(path, event, expected_sha256=state["last_sha256"])


def observe_recorded_war_cash_pending_v1(
    state_dir: Path, *, episode_run_id: str, war_id: int,
    current_frame: Mapping[str, object],
) -> dict[str, object]:
    """Return the recorded lower bound; never infer complete pending or zero."""
    frame = _frame(dict(current_frame))
    if frame["episode_run_id"] != episode_run_id:
        raise ValueError("war cash pending observation crossed episode")
    path = ledger_path(state_dir, episode_run_id=episode_run_id, war_id=war_id)
    state = _replay(path, episode_run_id=episode_run_id, war_id=war_id)
    if state is None:
        return {"schema": SCHEMA, "status": "uninitialized_unknown",
                "recorded_unresolved_quote_sum_raw": None,
                "pending_war_cash_raw": None, "formal_cash_receipt_eligible": False,
                "unresolved_request_ids": [], "source_frame": frame,
                "war_id": war_id, "ledger_sha256": None}
    pending = state["pending"]
    if any(frame["date_raw"] < row["source_frame"]["date_raw"] for row in pending.values()):
        status = "restore_before_quoted_frame_requires_requery"
        lower = None
    else:
        status = "recorded_scope_only_no_writer_coverage"
        lower = sum(row["raw"] for row in pending.values())
    return {"schema": SCHEMA, "status": status,
            "recorded_unresolved_quote_sum_raw": lower,
            "pending_war_cash_raw": None, "formal_cash_receipt_eligible": False,
            "unresolved_request_ids": sorted(pending), "source_frame": frame,
            "war_id": war_id, "ledger_sha256": state["last_sha256"]}


def inspect_owned_pending_source_bytes_v1(
    state_dir: Path, *, episode_run_id: str, war_id: int,
    snapshot: Mapping[str, object], expected_ledger_file_sha256: str | None,
    checkpoint_path: Path | None, expected_checkpoint_sha256: str,
    quote_evidence_paths: Mapping[str, Path],
) -> dict[str, object]:
    """Authenticate one frozen owned-writer subset, never all war commitments.

    File hashes prove exact supplied bytes, not that a native quote is pure,
    priced for this payer, or complete across CK3 and other writers. The
    standard pending field therefore stays null even for a positive subset.
    """
    if not isinstance(snapshot, Mapping):
        raise ValueError("pending source needs a paused snapshot")
    frame = _frame({key: snapshot.get(key) for key in _FRAME_KEYS})
    wars = snapshot.get("active_wars")
    played = snapshot.get("played_character")
    if (snapshot.get("paused") is not True
            or snapshot.get("map_ready") is not True
            or not isinstance(played, Mapping)
            or type(played.get("character_id")) is not int
            or played["character_id"] != frame["played_character_id"]
            or type(war_id) is not int or war_id <= 0
            or not isinstance(wars, list)
            or sum(isinstance(row, Mapping) and type(row.get("war_id")) is int
                   and row["war_id"] == war_id
                   for row in wars) != 1
            or frame["episode_run_id"] != episode_run_id):
        raise ValueError("pending source crossed paused player, WarID or episode")
    if (not _sha(expected_checkpoint_sha256)
            or not isinstance(quote_evidence_paths, Mapping)):
        raise ValueError("pending source lacks exact checkpoint/evidence identity")
    path = ledger_path(state_dir, episode_run_id=episode_run_id, war_id=war_id)
    base = {
        "schema": "xar.ck3.war-cash-owned-pending-source-candidate.v1",
        "source_frame": frame, "war_id": war_id,
        "expected_checkpoint_sha256": expected_checkpoint_sha256,
        "pending_war_cash_raw": None,
        "formal_cash_eligible": False,
        "complete_writer_coverage_proven": False,
        "native_quote_semantics_proven": False,
        "same_frame_native_postcheck_proven": False,
        "checkpoint_bytes_verified_by_this_tool": False,
    }
    if expected_ledger_file_sha256 is None and not path.exists():
        return {**base, "status": "owned_ledger_absent_unknown",
                "ledger_file_sha256": None,
                "recorded_unresolved_quote_sum_raw_candidate": None,
                "claims": []}
    if not _sha(expected_ledger_file_sha256) or not path.is_file():
        raise ValueError("pending source ledger is absent or lacks exact SHA")
    frozen = _bounded_read_bytes(path, max_bytes=4 * 1024 * 1024)
    if _digest(frozen) != expected_ledger_file_sha256:
        raise ValueError("pending source ledger bytes differ from manifest")
    state = _replay(path, episode_run_id=episode_run_id, war_id=war_id,
                    frozen_data=frozen)
    if _bounded_read_bytes(path, max_bytes=4 * 1024 * 1024) != frozen:
        raise ValueError("pending source ledger changed during read")
    if state is None or state["scope"]["source_checkpoint_sha256"] != expected_checkpoint_sha256:
        raise ValueError("pending source scope checkpoint differs from exact pair")
    pending = state["pending"]
    if set(quote_evidence_paths) != set(pending):
        raise ValueError("pending source quote evidence set is incomplete")
    if not pending:
        return {**base, "status": "owned_ledger_empty_unknown",
                "ledger_file_sha256": expected_ledger_file_sha256,
                "recorded_unresolved_quote_sum_raw_candidate": None,
                "claims": []}
    if (_bounded_file_sha256(checkpoint_path, max_bytes=256 * 1024 * 1024)
            != expected_checkpoint_sha256):
        raise ValueError("pending source checkpoint bytes differ from manifest")
    claims: list[dict[str, object]] = []
    total = 0
    for request_id in sorted(pending):
        quote = pending[request_id]
        if (quote["source_frame"] != frame
                or state["pending_checkpoint_sha256"][request_id]
                != expected_checkpoint_sha256):
            raise ValueError("pending source quote crossed exact paused frame")
        evidence_path = quote_evidence_paths[request_id]
        if not isinstance(evidence_path, Path) or not evidence_path.is_file():
            raise ValueError("pending source quote evidence file is missing")
        evidence = _bounded_read_bytes(evidence_path, max_bytes=4 * 1024 * 1024)
        if _digest(evidence) != quote["price_evidence_sha256"]:
            raise ValueError("pending source quote evidence SHA differs")
        total += quote["raw"]
        if total > (1 << 63) - 1:
            raise ValueError("pending source quote sum exceeds signed raw gold")
        claims.append({
            "request_id": request_id,
            "selected_step": quote["priced_action"]["selected_step"],
            "quoted_raw_candidate": quote["raw"],
            "scale": 100_000,
            "price_evidence_sha256": quote["price_evidence_sha256"],
        })
    return {**base, "status": "same_frame_owned_writer_subset_only",
            "checkpoint_bytes_verified_by_this_tool": True,
            "ledger_file_sha256": expected_ledger_file_sha256,
            "recorded_unresolved_quote_sum_raw_candidate": total,
            "claims": claims}
