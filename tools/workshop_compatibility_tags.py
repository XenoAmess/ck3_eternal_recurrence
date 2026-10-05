"""Render descriptor compatibility tags using the native publication registry.

Only descriptor bytes are projected. Every other release file is returned
unchanged, and this module neither contacts Steam nor establishes acceptance.
"""

from __future__ import annotations

import json
from pathlib import Path
import re
import sys


_MCP_SOURCE = Path(__file__).resolve().parents[1] / "ck3_workshop_mcp" / "src"
if str(_MCP_SOURCE) not in sys.path:
    sys.path.insert(0, str(_MCP_SOURCE))
from ck3_workshop_mcp import compatibility_tags as registry


_TAG_BLOCK = re.compile(r"\btags\s*=\s*\{([^{}]*)\}", re.DOTALL)
_STRING = re.compile(r'#[^\r\n]*|"(?:[^"\\]|\\.)*"')


def workshop_compatibility_tag(descriptor: str) -> str | None:
    """Use the same supported-version registry as native publication."""
    return registry.compatibility_tag_from_descriptor(descriptor)


def render_workshop_descriptor_bytes(data: bytes) -> bytes:
    """Replace version tags from supported_version, preserving all other fields.

    Unmapped legacy versions return their exact bytes when the shared registry
    returns None. Unknown current/future versions retain its fail-closed policy.
    """
    has_bom = data.startswith(b"\xef\xbb\xbf")
    descriptor = data.decode("utf-8-sig")
    label = workshop_compatibility_tag(descriptor)
    if label is None:
        return data
    blocks = list(_TAG_BLOCK.finditer(descriptor))
    if len(blocks) != 1:
        raise ValueError("descriptor must contain exactly one tags block")
    block = blocks[0]
    body = block.group(1)
    tokens = [token for token in _STRING.finditer(body) if token.group().startswith('"')]
    version_tokens = [token for token in tokens
                      if registry._COMPATIBILITY_TAG.fullmatch(json.loads(token.group()))]
    if len(version_tokens) == 1 and json.loads(version_tokens[0].group()) == label:
        return data
    # Remove only version-tag strings; non-version strings and comments survive.
    for token in reversed(version_tokens):
        begin, end = token.span()
        line_start = body.rfind("\n", 0, begin) + 1
        line_end = body.find("\n", end)
        if line_end >= 0 and not body[line_start:begin].strip() and not body[end:line_end].strip():
            begin, end = line_start, line_end + 1
        body = body[:begin] + body[end:]
    encoded_label = json.dumps(label, ensure_ascii=False)
    if "\n" in body:
        newline = "\r\n" if "\r\n" in body else "\n"
        indentation = re.search(r"(?:^|\n)([ \t]+)\"", body)
        indent = indentation.group(1) if indentation else "\t"
        closing_indent = re.search(r"[ \t]*$", body).group()
        body = body[:len(body) - len(closing_indent)] if closing_indent else body
        if not body.endswith("\n"):
            body += newline
        body += indent + encoded_label + newline + closing_indent
    else:
        body = body.rstrip() + " " + encoded_label + " "
    result = descriptor[:block.start(1)] + body + descriptor[block.end(1):]
    encoded = result.encode("utf-8")
    return (b"\xef\xbb\xbf" + encoded) if has_bom else encoded


def render_release_file_bytes(relative: str, data: bytes) -> bytes:
    """Project the descriptor alone; all non-descriptor bytes are exact."""
    return render_workshop_descriptor_bytes(data) if relative == "descriptor.mod" else data
