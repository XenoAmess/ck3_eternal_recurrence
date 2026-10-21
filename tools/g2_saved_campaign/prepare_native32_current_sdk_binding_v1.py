"""Compose an optional Native32 journal adapter for an independently frozen SDK.

The original Source31 Native32 qualification remains historical. This module
does not launch, connect, mutate an SDK, or qualify ordinary planner execution.
"""
from __future__ import annotations

import ast
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from tools.g2_saved_campaign.current_saved_basis_v1 import (
    ExactRefV1, JsonObject, digest, integer, need, parse_ref, record, text,
)

READER_NAME = "observer_journal_runtime_v1.py"
EXTENSION_NAME = "native32_mcp_extension_v1.py"
BINDING_NAME = "ROOT-NATIVE32-CURRENT-SDK-BINDING01.json"
HISTORICAL_BINDING_NAME = "ROOT-NATIVE32-PRODUCTION-BINDING01.json"
SCHEMA = "xar.native32.current-sdk-observer-binding/v1"
HISTORICAL_READER_PIN = (43698, "2a3016363c9b3633611f3ba75d217c36f5bb30e733886db571a48138bf6a47f8")
HISTORICAL_EXTENSION_PIN = (3082, "25d4b1c322f4bcaaf8382590c8ee95b6fd0277aa06bcf4a02391fba98630da18")


def _pin(raw: bytes) -> tuple[int, str]:
    need(type(raw) is bytes, "source bytes required")
    return len(raw), hashlib.sha256(raw).hexdigest()


def _replace(source: str, before: str, after: str, count: int = 1) -> str:
    need(source.count(before) == count, "one frozen source seam: " + before)
    return source.replace(before, after)


@dataclass(frozen=True, slots=True)
class Native32CurrentSdkBundleV1:
    reader_bytes: bytes
    extension_bytes: bytes
    current_binding_bytes: bytes

    def files(self) -> dict[str, bytes]:
        return {READER_NAME: self.reader_bytes, EXTENSION_NAME: self.extension_bytes,
                BINDING_NAME: self.current_binding_bytes}

    def refs(self, runtime_root: Path) -> dict[str, ExactRefV1]:
        need(runtime_root.is_absolute(), "absolute future runtime root")
        return {name: ExactRefV1(str(runtime_root / name), *_pin(raw))
                for name, raw in self.files().items()}



@dataclass(frozen=True, slots=True)
class Native32CurrentSdkConsumersV1:
    entry_bytes: bytes
    queue_bytes: bytes
    outer_bytes: bytes


def _outer_external_table_v1(
    raw: bytes,
) -> tuple[ast.Assign, dict[str, tuple[int, str]]]:
    matches = [node for node in ast.parse(raw).body if isinstance(node, ast.Assign)
               and any(isinstance(target, ast.Name)
                       and target.id == "_C23_EXTERNAL_IMPORT_PINS"
                       for target in node.targets)]
    need(len(matches) == 1, "one canonical external source assignment")
    node = matches[0]
    need(len(node.targets) == 1, "external assignment has no aliases")
    if not isinstance(node.value, ast.Dict):
        raise ValueError("literal canonical external source table required")
    pins: dict[str, tuple[int, str]] = {}
    for key_node, value_node in zip(node.value.keys, node.value.values, strict=True):
        if not isinstance(key_node, ast.Constant) or type(key_node.value) is not str:
            raise ValueError("literal external module name required")
        name = text(key_node.value)
        need(name not in pins, "unique external module name")
        if not isinstance(value_node, ast.Tuple) or len(value_node.elts) != 2:
            raise ValueError("external source pin is an exact tuple")
        size_node, sha_node = value_node.elts
        if not isinstance(size_node, ast.Constant) or not isinstance(sha_node, ast.Constant):
            raise ValueError("literal external source pin required")
        pins[name] = (integer(size_node.value, 1), digest(sha_node.value))
    need(len(pins) == 26, "exact original 26 external source pins")
    return node, pins


