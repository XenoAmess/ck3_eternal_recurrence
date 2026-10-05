"""Derive CK3 Workshop compatibility tags from a release staging descriptor.

These are ordinary Steam Workshop tags. A descriptor version is a metadata
claim; this helper does not establish gameplay acceptance or authorize upload.
Automatic tagging starts at CK3 1.20. Older versions preserve their tags. Add
future labels only after confirming the game's actual Workshop filter.
"""

from __future__ import annotations

from pathlib import Path
import re
from typing import Sequence


# Single registry for both native publication and staging descriptor rendering.
# Future confirmed minors need only a new entry here; consumers remain unchanged.
CK3_WORKSHOP_VERSION_TAGS = {"1.20": "1.20 'Crozier'"}
_SUPPORTED_VERSION = re.compile(
    r'^\s*supported_version\s*=\s*"([^"\r\n]+)"\s*(?:#.*)?$',
    re.MULTILINE,
)
_VERSION_ASSIGNMENT = re.compile(r"^\s*supported_version\s*=", re.MULTILINE)
_VERSION = re.compile(r"([0-9]+)\.([0-9]+)(?:\.(?:[0-9]+|\*)){0,2}")
_COMPATIBILITY_TAG = re.compile(r"[0-9]+\.[0-9]+(?: '[^'\r\n]+')?")


def compatibility_tag_from_descriptor(descriptor: str) -> str | None:
    """Return the confirmed Workshop tag, or None for versions before 1.20.

    The version may specify a minor, numeric patch/build or CK3 wildcard. Missing,
    duplicate, malformed and unmapped 1.20+ values fail before any remote operation.
    """
    if not isinstance(descriptor, str):
        raise ValueError("descriptor must be text")
    descriptor = descriptor.lstrip("\ufeff")
    versions = _SUPPORTED_VERSION.findall(descriptor)
    if len(versions) != 1 or len(_VERSION_ASSIGNMENT.findall(descriptor)) != 1:
        raise ValueError("descriptor must contain exactly one supported_version")
    version = _VERSION.fullmatch(versions[0])
    if version is None:
        raise ValueError(f"invalid supported_version: {versions[0]!r}")
    minor_version = (int(version.group(1)), int(version.group(2)))
    if minor_version < (1, 20):
        return None
    minor = f"{minor_version[0]}.{minor_version[1]}"
    try:
        return CK3_WORKSHOP_VERSION_TAGS[minor]
    except KeyError:
        raise ValueError(
            f"no confirmed CK3 Workshop compatibility tag for {minor}; "
            "confirm the official version label before publishing"
        ) from None


def compatibility_tags_for_staging(
    staging_dir: Path | str, tags: Sequence[str]
) -> tuple[str, ...]:
    """Replace version tags while preserving every other tag and its order.

    Read only the actual staging descriptor. Do not use the development tree or
    change a descriptor, content file, description or Change Notes.
    """
    if isinstance(tags, (str, bytes)) or not isinstance(tags, Sequence):
        raise ValueError("tags must be a sequence of non-empty strings")
    if any(not isinstance(tag, str) or not tag for tag in tags):
        raise ValueError("tags must be a sequence of non-empty strings")
    descriptor = Path(staging_dir) / "descriptor.mod"
    label = compatibility_tag_from_descriptor(descriptor.read_text(encoding="utf-8-sig"))
    if label is None:
        return tuple(tags)
    retained = tuple(tag for tag in tags if _COMPATIBILITY_TAG.fullmatch(tag) is None)
    return retained + (label,)
