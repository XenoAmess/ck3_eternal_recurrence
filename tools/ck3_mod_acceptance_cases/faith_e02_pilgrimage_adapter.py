"""Managed ordinary pilgrimage: native offers, finite planner, one Start, journey."""
from __future__ import annotations

from datetime import datetime, timezone
import importlib.util
import hashlib
import json
from pathlib import Path
from typing import TYPE_CHECKING
from ck3_mod_acceptance_native_day import (
    DayClient as PublicDayClient, native_day_request_count, obj, need,
)

if TYPE_CHECKING:
    from tools.ck3_mod_acceptance_cases.faith_e02_pilgrimage_observations import MilestoneObservation

CASE = "faith-engine-e02-d1-ordinary-pilgrimage-v1"
QUERY = "ck3_query_player_pilgrimage_planner_v1"
SUBMIT = "ck3_submit_player_pilgrimage_planner_v1"
IDENTITIES = "ck3_query_player_pilgrimage_activities_v1"
RELIGION = "ck3_query_player_religion_context_v1"
EXE_SHA256 = "98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518"


def require(value, message):
    if not value:
        raise ValueError(message)


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def sibling(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, "Selected finite helper is absent")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def validate_contract(context):
    c = context["case_contract"]
    require(c.get("schema") == "faith-engine-e02-d1-ordinary-pilgrimage-case-v1"
            and c.get("case") == context.get("case") == CASE
            and c.get("product") == context.get("product") == "faith-engine", "Ordinary case identity differs")
    spec = context["case_spec"]
    require(spec.get("opt_in_player_pilgrimage_execution") is True
            and {QUERY, SUBMIT} <= set(spec.get("required_mcp_tools", [])), "Independent execution opt-in is absent")
    require({RELIGION, IDENTITIES} <= set(spec.get("opt_in_read_only_mcp_tools", [])),
            "Original offers and hosted identities require explicit read permissions")
    require(c.get("profile") == {"enabled_mods": [], "product_files": []}, "Ordinary case requires vanilla profile")
    require(c.get("machine_id") not in {None, "", "unknown"}, "Explicit executing machine required")
    policy = c.get("policy", {})
    preferred = c.get("preferred_destination_id")
    require(preferred is None or type(preferred) is int and 0 < preferred < 2**32-1,
            "Optional preferred destination must be a positive full province ID")
    for key, low, high in (("reserve_gold_raw", 0, 2**63-1), ("max_journey_days", 1, 366),
                          ("max_day_requests", 1, 1024), ("max_events", 1, 256),
                          ("max_public_requests", 1, 1024),
                          ("one_day_timeout", 1, 300), ("quit_reserve_seconds", 90, 600)):
        require(type(policy.get(key)) is int and low <= policy[key] <= high, "Finite policy differs: " + key)
    return c


class BudgetedClient:
    """Count every original business control; snapshots/day calls count too."""
    def __init__(self, client: PublicDayClient, cap: int) -> None:
        need(type(cap) is int and cap > 0, "Finite public request cap must be a positive integer")
        self._client = client
        self.public_requests_cap = cap
        self.public_requests_used = 0

    def __getattr__(self, name):
        return getattr(self._client, name)

    def claim(self, count: int) -> None:
        need(type(count) is int and count > 0, "Public request count must be a positive integer")
        need(self.public_requests_used + count <= self.public_requests_cap,
             "Finite public request cap reached; preserve original results and normal Quit reserve")
        self.public_requests_used += count  # Unknown submissions remain consumed.

    def snapshot(self, **kwargs):
        self.claim(1)
        return self._client.snapshot(**kwargs)

    def advance_day(self, days: int = 1, timeout: float = 300,
                    allow_event_boundary: bool = False,
                    allow_actor_change: bool = False) -> dict[str, object]:
        # _client is the original CaseClient: its fresh snapshot does not pass
        # through this wrapper's snapshot(), so reserve both real tool calls here.
        report = obj(self._client.guard(90), "actual held report for request budget")
        self.claim(native_day_request_count(report, allow_actor_change=allow_actor_change))
        return self._client.advance_day(days, timeout, allow_event_boundary, allow_actor_change)

    def execute_plan(self, steps, *args, **kwargs):
        self.claim(len(steps))
        return self._client.execute_plan(steps, *args, **kwargs)


