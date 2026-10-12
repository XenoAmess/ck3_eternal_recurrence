"""Bounded static v2 fixture checks; no game, profile or acceptance execution."""
import copy
import hashlib
import json
from pathlib import Path
import re
import unittest

from xqol_vanilla_contract import block


CASES = Path(__file__).resolve().parent / "ck3_mod_acceptance_cases"
EVENT_KEY = "xqol_followup_cases/meritocratic_appointments/fixture/events/zqagov_events.txt"
ORIGINAL_EVENT = {
    "bytes": 2394,
    "sha256": "f3bede99ade8cbb23df525f3c350aa80a7a017cd9babf17cb08996c2c24f6b83",
}
ORIGINAL_CONTRACT_SHA = "207c7b0082adc7aef2ae0d98f496ab194387604e4b389d6019fd15574b93c981"
SCOPE_V1 = "controlled-qualified-merit-positive-v1"
SCOPE_V2 = "controlled-qualified-merit-direct-parent-positive-v2"
V2_MARKERS = ["ZQAGOV: SETUP " + phase + " " + SCOPE_V2 + " grant=k_goguryeo"
              for phase in ("BEGIN", "DONE")]
REGION_NAMES = ("preconditions", "controlled_grant", "post_readback_open", "post_readback_close")
REGION = re.compile(
    rb"(?ms)^ *# ZQAGOV_MERIT_V2_BEGIN ([a-z_]+)\n.*?^ *# ZQAGOV_MERIT_V2_END \1\n")
LAWS = {
    "d_haeju": "meritocratic_appointment_succession_law",
    "d_bukgye": "meritocratic_military_appointment_succession_law",
}


def restore_pre_v2_merit_event(raw):
    """Remove only the four named insertions, retaining every original byte."""
    matches = list(REGION.finditer(raw))
    if tuple(m[1].decode("ascii") for m in matches) != REGION_NAMES:
        raise ValueError("Expected exactly four ordered merit v2 insertion blocks")
    return REGION.sub(b"", raw)


def restore_pre_v2_merit_contract(contract):
    value = copy.deepcopy(contract)
    preparation = value["fixture_preparation"]
    if value["acceptance_scope"] != SCOPE_V2 or preparation["kind"] != SCOPE_V2:
        raise ValueError("Expected explicit controlled merit v2 contract")
    value["acceptance_scope"] = preparation["kind"] = SCOPE_V1
    for key in ("required_startup", "required_markers"):
        if value[key][-2:] != V2_MARKERS:
            raise ValueError("Original ordered markers must precede the two v2 markers")
        value[key] = value[key][:-2]
    del preparation["controlled_title_grant"]
    value["support_files"][EVENT_KEY] = dict(ORIGINAL_EVENT)
    return value


