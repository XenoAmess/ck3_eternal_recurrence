"""Strict shared wire contract for a current Steam App offline-mode observation."""
from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Literal, TypedDict

State = Literal["offline", "online", "unavailable"]
ObservationMethod = Literal["cef_app_getters", "native_current_user_byte"]
Reason = Literal[
    "observed", "unsupported_platform", "steam_not_found", "ambiguous_steam",
    "source_not_qualified", "cdp_not_enabled", "cdp_not_owned",
    "cdp_unavailable", "context_unavailable", "invalid_observation",
    "steam_instance_changed", "native_query_failed",
]
_REASON_VALUES: frozenset[str] = frozenset((
    "observed", "unsupported_platform", "steam_not_found", "ambiguous_steam",
    "source_not_qualified", "cdp_not_enabled", "cdp_not_owned",
    "cdp_unavailable", "context_unavailable", "invalid_observation",
    "steam_instance_changed", "native_query_failed",
))
_DECIMAL = re.compile(r"(?:0|[1-9][0-9]*)\Z")
_HEX64 = re.compile(r"[0-9a-f]{64}\Z")


class ProcessWire(TypedDict):
    pid: int
    birth_filetime: str
    exe: str
    file_version: str


class SourceWire(TypedDict):
    path: str
    bytes: int
    sha256: str
    file_id: str
    mtime_ns: str


class EndpointWire(TypedDict):
    pid: int
    birth_filetime: str
    port: int
    target_id: str
    target_url: str



class NativeEvidenceWire(TypedDict):
    machine_id: str
    observed_at_utc: str
    nonce: str
    module_base: str
    module_size: int
    value_rva: str
    value_address: str
    producer_rva: str
    producer_anchor_hex: str
    producer_anchor_sha256: str
    raw_samples: list[int]
    steam_before: ProcessWire
    steam_after: ProcessWire
    source_before: SourceWire
    source_after: SourceWire
    tray_manager_pointer_rva: str
    tray_manager_address: str
    tray_state_offset: str
    tray_state_samples: list[int]

class CommonWire(TypedDict):
    schema: Literal["xar.steam-offline-state-probe/v2"]
    machine_id: str
    observed_at_utc: str
    nonce: str
    reason: Reason
    steam: ProcessWire | None
    source: SourceWire | None
    endpoint: EndpointWire | None
    diagnostics: list[str]
    observation_method: ObservationMethod | None
    native_evidence: NativeEvidenceWire | None


class ObservedWire(CommonWire):
    status: Literal["offline", "online"]
    offline_mode: bool


class UnavailableWire(CommonWire):
    status: Literal["unavailable"]


ProbeWire = ObservedWire | UnavailableWire


@dataclass(frozen=True)
class ProcessIdentity:
    pid: int
    birth_filetime: str
    exe: str
    file_version: str

    def to_wire(self) -> ProcessWire:
        return {"pid": self.pid, "birth_filetime": self.birth_filetime, "exe": self.exe,
                "file_version": self.file_version}


@dataclass(frozen=True)
class SourceIdentity:
    path: str
    bytes: int
    sha256: str
    file_id: str
    mtime_ns: str

    def to_wire(self) -> SourceWire:
        return {"path": self.path, "bytes": self.bytes, "sha256": self.sha256,
                "file_id": self.file_id, "mtime_ns": self.mtime_ns}


@dataclass(frozen=True)
class EndpointIdentity:
    pid: int
    birth_filetime: str
    port: int
    target_id: str
    target_url: str

    def to_wire(self) -> EndpointWire:
        return {"pid": self.pid, "birth_filetime": self.birth_filetime,
                "port": self.port, "target_id": self.target_id,
                "target_url": self.target_url}



