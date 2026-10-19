"""Reviewed P37 source transformer and resident-App queue support.

The runtime owner emits to a separate review directory, inspects the result,
then installs it. Importing this file never reads or operates a runtime.
The current caller must pass --relay-module for its source-pinned provider;
handoff and deferred UI receive those exact relay functions explicitly.
"""
from __future__ import annotations

import argparse
import ast
import copy
import keyword
from pathlib import Path
import textwrap

UI = "ck3_resume_successor_ui_v1"
CLOSE = "ck3_continue_death_succession_modal_v1"


def require(condition, message):
    if not condition:
        raise ValueError("resident successor adoption: " + message)


def _same_frame(left, right):
    return all(left.get(key) == right.get(key) for key in (
        "snapshot_id", "revision", "native_revision", "date_raw", "episode_run_id", "episode_character_id"))


def _app_proof(resumed, continued, *, required=False):
    proof = resumed.get("transition")
    require(not required or isinstance(proof, dict), "App did not retain the original handoff")
    if proof is not None:
        require(isinstance(proof, dict)
            and proof.get("predecessor_character_id") == continued.get("predecessor_character_id")
            and proof.get("successor_character_id") == continued.get("successor_character_id")
            and proof.get("source_episode_run_id") == continued.get("source_episode_run_id")
            and proof.get("episode_run_id") == continued.get("episode_run_id")
            and proof.get("reconciliation") == continued.get("reconciliation")
            and proof.get("succession_lifecycle") == continued.get("succession_lifecycle")
            and proof.get("ck3_command_submitted") is False
            and proof.get("process_restarted") is False,
            "App proof differs from the original Queue result")


async def observe_app_ui_v1(call, env, current, current_path, continued, *, require_proof=False):
    """Observe, optionally Close once, then independently read the original frame."""
    from xar_autoplayer.native_auto_run import _ordinary_succession_close_issue

    resumed, _ = await call(UI, {"expected_revision": current["revision"]})
    require(isinstance(resumed, dict) and type(resumed.get("pending")) is bool
            and resumed.get("status") in {"clear", "deferred_player_decision", "ui_unresolved", "close_required"},
            "App UI result has no explicit clearance")
    _app_proof(resumed, continued, required=require_proof)
    fresh, fresh_path = await call(env["SEMANTIC"], {})
    require(_same_frame(fresh, resumed.get("snapshot", {})), "independent UI post differs from App")
    require(fresh.get("episode_run_id") == continued["episode_run_id"]
            and fresh.get("episode_character_id") == continued["successor_character_id"],
            "UI post changed successor identity")
    status, pending = resumed["status"], resumed["pending"]
    if status == "close_required":
        require(pending is True, "Close requirement lacks its pending obligation")
        closed, _ = await call(CLOSE, {
            "expected_revision": fresh["revision"],
            "expected_played_character_id": continued["successor_character_id"],
            "expected_episode_run_id": continued["episode_run_id"]})
        require(_ordinary_succession_close_issue(closed,
            starting_date_raw=fresh["date_raw"], successor_character_id=continued["successor_character_id"]) is None,
            "original typed Close did not verify; no replay")
        fresh, fresh_path = await call(env["SEMANTIC"], {})
        require(all(fresh.get(left) == closed.get(right) for left, right in (
            ("date_raw", "ending_date_raw"), ("revision", "ending_revision"), ("native_revision", "ending_native_revision"))),
            "independent Close post differs")
        pending = False
    else:
        require((status == "clear") is (pending is False), "App UI pending status contradicts clearance")
    require(fresh.get("paused") is True and fresh.get("map_ready") is True
            and fresh.get("played_character", {}).get("character_id") == continued["successor_character_id"]
            and fresh.get("played_character", {}).get("alive") is True
            and fresh.get("one_life_terminal") is False
            and fresh.get("one_life_terminal_reason") is None,
            "independent post is not the living paused successor")
    # Event and notification presence never grants SAVE even after an App claim.
    deferred = pending or fresh.get("active_event") is not None or fresh.get("pending_character_interaction") is not None
    return fresh, fresh_path, deferred, resumed


