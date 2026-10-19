"""Small episode-01 producers using the released toolchain's public APIs.

No desktop, game or recorder operations. Inputs and outputs are explicit;
attempts never overwrite or clean prior material. Context and causal credit
remain separate even when real gameplay supplies the background picture.
"""
import argparse
from dataclasses import asdict
from datetime import datetime, timezone
from importlib import metadata
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys
import traceback
import urllib.error
import urllib.request

from xar_promo.model import ProjectConfig
from xar_promo.operations import preserve_artifact, start_run
from xar_promo.pipeline_commands import handle_build, handle_plan
from xar_promo.process import CommandSpec, run_command
from xar_promo.project import sha256_file

from .context_composer import ADAPTER, PRESET, compose, registry

LATEST = "https://api.github.com/repos/XenoAmess/xar_promo_toolchain/releases/latest"


def now():
    return datetime.now(timezone.utc).isoformat()


def read(path):
    return json.loads(Path(path).read_text("utf-8"))


def write(path, value):
    with Path(path).open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, default=str)
        handle.write("\n")
    return Path(path)


def pin(path):
    path = Path(path).resolve()
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": sha256_file(path).lower()}


def bound(value):
    if not isinstance(value, dict) or not {"path", "bytes", "sha256"} <= value.keys():
        raise ValueError("Expected an explicit path/bytes/SHA-256 binding")
    actual = pin(value["path"])
    if actual["bytes"] != value["bytes"] or actual["sha256"] != value["sha256"].lower():
        raise ValueError(f"Input bytes changed: {value['path']}")
    return Path(actual["path"])


def package_bytes(root):
    return sum(p.stat().st_size for p in Path(root).rglob("*") if p.is_file() and not p.is_symlink())


def command(argv, directory, label):
    return run_command(CommandSpec.create(argv, label=label),
                       audit_directory=Path(directory) / "commands" / label)


def preserve(run, path, identifier, role, collection="derived", media_type=None):
    return preserve_artifact(run, Path(path), artifact_id=identifier, role=role,
                             label=Path(path).name, collection=collection, media_type=media_type)


def cue_duration(speech_seconds):
    """16 video frames = 25 AAC frames at 30fps/48kHz; retain 0.20s tail."""
    if not math.isfinite(speech_seconds) or speech_seconds <= 0:
        raise ValueError("Actual speech duration must be finite and positive")
    return math.ceil((speech_seconds + 0.20) * 30 / 16) * 16 / 30


def project(script, cues=None, *, sample=False):
    cues = script["cues"] if cues is None else cues
    if not cues or len({r["id"] for r in cues}) != len(cues):
        raise ValueError("Expected unique nonempty narration cues")
    if any(r.get("live_result_asserted") is not False for r in cues):
        raise ValueError("This producer only freezes explicitly result-independent text")
    config = {
        "format_version": 1, "kind": "xar_promo_project_config",
        "project": {"id": "ck3-faith-episode01-context" if sample else "ck3-faith-episode01",
                    "title": "信仰与权力：第一期上下文试拍" if sample else "信仰与权力：第一期逐句作者输入"},
        "pipeline": {"adapter": ADAPTER, "preset": PRESET},
        "locales": {"narration": "zh-CN", "subtitles": ["zh-CN", "en"]},
        "constraints": {"duration_limit_seconds": 60 if sample else 2400},
        "chapters": [{"id": "context-sample" if sample else "narration", "type": "mixed-explainer",
                      "state": "planned", "title": {"zh-CN": "准备与机制解释"},
                      "cues": [{"id": r["id"], "narration": {"zh-CN": r["zh"]},
                                "subtitles": {"zh-CN": r["zh"], "en": r["en"]}} for r in cues],
                      "artifact_ids": []}],
    }
    ProjectConfig.from_mapping(config)
    return config


