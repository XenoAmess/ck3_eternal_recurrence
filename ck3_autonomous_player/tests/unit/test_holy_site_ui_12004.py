"""HolySite presentation admission/schema; no native game function executes."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"src"))
from xar_autoplayer.bridge.ingame_ui_contract import validate_ui_request,validate_ui_build_scope
from xar_autoplayer.bridge.version_identity import CK3_11906,CK3_12003,CK3_12004
from xar_autoplayer.bridge.mcp_server import create_server


class NoIoDriver:
    allow_private_holy_site_adoption_detail_query = True
    def capabilities(self):raise AssertionError("unexpected game capability query")
    def take_snapshot(self):raise AssertionError("unexpected game snapshot")


class HolySiteUiAdmissionTests(unittest.TestCase):
    def test_complete_unsigned_identity_and_exact_build(self):
        for full_id in (0,0x81000002,0xFFFFFFFE):
            for operation in ("open_holy_site", "open_holy_site_adoption"):
                validate_ui_request(operation,"holy_site",full_id,1)
                validate_ui_build_scope(CK3_12004,operation,"holy_site")
            validate_ui_request("confirm_site_adoption","holy_site_adoption",full_id,1)
            validate_ui_build_scope(CK3_12004,"confirm_site_adoption","holy_site_adoption")
        for bad in (True,-1,0xFFFFFFFF,"nadjaf",None):
            with self.subTest(bad=bad),self.assertRaises(ValueError):
                validate_ui_request("open_holy_site","holy_site",bad,1)
        for build in (CK3_11906,CK3_12003):
            with self.assertRaises(ValueError):validate_ui_build_scope(build,"open_holy_site","holy_site")
            with self.assertRaises(ValueError):validate_ui_build_scope(build,"confirm_site_adoption","holy_site_adoption")
        for operation in ("select_army","adopt","open_character"):
            with self.assertRaises(ValueError):validate_ui_request(operation,"holy_site",0,1)


class HolySiteUiMcpTests(unittest.IsolatedAsyncioTestCase):
    async def test_real_mcp_discovers_typed_route_and_rejects_arbitrary_dispatch_before_io(self):
        from mcp import Client
        async with Client(create_server(NoIoDriver())) as client:
            tools={t.name:t for t in (await client.list_tools()).tools}
            for name in ("ck3_open_holy_site_window_v1", "ck3_open_holy_site_adoption_decision_v1",
                         "ck3_confirm_holy_site_adoption_decision_v1"):
                schema=tools[name].input_schema
                self.assertEqual(set(schema["properties"]),{"holy_site_id","expected_revision"})
                self.assertEqual(schema["properties"]["holy_site_id"]["minimum"],0)
                self.assertFalse(tools[name].annotations.idempotent_hint)
                for extra in ({"holy_site_id":True},{"holy_site_id":0xFFFFFFFF},{"rva":0xAF39E0},{"child_path":"0/1"}):
                    reply=await client.call_tool(name,{"holy_site_id":0,"expected_revision":1,**extra})
                    self.assertTrue(reply.is_error)
            self.assertIn("holy_site",tools["ck3_query_ingame_ui_window_v1"].input_schema["properties"]["window_kind"]["enum"])
            query=tools["ck3_query_player_holy_site_adoption_detail_v1"]
            self.assertTrue(query.annotations.read_only_hint)
            self.assertEqual(set(query.input_schema["properties"]),{"holy_site_id","expected_revision"})
            for invalid in ({"holy_site_id":True},{"holy_site_id":0xFFFFFFFF},{"confirm":True}):
                reply=await client.call_tool(query.name,{"holy_site_id":0,"expected_revision":1,**invalid})
                self.assertTrue(reply.is_error)


if __name__=="__main__":unittest.main()
