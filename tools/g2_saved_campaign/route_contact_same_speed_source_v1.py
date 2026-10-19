"""Offline source qualification only; no Game query, action, ledger or credit."""
from hashlib import sha256
import json
from pathlib import Path

from route_contact_exact_day_outcome import SOURCE15_SAME_SPEED_PINS


def build_source15_same_speed_proof(*, freeze_path, driver_mode_path,
                                    start_binding, requested_speed):
    """Qualify the actual closed C18 source chain, then bind one original frame.

    The operator must independently retain this SDK's actual owner/admission.
    These files prove source control flow, not a new fresh-speed getter receipt.
    A later SDK/freeze requires separate qualification; no truthy override exists.
    """
    def require(ok, reason):
        if not ok:
            raise ValueError("same-speed source qualification: " + reason)

    freeze_raw = Path(freeze_path).read_bytes()
    mode_raw = Path(driver_mode_path).read_bytes()
    require(sha256(freeze_raw).hexdigest() == SOURCE15_SAME_SPEED_PINS["freeze_sha256"],
            "different source freeze")
    require(sha256(mode_raw).hexdigest() == SOURCE15_SAME_SPEED_PINS["driver_mode_sha256"],
            "different actual driver-mode receipt")
    freeze, mode = json.loads(freeze_raw), json.loads(mode_raw)
    root = Path(freeze["source_root"]).resolve()
    require(Path(mode["source_file"]).resolve() == root / "xar_autoplayer/bridge/native_driver.py",
            "driver-mode source path differs")
    rows = {row["relative"]: row for row in freeze["files"]}
    for relative, size, key in (
        ("xar_autoplayer/bridge/native_driver.py", 1637048, "driver_sha256"),
        ("xar_autoplayer/bridge/exact_day_speed_configuration_v1.py", 3412, "helper_sha256"),
    ):
        row = rows.get(relative)
        require(isinstance(row, dict) and row.get("bytes") == size
                and row.get("sha256") == SOURCE15_SAME_SPEED_PINS[key], "freeze leaf differs")
        raw = (root / relative).read_bytes()
        require(len(raw) == size and sha256(raw).hexdigest() == SOURCE15_SAME_SPEED_PINS[key],
                "actual source leaf differs")
    keys = ("snapshot_id", "revision", "native_revision", "date_raw", "actor_character_id",
            "episode_run_id", "connection_generation", "bridge_pid")
    require(isinstance(start_binding, dict) and all(key in start_binding for key in keys),
            "incomplete original frame")
    frame = {key: start_binding[key] for key in keys}
    require(all(type(frame[key]) is int and frame[key] > 0 for key in keys
                if key not in {"snapshot_id", "episode_run_id"})
            and isinstance(frame["episode_run_id"], str) and bool(frame["episode_run_id"])
            and frame["snapshot_id"] == f"native:{frame['native_revision']}"
            and type(requested_speed) is int and 1 <= requested_speed <= 5,
            "unknown frame or speed")
    return {"schema": "g2.route-contact-same-speed-source/v1",
            "basis": "pinned_source_unique_same_speed_branch",
            "source_pins": dict(SOURCE15_SAME_SPEED_PINS),
            "start_binding": frame, "requested_speed": requested_speed}
