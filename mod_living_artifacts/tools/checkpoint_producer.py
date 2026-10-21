"""Offline Root checkpoint producer. Never sends a game command or starts a host.

CLI: --spec <predeclared JSON>. The spec pins a real public awaiting request,
runtime manifest, official tool provenance and the task's common storage inputs.
Input rejection before a credible identity is established writes no Root reply.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
from typing import Literal, TypedDict
import zipfile

from acceptance_contract import (Frame, Object, Pin, array, decimal_id, field, integer, json_value, mapping,
                                 pin, read, require, text, utc_now, write_once)
from checkpoint_callback import (BlockedReadbackResponse, CompletedReadbackResponse, FileIdentity, MeltProcessReceipt, ReadbackResponse, RootReadbackRequest, checked_pin)

REPO = Path(__file__).resolve().parents[2]


def stamp(value: object) -> datetime:
    result = datetime.fromisoformat(text(value, "UTC timestamp").replace("Z", "+00:00"))
    offset = result.utcoffset()
    require(result.tzinfo is not None and offset is not None and offset.total_seconds() == 0, "Explicit UTC timestamp required")
    return result


def deadline_seconds(value: object) -> float:
    if type(value) not in (int, float) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        raise ValueError("Finite numeric original hold deadline required; bool rejected")
    return float(value)


def _unique(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        require(key not in result, "Duplicate JSON key: " + key)
        result[key] = value
    return result


def raw_object(path: Path, maximum: int = 32 * 1024 * 1024) -> dict[str, object]:
    require(0 < path.stat().st_size <= maximum, "Bounded nonempty JSON input required")
    value: object = json.loads(path.read_text(encoding="utf-8-sig"), object_pairs_hook=_unique)
    # Native ABI fields remain exact Python ints, never safe-JSON reserialized.
    return mapping(value, "original raw JSON")


def declared_pin(value: object, label: str) -> Pin:
    row = mapping(value, label)
    require(set(row) == {"path", "bytes", "sha256"}, "Exact declared pin fields required: " + label)
    path = Path(text(row["path"], label + " path"))
    require(path.is_absolute() and str(path.resolve()) == row["path"], "Canonical absolute declared pin path required")
    digest = text(row["sha256"], label + " SHA")
    require(re.fullmatch("[0-9a-f]{64}", digest) is not None, "Canonical SHA256 required")
    return {"path": str(path), "bytes": integer(row["bytes"], label + " bytes", 1), "sha256": digest}


@dataclass(frozen=True)
class Identity:
    run_id: str
    machine_id: str
    reviewer: str
    pid: int
    generation: str
    actor: int
    date_raw: int

    @classmethod
    def parse(cls, value: object) -> Identity:
        row = mapping(value, "declared scene identity")
        require(set(row) == {"run_id", "machine_id", "reviewer", "pid", "connection_generation", "actor_character_id", "date_raw"}, "Exact declared scene fields required")
        return cls(text(row["run_id"], "run ID"), text(row["machine_id"], "machine ID"), text(row["reviewer"], "reviewer"),
                   integer(row["pid"], "PID", 1, 2**32 - 1), decimal_id(row["connection_generation"], "generation"),
                   integer(row["actor_character_id"], "actor", 1, 2**32 - 2), integer(row["date_raw"], "date"))

    def to_json(self) -> Object:
        return {"run_id": self.run_id, "machine_id": self.machine_id, "reviewer": self.reviewer, "pid": self.pid,
                "connection_generation": self.generation, "actor_character_id": self.actor, "date_raw": self.date_raw}


class StoragePins(TypedDict):
    policy: Pin
    machine_profile: Pin
    asset_ledger: Pin
    reservation: Pin
    inspection: Pin


@dataclass(frozen=True)
class ProducerSpec:
    identity: Identity
    request: Pin
    runtime_manifest: Pin
    melter: Pin
    official_release: Pin
    official_download: Pin
    storage: StoragePins
    output: Path
    maximum_melted_bytes: int
    maximum_log_bytes: int
    timeout_seconds: int

    def to_json(self) -> Object:
        return {"schema": "living-artifacts-checkpoint-producer-spec-v1", "schema_version": 1, "identity": self.identity.to_json(),
                "request": json_value(self.request), "runtime_manifest": json_value(self.runtime_manifest), "melter": json_value(self.melter),
                "official_release": json_value(self.official_release), "official_download": json_value(self.official_download), "storage": json_value(self.storage),
                "output_dir": str(self.output), "maximum_melted_bytes": self.maximum_melted_bytes, "maximum_log_bytes": self.maximum_log_bytes,
                "timeout_seconds": self.timeout_seconds}

    @classmethod
    def parse(cls, value: object) -> ProducerSpec:
        row = mapping(value, "predeclared producer spec")
        require(set(row) == {"schema", "schema_version", "identity", "request", "runtime_manifest", "melter", "official_release", "official_download", "storage",
                             "output_dir", "maximum_melted_bytes", "maximum_log_bytes", "timeout_seconds"} and
                row["schema"] == "living-artifacts-checkpoint-producer-spec-v1" and integer(row["schema_version"], "spec version", 1, 1) == 1,
                "Exact producer spec fields/version required")
        storage = mapping(row["storage"], "storage source pins")
        require(set(storage) == set(StoragePins.__required_keys__), "Common profile/ledger/reservation/inspection/policy pins required")
        sources: StoragePins = {"policy": checked_pin(storage["policy"], "common policy"),
            "machine_profile": checked_pin(storage["machine_profile"], "machine storage profile"), "asset_ledger": checked_pin(storage["asset_ledger"], "asset ledger"),
            "reservation": checked_pin(storage["reservation"], "coordinator reservation"), "inspection": checked_pin(storage["inspection"], "storage inspection")}
        output = Path(text(row["output_dir"], "unique output directory"))
        require(output.is_absolute() and not output.exists() and not output.resolve().is_relative_to(REPO), "Use a new absolute external output directory")
        return cls(Identity.parse(row["identity"]), checked_pin(row["request"], "public Root request"), checked_pin(row["runtime_manifest"], "runtime manifest"),
                   checked_pin(row["melter"], "predeclared official melter"), checked_pin(row["official_release"], "official release metadata"),
                   checked_pin(row["official_download"], "official download receipt"), sources, output.resolve(),
                   integer(row["maximum_melted_bytes"], "melted output bound", 1, 2**31), integer(row["maximum_log_bytes"], "per-stream log bound", 1, 16 * 1024 * 1024),
                   integer(row["timeout_seconds"], "melter timeout", 1, 180))


def actual_machine() -> str:
    result = subprocess.run([sys.executable, "-B", str(REPO / "tools/ck3_live_run_id.py"), "machine"],
        capture_output=True, text=True, check=True, timeout=20, creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
    return text(result.stdout.strip(), "actual stable machine ID")


def validate_request(spec: ProducerSpec, *, machine_id: str, now: datetime) -> tuple[Object, Pin, Path]:
    request = read(Path(spec.request["path"]))
    require(set(request) == set(RootReadbackRequest.__required_keys__) and request["schema"] == "living-artifacts-checkpoint-readback-request-v1" and request["business_pass"] is False and
            request["required_response_schema"] == "living-artifacts-checkpoint-readback-v1" and request["required_unknown_token_policy"] == "error" and
            request["storage_policy"] == "docs/storage-retention-policy.json", "Exact real public checkpoint request required")
    identity = spec.identity
    require(machine_id == identity.machine_id and request["operator_reviewer"] == identity.reviewer, "Producer belongs to another machine/reviewer")
    for key, wanted in identity.to_json().items():
        if key == "reviewer":
            continue
        actual = request[key]
        require(type(actual) is type(wanted) and actual == wanted, "Root request differs from declared identity: " + key)
    integer(request["observation_number"], "checkpoint observation number", 1, 3)
    if request["expected_target_id"] is not None:
        decimal_id(request["expected_target_id"], "expected target", allow_zero=True)
    deadline = deadline_seconds(request["original_hold_deadline"])
    require(deadline > now.timestamp() + integer(request["reserve_seconds"], "original Quit reserve", 180) + spec.timeout_seconds + 30,
            "Original hold leaves no bounded melt plus normal-Quit reserve")
    frame_pin = checked_pin(request["original_native_frame_record"], "original native snapshot")
    raw = raw_object(Path(frame_pin["path"]))
    rows = array(field(raw, "rows"), "original snapshot rows")
    require(len(rows) == 1, "Exactly one original public snapshot row required")
    row = mapping(rows[0], "original snapshot row")
    require(field(row, "ok") is True and field(field(row, "plan"), "tool") == "ck3_take_snapshot", "Original snapshot did not succeed")
    frame = Frame.parse(field(row, "result"), run_id=identity.run_id, machine_id=identity.machine_id, manifest=read(Path(spec.runtime_manifest["path"])))
    require((frame.pid, frame.generation_decimal, frame.player_id, frame.date_raw) == (identity.pid, identity.generation, identity.actor, identity.date_raw),
            "Original native snapshot crossed declared PID/generation/actor/date")
    source = declared_pin(request["actual_source_save"], "actual MCP source save")
    request_path = Path(spec.request["path"])
    require(request_path.name.endswith("-awaiting.json"), "Actual public Root request filename required")
    response = request_path.with_name(request_path.name.removesuffix("-awaiting.json") + "-root-result.json")
    require(not response.exists(), "Original Root response already exists; never overwrite/replay")
    return request, source, response


def validate_official_tool(spec: ProducerSpec) -> tuple[Pin, ...]:
    release = read(Path(spec.official_release["path"]))
    download = read(Path(spec.official_download["path"]))
    tag = text(field(release, "tag_name"), "official release tag")
    require(tag.startswith("v") and field(release, "html_url") == "https://github.com/rakaly/cli/releases/tag/" + tag and
            field(download, "release") == field(release, "html_url") and field(download, "machine_id") == spec.identity.machine_id and
            field(download, "official_github_asset_digest_verified") is True and field(download, "game_save_uploaded") is False,
            "Official locally verified melter provenance missing")
    require(Path(text(field(download, "exe"), "downloaded EXE")).resolve() == Path(spec.melter["path"]) and
            integer(field(download, "exe_bytes"), "downloaded EXE bytes", 1) == spec.melter["bytes"] and
            field(download, "exe_sha256") == spec.melter["sha256"], "Predeclared melter differs from official download receipt")
    asset_url = text(field(download, "asset_url"), "official asset URL")
    assets = [mapping(item, "official asset") for item in array(field(release, "assets"), "official release assets") if field(item, "browser_download_url") == asset_url]
    require(len(assets) == 1 and asset_url.startswith("https://github.com/rakaly/cli/releases/download/" + tag + "/"), "Unique official release asset required")
    asset = assets[0]
    archive = Path(spec.melter["path"]).parent / text(asset["name"], "official asset name")
    require(archive.parent == Path(spec.melter["path"]).parent and not archive.is_symlink(), "Official archive must be the retained sibling asset")
    archive_pin = pin(archive)
    require(archive_pin["bytes"] == integer(asset["size"], "official asset bytes", 1) and asset["digest"] == "sha256:" + archive_pin["sha256"] and
            field(download, "archive_sha256") == archive_pin["sha256"], "Official published archive digest differs")
    with zipfile.ZipFile(archive) as bundle:
        members = [item for item in bundle.infolist() if Path(item.filename).name == "rakaly.exe"]
        require(len(members) == 1 and members[0].file_size == spec.melter["bytes"], "Official archive must contain exactly the declared melter")
        digest = hashlib.sha256()
        with bundle.open(members[0]) as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(block)
        require(digest.hexdigest() == spec.melter["sha256"], "Local melter bytes differ from the official verified archive")
    return spec.official_release, spec.official_download, archive_pin, spec.melter


def storage_admission(spec: ProducerSpec, *, source_bytes: int, now: datetime) -> Object:
    """One scoped calculation from the common task inputs; grants no reservation."""
    policy = read(Path(spec.storage["policy"]["path"]))
    require(pin(REPO / "docs/storage-retention-policy.json")["sha256"] == spec.storage["policy"]["sha256"], "Use the repository's single current storage policy")
    profile = read(Path(spec.storage["machine_profile"]["path"]))
    ledger = read(Path(spec.storage["asset_ledger"]["path"]))
    reservation = read(Path(spec.storage["reservation"]["path"]))
    inspection = read(Path(spec.storage["inspection"]["path"]))
    machine = spec.identity.machine_id
    for data in (profile, ledger, reservation, inspection):
        require(field(data, "machine_id") == machine, "Storage input belongs to another machine")
    for data in (profile, ledger, inspection):
        require(field(data, "policy_version") == field(policy, "policy_version"), "Storage input uses another policy")
    require(field(inspection, "schema") == "xar.storage-retention-inspection.v1" and field(inspection, "trigger") == "before-heavy-write" and
            stamp(field(profile, "observed_at_utc")) <= stamp(field(inspection, "observed_at_utc")) <= now < stamp(field(reservation, "review_at_utc")),
            "Fresh complete before-heavy-write sources and unexpired coordinator reservation required")
    source_hashes = mapping(field(inspection, "input_pins"), "inspection source hashes")
    normalized = {str(Path(key).resolve()): item for key, item in source_hashes.items()}
    for key in ("policy", "machine_profile", "asset_ledger"):
        value = spec.storage[key]
        require(normalized.get(value["path"]) == value["sha256"], "Inspection does not bind the declared common storage input: " + key)
    require(field(field(profile, "usage_basis"), "bounded_project_roots_complete") is True, "Unknown project usage is not zero")
    roots = [Path(text(item, "approved root")).resolve() for item in mapping(field(profile, "project_root_map"), "approved project roots").values()]
    require(any(spec.output.is_relative_to(root) for root in roots), "Output lies outside approved project roots")
    outcomes = array(field(inspection, "outcomes"), "retention outcomes")
    groups = array(field(ledger, "asset_groups"), "asset ledger groups")
    require(bool(groups) and len(outcomes) == len(groups), "Inspection does not cover the complete declared asset ledger")
    require(all(field(row, "state") in ("current_use", "protected", "within_retention", "already_unavailable") for row in outcomes),
            "Unresolved expired/unknown assets block further heavy writes")
    for group in groups:
        require(field(group, "machine_id") == machine, "Ledger contains another machine")
    require(any(field(group, "owner_task") == field(reservation, "owner_task") for group in groups), "Reservation has no matching task owner in the declared ledger")
    volumes = mapping(field(profile, "volume_map"), "declared volumes")
    candidates = [(volume, mapping(value, "volume budget")) for volume, value in volumes.items() if Path(volume).resolve().anchor.casefold() == spec.output.anchor.casefold()]
    require(len(candidates) == 1, "Exactly one declared actual output volume required")
    volume, budget = candidates[0]
    live = shutil.disk_usage(volume)
    require(live.total > 0 and live.used >= 0 and live.free >= 0 and live.used + live.free == live.total, "Fresh capacity tuple is inconsistent")
    own = integer(field(field(reservation, "reservation_bytes"), volume), "whole task reserved bytes", 1)
    other = integer(field(field(reservation, "other_unspent_reservations_bytes"), volume), "other task reservations")
    require(other == integer(field(budget, "other_unspent_reservations_bytes"), "profile other reservations"), "Unknown changed parallel reservations")
    require(field(reservation, "state") == "reserved_for_python_native_runtime" and bool(text(field(reservation, "coordinator"), "coordinator")), "Coordinator-held task reservation required")
    peak = source_bytes + spec.maximum_melted_bytes + 2 * spec.maximum_log_bytes + 64 * 1024 * 1024
    require(peak <= own, "This bounded copy/melt exceeds the existing task reservation")
    capacity = field(policy, "capacity")
    fraction = Decimal(str(field(capacity, "safety_volume_fraction")))
    safety = max(integer(field(capacity, "safety_floor_bytes"), "policy floor"), min(integer(field(capacity, "safety_ceiling_bytes"), "policy ceiling"), int(Decimal(live.total) * fraction)))
    system = integer(field(budget, "system_growth_reserve_bytes"), "system growth reserve", 1)
    baseline = integer(field(budget, "current_project_usage_bytes"), "complete project baseline")
    quota = integer(field(budget, "effective_project_quota_bytes"), "effective quota", 1)
    default_quota = min(integer(field(capacity, "default_project_quota_ceiling_bytes"), "policy quota ceiling", 1),
                        int(Decimal(live.total) * Decimal(str(field(capacity, "default_project_quota_volume_fraction")))))
    require(quota <= default_quota, "This narrow producer does not authorize quota overrides; request coordinator review")
    # Conservatively count the entire task reservation as pending elsewhere,
    # and as growth beyond its complete baseline. This never allocates it again.
    physical = peak + own + other + system + safety
    projected = baseline + own + other + peak
    require(live.free >= physical and projected <= quota, "Fresh capacity/quota cannot cover existing holds and this melt")
    return {"schema": "living-artifacts-checkpoint-storage-check-v1", "machine_id": machine, "run_id": spec.identity.run_id,
        "observed_at_utc": now.isoformat(), "status": "ADMITTED_FOR_THIS_COPY_MELT_ONLY", "policy_version": text(field(policy, "policy_version"), "policy version"),
        "inputs": json_value(spec.storage), "volume": volume, "actual_total_bytes": live.total, "actual_free_bytes": live.free,
        "this_write_peak_bytes": peak, "complete_baseline_bytes": baseline, "whole_task_reservation_bytes": own,
        "other_reservations_bytes": other, "system_growth_reserve_bytes": system, "safety_bytes": safety,
        "required_free_bytes": physical, "projected_usage_upper_bound_bytes": projected, "quota_bytes": quota,
        "new_reservation_created": False, "gc_performed": False}


def file_identity(value: os.stat_result) -> FileIdentity:
    return {"device_id_decimal": decimal_id(str(value.st_dev), "file device", allow_zero=True),
            "file_id_decimal": decimal_id(str(value.st_ino), "file ID", allow_zero=True),
            "mtime_ns_decimal": decimal_id(str(value.st_mtime_ns), "mtime", allow_zero=True), "size_bytes": value.st_size}


def preserve_source(source: Pin, destination: Path) -> tuple[Pin, FileIdentity]:
    path = Path(source["path"])
    require(not path.is_symlink(), "Cannot preserve a linked source")
    with path.open("rb") as incoming, destination.open("xb") as outgoing:
        before = file_identity(os.fstat(incoming.fileno()))
        digest = hashlib.sha256()
        for block in iter(lambda: incoming.read(1024 * 1024), b""):
            digest.update(block)
            outgoing.write(block)
        outgoing.flush()
        os.fsync(outgoing.fileno())
        require(file_identity(os.fstat(incoming.fileno())) == before == file_identity(path.stat()), "Actual source changed identity during preservation")
    actual = pin(destination)
    require(actual["bytes"] == source["bytes"] == before["size_bytes"] and actual["sha256"] == source["sha256"] == digest.hexdigest(), "Preserved bytes differ from the real MCP save")
    return actual, before


@dataclass(frozen=True)
class ProcessOutcome:
    pid: int | None
    exit_code: int | None
    status: Literal["exited", "timeout", "output_limit", "launch_failed"]
    failure: str | None
    started_at: str
    finished_at: str


def execute_melter(argv: tuple[str, ...], *, output: Path, timeout: int, maximum_melted: int, maximum_log: int) -> ProcessOutcome:
    started = utc_now()
    with (output / "stdout.log").open("xb") as stdout, (output / "stderr.log").open("xb") as stderr:
        try:
            child = subprocess.Popen(argv, stdout=stdout, stderr=stderr, stdin=subprocess.DEVNULL,
                                     creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
        except OSError as failure:
            return ProcessOutcome(None, None, "launch_failed", str(failure), started, utc_now())
        deadline = time.monotonic() + timeout
        status: Literal["exited", "timeout", "output_limit"] = "exited"
        try:
            while child.poll() is None:
                if time.monotonic() >= deadline:
                    status = "timeout"
                elif any(path.exists() and path.stat().st_size > bound for path, bound in (
                        (output / "melted.ck3", maximum_melted), (output / "stdout.log", maximum_log), (output / "stderr.log", maximum_log))):
                    status = "output_limit"
                if status != "exited":
                    child.kill()
                    break
                time.sleep(0.05)
        finally:
            if child.poll() is None:
                child.kill()
            code = child.wait(timeout=10)
    if status == "exited" and any(path.exists() and path.stat().st_size > bound for path, bound in (
            (output / "melted.ck3", maximum_melted), (output / "stdout.log", maximum_log), (output / "stderr.log", maximum_log))):
        status = "output_limit"
    return ProcessOutcome(child.pid, code, status, None, started, utc_now())


def blocked_response(identity: Identity, *, reason: str, evidence: list[Pin]) -> BlockedReadbackResponse:
    return BlockedReadbackResponse(schema="living-artifacts-checkpoint-readback-v1", schema_version=1, status="blocked", run_id=identity.run_id,
        machine_id=identity.machine_id, reviewer=identity.reviewer, pid=identity.pid, connection_generation=identity.generation,
        actor_character_id=identity.actor, date_raw=identity.date_raw, reason=text(reason, "actual producer blocker"), evidence=evidence)


def produce_readback(spec_path: Path) -> ReadbackResponse:
    spec_pin = pin(spec_path.resolve())
    spec = ProducerSpec.parse(read(spec_path))
    identity = spec.identity
    # No Root reply is emitted until its identity and actual native frame prove
    # which pending request is being answered.
    request, source, response_path = validate_request(spec, machine_id=actual_machine(), now=datetime.now(timezone.utc))
    evidence: list[Pin] = [spec_pin, spec.request, spec.runtime_manifest]
    reply: ReadbackResponse
    try:
        checked_pin(source, "actual MCP source save before preservation")
        require(not Path(source["path"]).is_symlink(), "Source save must not be a link")
        evidence.extend(validate_official_tool(spec))
        admission = storage_admission(spec, source_bytes=source["bytes"], now=datetime.now(timezone.utc))
        for reference in (*spec.storage.values(), spec.request, spec.runtime_manifest):
            checked_pin(reference, "predeclared input immediately before preservation")
        spec.output.mkdir(parents=True, exist_ok=False)
        checked = write_once(spec.output / "storage-check.json", admission)
        evidence.append(checked)
        raw, original_identity = preserve_source(source, spec.output / "original.ck3")
        evidence.append(raw)
        request_copy = spec.output / "root-request.json"
        spec_copy = spec.output / "producer-spec.json"
        shutil.copyfile(spec.request["path"], request_copy)
        shutil.copyfile(spec_pin["path"], spec_copy)
        require(pin(request_copy)["sha256"] == spec.request["sha256"] and pin(spec_copy)["sha256"] == spec_pin["sha256"], "Original request/spec changed during preservation")
        argv = (spec.melter["path"], "melt", raw["path"], "--format", "ck3", "--unknown-key", "error", "-o", str(spec.output / "melted.ck3"))
        command = write_once(spec.output / "command.json", {"argv": argv})
        evidence.append(command)
        require(deadline_seconds(request["original_hold_deadline"]) > time.time() + spec.timeout_seconds + integer(request["reserve_seconds"], "Quit reserve", 180),
                "Original normal-Quit reserve reached before melter launch")
        checked_pin(spec.melter, "official melter immediately before launch")
        outcome = execute_melter(argv, output=spec.output, timeout=spec.timeout_seconds,
                                 maximum_melted=spec.maximum_melted_bytes, maximum_log=spec.maximum_log_bytes)
        melted = pin(spec.output / "melted.ck3") if (spec.output / "melted.ck3").is_file() else None
        stdout, stderr = pin(spec.output / "stdout.log"), pin(spec.output / "stderr.log")
        process_receipt: MeltProcessReceipt = {"schema": "living-artifacts-checkpoint-melt-process-v2", "machine_id": identity.machine_id,
            "run_id": identity.run_id, "exit_code": outcome.exit_code, "status": outcome.status, "failure": outcome.failure, "process_pid": outcome.pid,
            "raw": raw, "melted": melted, "melter": spec.melter, "command": command, "stdout": stdout, "stderr": stderr,
            "request": pin(request_copy), "spec": pin(spec_copy), "storage_check": checked, "source_file_identity": original_identity,
            "started_at_utc": outcome.started_at, "finished_at_utc": outcome.finished_at, "game_commands_sent": False}
        receipt = write_once(spec.output / "process.json", process_receipt)
        evidence.extend((raw, command, stdout, stderr, receipt))
        checked_pin(spec.melter, "official melter after execution")
        require(outcome.status == "exited" and outcome.exit_code == 0 and melted is not None and melted["bytes"] > 0,
                f"Actual strict melt did not complete: status={outcome.status}, exit={outcome.exit_code}")
        if melted is None:
            raise ValueError("Melted output missing")
        reply = CompletedReadbackResponse(schema="living-artifacts-checkpoint-readback-v1", schema_version=1, status="completed", run_id=identity.run_id,
            machine_id=identity.machine_id, reviewer=identity.reviewer, pid=identity.pid, connection_generation=identity.generation,
            actor_character_id=identity.actor, date_raw=identity.date_raw, source_save=raw, melted_save=melted, melter=spec.melter,
            command=command, process_receipt=receipt)
    except (ValueError, OSError, subprocess.SubprocessError, zipfile.BadZipFile) as failure:
        reply = blocked_response(identity, reason=type(failure).__name__ + ": " + str(failure), evidence=evidence)
    write_once(response_path, reply)
    return reply


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", type=Path, required=True)
    arguments = parser.parse_args()
    try:
        reply = produce_readback(arguments.spec)
    except (ValueError, OSError, subprocess.SubprocessError) as failure:
        print(json.dumps({"status": "input_rejected", "error": str(failure), "root_reply_written": False, "game_commands_sent": False}))
        return 2
    print(json.dumps({"status": reply["status"], "run_id": reply["run_id"], "machine_id": reply["machine_id"], "game_commands_sent": False}))
    return 0 if reply["status"] == "completed" else 3


if __name__ == "__main__":
    raise SystemExit(main())
