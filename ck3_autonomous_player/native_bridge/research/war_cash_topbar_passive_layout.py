"""Decode supplied InGameTopbar bytes without touching a CK3 process.

The caller owns all byte reads.  This layout diagnostic cannot identify the
unique live GUI object, prove cache freshness, or authorize a cash amount.
"""

from __future__ import annotations

from collections.abc import Mapping
import hashlib
import struct


TOPBAR_READ_SIZE = 0xF90
TOPBAR_PRIMARY_VTABLE_RVA = 0x40E6F68
TOPBAR_SECONDARY_VTABLE_RVA = 0x40E7038
ROW_STRIDE = 0x90
GOLD_SCALE = 100_000
MAX_DIAGNOSTIC_ROWS = 128
MILITARY_LABEL_KEYS = frozenset({
    "BREAKDOWN_ARMY_MAINTENANCE",
    "BREAKDOWN_ARMY_MAINTENANCE_EMBARKED",
    "BD_UNRAISED_MAA_MAINTENANCE",
    "BD_UNRAISED_MAA_MAINTENANCE_BASE",
    "BD_UNCONTROLLED_MAA_MAINTENANCE",
    "BD_UNCONTROLLED_MAA_MAINTENANCE_BASE",
})


def _u32(data: bytes, offset: int) -> int:
    return struct.unpack_from("<I", data, offset)[0]


def _u64(data: bytes, offset: int) -> int:
    return struct.unpack_from("<Q", data, offset)[0]


def _i64(data: bytes, offset: int) -> int:
    return struct.unpack_from("<q", data, offset)[0]


def _name_key(row: bytes, name_payloads: Mapping[int, bytes]) -> str:
    length = _u64(row, 0x28)
    capacity = _u64(row, 0x30)
    if length == 0 or length > 127 or capacity < length:
        raise ValueError("ValueBreakdown row name length/capacity is invalid")
    if capacity <= 15:
        name = row[0x18:0x18 + length]
        if row[0x18 + length] != 0:
            raise ValueError("inline ValueBreakdown row name lacks terminator")
    else:
        address = _u64(row, 0x18)
        if address < 0x10000 or address % 8:
            raise ValueError("heap ValueBreakdown row name pointer is invalid")
        payload = name_payloads.get(address)
        if not isinstance(payload, bytes) or len(payload) != length + 1:
            raise ValueError("heap ValueBreakdown row name bytes were not supplied")
        if payload[-1] != 0:
            raise ValueError("heap ValueBreakdown row name lacks terminator")
        name = payload[:-1]
    try:
        key = name.decode("ascii")
    except UnicodeDecodeError as error:
        raise ValueError("ValueBreakdown row name is not an ASCII key") from error
    if not key or any(not (character.isalnum() or character == "_")
                      for character in key):
        raise ValueError("ValueBreakdown row name is not a localization key")
    return key


def inspect_supplied_topbar_expense_bytes(
    *, image_base: int, topbar_address: int, topbar_bytes: bytes,
    row_array_address: int, row_bytes: bytes,
    name_payloads: Mapping[int, bytes],
) -> dict[str, object]:
    """Check layout of one externally supplied candidate, never live truth."""
    if (type(image_base) is not int or image_base < 0x10000
            or image_base % 0x10000
            or type(topbar_address) is not int or topbar_address < 0x10000
            or not isinstance(topbar_bytes, bytes)
            or len(topbar_bytes) != TOPBAR_READ_SIZE
            or type(row_array_address) is not int
            or row_array_address < 0x10000 or row_array_address % 8
            or not isinstance(row_bytes, bytes)
            or not isinstance(name_payloads, Mapping)):
        raise ValueError("exact supplied topbar and row bytes required")
    if (_u64(topbar_bytes, 0) != image_base + TOPBAR_PRIMARY_VTABLE_RVA
            or _u64(topbar_bytes, 0x10)
            != image_base + TOPBAR_SECONDARY_VTABLE_RVA):
        raise ValueError("CHudTopBar double vtable fingerprint does not match")
    if _u64(topbar_bytes, 0xB68) != topbar_address + 0xAD8:
        raise ValueError("expense ValueBreakdown back-pointer does not match")
    if _u64(topbar_bytes, 0xB58) != GOLD_SCALE:
        raise ValueError("expense total is not Q100000")
    count = _u32(topbar_bytes, 0xAE4)
    capacity = _u32(topbar_bytes, 0xAE0)
    if (not 0 < count <= capacity <= MAX_DIAGNOSTIC_ROWS
            or _u64(topbar_bytes, 0xAD8) != row_array_address
            or len(row_bytes) != count * ROW_STRIDE):
        raise ValueError("expense row vector is missing or out of bounds")
    rows = []
    for index in range(count):
        row = row_bytes[index * ROW_STRIDE:(index + 1) * ROW_STRIDE]
        if _u64(row, 0x80) != GOLD_SCALE:
            raise ValueError("expense row is not Q100000")
        name = _name_key(row, name_payloads)
        rows.append({
            "index": index,
            "address": hex(row_array_address + index * ROW_STRIDE),
            "name_key": name,
            "signed_raw_candidate": _i64(row, 0x78),
            "military_label_candidate": name in MILITARY_LABEL_KEYS,
        })
    return {
        "schema": "xar.ck3.war-cash-topbar-passive-layout-diagnostic.v1",
        "status": "structurally_matching_supplied_bytes_only",
        "topbar_address": hex(topbar_address),
        "image_base": hex(image_base),
        "double_vtable_fingerprint_matches": True,
        "topbar_sha256": hashlib.sha256(topbar_bytes).hexdigest().upper(),
        "row_array_address": hex(row_array_address),
        "row_array_sha256": hashlib.sha256(row_bytes).hexdigest().upper(),
        "row_count": count,
        "row_capacity": capacity,
        "last_update_render_frame_candidate": _u64(topbar_bytes, 0xF88),
        "expense_total_signed_raw_candidate": _i64(topbar_bytes, 0xB50),
        "rows": rows,
        "military_row_candidate_count": sum(
            row["military_label_candidate"] for row in rows),
        "unique_live_topbar_instance_proven": False,
        "same_frame_cache_freshness_proven": False,
        "military_component_complete_proven": False,
        "formal_cash_eligible": False,
    }
