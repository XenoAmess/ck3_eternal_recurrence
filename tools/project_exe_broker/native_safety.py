"""Protected broker Win32 safety adapter; construction/import perform no Win32 calls.

Only the protected bootstrap may instantiate this class. Backend injection is a
test seam, never a request option. No repository imports, subprocesses or COM.
"""
from contextlib import contextmanager
import ctypes
import hashlib
import json
import ntpath
import re
import time
import uuid

SYSTEM_SID = "S-1-5-18"
ADMIN_SID = "S-1-5-32-544"
INSTALL_ROOT = "C:\\Program Files\\XAR CK3 Project EXE Broker"
ATTR_DIRECTORY = 0x10
ATTR_REPARSE = 0x400
WRITE_MASK = 0x500D0156  # generic ALL/WRITE, DELETE/WDAC/WOWNER, file/dir writes
READ_MASK = 0xB2020089  # generic READ/EXECUTE/ALL/MAXIMUM_ALLOWED and read rights
WRITE_MASK |= 0x02000000  # conservatively reject MAXIMUM_ALLOWED grants
MAX_DIRECTORY_ENTRIES = 16384
MAX_PUBLICATION_BYTES = 16 * 1024 * 1024


class SafetyError(RuntimeError):
    pass


def canonical_path(value):
    """Validate syntax before touching the filesystem; never resolve links."""
    if not isinstance(value, str) or not re.match(r"^[A-Za-z]:[\\/]", value):
        raise SafetyError("local absolute drive path required")
    if any(ord(c) < 32 or 0xD800 <= ord(c) <= 0xDFFF for c in value) or any(c in value[2:] for c in ':*?<>|"'):
        raise SafetyError("device/ADS/control/wildcard path rejected")
    normalized = value.replace("/", "\\")
    tail = normalized[3:]
    components = [] if tail == "" else tail.split("\\")
    for part in components:
        if not part or part in (".", "..") or part[-1:] in (" ", "."):
            raise SafetyError("noncanonical path component rejected")
        stem = part.split(".", 1)[0].upper()
        if stem in {"CON", "PRN", "AUX", "NUL", "CLOCK$", "CONIN$", "CONOUT$"}:
            raise SafetyError("DOS device name rejected")
        if re.fullmatch(r"(?:COM|LPT)[1-9\u00b9\u00b2\u00b3]", stem):
            raise SafetyError("DOS device name rejected")
    return normalized[0].upper() + normalized[1:]


def _same_path(left, right):
    return ntpath.normcase(canonical_path(left)) == ntpath.normcase(canonical_path(right))


def _prefixes(path):
    pieces = path[3:].split("\\") if len(path) > 3 else []
    result = [path[:3]]
    for piece in pieces:
        result.append(ntpath.join(result[-1], piece))
    return result


def _descriptor_fingerprint(meta):
    return hashlib.sha256(json.dumps(meta["security"], sort_keys=True,
                                    separators=(",", ":")).encode("utf-8")).hexdigest()


def descriptor_proof(security, *, expected_owner=None, allowed_writers=(),
                     require_protected=False, allowed_readers=None):
    """Conservative raw owner/DACL proof, not an effective-rights approximation.

    Denies do not excuse a broad allow. Unknown ACE forms fail closed. Inherited
    and inherit-only allows are checked too; no future broad child grant passes.
    """
    if not isinstance(security, dict) or not security.get("dacl_present"):
        raise SafetyError("missing/null DACL rejected")
    owner = security.get("owner_sid")
    if expected_owner is not None and owner != expected_owner:
        raise SafetyError("unexpected file owner")
    writers = set(allowed_writers)
    if owner not in writers:
        raise SafetyError("owner can rewrite DACL outside permitted writer scope")
    if require_protected and security.get("dacl_protected") is not True:
        raise SafetyError("protected DACL required")
    aces = security.get("aces")
    if not isinstance(aces, list) or not isinstance(security.get("dacl_hex"), str):
        raise SafetyError("raw DACL evidence missing")
    for ace in aces:
        if ace.get("type") not in (0, 1, 5, 6, 9, 10, 11, 12):
            raise SafetyError("unsupported DACL ACE rejected")
        if ace["type"] in (1, 6, 10, 12):
            continue
        mask, sid = ace.get("mask"), ace.get("sid")
        if type(mask) is not int or not isinstance(sid, str):
            raise SafetyError("malformed DACL ACE")
        if mask & WRITE_MASK and sid not in writers:
            raise SafetyError("DACL permits an untrusted writer")
        if allowed_readers is not None and mask & READ_MASK and sid not in allowed_readers:
            raise SafetyError("DACL permits an unexpected reader")
    return {"owner_sid": owner, "owner_write_scope_verified": True,
            "dacl_protected": security.get("dacl_protected") is True,
            "descriptor_sha256": hashlib.sha256(json.dumps(
                security, sort_keys=True, separators=(",", ":")).encode()).hexdigest()}


