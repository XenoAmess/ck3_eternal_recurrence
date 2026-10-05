#!/usr/bin/env python3
"""Ordinary-owner client for the fixed, separately installed project EXE broker.

This module does not enroll/install, elevate, use WMI, or change Defender itself.
The backend parameter is a test seam; production never obtains paths from env.
"""
from __future__ import annotations

import base64
from contextlib import ExitStack, contextmanager
import hashlib
import json
import ntpath
import os
from pathlib import Path
import re
import subprocess
import time
import uuid

INSTALL_ROOT = r"C:\Program Files\XAR CK3 Project EXE Broker"
POLICY_PATH = INSTALL_ROOT + r"\policy.json"
SEAL_PATH = INSTALL_ROOT + r"\runtime-seal.json"
INSTALLATION_PATH = INSTALL_ROOT + r"\installation-manifest.json"
TASK_FOLDER = r"\XAR CK3 Project EXE Broker"
TASK_NAME = "RegisterDeclaredProjectExecutables"
SYSTEM_SID = "S-1-5-18"
ADMIN_SID = "S-1-5-32-544"
SCHEMA = "xar.project-exe-exclusions.v1"
POLICY_SCHEMA = "xar.project-exe-broker.policy.v1"
REQUEST_SCHEMA = "xar.project-exe-broker.request.v1"
RECEIPT_SCHEMA = "xar.project-exe-broker.receipt.v1"
SEAL_SCHEMA = "xar.project-exe-broker.runtime-seal.v1"
INSTALLATION_SCHEMA = "xar.project-exe-broker.installation-manifest.v1"
POLICY_KEYS = set("broker_schema installation_id owner_sid repo_root repo_common_dir allowed_external_source_roots allowed_build_roots forbidden_roots inbox_dir frozen_dir receipts_dir runtime_root runtime_manifest_sha256 max_request_bytes max_files max_requests_per_run request_budget_seconds run_budget_seconds".split())
IDENTITY_KEYS = set("installation_id owner_sid request_id request_sha256 manifest_bytes_sha256 policy_sha256 runtime_manifest_sha256 runtime_verified protected_code request_owner_sid actual_token_sid".split())
SETTING_KEYS = {"ExclusionPath", "ExclusionExtension", "ExclusionProcess"}
ACTION = {"path": INSTALL_ROOT + r"\runtime\python.exe",
          "arguments": subprocess.list2cmdline(["-I", "-S", "-B", INSTALL_ROOT + r"\broker_bootstrap.py", "--config", POLICY_PATH]),
          "working_directory": INSTALL_ROOT}


class BrokerValidationError(RuntimeError):
    def __init__(self, message: str, proof: dict | None = None):
        super().__init__(message)
        self.proof = proof or {}


class BrokerReceipt(dict):
    """In-memory metadata only: caller must copy these exact protected bytes."""
    def __init__(self, value: dict, raw: bytes):
        super().__init__(value)
        self.broker_raw_bytes = raw


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _strict_json(raw: bytes):
    def pairs(rows):
        result = {}
        for key, value in rows:
            if key in result:
                raise ValueError("Duplicate JSON key")
            result[key] = value
        return result
    def no_float(value):
        raise ValueError("Float or nonfinite JSON value is forbidden")
    return json.loads(raw.decode("utf-8"), object_pairs_hook=pairs,
                      parse_float=no_float, parse_constant=no_float)


def _uuid(value: str) -> bool:
    try:
        return isinstance(value, str) and str(uuid.UUID(value)) == value
    except (ValueError, AttributeError):
        return False


