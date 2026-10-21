"""A typed feeder boundary for the current saved checkpoint.

The ordinary timed loop remains the executor. This module performs no Game,
Steam, SDK, desktop, Task or Git operation. Its runtime entry publishes only
through the original ordinary loop after Root's exact finite admission.
"""
from __future__ import annotations

import ast
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from typing import Callable, Mapping, TypeAlias, Protocol, runtime_checkable

from tools.g2_saved_campaign.current_saved_basis_v1 import (
    BasisReaderV1, CurrentSavedBasisV1, ExactRefV1, JsonObject, JsonValue, exact_read,
    integer, json_object, need, parse_json, parse_ref, record, text, utc,
)
from tools.g2_saved_campaign.file_stat_identity_v1 import (
    FileStatIdentityV1, normalize_file_stat_identity_v1,
)
from tools.g2_saved_campaign.root_current_saved_campaign_cold_owner_v1 import (
    CURRENT_SAVED_COLD_KIND, CurrentSavedColdInputsV1, CurrentSavedFeederV1,
    WarmCurrentSavedFeederInputsV1,
    transition_current_saved_cold_v1, validate_current_saved_feeder_v1,
)

from tools.g2_saved_campaign.root_saved_campaign_preflight import (
    SavedCampaignVisualEnvV1, build_saved_map_first_frame_v1,
    require_saved_campaign_visual,
)

ADMISSION_SCHEMA = "xar.current-saved-feeder-admission/v1"
REF_NAMES = (
    "basis_ref", "cold_admission_ref", "cold_bound_ref", "actual_game_ref",
    "map_admission_ref", "first_frame_ref", "active_state_ref",
    "feeder_source_ref", "loop_source_ref", "owner_source_ref",
    "feeder_task_spec_ref", "budget_ref",
)
TransitionV1: TypeAlias = Callable[[object, str, JsonObject], JsonObject]


@dataclass(frozen=True, slots=True)
class CurrentSavedFeederAdmissionV1:
    machine_id: str
    basis_ref: ExactRefV1
    cold_admission_ref: ExactRefV1
    cold_bound_ref: ExactRefV1
    actual_game_ref: ExactRefV1
    map_admission_ref: ExactRefV1
    first_frame_ref: ExactRefV1
    active_state_ref: ExactRefV1
    feeder_source_ref: ExactRefV1
    loop_source_ref: ExactRefV1
    owner_source_ref: ExactRefV1
    feeder_task_spec_ref: ExactRefV1
    budget_ref: ExactRefV1
    feeder_task_nonce: str
    first_control_sequence: int
    review_deadline_utc: str
    continue_marker: str
    stop_path: str

    def __post_init__(self) -> None:
        text(self.machine_id)
        integer(self.first_control_sequence, 1)
        utc(self.review_deadline_utc)
        text(self.continue_marker)
        text(self.stop_path)
        need(re.fullmatch("[0-9a-f]{32}", self.feeder_task_nonce) is not None,
             "fresh feeder Task nonce")
        need(self.continue_marker != self.stop_path, "distinct stop and continue paths")

    def to_wire(self) -> JsonObject:
        result: JsonObject = {
            "schema": ADMISSION_SCHEMA, "machine_id": self.machine_id,
            "feeder_task_nonce": self.feeder_task_nonce,
            "first_control_sequence": self.first_control_sequence,
            "review_deadline_utc": self.review_deadline_utc,
            "continue_marker": self.continue_marker, "stop_path": self.stop_path,
            "ordinary_cycle_credit": 0, "game_day_credit": 0,
            "original_actions_replayed": False, "window_origin_reset": False,
        }
        for name, value in self.refs():
            result[name] = value.to_wire()
        return result

    def refs(self) -> tuple[tuple[str, ExactRefV1], ...]:
        return (
            ("basis_ref", self.basis_ref), ("cold_admission_ref", self.cold_admission_ref),
            ("cold_bound_ref", self.cold_bound_ref), ("actual_game_ref", self.actual_game_ref),
            ("map_admission_ref", self.map_admission_ref), ("first_frame_ref", self.first_frame_ref),
            ("active_state_ref", self.active_state_ref), ("feeder_source_ref", self.feeder_source_ref),
            ("loop_source_ref", self.loop_source_ref), ("owner_source_ref", self.owner_source_ref),
            ("feeder_task_spec_ref", self.feeder_task_spec_ref), ("budget_ref", self.budget_ref),
        )


def parse_current_saved_feeder_admission_v1(
    value: object, *, expected_machine_id: str,
) -> CurrentSavedFeederAdmissionV1:
    fields = set(REF_NAMES) | {
        "schema", "machine_id", "feeder_task_nonce", "first_control_sequence",
        "review_deadline_utc", "continue_marker", "stop_path",
        "ordinary_cycle_credit", "game_day_credit",
        "original_actions_replayed", "window_origin_reset",
    }
    row = record(value, fields)
    need(row["schema"] == ADMISSION_SCHEMA
         and text(row["machine_id"]) == text(expected_machine_id), "feeder schema/machine")
    need(integer(row["ordinary_cycle_credit"]) == 0 and integer(row["game_day_credit"]) == 0
         and row["original_actions_replayed"] is False and row["window_origin_reset"] is False,
         "cold attachment adds no progress or replay")
    return CurrentSavedFeederAdmissionV1(
        text(row["machine_id"]),
        parse_ref(row["basis_ref"]), parse_ref(row["cold_admission_ref"]),
        parse_ref(row["cold_bound_ref"]), parse_ref(row["actual_game_ref"]),
        parse_ref(row["map_admission_ref"]), parse_ref(row["first_frame_ref"]),
        parse_ref(row["active_state_ref"]), parse_ref(row["feeder_source_ref"]),
        parse_ref(row["loop_source_ref"]), parse_ref(row["owner_source_ref"]),
        parse_ref(row["feeder_task_spec_ref"]), parse_ref(row["budget_ref"]),
        text(row["feeder_task_nonce"]), integer(row["first_control_sequence"], 1),
        utc(row["review_deadline_utc"]), text(row["continue_marker"]), text(row["stop_path"]),
    )


