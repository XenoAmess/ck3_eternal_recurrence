"""Owned mechanics only; no real Game, DLL build, production issuer or settings."""
import os
import unittest
from unittest.mock import patch

from tools.g2_saved_campaign import private_handle_chain_v1 as chain

LAST_RUNS = []


class PureBoundaryTests(unittest.TestCase):
    def test_default_off_never_loads_windows_or_launches(self):
        with patch.object(chain,"_Windows",side_effect=AssertionError("default must be lazy")):
            self.assertEqual(chain.run_owned_fixture_v1(),
                {"status":"default_off","Native_DTO_issued":False,"H":"unknown"})

    def test_json_cannot_create_a_resource_holder(self):
        with self.assertRaisesRegex(chain.ChainUnavailable,"internal fixture receiver"):
            chain._ReceivedFixtureResources(None,{"target":123,"lease":456},object())

    def test_parent_manifest_must_equal_actual_kernel_observation(self):
        for actual,claim in (({"pid":7},{"pid":8}),
                             ({"birth_filetime":"134368863604700829"},
                              {"birth_filetime":"134368863604700820"}),
                             ({"file_id":"aa"},{"file_id":"bb"}),
                             ({"pid":7},"{\"pid\":7}")):
            with self.subTest(actual=actual,claim=claim):
                with self.assertRaises(chain.ChainUnavailable):chain._same_claim(actual,claim)


@unittest.skipUnless(os.name=="nt","owned Windows mechanics")
class OwnedMechanicalTests(unittest.TestCase):
    def test_real_four_roles_actual_MCP_creator_and_revocation(self):
        result=chain.run_owned_fixture_v1(enabled=True)
        LAST_RUNS.append(result)
        self.assertEqual(result["status"],"owned_chain_pass")
        self.assertTrue(result["actual_MCP_creator"])
        self.assertEqual([n["role"] for n in result["nodes"]],["owner","Queue","MCPApp"])
        self.assertEqual(len({n["process"]["pid"] for n in result["nodes"]}),3)
        self.assertTrue(all(n["adopted"] and n["valid_before_close"] is False
                            and n["resource_handles_remaining"]==0 for n in result["nodes"]))
        self.assertTrue(all(n["exact_resources"]==result["root"] for n in result["nodes"]))
        self.assertEqual(result["cleanup"],{"owned_remaining":0,"errors":[],"temporary_remaining":0})
        self.assertTrue(result["fixture_directory_removed"])
        self.assertFalse(result["Native_DTO_issued"])
        self.assertEqual(result["H"],"unknown")

    def test_real_bad_manifest_is_rejected_before_forwarding(self):
        result=chain.run_owned_fixture_v1(enabled=True,wrong_claim=True)
        LAST_RUNS.append(result)
        self.assertEqual(result["status"],"wrong_claim_rejected")
        self.assertIn("parent claim differs",result["reason"])
        self.assertEqual(result["cleanup"],{"owned_remaining":0,"errors":[],"temporary_remaining":0})
        self.assertTrue(result["fixture_directory_removed"])
        self.assertFalse(result["Native_DTO_issued"])

    def test_real_wrong_parent_handle_is_rejected_by_kernel_pipe_peer(self):
        result=chain.run_owned_fixture_v1(enabled=True,wrong_parent=True)
        LAST_RUNS.append(result)
        self.assertEqual(result["status"],"wrong_parent_peer_rejected")
        self.assertIn("server is not held parent",result["reason"])
        self.assertEqual(result["cleanup"],{"owned_remaining":0,"errors":[],"temporary_remaining":0})
        self.assertTrue(result["fixture_directory_removed"])
        self.assertFalse(result["Native_DTO_issued"])


if __name__=="__main__":
    unittest.main()