def _patch_native32_outer_v1(
    raw: bytes, bundle: Native32CurrentSdkBundleV1,
) -> bytes:
    node, before = _outer_external_table_v1(raw)
    updates = {
        "observer_journal_runtime_v1": _pin(bundle.reader_bytes),
        "native32_mcp_extension_v1": _pin(bundle.extension_bytes),
    }
    need(before.get("observer_journal_runtime_v1") == HISTORICAL_READER_PIN
         and before.get("native32_mcp_extension_v1") == HISTORICAL_EXTENSION_PIN,
         "canonical external table must match both historical sidecars")
    after = {**before, **updates}
    if node.end_lineno is None or node.end_col_offset is None:
        raise ValueError("bounded canonical assignment extent required")
    lines = raw.splitlines(keepends=True)
    start = sum(len(line) for line in lines[:node.lineno - 1]) + node.col_offset
    end = sum(len(line) for line in lines[:node.end_lineno - 1]) + node.end_col_offset
    changed = raw[:start] + ("_C23_EXTERNAL_IMPORT_PINS = " + repr(after)).encode() + raw[end:]
    compile(changed, "<current SDK canonical external pins>", "exec", dont_inherit=True)
    _, checked = _outer_external_table_v1(changed)
    need(set(checked) == set(before)
         and {name for name in before if before[name] != checked[name]} == set(updates)
         and all(checked[name] == before[name] for name in before if name not in updates),
         "only the two Native32 external pins may change")
    return changed