def encode_current_saved_feeder_admission_v1(value: CurrentSavedFeederAdmissionV1) -> bytes:
    checked = parse_current_saved_feeder_admission_v1(
        value.to_wire(), expected_machine_id=value.machine_id)
    return json.dumps(checked.to_wire(), ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def decode_current_saved_feeder_admission_v1(
    raw: bytes, *, expected_machine_id: str,
) -> CurrentSavedFeederAdmissionV1:
    need(type(raw) is bytes and len(raw) <= 32768, "bounded feeder admission")
    return parse_current_saved_feeder_admission_v1(
        parse_json(raw), expected_machine_id=expected_machine_id)


def _at(value: str) -> datetime:
    return datetime.fromisoformat(utc(value).replace("Z", "+00:00"))


def _same_path(left: str | Path, right: str | Path) -> bool:
    return Path(left).resolve() == Path(right).resolve()


def _checked(reader: BasisReaderV1, reference: ExactRefV1, limit: int = 262144) -> dict[str, object]:
    return record(parse_json(exact_read(reader, reference, limit)))


def _next(reader: BasisReaderV1, runtime_dir: Path) -> int:
    path = runtime_dir / "NEXT-SEQUENCE-P37.json"
    # NEXT is mutable and has no frozen hash: the exact integer is checked
    # again immediately before publishing by the original queue producer.
    with path.open("rb") as stream:
        raw = stream.read(16385)
    need(len(raw) <= 16384, "bounded current NEXT")
    return integer(record(parse_json(raw)).get("next_sequence"), 1)


def _first_frame(
    row: dict[str, object], game: dict[str, object], *, machine_id: str, now_utc: str,
) -> None:
    canonical = build_saved_map_first_frame_v1(row, expected_machine_id=machine_id)
    need(canonical["stage"] == "saved_map", "canonical saved-map stage")
    need(row.get("schema") == "xar.ck3.decision-text-first-frame/v1"
         and row.get("machine_id") == machine_id and row.get("status") == "GREEN"
         and row.get("stage") == "saved_map" and row.get("reviewer") == "/root",
         "actual Root saved-map first frame")
    for name in ("before_selection_game_pixels_reviewed", "before_selection_decision_pixels_reviewed",
                 "decision_text_visible", "Game_map_visible", "initial_waiting_text_is_not_planner_output"):
        need(row.get(name) is True, "Root first-frame fact: " + name)
    for name in ("legacy_blue_window_visible", "film_title_visible"):
        need(row.get(name) is False, "retired/film display present: " + name)
    need("decision_overlay_visible" not in row, "retired first-frame alias")
    pid = integer(row.get("game_pid"), 1, (1 << 32) - 1)
    # The existing Python-only first-frame receipt has an integer FILETIME ABI.
    # Preserve and compare it exactly; admission JSON never copies it.
    birth = integer(row.get("game_creation_filetime"), 1, (1 << 64) - 1)
    need(pid == integer(game.get("pid"), 1, (1 << 32) - 1)
         and birth == integer(game.get("creation_filetime"), 1, (1 << 64) - 1),
         "first frame actual Game identity")
    captured = _at(utc(row.get("at_utc")))
    reviewed = _at(utc(row.get("reviewed_at_utc")))
    need(captured <= reviewed <= _at(now_utc), "Root first-frame review time")


@dataclass(frozen=True, slots=True)
class _VisualArgsV1:
    first_frame_admission: Path


@dataclass(frozen=True, slots=True)
class _VisualQueueV1:
    launch: Mapping[str, object]
    record_job: Path
    args: _VisualArgsV1


def _qualify_current_saved_feeder_for_entry_v1(
    warm: WarmCurrentSavedFeederInputsV1, admission: CurrentSavedFeederAdmissionV1, *,
    reader: BasisReaderV1, actual_stage: Path, actual_loop: Path, actual_owner: Path,
    current_next_sequence: int, now_utc: str, exists: Callable[[Path], bool],
    runtime_root: Path, stage_args: tuple[str, ...],
) -> CurrentSavedFeederV1:
    """Verify the actual warm map and finite source-bound Task without a large reread."""
    inputs = warm.inputs
    checked = parse_current_saved_feeder_admission_v1(
        admission.to_wire(), expected_machine_id=inputs.basis.machine_id)
    need(checked.basis_ref == inputs.basis_ref, "single current saved basis")
    need(_at(now_utc) < _at(checked.review_deadline_utc), "feeder original review deadline")
    budget = _checked(reader, checked.budget_ref)
    need(budget.get("machine_id") == checked.machine_id
         and _at(checked.review_deadline_utc) <= _at(utc(budget.get("review_at_utc"))),
         "actual budget machine/deadline")
    for reference, path in (
        (checked.feeder_source_ref, actual_stage),
        (checked.loop_source_ref, actual_loop),
        (checked.owner_source_ref, actual_owner),
    ):
        need(_same_path(reference.path, path), "actual feeder source path")
        exact_read(reader, reference, 131072)
    spec = _checked(reader, checked.feeder_task_spec_ref, 16384)
    need(spec.get("schema") == "xar.interactive-task-owner/v1"
         and spec.get("role") == "feeder" and spec.get("machine_id") == checked.machine_id
         and spec.get("nonce") == checked.feeder_task_nonce
         and spec.get("task_name") == "XARG2ManagedOwner-" + checked.feeder_task_nonce,
         "actual feeder Task SPEC/nonce")
    need(_same_path(text(spec.get("stage")), actual_stage)
         and spec.get("stage_sha256") == checked.feeder_source_ref.sha256
         and spec.get("stage_args") == list(stage_args)
         and _same_path(text(spec.get("stop_path")), checked.stop_path),
         "actual Task stage/arguments/stop")
    spec_env = record(spec.get("env"))
    need("XAR_CK3_ENABLE_DRIVER_STATE_WAL_V1" not in spec_env, "feeder cannot impersonate SDK WAL owner")
    runtime_dir = runtime_root.resolve()
    need(_same_path(checked.continue_marker, runtime_dir / "CURRENT-SAVED-FIRST-FULL-CONTINUE.json")
         and _same_path(checked.stop_path, runtime_dir / "STOP-CURRENT-SAVED-FEEDER"),
         "canonical current saved control markers")
    need(not exists(Path(checked.continue_marker)) and not exists(Path(checked.stop_path)),
         "fresh feeder control markers")
    sequence = integer(current_next_sequence, 1)
    need(sequence == checked.first_control_sequence, "actual first FULL NEXT")
    for directory in ("p37-requests", "p37-responses"):
        need(not exists(runtime_dir / directory / f"{sequence:04d}-1-result.json"),
             "actual first FULL slot must be empty")
    game = _checked(reader, checked.actual_game_ref, 16384)
    _first_frame(_checked(reader, checked.first_frame_ref, 32768), game,
                 machine_id=checked.machine_id, now_utc=now_utc)
    visual_row = _checked(reader, checked.first_frame_ref, 32768)
    queue = _VisualQueueV1(game, Path(text(visual_row.get("recording_job_root"))),
                           _VisualArgsV1(Path(checked.first_frame_ref.path)))
    def visual_read(path: Path, limit: int = 1048576) -> object:
        with path.open("rb") as stream:
            raw = stream.read(limit + 1)
        need(len(raw) <= limit, "bounded visual input")
        return parse_json(raw)
    env: SavedCampaignVisualEnvV1 = {
        "N": runtime_dir, "R": runtime_dir, "read": visual_read,
        "aware": _at, "now": lambda: _at(now_utc),
    }
    require_saved_campaign_visual(queue, env)
    return validate_current_saved_feeder_v1(
        warm, checked.to_wire(), reader=reader, current_next_sequence=sequence)


def qualify_current_saved_feeder_v1(
    warm: WarmCurrentSavedFeederInputsV1, admission: CurrentSavedFeederAdmissionV1, *,
    reader: BasisReaderV1, actual_stage: Path, actual_loop: Path, actual_owner: Path,
    current_next_sequence: int, now_utc: str, exists: Callable[[Path], bool],
) -> CurrentSavedFeederV1:
    return _qualify_current_saved_feeder_for_entry_v1(
        warm, admission, reader=reader, actual_stage=actual_stage, actual_loop=actual_loop,
        actual_owner=actual_owner, current_next_sequence=current_next_sequence,
        now_utc=now_utc, exists=exists, runtime_root=actual_stage.resolve().parent,
        stage_args=("--first-control-sequence", str(admission.first_control_sequence)))


@dataclass(frozen=True, slots=True)
class InstalledCurrentSavedCallbacksV1:
    """Only these typed calls replace the two historical cold boundaries."""
    admitted: Callable[[], JsonObject]
    attach: Callable[[object, int, object], JsonObject]
    require_can_publish: Callable[[], None]


@dataclass(frozen=True, slots=True)
class CurrentSavedRuntimeV1:
    inputs: CurrentSavedColdInputsV1
    admission: CurrentSavedFeederAdmissionV1
    verified: CurrentSavedFeederV1
    attach_transition: Callable[[str, JsonObject], JsonObject]
    now_utc: Callable[[], str]
    exists: Callable[[Path], bool]

    def admitted(self) -> JsonObject:
        self.require_can_publish()
        return self.admission.to_wire()

    def attach(self, value: object, first_control: int, resume_admission: object) -> JsonObject:
        need(record(value) == record(self.admitted())
             and integer(first_control, 1) == self.admission.first_control_sequence
             and resume_admission is None, "actual current saved cold attachment only")
        return self.attach_transition(CURRENT_SAVED_COLD_KIND, self.verified.expected_transition())

    def require_can_publish(self) -> None:
        need(_at(self.now_utc()) < _at(self.admission.review_deadline_utc),
             "finite feeder review deadline")
        need(not self.exists(Path(self.admission.stop_path)), "Root stopped current saved feeder")

    def callbacks(self) -> InstalledCurrentSavedCallbacksV1:
        return InstalledCurrentSavedCallbacksV1(self.admitted, self.attach, self.require_can_publish)


def make_current_saved_transition_v1(
    original: TransitionV1, *, verified: CurrentSavedFeederV1,
) -> TransitionV1:
    def transition(previous: object, kind: str, details: JsonObject) -> JsonObject:
        if kind == CURRENT_SAVED_COLD_KIND:
            return transition_current_saved_cold_v1(previous, details, verified=verified)
        return original(previous, kind, details)
    return transition


def _replace_nodes(source: str, replacements: dict[str, str]) -> str:
    tree = ast.parse(source)
    found = {name: 0 for name in replacements}
    offsets = [0]
    for line in source.splitlines(keepends=True):
        offsets.append(offsets[-1] + len(line))
    edits: list[tuple[int, int, str]] = []
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name in replacements:
            found[node.name] += 1
            need(node.end_lineno is not None, "function source extent")
            if node.end_lineno is None:
                raise ValueError("function extent")
            edits.append((offsets[node.lineno - 1], offsets[node.end_lineno], replacements[node.name]))
    need(all(count == 1 for count in found.values()), "one exact ordinary loop seam per boundary")
    for start, end, value in sorted(edits, reverse=True):
        source = source[:start] + value.rstrip() + "\n" + source[end:]
    return source


def transform_current_saved_feeder_v1(
    source: bytes, basis: CurrentSavedBasisV1, *, source_sha256: str,
) -> bytes:
    """Replace cold seams only; all ordinary planner/recovery/main ASTs are retained."""
    need(type(source) is bytes and len(source) <= 131072
         and hashlib.sha256(source).hexdigest() == source_sha256, "exact ordinary loop source")
    basis.__post_init__()
    original = source.decode("utf-8")
    tree = ast.parse(original)
    required = ("main", "status", "result_for", "publish_or_follow", "continuity_settled",
                "recover_known_pause_for_failed_loop", "collect_incidents")
    previous = {node.name: ast.dump(node, include_attributes=False)
                for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in required}
    need(set(previous) == set(required), "actual ordinary loop functions")
    transformed = _replace_nodes(original, {
        "admitted": (
            "def admitted() -> dict[str, object]:\n"
            "    return dict(_current_saved_callbacks_v1().admitted())\n"
        ),
        "continuity_attach": (
            "def continuity_attach(v: object, first_control: int = 3, resume_admission: object = None)"
            " -> dict[str, object]:\n"
            "    return dict(_current_saved_callbacks_v1().attach(v, first_control, resume_admission))\n"
        ),
    })
    # Migrate the two ordinary review consumer lookups to the one new
    # admission contract. The first-batch receipt keeps its existing schema.
    parsed = ast.parse(transformed)
    gate = next((node for node in parsed.body
                 if isinstance(node, ast.FunctionDef) and node.name == "c23_gate_expected"), None)
    need(gate is not None, "ordinary first-batch review gate")
    if gate is None:
        raise ValueError("ordinary review gate")
    aliases = {"feeder_task_spec": "feeder_task_spec_ref", "feeder_source": "feeder_source_ref"}
    changes: dict[str, int] = {name: 0 for name in aliases}
    for node in ast.walk(gate):
        if (isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name)
                and node.value.id == "v" and isinstance(node.slice, ast.Constant)
                and type(node.slice.value) is str and node.slice.value in aliases):
            old = node.slice.value
            node.slice.value = aliases[old]
            changes[old] += 1
    need(all(count == 1 for count in changes.values()), "two exact review consumer fields")
    transformed = _replace_nodes(transformed, {"c23_gate_expected": ast.unparse(gate)})
    # Bind the original metadata slots to this basis. These are field/origin
    # migrations, not changes to planner choices, timing or settled credit.
    slots = {"machine": 0, "origin": 0}
    bound: dict[str, str] = {}
    for function in ast.parse(transformed).body:
        if not isinstance(function, ast.FunctionDef) or function.name not in ("main", "status"):
            continue
        for node in ast.walk(function):
            if isinstance(node, ast.Dict):
                for index, key in enumerate(node.keys):
                    if isinstance(key, ast.Constant) and key.value == "machine_id":
                        old_slot = node.values[index]
                        need(isinstance(old_slot, ast.Constant) and type(old_slot.value) is str,
                             "one original literal machine metadata slot")
                        node.values[index] = ast.Name(id="_CURRENT_SAVED_MACHINE_ID_V1", ctx=ast.Load())
                        slots["machine"] += 1
            if (isinstance(node, ast.BinOp) and isinstance(node.op, ast.Sub)
                    and isinstance(node.left, ast.Name) and node.left.id == "END_RAW"
                    and isinstance(node.right, ast.Constant) and type(node.right.value) is int):
                node.right = ast.Name(id="_CURRENT_SAVED_ORIGIN_RAW_V1", ctx=ast.Load())
                slots["origin"] += 1
        bound[function.name] = ast.unparse(function)
    need(slots == {"machine": 2, "origin": 1}, "exact ordinary metadata/origin slots")
    transformed = _replace_nodes(transformed, bound)
    # Keep the original exact timed publisher body. One precondition is inserted
    # before it so the finite Root deadline also bounds subsequent batches.
    target = next(node for node in ast.parse(transformed).body
                  if isinstance(node, ast.FunctionDef) and node.name == "publish_or_follow")
    lines = transformed.splitlines(keepends=True)
    lines.insert(target.lineno, "    _current_saved_callbacks_v1().require_can_publish()\n")
    transformed = "".join(lines)
    setup = (
        "\nfrom tools.g2_saved_campaign.current_saved_campaign_feeder_v1 import InstalledCurrentSavedCallbacksV1\n"
        "_CURRENT_SAVED_CALLBACKS_V1: InstalledCurrentSavedCallbacksV1 | None = None\n"
        f"_CURRENT_SAVED_MACHINE_ID_V1: str = {basis.machine_id!r}\n"
        f"_CURRENT_SAVED_ORIGIN_RAW_V1: int = {basis.origin.start_date_raw}\n"
        "def configure_current_saved_feeder_v1(value: InstalledCurrentSavedCallbacksV1) -> None:\n"
        "    global _CURRENT_SAVED_CALLBACKS_V1, BASELINE_CYCLES, BASELINE_DATE_RAW, STATUS, STOP\n"
        "    if _CURRENT_SAVED_CALLBACKS_V1 is not None:\n"
        "        raise ValueError('current saved callbacks already configured')\n"
        "    _CURRENT_SAVED_CALLBACKS_V1 = value\n"
        f"    BASELINE_CYCLES = {basis.completed_cycles}\n"
        f"    BASELINE_DATE_RAW = {basis.origin.start_date_raw}\n"
        "    STATUS = N / 'CURRENT-SAVED-FEEDER-STATUS.json'\n"
        "    STOP = N / 'STOP-CURRENT-SAVED-FEEDER'\n"
        "def _current_saved_callbacks_v1() -> InstalledCurrentSavedCallbacksV1:\n"
        "    value = _CURRENT_SAVED_CALLBACKS_V1\n"
        "    if value is None:\n"
        "        raise ValueError('current saved Root admission is not configured')\n"
        "    return value\n\n"
    )
    module_tree = ast.parse(transformed)
    first_guard = next((n for n in module_tree.body
                        if isinstance(n, ast.If) and "__main__" in ast.unparse(n.test)), None)
    need(first_guard is not None, "ordinary CLI guard")
    if first_guard is None:
        raise ValueError("ordinary CLI guard")
    ls = transformed.splitlines(keepends=True)
    ls.insert(first_guard.lineno - 1, setup)
    transformed = "".join(ls)
    after = ast.parse(transformed)
    current = {node.name: node for node in after.body if isinstance(node, ast.FunctionDef)}
    for name in required:
        actual = current[name]
        if name == "publish_or_follow":
            actual.body.pop(0)
        if name in ("main", "status"):
            # Compare to the real predecessor AST after undoing only the
            # three explicitly counted metadata slots above.
            original_function = next(node for node in tree.body
                                     if isinstance(node, ast.FunctionDef) and node.name == name)
            old_machines = [node.values[index] for node in ast.walk(original_function)
                            if isinstance(node, ast.Dict) for index, key in enumerate(node.keys)
                            if isinstance(key, ast.Constant) and key.value == "machine_id"]
            old_origin = [node.right for node in ast.walk(original_function)
                          if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Sub)
                          and isinstance(node.left, ast.Name) and node.left.id == "END_RAW"]
            class UndoMetadata(ast.NodeTransformer):
                def visit_Name(self, node: ast.Name) -> ast.AST:
                    if node.id == "_CURRENT_SAVED_MACHINE_ID_V1":
                        return old_machines.pop(0)
                    if node.id == "_CURRENT_SAVED_ORIGIN_RAW_V1":
                        return old_origin.pop(0)
                    return node
            UndoMetadata().visit(actual)
        need(ast.dump(actual, include_attributes=False) == previous[name],
             "ordinary function changed beyond finite publisher guard: " + name)
    for name in ("admitted", "continuity_attach"):
        body = ast.unparse(current[name])
        need("SAVE10480" not in body and "old_basis" not in body
             and "root_checkpoint_bootstrap" not in body, "historical cold boundary survived")
    encoded = transformed.encode("utf-8")
    compile(encoded, "<current-saved-ordinary-feeder>", "exec", dont_inherit=True)
    return encoded