class _Lease:
    def __init__(self, safety, records, *, expected_owner=None, directory=False):
        self._safety = safety
        self._records = records
        self._expected_owner = expected_owner
        self._directory = directory
        self._closed = False
        self._read_sha = None
        self._read_limit = None
        self.path = records[-1][0]
        self.file_id = records[-1][2]["file_id"]
        self.owner_sid = records[-1][2]["security"]["owner_sid"]
        self.owner_write_scope_verified = False
        if expected_owner is not None:
            descriptor_proof(records[-1][2]["security"], expected_owner=expected_owner,
                             allowed_writers=(expected_owner, SYSTEM_SID, ADMIN_SID))
            self.owner_write_scope_verified = True

    def _current(self, record, *, content=False):
        path, handle, before = record
        now = self._safety._backend().state(handle)
        self._safety._check_state(path, now, bool(before["attributes"] & ATTR_DIRECTORY))
        if now["file_id"] != before["file_id"]:
            raise SafetyError("stable volume/file identity changed")
        if _descriptor_fingerprint(now) != _descriptor_fingerprint(before):
            raise SafetyError("owner/DACL changed while leased")
        if content and (now["size"], now["mtime_ns"]) != (before["size"], before["mtime_ns"]):
            raise SafetyError("leased file size/time changed")
        return now

    def revalidate(self):
        if self._closed:
            raise SafetyError("closed lease")
        for index, record in enumerate(self._records):
            self._current(record, content=not self._directory and index == len(self._records) - 1)
        if self._expected_owner is not None:
            descriptor_proof(self._safety._backend().state(self._records[-1][1])["security"],
                             expected_owner=self._expected_owner,
                             allowed_writers=(self._expected_owner, SYSTEM_SID, ADMIN_SID))
        if self._read_sha is not None:
            current = self._safety._backend().read(self._records[-1][1], self._read_limit)
            if hashlib.sha256(current).hexdigest() != self._read_sha:
                raise SafetyError("leased file bytes changed")
            self._current(self._records[-1], content=True)

    def read_bytes(self, limit):
        if self._directory:
            raise SafetyError("cannot read directory bytes")
        if type(limit) is not int or limit < 0:
            raise SafetyError("finite nonnegative read limit required")
        self.revalidate()
        if self._records[-1][2]["size"] > limit:
            raise SafetyError("file exceeds read limit")
        data = self._safety._backend().read(self._records[-1][1], limit)
        if not isinstance(data, bytes) or len(data) > limit or len(data) != self._records[-1][2]["size"]:
            raise SafetyError("backend violated bounded byte read")
        self._current(self._records[-1], content=True)
        digest = hashlib.sha256(data).hexdigest()
        if self._read_sha is not None and digest != self._read_sha:
            raise SafetyError("leased file bytes changed")
        self._read_sha, self._read_limit = digest, limit
        return data


