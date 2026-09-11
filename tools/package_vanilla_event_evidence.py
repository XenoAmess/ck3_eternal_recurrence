"""Build or verify the portable vanilla-event evidence bundle.

Building imports the current reviewed event catalog. It reads new exact-hash
source files and observation artifacts from the local CK3/runtime trees, while
reusing an already packaged content-addressed blob when its historical source
path is no longer available at the reviewed hash. ``--check`` is intentionally
offline: it validates only the checked-in manifest and blobs, so a different
operator or machine needs no access to the original absolute paths.
"""

from __future__ import annotations

import argparse
from collections.abc import Mapping
import gzip
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import sys
from typing import Final


ROOT: Final = Path(__file__).resolve().parents[1]
PLAYER_SRC: Final = ROOT / "ck3_autonomous_player" / "src"
if str(PLAYER_SRC) not in sys.path:
    sys.path.insert(0, str(PLAYER_SRC))

from xar_autoplayer.vanilla_events.portable_evidence import (  # noqa: E402
    EVIDENCE_MANIFEST_SCHEMA,
    EVIDENCE_SCHEMA_VERSION,
    EvidenceBundleError,
    _media_type_for_path,
    _validate_payload_media_type,
    validate_portable_evidence_bundle_v1,
)
from xar_autoplayer.vanilla_events.registry import (  # noqa: E402
    EXACT_CK3_BUILD,
    EXACT_CK3_EXE_SHA256,
)
from xar_autoplayer.vanilla_events.source_index import (  # noqa: E402
    load_vanilla_event_source_index,
    validate_vanilla_event_source_index,
)


DEFAULT_OUTPUT: Final = (
    PLAYER_SRC / "xar_autoplayer" / "vanilla_events" / "portable_evidence"
)
_SHA256 = re.compile(r"^[0-9A-Fa-f]{64}$")
_READ_CHUNK_BYTES: Final = 64 * 1024


class EvidencePackagingError(ValueError):
    """Raised when referenced local evidence does not match reviewed metadata."""


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(_READ_CHUNK_BYTES):
            digest.update(chunk)
    return digest.hexdigest()


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _deterministic_gzip(data: bytes) -> bytes:
    output = io.BytesIO()
    with gzip.GzipFile(
        filename="",
        mode="wb",
        compresslevel=9,
        fileobj=output,
        mtime=0,
    ) as stream:
        stream.write(data)
    return output.getvalue()


def _safe_relative_path(raw_path: object, *, context: str) -> PurePosixPath:
    if not isinstance(raw_path, str) or not raw_path:
        raise EvidencePackagingError(f"{context} path must be a non-empty string")
    path = PurePosixPath(raw_path.replace("\\", "/"))
    if path.is_absolute() or ".." in path.parts:
        raise EvidencePackagingError(f"{context} path is not safely relative")
    return path


def _expected_digest(raw_digest: object, *, context: str) -> str:
    if not isinstance(raw_digest, str) or _SHA256.fullmatch(raw_digest) is None:
        raise EvidencePackagingError(f"{context} SHA-256 is invalid")
    return raw_digest.lower()


def _candidate_game_roots() -> list[Path]:
    candidates: list[Path] = []
    configured = os.environ.get("XAR_CK3_GAME_ROOT")
    if configured:
        candidates.append(Path(configured))
    candidates.extend(
        (
            ROOT / "Crusader Kings III",
            ROOT.parent / "Crusader Kings III",
            Path(r"Z:\SteamLibrary\steamapps\common\Crusader Kings III"),
        )
    )
    return candidates


def _candidate_runtime_roots() -> list[Path]:
    candidates: list[Path] = []
    configured = os.environ.get("XAR_CK3_RUNTIME_ROOT")
    if configured:
        candidates.append(Path(configured))
    candidates.extend((ROOT / "_runtime", ROOT.parent / "_runtime"))
    return candidates


def _find_root(
    explicit: Path | None,
    candidates: list[Path],
    *,
    marker: PurePosixPath,
    label: str,
) -> Path:
    search = [explicit] if explicit is not None else candidates
    for candidate in search:
        assert candidate is not None
        root = candidate.expanduser().resolve()
        if (root / Path(*marker.parts)).is_file():
            return root
    raise EvidencePackagingError(f"unable to locate {label}")


