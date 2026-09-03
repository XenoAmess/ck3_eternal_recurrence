#!/usr/bin/env python3
"""Create disposable, brace-balanced workforce endgame bisect segments.

The generated files are deliberately outside the product tree.  Each segment
contains the original header (including a UTF-8 BOM when present) followed by
complete top-level scripted-effect blocks, so a recovery run can replace one
file without cutting through a CK3 definition.  The source is never modified.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Iterable


DEFAULT_RELATIVE_SOURCE = Path(
    "mod_zhongguo_style/common/scripted_effects/"
    "zg361_workforce_endgame_runtime_effects.txt"
)
BLOCK_RE = re.compile(
    r"^\ufeff?\s*([A-Za-z_][A-Za-z0-9_.:-]*)\s*=\s*\{"
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def scan_line(line: str, in_quote: bool) -> tuple[int, bool]:
    """Return brace delta and quote state for one line.

    CK3 comments begin at ``#`` outside a quoted string.  Escaped quotes are
    retained as content.  This is intentionally a small lexical scanner, not a
    parser; it is sufficient to find complete top-level braces without
    rewriting any source bytes.
    """

    delta = 0
    escaped = False
    for char in line:
        if escaped:
            escaped = False
            continue
        if char == "\\" and in_quote:
            escaped = True
            continue
        if char == '"':
            in_quote = not in_quote
            continue
        if not in_quote and char == "#":
            break
        if not in_quote:
            if char == "{":
                delta += 1
            elif char == "}":
                delta -= 1
    return delta, in_quote


def find_blocks(data: bytes) -> tuple[bytes, list[dict[str, object]]]:
    """Find top-level blocks while retaining exact byte offsets."""

    bom = data.startswith(b"\xef\xbb\xbf")
    text = data.decode("utf-8-sig" if bom else "utf-8")
    lines = text.splitlines(keepends=True)
    # ``utf-8-sig`` strips the BOM from ``text`` while the source byte slices
    # below still address the original bytes.  Seed the offset table past the
    # three-byte BOM so every block and header slice remains byte-exact.
    byte_offsets: list[int] = [3 if bom else 0]
    encoded_lines: list[bytes] = []
    for line in lines:
        encoded = line.encode("utf-8")
        encoded_lines.append(encoded)
        byte_offsets.append(byte_offsets[-1] + len(encoded))

    header_end_line = None
    blocks: list[dict[str, object]] = []
    depth = 0
    in_quote = False
    current: dict[str, object] | None = None
    for line_no, line in enumerate(lines, start=1):
        if depth == 0:
            match = BLOCK_RE.match(line)
            if match:
                current = {
                    "index": len(blocks),
                    "name": match.group(1),
                    "start_line": line_no,
                    "start_byte": byte_offsets[line_no - 1],
                }
                if header_end_line is None:
                    header_end_line = line_no - 1
        delta, in_quote = scan_line(line, in_quote)
        depth += delta
        if current is not None and depth == 0:
            current["end_line"] = line_no
            current["end_byte"] = byte_offsets[line_no]
            block_bytes = data[
                int(current["start_byte"]): int(current["end_byte"])
            ]
            current["bytes"] = len(block_bytes)
            current["sha256"] = sha256(block_bytes)
            blocks.append(current)
            current = None
    if current is not None or depth != 0:
        raise ValueError(
            f"unbalanced source: depth={depth}, open block={current!r}"
        )
    if not blocks:
        raise ValueError("no top-level blocks found")
    header_line_count = header_end_line if header_end_line is not None else 0
    header_end_byte = byte_offsets[header_line_count]
    header = data[:header_end_byte]
    return header, blocks


def write_segment(
    output: Path,
    header: bytes,
    blocks: list[dict[str, object]],
    source: bytes,
) -> dict[str, object]:
    output.parent.mkdir(parents=True, exist_ok=True)
    pieces = [header]
    for block in blocks:
        pieces.append(
            source[int(block["start_byte"]): int(block["end_byte"])]
        )
    data = b"".join(pieces)
    output.write_bytes(data)
    return {
        "path": output.as_posix(),
        "block_indices": [int(block["index"]) for block in blocks],
        "first_block": blocks[0]["index"] if blocks else None,
        "last_block": blocks[-1]["index"] if blocks else None,
        "bytes": len(data),
        "sha256": sha256(data),
    }


def parse_ranges(spec: str, count: int) -> list[int]:
    selected: set[int] = set()
    for item in spec.split(","):
        item = item.strip()
        if not item:
            continue
        if "-" in item:
            left, right = item.split("-", 1)
            start, end = int(left), int(right)
        else:
            start = end = int(item)
        if start < 0 or end < start or end >= count:
            raise ValueError(f"range outside 0..{count - 1}: {item}")
        selected.update(range(start, end + 1))
    return sorted(selected)


def block_groups(blocks: list[dict[str, object]], size: int) -> Iterable[list[dict[str, object]]]:
    for start in range(0, len(blocks), size):
        yield blocks[start:start + size]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, help="exact source file to snapshot")
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument(
        "--chunk-size", type=int, default=16,
        help="blocks per sequential chunk (default: 16)",
    )
    parser.add_argument(
        "--ranges", help="optional comma-separated inclusive block ranges to emit",
    )
    args = parser.parse_args()
    if args.chunk_size <= 0:
        parser.error("--chunk-size must be positive")

    source_path = args.source
    if source_path is None:
        source_path = Path.cwd() / DEFAULT_RELATIVE_SOURCE
    source_path = source_path.resolve()
    data = source_path.read_bytes()
    header, blocks = find_blocks(data)
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    snapshot = output / "source" / source_path.name
    snapshot.parent.mkdir(parents=True, exist_ok=True)
    snapshot.write_bytes(data)

    generated: list[dict[str, object]] = []
    if args.ranges:
        selected = parse_ranges(args.ranges, len(blocks))
        generated.append(
            write_segment(
                output / "selected" / f"blocks-{args.ranges.replace(',', '_')}.txt",
                header,
                [blocks[index] for index in selected],
                data,
            )
        )
    else:
        for block in blocks:
            safe_name = re.sub(r"[^A-Za-z0-9_.-]+", "_", str(block["name"]))
            generated.append(
                write_segment(
                    output / "blocks" / f"block-{int(block['index']):04d}-{safe_name}.txt",
                    header,
                    [block],
                    data,
                )
            )
        for group_index, group in enumerate(block_groups(blocks, args.chunk_size)):
            generated.append(
                write_segment(
                    output / "chunks" / (
                        f"chunk-{int(group[0]['index']):04d}-"
                        f"{int(group[-1]['index']):04d}.txt"
                    ),
                    header, group, data,
                )
            )
        midpoint = len(blocks) // 2
        for name, group in (
            ("left", blocks[:midpoint]),
            ("right", blocks[midpoint:]),
        ):
            generated.append(
                write_segment(output / "halves" / f"{name}.txt", header, group, data)
            )

    manifest = {
        "schema_version": 1,
        "kind": "zg361_workforce_endgame_block_segments",
        "read_only_source": str(source_path),
        "source_bytes": len(data),
        "source_sha256": sha256(data),
        "utf8_bom": data.startswith(b"\xef\xbb\xbf"),
        "header_bytes": len(header),
        "header_lines": header.count(b"\n"),
        "block_count": len(blocks),
        "blocks": blocks,
        "generated": generated,
        "notes": [
            "Disposable output; no canonical source is changed.",
            "Every generated segment starts with the exact original header/BOM.",
            "Block ranges are zero-based and inclusive.",
        ],
    }
    manifest_path = output / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "source": str(source_path),
        "source_bytes": len(data),
        "source_sha256": sha256(data),
        "block_count": len(blocks),
        "header_bytes": len(header),
        "output": str(output),
        "manifest": str(manifest_path),
        "generated_count": len(generated),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