class NativeSafety:
    def __init__(self, owner_sid, frozen_dir, receipts_dir, backend=None):
        if not isinstance(owner_sid, str) or not re.fullmatch(r"S-1-(?:\d+-)*\d+", owner_sid):
            raise SafetyError("configured SID syntax rejected")
        if owner_sid in (SYSTEM_SID, ADMIN_SID):
            raise SafetyError("ordinary configured owner SID required")
        self.owner_sid = owner_sid
        self.frozen_dir = canonical_path(frozen_dir)
        self.receipts_dir = canonical_path(receipts_dir)
        if not _same_path(self.frozen_dir, INSTALL_ROOT + "\\private-frozen"):
            raise SafetyError("fixed private directory required")
        if not _same_path(self.receipts_dir, INSTALL_ROOT + "\\receipts"):
            raise SafetyError("fixed receipt directory required")
        self._native = backend

    def _backend(self):
        if self._native is None:
            self._native = Win32Backend()
        return self._native

    def _close_records(self, records):
        failures = []
        for _, handle, _ in reversed(records):
            try:
                self._backend().close(handle)
            except BaseException as exc:
                failures.append(exc)
        if failures:
            raise failures[0]

    def clock(self):
        return time.monotonic()

    def token_identity(self):
        return self._backend().token_identity()

    def _check_state(self, path, meta, directory):
        if meta.get("file_type") != 1:
            raise SafetyError("non-disk object rejected")
        if meta.get("attributes", 0) & ATTR_REPARSE:
            raise SafetyError("reparse point rejected before resolution")
        if bool(meta.get("attributes", 0) & ATTR_DIRECTORY) != directory:
            raise SafetyError("file/directory kind mismatch")
        if not _same_path(meta.get("final_path", ""), path):
            raise SafetyError("final handle canonical path differs from requested path")
        if not meta.get("file_id") or not isinstance(meta.get("security"), dict):
            raise SafetyError("handle identity/security evidence missing")

    @contextmanager
    def _lock(self, path, *, directory, owner_sid=None):
        path = canonical_path(path)
        if not directory and len(path) == 3:
            raise SafetyError("drive root cannot be a file")
        if owner_sid is not None and owner_sid != self.owner_sid:
            raise SafetyError("request owner must equal configured owner")
        records = []
        lease = None
        try:
            prefixes = _prefixes(path)
            for index, prefix in enumerate(prefixes):
                is_dir = index < len(prefixes) - 1 or directory
                handle = self._backend().open_existing(prefix, directory=is_dir)
                try:
                    meta = self._backend().state(handle)
                    self._check_state(prefix, meta, is_dir)
                except BaseException:
                    self._backend().close(handle)
                    raise
                records.append((prefix, handle, meta))
            lease = _Lease(self, records, expected_owner=owner_sid, directory=directory)
            lease.revalidate()
            yield lease
            lease.revalidate()
        finally:
            if lease is not None:
                lease._closed = True
            self._close_records(records)

    def lock_file(self, path, *, owner_sid=None):
        return self._lock(path, directory=False, owner_sid=owner_sid)

    def lock_dir(self, path):
        return self._lock(path, directory=True)

    def _classify(self, path):
        path = canonical_path(path)
        records = []
        try:
            for index, prefix in enumerate(_prefixes(path)):
                handle = self._backend().open_existing(prefix, directory=None if prefix == path else True)
                try:
                    meta = self._backend().state(handle)
                    directory = bool(meta.get("attributes", 0) & ATTR_DIRECTORY)
                    self._check_state(prefix, meta, directory if prefix == path else True)
                except BaseException:
                    self._backend().close(handle)
                    raise
                records.append((prefix, handle, meta))
            return bool(records[-1][2]["attributes"] & ATTR_DIRECTORY)
        except OSError as exc:
            if getattr(exc, "winerror", None) in (2, 3):
                return None
            raise
        finally:
            self._close_records(records)

    def exists(self, path):
        return self._classify(path) is not None

    def is_dir(self, path):
        return self._classify(path) is True

    def list_files(self, path):
        result = []
        with self.lock_dir(path) as lease:
            for entry in self._backend().list_entries(lease._records[-1][1], lease.path,
                                                       MAX_DIRECTORY_ENTRIES):
                name = entry["name"]
                if name in (".", ".."):
                    continue
                if "\\" in name or "/" in name:
                    raise SafetyError("directory entry is not an immediate child")
                child = canonical_path(ntpath.join(lease.path, name))
                result.append({"path": child, "mtime_ns": entry["mtime_ns"],
                               "is_file": not bool(entry["attributes"] & (ATTR_DIRECTORY | ATTR_REPARSE))})
                if len(result) > MAX_DIRECTORY_ENTRIES:
                    raise SafetyError("bounded directory metadata limit exceeded")
            lease.revalidate()
        return sorted(result, key=lambda item: ntpath.normcase(item["path"]))

    def _protected_records(self, lease, *, private=False, final_read_scope=False):
        verified = []
        for path, handle, _ in lease._records:
            if not (_same_path(path, INSTALL_ROOT) or ntpath.normcase(path).startswith(
                    ntpath.normcase(INSTALL_ROOT + "\\"))):
                continue
            meta = self._backend().state(handle)
            self._check_state(path, meta, bool(meta["attributes"] & ATTR_DIRECTORY))
            readers = None
            if private and (_same_path(path, self.frozen_dir) or ntpath.normcase(path).startswith(
                    ntpath.normcase(self.frozen_dir + "\\"))):
                readers = (SYSTEM_SID, ADMIN_SID)
            elif final_read_scope and _same_path(path, lease.path):
                readers = (SYSTEM_SID, ADMIN_SID, self.owner_sid)
            proof = descriptor_proof(meta["security"], allowed_writers=(SYSTEM_SID, ADMIN_SID),
                                     require_protected=True, allowed_readers=readers)
            verified.append({"path": path, "file_id": meta["file_id"], **proof})
        if not verified:
            raise SafetyError("protected installation ancestor missing")
        return verified

    def inspect_descriptor(self, path):
        """Read-only raw descriptor evidence; does not assert protected scope."""
        directory = self._classify(path)
        if directory is None:
            raise SafetyError("descriptor target absent")
        with self._lock(path, directory=directory) as lease:
            return {"path": lease.path, "file_id": lease.file_id,
                    "security": self._backend().state(lease._records[-1][1])["security"]}

    def verify_protected_path(self, path, *, private=False):
        """Read-only helper for fixed protected runtime/install paths, not inbox."""
        path = canonical_path(path)
        if not (_same_path(path, INSTALL_ROOT) or ntpath.normcase(path).startswith(
                ntpath.normcase(INSTALL_ROOT + "\\"))):
            raise SafetyError("protected proof outside fixed installation refused")
        directory = self._classify(path)
        if directory is None:
            raise SafetyError("protected target absent")
        with self._lock(path, directory=directory) as lease:
            proofs = self._protected_records(lease, private=private, final_read_scope=True)
            return {"protected_path_verified": True, "path": lease.path,
                    "file_id": lease.file_id, "ancestors": proofs}

    def publish_new(self, path, data, *, private):
        if type(private) is not bool or not isinstance(data, bytes) or len(data) > MAX_PUBLICATION_BYTES:
            raise SafetyError("bounded bytes and strict private flag required")
        path = canonical_path(path)
        parent, name = ntpath.split(path)
        expected = self.frozen_dir if private else self.receipts_dir
        if not _same_path(parent, expected) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,199}", name):
            raise SafetyError("publication must be an immediate fixed protected child")
        with self.lock_dir(parent) as lease:
            self._protected_records(lease, private=private, final_read_scope=not private)
            temporary = ntpath.join(parent, "native-publish-" + str(uuid.uuid4()) + ".tmp")
            handle = self._backend().create_new(temporary, private=private, owner_sid=self.owner_sid)
            try:
                original = self._backend().state(handle)
                self._check_state(temporary, original, False)
                descriptor_proof(original["security"], expected_owner=SYSTEM_SID,
                                 allowed_writers=(SYSTEM_SID, ADMIN_SID), require_protected=True,
                                 allowed_readers=(SYSTEM_SID, ADMIN_SID) if private else
                                 (SYSTEM_SID, ADMIN_SID, self.owner_sid))
                self._backend().write_and_flush(handle, data)
                if self._backend().read(handle, len(data)) != data:
                    raise SafetyError("publication bytes readback mismatch")
                lease.revalidate()
                self._protected_records(lease, private=private, final_read_scope=not private)
                self._backend().rename_new(handle, path)
                after = self._backend().state(handle)
                self._check_state(path, after, False)
                if after["file_id"] != original["file_id"] or _descriptor_fingerprint(after) != _descriptor_fingerprint(original):
                    raise SafetyError("publication identity/ACL changed")
                if self._backend().read(handle, len(data)) != data:
                    raise SafetyError("published bytes readback mismatch")
            finally:
                self._backend().close(handle)