def classify_ui_auto_result_v1(body, *, queue_state):
    """Consume only App UI AUTO receipts; every business/ordinary credit is zero."""
    if not isinstance(body, dict) or body.get("status") not in {"successor_ui_pending", "successor_ui_resumed"}:
        return None
    pending = queue_state.get("resident_successor_ui_pending")
    require(isinstance(pending, dict), "UI-only AUTO lacks the Queue's retained handoff")
    resumed = body.get("successor_ui_obligation_v1")
    require(isinstance(resumed, dict) and body.get("selected_step") is None, "UI-only AUTO is malformed")
    _app_proof(resumed, pending["continued"])
    snap = resumed.get("snapshot", {})
    require(snap.get("episode_run_id") == pending["continued"]["episode_run_id"]
            and snap.get("episode_character_id") == pending["continued"]["successor_character_id"]
            and snap.get("campaign_goal") == pending["campaign_goal_after"],
            "UI-only AUTO changed the retained successor goal")
    if body["status"] == "successor_ui_resumed":
        from xar_autoplayer.native_auto_run import _ordinary_succession_close_issue
        closed = body.get("result")
        require(resumed.get("pending") is False and resumed.get("date_advanced") is True
            and isinstance(closed, dict)
            and _ordinary_succession_close_issue(closed, starting_date_raw=closed.get("starting_date_raw"),
                successor_character_id=pending["continued"]["successor_character_id"]) is None,
            "UI-only AUTO lacks its original verified Close")
    else:
        require(resumed.get("pending") is True, "pending UI-only AUTO claims clear")
    return {"schema": "g2.queue.resident-successor-ui-observation/v1", "resident_ui_only": True,
            "selected_step": None, "new_natural_succession_credit": 0, "ordinary_cycle_credit": 0,
            "business_success_inferred": False,
            "ui_end": {"date_raw": snap.get("date_raw"), "actor_character_id": snap.get("episode_character_id"),
                       "episode_run_id": snap.get("episode_run_id"), "native_revision": snap.get("native_revision")}}