def _load_current_catalog() -> tuple[
    Mapping[str, object], Mapping[str, object], Mapping[str, object]
]:
    from xar_autoplayer.vanilla_events import (  # noqa: PLC0415
        DEFAULT_VANILLA_EVENT_ANALYSIS,
        DEFAULT_VANILLA_EVENT_OBSERVATIONS,
    )

    return (
        DEFAULT_VANILLA_EVENT_ANALYSIS,
        DEFAULT_VANILLA_EVENT_OBSERVATIONS,
        load_vanilla_event_source_index(),
    )


def _source_references(
    analysis: Mapping[str, object],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for event_key in sorted(analysis):
        metadata = analysis[event_key]
        if not isinstance(metadata, Mapping):
            raise EvidencePackagingError(f"analysis[{event_key!r}] is not an object")
        source_hashes = metadata.get("source_sha256", {})
        if not isinstance(source_hashes, Mapping):
            raise EvidencePackagingError(
                f"analysis[{event_key!r}].source_sha256 is not an object"
            )
        for raw_path, raw_digest in source_hashes.items():
            path = _safe_relative_path(
                raw_path,
                context=f"analysis[{event_key!r}].source_sha256",
            ).as_posix()
            digest = _expected_digest(
                raw_digest,
                context=f"analysis[{event_key!r}].source_sha256[{path!r}]",
            )
            rows.append(
                {
                    "caller_candidate_resolution": None,
                    "digest": digest,
                    "event_key": event_key,
                    "logical_path": path,
                    "provenance": "manually-reviewed-analysis-source",
                    "role": "analysis_source",
                    "source_column": None,
                    "source_line": None,
                }
            )
    return rows


def _indexed_source_references(
    source_index: Mapping[str, object],
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    validated = validate_vanilla_event_source_index(source_index)
    events = validated["events"]
    assert isinstance(events, Mapping)
    definitions: list[dict[str, object]] = []
    candidates: list[dict[str, object]] = []
    for event_key, raw_event in events.items():
        assert isinstance(event_key, str)
        assert isinstance(raw_event, Mapping)
        resolution = raw_event["caller_candidate_resolution"]
        assert isinstance(resolution, str)
        definition = raw_event["definition"]
        assert isinstance(definition, Mapping)
        definitions.append(
            {
                "caller_candidate_resolution": None,
                "digest": _expected_digest(
                    definition["file_sha256"],
                    context=f"source_index.events[{event_key!r}].definition",
                ),
                "event_key": event_key,
                "logical_path": _safe_relative_path(
                    definition["relative_path"],
                    context=f"source_index.events[{event_key!r}].definition",
                ).as_posix(),
                "provenance": "generated-definition-index",
                "role": "event_definition",
                "source_column": None,
                "source_line": definition["line"],
            }
        )
        raw_candidates = raw_event["caller_candidates"]
        assert isinstance(raw_candidates, list)
        for index, candidate in enumerate(raw_candidates):
            assert isinstance(candidate, Mapping)
            candidates.append(
                {
                    "caller_candidate_resolution": resolution,
                    "digest": _expected_digest(
                        candidate["file_sha256"],
                        context=(
                            f"source_index.events[{event_key!r}]"
                            f".caller_candidates[{index}]"
                        ),
                    ),
                    "event_key": event_key,
                    "logical_path": _safe_relative_path(
                        candidate["relative_path"],
                        context=(
                            f"source_index.events[{event_key!r}]"
                            f".caller_candidates[{index}]"
                        ),
                    ).as_posix(),
                    "provenance": (
                        "lexical-caller-candidate-not-proven-runtime-caller"
                    ),
                    "role": "caller_candidate",
                    "source_column": candidate["column"],
                    "source_line": candidate["line"],
                }
            )
    return definitions, candidates


def _observation_references(
    observations: Mapping[str, object],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []

    def visit(event_key: str, value: object, *, context: str) -> None:
        if isinstance(value, Mapping):
            for raw_key, child in value.items():
                key = str(raw_key)
                is_artifact = key == "artifact" or key.endswith("_artifact")
                if is_artifact and isinstance(child, str):
                    digest_key = f"{key}_sha256"
                    if digest_key not in value:
                        raise EvidencePackagingError(
                            f"{context}.{key} has no {digest_key}"
                        )
                    path = _safe_relative_path(
                        child,
                        context=f"{context}.{key}",
                    ).as_posix()
                    if not path.startswith("_runtime/"):
                        raise EvidencePackagingError(
                            f"{context}.{key} is outside _runtime"
                        )
                    digest = _expected_digest(
                        value[digest_key],
                        context=f"{context}.{digest_key}",
                    )
                    rows.append(
                        {
                            "caller_candidate_resolution": None,
                            "digest": digest,
                            "event_key": event_key,
                            "logical_path": path,
                            "provenance": "captured-observation-artifact",
                            "role": key,
                            "source_column": None,
                            "source_line": None,
                        }
                    )
                visit(event_key, child, context=f"{context}.{key}")
        elif isinstance(value, (list, tuple)):
            for index, child in enumerate(value):
                visit(event_key, child, context=f"{context}[{index}]")

    for event_key in sorted(observations):
        visit(
            event_key,
            observations[event_key],
            context=f"observations[{event_key!r}]",
        )
    return rows


def _read_exact_payload(path: Path, digest: str, *, context: str) -> bytes:
    if not path.is_file() or path.is_symlink():
        raise EvidencePackagingError(f"{context} evidence file is unavailable")
    observed_digest = _sha256_file(path)
    if observed_digest != digest:
        raise EvidencePackagingError(
            f"{context} SHA-256 mismatch: expected {digest}, got {observed_digest}"
        )
    return path.read_bytes()


def _read_exact_or_packaged_payload(
    path: Path,
    digest: str,
    *,
    context: str,
    output_root: Path,
) -> bytes:
    """Read the live source, or reuse its already verified content-addressed blob.

    Runtime reports can be extended in place after an earlier observation was
    reviewed. Once the exact old bytes are stored under their SHA-256, a later
    bundle rebuild must not depend on that mutable path still having those
    bytes. New digests still require an exact external source.
    """

    try:
        return _read_exact_payload(path, digest, context=context)
    except EvidencePackagingError as source_error:
        blob_path = output_root / "blobs" / f"{digest}.gz"
        if not blob_path.is_file() or blob_path.is_symlink():
            raise source_error
        try:
            payload = gzip.decompress(blob_path.read_bytes())
        except (OSError, EOFError) as error:
            raise EvidencePackagingError(
                f"{context} packaged fallback is not valid gzip"
            ) from error
        if _sha256(payload) != digest:
            raise EvidencePackagingError(
                f"{context} packaged fallback SHA-256 mismatch"
            )
        return payload


def _event_reference(
    *,
    event_key: str,
    origin: str,
    role: str,
    logical_path: str,
    provenance: str,
    source_line: int | None,
    source_column: int | None,
    caller_candidate_resolution: str | None,
) -> dict[str, object]:
    return {
        "caller_candidate_resolution": caller_candidate_resolution,
        "event_definition_key": event_key,
        "logical_path": logical_path,
        "origin": origin,
        "provenance": provenance,
        "role": role,
        "source_column": source_column,
        "source_line": source_line,
    }


def build_bundle(
    *,
    analysis: Mapping[str, object],
    observations: Mapping[str, object],
    source_index: Mapping[str, object],
    game_root: Path,
    runtime_root: Path,
    output_root: Path = DEFAULT_OUTPUT,
) -> dict[str, object]:
    """Materialize all currently referenced and hash-pinned portable evidence."""
    game_root = game_root.resolve()
    runtime_root = runtime_root.resolve()
    output_root = output_root.resolve()
    executable = game_root / "binaries" / "ck3.exe"
    if not executable.is_file() or _sha256_file(executable).upper() != EXACT_CK3_EXE_SHA256:
        raise EvidencePackagingError("CK3 executable does not match exact build 1.19.0.6")

    payload_by_id: dict[str, bytes] = {}
    metadata_by_id: dict[str, dict[str, object]] = {}

    def add(
        *,
        event_key: str,
        kind: str,
        role: str,
        logical_path: str,
        expected_digest: str,
        source_path: Path,
        origin: str,
        provenance: str,
        source_line: int | None,
        source_column: int | None,
        caller_candidate_resolution: str | None,
    ) -> None:
        media_type = _media_type_for_path(logical_path)
        payload = _read_exact_or_packaged_payload(
            source_path,
            expected_digest,
            context=f"{event_key}:{role}:{logical_path}",
            output_root=output_root,
        )
        _validate_payload_media_type(payload, media_type)
        evidence_id = _sha256(payload)
        if evidence_id != expected_digest:
            raise EvidencePackagingError("evidence id does not match reviewed SHA-256")
        existing_payload = payload_by_id.get(evidence_id)
        if existing_payload is not None and existing_payload != payload:
            raise EvidencePackagingError("SHA-256 evidence collision")
        reference = _event_reference(
            event_key=event_key,
            origin=origin,
            role=role,
            logical_path=logical_path,
            provenance=provenance,
            source_line=source_line,
            source_column=source_column,
            caller_candidate_resolution=caller_candidate_resolution,
        )
        if evidence_id not in metadata_by_id:
            payload_by_id[evidence_id] = payload
            metadata_by_id[evidence_id] = {
                "kind": kind,
                "media_type": media_type,
                "references": [reference],
            }
            return
        metadata = metadata_by_id[evidence_id]
        if metadata["kind"] != kind or metadata["media_type"] != media_type:
            raise EvidencePackagingError(
                "one evidence payload has conflicting kind or media type"
            )
        references = metadata["references"]
        assert isinstance(references, list)
        if reference not in references:
            references.append(reference)

    analysis_source_rows = _source_references(analysis)
    definition_rows, candidate_rows = _indexed_source_references(source_index)
    source_rows = [*definition_rows, *candidate_rows, *analysis_source_rows]
    for row in source_rows:
        event_key = str(row["event_key"])
        role = str(row["role"])
        logical_path = str(row["logical_path"])
        digest = str(row["digest"])
        add(
            event_key=event_key,
            kind="source_definition",
            role=role,
            logical_path=logical_path,
            expected_digest=digest,
            source_path=game_root / "game" / Path(*PurePosixPath(logical_path).parts),
            origin="ck3_game",
            provenance=str(row["provenance"]),
            source_line=row["source_line"],  # type: ignore[arg-type]
            source_column=row["source_column"],  # type: ignore[arg-type]
            caller_candidate_resolution=row["caller_candidate_resolution"],  # type: ignore[arg-type]
        )
    observation_rows = _observation_references(observations)
    for row in observation_rows:
        event_key = str(row["event_key"])
        role = str(row["role"])
        logical_path = str(row["logical_path"])
        digest = str(row["digest"])
        relative = PurePosixPath(logical_path)
        runtime_relative = PurePosixPath(*relative.parts[1:])
        add(
            event_key=event_key,
            kind="observation_artifact",
            role=role,
            logical_path=logical_path,
            expected_digest=digest,
            source_path=runtime_root / Path(*runtime_relative.parts),
            origin="runtime",
            provenance=str(row["provenance"]),
            source_line=None,
            source_column=None,
            caller_candidate_resolution=None,
        )

    output_root.mkdir(parents=True, exist_ok=True)
    blob_root = output_root / "blobs"
    blob_root.mkdir(parents=True, exist_ok=True)
    entries: list[dict[str, object]] = []
    expected_blob_names: set[str] = set()
    for evidence_id in sorted(payload_by_id):
        payload = payload_by_id[evidence_id]
        compressed = _deterministic_gzip(payload)
        metadata = metadata_by_id[evidence_id]
        references = metadata["references"]
        assert isinstance(references, list)
        references.sort(
            key=lambda item: (
                item["event_definition_key"],
                item["origin"],
                item["provenance"],
                item["role"],
                item["logical_path"],
                item["source_line"] if item["source_line"] is not None else 0,
                item["source_column"] if item["source_column"] is not None else 0,
            )
        )
        blob_name = f"{evidence_id}.gz"
        expected_blob_names.add(blob_name)
        blob_path = blob_root / blob_name
        if not blob_path.is_file() or blob_path.read_bytes() != compressed:
            blob_path.write_bytes(compressed)
        entries.append(
            {
                "blob_bytes": len(compressed),
                "blob_path": f"blobs/{blob_name}",
                "blob_sha256": _sha256(compressed),
                "bytes": len(payload),
                "evidence_id": evidence_id,
                "kind": metadata["kind"],
                "media_type": metadata["media_type"],
                "references": references,
                "sha256": evidence_id,
            }
        )

    resolved_blob_root = blob_root.resolve()
    for stale in blob_root.glob("*.gz"):
        if stale.name not in expected_blob_names:
            resolved_stale = stale.resolve()
            if stale.is_symlink() or resolved_stale.parent != resolved_blob_root:
                raise EvidencePackagingError(
                    "refusing to remove an unsafe orphan evidence blob"
                )
            stale.unlink()
    canonical_references = [
        reference
        for entry in entries
        for reference in entry["references"]
    ]

    def reference_count(provenance: str) -> int:
        return sum(
            reference["provenance"] == provenance
            for reference in canonical_references
        )

    manifest: dict[str, object] = {
        "schema": EVIDENCE_MANIFEST_SCHEMA,
        "schema_version": EVIDENCE_SCHEMA_VERSION,
        "ck3_build": EXACT_CK3_BUILD,
        "ck3_exe_sha256": EXACT_CK3_EXE_SHA256,
        "compression": {
            "algorithm": "gzip",
            "filename": "",
            "mtime": 0,
        },
        "statistics": {
            "evidence": len(entries),
            "observation_artifacts": sum(
                entry["kind"] == "observation_artifact" for entry in entries
            ),
            # Count the canonical references retained on entries. Multiple
            # observations may intentionally cite the same event/artifact pair;
            # add() deduplicates that reference, so pre-dedup input row counts
            # would make the generated manifest fail its own validator.
            "references": len(canonical_references),
            "generated_definition_references": reference_count(
                "generated-definition-index"
            ),
            "lexical_caller_candidate_references": reference_count(
                "lexical-caller-candidate-not-proven-runtime-caller"
            ),
            "manually_reviewed_analysis_source_references": reference_count(
                "manually-reviewed-analysis-source"
            ),
            "observation_artifact_references": reference_count(
                "captured-observation-artifact"
            ),
            "source_definitions": sum(
                entry["kind"] == "source_definition" for entry in entries
            ),
        },
        "evidence": entries,
    }
    manifest_bytes = (
        json.dumps(
            manifest,
            ensure_ascii=False,
            allow_nan=False,
            indent=2,
            sort_keys=True,
        ).encode("utf-8")
        + b"\n"
    )
    manifest_path = output_root / "manifest_v1.json"
    if not manifest_path.is_file() or manifest_path.read_bytes() != manifest_bytes:
        manifest_path.write_bytes(manifest_bytes)
    return manifest


def _build_from_current_catalog(args: argparse.Namespace) -> dict[str, object]:
    analysis, observations, source_index = _load_current_catalog()
    game_root = _find_root(
        args.game_root,
        _candidate_game_roots(),
        marker=PurePosixPath("binaries/ck3.exe"),
        label="exact CK3 game root",
    )
    runtime_root = _find_root(
        args.runtime_root,
        _candidate_runtime_roots(),
        marker=PurePosixPath(
            "p2r374-active-boundary-continuation-live/"
            "natural-disaster-7031-red-report.json"
        ),
        label="CK3 observation runtime root",
    )
    return build_bundle(
        analysis=analysis,
        observations=observations,
        source_index=source_index,
        game_root=game_root,
        runtime_root=runtime_root,
        output_root=args.output,
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="validate the packaged manifest/blobs without external source paths",
    )
    parser.add_argument("--game-root", type=Path)
    parser.add_argument("--runtime-root", type=Path)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.check:
            result = validate_portable_evidence_bundle_v1(args.output)
            print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        else:
            manifest = _build_from_current_catalog(args)
            print(json.dumps(manifest["statistics"], sort_keys=True))
    except (EvidenceBundleError, EvidencePackagingError, OSError) as exc:
        print(f"portable evidence: RED: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
