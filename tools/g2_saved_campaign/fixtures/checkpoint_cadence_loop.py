"""Offline exact coroutine excerpts; globals supplied by fake transport tests."""
"""Avoid invalidating a paused read-only evidence chain with redundant saves."""
import re


def checkpoint_step_is_readonly(step):
    """Existing query namespaces plus the exact current native route preview."""
    if not isinstance(step, str):
        return False
    if step.startswith(('query-', 'private-query-')):
        return True
    match = re.fullmatch(r'preview-move-army-(0|[1-9][0-9]{0,9})-to-([1-9][0-9]{0,9})', step)
    return match is not None and int(match[1]) <= 2**31 - 1 and int(match[2]) <= 2**31 - 1


def checkpoint_cycle_may_change_game(pending, after):
    before = pending['before']
    if any(after.get(key) != before.get(key) for key in ('date_raw', 'actor_character_id', 'episode_run_id')):
        return True
    observation = pending.get('observation') or {}
    if observation.get('submitted_pending') is True:
        return True
    if any(observation.get(key) is True for key in (
        'lifestyle_material_verified', 'council_material_verified',
        'construction_start_verified', 'construction_completion_verified',
        'crown_material_verified', 'existing_typed_material_verified',
    )):
        return True
    step = pending.get('selected_step')
    # These are the existing read-only native query namespaces. Applied
    # construction receipts can describe an earlier change; querying one is
    # not a new construction mutation.
    return not checkpoint_step_is_readonly(step)


def checkpoint_after_settled_cycle(state, pending, after):
    dirty = state.get('checkpoint_dirty_since_save', False)
    dirty = dirty or checkpoint_cycle_may_change_game(pending, after)
    state['checkpoint_dirty_since_save'] = dirty
    return state['completed_cycles'] % 5 == 0 and not state['terminal'] and dirty

