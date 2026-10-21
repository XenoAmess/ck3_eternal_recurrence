"""One registered retrieval of source-bound H and artifact-pair observations."""
from __future__ import annotations
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
from typing import Never, get_args
import unittest

REPO=Path(os.environ.get("XAR_E02_REPO",str(Path(__file__).resolve().parents[3]))).resolve()
CANDIDATE=Path(os.environ.get("XAR_E02_H_CANDIDATE_ROOT",str(REPO))).resolve()
DOCUMENT="promo/ck3_faith_and_power/episode02/docs/knowledge/h-common-mother-arms-hof-ghw-observed.json"
sys.path.insert(0,str(REPO/"ck3_autonomous_player/src"))
if CANDIDATE!=REPO:
    name="xar_autoplayer.holy_site_episode02_research"
    spec=importlib.util.spec_from_file_location(name,CANDIDATE/"ck3_autonomous_player/src/xar_autoplayer/holy_site_episode02_research.py")
    if spec is None or spec.loader is None:raise ValueError("H candidate module unavailable")
    module=importlib.util.module_from_spec(spec)
    sys.modules[name]=module
    spec.loader.exec_module(module)

from mcp import Client,ClientSession
from xar_autoplayer.bridge.mcp_server import create_server
from xar_autoplayer.holy_site_planning_knowledge import HolySitePlanningAction


def obj(value: object) -> dict[str,object]:
    if not isinstance(value,dict):raise ValueError("Expected object")
    out: dict[str,object]={}
    for key,item in value.items():
        if not isinstance(key,str):raise ValueError("Expected string key")
        out[key]=item
    return out


def array(value: object) -> list[object]:
    if not isinstance(value,list):raise ValueError("Expected array")
    return list(value)


def document(relative: str) -> Path:
    path=CANDIDATE/relative
    return path if path.is_file() else REPO/relative


class NoGameDriver:
    def __init__(self) -> None:self.calls: list[str]=[]
    def refuse(self,name: str) -> Never:
        self.calls.append(name);raise AssertionError("Historical knowledge accessed game: "+name)
    def capabilities(self) -> object:return self.refuse("capabilities")
    def take_snapshot(self) -> object:return self.refuse("take_snapshot")
    def take_snapshot_without_native_command_history(self) -> object:return self.refuse("take_snapshot_without_native_command_history")
    def execute_step(self,*args: object,**kwargs: object) -> object:return self.refuse("execute_step")
    def wait_for_change(self,*args: object,**kwargs: object) -> object:return self.refuse("wait_for_change")