# This suffix is emitted into the existing reader slot, after its immutable
# offline parser. It imports no public compositor and issues no extra RPC.
_RUNTIME = r'''
import sys as _current_sdk_sys


class CurrentSDKBindingWireV1(TypedDict):
    schema: Literal["xar.native32.current-sdk-observer-binding/v1"]
    machine_id: str
    status: Literal["CURRENT_SDK_SOURCE_BOUND_NOT_RUNTIME_ADMITTED"]
    historical_binding_ref: ExactRefV1
    current_sdk_base_ref: ExactRefV1
    current_sdk_anchor_ref: ExactRefV1


@dataclass(frozen=True, slots=True)
class CurrentSDKBindingV1:
    historical: ProductionBindingV2
    current_wire: CurrentSDKBindingWireV1
    sdk_root: Path


_CURRENT_SDK_DELTA_V1 = frozenset({
    "xar_autoplayer/bridge/native_driver.py",
    "xar_autoplayer/bridge/mcp_server.py",
    "xar_autoplayer/bridge/route_window_clock_v1.py",
    "xar_autoplayer/successor_ui_pending_ledger_v1.py",
    "xar_autoplayer/ordinary_sway_schedule_v1.py",
    "xar_autoplayer/bridge/ordinary_sway_service_v1.py",
    "xar_autoplayer/sway_formal_consumer.py",
    "xar_autoplayer/bridge/war_stationary_sway_opportunity_v1.py",
})
_CURRENT_SDK_NEW_V1 = frozenset({
    "xar_autoplayer/bridge/route_window_clock_v1.py",
    "xar_autoplayer/bridge/war_stationary_sway_opportunity_v1.py",
})


class _CurrentSdkSourceRowV1(TypedDict):
    relative: str
    bytes: int
    sha256: str
    git_blob_sha1: str
    git_mode: str


def _current_sdk_rows_v1(value: object, count: int) -> dict[str, _CurrentSdkSourceRowV1]:
    if type(value) is not list or len(value) != count:
        raise ValueError("exact current SDK inventory count required")
    result: dict[str, _CurrentSdkSourceRowV1] = {}
    for item in value:
        row = _obj(item, {"relative", "bytes", "sha256", "git_blob_sha1", "git_mode"})
        relative = _text32(row["relative"])
        if ("\\" in relative or relative.startswith("/") or ":" in relative
                or any(part in ("", ".", "..") for part in relative.split("/"))
                or relative in result):
            raise ValueError("unique confined SDK relative source required")
        size = _int(row["bytes"], (1 << 53) - 1)
        sha = _text32(row["sha256"])
        blob = _text32(row["git_blob_sha1"])
        mode = _text32(row["git_mode"])
        if (re.fullmatch("[0-9a-f]{64}", sha) is None
                or re.fullmatch("[0-9a-f]{40}", blob) is None
                or mode not in ("100644", "100755")):
            raise ValueError("exact SDK source identity required")
        result[relative] = _CurrentSdkSourceRowV1(relative=relative, bytes=size,
            sha256=sha, git_blob_sha1=blob, git_mode=mode)
    return result


def _current_sdk_pin2_v1(value: object) -> tuple[int, str]:
    row = _obj(value, {"bytes", "sha256"})
    size = _int(row["bytes"], (1 << 53) - 1)
    sha = _text32(row["sha256"])
    if re.fullmatch("[0-9a-f]{64}", sha) is None:
        raise ValueError("source delta SHA required")
    return size, sha


def _current_sdk_origins_v1(root: Path) -> None:
    paths = set(_CURRENT_SDK_DELTA_V1) | {
        "xar_autoplayer/bridge/player_heir_candidate_component_v1.py",
        "xar_autoplayer/bridge/native_loaded_provider_custody_v1.py",
        "xar_autoplayer/bridge/native_loaded_provider_origin_v1.py",
    }
    for relative in paths:
        module = _current_sdk_sys.modules.get(relative[:-3].replace("/", "."))
        if module is not None:
            actual = Path(_text32(getattr(module, "__file__", None))).resolve(strict=True)
            if actual != (root / relative).resolve(strict=True):
                raise ValueError("foreign cached current SDK module: " + relative)


def qualify_native32_binding_v1(value: object, *, machine_id: str) -> CurrentSDKBindingV1:
    """Explicit current SDK qualification; old v2 is never accepted as this wire."""
    row = _obj(value, {"schema", "machine_id", "status", "historical_binding_ref",
                      "current_sdk_base_ref", "current_sdk_anchor_ref"})
    if (row["schema"] != "xar.native32.current-sdk-observer-binding/v1"
            or row["machine_id"] != machine_id or not machine_id
            or row["status"] != "CURRENT_SDK_SOURCE_BOUND_NOT_RUNTIME_ADMITTED"):
        raise ValueError("explicit current SDK journal binding required")
    historical_ref = _ref32(row["historical_binding_ref"])
    base_ref = _ref32(row["current_sdk_base_ref"])
    anchor_ref = _ref32(row["current_sdk_anchor_ref"])
    historical = _qualify_native32_historical_binding_v2(
        _read32(historical_ref, 65536), machine_id=machine_id)
    old_base = _read32(historical.wire["sdk_base_ref"], 524288)
    old_anchor = _read32(historical.wire["sdk_anchor_ref"], 65536)
    base = _read32(base_ref, 524288)
    anchor = _read32(anchor_ref, 65536)
    if (base.get("schema") != "root.ck3.final-sdk-freeze/v1"
            or base.get("status") != "FINAL_SOURCE_FROZEN"
            or base.get("machine_id") != machine_id or base.get("runtime_admitted") is not False
            or type(base.get("source_file_count")) is not int or base["source_file_count"] != 1468
            or _ref32(base.get("source32_canonical_anchor")) != anchor_ref
            or anchor.get("schema") != "xar.source32.canonical-git-anchor/v1"
            or anchor.get("status") != "CANONICAL_REF_CREATED_NOT_DEPLOYED"
            or anchor.get("machine_id") != machine_id
            or anchor.get("parent") != old_anchor.get("commit")
            or anchor.get("commit") != base.get("business_source_commit")
            or re.fullmatch("[0-9a-f]{40}", _text32(anchor.get("commit"))) is None
            or type(anchor.get("source_epoch_count")) is not int or anchor["source_epoch_count"] != 43
            or type(anchor.get("source_file_count")) is not int or anchor["source_file_count"] != 1468):
        raise ValueError("independent Source32 BASE and canonical anchor required")
    old_rows = _current_sdk_rows_v1(old_base.get("files"), 1466)
    new_rows = _current_sdk_rows_v1(base.get("files"), 1468)
    if (set(old_rows) - set(new_rows)
            or set(new_rows) - set(old_rows) != _CURRENT_SDK_NEW_V1
            or {name for name in new_rows if old_rows.get(name) != new_rows[name]}
               != _CURRENT_SDK_DELTA_V1):
        raise ValueError("only the exact Source32 eight deltas and two new leaves are admitted")
    total = sum(item["bytes"] for item in new_rows.values())
    if (_int(base.get("source_bytes"), (1 << 53) - 1) != total
            or _int(anchor.get("source_bytes"), (1 << 53) - 1) != total):
        raise ValueError("Source32 inventory byte total differs")
    outputs = _current_sdk_rows_v1(anchor.get("output_pins"), 8)
    if outputs != {name: new_rows[name] for name in _CURRENT_SDK_DELTA_V1}:
        raise ValueError("canonical Source32 output pins differ")
    changes = anchor.get("canonical_patch_rows")
    if type(changes) is not list or len(changes) != 8:
        raise ValueError("eight canonical patch rows required")
    seen: set[str] = set()
    prefix = "ck3_autonomous_player/src/"
    for item in changes:
        patch = _obj(item)
        name = _text32(patch.get("relative"))
        if not name.startswith(prefix):
            raise ValueError("canonical patch path prefix required")
        name = name[len(prefix):]
        if name in seen or name not in _CURRENT_SDK_DELTA_V1:
            raise ValueError("unique approved canonical patch required")
        seen.add(name)
        if "before_pin" not in patch or "output_pin" not in patch:
            raise ValueError("explicit old and new source pins required")
        expected = new_rows[name]
        if _current_sdk_pin2_v1(patch["output_pin"]) != (expected["bytes"], expected["sha256"]):
            raise ValueError("canonical output pin differs")
        if name in _CURRENT_SDK_NEW_V1:
            if patch["before_pin"] is not None:
                raise ValueError("new source must have explicit null predecessor")
        else:
            old = old_rows[name]
            if _current_sdk_pin2_v1(patch["before_pin"]) != (old["bytes"], old["sha256"]):
                raise ValueError("canonical predecessor source differs")
    root = Path(_text32(base.get("source_root"))).resolve(strict=True)
    if not root.is_dir() or root == historical.sdk_root:
        raise ValueError("independent current SDK source root required")
    _current_sdk_origins_v1(root)
    wire: CurrentSDKBindingWireV1 = {
        "schema": "xar.native32.current-sdk-observer-binding/v1",
        "machine_id": machine_id, "status": "CURRENT_SDK_SOURCE_BOUND_NOT_RUNTIME_ADMITTED",
        "historical_binding_ref": historical_ref, "current_sdk_base_ref": base_ref,
        "current_sdk_anchor_ref": anchor_ref,
    }
    return CurrentSDKBindingV1(historical, wire, root)
'''