@dataclass(frozen=True)
class NativeEvidence:
    machine_id: str
    observed_at_utc: str
    nonce: str
    module_base: str
    module_size: int
    value_rva: str
    value_address: str
    producer_rva: str
    producer_anchor_hex: str
    producer_anchor_sha256: str
    raw_samples: tuple[int, int]
    steam_before: ProcessIdentity
    steam_after: ProcessIdentity
    source_before: SourceIdentity
    source_after: SourceIdentity
    tray_manager_pointer_rva: str
    tray_manager_address: str
    tray_state_offset: str
    tray_state_samples: tuple[int, int]

    def to_wire(self) -> NativeEvidenceWire:
        return {
            "machine_id": self.machine_id, "observed_at_utc": self.observed_at_utc,
            "nonce": self.nonce, "module_base": self.module_base,
            "module_size": self.module_size, "value_rva": self.value_rva,
            "value_address": self.value_address, "producer_rva": self.producer_rva,
            "producer_anchor_hex": self.producer_anchor_hex,
            "producer_anchor_sha256": self.producer_anchor_sha256,
            "raw_samples": list(self.raw_samples),
            "steam_before": self.steam_before.to_wire(),
            "steam_after": self.steam_after.to_wire(),
            "source_before": self.source_before.to_wire(),
            "source_after": self.source_after.to_wire(),
            "tray_manager_pointer_rva": self.tray_manager_pointer_rva,
            "tray_manager_address": self.tray_manager_address,
            "tray_state_offset": self.tray_state_offset,
            "tray_state_samples": list(self.tray_state_samples),
        }

@dataclass(frozen=True)
class ProbeResult:
    machine_id: str
    observed_at_utc: str
    nonce: str
    status: State
    reason: Reason
    steam: ProcessIdentity | None
    source: SourceIdentity | None
    endpoint: EndpointIdentity | None
    diagnostics: tuple[str, ...] = ()
    observation_method: ObservationMethod | None = None
    native_evidence: NativeEvidence | None = None

    def to_wire(self) -> ProbeWire:
        common: CommonWire = {
            "schema": "xar.steam-offline-state-probe/v2",
            "machine_id": self.machine_id, "observed_at_utc": self.observed_at_utc,
            "nonce": self.nonce, "reason": self.reason,
            "steam": self.steam.to_wire() if self.steam else None,
            "source": self.source.to_wire() if self.source else None,
            "endpoint": self.endpoint.to_wire() if self.endpoint else None,
            "diagnostics": list(self.diagnostics),
            "observation_method": self.observation_method,
            "native_evidence": self.native_evidence.to_wire() if self.native_evidence else None,
        }
        if self.status == "unavailable":
            return {**common, "status": "unavailable"}
        return {**common, "status": self.status,
                "offline_mode": self.status == "offline"}


def object_map(value: object) -> dict[str, object]:
    """Validate one JSON object without trusting arbitrary dynamic values."""
    if not isinstance(value, dict):
        raise ValueError("expected JSON object")
    result: dict[str, object] = {}
    for key, item in value.items():
        if type(key) is not str:
            raise ValueError("non-string object key")
        result[key] = item
    return result


