"""Validate a new recorded segment on one retained Game; no runtime operations."""
from pathlib import Path
import hashlib


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify_segment(n, r, launch, root, first_path, read, aware, now):
    root, first_path = Path(root).resolve(), Path(first_path).resolve()
    if not root.is_relative_to(n / "recordings") or not first_path.is_relative_to(n):
        raise ValueError("actual dedicated segment/review paths escaped admitted roots")
    job, started, first = read(root / "job.json"), read(root / "started.json"), read(first_path, 16384)
    storage = job.get("storage")
    if (job.get("continuous") is not True or any(job.get(key) is not None for key in (
            "deadline_utc", "duration_seconds", "max_output_bytes"))
            or job.get("pid") != launch.get("pid")
            or job.get("launch", {}).get("creation_date") != launch.get("creation_date")
            or job.get("launch", {}).get("pipe") != launch.get("pipe")
            or type(job.get("game_creation_filetime")) is not int or job["game_creation_filetime"] <= 0
            or Path(job["receipt_root"]).resolve() != root
            or job.get("capture_mode") != "game_decision"
            or started.get("state") != "recording" or started.get("game_pid") != launch.get("pid")
            or started.get("game_creation_filetime") != job["game_creation_filetime"]
            or started.get("capture_mode") != "game_decision" or started.get("decision_source") is not True
            or first.get("status") != "GREEN"
            or first.get("reviewer") not in {"/root", "automatic_continuity"}
            or first.get("game_pid") != launch.get("pid")
            or first.get("game_creation_date") != launch.get("creation_date")
            or first.get("recorder_session_id") != job.get("session_id")
            or Path(first["recording_job_root"]).resolve() != root
            or not aware(started["at_utc"]) <= aware(first["at_utc"]) <= now()
            or not isinstance(storage, dict) or type(storage.get("disk_reserve_bytes")) is not int
            or storage["disk_reserve_bytes"] <= 0):
        raise ValueError("exact continuous same-Game recording/source/pixel/storage binding differs")
    if first["reviewer"] == "/root":
        if (first.get("before_selection_game_pixels_reviewed") is not True
                or first.get("before_selection_decision_pixels_reviewed") is not True):
            raise ValueError("Root pixel admission is not an actual reviewed frame")
    else:
        from automatic_continuity import verify_automatic_continuity_receipt
        overlay_receipt = Path(first["overlay_started_receipt"]).resolve()
        if not overlay_receipt.is_relative_to(n):
            raise ValueError("automatic admission overlay receipt escaped session")
        overlay_started = read(overlay_receipt, 16384)
        frame = {
            "at_utc": first["at_utc"], "mutable_latest_frame": False,
            "game": {key: first["game_png"][key]
                     for key in ("path", "bytes", "sha256")},
            "scene": {key: first["scene_png"][key]
                      for key in ("path", "bytes", "sha256")},
        }
        verify_automatic_continuity_receipt(
            receipt=first, job=job, started=started,
            overlay_started=overlay_started,
            overlay_started_path=overlay_receipt,
            frame=frame, session_root=n, now_utc=now())
    admission_path = Path(storage["admission_path"]).resolve()
    if admission_path != (r / "STORAGE-ADMISSION.json").resolve() or digest(admission_path) != storage.get("admission_sha256"):
        raise ValueError("actual storage admission receipt bytes differ")
    admission = read(admission_path)
    if admission.get("status") != "ADMITTED":
        raise ValueError("actual storage admission is not admitted")
    output = Path(job["recording_root"]).resolve()
    approved = storage.get("approved_output_roots")
    if (not isinstance(approved, list) or not approved
            or not any(output.is_relative_to(Path(p).resolve()) for p in approved)
            or not all(any(Path(p).resolve().is_relative_to(Path(a).resolve())
                           for a in admission["approved_output_roots"]) for p in approved)):
        raise ValueError("recording output is outside the actual storage admission")
    if any((root / name).exists() for name in ("failed.json", "completed.json", "closed-file-probe.json")):
        raise ValueError("replacement recording is already terminal")
    return job, started, first
