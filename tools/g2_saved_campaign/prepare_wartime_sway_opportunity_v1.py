"""Mechanical, finite M6 overlay for a Source32 successor; no runtime or filesystem writes."""
from __future__ import annotations

import ast
import hashlib
from collections.abc import Mapping

BASELINE: dict[str, tuple[int, str]] = {
    "xar_autoplayer/bridge/ordinary_sway_service_v1.py": (9219, "3f45b4c07dd79a8279605c438a57fa7cdc819a7900a642953f9c3e0fd93d8321"),
    "xar_autoplayer/ordinary_sway_schedule_v1.py": (10142, "f61d179fccbcb1b656ebafa9b68a04ed9045c0b0b3e1a61fe11ca39361ad3cd4"),
    "xar_autoplayer/sway_formal_consumer.py": (35251, "99ea0b435442d9b842ebc40cc19601ea03c92a112cb2a8f257550de8ec2d9ad8"),
}
NEW_LEAF = "xar_autoplayer/bridge/war_stationary_sway_opportunity_v1.py"
HELPER = "\"\"\"A monthly Sway opportunity before an already proved stationary war wait.\"\"\"\nfrom __future__ import annotations\n\nfrom collections.abc import Callable, Mapping\nfrom dataclasses import dataclass\nfrom pathlib import Path\nfrom typing import Final, Literal, Protocol, TypeGuard, TypedDict, runtime_checkable\n\nfrom .war_contract import normalize_route_contact_horizon, parse_advance_route_contact_horizon_step\n\nSCHEMA: Final = \"xar.war-stationary-sway-opportunity/v1\"\nPHASE = \"native_war_stationary_contact_horizon_progress\"\n\n\nclass WindowV1(TypedDict):\n    schema: Literal[\"xar.war-stationary-sway-opportunity/v1\"]\n    original_selected_step: str\n    snapshot_id: str\n    revision: int\n    native_revision: int\n    date_raw: int\n    actor_character_id: int\n    episode_run_id: str\n    bridge_pid: int\n    connection_generation: int\n    contact_horizon: dict[str, object]\n\n\n@dataclass(frozen=True)\nclass _Frame:\n    snapshot_id: str\n    revision: int\n    native_revision: int\n    date_raw: int\n    actor_character_id: int\n    episode_run_id: str\n    bridge_pid: int\n    connection_generation: int\n\n\ndef _mapping(value: object) -> dict[str, object] | None:\n    if not isinstance(value, Mapping) or any(type(key) is not str for key in value):\n        return None\n    return {key: item for key, item in value.items()}\n\n\ndef _integer(value: object) -> TypeGuard[int]:\n    return type(value) is int\n\n\ndef _positive(value: object) -> TypeGuard[int]:\n    return type(value) is int and 0 < value <= 0xFFFFFFFF\n\n\ndef _text(value: object) -> TypeGuard[str]:\n    return type(value) is str and bool(value)\n\n\ndef _binding(value: object, *, window: bool = False) -> _Frame | None:\n    row = _mapping(value)\n    if row is None:\n        return None\n    played = _mapping(row.get(\"played_character\"))\n    diag = _mapping(row.get(\"diagnostics\"))\n    actor = row.get(\"actor_character_id\") if window else played.get(\"character_id\") if played else None\n    pid = row.get(\"bridge_pid\") if window else diag.get(\"bridge_pid\") if diag else None\n    generation = row.get(\"connection_generation\") if window else diag.get(\"connection_generation\") if diag else None\n    sid, revision, native, date, episode = (row.get(key) for key in\n        (\"snapshot_id\", \"revision\", \"native_revision\", \"date_raw\", \"episode_run_id\"))\n    if (not _text(sid) or not _positive(revision) or not _positive(native)\n            or not _integer(date) or not _positive(actor) or not _text(episode)\n            or not _positive(pid) or not _positive(generation)):\n        return None\n    return _Frame(sid, revision, native, date, actor, episode, pid, generation)\n\n\ndef _quiet(snapshot: object, *, subject: int, province: int, hostiles: tuple[int, ...]) -> bool:\n    row = _mapping(snapshot)\n    if row is None:\n        return False\n    played = _mapping(row.get(\"played_character\"))\n    context = _mapping(row.get(\"active_context\"))\n    if \"active_context\" not in row and {\"active_event\", \"pending_character_interaction\"} <= set(row):\n        context = {key: row[key] for key in (\"active_event\", \"pending_character_interaction\")}\n    hint = _mapping(row.get(\"top_exclusive_modal_choice_hint\"))\n    if (row.get(\"paused\") is not True or row.get(\"map_ready\") is not True\n            or row.get(\"episode_identity_pending\") is not False\n            or \"one_life_terminal_reason\" not in row or row[\"one_life_terminal_reason\"] is not None\n            or played is None or played.get(\"alive\") is not True\n            or type(row.get(\"episode_character_id\")) is not int\n            or row[\"episode_character_id\"] != played.get(\"character_id\")\n            or context is None or not {\"active_event\", \"pending_character_interaction\"} <= set(context)\n            or context.get(\"active_event\") is not None or context.get(\"pending_character_interaction\") is not None\n            or hint is None or hint.get(\"status\") != \"absent\" or hint.get(\"owner_verified\") is not True\n            or row.get(\"one_life_terminal\") is not False):\n        return False\n    armies, wars = row.get(\"player_armies\"), row.get(\"active_wars\")\n    if not isinstance(armies, list) or len(armies) != 1 or not isinstance(wars, list) or not wars:\n        return False\n    army = _mapping(armies[0])\n    if (army is None or type(army.get(\"army_id\")) is not int or army[\"army_id\"] != subject\n            or type(army.get(\"owner_character_id\")) is not int\n            or army[\"owner_character_id\"] != played.get(\"character_id\") or army.get(\"controllable\") is not True\n            or army.get(\"army_state\") != \"regular\" or army.get(\"in_combat\") is not False\n            or army.get(\"retreating\") is not False\n            or type(army.get(\"current_province_id\")) is not int or army[\"current_province_id\"] != province\n            or army.get(\"move_target_observable\") is not False or army.get(\"move_target_province_id\") is not None\n            or army.get(\"route_read_status\") != \"complete_empty\" or army.get(\"route_province_ids\") != []\n            or type(army.get(\"route_source_count\")) is not int or army[\"route_source_count\"] != 0):\n        return False\n    ids: set[int] = set()\n    for raw_war in wars:\n        war = _mapping(raw_war)\n        enemies = war.get(\"enemy_armies\") if war else None\n        if war is None or not _positive(war.get(\"war_id\")) or not isinstance(enemies, list):\n            return False\n        for raw_enemy in enemies:\n            enemy = _mapping(raw_enemy)\n            identity = enemy.get(\"army_id\") if enemy else None\n            if not _positive(identity):\n                return False\n            ids.add(identity)\n    return tuple(sorted(ids)) == hostiles\n\n\ndef parse_window_v1(value: object) -> WindowV1 | None:\n    row = _mapping(value)\n    keys = set(WindowV1.__annotations__)\n    if row is None or set(row) != keys or row.get(\"schema\") != SCHEMA:\n        return None\n    frame = _binding(row, window=True)\n    step = row.get(\"original_selected_step\")\n    request = parse_advance_route_contact_horizon_step(step)\n    if frame is None or not _text(step) or request is None:\n        return None\n    subject, province, hostiles = request\n    try:\n        proof = normalize_route_contact_horizon(row.get(\"contact_horizon\"),\n            expected_subject_army_id=subject, expected_target_province_id=province,\n            expected_hostile_army_ids=hostiles, expected_date_raw=frame.date_raw,\n            expected_snapshot_revision=frame.native_revision)\n    except ValueError:\n        return None\n    route = _mapping(proof.get(\"subject_route\"))\n    if (proof.get(\"one_day_contact_free\") is not True or proof.get(\"conflicts\") != []\n            or route is None or route.get(\"current_province_id\") != province\n            or route.get(\"route_province_ids\") != [] or route.get(\"arrival_date_raws\") != []):\n        return None\n    return WindowV1(schema=SCHEMA, original_selected_step=step,\n        snapshot_id=frame.snapshot_id, revision=frame.revision,\n        native_revision=frame.native_revision, date_raw=frame.date_raw,\n        actor_character_id=frame.actor_character_id, episode_run_id=frame.episode_run_id,\n        bridge_pid=frame.bridge_pid, connection_generation=frame.connection_generation,\n        contact_horizon=proof)\n\n\ndef require_current_window_v1(window: object, snapshot: object) -> bool:\n    \"\"\"Consumer admission: reread actual current paused state before a new intent.\"\"\"\n    parsed = parse_window_v1(window)\n    if parsed is None or _binding(parsed, window=True) != _binding(snapshot):\n        return False\n    request = parse_advance_route_contact_horizon_step(parsed[\"original_selected_step\"])\n    if request is None:\n        return False\n    return _quiet(snapshot, subject=request[0], province=request[1], hostiles=request[2])\n\n\ndef build_window_v1(planned: object) -> WindowV1 | None:\n    row = _mapping(planned)\n    plan = _mapping(row.get(\"plan\")) if row else None\n    source = _mapping(row.get(\"_ordinary_sway_input_v1\")) if row else None\n    snapshot = _mapping(source.get(\"snapshot\")) if source else None\n    frame = _binding(snapshot)\n    if plan is None or plan.get(\"phase\") != PHASE or frame is None:\n        return None\n    if (row is None or not _text(row.get(\"snapshot_id\")) or row.get(\"snapshot_id\") != frame.snapshot_id\n            or not _positive(row.get(\"revision\")) or row.get(\"revision\") != frame.revision):\n        return None\n    origin = _mapping(row.get(\"planning_source_frame\"))\n    if (origin is None or origin.get(\"schema\") != \"xar.ck3.planning-source-frame/v1\"\n            or origin.get(\"status\") != \"complete\" or _binding(origin, window=True) != frame):\n        return None\n    audit = _mapping(plan.get(\"route_audit\"))\n    if audit is None or audit.get(\"status\") != \"safe_one_day_stationary_contact_horizon\":\n        return None\n    value = {\"schema\": SCHEMA, \"original_selected_step\": plan.get(\"selected_step\"),\n        \"snapshot_id\": frame.snapshot_id, \"revision\": frame.revision,\n        \"native_revision\": frame.native_revision, \"date_raw\": frame.date_raw,\n        \"actor_character_id\": frame.actor_character_id, \"episode_run_id\": frame.episode_run_id,\n        \"bridge_pid\": frame.bridge_pid, \"connection_generation\": frame.connection_generation,\n        \"contact_horizon\": audit.get(\"contact_horizon\")}\n    parsed = parse_window_v1(value)\n    return parsed if parsed is not None and require_current_window_v1(parsed, snapshot) else None\n\ndef project_safety_inputs_v1(snapshot: Mapping[str, object]) -> dict[str, object]:\n    \"\"\"Copy only existing small safety fields inside the planning-view lock.\"\"\"\n    result: dict[str, object] = {key: snapshot[key] for key in\n        (\"episode_identity_pending\", \"one_life_terminal\") if key in snapshot}\n    for key, fields in ((\"diagnostics\", (\"bridge_pid\", \"connection_generation\")),\n            (\"top_exclusive_modal_choice_hint\", (\"status\", \"owner_verified\"))):\n        value = _mapping(snapshot.get(key))\n        if key in snapshot:\n            result[key] = {field: value[field] for field in fields if field in value} if value is not None else None\n    armies = snapshot.get(\"player_armies\")\n    result[\"player_armies\"] = [\n        {key: (list(field_value) if isinstance(field_value := row.get(key), list) else field_value) for key in\n         (\"army_id\", \"owner_character_id\", \"controllable\", \"army_state\", \"in_combat\", \"retreating\", \"current_province_id\",\n          \"move_target_observable\", \"move_target_province_id\", \"route_read_status\", \"route_source_count\", \"route_province_ids\")}\n        if (row := _mapping(raw)) is not None else None for raw in armies\n    ] if isinstance(armies, list) else None\n    wars = snapshot.get(\"active_wars\")\n    projected: list[object] = []\n    if isinstance(wars, list):\n        for raw in wars:\n            row = _mapping(raw)\n            enemies = row.get(\"enemy_armies\") if row else None\n            projected.append({\"war_id\": row.get(\"war_id\"),\n                \"enemy_armies\": [{\"army_id\": enemy.get(\"army_id\")} if\n                    (enemy := _mapping(item)) is not None else None for item in enemies]\n                    if isinstance(enemies, list) else None} if row else None)\n        result[\"active_wars\"] = projected\n    else:\n        result[\"active_wars\"] = None\n    return result\n\nBeforeSubmitV1 = Callable[[dict[str, object]], dict[str, object] | None] | None\n\n\n@runtime_checkable\nclass DriverV1(Protocol):\n    def query_active_scheme_sway_target_private_v1(self, *, expected_revision: int,\n            target_character_id: int) -> dict[str, object]: ...\n\n\n@runtime_checkable\nclass ServiceV1(Protocol):\n    driver: DriverV1\n\n    def _strategy_state_dir(self) -> Path | None: ...\n    def snapshot(self, *, include_native_command_history: bool = False) -> dict[str, object]: ...\n    def _plan_turn_internal(self) -> dict[str, object]: ...\n    def _execute_planned_turn(self, planned: dict[str, object], *, before_submit: BeforeSubmitV1 = None) -> dict[str, object]: ...\n\n\ndef object_v1(value: object) -> dict[str, object]:\n    row = _mapping(value)\n    if row is None:\n        raise ValueError(\"Sway internal JSON object is malformed\")\n    return row\n\ndef service_v1(value: object) -> ServiceV1:\n    \"\"\"Concentrate the legacy dynamic Service boundary; no unchecked cast.\"\"\"\n    if not isinstance(value, ServiceV1) or not isinstance(value.driver, DriverV1):\n        raise ValueError(\"ordinary Sway requires the existing native Service methods\")\n    return value\n"


