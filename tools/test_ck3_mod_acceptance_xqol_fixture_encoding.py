"""QOL fixture BOM regression; no game, profile or acceptance execution."""
import hashlib
import json
from pathlib import Path
import unittest

from test_ck3_mod_acceptance_xqol_merit_direct_parent import restore_pre_v2_merit_event


CASES = Path(__file__).resolve().parent / "ck3_mod_acceptance_cases"
BOM = b"\xef\xbb\xbf"
# Frozen pre-fix identities: adding BOM must not alter any script/body/newline.
ORIGINAL = {
    ("administrative_appointments", "common/on_action/zqagov_start.txt"):
        (170, "06301206b8e168679fe36252b9572165af0592972979465ab15d5cacff50aee6"),
    ("administrative_appointments", "events/zqagov_events.txt"):
        (1781, "a22160dbfba94b75c034e9c46b89fb4eede2f87f4d7236e298a128faf61088d7"),
    ("meritocratic_appointments", "common/on_action/zqagov_start.txt"):
        (170, "feaf62173b6821ed6154fabb9e5e3f1647ef0fe585209508e716f00903bbd2db"),
    ("meritocratic_appointments", "events/zqagov_events.txt"):
        (2391, "005dbcc532b7c710159fe4e1ccc8b1ef0ce3aa05ecaec19ec6de32af88cef32a"),
    ("liege_shared_ransom", "common/on_action/zqlr_startup_on_actions.txt"):
        (206, "d96f3dcafaec372edc5efff020c16ded1737a0cdf36812b7af34e910cf9b51ac"),
    ("liege_shared_ransom", "common/scripted_effects/zqlr_stock_ransom_observer.txt"):
        (6083, "0b10136c742ff9302a32975742fcd30a84680f653a1bd17c50d0bb6937b9aae8"),
    ("liege_shared_ransom", "events/zqlr_ransom_events.txt"):
        (352, "2e6690b1cae9f216a2905199a7467245890188a30ffdebaa27236a03a4d3c6f4"),
}


class QolFixtureEncoding(unittest.TestCase):
    def test_script_boms_support_pins_and_seven_exact_inverse_bodies(self):
        checked = set()
        affected = {case for case, _ in ORIGINAL}
        for contract_path in sorted(CASES.glob("xqol_*.json")):
            contract = json.loads(contract_path.read_bytes())
            if contract.get("schema") != "ck3-xqol-original-followup-case-v1":
                continue
            case = contract["case"]
            for relative in contract["fixture_files"]:
                if not relative.endswith(".txt"):
                    continue
                support = contract["data_directory"] + "/fixture/" + relative
                raw = (CASES / support).read_bytes()
                with self.subTest(case=case, script=relative):
                    self.assertTrue(raw.startswith(BOM))
                    self.assertEqual(raw.count(BOM), 1)
                    self.assertEqual(contract["support_files"][support], {
                        "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()})
                    key = (case, relative)
                    if key in ORIGINAL:
                        old_bytes, old_sha = ORIGINAL[key]
                        inverse = (restore_pre_v2_merit_event(raw)
                                   if key == ("meritocratic_appointments", "events/zqagov_events.txt") else raw)
                        self.assertEqual(len(inverse), old_bytes + len(BOM))
                        self.assertEqual(hashlib.sha256(inverse[len(BOM):]).hexdigest(), old_sha)
                        checked.add(key)
            if case in affected:
                for relative, expected in contract["support_files"].items():
                    with self.subTest(case=case, support=relative):
                        raw = (CASES / relative).read_bytes()
                        self.assertEqual(expected, {
                            "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()})
        self.assertEqual(checked, set(ORIGINAL))


if __name__ == "__main__":
    unittest.main()
