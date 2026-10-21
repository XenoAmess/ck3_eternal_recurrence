"""Pure RAM successor delta for a scope-bound route-window clock trial.

Inputs are the exact Source31 leaves.  This producer writes nothing, imports no
game SDK, and cannot change the active export, Driver state, save, or game.
The emitted qualification uses synthetic transport observations; live speed
4/5 safety and throughput remain separate, machine-bound qualifications.
"""
from __future__ import annotations

import ast
from dataclasses import dataclass
import hashlib
from typing import Literal, TypedDict


SOURCE31_COMMIT = "12e81b52c736baec02a85f32098bae5bdaa66a31"
NATIVE_PATH = "xar_autoplayer/bridge/native_driver.py"
MCP_PATH = "xar_autoplayer/bridge/mcp_server.py"
MODEL_PATH = "xar_autoplayer/bridge/route_window_clock_v1.py"
TEST_PATH = "qualification/test_route_window_clock_candidate_v1.py"
NATIVE_BYTES = 1648212
NATIVE_SHA256 = "aa7ac3a8e696ae2e4b2c61775b943624a23be4fed15196a8f23bb8e70aed57f8"
MCP_BYTES = 264973
MCP_SHA256 = "2c0d338d8e7c26c0cc52d1ac202329a610860fbb7f125851c089190d4422b68e"


class SourcePinV1(TypedDict):
    relative_path: str
    bytes: int
    sha256: str


class DeltaQuoteV1(TypedDict):
    schema: Literal["xar.route-window-clock-cold-delta/v1"]
    source31_commit: str
    inputs: list[SourcePinV1]
    production: list[SourcePinV1]
    qualification: SourcePinV1
    typecheck_bytes: int
    typecheck_sha256: str
    runtime_mutated: Literal[False]
    game_executed: Literal[False]
    live_high_speed_qualified: Literal[False]


@dataclass(frozen=True, slots=True)
class GeneratedSourceV1:
    relative_path: str
    payload: bytes
    role: Literal["production", "qualification"]


@dataclass(frozen=True, slots=True)
class RouteWindowColdDeltaV1:
    sources: tuple[GeneratedSourceV1, ...]
    typecheck_source: bytes


def _pin(path: str, payload: bytes) -> SourcePinV1:
    return {"relative_path": path, "bytes": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest()}


def _baseline(payload: bytes, size: int, sha256: str, path: str) -> bytes:
    if type(payload) is not bytes or len(payload) != size:
        raise ValueError(f"{path}: exact Source31 byte length required")
    if hashlib.sha256(payload).hexdigest() != sha256:
        raise ValueError(f"{path}: exact Source31 content required")
    payload.decode("utf-8")
    return payload


def _once(payload: bytes, before: str, after: str) -> bytes:
    old, new = before.encode("utf-8"), after.encode("utf-8")
    if payload.count(old) != 1:
        raise ValueError("cold delta seam is missing or not unique")
    return payload.replace(old, new, 1)


MODEL_SOURCE = '''"""Frozen configuration for route_contact_window only; no live qualification."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Literal, TypedDict

RouteWindowSpeedV1 = Literal[3, 4, 5]

class RouteWindowClockJsonV1(TypedDict):
    timeline_speed: RouteWindowSpeedV1
    research_high_speed_ab: bool

def _speed(value: object) -> RouteWindowSpeedV1:
    if type(value) is not int:
        raise ValueError("route-window speed must be an exact integer")
    if value == 3:
        return 3
    if value == 4:
        return 4
    if value == 5:
        return 5
    raise ValueError("route-window speed must be 3, 4, or 5")

def _permission(value: object) -> bool:
    if not isinstance(value, bool):
        raise ValueError("route-window A/B permission must be an exact boolean")
    return value

@dataclass(frozen=True, slots=True)
class RouteWindowClockConfigV1:
    timeline_speed: RouteWindowSpeedV1 = 3
    research_high_speed_ab: bool = False

    def __post_init__(self) -> None:
        speed = _speed(self.timeline_speed)
        admitted = _permission(self.research_high_speed_ab)
        if speed > 3 and admitted is not True:
            raise ValueError("route-window speed 4/5 requires explicit research A/B")

DEFAULT_ROUTE_WINDOW_CLOCK_V1 = RouteWindowClockConfigV1()

def validate_route_window_clock_v1(value: object) -> RouteWindowClockConfigV1:
    if not isinstance(value, RouteWindowClockConfigV1) or type(value) is not RouteWindowClockConfigV1:
        raise ValueError("route-window clock must use the shared frozen model")
    return RouteWindowClockConfigV1(_speed(value.timeline_speed),
                                  _permission(value.research_high_speed_ab))

def parse_route_window_clock_v1(value: object) -> RouteWindowClockConfigV1:
    # This is the sole dynamic JSON boundary. Values are individually validated
    # before constructing the internal model; missing/null never mean default.
    if not isinstance(value, dict) or set(value) != {"timeline_speed", "research_high_speed_ab"}:
        raise ValueError("route-window JSON requires exactly its two canonical fields")
    return RouteWindowClockConfigV1(_speed(value["timeline_speed"]),
                                  _permission(value["research_high_speed_ab"]))

def route_window_clock_json_v1(value: RouteWindowClockConfigV1) -> RouteWindowClockJsonV1:
    checked = validate_route_window_clock_v1(value)
    return {"timeline_speed": checked.timeline_speed,
            "research_high_speed_ab": checked.research_high_speed_ab}
'''


