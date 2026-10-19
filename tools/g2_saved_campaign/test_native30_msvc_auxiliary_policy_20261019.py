"""Finite safety-contract checks; no compiler, process termination, or Game use."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

PATH = Path(__file__).with_name("native30_msvc_auxiliary_policy_20261019.py")
SPEC = importlib.util.spec_from_file_location("native30_aux_policy_tested", PATH)
POLICY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(POLICY)

def image(name="vctip.exe", value="file-v", digest="sha-v", parent="C:\\MSVC\\bin"):
    return {"canonical_path": parent + "\\" + name,
            "file_id": {"volume_serial": "1", "file_id": value}, "sha256": digest}

BINDING = {"auxiliaries": {"vctip.exe": image(), "mspdbsrv.exe": image("mspdbsrv.exe", "file-m", "sha-m")}}

class Fake:
    def __init__(self, rows=(), root_wait=0, root_code=0):
        self.rows = {row["pid"]: row for row in rows}
        self.live = set(self.rows)
        self.terminated, self.closed = [], []
        self.root_wait_value, self.root_code = root_wait, root_code
        self.now = 0.0
        self.in_job, self.wait_override = True, None
        self.add_unknown_after_cleanup = False
        self.belongs_calls, self.change_membership_at = 0, None
    def root_wait(self): return self.root_wait_value
    def root_exit(self): return self.root_code
    def active(self): return len(self.live)
    def members(self): return sorted(self.live)
    def open(self, pid): return pid
    def identity(self, handle): return self.rows[handle]
    def belongs(self, handle):
        self.belongs_calls += 1
        return self.in_job and self.belongs_calls != self.change_membership_at
    def wait(self, handle, milliseconds):
        return self.wait_override if self.wait_override is not None else (258 if handle in self.live else 0)
    def terminate(self, handle):
        self.terminated.append(handle)
        self.live.remove(handle)
        if self.add_unknown_after_cleanup: self.live.add(999)
    def close(self, handle): self.closed.append(handle)
    def exit_code(self, handle): return 74 if handle not in self.live else 259
    def clock(self): return self.now
    def sleep(self, value): self.now += value

def row(pid=1, actual=None):
    return {"pid": pid, "creation_filetime": str(1000 + pid), "image": actual or image()}

def finish(fake, state=None):
    return POLICY.finish_command(fake, BINDING, lambda: None, grace_seconds=0, cleanup_seconds=.2,
                                 clock=fake.clock, sleep=fake.sleep, state=state)

class Contract(unittest.TestCase):
    def rejected(self, fake):
        with self.assertRaises(POLICY.AuxiliaryContractError): finish(fake)
        self.assertEqual(fake.terminated, [])

    def test_retained_command_must_be_signaled(self): self.rejected(Fake([row()], root_wait=258))
    def test_original_nonzero_is_never_success(self): self.rejected(Fake([row()], root_code=1))
    def test_still_active_exit_value_is_not_zero(self): self.rejected(Fake([row()], root_code=259))
    def test_empty_job_needs_no_auxiliary_cleanup(self):
        result = finish(Fake())
        self.assertEqual(result["owned_active_after"], 0)
        self.assertEqual(result["auxiliary_forced_cleanup"], [])
        self.assertEqual(result["original_root_exit_code"], 0)
    def test_exact_two_tools_are_separately_recorded(self):
        fake = Fake([row(), row(2, image("mspdbsrv.exe", "file-m", "sha-m"))])
        result = finish(fake)
        self.assertEqual(fake.terminated, [1, 2])
        self.assertEqual(sorted(fake.closed), [1, 2])
        self.assertEqual([r["tool"] for r in result["auxiliary_forced_cleanup"]], ["vctip.exe", "mspdbsrv.exe"])
        self.assertEqual(result["original_root_exit_code"], 0)
    def test_basename_alone_does_not_admit_a_tool(self):
        self.rejected(Fake([row(actual=image(parent="C:\\other"))]))
    def test_other_filename_is_not_a_known_tool(self):
        self.rejected(Fake([row(actual=image("compiler.exe"))]))
    def test_file_id_change_rejected(self): self.rejected(Fake([row(actual=image(value="replacement"))]))
    def test_digest_change_rejected(self): self.rejected(Fake([row(actual=image(digest="different"))]))
    def test_full_set_validates_before_any_termination(self):
        self.rejected(Fake([row(), row(2, image("unknown.exe"))]))
    def test_member_outside_original_job_rejected(self):
        fake = Fake([row()]); fake.in_job = False
        self.rejected(fake)
    def test_member_already_exited_is_not_reopened_by_pid(self):
        fake = Fake([row()]); fake.wait_override = 0
        self.rejected(fake)
    def test_membership_rechecked_before_first_termination(self):
        fake = Fake([row(), row(2, image("mspdbsrv.exe", "file-m", "sha-m"))])
        fake.change_membership_at = 3
        self.rejected(fake)
    def test_finite_member_limit(self): self.rejected(Fake([row(n) for n in range(1, 18)]))
    def test_unknown_new_member_never_gets_terminated(self):
        fake = Fake([row()]); fake.add_unknown_after_cleanup = True
        state = {}
        with self.assertRaises(POLICY.AuxiliaryContractError): finish(fake, state)
        self.assertEqual(fake.terminated, [1])
        self.assertIn(999, fake.live)
        self.assertEqual(len(state["auxiliary_forced_cleanup"]), 1)
    def test_volume_id_is_part_of_file_identity(self):
        actual = image(); actual["file_id"] = {"volume_serial": "2", "file_id": "file-v"}
        self.rejected(Fake([row(actual=actual)]))

class FailureJournal(unittest.TestCase):
    def exercise(self, stop_fails=False):
        process = SimpleNamespace(pid=123, process=object(), count=1, closed=False)
        process.processapi = SimpleNamespace(GetExitCodeProcess=lambda handle: 73)
        process.active = lambda: process.count
        def stop():
            if stop_fails: raise RuntimeError("owned Job remains")
            process.count = 0
        process.stop = stop
        process.close = lambda: setattr(process, "closed", True)
        records = []
        base = SimpleNamespace(utc=lambda: "test-UTC", OwnedJob=lambda *args: process,
                               write=lambda path, body: records.append(dict(body)))
        state = {}
        with patch.object(POLICY, "OwnedBackend", side_effect=RuntimeError("binding initialization failed")):
            with self.assertRaises(RuntimeError):
                POLICY.run_owned(base, [], Path("."), {}, Path("not-created.log"),
                                 lambda *args: None, BINDING, state=state)
        self.assertTrue(process.closed)
        self.assertTrue(state["failure_job_termination"])
        self.assertEqual(len(records), 1)
        return state
    def test_backend_initialization_failure_still_stops_only_owned_job(self):
        self.assertEqual(self.exercise()["owned_active_after"], 0)
    def test_failed_cleanup_keeps_actual_nonzero_in_journal(self):
        self.assertEqual(self.exercise(stop_fails=True)["owned_active_after"], 1)

if __name__ == "__main__": unittest.main(verbosity=2)
