import copy
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from readonly_precondition_portable_v1 import (
    classify_revision_mismatch_before_submit,
    qualify_observed_successor,
)


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


def test_revision_qualification():
    with TemporaryDirectory() as temporary:
        root = Path(temporary)
        response = root / "0011-1-result.json"
        metrics = root / "0010-1-result.json"
        plan = root / "0011-0-plan.json"
        driver = root / "driver.py"
        service = root / "service.py"
        driver.write_text("reviewed pre-send check", encoding="utf-8")
        service.write_text("reviewed pre-submit check", encoding="utf-8")
        pins = {path: hashlib.sha256(path.read_bytes()).hexdigest()
                for path in (driver, service)}
        mode = write(root / "mode.json", {
            "driver_class": "NativeHeadlessGameplayDriver",
            "episode_projection": "one_life", "before_submit_observation": True,
            "policy_replaced": False, "transport_cap_replaced": False,
            "source_file": str(driver),
        })
        row = {"request": {"sequence": 11, "tool": "ck3_auto_turn", "arguments": {}},
               "client_error": None, "result": {
                   "is_error": True, "structured_content": None,
                   "result_type": "complete", "content": [{"type": "text", "text":
                       "Error executing tool ck3_auto_turn: native gameplay revision mismatch: expected 71, current 72"}]}}
        write(response, row)
        before = {"revision": 71, "native_revision": 70, "snapshot_id": "native:70",
                  "actor_alive": True, "actor_character_id": 301, "date_raw": 1000,
                  "episode_run_id": "episode-1", "connection_generation": 1,
                  "paused": True, "map_ready": True}
        write(metrics, {"request": {"sequence": 10, "tool": "root_current_runtime_metrics"},
                        "result": {"is_error": False, "structured_content": before}})
        args = dict(original_response=response, prior_metrics=metrics, before_plan=plan,
                    pinned_sources=pins, driver_mode=mode, expected_driver_source=driver)
        classify = classify_revision_mismatch_before_submit
        qualified = classify(row, **args)
        assert qualified and qualified["business_submission"] is False
        assert qualified["failed_native_command_sent"] is False
        assert classify(row, **args) == qualified
        plan.write_text("before_submit already reached", encoding="utf-8")
        assert classify(row, **args) is None
        plan.unlink()
        bad = copy.deepcopy(row)
        bad["result"]["content"][0]["text"] = "another error"
        assert classify(bad, **args) is None
        bad = copy.deepcopy(row)
        bad["result"]["is_error"] = False
        assert classify(bad, **args) is None
        before["actor_alive"] = False
        write(metrics, {"request": {"sequence": 10, "tool": "root_current_runtime_metrics"},
                        "result": {"is_error": False, "structured_content": before}})
        assert classify(row, **args) is None
        before["actor_alive"] = True
        write(metrics, {"request": {"sequence": 10, "tool": "root_current_runtime_metrics"},
                        "result": {"is_error": False, "structured_content": before}})
        driver.write_text("different source", encoding="utf-8")
        assert classify(row, **args) is None


def test_observed_successor_qualification():
    old, heir, pid = 301, 302, 703
    before = {"actor_character_id": old, "episode_run_id": "predecessor-episode",
              "date_raw": 1000, "revision": 71, "native_revision": 70}
    goal = {"campaign_id": "campaign-a", "current_character_id": old}
    lifecycle = {"lifecycle": "ordinary_campaign_succession", "xar_enabled": "xar_off"}
    body = {"map_ready": True, "paused": True, "one_life_terminal": True,
            "one_life_terminal_reason": "played_character_changed",
            "succession_lifecycle": lifecycle, "played_character": {"character_id": heir, "alive": True},
            "diagnostics": {"connected": True, "bridge_pid": pid, "pipe_name": "pipe-a",
                            "connection_generation": 2,
                            "hello": {"pid": pid, "connection_generation": 2,
                                      "ck3_build_match": True, "game_adapter_status": "ready",
                                      "game_adapter_id": "adapter-a"}},
            "campaign_goal": goal, "episode_character_id": old,
            "episode_run_id": before["episode_run_id"], "date_raw": 1024,
            "revision": 72, "native_revision": 71, "snapshot_id": "native:71"}
    expectation = {"schema": "xar.ck3.succession-expectation/v1",
                   "status": "available", "expectation_state": "successor_expected",
                   "predecessor_character_id": old, "expected_successor_character_id": heir,
                   "title_expectations": [{"title": {"title_id": 17}}],
                   "binding": {"episode_character_id": old,
                               "episode_run_id": before["episode_run_id"], "date_raw": 900}}
    body["succession_expectation"] = expectation
    body["succession_reconciliation"] = {
        "status": "available", "verdict": "matched", "successor_match": True,
        "title_distribution_match": True, "predecessor_character_id": old,
        "expected_successor_character_id": heir, "actual_successor_character_id": heir,
        "predecessor_binding": expectation["binding"],
        "successor_binding": {key: body[key] for key in
                              ("snapshot_id", "revision", "native_revision", "date_raw")},
    }
    args = dict(before=before, retained_goal=goal, expected_lifecycle=lifecycle,
                game_pid=pid, pipe_name="pipe-a", expected_adapter_id="adapter-a",
                same_game_kernel_birth_verified=True)
    qualify = qualify_observed_successor
    positive = qualify(body, **args)
    assert positive and positive["successor_character_id"] == heir
    assert positive["original_auto_business_credit"] == 0
    assert positive["handoff_actions_performed"] is False
    for name, mutate in (
        ("no_heir", lambda x: x["succession_expectation"].update(expectation_state="no_successor")),
        ("dead", lambda x: x["played_character"].update(alive=False)),
        ("wrong_episode", lambda x: x.update(episode_run_id="new-episode")),
        ("wrong_game", lambda x: x["diagnostics"].update(bridge_pid=pid + 1)),
        ("unmatched", lambda x: x["succession_reconciliation"].update(verdict="pending")),
        ("wrong_title", lambda x: x["succession_reconciliation"].update(title_distribution_match=False)),
    ):
        bad = copy.deepcopy(body)
        mutate(bad)
        assert qualify(bad, **args) is None, name
    assert qualify(body, **{**args, "same_game_kernel_birth_verified": False}) is None


if __name__ == "__main__":
    test_revision_qualification()
    test_observed_successor_qualification()
    print("portable focused GREEN")
