from __future__ import annotations

import base64
import gzip
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[3]
PLAYER = ROOT / "ck3_autonomous_player"
SRC = PLAYER / "src"
sys.path.insert(0, str(SRC))

from xar_autoplayer.vanilla_events.portable_evidence import (  # noqa: E402
    MAX_EVIDENCE_READ_BYTES,
    query_vanilla_event_evidence_index_v1,
    read_vanilla_event_evidence_v1,
    validate_portable_evidence_bundle_v1,
)


BUNDLE = SRC / "xar_autoplayer" / "vanilla_events" / "portable_evidence"
MANIFEST = BUNDLE / "manifest_v1.json"
SCHEMAS = PLAYER / "schemas"


def _schema(name: str) -> dict[str, object]:
    result = json.loads((SCHEMAS / name).read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(result)
    return result


def _manifest() -> dict[str, object]:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def test_checked_in_bundle_is_complete_and_strictly_self_validating() -> None:
    result = validate_portable_evidence_bundle_v1()
    manifest = _manifest()

    assert result["status"] == "available"
    assert result["validated_evidence"] == 140
    assert result["statistics"] == {
        "evidence": 140,
        "observation_artifacts": 56,
        "references": 179,
        "source_definitions": 84,
    }
    assert result["manifest_sha256"] == hashlib.sha256(
        MANIFEST.read_bytes()
    ).hexdigest()
    Draft202012Validator(
        _schema("vanilla-event-portable-evidence-manifest-v1.schema.json")
    ).validate(manifest)
    assert len(list((BUNDLE / "blobs").glob("*.gz"))) == 140


def test_gzip_is_deterministic_and_contains_no_filename() -> None:
    manifest = _manifest()
    for entry in manifest["evidence"]:
        blob = (BUNDLE / entry["blob_path"]).read_bytes()
        assert blob[:3] == b"\x1f\x8b\x08"
        assert blob[3] & 0x08 == 0
        assert int.from_bytes(blob[4:8], "little") == 0
        payload = gzip.decompress(blob)
        assert hashlib.sha256(payload).hexdigest() == entry["evidence_id"]
        assert len(payload) == entry["bytes"]


def test_index_is_event_addressable_and_schema_valid() -> None:
    response = query_vanilla_event_evidence_index_v1("tgp_dynastic_cycle.0091")

    assert response["status"] == "available"
    assert response["unavailable_reason"] is None
    assert len(response["evidence"]) == 2
    assert {row["kind"] for row in response["evidence"]} == {
        "source_definition"
    }
    for row in response["evidence"]:
        assert row["evidence_id"] == row["sha256"]
        assert all(
            reference["event_definition_key"] == "tgp_dynastic_cycle.0091"
            for reference in row["references"]
        )
    Draft202012Validator(
        _schema("vanilla-event-evidence-index-v1.schema.json")
    ).validate(response)


def test_read_returns_verified_chunks_no_larger_than_64_kib() -> None:
    manifest = _manifest()
    entry = next(row for row in manifest["evidence"] if row["bytes"] > 131072)
    first = read_vanilla_event_evidence_v1(entry["evidence_id"])
    second = read_vanilla_event_evidence_v1(
        entry["evidence_id"], offset=MAX_EVIDENCE_READ_BYTES
    )

    assert first["status"] == "available"
    assert first["content_bytes"] == MAX_EVIDENCE_READ_BYTES
    assert len(base64.b64decode(first["content_base64"], validate=True)) == 65536
    assert first["eof"] is False
    assert second["status"] == "available"
    assert second["offset"] == MAX_EVIDENCE_READ_BYTES
    assert second["content_bytes"] <= MAX_EVIDENCE_READ_BYTES
    Draft202012Validator(
        _schema("vanilla-event-evidence-read-v1.schema.json")
    ).validate(first)


def test_index_and_read_fail_closed_with_typed_unavailable_rows(
    tmp_path: Path,
) -> None:
    missing = tmp_path / "missing-bundle"
    missing.mkdir()

    unknown_event = query_vanilla_event_evidence_index_v1("does.not.exist")
    wrong_build = query_vanilla_event_evidence_index_v1(
        ck3_build="1.19.0.5"
    )
    invalid_id = read_vanilla_event_evidence_v1("not-a-sha")
    oversized = read_vanilla_event_evidence_v1("0" * 64, max_bytes=65537)
    corrupt = read_vanilla_event_evidence_v1("0" * 64, bundle_root=missing)

    assert unknown_event["unavailable_reason"] == "event_definition_key_not_indexed"
    assert wrong_build["unavailable_reason"] == "unsupported_ck3_build"
    assert invalid_id["unavailable_reason"] == "invalid_evidence_id"
    assert oversized["unavailable_reason"] == "invalid_max_bytes"
    assert corrupt["unavailable_reason"] == "bundle_integrity_error"
    index_validator = Draft202012Validator(
        _schema("vanilla-event-evidence-index-v1.schema.json")
    )
    read_validator = Draft202012Validator(
        _schema("vanilla-event-evidence-read-v1.schema.json")
    )
    index_validator.validate(unknown_event)
    index_validator.validate(wrong_build)
    read_validator.validate(invalid_id)
    read_validator.validate(oversized)
    read_validator.validate(corrupt)


def test_offline_check_ignores_unavailable_external_roots() -> None:
    environment = dict(os.environ)
    environment["XAR_CK3_GAME_ROOT"] = str(ROOT / "does-not-exist" / "game")
    environment["XAR_CK3_RUNTIME_ROOT"] = str(
        ROOT / "does-not-exist" / "runtime"
    )
    completed = subprocess.run(
        [sys.executable, "tools/package_vanilla_event_evidence.py", "--check"],
        cwd=ROOT,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    result = json.loads(completed.stdout)
    assert result["status"] == "available"
    assert result["validated_evidence"] == 140