class LocalCurrentSavedFeederReaderV1:
    """Bounded metadata/source reader; no Driver or SAVE body is read here."""
    def read(self, reference: ExactRefV1, limit: int) -> bytes:
        need(0 <= reference.bytes <= limit <= 262144, "feeder metadata read limit")
        with Path(reference.path).open("rb") as stream:
            raw = stream.read(limit + 1)
        need(len(raw) <= limit, "bounded feeder metadata")
        return raw

    def stat(self, path: str) -> FileStatIdentityV1:
        return normalize_file_stat_identity_v1(Path(path).stat())


def utc_now_v1() -> str:
    return datetime.now(timezone.utc).isoformat()



WARM_FORWARD_SCHEMA = "xar.current-saved-pre-full-warm-forward/v1"
WARM_FORWARD_KIND = "current_saved_pre_full_cold_attachment_forward_v1"


@dataclass(frozen=True, slots=True)
class CurrentSavedWarmForwardAdmissionV1:
    machine_id: str
    observed_at_utc: str
    runtime_root: str
    admission_path: str
    original_admission_ref: ExactRefV1
    continuity_binding_ref: ExactRefV1
    continuity_source_ref: ExactRefV1
    previous_task_closed_ref: ExactRefV1
    failure_ref: ExactRefV1
    next_ref: ExactRefV1
    sdk_pair_ref: ExactRefV1
    feeder_admission: CurrentSavedFeederAdmissionV1

    def to_wire(self) -> JsonObject:
        return {
            "schema": WARM_FORWARD_SCHEMA, "machine_id": self.machine_id,
            "observed_at_utc": utc(self.observed_at_utc), "runtime_root": self.runtime_root,
            "admission_path": self.admission_path,
            "original_admission_ref": self.original_admission_ref.to_wire(),
            "continuity_binding_ref": self.continuity_binding_ref.to_wire(),
            "continuity_source_ref": self.continuity_source_ref.to_wire(),
            "previous_task_closed_ref": self.previous_task_closed_ref.to_wire(),
            "failure_ref": self.failure_ref.to_wire(), "next_ref": self.next_ref.to_wire(),
            "sdk_pair_ref": self.sdk_pair_ref.to_wire(),
            "feeder_admission": self.feeder_admission.to_wire(),
            "scope": "same_live_epoch_before_first_FULL_only",
            "ordinary_cycle_credit": 0, "game_day_credit": 0,
            "original_actions_replayed": False, "window_origin_reset": False}


