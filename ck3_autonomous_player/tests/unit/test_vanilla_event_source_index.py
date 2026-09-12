from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[3]
AUTOPLAYER_ROOT = ROOT / "ck3_autonomous_player"
sys.path.insert(0, str(AUTOPLAYER_ROOT / "src"))
sys.path.insert(0, str(ROOT))

from tools.gen_vanilla_event_source_index import (  # noqa: E402
    DEFAULT_OUTPUT,
    SourceIndexGenerationError,
    build_source_index,
    render_source_index,
    validate_exact_game_dir,
)
from xar_autoplayer.vanilla_events import (  # noqa: E402
    DEFAULT_VANILLA_EVENT_ANALYSIS,
    DEFAULT_VANILLA_EVENT_TIMELINE_CONTRACTS,
    EXACT_CK3_BUILD,
    EXACT_CK3_EXE_SHA256,
)
from xar_autoplayer.vanilla_events.source_index import (  # noqa: E402
    VanillaEventSourceIndexError,
    compute_source_index_dataset_sha256,
    load_vanilla_event_source_index,
    query_vanilla_event_source_provenance_v1,
    query_vanilla_event_source_v1,
    validate_vanilla_event_source_index,
)


GAME_DIR = ROOT.parent / "Crusader Kings III"


def test_frozen_index_covers_unique_exact_build_definitions_and_candidates() -> None:
    source_index = load_vanilla_event_source_index()
    audit = source_index["audit"]

    assert source_index["ck3_build"] == EXACT_CK3_BUILD
    assert source_index["ck3_exe_sha256"] == EXACT_CK3_EXE_SHA256
    assert source_index["dataset_sha256"] == (
        compute_source_index_dataset_sha256(source_index)
    )
    assert set(source_index["events"]) == set(
        DEFAULT_VANILLA_EVENT_TIMELINE_CONTRACTS
    )
    assert audit == {
        "registered_event_count": 188,
        "unique_definition_count": 188,
        "definition_file_count": 74,
        "missing_definition_count": 0,
        "ambiguous_definition_count": 0,
        "namespace_mismatch_count": 0,
        "caller_candidate_reference_count": 528,
        "external_caller_event_count": 153,
        "same_file_only_caller_event_count": 35,
        "caller_candidate_file_count": 82,
    }
    for event_key, row in source_index["events"].items():
        assert row["namespace"] == event_key.rsplit(".", 1)[0]
        assert row["definition"]["relative_path"].startswith("events/")
        assert row["caller_candidates"]
        assert all(
            candidate["kind"] == "exact-token-lexical-candidate"
            for candidate in row["caller_candidates"]
        )


def test_generator_matches_frozen_bytes_and_check_mode() -> None:
    generated = build_source_index(GAME_DIR)

    assert render_source_index(generated) == DEFAULT_OUTPUT.read_bytes()
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools" / "gen_vanilla_event_source_index.py"),
            "--game-dir",
            str(GAME_DIR),
            "--check",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "SOURCE INDEX CHECK: GREEN" in result.stdout


def test_analysis_source_hashes_are_compatible_with_definition_index() -> None:
    source_index = load_vanilla_event_source_index()
    source_backed = {
        event_key: analysis["source_sha256"]
        for event_key, analysis in DEFAULT_VANILLA_EVENT_ANALYSIS.items()
        if "source_sha256" in analysis
    }

    # The original migration audit contained 79 source-backed analyses. Keep
    # that floor while allowing subsequent portable migrations to add more.
    assert len(source_backed) >= 79
    definition_compatible_count = 0
    supporting_source_only = set()
    observed_hashes = {}
    for event_key, source_hashes in source_backed.items():
        for relative_path, expected_sha256 in source_hashes.items():
            source_path = GAME_DIR / "game" / relative_path
            assert source_path.is_file()
            observed_sha256 = observed_hashes.get(source_path)
            if observed_sha256 is None:
                observed_sha256 = (
                    hashlib.sha256(source_path.read_bytes()).hexdigest().upper()
                )
                observed_hashes[source_path] = observed_sha256
            assert observed_sha256 == expected_sha256
        definition = source_index["events"][event_key]["definition"]
        relative_path = definition["relative_path"]
        if relative_path not in source_hashes:
            supporting_source_only.add(event_key)
            continue
        definition_compatible_count += 1
        assert source_hashes[relative_path] == definition["file_sha256"]

    assert definition_compatible_count >= 79
    assert supporting_source_only == set()


