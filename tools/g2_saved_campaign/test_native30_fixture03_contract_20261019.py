"""Finite source/identity-contract tests; no configure, compiler, Task or Game."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import hashlib
import importlib.util
from pathlib import Path
import subprocess
from types import SimpleNamespace
import unittest
from unittest.mock import patch

PATH = Path(__file__).with_name("qualify_native30_fixture03_20261019.py")
SPEC = importlib.util.spec_from_file_location("native30_fixture03_tested", PATH)
Q = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(Q)
DIGEST = hashlib.sha256(b"fixture").hexdigest()

class Base:
    @staticmethod
    def machine(): return "test-machine"
    @staticmethod
    def digest(path): return DIGEST
    @staticmethod
    def git(*args): return b"fixture"

def valid():
    card = {"status": "ADMITTED", "machine_id": "test-machine", "root": str(Q.ROOT),
        "attempt_root": str(Q.ATTEMPT), "hard_bytes": 1610612736, "source_charge_cap_bytes": 100663296,
        "jobs": 4, "aggregate_includes_prior_retained": True, "prior_retained_allocation_bytes": 659564464,
        "new_reservation_bytes": 0, "source_commit": "704bdd3362bdc282ed5f5f8cf31fd3f50b90d747",
        "producer_sha256": DIGEST, "plan_sha256": DIGEST, "minimum_free_bytes": 2*1024**3,
        "quota_remaining_bytes": 1610612736, "implementation_commit": "a"*40,
        "deadline_utc": (datetime.now(timezone.utc)+timedelta(hours=1)).isoformat()}
    plan = {"helper_pins": {"some-helper.py": DIGEST}}
    args = SimpleNamespace(plan=Q.REPO/"example.json", admission=Path("card.json"), admission_sha256=DIGEST)
    return card, plan, args

class Admission(unittest.TestCase):
    def check(self, card, plan, args, exists=False):
        with patch.object(Path, "exists", return_value=exists): Q.validate_card(Base, card, plan, args)
    def test_valid_same_aggregate_contract(self): self.check(*valid())
    def test_existing_attempt_never_replayed(self):
        with self.assertRaises(RuntimeError): self.check(*valid(), exists=True)
    def test_prior_117MB_number_is_stale(self):
        card, plan, args = valid(); card["prior_retained_allocation_bytes"] = 117360240
        with self.assertRaises(RuntimeError): self.check(card, plan, args)
    def test_second_reservation_rejected(self):
        card, plan, args = valid(); card["new_reservation_bytes"] = 1610612736
        with self.assertRaises(RuntimeError): self.check(card, plan, args)
    def test_wrong_machine_rejected(self):
        card, plan, args = valid(); card["machine_id"] = "another"
        with self.assertRaises(RuntimeError): self.check(card, plan, args)
    def test_wrong_native_source_commit_rejected(self):
        card, plan, args = valid(); card["source_commit"] = "b"*40
        with self.assertRaises(RuntimeError): self.check(card, plan, args)
    def test_jobs_bool_rejected(self):
        card, plan, args = valid(); card["jobs"] = True
        with self.assertRaises(RuntimeError): self.check(card, plan, args)
    def test_expired_card_rejected(self):
        card, plan, args = valid(); card["deadline_utc"] = "2000-01-01T00:00:00+00:00"
        with self.assertRaises(RuntimeError): self.check(card, plan, args)
    def test_implementation_source_mismatch_rejected(self):
        with patch.object(Base, "git", return_value=b"other"):
            with self.assertRaises(RuntimeError): self.check(*valid())

class LiteralCopy(unittest.TestCase):
    def test_exact_copy_includes_literal_NUL_size(self): Q.fixture_delta(Q.OLD, Q.NEW)
    def test_strlen_length_rejected(self):
        with self.assertRaises(RuntimeError): Q.fixture_delta(Q.OLD, Q.NEW.replace(b'sizeof("b_fixture")', b'9'))
    def test_other_source_change_rejected(self):
        with self.assertRaises(RuntimeError): Q.fixture_delta(Q.OLD, Q.NEW+b"extra")
    def test_duplicate_old_copy_rejected(self):
        with self.assertRaises(RuntimeError): Q.fixture_delta(Q.OLD+Q.OLD, Q.NEW+Q.NEW)
    def test_actual_fixture_has_only_the_single_admitted_change(self):
        old = subprocess.run(["git", "show", "704bdd3362bdc282ed5f5f8cf31fd3f50b90d747:"+Q.FIXTURE],
                             cwd=Q.REPO, capture_output=True, check=True).stdout
        Q.fixture_delta(old, (Q.REPO/Q.FIXTURE).read_bytes())

class ArgGuard:
    @staticmethod
    def output_from_command(row): return Path(row["output"])

def row(target, file, output):
    return {"file": file, "output": output, "arguments": ["cl.exe", "/O2", "/W4", "/WX", "/UNDEBUG",
            "/Fo"+output, "/c", file]}

def graphs():
    before = {"link_contract": {"same": "order"}, "selected_compile_rows": [
        row(Q.TEST, "C:/frozen/src/camera_tracking_v1_test.cpp", "CMakeFiles/"+Q.TEST+".dir/src/old.obj"),
        row("xar_ck3_bridge", "C:/frozen/src/bridge.cpp", "CMakeFiles/xar_ck3_bridge.dir/src/bridge.cpp.obj"),
        row("xar_bridge_protocol", "C:/frozen/src/protocol.cpp", "CMakeFiles/xar_bridge_protocol.dir/src/protocol.cpp.obj")]}
    after = deepcopy(before)
    after["selected_compile_rows"][0] = row(Q.TEST, "C:/build/fixed/camera_tracking_v1_test.cpp",
                                          "CMakeFiles/"+Q.TEST+".dir/fixed/new.obj")
    return before, after

def compare(before, after):
    return Q.exact_graph_delta(before, after, ArgGuard, "C:/frozen/src/camera_tracking_v1_test.cpp",
                              "C:/build/fixed/camera_tracking_v1_test.cpp")

class GraphChange(unittest.TestCase):
    def test_only_fixture_source_and_object_change(self): self.assertEqual(compare(*graphs())["selected_commands"], 3)
    def test_production_compile_option_change_rejected(self):
        before, after = graphs(); after["selected_compile_rows"][1]["arguments"].append("/DCHANGED=1")
        with self.assertRaises(RuntimeError): compare(before, after)
    def test_protocol_macro_leak_rejected(self):
        before, after = graphs(); after["selected_compile_rows"][2]["arguments"].append("/DXAR_LEAK=1")
        with self.assertRaises(RuntimeError): compare(before, after)
    def test_fixture_WX_cannot_be_disabled(self):
        before, after = graphs(); after["selected_compile_rows"][0]["arguments"].remove("/WX")
        with self.assertRaises(RuntimeError): compare(before, after)
    def test_fixture_assertions_cannot_be_disabled(self):
        before, after = graphs(); after["selected_compile_rows"][0]["arguments"].remove("/UNDEBUG")
        with self.assertRaises(RuntimeError): compare(before, after)
    def test_link_change_rejected(self):
        before, after = graphs(); after["link_contract"] = {"changed": "link"}
        with self.assertRaises(RuntimeError): compare(before, after)
    def test_other_source_replacement_rejected(self):
        before, after = graphs(); after["selected_compile_rows"].pop()
        with self.assertRaises(RuntimeError): compare(before, after)
    def test_duplicate_source_rejected(self):
        before, after = graphs(); after["selected_compile_rows"].append(after["selected_compile_rows"][1])
        with self.assertRaises(RuntimeError): compare(before, after)

class NoProductionWork(unittest.TestCase):
    def test_explicit_no_work(self): Q.assert_no_work("ninja: no work to do.\n")
    def test_empty_quiet_output_is_not_proof(self):
        with self.assertRaises(RuntimeError): Q.assert_no_work("")
    def test_any_planned_production_build_rejected(self):
        with self.assertRaises(RuntimeError): Q.assert_no_work("[1/1] Building CXX object bridge.cpp.obj")

class PriorOutput(unittest.TestCase):
    def test_exact_old_closed_name_size_and_production_window(self):
        Q.prior_output_boundary("build/x.obj", 123, 150, {"build/x.obj": {"eof": 123}}, 100, 200)
    def test_missing_old_member_rejected(self):
        with self.assertRaises(RuntimeError): Q.prior_output_boundary("build/x.obj", 123, 150, {}, 100, 200)
    def test_changed_size_rejected(self):
        with self.assertRaises(RuntimeError):
            Q.prior_output_boundary("build/x.obj", 124, 150, {"build/x.obj": {"eof": 123}}, 100, 200)
    def test_later_modified_output_rejected(self):
        with self.assertRaises(RuntimeError):
            Q.prior_output_boundary("build/x.obj", 123, 202, {"build/x.obj": {"eof": 123}}, 100, 200)

if __name__ == "__main__": unittest.main(verbosity=2)
