"""Check externally supplied CHudTopBar owner-path bytes without process I/O.

Only an exact-build static locator is represented. The caller must separately
prove the live module identity, unique current owner, cache freshness and a
paused native before/after frame. This decoder never creates a cash receipt.
"""

from __future__ import annotations

import hashlib
import struct


GLOBAL_OWNER_SLOT_RVA = 0x570F7B8
IDLER_PRIMARY_VTABLE_RVA = 0x40B1D30
HANDLER_PRIMARY_VTABLE_RVA = 0x40AF630
HANDLER_SECONDARY_VTABLE_RVA = 0x40AF6A8
TOPBAR_PRIMARY_VTABLE_RVA = 0x40E6F68
TOPBAR_SECONDARY_VTABLE_RVA = 0x40E7038
TOPBAR_READ_SIZE = 0xF90


def _u64(data: bytes, offset: int) -> int:
    return struct.unpack_from("<Q", data, offset)[0]


def _address(value: object, label: str) -> int:
    if (type(value) is not int or value < 0x10000
            or value >= 0x0000800000000000 or value % 8):
        raise ValueError(f"{label} is not an aligned user-mode address")
    return value


def inspect_supplied_topbar_owner_path(
    *, image_base: int, global_slot_address: int,
    global_slot_bytes: bytes,
    global_owner_address: int, global_owner_bytes: bytes,
    idler_address: int, idler_bytes: bytes,
    handler_address: int, handler_bytes: bytes,
    topbar_address: int, topbar_bytes: bytes,
) -> dict[str, object]:
    """Require G -> I -> H -> T and the verified reverse owner pointers."""
    base = _address(image_base, "module image base")
    if base % 0x10000:
        raise ValueError("module image base is not allocation aligned")
    slot = _address(global_slot_address, "global slot")
    if slot != base + GLOBAL_OWNER_SLOT_RVA:
        raise ValueError("global slot address is not at the exact-build RVA")
    for label, data, size in (
        ("global slot", global_slot_bytes, 8),
        ("global owner", global_owner_bytes, 0x18),
        ("idler", idler_bytes, 0x90),
        ("handler", handler_bytes, 0x478),
        ("topbar", topbar_bytes, TOPBAR_READ_SIZE),
    ):
        if type(data) is not bytes or len(data) != size:
            raise ValueError(f"{label} requires exactly {size} supplied bytes")
    owner = _address(global_owner_address, "global owner")
    idler = _address(idler_address, "ingame idler")
    handler = _address(handler_address, "ingame handler")
    topbar = _address(topbar_address, "topbar")
    regions = sorted((
        (slot, slot + 8), (owner, owner + 0x18),
        (idler, idler + 0x90), (handler, handler + 0x478),
        (topbar, topbar + TOPBAR_READ_SIZE),
    ))
    if any(left_end > right_start for (_, left_end), (right_start, _)
           in zip(regions, regions[1:])):
        raise ValueError("supplied GUI owner-path byte regions overlap")
    if _u64(global_slot_bytes, 0) != owner:
        raise ValueError("global slot does not point to the supplied owner")
    if _u64(global_owner_bytes, 0x10) != idler:
        raise ValueError("global owner does not point to the supplied idler")
    if _u64(idler_bytes, 0) != base + IDLER_PRIMARY_VTABLE_RVA:
        raise ValueError("idler primary vtable fingerprint changed")
    if _u64(idler_bytes, 0x88) != handler:
        raise ValueError("idler does not point to the supplied handler")
    if (_u64(handler_bytes, 0) != base + HANDLER_PRIMARY_VTABLE_RVA
            or _u64(handler_bytes, 0x58)
            != base + HANDLER_SECONDARY_VTABLE_RVA):
        raise ValueError("handler double vtable fingerprint changed")
    if _u64(handler_bytes, 0x470) != topbar:
        raise ValueError("handler does not point to the supplied topbar")
    if (_u64(topbar_bytes, 0) != base + TOPBAR_PRIMARY_VTABLE_RVA
            or _u64(topbar_bytes, 0x10)
            != base + TOPBAR_SECONDARY_VTABLE_RVA):
        raise ValueError("topbar double vtable fingerprint changed")
    context = _address(_u64(handler_bytes, 0x40), "topbar context")
    if _u64(topbar_bytes, 0xC8) != context:
        raise ValueError("topbar context does not match its handler")
    if _u64(topbar_bytes, 0xD0) != handler:
        raise ValueError("topbar reverse handler pointer changed")
    return {
        "schema": "xar.ck3.war-cash-topbar-owner-path-diagnostic.v1",
        "status": "structurally_matching_supplied_bytes_only",
        "module_image_base": hex(base),
        "global_slot_address": hex(slot),
        "global_owner_address": hex(owner),
        "idler_address": hex(idler),
        "handler_address": hex(handler),
        "topbar_address": hex(topbar),
        "topbar_context_address": hex(context),
        "supplied_bytes_sha256": {
            label: hashlib.sha256(data).hexdigest().upper()
            for label, data in (
                ("global_slot", global_slot_bytes),
                ("global_owner", global_owner_bytes),
                ("idler", idler_bytes),
                ("handler", handler_bytes),
                ("topbar", topbar_bytes),
            )
        },
        "unique_live_topbar_instance_proven": False,
        "same_frame_cache_freshness_proven": False,
        "formal_cash_eligible": False,
    }