_IMPORT = '''from .route_window_clock_v1 import (
    DEFAULT_ROUTE_WINDOW_CLOCK_V1, RouteWindowClockConfigV1,
    route_window_clock_json_v1, validate_route_window_clock_v1,
)
'''
_PARAM = "        route_window_clock_v1: RouteWindowClockConfigV1 = DEFAULT_ROUTE_WINDOW_CLOCK_V1,\n"


def _native_delta(payload: bytes) -> bytes:
    payload = _once(payload, "from .holy_site_decision_action_v1 import HolySiteDecisionActionV1\n",
                    "from .holy_site_decision_action_v1 import HolySiteDecisionActionV1\n" + _IMPORT)
    payload = _once(payload, "        route_contact_timeline_speed: int = (\n",
                    _PARAM + "        route_contact_timeline_speed: int = (\n")
    payload = _once(payload, "        self.route_contact_timeline_speed = _timeline_speed(\n",
                    "        self.route_window_clock_v1 = validate_route_window_clock_v1(route_window_clock_v1)\n"
                    "        self.route_contact_timeline_speed = _timeline_speed(\n")
    payload = _once(payload,
                    'and f"set-speed-{self.route_contact_effective_timeline_speed}" in action_steps\n',
                    'and f"set-speed-{self.route_window_clock_v1.timeline_speed}" in action_steps\n')
    payload = _once(payload, '            speed = self.route_contact_effective_timeline_speed\n            wire_mode = "terminal"\n',
                    '            speed = self.route_window_clock_v1.timeline_speed\n            wire_mode = "terminal"\n')
    payload = _once(payload, '                **_BATTLE_SPEED_READINESS,\n',
                    '                **_BATTLE_SPEED_READINESS,\n'
                    '                "route_window_clock_v1": route_window_clock_json_v1(self.route_window_clock_v1),\n')
    return payload


def _mcp_delta(payload: bytes) -> bytes:
    payload = _once(payload, "from .holy_site_decision_action_v1 import HolySiteDecisionActionV1\n",
                    "from .holy_site_decision_action_v1 import HolySiteDecisionActionV1\n" + _IMPORT)
    payload = _once(payload, "    route_contact_timeline_speed: int = 3,\n",
                    "    route_window_clock_v1: RouteWindowClockConfigV1 = DEFAULT_ROUTE_WINDOW_CLOCK_V1,\n"
                    "    route_contact_timeline_speed: int = 3,\n")
    payload = _once(payload, '    if type(allow_war_daily_watch_v1) is not bool:\n',
                    '    route_window_clock_v1 = validate_route_window_clock_v1(route_window_clock_v1)\n'
                    '    if type(allow_war_daily_watch_v1) is not bool:\n')
    payload = _once(payload, '        route_contact_timeline_speed != 3 or allow_route_contact_high_speed_ab\n',
                    '        route_contact_timeline_speed != 3 or allow_route_contact_high_speed_ab\n'
                    '        or route_window_clock_v1 != DEFAULT_ROUTE_WINDOW_CLOCK_V1\n')
    payload = _once(payload, '            route_contact_timeline_speed=route_contact_timeline_speed,\n',
                    '            route_window_clock_v1=route_window_clock_v1,\n'
                    '            route_contact_timeline_speed=route_contact_timeline_speed,\n')
    return payload