def _hash(value) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def _canonical_path(value: str) -> str:
    if not isinstance(value, str) or not value or any(c in value for c in "*?%\x00"):
        raise ValueError("Invalid local path")
    drive, tail = ntpath.splitdrive(value)
    if not re.fullmatch(r"[A-Za-z]:", drive) or not tail.startswith(("\\", "/")) or ":" in tail:
        raise ValueError("Absolute local non-ADS path required")
    parts = tail.replace("/", "\\").split("\\")
    if any(p in (".", "..") or p.endswith((".", " ")) for p in parts if p):
        raise ValueError("Noncanonical path component")
    return ntpath.normcase(ntpath.normpath(value))


def _same_path(left: str, right: str) -> bool:
    return _canonical_path(left) == _canonical_path(right)


def _validate_policy(policy: dict) -> None:
    if not isinstance(policy, dict) or set(policy) != POLICY_KEYS or policy["broker_schema"] != POLICY_SCHEMA:
        raise ValueError("Installed policy schema/keys mismatch")
    if not _uuid(policy["installation_id"]) or not re.fullmatch(r"S-1-(?:\d+-)+\d+", policy["owner_sid"]):
        raise ValueError("Installed UUID/owner SID mismatch")
    if not _hash(policy["runtime_manifest_sha256"]):
        raise ValueError("Installed runtime seal SHA invalid")
    for key, child in (("runtime_root", ""), ("inbox_dir", "inbox"), ("frozen_dir", "private-frozen"), ("receipts_dir", "receipts")):
        if not _same_path(policy[key], ntpath.join(INSTALL_ROOT, child)):
            raise ValueError("Installed policy must use fixed protected directories")
    for key in ("repo_root", "repo_common_dir"):
        _canonical_path(policy[key])
    for key in ("allowed_external_source_roots", "allowed_build_roots", "forbidden_roots"):
        if not isinstance(policy[key], list) or len(policy[key]) > 1024:
            raise ValueError("Installed path policy list invalid")
        for item in policy[key]:
            _canonical_path(item)
    limits = {"max_request_bytes": 2 * 1024 * 1024, "max_files": 1024,
              "max_requests_per_run": 1024, "request_budget_seconds": 180, "run_budget_seconds": 180}
    for key, bound in limits.items():
        if type(policy[key]) is not int or not 1 <= policy[key] <= bound:
            raise ValueError("Installed finite budget invalid")


def validate_task_contract(task: dict) -> None:
    expected = {"folder": TASK_FOLDER, "name": TASK_NAME, "action": ACTION,
                "principal": {"user_id": SYSTEM_SID, "logon_type": 5, "run_level": 1},
                "actions_count": 1, "action_type": 0, "triggers_count": 0,
                "allow_demand_start": True, "task_acl_protected": True, "folder_acl_protected": True}
    if task != expected or any(task.get(key) is not True for key in ("allow_demand_start", "task_acl_protected", "folder_acl_protected")):
        raise ValueError("Installed Task action/principal/ACL differs from fixed contract")


def _validate_settings(value) -> dict:
    if not isinstance(value, dict) or set(value) != SETTING_KEYS:
        raise ValueError("Three-setting readback missing")
    if any(not isinstance(rows, list) or any(not isinstance(item, str) for item in rows) for rows in value.values()):
        raise ValueError("Invalid settings readback arrays")
    return value


def _path_set(rows: list[str]) -> set[str]:
    # Existing Defender paths can be wildcard/directory entries; compare them
    # without interpreting or authorizing them as requested EXE paths.
    return {ntpath.normcase(ntpath.normpath(item)) for item in rows}


