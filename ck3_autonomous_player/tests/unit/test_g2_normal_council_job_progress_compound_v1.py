"""ONE new registered ordinary job-progress compound; Root SOURCE_NOTRUN.

Existing native assignment DTOs are reused. Development task/progress changes
are explicit offline poststates, never new native or campaign qualification.
"""
import asyncio
from copy import deepcopy
import json
import os
from pathlib import Path
from unittest.mock import patch

from test_private_council_formal_consumer_v1 import (
    ActualCouncilDriver, OfflineChancellorDriver,
)
from xar_autoplayer.bridge.mcp_server import create_server
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.private_council_formal_consumer_v1 import (
    RECEIPT_STEP, SUBMIT_STEP, read_council_ledger,
)


class NormalCouncilJobDriver(ActualCouncilDriver):
    nonwar_only = False

    def __init__(self, state_dir):
        super().__init__(state_dir)
        self.role_queries = []
        self.last_queried_role = None
        self.candidate_character_id = 9909
        self.diplomacy = 7
        self.steward_improvement = False
        self.job = "develop"
        self.frozen = False
        self.current_raw = 325000

    def capabilities(self):
        return {"action_steps": ["life-advance", "query-army-strengths-v1"],
                "bridge_capabilities": []}

    def query_council_final_gates_private_v1(self, *, expected_revision, **arguments):
        role = arguments.get("position_key", "councillor_steward")
        if role == "councillor_chancellor":
            return OfflineChancellorDriver.query_council_final_gates_private_v1(
                self, expected_revision=expected_revision, **arguments)
        self.role_queries.append(role)
        self.last_queried_role = role
        return super().query_council_final_gates_private_v1(expected_revision=expected_revision)

    def execute_step(self, step, *, expected_revision):
        result = super().execute_step(step, expected_revision=expected_revision)
        root = result["campaign_root_context"]
        row = next(row for row in root["council"]["positions"]
                   if row["position_key"] == "councillor_steward")
        if self.job == "develop":
            row.update(task_key="task_develop_county", task_type="county",
                target={"kind": "province", "province_id": 2619}, frozen=self.frozen,
                progress={"kind": "value",
                    "current": {"raw": 250000 if self.phase == "post" else self.current_raw, "scale": 100000},
                    "maximum": {"raw": 10000000, "scale": 100000}})
        else:
            row.update(task_key="task_collect_taxes", task_type="general", target=None,
                frozen=False, progress={"kind": "infinite", "current": None, "maximum": None})
        return result