QUALIFICATION_SOURCE = '''"""Synthetic native transport; real Service/planner/Driver and stop validators."""
from __future__ import annotations
from collections.abc import Callable
import copy
from typing import Literal, TypedDict
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.route_contact_window_contract import advance_route_contact_window_step
from xar_autoplayer.bridge.route_window_clock_v1 import RouteWindowClockConfigV1, RouteWindowSpeedV1
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.bridge.war_contract import query_route_contact_horizon_step

class QualificationResultV1(TypedDict):
    cases: int
    native_transport: Literal["synthetic"]
    live_qualified: Literal[False]

class FakeEndpoint:
    pipe_name = r"\\\\.\\pipe\\xar_route_window_synthetic"
    def __init__(self) -> None:
        self.frames: list[dict[str, object]] = []
        self.on_frame: Callable[[dict[str, object]], None] | None = None
        self.send_hook: Callable[[dict[str, object]], None] | None = None
    def start(self, on_frame: Callable[[dict[str, object]], None],
              on_disconnect: Callable[[], None]) -> None:
        self.on_frame = on_frame
    def publish(self, frame: dict[str, object]) -> None:
        if self.on_frame is None:
            raise AssertionError("endpoint has not started")
        self.on_frame(frame)
    def send(self, frame: dict[str, object]) -> None:
        self.frames.append(frame)
        if self.send_hook is not None:
            self.send_hook(frame)
    def close(self) -> None:
        self.on_frame = None
    def transport_error(self) -> str | None:
        return None

def _map(value: object) -> dict[str, object]:
    if not isinstance(value, dict) or any(not isinstance(k, str) for k in value):
        raise AssertionError("expected string-keyed JSON object")
    return {str(k): v for k, v in value.items()}

def _strings(value: object) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise AssertionError("expected string list")
    return [str(item) for item in value]

def _status(*, speed: RouteWindowSpeedV1, early: bool, armed: bool) -> dict[str, object]:
    days = 2 if early else 3
    start, target = 24000, 24072
    date = start if armed else start + days * 24
    return {"state": "armed" if armed else "triggered", "generation": 17,
        "starting_date_raw": start, "target_date_raw": target,
        "last_observed_date_raw": date, "trigger_date_raw": 0 if armed else date,
        "speed": speed, "mode": "terminal_or_sentinel", "army_count": 2, "combat_count": 0,
        "completed_daily_ticks": 0 if armed else days, "intermediate_pause_count": 0,
        "trigger_flags": 0 if armed else (1 << 16 if early else 1),
        "trigger_reasons": [] if armed else (["army_position_changed"] if early else ["date_deadline"]),
        "signed_date_delta_from_target_raw": 0 if armed else date-target,
        "overshoot_days": -1 if armed else 0, "pause_wrapper_called": not armed,
        "pause_observed": not armed, "terminal_observed": False, "abnormal": False}

def _case(speed: RouteWindowSpeedV1, *, early: bool, second_day_contact: bool) -> None:
    endpoint = FakeEndpoint()
    clock = RouteWindowClockConfigV1(speed, speed > 3)
    driver = NativeHeadlessGameplayDriver(endpoint.pipe_name, endpoint=endpoint,
        command_timeout_seconds=0.2, life_advance_timeout_seconds=0.2,
        route_window_clock_v1=clock)
    start, target, subject, hostile = 24000, 2585, 11, 21
    hostile_route = [20, 31, target] if second_day_contact else [31, target]
    hostile_arrivals = [start+48, start+360, start+480] if second_day_contact else [start+360, start+480]
    horizon: dict[str, object] = {"status": "available", "date_raw": start, "snapshot_revision": 40,
        "subject_army_id": subject, "target_province_id": target, "hostile_army_ids": [hostile],
        "subject_route": {"timeline_observable": True, "army_id": subject,
            "current_province_id": 20, "effective_origin_province_id": 31,
            "route_province_ids": [31, target], "arrival_date_raws": [start+120, start+240]},
        "hostile_routes": [{"timeline_observable": True, "army_id": hostile,
            "current_province_id": 99, "effective_origin_province_id": hostile_route[0],
            "route_province_ids": hostile_route, "arrival_date_raws": hostile_arrivals}],
        "horizon_start_date_raw": start, "horizon_end_date_raw": start+24,
        "one_day_contact_free": True, "conflicts": []}
    original = copy.deepcopy(horizon)
    query = query_route_contact_horizon_step(subject, target, (hostile,))
    window = advance_route_contact_window_step(subject, target, (hostile,), horizon_days=3)
    def publish(revision: int, *, date: int = start, actual_speed: int = 1,
                arrival: bool = False) -> None:
        player = {"army_id": subject, "owner_character_id": 707, "soldiers": 900,
            "current_province_id": 31 if arrival else 20, "move_target_province_id": target,
            "controllable": True, "army_state": "moving",
            "route_province_ids": [target] if arrival else [31, target]}
        enemy = {"army_id": hostile, "owner_character_id": 808, "soldiers": 800,
            "current_province_id": 99, "move_target_province_id": target,
            "controllable": False, "army_state": "moving", "route_province_ids": hostile_route}
        war = {"war_id": 61, "player_side": "attacker", "primary_opponent_character_id": 808,
            "player_is_primary_war_leader": True, "enemy_primary_default_raise_province_id": None,
            "player_relative_war_score": 0, "allied_armies": [player], "enemy_armies": [enemy],
            "war_objective_province_ids": [target], "objective_province_states": [], "targeted_title_ids": []}
        endpoint.publish({"type": "state_snapshot", "protocol_version": 1,
            "snapshot_id": f"native:{revision}", "revision": revision,
            "state": {"phase": "map_hud", "date": "1066.9.15", "date_raw": date,
                "speed": actual_speed, "paused": True, "map_ready": True, "history": [],
                "active_event": None, "pending_character_interaction": None,
                "played_character": {"character_id": 707, "alive": True},
                "played_character_gold": None, "played_character_prestige": None,
                "played_character_piety": None, "one_life_settlement": None,
                "active_wars": [war], "player_armies": [player]}})
    def answer(frame: dict[str, object]) -> None:
        if frame.get("type") != "execute_step":
            return
        step = str(frame["step"])
        result: dict[str, object] = {"step": step, "accepted": True, "status": "available"}
        if step == query:
            result.update(query_sequence=1, snapshot_revision=40, route_contact_horizon=copy.deepcopy(horizon))
        elif step.startswith("research-arm-tactical-daily-sentinel-v1-"):
            result["tactical_daily_sentinel"] = _status(speed=speed, early=early, armed=True)
        elif step == "research-query-tactical-daily-sentinel-v1":
            result["tactical_daily_sentinel"] = _status(speed=speed, early=early, armed=False)
        endpoint.publish({"type": "command_result", "protocol_version": 1,
            "request_id": frame["request_id"], "ok": True, "result": result})
        if step == f"set-speed-{speed}":
            publish(41, actual_speed=speed)
        elif step == "resume-map":
            publish(42, date=start+(48 if early else 72), actual_speed=speed, arrival=early)
    try:
        capabilities = ["game.state.snapshot", "game.state.war-objectives", "game.state.army-routes",
            "game.command.query-route-contact-horizon-v1-N", "game.command.resume-map", "game.command.pause-map",
            "game.command.research-arm-tactical-daily-sentinel-v1-N",
            "game.command.research-query-tactical-daily-sentinel-v1"]
        capabilities.extend(f"game.command.set-speed-{n}" for n in (1, 3, 4, 5))
        endpoint.publish({"type": "hello", "protocol_version": 1, "bridge_version": "0.1.0",
            "pid": 4242, "session_generation": 0, "capabilities": capabilities})
        publish(40)
        endpoint.send_hook = answer
        revision = driver.take_snapshot()["revision"]
        assert type(revision) is int
        driver.execute_step(query, expected_revision=revision)
        plan = _map(GameplayBridgeService(driver).plan_turn()["plan"])
        projected = driver.capabilities()
        readiness = _map(projected["battle_speed_readiness"])
        assert readiness["noncombat_sentinel_timeline_speed"] == 3
        assert readiness["route_contact_effective_timeline_speed"] == 3
        assert readiness["noncombat_sentinel_high_speed_ab"] is False
        assert readiness["route_window_clock_v1"] == {"timeline_speed": speed, "research_high_speed_ab": speed > 3}
        if second_day_contact:
            assert plan["selected_step"] != window
            assert window not in _strings(projected["action_steps"])
            assert not any(str(row.get("step", "")).startswith("research-arm-tactical-daily-sentinel-v1-")
                           for row in endpoint.frames)
            return
        assert plan["selected_step"] == window
        assert window in _strings(projected["action_steps"])
        revision = driver.take_snapshot()["revision"]
        assert type(revision) is int
        result = driver.execute_step(window, expected_revision=revision)
        wire = [row["step"] for row in endpoint.frames if row.get("type") == "execute_step"]
        expected_arm = f"research-arm-tactical-daily-sentinel-v1-{start}-to-{start+72}-speed-{speed}-mode-terminal-a-2-11-21"
        assert expected_arm in wire and wire.count("resume-map") == 1 and "pause-map" not in wire
        assert result["timeline_speed"] == speed and result["sentinel_scope"] == "route_contact_window"
        assert result["progress_status"] == "postcondition"
        assert result["ending_date_raw"] == start+(48 if early else 72)
        assert result["completed_daily_ticks"] == (2 if early else 3)
        assert result["overshoot_days"] == 0 and result["intermediate_pause_count"] == 0
        assert horizon == original
    finally:
        driver.close()

def run_route_window_clock_qualification_v1() -> QualificationResultV1:
    count = 0
    for speed in (3, 4, 5):
        for early in (False, True):
            _case(speed, early=early, second_day_contact=False)
            count += 1
        _case(speed, early=False, second_day_contact=True)
        count += 1
    return {"cases": count, "native_transport": "synthetic", "live_qualified": False}
'''


