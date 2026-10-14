"""Review completed native vanilla-event batches without calling Game/MCP/OBS."""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import hashlib
import importlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import time


def load_analyzer(sdk_src=None, analysis_file=None, analysis_sha=None):
    if sdk_src is not None:
        sys.path.insert(0, str(sdk_src))
    if analysis_file is None:
        return importlib.import_module("xar_autoplayer.vanilla_events.event_offline_analysis")
    path = Path(analysis_file)
    if not analysis_sha or hashlib.sha256(path.read_bytes()).hexdigest() != analysis_sha:
        raise ValueError("offline vanilla analyzer SHA missing or changed")
    spec = importlib.util.spec_from_file_location(
        "xar_autoplayer.vanilla_events.offline_worker_pinned_analyzer", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def process_batches(analyzer, run_root, game_root, output_root, state_dir):
    results = []
    for batch in sorted(Path(run_root).glob("p*-offline-batches/*.json")):
        manifest, raw = analyzer.read_json(batch)
        vanilla = [item for item in manifest.get("new_incidents", [])
                   if item.get("kind") != "pending_character_interaction"
                   and item.get("event_definition_key")]
        if not vanilla:
            continue
        digest = hashlib.sha256(raw).hexdigest()
        destination = Path(output_root) / (batch.parent.name + "-" + batch.stem + "-" + digest[:12])
        done = destination / "EVENT-SOURCE-REVIEW.json"
        if done.exists():
            continue
        result = analyzer.analyze_event_batch(batch, game_root, destination, publish_state_dir=state_dir)
        results.append({"batch": str(batch), "reviewed": len(result["entries"]),
                        "already_known": len(result["already_known"]),
                        "unknown": len(result["unresolved"]), "report": str(done)})
    return results


@contextmanager
def worker_lock(output_root):
    with (Path(output_root) / "worker.lock").open("a+b") as lock:
        lock.seek(0)
        if os.name == "nt":
            import msvcrt
            msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            yield
        finally:
            lock.seek(0)
            if os.name == "nt":
                msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(lock.fileno(), fcntl.LOCK_UN)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--sdk-src", type=Path)
    parser.add_argument("--game-root", type=Path, required=True)
    parser.add_argument("--state-dir", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--analysis-file", type=Path)
    parser.add_argument("--analysis-sha")
    parser.add_argument("--stop-file", type=Path, required=True)
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    analyzer = load_analyzer(args.sdk_src, args.analysis_file, args.analysis_sha)
    args.output_root.mkdir(parents=True, exist_ok=True)
    with worker_lock(args.output_root):
        while not args.stop_file.exists():
            if args.analysis_file is not None and hashlib.sha256(args.analysis_file.read_bytes()).hexdigest() != args.analysis_sha:
                raise ValueError("offline vanilla analyzer SHA changed")
            rows = process_batches(analyzer, args.run_root, args.game_root, args.output_root, args.state_dir)
            for row in rows:
                print(json.dumps(row), flush=True)
            if args.once:
                print(json.dumps({"status": "offline_scan_finished", "batches": len(rows),
                                  "Game_MCP_OBS_calls": 0}), flush=True)
                return
            time.sleep(3)


if __name__ == "__main__":
    main()
