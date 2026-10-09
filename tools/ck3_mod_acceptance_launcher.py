"""Launch one frozen shared host after direct, fresh Steam image review.

The detached supervisor retains the real host Popen. Its exit receipt is host
process evidence only; product acceptance and normal CK3 exit remain separate.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import time

from ck3_mod_acceptance_keeper import check_pin, live_lease, pin, read_json, require, utc, write_new

MAX_REVIEW_AGE = 600


def recent(timestamp, *, now=None):
    instant = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    now = now or datetime.now(timezone.utc)
    require(instant.tzinfo is not None and 0 <= (now - instant).total_seconds() <= MAX_REVIEW_AGE,
            "Direct review/challenge/Steam frame is stale or from the future")
    return instant


def frozen_run(run_root, *, all_pins=True):
    root = Path(run_root).resolve()
    frozen_path = root / "frozen-argv.json"
    frozen = read_json(frozen_path)
    require(isinstance(frozen.get("run_id"), str) and frozen["run_id"] and
            isinstance(frozen.get("argv"), list) and frozen["argv"] and
            all(isinstance(arg, str) and arg for arg in frozen["argv"]), "Actual frozen run/argv required")
    require(frozen.get("launch_requires_fresh_owned_cas_and_offline_direct_review") is True,
            "Allocated direct review gate is missing")
    require(frozen.get("previous_session_closed") is True and frozen.get("previous_screen_released") is True,
            "Previous managed session/screen closure is not admitted")
    context = read_json(root / "ready-context.json")
    check_pin(context["frozen_argv"])
    require(Path(context["frozen_argv"]["path"]).resolve() == frozen_path and
            context.get("run_id") == frozen["run_id"] and Path(context["run_dir"]).resolve() == root,
            "Ready allocation does not bind this exact frozen argv")
    files = frozen.get("files")
    require(isinstance(files, dict) and files, "Allocated exact input pins required")
    if all_pins:
        for name, row in files.items():
            check_pin({**row, "path": name})
        check_pin(frozen["runtime_manifest"])
    # A copied helper must not silently import another unpinned sibling.
    for name in ("ck3_mod_acceptance_launcher.py", "ck3_mod_acceptance_keeper.py", "ck3_mod_acceptance_queue.py"):
        path = Path(__file__).with_name(name).resolve()
        require(str(path) in files, "Public helper is absent from allocation pins: " + str(path))
        check_pin({**files[str(path)], "path": str(path)})
    host = str(Path(frozen["argv"][frozen["argv"].index("--agent-source-root") - 1]).resolve())
    require(host in files, "Actual shared host is absent from allocation pins")
    check_pin({**files[host], "path": host})
    frozen["_checked_frozen_argv"] = pin(frozen_path)
    return frozen, context


def check_fresh_frame(frame_path, image, *, now=None):
    frame_path, image = Path(frame_path).resolve(), Path(image).resolve()
    frame = read_json(frame_path)
    require(frame.get("schema") == "ck3.steam_fresh_desktop_frame.v1" and
            frame.get("moving_edge_changed") is True and
            frame.get("restored_rect") == frame.get("before_rect") and
            frame.get("moved_rect") != frame.get("before_rect"), "Actual reversible Steam freshness proof required")
    captured = recent(frame["captured_at_utc"], now=now)
    require(Path(frame["moved_path"]).resolve() == image and
            pin(image)["sha256"] == str(frame["moved_sha256"]).lower() and
            str(frame["before_sha256"]).lower() != str(frame["moved_sha256"]).lower(),
            "Freshness proof differs from the directly reviewed original frame")
    check_pin({"path": frame["before_path"], "bytes": Path(frame["before_path"]).stat().st_size,
               "sha256": str(frame["before_sha256"]).lower()})
    if frame.get("clock_check") is not None:
        require(frame["clock_check"].get("clock_pixels_unchanged") is False,
                "Freshness proof retains a stale desktop clock")
    from PIL import Image, ImageChops
    with Image.open(image) as moved, Image.open(frame["before_path"]) as before:
        require(list(moved.size) == frame["desktop_size"] and before.size == moved.size,
                "Steam original dimensions differ from freshness receipt")
        delta = ImageChops.difference(before.convert("RGB"), moved.convert("RGB"))
        first, second = frame["before_rect"], frame["moved_rect"]
        edge = (min(first[0], second[0]), first[1], max(first[0], second[0]), first[3])
        require(delta.getbbox() is not None and delta.crop(edge).getbbox() is not None,
                "Original image bytes do not prove Steam window edge movement")
    return frame, captured


def create_challenge(run_root, keeper_root, frame_path, image, output):
    frozen, context = frozen_run(run_root)
    require(Path(context["keeper_root"]).resolve() == Path(keeper_root).resolve(), "Wrong allocated keeper")
    lease = live_lease(keeper_root, frozen)
    frame, _ = check_fresh_frame(frame_path, image)
    output = Path(output).resolve()
    require(not output.exists(), "Use a new direct-review challenge directory")
    output.mkdir(parents=True)
    nonce = secrets.token_hex(16)
    from PIL import Image, ImageDraw
    with Image.open(image) as original:
        reviewed = Image.new("RGB", (max(original.width, 760), original.height + 64), "white")
        reviewed.paste(original.convert("RGB"), (0, 64))
        draw = ImageDraw.Draw(reviewed)
        draw.text((10, 8), "DIRECT REVIEW NONCE: " + nonce, fill="black")
        draw.text((10, 30), "Read Steam offline status in the original frame below; this banner does not certify it.", fill="black")
        reviewed.save(output / "direct-review.png")
    challenge = {"schema": "ck3-mod-acceptance-review-challenge-v1", "created_at_utc": utc(),
        "nonce": nonce, "run_id": frozen["run_id"], "screen_task": frozen["screen_task"],
        "frozen_argv": pin(Path(run_root) / "frozen-argv.json"), "keeper_root": str(Path(keeper_root).resolve()),
        "keeper_inputs": pin(Path(keeper_root) / "inputs.json"), "frame": pin(frame_path), "image": pin(image),
        "review_image": pin(output / "direct-review.png"), "cas_at_creation": lease["lease"],
        "offline_status_observed": None, "business_pass": False}
    write_new(output / "challenge.json", challenge)
    return {"status": "DIRECT_IMAGE_REVIEW_REQUIRED", "challenge": pin(output / "challenge.json"),
            "review_image": challenge["review_image"], "business_pass": False}


def validate_review(frozen, keeper_root, proof_path, challenge_path, observed_nonce, reviewer, *, now=None):
    proof, challenge = read_json(proof_path), read_json(challenge_path)
    require(challenge.get("schema") == "ck3-mod-acceptance-review-challenge-v1" and
            proof.get("schema") == "ck3-mod-acceptance-direct-review-v1", "Shared direct-review schemas required")
    created, reviewed = recent(challenge["created_at_utc"], now=now), recent(proof["reviewed_at_utc"], now=now)
    require(created <= reviewed and isinstance(reviewer, str) and reviewer.strip() and
            proof.get("reviewer") == reviewer and proof.get("direct_image_review") is True and
            proof.get("steam_offline_confirmed") is True, "Current operator's direct Steam offline image review required")
    require(isinstance(observed_nonce, str) and len(observed_nonce) == 32 and
            secrets.compare_digest(observed_nonce, str(challenge.get("nonce", ""))) and
            proof.get("observed_nonce") == observed_nonce, "Directly observed fresh image nonce differs")
    for value in (proof, challenge):
        require(value.get("run_id") == frozen["run_id"] and value.get("screen_task") == frozen["screen_task"],
                "Direct review belongs to another allocated run/screen task")
    require(Path(challenge["keeper_root"]).resolve() == Path(keeper_root).resolve(), "Challenge crossed keeper")
    for key in ("frozen_argv", "keeper_inputs", "frame", "image", "review_image"):
        check_pin(challenge[key])
    require(challenge["frozen_argv"] == frozen["_checked_frozen_argv"] and
            Path(challenge["keeper_inputs"]["path"]).resolve() == Path(keeper_root).resolve() / "inputs.json",
            "Direct review differs from this actual frozen allocation/keeper")
    require(challenge["frozen_argv"] == pin(Path(proof["frozen_argv"]["path"])), "Review frozen argv changed")
    for key in ("frozen_argv", "image", "review_image"):
        require(proof.get(key) == challenge[key], "Direct review bytes differ: " + key)
    require(proof.get("challenge") == pin(challenge_path), "Direct review challenge bytes changed")
    frame, captured = check_fresh_frame(challenge["frame"]["path"], challenge["image"]["path"], now=now)
    require(captured <= created, "Challenge predates its claimed Steam frame")
    return {"proof": pin(proof_path), "challenge": pin(challenge_path), "image": challenge["image"],
            "reviewer": reviewer, "screen_task": frozen["screen_task"], "steam_pid": frame["steam_pid"],
            "reviewed_at_utc": proof["reviewed_at_utc"]}


def admission(args):
    root = args.run_root.resolve()
    frozen, context = frozen_run(root)
    require(Path(context["keeper_root"]).resolve() == args.keeper_root.resolve(), "Wrong allocated keeper")
    review = validate_review(frozen, args.keeper_root, args.proof, args.challenge, args.observed_nonce, args.reviewer)
    owner = live_lease(args.keeper_root, frozen)
    import psutil
    steam = psutil.Process(review["steam_pid"])
    require(steam.name().lower() in ("steam.exe", "steamwebhelper.exe"), "Reviewed Steam UI process is absent or replaced")
    require(not any((row.info["name"] or "").lower() == "ck3.exe" for row in psutil.process_iter(["name"])),
            "CK3 is already running")
    expected_environment = frozen.get("runtime_environment", {})
    require(all(os.environ.get(name) == value for name, value in expected_environment.items()),
            "Actual host import environment differs from frozen shared runtime")
    require("--output" in frozen["argv"] and
            Path(frozen["argv"][frozen["argv"].index("--output") + 1]).resolve() == root / "native-report.json",
            "Host output differs from actual allocation")
    return frozen, review, owner


def retain_host(root, frozen, review, owner):
    """Retain one actual Popen until wait returns; useful with harmless test children."""
    root = Path(root).resolve()
    require(not (root / "host-started.json").exists(), "Shared host launch already consumed")
    stdout = (root / "host-stdout.log").open("xb")
    stderr = (root / "host-stderr.log").open("xb")
    child = None
    try:
        child = subprocess.Popen(frozen["argv"], cwd=frozen["lease_anchor"], stdout=stdout, stderr=stderr)
        import psutil
        try:
            creation = psutil.Process(child.pid).create_time()
        except psutil.NoSuchProcess:
            creation = None  # A quick real child can already be waitable.
        write_new(root / "host-started.json", {"at_utc": utc(), "pid": child.pid,
            "create_time": creation, "supervisor_pid": os.getpid(),
            "argv": frozen["argv"], "run_id": frozen["run_id"], "admitted_lease": owner["lease"],
            "direct_review": review, "actual_popen_retained": True, "business_pass": False})
        code = child.wait()
        write_new(root / "host-original-process-exit.json", {"at_utc": utc(), "pid": child.pid,
            "returncode": code, "run_id": frozen["run_id"], "actual_original_popen_wait": True,
            "normal_ck3_exit_inferred": False, "business_pass": False})
        return 0 if code == 0 else 1
    finally:
        # If recording the start fails after CreateProcess, keep the original
        # handle alive until that same child exits. Never turn a lost parent
        # observation into an invented process-gone/exit0 receipt.
        if child is not None and not (root / "host-original-process-exit.json").exists():
            code = child.wait()
            write_new(root / "host-original-process-exit.json", {"at_utc": utc(), "pid": child.pid,
                "returncode": code, "run_id": frozen["run_id"], "actual_original_popen_wait": True,
                "normal_ck3_exit_inferred": False, "business_pass": False,
                "start_recording_failed": True})
        stdout.close(); stderr.close()


def supervise(args):
    root = args.run_root.resolve()
    intent = read_json(root / "launch-intent.json")
    require(intent.get("ticket") == args.launch_ticket, "Original once-only launcher ticket differs")
    check_pin(intent["proof"]); check_pin(intent["challenge"]); check_pin(intent["frozen_argv"])
    frozen, review, owner = admission(args)
    return retain_host(root, frozen, review, owner)


def launch(args):
    root = args.run_root.resolve()
    frozen, review, owner = admission(args)
    require(not (root / "launch-intent.json").exists(), "Original launch intent already consumed; never replay")
    ticket = secrets.token_hex(32)
    write_new(root / "launch-intent.json", {"at_utc": utc(), "ticket": ticket, "run_id": frozen["run_id"],
        "proof": pin(args.proof), "challenge": pin(args.challenge), "frozen_argv": pin(root / "frozen-argv.json"),
        "admitted_lease": owner["lease"], "business_pass": False})
    argv = [sys.executable, "-B", "-X", "utf8", str(Path(__file__).resolve()),
            "--run-root", str(root), "--keeper-root", str(args.keeper_root.resolve()),
            "--proof", str(args.proof.resolve()), "--challenge", str(args.challenge.resolve()),
            "--observed-nonce", args.observed_nonce, "--reviewer", args.reviewer,
            "--supervise", "--launch-ticket", ticket]
    with (root / "host-supervisor-stdout.log").open("xb") as stdout, (root / "host-supervisor-stderr.log").open("xb") as stderr:
        child = subprocess.Popen(argv, cwd=frozen["lease_anchor"], stdout=stdout, stderr=stderr,
                                 creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    write_new(root / "host-supervisor-started.json", {"at_utc": utc(), "pid": child.pid, "argv": argv,
                                                    "business_pass": False})
    deadline = time.monotonic() + 45
    while time.monotonic() < deadline:
        if (root / "host-started.json").exists():
            print(json.dumps({"status": "ORIGINAL_SHARED_HOST_STARTED", "run_id": frozen["run_id"],
                "host": read_json(root / "host-started.json"), "business_pass": False}), flush=True)
            return 0
        require(child.poll() is None, "Original host supervisor failed; inspect retained stderr and never replay")
        time.sleep(.05)
    raise TimeoutError("Original host supervisor launch not proved in budget; never replay")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-root", required=True, type=Path)
    parser.add_argument("--keeper-root", required=True, type=Path)
    parser.add_argument("--proof", type=Path)
    parser.add_argument("--challenge", type=Path)
    parser.add_argument("--observed-nonce")
    parser.add_argument("--reviewer")
    parser.add_argument("--create-challenge", action="store_true")
    parser.add_argument("--fresh-frame", type=Path)
    parser.add_argument("--image", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--supervise", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--launch-ticket", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    try:
        if args.create_challenge:
            require(args.fresh_frame and args.image and args.output and not args.supervise,
                    "Challenge requires --fresh-frame --image --output")
            print(json.dumps(create_challenge(args.run_root, args.keeper_root, args.fresh_frame, args.image, args.output)))
            return 0
        require(args.proof and args.challenge and args.observed_nonce and args.reviewer,
                "Fresh directly reviewed proof/challenge/nonce/reviewer required")
        return supervise(args) if args.supervise else launch(args)
    except Exception as error:
        print(json.dumps({"status": "BLOCKED", "error": repr(error), "business_pass": False}), file=sys.stderr, flush=True)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
