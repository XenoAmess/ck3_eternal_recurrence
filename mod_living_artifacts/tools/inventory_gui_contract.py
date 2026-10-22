"""Source-bound GUI-only inventory opening after a proven pre-intent refusal."""
from __future__ import annotations

from dataclasses import dataclass
import math
from pathlib import Path
import struct
import sys
from typing import Literal, TypedDict

from acceptance_contract import Frame, Object, Pin, array, decimal_id, field, integer, mapping, pin, read, require, text
from checkpoint_callback import checked_pin

SHARED = Path(__file__).resolve().parents[2] / "tools"
if str(SHARED) not in sys.path:
    sys.path.append(str(SHARED))
from desktop_coordinate_map import map_point

# Exact public MCP error row observed in R5; substring matches never qualify.
REFUSAL = ("RuntimeError: MCP tool ck3_open_player_inventory_window_v1 returned an error: "
           "Error executing tool ck3_open_player_inventory_window_v1: "
           "Inventory opening requires the existing actual managed-source inventory")
GUARD_RELATIVE = "ck3_autonomous_player/src/xar_autoplayer/bridge/player_inventory_window_private_transport_v1.py"
GUARD_SHA = "8c316ca5efb687ffdfc411854f0af8c1d822039419d894e40b57bdb8081fd6a3"


class InventoryOpenRequest(TypedDict):
    schema: Literal["living-artifacts-inventory-gui-open-request-v1"]
    run_id: str
    machine_id: str
    pid: int
    connection_generation: str
    actor_character_id: int
    date_raw: int
    target_artifact_id: str
    original_native_refusal: Pin
    refusal_source: Pin
    original_open_intent_not_admitted: Literal[True]
    action: Literal["open-inventory-only"]
    required_route: Literal["desktop_coordinate_map"]
    business_pass: Literal[False]


class InventoryOpenResponse(TypedDict):
    schema: Literal["living-artifacts-inventory-gui-open-result-v1"]
    schema_version: Literal[1]
    run_id: str
    machine_id: str
    reviewer: str
    pid: int
    connection_generation: str
    actor_character_id: int
    date_raw: int
    target_artifact_id: str
    status: Literal["completed", "blocked", "outcome_unknown"]
    submitted: bool
    reason: str | None
    native_refusal: Pin
    mapping_receipt: Pin | None
    source_screenshot: Pin | None
    after_screenshot: Pin | None
    business_pass: Literal[False]


def pre_intent_source(frozen: object) -> Pin:
    root = Path(text(field(frozen, "source_root"), "original shared source root")).resolve()
    source = pin(root / GUARD_RELATIVE)
    require(source["sha256"] == GUARD_SHA, "Native inventory refusal source changed; review before GUI fallback")
    return source


def png_size(path: Path) -> tuple[int, int]:
    with path.open("rb") as stream:
        prefix = stream.read(24)
    require(len(prefix) == 24 and prefix[:8] == b"\x89PNG\r\n\x1a\n" and prefix[12:16] == b"IHDR", "Original PNG screenshot required")
    width, height = struct.unpack(">II", prefix[16:24])
    return integer(width, "PNG width", 1, 65536), integer(height, "PNG height", 1, 65536)


def _size(value: object) -> tuple[int, int]:
    items = array(value, "actual image/desktop dimensions")
    require(len(items) == 2, "Two independent image dimensions required")
    return integer(items[0], "width", 1), integer(items[1], "height", 1)


def _coordinate(value: object) -> float:
    if type(value) not in (int, float) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        raise ValueError("Finite coordinate required; bool rejected")
    return float(value)


@dataclass(frozen=True)
class GuiOpening:
    status: Literal["completed", "blocked", "outcome_unknown"]
    submitted: bool
    reason: str | None
    evidence: tuple[Pin, ...]


