from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import subprocess


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / (
    "docs/phase2-promo/"
    "incident-production-source-capture-no-launch-candidate-5c54014-2026-09-04.json"
)
EFFECT_PATTERN = re.compile(r"^[A-Za-z0-9_]+\s*=\s*\{$", re.MULTILINE)


def _load() -> dict[str, object]:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def _effect_count(path: Path) -> int:
    return len(EFFECT_PATTERN.findall(path.read_text(encoding="utf-8-sig")))


def _git_blob(commit: str, relative: str) -> bytes:
    completed = subprocess.run(
        ["git", "show", f"{commit}:{relative}"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    return completed.stdout


def test_candidate_pins_integrated_read_only_capture_and_real_grade_boundary() -> None:
    manifest = _load()
    assert manifest["kind"] == (
        "zg361_incident_production_source_capture_no_launch_candidate"
    )
    assert manifest["readiness"] == "static-ready-live-pending"
    assert manifest["live_gate_ready"] is False
    assert manifest["execution_authorized"] is False

    source = manifest["source"]
    assert source["canonical_base_commit"] == (
        "5c54014c7317bd2446bd342d7205cf00fe024dc9"
    )
    assert source["choreography_commit"].startswith("baaf048")
    assert source["capture_runner_commit"].startswith("55c23da")
    assert source["formal_runner_registry_modified_by_candidate"] is False
    assert source["production_files_modified_by_candidate"] == []
    base = source["canonical_base_commit"]
    for relative, expected in source["frozen_repo_files"].items():
        payload = _git_blob(base, relative)
        assert len(payload) == expected["bytes"]
        assert hashlib.sha256(payload).hexdigest().upper() == expected["sha256"]

    grade = manifest["fresh_seed_candidate"]["real_grade_condition"]
    assert grade == {
        "subject_character_id": 29037,
        "owner_character_id": 32904,
        "result_grade": 1,
        "absolute_grade": 1,
        "display_band": "3.25",
        "observed_from_provider": True,
        "fabricated_for_candidate": False,
    }
    assert manifest["fresh_seed_candidate"]["source_position"] == (
        "post_delivery_seed"
    )
    assert manifest["fresh_seed_candidate"]["target_event_currently_visible"] is False
    assert manifest["fresh_seed_candidate"]["target_event_reopen_allowed"] is False

    # Machine-local evidence is optional in CI, but when this frozen evidence
    # store is present the test rechecks both its bytes and the provider values
    # behind the real (not candidate-authored) 3.25 claim.
    seed = manifest["fresh_seed_candidate"]
    for key in (
        "contract",
        "checkpoint",
        "source_report",
        "source_evidence_index",
        "provider_probes",
    ):
        record = seed[key]
        path = Path(record["path"])
        if path.is_file():
            payload = path.read_bytes()
            assert len(payload) == record["bytes"]
            assert hashlib.sha256(payload).hexdigest().upper() == record["sha256"]
    provider_path = Path(seed["provider_probes"]["path"])
    if provider_path.is_file():
        provider = json.loads(provider_path.read_text(encoding="utf-8"))
        gate = provider["responses"]["b2_pip"]["response"]["gate"]
        assert provider["responses"]["b2_pip"]["response"]["player_character_id"] == 29037
        assert gate["owner_character_id"]["value"] == 32904
        assert gate["subject_character_id"]["value"] == 29037
        assert gate["result_grade"]["value"] == 1
        assert gate["absolute_grade"]["value"] == 1

    fixture = _git_blob(
        base,
        "tools/fixtures/zg361_phase2_seed_bootstrap/events/"
        "zga_phase2_seed_events.txt",
    ).decode("utf-8-sig")
    assert "var:zg361_result_grade = 1" in fixture
    assert "var:zg361_result_case_state = 3" in fixture
    assert "var:zg361_result_settlement_posted_serial = var:zg361_result_case_serial" in fixture
    assert "set_variable = { name = zg361_result_grade value = 1 }" not in fixture


def test_exact_command_is_frozen_but_blocked_and_capture_stays_read_only() -> None:
    manifest = _load()
    commands = manifest["commands"]
    preflight = commands["tested_no_launch_preflight"]
    live = commands["exact_live_ck3_command"]
    assert preflight["result"] == "GREEN"
    assert preflight["ck3_process_count_before"] == 0
    assert preflight["ck3_process_count_after"] == 0
    assert "--preflight" in preflight["argv"]
    assert live["status"] == "blocked_do_not_execute"
    assert "--preflight" not in live["argv"]
    assert "--phase2-incident-source-checkpoint-capture" in live["argv"]
    assert live["argv"].count("--artifacts-dir") == 1
    joined = " ".join(live["argv"]).lower()
    for forbidden in ("fixture", "console", "debug_mode", "select-event-option"):
        assert forbidden not in joined
    pipe = live["argv"][live["argv"].index("--bridge-pipe") + 1]
    assert re.fullmatch(
        r"\\\\\.\\pipe\\xar_ck3_bridge_zg361_[0-9a-f]{32}", pipe
    )
    assert manifest["reserved_live_attempt"] == {
        "attempt_id": "incident-production-source-capture-5c54014-20260904T081913Z",
        "path": (
            "Z:\\ck3_mod_rewrite_process_assets\\zg361\\"
            "incident-production-source-capture-5c54014-20260904T081913Z"
        ),
        "status": "absent",
        "started": False,
        "consumed": False,
    }

    capture = (ROOT / "tools/zg361_phase2_incident_source_capture_entry.py").read_text(
        encoding="utf-8-sig"
    )
    body = capture.split(
        "def wait_for_and_capture_incident_source_checkpoint(", 1
    )[1].split("\n\n__all__", 1)[0]
    assert '"real_zg361_50_wait_timeout"' in body
    assert '"state_advance_attempted": False' in body
    assert "select_event_option" not in body
    assert "execute_step" not in body
    behavior = manifest["capture_behavior"]
    assert behavior["poll_only"] is True
    assert behavior["state_advance_attempted"] is False
    assert behavior["action_ack_used_as_state_evidence"] is False
    assert behavior["current_seed_expected_terminal"] == (
        "real_zg361_50_wait_timeout"
    )


def test_incident_effect_family_respects_hard_boundary() -> None:
    manifest = _load()
    boundary = manifest["effect_file_boundary"]
    assert boundary["candidate_production_effect_files_added_or_modified"] == []
    assert boundary["over_20_exception"] is None
    assert boundary["selected_product_incident_family"]["max_effect_count"] == 10
    assert boundary["selected_product_incident_family"]["files_over_hard_principle_max"] == []

    effect_root = ROOT / "mod_zhongguo_style/common/scripted_effects"
    files = sorted(effect_root.glob("zg361_incident_platform_*_effects.txt"))
    counts = {path.name: _effect_count(path) for path in files}
    assert files
    assert all(1 <= value <= 20 for value in counts.values())
    recorded = boundary["canonical_incident_family_at_base"]
    assert recorded["file_count"] == 27
    assert recorded["min_effect_count"] == 1
    assert recorded["max_effect_count"] == 12
    assert {
        Path(item["path"]).name: item["effect_count"]
        for item in recorded["files_over_target_max"]
    } == {
        "zg361_incident_platform_z_apply_217_222_effects.txt": 11,
        "zg361_incident_platform_z_apply_223_228_effects.txt": 12,
    }
    assert recorded["files_over_hard_principle_max"] == []


def test_no_launch_attestation_never_claims_live_or_ack_evidence() -> None:
    manifest = _load()
    assert manifest["no_launch_attestation"] == {
        "ck3_started": False,
        "injector_started": False,
        "live_attempt_directory_created": False,
        "live_checkpoint_claimed": False,
        "schema2_registry_entry_claimed": False,
    }
    requirement = manifest["next_live_checkpoint_requirement"]
    assert requirement["required"] is True
    assert requirement["static_preflight_is_result_evidence"] is False
    assert requirement["command_ack_is_result_evidence"] is False
