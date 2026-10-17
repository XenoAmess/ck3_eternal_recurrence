"""Relevant natural-handoff baseline assignment; no lifecycle or RPC calls."""
import ast
import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import tempfile
import types

PACK = Path(__file__).resolve().parent
source = PACK / "test_classifier_startup_baseline.py"
tree = ast.parse(source.read_text(encoding="utf-8"))
prefix = []
for node in tree.body:
    if isinstance(node, ast.With):
        break
    prefix.append(node)
scope = {"__file__": str(source), "__name__": "natural_baseline_offline"}
exec(compile(ast.Module(body=prefix, type_ignores=[]), str(source), "exec"), scope)
env, original_body = scope["env"], scope["body"]
N, R3 = scope["N"], scope["R3"]
canonical = PACK / "root_p34_canonical_result_classifier.py"
with tempfile.TemporaryDirectory(dir=PACK, prefix="natural-baseline-") as temporary:
    root = Path(temporary)
    target = root / "canonical.py"
    target.write_bytes(canonical.read_bytes())
    (root / "ROOT-P33-CLASSIFIER-PIN.json").write_text(json.dumps({
        "source": str(target), "sha256": hashlib.sha256(target.read_bytes()).hexdigest()
    }), encoding="utf-8")
    env["N"] = root
    classifier = env["load_cold_result_classifier"]()
    old_source = original_body["planning_source_frame"]
    actor, episode = old_source["actor_character_id"] + 1, "synthetic-actual-handoff-new-episode"
    def updated(value):
        if isinstance(value, dict):
            return {key: updated(item) for key, item in value.items()}
        if isinstance(value, list):
            return [updated(item) for item in value]
        if type(value) is int and value == old_source["actor_character_id"]:
            return actor
        if value == old_source["episode_run_id"]:
            return episode
        return value
    new_body = updated(copy.deepcopy(original_body))
    current = dict(new_body["planning_source_frame"], paused=True, map_ready=True, actor_alive=True)
    compact = env["frame"](current)
    natural = R3 / "root_p33_automatic_natural_succession_handoff.py"
    nt = ast.parse(natural.read_text(encoding="utf-8"))
    assignment = next(node for node in ast.walk(nt) if isinstance(node, ast.Assign)
        and ast.unparse(node.targets[0]) == "(queue.semantic, queue.initial_frame, queue.initial_save)")
    queue = types.SimpleNamespace(initial_frame=scope["startup"])
    old_baseline = queue.initial_frame
    saved, final_body = {"status": "saved"}, current
    exec(compile(ast.Module(body=[assignment], type_ignores=[]), str(natural), "exec"),
         dict(queue=queue, compact=compact, final_body=final_body, saved=saved, copy=copy))
    assert queue.initial_frame == compact and len(compact) == 6
    credit = classifier(new_body, initial_frame=queue.initial_frame,
                        game_pid=current["bridge_pid"])[0]
    assert credit["typed_nonmaterial_observation"] is True
    try:
        classifier(new_body, initial_frame=old_baseline, game_pid=current["bridge_pid"])
    except ValueError:
        pass
    else:
        raise AssertionError("stale old-actor baseline accepted")
receipt = {
    "status": "ACTUAL_NATURAL_HANDOFF_BASELINE_ASSIGNMENT_AND_CLASSIFIER_GREEN_NOT_LIVE",
    "at_utc": datetime.now(timezone.utc).isoformat(),
    "canonical_sha256": hashlib.sha256(canonical.read_bytes()).hexdigest(),
    "natural_handoff_source": str(natural),
    "natural_handoff_source_sha256": hashlib.sha256(natural.read_bytes()).hexdigest(),
    "actual_assignment_line": assignment.lineno,
    "actual_queue_frame_six_fields": True,
    "synthetic_new_actor_updated_baseline_accepted": True,
    "synthetic_old_actor_stale_baseline_rejected": True,
    "RPC_or_lifecycle_calls": 0,
    "SDK_or_ledger_writes": 0,
    "temporary_fixture_reclaimed": True,
    "limit": "Only the existing production assignment and classifier were replayed; no actual succession occurred."
}
with (PACK / "NATURAL-BASELINE-ASSIGNMENT-REVIEW.json").open("x", encoding="utf-8", newline="\n") as stream:
    json.dump(receipt, stream, indent=2)
    stream.write("\n")
print(json.dumps(receipt))
