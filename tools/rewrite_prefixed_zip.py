"""Pure, checked rewrite of one standard ZIP member with an opaque prefix.

No paths, processes, game formats, migration policy, or filesystem writes.
Unsupported archive shapes fail before invoking the caller's transform.
"""
from __future__ import annotations

import copy
import hashlib
import io
from typing import Callable
import zipfile


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _shape(info: zipfile.ZipInfo) -> tuple:
    return (info.filename, info.date_time, info.compress_type, info.flag_bits,
            info.create_system, info.create_version, info.extract_version,
            info.reserved, info.internal_attr, info.external_attr, info.extra,
            info.comment)


def rewrite_single_member_zip(
    source: bytes, member_name: str, transform: Callable[[bytes], bytes],
) -> tuple[bytes, dict]:
    """Preserve prefix, member metadata, archive comment and offset convention.

    The supported shape is exactly one unencrypted, non-ZIP64 member using
    stored/deflated compression and no data descriptor. Only its payload is
    transformed. Complete input/output CRC reads and metadata equality are
    checked. Recompression can change the compressed bytes and directory
    location; the caller proves its own payload changes separately.
    """
    if not isinstance(source, bytes) or not isinstance(member_name, str):
        raise TypeError("source bytes and explicit member name required")
    with zipfile.ZipFile(io.BytesIO(source)) as archive:
        infos = archive.infolist()
        if len(infos) != 1 or infos[0].filename != member_name or infos[0].is_dir():
            raise ValueError("expected exactly the selected single file member")
        info = infos[0]
        if info.compress_type not in {zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED}:
            raise ValueError("unsupported compression method")
        if info.flag_bits & ~0x800 or info.extract_version >= 45:
            raise ValueError("encrypted, descriptor or ZIP64 shape unsupported")
        if max(info.file_size, info.compress_size, info.header_offset, archive.start_dir) >= 0xFFFFFFFF:
            raise ValueError("ZIP64 shape unsupported")
        prefix_offset = info.header_offset
        central = archive.start_dir
        if source[prefix_offset:prefix_offset + 4] != b"PK\x03\x04" or source[central:central + 4] != b"PK\x01\x02":
            raise ValueError("unsupported standard ZIP header shape")
        encoded_offset = int.from_bytes(source[central + 42:central + 46], "little")
        if encoded_offset not in {0, prefix_offset}:
            raise ValueError("unsupported local-header offset convention")
        relative_offsets = encoded_offset == 0
        prefix = source[:prefix_offset]
        original_shape = _shape(info)
        comment = archive.comment
        before = archive.read(info)  # full source member CRC check
        after = transform(before)
        if not isinstance(after, bytes):
            raise TypeError("transform must return bytes")
        if len(after) >= 0xFFFFFFFF:
            raise ValueError("replacement ZIP64 size unsupported")
        original_crc = info.CRC

    buffer = io.BytesIO()
    if not relative_offsets:
        buffer.write(prefix)
    with zipfile.ZipFile(buffer, "w", allowZip64=False) as output:
        output.comment = comment
        output.writestr(copy.copy(info), after, compress_type=info.compress_type,
                        compresslevel=9 if info.compress_type == zipfile.ZIP_DEFLATED else None)
        # zipfile supplies default permissions when external_attr is zero.
        # Restore via the public ZipInfo object before close writes central data.
        output.getinfo(member_name).external_attr = info.external_attr
    rewritten = buffer.getvalue()
    if relative_offsets:
        rewritten = prefix + rewritten

    with zipfile.ZipFile(io.BytesIO(rewritten)) as verified:
        out_infos = verified.infolist()
        out_info = out_infos[0]
        if len(out_infos) != 1 or _shape(out_info) != original_shape or verified.comment != comment:
            raise ValueError("member metadata or archive comment changed")
        if out_info.header_offset != prefix_offset or rewritten[:prefix_offset] != prefix:
            raise ValueError("opaque prefix changed")
        out_encoded = int.from_bytes(rewritten[verified.start_dir + 42:verified.start_dir + 46], "little")
        if out_encoded != encoded_offset:
            raise ValueError("offset convention changed")
        if verified.read(out_info) != after:  # full output CRC check
            raise ValueError("rewritten payload readback differs")
        receipt = {
            "source_bytes": len(source), "source_sha256": _sha(source),
            "output_bytes": len(rewritten), "output_sha256": _sha(rewritten),
            "member_name": member_name, "source_member_bytes": len(before),
            "source_member_sha256": _sha(before), "source_member_crc32": f"{original_crc:08x}",
            "output_member_bytes": len(after), "output_member_sha256": _sha(after),
            "output_member_crc32": f"{out_info.CRC:08x}",
            "prefix_bytes": len(prefix), "prefix_sha256": _sha(prefix),
            "prefix_byte_exact": True, "member_shape_equal": True,
            "external_attr": out_info.external_attr, "member_order": [member_name],
            "relative_offsets": relative_offsets, "encoded_local_header_offset": encoded_offset,
            "source_and_output_full_CRC_read": True,
            "compression_method": info.compress_type,
            "compression_note": "Payload recompression changes compressed bytes/CRC/sizes/directory position; opaque prefix and declared member metadata remain exact",
        }
    return rewritten, receipt
