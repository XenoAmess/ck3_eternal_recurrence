"""Pure protocol negatives and custody checks; no fixture, Task or OS setting calls."""
import ast
import copy
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("functional09_under_test", HERE / "native30_functional09_20261020.py")
F = importlib.util.module_from_spec(spec)
spec.loader.exec_module(F)
MACHINE = "xenoamess-full-tower-eb9d2c1186"


def plan():
    return {"schema": "native30-functional09-plan-v1", "protocol_version": 1, "run_id": F.RUN_ID,
            "machine_id": MACHINE, "source_commit": F.SOURCE_COMMIT,
            "status": "SOURCE_ONLY_NOT_EXECUTION_ADMISSION", "original_records": F.expected_refs(),
            "fields": dict(F.FIELDS), "common": {"path": str(F.COMMON_PATH), "sha256": F.COMMON_SHA},
            "phase_metadata_cap_bytes": 167772160,
            "base_plan": {"path": str(F.BASE_PLAN), "sha256": F.BASE_PLAN_SHA},
            "roots": {"aggregate": str(F.ROOT), "functional": str(F.STAGE), "owner": str(F.OWNER)},
            "functional_nonce": "123456789abcdef0123456789abcdef0"}


def records():
    return {
        "original_build_result": {"machine_id": MACHINE, "schema": F.Q.SCHEMA, "stage": "build_only",
            "status": "BUILD_READY_FOR_ADMIN", "fixture_executions": 0, "owned_active_after": 0,
            "future_writes": 0, "production_recompiled": False,
            "fixture_builds": [{"returncode": 0, "owned_active_after": 0} for _ in range(9)],
            "plan": {"sha256": F.BASE_PLAN_SHA}, "admission": {"sha256": "original-card"}},
        "original_build_owner_spec": {"machine_id": MACHINE, "nonce": F.OLD_NONCE,
            "role": "native_build", "sid": F.Q.OWNER_SID, "task_name": "XARG2ManagedOwner-" + F.OLD_NONCE,
            "stage": str(F.COMMON_PATH), "stage_sha256": F.COMMON_SHA,
            "stage_args": ["--phase", "build"], "admission_sha256": "original-card"},
        "original_build_owner_closed": {"machine_id": MACHINE, "nonce": F.OLD_NONCE,
            "spec_sha256": F.EXPECTED["original_build_owner_spec"][2], "child_exit_code": 0,
            "bootstrap_exit_code": 0, "job_active_after_stage": 0, "forced_remaining_cleanup": False},
        "original_build_unregister": {"machine_id": MACHINE, "operation": "unregister",
            "task_name": "XARG2ManagedOwner-" + F.OLD_NONCE,
            "actual": {"instances": 0, "last_result": 0, "absent_after": True,
                       "sid": F.Q.OWNER_SID, "run_level": 0}},
        "prior_failed_admin_launch": {"machine_id": MACHINE, "status": "FAILED_OR_UNKNOWN",
            "settings_success": False, "future_writes": None,
            "build_result": F.expected_refs()["original_build_result"]},
    }


