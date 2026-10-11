"""Root-owned finite ordinary chunks with the existing normal checkpoint API.

Root starts this after its current serial loop and actual SAVE.
The existing file SDK owns all MCP calls. No SDK/Game/process/window operation,
policy or Actor change, Driver/save-body read, hashing, trimming, or resubmission.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace


LOOP_SOURCE = Path(__file__).with_name("ordinary_loop_root_checkpoint_stop.py")
CHECKPOINTABLE = {
    "TARGET_DATE_REACHED_ROOT_CHECKPOINT_PENDING",
    "ROOT_STOP_AT_NORMAL_CHECKPOINT_PENDING",
    "ROOT_SUCCESSOR_SAVED_CHECKPOINT_PENDING",
}


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def latest_refs(result: dict, normal: Path, completion: Path, opinion: Path):
    """Use completed loop response references without reparsing normal payloads."""
    for request in result["requests"]:
        response = Path(request["response"])
        if (response.name.endswith("-normal.json")
                or response.name.endswith("-m7-successor-continue.json")):
            normal = response
        elif response.name.endswith("-sway-completion.json"):
            completion = response
        elif response.name.endswith("-sway-opinion.json"):
            opinion = response
    return normal, completion, opinion


def run(args) -> int:
    spec = importlib.util.spec_from_file_location("_root_checkpoint_loop", LOOP_SOURCE)
    loop = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loop)
    args.output.mkdir(parents=True, exist_ok=False)
    started = now()
    snapshot_path, save_path = args.current_snapshot, args.current_save
    normal_path = args.resume_response
    completion_path, opinion_path = args.sway_completion, args.sway_opinion
    saved_days = args.saved_normal_days
    saved_date = None
    chunks = []
    checkpoint_requests = []
    status, error = "RUNNING", None
    try:
        # These are Root's already-completed current snapshot/SAVE, not new calls.
        initial_snapshot = loop.body(loop.read(snapshot_path))
        initial_save = loop.body(loop.read(save_path))
        checkpoint = initial_save.get("checkpoint", {})
        if (checkpoint.get("status") != "saved"
                or checkpoint.get("date_raw") != initial_snapshot.get("date_raw")
                or not isinstance(initial_snapshot.get("episode_run_id"), str)
                or not initial_snapshot["episode_run_id"]
                or type(initial_snapshot.get("episode_character_id")) is not int
                or initial_snapshot["episode_character_id"] <= 0
                or checkpoint.get("episode_run_id") != initial_snapshot["episode_run_id"]
                or checkpoint.get("episode_character_id") != initial_snapshot["episode_character_id"]
                or checkpoint.get("succession_lifecycle") != initial_snapshot.get("succession_lifecycle")):
            raise ValueError("bind the actual matching current snapshot and saved checkpoint")
        saved_date = checkpoint["date_raw"]
        for chunk_index in range(1, args.chunks + 1):
            if args.stop_file is not None and args.stop_file.exists():
                status = "ROOT_STOPPED_AT_SAVED_CHECKPOINT"
                break
            chunk_prefix = f"{args.prefix}-chunk{chunk_index:02d}"
            chunk_output = args.output / f"chunk{chunk_index:02d}-ordinary"
            ordinary_args = SimpleNamespace(
                packet=args.packet, qualification=args.qualification,
                initial_snapshot=snapshot_path, first_turn_response=normal_path,
                sway_completion=completion_path, sway_opinion=opinion_path,
                output=chunk_output, prefix=chunk_prefix,
                days=args.days_per_chunk,
                response_timeout_seconds=args.response_timeout_seconds,
                stop_after_normal_file=args.stop_file,
                # Actual current SAVE was paired with snapshot above or below.
                matched_checkpoint_episode={key: checkpoint[key] for key in (
                    "episode_character_id", "episode_run_id", "succession_lifecycle")},
            )
            code = loop.run(ordinary_args)
            result_path = chunk_output / "LOOP-RESULT.json"
            result = loop.read(result_path)
            chunk = {
                "chunk": chunk_index, "loop_result": str(result_path),
                "loop_status": result["status"],
                "loop_start_date_raw": result["starting_date_raw"],
                "loop_end_date_raw": result["current_date_raw"],
                "normal_turns": result["normal_turns"],
                "checkpoint_status": "NOT_REQUESTED",
            }
            chunks.append(chunk)
            if code != 0 or result["status"] not in CHECKPOINTABLE:
                status = "ROOT_REVIEW_ORIGINAL_LOOP_RESULT_REQUIRED"
                break  # Retain all failed/pending requests; never resend.
            normal_path, completion_path, opinion_path = latest_refs(
                result, normal_path, completion_path, opinion_path)
            actual_normal_days = result["actual_days_from_initial"]
            chunk["actual_normal_days_from_loop"] = actual_normal_days
            reuse_successor_save = result.get("last_successor_save_is_loop_endpoint") is True
            if actual_normal_days <= 0 and not reuse_successor_save:
                chunk["checkpoint_status"] = "NO_NEW_NORMAL_DAYS_NO_SAVE"
                status = "ROOT_STOPPED_AT_SAVED_CHECKPOINT"
                break
            if reuse_successor_save:
                next_snapshot_path = Path(result["latest_successor_snapshot"])
                next_save_path = Path(result["latest_successor_save"])
                snapshot = loop.body(loop.read(next_snapshot_path))
                saved = loop.body(loop.read(next_save_path))
                checkpoint = saved.get("checkpoint", {})
                if (checkpoint.get("status") != "saved"
                        or checkpoint.get("date_raw") != result["current_date_raw"]
                        or checkpoint.get("date_raw") != snapshot.get("date_raw")):
                    raise ValueError("reuse requires the actual endpoint successor SAVE")
                queue = None
            else:
                checkpoint_output = args.output / f"chunk{chunk_index:02d}-checkpoint"
                checkpoint_output.mkdir()
                queue = loop.Queue(args.packet, checkpoint_output,
                                   chunk_prefix + "-checkpoint",
                                   args.response_timeout_seconds)
                checkpoint_requests = queue.requests
                # Exact normal snapshot/SAVE request shapes from ROOT-QUEUE-R85-LIFECYCLE.py.
                snapshot, next_snapshot_path = queue.call(
                    "ck3_take_snapshot", {"include_native_command_history": False}, "snapshot")
                revision = snapshot.get("revision")
                if type(revision) is not int or revision <= 0:
                    raise ValueError("normal SAVE requires the fresh actual PUBLIC revision")
                if snapshot.get("date_raw") != result["current_date_raw"]:
                    raise ValueError("fresh snapshot differs from the completed normal-loop endpoint")
                queue.thin("snapshot", {
                    "response": str(next_snapshot_path), "revision": revision,
                    "native_revision": snapshot.get("native_revision"),
                    "date_raw": snapshot.get("date_raw"), "paused": snapshot.get("paused"),
                    "episode_run_id": snapshot.get("episode_run_id"),
                })
                saved, next_save_path = queue.call(
                    "ck3_save_checkpoint", {"expected_revision": revision}, "save")
                checkpoint = saved.get("checkpoint", {})
                if (checkpoint.get("status") != "saved"
                        or checkpoint.get("date_raw") != snapshot.get("date_raw")):
                    raise ValueError("normal checkpoint was not confirmed saved at the current date")
            if (checkpoint.get("episode_character_id") != snapshot.get("episode_character_id")
                    or checkpoint.get("episode_run_id") != snapshot.get("episode_run_id")
                    or checkpoint.get("succession_lifecycle") != snapshot.get("succession_lifecycle")):
                raise ValueError("actual endpoint SAVE differs from its snapshot episode/lifecycle")
            # Count only the completed ordinary loop's actual day credit.
            # Snapshot/SAVE dates verify its endpoint; neither creates credit.
            actual_saved_days = actual_normal_days
            saved_days += actual_saved_days
            saved_date = checkpoint["date_raw"]
            snapshot_path, save_path = next_snapshot_path, next_save_path
            chunk.update({
                "checkpoint_status": "SAVED", "snapshot": str(snapshot_path),
                "save": str(save_path), "date_raw": saved_date,
                "history_index": checkpoint.get("history_index"),
                "actual_days_saved_this_chunk": actual_saved_days,
                "saved_normal_days_cumulative": saved_days,
                "saved_count_origin": "prior explicit saved count + LOOP-RESULT.actual_days_from_initial",
                "last_normal": str(normal_path),
                "last_sway_completion": str(completion_path),
                "last_sway_opinion": str(opinion_path),
            })
            chunk["natural_succession_transitions"] = result.get("natural_succession_transitions", [])
            chunk["reused_actual_successor_endpoint_save"] = reuse_successor_save
            if queue is not None:
                queue.thin("save", {**chunk, "checkpoint": checkpoint})
            loop.write(args.output / f"chunk{chunk_index:02d}-saved.json", chunk)
            checkpoint_requests = []
            if (result["status"] == "ROOT_STOP_AT_NORMAL_CHECKPOINT_PENDING"
                    or (args.stop_file is not None and args.stop_file.exists())):
                status = "ROOT_STOPPED_AT_SAVED_CHECKPOINT"
                break
        else:
            status = "ROOT_BOUNDED_CHUNKS_SAVED"
    except Exception as caught:
        status = "ROOT_REVIEW_ORIGINAL_RESPONSE_REQUIRED"
        error = repr(caught)
    finally:
        receipt = {
            "status": status, "started_at_utc": started, "ended_at_utc": now(),
            "packet": str(args.packet), "qualification": str(args.qualification),
            "chunks_requested": args.chunks, "days_per_chunk": args.days_per_chunk,
            "chunks": chunks, "current_saved_date_raw": saved_date,
            "saved_normal_days_cumulative": saved_days,
            "saved_count_origin": "Root supplied initial count plus completed ordinary-loop actual days only",
            "current_snapshot": str(snapshot_path), "current_save": str(save_path),
            "last_normal": str(normal_path),
            "last_sway_completion": str(completion_path),
            "last_sway_opinion": str(opinion_path),
            "checkpoint_requests_retained": checkpoint_requests,
            "error": error, "failed_pending_never_resent": True,
            "Actor_Game_source_policy_changes": 0,
            "Driver_save_body_reads_hashes_history_trims": 0,
            "new_qualification_runs": 0,
        }
        loop.write(args.output / "BOUNDED-RESULT.json", receipt)
        print(json.dumps(receipt, ensure_ascii=False, separators=(",", ":")), flush=True)
    return 0 if status in {
        "ROOT_BOUNDED_CHUNKS_SAVED", "ROOT_STOPPED_AT_SAVED_CHECKPOINT",
    } else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("packet", "qualification", "current-snapshot", "current-save",
                 "resume-response", "sway-completion", "sway-opinion", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--saved-normal-days", type=float, required=True)
    parser.add_argument("--prefix", required=True)
    parser.add_argument("--chunks", type=int, default=4)
    parser.add_argument("--days-per-chunk", type=int, default=7)
    parser.add_argument("--response-timeout-seconds", type=float, required=True)
    parser.add_argument("--stop-file", type=Path)
    return run(parser.parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
