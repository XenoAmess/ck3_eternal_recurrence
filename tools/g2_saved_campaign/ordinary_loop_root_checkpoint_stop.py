"""Root file-queue ordinary loop bound to actual saved-campaign responses.

No SDK import/launch, process/window operation, policy edit or ledger write.
An actual matched natural successor uses the existing Queue and normal SAVE.
The held Root SDK executor owns every call and preserves each raw response.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import time

import m7_ordinary_successor_queue as m7


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
    def __init__(self, packet: Path, output: Path, prefix: str, timeout: float):
        self.inbox = packet / "gameplay-requests"
        self.outbox = packet / "gameplay-responses"
        self.output, self.prefix, self.timeout = output, prefix, timeout
        self.sequence = 0
        self.requests = []

    def call(self, tool: str, arguments: dict, kind: str) -> tuple[dict, Path]:
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
                    return body(raw), response_path
            if time.monotonic() >= deadline:
                raise TimeoutError(f"Original request remains pending; do not resend: {request_path}")
            time.sleep(0.25)

    def thin(self, kind: str, value: dict) -> None:
        write(self.output / f"{self.sequence:06d}-{kind}-thin.json", value)
        print(json.dumps(value, ensure_ascii=False, separators=(",", ":")), flush=True)


def observe_sway(queue: Queue, revision: int) -> int:
    completion, completion_path = queue.call(
        "ck3_query_active_scheme_sway_completion_private_v1",
        {"expected_revision": revision, "target_character_id": 34333,
         "scheme_instance_id": 134217986}, "sway-completion")
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
    opinion, opinion_path = queue.call(
        "ck3_query_active_scheme_sway_outcome_opinion_private_v1",
        {"expected_revision": revision, "target_character_id": 34333}, "sway-opinion")
    queue.thin("sway-opinion", {
        "response": str(opinion_path),
        **{key: opinion.get(key) for key in (
            "schema", "available", "unavailable_reason", "date_raw",
            "actor_character_id", "target_character_id", "target_opinion_of_actor",
            "scheme_sway_opinion", "sway_blocker_opinion", "queried_revision",
            "queried_native_revision")},
    })
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
    initial_opinion = body(read(args.sway_opinion))
    initial_completion = body(read(args.sway_completion))
    last_leaf_date = initial_opinion["date_raw"]
    args.output.mkdir(parents=True, exist_ok=False)
    queue = Queue(args.packet, args.output, args.prefix, args.response_timeout_seconds)
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
    sway_episode_observer = initial.get("episode_character_id") == 29829
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
        sway_episode_observer = False  # Robert's fixed scheme ends with his actual episode.

    def adopt_observed_successor():
        snapshot, path, transition = m7.continue_successor(
            queue, current_episode, transitions)
        adopt_snapshot(snapshot, path, transition)

    def adopt_completed_response(turn, response_path):
        snapshot, path, transition = m7.consume_completed(
            queue, turn, response_path, source_snapshot, source_snapshot_path,
            transitions, checkpoint_pair)
        adopt_snapshot(snapshot, path, transition)

    try:
        if m7.completed_continuation(first):
            adopt_completed_response(first, args.first_turn_response)
        elif first.get("status") != "executed":
            raise ValueError("retain original nonexecuted first response for Root review")
        elif frame is not None and frame.get("one_life_terminal") is True:
            if frame.get("one_life_terminal_reason") != "played_character_changed":
                raise ValueError("retain actual non-successor terminal for Root review")
            adopt_observed_successor()
        if (sway_episode_observer and frame is not None
                and current_date > last_leaf_date):
            last_leaf_date = observe_sway(queue, frame["revision"])
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
                last_leaf_date = observe_sway(queue, frame["revision"])
        else:
            status = "TARGET_DATE_REACHED_ROOT_CHECKPOINT_PENDING"
    except Exception as error:
        status = "ROOT_REVIEW_ORIGINAL_RESPONSE_REQUIRED"
        queue.thin("error", {"error": repr(error), "pending_requests_not_resent": True})
    finally:
        write(args.output / "LOOP-RESULT.json", {
            "status": status, "started_at_utc": started,
            "ended_at_utc": datetime.now(timezone.utc).isoformat(),
            "qualification": str(args.qualification), "initial_snapshot": str(args.initial_snapshot),
            "first_turn_response": str(args.first_turn_response),
            "sway_baseline_responses": [str(args.sway_completion), str(args.sway_opinion)],
            "initial_original_scheme": {key: initial_completion.get(key) for key in (
                "scheme_instance_id", "scheme_instance_generation", "native_status_key")},
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
            "original_sway_episode_observation_ended": not sway_episode_observer,
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
    return 0 if status in {
        "TARGET_DATE_REACHED_ROOT_CHECKPOINT_PENDING",
        "ROOT_STOP_AT_NORMAL_CHECKPOINT_PENDING",
        "ROOT_SUCCESSOR_SAVED_CHECKPOINT_PENDING",
    } else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("packet", "qualification", "initial-snapshot",
                 "sway-completion", "sway-opinion", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--first-turn-response", "--resume-response",
                        dest="first_turn_response", type=Path, required=True,
                        help="Root latest completed ordinary response before this serial loop")
    parser.add_argument("--prefix", required=True)
    parser.add_argument("--days", type=int, default=24)
    parser.add_argument("--response-timeout-seconds", type=float, required=True)
    return run(parser.parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