def parse_current_saved_warm_forward_admission_v1(
    value: object, *, expected_machine_id: str,
) -> CurrentSavedWarmForwardAdmissionV1:
    row = record(value, {"schema", "machine_id", "observed_at_utc", "runtime_root",
        "admission_path", "original_admission_ref", "continuity_binding_ref",
        "continuity_source_ref", "previous_task_closed_ref", "failure_ref", "next_ref",
        "sdk_pair_ref", "feeder_admission", "scope", "ordinary_cycle_credit",
        "game_day_credit", "original_actions_replayed", "window_origin_reset"})
    need(row["schema"] == WARM_FORWARD_SCHEMA and row["machine_id"] == expected_machine_id
         and row["scope"] == "same_live_epoch_before_first_FULL_only"
         and integer(row["ordinary_cycle_credit"], 0, 0) == 0
         and integer(row["game_day_credit"], 0, 0) == 0
         and row["original_actions_replayed"] is False and row["window_origin_reset"] is False,
         "formal pre-FULL warm-forward contract")
    return CurrentSavedWarmForwardAdmissionV1(
        text(row["machine_id"]), utc(row["observed_at_utc"]), text(row["runtime_root"]),
        text(row["admission_path"]), parse_ref(row["original_admission_ref"]),
        parse_ref(row["continuity_binding_ref"]), parse_ref(row["continuity_source_ref"]),
        parse_ref(row["previous_task_closed_ref"]), parse_ref(row["failure_ref"]),
        parse_ref(row["next_ref"]), parse_ref(row["sdk_pair_ref"]),
        parse_current_saved_feeder_admission_v1(row["feeder_admission"],
                                               expected_machine_id=expected_machine_id))