def prepare_case(context):
    from ck3_mod_acceptance import check_pin, pin
    from ck3_mod_acceptance_prepare import materialize_product_profile, finish_product_profile
    from ck3_live_run_id import current_machine_id
    c = validate_contract(context)
    require(current_machine_id() == c["machine_id"], "Executing machine differs")
    admission = context["case_inputs"]["storage_admission"]
    check_pin(Path(admission["path"]), admission)
    grant = read(admission["path"])
    require(grant.get("active") is True and grant.get("machine_id") == c["machine_id"]
            and datetime.now(timezone.utc) < datetime.fromisoformat(grant["expires_at_utc"].replace("Z", "+00:00")),
            "A fresh matching storage admission is required")
    saved = dict(context["saved_campaign"])
    require(saved == c["saved_input"], "Original saved input differs")
    actual = pin(Path(saved["save"]))
    require(actual["bytes"] == saved["bytes"] and actual["sha256"] == saved["sha256"], "Original save bytes differ")
    profile = materialize_product_profile(context, None, context["case_inputs"]["configuration"])
    profile = finish_product_profile(context, profile, provenance={
        "machine_id": c["machine_id"], "kind": "ordinary-pilgrimage-execution-preparation",
        "saved_input": saved, "storage_admission": admission, "preparation_mod_mounted": False,
        "world_actions_performed": False, "actual_restore_observed": False})
    return {"startup": {"mode": "saved_campaign", "state_dir": profile["state_dir"],
        "saved_campaign": {**saved, "product_inventory": profile["product_inventory"]["path"]}},
        "profile": profile, "initial_plan": context["case_spec"]["initial_plan"],
        "runtime_status": "NOT_RUN", "business_pass": False, "product_release_pass": False}


def frame_binding(frame, context, expected_actor):
    diagnostics, actor = frame["diagnostics"], frame["played_character"]
    hello = diagnostics["hello"]
    require(frame.get("paused") is True and frame.get("map_ready") is True
            and frame.get("source") == "injected-dll-named-pipe"
            and frame.get("backend_id") == "native-headless"
            and frame.get("episode_projection") == "native_campaign"
            and actor.get("alive") is True and actor.get("source") == "native"
            and actor.get("character_id") == expected_actor
            and hello.get("ck3_build_match") is True
            and hello.get("game_adapter_id") == "ck3-1.20.0.4-msvc-x64"
            and str(hello.get("expected_ck3_sha256", "")).lower() == EXE_SHA256,
            "Fresh exact4 paused native actor differs")
    pid, generation = diagnostics.get("bridge_pid"), diagnostics.get("connection_generation")
    require(type(pid) is int and pid > 0 and type(generation) is int and generation > 0
            and hello.get("pid") == pid and hello.get("connection_generation") == generation,
            "Fresh native process/generation differs")
    return {"run_id": context["run_id"], "machine_id": context["case_contract"]["machine_id"],
            "actor_character_id": expected_actor, "bridge_pid": pid,
            "connection_generation": generation, "episode_run_id": frame.get("episode_run_id")}