class OriginalQueueFixture:
    async def full_loop(self, session, request, path):
            """One batch <=30; cumulative cycles and fifth-cycle SAVE never reset."""
            if getattr(self, "halted", None):
                raise RuntimeError("original failed response remains halted; observe/reconsume it first")
            self.current_attempt = None
            if self.initial_save is None or not self.checkpoint_bootstrap_verified:
                raise ValueError("full_loop requires actual verified cold canonical bootstrap")
            self.require_camera_pixel_admission()
            arguments = request.get("arguments", {})
            maximum = arguments.get("max_turns", 30) if isinstance(arguments, dict) else None
            if not isinstance(arguments, dict) or set(arguments) - {"max_turns"} or type(maximum) is not int or not 1 <= maximum <= 30:
                raise ValueError("each full_loop batch max_turns must be 1..30")
            control_sequence = self.consume_sequence(request)
            self.held_control = path.name
            self.loop_count += 1
            atomic(Q / f"INFLIGHT-{control_sequence:04d}.json", {"request": request, "control_only": True,
                   "batch": self.loop_count, "original_action_replay_allowed": False}, limit=16384)
            state = getattr(self, "full_loop_state", None)
            if state is None:
                initial, initial_path = await self.generated(session, METRICS)
                initial = frame(initial)
                state = self.full_loop_state = {"schema": "g2.queue.cumulative-loop/v1", "completed_cycles": 0,
                    "start_date_raw": initial["date_raw"], "before": initial, "before_metrics_response": str(initial_path),
                    "pending_cycle": None, "pending_checkpoint": None, "terminal": None,
                    "counts": {key: 0 for key in ("submitted_pending_turns", "lifestyle_material_verified_turns",
                        "existing_focus_verified_turns", "primitive_accepted_turns", "council_material_verified_turns",
                        "construction_material_verified_turns", "construction_start_verified_turns", "construction_completion_verified_turns",
                        "crown_material_verified_turns", "crown_receipt_nonmaterial_turns", "existing_typed_material_verified_turns",
                        "typed_nonmaterial_observation_turns", "date_advanced_turns", "checkpoint_saved", "checkpoint_deferred")}}
                self.persist_loop_state()
            if state["terminal"]:
                raise ValueError("cumulative run reached its retained terminal boundary")
            settled = 0
            while settled < maximum:
                self.guard()
                # Complete an already settled fifth cycle before any new AUTO.
                if state["pending_checkpoint"] is not None:
                    checkpoint = state["pending_checkpoint"]
                    if checkpoint.get("save_sequence") is not None:
                        raise ValueError("original SAVE unresolved; no repeated SAVE or new AUTO")
                    snapshot, snapshot_path = await self.generated(session, SEMANTIC)
                    actual = frame(snapshot, semantic=True, expected_lifecycle=self.expected_lifecycle_binding)
                    if any(actual[key] != state["before"][key] for key in ("date_raw", "actor_character_id", "episode_run_id")):
                        raise ValueError("cumulative safe-save frame differs from paired after metrics")
                    checkpoint["semantic_response"] = str(snapshot_path)
                    if isinstance(snapshot.get("active_event"), dict) or isinstance(snapshot.get("pending_character_interaction"), dict):
                        atomic(Q / f"CUMULATIVE-SAVE-{checkpoint['global_turn']:06d}.json", {"status": "deferred_player_decision",
                            "global_turn": checkpoint["global_turn"], "semantic_response": str(snapshot_path)}, limit=16384)
                        state["counts"]["checkpoint_deferred"] += 1
                        state["pending_checkpoint"] = None
                        self.persist_loop_state()
                    else:
                        checkpoint["save_sequence"] = self.next_sequence
                        self.persist_loop_state()
                        saved, save_path = await self.generated(session, SAVE, {"expected_revision": snapshot["revision"]})
                        self.finish_cumulative_checkpoint(saved, save_path)
                    if settled >= maximum:
                        break
                pending = state["pending_cycle"]
                if pending is None:
                    pending = state["pending_cycle"] = {"global_turn": state["completed_cycles"] + 1,
                        "before": state["before"], "before_metrics_response": state["before_metrics_response"],
                        "auto_sequence": self.next_sequence, "stage": "auto_unsettled"}
                    self.persist_loop_state()
                    turn, auto_path = await self.generated(session, AUTO)
                    plan = turn.get("plan") if isinstance(turn.get("plan"), dict) else {}
                    pending.update(stage="auto_verified", auto_response=str(auto_path), observation=dict(self.last_auto_observation),
                                   phase=plan.get("phase"), selected_step=turn.get("selected_step", plan.get("selected_step")))
                    self.persist_loop_state()
                elif pending["stage"] != "auto_verified":
                    raise ValueError("original AUTO unresolved; install reviewed classifier and reconsume original response, never resend")
                after_body, after_path = await self.generated(session, METRICS)
                after = frame(after_body)
                before = pending["before"]
                observation = pending["observation"]
                event = {**pending, "after": after, "after_metrics_response": str(after_path),
                         "date_delta_raw": after["date_raw"] - before["date_raw"], "business_success_inferred": False}
                for field, counter in (("submitted_pending", "submitted_pending_turns"),
                        ("lifestyle_material_verified", "lifestyle_material_verified_turns"),
                        ("existing_focus_verified", "existing_focus_verified_turns"), ("primitive_accepted", "primitive_accepted_turns"),
                        ("council_material_verified", "council_material_verified_turns"),
                        ("construction_material_verified", "construction_material_verified_turns"),
                        ("construction_start_verified", "construction_start_verified_turns"),
                        ("construction_completion_verified", "construction_completion_verified_turns"),
                        ("crown_material_verified", "crown_material_verified_turns"), ("crown_receipt_nonmaterial", "crown_receipt_nonmaterial_turns"),
                        ("existing_typed_material_verified", "existing_typed_material_verified_turns"),
                        ("typed_nonmaterial_observation", "typed_nonmaterial_observation_turns")):
                    state["counts"][counter] += int(observation.get(field) is True)
                state["counts"]["date_advanced_turns"] += int(event["date_delta_raw"] > 0)
                if after["date_raw"] < before["date_raw"]:
                    state["terminal"] = "actual_date_regressed"
                elif any(after[key] != before[key] for key in ("actor_character_id", "episode_run_id")):
                    state["terminal"] = "actual_actor_or_episode_changed_Root_checkpoint_handoff_required"
                event["cumulative_observation_counts"] = dict(state["counts"])
                atomic(Q / f"CUMULATIVE-TURN-{pending['global_turn']:06d}.json", event, limit=16384)
                state["completed_cycles"] = pending["global_turn"]
                state["before"], state["before_metrics_response"] = after, str(after_path)
                state["pending_cycle"] = None
                if checkpoint_after_settled_cycle(state, pending, after):
                    state["pending_checkpoint"] = {"global_turn": state["completed_cycles"], "save_sequence": None}
                elif state["completed_cycles"] % 5 == 0 and not state["terminal"]:
                    state["counts"]["checkpoint_readonly_skipped"] = state["counts"].get("checkpoint_readonly_skipped", 0) + 1
                    atomic(Q / f"CUMULATIVE-READONLY-SAVE-SKIP-{state['completed_cycles']:06d}.json", {
                        "status": "unchanged_readonly_evidence_chain", "global_turn": state["completed_cycles"],
                        "frame": after, "new_gameplay_mutations_observed": False,
                        "last_actual_checkpoint_retained": True}, limit=16384)
                self.persist_loop_state()
                settled += 1
                if state["terminal"]:
                    break
            # The final fifth cycle's checkpoint belongs to this batch, too.
            if state["pending_checkpoint"] is not None and not state["terminal"]:
                checkpoint = state["pending_checkpoint"]
                snapshot, snapshot_path = await self.generated(session, SEMANTIC)
                actual = frame(snapshot, semantic=True, expected_lifecycle=self.expected_lifecycle_binding)
                if any(actual[key] != state["before"][key] for key in ("date_raw", "actor_character_id", "episode_run_id")):
                    raise ValueError("final cumulative checkpoint frame differs")
                checkpoint["semantic_response"] = str(snapshot_path)
                if isinstance(snapshot.get("active_event"), dict) or isinstance(snapshot.get("pending_character_interaction"), dict):
                    atomic(Q / f"CUMULATIVE-SAVE-{checkpoint['global_turn']:06d}.json", {"status": "deferred_player_decision",
                        "global_turn": checkpoint["global_turn"], "semantic_response": str(snapshot_path)}, limit=16384)
                    state["counts"]["checkpoint_deferred"] += 1
                    state["pending_checkpoint"] = None
                    self.persist_loop_state()
                else:
                    checkpoint["save_sequence"] = self.next_sequence
                    self.persist_loop_state()
                    saved, save_path = await self.generated(session, SAVE, {"expected_revision": snapshot["revision"]})
                    self.finish_cumulative_checkpoint(saved, save_path)
            result = {"status": "bounded_loop_finished", "batch": self.loop_count, "actual_turns": settled,
                      "cumulative_cycles": state["completed_cycles"], "observation_counts": dict(state["counts"]),
                      "actual_calendar_days": (state["before"]["date_raw"] - state["start_date_raw"]) / 24,
                      "actual_end_date_raw": state["before"]["date_raw"], "reason": state["terminal"] or "batch_bound_reached",
                      "same_SDK_continuation_available": not bool(state["terminal"]), "next_sequence": self.next_sequence,
                      "campaign_complete_claimed": False, "replay_allowed": False}
            atomic(OUTBOX / path.name, {"request": request, "result": {"is_error": False, "structured_content": result}}, limit=16384)
            self.held_control = None
            return result

