"""No machine Task/Defender operations: broker and Win32 boundaries are fakes."""
import base64
import copy
import hashlib
import json
import ntpath
from pathlib import Path
import tempfile
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch

import project_exe_exclusion_broker_client as c
import register_project_exe_exclusions as h

OWNER = "S-1-5-21-100-200-300-1001"
INSTALL_ID = "36195828-225b-437c-b0e3-953c63c76b6c"


def raw(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode()


def digest(data):
    return hashlib.sha256(data).hexdigest()


class FakeBackend:
    def __init__(self, manifest):
        self.manifest = manifest
        self.files = {}
        self.task_runs = []
        self.published = []
        self.clock = 0.0
        self.mutate_result = lambda result: None
        self.produce_result = True
        self.stale_result = False
        self.changed_output = False
        self.task = {"folder": c.TASK_FOLDER, "name": c.TASK_NAME, "action": copy.deepcopy(c.ACTION),
                     "principal": {"user_id": "S-1-5-18", "logon_type": 5, "run_level": 1},
                     "actions_count": 1, "action_type": 0, "triggers_count": 0, "allow_demand_start": True,
                     "task_acl_protected": True, "folder_acl_protected": True}
        self.policy = {"broker_schema": c.POLICY_SCHEMA, "installation_id": INSTALL_ID, "owner_sid": OWNER,
            "repo_root": "D:/workspace/ck3_eternal_recurrence", "repo_common_dir": "D:/workspace/ck3_eternal_recurrence/.git",
            "allowed_external_source_roots": ["C:/research"], "allowed_build_roots": ["C:/research", "C:/w"],
            "forbidden_roots": ["C:/Windows", "C:/Program Files"], "runtime_root": c.INSTALL_ROOT,
            "inbox_dir": c.INSTALL_ROOT + r"\inbox", "frozen_dir": c.INSTALL_ROOT + r"\private-frozen",
            "receipts_dir": c.INSTALL_ROOT + r"\receipts", "runtime_manifest_sha256": "0" * 64,
            "max_request_bytes": 2097152, "max_files": 1024, "max_requests_per_run": 8,
            "request_budget_seconds": 60, "run_budget_seconds": 1}
        names = ["runtime/python.exe", "broker_bootstrap.py", "protected_runtime.py", "worker_core.py", "native_safety.py", "windows_adapter.py"]
        pins = []
        for name in names:
            data = b"fixed fake protected runtime " + name.encode()
            self.files[ntpath.join(c.INSTALL_ROOT, name)] = data
            pins.append({"path": name, "size": len(data), "sha256": digest(data)})
        self.files[c.SEAL_PATH] = raw({"schema": c.SEAL_SCHEMA, "installation_id": INSTALL_ID, "python_version": "3.14.7", "files": pins})
        self.policy["runtime_manifest_sha256"] = digest(self.files[c.SEAL_PATH])
        self.files[c.POLICY_PATH] = raw(self.policy)
        self.files[c.INSTALLATION_PATH] = raw({"schema": c.INSTALLATION_SCHEMA, "installation_id": INSTALL_ID, "owner_sid": OWNER,
            "policy": {"path": "policy.json", "size": len(self.files[c.POLICY_PATH]), "sha256": digest(self.files[c.POLICY_PATH])},
            "runtime_seal": {"path": "runtime-seal.json", "size": len(self.files[c.SEAL_PATH]), "sha256": digest(self.files[c.SEAL_PATH])},
            "task": {"folder": c.TASK_FOLDER, "name": c.TASK_NAME, "path": c.TASK_FOLDER + "\\" + c.TASK_NAME,
                     "action": copy.deepcopy(c.ACTION), "principal": {"user_id": "S-1-5-18", "logon_type": 5, "run_level": 1},
                     "triggers_count": 0, "allow_demand_start": True},
            "acl_policy": "BA/SY-owner-protected; inbox-owner-write; receipts-owner-read; private-SY/BA"})

    def exists(self, path):
        return path in self.files or (self.stale_result and path.endswith(".receipt.json"))

    def read_protected(self, path, limit):
        data = self.files[path]
        if len(data) > limit:
            raise ValueError("fake bounded read rejected")
        return data

    def verify_protected_file(self, path, size, sha256):
        data = self.files[path]
        if len(data) != size or digest(data) != sha256:
            raise ValueError("fake actual runtime bytes mismatch")

    def current_sid(self):
        return OWNER

    def task_contract(self, owner):
        assert owner == OWNER
        return copy.deepcopy(self.task)

    def publish_request(self, path, data, owner):
        if path in self.files:
            raise FileExistsError(path)
        assert owner == OWNER
        self.files[path] = data
        self.published.append((path, data))

    def run_task(self):
        self.task_runs.append(None)
        if not self.produce_result:
            return
        _, data = self.published[-1]
        request = json.loads(data)
        frozen = base64.b64decode(request["manifest_b64"], validate=True)
        manifest = json.loads(frozen)
        paths = [row["path"] for row in manifest["files"]]
        before = {"ExclusionPath": [r"C:\prior\keep.exe"], "ExclusionExtension": ["prior-extension"], "ExclusionProcess": [r"C:\prior\process.exe"]}
        after = copy.deepcopy(before)
        after["ExclusionPath"] += paths
        result = {"schema": c.SCHEMA, "broker_schema": c.RECEIPT_SCHEMA, "status": "verified", "admin_token": True,
                  "system_token_sid": "S-1-5-18", "settings_success_is_runtime_trust": False,
                  "files": manifest["files"], "manifest_sha256": digest(json.dumps(manifest, sort_keys=True).encode()),
                  "before": before["ExclusionPath"], "after": after["ExclusionPath"], "calls": [],
                  "before_settings": before, "after_settings": after, "observed_prior_settings_preserved": True,
                  "observed_extensions_unchanged": True, "observed_processes_unchanged": True,
                  "verified_requested_paths": paths, "missing_requested_paths": [], "partial_mutation": False,
                  "broker_identity": {"installation_id": INSTALL_ID, "owner_sid": OWNER, "request_id": request["request_id"],
                      "request_sha256": digest(data), "manifest_bytes_sha256": digest(frozen), "policy_sha256": digest(self.files[c.POLICY_PATH]),
                      "runtime_manifest_sha256": self.policy["runtime_manifest_sha256"], "runtime_verified": True,
                      "protected_code": True, "request_owner_sid": OWNER, "actual_token_sid": "S-1-5-18"}}
        self.mutate_result(result)
        result_path = ntpath.join(self.policy["receipts_dir"], request["request_id"] + ".receipt.json")
        # Deliberately noncanonical formatting: exact caller copy must preserve it.
        self.files[result_path] = (json.dumps(result, ensure_ascii=False, indent=4) + "\n\n").encode()

    def fingerprint(self, path):
        match = next(row for row in self.manifest["files"] if row["path"] == path)
        result = {key: match[key] for key in ("path", "size", "sha256")}
        if self.changed_output:
            result["sha256"] = "f" * 64
        return result

    def monotonic(self):
        return self.clock

    def sleep(self, seconds):
        self.clock += seconds


class ClientTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.manifest = {"schema": c.SCHEMA, "repo": "D:/workspace/ck3_eternal_recurrence", "source_dir": "C:/w/source",
                         "build_dir": "C:/w/build", "configuration": "Release", "requested_targets": ["fixture"],
                         "files": [{"path": r"C:\w\build\fixture.exe", "size": 128, "sha256": "a" * 64, "target": "fixture", "target_id": "fixture::id"}]}
        self.backend = FakeBackend(self.manifest)

    def dispatch(self):
        return c.dispatch_manifest(self.manifest, proof_dir=self.root / "proof", backend=self.backend)

    def reject(self, phrase):
        with self.assertRaises(c.BrokerValidationError) as raised:
            self.dispatch()
        self.assertIn(phrase, str(raised.exception))
        self.assertTrue((self.root / "proof/failure-proof.json").is_file())
        return raised.exception

    def test_success_exact_protocol_and_raw_result_copy(self):
        receipt = self.dispatch()
        self.assertEqual(receipt["status"], "verified")
        self.assertEqual(self.backend.task_runs, [None])
        path, request_raw = self.backend.published[0]
        request = json.loads(request_raw)
        self.assertEqual(set(request), {"schema", "request_id", "installation_id", "expected_policy_sha256", "producer_kind", "manifest_b64", "manifest_sha256"})
        self.assertEqual(request["producer_kind"], "cmake-file-api-v2")
        frozen = base64.b64decode(request["manifest_b64"], validate=True)
        self.assertEqual(json.loads(frozen), self.manifest)
        self.assertEqual(request["manifest_sha256"], digest(frozen))
        self.assertEqual(request_raw, (json.dumps(request, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode())
        self.assertTrue(path.startswith(self.backend.policy["inbox_dir"]))
        h._write_receipt(self.root / "caller.json", receipt)
        self.assertEqual((self.root / "caller.json").read_bytes(), receipt.broker_raw_bytes)
        self.assertEqual(receipt["files"], self.manifest["files"])
        self.assertNotEqual(receipt.broker_raw_bytes, raw(dict(receipt)))
        with self.assertRaises(FileExistsError):
            h._write_receipt(self.root / "caller.json", receipt)

    def test_command_producer_keeps_source_fields(self):
        self.manifest["command_provenance"] = {"kind": "msvc-explicit-command", "sources": [{"path": "C:/w/source/one.cpp"}]}
        self.dispatch()
        request = json.loads(self.backend.published[0][1])
        self.assertEqual(request["producer_kind"], "msvc-explicit-command-v1")
        self.assertEqual(json.loads(base64.b64decode(request["manifest_b64"])), self.manifest)

    def test_original_manifest_bytes_preserved_including_crlf(self):
        original = (json.dumps(self.manifest, ensure_ascii=False, indent=4) + "\n\n").replace("\n", "\r\n").encode()
        receipt = c.dispatch_manifest(self.manifest, proof_dir=self.root / "proof", backend=self.backend, manifest_bytes=original)
        request = json.loads(self.backend.published[0][1])
        self.assertEqual(base64.b64decode(request["manifest_b64"]), original)
        self.assertEqual(request["manifest_sha256"], digest(original))
        self.assertEqual((self.root / "proof/manifest.json").read_bytes(), original)
        self.assertEqual(receipt["broker_identity"]["manifest_bytes_sha256"], digest(original))

    def test_original_manifest_bytes_mismatch_never_published(self):
        mismatched = copy.deepcopy(self.manifest)
        mismatched["requested_targets"] = ["different"]
        with self.assertRaisesRegex(c.BrokerValidationError, "strict JSON"):
            c.dispatch_manifest(self.manifest, proof_dir=self.root / "proof", backend=self.backend, manifest_bytes=raw(mismatched))
        self.assertEqual(self.backend.published, [])
        self.assertEqual(self.backend.task_runs, [])

    def test_not_installed_has_no_task_or_artifact(self):
        del self.backend.files[c.POLICY_PATH]
        self.assertIsNone(self.dispatch())
        self.assertEqual(self.backend.task_runs, [])
        self.assertFalse((self.root / "proof").exists())

    def test_task_ack_without_result_times_out_no_success(self):
        self.backend.produce_result = False
        self.reject("no protected result")
        self.assertEqual(self.backend.task_runs, [None])
        self.assertLessEqual(self.backend.clock, 11.2)

    def test_preexisting_protected_result_is_stale_no_task(self):
        self.backend.stale_result = True
        self.reject("Stale/pre-existing")
        self.assertEqual(self.backend.published, [])
        self.assertEqual(self.backend.task_runs, [])

    def test_request_hash_wrong_preserves_raw_failure(self):
        self.backend.mutate_result = lambda r: r["broker_identity"].update(request_sha256="e" * 64)
        failure = self.reject("identity mismatch")
        pin = failure.proof["pins"]["protected-worker-receipt.json"]
        self.assertEqual(digest(Path(pin["path"]).read_bytes()), pin["sha256"])

    def test_current_exe_changed_result_rejected(self):
        self.backend.changed_output = True
        self.reject("EXE changed")

    def test_claimed_verified_partial_is_rejected(self):
        self.backend.mutate_result = lambda r: r.update(partial_mutation=True, missing_requested_paths=[self.manifest["files"][0]["path"]])
        self.reject("partial")

    def test_actual_bound_partial_failure_copies_exact_bytes(self):
        def partial(r):
            r.update(status="settings_failed", partial_mutation=True, error="provider stopped after first actual Add")
        self.backend.mutate_result = partial
        receipt = self.dispatch()
        self.assertEqual(receipt["status"], "settings_failed")
        h._write_receipt(self.root / "caller.json", receipt)
        self.assertEqual((self.root / "caller.json").read_bytes(), receipt.broker_raw_bytes)
        self.assertTrue(receipt["partial_mutation"])

    def test_lost_prior_setting_is_rejected(self):
        def remove_prior(r):
            r["after"].remove(r"C:\prior\keep.exe")
        self.backend.mutate_result = remove_prior
        self.reject("lost prior")

    def test_extension_change_is_rejected(self):
        self.backend.mutate_result = lambda r: r["after_settings"]["ExclusionExtension"].append("unauthorized")
        self.reject("extension/process")

    def test_missing_requested_path_is_rejected(self):
        self.backend.mutate_result = lambda r: r["after"].pop()
        self.reject("missing requested")

    def test_runtime_bool_is_strict(self):
        self.backend.mutate_result = lambda r: r["broker_identity"].update(runtime_verified=1)
        self.reject("strict true")

    def test_wrong_elevated_action_stops_before_publish(self):
        self.backend.task["action"]["arguments"] += " --arbitrary-command"
        self.reject("Task action")
        self.assertEqual(self.backend.published, [])
        self.assertEqual(self.backend.task_runs, [])

    def test_actual_runtime_file_hash_mismatch_stops_before_task(self):
        self.backend.files[ntpath.join(c.INSTALL_ROOT, "worker_core.py")] = b"modified ordinary bytes"
        self.reject("runtime bytes mismatch")
        self.assertEqual(self.backend.task_runs, [])

    def test_duplicate_policy_keys_rejected_before_task(self):
        self.backend.files[c.POLICY_PATH] = b'{"installation_id":"x","installation_id":"y"}'
        self.reject("Duplicate JSON")
        self.assertEqual(self.backend.task_runs, [])

    def test_raw_copy_refuses_modified_memory_receipt(self):
        receipt = self.dispatch()
        receipt["status"] = "forged"
        with self.assertRaisesRegex(ValueError, "raw receipt bytes differ"):
            h._write_receipt(self.root / "caller.json", receipt)
        self.assertFalse((self.root / "caller.json").exists())


class HelperIntegrationTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / "repo"
        self.source = self.repo / "ck3_autonomous_player/native_bridge"
        self.source.mkdir(parents=True)
        self.cpp = self.source / "actual.cpp"
        self.cpp.write_text("int main() {return 0;}")
        self.build = self.root / "build"
        self.build.mkdir()
        self.exe = self.build / "actual.exe"
        self.exe.write_bytes(b"MZ offline fixture")
        self.argv = [str(self.root / "cl.exe"), str(self.cpp), "/Fe" + str(self.exe)]
        self.manifest = h.collect_command_manifest(self.repo, self.source, self.build, self.argv, [self.exe])

    def register(self, **kwargs):
        with patch.object(h, "opted_in", return_value=True):
            return h.register_manifest(self.manifest, self.root / "caller.json", **kwargs)

    def test_explicit_admin_false_never_discovers_real_task(self):
        with patch.object(c, "dispatch_manifest", side_effect=AssertionError("must not run task")):
            result = self.register(admin=False)
        self.assertEqual(result["status"], "settings_failed")
        self.assertTrue(result["admin_required_for_verified_readback"])

    def test_fake_client_default_nonadmin_never_discovers_real_task(self):
        fake = NS(read_paths=lambda: (_ for _ in ()).throw(AssertionError("must not read WMI")))
        with patch.object(h.ctypes, "windll", NS(shell32=NS(IsUserAnAdmin=lambda: 0)), create=True), patch.object(c, "dispatch_manifest", side_effect=AssertionError("must not run task")):
            result = self.register(client=fake)
        self.assertEqual(result["status"], "settings_failed")

    def test_default_auto_absent_config_keeps_admin_required(self):
        with patch.object(h.ctypes, "windll", NS(shell32=NS(IsUserAnAdmin=lambda: 0)), create=True), patch.object(c, "dispatch_manifest", return_value=None) as dispatch:
            result = self.register()
        self.assertEqual(dispatch.call_count, 1)
        self.assertTrue(result["admin_required_for_verified_readback"])

    def test_injected_dispatch_preserves_exact_raw_outer_finally(self):
        receipt_value = {"schema": h.SCHEMA, "status": "verified", "files": self.manifest["files"], "settings_success_is_runtime_trust": False}
        protected = (json.dumps(receipt_value, indent=4) + "\n\n").encode()
        with patch.object(c, "dispatch_manifest", side_effect=AssertionError("must not resolve real client")):
            result = self.register(admin=False, broker_dispatch=lambda manifest, **kwargs: c.BrokerReceipt(receipt_value, protected))
        self.assertEqual(result["status"], "verified")
        self.assertEqual((self.root / "caller.json").read_bytes(), protected)

    def test_source_changed_never_dispatches(self):
        self.cpp.write_text("changed after manifest")
        dispatch = unittest.mock.Mock(side_effect=AssertionError("must not dispatch invalid producer"))
        result = self.register(admin=False, broker_dispatch=dispatch)
        self.assertEqual(result["status"], "settings_failed")
        self.assertEqual(dispatch.call_count, 0)

    def test_rejected_result_retains_failure_proof_in_caller(self):
        def reject(*args, **kwargs):
            raise c.BrokerValidationError("wrong actual request SHA", {"raw_pin": {"sha256": "e" * 64}})
        result = self.register(admin=False, broker_dispatch=reject)
        self.assertEqual(result["status"], "settings_failed")
        self.assertEqual(result["error_stage"], "broker-dispatch")
        self.assertEqual(result["broker_failure_proof"]["raw_pin"]["sha256"], "e" * 64)

    def test_build_hook_forwards_exact_created_manifest_bytes(self):
        submitted = []
        def dispatch(manifest, *, proof_dir, manifest_bytes):
            submitted.append(manifest_bytes)
            self.assertEqual(json.loads(manifest_bytes), manifest)
            receipt = {"schema": h.SCHEMA, "status": "verified", "files": manifest["files"], "settings_success_is_runtime_trust": False}
            return c.BrokerReceipt(receipt, raw(receipt))
        with patch.object(h, "opted_in", return_value=True), patch.object(h.ctypes, "windll", NS(shell32=NS(IsUserAnAdmin=lambda: 0)), create=True), patch.object(c, "dispatch_manifest", side_effect=dispatch):
            result = h.after_successful_command_build(self.repo, self.source, self.build, self.argv, [self.exe])
        self.assertEqual(result["status"], "verified")
        self.assertEqual(submitted, [Path(result["manifest"]).read_bytes()])
        self.assertEqual(result["receipt_sha256"], digest(Path(result["receipt"]).read_bytes()))


class ProtectionPredicateTest(unittest.TestCase):
    def check(self, aces, owner=c.ADMIN_SID, control=0x1000, task_owner_sid=None):
        dacl = NS(GetAceCount=lambda: len(aces), GetAce=lambda i: aces[i])
        sd = NS(GetSecurityDescriptorOwner=lambda: owner, GetSecurityDescriptorDacl=lambda: dacl,
                GetSecurityDescriptorControl=lambda: (control, 1))
        module = NS(ConvertSidToStringSid=lambda value: value)
        with patch.dict("sys.modules", {"win32security": module}):
            c.WindowsBackend._validate_acl(sd, task_owner_sid=task_owner_sid)

    def test_owner_read_run_allowed_but_write_delete_rejected(self):
        self.check([((0, 0), 0xA0000000, OWNER), ((0, 0), 0x10000000, c.SYSTEM_SID), ((0, 0), 0x10000000, c.ADMIN_SID)])
        for access in (0x40000000, 0x10000, 0x40000, 0x2, 0x40, 0x02000000):
            with self.subTest(access=access), self.assertRaises(ValueError):
                self.check([((0, 0), access, OWNER)])

    def test_untrusted_protected_owner_rejected(self):
        with self.assertRaisesRegex(ValueError, "BA/SY owned"):
            self.check([], owner=OWNER)

    def test_inheriting_dacl_cannot_claim_protected(self):
        with self.assertRaisesRegex(ValueError, "not protected"):
            self.check([((0, 0), 0x10000000, c.SYSTEM_SID)], control=0)

    def test_task_allows_only_fixed_owner_read_run_and_system_admin(self):
        aces = [((0, 0), 0x10000000, c.SYSTEM_SID), ((0, 0), 0x10000000, c.ADMIN_SID), ((0, 0), 0xA0000000, OWNER)]
        self.check(aces, task_owner_sid=OWNER)
        for extra in (((0, 0), 0x80000000, "S-1-1-0"), ((0, 0), 0x40, OWNER)):
            with self.subTest(extra=extra), self.assertRaisesRegex(ValueError, "third-party or excess"):
                self.check(aces + [extra], task_owner_sid=OWNER)
        with self.assertRaisesRegex(ValueError, "lacks fixed"):
            self.check(aces[:-1], task_owner_sid=OWNER)

    def test_task_mapped_equivalent_read_run_mask(self):
        aces = [((0, 0), 0x1F01FF, c.SYSTEM_SID), ((0, 0), 0x1F01FF, c.ADMIN_SID), ((0, 0), 0x1200A9, OWNER)]
        self.check(aces, task_owner_sid=OWNER)


class InboxPublicationLeaseTest(unittest.TestCase):
    def fake_native(self, directory=True, mutate=None):
        from contextlib import contextmanager
        constants = NS(GENERIC_READ=0x80000000, FILE_SHARE_READ=1, FILE_SHARE_WRITE=2,
                       OPEN_EXISTING=3, FILE_FLAG_BACKUP_SEMANTICS=0x02000000,
                       FILE_ATTRIBUTE_REPARSE_POINT=0x400, FILE_ATTRIBUTE_DIRECTORY=0x10,
                       FILE_TYPE_DISK=1)
        self.opens = []
        leaf_path = c.INSTALL_ROOT + (r"\inbox" if directory else r"\policy.json")
        state = {"post": False}
        def create(path, access, sharing, security, disposition, flags, template):
            handle = NS(path=path, sharing=sharing, Close=lambda: None)
            self.opens.append(handle)
            return handle
        def info(handle):
            leaf = c._same_path(handle.path, leaf_path)
            attrs = 0x10 if directory or not leaf else 0
            value = (attrs, 0, 0, 0, 100, 0, 0, 1, 0, 200)
            if leaf and state["post"] and mutate == "identity":
                value = (*value[:9], 201)
            if leaf and state["post"] and mutate == "reparse":
                value = (value[0] | 0x400, *value[1:])
            return value
        def final(handle, flags):
            if state["post"] and mutate == "path":
                return c.INSTALL_ROOT + r"\changed-inbox"
            return "\\\\?\\" + handle.path
        fileapi = NS(CreateFile=create, GetFileInformationByHandle=info, GetFileType=lambda h: 1,
                     GetFinalPathNameByHandle=final, FILE_FLAG_OPEN_REPARSE_POINT=0x00200000)
        security = NS(SE_FILE_OBJECT=1, OWNER_SECURITY_INFORMATION=1, DACL_SECURITY_INFORMATION=4,
                      GetSecurityInfo=lambda *args: NS())
        @contextmanager
        def context():
            with patch.dict("sys.modules", {"win32con": constants, "win32file": fileapi, "win32security": security}), patch.object(c.WindowsBackend, "_validate_acl"):
                yield state
        return context(), leaf_path

    def test_write_share_only_fixed_inbox_and_default_files_remain_readonly(self):
        backend = c.WindowsBackend()
        fixture, inbox = self.fake_native()
        with fixture as state:
            with backend._locked(inbox, write_sid=OWNER, directory=True, inbox_publication=True):
                self.assertEqual(self.opens[-1].sharing, 3)
                self.assertTrue(all(handle.sharing == 3 for handle in self.opens[:-1]))
                self.assertTrue(all(not handle.sharing & 4 for handle in self.opens))
                state["post"] = True
        fixture, file_path = self.fake_native(directory=False)
        with fixture:
            with backend._locked(file_path):
                self.assertEqual(self.opens[-1].sharing, 1)

    def test_publication_flag_cannot_relax_runtime_or_other_directory(self):
        fixture, _ = self.fake_native()
        with fixture:
            for path, kwargs in ((c.INSTALL_ROOT + r"\runtime", {"write_sid": OWNER, "directory": True}),
                                 (c.POLICY_PATH, {"write_sid": OWNER, "directory": False}),
                                 (c.INSTALL_ROOT + r"\inbox", {"directory": True})):
                with self.subTest(path=path), self.assertRaisesRegex(ValueError, "restricted to fixed inbox"):
                    with c.WindowsBackend()._locked(path, inbox_publication=True, **kwargs):
                        self.fail("Must reject before any open")
            self.assertEqual(self.opens, [])

    def test_publication_revalidates_directory_identity_before_task_can_run(self):
        fixture, path = self.fake_native(mutate="identity")
        with fixture as state, self.assertRaisesRegex(ValueError, "identity/type changed"):
            with c.WindowsBackend()._locked(path, write_sid=OWNER, directory=True, inbox_publication=True):
                state["post"] = True

    def test_publication_rejects_post_reparse_and_final_path_change(self):
        for mutation in ("reparse", "path"):
            fixture, path = self.fake_native(mutate=mutation)
            with self.subTest(mutation=mutation), fixture as state, self.assertRaises(ValueError):
                with c.WindowsBackend()._locked(path, write_sid=OWNER, directory=True, inbox_publication=True):
                    state["post"] = True


if __name__ == "__main__":
    unittest.main()