def compose_native32_current_sdk_binding_v1(
    historical_reader: bytes, historical_extension: bytes, *,
    historical_binding_ref: ExactRefV1, current_sdk_base_ref: ExactRefV1,
    current_sdk_anchor_ref: ExactRefV1, machine_id: str,
) -> Native32CurrentSdkBundleV1:
    """Emit three immutable materials; actual refs must exist before runtime use."""
    need(_pin(historical_reader) == HISTORICAL_READER_PIN, "exact historical reader required")
    need(_pin(historical_extension) == HISTORICAL_EXTENSION_PIN, "exact historical extension required")
    for reference in (historical_binding_ref, current_sdk_base_ref, current_sdk_anchor_ref):
        parse_ref(reference.to_wire())
        need(Path(reference.path).is_absolute() and reference.bytes > 0, "absolute nonempty exact ref")
    text(machine_id)
    source = historical_reader.decode("utf-8")
    old_tree = ast.parse(source)
    old_function = next(node for node in old_tree.body
                        if isinstance(node, ast.FunctionDef) and node.name == "qualify_native32_binding_v1")
    old_body = ast.dump(ast.Module(body=old_function.body, type_ignores=[]), include_attributes=False)
    source = _replace(source, "def qualify_native32_binding_v1(value: object, *,",
                      "def _qualify_native32_historical_binding_v2(value: object, *,")
    source = _replace(source, "    binding: ProductionBindingV2\n", "    binding: CurrentSDKBindingV1\n")
    source = _replace(source, 'value.native_dll_sha256 != binding.wire["dll"]',
                      'value.native_dll_sha256 != binding.historical.wire["dll"]')
    source = _replace(source, 'context.binding.wire["dll"]', 'context.binding.historical.wire["dll"]')
    source = _replace(source, 'context.binding.wire["production_result_ref"]',
                      'context.binding.historical.wire["production_result_ref"]')
    source = _replace(source, "    _same_holder32(owner, context.binding.sdk_root)\n",
                      "    _same_holder32(owner, context.binding.sdk_root)\n"
                      "    _current_sdk_origins_v1(context.binding.sdk_root)\n")
    source += "\n" + _RUNTIME
    tree = ast.parse(source)
    kept = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
                and node.name == "_qualify_native32_historical_binding_v2")
    need(ast.dump(ast.Module(body=kept.body, type_ignores=[]), include_attributes=False) == old_body,
         "historical qualifier body must remain unchanged")
    extension = historical_extension.decode("utf-8")
    extension = _replace(extension, 'binding.wire["dll"]', 'binding.historical.wire["dll"]')
    extension = _replace(extension, 'binding.wire["production_result_ref"]',
                         'binding.historical.wire["production_result_ref"]')
    binding: JsonObject = {
        "schema": SCHEMA, "machine_id": machine_id,
        "status": "CURRENT_SDK_SOURCE_BOUND_NOT_RUNTIME_ADMITTED",
        "historical_binding_ref": historical_binding_ref.to_wire(),
        "current_sdk_base_ref": current_sdk_base_ref.to_wire(),
        "current_sdk_anchor_ref": current_sdk_anchor_ref.to_wire(),
    }
    compile(source, "<Native32 current SDK reader>", "exec", dont_inherit=True)
    compile(extension, "<Native32 current SDK extension>", "exec", dont_inherit=True)
    return Native32CurrentSdkBundleV1(source.encode(), extension.encode(),
        json.dumps(binding, ensure_ascii=True, sort_keys=True,
                   separators=(",", ":"), allow_nan=False).encode())


