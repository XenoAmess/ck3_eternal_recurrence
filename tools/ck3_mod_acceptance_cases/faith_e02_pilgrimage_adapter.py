"""Managed ordinary pilgrimage: native offers, finite planner, one Start, journey."""
from __future__ import annotations
from ck3_mod_acceptance_saved_profile_v2 import materialize_saved_profile_v2

from datetime import datetime, timezone
import importlib.util
import hashlib
import json
from pathlib import Path
from typing import TYPE_CHECKING, Protocol
from ck3_mod_acceptance_native_day import (
    DayClient as PublicDayClient, native_day_request_count, obj, need, integer,
)

if TYPE_CHECKING:
    from tools.ck3_mod_acceptance_cases.faith_e02_pilgrimage_observations import MilestoneObservation
    from ck3_mod_acceptance_client import CaseClient

JSONObject = dict[str, object]

CASE = "faith-engine-e02-d1-ordinary-pilgrimage-v1"
MECHANISM_CASE = "faith-engine-e02-pilgrimage-mechanism-v2"
QUERY = "ck3_query_player_pilgrimage_planner_v1"
SUBMIT = "ck3_submit_player_pilgrimage_planner_v1"
IDENTITIES = "ck3_query_player_pilgrimage_activities_v1"
RELIGION = "ck3_query_player_religion_context_v1"
EXE_SHA256 = "98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518"