def parse_opening(value: object, *, frame: Frame, run_id: str, machine_id: str, reviewer: str,
                  target: str, refusal: Pin) -> GuiOpening:
    row = mapping(value, "Root GUI inventory result")
    require(set(row) == set(InventoryOpenResponse.__required_keys__) and row["schema"] == "living-artifacts-inventory-gui-open-result-v1" and
            integer(row["schema_version"], "GUI opening schema", 1, 1) == 1 and row["business_pass"] is False,
            "Closed GUI inventory result required")
    require(row["run_id"] == run_id and row["machine_id"] == machine_id and row["reviewer"] == reviewer and
            integer(row["pid"], "GUI PID", 1) == frame.pid and decimal_id(row["connection_generation"], "GUI generation") == frame.generation_decimal and
            integer(row["actor_character_id"], "GUI actor", 1) == frame.player_id and integer(row["date_raw"], "GUI date") == frame.date_raw and
            decimal_id(row["target_artifact_id"], "GUI target", allow_zero=True) == target and checked_pin(row["native_refusal"], "original refusal") == refusal,
            "GUI inventory callback crossed the original scene/target/refusal")
    require(type(row["submitted"]) is bool, "Actual GUI submission bool required")
    submitted = row["submitted"] is True
    if row["status"] != "completed":
        require(row["status"] in ("blocked", "outcome_unknown") and ((row["status"] == "blocked" and not submitted) or
                (row["status"] == "outcome_unknown" and submitted)), "Unknown GUI action must stay unknown; blocked means no action")
        require(all(row[key] is None for key in ("mapping_receipt", "source_screenshot", "after_screenshot")), "Incomplete GUI result must not claim completed mapping evidence")
        return GuiOpening("blocked" if row["status"] == "blocked" else "outcome_unknown", submitted, text(row["reason"], "actual GUI blocker"), (refusal,))
    require(submitted and row["reason"] is None, "Completed GUI opening requires actual submission and no blocker")
    mapped = checked_pin(row["mapping_receipt"], "actual coordinate-map receipt")
    source = checked_pin(row["source_screenshot"], "original desktop screenshot")
    after = checked_pin(row["after_screenshot"], "post-click screenshot")
    receipt = read(Path(mapped["path"]))
    require(receipt.get("action") == "click" and receipt.get("status") == "guarded-click-readback-matched" and
            receipt.get("click_completed") is True and receipt.get("failures") == [], "Actual guarded coordinate-map click required")
    size = _size(field(receipt, "screen_size_before"))
    require(all(_size(field(receipt, key)) == size for key in ("screen_size_after", "live_screen_size", "source_image_size", "receipt_image_size")) and
            png_size(Path(source["path"])) == size == png_size(Path(after["path"])), "Source/current desktop dimensions differ")
    require(Path(text(field(receipt, "source_image"), "mapped source")).resolve() == Path(source["path"]) and
            Path(text(field(receipt, "receipt_path"), "mapped receipt screenshot")).resolve() == Path(after["path"]), "Coordinate receipt references different screenshots")
    hwnd = integer(field(receipt, "expected_foreground_hwnd"), "reviewed HWND", 1)
    for key in ("focus_before", "focus_after"):
        focus = field(receipt, key)
        require(integer(field(focus, "foreground_pid"), "foreground PID", 1) == frame.pid and
                integer(field(focus, "foreground_hwnd"), "foreground HWND", 1) == hwnd, "Mapped click belongs to another window/process")
    rectangle = array(field(receipt, "preview_bounds"), "explicit image content rectangle")
    point = array(field(receipt, "observed_point"), "observed image point")
    screen = array(field(receipt, "screen_point"), "actual screen point")
    require(len(rectangle) == 4 and len(point) == len(screen) == 2, "Explicit independent-axis geometry required")
    actual = (integer(screen[0], "screen X", 0, size[0] - 1), integer(screen[1], "screen Y", 0, size[1] - 1))
    require(map_point(preview_bounds=(_coordinate(rectangle[0]), _coordinate(rectangle[1]), integer(rectangle[2], "content width", 1), integer(rectangle[3], "content height", 1)),
            observed_point=(_coordinate(point[0]), _coordinate(point[1])), target_size=size) == actual, "Shared coordinate conversion does not reproduce actual point")
    return GuiOpening("completed", True, None, (refusal, mapped, source, after))
