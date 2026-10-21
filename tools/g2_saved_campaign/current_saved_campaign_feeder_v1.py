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
from typing import Callable, Mapping, TypeAlias

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


def qualify_current_saved_feeder_v1(
    warm: WarmCurrentSavedFeederInputsV1, admission: CurrentSavedFeederAdmissionV1, *,
    reader: BasisReaderV1, actual_stage: Path, actual_loop: Path, actual_owner: Path,
    current_next_sequence: int, now_utc: str, exists: Callable[[Path], bool],
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
         and spec.get("stage_args") == [
             "--first-control-sequence", str(checked.first_control_sequence),
         ]
         and _same_path(text(spec.get("stop_path")), checked.stop_path),
         "actual Task stage/arguments/stop")
    spec_env = record(spec.get("env"))
    need("XAR_CK3_ENABLE_DRIVER_STATE_WAL_V1" not in spec_env, "feeder cannot impersonate SDK WAL owner")
    runtime_dir = actual_stage.resolve().parent
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
        "    if qualify:\n"
        "        print(json.dumps({'machine_id': inputs.basis.machine_id, 'status': 'READONLY_QUALIFIED',\n"
        "                          'Game_SDK_Task_calls': 0, 'ordinary_cycle_credit': 0, 'game_day_credit': 0}))\n"
        "        return\n"
        "    original_transition = ledger.transition\n"
        "    def normal_transition(previous: object, kind: str, details: JsonObject) -> JsonObject:\n"
        "        return json_object(original_transition(previous, kind, details))\n"
        "    def apply(kind: str, details: JsonObject) -> JsonObject:\n"
        "        return json_object(ledger.WindowLedger(ordinary.CONTINUITY_WINDOW).apply(kind, details))\n"
        "    runtime = CurrentSavedRuntimeV1(inputs, admission, verified, apply, utc_now_v1, Path.exists)\n"
        "    ledger.transition = make_current_saved_transition_v1(normal_transition, verified=verified)\n"
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