def _validate_receipt(value: dict, manifest: dict, policy: dict, expected: dict, backend) -> None:
    if not isinstance(value, dict) or value.get("schema") != SCHEMA or value.get("broker_schema") != RECEIPT_SCHEMA:
        raise ValueError("Protected result schema mismatch")
    identity = value.get("broker_identity")
    if not isinstance(identity, dict) or set(identity) != IDENTITY_KEYS or identity != expected:
        raise ValueError("Protected result request/installation/runtime identity mismatch")
    if identity["runtime_verified"] is not True or identity["protected_code"] is not True:
        raise ValueError("Protected result runtime proof must be strict true")
    if value.get("admin_token") is not True or value.get("system_token_sid") != SYSTEM_SID:
        raise ValueError("Protected result lacks actual SYSTEM/admin token")
    if value.get("settings_success_is_runtime_trust") is not False:
        raise ValueError("Protected result claims unsupported runtime trust")
    if value.get("files") != manifest["files"]:
        raise ValueError("Protected result EXE rows differ from exact requested rows")
    semantic_hash = _sha(json.dumps(manifest, sort_keys=True).encode())
    if value.get("manifest_sha256") != semantic_hash:
        raise ValueError("Protected result semantic source binding mismatch")
    for row in manifest["files"]:
        if backend.fingerprint(row["path"]) != {key: row[key] for key in ("path", "size", "sha256")}:
            raise ValueError("Requested EXE changed before result acceptance")
    if value.get("status") not in ("verified", "settings_failed"):
        raise ValueError("Protected result has no completed status")
    if value["status"] == "settings_failed":
        # Preserve fully bound actual failure/partial bytes. It grants no success.
        return
    before = _validate_settings(value.get("before_settings"))
    after = _validate_settings(value.get("after_settings"))
    if value.get("before") != before["ExclusionPath"] or value.get("after") != after["ExclusionPath"]:
        raise ValueError("Protected result path arrays disagree with three-setting proof")
    requested = [row["path"] for row in manifest["files"]]
    if not _path_set(requested) <= _path_set(after["ExclusionPath"]):
        raise ValueError("Protected verified result is missing requested exact paths")
    if not _path_set(before["ExclusionPath"]) <= _path_set(after["ExclusionPath"]):
        raise ValueError("Protected verified result lost prior paths")
    if set(before["ExclusionExtension"]) != set(after["ExclusionExtension"]) or set(before["ExclusionProcess"]) != set(after["ExclusionProcess"]):
        raise ValueError("Protected verified result changed extension/process exclusions")
    for field in ("observed_prior_settings_preserved", "observed_extensions_unchanged", "observed_processes_unchanged"):
        if value.get(field) is not True:
            raise ValueError("Protected verified result readback flags missing")
    if value.get("partial_mutation") is not False or value.get("missing_requested_paths") != [] or value.get("verified_requested_paths") != requested:
        raise ValueError("Protected verified result is partial or contradicts requested paths")