def build_current_saved_warm_forward_admission_v1(
    *, original_admission_ref: ExactRefV1, continuity_binding_ref: ExactRefV1,
    continuity_source_ref: ExactRefV1, previous_task_closed_ref: ExactRefV1,
    failure_ref: ExactRefV1, next_ref: ExactRefV1, sdk_pair_ref: ExactRefV1,
    controller_source_ref: ExactRefV1, controller_spec_ref: ExactRefV1,
    budget_ref: ExactRefV1, runtime_root: Path, admission_path: Path,
    observed_at_utc: str, review_deadline_utc: str, expected_machine_id: str,
    reader: BasisReaderV1,
) -> CurrentSavedWarmForwardAdmissionV1:
    """Prepare a new authority; never mutate or relabel the old Task/admission."""
    from dataclasses import replace
    original = parse_current_saved_feeder_admission_v1(
        _checked(reader, original_admission_ref, 32768),
        expected_machine_id=expected_machine_id)
    spec = _checked(reader, controller_spec_ref, 16384)
    nonce = text(spec.get("nonce"))
    need(nonce != original.feeder_task_nonce, "new controller needs a new Task generation")
    next_row = _checked(reader, next_ref, 16384)
    first = integer(next_row.get("next_sequence"), 1)
    need(first == original.first_control_sequence, "pre-FULL forward cannot consume a new sequence")
    forwarded = replace(original, feeder_source_ref=controller_source_ref,
        feeder_task_spec_ref=controller_spec_ref, feeder_task_nonce=nonce,
        budget_ref=budget_ref, review_deadline_utc=utc(review_deadline_utc))
    result = CurrentSavedWarmForwardAdmissionV1(
        text(expected_machine_id), utc(observed_at_utc), str(runtime_root.resolve()),
        str(admission_path.resolve()), original_admission_ref, continuity_binding_ref,
        continuity_source_ref, previous_task_closed_ref, failure_ref, next_ref,
        sdk_pair_ref, forwarded)
    _validate_forward_authority_v1(result, reader=reader)
    return parse_current_saved_warm_forward_admission_v1(
        parse_json(canonical_forward_bytes_v1(result)), expected_machine_id=expected_machine_id)


def canonical_forward_bytes_v1(value: CurrentSavedWarmForwardAdmissionV1) -> bytes:
    from tools.g2_saved_campaign.current_saved_basis_v1 import canonical_json_v1
    return canonical_json_v1(value.to_wire())


def _validate_forward_authority_v1(
    value: CurrentSavedWarmForwardAdmissionV1, *, reader: BasisReaderV1,
) -> CurrentSavedFeederAdmissionV1:
    original = parse_current_saved_feeder_admission_v1(
        _checked(reader, value.original_admission_ref, 32768),
        expected_machine_id=value.machine_id)
    changed = value.feeder_admission
    old_wire, new_wire = original.to_wire(), changed.to_wire()
    replaceable = {"feeder_source_ref", "feeder_task_spec_ref", "feeder_task_nonce",
                   "budget_ref", "review_deadline_utc"}
    need(all(new_wire[key] == old for key, old in old_wire.items() if key not in replaceable),
         "forward cannot change original Game/SDK/basis/visual/sequence bindings")
    need(changed.feeder_task_nonce != original.feeder_task_nonce
         and changed.feeder_source_ref.path != original.feeder_source_ref.path,
         "new Task/controller must not impersonate the old frozen stage")
    need(_at(changed.review_deadline_utc) <= _at(original.review_deadline_utc),
         "warm-forward cannot extend the original runtime review deadline")
    old_spec = _checked(reader, original.feeder_task_spec_ref, 16384)
    closed = _checked(reader, value.previous_task_closed_ref, 16384)
    need(old_spec.get("nonce") == original.feeder_task_nonce
         and closed.get("machine_id") == value.machine_id
         and closed.get("nonce") == original.feeder_task_nonce
         and closed.get("spec_sha256") == original.feeder_task_spec_ref.sha256
         and integer(closed.get("job_active_after_stage"), 0, 0) == 0
         and type(closed.get("child_exit_code")) is int
         and type(closed.get("bootstrap_exit_code")) is int,
         "previous feeder Task must actually be closed")
    failure = _checked(reader, value.failure_ref, 16384)
    need(failure.get("machine_id") == value.machine_id
         and failure.get("status") == "feeder_error_review_required"
         and failure.get("error_type") == "ValueError"
         and failure.get("error") == "exact frozen predecessor",
         "known local pre-FULL predecessor failure; no business success inferred")
    need(_same_path(value.next_ref.path, Path(value.runtime_root) / "NEXT-SEQUENCE-P37.json")
         and integer(_checked(reader, value.next_ref, 16384).get("next_sequence"), 1)
             == changed.first_control_sequence, "unchanged actual NEXT")
    return original