class HFinalKnowledgeMcpTest(unittest.IsolatedAsyncioTestCase):
    async def test_registered_h_history_is_retrievable_without_permission_upgrade(self) -> None:
        # Product preparation is not a passing final source qualification.
        raw=document(DOCUMENT).read_bytes()
        decoded: object=json.loads(raw)
        facts=obj(decoded)
        self.assertIs(facts["final_data_ready"],True,"Requires actual H2/H3 Native case sources")
        self.assertIsInstance(facts["h2_actual"],dict)
        self.assertIsInstance(facts["h3_actual"],dict)
        driver=NoGameDriver()
        async with Client(create_server(driver)) as client:
            self.assertIsInstance(client.session,ClientSession)
            reply=await client.session.call_tool("ck3_query_holy_site_planning_knowledge_v1",{"action":"promote"})
        self.assertFalse(reply.is_error)
        output=obj(reply.structured_content)
        research=obj(obj(output["knowledge"])["episode02_research"])
        topics=obj(research["topics"])
        self.assertEqual(set(topics),{"artifacts","site_effects_and_cache","mecca","head_of_faith","pilgrimage","great_holy_war"})
        self.assertEqual(set(get_args(HolySitePlanningAction)),{"adopt","create","promote","demote","abandon","enshrine_relic","remove_relic"})
        head=obj(topics["head_of_faith"])
        reference=obj(head["historical_h_reference"])
        self.assertEqual(reference,obj(facts["mcp_summary"]))
        self.assertEqual(reference["source_document"],DOCUMENT)
        self.assertEqual(reference["analysis_status"],"historical_h_source_closed")
        self.assertEqual(reference["historical_machine_id"],"4-8e1c2f1861")
        self.assertIn(DOCUMENT,array(head["documents"]))
        self.assertIn(DOCUMENT,array(obj(topics["great_holy_war"])["documents"]))
        art=obj(topics["artifacts"])
        self.assertIn(DOCUMENT,array(art["documents"]))
        ar=obj(art["artifact_pair_reference"])
        self.assertEqual(ar,obj(facts["artifact_pair_reference"]))
        self.assertIs(ar["action_ready"],False)
        self.assertIs(ar["ordinary_auto_consumes"],False)
        pair=obj(facts["artifact_pair"])
        self.assertEqual([obj(v)["raw_decimal_unchanged"] for v in array(pair["actors"])],["104000","129000"])
        self.assertEqual(pair["enshrine_breakdown_mecca_percent"],[4,8])
        self.assertEqual(pair["site_cached_rarity"],[4,8])
        for flag in ("refresh_time_known","world_effects_applied_observed","site_attribution_observed","total_payment_observed"):
            self.assertIs(pair[flag],False)
            self.assertIs(ar[flag],False)
        self.assertEqual(reference["ordinary_hof_quote"],{"piety":300,"gold":225})
        self.assertEqual(reference["ordinary_fresh_native_full10_quotes"],2)
        self.assertEqual(reference["promoted_hof_display_quote"],{"piety":200,"gold":150})
        self.assertEqual(reference["promoted_hof_quote_evidence"],"display_only")
        self.assertIsNone(reference["promoted_hof_native_full10"])
        self.assertIsNone(reference["promoted_hof_native_can_confirm"])
        self.assertIs(reference["four_native_hof_quotes_complete"],False)
        self.assertIs(reference["actual_hof_fee_savings_observed"],False)
        h1=obj(facts["h1_same_mother_comparison"])
        ordinary=obj(h1["ordinary"])
        vector=array(ordinary["full10_native_quote"])
        self.assertEqual(vector,[0,0,30000000,0,0,0,0,22500000,0,0])
        self.assertTrue(all(type(value) is int for value in vector))
        self.assertIs(ordinary["counts_are_realm_controlled_qualifying_counts"],False)
        self.assertIs(obj(ordinary["execution"])["business_pass"],False)
        major=obj(h1["major"])
        self.assertIs(major["promotion_observed"],True)
        self.assertEqual(major["hof_named_parameter_count"],3)
        self.assertEqual(major["hof_native_terms_unavailable_reason"],"selected_terms_nonempty_parameters_not_yet_qualified")
        self.assertIsNone(major["hof_full10_native_quote"])
        self.assertIsNone(major["hof_native_can_confirm"])
        self.assertIs(obj(major["execution"])["business_pass"],False)
        self.assertEqual(obj(facts["h2_independent_parent_plan"])["parent_sha256"],"de0f97b142ea88f13797d2f025380a52c5bab396b3d4986b8be6bf3ef653cc07")
        for key in ("h2_actual_document","h3_actual_document"):
            self.assertEqual(reference[key],DOCUMENT)
        h2=obj(facts["h2_actual"])
        self.assertEqual(h2["confirm_dispatch_attempts"],1)
        self.assertEqual(obj(h2["head_after"])["faith_religious_head_holder_character_id"],65865)
        self.assertEqual(obj(h2["head_after"])["faith_religious_head_title_id"],18373)
        self.assertIsNone(obj(h2["head_before"])["faith_religious_head_holder_character_id"])
        self.assertEqual(obj(h2["head_after"])["actor_rite_head_character_id"],31254)
        self.assertEqual(h2["wallet_delta_raw"],{"gold":-22500000,"piety":-30000000})
        self.assertIs(h2["quote_settlement_resource_index_join_verified"],False)
        self.assertIs(h2["h2_business_pass"],True)
        self.assertIs(h2["aggregate_business_pass"],False)
        self.assertIs(h2["whole_product_acceptance_credit"],False)
        self.assertEqual(obj(h2["event_policy"])["status"],"DRAINED")
        self.assertEqual(obj(h2["event_policy"])["events"],[])
        h3=obj(facts["h3_actual"])
        self.assertEqual(h3["capture_epochs"],[82387,84327])
        fields=array(obj(h3["variables"])["fields"])
        self.assertEqual(len(fields),4)
        for field in fields:
            value=obj(field)
            self.assertIs(value["read_available"],True)
            self.assertIs(value["present"],False)
            self.assertIsNone(value["numeric_value_raw"])
            self.assertIsNone(value["expiry_date_raw"])
            self.assertEqual(value["remaining_raw"],-1)
        self.assertEqual(obj(h3["object_links"])["war"],"absent")
        self.assertEqual(obj(h3["actual_launch_row"])["matching_row_count"],0)
        self.assertIsNone(h3["current_permitted"])
        for flag in ("missing_variable_is_false","no_ghw_is_world_peace","calendar_countdown_qualified","target_legality_observed","director_slot25_complete","action_ready","ordinary_auto_consumes"):
            self.assertIs(h3[flag],False)
        self.assertEqual(h3["launch_confirm_submissions"],0)
        self.assertEqual(h3["war_commands_submitted"],0)
        self.assertIsNone(obj(facts["scene_closure"])["normal_close"])
        for record in (facts,research,reference):
            for key in ("state_observed","action_ready","ordinary_auto_consumes","historical_evidence_is_current_state"):
                self.assertIs(record[key],False)
            self.assertIsNone(record["native_legality"])
        self.assertIsNone(output["native_legality"])
        self.assertIs(output["action_ready"],False)
        self.assertEqual(driver.calls,[])
        self.assertEqual(json.loads(json.dumps(facts,ensure_ascii=False)),facts)
        guide=document("docs/ck3-native-ai/faith-and-power-episode02-agent-reference-12004.md").read_text(encoding="utf-8-sig")
        self.assertIn("h-common-mother-arms-hof-ghw-observed.json",guide)
        print("H_FINAL_KNOWLEDGE_MCP_ACTUAL="+json.dumps({"registered_mcp_calls":1,"game_driver_calls":driver.calls,"source_document_sha256":hashlib.sha256(raw).hexdigest(),"H1_GUI_does_not_grant_Native":True,"ordinary_auto_consumption_proven":False},sort_keys=True))


if __name__=="__main__":unittest.main(verbosity=2)
