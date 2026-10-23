"""Bounded public CaseClient pilgrimage continuation; no launcher or direct driver."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import importlib
import importlib.util
from pathlib import Path
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tools.ck3_mod_acceptance_cases.faith_e02_pilgrimage_observations import JSONObject, MilestoneObservation
    from ck3_mod_acceptance_native_day import DayClient

CASE = "faith-engine-e02-d1-ordinary-pilgrimage-v1"
MECHANISM_CASE = "faith-engine-e02-pilgrimage-mechanism-v2"
KEY_EVENTS = frozenset({"pilgrimage.5001", "pilgrimage.7000", "pilgrimage.9001",
    "pilgrimage.3101", "hajj.3010", "hajj.3020", "hajj.3021", "hajj.3030",
    "hajj.3040", "hajj.3001"})
IDENTITIES = "ck3_query_player_pilgrimage_activities_v1"
EVENT_CONTEXT = "ck3_query_current_event_window_context_v1"
EVENT_SELECT = "ck3_select_event_option"
INTERACTION_CONTEXT = "ck3_query_pending_character_interaction_context_v1"
INTERACTION_REPLY = "ck3_reply_pending_character_interaction"
REQUIRED_TOOLS = frozenset({"ck3_take_snapshot", IDENTITIES, EVENT_CONTEXT, EVENT_SELECT,
                            INTERACTION_CONTEXT, INTERACTION_REPLY})
RETURN_SCRIPT_REFERENCE = {'schema': 'faith-e02-pilgrimage-return-script-reference-v1', 'machine_id': '4-8e1c2f1861', 'observed_at_utc': '2026-10-19T21:55:02.662571+00:00', 'source_pins': [{'path': 'C:\\Program Files (x86)\\Steam\\steamapps\\common\\Crusader Kings III\\game\\common\\on_action\\travel_on_actions.txt', 'bytes': 71526, 'sha256': 'cd40f30a9280ea9ba656b59005201550f3991afd646fd686d7474657b1b1ff70'}, {'path': 'C:\\Program Files (x86)\\Steam\\steamapps\\common\\Crusader Kings III\\game\\common\\on_action\\activities\\pilgrimage_on_actions.txt', 'bytes': 11904, 'sha256': 'fdf71f074882f94eb3df497a1ddb2cb9a95fb13e973aebf25d4c3569729ee354'}, {'path': 'C:\\Program Files (x86)\\Steam\\steamapps\\common\\Crusader Kings III\\game\\common\\activities\\activity_types\\pilgrimage.txt', 'bytes': 111931, 'sha256': '24153043485b035cb0477de7306649027cb68c039e4a9d903776eddd870d8b9f'}, {'path': 'C:\\Program Files (x86)\\Steam\\steamapps\\common\\Crusader Kings III\\game\\events\\activities\\pilgrimage_activity\\pilgrimage_events.txt', 'bytes': 358138, 'sha256': '900959b36dfc121bb0e785733723ea7e70e3931e7377a16206ba98eba555be06'}], 'method': 'Read current game script files; search common/events callers. Not a loaded-script runtime receipt.', 'return_hook': 'on_travel_plan_complete', 'return_event': 'pilgrimage.9001', 'conclusion_event': 'pilgrimage.7000', 'meaning': 'source-bound return event phase, not independently read home coordinates', 'limits': ['travel completion hook also permits script completion', '9001 alone also permits invalidation', '9010 supersedes 9001 on death/burial paths and is not a normal success receipt', '7000 first option is tooltip-only for the already-resolved main reward']}

DEFAULT_LIMITS = {"max_days": 240, "max_day_requests": 480, "max_events": 128,
                  "quit_reserve_seconds": 120, "one_day_timeout": 60}


class JourneyStop(Exception):
    def __init__(self, status: str, reason: str) -> None:
        super().__init__(reason)
        self.status = status


def _need(value: object, reason: str, status: str = "PARTIAL_NATIVE_CONTRACT_GAP") -> None:
    if not value:
        raise JourneyStop(status, reason)


def _pin(path):
    path = Path(path).resolve()
    raw = path.read_bytes()
    return {"path": str(path), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def _limits(value: dict[str, object], *, case_id: object = CASE) -> dict[str, int]:
    from tools.ck3_mod_acceptance_cases.faith_e02_pilgrimage_contract import pilgrimage_policy_caps
    caps = pilgrimage_policy_caps(case_id)
    value = dict(value)
    if "max_journey_days" in value:
        _need("max_days" not in value or value["max_days"] == value["max_journey_days"],
              "Conflicting journey-day limits")
        value["max_days"] = value.pop("max_journey_days")
    _need(set(value) <= set(DEFAULT_LIMITS), "Unknown journey limit")
    result = {**DEFAULT_LIMITS, **value}
    for key, maximum in (("max_days", caps.max_days), ("max_day_requests", caps.max_day_requests), ("max_events", 128),
                         ("one_day_timeout", 300)):
        item = result[key]
        _need(type(item) is int and 1 <= item <= maximum,
              "Invalid finite journey limit: " + key)
    reserve = result["quit_reserve_seconds"]
    _need(type(reserve) is int and
          90 <= reserve <= 600, "Original Quit reserve must be at least 90 seconds")
    return {key: item for key, item in result.items() if type(item) is int}


def _opening_reader(context):
    source = Path(context["shared_source_root"]).resolve()
    if (source / "ck3_autonomous_player/src/xar_autoplayer").is_dir():
        source = source / "ck3_autonomous_player/src"
    expected = source / "xar_autoplayer/bridge/ingame_decisions_open_contract.py"
    identity = source / "xar_autoplayer/bridge/version_identity.py"
    previous = list(sys.path)
    try:
        sys.path.insert(0, str(source))
        module = importlib.import_module("xar_autoplayer.bridge.ingame_decisions_open_contract")
        dependency = importlib.import_module("xar_autoplayer.bridge.version_identity")
        _need(Path(module.__file__).resolve() == expected and
              Path(dependency.__file__).resolve() == identity, "Opening binding import escaped selected source")
        return module.opening_binding, {"opening_contract": _pin(expected), "version_identity": _pin(identity)}
    finally:
        sys.path[:] = previous


def _event_policy_reader(context):
    source = Path(context["shared_source_root"]).resolve()
    if (source / "ck3_autonomous_player/src/xar_autoplayer").is_dir():
        source = source / "ck3_autonomous_player/src"
    previous = list(sys.path)
    try:
        sys.path.insert(0, str(source))
        modules = {name: importlib.import_module("xar_autoplayer.vanilla_events." + name)
                   for name in ("policy", "registry", "records_manager_a")}
        for name, module in modules.items():
            _need(Path(module.__file__).resolve() == source / ("xar_autoplayer/vanilla_events/" + name + ".py"),
                  "Event policy import escaped selected source")
        return (modules["policy"].recommend_registered_vanilla_event_option_v1,
                modules["registry"].query_vanilla_event_knowledge_v1,
                {name: _pin(module.__file__) for name, module in modules.items()})
    finally:
        sys.path[:] = previous


class _Journey:
    def __init__(self, context, client, binding, initial_identity, limits, *, natural_capabilities: object = None,
                 consumed_event_definitions: tuple[str, ...] = ()):
        self.context, self.client = context, client
        self.binding = dict(binding)
        self.identity = dict(initial_identity) if initial_identity is not None else None
        self.limits = _limits(limits, case_id=context.get("case"))
        from tools.ck3_mod_acceptance_cases.faith_e02_pilgrimage_contract import pilgrimage_natural_advance_mode
        self.advance_mode = pilgrimage_natural_advance_mode(context.get("case"),
            context.get("case_contract", {}).get("policy", {}))
        self.natural_capabilities = natural_capabilities
        _need(type(consumed_event_definitions) is tuple
              and all(type(key) is str and key for key in consumed_event_definitions)
              and len(set(consumed_event_definitions)) == len(consumed_event_definitions),
              "Resume consumed event definitions must be a unique immutable tuple")
        self.consumed_event_definitions = consumed_event_definitions
        _need(context.get("case") in {CASE, MECHANISM_CASE}
              and context.get("product") == "faith-engine", "Foreign pilgrimage case")
        _need(set(self.binding) == {"run_id", "machine_id", "actor_character_id", "bridge_pid",
                                   "connection_generation", "episode_run_id"}, "Exact journey binding required")
        _need(self.binding["run_id"] == context.get("run_id") and
              self.binding["machine_id"] == context["case_contract"].get("machine_id") and
              self.binding["machine_id"] not in (None, "", "unknown"), "Journey run/machine differs")
        for key in ("actor_character_id", "bridge_pid", "connection_generation"):
            _need(type(self.binding[key]) is int and self.binding[key] > 0, "Invalid actual identity " + key)
        if self.identity is not None:
            _need(type(self.identity.get("activity_id")) is int and 0 <= self.identity["activity_id"] < 2**32 - 1 and
                  self.identity.get("host_character_id") == self.binding["actor_character_id"] and
                  self.identity.get("type_key") == "activity_pilgrimage", "Initial full activity identity differs")
        self.reader, self.sources = _opening_reader(context)
        invocation = getattr(client, "_faith_e02_journey_invocations", 0) + 1
        client._faith_e02_journey_invocations = invocation
        self.prefix = "faith-e02-journey-" + str(invocation).zfill(3) + "-"
        self.seq = 0
        self.last_frame = None
        self.last_identity_date = None
        self.consumed_events: set[int] = set()
        self.consumed_interactions: set[int] = set()
        self.result = {"schema": "faith-e02-pilgrimage-bounded-journey-v1", "case": context["case"],
            "binding": self.binding, "machine_id": self.binding["machine_id"], "run_id": context["run_id"],
            "started_at_utc": datetime.now(timezone.utc).isoformat(), "limits": self.limits,
            "initial_activity_identity": self.identity, "opening_binding_sources": self.sources,
            "status": "RUNNING", "observed_days": 0, "elapsed_hours": 0, "day_requests": 0,
            "day_receipts": [], "event_receipts": [], "interaction_receipts": [],
            "identity_receipts": [], "offline_analysis_inputs": [], "root_capture_checkpoints": [],
            "terminal_observed": False, "completion_evidence": None,
            "payment_or_travel_total_known": False, "arrival_observed": False, "return_observed": False,
            "business_pass": False, "normal_close_pending": True, "new_save_performed": False,
            "activity_identity_absence_observed": False, "destination_phase_conclusion_observed": False,
            "destination_conclusion_evidence": None, "return_phase_evidence": None,
            "return_event_chain_complete": False, "coordinate_home_observed": False,
            "return_support_reference": RETURN_SCRIPT_REFERENCE, "milestone_observations": []}

    def public_budget(self):
        used = getattr(self.client, "public_requests_used", None)
        cap = getattr(self.client, "public_requests_cap", None)
        if cap is None:
            cap = getattr(self.client, "public_request_cap", None)
        if cap is None:
            cap = getattr(self.client, "cap", None)
        return used, cap

    def budget_evidence(self):
        used, cap = self.public_budget()
        self.result.update(public_requests_used=used, public_requests_cap=cap,
                           day_requests_are_advance_day_subcount_only=self.advance_mode == "one_day",
                           identity_observation_policy=("initial/after_actual_interruption/each_7_actual_days/necessary_final"
                               if self.advance_mode == "one_day" else
                               "initial/after_actual_interruption/after_native_slice_or_7_days/necessary_final"))

    def record(self, name, value):
        packet = {"machine_id": self.binding["machine_id"], "run_id": self.binding["run_id"],
                  "observed_at_utc": datetime.now(timezone.utc).isoformat(), **value}
        return _pin(self.client.checkpoint(self.prefix + name, packet))

    def guard(self, budget=30):
        used, cap = self.public_budget()
        _need(not (type(used) is int and type(cap) is int and used >= cap),
              "Whole-case public request budget exhausted", "PARTIAL_PUBLIC_REQUEST_CAP")
        _need(self.client.remaining() > self.limits["quit_reserve_seconds"] + budget,
              "Original normal Quit reserve reached", "PARTIAL_QUIT_RESERVE")
        self.client.guard()

    def frame(self, value, previous=None, same_date=False):
        self.client.validate_frame(value, require_event_free=False)
        actual = self.reader(value)
        expected = {"played_character_id": self.binding["actor_character_id"],
                    "game_pid": self.binding["bridge_pid"],
                    "connection_generation": self.binding["connection_generation"],
                    "episode_run_id": self.binding["episode_run_id"]}
        _need(all(actual[key] == wanted for key, wanted in expected.items()), "Actual journey owner/episode changed")
        _need(value["diagnostics"]["hello"].get("expected_ck3_version") == "1.20.0.4", "Journey requires exact .4")
        if previous is not None:
            _need(value["date_raw"] >= previous["date_raw"] and
                  (not same_date or value["date_raw"] == previous["date_raw"]), "Journey date drift")
        self.last_frame = value
        return value

    def snapshot(self, previous=None, same_date=False):
        self.guard()
        return self.frame(self.client.snapshot(require_event_free=False), previous, same_date)

    def call(self, suffix, tool, args, frame):
        self.guard()
        self.seq += 1
        name = self.prefix + str(self.seq).zfill(4) + "-" + suffix
        rows = self.client.execute_plan([{"id": name, "tool": tool, "fresh_revision": False,
            "args": {**args, "expected_revision": frame["revision"]}}], name)
        _need(isinstance(rows, list) and len(rows) == 1 and rows[0].get("ok") is True and
              not rows[0].get("error"), "Original MCP result failed; never replay")
        row = rows[0]
        after = self.frame(row["after_snapshot"], frame, same_date=True)
        return row, after, _pin(self.client.output / (name + ".actual-results.json"))

    def observe_milestone(self, label: str, *, event: object = None,
                          identity: object = None) -> JSONObject | None:
        path = Path(__file__).with_name("faith_e02_pilgrimage_observations.py")
        spec = importlib.util.spec_from_file_location("_faith_e02_pilgrimage_milestone", path)
        if spec is None or spec.loader is None:
            raise ValueError("Selected typed milestone helper is absent")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        # Fixed sibling loader is the legacy dynamic boundary; the helper validates
        # JSON input before constructing its shared typed observation contract.
        result: tuple[MilestoneObservation | None, JSONObject | None] = module.observe_milestone(self.context, self.client, self.binding,
            self.result.setdefault("milestone_observations", []), self.prefix + label, event=event, identity=identity)
        observation, latest = result
        if latest is not None:
            self.frame(latest, self.last_frame, same_date=True)
        return latest

    def observe_identity(self, frame, reason="key_node"):
        frame = self.snapshot(frame, same_date=True)
        row, after, ref = self.call("identity", IDENTITIES, {}, frame)
        value = row["result"]
        _need(value.get("schema") == "ck3_12004_player_pilgrimage_activities_v1" and
              value.get("scope") == "currently-hosted-by-current-player" and
              value.get("activity_type_key") == "activity_pilgrimage" and
              value.get("absence_is_completion") is False and value.get("read_only") is True and
              value.get("queried_revision") == frame["revision"] and
              value.get("snapshot_revision") == frame["native_revision"] and
              value.get("date_raw") == frame["date_raw"] and
              value.get("played_character_id") == self.binding["actor_character_id"] and
              isinstance(value.get("activities"), list) and
              value.get("activity_count") == len(value["activities"]), "Actual hosted identity query unavailable")
        matches = [r for r in value["activities"] if r.get("activity_id") == self.identity["activity_id"]]
        _need(len(matches) <= 1, "Duplicate full activity identity")
        receipt = {"date_raw": frame["date_raw"], "source": ref, "query_reason": reason,
                   "target_present": bool(matches), "identity": matches[0] if matches else None}
        self.result["identity_receipts"].append(receipt)
        self.last_identity_date = frame["date_raw"]
        if not matches:
            self.result["activity_identity_absence_observed"] = True
            receipt["meaning"] = "hosted full ID absent; continue bounded return-event observation; no completion inference"
            return after
        actual = matches[0]
        _need(actual.get("host_character_id") == self.identity["host_character_id"] and
              actual.get("type_key") == "activity_pilgrimage", "Hosted full ID owner/type changed")
        if actual.get("terminal_flags_observed") is True:
            _need(type(actual.get("native_completed")) is bool and type(actual.get("native_invalidated")) is bool,
                  "Terminal flags lack actual values")
            if actual["native_completed"] or actual["native_invalidated"]:
                first_terminal = not self.result["terminal_observed"]
                self.result["terminal_observed"] = True
                self.result["completion_evidence"] = {"source": ref, "identity": actual,
                    "native_completed": actual["native_completed"], "native_invalidated": actual["native_invalidated"],
                    "reward_or_return_completion_claimed": False}
                if first_terminal:
                    latest = self.observe_milestone("terminal-" + str(actual["activity_id"]), identity=actual)
                    if latest is not None:
                        after = latest
        return after

    def necessary_final_identity(self):
        frame = self.last_frame
        if (self.identity is None or not isinstance(frame, dict) or
                self.last_identity_date == frame["date_raw"] or
                self.result["terminal_observed"] or frame.get("active_event") is not None or
                frame.get("pending_character_interaction") is not None):
            return
        used, cap = self.public_budget()
        if ((type(used) is int and type(cap) is int and used >= cap) or
                self.client.remaining() <= self.limits["quit_reserve_seconds"] + 35):
            self.result["final_identity_read"] = "not_attempted_original_request_or_quit_reserve"
            return
        self.observe_identity(frame, "necessary_final")
        self.result["final_identity_read"] = "observed"
        if self.result["terminal_observed"]:
            evidence = self.result["completion_evidence"]
            if evidence["native_invalidated"]:
                self.result["status"] = "INVALIDATED_NATIVE_FLAG_OBSERVED"
            # Native activity completion alone never overwrites a partial return status.

    def choose_event_option(self, typed, options, frame, after):
        # Reuse the existing registry. The explicit user doctor preference is a
        # current named-row override, not a historical scope/index projection.
        def legal(option):
            index = option.get("native_option_index")
            return (option.get("shown") is True and option.get("enabled") is True and
                type(index) is int and index >= 0 and
                any(row.get("option_number") == index + 1 and row.get("enabled") is True
                    for row in (after.get("active_event") or {}).get("options", [])))
        decision = {"policy": "native_first_displayed_v1", "registry_decision": None,
                    "registry_knowledge_status": None, "registry_analysis_available": False,
                    "source_sha256": None, "policy_sources": None, "gap": None}
        knowledge = {}
        try:
            recommend, query, sources = _event_policy_reader(self.context)
            knowledge = query(typed["event_definition_key"], "1.20.0.4")
            decision.update(policy_sources=sources, registry_knowledge_status=knowledge.get("status"),
                registry_analysis_available=isinstance(knowledge.get("analysis"), dict) and bool(knowledge["analysis"]),
                source_sha256=(knowledge.get("analysis") or {}).get("source_sha256"))
            decision["registry_decision"] = recommend(typed,
                played_character_id=self.binding["actor_character_id"],
                snapshot_option_count=(after.get("active_event") or {}).get("option_count"),
                ck3_build="1.20.0.4", played_character=frame.get("played_character"))
        except Exception as error:
            decision["gap"] = "registry_reader_or_consumer_unavailable: " + type(error).__name__ + ": " + str(error)
        if typed["event_definition_key"] == "health.1015":
            analysis = knowledge.get("analysis") or {}
            hashes = analysis.get("source_sha256") or {}
            root = (typed.get("root_scope") or {}).get("typed_identity") or {}
            sick = [row.get("scope", {}).get("typed_identity", {}) for row in typed.get("saved_scopes", [])
                    if row.get("name") == "sick_character"]
            source_ready = (knowledge.get("status") == "available" and
                hashes.get("events/health_events.txt") == "74073E049A416C744B36A2A996FA467610705E38D53C836B050F1AC6F66E1212" and
                hashes.get("common/scripted_effects/20_health_effects.txt") == "ABEFA738C913C660A52FA747BCC92FCA2F57D77A0F47D903BEDC2882F3D5A9DB")
            owner_ready = (root.get("status") == "available" and root.get("kind") == "character" and
                root.get("character_id") == self.binding["actor_character_id"] and len(sick) == 1 and
                sick[0].get("status") == "available" and sick[0].get("kind") == "character" and
                sick[0].get("character_id") == self.binding["actor_character_id"])
            named = [option for option in options if option.get("resolved_name") == "叫医生来！马上！"]
            available = [option for option in named if legal(option)]
            decision["health1015_user_preference"] = {"source_ready": source_ready, "current_patient_owner_ready": owner_ready,
                "localization_key": "health.3101.e", "resolved_name": "叫医生来！马上！",
                "localization_source_sha256": "7600AD3C4A482F335DE1B27367CE81F27348742F8F19BE034FD1B547686A747A",
                "shown_named_rows": len(named), "legal_named_rows": len(available),
                "full_registry_occurrence_contract_claimed": False}
            if source_ready and owner_ready and len(named) == len(available) == 1:
                decision["policy"] = "user_health1015_current_named_doctor_v1"
                return available[0], decision
            decision["gap"] = "health1015 named doctor unavailable/disabled/ambiguous or current source/patient not bound"
        recommended = decision["registry_decision"] or {}
        if recommended.get("status") == "recommended":
            matches = [option for option in options if legal(option) and
                option.get("native_option_index") == recommended.get("selected_native_option_index") and
                option["native_option_index"] + 1 == recommended.get("selected_option_number")]
            if len(matches) == 1:
                decision["policy"] = "existing_registered_vanilla_event_v1"
                return matches[0], decision
            decision["gap"] = "registry recommendation not a unique currently legal displayed native row"
        elif decision["gap"] is None:
            decision["gap"] = "registry did not recommend: " + str(recommended.get("reason", recommended.get("status")))
        _need(legal(options[0]), "First displayed option unavailable/disabled; no silent skip to another row")
        return options[0], decision

    def event(self, frame):
        _need(len(self.result["event_receipts"]) + len(self.result["interaction_receipts"]) < self.limits["max_events"],
              "Finite modal cap", "PARTIAL_EVENT_CAP")
        active = frame.get("active_event")
        _need(isinstance(active, dict) and type(active.get("instance_id")) is int and active["instance_id"] > 0,
              "Native active event has no full instance")
        instance = active["instance_id"]
        _need(instance not in self.consumed_events, "Consumed/unknown event cannot be replayed", "PARTIAL_EVENT_NO_REPLAY")
        row, before, source = self.call("event-query", EVENT_CONTEXT, {"event_instance_id": instance}, frame)
        value, typed = row["result"], row["result"].get("current_event_window_context", {})
        capture = {"frame": frame, "query_after_frame": before, "active_event": active,
                   "typed_context": typed, "query_source": source, "policy": "dedicated_then_native_first_displayed_v1",
                   "offline_analysis_required_after_batch": True}
        offline = self.record("event-" + str(instance) + "-offline-analysis-input", capture)
        self.result["offline_analysis_inputs"].append(offline)
        _need(value.get("accepted") is True and value.get("current_event_window_context_ready") is True and
              typed.get("schema") == "current-event-window-context-v1" and typed.get("status") == "available" and
              typed.get("current_event_instance_id") == instance and typed.get("date_raw") == frame["date_raw"] and
              typed.get("snapshot_revision") == frame["native_revision"] and
              isinstance(typed.get("event_definition_key"), str) and bool(typed["event_definition_key"]) and
              typed.get("readiness", {}).get("option_presentation_ready") is True and
              (before.get("active_event") or {}).get("instance_id") == instance,
              "Current event presentation/definition unavailable; no invented fallback")
        _need(typed["event_definition_key"] not in self.consumed_event_definitions,
              "Predecessor native selection already consumed this definition; never replay after cold restore",
              "PARTIAL_EVENT_NO_REPLAY")
        options = typed.get("options")
        _need(isinstance(options, list) and options and len(options) <= 64 and
              [o.get("rendered_index") for o in options] == list(range(len(options))), "Native rendered order unavailable")
        chosen, event_policy = self.choose_event_option(typed, options, frame, before)
        index = chosen["native_option_index"]
        number = index + 1
        snapshot_options = (before.get("active_event") or {}).get("options", [])
        _need(any(o.get("option_number") == number and o.get("enabled") is True for o in snapshot_options),
              "Chosen displayed option differs from actual native option map")
        capture_response = self.capture_key_window(typed, options, frame)
        refresh_source = None
        if capture_response is not None:
            refreshed = self.refresh_key_window(typed, chosen, before)
            typed, frame, before = refreshed["typed_context"], refreshed["query_frame"], refreshed["query_after_frame"]
            refresh_source = refreshed["evidence"]
            event_policy = refreshed["event_policy"]
        intent = self.record("event-" + str(instance) + "-selection-intent", {
            **capture, "actual_displayed_options": options, "selected_native_option_index": index,
            "selected_option_number": number, "submission_attempted": False,
            "decision_reason": event_policy["policy"], "event_policy": event_policy,
            "decision_display_evidence": None})
        receipt = {"event_instance_id": instance, "event_definition_key": typed["event_definition_key"],
            "intent": intent, "offline_analysis_input": offline, "selected_option_number": number,
            "selected_native_option_index": index, "submission_attempted": True, "ack_accepted": False,
            "old_instance_gone_in_independent_snapshot": False, "selection_source": None,
            "root_capture_checkpoint": capture_response, "key_window_refresh_source": refresh_source,
            "event_policy": event_policy}
        self.guard()  # Budget exhaustion before submission remains a budget partial, not an unknown ACK.
        self.result["event_receipts"].append(receipt)
        self.consumed_events.add(instance)  # Before the sole original submission.
        try:
            selected, _, selected_source = self.call("event-select-once", EVENT_SELECT,
                {"event_instance_id": instance, "option_number": number}, before)
            ack = selected["result"]
            receipt["selection_source"] = selected_source
            receipt["ack_accepted"] = (ack.get("accepted") is True and
                ack.get("event_instance_id") == instance and ack.get("option_number") == number and
                ack.get("option_index") == index)
        except Exception as error:
            receipt["selection_error"] = type(error).__name__ + ": " + str(error)
            # One independent read is recovery evidence, never a repeat action.
            try:
                after = self.snapshot(before, same_date=True)
                receipt["independent_after_snapshot"] = after
                receipt["old_instance_gone_in_independent_snapshot"] = (after.get("active_event") or {}).get("instance_id") != instance
            except Exception as read_error:
                receipt["independent_read_error"] = type(read_error).__name__ + ": " + str(read_error)
            raise JourneyStop("PARTIAL_EVENT_SUBMISSION_UNKNOWN", "Original event submission failed/unknown; not replayed")
        after = self.snapshot(before, same_date=True)
        receipt["independent_after_snapshot"] = after
        receipt["old_instance_gone_in_independent_snapshot"] = (after.get("active_event") or {}).get("instance_id") != instance
        self.record("event-" + str(instance) + "-selection-observed", receipt)
        _need(receipt["ack_accepted"], "Option ACK unavailable; no replay", "PARTIAL_EVENT_ACK_UNKNOWN")
        _need(receipt["old_instance_gone_in_independent_snapshot"], "Original event remains active; no replay", "PARTIAL_EVENT_NOT_CONSUMED")
        self.accept_source_bound_phase_event(typed, receipt, frame)
        if typed["event_definition_key"] in KEY_EVENTS:
            latest = self.observe_milestone(typed["event_definition_key"] + "-" + str(instance) + "-consumed", event=typed)
            if latest is not None:
                after = latest
        return after

    def refresh_key_window(self, original, chosen, previous):
        # Root's capture can publish a new public revision. Never submit the old one.
        instance = original["current_event_instance_id"]
        fresh = self.snapshot(previous, same_date=True)
        _need((fresh.get("active_event") or {}).get("instance_id") == instance,
              "Key event instance changed during Root capture; no option submitted", "PARTIAL_KEY_EVENT_CHANGED")
        row, after, source = self.call("key-window-refresh-query", EVENT_CONTEXT,
            {"event_instance_id": instance}, fresh)
        value = row["result"]
        typed = value.get("current_event_window_context", {})
        options = typed.get("options")
        evidence = {"query_frame": fresh, "query_after_frame": after,
            "typed_context": typed, "query_source": source,
            "captured_instance_id": instance, "captured_definition_key": original["event_definition_key"],
            "captured_selected_native_option_index": chosen["native_option_index"]}
        evidence["evidence"] = self.record("event-" + str(instance) + "-key-window-refresh", evidence)
        _need(value.get("accepted") is True and value.get("current_event_window_context_ready") is True and
              typed.get("schema") == "current-event-window-context-v1" and typed.get("status") == "available" and
              typed.get("current_event_instance_id") == instance and
              typed.get("date_raw") == fresh["date_raw"] and typed.get("snapshot_revision") == fresh["native_revision"] and
              typed.get("event_definition_key") == original["event_definition_key"] and
              typed.get("root_scope") == original.get("root_scope") and
              typed.get("readiness", {}).get("option_presentation_ready") is True and
              (after.get("active_event") or {}).get("instance_id") == instance and
              isinstance(options, list) and 1 <= len(options) <= 64 and
              [o.get("rendered_index") for o in options] == list(range(len(options))),
              "Key event definition/root/first displayed option changed or unavailable after Root capture; no option submitted",
              "PARTIAL_KEY_EVENT_CHANGED")
        selected, policy = self.choose_event_option(typed, options, fresh, after)
        _need(selected["native_option_index"] == chosen["native_option_index"],
              "Key event policy selected a different native option after capture; no option submitted",
              "PARTIAL_KEY_EVENT_CHANGED")
        evidence["event_policy"] = policy
        return evidence

    def capture_key_window(self, typed, options, frame):
        key = typed["event_definition_key"]
        if key not in KEY_EVENTS:
            return None
        self.observe_milestone(key + "-" + str(typed["current_event_instance_id"]) + "-window", event=typed)
        self.guard()
        reviewer = getattr(self.client, "operator_reviewer", None)
        _need(isinstance(reviewer, str) and bool(reviewer), "Root capture reviewer unavailable",
              "PARTIAL_ROOT_CAPTURE_CHECKPOINT_REJECTED")
        name = self.prefix + "key-window-" + key.replace(".", "-") + "-" + str(typed["current_event_instance_id"])
        request = {"run_id": self.context["run_id"], "machine_id": self.binding["machine_id"],
            "case": self.context["case"], "binding": self.binding,
            "event_definition_key": key, "event_instance_id": typed["current_event_instance_id"],
            "root_scope": typed.get("root_scope"), "actual_displayed_options": options, "frame": frame,
            "prepare_original_image": True, "requested_action": "Root records take and captures original image",
            "game_option_selection_requested_from_root": False,
            "after_complete_policy": "same current first displayed native option; no alternate content selected"}
        response = self.client.root_checkpoint(name, request, reserve=120)
        evidence = {"checkpoint_name": name, "request": request, "response": response}
        evidence["evidence"] = self.record(name + "-capture-response", evidence)
        self.result["root_capture_checkpoints"].append(evidence)
        _need(isinstance(response, dict) and response.get("run_id") == self.context["run_id"] and
              response.get("reviewer") == reviewer and response.get("status") == "complete",
              "Root capture checkpoint did not complete in this exact run/reviewer",
              "PARTIAL_ROOT_CAPTURE_CHECKPOINT_REJECTED")
        return evidence

    def accept_source_bound_phase_event(self, typed, receipt, frame):
        # This adds interpretation to an already independently consumed event.
        # The ordinary first-displayed fallback still handles every other event.
        key = typed.get("event_definition_key")
        if key not in {"pilgrimage.7000", "pilgrimage.9001"}:
            return
        root = typed.get("root_scope") or {}
        who = root.get("typed_identity") or {}
        actual_owner = (root.get("status") == "available" and root.get("raw_type_index") == 4 and
            root.get("type_key") == "character" and who.get("status") == "available" and
            who.get("kind") == "character" and who.get("character_id") == self.binding["actor_character_id"])
        if not actual_owner:
            receipt["return_interpretation"] = "not_credited_root_character_identity_unavailable_or_foreign"
            return
        evidence = {"event_definition_key": key, "event_instance_id": receipt["event_instance_id"],
            "actor_character_id": who["character_id"], "binding": self.binding,
            "date_raw": frame["date_raw"], "native_revision": frame["native_revision"],
            "offline_analysis_input": receipt["offline_analysis_input"],
            "selection_source": receipt["selection_source"],
            "selected_native_option_index": receipt["selected_native_option_index"],
            "ack_accepted": receipt["ack_accepted"],
            "old_instance_gone_in_independent_snapshot": receipt["old_instance_gone_in_independent_snapshot"],
            "independent_after_snapshot": receipt["independent_after_snapshot"]}
        if key == "pilgrimage.7000":
            self.result["destination_phase_conclusion_observed"] = True
            self.result["destination_conclusion_evidence"] = evidence
            evidence["main_reward_paid_by_selecting_option"] = False
            return
        self.result["return_observed"] = True
        self.result["return_phase_evidence"] = evidence
        evidence["meaning"] = "actual source-bound pilgrimage return event consumed; home coordinates not independently read"
        conclusion = self.result["destination_conclusion_evidence"]
        self.result["return_event_chain_complete"] = (isinstance(conclusion, dict) and
            conclusion["event_instance_id"] != evidence["event_instance_id"] and
            conclusion["date_raw"] <= evidence["date_raw"])

    def interaction(self, frame):
        _need(len(self.result["event_receipts"]) + len(self.result["interaction_receipts"]) < self.limits["max_events"],
              "Finite modal cap", "PARTIAL_EVENT_CAP")
        pending = frame.get("pending_character_interaction")
        _need(isinstance(pending, dict) and type(pending.get("instance_id")) is int and pending["instance_id"] > 0,
              "Native pending interaction has no full instance")
        instance = pending["instance_id"]
        _need(instance not in self.consumed_interactions, "Interaction outcome cannot be replayed", "PARTIAL_INTERACTION_NO_REPLAY")
        row, before, source = self.call("interaction-query", INTERACTION_CONTEXT,
            {"pending_interaction_id": instance}, frame)
        typed = row["result"].get("pending_character_interaction_context", {})
        capture = {"frame": frame, "query_after_frame": before, "pending_interaction": pending,
                   "typed_context": typed, "query_source": source,
                   "policy": "native_ordinary_left_reject_v1", "offline_analysis_required_after_batch": True}
        offline = self.record("interaction-" + str(instance) + "-offline-analysis-input", capture)
        self.result["offline_analysis_inputs"].append(offline)
        reject = typed.get("legality", {}).get("reject", {})
        routing = typed.get("routing", {})
        _need(typed.get("schema") == "pending-character-interaction-context-v1" and
              typed.get("status") == "available" and typed.get("pending_interaction_id") == instance and
              typed.get("snapshot_revision") == frame["native_revision"] and typed.get("date_raw") == frame["date_raw"] and
              typed.get("readiness", {}).get("reply_legality_ready") is True and
              routing.get("played_character_id") == self.binding["actor_character_id"] and
              routing.get("auto_accept_notification") is False and
              reject.get("status") == "available" and reject.get("allowed") is True and
              (before.get("pending_character_interaction") or {}).get("instance_id") == instance,
              "Ordinary native left reject unavailable/disabled; no right-button substitution",
              "PARTIAL_INTERACTION_LEFT_UNAVAILABLE")
        intent = self.record("interaction-" + str(instance) + "-reject-intent", {
            **capture, "selected_action": "reject", "rendered_position_source": "user-original-GUI-left-reject-rule",
            "reply_argument_accept": False, "submission_attempted": False})
        receipt = {"interaction_instance_id": instance, "intent": intent, "offline_analysis_input": offline,
            "reply_argument_accept": False, "submission_attempted": True, "command_result_observed": False,
            "old_instance_gone_in_independent_snapshot": False}
        self.guard()
        self.result["interaction_receipts"].append(receipt)
        self.consumed_interactions.add(instance)
        try:
            selected, _, selected_source = self.call("interaction-reject-once", INTERACTION_REPLY,
                {"interaction_instance_id": instance, "accept": False}, before)
            reply = selected["result"]
            actual = reply.get("interaction_result", {})
            receipt["selection_source"] = selected_source
            # Public reply's accepted=False means "reject", not failed transport.
            receipt["command_result_observed"] = (
                reply.get("step") == "reject-pending-character-interaction" and
                reply.get("accepted") is False and reply.get("interaction_instance_id") == instance and
                actual.get("status") == "rejected" and actual.get("instance_id") == instance)
        except Exception as error:
            receipt["selection_error"] = type(error).__name__ + ": " + str(error)
            try:
                after = self.snapshot(before, same_date=True)
                receipt["independent_after_snapshot"] = after
                receipt["old_instance_gone_in_independent_snapshot"] = (after.get("pending_character_interaction") or {}).get("instance_id") != instance
            except Exception as read_error:
                receipt["independent_read_error"] = type(read_error).__name__ + ": " + str(read_error)
            raise JourneyStop("PARTIAL_INTERACTION_SUBMISSION_UNKNOWN", "Original interaction outcome unknown; no replay")
        after = self.snapshot(before, same_date=True)
        receipt["independent_after_snapshot"] = after
        receipt["old_instance_gone_in_independent_snapshot"] = (after.get("pending_character_interaction") or {}).get("instance_id") != instance
        self.record("interaction-" + str(instance) + "-reject-observed", receipt)
        _need(receipt["command_result_observed"], "Native reject result unknown; no replay", "PARTIAL_INTERACTION_ACK_UNKNOWN")
        _need(receipt["old_instance_gone_in_independent_snapshot"], "Original pending instance remains; no replay", "PARTIAL_INTERACTION_NOT_CONSUMED")
        return after

    def drain(self, frame):
        while frame.get("active_event") is not None or frame.get("pending_character_interaction") is not None:
            frame = self.event(frame) if frame.get("active_event") is not None else self.interaction(frame)
        return frame

    def _advance_native_horizon(self, before: JSONObject) -> JSONObject:
        from ck3_mod_acceptance_native_day import obj, integer
        from tools.ck3_mod_acceptance_cases.faith_e02_pilgrimage_contract import (
            parse_pilgrimage_natural_interval, require_pilgrimage_natural_capabilities)
        require_pilgrimage_natural_capabilities(self.natural_capabilities)
        _need(before.get("active_event") is None and before.get("pending_character_interaction") is None,
              "Natural horizon requires the original modal-free frame")
        self.guard(self.limits["one_day_timeout"] + 5)
        self.seq += 1
        name = self.prefix + str(self.seq).zfill(4) + "-native-horizon"
        self.result["day_requests"] += 1
        rows = self.client.execute_plan([{"id": name, "tool": "ck3_execute_step",
            "fresh_revision": False, "args": {"step": "life-advance",
                "expected_revision": before["revision"]}}], name, timeout=self.limits["one_day_timeout"])
        _need(isinstance(rows, list) and len(rows) == 1, "One original natural interval required")
        row = obj(rows[0], "actual natural interval row")
        _need(row.get("ok") is True and not row.get("error"),
              "Original natural interval failed; never replay", "PARTIAL_DAY_UNKNOWN")
        after = obj(self.frame(row.get("after_snapshot"), before), "actual natural after-frame")
        remaining = self.limits["max_days"] * 24 - self.result["elapsed_hours"]
        source = _pin(self.client.output / (name + ".actual-results.json"))
        receipt = {"source": source, "interval": None}
        self.result["natural_horizon_receipts"].append(receipt)
        interval = parse_pilgrimage_natural_interval(row.get("result"),
            before_date_raw=integer(before.get("date_raw"), "natural before date"),
            after_date_raw=integer(after.get("date_raw"), "natural after date"),
            has_event=after.get("active_event") is not None,
            has_interaction=after.get("pending_character_interaction") is not None,
            remaining_hours=remaining)
        receipt["interval"] = interval.to_json()
        self.result["elapsed_hours"] += interval.elapsed_hours
        _need(after["date_raw"] - self.result["initial_date_raw"] == self.result["elapsed_hours"],
              "Natural timeline is not contiguous")
        self.result["observed_days"] = self.result["elapsed_hours"] / 24
        day = {"step_id": row["id"], "requested_days": interval.requested_horizon_days,
            "elapsed_hours": interval.elapsed_hours, "event_boundary": interval.boundary != "none",
            "date_raw": after["date_raw"], "native_clock_step": "life-advance", "source": source}
        self.result["day_receipts"].append(self.record(
            "day-" + str(self.result["day_requests"]).zfill(4), day))
        return after

    def run(self):
        _need(self.identity is not None, "Journey needs one actual initial activity identity")
        if self.advance_mode == "native_horizon":
            from tools.ck3_mod_acceptance_cases.faith_e02_pilgrimage_contract import require_pilgrimage_natural_capabilities
            require_pilgrimage_natural_capabilities(self.natural_capabilities)
            self.result["natural_advance_mode"] = self.advance_mode
            self.result["natural_horizon_receipts"] = []
        self.record("started-once", self.result)
        frame = self.snapshot()
        initial_date = frame["date_raw"]
        self.result["initial_date_raw"] = initial_date
        frame = self.observe_identity(frame, "initial")
        while True:
            handled_before = len(self.result["event_receipts"]) + len(self.result["interaction_receipts"])
            frame = self.drain(frame)
            handled_after = len(self.result["event_receipts"]) + len(self.result["interaction_receipts"])
            if handled_after != handled_before and not self.result["return_observed"]:
                frame = self.observe_identity(frame, "after_actual_interruption")
            elif not self.result["return_observed"] and frame["date_raw"] - self.last_identity_date >= 7 * 24:
                frame = self.observe_identity(frame, "seven_actual_days")
            # A readonly identity/milestone refresh can publish a new modal at
            # the same date after drain. Handle it before attempting any day.
            if frame.get("active_event") is not None or frame.get("pending_character_interaction") is not None:
                continue
            if self.result["return_observed"]:
                self.result["status"] = ("JOURNEY_CONCLUSION_AND_RETURN_EVENT_OBSERVED"
                    if self.result["return_event_chain_complete"] else "PARTIAL_RETURN_EVENT_WITHOUT_CONCLUSION")
                if self.result["terminal_observed"] and self.result["completion_evidence"]["native_invalidated"]:
                    self.result["status"] = "INVALIDATED_PILGRIMAGE_RETURN_EVENT_OBSERVED"
                break
            # native_completed can occur before travel home; keep the original finite day/lease/public caps.
            _need(self.result["day_requests"] < self.limits["max_day_requests"], "Finite day-request cap", "PARTIAL_DAY_REQUEST_CAP")
            # Shared native one-day requests may cover up to 47 actual hours.
            # Keep the final request inside the actual natural-duration cap.
            _need(self.result["elapsed_hours"] + 48 <= self.limits["max_days"] * 24,
                  "Finite natural-duration cap", "PARTIAL_DAY_CAP")
            self.guard(self.limits["one_day_timeout"] + 5)
            from tools.ck3_mod_acceptance_cases.faith_e02_pilgrimage_contract import (
                NATURAL_HORIZON_MAX_DAYS, NATURAL_HORIZON_RESERVE_HOURS)
            remaining = self.limits["max_days"] * 24 - self.result["elapsed_hours"]
            if (self.advance_mode == "native_horizon" and remaining >=
                    NATURAL_HORIZON_MAX_DAYS * 24 + NATURAL_HORIZON_RESERVE_HOURS):
                frame = self.snapshot(frame, same_date=True)
                if frame.get("active_event") is not None or frame.get("pending_character_interaction") is not None:
                    continue
                frame = self._advance_native_horizon(frame)
                continue
            self.result["day_requests"] += 1
            row = self.client.advance_day(days=1, timeout=self.limits["one_day_timeout"], allow_event_boundary=True)
            _need(row.get("ok") is True and not row.get("error"), "Original day request failed; never replay", "PARTIAL_DAY_UNKNOWN")
            value = row["result"]
            before = self.frame(value["before"], frame, same_date=True)
            after = self.frame(row.get("after_snapshot", value["after"]), before)
            hours = value.get("elapsed_hours")
            _need(value.get("requested_days") == 1 and type(hours) is int and 0 <= hours < 48 and
                  after["date_raw"] - before["date_raw"] == hours,
                  "Actual bounded natural interval missing", "PARTIAL_DAY_UNKNOWN")
            boundary = value.get("event_boundary") is not None
            _need((boundary and isinstance(after.get("active_event"), dict)) or
                  (not boundary and value.get("requested_interval_complete") is True and 24 <= hours < 48),
                  "Actual one-day/event boundary differs", "PARTIAL_DAY_UNKNOWN")
            self.result["elapsed_hours"] += hours
            _need(after["date_raw"] - initial_date == self.result["elapsed_hours"], "Natural timeline is not contiguous")
            self.result["observed_days"] = self.result["elapsed_hours"] / 24
            day = {"step_id": row["id"], "requested_days": 1, "elapsed_hours": hours,
                   "requested_interval_complete": value.get("requested_interval_complete"),
                   "event_boundary": boundary, "date_raw": after["date_raw"]}
            self.result["day_receipts"].append(self.record("day-" + str(self.result["day_requests"]).zfill(4), day))
            frame = after
        self.result["last_frame"] = frame
        return self.result


def run_journey(context: JSONObject, client: DayClient, binding: JSONObject,
                initial_activity_identity: JSONObject, limits: dict[str, object], *,
                natural_capabilities: object = None,
                consumed_event_definitions: tuple[str, ...] = ()) -> JSONObject:
    """Continue boundedly through source-bound conclusion/return events; no coordinate or payment inference."""
    journey = _Journey(context, client, binding, initial_activity_identity, limits,
        natural_capabilities=natural_capabilities, consumed_event_definitions=consumed_event_definitions)
    try:
        result = journey.run()
    except JourneyStop as stop:
        result = journey.result
        result.update(status=stop.status, reason=str(stop))
        if stop.status in {"PARTIAL_DAY_CAP", "PARTIAL_DAY_REQUEST_CAP", "PARTIAL_QUIT_RESERVE"}:
            try:
                journey.necessary_final_identity()
            except Exception as error:
                result["final_identity_read_error"] = type(error).__name__ + ": " + str(error)
    except Exception as error:
        result = journey.result
        result.update(status="PARTIAL_ORIGINAL_FAILURE_PRESERVED", reason=type(error).__name__ + ": " + str(error))
    result["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
    if isinstance(journey.last_frame, dict):
        result["last_frame"] = journey.last_frame
    journey.budget_evidence()
    result["result_evidence"] = journey.record("result", result)
    from ck3_mod_acceptance_native_day import obj
    return obj(result, "actual bounded journey result")


def drain_interruptions(context, client, binding, limits):
    """Only current native interruptions; no day request and no activity ID."""
    controller = _Journey(context, client, binding, None, limits)
    controller.record("drain-started-once", controller.result)
    try:
        frame = controller.snapshot()
        frame = controller.drain(frame)
        result = controller.result
        result.update(status="INTERRUPTIONS_DRAINED", last_frame=frame)
    except JourneyStop as stop:
        result = controller.result
        result.update(status=stop.status, reason=str(stop))
    except Exception as error:
        result = controller.result
        result.update(status="PARTIAL_ORIGINAL_FAILURE_PRESERVED", reason=type(error).__name__ + ": " + str(error))
    result.update(handled_events=len(result["event_receipts"]), handled_interactions=len(result["interaction_receipts"]),
                  finished_at_utc=datetime.now(timezone.utc).isoformat())
    if isinstance(controller.last_frame, dict):
        result["last_frame"] = controller.last_frame
    controller.budget_evidence()
    result["result_evidence"] = controller.record("drain-result", result)
    return result