class CandidateQueueFixture:
    async def full_loop(self, session, request, path):
            """One batch <=30; cumulative cycles and fifth-cycle SAVE never reset."""
            if getattr(self, "halted", None):
                raise RuntimeError("original failed response remains halted; observe/reconsume it first")
            self.current_attempt = None
            if self.initial_save is None or not self.checkpoint_bootstrap_verified:
                raise ValueError("full_loop requires actual verified cold canonical bootstrap")
            self.require_camera_pixel_admission()
            arguments = request.get("arguments", {})
            maximum = arguments.get("max_turns", 30) if isinstance(arguments, dict) else None
            if not isinstance(arguments, dict) or set(arguments) - {"max_turns"} or type(maximum) is not int or not 1 <= maximum <= 30:
                raise ValueError("each full_loop batch max_turns must be 1..30")
            control_sequence = self.consume_sequence(request)
            self.held_control = path.name
            self.loop_count += 1
            atomic(Q / f"INFLIGHT-{control_sequence:04d}.json", {"request": request, "control_only": True,
                   "batch": self.loop_count, "original_action_replay_allowed": False}, limit=16384)
            state = getattr(self, "full_loop_state", None)
            if state is None:
                initial, initial_path = await self.generated(session, METRICS)
                initial = frame(initial)
                state = self.full_loop_state = {"schema": "g2.queue.cumulative-loop/v1", "completed_cycles": 0,
                    "start_date_raw": initial["date_raw"], "before": initial, "before_metrics_response": str(initial_path),
                    "pending_cycle": None, "pending_checkpoint": None, "terminal": None,
                    "counts": {key: 0 for key in ("submitted_pending_turns", "lifestyle_material_verified_turns",
                        "existing_focus_verified_turns", "primitive_accepted_turns", "council_material_verified_turns",
                        "construction_material_verified_turns", "construction_start_verified_turns", "construction_completion_verified_turns",
                        "crown_material_verified_turns", "crown_receipt_nonmaterial_turns", "existing_typed_material_verified_turns",
                        "typed_nonmaterial_observation_turns", "date_advanced_turns", "checkpoint_saved", "checkpoint_deferred")}}
                self.persist_loop_state()
            if state["terminal"]:
                raise ValueError("cumulative run reached its retained terminal boundary")
            settled = 0
            while settled < maximum:
                self.guard()
                # Complete an already settled fifth cycle before any new AUTO.
                if state["pending_checkpoint"] is not None:
                    checkpoint = state["pending_checkpoint"]
                    if checkpoint.get("save_sequence") is not None:
                        raise ValueError("original SAVE unresolved; no repeated SAVE or new AUTO")
                    snapshot, snapshot_path = await self.generated(session, SEMANTIC)
                    actual = frame(snapshot, semantic=True, expected_lifecycle=self.expected_lifecycle_binding)
                    if any(actual[key] != state["before"][key] for key in ("date_raw", "actor_character_id", "episode_run_id")):
                        raise ValueError("cumulative safe-save frame differs from paired after metrics")
                    checkpoint["semantic_response"] = str(snapshot_path)
                    if isinstance(snapshot.get("active_event"), dict) or isinstance(snapshot.get("pending_character_interaction"), dict):
                        atomic(Q / f"CUMULATIVE-SAVE-{checkpoint['global_turn']:06d}.json", {"status": "deferred_player_decision",
                            "global_turn": checkpoint["global_turn"], "semantic_response": str(snapshot_path)}, limit=16384)
                        state["counts"]["checkpoint_deferred"] += 1
                        state["pending_checkpoint"] = None
                        self.persist_loop_state()
                    else:
                        checkpoint["save_sequence"] = self.next_sequence
                        self.persist_loop_state()
                        saved, save_path = await self.generated(session, SAVE, {"expected_revision": snapshot["revision"]})
                        self.finish_cumulative_checkpoint(saved, save_path)
                    if settled >= maximum:
                        break
                pending = state["pending_cycle"]
                if pending is None:
                    pending = state["pending_cycle"] = {"global_turn": state["completed_cycles"] + 1,
                        "before": state["before"], "before_metrics_response": state["before_metrics_response"],
                        "auto_sequence": self.next_sequence, "stage": "auto_unsettled"}
                    self.persist_loop_state()
                    turn, auto_path = await self.generated(session, AUTO)
                    plan = turn.get("plan") if isinstance(turn.get("plan"), dict) else {}
                    pending.update(stage="auto_verified", auto_response=str(auto_path), observation=dict(self.last_auto_observation),
                                   phase=plan.get("phase"), selected_step=turn.get("selected_step", plan.get("selected_step")),
                                   checkpoint_context=checkpoint_context_from_auto(turn))
                    self.persist_loop_state()
                elif pending["stage"] != "auto_verified":
                    raise ValueError("original AUTO unresolved; install reviewed classifier and reconsume original response, never resend")
                after_body, after_path = await self.generated(session, METRICS)
                after = frame(after_body)
                before = pending["before"]
                observation = pending["observation"]
                event = {**pending, "after": after, "after_metrics_response": str(after_path),
                         "date_delta_raw": after["date_raw"] - before["date_raw"], "business_success_inferred": False}
                for field, counter in (("submitted_pending", "submitted_pending_turns"),
                        ("lifestyle_material_verified", "lifestyle_material_verified_turns"),
                        ("existing_focus_verified", "existing_focus_verified_turns"), ("primitive_accepted", "primitive_accepted_turns"),
                        ("council_material_verified", "council_material_verified_turns"),
                        ("construction_material_verified", "construction_material_verified_turns"),
                        ("construction_start_verified", "construction_start_verified_turns"),
                        ("construction_completion_verified", "construction_completion_verified_turns"),
                        ("crown_material_verified", "crown_material_verified_turns"), ("crown_receipt_nonmaterial", "crown_receipt_nonmaterial_turns"),
                        ("existing_typed_material_verified", "existing_typed_material_verified_turns"),
                        ("typed_nonmaterial_observation", "typed_nonmaterial_observation_turns")):
                    state["counts"][counter] += int(observation.get(field) is True)
                state["counts"]["date_advanced_turns"] += int(event["date_delta_raw"] > 0)
                if after["date_raw"] < before["date_raw"]:
                    state["terminal"] = "actual_date_regressed"
                elif any(after[key] != before[key] for key in ("actor_character_id", "episode_run_id")):
                    state["terminal"] = "actual_actor_or_episode_changed_Root_checkpoint_handoff_required"
                event["cumulative_observation_counts"] = dict(state["counts"])
                atomic(Q / f"CUMULATIVE-TURN-{pending['global_turn']:06d}.json", event, limit=16384)
                state["completed_cycles"] = pending["global_turn"]
                state["before"], state["before_metrics_response"] = after, str(after_path)
                state["pending_cycle"] = None
                if checkpoint_after_settled_cycle(state, pending, after):
                    state["pending_checkpoint"] = {"global_turn": state["completed_cycles"], "save_sequence": None}
                elif state["completed_cycles"] % 5 == 0 and not state["terminal"]:
                    decision = dict(state.get("checkpoint_last_decision") or {})
                    readonly = decision.get("reason") == "unchanged_readonly_evidence_chain"
                    counter = "checkpoint_readonly_skipped" if readonly else "checkpoint_siege_interval_deferred"
                    state["counts"][counter] = state["counts"].get(counter, 0) + 1
                    prefix = "CUMULATIVE-READONLY-SAVE-SKIP" if readonly else "CUMULATIVE-SIEGE-SAVE-DEFER"
                    atomic(Q / f"{prefix}-{state['completed_cycles']:06d}.json", {
                        "status": decision.get("reason"), "global_turn": state["completed_cycles"],
                        "frame": after, "new_gameplay_mutations_observed": decision.get("dirty"),
                        "interval_settled_cycles": decision.get("interval_settled_cycles"),
                        "last_actual_checkpoint_retained": True}, limit=16384)
                self.persist_loop_state()
                settled += 1
                if state["terminal"]:
                    break
            # The final fifth cycle's checkpoint belongs to this batch, too.
            if state["pending_checkpoint"] is not None and not state["terminal"]:
                checkpoint = state["pending_checkpoint"]
                snapshot, snapshot_path = await self.generated(session, SEMANTIC)
                actual = frame(snapshot, semantic=True, expected_lifecycle=self.expected_lifecycle_binding)
                if any(actual[key] != state["before"][key] for key in ("date_raw", "actor_character_id", "episode_run_id")):
                    raise ValueError("final cumulative checkpoint frame differs")
                checkpoint["semantic_response"] = str(snapshot_path)
                if isinstance(snapshot.get("active_event"), dict) or isinstance(snapshot.get("pending_character_interaction"), dict):
                    atomic(Q / f"CUMULATIVE-SAVE-{checkpoint['global_turn']:06d}.json", {"status": "deferred_player_decision",
                        "global_turn": checkpoint["global_turn"], "semantic_response": str(snapshot_path)}, limit=16384)
                    state["counts"]["checkpoint_deferred"] += 1
                    state["pending_checkpoint"] = None
                    self.persist_loop_state()
                else:
                    checkpoint["save_sequence"] = self.next_sequence
                    self.persist_loop_state()
                    saved, save_path = await self.generated(session, SAVE, {"expected_revision": snapshot["revision"]})
                    self.finish_cumulative_checkpoint(saved, save_path)
            result = {"status": "bounded_loop_finished", "batch": self.loop_count, "actual_turns": settled,
                      "cumulative_cycles": state["completed_cycles"], "observation_counts": dict(state["counts"]),
                      "actual_calendar_days": (state["before"]["date_raw"] - state["start_date_raw"]) / 24,
                      "actual_end_date_raw": state["before"]["date_raw"], "reason": state["terminal"] or "batch_bound_reached",
                      "same_SDK_continuation_available": not bool(state["terminal"]), "next_sequence": self.next_sequence,
                      "campaign_complete_claimed": False, "replay_allowed": False}
            atomic(OUTBOX / path.name, {"request": request, "result": {"is_error": False, "structured_content": result}}, limit=16384)
            self.held_control = None
            return result