# ctypes declarations use fixed-width integers, including in fake-only imports.
DWORD = ctypes.c_uint32
WORD = ctypes.c_uint16
BOOL = ctypes.c_int32
HANDLE = ctypes.c_void_p
LPVOID = ctypes.c_void_p
WCHAR = ctypes.c_wchar


class FILETIME(ctypes.Structure):
    _fields_ = [("low", DWORD), ("high", DWORD)]


class BY_HANDLE_FILE_INFORMATION(ctypes.Structure):
    _fields_ = [("attributes", DWORD), ("created", FILETIME), ("accessed", FILETIME),
                ("written", FILETIME), ("volume", DWORD), ("size_high", DWORD),
                ("size_low", DWORD), ("links", DWORD), ("index_high", DWORD), ("index_low", DWORD)]


class FILE_ID_INFO(ctypes.Structure):
    _fields_ = [("volume", ctypes.c_uint64), ("identifier", ctypes.c_ubyte * 16)]


class ACL_HEADER(ctypes.Structure):
    _fields_ = [("revision", ctypes.c_ubyte), ("reserved", ctypes.c_ubyte),
                ("size", WORD), ("ace_count", WORD), ("reserved2", WORD)]


class ACL_SIZE_INFORMATION(ctypes.Structure):
    _fields_ = [("ace_count", DWORD), ("bytes_used", DWORD), ("bytes_free", DWORD)]