def exact_int(value: object, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError("invalid exact integer")
    return value


def text(value: object) -> str:
    if type(value) is not str or not value:
        raise ValueError("expected nonempty text")
    return value


def decimal(value: object, *, maximum: int = 2**128-1) -> str:
    result = text(value)
    if len(result) > 39 or _DECIMAL.fullmatch(result) is None or int(result) > maximum:
        raise ValueError("expected canonical decimal string")
    return result


def parse_getter(value: object, nonce: str) -> Literal["offline", "online"]:
    """Both independently returned App getters must be strict equal booleans."""
    item = object_map(value)
    if set(item) != {"nonce", "direct", "method"} or item["nonce"] != nonce:
        raise ValueError("invalid getter shape or nonce")
    direct, method = item["direct"], item["method"]
    if type(direct) is not bool or type(method) is not bool or direct is not method:
        raise ValueError("missing, nonboolean or inconsistent App getters")
    return "offline" if direct else "online"



def parse_process_identity(value: object) -> ProcessIdentity:
    p = object_map(value)
    if set(p) != {"pid", "birth_filetime", "exe", "file_version"}:
        raise ValueError("invalid Steam identity")
    return ProcessIdentity(exact_int(p["pid"], 1, 2**32-1),
                           decimal(p["birth_filetime"], maximum=2**64-1), text(p["exe"]),
                           text(p["file_version"]))


def parse_source_identity(value: object) -> SourceIdentity:
    s = object_map(value)
    if set(s) != {"path", "bytes", "sha256", "file_id", "mtime_ns"}:
        raise ValueError("invalid source identity")
    digest = text(s["sha256"])
    if _HEX64.fullmatch(digest) is None:
        raise ValueError("invalid source digest")
    return SourceIdentity(text(s["path"]), exact_int(s["bytes"], 1, 2**53-1),
                          digest, decimal(s["file_id"]), decimal(s["mtime_ns"], maximum=2**64-1))


def parse_native_evidence(value: object) -> NativeEvidence:
    item = object_map(value)
    if set(item) != {
        "machine_id", "observed_at_utc", "nonce", "module_base", "module_size",
        "value_rva", "value_address", "producer_rva", "producer_anchor_hex",
        "producer_anchor_sha256", "raw_samples", "steam_before", "steam_after",
        "source_before", "source_after", "tray_manager_pointer_rva",
        "tray_manager_address", "tray_state_offset", "tray_state_samples",
    }:
        raise ValueError("invalid native evidence shape")
    base = decimal(item["module_base"], maximum=2**64-1)
    size = exact_int(item["module_size"], 1, 2**32-1)
    rva = decimal(item["value_rva"])
    address = decimal(item["value_address"], maximum=2**64-1)
    producer_rva = decimal(item["producer_rva"])
    if (int(base) == 0 or not 0 <= int(rva) < size or
            int(base) + int(rva) != int(address) or
            not 0 <= int(producer_rva) < size):
        raise ValueError("native address/module binding mismatch")
    anchor = text(item["producer_anchor_hex"])
    if re.fullmatch(r"(?:[0-9a-f]{2}){1,256}", anchor) is None:
        raise ValueError("invalid native producer anchor")
    import hashlib
    anchor_sha = text(item["producer_anchor_sha256"])
    if hashlib.sha256(bytes.fromhex(anchor)).hexdigest() != anchor_sha:
        raise ValueError("native producer anchor digest mismatch")
    raw = item["raw_samples"]
    if not isinstance(raw, list) or len(raw) != 2:
        raise ValueError("native samples must be a two-element JSON array")
    samples = (exact_int(raw[0], 0, 1), exact_int(raw[1], 0, 1))
    if samples[0] != samples[1]:
        raise ValueError("native mode changed during observation")
    manager_rva = decimal(item["tray_manager_pointer_rva"])
    manager = decimal(item["tray_manager_address"], maximum=2**64-1)
    tray_offset = decimal(item["tray_state_offset"])
    if (not 0 <= int(manager_rva) <= size - 8 or int(manager) == 0 or
            int(tray_offset) != 340):
        raise ValueError("invalid tray manager/address/state offset")
    tray_raw = item["tray_state_samples"]
    if not isinstance(tray_raw, list) or len(tray_raw) != 2:
        raise ValueError("tray states must be a two-element JSON array")
    tray_samples = (exact_int(tray_raw[0], 4, 4), exact_int(tray_raw[1], 4, 4))
    if samples != (1, 1) or tray_samples != (4, 4):
        raise ValueError("native provider only qualifies stable offline mode")
    before, after = parse_process_identity(item["steam_before"]), parse_process_identity(item["steam_after"])
    source_before, source_after = parse_source_identity(item["source_before"]), parse_source_identity(item["source_after"])
    if before != after or source_before != source_after:
        raise ValueError("native process/source identity changed")
    return NativeEvidence(
        text(item["machine_id"]), text(item["observed_at_utc"]), text(item["nonce"]),
        base, size, rva, address, producer_rva, anchor, anchor_sha, samples,
        before, after, source_before, source_after,
        manager_rva, manager, tray_offset, tray_samples,
    )


def parse_result(value: object) -> ProbeResult:
    """Validate persisted JSON before constructing the internal immutable model."""
    item = object_map(value)
    required = {"schema", "machine_id", "observed_at_utc", "nonce", "status",
                "reason", "steam", "source", "endpoint", "diagnostics"}
    status = item.get("status")
    if status not in ("offline", "online", "unavailable"):
        raise ValueError("unknown status")
    schema = item.get("schema")
    if schema == "xar.steam-offline-state-probe/v2":
        required |= {"observation_method", "native_evidence"}
    elif schema != "xar.steam-offline-state-probe/v1":
        raise ValueError("unknown receipt schema")
    expected = required if status == "unavailable" else required | {"offline_mode"}
    if set(item) != expected:
        raise ValueError("invalid receipt shape")
    reason = text(item["reason"])
    if reason not in _REASON_VALUES:
        raise ValueError("unknown reason")
    if (reason == "observed") != (status != "unavailable"):
        raise ValueError("status/reason disagree")
    if status != "unavailable":
        offline = item["offline_mode"]
        if type(offline) is not bool or offline != (status == "offline"):
            raise ValueError("status/offline_mode disagree")
    steam = parse_process_identity(item["steam"]) if item["steam"] is not None else None
    source = parse_source_identity(item["source"]) if item["source"] is not None else None
    endpoint: EndpointIdentity | None = None
    if item["endpoint"] is not None:
        e = object_map(item["endpoint"])
        if set(e) != {"pid", "birth_filetime", "port", "target_id", "target_url"}:
            raise ValueError("invalid endpoint identity")
        endpoint = EndpointIdentity(exact_int(e["pid"], 1, 2**32-1),
                                    decimal(e["birth_filetime"]),
                                    exact_int(e["port"], 1, 65535),
                                    text(e["target_id"]), text(e["target_url"]))
    diagnostics_value = item["diagnostics"]
    if not isinstance(diagnostics_value, list):
        raise ValueError("diagnostics must be a JSON array")
    diagnostics = tuple(text(entry) for entry in diagnostics_value)
    if status == "unavailable":
        state: State = "unavailable"
    elif status == "offline":
        state = "offline"
    else:
        state = "online"
    # Narrow the validated finite reason without a cast or unchecked alias.
    reason_value: Reason
    if reason == "observed": reason_value = "observed"
    elif reason == "unsupported_platform": reason_value = "unsupported_platform"
    elif reason == "steam_not_found": reason_value = "steam_not_found"
    elif reason == "ambiguous_steam": reason_value = "ambiguous_steam"
    elif reason == "source_not_qualified": reason_value = "source_not_qualified"
    elif reason == "cdp_not_enabled": reason_value = "cdp_not_enabled"
    elif reason == "cdp_not_owned": reason_value = "cdp_not_owned"
    elif reason == "cdp_unavailable": reason_value = "cdp_unavailable"
    elif reason == "context_unavailable": reason_value = "context_unavailable"
    elif reason == "invalid_observation": reason_value = "invalid_observation"
    elif reason == "steam_instance_changed": reason_value = "steam_instance_changed"
    else: reason_value = "native_query_failed"
    native_evidence: NativeEvidence | None = None
    method: ObservationMethod | None = None
    if schema == "xar.steam-offline-state-probe/v1":
        # Explicit persisted-v1 migration; v1 only implemented the CEF provider.
        method = "cef_app_getters" if state != "unavailable" else None
    else:
        raw_method = item["observation_method"]
        if raw_method == "cef_app_getters": method = "cef_app_getters"
        elif raw_method == "native_current_user_byte": method = "native_current_user_byte"
        elif raw_method is not None: raise ValueError("unknown observation method")
        if item["native_evidence"] is not None:
            native_evidence = parse_native_evidence(item["native_evidence"])
    if state != "unavailable":
        if steam is None or source is None:
            raise ValueError("observed state requires source and live instance bindings")
        if method == "cef_app_getters":
            if endpoint is None or native_evidence is not None:
                raise ValueError("invalid CEF observation provenance")
        elif method == "native_current_user_byte":
            if endpoint is not None or native_evidence is None:
                raise ValueError("invalid native observation provenance")
            if (native_evidence.machine_id != item["machine_id"] or
                    native_evidence.observed_at_utc != item["observed_at_utc"] or
                    native_evidence.nonce != item["nonce"] or
                    native_evidence.steam_before != steam or
                    native_evidence.source_before != source or
                    state != "offline" or native_evidence.raw_samples != (1, 1)):
                raise ValueError("native observation/receipt binding mismatch")
        else:
            raise ValueError("observed state requires an explicit method")
    elif method is not None or native_evidence is not None:
        raise ValueError("unavailable result cannot carry verified native provenance")
    return ProbeResult(text(item["machine_id"]), text(item["observed_at_utc"]),
                       text(item["nonce"]), state, reason_value,
                       steam, source, endpoint, diagnostics, method, native_evidence)