def test_registered_normal_council_job_progress_receipt_following_reset_and_priority(tmp_path):
    from mcp import Client

    baseline = {"policy": "normal-job-progress-fixture", "phase": "life_advance",
                "selected_step": "life-advance"}
    evidence = []

    async def call(client, name):
        result = await client.call_tool(name, {})
        assert not result.is_error, result.content
        return result.structured_content

    async def run():
        with patch("xar_autoplayer.bridge.service.choose_one_life_turn", return_value=baseline), \
                patch.object(GameplayBridgeService, "plan_nonwar_turn", side_effect=AssertionError("ordinary job context stays normal")), \
                patch.object(GameplayBridgeService, "auto_nonwar_turn", side_effect=AssertionError("ordinary job context stays normal")):
            driver = NormalCouncilJobDriver(tmp_path / "development-context")
            async with Client(create_server(driver)) as client:
                planned = await call(client, "ck3_plan_turn")
                assert planned["plan"]["selected_step"] == SUBMIT_STEP
                assert planned["plan"]["council_decision"]["skill_gain"] == 4
                pending = await call(client, "ck3_auto_turn")
                assert pending["result"]["stage"] == "receipt_pending"
                assert read_council_ledger(driver.state_dir)["applied"] is None
                driver.phase = "post"
                material = await call(client, "ck3_auto_turn")
                assert material["selected_step"] == RECEIPT_STEP
                applied = material["result"]
                assert applied["status"] == "applied"
                job = applied["independent_job_progress_observation"]
                assert job["task_key"] == "task_develop_county"
                assert job["remaining_progress"] == {"raw": 9750000, "scale": 100000}
                assert job["effect_attribution"] == "not_observed"
                assert (driver.submit_calls, driver.receipt_calls, driver.root_calls) == (1, 1, 1)

                driver.phase = "current"
                following = await call(client, "ck3_plan_turn")
                plan = following["plan"]
                assert plan["selected_step"] == "life-advance"
                consumed = plan["council_receipt_consumed"]
                assert consumed["next_turn_consumed"] is True
                observed = consumed["next_turn_job_progress_observation"]
                assert observed["following_comparison"]["status"] == "same_job"
                assert observed["following_comparison"]["progress_change"] == {"raw": 75000, "scale": 100000}
                jobs = {row["position_key"]: row for row in plan["council_job_progress_observations"]}
                assert jobs["councillor_steward"]["target"] == {"kind": "province", "province_id": 2619}
                assert jobs["councillor_steward"]["remaining_progress"] == {"raw": 9675000, "scale": 100000}
                assert jobs["councillor_chancellor"]["progress"] == {"kind": "infinite", "current": None, "maximum": None}
                assert "remaining_progress" not in jobs["councillor_chancellor"]
                assert "completion_date_raw" not in observed
                assert driver.root_calls == 2  # Existing independent following read only.

                driver.frozen = True
                driver.current_raw = 125000
                reset = (await call(client, "ck3_plan_turn"))["plan"]
                reset_job = reset["council_receipt_consumed"]["next_turn_job_progress_observation"]
                assert reset_job["frozen"] is True
                assert reset_job["following_comparison"]["progress_change"] == {"raw": -125000, "scale": 100000}
                assert reset["selected_step"] == "life-advance"
                assert reset["council_receipt_consumed"]["next_turn_consumed"] is True
                driver.job = "tax"
                changed = (await call(client, "ck3_plan_turn"))["plan"]
                changed_job = changed["council_receipt_consumed"]["next_turn_job_progress_observation"]
                assert changed_job["following_comparison"]["status"] == "job_changed"
                assert "progress_change" not in changed_job["following_comparison"]
                assert changed_job["progress"] == {"kind": "infinite", "current": None, "maximum": None}
                assert changed["selected_step"] == "life-advance"
                assert (driver.submit_calls, driver.receipt_calls) == (1, 1)
            evidence.append({"scene": "registered-normal-current-and-following-job-context",
                "native_assignment_receipt_reused": True, "new_native_qualification": False,
                "task_poststates": "explicit offline value/infinite/frozen/reset fixtures",
                "progress_delta_raw": 75000, "signed_reset_delta_raw": -125000,
                "task_change_has_no_delta": True, "effect_attribution": "not_observed",
                "assignment_submit_count": 1, "material_receipt_count": 1})

            urgent = NormalCouncilJobDriver(tmp_path / "urgent")
            with patch("xar_autoplayer.bridge.service.choose_one_life_turn", return_value={
                    **baseline, "phase": "native_war_army_strength_query",
                    "selected_step": "query-army-strengths-v1"}):
                async with Client(create_server(urgent)) as client:
                    plan = (await call(client, "ck3_plan_turn"))["plan"]
                    assert plan["selected_step"] == "query-army-strengths-v1"
                    assert "council_job_progress_observations" not in plan
            assert urgent.query_calls == urgent.root_calls == urgent.submit_calls == 0
            evidence.append({"scene": "urgent-war-priority", "extra_council_reads": 0})

    asyncio.run(run())
    output_path = os.environ.get("XAR_COUNCIL_JOB_PROGRESS_OUTPUT")
    if output_path:
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps({"scenes": evidence, "live": False,
            "m4_complete": False, "boundary": "registered ordinary consumer; explicit offline job poststates"},
            indent=2) + "\n", encoding="utf-8")
