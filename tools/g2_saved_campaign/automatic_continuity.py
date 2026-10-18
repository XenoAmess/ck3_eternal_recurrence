"""Read-only pixel admission for a newly recorded Game + decision-overlay scene.

The caller freezes recorder's mutable latest PNG pair into immutable files first.
This module never captures the screen or controls Game/OBS.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
from io import BytesIO
import json
from pathlib import Path

from PIL import Image, ImageChops, ImageStat


def _time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("admission time lacks timezone")
    return parsed.astimezone(timezone.utc)


def _asset(row: dict, root: Path) -> tuple[Image.Image, str]:
    path = Path(row["path"]).resolve()
    if not path.is_relative_to(root):
        raise ValueError("admission PNG escaped new recorder receipt root")
    if path.name.startswith("recording-latest-"):
        raise ValueError("mutable latest PNG cannot be the retained admission evidence")
    data = path.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if len(data) != row.get("bytes") or digest != row.get("sha256"):
        raise ValueError("admission PNG bytes changed after freeze")
    with Image.open(BytesIO(data)) as image:
        if image.format != "PNG":
            raise ValueError("admission frame is not PNG")
        rgb = image.convert("RGB")
        rgb.load()
    return rgb, digest


def _nonblack(image: Image.Image) -> dict:
    if image.width < 640 or image.height < 360:
        raise ValueError("admission frame is too small")
    small = image.resize((128, 72))
    stats = ImageStat.Stat(small)
    extrema = small.getextrema()
    mean = sum(stats.mean) / 3
    span = max(hi for _, hi in extrema) - min(lo for lo, _ in extrema)
    if mean < 10 or span < 24:
        raise ValueError("admission frame is black or nearly flat")
    return {"width": image.width, "height": image.height,
            "mean_rgb": round(mean, 2), "color_span": span}


def automatic_continuity_admission(
    *, job: dict, started: dict, overlay_started: dict,
    overlay_started_path: Path, frame: dict,
    session_root: Path, now_utc: datetime, max_age_seconds: int = 120,
) -> dict:
    """Validate actual receipt identity plus fresh nonblack PNG and overlay pixels."""
    session_root = Path(session_root).resolve()
    root = Path(job["receipt_root"]).resolve()
    if not root.is_relative_to(session_root / "recordings"):
        raise ValueError("recorder root escaped session")
    overlay_started_path = Path(overlay_started_path).resolve()
    if not overlay_started_path.is_relative_to(session_root):
        raise ValueError("new overlay STARTED receipt escaped session")
    overlay_bytes = overlay_started_path.read_bytes()
    if json.loads(overlay_bytes.decode("utf-8-sig")) != overlay_started:
        raise ValueError("explicit new overlay STARTED receipt bytes differ")
    overlay_sha = hashlib.sha256(overlay_bytes).hexdigest()
    overlay_path = Path(overlay_started["decision_text_file"]).resolve()
    if not overlay_path.is_relative_to(session_root) or not overlay_path.is_file():
        raise ValueError("exact new overlay decision text file is absent")
    if overlay_path.stat().st_size == 0:
        raise ValueError("new overlay decision text file is empty")
    game_pid = job.get("pid")
    game_stamp = job.get("game_creation_filetime")
    overlay = job.get("overlay")
    decision = started.get("decision_settings")
    if (type(game_pid) is not int or game_pid <= 0
            or type(game_stamp) is not int or game_stamp <= 0
            or job.get("capture_mode") != "game_decision"
            or job.get("continuous") is not True
            or any(job.get(key) is not None for key in
                   ("duration_seconds", "max_output_bytes", "deadline_utc"))
            or started.get("state") != "recording"
            or started.get("game_pid") != game_pid
            or started.get("game_creation_filetime") != game_stamp
            or started.get("capture_mode") != "game_decision"
            or started.get("decision_source") is not True
            or not isinstance(decision, dict)
            or decision.get("read_from_file") is not True
            or Path(decision.get("file", "")).resolve() != overlay_path
            or job.get("decision_text_file") != str(overlay_path)
            or not isinstance(overlay, dict)
            or overlay.get("game_pid") != game_pid
            or overlay.get("game_creation_filetime") != game_stamp
            or overlay.get("overlay_pid") != overlay_started.get("overlay_pid")
            or overlay.get("overlay_creation_filetime")
               != overlay_started.get("overlay_creation_filetime")
            or overlay.get("overlay_hwnd") != overlay_started.get("overlay_hwnd")
            or Path(overlay.get("decision_text_file", "")).resolve() != overlay_path
            or overlay.get("managed_desktop_id")
               != overlay_started.get("managed_desktop_id")
            or overlay.get("game_virtual_desktop", {}).get("desktop_id")
               != overlay_started.get("managed_desktop_id")
            or overlay.get("overlay_virtual_desktop", {}).get("desktop_id")
               != overlay_started.get("managed_desktop_id")):
        raise ValueError("recorder is not bound to actual new Game/overlay source")
    frame_time = _time(frame["at_utc"])
    if (frame.get("mutable_latest_frame") is not False
            or _time(overlay_started["at_utc"]) > _time(started["at_utc"])
            or not _time(started["at_utc"]) <= frame_time <= now_utc
            or (now_utc - frame_time).total_seconds() > max_age_seconds):
        raise ValueError("frozen frame is stale or predates new scene")
    game, game_sha = _asset(frame["game"], root)
    scene, scene_sha = _asset(frame["scene"], root)
    game_stats, scene_stats = _nonblack(game), _nonblack(scene)
    if game.size != scene.size:
        raise ValueError("Game and scene PNG dimensions differ")
    diff = ImageChops.difference(
        game.resize((128, 72)), scene.resize((128, 72)))
    changed = sum(
        1 for pixel in diff.getdata() if max(pixel) >= 12
    )
    fraction = changed / (128 * 72)
    if fraction < 0.005:
        raise ValueError("decision scene has no visible overlay difference from Game")
    return {
        "schema": "xar.ck3.automatic-recording-continuity/v1",
        "status": "GREEN",
        "reviewer": "automatic_continuity",
        "admission_method": "automatic_continuity",
        "at_utc": frame["at_utc"],
        "game_pid": game_pid,
        "game_creation_date": job["launch"]["creation_date"],
        "game_creation_filetime": game_stamp,
        "recorder_session_id": job["session_id"],
        "recording_job_root": str(root),
        "overlay_pid": overlay_started["overlay_pid"],
        "overlay_creation_filetime": overlay_started["overlay_creation_filetime"],
        "overlay_started_receipt": str(overlay_started_path),
        "overlay_started_receipt_sha256": overlay_sha,
        "decision_text_file": str(overlay_path),
        "game_png": {**frame["game"], "sha256": game_sha, **game_stats},
        "scene_png": {**frame["scene"], "sha256": scene_sha, **scene_stats},
        "scene_overlay_diff_fraction": round(fraction, 6),
        "human_pixel_review_claimed": False,
    }


def verify_automatic_continuity_receipt(
    *, receipt: dict, job: dict, started: dict, overlay_started: dict,
    overlay_started_path: Path,
    frame: dict, session_root: Path, now_utc: datetime,
) -> dict:
    expected = automatic_continuity_admission(
        job=job, started=started, overlay_started=overlay_started,
        overlay_started_path=overlay_started_path,
        frame=frame, session_root=session_root, now_utc=now_utc)
    if receipt != expected:
        raise ValueError("automatic continuity receipt differs from actual PNG/source proof")
    return expected


def automatic_text_continuity_admission(*, job, started, frame, session_root,
                                      now_utc, max_age_seconds=120):
    """New independent publisher identity; no synthetic legacy overlay receipt."""
    try:
        from . import decision_text_publisher as publisher
    except ImportError:
        import decision_text_publisher as publisher
    session_root = Path(session_root).resolve()
    root = Path(job['receipt_root']).resolve()
    if not root.is_relative_to(session_root / 'recordings'):
        raise ValueError('Text continuity recording escaped its session')
    reference = job['decision_text_publisher_receipt']
    bound = publisher.read_text_binding(reference, game={
        'pid': job['pid'], 'creation_filetime': job['game_creation_filetime'],
        'hwnd': job['hwnd'], 'desktop_id': job['desktop_id']})
    settings = started.get('decision_settings') or {}
    if (job.get('capture_mode') != 'game_decision_text' or job.get('overlay') is not None
            or job.get('continuous') is not True or any(job.get(k) is not None for k in ('duration_seconds', 'max_output_bytes', 'deadline_utc'))
            or job.get('decision_text_publisher') != bound or started.get('decision_text_publisher') != bound
            or started.get('state') != 'recording' or started.get('capture_mode') != 'game_decision_text'
            or started.get('game_pid') != job['pid'] or started.get('game_creation_filetime') != job['game_creation_filetime']
            or started.get('decision_source') is not True or settings.get('read_from_file') is not True
            or settings.get('file') != bound['decision_text_file'] or job.get('decision_text_file') != bound['decision_text_file']):
        raise ValueError('Actual new Game/text source identity differs')
    at = _time(frame['at_utc'])
    if (frame.get('mutable_latest_frame') is not False or not _time(bound['at_utc']) <= _time(started['at_utc']) <= at <= now_utc
            or (now_utc-at).total_seconds() > max_age_seconds):
        raise ValueError('Frozen new-text continuity frame is stale')
    game, gs = _asset(frame['game'], root)
    scene, ss = _asset(frame['scene'], root)
    game_stats, scene_stats = _nonblack(game), _nonblack(scene)
    if game.size != scene.size: raise ValueError('Actual Game/scene sizes differ')
    diff = ImageChops.difference(game.resize((128,72)), scene.resize((128,72)))
    fraction = sum(1 for pixel in diff.getdata() if max(pixel) >= 12) / (128*72)
    if fraction < .005: raise ValueError('Actual new-text scene has no visible difference')
    return {'schema': 'xar.ck3.automatic-text-recording-continuity/v1', 'status': 'GREEN',
        'reviewer': 'automatic_text_continuity', 'admission_method': 'automatic_text_continuity',
        'machine_id': bound['machine_id'], 'at_utc': frame['at_utc'],
        'game_pid': job['pid'], 'game_creation_filetime': job['game_creation_filetime'],
        'game_creation_date': job['launch']['creation_date'], 'recorder_session_id': job['session_id'],
        'recording_job_root': str(root), 'publisher_started': reference,
        'frame': frame, 'game_png': {**frame['game'], **game_stats, 'sha256':gs},
        'scene_png': {**frame['scene'], **scene_stats, 'sha256':ss},
        'scene_text_diff_fraction': round(fraction,6), 'human_pixel_review_claimed':False,
        'exact_text_draw_ACK_claimed':False}


def verify_automatic_text_continuity_receipt(*, receipt, **inputs):
    expected = automatic_text_continuity_admission(**inputs)
    if receipt != expected: raise ValueError('New text continuity receipt differs from actual proof')
    return expected