def _official_latest_release(destination, machine):
    """Retain authenticated CLI evidence only after explicit anonymous rate limiting."""
    request = urllib.request.Request(LATEST, headers={"Accept": "application/vnd.github+json",
                                                     "User-Agent": "ck3-faith-production"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            release = json.load(response)
            transport = {"method": "urllib", "anonymous_http_status": response.status}
    except urllib.error.HTTPError as error:
        if error.code not in (403, 429):
            raise
        body = error.read(65537)
        if len(body) > 65536:
            raise ValueError("Official API error body exceeds the bounded diagnostic") from error
        text = body.decode("utf-8", errors="replace")
        remaining = error.headers.get("X-RateLimit-Remaining")
        limited = (remaining is not None and remaining.strip() == "0"
                   or "rate limit exceeded" in text.casefold()
                   or "exceeded a secondary rate limit" in text.casefold())
        if error.code != 429 and not limited:
            raise
        diagnostic = write(Path(destination) / "official-latest-anonymous-rate-limit.json", {
            "machine_id": machine, "url": LATEST, "observed_at_utc": now(), "http_status": error.code,
            "reason": str(error.reason), "rate_limit_remaining": remaining, "body": text,
        })
        label = "official-latest-gh-api"
        result = command(["gh", "api", "--hostname", "github.com", "--method", "GET",
                          "--header", "Accept:application/vnd.github+json",
                          LATEST.removeprefix("https://api.github.com/")], destination, label)
        if result.returncode != 0:
            raise RuntimeError("Official latest release gh api failed; see command audit") from error
        release = json.loads(result.stdout)
        transport = {"method": "gh-api", "anonymous_http_status": error.code,
                     "anonymous_error": pin(diagnostic), "command_label": label}
    if not isinstance(release, dict):
        raise ValueError("Official latest release must be a JSON object")
    return release, transport


def fresh_runtime(repo, runtime, destination):
    """Read official latest Release, exact installed wheel, help and tool bytes."""
    machine = subprocess.check_output(
        [sys.executable, "-B", Path(repo) / "tools/ck3_live_run_id.py", "machine"],
        text=True, encoding="utf-8").strip()
    if runtime.get("machine_id") != machine:
        raise ValueError("Runtime input belongs to another machine")
    release, transport = _official_latest_release(destination, machine)
    dist = metadata.distribution("xar-promo-toolchain")
    direct = json.loads(dist.read_text("direct_url.json") or "null")
    wheels = [r for r in release["assets"] if r["name"].endswith(".whl")]
    if (release.get("draft") or release.get("prerelease")
            or release["tag_name"] != "v" + dist.version or len(wheels) != 1):
        raise ValueError("Install and qualify the current official final Release first")
    wheel = wheels[0]
    digest = (wheel.get("digest") or "").removeprefix("sha256:").lower()
    if (len(digest) != 64 or not direct or direct.get("url") != wheel["browser_download_url"]
            or direct.get("archive_info", {}).get("hashes", {}).get("sha256", "").lower() != digest):
        raise ValueError("Installed direct_url must match latest official wheel URL and SHA-256")
    results = {}
    for label, argv in (
        ("version", [sys.executable, "-B", "-m", "xar_promo", "--version"]),
        ("help", [sys.executable, "-B", "-m", "xar_promo", "--help"]),
        ("build-help", [sys.executable, "-B", "-m", "xar_promo", "build", "--help"]),
    ):
        result = command(argv, destination, label)
        results[label] = {"exit_code": result.returncode, "stdout": result.stdout}
    tools = {}
    for name in ("ffmpeg", "ffprobe"):
        path = bound(runtime[name])
        result = command([path, "-version"], destination, name + "-version")
        tools[name] = {**pin(path), "version": result.stdout}
    record = {"schema": "ck3-faith-power-production-runtime-v1", "machine_id": machine,
              "observed_at_utc": now(), "evidence_source": "fresh official API/direct_url/interpreter/help/executable observations",
              "python": {"path": sys.executable, "version": sys.version},
              "release": {"url": LATEST, "tag": release["tag_name"],
                          "published_at": release["published_at"], "wheel": wheel,
                          "transport": transport},
              "installed": {"version": dist.version, "direct_url": direct, "commands": results},
              "tools": tools, "game_started": False, "screen_owner_created": False}
    write(Path(destination) / "fresh-runtime.json", record)
    return record


def admission(args, machine, *, closed=False):
    """Consume the existing common-policy reservation; do not create a new one."""
    reservation = read(args.reservation)
    policy = read(Path(args.repo) / "docs/storage-retention-policy.json")
    if (reservation["machine_id"] != machine or not reservation["capacity_passed"]
            or not reservation["quota_passed"]
            or datetime.fromisoformat(reservation["reservation_review_at_utc"]) < datetime.now(timezone.utc)):
        raise ValueError("Fresh same-machine common storage reservation required")
    selected = [r for r in reservation["reservations"] if r["task"] == args.reservation_task]
    if len(selected) != 1 or args.peak_bytes <= 0:
        raise ValueError("One existing reservation and an explicit positive write peak required")
    package = Path(args.package_root).resolve()
    Path(args.output).resolve().relative_to(package)
    used = package_bytes(package)
    remaining_peak = 0 if closed else args.peak_bytes
    if used + remaining_peak > selected[0]["peak_bytes"]:
        raise ValueError("This write does not fit the existing package reservation")
    profile = reservation["profile"]
    volume_key = package.anchor.replace("\\", "/")
    growth = profile["system_growth_reserve_bytes_by_volume"][volume_key]
    disk = shutil.disk_usage(package)
    limits = policy["capacity"]
    safety = max(limits["safety_floor_bytes"], min(limits["safety_ceiling_bytes"],
                                                disk.total * limits["safety_volume_fraction"]))
    # Full admitted peaks are conservative upper bounds on unspent shares.
    all_peaks = sum(r["peak_bytes"] for r in reservation["reservations"])
    if disk.free < all_peaks + growth + safety:
        raise ValueError("Fresh volume free space no longer covers concurrent admitted peaks")
    if reservation["current_project_usage_upper_bound_bytes"] + all_peaks > reservation["effective_project_quota_bytes"]:
        raise ValueError("Common project quota no longer covers admitted peaks")
    return {"machine_id": machine, "observed_at_utc": now(),
            "evidence_source": "common-policy reservation plus fresh package inventory and disk_usage",
            "reservation": pin(args.reservation), "policy": pin(Path(args.repo) / "docs/storage-retention-policy.json"),
            "package_bytes": used, "this_write_peak_bytes": remaining_peak,
            "package_budget_bytes": selected[0]["peak_bytes"], "disk": disk._asdict(),
            "checkpoint": "task_close" if closed else "before_heavy_write",
            "capacity_passed": True, "quota_passed": True}


def open_attempt(args):
    runtime = read(args.runtime)
    # Admission precedes media writes and any provider call.
    admitted = admission(args, runtime["machine_id"])
    destination = Path(args.output).resolve()
    destination.mkdir(parents=True, exist_ok=False)
    args._created_output = True
    write(destination / "storage-admission.json", admitted)
    fresh = fresh_runtime(args.repo, runtime, destination)
    return runtime, fresh, destination


def run_synthesize(args):
    runtime, fresh, destination = open_attempt(args)
    script, recipe = read(args.script), read(args.recipe)
    # Optional provider installation is selected explicitly, not a machine path
    # imported by the repository. Its distribution identity is checked below.
    if runtime.get("edge_tts_module_root"):
        sys.path.insert(0, str(Path(runtime["edge_tts_module_root"]).resolve()))
    from xar_promo.tts.edge import EdgeTtsProvider
    from xar_promo.tts.provider import TtsRequest
    from xar_promo.tts.cache import tts_fingerprint
    import edge_tts
    provider = EdgeTtsProvider()
    if asdict(provider.identity) != recipe["provider_identity_for_frozen_fingerprints"]:
        raise ValueError("Provider version differs from the frozen voice recipe; freeze a new recipe")
    provider_receipt = bound(runtime["tts_runtime_receipt"])
    if metadata.version("edge-tts") != provider.identity.tool_version:
        raise ValueError("Imported provider and installed distribution version differ")
    provider_observation = write(destination / "provider-runtime.json", {
        "machine_id": fresh["machine_id"], "observed_at_utc": now(),
        "evidence_source": "imported provider module, installed distribution and explicit dependency receipt",
        "identity": asdict(provider.identity), "module": pin(edge_tts.__file__),
        "dependency_receipt": pin(provider_receipt),
    })
    cues = script["cues"]
    entries = {r["cue_id"]: r for r in recipe["entries"]}
    defaults = recipe["request_defaults"]
    project_path = write(destination / "project-config.json", project(script))
    run = start_run(project_path, run_id=destination.name, run_directory=destination / "native-run")
    for path, identifier, role in (
        (args.script, "episode-script-v1", "authoring-script"),
        (args.recipe, "voice-recipe-v1", "narration-recipe"),
        (provider_receipt, "provider-installation-v1", "runtime-dependencies"),
        (provider_observation, "provider-runtime-v1", "runtime-dependencies"),
        (destination / "fresh-runtime.json", "runtime-v1", "runtime-dependencies"),
        (destination / "storage-admission.json", "storage-v1", "storage-admission"),
        (Path(__file__), "producer-source-v1", "producer-source"),
    ):
        preserve(run, path, identifier, role)
    completed, failures = [], []
    for cue in cues:
        request = TtsRequest(cue["zh"], **defaults)
        if tts_fingerprint(request, provider.identity) != entries[cue["id"]]["tts_fingerprint"]:
            raise ValueError("Frozen voice fingerprint differs from exact cue text")
        request_path = write(destination / (cue["id"] + ".request.json"), {
            "machine_id": fresh["machine_id"], "observed_at_utc": now(),
            "evidence_source": "one actual provider invocation; no automatic replay",
            "provider": asdict(provider.identity), "request": request.cache_payload(),
            "cue_id": cue["id"],
        })
        target = destination / (cue["id"] + ".mp3")
        try:
            provider.synthesize(request, target)
            measured = json.loads(command([bound(runtime["ffprobe"]), "-v", "error",
                "-show_streams", "-show_format", "-of", "json", target], destination,
                cue["id"] + "-probe").stdout)
            duration = float(measured["format"]["duration"])
            cue_duration(duration)
            row = {"id": cue["id"], "audio": pin(target), "request": pin(request_path),
                   "speech_duration_seconds": duration, "status": "SYNTHESIZED_UNLISTENED",
                   "human_listening_performed": False, "pronunciation_approved": False}
            completed.append(row)
            preserve(run, target, "audio." + cue["id"], "narration", "raw", "audio/mpeg")
        except Exception as error:
            row = {"id": cue["id"], "error": repr(error), "traceback": traceback.format_exc(),
                   "status": "RED_PRESERVED_NO_AUTOMATIC_REPLAY", "request": pin(request_path),
                   "partial_audio": pin(target) if target.is_file() else None}
            failure = write(destination / (cue["id"] + ".failure.json"), row)
            preserve(run, failure, "failure." + cue["id"], "failure-material")
            failures.append(row)
        preserve(run, request_path, "request." + cue["id"], "provider-request")
    result = {"schema": "ck3-faith-power-measured-narration-v1", "machine_id": fresh["machine_id"],
              "observed_at_utc": now(), "evidence_source": "actual provider requests and MP3 ffprobe durations",
              "script": pin(args.script), "provider": asdict(provider.identity),
              "cues": completed, "failures": failures,
              "speech_total_seconds": sum(r["speech_duration_seconds"] for r in completed),
              "unvoiced_result_slots": script.get("live_result_slots", []),
              "human_listening_performed": False, "video_render_performed": False}
    measured_path = write(destination / "measured-narration.json", result)
    preserve(run, measured_path, "narration-measurement-v1", "audio-duration-audit")
    write(destination / "storage-close.json", admission(args, fresh["machine_id"], closed=True))
    return {"measured_narration": pin(measured_path), "failed": len(failures)}


def select_context(script, measured, selection):
    """Bind disjoint real source spans to exact, already measured narration."""
    if (selection.get("scope") != "context-only-first-opening"
            or selection.get("business_result_verified") is not False):
        raise ValueError("Explicit unadopted context-only selection required")
    by_id, audio = {r["id"]: r for r in script["cues"]}, {r["id"]: r for r in measured["cues"]}
    rows, cursor = [], 0.0
    for chosen in selection["segments"]:
        cue, spoken = by_id[chosen["cue_id"]], audio[chosen["cue_id"]]
        if cue.get("live_result_asserted") is not False:
            raise ValueError("Live-result text remains unvoiced until independent evidence")
        request = read(bound(spoken["request"]))
        if request["request"]["text"] != cue["zh"]:
            raise ValueError("Audio provider request differs from authored cue")
        bound(spoken["audio"])
        bound(chosen["raw"])
        audit = read(bound(chosen["raw_audit"]))
        if (audit.get("schema") != "ck3-faith-power-raw-media-read-audit-v1"
                or not chosen.get("source_machine_id")
                or audit.get("machine_id") != chosen["source_machine_id"]
                or audit["raw"]["bytes"] != chosen["raw"]["bytes"]
                or audit["raw"]["sha256"].lower() != chosen["raw"]["sha256"].lower()):
            raise ValueError("Raw audit must bind this source and the actual source machine")
        terminal = read(bound(audit["terminal"]))
        if (terminal["machine_id"] != chosen["source_machine_id"]
                or terminal["job"]["state"] != chosen["raw_terminal_status"]
                or terminal["job"]["job_active_processes"] != 0):
            raise ValueError("Actual original recorder terminal/Job-empty receipt differs")
        duration = cue_duration(spoken["speech_duration_seconds"])
        start = chosen["raw_start_seconds"]
        end = start + duration
        if (not math.isfinite(start) or start < 0
                or end > chosen["approved_raw_end_seconds"] + 1e-6
                or end > chosen["decoded_last_pts_seconds"] + 1 / 30 + 1e-6):
            raise ValueError("Selected span exceeds its approved, actually decoded source")
        if chosen["raw_terminal_status"] not in {"NORMAL_TREE_EMPTY", "ABORT_TREE_EMPTY"}:
            raise ValueError("Retain the exact original terminal status, including abort RED")
        rows.append({**cue, "speech_duration_seconds": spoken["speech_duration_seconds"],
                     "duration_seconds": duration, "audio_artifact_id": "audio." + cue["id"],
                     "source_machine_id": chosen["source_machine_id"],
                     "raw": chosen["raw"], "raw_audit": chosen["raw_audit"], "raw_terminal": audit["terminal"],
                     "raw_start_seconds": start, "raw_end_seconds_exclusive": end,
                     "raw_terminal_status": chosen["raw_terminal_status"],
                     "timeline_start_seconds": cursor, "timeline_end_seconds": cursor + duration})
        cursor += duration
    if not 30 <= cursor <= 60 or len({r["id"] for r in rows}) != len(rows):
        raise ValueError("Expected unique cues totaling 30–60 authored seconds")
    for raw_sha in {r["raw"]["sha256"].lower() for r in rows}:
        spans = sorted((r["raw_start_seconds"], r["raw_end_seconds_exclusive"])
                       for r in rows if r["raw"]["sha256"].lower() == raw_sha)
        if any(right[0] < left[1] for left, right in zip(spans, spans[1:])):
            raise ValueError("A source interval would be repeated")
    return rows


def run_context(args):
    runtime, fresh, destination = open_attempt(args)
    script, measured, selection = read(args.script), read(args.measured), read(args.selection)
    if selection["machine_id"] != fresh["machine_id"]:
        raise ValueError("Raw selection belongs to another machine")
    # Packaging can reorganize/merge the authoring document. Preserve the exact
    # old measured script as well; selected provider text must match cue by cue.
    measured_source_script = bound(measured["script"])
    rows = select_context(script, measured, selection)
    config_path = write(destination / "project-config.json", project(script, rows, sample=True))
    run = start_run(config_path, run_id=destination.name, run_directory=destination / "native-run")
    for path, identifier, role in (
        (args.script, "episode-script-v1", "authoring-script"),
        (args.measured, "speech-measurement-v1", "narration-evidence"),
        (measured_source_script, "measured-source-script-v1", "original-narration-script"),
        (args.selection, "raw-selection-v1", "context-source-selection"),
        (destination / "fresh-runtime.json", "runtime-v1", "runtime-dependencies"),
        (destination / "storage-admission.json", "storage-v1", "storage-admission"),
        (Path(__file__), "producer-source-v1", "producer-source"),
        (Path(__file__).with_name("context_composer.py"), "composer-source-v1", "producer-source"),
    ):
        preserve(run, path, identifier, role)
    font_file = bound(runtime["subtitle_font"]["file"])
    font_name = runtime["subtitle_font"]["family"]
    from PIL import ImageFont
    if ImageFont.truetype(str(font_file), size=49).getname()[0] != font_name:
        raise ValueError("Configured font family differs from the exact provided font")
    preserve(run, font_file, "subtitle-font-v1", "subtitle-font", "raw")
    spoken_by_id = {r["id"]: r for r in measured["cues"]}
    for row in rows:
        spoken = spoken_by_id[row["id"]]
        preserve(run, bound(spoken["audio"]), row["audio_artifact_id"], "frozen-narration", "raw", "audio/mpeg")
        preserve(run, bound(spoken["request"]), "request." + row["id"], "original-provider-request")
    # Original raw remains uncopied in its current protected evidence location;
    # its binding, audit and exact source argv are retained. No raw is rewritten.
    for index, audit in enumerate({r["raw_audit"]["sha256"]: r["raw_audit"] for r in rows}.values()):
        preserve(run, bound(audit), f"raw-audit.{index}", "capture-audit")
    for index, terminal in enumerate({r["raw_terminal"]["sha256"]: r["raw_terminal"] for r in rows}.values()):
        preserve(run, bound(terminal), f"raw-terminal.{index}", "original-recorder-terminal")
    ffmpeg, ffprobe = bound(runtime["ffmpeg"]), bound(runtime["ffprobe"])
    source_pts = {}
    for index, raw in enumerate({r["raw"]["sha256"]: r["raw"] for r in rows}.values()):
        result = command([ffprobe, "-v", "error", "-select_streams", "v:0", "-show_entries",
                          "frame=best_effort_timestamp_time", "-of", "json", bound(raw)],
                         destination, f"raw-{index}-decoded-frame-pts")
        pts = [float(r["best_effort_timestamp_time"]) for r in json.loads(result.stdout)["frames"]]
        if not pts or any(b <= a for a, b in zip(pts, pts[1:])):
            raise ValueError("Actual source frame PTS is empty or not strictly increasing")
        source_pts[raw["sha256"]] = pts
    for row in rows:
        pts = source_pts[row["raw"]["sha256"]]
        if row["raw_end_seconds_exclusive"] > pts[-1] + 1 / 30 + 1e-6:
            raise ValueError("Actual decoded source ends before the selected excerpt")
        row["selected_source_pts_seconds"] = [t for t in pts
            if row["raw_start_seconds"] <= t < row["raw_end_seconds_exclusive"]]
        row["source_is_vfr"] = any(abs(b - a - 1 / 30) > 0.0011 for a, b in zip(pts, pts[1:]))
        row["source_cadence"] = "actual source frame PTS; 30fps header alone does not establish cadence"
        if not row["selected_source_pts_seconds"]:
            raise ValueError("No actual decoded source frames in selected interval")
        row["source_pts_mapping_scope"] = "actual frames in selected raw clock interval; no per-frame pixel equivalence claim"
    visual = destination / "visual-context-input.mp4"
    argv = [ffmpeg, "-nostdin", "-n", "-hide_banner", "-loglevel", "error", "-threads", "2"]
    filters = []
    for index, row in enumerate(rows):
        argv += ["-ss", f"{row['raw_start_seconds']:.9f}", "-t", f"{row['duration_seconds']:.9f}", "-i", bound(row["raw"])]
        filters.append(f"[{index}:v]setpts=PTS-STARTPTS,scale=2560:1120:force_original_aspect_ratio=decrease:flags=lanczos,"
                       f"pad=2560:1440:(ow-iw)/2:0:color=0x211813,fps=30:round=near,"
                       f"trim=duration={row['duration_seconds']:.9f},setpts=PTS-STARTPTS[v{index}]")
    filters.append("".join(f"[v{i}]" for i in range(len(rows))) + f"concat=n={len(rows)}:v=1:a=0[out]")
    argv += ["-filter_complex", ";".join(filters), "-map", "[out]", "-an", "-c:v", "libx264",
             "-threads", "2", "-preset", "veryfast", "-crf", "21", "-pix_fmt", "yuv420p", visual]
    command(argv, destination, "prepare-context-excerpts")
    total = sum(r["duration_seconds"] for r in rows)
    prepared = json.loads(command([ffprobe, "-v", "error", "-show_format", "-of", "json", visual],
                                  destination, "prepared-duration").stdout)
    if abs(float(prepared["format"]["duration"]) - total) > 0.01:
        raise ValueError("Prepared real source does not cover the entire narration clock")
    preserve(run, visual, "context-visual-v1", "actual-context-excerpts", "raw", "video/mp4")
    inputs = {"schema": "ck3-faith-power-context-sample-inputs-v1", "scope": "context-only-first-opening",
              "machine_id": fresh["machine_id"], "observed_at_utc": now(),
              "evidence_source": "exact real raw selections and measured MP3 inputs",
              "video_artifact_id": "context-visual-v1", "font_artifact_id": "subtitle-font-v1",
              "font_name": font_name, "ffmpeg": str(ffmpeg), "ffprobe": str(ffprobe), "cues": rows,
              "business_result_verified": False, "human_1x_review_performed": False,
              "no_gameplay_credit": True,
              "conversion": "30fps CFR holds/duplicates selected VFR frames; no interpolation, loop or slowdown"}
    inputs_path = write(destination / "measured-inputs.json", inputs)
    preserve(run, inputs_path, "episode01-context-inputs-v1", "production-inputs")
    planned = handle_plan(run, workdir=destination / "build", registry=registry(), composer=compose)
    write(destination / "plan-outcome.json", asdict(planned))
    if not planned.succeeded:
        raise RuntimeError(str(planned.failure))
    result = handle_build(run, workdir=destination / "build", registry=registry(), composer=compose)
    write(destination / "build-outcome.json", asdict(result))
    if not result.succeeded:
        raise RuntimeError(str(result.failure))
    final = destination / "build/episode01-context-sample.mp4"
    command([ffmpeg, "-nostdin", "-v", "error", "-xerror", "-err_detect", "explode", "-threads", "2",
             "-i", final, "-map", "0:v:0", "-map", "0:a:0", "-f", "null", "-"], destination, "full-av-decode")
    probed = json.loads(command([ffprobe, "-v", "error", "-show_streams", "-show_format", "-of", "json", final],
                               destination, "final-probe").stdout)
    frame_doc = json.loads(command([ffprobe, "-v", "error", "-select_streams", "v:0", "-show_entries",
                                   "frame=best_effort_timestamp_time", "-of", "json", final],
                                  destination, "final-frame-pts").stdout)
    pts = [float(r["best_effort_timestamp_time"]) for r in frame_doc["frames"]]
    if len(pts) != round(total * 30) or any(abs(b - a - 1 / 30) > 0.00001 for a, b in zip(pts, pts[1:])):
        raise ValueError("Actual final frame cadence/count differs from the authored CFR clock")
    video = next(s for s in probed["streams"] if s["codec_type"] == "video")
    audio = next(s for s in probed["streams"] if s["codec_type"] == "audio")
    if (video["width"], video["height"], audio["sample_rate"], audio["channels"]) != (2560, 1440, "48000", 2):
        raise ValueError("Actual encoded video/audio geometry differs")
    mapping = []
    for row in rows:
        first, end = round(row["timeline_start_seconds"] * 30), round(row["timeline_end_seconds"] * 30)
        mapping.append({**row, "actual_final_first_pts": pts[first], "actual_final_last_pts": pts[end - 1],
                        "actual_final_end_pts_exclusive": pts[end - 1] + 1 / 30,
                        "actual_final_frame_indices_exclusive": [first, end], "business_credit": False,
                        "clean_span_credit": False})
    audit = {"schema": "ck3-faith-power-context-sample-audit-v1", "machine_id": fresh["machine_id"],
             "observed_at_utc": now(), "evidence_source": "actual full decode, stream probe and every final frame PTS",
             "final": pin(final), "authored_seconds": total,
             "actual_container_seconds": float(probed["format"]["duration"]), "segments": mapping,
             "human_listening_performed": False, "human_full_1x_review_performed": False,
             "native_business_verified": False, "clean_span_certified": False, "signoff": "pending"}
    audit_path = write(destination / "raw-to-final-map.json", audit)
    preserve(run, audit_path, "raw-final-map-v1", "provenance-map")
    write(destination / "storage-close.json", admission(args, fresh["machine_id"], closed=True))
    return {"final": pin(final), "audit": pin(audit_path)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="operation", required=True)
    author = sub.add_parser("project", help="write a planned, unbound ProjectConfig; no production")
    author.add_argument("--script", type=Path, required=True)
    author.add_argument("--output", type=Path, required=True)
    for name in ("synthesize", "context-sample"):
        child = sub.add_parser(name)
        for option in ("repo", "script", "runtime", "reservation", "package-root", "output"):
            child.add_argument("--" + option, type=Path, required=True)
        child.add_argument("--reservation-task", required=True)
        child.add_argument("--peak-bytes", type=int, required=True)
        if name == "synthesize":
            child.add_argument("--recipe", type=Path, required=True)
        else:
            child.add_argument("--measured", type=Path, required=True)
            child.add_argument("--selection", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.operation == "project":
            result = {"project_config": pin(write(args.output, project(read(args.script))))}
        else:
            result = run_synthesize(args) if args.operation == "synthesize" else run_context(args)
        print(json.dumps(result, ensure_ascii=False))
        return 2 if result.get("failed") else 0
    except Exception as error:
        output = Path(args.output)
        if getattr(args, "_created_output", False) and output.is_dir() and not (output / "failure.json").exists():
            write(output / "failure.json", {"observed_at_utc": now(),
                  "machine_id": read(args.runtime).get("machine_id") if hasattr(args, "runtime") else "unknown",
                  "evidence_source": "actual producer exception; original inputs/partial output retained",
                  "error": repr(error), "traceback": traceback.format_exc()})
        raise