def qualify_current_saved_warm_forward_v1(
    value: CurrentSavedWarmForwardAdmissionV1, *, warm: WarmCurrentSavedFeederInputsV1,
    reader: BasisReaderV1, actual_stage: Path, actual_loop: Path, actual_owner: Path,
    now_utc: str, exists: Callable[[Path], bool],
) -> tuple[CurrentSavedFeederV1, JsonObject]:
    """Reuse live warm/visual checks, with explicit new controller authority."""
    _validate_forward_authority_v1(value, reader=reader)
    need(value.machine_id == warm.inputs.basis.machine_id
         and warm.warm_proof.sources.sdk_pair_ref == value.sdk_pair_ref,
         "exact retained live SDK pair")
    need(_at(value.observed_at_utc) <= _at(now_utc)
         and (_at(now_utc) - _at(value.observed_at_utc)).total_seconds() <= 600,
         "fresh Root forward authority")
    runtime = Path(value.runtime_root)
    need(warm.inputs.basis.next_sequence + 2 == value.feeder_admission.first_control_sequence,
         "only the untouched first FULL after original SEM/CAP")
    for name in ("ROOT-CURRENT-HALT-P37.json", "ROOT-FIRST-QUEUE-EXCEPTION-P37C23.json",
                 "REQUEST-ADMISSION-CLOSED-C23", "EXIT-SDK-P37C23",
                 "STOP-CURRENT-SAVED-FEEDER", "ROOT-CONTINUOUS-FEEDER-STOP-P37C23",
                 "p37-queue/ROOT-QUEUE-HALTED.json"):
        need(not exists(runtime / name), "current runtime remains halted/stopped: " + name)
    verified = _qualify_current_saved_feeder_for_entry_v1(
        warm, value.feeder_admission, reader=reader, actual_stage=actual_stage,
        actual_loop=actual_loop, actual_owner=actual_owner,
        current_next_sequence=value.feeder_admission.first_control_sequence,
        now_utc=now_utc, exists=exists, runtime_root=runtime,
        stage_args=("--warm-forward-admission", value.admission_path))
    from tools.g2_saved_campaign.current_saved_continuity_v1 import (
        LocalContinuityReaderV1, validate_continuity_binding_v1, continuity_digest_v1,
    )
    binding = _checked(reader, value.continuity_binding_ref, 32768)
    view = validate_continuity_binding_v1(binding, expected_machine_id=value.machine_id,
                                        reader=LocalContinuityReaderV1())
    basis = warm.inputs.basis
    need(view.ready and _same_path(view.canonical_path, runtime.parent / "ROOT-CONTINUITY-WINDOW.json")
         and view.anchor_ref == basis.refs.ledger
         and integer(view.head_state.get("last_settled_cycles")) == basis.completed_cycles
         and integer(view.head_state.get("last_settled_date_raw")) == basis.frame.date_raw
         and view.head_state.get("game_binding") != verified.game.to_ledger(),
         "actual current ledger awaits this cold attachment only")
    progress = basis.progress.to_wire()
    progress.update(ledger_cycles=basis.completed_cycles, ledger_date_raw=basis.frame.date_raw)
    details = verified.expected_transition()
    source = json_object(details["source"])
    source.update(original_old_ledger_ref=basis.refs.ledger.to_wire(),
        original_progress=basis.progress.to_wire(), progress=progress,
        continuity_binding_ref=value.continuity_binding_ref.to_wire(),
        controller_spec_ref=value.feeder_admission.feeder_task_spec_ref.to_wire(),
        original_admission_ref=value.original_admission_ref.to_wire())
    details.update(evidence_id=WARM_FORWARD_KIND + ":" + continuity_digest_v1(value.to_wire()),
        source=source, old_ledger_ref=view.snapshot_ref.to_wire())
    return verified, {"view": view.to_wire(), "details": details, "progress": progress}


def _load_continuity_extension_v1(reference: ExactRefV1, *, reader: BasisReaderV1) -> None:
    import importlib.util
    import sys
    name = "tools.g2_saved_campaign.current_saved_continuity_v1"
    verified_raw = exact_read(reader, reference, 131072)
    prior = sys.modules.get(name)
    if prior is not None:
        filename: object = getattr(prior, "__file__", None)
        need(type(filename) is str, "continuity extension origin")
        if not isinstance(filename, str):
            raise ValueError("continuity extension origin")
        need(_same_path(filename, reference.path), "a different continuity extension is already imported")
        return
    spec = importlib.util.spec_from_file_location(name, reference.path)
    need(spec is not None and spec.loader is not None, "actual continuity extension loader")
    if spec is None or spec.loader is None:
        raise ValueError("continuity extension loader")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        exec(compile(verified_raw, reference.path, "exec"), vars(module))
    except BaseException:
        if sys.modules.get(name) is module:
            del sys.modules[name]
        raise



@runtime_checkable
class ForwardWindowWriterV1(Protocol):
    def apply(self, kind: str, details: JsonObject) -> object: ...


@runtime_checkable
class ForwardLedgerV1(Protocol):
    __file__: str
    transition: TransitionV1
    def WindowLedger(self, path: Path) -> ForwardWindowWriterV1: ...


@runtime_checkable
class ForwardOrdinaryV1(Protocol):
    __file__: str
    CONTINUITY_WINDOW: Path
    def configure_current_saved_feeder_v1(self, value: InstalledCurrentSavedCallbacksV1) -> None: ...
    def main(self, first_control: int, continuity_resume_admission: object = None) -> None: ...
    def continuity_interrupted(self, reason: str, source: Path) -> object: ...
    def status(self, value: str, **details: object) -> None: ...


@runtime_checkable
class ForwardWarmLoaderV1(Protocol):
    def __call__(self) -> WarmCurrentSavedFeederInputsV1: ...


@runtime_checkable
class RuntimeInitializerV1(Protocol):
    def __call__(self) -> object: ...


@runtime_checkable
class SharedVerifierV1(Protocol):
    def __call__(self, root: Path) -> None: ...


