#!/usr/bin/env python3
"""Strict release gate for the ZhongGuo 361 Steam Workshop description.

This validator is intentionally independent from ``validate_local.py`` while
the tracked description/media strip is still being assembled.  Run it as a
release gate once all eight final images have been projected and committed.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import re
import sys

import compose_workshop_media as workshop_media


MOD_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DESCRIPTION = MOD_ROOT / "workshop" / "description.bbcode"
DEFAULT_MEDIA_DIRECTORY = MOD_ROOT / "workshop" / "media"
MAX_DESCRIPTION_BYTES = 8_000
EXPECTED_IMAGE_COUNT = 8
EXPECTED_MEDIA_INVENTORY = frozenset(
    workshop_media.EXPECTED_RELEASE_MEDIA_INVENTORY
)

IMAGE_OPEN_RE = re.compile(r"\[img\]", re.IGNORECASE)
IMAGE_CLOSE_RE = re.compile(r"\[/img\]", re.IGNORECASE)
IMAGE_TAG_RE = re.compile(r"\[img\](?P<url>.*?)\[/img\]", re.IGNORECASE | re.DOTALL)
RAW_URL_RE = re.compile(r'https://raw\.githubusercontent\.com/[^\s\[\]"<>]+')
MEDIA_URL_RE = re.compile(
    r"https://raw\.githubusercontent\.com/"
    r"XenoAmess/ck3_eternal_recurrence/"
    r"(?P<commit>[0-9a-fA-F]{40})/"
    r"mod_zhongguo_style/workshop/media/"
    r"(?P<filename>[^/?#\s\[\]<>]+)"
)
HEX_COMMIT_RE = re.compile(r"[0-9a-fA-F]{40}")


@dataclass(frozen=True)
class ValidationResult:
    byte_count: int
    submitted_byte_count: int
    image_count: int
    commit_sha: str | None
    media_inventory: tuple[str, ...]
    errors: tuple[str, ...]

    @property
    def ok(self) -> bool:
        return not self.errors


def _inventory_error(label: str, actual: set[str]) -> str | None:
    if actual == EXPECTED_MEDIA_INVENTORY:
        return None
    missing = sorted(EXPECTED_MEDIA_INVENTORY - actual)
    unexpected = sorted(actual - EXPECTED_MEDIA_INVENTORY)
    return f"{label} inventory mismatch; missing={missing}, unexpected={unexpected}"


def validate_description(
    description: Path,
    media_directory: Path,
) -> ValidationResult:
    errors: list[str] = []
    try:
        data = description.read_bytes()
    except OSError as error:
        return ValidationResult(0, 0, 0, None, (), (f"cannot read description: {error}",))
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        return ValidationResult(
            len(data),
            0,
            0,
            None,
            (),
            tuple(errors + [f"Workshop description is not valid UTF-8: {error}"]),
        )

    # Steam's HTML form serializes textarea line endings as CRLF. Checking
    # only repository LF bytes can admit a value that the endpoint rejects.
    submitted_text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\n", "\r\n")
    submitted_byte_count = len(submitted_text.encode("utf-8"))
    if submitted_byte_count >= MAX_DESCRIPTION_BYTES:
        errors.append(
            "Workshop description must be below 8000 UTF-8 bytes after CRLF "
            f"form projection: local={len(data)}, submitted={submitted_byte_count} bytes"
        )

    opening_count = len(IMAGE_OPEN_RE.findall(text))
    closing_count = len(IMAGE_CLOSE_RE.findall(text))
    image_urls = [match.group("url").strip() for match in IMAGE_TAG_RE.finditer(text)]
    if opening_count != EXPECTED_IMAGE_COUNT or closing_count != EXPECTED_IMAGE_COUNT:
        errors.append(
            "Workshop description must contain exactly 8 [img]...[/img] tags: "
            f"open={opening_count}, close={closing_count}"
        )
    if len(image_urls) != opening_count or len(image_urls) != closing_count:
        errors.append("Workshop description contains an unmatched or malformed [img] tag")

    commits: set[str] = set()
    referenced_files: list[str] = []
    for url in image_urls:
        match = MEDIA_URL_RE.fullmatch(url)
        if match is None:
            errors.append(f"image URL is not a canonical commit-pinned media URL: {url}")
            continue
        commits.add(match.group("commit").lower())
        referenced_files.append(match.group("filename"))

    raw_urls = RAW_URL_RE.findall(text)
    for url in raw_urls:
        segments = url.split("/")
        # https:, '', host, owner, repo, revision, path...
        revision = segments[5] if len(segments) > 5 else ""
        if HEX_COMMIT_RE.fullmatch(revision) is None:
            errors.append(f"raw URL is not pinned to a 40-character commit SHA: {url}")
        else:
            commits.add(revision.lower())
    if len(commits) != 1:
        errors.append(
            "all raw URLs must use one identical 40-character commit SHA: "
            f"found={sorted(commits)}"
        )

    referenced_set = set(referenced_files)
    inventory_error = _inventory_error("description image", referenced_set)
    if inventory_error:
        errors.append(inventory_error)
    if len(referenced_files) != len(referenced_set):
        errors.append("Workshop description references a media filename more than once")

    try:
        tracked_set = {
            path.name for path in media_directory.iterdir() if path.is_file()
        }
    except OSError as error:
        errors.append(f"cannot read Workshop media directory: {error}")
    else:
        inventory_error = _inventory_error("tracked Workshop media", tracked_set)
        if inventory_error:
            errors.append(inventory_error)

    commit_sha = next(iter(commits)) if len(commits) == 1 else None
    return ValidationResult(
        byte_count=len(data),
        submitted_byte_count=submitted_byte_count,
        image_count=len(image_urls),
        commit_sha=commit_sha,
        media_inventory=tuple(sorted(referenced_set)),
        errors=tuple(errors),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--description", type=Path, default=DEFAULT_DESCRIPTION)
    parser.add_argument("--media-directory", type=Path, default=DEFAULT_MEDIA_DIRECTORY)
    arguments = parser.parse_args(argv)
    result = validate_description(
        arguments.description.resolve(),
        arguments.media_directory.resolve(),
    )
    if not result.ok:
        print(f"RED: {len(result.errors)} Workshop description problem(s)", file=sys.stderr)
        for error in result.errors:
            print(f"  - {error}", file=sys.stderr)
        return 1
    print(
        "GREEN: Workshop description is release-ready; "
        f"{result.byte_count} local / {result.submitted_byte_count} CRLF-projected "
        f"UTF-8 bytes, {result.image_count} images, "
        f"commit {result.commit_sha}, exact 01-08 media inventory"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
