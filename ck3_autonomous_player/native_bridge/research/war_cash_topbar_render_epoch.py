"""Decode supplied GUI render-clock bytes for a topbar cache diagnostic.

The stock getter records its render tick *before* rebuilding the expense
breakdown. Matching this clock therefore cannot prove a completed refresh,
a native gameplay revision, a military rate, or a war cash amount.
"""

from __future__ import annotations

import struct


RENDER_CONTEXT_SLOT_RVA = 0x576CC68
EXPENSE_REFRESH_INTERVAL_RVA = 0x570D8D0
RENDER_CONTEXT_READ_SIZE = 0x188
TOPBAR_READ_SIZE = 0xF90


def inspect_supplied_topbar_render_epoch(
    *, image_base: int, topbar_bytes: bytes,
    render_context_slot_address: int, render_context_slot_bytes: bytes,
    render_context_address: int, render_context_bytes: bytes,
    refresh_interval_address: int, refresh_interval_bytes: bytes,
) -> dict[str, object]:
    """Inspect exact supplied bytes; never read or call the target process."""
    if (type(image_base) is not int or image_base < 0x10000
            or image_base % 0x10000
            or type(topbar_bytes) is not bytes
            or len(topbar_bytes) != TOPBAR_READ_SIZE
            or type(render_context_slot_address) is not int
            or render_context_slot_address != image_base + RENDER_CONTEXT_SLOT_RVA
            or type(render_context_slot_bytes) is not bytes
            or len(render_context_slot_bytes) != 8
            or type(render_context_address) is not int
            or render_context_address < 0x10000
            or render_context_address % 8
            or type(render_context_bytes) is not bytes
            or len(render_context_bytes) != RENDER_CONTEXT_READ_SIZE
            or type(refresh_interval_address) is not int
            or refresh_interval_address
            != image_base + EXPENSE_REFRESH_INTERVAL_RVA
            or type(refresh_interval_bytes) is not bytes
            or len(refresh_interval_bytes) != 4):
        raise ValueError("exact supplied topbar render-clock bytes required")
    if struct.unpack("<Q", render_context_slot_bytes)[0] != render_context_address:
        raise ValueError("render-context slot pointer differs from supplied object")
    current_tick = struct.unpack_from("<Q", render_context_bytes, 0x180)[0]
    last_update_tick = struct.unpack_from("<Q", topbar_bytes, 0xF88)[0]
    interval = struct.unpack("<i", refresh_interval_bytes)[0]
    if (not 0 < interval <= 100_000 or not 0 < last_update_tick
            or not last_update_tick <= current_tick <= 2**63 - 1):
        raise ValueError("render tick or refresh interval is invalid")
    lag = current_tick - last_update_tick
    return {
        "schema": "xar.ck3.war-cash-topbar-render-epoch-diagnostic.v1",
        "status": "structurally_matching_gui_render_epoch_only",
        "render_context_address": hex(render_context_address),
        "current_render_tick_candidate": current_tick,
        "topbar_last_update_tick_candidate": last_update_tick,
        "stock_refresh_interval_render_ticks_candidate": interval,
        "render_tick_lag": lag,
        "getter_refresh_due_if_called_candidate": lag >= interval,
        "getter_called_in_this_sample": False,
        "cache_refresh_completed_proven": False,
        "same_native_revision_proven": False,
        "formal_cash_eligible": False,
    }