async def finish_deferred_ui_v1(queue, session, state, env, *, relay_compact, error_projection):
    """At batch end only, finish an existing UI obligation; no new Continue."""
    pending = state.get("resident_successor_ui_pending")
    if pending is None:
        return state
    require(isinstance(pending, dict) and state.get("pending_cycle") is None
            and state.get("pending_checkpoint") is None and state.get("pending_natural_succession") is None,
            "deferred UI cannot cross another unsettled transaction")
    from root_p37_automatic_natural_succession_handoff import _resident_make_call, qualified_frame
    from root_p37_known_pause_recovery_control import process_birth_filetime
    from root_p37_checkpoint_cadence import checkpoint_saved
    from xar_autoplayer.bridge.succession_transition_contract import normalize_succession_lifecycle_binding_v1
    pid, birth = queue.launch["pid"], queue.job.get("game_creation_filetime")
    require(type(birth) is int and birth > 0, "deferred UI lacks original Game birth")
    audit_path = env["Q"] / f"RESIDENT-SUCCESSOR-UI-{queue.next_sequence:06d}.json"
    audit = {"schema": "g2.queue.resident-successor-ui/v1", "status": "started", "calls": [],
             "original_handoff": pending["audit"], "same_game": {"pid": pid, "creation_filetime": birth},
             "new_natural_succession_credit": 0, "ordinary_cycle_credit": 0, "original_actions_replayed": False}
    env["atomic"](audit_path, audit, limit=65536)
    call = _resident_make_call(queue, session, env, audit, audit_path, process_birth_filetime, pid, birth,
                               relay_compact=relay_compact, error_projection=error_projection)
    try:
        before, before_path = await call(env["SEMANTIC"], {})
        qualified_frame(before, queue, normalize_succession_lifecycle_binding_v1, terminal=False)
        require(before.get("campaign_goal") == pending["campaign_goal_after"], "deferred successor goal changed")
        current, current_path, deferred, _ = await observe_app_ui_v1(
            call, env, before, before_path, pending["continued"])
        require(current.get("campaign_goal") == pending["campaign_goal_after"], "UI changed successor goal")
        if deferred:
            audit.update(status="deferred", action_replay_allowed=False)
            env["atomic"](audit_path, audit, replace=True, limit=65536)
            queue.current_attempt = None
            return state
        saved_body, save_path = await call("ck3_save_checkpoint", {"expected_revision": current["revision"]})
        saved = saved_body.get("checkpoint")
        require(saved_body.get("step") == "save-checkpoint" and saved_body.get("accepted") is True
            and (saved_body.get("materialization") or {}).get("available") is True
            and isinstance(saved, dict) and saved.get("status") == "saved"
            and saved.get("date_raw") == current["date_raw"]
            and saved.get("episode_character_id") == pending["continued"]["successor_character_id"]
            and saved.get("episode_run_id") == current["episode_run_id"]
            and saved.get("succession_lifecycle") == queue.expected_lifecycle_binding
            and type(saved.get("size")) is int and saved["size"] > 0
            and isinstance(saved.get("sha256"), str) and len(saved["sha256"]) == 64
            and (saved_body.get("driver_state_replace_receipt") or {}).get("save_binding_verified") is True,
            "deferred successor SAVE lacks original materialization; no replay")
        final, final_path = await call(env["SEMANTIC"], {})
        qualified_frame(final, queue, normalize_succession_lifecycle_binding_v1, terminal=False)
        require(all(final.get(key) == current.get(key) for key in ("date_raw", "episode_run_id", "episode_character_id"))
                and all(type(final.get(key)) is int and final[key] >= current[key] for key in ("revision", "native_revision"))
                and final.get("active_event") == current.get("active_event")
                and final.get("pending_character_interaction") == current.get("pending_character_interaction")
                and final.get("campaign_goal") == pending["campaign_goal_after"],
                "independent deferred SAVE post changed")
        compact = {key: final[key] for key in ("snapshot_id", "revision", "native_revision", "date_raw", "episode_run_id")}
        compact["actor_character_id"] = final["played_character"]["character_id"]
        state.pop("resident_successor_ui_pending")
        state.update(before=compact, before_metrics_response=str(final_path), actual_saved_checkpoint=copy.deepcopy(saved),
                     checkpoint_dirty_since_save=False)
        checkpoint_saved(state, saved)
        state["counts"]["checkpoint_saved"] += 1
        state["actual_saved_checkpoint_source"] = {"global_turn": state["completed_cycles"],
            "semantic_response": str(current_path), "save_response": str(save_path)}
        queue.full_loop_state = state
        queue.persist_loop_state()
        queue.semantic, queue.initial_frame, queue.initial_save = final, compact, copy.deepcopy(saved)
        audit.update(status="verified", checkpoint=saved, final_frame=compact)
        env["atomic"](audit_path, audit, replace=True, limit=65536)
        queue.current_attempt = None
        return state
    except Exception as error:
        audit.update(status="failed_retained", error_type=type(error).__name__, error=str(error)[:4096],
                     automatic_action_retry=False)
        env["atomic"](audit_path, audit, replace=True, limit=65536)
        raise


def _replace(source, old, new):
    require(source.count(old) == 1, "source anchor changed: " + old[:100])
    return source.replace(old, new, 1)


def _relay_module_v1(relay_module):
    require(isinstance(relay_module, str) and bool(relay_module)
            and all(part.isidentifier() and not keyword.iskeyword(part)
                    for part in relay_module.split('.')),
            "explicit current relay module required")
    return relay_module


def bind_handoff_relay_v1(source):
    """Bind only the two legacy relay imports in the reviewed handoff shape."""
    old_import = '    from root_p37_overlay_relay import relay_compact, error_projection\n'
    require(source.count(old_import) == 2, "expected the original two handoff relay imports")
    source = source.replace(old_import, '')
    source = _replace(source,
        '                            birth_reader=None):\n',
        '                            relay_compact, error_projection, birth_reader=None):\n')
    source = _replace(source,
        'def _resident_make_call(queue, session, env, audit, audit_path, birth_reader, pid, birth):\n',
        'def _resident_make_call(queue, session, env, audit, audit_path, birth_reader, pid, birth,\n'
        '                        *, relay_compact, error_projection):\n'
        '    require(callable(relay_compact) and callable(error_projection), "current relay functions required")\n')
    source = _replace(source,
        '    call = _resident_make_call(queue, session, env, audit, audit_path, birth_reader, pid, birth)\n',
        '    call = _resident_make_call(queue, session, env, audit, audit_path, birth_reader, pid, birth,\n'
        '                               relay_compact=relay_compact, error_projection=error_projection)\n')
    ast.parse(source)
    return source


