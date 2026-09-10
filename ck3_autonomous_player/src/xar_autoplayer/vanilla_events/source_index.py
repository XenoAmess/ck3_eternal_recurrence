"""Read and validate the frozen exact-build vanilla-event source index."""

from __future__ import annotations

from copy import deepcopy
import hashlib
from importlib import resources
import json
from pathlib import Path, PurePosixPath
import re
from typing import Final, Mapping

from .registry import EXACT_CK3_BUILD, EXACT_CK3_EXE_SHA256


SOURCE_INDEX_SCHEMA: Final = "xar.ck3.vanilla-event-source-index"
SOURCE_INDEX_SCHEMA_VERSION: Final = 1
SOURCE_INDEX_RESOURCE: Final = "data/source_index_1_19_0_6.json"
_SHA256_PATTERN: Final = re.compile(r"^[0-9A-F]{64}$")


class VanillaEventSourceIndexError(ValueError):
    """Raised when the frozen source index fails its deterministic contract."""


def _canonical_dataset_bytes(document: Mapping[str, object]) -> bytes:
    payload = dict(document)
    payload.pop("dataset_sha256", None)
    return json.dumps(
        payload,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def compute_source_index_dataset_sha256(document: Mapping[str, object]) -> str:
    """Hash canonical JSON while excluding the self-referential hash field."""
    return hashlib.sha256(_canonical_dataset_bytes(document)).hexdigest().upper()


def _require_mapping(value: object, *, path: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise VanillaEventSourceIndexError(f"{path} must be an object")
    return value


def _validate_relative_path(value: object, *, path: str) -> str:
    if not isinstance(value, str) or not value or "\\" in value:
        raise VanillaEventSourceIndexError(
            f"{path} must be a non-empty POSIX relative path"
        )
    candidate = PurePosixPath(value)
    has_drive_prefix = bool(candidate.parts) and bool(
        re.fullmatch(r"[A-Za-z]:", candidate.parts[0])
    )
    if candidate.is_absolute() or has_drive_prefix or ".." in candidate.parts:
        raise VanillaEventSourceIndexError(f"{path} must remain relative")
    return value


def _validate_source_record(
    value: object,
    *,
    path: str,
    require_candidate_fields: bool,
) -> str:
    record = _require_mapping(value, path=path)
    relative_path = _validate_relative_path(
        record.get("relative_path"), path=f"{path}.relative_path"
    )
    line = record.get("line")
    if not isinstance(line, int) or isinstance(line, bool) or line < 1:
        raise VanillaEventSourceIndexError(f"{path}.line must be positive")
    sha256 = record.get("file_sha256")
    if not isinstance(sha256, str) or _SHA256_PATTERN.fullmatch(sha256) is None:
        raise VanillaEventSourceIndexError(
            f"{path}.file_sha256 must be uppercase SHA-256"
        )
    if require_candidate_fields:
        column = record.get("column")
        if not isinstance(column, int) or isinstance(column, bool) or column < 1:
            raise VanillaEventSourceIndexError(
                f"{path}.column must be positive"
            )
        if record.get("kind") != "exact-token-lexical-candidate":
            raise VanillaEventSourceIndexError(f"{path}.kind is unsupported")
    return relative_path


def validate_vanilla_event_source_index(
    document: object,
) -> dict[str, object]:
    """Validate and defensively copy one source-index document."""
    root = _require_mapping(document, path="source_index")
    if root.get("schema") != SOURCE_INDEX_SCHEMA:
        raise VanillaEventSourceIndexError("source_index.schema is unsupported")
    if root.get("schema_version") != SOURCE_INDEX_SCHEMA_VERSION:
        raise VanillaEventSourceIndexError(
            "source_index.schema_version is unsupported"
        )
    if root.get("ck3_build") != EXACT_CK3_BUILD:
        raise VanillaEventSourceIndexError("source_index.ck3_build is unsupported")
    if root.get("ck3_exe_sha256") != EXACT_CK3_EXE_SHA256:
        raise VanillaEventSourceIndexError(
            "source_index.ck3_exe_sha256 is unsupported"
        )
    dataset_sha256 = root.get("dataset_sha256")
    if (
        not isinstance(dataset_sha256, str)
        or _SHA256_PATTERN.fullmatch(dataset_sha256) is None
        or dataset_sha256 != compute_source_index_dataset_sha256(root)
    ):
        raise VanillaEventSourceIndexError("source_index dataset SHA-256 mismatch")

    events = _require_mapping(root.get("events"), path="source_index.events")
    if tuple(events) != tuple(sorted(events)):
        raise VanillaEventSourceIndexError(
            "source_index.events must use deterministic key order"
        )
    definition_paths: set[str] = set()
    candidate_paths: set[str] = set()
    external_event_count = 0
    same_file_only_event_count = 0
    candidate_count = 0
    for event_key, raw_event in events.items():
        if not isinstance(event_key, str) or "." not in event_key:
            raise VanillaEventSourceIndexError(
                "source_index.events contains an invalid event key"
            )
        event = _require_mapping(
            raw_event, path=f"source_index.events[{event_key!r}]"
        )
        namespace = event.get("namespace")
        if namespace != event_key.rsplit(".", 1)[0]:
            raise VanillaEventSourceIndexError(
                f"source_index.events[{event_key!r}] namespace mismatch"
            )
        definition_path = _validate_source_record(
            event.get("definition"),
            path=f"source_index.events[{event_key!r}].definition",
            require_candidate_fields=False,
        )
        if not definition_path.startswith("events/"):
            raise VanillaEventSourceIndexError(
                f"source_index.events[{event_key!r}] definition is outside events/"
            )
        definition_paths.add(definition_path)
        resolution = event.get("caller_candidate_resolution")
        if resolution == "external-definition-file":
            external_event_count += 1
        elif resolution == "same-definition-file-only":
            same_file_only_event_count += 1
        else:
            raise VanillaEventSourceIndexError(
                f"source_index.events[{event_key!r}] has invalid resolution"
            )
        candidates = event.get("caller_candidates")
        if not isinstance(candidates, list) or not candidates:
            raise VanillaEventSourceIndexError(
                f"source_index.events[{event_key!r}] has no candidates"
            )
        for index, candidate in enumerate(candidates):
            candidate_path = _validate_source_record(
                candidate,
                path=(
                    f"source_index.events[{event_key!r}]"
                    f".caller_candidates[{index}]"
                ),
                require_candidate_fields=True,
            )
            if not (
                candidate_path.startswith("events/")
                or candidate_path.startswith("common/")
            ):
                raise VanillaEventSourceIndexError(
                    f"caller candidate for {event_key!r} is outside scan roots"
                )
            if resolution == "external-definition-file" and (
                candidate_path == definition_path
            ):
                raise VanillaEventSourceIndexError(
                    f"external caller candidate for {event_key!r} is same-file"
                )
            if resolution == "same-definition-file-only" and (
                candidate_path != definition_path
            ):
                raise VanillaEventSourceIndexError(
                    f"same-file caller candidate for {event_key!r} is external"
                )
            candidate_paths.add(candidate_path)
            candidate_count += 1

    audit = _require_mapping(root.get("audit"), path="source_index.audit")
    expected_audit = {
        "registered_event_count": len(events),
        "unique_definition_count": len(events),
        "definition_file_count": len(definition_paths),
        "missing_definition_count": 0,
        "ambiguous_definition_count": 0,
        "namespace_mismatch_count": 0,
        "caller_candidate_reference_count": candidate_count,
        "external_caller_event_count": external_event_count,
        "same_file_only_caller_event_count": same_file_only_event_count,
        "caller_candidate_file_count": len(candidate_paths),
    }
    if dict(audit) != expected_audit:
        raise VanillaEventSourceIndexError(
            "source_index.audit does not match indexed rows"
        )
    return deepcopy(dict(root))


def load_vanilla_event_source_index(
    path: str | Path | None = None,
) -> dict[str, object]:
    """Load a local override or the package's frozen exact-build dataset."""
    if path is None:
        resource = resources.files(__package__).joinpath(SOURCE_INDEX_RESOURCE)
        payload = resource.read_bytes()
    else:
        payload = Path(path).read_bytes()
    try:
        document = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise VanillaEventSourceIndexError(
            f"source index is not valid UTF-8 JSON: {exc}"
        ) from exc
    return validate_vanilla_event_source_index(document)


def query_vanilla_event_source_v1(
    event_definition_key: str,
    *,
    source_index: Mapping[str, object] | None = None,
) -> dict[str, object]:
    """Return one detached source row without claiming a proven call edge."""
    document = (
        load_vanilla_event_source_index()
        if source_index is None
        else validate_vanilla_event_source_index(source_index)
    )
    events = _require_mapping(document["events"], path="source_index.events")
    event = events.get(event_definition_key)
    return {
        "schema": SOURCE_INDEX_SCHEMA,
        "schema_version": SOURCE_INDEX_SCHEMA_VERSION,
        "status": "available" if event is not None else "unavailable",
        "event_definition_key": event_definition_key,
        "ck3_build": EXACT_CK3_BUILD,
        "ck3_exe_sha256": EXACT_CK3_EXE_SHA256,
        "dataset_sha256": document["dataset_sha256"],
        "source": deepcopy(event) if event is not None else None,
        "unavailable_reason": (
            None if event is not None else "event_definition_key_not_indexed"
        ),
    }


__all__ = [
    "SOURCE_INDEX_RESOURCE",
    "SOURCE_INDEX_SCHEMA",
    "SOURCE_INDEX_SCHEMA_VERSION",
    "VanillaEventSourceIndexError",
    "compute_source_index_dataset_sha256",
    "load_vanilla_event_source_index",
    "query_vanilla_event_source_v1",
    "validate_vanilla_event_source_index",
]
