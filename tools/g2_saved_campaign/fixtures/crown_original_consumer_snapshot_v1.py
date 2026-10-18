"""Test-only snapshot of the complete original Crown consumer.

The prototype tests need an independent full consumer, including exact quote,
ID/build/frame, resource, law and successor verification. This is not a new
production policy or a native runtime qualification. Hosts supply their own
complete original consumer to the production adapter.
"""
import json
CROWN_SUBMIT = 'enact-realm-law-crown-v1-private'
CROWN_RECEIPT = 'verify-realm-law-crown-v1-private'
ORIGINAL_OWNER_SOURCE_SHA256 = '8ea8bbb1700971552e4e14b6fe38f512c66d8de5997908c77c1ea6edc42d0a1c'
ORIGINAL_CONSUMER_AST_SHA256 = '7d98783df3b1cf105cc4892ed380ebf0d20a7d5bb9383ffa1358f4e159871a3a'

def classify_governance_with_crown_base_v1(body, *, state=None, initial_frame=None, game_pid=None):
    """Compose strict Crown consumption with the unchanged governance classifier."""
    plan = body.get("plan") if isinstance(body.get("plan"), dict) else {}
    step = body.get("selected_step", plan.get("selected_step"))
    if step not in {CROWN_SUBMIT, CROWN_RECEIPT}:
        return classify_governance_auto_outcome_v1(body, state=state, initial_frame=initial_frame)
    from dataclasses import asdict
    from xar_autoplayer.crown_authority_policy_v1 import choose_crown_authority_upgrade_v1
    from xar_autoplayer.bridge.realm_law_formal_private_transport import _valid_observation, _valid_titles
    from xar_autoplayer.bridge.version_identity import require_exact_native_build

    def require(condition, reason):
        if not condition:
            raise ValueError("ordinary Crown result rejected: " + reason)

    def integer(value):
        return type(value) is int and -(1 << 63) <= value < (1 << 63)

    def positive(value):
        return type(value) is int and value > 0

    def charges(value):
        require(isinstance(value, list) and len(value) <= 6, "bounded resource charges unavailable")
        result = {}
        for row in value:
            require(isinstance(row, dict) and row.get("currency_key") in {"gold", "prestige", "piety", "influence", "merit"}
                    and row["currency_key"] not in result
                    and all(integer(row.get(key)) for key in ("cost_raw", "pre_balance_raw", "post_balance_raw"))
                    and row["cost_raw"] >= 0 and row["pre_balance_raw"] >= row["cost_raw"], "resource charge malformed")
            result[row["currency_key"]] = row
        return result

    inner = body.get("result")
    require(body.get("status") == "executed" and isinstance(inner, dict)
            and plan.get("selected_step") == step, "typed Service outcome unavailable")
    require(isinstance(initial_frame, dict) and positive(initial_frame.get("actor_character_id"))
            and isinstance(initial_frame.get("episode_run_id"), str) and positive(game_pid), "admitted campaign generation unavailable")
    actor, episode = initial_frame["actor_character_id"], initial_frame["episode_run_id"]
    require(inner.get("schema") == "realm-law-crown-formal-private-v1", "typed schema differs")
    exact_build = require_exact_native_build(inner.get("exact_ck3_build"), inner.get("exe_sha256"))
    state = json.loads(json.dumps(state or {"council_pending": None, "construction_actions": {}}))
    tracked = state.get("crown_pending")
    record = {"schema": "g2.queue.ordinary-result-credit/v1", "selected_step": step,
              "service_status": body["status"], "result_status": inner.get("status"),
              "submitted_pending": False, "lifestyle_material_verified": False,
              "existing_focus_verified": False, "primitive_accepted": False,
              "council_material_verified": False, "construction_material_verified": False,
              "construction_start_verified": False, "construction_completion_verified": False,
              "crown_material_verified": False, "crown_receipt_nonmaterial": False,
              "business_success_inferred": False, "replay_allowed": False}
    if step == CROWN_SUBMIT:
        require(tracked is None, "unresolved original Crown action already tracked")
        readback = plan.get("crown_readback")
        require(isinstance(readback, dict) and readback.get("schema") == "realm-law-crown-action-private-read-v1"
                and readback.get("read_only") is True and readback.get("advertised") is False
                and readback.get("player_character_id") == actor
                and positive(readback.get("queried_native_revision")) and positive(readback.get("queried_revision")),
                "selected source readback unavailable")
        before = {"native_revision": readback["queried_native_revision"], "date_raw": readback.get("date_raw"),
                  "played_character": {"character_id": actor}}
        require(_valid_observation(readback, before), "production paused observation contract failed")
        require(require_exact_native_build(readback.get("exact_ck3_build"), readback.get("exe_sha256")) == exact_build,
                "source and ACK exact build differ")
        choice = choose_crown_authority_upgrade_v1(readback)
        normalized_choice = json.loads(json.dumps(asdict(choice)))
        require(choice.status == "ready" and plan.get("crown_decision") == normalized_choice
                and plan.get("crown_observation_consumed") is True, "selected native-final quote differs")
        request_id = inner.get("submitted_request_id")
        require(isinstance(request_id, str) and request_id.startswith("crown-formal-") and len(request_id.encode()) <= 63,
                "original submitted action ID unavailable")
        require(inner.get("status") == "submitted_verification_pending" and inner.get("verification_pending") is True
                and inner.get("material_result") is False and inner.get("failure") == "none"
                and inner.get("player_character_id") == actor and inner.get("group_key") == "crown_authority"
                and inner.get("requested_law_key") == choice.law_key
                and inner.get("previous_effective_law_key") == readback["active_law_key"]
                and inner.get("pre_public_revision") == readback["queried_native_revision"]
                and inner.get("pre_native_revision") == readback["native_snapshot_revision"]
                and inner.get("pre_proof_epoch") == readback["proof_epoch"]
                and inner.get("pre_date_raw") == readback["date_raw"]
                and _valid_titles(inner.get("title_successors")), "pending ACK source/target/frame mismatch")
        quoted = dict(choice.budgets_raw)
        debit = charges(inner.get("charges"))
        balances = {row["currency_key"]: row["amount_raw"] for row in readback["resources"]}
        require(set(debit) == set(quoted)
                and all(row["cost_raw"] == quoted[key] and row["pre_balance_raw"] == balances[key] for key, row in debit.items()),
                "pending charges differ from exact source quote")
        state["crown_pending"] = {"action_id": request_id, "law_key": choice.law_key,
            "actor_character_id": actor, "episode_run_id": episode, "game_pid": game_pid,
            "readback": readback, "choice": normalized_choice, "ack": inner,
            "pre_native_revision": readback["queried_native_revision"], "pre_date_raw": readback["date_raw"]}
        record.update(category="crown_submission_pending", submitted_pending=True, material_verified=False,
                      action_request_id=request_id, requested_law_key=choice.law_key)
    else:
        pending = plan.get("crown_pending_action")
        require(isinstance(tracked, dict) and isinstance(pending, dict), "original pending Crown action not tracked")
        require(tracked["actor_character_id"] == actor and tracked["episode_run_id"] == episode and tracked["game_pid"] == game_pid,
                "tracked actor/episode/generation differs")
        require(pending.get("stage") == "receipt_pending"
                and pending.get("action_id") == tracked["action_id"] and inner.get("submitted_request_id") == tracked["action_id"]
                and pending.get("law_key") == tracked["law_key"]
                and pending.get("actor_character_id") == actor and pending.get("episode_run_id") == episode
                and pending.get("source_context") == {"bridge_pid": game_pid, "episode_run_id": episode}
                and plan.get("crown_cold_recovery") is False
                and all(pending.get(key) == tracked[key] for key in ("readback", "choice", "ack", "pre_native_revision", "pre_date_raw"))
                and pending.get("budgets") == dict(tracked["choice"]["budgets_raw"]),
                "receipt original ID/target/source/frame mismatch")
        ack = tracked["ack"]
        require(inner.get("exact_ck3_build") == ack["exact_ck3_build"] and inner.get("exe_sha256") == ack["exe_sha256"],
                "receipt exact build differs")
        pairs = (("post_public_revision", "pre_public_revision"), ("post_native_revision", "pre_native_revision"),
                 ("post_proof_epoch", "pre_proof_epoch"), ("post_date_raw", "pre_date_raw"))
        require(all(integer(inner.get(post)) and inner[post] >= ack[pre] for post, pre in pairs)
                and any(inner[post] > ack[pre] for post, pre in pairs), "independent newer paused proof unavailable")
        require(_valid_titles(inner.get("title_successors")), "independent successor material unavailable")
        if inner.get("status") == "enacted":
            require(inner.get("material_result") is True and inner.get("failure") == "none"
                    and inner.get("effective_law_key") == tracked["law_key"]
                    and all(inner.get(key) is True for key in ("effective_law_verified", "resources_verified", "succession_verified")),
                    "independent active law/resource/succession not verified")
            before_debits, after_debits = charges(ack["charges"]), charges(inner.get("charges"))
            require(set(before_debits) == set(after_debits)
                    and all(after_debits[key]["cost_raw"] == old["cost_raw"]
                            and after_debits[key]["pre_balance_raw"] == old["pre_balance_raw"]
                            and after_debits[key]["post_balance_raw"] == old["pre_balance_raw"] - old["cost_raw"]
                            for key, old in before_debits.items()), "independent exact resource debit differs")
            state["crown_pending"] = None
            record.update(category="crown_material_verified", crown_material_verified=True, material_verified=True,
                          effective_law_key=inner["effective_law_key"], source="independent native enact receipt")
        else:
            # The existing consumer deliberately keeps this original action pending.
            # Only this independently observed negative has a complete later law frame.
            require(inner.get("status") == "failed" and inner.get("failure") == "effective_law_not_enacted"
                    and inner.get("material_result") is False and inner.get("effective_law_key") != tracked["law_key"]
                    and all(inner.get(key) is False for key in ("effective_law_verified", "resources_verified", "succession_verified")),
                    "unknown/partial Crown receipt remains halted")
            record.update(category="crown_independent_not_enacted", crown_receipt_nonmaterial=True,
                          material_verified=False, original_action_still_pending=True)
        record.update(action_request_id=tracked["action_id"], requested_law_key=tracked["law_key"],
                      post_public_revision=inner["post_public_revision"], post_native_revision=inner["post_native_revision"],
                      post_proof_epoch=inner["post_proof_epoch"], post_date_raw=inner["post_date_raw"])
    return record, state