def bind_queue_relay_v1(source, *, relay_module):
    """The generation owner names the qualified relay; no implicit fallback."""
    relay_module = _relay_module_v1(relay_module)
    source = _replace(source,
        '                state = await automatic_handoff(self, session, state,\n'
        '                    original_before=before, event=event, env=globals())\n',
        f'                from {relay_module} import relay_compact, error_projection\n'
        '                state = await automatic_handoff(self, session, state,\n'
        '                    original_before=before, event=event, env=globals(),\n'
        '                    relay_compact=relay_compact, error_projection=error_projection)\n')
    source = _replace(source,
        '            state = await finish_deferred_ui_v1(self, session, state, globals())\n',
        f'            from {relay_module} import relay_compact, error_projection\n'
        '            state = await finish_deferred_ui_v1(self, session, state, globals(),\n'
        '                relay_compact=relay_compact, error_projection=error_projection)\n')
    ast.parse(source)
    return source


def transform_handoff_v1(source):
    # Lift the original durable unique-request I/O unchanged; both paths retain
    # original kernel birth, guard, held-control, overlay and response evidence.
    start = source.index("    def verify():\n", source.index("async def automatic_handoff"))
    end = source.index("    try:\n        first_body, first_path", start)
    io = textwrap.dedent(source[start:end]).replace(
        '"ck3_query_current_timeline_blocker_context_v1",',
        '"ck3_query_current_timeline_blocker_context_v1", "ck3_resume_successor_ui_v1",')
    factory = '\n\ndef _resident_make_call(queue, session, env, audit, audit_path, birth_reader, pid, birth):\n'
    factory += '    from root_p37_overlay_relay import relay_compact, error_projection\n'
    factory += textwrap.indent(io, '    ') + '    return call\n'
    source = source[:start] + '    call = _resident_make_call(queue, session, env, audit, audit_path, birth_reader, pid, birth)\n\n' + source[end:]
    start = source.index('        timeline, _ = await call("ck3_query_current_timeline_blocker_context_v1",')
    end = source.index('        # A checkpoint serializes unresolved choices.', start)
    source = source[:start] + '''        from p51_resident_successor_adoption_v1 import observe_app_ui_v1
        after_body, after_path, deferred_ui, app_ui = await observe_app_ui_v1(
            call, env, after_body, after_path, continued, require_proof=True)
        after = checked_successor(after_body, dict(after, date_raw=after_body["date_raw"],
            revision=after_body["revision"], native_revision=after_body["native_revision"]),
            continued, queue, normalize, old_goal)

''' + source[end:]
    start = source.index('        saved_body, save_path = await call(SAVE,')
    end = source.index('        final_body, final_path = await call(env["SEMANTIC"], {})', start)
    source = source[:start] + '        saved = save_path = None\n        if not deferred_ui:\n' + textwrap.indent(source[start:end], '    ') + source[end:]
    source = _replace(source, '                         actual_saved_checkpoint=copy.deepcopy(saved),\n',
        '                         actual_saved_checkpoint=copy.deepcopy(saved) if saved is not None else state.get("actual_saved_checkpoint"),\n')
    source = _replace(source, '                         checkpoint_dirty_since_save=False)\n        checkpoint_saved(projected, saved)\n        projected["counts"]["checkpoint_saved"] += 1\n',
        '''                         checkpoint_dirty_since_save=deferred_ui)
        if deferred_ui:
            projected["resident_successor_ui_pending"] = {"audit": str(audit_path),
                "continued": copy.deepcopy(continued), "campaign_goal_after": copy.deepcopy(final_body["campaign_goal"])}
        else:
            checkpoint_saved(projected, saved)
            projected["counts"]["checkpoint_saved"] += 1
''')
    source = _replace(source, '        projected["actual_saved_checkpoint_source"] = {\n            "global_turn": key, "semantic_response": str(after_path), "save_response": str(save_path)}\n',
        '        if saved is not None:\n            projected["actual_saved_checkpoint_source"] = {\n                "global_turn": key, "semantic_response": str(after_path), "save_response": str(save_path)}\n')
    source = _replace(source, '        queue.semantic, queue.initial_frame, queue.initial_save = final_body, compact, copy.deepcopy(saved)\n',
        '        queue.semantic, queue.initial_frame = final_body, compact\n        if saved is not None:\n            queue.initial_save = copy.deepcopy(saved)\n')
    source = _replace(source, '        audit.update(status="verified", terminal_cleared=True, original_actions_replayed=False)\n',
        '        audit.update(status="deferred_resident_ui" if deferred_ui else "verified",\n                     terminal_cleared=not deferred_ui, original_actions_replayed=False)\n')
    source = source.replace('"unresolved_decisions_saved_not_resolved": True',
                            '"unresolved_decisions_saved_not_resolved": saved is not None, "resident_ui_deferred": deferred_ui')
    source = source.replace('unresolved_decisions_saved_not_resolved=True)',
                            'unresolved_decisions_saved_not_resolved=saved is not None, resident_ui_deferred=deferred_ui)')
    source += factory
    return bind_handoff_relay_v1(source)