class MeritDirectParentFixture(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = (CASES / EVENT_KEY).read_bytes()
        cls.text = cls.raw.decode("utf-8-sig")
        cls.contract = json.loads((CASES / "xqol_meritocratic_appointments.json").read_bytes())
        cls.regions = {m[1].decode("ascii"): m[0].decode("utf-8")
                       for m in REGION.finditer(cls.raw)}

    def test_four_insertions_restore_entire_v1_and_single_original_merit_award(self):
        inverse = restore_pre_v2_merit_event(self.raw)
        self.assertEqual(len(inverse), ORIGINAL_EVENT["bytes"])
        self.assertEqual(hashlib.sha256(inverse).hexdigest(), ORIGINAL_EVENT["sha256"])
        self.assertEqual(hashlib.sha256(inverse[3:]).hexdigest(),
                         "005dbcc532b7c710159fe4e1ccc8b1ef0ce3aa05ecaec19ec6de32af88cef32a")
        self.assertTrue(self.raw.startswith(b"\xef\xbb\xbf"))
        self.assertEqual(self.raw.count(b"\xef\xbb\xbf"), 1)
        self.assertEqual(self.text.count("change_merit = 2000"), 1)
        self.assertEqual(self.text.count("set_player_character = scope:zqagov_target"), 1)
        self.assertEqual(self.text.count("trigger_event = { id = zqagov_merit.2 }"), 1)
        for event in ("zqagov_merit.1", "zqagov_merit.2"):
            self.assertIn("hidden = yes", block(self.text, event))
        self.assertTrue(self.text.rstrip().endswith(block(self.text, "zqagov_merit.2")))
        with self.assertRaises(ValueError):
            restore_pre_v2_merit_event(self.raw.replace(
                b"ZQAGOV_MERIT_V2_END controlled_grant", b"ZQAGOV_MERIT_V2_END wrong", 1))

    def test_unowned_parent_and_fixed_original_holders_laws_lieges_guard_grant(self):
        pre = self.regions["preconditions"]
        self.assertIn("NOT = { exists = title:k_goguryeo.holder }", pre)
        self.assertIn("title:k_goguryeo = { de_jure_liege = title:e_goryeo }", pre)
        self.assertIn("title:e_goryeo.holder = { primary_title = title:e_goryeo }", pre)
        for title, law in LAWS.items():
            target = block(pre, "title:" + title, indentation=" " * 16)
            self.assertIn("exists = holder", target)
            self.assertIn("de_jure_liege = title:k_goguryeo", target)
            holder = block(target, "holder", indentation=" " * 20)
            self.assertIn("has_realm_law = " + law, holder)
            for assertion in ("is_alive = yes", "is_ai = yes", "is_independent_ruler = no",
                              "liege = title:e_goryeo.holder", "primary_title = title:" + title):
                self.assertIn(assertion, holder)
        grant = self.regions["controlled_grant"]
        creation = block(grant, "create_title_and_vassal_change", indentation=" " * 16)
        for assertion in ("type = created", "save_scope_as = zqagov_v2_parent_change", "add_claim_on_loss = no"):
            self.assertIn(assertion, creation)
        changes = re.findall(r"change_title_holder\s*=", grant)
        self.assertEqual(len(changes), 1)
        parent = block(grant[grant.index(creation) + len(creation):],
                       "title:k_goguryeo", indentation=" " * 16)
        self.assertIn("holder = scope:zqagov_target", parent)
        self.assertIn("change = scope:zqagov_v2_parent_change", parent)
        self.assertNotIn("holder = root", grant)
        self.assertEqual(grant.count("resolve_title_and_vassal_change = scope:zqagov_v2_parent_change"), 1)
        for role in ("civic", "military"):
            self.assertIn("save_scope_as = zqagov_v2_" + role + "_holder_before", grant)
            self.assertIn("save_scope_as = zqagov_v2_" + role + "_liege_before", grant)
        script = re.sub(r'"(?:\\.|[^"\\])*"|#[^\n]*', "", grant)
        assignments = set(re.findall(r"\b([A-Za-z_][A-Za-z_0-9:.]*)\s*=", script))
        self.assertEqual(assignments, {
            "debug_log", "title:k_goguryeo", "save_scope_as", "title:d_haeju", "title:d_bukgye",
            "holder", "liege", "create_title_and_vassal_change", "type", "add_claim_on_loss",
            "change_title_holder", "change", "resolve_title_and_vassal_change"})

    def test_direct_parent_and_unchanged_targets_read_back_before_original_qualification(self):
        post = self.regions["post_readback_open"]
        limit = block(post, "limit", indentation=" " * 12)
        for assertion in ("current_date = 1066.9.15", "this = scope:zqagov_target", "is_ai = no",
                          "is_independent_ruler = yes", "has_government = meritocratic_government",
                          "primary_title = title:e_goryeo", "has_title = title:k_goguryeo"):
            self.assertIn(assertion, limit)
        for (title, law), role in zip(LAWS.items(), ("civic", "military")):
            target = block(post, "title:" + title, indentation=" " * 16)
            for assertion in ("holder = scope:zqagov_v2_" + role + "_holder_before",
                              "holder.liege = scope:zqagov_v2_" + role + "_liege_before",
                              "holder.liege = scope:zqagov_target", "holder.primary_title = title:" + title,
                              "holder = { has_realm_law = " + law + " }"):
                self.assertIn(assertion, target)
            direct = block(target, "de_jure_liege", indentation=" " * 20)
            self.assertIn("this = scope:zqagov_v2_parent_title", direct)
            self.assertIn("holder = scope:zqagov_target", direct)
        event = block(self.text, "zqagov_merit.2")
        self.assertLess(event.index(V2_MARKERS[1]), event.index("ZQAGOV: QUAL PASS"))
        self.assertIn("ZQAGOV: QUAL FAIL controlled_direct_parent_post_grant_v2",
                      self.regions["post_readback_close"])
        inserted = "\n".join(self.regions.values())
        for forbidden in ("add_title_law", "add_realm_law", "set_de_jure_liege_title", "change_government",
                          "allowed_candidate_tier", "change_merit", "trigger_event", "add_trait",
                          "remove_trait", "set_variable", "advance_day"):
            self.assertNotIn(forbidden, inserted)

    def test_both_original_law_gates_use_holder_realm_scope_before_and_after_grant(self):
        # Stock appointment laws are realm laws; a title-local gate rejects the
        # normal effective law before the controlled grant (A192/R0084).
        for region in ("preconditions", "post_readback_open"):
            for title, law in LAWS.items():
                with self.subTest(region=region, title=title, law=law):
                    target = block(self.regions[region], "title:" + title, indentation=" " * 16)
                    holder = block(target, "holder", indentation=" " * 20)
                    self.assertEqual(holder.count("has_realm_law = " + law), 1)
                    self.assertNotIn("has_realm_law", target.replace(holder, "", 1))
                    self.assertNotIn("has_title_law", target)

    def test_contract_inverse_preserves_original_markers_budgets_nine_supports_and_plan(self):
        restored = restore_pre_v2_merit_contract(self.contract)
        old = (json.dumps(restored, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
        self.assertEqual(len(old), 3888)
        self.assertEqual(hashlib.sha256(old).hexdigest(), ORIGINAL_CONTRACT_SHA)
        self.assertEqual(self.contract["required_markers"][:5], restored["required_markers"])
        self.assertEqual(self.contract["required_startup"][:5], restored["required_startup"])
        self.assertEqual(self.contract["forbidden_markers"], restored["forbidden_markers"])
        self.assertEqual(self.contract["forbidden_startup"], restored["forbidden_startup"])
        self.assertEqual(self.contract["original_budgets"], {
            "command_timeout": 300, "readiness_timeout": 400, "timeout": 3000,
            "hold_seconds": 1800, "poll_interval": 0.05})
        self.assertEqual(self.contract["original_step_count"], 2)
        self.assertEqual(self.contract["maximum_natural_days"], 0)
        self.assertEqual(self.contract["appointment_laws"], list(LAWS.values()))
        self.assertFalse(self.contract["full_product_pass_from_cell"])
        preparation = self.contract["fixture_preparation"]
        self.assertEqual((preparation["stock_effect"], preparation["amount"], preparation["applications"]),
                         ("change_merit", 2000, 1))
        grant = preparation["controlled_title_grant"]
        self.assertEqual(grant["target_laws"], LAWS)
        self.assertEqual((grant["title"], grant["holder"], grant["applications"]),
                         ("title:k_goguryeo", "scope:zqagov_target", 1))
        self.assertFalse(grant["stock_default_gui_can_create"])
        self.assertIn("A190/R0082", grant["credit_scope"])
        self.assertIn("setup does not imply eligibility", grant["required_actual_readback"][-1])
        self.assertEqual(len(self.contract["support_files"]), 9)
        changed = {k for k, v in self.contract["support_files"].items() if v != restored["support_files"][k]}
        self.assertEqual(changed, {EVENT_KEY})
        for relative, expected in self.contract["support_files"].items():
            raw = (CASES / relative).read_bytes()
            self.assertEqual(expected, {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()})
        plan = json.loads((CASES / self.contract["data_directory"] / "original-plan.json").read_bytes())
        self.assertEqual(len(plan["steps"]), 2)
        self.assertFalse(any(s.get("kind") == "advance_day" for s in plan["steps"]))


if __name__ == "__main__":
    unittest.main()
