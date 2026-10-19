"""Offline qualification of closed originals; prints JSON, writes nothing."""
import ast
import copy
import hashlib
import json
from pathlib import Path
import re
import sys
from unittest.mock import patch


def selected(raw):
    nodes = []
    for node in ast.parse(raw.decode("utf-8-sig")).body:
        if isinstance(node, ast.FunctionDef) and node.name.startswith("classify_"):
            nodes.append(node)
        elif isinstance(node, ast.Assign) and all(
                isinstance(target, ast.Name) and target.id.isupper() for target in node.targets):
            try:
                ast.literal_eval(node.value)
            except (ValueError, TypeError):
                continue
            nodes.append(node)
    return ast.Module(body=nodes, type_ignores=[])


def main(runtime):
    runtime = Path(runtime).resolve()
    fixture = runtime.parent.parent / "p51-fresh1066-v20261019-prepare01" / \
        "c18-route10416-classifier-failure94"
    donor = Path(__file__).resolve().parent
    files = {
        fixture / "auto.json": "f55b4b439854ce0f6e9c5543b7281ebcbb2bba84c07a8b4cc46f242211de39c1",
        fixture / "before_MET.json": "5d18290f89f6348e0088a62f0aed482e6378e843292cf30af092a295226b69a3",
        runtime / "p37-responses/10410-1-result.json": "851ec264d33fecfd9e124deb869e68590a89396fc2d4256a6f2f0e5c004e8d67",
        runtime / "root_p37c18_sdk_queue.py": "f4adb613364e56413b5244e13122f2530a897a5e42d76c1fa9897e2c7bfcd694",
        runtime / "root_p37c11_prisoner_epoch_classifier.py": "0bff8fae24c072d5f05285ba62c503dfed408f8095690fb8dffec16fe72ec28b",
    }
    raw = {path: path.read_bytes() for path in files}
    assert all(hashlib.sha256(raw[path]).hexdigest() == sha for path, sha in files.items())
    body = json.loads(raw[fixture / "auto.json"])["result"]["structured_content"]
    before = json.loads(raw[fixture / "before_MET.json"])["result"]["structured_content"]
    keys = ("snapshot_id", "revision", "native_revision", "date_raw", "actor_character_id",
            "episode_run_id", "connection_generation", "bridge_pid")
    assert all(type(before[key]) is type(body["planning_source_frame"][key])
               and before[key] == body["planning_source_frame"][key] for key in keys)
    env = {"Path": Path, "ast": ast, "hashlib": hashlib, "json": json,
           "copy": copy, "re": re, "AUTO": "ck3_auto_turn", "SAVE": "ck3_save_checkpoint"}
    outer_path = runtime / "root_p37c11_prisoner_epoch_classifier.py"
    base = dict(env)
    exec(compile(selected(raw[outer_path]), str(outer_path), "exec"), base)
    adapter_path = runtime / "root_route_source15_classifier_adapter_v1.py"
    exec(compile(selected((donor / "route_contact_source15_classifier_adapter_v1.py").read_bytes()),
                 str(adapter_path), "exec"), env)
    # Simulate only the proposed small source copies; original evidence stays in place.
    redirect = {runtime / name: donor / name for name in (
        "route_contact_exact_day_outcome.py", "route_contact_same_speed_source_v1.py")}
    read_bytes = Path.read_bytes
    def read(path):
        return read_bytes(redirect.get(path, path))
    original = copy.deepcopy(body)
    state, pending = {"retained": True}, {"retained": True}
    with patch.object(Path, "read_bytes", read):
        result = env["classify_auto_result_credit_v1"](
            body, state=state, pending_focus=pending, initial_frame=before, game_pid=30852)
    assert body == original and result[1] is state and result[2] is pending
    assert result[0]["actual_date_delta_raw"] == 24 and result[0]["replay_allowed"] is False
    four = json.loads(raw[runtime / "p37-responses/10410-1-result.json"])["result"]["structured_content"]
    kwargs = dict(initial_frame=four["planning_source_frame"], game_pid=30852)
    expected = base["classify_auto_result_credit_v1"](four, **kwargs)
    with patch.object(Path, "read_bytes", read):
        assert env["classify_auto_result_credit_v1"](four, **kwargs) == expected
    queue = ast.parse(raw[runtime / "root_p37c18_sdk_queue.py"])
    apis = {node.name: ast.unparse(node.args) for node in ast.walk(queue)
            if isinstance(node, ast.AsyncFunctionDef) and node.name in {
                "install_result_classifier", "reconsume_original_response"}}
    assert apis == dict.fromkeys(apis, "self, session, request, path") and len(apis) == 2
    print(json.dumps({"status": "PASS", "full_original_10416_bytes": 58937,
        "independent_before_MET_eight_keys": True, "old_four_top_level_equal": True,
        "body_state_pending_unchanged": True, "actual_queue_API": apis,
        "credit": result[0], "new_Game_RPC_calls": 0, "installed": False}, ensure_ascii=False))


if __name__ == "__main__":
    main(sys.argv[1])