def run_current_saved_warm_forward_v1(
    value: CurrentSavedWarmForwardAdmissionV1, *, ordinary: ForwardOrdinaryV1,
    ledger: ForwardLedgerV1, warm_loader: ForwardWarmLoaderV1,
    actual_stage: Path, reader: LocalCurrentSavedFeederReaderV1,
    qualify: bool = False,
) -> JsonObject:
    """Official new-controller entry; the old immutable ordinary loop executes."""
    _load_continuity_extension_v1(value.continuity_source_ref, reader=reader)
    from tools.g2_saved_campaign.current_saved_continuity_v1 import (
        LocalContinuityReaderV1, validate_continuity_binding_v1,
        dry_run_attachment_v1, checked_attachment_reducer_v1,
        reduce_saved_continuity_attachment_v1,
    )
    from tools.g2_saved_campaign import root_current_saved_campaign_cold_owner_v1 as owner
    warm = warm_loader()
    verified, prepared = qualify_current_saved_warm_forward_v1(
        value, warm=warm, reader=reader, actual_stage=actual_stage,
        actual_loop=Path(ordinary.__file__), actual_owner=Path(owner.__file__),
        now_utc=utc_now_v1(), exists=Path.exists)
    continuity_reader = LocalContinuityReaderV1()
    view = validate_continuity_binding_v1(prepared["view"],
        expected_machine_id=value.machine_id, reader=continuity_reader)
    details = json_object(prepared["details"])
    progress = json_object(prepared["progress"])
    original_transition = ledger.transition
    def forward_transition(previous: object, kind: str, supplied: JsonObject) -> JsonObject:
        if kind != WARM_FORWARD_KIND:
            return json_object(original_transition(previous, kind, supplied))
        return reduce_saved_continuity_attachment_v1(previous, supplied,
            expected_details=details, expected_predecessor=view.head_state,
            basis_value=warm.inputs.basis.to_wire(), game=verified.game.to_ledger(),
            opening=verified.opening.to_wire(), progress=progress)
    ledger_source = continuity_reader.probe(str(Path(ledger.__file__)), 65536)
    need(ledger_source is not None, "original frozen continuity reducer source")
    if ledger_source is None:
        raise ValueError("missing original reducer")
    attachment = dry_run_attachment_v1(view, kind=WARM_FORWARD_KIND, details=details,
        reducer=forward_transition, reducer_sources=(
            value.feeder_admission.feeder_source_ref, value.continuity_source_ref,
            value.feeder_admission.owner_source_ref, value.feeder_admission.loop_source_ref,
            ledger_source.reference))
    report: JsonObject = {
        "schema": "xar.current-saved-pre-full-warm-forward-qualification/v1",
        "machine_id": value.machine_id, "status": "READONLY_FORWARD_QUALIFIED",
        "observed_at_utc": utc_now_v1(), "admission": value.to_wire(),
        "warm": warm.warm_proof.to_wire(), "attachment": attachment.to_wire(),
        "Game_SDK_Task_calls": 0, "ledger_writes": 0,
        "ordinary_cycle_credit": 0, "game_day_credit": 0}
    if qualify:
        return report
    def apply(kind: str, supplied: JsonObject) -> JsonObject:
        return json_object(ledger.WindowLedger(ordinary.CONTINUITY_WINDOW).apply(kind, supplied))
    runtime = CurrentSavedRuntimeV1(warm.inputs, value.feeder_admission, verified,
                                    apply, utc_now_v1, Path.exists)
    def can_publish() -> None:
        runtime.require_can_publish()
        for source in (value.feeder_admission.feeder_source_ref, value.continuity_source_ref,
                       value.feeder_admission.feeder_task_spec_ref, value.feeder_admission.budget_ref):
            exact_read(reader, source, 262144)
        with Path(value.admission_path).open("rb") as authority_stream:
            current_authority = authority_stream.read(32769)
        need(len(current_authority) <= 32768
             and canonical_forward_bytes_v1(parse_current_saved_warm_forward_admission_v1(
                 parse_json(current_authority), expected_machine_id=value.machine_id))
                 == canonical_forward_bytes_v1(value), "Root forward authority changed")
    def admitted() -> JsonObject:
        can_publish()
        return value.feeder_admission.to_wire()
    def attach(admission_value: object, first: int, resume: object) -> JsonObject:
        need(record(admission_value) == record(admitted())
             and integer(first, 1) == value.feeder_admission.first_control_sequence
             and resume is None, "formal same-epoch first FULL attachment")
        return apply(WARM_FORWARD_KIND, details)
    import msvcrt
    lock_path = Path(value.admission_path).with_suffix(".lock")
    with lock_path.open("a+b") as lock:
        lock.seek(0)
        msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
        try:
            ledger.transition = checked_attachment_reducer_v1(
                forward_transition, attachment=attachment, reader=continuity_reader)
            ordinary.configure_current_saved_feeder_v1(
                InstalledCurrentSavedCallbacksV1(admitted, attach, can_publish))
            ordinary.main(value.feeder_admission.first_control_sequence, None)
        except Exception as error:
            ordinary.continuity_interrupted(str(error),
                Path(value.runtime_root) / "p37-queue/ROOT-CUMULATIVE-LOOP-STATE.json")
            ordinary.status("feeder_error_review_required",
                error_type=type(error).__name__, error=str(error)[:2048])
            raise
        finally:
            lock.seek(0)
            msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)
    return report


def warm_forward_cli_v1() -> None:
    import argparse
    import importlib
    import sys
    parser = argparse.ArgumentParser(description="Managed same-live-epoch pre-FULL continuity attachment")
    parser.add_argument("--warm-forward-admission", type=Path, required=True)
    parser.add_argument("--qualify", action="store_true")
    args = parser.parse_args()
    with args.warm_forward_admission.open("rb") as stream:
        raw = stream.read(32769)
    need(len(raw) <= 32768, "bounded Root forward authority")
    from tools.ck3_live_run_id import current_machine_id
    value = parse_current_saved_warm_forward_admission_v1(
        parse_json(raw), expected_machine_id=current_machine_id())
    need(_same_path(value.admission_path, args.warm_forward_admission),
         "canonical new admission path")
    runtime = Path(value.runtime_root).resolve()
    parent = runtime.parent.parent
    sys.path[:0] = [str(runtime), str(parent / "p27-shared-harness-read01"),
                   str(parent / "p28-commonrunner-preflight01")]
    harness = importlib.import_module("shared_harness_reads")
    install: object = getattr(harness, "install")
    if not isinstance(install, RuntimeInitializerV1):
        raise TypeError("original shared harness installer")
    install()
    outer = importlib.import_module("root_c23_canonical_outer")
    verifier: object = getattr(outer, "verify_current_saved_shared_sources_v1")
    if not isinstance(verifier, SharedVerifierV1):
        raise TypeError("original shared-source verifier")
    verifier(runtime)
    boot = importlib.import_module("root_checkpoint_bootstrap_c23")
    initialize: object = getattr(boot, "api")
    if not isinstance(initialize, RuntimeInitializerV1):
        raise TypeError("original bound SDK initializer")
    initialize()
    ordinary_module: object = importlib.import_module("root_p37c23_same_game_loop_feeder100")
    ledger_module: object = importlib.import_module("root_continuity_window_c23_100")
    cold = importlib.import_module("root_p37c23_cold_resume")
    load: object = getattr(cold, "load_current_saved_feeder_inputs_v1")
    if not isinstance(ordinary_module, ForwardOrdinaryV1) or not isinstance(ledger_module, ForwardLedgerV1):
        raise TypeError("original frozen ordinary/ledger interfaces")
    if not isinstance(load, ForwardWarmLoaderV1):
        raise TypeError("original current-saved warm loader")
    need(_same_path(ordinary_module.__file__, runtime / "root_p37c23_same_game_loop_feeder100.py")
         and _same_path(ledger_module.__file__, runtime / "root_continuity_window_c23_100.py"),
         "original frozen controller dependencies")
    result = run_current_saved_warm_forward_v1(
        value, ordinary=ordinary_module, ledger=ledger_module, warm_loader=load,
        actual_stage=Path(__file__), reader=LocalCurrentSavedFeederReaderV1(),
        qualify=args.qualify)
    if args.qualify:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))