def require(value: object, message: str) -> None:
    if not value:
        raise ValueError(message)


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def sibling(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ValueError("Selected finite helper is absent")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def validate_contract(context: JSONObject) -> JSONObject:
    from tools.ck3_mod_acceptance_cases.faith_e02_pilgrimage_contract import (
        pilgrimage_identity, pilgrimage_policy_caps, pilgrimage_natural_advance_mode, pilgrimage_resume,
        verify_pilgrimage_resume_origin)
    c = obj(context["case_contract"], "pilgrimage case contract")
    identity = pilgrimage_identity(c)
    resume = pilgrimage_resume(c)
    if resume is not None:
        verify_pilgrimage_resume_origin(resume, identity=identity,
            machine_id=str(c.get("machine_id")), run_id=str(context.get("run_id")),
            preferred_destination_id=c.get("preferred_destination_id"))
    caps = pilgrimage_policy_caps(identity.case)
    require(c.get("case") == context.get("case") == identity.case
            and c.get("product") == context.get("product") == "faith-engine", "Ordinary case identity differs")
    spec = obj(context["case_spec"], "pilgrimage case specification")
    require(spec.get("opt_in_player_pilgrimage_execution") is True
            and {QUERY, SUBMIT} <= set(spec.get("required_mcp_tools", [])), "Independent execution opt-in is absent")
    require({RELIGION, IDENTITIES} <= set(spec.get("opt_in_read_only_mcp_tools", [])),
            "Original offers and hosted identities require explicit read permissions")
    saved = obj(c.get("saved_input", {}), "pilgrimage saved input")
    require(type(saved.get("player_id")) is int and saved["player_id"] == identity.actor_character_id
            and type(saved.get("date_raw")) is int and saved["date_raw"] == identity.date_raw,
            "Frozen saved input actor/date differ from mechanism identity")
    require(c.get("profile") == {"enabled_mods": [], "product_files": []}, "Ordinary case requires vanilla profile")
    scope = obj(c.get("scope", {}), "pilgrimage scope")
    if "new_save_allowed" in scope:
        require(type(scope["new_save_allowed"]) is bool, "Save scope must be an explicit boolean")
    if scope.get("new_save_allowed") is True:
        require(identity.case == MECHANISM_CASE and "ck3_save_checkpoint" in spec.get("required_mcp_tools", []),
                "Only the v2 mechanism case can explicitly opt in to an original continuation save")
    require(c.get("machine_id") not in {None, "", "unknown"}, "Explicit executing machine required")
    policy = obj(c.get("policy", {}), "pilgrimage finite policy")
    if pilgrimage_natural_advance_mode(identity.case, policy) == "native_horizon":
        require({"ck3_get_capabilities", "ck3_execute_step"} <= set(spec.get("required_mcp_tools", [])),
                "Native horizon requires its actual public capability query and existing execute tool")
    preferred = c.get("preferred_destination_id")
    require(preferred is None or type(preferred) is int and 0 < preferred < 2**32-1,
            "Optional preferred destination must be a positive full province ID")
    for key, low, high in (("reserve_gold_raw", 0, 2**63-1), ("max_journey_days", 1, caps.max_days),
                          ("max_day_requests", 1, caps.max_day_requests), ("max_events", 1, 256),
                          ("max_public_requests", 1, caps.max_public_requests),
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
    from ck3_mod_acceptance_prepare import finish_product_profile
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
    profile = materialize_saved_profile_v2(context, None, context["case_inputs"]["configuration"], source_role=None)
    profile = finish_product_profile(context, profile, provenance={
        "machine_id": c["machine_id"], "kind": "ordinary-pilgrimage-execution-preparation",
        "saved_input": saved, "storage_admission": admission, "preparation_mod_mounted": False,
        "world_actions_performed": False, "actual_restore_observed": False})
    return {"startup": {"mode": "saved_campaign", "state_dir": profile["state_dir"],
        "saved_campaign": {**saved, "product_inventory": profile["product_inventory"]["path"]}},
        "profile": profile, "initial_plan": context["case_spec"]["initial_plan"],
        "runtime_status": "NOT_RUN", "business_pass": False, "product_release_pass": False}


def frame_binding(frame: JSONObject, context: JSONObject, expected_actor: int) -> JSONObject:
    diagnostics, actor = obj(frame["diagnostics"], "native diagnostics"), obj(frame["played_character"], "native actor")
    hello = obj(diagnostics["hello"], "native hello")
    require(frame.get("paused") is True and frame.get("map_ready") is True
            and frame.get("source") == "injected-dll-named-pipe"
            and frame.get("backend_id") == "native-headless"
            and frame.get("episode_projection") == "native_campaign"
            and actor.get("alive") is True and actor.get("source") == "native"
             and type(actor.get("character_id")) is int
            and actor.get("character_id") == expected_actor
            and hello.get("ck3_build_match") is True
            and hello.get("game_adapter_id") == "ck3-1.20.0.4-msvc-x64"
            and str(hello.get("expected_ck3_sha256", "")).lower() == EXE_SHA256,
            "Fresh exact4 paused native actor differs")
    pid, generation = diagnostics.get("bridge_pid"), diagnostics.get("connection_generation")
    require(type(pid) is int and pid > 0 and type(generation) is int and generation > 0
            and hello.get("pid") == pid and hello.get("connection_generation") == generation,
            "Fresh native process/generation differs")
    return {"run_id": context["run_id"], "machine_id": obj(context["case_contract"], "case contract")["machine_id"],
            "actor_character_id": expected_actor, "bridge_pid": pid,
            "connection_generation": generation, "episode_run_id": frame.get("episode_run_id")}


def choose_destination(result: JSONObject, actor: int, date_raw: int,
                       preferred_destination_id: int | None = None,
                       expected_faith_id: int = 13, expected_rite_id: int | None = 0) -> JSONObject:
    require(preferred_destination_id is None or type(preferred_destination_id) is int
            and 0 < preferred_destination_id < 2**32-1, "Invalid preferred destination ID")
    type_terms = result.get("player_pilgrimage_activity_type_terms")
    terms = result.get("player_pilgrimage_headless_activity_terms")
    routes = result.get("player_pilgrimage_candidate_routes")
    if not isinstance(type_terms, dict) or not isinstance(terms, dict) or not isinstance(routes, list):
        raise ValueError("Native pilgrimage offers require typed term objects and route list")
    require(isinstance(type_terms, dict) and type_terms.get("available") is True
            and type_terms.get("can_plan") is True and isinstance(terms, dict)
            and terms.get("available") is True and type(terms.get("faith_id")) is int
            and terms.get("faith_id") == expected_faith_id and "rite_id" in terms
            and terms.get("rite_id") == expected_rite_id
            and (terms.get("rite_id") is None or type(terms.get("rite_id")) is int)
            and terms.get("single_location") is True and terms.get("configured_phase_count") == 1
            and terms.get("journey_cost_included") is False and isinstance(routes, list),
             "Fresh frozen-faith pilgrimage offers/CanPlan are unavailable")
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


def capture_checkpoint(context: JSONObject, client: CaseClient, name: str, request: JSONObject) -> JSONObject:
    response = client.root_checkpoint(name, {"machine_id": obj(context["case_contract"], "case contract")["machine_id"],
        "run_id": context["run_id"], "case": context["case"], **request}, reserve=120)
    response = obj(response, "Root pilgrimage checkpoint response")
    require(response.get("run_id") == context["run_id"]
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
        from tools.ck3_mod_acceptance_cases.faith_e02_pilgrimage_contract import pilgrimage_identity
        self.identity = pilgrimage_identity(context["case_contract"])
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
        return self.call(QUERY, {"operation": operation, "option_key": self.identity.option_key, **kwargs})

    def submit(self, operation, **kwargs):
        return self.call(SUBMIT, {"operation": operation, "option_key": self.identity.option_key,
                                  "policy_positive": True, **kwargs})


def require_planner(value: JSONObject, stage: int, province: int | None = None,
                    option_key: str = "pilgrimage_type_pious") -> JSONObject:
    require(value.get("operation_status") == "observed" and value.get("needs_recovery") is False
            and isinstance(value.get("planner"), dict), "Planner operation was not independently observed")
    planner = obj(value["planner"], "native pilgrimage planner")
    require(planner.get("stage") == stage and planner.get("selected_option_key") == option_key,
            "Actual planner did not retain the requested original option at expected stage")
    if province is not None:
        require(planner.get("destination_province_id") == province, "Actual selected destination differs")
    return planner


class ResumeReadClient(Protocol):
    output: Path

    def execute_plan(self, steps: list[JSONObject], name: str) -> object: ...
    def checkpoint(self, name: str, value: JSONObject) -> object: ...


def resume_native_identity(context: JSONObject, client: ResumeReadClient, binding: JSONObject,
        before: JSONObject) -> tuple[JSONObject, JSONObject, tuple[str, ...], int]:
    """Read only, before any drain/advance: bind the cold owner to one saved activity."""
    from tools.ck3_mod_acceptance_cases.faith_e02_pilgrimage_contract import (
        pilgrimage_identity, pilgrimage_resume, verify_pilgrimage_resume_origin)
    c = obj(context["case_contract"], "resume case")
    identity = pilgrimage_identity(c)
    resume = pilgrimage_resume(c)
    if resume is None:
        raise ValueError("explicit resume_existing required")
    origin = verify_pilgrimage_resume_origin(resume, identity=identity,
        machine_id=str(c["machine_id"]), run_id=str(context["run_id"]),
        preferred_destination_id=c.get("preferred_destination_id"))
    require(binding["bridge_pid"] != origin.bridge_pid,
            "Resume requires a new cold native process, never the predecessor PID")
    hello = obj(obj(before.get("diagnostics"), "resume diagnostics").get("hello"), "resume hello")
    require(hello.get("expected_ck3_version") == "1.20.0.4", "Resume requires the exact native game version")
    require({"active_event", "pending_character_interaction"} <= before.keys()
            and before["active_event"] is None and before["pending_character_interaction"] is None,
            "Resume saved postcondition must restore a modal-free native frame before any drain")
    sources: list[JSONObject] = []
    observed: JSONObject = {}
    for name, tool in (("pilgrimage-resume-religion", RELIGION), ("pilgrimage-resume-identity", IDENTITIES)):
        revision = integer(before.get("revision"), "resume revision")
        native_revision = integer(before.get("native_revision"), "resume native revision")
        submitted = client.execute_plan([{"id": name, "tool": tool, "fresh_revision": False,
            "args": {"expected_revision": revision}}], name)
        if not isinstance(submitted, list) or len(submitted) != 1:
            raise ValueError("Resume query requires one actual result")
        row = obj(submitted[0], "resume actual query row")
        require(row.get("ok") is True and not row.get("error"), "Resume readonly query failed")
        value = obj(row.get("result"), "resume native readonly value")
        after = obj(row.get("after_snapshot"), "resume native query after-frame")
        integer(after.get("revision"), "resume query after revision")
        integer(after.get("native_revision"), "resume query after native revision")
        require(frame_binding(after, context, identity.actor_character_id) == binding
                and after.get("date_raw") == identity.date_raw and type(after.get("date_raw")) is int
                and {"active_event", "pending_character_interaction"} <= after.keys()
                and after["active_event"] is None and after["pending_character_interaction"] is None,
                "Resume query crossed its cold owner/date or published a modal; no action submitted")
        require(value.get("read_only") is True and value.get("queried_revision") == revision
                and type(value.get("queried_revision")) is int
                and value.get("snapshot_revision") == native_revision
                and type(value.get("snapshot_revision")) is int
                and value.get("date_raw") == identity.date_raw and type(value.get("date_raw")) is int
                and value.get("played_character_id") == identity.actor_character_id
                and type(value.get("played_character_id")) is int,
                "Resume readonly result lacks the exact current native scope")
        if tool == RELIGION:
            require(value.get("available") is True and type(value.get("faith_id")) is int
                    and value["faith_id"] == identity.faith_id and "rite_id" in value
                    and (value["rite_id"] is None if identity.rite_id is None else
                         type(value["rite_id"]) is int and value["rite_id"] == identity.rite_id),
                    "Resume actual Faith/Rite differs from saved expected identity")
        else:
            rows = value.get("activities")
            require(value.get("schema") == "ck3_12004_player_pilgrimage_activities_v1"
                    and value.get("scope") == "currently-hosted-by-current-player"
                    and value.get("activity_type_key") == "activity_pilgrimage"
                    and value.get("absence_is_completion") is False
                    and type(value.get("activity_count")) is int and value["activity_count"] == 1
                    and isinstance(rows, list) and len(rows) == 1,
                    "Resume requires exactly one actual currently hosted pilgrimage")
            observed = obj(rows[0], "actual resumed activity")
            require(all(type(observed.get(k)) is type(v) and observed.get(k) == v
                        for k, v in resume.activity_json().items()), "Resume full activity identity differs")
        source_path = client.output / (name + ".actual-results.json")
        raw = source_path.read_bytes()
        sources.append({"path": str(source_path), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()})
        before = after
    elapsed = identity.date_raw - origin.start_date_raw
    proof: JSONObject = {"entry_mode": "resume_existing", "predecessor_run_id": resume.predecessor_run_id,
        "original_start": dict(resume.original_start), "predecessor_runtime": dict(resume.predecessor_runtime),
        "predecessor_source_commit": origin.source_commit, "binding": binding,
        "activity": resume.activity_json(), "source_pins": sources, "prior_elapsed_hours": elapsed,
        "consumed_event_definitions": list(origin.consumed_event_definitions), "start_replayed": False,
        "consumed_event_instance_ids_not_reused_across_processes": True}
    client.checkpoint("pilgrimage-resume-native-identity", proof)
    return resume.activity_json(), proof, origin.consumed_event_definitions, elapsed


def run_case(context: JSONObject, client: CaseClient) -> JSONObject:
    from tools.ck3_mod_acceptance_cases.faith_e02_pilgrimage_contract import (
        pilgrimage_identity, pilgrimage_natural_advance_mode, require_pilgrimage_natural_capabilities,
        pilgrimage_resume)
    c = validate_contract(context)
    mechanism = pilgrimage_identity(c)
    resume = pilgrimage_resume(c)
    policy = obj(c["policy"], "finite policy")
    client = BudgetedClient(client, integer(policy["max_public_requests"], "request cap"))
    before = client.snapshot(require_event_free=False)
    require(type(before.get("date_raw")) is int and before["date_raw"] == mechanism.date_raw,
            "Actual restored date differs from frozen saved input")
    binding = frame_binding(before, context, mechanism.actor_character_id)
    client.checkpoint("ordinary-pilgrimage-first-native-frame", {"machine_id": c["machine_id"],
        "run_id": context["run_id"], "binding": binding, "frame": before,
        "prior_scene_date_is_expectation_only": c.get("prior_scene_date_raw")})
    milestone_observations: list[MilestoneObservation] = []
    result = {"schema": "faith-e02-ordinary-pilgrimage-result-v1", "machine_id": c["machine_id"],
        "run_id": context["run_id"], "case": context["case"], "binding": binding,
        "status": "not_started", "start_intent_written": False, "start_invoked": False,
        "hosted_identity_observed": False, "journey": None, "needs_recovery": False,
        "journey_cost_known": False, "payment_total_proven": False,
        "absence_is_completion": False, "business_pass": False, "product_release_pass": False,
        "milestone_observations": milestone_observations}
    planner = Planner(context, client, binding, before["date_raw"])
    natural_capabilities: JSONObject | None = None
    consumed_event_definitions: tuple[str, ...] = ()
    prior_elapsed_hours = 0
    try:
        if pilgrimage_natural_advance_mode(context["case"], policy) == "native_horizon":
            name = "ordinary-pilgrimage-natural-clock-capabilities"
            cap_row = client.execute_plan([{"id": name, "tool": "ck3_get_capabilities",
                "args": {}, "fresh_revision": True}], name)[0]
            require(cap_row.get("ok") is True and not cap_row.get("error"),
                    "Original natural-clock capability query failed")
            natural_capabilities = obj(cap_row.get("result"), "actual natural-clock capabilities")
            require_pilgrimage_natural_capabilities(natural_capabilities)
            cap_frame = obj(cap_row.get("after_snapshot"), "actual capability after-frame")
            require(frame_binding(cap_frame, context, mechanism.actor_character_id) == binding
                    and cap_frame.get("date_raw") == before["date_raw"],
                    "Natural-clock capability observation crossed the paused native owner/date")
            before = cap_frame
            cap_path = client.output / (name + ".actual-results.json")
            cap_raw = cap_path.read_bytes()
            result["natural_clock_capability_observation"] = {
                "mode": "native_horizon", "life_advance_composite_observed": True,
                "typed_event_observer_observed": True,
                "source": {"path": str(cap_path), "bytes": len(cap_raw),
                    "sha256": hashlib.sha256(cap_raw).hexdigest()}}
        if resume is not None:
            identity, resume_proof, consumed_event_definitions, prior_elapsed_hours = resume_native_identity(
                context, client, binding, before)
            result.update(status="hosted_identity_observed", hosted_identity_observed=True,
                hosted_identity=identity, resume=resume_proof, entry_mode="resume_existing")
        else:
            before = drain_if_needed(context, client, binding, before)
            require(frame_binding(before, context, mechanism.actor_character_id) == binding,
                    "Initial interruption changed original actor or native owner")
            planner.start_date = before["date_raw"]
            identities = planner.call(IDENTITIES)
            require(identities.get("activity_count") == 0 and identities.get("activities") == [],
                    "Existing hosted pilgrimage precludes a new once-only Start")
            offers = planner.call(RELIGION)
            preferred = c.get("preferred_destination_id")
            if preferred is not None and type(preferred) is not int:
                raise ValueError("Frozen preferred destination is not an integer")
            destination = choose_destination(offers, mechanism.actor_character_id, before["date_raw"],
                preferred, mechanism.faith_id, mechanism.rite_id)
            province = integer(destination["province_id"], "selected destination")
            client.checkpoint("ordinary-pilgrimage-destination-policy", destination)
            capture_checkpoint(context, client, "ordinary-pilgrimage-record-before-planner", {
                "binding": binding, "date_raw": before["date_raw"], "actor_character_id": binding["actor_character_id"],
                "faith_id": mechanism.faith_id, "rite_id": mechanism.rite_id,
                "option_key": mechanism.option_key, "native_offers": offers, "destination": destination,
                "next_action": "Open original pious pilgrimage planner after recording is ready"})
            initial = planner.query()
            require(initial.get("ledger_state") == "idle" and initial.get("needs_recovery") is False,
                    "Existing native submission ledger cannot be reset")
            opened = planner.submit("open")
            # A separate native stage1 read binds the actual selected option.
            # stage1 read below must independently observe the current selection.
            require(opened.get("operation_status") == "observed" and opened.get("invoked") is True
                    and opened.get("needs_recovery") is False
                    and isinstance(opened.get("planner"), dict)
                    and opened["planner"].get("stage") == 1
                    and opened["planner"].get("can_progress") is True,
                    "Original Open was not observed at ready stage1")
            stage1 = planner.query(read_stage=1)
            require_planner(stage1, 1, option_key=mechanism.option_key)
            reviewed_stage1 = capture_checkpoint(context, client, "ordinary-pilgrimage-review-stage1-before-confirm", {
                "binding": binding, "native_observation": stage1,
                "native_observation_sha256": visual_observation_sha256(stage1),
                "prepare_original_image": True, "approval_key": "confirm_once_authorized",
                "review_contract": "Root directly reviews original PNG and the frozen selected_option_key at stage1; only explicit current-observation approval permits Confirm",
                "next_action": "Fresh native stage1 read, then one original pious Confirm"})
            require_root_visual_review(reviewed_stage1, stage1, "confirm_once_authorized")
            # The scene stayed paused for Root; reject changed selection after review.
            require_planner(planner.query(read_stage=1), 1, option_key=mechanism.option_key)
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
            require_planner(planner.query(), 5, province, mechanism.option_key)
            quoted = planner.query("quote")
            quote = quoted.get("quote")
            require(quoted.get("operation_status") == "observed" and isinstance(quote, dict)
                    and quote.get("observed") is True and quote.get("planning_stage") == 5
                    and quote.get("final_can_start_observed") is True and quote.get("final_can_start") is True
                    and quote.get("unknown_positive_configured_cost") is False
                    and quote.get("selected_option", {}).get("key") == mechanism.option_key,
                    "Real configured full10 quote or final CanStart unavailable")
            client.checkpoint("ordinary-pilgrimage-final-configured-full10-quote", {
                "quote": quote, "journey_inclusion_proven": False,
                "native_final_canstart_required": True, "reserve_gold_raw": policy["reserve_gold_raw"],
                "policy": "retain explicit gold reserve; never present activity-only offer as all journey cost"})
            reviewed_quote = capture_checkpoint(context, client, "ordinary-pilgrimage-record-quote-before-start", {
                "binding": binding, "province_id": province, "quote": quote,
                "native_observation": quoted, "native_observation_sha256": visual_observation_sha256(quoted),
                "prepare_original_image": True, "approval_key": "start_once_authorized",
                "review_contract": "Root directly reviews original PNG and actual final configured price/CanStart/reserve; this quote is not a proven total journey cost",
                "reserve_gold_raw": policy["reserve_gold_raw"], "journey_cost_inclusion_proven": False,
                "next_action": "One original Start only after explicit Root review of this final native price"})
            require_root_visual_review(reviewed_quote, quoted, "start_once_authorized")
            observations = sibling(Path(__file__).with_name("faith_e02_pilgrimage_observations.py"),
                                   "_faith_e02_pilgrimage_milestone_observations")
            observations.observe_milestone(context, client, binding, milestone_observations,
                                           "before-start")
            # The scene remains paused during capture coordination. Re-read the
            # actual destination and priced configuration before the one submission.
            require_planner(planner.query(), 5, province, mechanism.option_key)
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
                "reserve_gold_raw": policy["reserve_gold_raw"], "attempt": 1,
                "unknown_result_policy": "never resubmit; query native persistent ledger and hosted identities only"})
            result["start_intent_written"] = True
            # This is the only Start call in this case. Any exception leaves the
            # durable intent unresolved; neither this adapter nor Python retries it.
            start = None
            try:
                start = planner.submit("start", province_id=province,
                    reserve_gold_raw=policy["reserve_gold_raw"])
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
        limits = journey_limits(policy)
        if resume is not None:
            remaining_days = (integer(policy["max_journey_days"], "original journey cap") * 24 - prior_elapsed_hours) // 24
            require(remaining_days >= 2, "Original journey duration has no remaining finite advance reserve")
            limits["max_days"] = remaining_days
        if resume is not None:
            journey_value = journey.run_journey(context, client, binding, identity, limits,
                natural_capabilities=natural_capabilities, consumed_event_definitions=consumed_event_definitions)
        elif natural_capabilities is None:
            journey_value = journey.run_journey(context, client, binding, identity, limits)
        else:
            journey_value = journey.run_journey(context, client, binding, identity, limits,
                natural_capabilities=natural_capabilities)
        journey_result = obj(journey_value, "journey result")
        result["journey"] = journey_result
        result["status"] = journey_result["status"]
        if (context["case"] == MECHANISM_CASE and obj(c.get("scope", {}), "case scope").get("new_save_allowed") is True
                and journey_result.get("return_observed") is True
                and journey_result.get("return_event_chain_complete") is True):
            # One native SAVE after the observed return. Keep the immutable source
            # save separate; ACK, scoped checkpoint metadata and actual file readback
            # are recorded independently, and an unknown SAVE is never retried.
            current = client.snapshot(require_event_free=True)
            require(frame_binding(current, context, mechanism.actor_character_id) == binding,
                    "Continuation save crossed native actor/process identity")
            result["continuation_save_attempted"] = True
            row = client.execute_plan([{"id": "pilgrimage-return-save-once", "tool": "ck3_save_checkpoint",
                "args": {}, "fresh_revision": True, "continue_on_error": True}],
                "pilgrimage-return-save-once")[0]
            client.checkpoint("pilgrimage-return-save-command", row)
            saved = row.get("result", {})
            require(row.get("ok") is True and saved.get("accepted") is True
                    and saved.get("step") == "save-checkpoint", "Original continuation SAVE not accepted; never replay")
            checkpoint = saved.get("checkpoint", {})
            require(checkpoint.get("status") == "saved" and type(checkpoint.get("date_raw")) is int
                    and checkpoint["date_raw"] == current["date_raw"]
                    and checkpoint.get("episode_projection") == "native_campaign"
                    and isinstance(checkpoint.get("path"), str), "Native continuation checkpoint scope is unavailable")
            saved_input = obj(c["saved_input"], "immutable saved input")
            source_path = saved_input.get("save")
            if not isinstance(source_path, str):
                raise ValueError("Immutable source save path is unavailable")
            target = Path(checkpoint["path"]).resolve()
            require(target != Path(source_path).resolve(), "Continuation SAVE overwrote immutable source")
            raw = target.read_bytes()
            require(type(checkpoint.get("size")) is int and len(raw) == checkpoint["size"]
                    and hashlib.sha256(raw).hexdigest() == checkpoint.get("sha256"),
                    "Continuation SAVE file differs from native checkpoint metadata")
            after_save = client.snapshot(require_event_free=True)
            require(frame_binding(after_save, context, mechanism.actor_character_id) == binding
                    and after_save["date_raw"] == current["date_raw"], "Paused SAVE crossed actor/date")
            result["continuation_save"] = {"checkpoint": checkpoint, "file_bytes_verified": True,
                "before_frame": current, "after_frame": after_save,
                "reload_business_qualified": False, "gameplay_achievement_credit": False}
            client.checkpoint("pilgrimage-return-continuation-save", result["continuation_save"])
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


def verify_case(context: JSONObject) -> JSONObject:
    c = validate_contract(context)
    output = context["output"]
    if not isinstance(output, (str, Path)):
        raise ValueError("Pilgrimage verification output must be an explicit path")
    result = read(Path(output) / "ordinary-pilgrimage-result.json")
    require(result.get("machine_id") == c["machine_id"] and result.get("case") == context["case"]
            and result.get("run_id") == context["run_id"], "Actual result crossed public case")
    return {"status": result["status"], "hosted_identity_observed": result["hosted_identity_observed"],
            "journey": result["journey"], "needs_recovery": result["needs_recovery"],
            "public_requests_used": result["public_requests_used"], "public_requests_cap": result["public_requests_cap"],
            "payment_total_proven": False, "absence_is_completion": False,
            "business_pass": False, "product_release_pass": False}