def choose_destination(result, actor, date_raw, preferred_destination_id=None):
    require(preferred_destination_id is None or type(preferred_destination_id) is int
            and 0 < preferred_destination_id < 2**32-1, "Invalid preferred destination ID")
    type_terms = result.get("player_pilgrimage_activity_type_terms")
    terms = result.get("player_pilgrimage_headless_activity_terms")
    routes = result.get("player_pilgrimage_candidate_routes")
    require(isinstance(type_terms, dict) and type_terms.get("available") is True
            and type_terms.get("can_plan") is True and isinstance(terms, dict)
            and terms.get("available") is True and terms.get("faith_id") == 13 and terms.get("rite_id") == 0
            and terms.get("single_location") is True and terms.get("configured_phase_count") == 1
            and terms.get("journey_cost_included") is False and isinstance(routes, list),
            "Fresh ordinary Catholic offers/CanPlan are unavailable")
    for item in (type_terms, terms, *routes):
        require(item.get("played_character_id") == actor and item.get("date_raw") == date_raw
                and item.get("capture_epoch") == terms.get("capture_epoch"), "Offer crossed its native context")
    valid_routes = {r["candidate_province_id"]: r for r in routes
                    if r.get("available") is True and r.get("route_valid") is True
                    and type(r.get("outbound_arrival_date_raw")) is int}
    choices = []
    for candidate in terms.get("candidates", []):
        province = candidate.get("province_id")
        quote = candidate.get("default_activity_quote")
        if (type(province) is not int or province <= 0 or province not in valid_routes
                or candidate.get("can_select") is not True
                or candidate.get("location_predicate", {}).get("value") is not True
                or candidate.get("same_province_cap_allows") is not True
                or candidate.get("total_cap_allows") is not True
                or not isinstance(quote, dict) or quote.get("affordable") is not True
                or quote.get("journey_cost_included") is not False):
            continue
        cost = quote.get("activity_gold_cost_raw")
        if type(cost) is not int or cost < 0:
            continue
        choices.append((valid_routes[province]["outbound_arrival_date_raw"], cost, province, candidate))
    require(choices, "No fresh selectable affordable destination with a native valid route")
    preferred_available = (any(item[2] == preferred_destination_id for item in choices)
                           if preferred_destination_id is not None else None)
    _, _, province, candidate = min(choices,
        key=lambda item: (item[2] != preferred_destination_id, *item[:3]))
    selected = {"province_id": province, "native_candidate": candidate, "native_local_route": valid_routes[province],
            "selection_policy": "earliest native outbound arrival, then activity-only gold, then province id",
            "journey_cost_known": False, "route_is_only_local_candidate": True, "can_start_inferred": False}
    if preferred_destination_id is not None:
        selected.update(preferred_destination_id=preferred_destination_id,
            preferred_destination_available=preferred_available,
            preferred_destination_selected=province == preferred_destination_id,
            preferred_destination_diagnostic=("fresh_eligible_preference_selected" if preferred_available
                else "preferred_not_in_fresh_eligible_choices_fallback_used"),
            selection_policy="fresh eligible preference, otherwise earliest native outbound arrival, activity-only gold, province id")
    return selected


def journey_limits(policy):
    return {"max_days": policy["max_journey_days"], "max_day_requests": policy["max_day_requests"],
            "max_events": policy["max_events"], "one_day_timeout": policy["one_day_timeout"],
            "quit_reserve_seconds": policy["quit_reserve_seconds"]}


def capture_checkpoint(context, client, name, request):
    response = client.root_checkpoint(name, {"machine_id": context["case_contract"]["machine_id"],
        "run_id": context["run_id"], "case": CASE, **request}, reserve=120)
    require(isinstance(response, dict) and response.get("run_id") == context["run_id"]
            and response.get("reviewer") == client.operator_reviewer and response.get("status") == "complete",
            "Root capture checkpoint is foreign or incomplete")
    client.checkpoint(name + "-validated", response)
    return response



def visual_observation_sha256(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=True,
        separators=(",", ":")).encode("utf-8")).hexdigest()