def dispatch_manifest(manifest: dict, *, proof_dir: Path, backend=None, manifest_bytes: bytes | None = None) -> BrokerReceipt | None:
    """Return None only if not installed; else a bound receipt or explicit error.

    register_manifest has already checked fresh ordinary producer evidence.
    This client rechecks output hashes when accepting the protected result.
    """
    backend = WindowsBackend() if backend is None else backend
    if not backend.exists(POLICY_PATH):
        return None
    proof_dir = Path(proof_dir)
    proof_dir.mkdir(parents=True, exist_ok=False)
    proof = {"proof_dir": str(proof_dir), "pins": {}, "stage": "policy-read"}
    def preserve(name, raw):
        path = proof_dir / name
        with path.open("xb") as handle:
            handle.write(raw)
        proof["pins"][name] = {"path": str(path), "size": len(raw), "sha256": _sha(raw)}
    try:
        raw_policy = backend.read_protected(POLICY_PATH, 2 * 1024 * 1024)
        preserve("installed-policy.json", raw_policy)
        policy = _strict_json(raw_policy)
        _validate_policy(policy)
        if backend.current_sid() != policy["owner_sid"]:
            raise ValueError("Ordinary caller is not the installed authorized owner SID")
        proof["stage"] = "installed-runtime-read"
        raw_seal = backend.read_protected(SEAL_PATH, 16 * 1024 * 1024)
        preserve("installed-runtime-seal.json", raw_seal)
        if _sha(raw_seal) != policy["runtime_manifest_sha256"]:
            raise ValueError("Installed runtime seal differs from protected policy")
        seal = _strict_json(raw_seal)
        if not isinstance(seal, dict) or set(seal) != {"schema", "installation_id", "python_version", "files"} or seal["schema"] != SEAL_SCHEMA or seal["installation_id"] != policy["installation_id"] or seal["python_version"] != "3.14.7":
            raise ValueError("Installed runtime seal identity mismatch")
        if not isinstance(seal["files"], list) or not 1 <= len(seal["files"]) <= 50000:
            raise ValueError("Installed runtime inventory invalid")
        seen = set()
        for row in seal["files"]:
            if not isinstance(row, dict) or set(row) != {"path", "size", "sha256"} or type(row["size"]) is not int or row["size"] < 0 or not _hash(row["sha256"]):
                raise ValueError("Installed runtime file pin invalid")
            relative = row["path"]
            if not isinstance(relative, str) or relative.startswith(("/", "\\")) or ntpath.splitdrive(relative)[0] or any(part in ("", ".", "..") for part in relative.replace("\\", "/").split("/")):
                raise ValueError("Installed runtime inventory path escapes root")
            absolute = ntpath.join(INSTALL_ROOT, relative)
            key = _canonical_path(absolute)
            if key in seen:
                raise ValueError("Installed runtime inventory duplicate path")
            seen.add(key)
            backend.verify_protected_file(absolute, row["size"], row["sha256"])
        required = {"runtime/python.exe", "broker_bootstrap.py", "protected_runtime.py", "worker_core.py", "native_safety.py", "windows_adapter.py"}
        if not required <= {row["path"].replace("\\", "/") for row in seal["files"]}:
            raise ValueError("Installed runtime inventory lacks required protected entry points")
        raw_installation = backend.read_protected(INSTALLATION_PATH, 2 * 1024 * 1024)
        preserve("installed-manifest.json", raw_installation)
        installation = _strict_json(raw_installation)
        expected_installation = {"schema": INSTALLATION_SCHEMA, "installation_id": policy["installation_id"], "owner_sid": policy["owner_sid"],
            "policy": {"path": "policy.json", "size": len(raw_policy), "sha256": _sha(raw_policy)},
            "runtime_seal": {"path": "runtime-seal.json", "size": len(raw_seal), "sha256": _sha(raw_seal)},
            "task": {"folder": TASK_FOLDER, "name": TASK_NAME, "path": TASK_FOLDER + "\\" + TASK_NAME, "action": ACTION,
                     "principal": {"user_id": SYSTEM_SID, "logon_type": 5, "run_level": 1}, "triggers_count": 0, "allow_demand_start": True},
            "acl_policy": "BA/SY-owner-protected; inbox-owner-write; receipts-owner-read; private-SY/BA"}
        if installation != expected_installation:
            raise ValueError("Protected installation manifest differs from current policy/seal/fixed action")
        proof["stage"] = "task-contract-read"
        task = backend.task_contract(policy["owner_sid"])
        validate_task_contract(task)
        preserve("task-readback.json", (json.dumps(task, sort_keys=True, indent=2) + "\n").encode())
        if not isinstance(manifest, dict) or manifest.get("schema") != SCHEMA or not isinstance(manifest.get("files"), list) or not 1 <= len(manifest["files"]) <= policy["max_files"]:
            raise ValueError("Manifest schema/files invalid")
        for row in manifest["files"]:
            if not isinstance(row, dict) or type(row.get("size")) is not int or row["size"] < 0 or not _hash(row.get("sha256")) or not isinstance(row.get("path"), str) or not row["path"].lower().endswith(".exe"):
                raise ValueError("Requested EXE file pin invalid")
        # Reject unsupported numeric types/duplicate-normalized outputs before publish.
        raw_manifest = (json.dumps(manifest, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8") if manifest_bytes is None else manifest_bytes
        if not isinstance(raw_manifest, bytes):
            raise ValueError("Original manifest bytes must be bytes")
        if _strict_json(raw_manifest) != manifest:
            raise ValueError("Manifest cannot be represented by strict JSON")
        if len({_canonical_path(row["path"]) for row in manifest["files"]}) != len(manifest["files"]):
            raise ValueError("Duplicate requested output path")
        preserve("manifest.json", raw_manifest)
        request_id = str(uuid.uuid4())
        request = {"schema": REQUEST_SCHEMA, "request_id": request_id, "installation_id": policy["installation_id"],
                   "expected_policy_sha256": _sha(raw_policy), "producer_kind": "msvc-explicit-command-v1" if "command_provenance" in manifest else "cmake-file-api-v2",
                   "manifest_b64": base64.b64encode(raw_manifest).decode("ascii"), "manifest_sha256": _sha(raw_manifest)}
        raw_request = (json.dumps(request, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")
        if len(raw_request) > policy["max_request_bytes"]:
            raise ValueError("Request exceeds installed byte budget")
        preserve("request.json", raw_request)
        request_path = ntpath.join(policy["inbox_dir"], request_id + ".request.json")
        result_path = ntpath.join(policy["receipts_dir"], request_id + ".receipt.json")
        proof.update(request_id=request_id, request_path=request_path, protected_result_path=result_path, request_sha256=_sha(raw_request))
        if backend.exists(result_path) or backend.exists(request_path):
            raise ValueError("Stale/pre-existing request or protected result UUID")
        proof["stage"] = "request-publish"
        backend.publish_request(request_path, raw_request, policy["owner_sid"])
        proof["stage"] = "task-run"
        backend.run_task()
        # ACK is deliberately not a completion state. A failed/late worker remains a failure.
        proof["stage"] = "protected-result-wait"
        deadline = backend.monotonic() + policy["run_budget_seconds"] + 10
        while not backend.exists(result_path):
            if backend.monotonic() >= deadline:
                raise TimeoutError("Task ACK received but no protected result within bound")
            backend.sleep(min(0.2, max(0, deadline - backend.monotonic())))
        raw_result = backend.read_protected(result_path, 16 * 1024 * 1024)
        preserve("protected-worker-receipt.json", raw_result)
        proof["stage"] = "result-validation"
        expected = {"installation_id": policy["installation_id"], "owner_sid": policy["owner_sid"], "request_id": request_id,
                    "request_sha256": _sha(raw_request), "manifest_bytes_sha256": _sha(raw_manifest), "policy_sha256": _sha(raw_policy),
                    "runtime_manifest_sha256": policy["runtime_manifest_sha256"], "runtime_verified": True, "protected_code": True,
                    "request_owner_sid": policy["owner_sid"], "actual_token_sid": SYSTEM_SID}
        receipt = _strict_json(raw_result)
        _validate_receipt(receipt, manifest, policy, expected, backend)
        proof.update(status=receipt["status"], copied_receipt_bytes_sha256=_sha(raw_result))
        preserve("proof.json", (json.dumps(proof, sort_keys=True, ensure_ascii=False, indent=2) + "\n").encode())
        return BrokerReceipt(receipt, raw_result)
    except Exception as error:
        proof.update(status="client_rejected", error=str(error), error_type=type(error).__name__)
        failure_path = proof_dir / "failure-proof.json"
        with failure_path.open("x", encoding="utf-8") as handle:
            json.dump(proof, handle, sort_keys=True, ensure_ascii=False, indent=2)
            handle.write("\n")
        proof["failure_proof"] = {"path": str(failure_path), "size": failure_path.stat().st_size, "sha256": _sha(failure_path.read_bytes())}
        raise BrokerValidationError(str(error), proof) from error


class WindowsBackend:
    """Deferred Win32/TaskScheduler only; no Defender/WMI or UAC calls."""
    def __init__(self):
        self._task = None
        self._task_owner = None

    def exists(self, path):
        return os.path.lexists(path)

    @staticmethod
    def monotonic():
        return time.monotonic()

    @staticmethod
    def sleep(seconds):
        time.sleep(seconds)

    @staticmethod
    def current_sid():
        import win32api
        import win32con
        import win32security
        token = win32security.OpenProcessToken(win32api.GetCurrentProcess(), win32con.TOKEN_QUERY)
        try:
            value = win32security.GetTokenInformation(token, win32security.TokenUser)
            sid = value[0] if isinstance(value, tuple) else value
            return win32security.ConvertSidToStringSid(sid)
        finally:
            token.Close()

    @staticmethod
    def _validate_acl(sd, *, write_sid=None, task_owner_sid=None):
        import win32security
        owner = win32security.ConvertSidToStringSid(sd.GetSecurityDescriptorOwner())
        if owner not in (SYSTEM_SID, ADMIN_SID):
            raise ValueError("Installed protected object is not BA/SY owned")
        control, _revision = sd.GetSecurityDescriptorControl()
        if not control & 0x1000:  # actual SE_DACL_PROTECTED, never a synthetic flag
            raise ValueError("Installed object DACL is not protected from inheritance")
        dacl = sd.GetSecurityDescriptorDacl()
        if dacl is None:
            raise ValueError("Installed object has an unrestricted DACL")
        # GenericAll/Write, DELETE, WRITE_DAC/OWNER, data/append/EA/attributes.
        writable = 0x10000000 | 0x40000000 | 0x02000000 | 0x10000 | 0x40000 | 0x80000 | 0x2 | 0x4 | 0x10 | 0x40 | 0x100
        allowed = {SYSTEM_SID, ADMIN_SID}
        if write_sid:
            allowed.add(write_sid)
        task_grants = set()
        for i in range(dacl.GetAceCount()):
            ace = dacl.GetAce(i)
            ace_type, flags = ace[0]
            if ace_type == 1:  # deny ACE does not grant access
                continue
            if ace_type != 0:
                raise ValueError("Unsupported object/callback ACE in installed protection")
            if flags & 0x08:  # inherit-only does not grant this object access
                continue
            sid = win32security.ConvertSidToStringSid(ace[2])
            if task_owner_sid is not None:
                accepted_masks = (0x10000000, 0x1F01FF) if sid in (SYSTEM_SID, ADMIN_SID) else (0xA0000000, 0x1200A9)
                if sid not in (SYSTEM_SID, ADMIN_SID, task_owner_sid) or ace[1] not in accepted_masks:
                    raise ValueError("Task ACL has third-party or excess grants")
                task_grants.add(sid)
            if ace[1] & writable and sid not in allowed:
                raise ValueError("Installed object grants nontrusted write/delete access")
        if task_owner_sid is not None and task_grants != {SYSTEM_SID, ADMIN_SID, task_owner_sid}:
            raise ValueError("Task ACL lacks fixed SYSTEM/admin/owner read-run grants")

    @contextmanager
    def _locked(self, path, *, write_sid=None, directory=False, inbox_publication=False):
        import win32con
        import win32file
        import win32security
        canonical = _canonical_path(path)
        if inbox_publication and (not directory or not write_sid or not _same_path(path, INSTALL_ROOT + r"\inbox")):
            raise ValueError("Write sharing is restricted to fixed inbox publication directory")
        root = _canonical_path(INSTALL_ROOT)
        if canonical != root and not canonical.startswith(root + "\\"):
            raise ValueError("Protected read outside fixed installation")
        with ExitStack() as stack:
            drive, tail = ntpath.splitdrive(ntpath.normpath(path))
            parts = tail.strip("\\/").split("\\")
            ancestors = [drive + "\\"]
            for part in parts[:-1]:
                ancestors.append(ntpath.join(ancestors[-1], part))
            for ancestor in ancestors:
                handle = win32file.CreateFile(ancestor, win32con.GENERIC_READ, win32con.FILE_SHARE_READ | win32con.FILE_SHARE_WRITE,
                    None, win32con.OPEN_EXISTING, win32con.FILE_FLAG_BACKUP_SEMANTICS | win32file.FILE_FLAG_OPEN_REPARSE_POINT, None)
                stack.callback(handle.Close)
                attrs = win32file.GetFileInformationByHandle(handle)[0]
                if attrs & win32con.FILE_ATTRIBUTE_REPARSE_POINT:
                    raise ValueError("Reparse ancestor in fixed installation")
                if _canonical_path(ancestor) == root or _canonical_path(ancestor).startswith(root + "\\"):
                    sd = win32security.GetSecurityInfo(handle, win32security.SE_FILE_OBJECT, win32security.OWNER_SECURITY_INFORMATION | win32security.DACL_SECURITY_INFORMATION)
                    self._validate_acl(sd, write_sid=write_sid if _same_path(ancestor, INSTALL_ROOT + r"\inbox") else None)
            flags = win32file.FILE_FLAG_OPEN_REPARSE_POINT | (win32con.FILE_FLAG_BACKUP_SEMANTICS if directory else 0)
            # Child rename needs WRITE sharing on its parent directory. Keep
            # DELETE unshared and every protected file/default lease unchanged.
            sharing = win32con.FILE_SHARE_READ | (win32con.FILE_SHARE_WRITE if inbox_publication else 0)
            handle = win32file.CreateFile(path, win32con.GENERIC_READ, sharing, None, win32con.OPEN_EXISTING, flags, None)
            stack.callback(handle.Close)
            info = win32file.GetFileInformationByHandle(handle)
            if info[0] & win32con.FILE_ATTRIBUTE_REPARSE_POINT or bool(info[0] & win32con.FILE_ATTRIBUTE_DIRECTORY) != directory:
                raise ValueError("Installed protected leaf reparse/type mismatch")
            if win32file.GetFileType(handle) != win32con.FILE_TYPE_DISK:
                raise ValueError("Installed object is not a disk file/directory")
            final = win32file.GetFinalPathNameByHandle(handle, 0)
            if final.startswith("\\\\?\\"):
                final = final[4:]
            if _canonical_path(final) != canonical:
                raise ValueError("Protected handle final path mismatch")
            sd = win32security.GetSecurityInfo(handle, win32security.SE_FILE_OBJECT, win32security.OWNER_SECURITY_INFORMATION | win32security.DACL_SECURITY_INFORMATION)
            self._validate_acl(sd, write_sid=write_sid)
            yield handle
            if inbox_publication:
                current = win32file.GetFileInformationByHandle(handle)
                if tuple(current[i] for i in (4, 8, 9)) != tuple(info[i] for i in (4, 8, 9)) or current[0] & win32con.FILE_ATTRIBUTE_REPARSE_POINT or not current[0] & win32con.FILE_ATTRIBUTE_DIRECTORY:
                    raise ValueError("Inbox directory identity/type changed during publication")
                final_after = win32file.GetFinalPathNameByHandle(handle, 0)
                if final_after.startswith("\\\\?\\"):
                    final_after = final_after[4:]
                if _canonical_path(final_after) != canonical:
                    raise ValueError("Inbox final path changed during publication")
                sd_after = win32security.GetSecurityInfo(handle, win32security.SE_FILE_OBJECT, win32security.OWNER_SECURITY_INFORMATION | win32security.DACL_SECURITY_INFORMATION)
                self._validate_acl(sd_after, write_sid=write_sid)

    def read_protected(self, path, limit):
        import win32file
        with self._locked(path) as handle:
            size = win32file.GetFileSize(handle)
            if size > limit:
                raise ValueError("Protected file exceeds bounded read")
            chunks = []
            remaining = size
            while remaining:
                _, chunk = win32file.ReadFile(handle, min(remaining, 1024 * 1024))
                if not chunk:
                    raise ValueError("Short protected file read")
                chunks.append(chunk)
                remaining -= len(chunk)
            return b"".join(chunks)

    def verify_protected_file(self, path, size, sha256):
        import win32file
        with self._locked(path) as handle:
            if win32file.GetFileSize(handle) != size:
                raise ValueError("Protected runtime file size mismatch")
            digest = hashlib.sha256()
            remaining = size
            while remaining:
                _, chunk = win32file.ReadFile(handle, min(remaining, 1024 * 1024))
                if not chunk:
                    raise ValueError("Short protected runtime read")
                digest.update(chunk)
                remaining -= len(chunk)
            if digest.hexdigest() != sha256:
                raise ValueError("Protected runtime file SHA mismatch")

    def task_contract(self, owner_sid):
        import pythoncom
        import win32com.client.dynamic
        import win32security
        pythoncom.CoInitialize()
        service = win32com.client.dynamic.Dispatch("Schedule.Service")
        service.Connect()
        folder = service.GetFolder(TASK_FOLDER)
        task = folder.GetTask(TASK_NAME)
        for obj in (folder, task):
            sd = win32security.ConvertStringSecurityDescriptorToSecurityDescriptor(obj.GetSecurityDescriptor(7), 1)
            self._validate_acl(sd, task_owner_sid=owner_sid)
        definition = task.Definition
        action = definition.Actions.Item(1) if definition.Actions.Count == 1 else None
        user_id = definition.Principal.UserId
        if user_id != SYSTEM_SID:
            sid, _, _ = win32security.LookupAccountName(None, user_id)
            user_id = win32security.ConvertSidToStringSid(sid)
        result = {"folder": TASK_FOLDER, "name": TASK_NAME,
            "action": {"path": action.Path, "arguments": action.Arguments, "working_directory": action.WorkingDirectory} if action else {},
            "principal": {"user_id": user_id, "logon_type": definition.Principal.LogonType, "run_level": definition.Principal.RunLevel},
            "actions_count": definition.Actions.Count, "action_type": action.Type if action else -1,
            "triggers_count": definition.Triggers.Count, "allow_demand_start": bool(definition.Settings.AllowDemandStart),
            "task_acl_protected": True, "folder_acl_protected": True}
        validate_task_contract(result)
        self._task = task
        self._task_owner = owner_sid
        return result

    def publish_request(self, path, raw, owner_sid):
        inbox = INSTALL_ROOT + r"\inbox"
        if not _same_path(ntpath.dirname(path), inbox) or not re.fullmatch(r"[0-9a-f-]{36}\.request\.json", ntpath.basename(path)):
            raise ValueError("Request path outside fixed UUID inbox")
        if self.current_sid() != owner_sid:
            raise ValueError("Request publisher owner SID changed")
        with self._locked(inbox, write_sid=owner_sid, directory=True, inbox_publication=True):
            temporary = Path(path + "." + uuid.uuid4().hex + ".tmp")
            with temporary.open("xb") as handle:
                handle.write(raw)
                handle.flush()
                os.fsync(handle.fileno())
            # Windows rename does not replace an existing destination. Never unlink.
            temporary.rename(path)

    def run_task(self):
        if self._task is None:
            raise ValueError("Task not verified before request")
        self.task_contract(self._task_owner)  # current protected action, before Run
        self._task.Run(None)

    @staticmethod
    def fingerprint(path):
        item = Path(path)
        if not item.is_file() or item.suffix.lower() != ".exe":
            raise ValueError("Requested current EXE missing")
        with item.open("rb") as handle:
            digest = hashlib.file_digest(handle, "sha256").hexdigest()
        return {"path": str(item.resolve()), "size": item.stat().st_size, "sha256": digest}