def _class(tree: ast.Module, name: str) -> ast.ClassDef:
    found = [node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == name]
    if len(found) != 1:
        raise ValueError("expected one source class")
    return found[0]


def _function(nodes: list[ast.stmt], name: str) -> ast.FunctionDef:
    found = [node for node in nodes if isinstance(node, ast.FunctionDef) and node.name == name]
    if len(found) != 1:
        raise ValueError("expected one source function")
    return found[0]


def _assignment(nodes: ast.AST, target: str) -> ast.Assign:
    matches = [node for node in ast.walk(nodes) if isinstance(node, ast.Assign)
               and any(ast.unparse(item) == target for item in node.targets)]
    if len(matches) != 1:
        raise ValueError("expected one generated clock assignment")
    return matches[0]


def _typecheck_source(native: bytes, mcp: bytes) -> bytes:
    """Extract the actual changed bindings, not a second hand-written policy.

    Legacy Driver/MCP bodies are not claimed wholly strict. This probe checks
    their new constructor/loader annotations, validated assignments, selected
    clock expression, capability expression and forwarded keyword, alongside
    whole-module strict checks of the new model and qualification.
    """
    nt, mt = ast.parse(native), ast.parse(mcp)
    cls = _class(nt, "NativeHeadlessGameplayDriver")
    init = _function(cls.body, "__init__")
    load = _function(mt.body, "load_driver")
    for fn in (init, load):
        args = [arg for arg in fn.args.kwonlyargs if arg.arg == "route_window_clock_v1"]
        annotation = args[0].annotation if len(args) == 1 else None
        if annotation is None or ast.unparse(annotation) != "RouteWindowClockConfigV1":
            raise ValueError("generated public clock parameter is not strongly typed")
    init_bind = _assignment(init, "self.route_window_clock_v1")
    load_bind = _assignment(load, "route_window_clock_v1")
    advance = _function(cls.body, "_execute_battle_sentinel_advance")
    scopes = [node for node in ast.walk(advance) if isinstance(node, ast.If)
              and ast.unparse(node.test) == "route_window_proof is not None"]
    selected = [node for scope in scopes for node in scope.body
                if isinstance(node, ast.Assign) and any(ast.unparse(t) == "speed" for t in node.targets)]
    if len(selected) != 1:
        raise ValueError("route-window clock selection is ambiguous")
    caps = _function(cls.body, "capabilities")
    tests = [node for node in ast.walk(caps) if isinstance(node, ast.Compare)
             and "self.route_window_clock_v1.timeline_speed" in ast.unparse(node)]
    if len(tests) != 1:
        raise ValueError("route-window capability selection is ambiguous")
    calls = [node for node in ast.walk(load) if isinstance(node, ast.Call)
             and ast.unparse(node.func) == "NativeHeadlessGameplayDriver"
             and any(kw.arg == "route_window_clock_v1" for kw in node.keywords)]
    if len(calls) != 1:
        raise ValueError("MCP native constructor is ambiguous")
    values = [kw.value for kw in calls[0].keywords if kw.arg == "route_window_clock_v1"]
    if len(values) != 1:
        raise ValueError("MCP clock forwarding is missing")
    source = '''from __future__ import annotations
from typing import Protocol
from xar_autoplayer.bridge.route_window_clock_v1 import (
    RouteWindowClockConfigV1, RouteWindowSpeedV1, validate_route_window_clock_v1,
)
class Owner(Protocol):
    route_window_clock_v1: RouteWindowClockConfigV1
def bind(self: Owner, route_window_clock_v1: RouteWindowClockConfigV1) -> None:
    INIT_BIND
def load(route_window_clock_v1: RouteWindowClockConfigV1) -> RouteWindowClockConfigV1:
    LOAD_BIND
    return FORWARD
def select(self: Owner) -> RouteWindowSpeedV1:
    SELECT
    return speed
def capability(self: Owner, action_steps: set[str]) -> bool:
    return CAPABILITY
'''
    source = source.replace("INIT_BIND", ast.unparse(init_bind))
    source = source.replace("LOAD_BIND", ast.unparse(load_bind))
    source = source.replace("FORWARD", ast.unparse(values[0]))
    source = source.replace("SELECT", ast.unparse(selected[0]))
    source = source.replace("CAPABILITY", ast.unparse(tests[0]))
    return source.encode("utf-8")