def transform_queue_v1(source, *, relay_module):
    _relay_module_v1(relay_module)
    source = _replace(source, '            if observation is None:\n                observation, self.governance_result_state, self.lifestyle_pending_focus = classifier(\n',
        '            if observation is None:\n                from p51_resident_successor_adoption_v1 import classify_ui_auto_result_v1\n                observation = classify_ui_auto_result_v1(body, queue_state=ordinary_state)\n            if observation is None:\n                observation, self.governance_result_state, self.lifestyle_pending_focus = classifier(\n')
    source = _replace(source, '            event = {**pending, "after": after, "after_metrics_response": str(after_path),\n',
        '''            if observation.get("resident_ui_only") is True:
                end = observation["ui_end"]
                if (any(after[k] != end[k] for k in ("date_raw", "actor_character_id", "episode_run_id"))
                        or after["native_revision"] < end["native_revision"]):
                    raise ValueError("paired metrics differ from original resident UI AUTO")
                atomic(Q / f"RESIDENT-UI-AUTO-{pending['auto_sequence']:06d}.json", {
                    "source": pending["auto_response"], "after_metrics_response": str(after_path),
                    "observation": observation, "new_natural_succession_credit": 0,
                    "ordinary_cycle_credit": 0}, limit=16384)
                state["before"], state["before_metrics_response"] = after, str(after_path)
                state["pending_cycle"] = None
                self.persist_loop_state()
                break
            event = {**pending, "after": after, "after_metrics_response": str(after_path),
''')
    source = _replace(source, '            elif checkpoint_after_settled_cycle(state, pending, after):\n',
        '            elif not state.get("resident_successor_ui_pending") and checkpoint_after_settled_cycle(state, pending, after):\n')
    source = _replace(source, '        result = {"status": "bounded_loop_finished", "batch": self.loop_count, "actual_turns": settled,\n',
        '        if state.get("resident_successor_ui_pending") is not None:\n            from p51_resident_successor_adoption_v1 import finish_deferred_ui_v1\n            state = await finish_deferred_ui_v1(self, session, state, globals())\n        result = {"status": "bounded_loop_finished", "batch": self.loop_count, "actual_turns": settled,\n')
    return bind_queue_relay_v1(source, relay_module=relay_module)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--relay-module", required=True,
                        help="Current source-pinned relay module for this generation")
    args = parser.parse_args()
    _relay_module_v1(args.relay_module)
    require(args.source_root.resolve() != args.output_root.resolve(), "review output must differ from runtime source")
    args.output_root.mkdir(parents=True, exist_ok=False)
    for name, transform in (("root_p37_sdk_queue.py", transform_queue_v1),
                            ("root_p37_automatic_natural_succession_handoff.py", transform_handoff_v1)):
        source = (args.source_root / name).read_text(encoding="utf-8")
        content = (transform(source, relay_module=args.relay_module)
                   if transform is transform_queue_v1 else transform(source))
        (args.output_root / name).write_text(content, encoding="utf-8", newline="\n")
    (args.output_root / Path(__file__).name).write_bytes(Path(__file__).read_bytes())
    print("REVIEW_OUTPUT_EMITTED_NO_RUNTIME_MUTATION")


if __name__ == "__main__":
    main()
