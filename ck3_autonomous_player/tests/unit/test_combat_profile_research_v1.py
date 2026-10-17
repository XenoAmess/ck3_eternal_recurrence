"""The observed mod-absent .4 shape is a research profile, not xar_off."""
import copy
import unittest

from xar_autoplayer.combat_profile_research_v1 import is_verified_vanilla_research_profile_v1


def profile():
    return {"diagnostics":{"hello":{"ck3_build_match":True,"expected_ck3_version":"1.20.0.4",
        "expected_ck3_sha256":"98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518"}},
        "succession_lifecycle":{"schema":"xar.ck3.succession-lifecycle-binding/v1",
            "lifecycle":"ordinary_campaign_succession","xar_enabled":None,
            "pact_contract":"absent_by_verified_xar_mod_not_loaded",
            "source":"absent_by_verified_xar_mod_not_loaded","environment_sha256":"a"*64}}


class VerifiedVanillaResearchProfile(unittest.TestCase):
    def test_canonical_profile_is_unchanged_and_six_incomplete_or_wrong_profiles_reject(self):
        current = profile()
        original = copy.deepcopy(current)
        self.assertTrue(is_verified_vanilla_research_profile_v1(current, expected_environment_sha256="a"*64))
        for path, value in (
            (("diagnostics","hello","expected_ck3_version"),"1.20.0.3"),
            (("diagnostics","hello","expected_ck3_sha256"),"0"*64),
            (("diagnostics","hello","ck3_build_match"),False),
            (("succession_lifecycle","source"),"unknown"),
            (("succession_lifecycle","pact_contract"),"unknown"),
            (("succession_lifecycle","environment_sha256"),None),
        ):
            changed = copy.deepcopy(current)
            cursor = changed
            for key in path[:-1]:
                cursor = cursor[key]
            cursor[path[-1]] = value
            with self.subTest(path=path):
                self.assertFalse(is_verified_vanilla_research_profile_v1(changed))
        self.assertFalse(is_verified_vanilla_research_profile_v1(current, expected_environment_sha256="b"*64))
        legacy = copy.deepcopy(current)
        legacy["succession_lifecycle"].update(xar_enabled="xar_off",
            pact_contract="absent_by_fresh_campaign_xar_off_contract",source="prepared-environment-manifest")
        self.assertFalse(is_verified_vanilla_research_profile_v1(legacy))
        self.assertEqual(current, original)


if __name__ == "__main__":
    unittest.main()