def require_root_visual_review(response, observation, approval_key):
    # A complete capture response alone cannot authorize a game mutation.
    require(response.get("original_image_directly_reviewed") is True
            and response.get(approval_key) is True
            and response.get("reviewed_native_observation_sha256") == visual_observation_sha256(observation),
            "Root must directly review this native observation and explicitly authorize " + approval_key)
    image = response.get("original_image")
    require(isinstance(image, dict) and isinstance(image.get("path"), str),
            "Root original PNG evidence is absent")
    path = Path(image["path"])
    require(path.is_absolute() and path.is_file() and not path.is_symlink(),
            "Root original PNG must be an actual absolute regular file")
    raw = path.read_bytes()
    require(raw.startswith(b"\x89PNG\r\n\x1a\n") and len(raw) == image.get("bytes")
            and hashlib.sha256(raw).hexdigest() == image.get("sha256"),
            "Root original PNG evidence changed or is not a PNG")


def drain_if_needed(context, client, binding, frame):
    if frame.get("active_event") is None and frame.get("pending_character_interaction") is None:
        return frame
    helper = sibling(Path(__file__).with_name("faith_e02_pilgrimage_journey.py"), "_faith_e02_pilgrimage_drain")
    observed = helper.drain_interruptions(context, client, binding, journey_limits(context["case_contract"]["policy"]))
    require(observed.get("status") == "INTERRUPTIONS_DRAINED" and isinstance(observed.get("last_frame"), dict),
            "Original native interruption outcome remains unresolved; never repeat its action")
    frame = observed["last_frame"]
    require(frame.get("active_event") is None and frame.get("pending_character_interaction") is None,
            "Native interruption still visible after original action")
    return frame


class Planner:
    def __init__(self, context, client, binding, start_date):
        self.context, self.client, self.binding, self.start_date = context, client, binding, start_date
        self.sequence = 0
        self.policy = sibling(Path(__file__).resolve().parents[1] / "faith_e02_pilgrimage_queue.py",
                              "_faith_e02_pilgrimage_finite_queue")

    def snapshot(self, *, same_date=True):
        frame = self.client.snapshot(require_event_free=False)
        frame = drain_if_needed(self.context, self.client, self.binding, frame)
        require(frame_binding(frame, self.context, self.binding["actor_character_id"]) == self.binding,
                "Actual owner changed during ordinary pilgrimage")
        require(not same_date or frame["date_raw"] == self.start_date, "Planner crossed paused date")
        return frame

    def call(self, tool, args=None):
        self.client.guard(self.context["case_contract"]["policy"]["quit_reserve_seconds"])
        self.snapshot()
        self.sequence += 1
        name = "ordinary-pilgrimage-" + str(self.sequence).zfill(4)
        step = {"id": name, "tool": tool, "args": args or {},
                "fresh_revision": True, "continue_on_error": True}
        self.policy.validate({"steps": [step]})
        row = self.client.execute_plan([step], name)[0]
        self.client.checkpoint(name + "-receipt", row)
        require(row.get("ok") is True and not row.get("error") and isinstance(row.get("result"), dict),
                "Original tool failed; retained request is never replayed: " + name)
        self.snapshot()
        return row["result"]

    def query(self, operation="read", **kwargs):
        return self.call(QUERY, {"operation": operation, **kwargs})

    def submit(self, operation, **kwargs):
        return self.call(SUBMIT, {"operation": operation, "policy_positive": True, **kwargs})


def require_planner(value, stage, province=None):
    require(value.get("operation_status") == "observed" and value.get("needs_recovery") is False
            and isinstance(value.get("planner"), dict), "Planner operation was not independently observed")
    planner = value["planner"]
    require(planner.get("stage") == stage and planner.get("selected_pious") is True,
            "Actual planner did not retain pious selection at expected stage")
    if province is not None:
        require(planner.get("destination_province_id") == province, "Actual selected destination differs")
    return planner


