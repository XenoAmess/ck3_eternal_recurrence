"""Default-OFF internal loaded-provider issuer contract, with injected OS reads.

No Win32 adapter, controller/App handle transfer, public tool or production hook
is installed here. Enabling a flag cannot replace those missing inputs. The
facade is an internal trusted-code boundary, not a caller-supplied JSON reader.
Only the existing M7 DTO is qualification; the private holder owns resources.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import re
from contextlib import nullcontext
import os
from pathlib import PureWindowsPath

from ..environment import process_creation_utc

_RESOURCE_SEAL = object()


@dataclass(frozen=True)
class _ProcessReadbackV1:
    pid: int
    creation_filetime: int
    creation_date: str
    executable: str
    alive: bool


@dataclass(frozen=True)
class _DLLReadbackV1:
    final_path: str
    volume_serial: int
    file_id: bytes
    sha256: str
    size: int


@dataclass(frozen=True)
class _ModuleReadbackV1:
    path: str
    base: int
    image_size: int
    volume_serial: int
    file_id: bytes


@dataclass(frozen=True)
class _TransferReadbackV1:
    source_resource: object
    receiver_owner: object
    receiver_pid: int
    process_handle: object
    dll_handle: object


@dataclass(frozen=True)
class _PipeReadbackV1:
    handle: object
    client_pid: int
    name: str


@dataclass(frozen=True)
class CustodyIssueResultV1:
    issued: bool
    reason: str


class _CustodyOSFacadeV1:
    """Reserved trusted OS adapter; no production implementation is supplied.

    open_read_shared_preload_dll MUST itself execute the fixed
    CreateFile(GENERIC_READ, FILE_SHARE_READ, OPEN_EXISTING) operation. It must
    retain that owned handle; a raw handle and a self-reported share flag cannot
    implement it. observe_dll hashes that same open file, without reopening its
    path. observe_modules returns mapped-file identity, not a basename lookup.
    transfer_readback must verify actual inheritance/DuplicateHandle continuity
    from the still-live preload resource into this SDK process. No JSON import
    or post-load re-open can implement it. Handles returned here are owned by
    this helper; the original runtime target/job handles are always borrowed.
    """
    def duplicate_target_read_handle(self, borrowed_handle):
        raise NotImplementedError("canonical target-handle duplication not connected")

    def open_read_shared_preload_dll(self, path):
        raise NotImplementedError("fixed pre-load DLL opener not connected")

    def observe_process(self, handle):
        raise NotImplementedError("kernel target reader not connected")

    def observe_dll(self, handle):
        raise NotImplementedError("held DLL reader not connected")

    def observe_modules(self, process_handle):
        raise NotImplementedError("mapped-module identity reader not connected")

    def transfer_readback(self, resource, transfer, owner):
        raise NotImplementedError("canonical controller-to-SDK handle transfer not connected")

    def current_process_id(self):
        raise NotImplementedError("receiver kernel identity not connected")

    def observe_pipe_client(self, actual_server_handle):
        raise NotImplementedError("GetNamedPipeClientProcessId reader not connected")

    def close_owned_handle(self, handle):
        raise NotImplementedError("owned duplicate/file release not connected")


def _require(ok, why):
    if not ok:
        raise ValueError(why)


def _path(value):
    _require(isinstance(value, str) and value.strip(), "missing full path")
    _require(PureWindowsPath(value).is_absolute(), "absolute Windows path required")
    return os.path.normcase(os.path.abspath(value))


def _sha(value):
    return isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdef" for c in value)


def _process(value):
    _require(type(value) is _ProcessReadbackV1, "kernel process readback required")
    _require(type(value.pid) is int and value.pid > 0 and value.alive is True,
             "target is not a live exact process")
    _require(type(value.creation_filetime) is int and 0 < value.creation_filetime < 2**64,
             "integer kernel FILETIME required")
    _require(isinstance(value.creation_date, str), "original OS birth string required")
    full = re.fullmatch(r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})\.(\d{7})Z",value.creation_date)
    instant = (datetime.strptime(full[1],"%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
               if full else process_creation_utc(value.creation_date))
    delta = instant - datetime(1601, 1, 1, tzinfo=timezone.utc)
    ticks = ((delta.days * 86400 + delta.seconds) * 1000000 + delta.microseconds) * 10
    if full:
        ticks += int(full[2])
    _require(ticks == value.creation_filetime, "OS birth encoding cannot represent exact kernel FILETIME")
    _path(value.executable)
    return value


def _same_process(first, second):
    first, second = _process(first), _process(second)
    return (first.pid == second.pid and first.creation_filetime == second.creation_filetime
            and _path(first.executable) == _path(second.executable))


def _dll(value):
    _require(type(value) is _DLLReadbackV1, "held DLL readback required")
    _path(value.final_path)
    _require(type(value.volume_serial) is int and 0 <= value.volume_serial < 2**64
             and type(value.file_id) is bytes and len(value.file_id) == 16
             and _sha(value.sha256) and type(value.size) is int and value.size > 0,
             "exact held DLL file identity/hash required")
    return value


def _same_dll(first, second):
    first, second = _dll(first), _dll(second)
    return (first.volume_serial == second.volume_serial and first.file_id == second.file_id
            and first.sha256 == second.sha256 and first.size == second.size
            and _path(first.final_path) == _path(second.final_path))


def _modules(facade, handle):
    values = facade.observe_modules(handle)
    _require(type(values) is tuple and all(type(v) is _ModuleReadbackV1 for v in values),
             "kernel mapped-module readbacks required")
    return values


class _PreloadCustodyV1:
    """Resource holder only; it is neither a score token nor serializable proof."""
    def __init__(self, *, target, facade, process_handle, dll_handle, process, dll,
                 machine_id, pipe_name, seal, source_role="controller"):
        _require(seal is _RESOURCE_SEAL, "internal resource producer required")
        self.target, self.facade = target, facade
        self.process_handle, self.dll_handle = process_handle, dll_handle
        self.process, self.dll = process, dll
        self.machine_id, self.pipe_name, self.seal = machine_id, pipe_name, seal
        _require(source_role in ("controller","received"),"unknown custody role")
        _require(source_role != "received" or target is None,"received custody has no local controller original")
        self.source_role = source_role
        self._preload_source_verified = source_role == "controller"
        self.owner = self.transfer = None
        self.closed = False
        self.last_error = None
        self._owned = [process_handle, dll_handle]

    def close(self):
        with self.owner.lock if self.owner is not None else nullcontext():
            return self._close_locked()

    def _close_locked(self):
        # Clear qualification first. Never close the borrowed runtime target or
        # job handle, and never terminate a Game/process from this observer.
        if self.owner is not None:
            _clear_issued(self.owner, self)
        self.closed = True
        errors = []
        for handle in tuple(self._owned):
            try:
                self.facade.close_owned_handle(handle)
                self._owned.remove(handle)
            except Exception as error:
                errors.append(type(error).__name__)
        if not self._owned and self.owner is not None:
            if getattr(self.owner, "_player_heir_loaded_custody_v1", None) is self:
                self.owner._player_heir_loaded_custody_v1 = None
        return CustodyIssueResultV1(False, "closed" if not errors else "owned_handle_release_unverified:" + ",".join(errors))


def prepare_canonical_cold_custody_v1(*, target, dll_path, expected_dll_sha256,
                                    machine_id, pipe_name, os_facade=None, enabled=False):
    """Run before the original cold LoadLibrary; default OFF returns no holder.

    The target must be the actual canonical suspended-process object. This
    function creates its OWN read duplicate and fixed-mode pre-load DLL handle.
    A caller cannot provide an arbitrary handle plus a share-mode assertion.
    """
    if enabled is not True:
        return None
    handles = []
    try:
        from ..runtime import _SuspendedWindowsProcess
        from ..player_heir_fixed_dynasty_projection_v1 import GETTER_SOURCE_CLOSURE_SHA256
        _require(isinstance(os_facade, _CustodyOSFacadeV1), "trusted OS facade missing")
        _require(isinstance(target, _SuspendedWindowsProcess) and target.resumed is False
                 and target.returncode is None and target._process_handle is not None
                 and target._thread_handle is not None, "original canonical pre-resume target required")
        _require(_sha(expected_dll_sha256) and expected_dll_sha256 != GETTER_SOURCE_CLOSURE_SHA256,
                 "actual DLL SHA required; source-contract SHA forbidden")
        _require(isinstance(machine_id, str) and machine_id.strip(), "machine identity required")
        from .native_driver import _validate_pipe_name
        pipe_name = _validate_pipe_name(pipe_name)
        path = _path(dll_path)
        process_handle = os_facade.duplicate_target_read_handle(target._process_handle)
        _require(process_handle is not None and process_handle != target._process_handle,
                 "own read-only target duplicate required")
        handles.append(process_handle)
        process = _process(os_facade.observe_process(process_handle))
        _require(process.pid == target.pid and target.args
                 and _path(process.executable) == _path(target.args[0]), "canonical target identity differs")
        _require(_same_process(process, os_facade.observe_process(target._process_handle)),
                 "target duplicate differs from original retained process")
        dll_handle = os_facade.open_read_shared_preload_dll(path)
        _require(dll_handle is not None and dll_handle not in handles, "owned fixed-mode DLL handle required")
        handles.append(dll_handle)
        dll = _dll(os_facade.observe_dll(dll_handle))
        _require(_path(dll.final_path) == path and dll.sha256 == expected_dll_sha256,
                 "pre-load DLL path/hash differs")
        basename = PureWindowsPath(path).name.casefold()
        _require(not any(PureWindowsPath(v.path).name.casefold() == basename
                         for v in _modules(os_facade, process_handle)),
                 "DLL was already mapped before preload custody")
        return _PreloadCustodyV1(target=target, facade=os_facade, process_handle=process_handle,
            dll_handle=dll_handle, process=process, dll=dll, machine_id=machine_id,
            pipe_name=pipe_name, seal=_RESOURCE_SEAL)
    except Exception as error:
        # Fail closed, but retain any handle whose release was not proved.
        # Such a returned holder is closed/unqualified and exists for cleanup.
        failed = []
        if isinstance(os_facade, _CustodyOSFacadeV1):
            for handle in reversed(handles):
                try:
                    os_facade.close_owned_handle(handle)
                except Exception:
                    failed.append(handle)
        if failed:
            holder = _PreloadCustodyV1(target=target, facade=os_facade,
                process_handle=None, dll_handle=None, process=None, dll=None,
                machine_id=machine_id, pipe_name=pipe_name, seal=_RESOURCE_SEAL)
            holder.closed, holder._owned = True, failed
            holder.last_error = type(error).__name__ + ":preload_cleanup_unverified"
            return holder
        return None


def _clear_issued(owner, custody):
    if getattr(owner, "_player_heir_loaded_custody_v1", None) is custody:
        owner._player_heir_loaded_provider_v1 = None
        owner._player_heir_game_identity_cache_v1 = None


def _clear_current_issued(owner):
    current = getattr(owner, "_player_heir_loaded_custody_v1", None)
    if isinstance(current, _PreloadCustodyV1) and current.seal is _RESOURCE_SEAL:
        _clear_issued(owner, current)


def invalidate_loaded_native_provider_v1(owner, *, reason="disconnect_or_close"):
    """Future canonical disconnect/close hook; releases only this holder's handles."""
    custody = getattr(owner, "_player_heir_loaded_custody_v1", None)
    if not isinstance(custody, _PreloadCustodyV1) or custody.seal is not _RESOURCE_SEAL:
        return CustodyIssueResultV1(False, "no_internal_custody")
    result = custody.close()
    return CustodyIssueResultV1(False, reason + ":" + result.reason)