def patch_native32_current_sdk_consumers_v1(
    entry: bytes, queue: bytes, outer: bytes, bundle: Native32CurrentSdkBundleV1,
) -> Native32CurrentSdkConsumersV1:
    """Patch the three real consumers while preserving the other 24 external pins."""
    source = entry.decode("utf-8")
    for name, old_pin, raw in ((READER_NAME, HISTORICAL_READER_PIN, bundle.reader_bytes),
                              (EXTENSION_NAME, HISTORICAL_EXTENSION_PIN, bundle.extension_bytes)):
        source = _replace(source, repr((name, *old_pin)), repr((name, *_pin(raw))))
    source = _replace(source, "_n32_native.get('native32_observer_binding')",
                      "_n32_native.get('native32_current_sdk_binding')")
    need(source.count(HISTORICAL_BINDING_NAME) == 2, "two exact entry binding consumer paths")
    source = source.replace(HISTORICAL_BINDING_NAME, BINDING_NAME)
    control = queue.decode("utf-8")
    control = _replace(control, repr(HISTORICAL_BINDING_NAME), repr(BINDING_NAME))
    compile(source, "<current SDK entry pins>", "exec", dont_inherit=True)
    compile(control, "<current SDK Queue binding>", "exec", dont_inherit=True)
    return Native32CurrentSdkConsumersV1(source.encode(), control.encode(),
                                        _patch_native32_outer_v1(outer, bundle))
