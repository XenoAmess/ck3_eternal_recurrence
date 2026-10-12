"""Root file-queue ordinary loop bound to actual saved-campaign responses.

No SDK import/launch, process/window operation, policy edit or ledger write.
An actual matched natural successor uses the existing Queue and normal SAVE.
The held Root SDK executor owns every call and preserves each raw response.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import sys
import time

import m7_ordinary_successor_queue as m7


def _note_diagnostic_failure(original, phase: str, secondary) -> None:
    """Keep diagnostic failure best-effort; never replace the selected error."""
    note = None
    try:
        note = f"Root diagnostic failed at {phase}; original error retained"
        note += (f"; original={type(original).__name__}: {str(original)[:1024]}"
                 f"; secondary={type(secondary).__name__}: {str(secondary)[:512]}")
        context = getattr(original, "root_response_context", None)
        if isinstance(context, dict):
            refs = {}
            for key in ("request", "response", "tool", "request_expected_revision"):
                value = context.get(key)
                if isinstance(value, str):
                    refs[key] = value[:384]
                elif value is None or type(value) is int:
                    refs[key] = value
            note += "; original_context_refs_excerpt=" + json.dumps(
                refs, ensure_ascii=False, separators=(",", ":"))
        note = note[:4096]
        original.add_note(note)
    except Exception:
        pass
    if note is None:
        return
    try:
        sys.stderr.write(note[:4096] + "\n")
        sys.stderr.flush()
    except Exception:
        pass


BINDING_STATUS = "ROOT_ACTUAL_NATIVE60_FIRST_RESPONSE_BOUND"


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write(path: Path, value: dict) -> None:
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, separators=(",", ":"))
        stream.write("\n")


def body(response: dict) -> dict:
    """Reuse Root executor structured-content first, JSON text fallback decoding."""
    if response.get("client_error"):
        raise RuntimeError(response["client_error"])
    result = response.get("result", {})
    if result.get("isError", result.get("is_error", False)):
        raise RuntimeError("Root SDK returned an error; retain the raw response")
    observed = result.get("structuredContent", result.get("structured_content"))
    if isinstance(observed, dict):
        return observed
    for block in result.get("content", []):
        if block.get("type") == "text":
            try:
                observed = json.loads(block["text"])
            except (TypeError, ValueError):
                continue
            if isinstance(observed, dict):
                return observed
    raise ValueError("Root response contains no decoded object")


def ending_frame(turn: dict) -> dict | None:
    """Actual R85 receipt post-frame and existing R83 advance end-frame shapes."""
    result = turn.get("result")
    if not isinstance(result, dict):
        return None
    if type(result.get("ending_date_raw")) is int:
        if type(result.get("revision")) is not int:
            raise ValueError("advancing result lacks its current public revision")
        return {key: result.get(key) for key in (
            "ending_date_raw", "revision", "native_revision", "paused",
            "episode_run_id", "episode_character_id", "played_character_id",
            "played_character_alive", "one_life_terminal", "one_life_terminal_reason",
        )}
    if (type(result.get("post_date_raw")) is int
            and type(result.get("post_public_revision")) is int):
        return {
            "ending_date_raw": result["post_date_raw"],
            "revision": result["post_public_revision"],
            "native_revision": result.get("post_native_revision"),
            "episode_run_id": result.get("episode_run_id"),
            "played_character_id": result.get("actor_character_id"),
            "frame_source": "actual_construction_receipt_post_frame",
        }
    return None  # Other query-only results do not establish a new calendar date.


class Queue:
    def __init__(self, packet: Path, output: Path, prefix: str, timeout: float, runtime_guard=None):
        self.inbox = packet / "gameplay-requests"
        self.outbox = packet / "gameplay-responses"
        self.output, self.prefix, self.timeout = output, prefix, timeout
        self.sequence = 0
        self.requests = []
        self.runtime_guard = runtime_guard

    def call(self, tool: str, arguments: dict, kind: str) -> tuple[dict, Path]:
        if self.runtime_guard is not None:
            self.runtime_guard(tool, arguments, kind)
        self.sequence += 1
        name = f"{self.prefix}-{self.sequence:06d}-{kind}.json"
        request_path = self.inbox / name
        response_path = self.outbox / name
        request = {"tool": tool, "arguments": arguments}
        pending = request_path.with_suffix(".pending")
        write(pending, request)
        pending.rename(request_path)
        self.requests.append({"request": str(request_path), "response": str(response_path)})
        deadline = time.monotonic() + self.timeout
        while True:
            if response_path.exists():
                try:
                    raw = read(response_path)
                except json.JSONDecodeError:
                    pass  # The existing executor writes its response before closing it.
                else:
                    try:
                        return body(raw), response_path
                    except (RuntimeError, ValueError) as error:
                        result = raw.get("result")
                        content = result.get("content") if isinstance(result, dict) else None
                        text = next((block["text"] for block in content
                            if isinstance(block, dict) and block.get("type") == "text"
                            and isinstance(block.get("text"), str)), None
                        ) if isinstance(content, list) else None
                        expected_revision = arguments.get("expected_revision")
                        error.root_response_context = {
                            "request": str(request_path), "response": str(response_path),
                            "tool": tool,
                            "request_expected_revision": expected_revision
                                if type(expected_revision) is int else None,
                            "remote_error_excerpt": text[:4096] if text is not None else None,
                            "remote_error_excerpt_basis": "first_mcp_text_block"
                                if text is not None else None,
                            "remote_error_excerpt_truncated": len(text) > 4096
                                if text is not None else False,
                        }
                        raise
            if time.monotonic() >= deadline:
                raise TimeoutError(f"Original request remains pending; do not resend: {request_path}")
            time.sleep(0.25)

    def thin(self, kind: str, value: dict) -> None:
        write(self.output / f"{self.sequence:06d}-{kind}-thin.json", value)
        print(json.dumps(value, ensure_ascii=False, separators=(",", ":")), flush=True)



def _sway_int(value, low=1, high=(1 << 64) - 1):
    return type(value) is int and low <= value <= high


def _sway_reference(reference, limit=65536):
    if (type(reference) is not dict or set(reference) != {"path", "bytes", "sha256"}
            or type(reference["path"]) is not str or not Path(reference["path"]).is_absolute()
            or not _sway_int(reference["bytes"], 1, limit)
            or type(reference["sha256"]) is not str
            or len(reference["sha256"]) != 64
            or any(c not in "0123456789abcdef" for c in reference["sha256"])):
        raise ValueError("Sway observer requires an explicit bounded actual reference")
    path = Path(reference["path"])
    if path.stat().st_size != reference["bytes"]:
        raise ValueError("Sway observer reference size changed")
    raw = path.read_bytes()
    if (len(raw) != reference["bytes"]
            or hashlib.sha256(raw).hexdigest() != reference["sha256"]):
        raise ValueError("Sway observer reference bytes changed")
    value = json.loads(raw.decode("utf-8-sig"))
    if type(value) is not dict:
        raise ValueError("Sway observer reference is not an object")
    return value, path.resolve()


def _sway_response_pair(witness, request_key, response_key, packet, tool, arguments):
    request, request_path = _sway_reference(witness[request_key])
    raw, response_path = _sway_reference(witness[response_key], 8 * 1024 * 1024)
    if (request_path.parent != (packet / "gameplay-requests").resolve()
            or response_path.parent != (packet / "gameplay-responses").resolve()
            or request_path.suffix != ".json" or response_path.name != request_path.name
            or request.get("tool") != tool or request.get("arguments") != arguments
            or type(request.get("arguments")) is not dict):
        raise ValueError("Sway seed is not its actual same-packet request/response")
    # Integer equality alone would accept bool; validate the real argument types.
    if any(type(request["arguments"].get(key)) is not type(value)
           for key, value in arguments.items()):
        raise ValueError("Sway seed request argument types changed")
    return body(raw)


def load_sway_observer_binding(args, current_snapshot):
    path = args.sway_observer_binding
    if type(path) is not Path and not isinstance(path, Path):
        raise ValueError("Sway observer binding must be an explicit Path")
    if not path.is_absolute() or not 0 < path.stat().st_size <= 16384:
        raise ValueError("Sway observer binding is absent or exceeds 16 KiB")
    binding = read(path)
    if (type(binding) is not dict
            or binding.get("schema") != "xar.r104.dynamic-sway-observer-binding.v1"):
        raise ValueError("Sway observer binding schema is not the explicit Root contract")
    for key in ("actor_character_id", "target_character_id", "scheme_instance_id",
                "episode_character_id", "owned_game_pid"):
        if not _sway_int(binding.get(key), 1, 0xFFFFFFFF):
            raise ValueError("Sway binding lacks full integer identity: " + key)
    for key in ("creation_filetime_100ns", "connection_generation",
                "seed_public_revision", "seed_native_revision"):
        if not _sway_int(binding.get(key)):
            raise ValueError("Sway binding lacks actual integer provenance: " + key)
    if (not _sway_int(binding.get("scheme_instance_generation"), 0, 255)
            or not _sway_int(binding.get("seed_date_raw"), -(1 << 63), (1 << 63) - 1)
            or binding["actor_character_id"] == binding["target_character_id"]
            or binding["episode_character_id"] != binding["actor_character_id"]
            or type(binding.get("episode_run_id")) is not str or not binding["episode_run_id"]
            or type(binding.get("seed_snapshot_id")) is not str or not binding["seed_snapshot_id"]):
        raise ValueError("Sway binding has malformed episode, frame or instance")
    witness, _ = _sway_reference(binding["query_witness_reference"])
    packet = args.packet.resolve()
    if (witness.get("schema") != "xar.r104.root-held-queue-query-witness.v1"
            or witness.get("status") != "ACTUAL_TARGET_QUERY_PUBLISHED_AND_RESPONDED_IN_HELD_SESSION"
            or type(witness.get("packet")) is not str
            or Path(witness["packet"]).resolve() != packet):
        raise ValueError("Sway binding lacks the actual held-queue query witness")
    for key in ("owned_game_pid", "creation_filetime_100ns", "connection_generation"):
        if type(witness.get(key)) is not int or witness[key] != binding[key]:
            raise ValueError("Sway query witness differs from its current owner: " + key)
    if type(witness.get("bridge_pid")) is not int or witness["bridge_pid"] != binding["owned_game_pid"]:
        raise ValueError("Sway query witness lacks its actual bridge process")
    ready, _ = _sway_reference(witness["actual_ready_reference"])
    if (ready.get("status") != "ACTUAL_NEW_NATIVE_SESSION_READY_GAME_ALIVE"
            or type(ready.get("pid")) is not int or ready["pid"] != binding["owned_game_pid"]
            or type(ready.get("owned_game_pid")) is not int or ready["owned_game_pid"] != ready["pid"]
            or type(ready.get("creation_filetime_100ns")) is not int
            or ready["creation_filetime_100ns"] != binding["creation_filetime_100ns"]
            or type(ready.get("kernel_wait_result")) is not int or ready["kernel_wait_result"] != 258
            or ready.get("kernel_identity_observed_while_handle_held") is not True
            or ready.get("CloseHandle_ok") is not True
            or type(ready.get("operator_packet")) is not str
            or Path(ready["operator_packet"]).resolve() != packet
            or type(ready.get("owned_job_id")) is not str or not ready["owned_job_id"]
            or any(type(ready.get(key)) is not str or not Path(ready[key]).is_absolute()
                   for key in ("operator_handoff_reference", "ready_stdout_reference"))
            or type(ready.get("owned_job_started_unix")) not in (int, float)
            or not math.isfinite(ready["owned_job_started_unix"])
            or ready["owned_job_started_unix"] <= 0):
        raise ValueError("Sway query is not bound to its actual owned kernel-ready identity")
    # The existing guard emits one immutable JSON per call; it is capacity-only.
    guard, _ = _sway_reference(witness["guard_before_publish_receipt_reference"])
    owner = guard.get("owned_process_observation")
    if (guard.get("status") != "GREEN"
            or guard.get("qualification_scope") != "next_request_capacity_only"
            or guard.get("tool") != "ck3_query_active_scheme_sway_target_private_v1"
            or type(guard.get("kind")) is not str or guard["kind"] != witness["guard_kind"]
            or type(guard.get("runtime_config_reference")) is not str
            or guard["runtime_config_reference"] != witness["runtime_config_reference"]
            or type(guard.get("owned_game_pid")) is not int
            or guard["owned_game_pid"] != binding["owned_game_pid"]
            or type(guard.get("expected_creation_filetime_100ns")) is not int
            or guard["expected_creation_filetime_100ns"] != binding["creation_filetime_100ns"]
            or type(owner) is not dict):
        raise ValueError("Sway query guard is not the actual accepted owner check for this call")
    for key, expected in (("pid", binding["owned_game_pid"]),
                          ("expected_creation_filetime_100ns", binding["creation_filetime_100ns"]),
                          ("creation_filetime_100ns", binding["creation_filetime_100ns"]),
                          ("kernel_wait_result", 258)):
        if type(owner.get(key)) is not int or owner[key] != expected:
            raise ValueError("Sway query guard observed a different kernel identity")
    if (owner.get("kernel_identity_observed_while_handle_held") is not True
            or owner.get("CloseHandle_ok") is not True
            or type(owner.get("image_name")) is not str
            or Path(owner["image_name"]).name.casefold() != "ck3.exe"):
        raise ValueError("Sway query guard did not observe the expected held CK3 process")
    expected_arguments = {"expected_revision": binding["seed_public_revision"],
                          "target_character_id": binding["target_character_id"]}
    if (witness.get("tool") != guard["tool"]
            or type(witness.get("arguments")) is not dict
            or witness["arguments"] != expected_arguments
            or any(type(witness["arguments"].get(key)) is not int for key in expected_arguments)):
        raise ValueError("Sway query witness differs from the actual guarded target arguments")
    seed_raw, _ = _sway_reference(witness["current_snapshot_reference"], 8 * 1024 * 1024)
    caps_raw, _ = _sway_reference(witness["current_capabilities_reference"], 8 * 1024 * 1024)
    seed, caps = body(seed_raw), body(caps_raw)
    for snapshot in (seed, current_snapshot):
        if type(snapshot.get("diagnostics")) is not dict or type(snapshot.get("capabilities")) is not dict:
            raise ValueError("Sway observer snapshot lacks current session diagnostics")
        diagnostics = snapshot.get("diagnostics", {})
        embedded = snapshot.get("capabilities", {}).get("diagnostics", {})
        for observed in (diagnostics, embedded):
            if (type(observed.get("bridge_pid")) is not int
                    or observed["bridge_pid"] != binding["owned_game_pid"]
                    or type(observed.get("connection_generation")) is not int
                    or observed["connection_generation"] != binding["connection_generation"]):
                raise ValueError("Sway observer snapshot belongs to a different bridge session")
    diagnostics = caps.get("diagnostics", {})
    if (type(diagnostics.get("bridge_pid")) is not int
            or diagnostics["bridge_pid"] != binding["owned_game_pid"]
            or type(diagnostics.get("connection_generation")) is not int
            or diagnostics["connection_generation"] != binding["connection_generation"]):
        raise ValueError("Sway observer capabilities differ from the actual query owner")
    played = seed.get("played_character", {})
    if (seed.get("paused") is not True or seed.get("map_ready") is not True
            or played.get("alive") is not True
            or type(played.get("character_id")) is not int
            or played["character_id"] != binding["actor_character_id"]
            or type(seed.get("episode_character_id")) is not int
            or seed["episode_character_id"] != binding["episode_character_id"]
            or seed.get("episode_run_id") != binding["episode_run_id"]
            or seed.get("snapshot_id") != binding["seed_snapshot_id"]):
        raise ValueError("Sway seed snapshot is not the bound paused living episode")
    for source, declared in (("revision", "seed_public_revision"),
                             ("native_revision", "seed_native_revision"), ("date_raw", "seed_date_raw")):
        if type(seed.get(source)) is not int or seed[source] != binding[declared]:
            raise ValueError("Sway seed snapshot differs from the actual query frame")
    target = _sway_response_pair(witness, "request_reference", "response_reference", packet,
        "ck3_query_active_scheme_sway_target_private_v1",
        {"expected_revision": binding["seed_public_revision"],
         "target_character_id": binding["target_character_id"]})
    for key in ("actor_character_id", "target_character_id"):
        if type(target.get(key)) is not int or target[key] != binding[key]:
            raise ValueError("Sway actual target query differs from the chosen role identity")
    for key, declared in (("date_raw", "seed_date_raw"), ("snapshot_revision", "seed_native_revision"),
                          ("queried_revision", "seed_public_revision"), ("queried_native_revision", "seed_native_revision")):
        if type(target.get(key)) is not int or target[key] != binding[declared]:
            raise ValueError("Sway actual target query differs from its frame")
    if (target.get("queried_snapshot_id") != binding["seed_snapshot_id"]
            or not _sway_int(target.get("capture_epoch")) or not _sway_int(target.get("container_generation"))
            or target.get("matching_sway_active") is not True
            or type(target.get("active_sway_instances")) is not list):
        raise ValueError("Sway actual target query lacks an observed active instance")
    matches = [row for row in target["active_sway_instances"] if type(row) is dict
        and type(row.get("target_character_id")) is int and row["target_character_id"] == binding["target_character_id"]
        and type(row.get("scheme_instance_id")) is int and row["scheme_instance_id"] == binding["scheme_instance_id"]
        and type(row.get("scheme_instance_generation")) is int
        and row["scheme_instance_generation"] == binding["scheme_instance_generation"]]
    if len(matches) != 1:
        raise ValueError("Sway actual target query has no unique full instance/generation match")
    seed_frame = {"revision": binding["seed_public_revision"],
                  "native_revision": binding["seed_native_revision"], "ending_date_raw": binding["seed_date_raw"]}
    for request_key, response_key, tool, completion in (
            ("completion_request_reference", "completion_response_reference",
             "ck3_query_active_scheme_sway_completion_private_v1", True),
            ("opinion_request_reference", "opinion_response_reference",
             "ck3_query_active_scheme_sway_outcome_opinion_private_v1", False)):
        arguments = dict(expected_arguments)
        if completion:
            arguments["scheme_instance_id"] = binding["scheme_instance_id"]
        leaf = _sway_response_pair(witness, request_key, response_key, packet, tool, arguments)
        require_sway_leaf(leaf, binding, seed_frame, Path(witness[response_key]["path"]), completion=completion)
    normal = _sway_response_pair(witness, "completed_normal_request_reference",
        "completed_normal_response_reference", packet, "ck3_auto_turn", {})
    end = ending_frame(normal)
    # This joins existing frame fields, not a new semantic normal-result qualification.
    # Root must verify the actual completed-normal endpoint; absent fields stay pending.
    if end is None:
        raise ValueError("Root actual normal endpoint frame is pending; preserve its response")
    for key, expected in (("ending_date_raw", binding["seed_date_raw"]),
                          ("revision", binding["seed_public_revision"]),
                          ("native_revision", binding["seed_native_revision"])):
        if type(end.get(key)) is not int or end[key] != expected:
            raise ValueError("Root actual normal endpoint lacks its matched seed frame")
    for key, expected in (("played_character_id", binding["actor_character_id"]),
                          ("episode_character_id", binding["episode_character_id"]),
                          ("episode_run_id", binding["episode_run_id"])):
        if end.get(key) is not None and (type(end[key]) is not type(expected) or end[key] != expected):
            raise ValueError("Root actual normal endpoint contradicts the observed seed episode")
    return binding


def require_sway_baseline(path, leaf, binding, snapshot, packet, *, completion=False):
    if (not _sway_int(snapshot.get("revision")) or not _sway_int(snapshot.get("native_revision"))
            or not _sway_int(snapshot.get("date_raw"), -(1 << 63), (1 << 63) - 1)):
        raise ValueError("Sway baseline requires a strictly typed actual current snapshot frame")
    path = path.resolve()
    request_path = packet.resolve() / "gameplay-requests" / path.name
    if (path.parent != (packet / "gameplay-responses").resolve() or path.suffix != ".json"
            or not 0 < request_path.stat().st_size <= 8192):
        raise ValueError("Sway baseline is not an actual request/response of this packet")
    arguments = {"expected_revision": snapshot["revision"], "target_character_id": binding["target_character_id"]}
    tool = "ck3_query_active_scheme_sway_outcome_opinion_private_v1"
    if completion:
        tool = "ck3_query_active_scheme_sway_completion_private_v1"
        arguments["scheme_instance_id"] = binding["scheme_instance_id"]
    request = read(request_path)
    if (request.get("tool") != tool or type(request.get("arguments")) is not dict
            or request["arguments"] != arguments
            or any(type(request["arguments"].get(key)) is not int for key in arguments)):
        raise ValueError("Sway baseline request differs from its current actual snapshot")
    frame = {"revision": snapshot["revision"], "native_revision": snapshot["native_revision"],
             "ending_date_raw": snapshot["date_raw"]}
    require_sway_leaf(leaf, binding, frame, path, completion=completion)
    if snapshot["snapshot_id"] == binding["seed_snapshot_id"]:
        witness, _ = _sway_reference(binding["query_witness_reference"])
        key = "completion_response_reference" if completion else "opinion_response_reference"
        if path != Path(witness[key]["path"]).resolve():
            raise ValueError("Sway initial baseline is not the exact witnessed seed response")


def require_sway_leaf(value, binding, frame, response_path, *, completion=False):
    if type(value.get("available")) is not bool:
        raise ValueError("Sway observer leaf lacks a typed availability result")
    for key, expected in (("actor_character_id", binding["actor_character_id"]),
                          ("target_character_id", binding["target_character_id"]),
                          ("queried_revision", frame["revision"]),
                          ("queried_native_revision", frame["native_revision"]),
                          ("date_raw", frame["ending_date_raw"])):
        if type(value.get(key)) is not int or value[key] != expected:
            error = ValueError("Sway observer returned a different actual identity/frame: " + key)
            error.root_response_context = {"response": str(response_path),
                "sway_binding": str(binding["query_witness_reference"]["path"])}
            raise error
    if completion and (type(value.get("scheme_instance_id")) is not int
            or (value["available"] is True and value.get("scheme_instance_generation") is None)
            or value["scheme_instance_id"] != binding["scheme_instance_id"]
            or (value.get("scheme_instance_generation") is not None
                and (type(value["scheme_instance_generation"]) is not int
                     or value["scheme_instance_generation"] != binding["scheme_instance_generation"]))):
        error = ValueError("Sway completion returned a different full instance/generation")
        error.root_response_context = {"response": str(response_path),
            "sway_binding": str(binding["query_witness_reference"]["path"])}
        raise error


def observe_sway(queue: Queue, frame: dict, binding: dict) -> int:
    if (not _sway_int(frame.get("revision")) or not _sway_int(frame.get("native_revision"))
            or not _sway_int(frame.get("ending_date_raw"), -(1 << 63), (1 << 63) - 1)):
        raise ValueError("Sway observer requires the actual completed current frame")
    revision = frame["revision"]
    completion, completion_path = queue.call(
        "ck3_query_active_scheme_sway_completion_private_v1",
        {"expected_revision": revision, "target_character_id": binding["target_character_id"],
         "scheme_instance_id": binding["scheme_instance_id"]}, "sway-completion")
    queue.thin("sway-completion", {
        "response": str(completion_path),
        **{key: completion.get(key) for key in (
            "schema", "available", "unavailable_reason", "date_raw",
            "actor_character_id", "target_character_id", "scheme_instance_id",
            "scheme_instance_generation", "instance_present", "storage_slot_reused",
            "exact_instance_join_ready", "native_owner_raw", "native_status_raw",
            "native_status_key", "native_terminal_state_observed",
            "terminal_cause_observed", "terminal_cause", "queried_revision",
            "queried_native_revision")},
    })
    require_sway_leaf(completion, binding, frame, completion_path, completion=True)
    opinion, opinion_path = queue.call(
        "ck3_query_active_scheme_sway_outcome_opinion_private_v1",
        {"expected_revision": revision, "target_character_id": binding["target_character_id"]}, "sway-opinion")
    queue.thin("sway-opinion", {
        "response": str(opinion_path),
        **{key: opinion.get(key) for key in (
            "schema", "available", "unavailable_reason", "date_raw",
            "actor_character_id", "target_character_id", "target_opinion_of_actor",
            "scheme_sway_opinion", "sway_blocker_opinion", "queried_revision",
            "queried_native_revision")},
    })
    require_sway_leaf(opinion, binding, frame, opinion_path)
    return opinion["date_raw"]


def run(args) -> int:
    if BINDING_STATUS != "ROOT_ACTUAL_NATIVE60_FIRST_RESPONSE_BOUND":
        raise SystemExit(BINDING_STATUS + "; source draft must not queue calls yet")
    qualification = read(args.qualification)
    if qualification.get("status") != "GREEN":
        raise ValueError("Root actual initial paused qualification is not GREEN")
    initial = body(read(args.initial_snapshot))
    first = body(read(args.first_turn_response))
    start_date = initial["date_raw"]
    target_date = start_date + args.days * 24
    frame = ending_frame(first)
    current_date = frame["ending_date_raw"] if frame else start_date
    initial_opinion = initial_completion = sway_binding = None
    sway_episode_observer = False
    if args.sway_observer_binding is not None:
        if args.sway_completion is None or args.sway_opinion is None:
            raise ValueError("Sway observer binding requires both baseline responses")
        initial_opinion = body(read(args.sway_opinion))
        initial_completion = body(read(args.sway_completion))
        sway_binding = load_sway_observer_binding(args, initial)
        sway_episode_observer = (
            type(initial.get("episode_character_id")) is int
            and initial["episode_character_id"] == sway_binding["episode_character_id"]
            and initial.get("episode_run_id") == sway_binding["episode_run_id"])
    if sway_episode_observer:
        played = initial.get("played_character", {})
        if (initial.get("paused") is not True or initial.get("map_ready") is not True
                or played.get("alive") is not True
                or type(played.get("character_id")) is not int
                or played["character_id"] != sway_binding["actor_character_id"]):
            raise ValueError("Sway current episode is not the bound paused living actor")
        require_sway_baseline(args.sway_completion, initial_completion, sway_binding, initial, args.packet, completion=True)
        require_sway_baseline(args.sway_opinion, initial_opinion, sway_binding, initial, args.packet)
    sway_observer_enabled_initially = sway_episode_observer
    last_leaf_date = initial_opinion["date_raw"] if initial_opinion is not None else start_date
    args.output.mkdir(parents=True, exist_ok=False)
    queue = Queue(args.packet, args.output, args.prefix, args.response_timeout_seconds,
                  getattr(args, "runtime_guard", None))
    started = datetime.now(timezone.utc).isoformat()
    turns = 0
    status = "RUNNING"
    transitions = []
    pending_successor = None
    latest_successor_snapshot = None
    latest_successor_save = None
    last_successor_save_is_loop_endpoint = False
    current_episode = {key: initial.get(key) for key in (
        "episode_character_id", "episode_run_id")}
    source_snapshot, source_snapshot_path = initial, args.initial_snapshot
    checkpoint_pair = getattr(args, "matched_checkpoint_episode", None)

    def adopt_snapshot(snapshot, path, transition):
        nonlocal frame, current_date, current_episode, pending_successor
        nonlocal latest_successor_snapshot, sway_episode_observer
        nonlocal source_snapshot, source_snapshot_path
        frame = m7.frame(snapshot)
        current_date = snapshot["date_raw"]
        current_episode = {key: snapshot[key] for key in (
            "episode_character_id", "episode_run_id")}
        pending_successor = transition
        latest_successor_snapshot = path
        source_snapshot, source_snapshot_path = snapshot, path
        sway_episode_observer = False  # The explicitly bound scheme ends with its actual episode.

    def adopt_observed_successor():
        snapshot, path, transition = m7.continue_successor(
            queue, current_episode, transitions)
        adopt_snapshot(snapshot, path, transition)

    def adopt_completed_response(turn, response_path):
        snapshot, path, transition = m7.consume_completed(
            queue, turn, response_path, source_snapshot, source_snapshot_path,
            transitions, checkpoint_pair)
        adopt_snapshot(snapshot, path, transition)

    def plan_before_action(kind):
        # Ordinary advance receipts omit terminal/episode post-frame fields.
        # Read the existing planner before another auto or fixed Sway query so
        # the same Queue can retain the real terminal before continuation.
        planned, path = queue.call("ck3_plan_turn", {}, kind)
        step = planned.get("plan", {}).get("selected_step")
        queue.thin(kind, {"response": str(path), "selected_step": step,
                          "snapshot_id": planned.get("snapshot_id"),
                          "revision": planned.get("revision")})
        if step == m7.CONTINUE_AS_RECONCILED_SUCCESSOR_STEP:
            adopt_observed_successor()
            return True
        if not isinstance(step, str) or not step:
            raise ValueError("retain unavailable/blocked ordinary plan before next action")
        return False

    primary_error = primary_traceback = None
    unwinding_error = None
    diagnostic_failed = False
    try:
        if m7.completed_continuation(first):
            adopt_completed_response(first, args.first_turn_response)
        elif first.get("status") != "executed":
            raise ValueError("retain original nonexecuted first response for Root review")
        elif frame is not None and frame.get("one_life_terminal") is True:
            if frame.get("one_life_terminal_reason") != "played_character_changed":
                raise ValueError("retain actual non-successor terminal for Root review")
            adopt_observed_successor()
        if pending_successor is None:
            plan_before_action("initial-ordinary-plan")
        if (sway_episode_observer and frame is not None
                and current_date > last_leaf_date):
            last_leaf_date = observe_sway(queue, frame, sway_binding)
        while current_date < target_date or pending_successor is not None:
            if pending_successor is not None:
                snapshot, path, saved_path = m7.checkpoint_if_clear(queue, pending_successor)
                frame = m7.frame(snapshot)
                current_date = snapshot["date_raw"]
                latest_successor_snapshot = path
                source_snapshot, source_snapshot_path = snapshot, path
                if saved_path is not None:
                    checkpoint_pair = {
                        key: pending_successor["successor_checkpoint"]["checkpoint"][key]
                        for key in ("episode_character_id", "episode_run_id", "succession_lifecycle")}
                    latest_successor_save = saved_path
                    last_successor_save_is_loop_endpoint = True
                    pending_successor = None
                    # Hand the confirmed pair to the bounded owner before any
                    # following turn can fail or overwrite this checkpoint.
                    status = "ROOT_SUCCESSOR_SAVED_CHECKPOINT_PENDING"
                    break
            if (getattr(args, "stop_after_normal_file", None) is not None
                    and args.stop_after_normal_file.exists()):
                status = ("ROOT_STOP_SUCCESSOR_CHECKPOINT_DEFERRED"
                          if pending_successor is not None
                          else "ROOT_STOP_AT_NORMAL_CHECKPOINT_PENDING")
                break
            if current_date >= target_date and pending_successor is None:
                status = "TARGET_DATE_REACHED_ROOT_CHECKPOINT_PENDING"
                break
            if plan_before_action("ordinary-plan"):
                continue
            turn, turn_path = queue.call("ck3_auto_turn", {}, "normal")
            turns += 1
            last_successor_save_is_loop_endpoint = False
            observed = ending_frame(turn)
            before_date = current_date
            if observed is not None:
                current_date = observed["ending_date_raw"]
                frame = observed
            queue.thin("normal", {
                "response": str(turn_path), "turn": turns,
                "status": turn.get("status"), "selected_step": turn.get("selected_step"),
                "result_status": turn.get("result", {}).get("status"),
                "postcondition_verified": turn.get("result", {}).get("postcondition_verified"),
                "before_date_raw": before_date, "after_date_raw": current_date,
                "actual_days_from_initial": (current_date - start_date) / 24,
                "ending_frame": observed, "sway_following_turn": turn.get("sway_following_turn"),
            })
            if m7.completed_continuation(turn):
                adopt_completed_response(turn, turn_path)
            elif turn.get("status") != "executed":
                status = "ROOT_NORMAL_TURN_RETURNED_" + str(turn.get("status"))
                break
            elif observed and observed.get("one_life_terminal") is True:
                if observed.get("one_life_terminal_reason") != "played_character_changed":
                    status = "ROOT_ORIGINAL_EPISODE_TERMINAL"
                    break
                adopt_observed_successor()
            elif pending_successor is not None:
                # A new actual player decision stays in the original ordinary planner.
                snapshot, path = m7.snapshot_once(queue, "m7-player-decision-readback")
                m7.require_current_successor(snapshot, pending_successor)
                frame = m7.frame(snapshot)
                current_date = snapshot["date_raw"]
                latest_successor_snapshot = path
                source_snapshot, source_snapshot_path = snapshot, path
            if (sway_episode_observer and current_date > before_date
                    and current_date != last_leaf_date):
                if plan_before_action("sway-date-plan"):
                    continue
                last_leaf_date = observe_sway(queue, frame, sway_binding)
        else:
            status = "TARGET_DATE_REACHED_ROOT_CHECKPOINT_PENDING"
    except Exception as error:
        primary_error, primary_traceback = error, error.__traceback__
        status = "ROOT_REVIEW_ORIGINAL_RESPONSE_REQUIRED"
        try:
            queue.thin("error", {
                "error": repr(error), "pending_requests_not_resent": True,
                "original_response_context": getattr(error, "root_response_context", None),
            })
        except Exception as diagnostic_error:
            diagnostic_failed = True
            _note_diagnostic_failure(primary_error, "ERROR thin", diagnostic_error)
    except BaseException as interruption:
        unwinding_error = interruption
        raise
    finally:
        selected_error = unwinding_error if unwinding_error is not None else primary_error
        try:
            write(args.output / "LOOP-RESULT.json", {
                "original_error": repr(selected_error) if selected_error is not None else None,
                "original_response_context": getattr(selected_error, "root_response_context", None),
                "original_exception_notes_excerpt": [
                    note[:4096] for note in getattr(selected_error, "__notes__", [])[:4]
                    if isinstance(note, str)
                ] if selected_error is not None else [],
                "status": status, "started_at_utc": started,
                "ended_at_utc": datetime.now(timezone.utc).isoformat(),
                "qualification": str(args.qualification), "initial_snapshot": str(args.initial_snapshot),
                "first_turn_response": str(args.first_turn_response),
                "sway_baseline_responses": ([str(args.sway_completion), str(args.sway_opinion)]
                                            if sway_binding is not None else None),
                "sway_observer_binding": (str(args.sway_observer_binding)
                                          if sway_binding is not None else None),
                "sway_query_witness_reference": (sway_binding["query_witness_reference"]
                                                 if sway_binding is not None else None),
                "initial_original_scheme": ({key: initial_completion.get(key) for key in (
                    "scheme_instance_id", "scheme_instance_generation", "native_status_key")}
                                            if initial_completion is not None else None),
                "starting_date_raw": start_date, "current_date_raw": current_date,
                "target_date_raw": target_date, "actual_days_from_initial": (current_date-start_date)/24,
                "normal_turns": turns, "requests": queue.requests,
                "new_full_snapshot_queries": sum(
                    "snapshot" in Path(item["response"]).name
                    or "save-readback" in Path(item["response"]).name
                    or "player-decision-readback" in Path(item["response"]).name
                    for item in queue.requests),
                "checkpoint_calls": sum(
                    Path(item["response"]).name.endswith("-m7-successor-save.json")
                    for item in queue.requests),
                "natural_succession_transitions": transitions,
                "natural_continuation_turns": len(transitions),
                "current_episode": ({
                    "episode_character_id": transitions[-1]["successor_character_id"],
                    "episode_run_id": transitions[-1]["episode_run_id"],
                } if transitions else current_episode),
                "current_episode_evidence_source": (
                    "last_verified_transition_snapshot" if transitions
                    else "last_controller_adopted_snapshot"),
                "live_episode_after_error": (
                    "unverified" if status == "ROOT_REVIEW_ORIGINAL_RESPONSE_REQUIRED"
                    else "not_applicable"),
                "sway_observer_enabled_initially": sway_observer_enabled_initially,
                "last_sway_leaf_date_raw": (last_leaf_date if sway_observer_enabled_initially else None),
                "original_sway_episode_observation_ended": (
                    sway_observer_enabled_initially and not sway_episode_observer),
                "latest_successor_snapshot": (str(latest_successor_snapshot)
                                              if latest_successor_snapshot else None),
                "latest_successor_save": (str(latest_successor_save)
                                          if latest_successor_save else None),
                "last_successor_save_is_loop_endpoint": last_successor_save_is_loop_endpoint,
                "successor_checkpoint_pending": (pending_successor is not None
                    or bool(transitions and transitions[-1]["successor_checkpoint"].get("status") != "saved")),
                "policy_or_ledger_edits": 0, "new_sway_start_stop_retarget": 0,
                "checkpoint_owner": "Root normal checkpoint operation after this helper",
            })
        except Exception as diagnostic_error:
            if selected_error is None:
                raise
            diagnostic_failed = True
            _note_diagnostic_failure(selected_error, "LOOP-RESULT", diagnostic_error)
    if primary_error is not None and diagnostic_failed:
        raise primary_error.with_traceback(primary_traceback)
    return 0 if status in {
        "TARGET_DATE_REACHED_ROOT_CHECKPOINT_PENDING",
        "ROOT_STOP_AT_NORMAL_CHECKPOINT_PENDING",
        "ROOT_SUCCESSOR_SAVED_CHECKPOINT_PENDING",
    } else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("packet", "qualification", "initial-snapshot", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    for name in ("sway-completion", "sway-opinion", "sway-observer-binding"):
        parser.add_argument("--" + name, type=Path)
    parser.add_argument("--first-turn-response", "--resume-response",
                        dest="first_turn_response", type=Path, required=True,
                        help="Root latest completed ordinary response before this serial loop")
    parser.add_argument("--prefix", required=True)
    parser.add_argument("--days", type=int, default=24)
    parser.add_argument("--response-timeout-seconds", type=float, required=True)
    return run(parser.parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