def compose_route_window_clock_v1(native_driver_source: bytes,
                                 mcp_server_source: bytes) -> RouteWindowColdDeltaV1:
    native = _native_delta(_baseline(native_driver_source, NATIVE_BYTES, NATIVE_SHA256, NATIVE_PATH))
    mcp = _mcp_delta(_baseline(mcp_server_source, MCP_BYTES, MCP_SHA256, MCP_PATH))
    sources = (
        GeneratedSourceV1(MODEL_PATH, MODEL_SOURCE.encode("utf-8"), "production"),
        GeneratedSourceV1(NATIVE_PATH, native, "production"),
        GeneratedSourceV1(MCP_PATH, mcp, "production"),
        GeneratedSourceV1(TEST_PATH, QUALIFICATION_SOURCE.encode("utf-8"), "qualification"),
    )
    for item in sources:
        compile(item.payload, item.relative_path, "exec", dont_inherit=True)
    return RouteWindowColdDeltaV1(sources, _typecheck_source(native, mcp))


def route_window_clock_quote_v1(delta: RouteWindowColdDeltaV1) -> DeltaQuoteV1:
    if type(delta) is not RouteWindowColdDeltaV1 or len(delta.sources) != 4:
        raise ValueError("expected one exact route-window cold delta")
    expected = ((MODEL_PATH, "production"), (NATIVE_PATH, "production"),
                (MCP_PATH, "production"), (TEST_PATH, "qualification"))
    if tuple((s.relative_path, s.role) for s in delta.sources) != expected:
        raise ValueError("cold delta source roles/order differ")
    return {"schema": "xar.route-window-clock-cold-delta/v1", "source31_commit": SOURCE31_COMMIT,
            "inputs": [{"relative_path": NATIVE_PATH, "bytes": NATIVE_BYTES, "sha256": NATIVE_SHA256},
                       {"relative_path": MCP_PATH, "bytes": MCP_BYTES, "sha256": MCP_SHA256}],
            "production": [_pin(item.relative_path, item.payload) for item in delta.sources[:3]],
            "qualification": _pin(delta.sources[3].relative_path, delta.sources[3].payload),
            "typecheck_bytes": len(delta.typecheck_source),
            "typecheck_sha256": hashlib.sha256(delta.typecheck_source).hexdigest(),
            "runtime_mutated": False, "game_executed": False, "live_high_speed_qualified": False}