def test_index_contains_no_absolute_source_paths() -> None:
    source_index = load_vanilla_event_source_index()
    for row in source_index["events"].values():
        records = [row["definition"], *row["caller_candidates"]]
        for record in records:
            relative_path = record["relative_path"]
            assert not Path(relative_path).is_absolute()
            assert "\\" not in relative_path
            assert ".." not in relative_path.split("/")
            assert "Crusader Kings III" not in relative_path


def test_query_is_detached_and_marks_references_as_candidates() -> None:
    response = query_vanilla_event_source_v1("health.1001")

    assert response["status"] == "available"
    assert response["source"]["caller_candidates"]
    assert all(
        candidate["kind"] == "exact-token-lexical-candidate"
        for candidate in response["source"]["caller_candidates"]
    )
    response["source"]["definition"]["line"] = 0
    assert query_vanilla_event_source_v1("health.1001")["source"][
        "definition"
    ]["line"] > 0

    unavailable = query_vanilla_event_source_v1("not_registered.1")
    assert unavailable["status"] == "unavailable"
    assert unavailable["source"] is None
    assert unavailable["unavailable_reason"] == "event_definition_key_not_indexed"
    json.dumps(unavailable, allow_nan=False)


def test_portable_provenance_query_is_schema_valid_and_typed() -> None:
    from jsonschema import Draft202012Validator

    schema = json.loads(
        (
            AUTOPLAYER_ROOT
            / "schemas"
            / "vanilla-event-source-provenance-v1.schema.json"
        ).read_text(encoding="utf-8")
    )
    validator = Draft202012Validator(schema)
    response = query_vanilla_event_source_provenance_v1(
        "health.1001",
        EXACT_CK3_BUILD,
    )

    validator.validate(response)
    assert response["status"] == "available"
    assert response["namespace"] == "health"
    assert response["definition"]["relative_path"].startswith("events/")
    assert response["caller_candidates"]
    assert response["caller_candidates_are_lexical_only"] is True
    assert response["caller_candidates_review_status"] == (
        "not_manually_reviewed_as_call_edges"
    )
    assert all(
        row["kind"] == "exact-token-lexical-candidate"
        for row in response["caller_candidates"]
    )
    assert all(
        not Path(row["relative_path"]).is_absolute()
        for row in [response["definition"], *response["caller_candidates"]]
    )

    for unavailable in (
        query_vanilla_event_source_provenance_v1("missing.1"),
        query_vanilla_event_source_provenance_v1("", EXACT_CK3_BUILD),
        query_vanilla_event_source_provenance_v1(
            "health.1001", "1.19.0.5"
        ),
    ):
        validator.validate(unavailable)
        assert unavailable["status"] == "unavailable"


def test_validation_rejects_tampering_and_absolute_paths() -> None:
    source_index = load_vanilla_event_source_index()
    tampered = deepcopy(source_index)
    tampered["events"]["health.1001"]["definition"]["line"] += 1
    with pytest.raises(VanillaEventSourceIndexError, match="dataset SHA-256"):
        validate_vanilla_event_source_index(tampered)

    absolute = deepcopy(source_index)
    absolute["events"]["health.1001"]["definition"]["relative_path"] = (
        "Z:/game/events/health_events.txt"
    )
    absolute["dataset_sha256"] = compute_source_index_dataset_sha256(absolute)
    with pytest.raises(VanillaEventSourceIndexError, match="remain relative"):
        validate_vanilla_event_source_index(absolute)


def test_generator_rejects_missing_or_wrong_executable(tmp_path: Path) -> None:
    with pytest.raises(SourceIndexGenerationError, match="missing frozen"):
        validate_exact_game_dir(tmp_path)

    executable = tmp_path / "binaries" / "ck3.exe"
    executable.parent.mkdir(parents=True)
    executable.write_bytes(b"not the frozen executable")
    with pytest.raises(SourceIndexGenerationError, match="unexpected ck3.exe"):
        validate_exact_game_dir(tmp_path)
