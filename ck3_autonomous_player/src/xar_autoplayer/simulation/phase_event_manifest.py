"""Strict immutable loader for the pinned stock combat phase-event manifest."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from importlib import resources
import json
from pathlib import Path
import re
from types import MappingProxyType
from typing import Any, Mapping


STOCK_PHASE_EVENT_MANIFEST_SHA256 = (
    "91EDCEEDC634C5ACDCFAC8B02F53FE74C4E7A2E1768AAFC12CD0D976E874F2AC"
)
_MANIFEST_RESOURCE = "data/ck3_1_19_0_6_stock_combat_phase_events.json"
_EXPECTED_TOP_LEVEL_KEYS = (
    "schema_version",
    "game_version",
    "executable_sha256",
    "rules_source",
    "files",
    "event_rows",
    "supported_transition_opcodes",
    "completeness",
    "canonical_manifest_sha256",
)
_EXPECTED_ROW_KEYS = frozenset(
    {
        "global_load_index",
        "type_load_index",
        "key",
        "type",
        "base_weight",
        "validity_ast",
        "chance_ast",
        "effect_ast",
        "transition_tags",
        "state_dependencies",
    }
)
_NORMALIZED_AST_OPS = frozenset(
    {
        "all",
        "any",
        "call_transition",
        "ceiling",
        "compare",
        "const_bool",
        "const_fixed",
        "divide",
        "floor",
        "if",
        "modifier",
        "modifier_sequence",
        "multiply",
        "not",
        "random_branch",
        "random_list",
        "select_side_knight",
        "sequence",
        "state_ref",
        "subtract",
    }
)
_SHA256 = re.compile(r"[0-9A-F]{64}")


class PhaseEventManifestError(ValueError):
    pass


class PhaseEventEvaluatorUnavailable(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class FrozenPhaseEventSource:
    relative_path: str
    sha256: str
    load_order: int


@dataclass(frozen=True, slots=True)
class FrozenPhaseEventRow:
    global_load_index: int
    type_load_index: int
    key: str
    event_type: str
    base_weight: int
    validity_ast: Mapping[str, Any]
    chance_ast: Mapping[str, Any]
    effect_ast: Mapping[str, Any]
    transition_tags: tuple[str, ...]
    state_dependencies: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class FrozenPhaseEventCompleteness:
    loaded_playset_verified: bool
    ast_evaluator_ready: bool
    original_trace_ready: bool
    unsupported_opcodes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class FrozenPhaseEventManifest:
    schema_version: int
    game_version: str
    executable_sha256: str
    rules_source: str
    files: tuple[FrozenPhaseEventSource, ...]
    event_rows: tuple[FrozenPhaseEventRow, ...]
    supported_transition_opcodes: tuple[str, ...]
    completeness: FrozenPhaseEventCompleteness
    canonical_manifest_sha256: str

    @property
    def fidelity_gate(self) -> bool:
        return (
            self.completeness.loaded_playset_verified
            and self.completeness.ast_evaluator_ready
            and self.completeness.original_trace_ready
        )

    def require_evaluator_ready(self) -> None:
        if not self.fidelity_gate:
            raise PhaseEventEvaluatorUnavailable(
                "stock AST is frozen, but loaded-playset/evaluator/original-trace "
                "gates are not all ready"
            )


def _integer(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise PhaseEventManifestError(f"{name} must be an integer")
    return value


def _string(value: object, name: str) -> str:
    if not isinstance(value, str) or not value:
        raise PhaseEventManifestError(f"{name} must be a nonempty string")
    return value


def _string_tuple(value: object, name: str) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise PhaseEventManifestError(f"{name} must be an array")
    result = tuple(_string(item, f"{name}[{index}]") for index, item in enumerate(value))
    if len(result) != len(set(result)):
        raise PhaseEventManifestError(f"{name} contains duplicates")
    return result


def _object(value: object, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise PhaseEventManifestError(f"{name} must be an object")
    return value


def _canonical_hash(payload: dict[str, Any]) -> str:
    without_hash = dict(payload)
    without_hash.pop("canonical_manifest_sha256", None)
    encoded = json.dumps(
        without_hash,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest().upper()


def _walk_nodes(value: object):
    if isinstance(value, dict):
        if "op" in value:
            yield value
        for child in value.values():
            yield from _walk_nodes(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_nodes(child)


def _freeze_json(value: Any) -> Any:
    if isinstance(value, dict):
        return MappingProxyType({key: _freeze_json(child) for key, child in value.items()})
    if isinstance(value, list):
        return tuple(_freeze_json(child) for child in value)
    return value


def _validate_ast_row(
    row: dict[str, Any],
    *,
    name: str,
    supported_transitions: frozenset[str],
) -> None:
    declared_dependencies = set(_string_tuple(row.get("state_dependencies"), f"{name}.state_dependencies"))
    referenced_dependencies: set[str] = set()
    for field in ("validity_ast", "chance_ast", "effect_ast"):
        ast = _object(row.get(field), f"{name}.{field}")
        for node in _walk_nodes(ast):
            op = _string(node.get("op"), f"{name}.{field}.op")
            if op not in _NORMALIZED_AST_OPS:
                raise PhaseEventManifestError(f"{name} uses unsupported normalized op {op!r}")
            if op == "const_fixed":
                _integer(node.get("raw"), f"{name}.const_fixed.raw")
                if _integer(node.get("scale"), f"{name}.const_fixed.scale") != 100_000:
                    raise PhaseEventManifestError(f"{name} const_fixed scale drifted")
            elif op == "state_ref":
                referenced_dependencies.add(_string(node.get("path"), f"{name}.state_ref.path"))
            elif op == "call_transition":
                key = _string(node.get("key"), f"{name}.call_transition.key")
                if key not in supported_transitions:
                    raise PhaseEventManifestError(f"{name} transition {key!r} is not declared")
                _object(node.get("args"), f"{name}.call_transition.args")
                referenced_dependencies.update(
                    _string_tuple(
                        node.get("dependencies"),
                        f"{name}.call_transition.dependencies",
                    )
                )
    if not referenced_dependencies <= declared_dependencies:
        missing = sorted(referenced_dependencies - declared_dependencies)
        raise PhaseEventManifestError(f"{name} omits dependencies {missing!r}")


def load_stock_phase_event_manifest(
    path: str | Path | None = None,
) -> FrozenPhaseEventManifest:
    """Load and freeze the exact-build stock manifest; never enables evaluation."""

    text = (
        Path(path).read_text(encoding="utf-8")
        if path is not None
        else resources.files("xar_autoplayer.simulation")
        .joinpath(_MANIFEST_RESOURCE)
        .read_text(encoding="utf-8")
    )
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise PhaseEventManifestError("phase-event manifest is not valid JSON") from exc
    payload = _object(payload, "manifest")
    if tuple(payload) != _EXPECTED_TOP_LEVEL_KEYS:
        raise PhaseEventManifestError("phase-event manifest top-level schema/order drifted")
    canonical = _string(
        payload.get("canonical_manifest_sha256"),
        "manifest.canonical_manifest_sha256",
    )
    if canonical != STOCK_PHASE_EVENT_MANIFEST_SHA256 or _canonical_hash(payload) != canonical:
        raise PhaseEventManifestError("phase-event manifest canonical hash drifted")
    if _integer(payload.get("schema_version"), "manifest.schema_version") != 1:
        raise PhaseEventManifestError("unsupported phase-event schema version")
    if payload.get("game_version") != "1.19.0.6" or payload.get("executable_sha256") != (
        "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
    ):
        raise PhaseEventManifestError("phase-event exact-build identity drifted")
    if payload.get("rules_source") != "stock-installation-static-manifest":
        raise PhaseEventManifestError("phase-event rules source drifted")

    raw_files = payload.get("files")
    if not isinstance(raw_files, list):
        raise PhaseEventManifestError("manifest.files must be an array")
    sources: list[FrozenPhaseEventSource] = []
    for index, value in enumerate(raw_files):
        row = _object(value, f"files[{index}]")
        if set(row) != {"relative_path", "sha256", "load_order"}:
            raise PhaseEventManifestError(f"files[{index}] schema drifted")
        sha256 = _string(row.get("sha256"), f"files[{index}].sha256")
        if _SHA256.fullmatch(sha256) is None:
            raise PhaseEventManifestError(f"files[{index}].sha256 is malformed")
        if _integer(row.get("load_order"), f"files[{index}].load_order") != index:
            raise PhaseEventManifestError("phase-event source load order drifted")
        sources.append(
            FrozenPhaseEventSource(
                relative_path=_string(row.get("relative_path"), f"files[{index}].relative_path"),
                sha256=sha256,
                load_order=index,
            )
        )

    supported = _string_tuple(
        payload.get("supported_transition_opcodes"),
        "manifest.supported_transition_opcodes",
    )
    raw_rows = payload.get("event_rows")
    if not isinstance(raw_rows, list) or len(raw_rows) != 13:
        raise PhaseEventManifestError("manifest.event_rows must contain 13 rows")
    rows: list[FrozenPhaseEventRow] = []
    type_indices = {"commander": 0, "knight": 0}
    for index, value in enumerate(raw_rows):
        row = _object(value, f"event_rows[{index}]")
        if set(row) != _EXPECTED_ROW_KEYS:
            raise PhaseEventManifestError(f"event_rows[{index}] schema drifted")
        if _integer(row.get("global_load_index"), f"event_rows[{index}].global_load_index") != index:
            raise PhaseEventManifestError("global phase-event load order drifted")
        event_type = _string(row.get("type"), f"event_rows[{index}].type")
        if event_type not in type_indices:
            raise PhaseEventManifestError(f"event_rows[{index}] type is invalid")
        if _integer(row.get("type_load_index"), f"event_rows[{index}].type_load_index") != type_indices[event_type]:
            raise PhaseEventManifestError("per-type phase-event load order drifted")
        type_indices[event_type] += 1
        _validate_ast_row(
            row,
            name=f"event_rows[{index}]",
            supported_transitions=frozenset(supported),
        )
        rows.append(
            FrozenPhaseEventRow(
                global_load_index=index,
                type_load_index=type_indices[event_type] - 1,
                key=_string(row.get("key"), f"event_rows[{index}].key"),
                event_type=event_type,
                base_weight=_integer(row.get("base_weight"), f"event_rows[{index}].base_weight"),
                validity_ast=_freeze_json(row["validity_ast"]),
                chance_ast=_freeze_json(row["chance_ast"]),
                effect_ast=_freeze_json(row["effect_ast"]),
                transition_tags=_string_tuple(row.get("transition_tags"), f"event_rows[{index}].transition_tags"),
                state_dependencies=_string_tuple(row.get("state_dependencies"), f"event_rows[{index}].state_dependencies"),
            )
        )
    if type_indices != {"commander": 4, "knight": 9}:
        raise PhaseEventManifestError("phase-event type counts drifted")
    if len({row.key for row in rows}) != len(rows):
        raise PhaseEventManifestError("phase-event keys are not unique")

    completeness_row = _object(payload.get("completeness"), "manifest.completeness")
    if set(completeness_row) != {
        "loaded_playset_verified",
        "ast_evaluator_ready",
        "original_trace_ready",
        "unsupported_opcodes",
    }:
        raise PhaseEventManifestError("phase-event completeness schema drifted")
    booleans = tuple(
        completeness_row.get(name)
        for name in (
            "loaded_playset_verified",
            "ast_evaluator_ready",
            "original_trace_ready",
        )
    )
    if any(not isinstance(value, bool) for value in booleans):
        raise PhaseEventManifestError("phase-event completeness flags are malformed")
    completeness = FrozenPhaseEventCompleteness(
        loaded_playset_verified=booleans[0],
        ast_evaluator_ready=booleans[1],
        original_trace_ready=booleans[2],
        unsupported_opcodes=_string_tuple(
            completeness_row.get("unsupported_opcodes"),
            "manifest.completeness.unsupported_opcodes",
        ),
    )
    return FrozenPhaseEventManifest(
        schema_version=1,
        game_version="1.19.0.6",
        executable_sha256=str(payload["executable_sha256"]),
        rules_source=str(payload["rules_source"]),
        files=tuple(sources),
        event_rows=tuple(rows),
        supported_transition_opcodes=supported,
        completeness=completeness,
        canonical_manifest_sha256=canonical,
    )