def _replace(source: str, before: str, after: str) -> str:
    if source.count(before) != 1:
        raise ValueError("M6 overlay requires one exact source seam: " + before[:100])
    return source.replace(before, after, 1)


def compose_wartime_sway_opportunity_v1(source_leaves: Mapping[str, bytes]) -> dict[str, bytes]:
    """Return exactly three changed leaves and one new leaf; never an entire SDK."""
    if set(source_leaves) != set(BASELINE):
        raise ValueError("M6 input must be the exact three qualified Source31 leaves")
    texts: dict[str, str] = {}
    endings: dict[str, str] = {}
    for name, (size, sha) in BASELINE.items():
        raw = source_leaves[name]
        if type(raw) is not bytes or len(raw) != size or hashlib.sha256(raw).hexdigest() != sha:
            raise ValueError("M6 source preimage drift: " + name)
        endings[name] = "\r\n" if b"\r\n" in raw else "\n"
        texts[name] = raw.decode("utf-8").replace("\r\n", "\n")
    service = "xar_autoplayer/bridge/ordinary_sway_service_v1.py"
    text = texts[service]
    text = _replace(text, 'from .driver import BridgeUnavailableError, UnsupportedStepError\n',
        'from .driver import BridgeUnavailableError, UnsupportedStepError\n'
        'from .war_stationary_sway_opportunity_v1 import (\n'
        '    ServiceV1, BeforeSubmitV1, service_v1, object_v1, build_window_v1, require_current_window_v1, project_safety_inputs_v1,\n)\n')
    text = _replace(text, '    frame["active_context"] = dict(context) if isinstance(context, Mapping) else None\n',
        '    frame["active_context"] = dict(context) if isinstance(context, Mapping) else None\n'
        '    frame.update(project_safety_inputs_v1(snapshot))\n')
    text = _replace(text, '    source = planned.get(INPUT)\n    if (not isinstance(plan, dict) or plan.get("selected_step") != "life-advance"\n',
        '    source = planned.get(INPUT)\n    window = build_window_v1(planned)\n'
        '    if (not isinstance(plan, dict)\n'
        '            or (plan.get("selected_step") != "life-advance" and window is None)\n')
    text = _replace(text, '            root=source.get("root"), ledger=ledger, state=state,\n',
        '            root=source.get("root"), ledger=ledger, state=state,\n'
        '            war_stationary_window=window,\n')
    text = _replace(text, '                 "ordinary_sway_job_v1": job},\n',
        '                 "ordinary_sway_job_v1": job,\n'
        '                 **({"war_stationary_sway_window_v1": window} if window is not None else {})},\n')
    text = _replace(text, '    frame = planned[INPUT]["snapshot"]\n    try:\n',
        '    frame = planned[INPUT]["snapshot"]\n'
        '    window = plan.get("war_stationary_sway_window_v1")\n'
        '    if window is not None and not require_current_window_v1(\n'
        '            window, service.snapshot(include_native_command_history=False)):\n'
        '        return _ordinary_fallback(service, {"status": "war_opportunity_frame_changed",\n'
        '            "submit_attempted": False}, before_submit)\n'
        '    try:\n')
    text = _replace(text, '                    snapshot=frame, readback=read)\n',
        '                    snapshot=frame, readback=read,\n'
        '                    pre_submit_admission=(lambda: require_current_window_v1(\n'
        '                        window, service.snapshot(include_native_command_history=False)))\n'
        '                        if window is not None else None)\n')
    text = _replace(text, 'def project_ordinary_sway_input_v1(snapshot: Mapping[str, object], root_result: object) -> dict:\n',
        'def project_ordinary_sway_input_v1(snapshot: Mapping[str, object], root_result: object) -> dict[str, object]:\n')
    text = _replace(text, 'def _inputs(service):\n',
        'def _inputs(service: ServiceV1) -> tuple[Path, dict[str, object] | None, dict[str, object]] | None:\n')
    text = _replace(text, '    return state_dir, state, read_sway_ledger(state_dir)\n',
        '    return state_dir, object_v1(state) if state is not None else None, read_sway_ledger(state_dir)\n')
    text = _replace(text, 'def stage_ordinary_sway_v1(service, planned: dict) -> dict:\n',
        'def stage_ordinary_sway_v1(service: object, planned: dict[str, object]) -> dict[str, object]:\n')
    text = _replace(text, '    driver = service.driver\n', '    service = service_v1(service)\n    driver = service.driver\n')
    text = _replace(text, '    frame = source["snapshot"]\n', '    frame = object_v1(source["snapshot"])\n')
    text = _replace(text, 'def _ordinary_fallback(service, receipt, before_submit):\n',
        'def _ordinary_fallback(service: ServiceV1, receipt: dict[str, object], before_submit: BeforeSubmitV1) -> dict[str, object]:\n')
    text = _replace(text, 'def _finish(state_dir, job, frame, outcome, result) -> dict:\n',
        'def _finish(state_dir: Path, job: dict[str, object], frame: Mapping[str, object], outcome: str, result: dict[str, object]) -> dict[str, object]:\n'
        '    date, kind = frame.get("date_raw"), job.get("job")\n'
        '    target, action = job.get("target_character_id"), job.get("action_id") or result.get("action_id")\n'
        '    if type(date) is not int or type(kind) is not str or (target is not None and type(target) is not int) or (action is not None and type(action) is not str):\n'
        '        raise ValueError("Sway completed-check fields are malformed")\n'
        '    assert isinstance(date, int) and isinstance(kind, str)\n'
        '    assert target is None or isinstance(target, int)\n'
        '    assert action is None or isinstance(action, str)\n')
    text = _replace(text, '        job["state"], date_raw=frame["date_raw"], job_kind=job["job"], outcome=outcome,\n'
        '        target_character_id=job.get("target_character_id"),\n'
        '        action_id=job.get("action_id") or result.get("action_id"),\n',
        '        object_v1(job["state"]), date_raw=date, job_kind=kind, outcome=outcome,\n'
        '        target_character_id=target, action_id=action,\n')
    text = _replace(text, 'def execute_ordinary_sway_v1(service, planned: dict, *, before_submit=None) -> dict:\n',
        'def execute_ordinary_sway_v1(service: object, planned: dict[str, object], *, before_submit: BeforeSubmitV1 = None) -> dict[str, object]:\n')
    text = _replace(text, '    plan = planned["plan"]\n    job = plan["ordinary_sway_job_v1"]\n    frame = planned[INPUT]["snapshot"]\n',
        '    service = service_v1(service)\n    plan = object_v1(planned["plan"])\n    job = object_v1(plan["ordinary_sway_job_v1"])\n'
        '    frame = object_v1(object_v1(planned[INPUT])["snapshot"])\n')
    text = _replace(text, '    result = {}\n    outcome = "unavailable"\n', '    result: dict[str, object] = {}\n    outcome = "unavailable"\n')
    text = _replace(text, '            else:\n                read = service.driver.query_active_scheme_sway_target_private_v1(\n',
        '            else:\n'
        '                if type(frame.get("revision")) is not int or type(job.get("target_character_id")) is not int:\n'
        '                    raise ValueError("Sway target/revision requires exact integer identities")\n'
        '                revision, target = frame["revision"], job["target_character_id"]\n'
        '                assert isinstance(revision, int) and isinstance(target, int)\n'
        '                read = service.driver.query_active_scheme_sway_target_private_v1(\n')
    text = _replace(text, '                    expected_revision=frame["revision"], target_character_id=job["target_character_id"])\n',
        '                    expected_revision=revision, target_character_id=target)\n')
    text = _replace(text, '                    service.driver, target_character_id=job["target_character_id"],\n',
        '                    service.driver, target_character_id=target,\n')
    text = _replace(text, 'result.get("followup", {}).get("decision")',
        '(object_v1(result["followup"]) if result.get("followup") is not None else {}).get("decision")')
    texts[service] = text
    schedule = "xar_autoplayer/ordinary_sway_schedule_v1.py"
    text = texts[schedule]
    text = _replace(text, 'from .reused_sway_opportunity_v1 import reused_sway_observation_gap_v1\n',
        'from .reused_sway_opportunity_v1 import reused_sway_observation_gap_v1\n'
        'from .bridge.war_stationary_sway_opportunity_v1 import parse_window_v1, require_current_window_v1\n')
    text = _replace(text, '    active_observation_only: bool = False,\n',
        '    active_observation_only: bool = False,\n    war_stationary_window: object = None,\n')
    text = _replace(text, '    if selected_step != "life-advance" and active_observation_only is not True:\n',
        '    window = parse_window_v1(war_stationary_window)\n'
        '    war_opportunity = (window is not None\n'
        '        and window["original_selected_step"] == selected_step\n'
        '        and require_current_window_v1(window, snapshot))\n'
        '    if selected_step != "life-advance" and active_observation_only is not True and not war_opportunity:\n')
    texts[schedule] = text
    consumer = "xar_autoplayer/sway_formal_consumer.py"
    text = texts[consumer]
    text = _replace(text, 'from collections.abc import Mapping\n', 'from collections.abc import Callable, Mapping\n')
    text = _replace(text, '                              readback: Mapping[str, object]) -> dict[str, object]:\n',
        '                              readback: Mapping[str, object],\n'
        '                              pre_submit_admission: Callable[[], bool] | None = None) -> dict[str, object]:\n')
    text = _replace(text, '    action_id = "sway-" + uuid.uuid4().hex\n',
        '    if pre_submit_admission is not None and pre_submit_admission() is not True:\n'
        '        return {"status": "wartime_opportunity_no_longer_admitted", "submit_attempted": False}\n'
        '    action_id = "sway-" + uuid.uuid4().hex\n')
    texts[consumer] = text
    output: dict[str, bytes] = {name: body.replace("\n", endings[name]).encode("utf-8")
        for name, body in texts.items()}
    output[NEW_LEAF] = HELPER.encode("utf-8")
    for name, raw in output.items():
        ast.parse(raw, filename=name)
    return output

