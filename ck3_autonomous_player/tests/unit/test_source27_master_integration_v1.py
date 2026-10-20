"""Integration contracts."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, replace
import gzip
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from xar_autoplayer import ordinary_sway_schedule_v1 as schedule
from xar_autoplayer import strategy, sway_formal_consumer as formal
from xar_autoplayer.bridge.driver import BridgeUnavailableError
from xar_autoplayer.bridge import native_loaded_provider_origin_io_v1 as origin_io
from xar_autoplayer.bridge import service
from xar_autoplayer.bridge.player_heir_projection_service_contract_v1 import PROJECTION
from xar_autoplayer.bridge.version_identity import CK3_12004
from xar_autoplayer.reused_sway_opportunity_v1 import (
    fresh_empty_sway_slot_after_reuse_v1, reused_sway_observation_gap_v1,
)
from xar_autoplayer.war_reinforcement_tradeoff_v1 import observe_war_spending_priority_v1
import test_campaign_root_context_v1_bridge as campaign
import test_player_heir_candidate_component_v1 as heir
import test_player_heir_fixed_dynasty_projection_v1 as projection
import test_nonleading_siege_priority_v1 as siege

REPO = Path(__file__).resolve().parents[3]
EVIDENCE = REPO / "docs/ck3-native-ai/evidence"
DATE = 53274960


def sway_case():
    ledger = json.loads((EVIDENCE / "m6-sway-closed-ledger-2026-10-20.json").read_bytes())
    quote = {"schema": "active-scheme-sway-private-read-v1", "date_raw": DATE,
        "actor_character_id": 40526, "target_character_id": 34973,
        "active_scheme_count": 0, "active_sway_instances": [], "matching_sway_active": False,
        "native_complete_can_send": True, "native_legal_now": True,
        "exact_ck3_build": CK3_12004.game_version, "exe_sha256": CK3_12004.executable_sha256}
    return ledger, quote


def test_reuse_consumers():
    ledger, quote = sway_case()
    before = deepcopy(ledger)
    frame = {"snapshot_id": "synthetic:10", "revision": 20, "native_revision": 10,
        "date_raw": DATE, "paused": True, "map_ready": True,
        "played_character": {"character_id": 40526, "alive": True},
        "active_context": {"active_event": None, "pending_character_interaction": None}}
    root = {"status": "available", "player_character_id": 40526, "player_character_alive": True,
        "snapshot_revision": 10, "date_raw": DATE, "direct_landed_vassal_character_ids": [34973, 35899]}
    state = json.loads((EVIDENCE / "m6-sway-closed-schedule-2026-10-20.json").read_bytes())
    state["frontier_membership"] = [34973, 35899]
    job = schedule.plan_ordinary_sway_schedule_v1(frame, selected_step="life-advance",
        root=root, ledger=ledger, state=state)
    assert job["target_character_id"] == 35899
    followup = formal._same_target_followup(ledger["resolved"], quote)
    assert followup["decision"] == "repeat_selected_target"
    assert followup["previous_instance_terminal_observed"] is False
    assert ledger == before


@pytest.mark.parametrize("change", [
    {"active_scheme_count": True}, {"active_scheme_count": None},
    {"active_sway_instances": None}, {"active_sway_instances": [{}]},
    {"native_legal_now": False}, {"matching_sway_active": True},
])
def test_reuse_requires_legal_empty_slot(change):
    ledger, quote = sway_case()
    assert fresh_empty_sway_slot_after_reuse_v1(ledger["resolved"], {**quote, **change}) is None


def test_reuse_rejects_float_identity():
    ledger, _ = sway_case()
    native = ledger["resolved"]["latest_instance_observation"]["native_observation"]
    native["scheme_instance_generation"] = float(native["scheme_instance_generation"])
    assert reused_sway_observation_gap_v1(
        ledger["resolved"], actor_character_id=40526, date_raw=DATE) is None


class ProjectionDriver(campaign._ServiceDriver):
    def __init__(self, mutate=None, include=True):
        super().__init__()
        self.mutate, self.include = mutate, include

    def take_snapshot(self):
        value = super().take_snapshot()
        value["diagnostics"]["hello"].update(game_version=CK3_12004.game_version,
            expected_ck3_version=CK3_12004.game_version, expected_ck3_sha256=CK3_12004.executable_sha256)
        return value

    def execute_step(self, step, *, expected_revision=None):
        value = super().execute_step(step, expected_revision=expected_revision)
        root = heir.native_result()["campaign_root_context"]
        value["campaign_root_context"] = root
        for field in set(value) & set(root):
            value[field] = deepcopy(root[field])
        value["backend_id"] = CK3_12004.backend_id("campaign-root-context-v1")
        case = projection.fixture()
        core = replace(case["current_core"], date_raw=root["date_raw"],
            played_character_id=root["player_character_id"])
        observation = replace(case["captured"].observation, actor_character_id=core.played_character_id,
            before=core, after=core, candidate_character_id=root["player_heir_candidate_v1"]["observation"]["candidate_character_id"])
        binding = replace(case["current"], date_raw=core.date_raw, actor_character_id=core.played_character_id)
        case.update(current=binding, current_core=core,
            captured=replace(case["captured"], binding=binding, observation=observation))
        from xar_autoplayer.player_heir_fixed_dynasty_projection_v1 import project_fixed_dynasty_candidate_v1
        payload = asdict(project_fixed_dynasty_candidate_v1(**case))
        payload.update(machine_id="synthetic-service-fixture",
            game_identity={"pid": 123, "creation_date": "synthetic-exact-birth", "executable": "synthetic/ck3.exe"},
            native_provider_sha256="a"*64, owner_source_epoch="b"*64,
            query_id="synthetic-query", native_query_sequence=value["query_sequence"],
            capture_epoch_basis="original_root_query_sequence",
            **{field: value[field] for field in ("queried_snapshot_id", "queried_revision", "queried_native_revision")})
        if self.include:
            value[PROJECTION] = json.loads(json.dumps(payload))
        if self.mutate:
            self.mutate(value)
        return value


def test_service_projection_roundtrip():
    value = service.GameplayBridgeService(ProjectionDriver()).query_campaign_root_context_v1(
        expected_revision=campaign.PUBLIC_REVISION)
    assert value[PROJECTION]["status"] == "positive_witness"
    legacy = service.GameplayBridgeService(ProjectionDriver(include=False)).query_campaign_root_context_v1(
        expected_revision=campaign.PUBLIC_REVISION)
    assert PROJECTION not in legacy


@pytest.mark.parametrize("mutate", [
    lambda v: v[PROJECTION].update(k=True),
    lambda v: v[PROJECTION].pop("native_provider_sha256"),
    lambda v: v["campaign_root_context"].pop("player_heir_candidate_v1"),
    lambda v: v.update(foreign_extra=True),
])
def test_service_rejects_bad_optional_projection(mutate):
    with pytest.raises(BridgeUnavailableError):
        service.GameplayBridgeService(ProjectionDriver(mutate)).query_campaign_root_context_v1(
            expected_revision=campaign.PUBLIC_REVISION)


def test_nonleading_strategy_and_cash():
    path = REPO / "ck3_autonomous_player/tests/fixtures/portable_actual_695.json.gz"
    case = siege.synthetic(json.loads(gzip.decompress(path.read_bytes())))
    plan = siege.assessment(strategy, case)
    assert plan is not None
    priority = observe_war_spending_priority_v1(case["snapshot"])
    assert priority["nonleading_realm_siege_construction_deferred_v1"] is True


def test_startup_recv_budget():
    transport = object.__new__(origin_io.OriginKernelIOV1)
    transport.timeout, transport.startup_timeout, transport.rx = 1.0, 4.0, {}
    transport.api = SimpleNamespace(_ok=lambda *args: None)
    transport._peek = lambda *args: None
    for startup, ticks in ((False, [0.0, 2.0]), (True, [0.0, 2.0, 5.0])):
        with patch.object(origin_io.time, "monotonic", side_effect=ticks), patch.object(origin_io.time, "sleep"):
            with pytest.raises(TimeoutError):
                transport.recv(1, startup=startup)
    with pytest.raises(ValueError):
        transport.recv(1, startup=1)