def issue_loaded_native_provider_v1(*, custody, owner, driver, endpoint, transfer,
                                   os_facade=None, enabled=False):
    """Only mint branch, after actual SDK pipe/module/handle-transfer adoption.

    transfer is an opaque actual handle-transfer operation object, never a JSON
    tuple or claimed exit status. The future canonical adapter must independently
    verify it. Local receiver staging is not canonical preload-origin proof;
    no production caller or source-promotion path exists in this change.
    """
    if enabled is not True:
        _clear_current_issued(owner)
        return CustodyIssueResultV1(False, "default_off")
    try:
        with owner.lock:
            return _issue_locked(custody=custody, owner=owner, driver=driver,
                endpoint=endpoint, transfer=transfer, os_facade=os_facade)
    except Exception as error:
        _clear_current_issued(owner)
        return CustodyIssueResultV1(False, "unavailable:" + str(error)[:200])


def _issue_locked(*, custody, owner, driver, endpoint, transfer, os_facade):
    try:
        from .native_driver import NativeHeadlessGameplayDriver, NativeNamedPipeServer
        from .successor_ui_app_owner_v1 import SuccessorUIAppOwner
        from . import player_heir_candidate_component_v1 as component
        _require(isinstance(custody, _PreloadCustodyV1) and custody.seal is _RESOURCE_SEAL
                 and custody.closed is False, "pre-load resource missing or closed")
        _require(custody._preload_source_verified is True,
                 "received canonical preload continuity is not qualified")
        _require(custody.owner is None or custody.owner is owner, "resource belongs to another SDK owner")
        current = getattr(owner, "_player_heir_loaded_custody_v1", None)
        _require(current is None or current is custody, "previous custody must be normally released first")
        _require(isinstance(os_facade, _CustodyOSFacadeV1) and custody.facade is os_facade,
                 "original trusted custody facade required")
        _require(isinstance(owner, SuccessorUIAppOwner) and isinstance(driver, NativeHeadlessGameplayDriver)
                 and owner.driver is driver and owner.service.driver is driver
                 and getattr(owner.service, "_successor_ui_app_owner_v1", None) is owner
                 and getattr(driver, "_player_heir_candidate_owner_v1", None) is owner,
                 "canonical App/driver/Service binding required")
        _require(isinstance(endpoint, NativeNamedPipeServer) and endpoint is driver.endpoint
                 and endpoint.pipe_name == driver.pipe_name == custody.pipe_name
                 and owner.machine == custody.machine_id, "actual SDK endpoint/machine differs")
        _require(transfer is not None and not isinstance(transfer, (dict, list, tuple, str, bytes, int, float, bool)),
                 "actual canonical handle transfer missing")
        received = os_facade.transfer_readback(custody, transfer, owner)
        _require(type(received) is _TransferReadbackV1 and received.source_resource is custody
                 and received.receiver_owner is owner and type(received.receiver_pid) is int
                 and received.receiver_pid == os_facade.current_process_id()
                 and received.process_handle is not None and received.dll_handle is not None
                 and received.process_handle != received.dll_handle,
                 "canonical live preload-to-SDK handle transfer unverified")
        for owned in (received.process_handle, received.dll_handle):
            original = custody.target._process_handle if custody.source_role == "controller" else None
            _require(owned != original, "runtime original handle must remain borrowed")
            if owned not in custody._owned:
                custody._owned.append(owned)
        # Once transfer ownership is proved, even a later observer refusal must
        # keep the SDK duplicates under an owner for explicit normal cleanup.
        custody.owner, custody.transfer = owner, transfer
        owner._player_heir_loaded_custody_v1 = custody
        # Read original held handles as well: post-load re-open plus equal hash
        # cannot reconstruct the missing pre-load chain.
        _require(_same_process(custody.process, os_facade.observe_process(custody.process_handle))
                 and _same_process(custody.process, os_facade.observe_process(received.process_handle))
                 and _same_dll(custody.dll, os_facade.observe_dll(custody.dll_handle))
                 and _same_dll(custody.dll, os_facade.observe_dll(received.dll_handle)),
                 "pre-load retained handle continuity changed")
        handle = endpoint._current_handle()
        _require(handle is not None, "actual server pipe handle unavailable")
        peer = os_facade.observe_pipe_client(handle)
        _require(type(peer) is _PipeReadbackV1 and peer.handle == handle
                 and type(peer.client_pid) is int and peer.client_pid > 0
                 and peer.name == custody.pipe_name and peer.client_pid == custody.process.pid,
                 "kernel pipe client is not the held Game")
        with driver.state._condition:
            hello = driver.state._hello
            generation = driver.state._connection_generation
            _require(driver.state._connected is True and isinstance(hello, dict)
                     and hello.get("pid") == peer.client_pid and type(generation) is int and generation > 0
                     and hello.get("connection_generation") == generation
                     and driver._session_bridge_pid == peer.client_pid, "actual native hello/connection differs")
        modules = _modules(os_facade, received.process_handle)
        basename = PureWindowsPath(custody.dll.final_path).name.casefold()
        namesakes = [v for v in modules if PureWindowsPath(v.path).name.casefold() == basename]
        matches = [v for v in namesakes if _path(v.path) == _path(custody.dll.final_path)]
        _require(len(namesakes) == len(matches) == 1, "exact loaded module is missing or ambiguous")
        module = matches[0]
        _require(type(module.base) is int and module.base > 0 and type(module.image_size) is int
                 and module.image_size > 0 and type(module.volume_serial) is int
                 and type(module.file_id) is bytes and len(module.file_id) == 16
                 and module.volume_serial == custody.dll.volume_serial
                 and module.file_id == custody.dll.file_id, "mapped DLL file identity differs from pre-load handle")
        _require(endpoint._current_handle() == handle, "pipe instance changed during qualification")
        with driver.state._condition:
            _require(driver.state._connected is True and driver.state._connection_generation == generation
                     and driver.state._hello == hello, "connection changed during qualification")
        # Single qualification token: reuse M7's existing private DTO and seal.
        provider = component._LoadedNativeProviderV1(owner, driver, owner.machine,
            custody.process.pid, custody.process.creation_date, custody.process.executable,
            generation, driver.pipe_name, custody.dll.sha256, component._LOADED_NATIVE_SEAL,
            game_creation_filetime=custody.process.creation_filetime)
        owner._player_heir_loaded_provider_v1 = provider
        owner._player_heir_game_identity_cache_v1 = None
        return CustodyIssueResultV1(True, "software_contract_qualified_no_production_adapter")
    except Exception as error:
        _clear_current_issued(owner)
        return CustodyIssueResultV1(False, "unavailable:" + str(error)[:200])