class SID_AND_ATTRIBUTES(ctypes.Structure):
    _fields_ = [("sid", LPVOID), ("attributes", DWORD)]


class SECURITY_ATTRIBUTES(ctypes.Structure):
    _fields_ = [("length", DWORD), ("descriptor", LPVOID), ("inherit", BOOL)]


class FILE_RENAME_INFO(ctypes.Structure):
    _fields_ = [("replace", ctypes.c_ubyte), ("root", HANDLE),
                ("name_length", DWORD), ("name", WCHAR * 1)]


class WIN32_FIND_DATA(ctypes.Structure):
    _fields_ = [("attributes", DWORD), ("created", FILETIME), ("accessed", FILETIME),
                ("written", FILETIME), ("size_high", DWORD), ("size_low", DWORD),
                ("reserved0", DWORD), ("reserved1", DWORD),
                ("name", WCHAR * 260), ("alternate", WCHAR * 14)]


def _ftime_ns(value):
    return (((int(value.high) << 32) | int(value.low)) - 116444736000000000) * 100


class Win32Backend:
    """Lazy Win32 functions; this constructor has no OS call or library load."""
    def __init__(self):
        self._loaded = False

    def _api(self):
        if self._loaded:
            return
        if not hasattr(ctypes, "WinDLL"):
            raise SafetyError("production Win32 backend requires Windows")
        self.k = ctypes.WinDLL("kernel32", use_last_error=True)
        self.a = ctypes.WinDLL("advapi32", use_last_error=True)
        def bind(dll, name, restype, args):
            function = getattr(dll, name)
            function.restype, function.argtypes = restype, args
            return function
        self.CreateFile = bind(self.k, "CreateFileW", HANDLE, [ctypes.c_wchar_p, DWORD, DWORD, LPVOID, DWORD, DWORD, HANDLE])
        self.CloseHandle = bind(self.k, "CloseHandle", BOOL, [HANDLE])
        self.GetFileType = bind(self.k, "GetFileType", DWORD, [HANDLE])
        self.GetFileInformation = bind(self.k, "GetFileInformationByHandle", BOOL, [HANDLE, ctypes.POINTER(BY_HANDLE_FILE_INFORMATION)])
        self.GetFileInfoEx = bind(self.k, "GetFileInformationByHandleEx", BOOL, [HANDLE, ctypes.c_int, LPVOID, DWORD])
        self.FinalPath = bind(self.k, "GetFinalPathNameByHandleW", DWORD, [HANDLE, ctypes.c_wchar_p, DWORD, DWORD])
        self.SetFilePointer = bind(self.k, "SetFilePointerEx", BOOL, [HANDLE, ctypes.c_int64, ctypes.POINTER(ctypes.c_int64), DWORD])
        self.ReadFile = bind(self.k, "ReadFile", BOOL, [HANDLE, LPVOID, DWORD, ctypes.POINTER(DWORD), LPVOID])
        self.WriteFile = bind(self.k, "WriteFile", BOOL, [HANDLE, LPVOID, DWORD, ctypes.POINTER(DWORD), LPVOID])
        self.FlushFile = bind(self.k, "FlushFileBuffers", BOOL, [HANDLE])
        self.SetFileInfo = bind(self.k, "SetFileInformationByHandle", BOOL, [HANDLE, ctypes.c_int, LPVOID, DWORD])
        self.FindFirst = bind(self.k, "FindFirstFileW", HANDLE, [ctypes.c_wchar_p, ctypes.POINTER(WIN32_FIND_DATA)])
        self.FindNext = bind(self.k, "FindNextFileW", BOOL, [HANDLE, ctypes.POINTER(WIN32_FIND_DATA)])
        self.FindClose = bind(self.k, "FindClose", BOOL, [HANDLE])
        self.LocalFree = bind(self.k, "LocalFree", LPVOID, [LPVOID])
        self.GetCurrentProcess = bind(self.k, "GetCurrentProcess", HANDLE, [])
        self.GetCurrentThread = bind(self.k, "GetCurrentThread", HANDLE, [])
        self.GetSecurityInfo = bind(self.a, "GetSecurityInfo", DWORD, [HANDLE, ctypes.c_int, DWORD, ctypes.POINTER(LPVOID), ctypes.POINTER(LPVOID), ctypes.POINTER(LPVOID), ctypes.POINTER(LPVOID), ctypes.POINTER(LPVOID)])
        self.SidString = bind(self.a, "ConvertSidToStringSidW", BOOL, [LPVOID, ctypes.POINTER(LPVOID)])
        self.StringSid = bind(self.a, "ConvertStringSidToSidW", BOOL, [ctypes.c_wchar_p, ctypes.POINTER(LPVOID)])
        self.ValidSid = bind(self.a, "IsValidSid", BOOL, [LPVOID])
        self.SidLength = bind(self.a, "GetLengthSid", DWORD, [LPVOID])
        self.AclInfo = bind(self.a, "GetAclInformation", BOOL, [LPVOID, LPVOID, DWORD, ctypes.c_int])
        self.GetAce = bind(self.a, "GetAce", BOOL, [LPVOID, DWORD, ctypes.POINTER(LPVOID)])
        self.SDControl = bind(self.a, "GetSecurityDescriptorControl", BOOL, [LPVOID, ctypes.POINTER(WORD), ctypes.POINTER(DWORD)])
        self.Sddl = bind(self.a, "ConvertStringSecurityDescriptorToSecurityDescriptorW", BOOL, [ctypes.c_wchar_p, DWORD, ctypes.POINTER(LPVOID), ctypes.POINTER(DWORD)])
        self.OpenProcessToken = bind(self.a, "OpenProcessToken", BOOL, [HANDLE, DWORD, ctypes.POINTER(HANDLE)])
        self.OpenThreadToken = bind(self.a, "OpenThreadToken", BOOL, [HANDLE, DWORD, BOOL, ctypes.POINTER(HANDLE)])
        self.TokenInformation = bind(self.a, "GetTokenInformation", BOOL, [HANDLE, ctypes.c_int, LPVOID, DWORD, ctypes.POINTER(DWORD)])
        self.CheckMembership = bind(self.a, "CheckTokenMembership", BOOL, [HANDLE, LPVOID, ctypes.POINTER(BOOL)])
        self._loaded = True

    def _ok(self, value):
        if not value:
            raise ctypes.WinError(ctypes.get_last_error())
        return value

    def _sid(self, pointer):
        if not pointer or not self.ValidSid(pointer):
            raise SafetyError("invalid native SID")
        text = LPVOID()
        self._ok(self.SidString(pointer, ctypes.byref(text)))
        try:
            return ctypes.wstring_at(text.value)
        finally:
            self.LocalFree(text)

    @staticmethod
    def _extended(path):
        return "\\\\?\\" + canonical_path(path)

    def open_existing(self, path, *, directory):
        self._api()
        # Directories permit READ/WRITE sharing but never DELETE; leaf files only READ.
        access = 0x00120080 | (1 if directory is not True else 0)  # READ_CONTROL/ATTRIBUTES/SYNCHRONIZE
        sharing = 3 if directory is True else 1
        handle = self.CreateFile(self._extended(path), access, sharing, None, 3,
                                 0x00200000 | 0x02000000, None)  # OPEN_REPARSE_POINT/BACKUP_SEMANTICS
        if handle == ctypes.c_void_p(-1).value:
            raise ctypes.WinError(ctypes.get_last_error())
        return handle

    def close(self, handle):
        self._api()
        self._ok(self.CloseHandle(handle))

    def _security(self, handle):
        owner, dacl, descriptor = LPVOID(), LPVOID(), LPVOID()
        error = self.GetSecurityInfo(handle, 1, 0x5, ctypes.byref(owner), None,
                                     ctypes.byref(dacl), None, ctypes.byref(descriptor))
        if error:
            raise ctypes.WinError(error)
        try:
            control, revision = WORD(), DWORD()
            self._ok(self.SDControl(descriptor, ctypes.byref(control), ctypes.byref(revision)))
            result = {"owner_sid": self._sid(owner.value), "dacl_present": bool(dacl.value),
                      "control": int(control.value),
                      "dacl_protected": bool(control.value & 0x1000), "aces": [], "dacl_hex": ""}
            if not dacl.value:
                return result
            header = ctypes.cast(dacl, ctypes.POINTER(ACL_HEADER)).contents
            if header.size < ctypes.sizeof(ACL_HEADER):
                raise SafetyError("malformed ACL header")
            result["dacl_hex"] = ctypes.string_at(dacl.value, header.size).hex()
            acl_info = ACL_SIZE_INFORMATION()
            self._ok(self.AclInfo(dacl, ctypes.byref(acl_info), ctypes.sizeof(acl_info), 2))
            if acl_info.ace_count != header.ace_count or acl_info.bytes_used > header.size:
                raise SafetyError("ACL size/count mismatch")
            for index in range(header.ace_count):
                ace_pointer = LPVOID()
                self._ok(self.GetAce(dacl, index, ctypes.byref(ace_pointer)))
                offset = ace_pointer.value - dacl.value
                if offset < 8 or offset + 4 > header.size:
                    raise SafetyError("ACE outside raw ACL")
                prefix = ctypes.string_at(ace_pointer.value, 4)
                ace_type, flags = prefix[0], prefix[1]
                size = int.from_bytes(prefix[2:4], "little")
                if size < 8 or offset + size > header.size:
                    raise SafetyError("invalid ACE extent")
                raw = ctypes.string_at(ace_pointer.value, size)
                mask = int.from_bytes(raw[4:8], "little")
                sid_offset = 8
                if ace_type in (5, 6, 11, 12):
                    if size < 12:
                        raise SafetyError("truncated object ACE")
                    object_flags = int.from_bytes(raw[8:12], "little")
                    if object_flags & ~3:
                        raise SafetyError("unknown object ACE flags")
                    sid_offset = 12 + (16 if object_flags & 1 else 0) + (16 if object_flags & 2 else 0)
                if ace_type not in (0, 1, 5, 6, 9, 10, 11, 12):
                    # Keep unknown raw type for proof to reject, without unsafe SID parsing.
                    result["aces"].append({"type": ace_type, "flags": flags, "mask": mask, "sid": ""})
                    continue
                if sid_offset + 8 > size:
                    raise SafetyError("ACE SID header truncated")
                subauthorities = raw[sid_offset + 1]
                if sid_offset + 8 + subauthorities * 4 > size:
                    raise SafetyError("ACE SID extent truncated")
                sid_address = ace_pointer.value + sid_offset
                result["aces"].append({"type": ace_type, "flags": flags, "mask": mask,
                                       "sid": self._sid(sid_address)})
            return result
        finally:
            self.LocalFree(descriptor)

    def state(self, handle):
        self._api()
        info, identity = BY_HANDLE_FILE_INFORMATION(), FILE_ID_INFO()
        self._ok(self.GetFileInformation(handle, ctypes.byref(info)))
        # Check attributes/type before normalized FinalPath can resolve anything.
        if info.attributes & ATTR_REPARSE:
            raise SafetyError("reparse point rejected before FinalPath")
        file_type = int(self.GetFileType(handle))
        if file_type != 1:
            raise SafetyError("non-disk object rejected before FinalPath")
        self._ok(self.GetFileInfoEx(handle, 18, ctypes.byref(identity), ctypes.sizeof(identity)))
        needed = self.FinalPath(handle, None, 0, 0)
        if needed == 0 or needed > 32768:
            raise SafetyError("final handle path unavailable/oversized")
        buffer = ctypes.create_unicode_buffer(needed + 1)
        actual = self.FinalPath(handle, buffer, needed + 1, 0)
        if actual == 0 or actual > needed:
            raise SafetyError("final handle path changed while read")
        final_path = buffer.value
        if not final_path.startswith("\\\\?\\") or final_path.startswith("\\\\?\\UNC\\"):
            raise SafetyError("non-local final handle path rejected")
        return {"attributes": int(info.attributes), "file_type": file_type,
                "final_path": canonical_path(final_path[4:]),
                "file_id": (int(identity.volume), bytes(identity.identifier).hex()),
                "size": (int(info.size_high) << 32) | int(info.size_low),
                "mtime_ns": _ftime_ns(info.written), "security": self._security(handle)}

    def read(self, handle, limit):
        self._api()
        self._ok(self.SetFilePointer(handle, 0, None, 0))
        chunks, total = [], 0
        while True:
            count = min(65536, limit - total + 1)
            if count <= 0:
                raise SafetyError("file exceeds bounded read")
            buffer, received = ctypes.create_string_buffer(count), DWORD()
            self._ok(self.ReadFile(handle, buffer, count, ctypes.byref(received), None))
            if received.value == 0:
                break
            total += received.value
            if total > limit:
                raise SafetyError("file exceeds bounded read")
            chunks.append(buffer.raw[:received.value])
        return b"".join(chunks)

    def list_entries(self, directory_handle, path, limit):
        self._api()
        data = WIN32_FIND_DATA()
        handle = self.FindFirst(self._extended(path).rstrip("\\") + "\\*", ctypes.byref(data))
        if handle == ctypes.c_void_p(-1).value:
            error = ctypes.get_last_error()
            if error == 2:
                return []
            raise ctypes.WinError(error)
        result = []
        try:
            while True:
                name = data.name
                if name not in (".", ".."):
                    result.append({"name": name, "attributes": int(data.attributes),
                                   "mtime_ns": _ftime_ns(data.written)})
                    if len(result) > limit:
                        raise SafetyError("bounded directory metadata limit exceeded")
                if not self.FindNext(handle, ctypes.byref(data)):
                    error = ctypes.get_last_error()
                    if error != 18:
                        raise ctypes.WinError(error)
                    break
        finally:
            self._ok(self.FindClose(handle))
        return result

    def create_new(self, path, *, private, owner_sid):
        self._api()
        sddl = "O:SYG:SYD:P(A;;FA;;;SY)(A;;FA;;;BA)"
        if not private:
            sddl += "(A;;GR;;;" + owner_sid + ")"
        descriptor = LPVOID()
        self._ok(self.Sddl(sddl, 1, ctypes.byref(descriptor), None))
        try:
            attributes = SECURITY_ATTRIBUTES(ctypes.sizeof(SECURITY_ATTRIBUTES), descriptor, 0)
            handle = self.CreateFile(self._extended(path), 0xC0030080, 1, ctypes.byref(attributes),
                                     1, 0x00200080, None)  # CREATE_NEW; write/read/delete/read-control
            if handle == ctypes.c_void_p(-1).value:
                raise ctypes.WinError(ctypes.get_last_error())
            return handle
        finally:
            self.LocalFree(descriptor)

    def write_and_flush(self, handle, data):
        self._api()
        self._ok(self.SetFilePointer(handle, 0, None, 0))
        offset = 0
        while offset < len(data):
            chunk = data[offset:offset + 65536]
            buffer, written = ctypes.create_string_buffer(chunk), DWORD()
            self._ok(self.WriteFile(handle, buffer, len(chunk), ctypes.byref(written), None))
            if written.value == 0:
                raise SafetyError("zero-byte write")
            offset += written.value
        self._ok(self.FlushFile(handle))

    def rename_new(self, handle, path):
        self._api()
        # SetFileInformationByHandle performs one no-replace rename of this exact handle.
        encoded = canonical_path(path).encode("utf-16-le")
        size = FILE_RENAME_INFO.name.offset + len(encoded) + 2
        buffer = ctypes.create_string_buffer(size)
        info = ctypes.cast(buffer, ctypes.POINTER(FILE_RENAME_INFO)).contents
        info.replace, info.root, info.name_length = 0, None, len(encoded)
        ctypes.memmove(ctypes.addressof(buffer) + FILE_RENAME_INFO.name.offset, encoded, len(encoded))
        self._ok(self.SetFileInfo(handle, 3, buffer, size))

    def token_identity(self):
        self._api()
        token = HANDLE()
        if not self.OpenThreadToken(self.GetCurrentThread(), 8, 1, ctypes.byref(token)):
            error = ctypes.get_last_error()
            if error != 1008:
                raise ctypes.WinError(error)
            self._ok(self.OpenProcessToken(self.GetCurrentProcess(), 8, ctypes.byref(token)))
        try:
            needed = DWORD()
            self.TokenInformation(token, 1, None, 0, ctypes.byref(needed))
            if not 8 <= needed.value <= 65536:
                raise SafetyError("token SID size invalid")
            buffer = ctypes.create_string_buffer(needed.value)
            self._ok(self.TokenInformation(token, 1, buffer, needed.value, ctypes.byref(needed)))
            sid_pointer = ctypes.cast(buffer, ctypes.POINTER(SID_AND_ATTRIBUTES)).contents.sid
            sid = self._sid(sid_pointer)
            administrators = LPVOID()
            self._ok(self.StringSid(ADMIN_SID, ctypes.byref(administrators)))
            try:
                member = BOOL()
                # NULL checks the same effective thread/process token used above.
                self._ok(self.CheckMembership(None, administrators, ctypes.byref(member)))
                return {"sid": sid, "admin": bool(member.value)}
            finally:
                self.LocalFree(administrators)
        finally:
            self._ok(self.CloseHandle(token))
