"""The ordinary no-modal planner must retain its managed state directory."""
from pathlib import Path
from types import SimpleNamespace
import ast

import xar_autoplayer.bridge.service as service


def _planner(state_dir: Path | None):
    source = Path(service.__file__)
    cls = next(node for node in ast.parse(source.read_text(encoding="utf-8-sig")).body
               if isinstance(node, ast.ClassDef) and node.name == "GameplayBridgeService")
    method = next(node for node in cls.body
                  if isinstance(node, ast.FunctionDef) and node.name == "_plan_turn_internal")
    nested = next(node for node in method.body
                  if isinstance(node, ast.FunctionDef) and node.name == "plan_from_view")
    names = ("self", "state_dir", "overview_projection", "available_steps",
             "bridge_capabilities", "campaign_goal_plan", "cross_run_plan",
             "battle_speed_readiness", "feast_lifecycle_observation",
             "use_internal_view", "private_history_views")
    factory = ast.FunctionDef(
        name="factory",
        args=ast.arguments(posonlyargs=[], args=[ast.arg(arg=name) for name in names],
                           kwonlyargs=[], kw_defaults=[], defaults=[]),
        body=[nested, ast.Return(value=ast.Name(id="plan_from_view", ctx=ast.Load()))],
        decorator_list=[])
    namespace = vars(service).copy()
    exec(compile(ast.fix_missing_locations(ast.Module(body=[factory], type_ignores=[])),
                 str(source), "exec"), namespace)
    driver = SimpleNamespace(allow_private_construction_formal_trial=True)
    owner = SimpleNamespace(driver=driver, _strategy_state_dir=lambda: state_dir,
                            _observed_planning_source_frame=lambda value: {"status": "complete"},
                            _auto_camera_hotspot_input=lambda *args: None)
    args = (owner, state_dir, {}, {"query-army-strengths"}, [], None, None, None,
            None, False, {})
    reads = []
    namespace["read_construction_ledger"] = lambda directory: reads.append(directory) or {}
    namespace["plan_one_life_window_priority_v1"] = lambda *args, **kwargs: {
        "selected_step": "query-army-strengths", "phase": "fixture_readonly"}
    namespace["_route_plan_to_available_step"] = lambda plan, steps: plan
    return namespace["factory"](*args), reads


def _frame():
    return {
        "snapshot_id": "fixture:1", "revision": 1, "native_revision": 1,
        "date_raw": 53296104,
        "played_character": {"character_id": 40526, "alive": True},
        "episode_run_id": "fixture-episode", "active_wars": [], "history": [],
        "top_exclusive_modal_choice_hint": {"status": "absent"},
    }


def test_no_modal_uses_outer_managed_state_for_construction(tmp_path: Path):
    planner, reads = _planner(tmp_path)
    assert planner(_frame(), [])["plan"]["selected_step"] == "query-army-strengths"
    assert reads == [tmp_path]


def test_no_managed_state_skips_construction_ledger():
    planner, reads = _planner(None)
    assert planner(_frame(), [])["plan"]["selected_step"] == "query-army-strengths"
    assert reads == []