class Functional09Tests(unittest.TestCase):
    def test_independent_protocol_and_pending_unknown_are_required(self):
        value = plan()
        F.verify_plan(value)
        for key, replacement in (("schema", "native30-two-stage-qualification-v1"),
                                 ("run_id", "native30-08B"), ("protocol_version", 2),
                                 ("functional_nonce", F.OLD_NONCE), ("functional_nonce", "bad")):
            with self.subTest(key=key), self.assertRaises(RuntimeError):
                F.verify_plan({**value, key: replacement})
        for key in F.FIELDS:
            changed = copy.deepcopy(value)
            changed["fields"][key] = "verified"
            with self.subTest(field=key), self.assertRaises(RuntimeError):
                F.verify_plan(changed)

    def test_no_reused_admin_or_run_directory(self):
        value = plan()
        value["roots"]["functional"] = str(F.Q.RUN)
        with self.assertRaisesRegex(RuntimeError, "independent functional roots"):
            F.verify_plan(value)

    def test_original_pins_cannot_be_replaced_by_current_latest(self):
        value = plan()
        for key in F.EXPECTED:
            changed = copy.deepcopy(value)
            changed["original_records"][key]["sha256"] = "0" * 64
            with self.subTest(key=key), self.assertRaises(RuntimeError):
                F.verify_plan(changed)

    def test_nine_builds_are_reused_without_awarding_old_admin_credit(self):
        value = records()
        before = copy.deepcopy(value)
        F.verify_seed_values(value, MACHINE)
        self.assertEqual(value, before)
        self.assertIsNone(value["prior_failed_admin_launch"]["future_writes"])
        for replacement in (0, False, 1, "0"):
            changed = copy.deepcopy(value)
            changed["prior_failed_admin_launch"]["future_writes"] = replacement
            with self.subTest(replacement=replacement), self.assertRaises(RuntimeError):
                F.verify_seed_values(changed, MACHINE)

    def test_build_machine_count_closure_and_future_negatives(self):
        value = records()
        for key, replacement in (("machine_id", "other"), ("status", "FAILED"), ("fixture_executions", 1),
                                 ("owned_active_after", 1), ("future_writes", None),
                                 ("production_recompiled", True), ("fixture_builds", [])):
            changed = copy.deepcopy(value)
            changed["original_build_result"][key] = replacement
            with self.subTest(key=key), self.assertRaises(RuntimeError):
                F.verify_seed_values(changed, MACHINE)
        changed = copy.deepcopy(value)
        changed["original_build_result"]["fixture_builds"][8]["returncode"] = 1
        with self.assertRaisesRegex(RuntimeError, "nine successful"):
            F.verify_seed_values(changed, MACHINE)

    def test_old_task_nonce_and_actual_unregister_are_not_inferred(self):
        value = records()
        changes = [("original_build_owner_spec", "nonce", "other"),
                   ("original_build_owner_closed", "machine_id", "other"),
                   ("original_build_owner_closed", "spec_sha256", "other"),
                   ("original_build_owner_closed", "job_active_after_stage", 1),
                   ("original_build_owner_closed", "child_exit_code", None),
                   ("original_build_owner_closed", "forced_remaining_cleanup", True)]
        for section, key, replacement in changes:
            changed = copy.deepcopy(value)
            changed[section][key] = replacement
            with self.subTest(section=section, key=key), self.assertRaises(RuntimeError):
                F.verify_seed_values(changed, MACHINE)
        for key, replacement in (("instances", 1), ("last_result", 1), ("absent_after", False), ("sid", "other")):
            changed = copy.deepcopy(value)
            changed["original_build_unregister"]["actual"][key] = replacement
            with self.subTest(key=key), self.assertRaises(RuntimeError):
                F.verify_seed_values(changed, MACHINE)

    def test_new_task_requires_own_nonce_exact_stage_and_args(self):
        value = plan()
        args = SimpleNamespace(plan=F.REPO / "docs/functional-plan.json", admission=F.ROOT / "new-card.json",
                               admission_sha256="card")
        owner = {"machine_id": MACHINE, "role": "native_build", "nonce": value["functional_nonce"],
                 "task_name": "XARG2ManagedOwner-" + value["functional_nonce"], "sid": F.Q.OWNER_SID,
                 "root": str(F.OWNER), "cwd": str(F.REPO), "stage": str(HERE / "native30_functional09_20261020.py"),
                 "stage_sha256": "producer", "stage_args": F.expected_stage_args(args),
                 "admission_path": str(args.admission), "admission_sha256": "card"}
        F.verify_owner_spec(owner, value, args, "producer")
        for key, replacement in (("nonce", F.OLD_NONCE), ("stage_sha256", "old"),
                                 ("stage_args", ["--phase", "build"]), ("admission_sha256", "old"),
                                 ("root", str(F.Q.OWNER_BUILD)), ("machine_id", "other")):
            with self.subTest(key=key), self.assertRaises(RuntimeError):
                F.verify_owner_spec({**owner, key: replacement}, value, args, "producer")

    def test_plan_derivation_preserves_frozen_source_and_module_globals(self):
        raw = F.BASE_PLAN.read_bytes()
        value = plan()
        value["base_plan"]["bytes"] = len(raw)
        value["producer"] = {"sha256": "new-producer"}
        old_admin, old_run, old_build = F.Q.ADMIN, F.Q.RUN, F.Q.BUILD
        derived = F.derive_readonly_plan(value)
        self.assertEqual(F.BASE_PLAN.read_bytes(), raw)
        self.assertEqual((F.Q.ADMIN, F.Q.RUN, F.Q.BUILD), (old_admin, old_run, old_build))
        self.assertEqual(derived["helper_pins"][F.COMMON_PATH.relative_to(F.REPO).as_posix()], F.COMMON_SHA)
        self.assertEqual(derived["helper_pins"]["tools/g2_saved_campaign/native30_functional09_20261020.py"], "new-producer")

    def test_execution_retains_order_no_work_postcheck_and_final_guards(self):
        tree = ast.parse((HERE / "native30_functional09_20261020.py").read_text())
        node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "execute")
        calls = [(n.lineno, ast.unparse(n.func)) for n in ast.walk(node) if isinstance(n, ast.Call)]
        mkdir = next(line for line, name in calls if name == "STAGE.mkdir")
        for name in ("validate_card", "read_seed", "verify_owner_spec", "collect_readonly"):
            self.assertLess(next(line for line, called in calls if called == name), mkdir)
        names = {name for _, name in calls}
        for name in ("Q.Q.assert_no_work", "Q.final_delivery", "Q.immutable", "Q.exe_leases", "base.dependencies"):
            self.assertIn(name, names)
        source = ast.unparse(node)
        self.assertIn("fixture['postcheck']", source)
        self.assertNotIn("Q.execute(", source)
        self.assertNotIn("verify_admin(", source)

    def test_new_metadata_includes_all_owner_files_and_uses_allocation(self):
        rows = [{"path": "attempt09-functional/fixture.log", "eof": 1, "allocation": 8192},
                {"path": "owner09-functional/owner-spec/SPEC.json", "eof": 20, "allocation": 4096},
                {"path": "owner09-functional/UNREGISTER.json", "eof": 20, "allocation": 4096},
                {"path": "attempt08-admin/LAUNCH-RESULT.json", "eof": 1817, "allocation": 4096}]
        parent = lambda reserve=0: {"files": rows}
        card = {"owner_metadata_cap_bytes": 8192, "new_metadata_upper_bytes": 16384}
        guard = F.FunctionalScopeGuard(parent, card)
        guard()
        rows[2]["allocation"] = 8192
        with self.assertRaisesRegex(RuntimeError, "owner metadata cap"):
            guard()
        rows[2]["allocation"] = 4096
        rows[0]["allocation"] = 12288
        with self.assertRaisesRegex(RuntimeError, "complete new metadata cap"):
            guard()

    def test_source_has_no_admin_builder_or_module_mutation_route(self):
        source = (HERE / "native30_functional09_20261020.py").read_text()
        for forbidden in ("ShellExecute", "runas", "SameAdminDefenderClient", "register_manifest(",
                          "collect_manifest(", "--phase", "CMAKE_BUILD_PARALLEL_LEVEL=", "--build"):
            if forbidden == "--phase":
                continue  # Original SPEC validation names its historical build phase.
            self.assertNotIn(forbidden, source)
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    self.assertFalse(isinstance(target, ast.Attribute) and ast.unparse(target).startswith("Q."))

    def test_metadata160_parent_boundaries_and_old128_are_independent(self):
        mib = 1024**2
        changed = plan()
        changed["phase_metadata_cap_bytes"] = 128*mib
        with self.assertRaisesRegex(RuntimeError,"private metadata160"):
            F.verify_plan(changed)
        rows = [{"path": "evidence/meta.json", "eof": 148015296, "allocation": 148015296}]
        data = {"files": rows, "eof": 148015296, "allocation": 148015296, "raced": 0}
        base = SimpleNamespace(MIB=mib, inventory=lambda *a:data, utc=lambda:"synthetic")
        card = {"metadata_charge_cap_bytes": 160*mib, "deadline_utc":"2099-01-01T00:00:00Z",
                "hard_bytes":1536*mib, "minimum_free_bytes":0}
        original = F.Q.Q.SnapshotGuard.__call__
        with patch.object(F.shutil,"disk_usage",return_value=SimpleNamespace(free=10**12)):
            current = F.FunctionalParentGuard160(base,F.ROOT,card,None)
            current()
            self.assertEqual(current.last["metadata"],148015296)
            rows[0].update(eof=160*mib,allocation=160*mib)
            current()
            with self.assertRaisesRegex(RuntimeError,"component cap"):
                F.Q.Q.SnapshotGuard(base,F.ROOT,card,None)()
            for key, size in (("evidence/meta.json",160*mib+1),("source/a.cpp",96*mib+1),
                              ("attempt09-functional/.msvc-temp/a",384*mib+1)):
                rows[:] = [{"path":key,"eof":size,"allocation":size}]
                with self.subTest(key=key),self.assertRaisesRegex(RuntimeError,"component cap"):
                    current()
            rows[:] = []
            data["allocation"] = 1536*mib+1
            with self.assertRaisesRegex(RuntimeError,"aggregate cap"):
                current()
        self.assertIs(F.Q.Q.SnapshotGuard.__call__,original)


if __name__ == "__main__":
    unittest.main()
