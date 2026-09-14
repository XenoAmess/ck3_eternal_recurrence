#!/usr/bin/env python3
"""Fetch and exactly verify public Steam Workshop metadata and Change Notes."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
from pathlib import Path
import re
import sys
from urllib import parse, request


ITEM_API = "https://api.steampowered.com/ISteamRemoteStorage/GetPublishedFileDetails/v1/"
CHANGELOG_URL = "https://steamcommunity.com/sharedfiles/filedetails/changelog/{item_id}"
ITEM_ID = re.compile(r"[1-9][0-9]*", re.ASCII)
PARAGRAPH = re.compile(r'<p\s+id="([0-9]+)"[^>]*>(.*?)</p>', re.IGNORECASE | re.DOTALL)
BREAK = re.compile(r"<br\s*/?>", re.IGNORECASE)
TAG = re.compile(r"<[^>]+>")


def normalized(value: str) -> str:
    return value.replace("\r\n", "\n").replace("\r", "\n").rstrip("\n")


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest().upper()


def decode_changelog_paragraphs(raw_html: str) -> list[tuple[str, str]]:
    result: list[tuple[str, str]] = []
    for entry_id, body in PARAGRAPH.findall(raw_html):
        value = BREAK.sub("\n", body)
        value = html.unescape(TAG.sub("", value))
        result.append((entry_id, normalized(value)))
    return result


def verify_payloads(
    *,
    item_api: dict[str, object],
    changelog_html: str,
    expected_title: str,
    expected_description: str,
    expected_change_notes: str,
) -> dict[str, object]:
    try:
        details = item_api["response"]["publishedfiledetails"]
        item = details[0]
    except (KeyError, IndexError, TypeError) as error:
        raise ValueError("public item API response has an unexpected shape") from error
    if not isinstance(item, dict):
        raise ValueError("public item API detail is not an object")
    description = normalized(str(item.get("description", "")))
    expected_description = normalized(expected_description)
    expected_change_notes = normalized(expected_change_notes)
    matches = [
        (entry_id, value)
        for entry_id, value in decode_changelog_paragraphs(changelog_html)
        if value == expected_change_notes
    ]
    if len(matches) > 1:
        raise ValueError("multiple public Change Notes entries equal the expected text")
    entry_id, public_notes = matches[0] if matches else (None, "")
    result = {
        "title_exact": item.get("title") == expected_title,
        "description_exact": description == expected_description,
        "description_characters": len(description),
        "description_sha256": sha256_text(description),
        "expected_description_sha256": sha256_text(expected_description),
        "change_notes_exact": entry_id is not None,
        "changelog_entry_id": entry_id,
        "change_notes_characters": len(public_notes),
        "change_notes_lines": public_notes.count("\n") + 1 if public_notes else 0,
        "change_notes_sha256": sha256_text(public_notes),
        "expected_change_notes_characters": len(expected_change_notes),
        "expected_change_notes_lines": expected_change_notes.count("\n") + 1,
        "expected_change_notes_sha256": sha256_text(expected_change_notes),
        "time_updated": item.get("time_updated"),
        "file_size": item.get("file_size"),
    }
    result["ok"] = bool(
        result["title_exact"]
        and result["description_exact"]
        and result["change_notes_exact"]
    )
    return result


def fetch_public_item(item_id: str, timeout: float) -> bytes:
    payload = parse.urlencode(
        {"itemcount": "1", "publishedfileids[0]": item_id}
    ).encode("ascii")
    call = request.Request(
        ITEM_API,
        data=payload,
        headers={"User-Agent": "tributary-expansion-directives-release-verifier/1.0"},
        method="POST",
    )
    with request.urlopen(call, timeout=timeout) as response:
        return response.read()


def fetch_changelog(item_id: str, timeout: float) -> bytes:
    call = request.Request(
        CHANGELOG_URL.format(item_id=item_id),
        headers={"User-Agent": "tributary-expansion-directives-release-verifier/1.0"},
    )
    with request.urlopen(call, timeout=timeout) as response:
        return response.read()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--item-id", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--description", type=Path, required=True)
    parser.add_argument("--change-notes", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--timeout", type=float, default=30.0)
    args = parser.parse_args(argv)
    try:
        if ITEM_ID.fullmatch(args.item_id) is None:
            raise ValueError("--item-id must be positive ASCII digits without leading zeros")
        output = args.output.expanduser().resolve()
        if output.exists() or not output.parent.is_dir():
            raise ValueError("--output must be a new directory under an existing parent")
        expected_description = args.description.read_text(encoding="utf-8")
        expected_change_notes = args.change_notes.read_text(encoding="utf-8")
        item_bytes = fetch_public_item(args.item_id, args.timeout)
        changelog_bytes = fetch_changelog(args.item_id, args.timeout)
        item_api = json.loads(item_bytes.decode("utf-8-sig"))
        changelog = changelog_bytes.decode("utf-8-sig")
        result = verify_payloads(
            item_api=item_api,
            changelog_html=changelog,
            expected_title=args.title,
            expected_description=expected_description,
            expected_change_notes=expected_change_notes,
        )
        output.mkdir()
        (output / "public_item_api_raw.json").write_bytes(item_bytes)
        (output / "public_changelog_raw.html").write_bytes(changelog_bytes)
        (output / "verification.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["ok"] else 1
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
        print(f"WORKSHOP PUBLICATION VERIFICATION FAILED: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