def emit_current_saved_feeder_launcher_v1(
    *, feeder_module_name: str = "root_p37c23_same_game_loop_feeder100",
    cold_module_name: str = "root_p37c23_cold_resume",
) -> bytes:
    """Emit the actual Task stage in RAM; caller freezes it in the runtime graph."""
    for name in (feeder_module_name, cold_module_name):
        need(re.fullmatch("[a-z][a-z0-9_]{1,100}", name) is not None, "one static runtime module")
    result = (
        '"""Current saved checkpoint feeder. No historical attempt cold route."""\n'
        "from __future__ import annotations\n"
        "import argparse\n"
        "import json\n"
        "import msvcrt\n"
        "from pathlib import Path\n"
        "import sys\n"
        "N = Path(__file__).resolve().parent\n"
        "P = N.parent.parent\n"
        "sys.path[:0] = [str(N), str(P / 'p27-shared-harness-read01'), str(P / 'p28-commonrunner-preflight01')]\n"
        "import shared_harness_reads\n"
        "shared_harness_reads.install()\n"
        "import root_p37_readonly_recovery_registry as recovery_registry\n"
        "if recovery_registry.qualify_failed_readonly_auto({}) is not None:\n"
        "    raise ValueError('ordinary readonly recovery closure differs')\n"
        f"import {feeder_module_name} as ordinary\n"
        "import root_continuity_window_c23_100 as ledger\n"
        "import tools.g2_saved_campaign.root_current_saved_campaign_cold_owner_v1 as owner\n"
        f"from {cold_module_name} import load_current_saved_feeder_inputs_v1\n"
        "from tools.g2_saved_campaign.current_saved_campaign_feeder_v1 import (\n"
        "    CurrentSavedRuntimeV1, LocalCurrentSavedFeederReaderV1,\n"
        "    decode_current_saved_feeder_admission_v1, make_current_saved_transition_v1,\n"
        "    qualify_current_saved_feeder_v1, utc_now_v1,\n"
        ")\n"
        "from tools.g2_saved_campaign.current_saved_basis_v1 import JsonObject, integer, json_object, need\n"
        "from tools.g2_saved_campaign.current_saved_continuity_v1 import (\n"
        "    LocalContinuityReaderV1, read_continuity_view_v1, dry_run_attachment_v1,\n"
        "    checked_attachment_reducer_v1,\n"
        ")\n"
        "def main(first_control_sequence: int, *, qualify: bool = False) -> None:\n"
        "    first = integer(first_control_sequence, 1)\n"
        "    warm = load_current_saved_feeder_inputs_v1()\n"
        "    inputs = warm.inputs\n"
        "    path = N / 'CURRENT-SAVED-FEEDER-ADMISSION.json'\n"
        "    with path.open('rb') as stream:\n"
        "        raw = stream.read(32769)\n"
        "    admission = decode_current_saved_feeder_admission_v1(raw, expected_machine_id=inputs.basis.machine_id)\n"
        "    need(first == admission.first_control_sequence, 'CLI actual first FULL differs')\n"
        "    verified = qualify_current_saved_feeder_v1(\n"
        "        warm, admission, reader=LocalCurrentSavedFeederReaderV1(),\n"
        "        actual_stage=Path(__file__), actual_loop=Path(ordinary.__file__),\n"
        "        actual_owner=Path(owner.__file__), current_next_sequence=ordinary.next_sequence(),\n"
        "        now_utc=utc_now_v1(), exists=Path.exists,\n"
        "    )\n"
        "    original_transition = ledger.transition\n"
        "    def normal_transition(previous: object, kind: str, details: JsonObject) -> JsonObject:\n"
        "        return json_object(original_transition(previous, kind, details))\n"
        "    wrapped = make_current_saved_transition_v1(normal_transition, verified=verified)\n"
        "    continuity_reader = LocalContinuityReaderV1()\n"
        "    view = read_continuity_view_v1(canonical_path=ordinary.CONTINUITY_WINDOW,\n"
        "        anchor_ref=inputs.basis.refs.ledger, expected_machine_id=inputs.basis.machine_id,\n"
        "        reader=continuity_reader)\n"
        "    ledger_source = continuity_reader.probe(str(Path(ledger.__file__)), 65536)\n"
        "    need(ledger_source is not None, 'actual continuity reducer source')\n"
        "    if ledger_source is None: raise ValueError('missing continuity source')\n"
        "    attachment = dry_run_attachment_v1(view, kind=owner.CURRENT_SAVED_COLD_KIND,\n"
        "        details=verified.expected_transition(), reducer=wrapped,\n"
        "        reducer_sources=(admission.feeder_source_ref, admission.owner_source_ref,\n"
        "                         admission.loop_source_ref, ledger_source.reference))\n"
        "    if qualify:\n"
        "        print(json.dumps({'machine_id': inputs.basis.machine_id, 'status': 'READONLY_QUALIFIED',\n"
        "                          'attachment': attachment.to_wire(), 'Game_SDK_Task_calls': 0,\n"
        "                          'ordinary_cycle_credit': 0, 'game_day_credit': 0}))\n"
        "        return\n"
        "    def apply(kind: str, details: JsonObject) -> JsonObject:\n"
        "        return json_object(ledger.WindowLedger(ordinary.CONTINUITY_WINDOW).apply(kind, details))\n"
        "    runtime = CurrentSavedRuntimeV1(inputs, admission, verified, apply, utc_now_v1, Path.exists)\n"
        "    ledger.transition = checked_attachment_reducer_v1(wrapped, attachment=attachment, reader=continuity_reader)\n"
        "    ordinary.configure_current_saved_feeder_v1(runtime.callbacks())\n"
        "    with (N / 'CURRENT-SAVED-FEEDER.lock').open('a+b') as lock:\n"
        "        lock.seek(0)\n"
        "        msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)\n"
        "        try:\n"
        "            ordinary.main(first, None)\n"
        "        except Exception as error:\n"
        "            ordinary.continuity_interrupted(str(error), ordinary.Q / 'ROOT-CUMULATIVE-LOOP-STATE.json')\n"
        "            ordinary.status('feeder_error_review_required', error_type=type(error).__name__, error=str(error)[:2048])\n"
        "            raise\n"
        "        finally:\n"
        "            lock.seek(0)\n"
        "            msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)\n"
        "if __name__ == '__main__':\n"
        "    parser = argparse.ArgumentParser(description=__doc__)\n"
        "    parser.add_argument('--first-control-sequence', type=int, required=True)\n"
        "    parser.add_argument('--qualify', action='store_true')\n"
        "    args = parser.parse_args()\n"
        "    main(args.first_control_sequence, qualify=args.qualify)\n"
    ).encode("utf-8")
    compile(result, "<current-saved-feeder-launcher>", "exec", dont_inherit=True)
    return result


if __name__ == "__main__":
    warm_forward_cli_v1()

