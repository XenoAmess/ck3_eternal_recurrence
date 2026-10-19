"""No configure/build: finite admission and exact compiler-argv change checks."""
from copy import deepcopy
from datetime import datetime, timezone, timedelta
import hashlib
import io
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

PATH = Path(__file__).with_name("build_native30_resume_20261019.py")
SPEC = importlib.util.spec_from_file_location("native30_resume_tested", PATH)
RESUME = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RESUME)
DIGEST = hashlib.sha256(b"fixture").hexdigest()

class Base:
    @staticmethod
    def require(value, message):
        if not value: raise RuntimeError(message)
    @staticmethod
    def machine(): return "machine-test"
    @staticmethod
    def digest(path): return DIGEST
    @staticmethod
    def git(*args): return b"fixture"

def valid():
    card = {"status": "ADMITTED", "machine_id": "machine-test", "root": str(RESUME.ROOT),
        "attempt_root": str(RESUME.ATTEMPT), "hard_bytes": 1610612736,
        "source_charge_cap_bytes": 100663296, "jobs": 4,
        "source_commit": "704bdd3362bdc282ed5f5f8cf31fd3f50b90d747", "aggregate_includes_prior_retained": True,
        "prior_retained_allocation_bytes": 117360240, "new_reservation_bytes": 0,
        "producer_sha256": DIGEST, "plan_sha256": DIGEST, "minimum_free_bytes": 2*1024**3,
        "quota_remaining_bytes": 1610612736, "implementation_commit": "a"*40,
        "deadline_utc": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()}
    plan = {"prior_closed_sha256": DIGEST, "helper_pins": {"tools/g2_saved_campaign/example.py": DIGEST}}
    args = SimpleNamespace(plan=RESUME.REPO / "example-plan.json", admission=Path("example-card.json"),
                           admission_sha256=DIGEST)
    return card, plan, args

class Admission(unittest.TestCase):
    def check(self, card, plan, args, exists=False):
        with patch.object(Path, "exists", return_value=exists):
            RESUME.validate_card(Base, card, plan, args)
    def test_valid_shared_cap_contract(self): self.check(*valid())
    def test_wrong_machine(self):
        card, plan, args = valid(); card["machine_id"] = "other"
        with self.assertRaises(RuntimeError): self.check(card, plan, args)
    def test_existing_attempt_is_never_replayed(self):
        with self.assertRaises(RuntimeError): self.check(*valid(), exists=True)
    def test_wrong_budget_root(self):
        card, plan, args = valid(); card["root"] = str(RESUME.ROOT / "wrong")
        with self.assertRaises(RuntimeError): self.check(card, plan, args)
    def test_prior_retained_allocation_cannot_be_zeroed(self):
        card, plan, args = valid(); card["prior_retained_allocation_bytes"] = 0
        with self.assertRaises(RuntimeError): self.check(card, plan, args)
    def test_no_second_independent_reservation(self):
        card, plan, args = valid(); card["new_reservation_bytes"] = 1610612736
        with self.assertRaises(RuntimeError): self.check(card, plan, args)
    def test_job_boolean_is_not_a_worker_count(self):
        card, plan, args = valid(); card["jobs"] = True
        with self.assertRaises(RuntimeError): self.check(card, plan, args)
    def test_jobs_above_four(self):
        card, plan, args = valid(); card["jobs"] = 5
        with self.assertRaises(RuntimeError): self.check(card, plan, args)
    def test_expired_card(self):
        card, plan, args = valid(); card["deadline_utc"] = "2020-01-01T00:00:00+00:00"
        with self.assertRaises(RuntimeError): self.check(card, plan, args)
    def test_wrong_producer_pin(self):
        card, plan, args = valid(); card["producer_sha256"] = "different"
        with self.assertRaises(RuntimeError): self.check(card, plan, args)
    def test_short_implementation_commit(self):
        card, plan, args = valid(); card["implementation_commit"] = "aaaa"
        with self.assertRaises(RuntimeError): self.check(card, plan, args)
    def test_code_not_in_implementation_commit(self):
        with patch.object(Base, "git", return_value=b"other"):
            with self.assertRaises(RuntimeError): self.check(*valid())

def compiler_row(target, name):
    output = "CMakeFiles/" + target + ".dir/src/" + name + ".obj"
    return {"file": "C:/frozen/src/" + name, "output": output,
            "arguments": ["cl.exe", "/DOLD=1", "/O2", "/Fo" + output, "/c", "C:/frozen/src/" + name]}

class ArgGuard:
    @staticmethod
    def output_from_command(row): return Path(row["output"])