def run_case(context, client):
    c = validate_contract(context)
    client = BudgetedClient(client, c["policy"]["max_public_requests"])
    before = client.snapshot(require_event_free=False)
    binding = frame_binding(before, context, c["expected_actor_character_id"])
    client.checkpoint("ordinary-pilgrimage-first-native-frame", {"machine_id": c["machine_id"],
        "run_id": context["run_id"], "binding": binding, "frame": before,
        "prior_scene_date_is_expectation_only": c.get("prior_scene_date_raw")})
    milestone_observations: list[MilestoneObservation] = []
    result = {"schema": "faith-e02-ordinary-pilgrimage-result-v1", "machine_id": c["machine_id"],
        "run_id": context["run_id"], "case": CASE, "binding": binding,
        "status": "not_started", "start_intent_written": False, "start_invoked": False,
        "hosted_identity_observed": False, "journey": None, "needs_recovery": False,
        "journey_cost_known": False, "payment_total_proven": False,
        "absence_is_completion": False, "business_pass": False, "product_release_pass": False,
        "milestone_observations": milestone_observations}
    planner = Planner(context, client, binding, before["date_raw"])
    try:
        before = drain_if_needed(context, client, binding, before)
        require(frame_binding(before, context, c["expected_actor_character_id"]) == binding,
                "Initial interruption changed original actor or native owner")
        planner.start_date = before["date_raw"]
        identities = planner.call(IDENTITIES)
        require(identities.get("activity_count") == 0 and identities.get("activities") == [],
                "Existing hosted pilgrimage precludes a new once-only Start")
        offers = planner.call(RELIGION)
        destination = choose_destination(offers, binding["actor_character_id"], before["date_raw"], c.get("preferred_destination_id"))
        province = destination["province_id"]
        client.checkpoint("ordinary-pilgrimage-destination-policy", destination)
        capture_checkpoint(context, client, "ordinary-pilgrimage-record-before-planner", {
            "binding": binding, "date_raw": before["date_raw"], "actor_character_id": binding["actor_character_id"],
            "faith_id": 13, "rite_id": 0, "native_offers": offers, "destination": destination,
            "next_action": "Open original pious pilgrimage planner after recording is ready"})
        initial = planner.query()
        require(initial.get("ledger_state") == "idle" and initial.get("needs_recovery") is False,
                "Existing native submission ledger cannot be reset")
        opened = planner.submit("open")
        # Open's action DTO does not report selected_pious. A separate native
        # stage1 read below must independently observe the current selection.
        require(opened.get("operation_status") == "observed" and opened.get("invoked") is True
                and opened.get("needs_recovery") is False
                and isinstance(opened.get("planner"), dict)
                and opened["planner"].get("stage") == 1
                and opened["planner"].get("can_progress") is True,
                "Original Open was not observed at ready stage1")
        stage1 = planner.query(read_stage=1)
        require_planner(stage1, 1)
        reviewed_stage1 = capture_checkpoint(context, client, "ordinary-pilgrimage-review-stage1-before-confirm", {
            "binding": binding, "native_observation": stage1,
            "native_observation_sha256": visual_observation_sha256(stage1),
            "prepare_original_image": True, "approval_key": "confirm_once_authorized",
            "review_contract": "Root directly reviews original PNG and actual selected_pious=true at stage1; only explicit current-observation approval permits Confirm",
            "next_action": "Fresh native stage1 read, then one original pious Confirm"})
        require_root_visual_review(reviewed_stage1, stage1, "confirm_once_authorized")
        # The scene stayed paused for Root; reject changed selection after review.
        require_planner(planner.query(read_stage=1), 1)
        confirmed = planner.submit("confirm")
        require(confirmed.get("operation_status") == "observed" and not confirmed.get("needs_recovery"),
                "Pious confirmation was not observed")
        selectable = planner.query("can_select", province_id=province)
        require(selectable.get("operation_status") == "observed"
                and selectable.get("planner", {}).get("can_select") is True,
                "Original current planner rejects the fresh destination")
        selected = planner.submit("select", province_id=province)
        require(selected.get("operation_status") == "observed" and not selected.get("needs_recovery"),
                "Destination submission has unknown or rejected state")
        require_planner(planner.query(), 5, province)
        quoted = planner.query("quote")
        quote = quoted.get("quote")
        require(quoted.get("operation_status") == "observed" and isinstance(quote, dict)
                and quote.get("observed") is True and quote.get("planning_stage") == 5
                and quote.get("final_can_start_observed") is True and quote.get("final_can_start") is True
                and quote.get("unknown_positive_configured_cost") is False
                and quote.get("selected_option", {}).get("key") == "pilgrimage_type_pious",
                "Real configured full10 quote or final CanStart unavailable")
        client.checkpoint("ordinary-pilgrimage-final-configured-full10-quote", {
            "quote": quote, "journey_inclusion_proven": False,
            "native_final_canstart_required": True, "reserve_gold_raw": c["policy"]["reserve_gold_raw"],
            "policy": "retain explicit gold reserve; never present activity-only offer as all journey cost"})
        reviewed_quote = capture_checkpoint(context, client, "ordinary-pilgrimage-record-quote-before-start", {
            "binding": binding, "province_id": province, "quote": quote,
            "native_observation": quoted, "native_observation_sha256": visual_observation_sha256(quoted),
            "prepare_original_image": True, "approval_key": "start_once_authorized",
            "review_contract": "Root directly reviews original PNG and actual final configured price/CanStart/reserve; this quote is not a proven total journey cost",
            "reserve_gold_raw": c["policy"]["reserve_gold_raw"], "journey_cost_inclusion_proven": False,
            "next_action": "One original Start only after explicit Root review of this final native price"})
        require_root_visual_review(reviewed_quote, quoted, "start_once_authorized")
        observations = sibling(Path(__file__).with_name("faith_e02_pilgrimage_observations.py"),
                               "_faith_e02_pilgrimage_milestone_observations")
        observations.observe_milestone(context, client, binding, milestone_observations,
                                       "before-start")
        # The scene remains paused during capture coordination. Re-read the
        # actual destination and priced configuration before the one submission.
        require_planner(planner.query(), 5, province)
        latest = planner.query("quote")
        latest_quote = latest.get("quote")
        require(latest.get("operation_status") == "observed" and isinstance(latest_quote, dict)
                and latest_quote.get("final_can_start_observed") is True and latest_quote.get("final_can_start") is True
                and latest_quote.get("unknown_positive_configured_cost") is False,
                "Final native quote unavailable after capture checkpoint")
        for key in ("configured_cost_raw", "known_name_resource_indices", "named_cost_verified", "selected_option"):
            require(latest_quote.get(key) == quote.get(key), "Priced configuration changed after Root capture: " + key)
        quote = latest_quote
        wallet_before = planner.snapshot()
        client.checkpoint("ordinary-pilgrimage-start-once-intent", {"run_id": context["run_id"],
            "machine_id": c["machine_id"], "province_id": province, "quote": quote,
            "reserve_gold_raw": c["policy"]["reserve_gold_raw"], "attempt": 1,
            "unknown_result_policy": "never resubmit; query native persistent ledger and hosted identities only"})
        result["start_intent_written"] = True
        # This is the only Start call in this case. Any exception leaves the
        # durable intent unresolved; neither this adapter nor Python retries it.
        start = None
        try:
            start = planner.submit("start", province_id=province,
                reserve_gold_raw=c["policy"]["reserve_gold_raw"])
        except Exception as error:
            result.update(status="start_outcome_unknown", needs_recovery=True,
                start_acknowledgement_missing=True, start_response_error=type(error).__name__ + ": " + str(error))
        result["start_invoked"] = start is not None and start.get("invoked") is True
        result["start_response"] = start
        if start is not None:
            result["needs_recovery"] = start.get("needs_recovery") is True
            require(result["start_invoked"], "Original Start was rejected before native invocation")
        identity = None
        post_failures = []
        for _ in range(4):
            try:
                post = planner.query("post")
            except Exception as error:
                post_failures.append(type(error).__name__ + ": " + str(error))
                continue
            client.checkpoint("ordinary-pilgrimage-post-" + str(planner.sequence), post)
            if post.get("operation_status") == "identity_observed" and isinstance(post.get("new_identity"), dict):
                identity = post["new_identity"]
                break
            if post.get("operation_status") not in {"post_pending", "unavailable"}:
                post_failures.append("Native post observer: " + str(post.get("operation_status")))
                break
        result["post_observation_failures"] = post_failures
        hosted = None
        try:
            hosted = planner.call(IDENTITIES)
        except Exception as error:
            result["independent_hosted_read_error"] = type(error).__name__ + ": " + str(error)
        wallet_after = None
        try:
            wallet_after = planner.snapshot()
        except Exception as error:
            result["wallet_post_read_error"] = type(error).__name__ + ": " + str(error)
        client.checkpoint("ordinary-pilgrimage-post-start-wallet-observation", {
            "before": {k: wallet_before.get(k) for k in ("played_character_gold", "played_character_piety", "native_revision", "date_raw")},
            "after": {k: wallet_after.get(k) for k in ("played_character_gold", "played_character_piety", "native_revision", "date_raw")} if wallet_after else None,
            "payment_total_proven": False, "hosted_identity": identity})
        rows = hosted.get("activities", []) if isinstance(hosted, dict) else []
        ledger_reconciled = identity is not None
        if identity is None and len(rows) == 1:
            observed = rows[0]
            if (observed.get("host_character_id") == binding["actor_character_id"]
                    and observed.get("type_key") == "activity_pilgrimage"):
                identity = observed
        require(identity is not None and any(row == identity for row in rows),
                "Native new identity remains pending or independent full identity is absent; Start is never retried")
        result.update(status="hosted_identity_observed", hosted_identity_observed=True,
            hosted_identity=identity, native_ledger_state_reconciled=ledger_reconciled,
            needs_recovery=not ledger_reconciled)
        capture_checkpoint(context, client, "ordinary-pilgrimage-start-observed-take", {
            "binding": binding, "hosted_identity": identity, "start_response": start,
            "start_acknowledgement_missing": result.get("start_acknowledgement_missing", False),
            "native_ledger_state_reconciled": ledger_reconciled, "next_action": "Finish start take, then natural journey"})
        journey = sibling(Path(__file__).with_name("faith_e02_pilgrimage_journey.py"), "_faith_e02_pilgrimage_journey")
        limits = journey_limits(c["policy"])
        result["journey"] = journey.run_journey(context, client, binding, identity, limits)
        result["status"] = result["journey"]["status"]
        # Native terminal fields, event effects, travel return and payment are
        # separate evidence. The public lifecycle verifier closes the scene.
    except Exception as error:
        result["failure"] = type(error).__name__ + ": " + str(error)
        response = result.get("start_response")
        known_rejected = (isinstance(response, dict) and response.get("invoked") is False
                          and response.get("needs_recovery") is False)
        if result["start_intent_written"] and not result["hosted_identity_observed"] and not known_rejected:
            result["needs_recovery"] = True
        if result["status"] == "not_started":
            result["status"] = "capability_or_legality_blocked"
    finally:
        result["public_requests_used"] = client.public_requests_used
        result["public_requests_cap"] = client.public_requests_cap
        result["public_request_scope"] = "all adapter and journey submitted controls, including snapshots and day requests"
        client.checkpoint("ordinary-pilgrimage-result", result)
    return result


def verify_case(context):
    c = validate_contract(context)
    result = read(Path(context["output"]) / "ordinary-pilgrimage-result.json")
    require(result.get("machine_id") == c["machine_id"] and result.get("case") == CASE
            and result.get("run_id") == context["run_id"], "Actual result crossed public case")
    return {"status": result["status"], "hosted_identity_observed": result["hosted_identity_observed"],
            "journey": result["journey"], "needs_recovery": result["needs_recovery"],
            "public_requests_used": result["public_requests_used"], "public_requests_cap": result["public_requests_cap"],
            "payment_total_proven": False, "absence_is_completion": False,
            "business_pass": False, "product_release_pass": False}