def graphs():
    before = {"selected_compile_rows": [compiler_row("xar_ck3_12002_runtime", "ck3_12002.cpp"),
                                        compiler_row("xar_bridge_protocol", "protocol.cpp")], "link_contract": {"same": "link"}}
    after = deepcopy(before)
    after["selected_compile_rows"][0]["arguments"][1:1] = ["/D" + value for value in sorted(RESUME.RESTORED)]
    return before, after

class CompileArguments(unittest.TestCase):
    def test_exact_two_restored_defines_only(self):
        report = RESUME.source_defines_only(*graphs(), ArgGuard)
        self.assertEqual(report["selected_commands"], 2)
        self.assertEqual(report["restored_definitions"], sorted(RESUME.RESTORED))
    def test_protocol_is_not_given_runtime_macros(self):
        before, after = graphs(); after["selected_compile_rows"][1]["arguments"].append("/DUNADMITTED=1")
        with self.assertRaises(RuntimeError): RESUME.source_defines_only(before, after, ArgGuard)
    def test_other_flag_change_rejected(self):
        before, after = graphs(); after["selected_compile_rows"][0]["arguments"].append("/O1")
        with self.assertRaises(RuntimeError): RESUME.source_defines_only(before, after, ArgGuard)
    def test_missing_one_definition_rejected(self):
        before, after = graphs(); del after["selected_compile_rows"][0]["arguments"][1]
        with self.assertRaises(RuntimeError): RESUME.source_defines_only(before, after, ArgGuard)
    def test_duplicate_definition_rejected(self):
        before, after = graphs(); after["selected_compile_rows"][0]["arguments"].insert(1, "/D" + sorted(RESUME.RESTORED)[0])
        with self.assertRaises(RuntimeError): RESUME.source_defines_only(before, after, ArgGuard)
    def test_source_set_change_rejected(self):
        before, after = graphs(); after["selected_compile_rows"].pop()
        with self.assertRaises(RuntimeError): RESUME.source_defines_only(before, after, ArgGuard)
    def test_link_change_rejected(self):
        before, after = graphs(); after["link_contract"] = {"same": "different"}
        with self.assertRaises(RuntimeError): RESUME.source_defines_only(before, after, ArgGuard)

def member(name, payload):
    header = (name.ljust(16) + "0".ljust(12) + "0".ljust(6) + "0".ljust(6) + "0".ljust(8)
              + str(len(payload)).ljust(10) + "`\n").encode()
    return header + payload + (b"\n" if len(payload) % 2 else b"")

class Archive(unittest.TestCase):
    def read(self, body):
        with patch.object(Path, "open", return_value=io.BytesIO(body)):
            return RESUME.archive_payloads("in-memory-fixture.lib")
    def test_long_member_payload_is_byte_exact(self):
        name, payload = b"CMakeFiles/runtime.dir/typed.cpp.obj\0", b"COFF-object-fixture"
        rows = self.read(b"!<arch>\n" + member("/", b"index") + member("//", name) + member("/0", payload))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["name"], name[:-1].decode())
        self.assertEqual(rows[0]["sha256"], hashlib.sha256(payload).hexdigest())
    def test_duplicate_payload_members_are_not_collapsed(self):
        rows = self.read(b"!<arch>\n" + member("typed.obj/", b"x") * 2)
        self.assertEqual(len(rows), 2)
    def test_bad_long_name_offset_rejected(self):
        with self.assertRaises(RuntimeError): self.read(b"!<arch>\n" + member("/999", b"x"))
    def test_truncation_rejected(self):
        with self.assertRaises(RuntimeError): self.read((b"!<arch>\n" + member("typed.obj/", b"long"))[:-2])
    def test_wrong_archive_signature_rejected(self):
        with self.assertRaises(RuntimeError): self.read(b"not a COFF archive")

class ComponentBudget(unittest.TestCase):
    def test_new_owned_temp_is_charged_by_unchanged_frozen_guard(self):
        base = RESUME.load_module("native30_frozen_budget_test", PATH.with_name("build_native30_wholeclean_20261019.py"))
        temporary = (RESUME.ATTEMPT / RESUME.TEMP_RELATIVE / "sample.tmp").relative_to(RESUME.ROOT).as_posix()
        size = 384 * 1048576 + 1
        inventory = {"eof": size, "allocation": size, "raced": 0,
                     "files": [{"path": temporary, "eof": size, "allocation": size}]}
        card = {"hard_bytes": 1610612736, "minimum_free_bytes": 0,
                "deadline_utc": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()}
        with patch.object(base, "inventory", return_value=inventory), \
             patch.object(base.shutil, "disk_usage", return_value=SimpleNamespace(free=10**12)):
            with self.assertRaisesRegex(RuntimeError, "component cap"):
                base.Guard(RESUME.ROOT, card, object())()

if __name__ == "__main__": unittest.main(verbosity=2)
