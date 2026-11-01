package org.xar.ck3.control.application.planning;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.JsonNodeFactory;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.math.BigInteger;
import java.net.URI;
import java.nio.charset.StandardCharsets;
import java.time.Clock;
import java.time.Duration;
import java.time.ZoneOffset;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.admission.deadlinecredit.CampaignDeadline;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.advance.AdvanceHistory;
import org.xar.ck3.control.application.advance.AdvancePlan;
import org.xar.ck3.control.application.advance.AdvanceProgress;
import org.xar.ck3.control.application.advance.ClockStatusRead;
import org.xar.ck3.control.application.capabilities.CampaignRootContextJson;
import org.xar.ck3.control.contracts.FullJsonTree;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Claims;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.service.root.RootOnlineDecisionSelector;
import org.xar.ck3.control.service.root.RootOrdinaryRuntimeConfiguration.DecisionProvider;
import org.xar.ck3.control.wave2.planning.jointshortlist.JointShortlist.Domain;

/** Protocol-derived fixtures: no HTTP, archive reads, D-drive resources or game execution. */
final class CompactPeacefulLifeDecision220Test {
    private static final String SCHEMA = "xar.model-peaceful-life-decision/v1";
    private static final int MATERIAL = 16 * 1024 * 1024;
    private static final Claims EMPTY = new Claims(Set.of(), Set.of(), Set.of(), Set.of());
    private static final Obj EVIDENCE = obj("business_unknown", new Text("visit-evidence-must-survive"),
            "precise", new DecimalValue("1.230000000000000000000000000000e-23"));

    @Test void peacefulEightDayRetainsCompleteCurrentBusinessAndOriginalProposal() throws Exception {
        PlanningRequest initial = request(snapshot(), List.of(), List.of());
        PlanningRequest request = request(snapshot(), history(), List.of(
                fact(initial, "settled-send", ExternalState.SEND_CONFIRMED),
                fact(initial, "settled-reject", ExternalState.REJECTED_CONFIRMED)));
        PlanningResult.ActionSelected selected = selected(request, arguments(plan(8, false,
                AdvancePlan.ClockMode.CAMPAIGN_SENTINEL, true)), "life-advance", false, EMPTY);
        // Source-legal Annotate may retain the exact command/core while accumulating domain data.
        String domainOnly = "ANNOTATED_OTHER_DOMAIN_DO_NOT_EXPORT:" + "f".repeat(100000);
        Obj annotation = obj("family", new Text(domainOnly), "council", obj("receipt", new Text(domainOnly)));
        OrdinaryPolicy.Draft originalDraft = selected.trace().finalPlan().orElseThrow();
        OrdinaryPolicy.Draft annotatedDraft = new OrdinaryPolicy.Draft(originalDraft.policy(), originalDraft.phase(),
                originalDraft.reason(), originalDraft.kind(), originalDraft.command(), originalDraft.purpose(),
                originalDraft.domain(), annotation);
        List<PlanTrace.StageVisit> annotatedVisits = selected.trace().visits().stream().map(visit ->
                new PlanTrace.StageVisit(visit.stage(), visit.outcome(), visit.reason(), visit.source(),
                        Optional.of(annotation))).toList();
        selected = new PlanningResult.ActionSelected(selected.command(),
                new PlanTrace(selected.trace().before(), annotatedVisits, Optional.of(annotatedDraft)));
        Wire wire = wire(request, selected);
        compact(wire);
        JsonNode data = wire.data();
        assertEquals(tree(ActionCodec.encodeCommand(selected.command())), data.get("proposal"));
        assertEquals(selected.command().actionId(), data.path("proposal_id").textValue());
        assertEquals(ActionCodec.bodySha256(selected.command()), data.path("body_sha256").textValue());
        assertEquals(request.deadline().toString(), data.path("planning_deadline").textValue());
        assertEquals(toNode(request.observations().snapshot()), data.get("snapshot"));
        assertEquals(toNode(object(request.observations().snapshot().get("campaign_root_context_query"), "query")),
                data.path("snapshot").path("campaign_root_context_query"));
        assertEquals(arrayOf("game.command.pause-map", ClockStatusRead.ARM_CAP, ClockStatusRead.CANCEL_CAP,
                ClockStatusRead.STATUS_CAP, "game.command.resume-map", "game.command.set-speed-5"),
                data.get("required_capabilities"));
        assertEquals(arrayOf("life-advance", "pause-map", ClockStatusRead.STEP, "resume-map", "set-speed-5"),
                data.get("required_routable_operations"));
        assertFalse(data.has("capabilities"), "required dependencies are a subset, not the full capability registry");
        assertFalse(data.has("routable_operations"), "required static dependencies are not the full operation registry");
        assertEquals(expectedFacts(request), data.get("action_facts"));
        OrdinaryPolicy.Draft draft = selected.trace().finalPlan().orElseThrow();
        assertTrue(containsFields(data, finalBusiness(draft)), "all final-plan business fields must survive together");
        for (PlanTrace.StageVisit visit : selected.trace().visits()) {
            assertTrue(containsFields(data, visitBusiness(visit)), "every business stage visit must survive together");
        }
        assertFalse(data.path("final_plan").has("detail"), "domain detail remains in Java custody");
        JsonNode exportedVisits = data.get("planner_visits");
        assertNotNull(exportedVisits); assertTrue(exportedVisits.isArray());
        assertEquals(selected.trace().visits().size(), exportedVisits.size());
        for (JsonNode visit : exportedVisits) {
            assertFalse(visit.has("evidence")); assertFalse(visit.has("source"));
        }
        assertFalse(containsText(data, domainOnly), "domain annotations must not flow back into this admission task");
        assertEquals(annotation, selected.trace().finalPlan().orElseThrow().detail());
        assertTrue(selected.trace().visits().stream().allMatch(visit -> visit.evidence().orElseThrow().equals(annotation)));
        JsonNode intent = data.get("bounded_stop_intent");
        assertNotNull(intent);
        for (AdvanceProgress.Boundary boundary : AdvanceProgress.Boundary.values()) {
            assertTrue(containsText(intent, boundary.name()), "missing actual Java boundary " + boundary);
        }
        assertFalse(data.has("history"));
        assertFalse(data.has("root_facts"));
        assertFalse(data.has("history_projection_schema"));
    }

    @Test void onlyTheWholeEqualNativeHistoryDuplicateMayDisappear() throws Exception {
        List<Obj> history = history();
        Obj equal = snapshot().with("native_command_history", new Arr(new ArrayList<Value>(history)));
        PlanningRequest request = request(equal, history, List.of());
        Wire duplicated = wire(request, selected(request));
        compact(duplicated);
        ObjectNode expected = (ObjectNode) toNode(equal);
        expected.remove("native_command_history");
        assertEquals(expected, duplicated.data().get("snapshot"));
        Obj unequal = snapshot().with("native_command_history", new Arr(List.of(obj("not_actual_history", new Bool(true)))));
        PlanningRequest different = request(unequal, history, List.of());
        Wire retained = wire(different, selected(different));
        compact(retained);
        assertEquals(toNode(unequal), retained.data().get("snapshot"));
    }

    @Test void warArmyAndUnsafeForegroundRequireFullLegacy() throws Exception {
        for (Obj snapshot : List.of(
                snapshot().with("active_wars", new Arr(List.of(obj("war_id", integer(17))))),
                snapshot().with("player_armies", new Arr(List.of(obj("army_id", integer(19))))),
                snapshot().with("active_event", obj("event_id", new Text("event-1"))),
                snapshot().with("pending_character_interaction", obj("interaction_id", integer(2))),
                snapshot().with("one_life_terminal_reason", new Text("player_dead")),
                snapshot().with("top_exclusive_modal_choice_hint", obj("status", new Text("present"))),
                snapshot().with("top_exclusive_modal_choice_hint", obj("status", new Text("absent"))),
                // episode_transition cache shape is not a closed pending predicate.
                snapshot().with("one_life_terminal", new Bool(true)),
                snapshot().with("episode_identity_pending", new Bool(true)),
                without(snapshot(), "one_life_terminal"),
                without(snapshot(), "episode_identity_pending"),
                without(snapshot(), "active_event"),
                snapshot().with("cold_candidate_rejection", new Text("unaccepted-state")),
                snapshot().with("driver_state_error", new Text("state unavailable")),
                snapshot().with("played_character", obj("character_id", integer(29829), "alive", new Bool(false))))) {
            PlanningRequest request = request(snapshot, history(), List.of());
            legacy(wire(request, selected(request)), request);
        }
    }

    @Test void unresolvedActionWarWatchAndOpenAssaultCannotBeSummarizedAway() throws Exception {
        PlanningRequest before = request(snapshot(), history(), List.of());
        PlanningRequest unknown = request(snapshot(), history(), List.of(fact(before, "unresolved", ExternalState.UNKNOWN)));
        legacy(wire(unknown, selected(unknown)), unknown);
        List<Obj> watch = List.of(obj("index", integer(1), "command", new Text("life-advance"), "ok", new Bool(false),
                "result", obj("schema", new Text("xar.war-daily-watch-unresolved.v1"), "never_replay", new Bool(true))));
        assertTrue(AdvanceHistory.unresolvedWarWatch(watch));
        PlanningRequest warWatch = request(snapshot(), watch, List.of());
        legacy(wire(warWatch, selected(warWatch)), warWatch);
        List<Obj> assault = List.of(obj("index", integer(1), "command", new Text("start-assault-3"), "ok", new Bool(true),
                "result", obj("assault_action", obj("status", new Text("assault_started"), "war_id", integer(1),
                        "province_id", integer(2), "siege_id", integer(3)))));
        assertEquals(1, AdvanceHistory.openAssaults(assault).size());
        PlanningRequest openAssault = request(snapshot(), assault, List.of());
        legacy(wire(openAssault, selected(openAssault)), openAssault);
    }

    @Test void currentRootIsMandatoryCompleteTypedAndBoundToEveryCurrentCacheField() throws Exception {
        Obj snapshot = snapshot();
        Obj query = object(snapshot.get("campaign_root_context_query"), "query");
        Obj root = object(query.get("campaign_root_context"), "root");
        Obj binding = object(query.get("cache_binding"), "cache_binding");
        List<Obj> invalid = new ArrayList<>();
        invalid.add(without(snapshot, "campaign_root_context_query"));
        invalid.add(snapshot.with("campaign_root_context_query", query.with("campaign_root_context", obj("root_ref", integer(0)))));
        invalid.add(snapshot.with("campaign_root_context_query", query.with("query_sequence", integer(0))));
        invalid.add(snapshot.with("campaign_root_context_query", query.with("campaign_root_context", root.with("snapshot_revision", integer(2)))));
        invalid.add(snapshot.with("campaign_root_context_query", query.with("campaign_root_context", root.with("schema_version", integer(2)))));
        invalid.add(snapshot.with("campaign_root_context_query", query.with("campaign_root_context", root.with("schema_version", new Text("1")))));
        invalid.add(snapshot.with("campaign_root_context_query", query.with("campaign_root_context", new Text("not-a-root"))));
        invalid.add(snapshot.with("campaign_root_context_query", query.with("campaign_root_context", root.with("date_raw", integer(24024)))));
        invalid.add(snapshot.with("campaign_root_context_query", query.with("campaign_root_context", without(root, "provenance"))));
        invalid.add(snapshot.with("campaign_root_context_query", query.with("cache_binding", Nil.INSTANCE)));
        for (String key : binding.members().keySet()) {
            Value bad = key.equals("snapshot_id") ? new Text("older-snapshot") : integer(99999);
            invalid.add(snapshot.with("campaign_root_context_query", query.with("cache_binding", binding.with(key, bad))));
            invalid.add(snapshot.with("campaign_root_context_query", query.with("cache_binding", without(binding, key))));
        }
        invalid.add(snapshot.with("diagnostics", object(snapshot.get("diagnostics"), "diagnostics").with("connection_generation", integer(2))));
        for (Obj invalidSnapshot : invalid) {
            PlanningRequest request = request(invalidSnapshot, history(), List.of());
            legacy(wire(request, selected(request)), request);
        }
        // A complete ROOT in historical data is still not the current snapshot cache.
        List<Obj> older = List.of(obj("index", integer(1), "command", new Text("historical-root"), "ok", new Bool(true),
                "result", obj("campaign_root_context", root)));
        PlanningRequest historyOnly = request(without(snapshot, "campaign_root_context_query"), older, List.of());
        legacy(wire(historyOnly, selected(historyOnly)), historyOnly);
    }

    @Test void unsupportedPlansOperationsAndOriginalProposalContractsUseLegacy() throws Exception {
        PlanningRequest request = request(snapshot(), history(), List.of());
        AdvancePlan good = plan(8, false, AdvancePlan.ClockMode.CAMPAIGN_SENTINEL, true);
        List<Obj> unsupported = new ArrayList<>();
        unsupported.add(arguments(plan(1, true, AdvancePlan.ClockMode.EXACT_SENTINEL, false)));
        unsupported.add(arguments(plan(8, false, AdvancePlan.ClockMode.POLLED, false)));
        unsupported.add(arguments(plan(9, false, AdvancePlan.ClockMode.CAMPAIGN_SENTINEL, true)));
        unsupported.add(obj(AdvancePlan.KEY, without(good.json(), "war_daily_watch").with("schema", new Text(AdvancePlan.LEGACY_SCHEMA))));
        unsupported.add(obj(AdvancePlan.KEY, good.json().with("policy", new Text("war_daily_watch"))
                .with("war_daily_watch", obj("unsupported", new Bool(true)))));
        unsupported.add(obj(AdvancePlan.KEY, good.json().with("schema", new Text("unsupported-plan-v99"))));
        for (Obj args : unsupported) legacy(wire(request, selected(request, args, "life-advance", false, EMPTY)), request);
        legacy(wire(request, selected(request, arguments(good), "life-advance-one-day", false, EMPTY)), request);
        legacy(wire(request, selected(request, arguments(good), "unknown-operation", false, EMPTY)), request);
        legacy(wire(request, selected(request, arguments(good), "life-advance", true, EMPTY)), request);
        Claims claims = new Claims(Set.of(), Set.of(), Set.of(BigInteger.valueOf(29829)), Set.of());
        legacy(wire(request, selected(request, arguments(good), "life-advance", false, claims)), request);
        PlanningResult.ActionSelected valid = selected(request);
        ActionCommand original = valid.command();
        ExpectedPostcondition wrongValues = new ExpectedPostcondition(1, request.before(), request.source(), AdvancePlan.OBSERVER,
                List.of(new ExpectedBoolean(new FieldKey("advance.completion_verified"), false)));
        ActionCommand crossedExpected = new ActionCommand(original.actionId(), request.before(), request.source(), request.sessionId(),
                original.operation(), original.arguments(), wrongValues, EMPTY, original.deadline());
        legacy(wire(request, withCommand(valid, crossedExpected)), request);
        PlanningRequest otherSession = new PlanningRequest(request.before(), request.source(), "other-session", request.deadline(), request.observations());
        legacy(wire(otherSession, valid), otherSession);
        for (String missing : List.of("life-advance", "pause-map", "resume-map", "set-speed-5", ClockStatusRead.STEP)) {
            Set<OperationKey> operations = new java.util.HashSet<>(request.observations().actionSteps());
            assertTrue(operations.remove(new OperationKey(missing)));
            PlanningRequest incomplete = withAdvertisements(request, operations, request.observations().bridgeCapabilities());
            legacy(wire(incomplete, selected(incomplete)), incomplete);
        }
        for (String missing : List.of("game.command.pause-map", "game.command.resume-map", "game.command.set-speed-5",
                ClockStatusRead.ARM_CAP, ClockStatusRead.STATUS_CAP, ClockStatusRead.CANCEL_CAP)) {
            Set<String> capabilities = new java.util.HashSet<>(request.observations().bridgeCapabilities());
            assertTrue(capabilities.remove(missing));
            PlanningRequest incomplete = withAdvertisements(request, request.observations().actionSteps(), capabilities);
            legacy(wire(incomplete, selected(incomplete)), incomplete);
        }
    }

    @Test void completeEnvelopeCapFallsBackWithoutCroppingUnknownCurrentFacts() throws Exception {
        String large = "unknown-current-business-fact:" + "界".repeat(30000);
        Obj huge = snapshot().with("future_business_fact", new Text(large));
        PlanningRequest request = request(huge, history(), List.of());
        Wire wire = wire(request, selected(request));
        legacy(wire, request);
        assertEquals(large, wire.data().path("snapshot").path("future_business_fact").textValue());
        assertTrue(wire.bytes().length > 65536, "legacy full request retains oversize facts");
    }

    @Test void formatterDoesNotMutateOriginalInputsOrChangeProposalIdentity() throws Exception {
        PlanningRequest request = request(snapshot(), history(), List.of());
        PlanningResult.ActionSelected selected = selected(request);
        byte[] command = ActionCodec.encodeCommand(selected.command());
        byte[] snapshot = encode(request.observations().snapshot());
        byte[] history = encode(new Arr(new ArrayList<Value>(request.observations().history())));
        String sha = ActionCodec.bodySha256(selected.command());
        Wire first = wire(request, selected), second = wire(request, selected);
        compact(first); compact(second);
        assertArrayEquals(first.bytes(), second.bytes());
        assertArrayEquals(command, ActionCodec.encodeCommand(selected.command()));
        assertArrayEquals(snapshot, encode(request.observations().snapshot()));
        assertArrayEquals(history, encode(new Arr(new ArrayList<Value>(request.observations().history()))));
        assertEquals(sha, ActionCodec.bodySha256(selected.command()));
        assertEquals(tree(command), first.data().get("proposal"));
        assertEquals(selected.command().actionId(), first.data().path("proposal_id").textValue());
        assertEquals(sha, first.data().path("body_sha256").textValue());
    }

    private static Obj snapshot() {
        Obj root = jsonObject("""
                {"schema_version":1,"status":"available","snapshot_revision":1,"date_raw":24000,
                 "local_player_id":0,"player_character_id":29829,"player_character_alive":true,
                 "primary_title":null,"capital_province_id":null,"immediate_liege_character_id":null,
                 "top_liege_character_id":29829,"independent":true,"government":null,
                 "selected_game_rule_tokens":[],"native_selected_game_rule_token_count":0,
                 "readiness":{"capital_ready":true,"government_ready":true,"lieges_ready":true,
                   "player_identity_ready":true,"primary_title_ready":true,"ready":true,
                   "same_frame_ready":true,"selected_game_rule_tokens_ready":true},
                 "unavailable_reason":null,
                 "provenance":{"game_version":"1.20.0.4",
                   "executable_sha256":"98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518",
                   "backend_id":"ck3-1.20.0.4-native-campaign-root-context-v1",
                   "primary_title_rva":"0x289DA10","capital_province_rva":"0x28B1CB0",
                   "immediate_liege_rva":"0x28BFC50","top_liege_rva":"0x28BFD80",
                   "government_rva":"0x28C2DF0","selected_game_rule_service_slot_rva":"0x5CB3D78"}}
                """);
        assertEquals(root, CampaignRootContextJson.normalize(root, BigInteger.valueOf(24000), BigInteger.ONE),
                "fixture must itself satisfy the real current ROOT normalizer");
        Obj binding = obj("snapshot_id", new Text("snapshot-1"), "revision", integer(1), "native_revision", integer(1),
                "date_raw", integer(24000), "actor_character_id", integer(29829), "bridge_pid", integer(123),
                "connection_generation", integer(1));
        return PlanningFixtures.snapshot()
                .with("one_life_terminal", new Bool(false)).with("episode_identity_pending", new Bool(false))
                .with("active_event", Nil.INSTANCE).with("pending_character_interaction", Nil.INSTANCE)
                .with("one_life_terminal_reason", Nil.INSTANCE).with("episode_transition", Nil.INSTANCE)
                .with("episode_transition_error", Nil.INSTANCE).with("driver_state_error", Nil.INSTANCE)
                .with("cold_candidate_rejection", Nil.INSTANCE)
                .with("top_exclusive_modal_choice_hint", Nil.INSTANCE)
                .with("campaign_root_context_query", obj("query_sequence", integer(1), "campaign_root_context", root,
                        "cache_binding", binding))
                .with("unknown_current_fields", obj("not_a_success_claim", new Text("retain-me"),
                        "large_integer", new IntegerValue(new BigInteger("18446744073709551615")),
                        "signed_zero", new DecimalValue("-0.000"),
                        "precise_decimal", new DecimalValue("1.23456789012345678901234567890e-17")));
    }

    private static PlanningRequest request(Obj snapshot, List<Obj> history, List<ExternalFact> facts) {
        PlanningRequest baseline = PlanningFixtures.request(PlanningFixtures.snapshot(), List.of(), Set.of());
        PlanningObservation observations = new PlanningObservation(snapshot, history,
                Set.of(new OperationKey("life-advance"), new OperationKey("pause-map"),
                        new OperationKey("query-campaign-root-context-v1"), new OperationKey(ClockStatusRead.STEP),
                        new OperationKey("resume-map"), new OperationKey("set-speed-5")),
                Set.of("zeta-capability", "alpha-capability", "game.command.pause-map", "game.command.resume-map",
                        "game.command.set-speed-5", ClockStatusRead.ARM_CAP, ClockStatusRead.STATUS_CAP,
                        ClockStatusRead.CANCEL_CAP), Optional.empty(), facts, Optional.empty(), Optional.empty(), false);
        assertTrue(ClockStatusRead.available(observations.bridgeCapabilities()), "fixture advertises actual clock ports");
        return new PlanningRequest(baseline.before(), baseline.source(), baseline.sessionId(), baseline.deadline(), observations);
    }

    private static PlanningRequest withAdvertisements(PlanningRequest request, Set<OperationKey> operations, Set<String> capabilities) {
        PlanningObservation old = request.observations();
        PlanningObservation replacement = new PlanningObservation(old.snapshot(), old.history(), operations, capabilities,
                old.battleSpeedReadiness(), old.actionFacts(), old.campaignGoal(), old.crossRunPlan(), old.initialLifestyleFocusRequired());
        return new PlanningRequest(request.before(), request.source(), request.sessionId(), request.deadline(), replacement);
    }

    private static AdvancePlan plan(int days, boolean exact, AdvancePlan.ClockMode mode, boolean capped) {
        BigInteger start = BigInteger.valueOf(24000), end = start.add(AdvancePlan.DAY.multiply(BigInteger.valueOf(days)));
        Optional<CampaignDeadline.Cap> cap = capped ? Optional.of(new CampaignDeadline.Cap("fixture-campaign",
                CampaignDeadline.CALENDAR_PROFILE, start, end, start.add(BigInteger.valueOf(720)),
                start.add(BigInteger.valueOf(1440)), end, CampaignDeadline.Status.ADVANCE)) : Optional.empty();
        return new AdvancePlan(start, end, days, 5, "bounded_non_tactical", exact, mode, cap);
    }

    private static PlanningResult.ActionSelected selected(PlanningRequest request) {
        return selected(request, arguments(plan(8, false, AdvancePlan.ClockMode.CAMPAIGN_SENTINEL, true)), "life-advance", false, EMPTY);
    }

    private static PlanningResult.ActionSelected selected(PlanningRequest request, Obj args, String operation,
            boolean wrongExpected, Claims claims) {
        AdvancePlan expectedPlan = plan(8, false, AdvancePlan.ClockMode.CAMPAIGN_SENTINEL, true);
        try { expectedPlan = AdvancePlan.decode(object(args.get(AdvancePlan.KEY), "advance")); }
        catch (IllegalArgumentException malformedUnsupportedFixture) { /* malformed plans test legacy fallback */ }
        ExpectedPostcondition expected = new ExpectedPostcondition(1, request.before(), request.source(),
                wrongExpected ? "fixture-wrong-observer/v1" : AdvancePlan.OBSERVER, expectedPlan.expected());
        ActionCommand command = new ActionCommand("compact-fixture-action", request.before(), request.source(), request.sessionId(),
                new OperationKey(operation), args, expected, claims, request.deadline());
        OrdinaryPolicy.Draft draft = new OrdinaryPolicy.Draft("business-policy", "business-phase", "business reason retained",
                OrdinaryPolicy.Kind.ORDINARY, Optional.of(command), OrdinaryPolicy.Purpose.DATE_ADVANCE,
                Optional.of(Domain.lifestyle), args.get("plan") instanceof Obj detail ? detail : selectedDetail(operation));
        List<PlanTrace.StageVisit> visits = List.of(
                new PlanTrace.StageVisit(PlanningStage.CROWN_AUTHORITY, PlanTrace.Outcome.KEPT, "first business visit",
                        Optional.of(PlanningFixtures.SOURCE), Optional.of(EVIDENCE)),
                new PlanTrace.StageVisit(PlanningStage.CAMPAIGN_ADVANCE_CAP, PlanTrace.Outcome.REPLACED, "campaign bound retained",
                        Optional.empty(), Optional.of(obj("unknown_business", new Text("second-evidence")))));
        return new PlanningResult.ActionSelected(command, new PlanTrace(request.before(), visits, Optional.of(draft)));
    }

    private static Obj arguments(AdvancePlan plan) {
        return obj(AdvancePlan.KEY, plan.json(), "plan", selectedDetail("life-advance"),
                "original_unknown_argument", obj("text", new Text("retain-original-proposal")));
    }

    private static Obj selectedDetail(String operation) {
        return obj("selected_step", new Text(operation), "policy", new Text("business-policy"),
                "phase", new Text("business-phase"), "reason", new Text("business reason retained"),
                "complete_business_detail", EVIDENCE);
    }

    private static ExternalFact fact(PlanningRequest request, String id, ExternalState state) {
        return new ExternalFact(id, "b".repeat(64), request.before(), state, UnknownScope.GLOBAL,
                Domain.lifestyle, EMPTY, PlanningFixtures.SOURCE);
    }

    private static PlanningResult.ActionSelected withCommand(PlanningResult.ActionSelected selected, ActionCommand command) {
        OrdinaryPolicy.Draft old = selected.trace().finalPlan().orElseThrow();
        OrdinaryPolicy.Draft replacement = new OrdinaryPolicy.Draft(old.policy(), old.phase(), old.reason(), old.kind(),
                Optional.of(command), old.purpose(), old.domain(), old.detail());
        return new PlanningResult.ActionSelected(command,
                new PlanTrace(selected.trace().before(), selected.trace().visits(), Optional.of(replacement)));
    }

    private static List<Obj> history() {
        return List.of(obj("index", integer(1), "command", new Text("fixture-history-with-business-data"),
                "ok", new Bool(true), "result", obj("historical_only", new Text("do-not-copy-to-compact"))));
    }

    private record Wire(byte[] bytes, JsonNode envelope, JsonNode data) { }

    private static Wire wire(PlanningRequest request, PlanningResult.ActionSelected selected) throws Exception {
        DecisionProvider config = new DecisionProvider(URI.create("http://127.0.0.1:1/v1"), "fixture-model",
                Duration.ofSeconds(10), 1, Duration.ZERO);
        RootOnlineDecisionSelector selector = new RootOnlineDecisionSelector(config,
                Clock.fixed(PlanningFixtures.NOW, ZoneOffset.UTC), raw -> { throw new AssertionError("no material I/O expected"); });
        Method payload = RootOnlineDecisionSelector.class.getDeclaredMethod("requestPayload", PlanningRequest.class,
                PlanningResult.ActionSelected.class, String.class);
        payload.setAccessible(true);
        byte[] bytes;
        try { bytes = (byte[]) payload.invoke(selector, request, selected, ActionCodec.bodySha256(selected.command())); }
        catch (InvocationTargetException failure) {
            Throwable cause = failure.getCause();
            if (cause instanceof Exception exception) throw exception;
            if (cause instanceof Error error) throw error;
            throw failure;
        }
        JsonNode envelope = tree(bytes);
        JsonNode data = tree(envelope.path("messages").get(1).path("content").textValue().getBytes(StandardCharsets.UTF_8));
        assertEquals("fixture-model", envelope.path("model").textValue());
        assertEquals(256, envelope.path("max_tokens").intValue());
        assertTrue(envelope.path("stream").booleanValue());
        return new Wire(bytes, envelope, data);
    }

    private static void compact(Wire wire) {
        assertEquals(SCHEMA, wire.data().path("decision_context_schema").textValue());
        assertEquals("peaceful_clock_advance_admission/v1", wire.data().path("decision_scope").textValue());
        assertTrue(wire.bytes().length <= 65536, "cap applies to complete UTF8 HTTP envelope");
    }

    private static void legacy(Wire wire, PlanningRequest request) {
        assertFalse(wire.data().has("decision_context_schema"));
        assertFalse(wire.data().has("decision_scope"));
        assertEquals("xar.model-root-history-dictionary/v1", wire.data().path("history_projection_schema").textValue());
        assertEquals(toNode(new Arr(new ArrayList<Value>(request.observations().history()))), wire.data().get("history"));
        assertEquals(toNode(request.observations().snapshot()), wire.data().get("snapshot"));
    }

    private static ArrayNode expectedFacts(PlanningRequest request) {
        ArrayNode facts = JsonNodeFactory.instance.arrayNode();
        for (ExternalFact fact : request.observations().actionFacts()) {
            ObjectNode node = facts.addObject(); node.put("action_id", fact.actionId()); node.put("body_sha256", fact.bodySha256());
            node.put("state", fact.state().name()); node.put("unresolved", fact.unresolved()); node.put("scope", fact.scope().name());
            node.put("domain", String.valueOf(fact.domain())); node.set("affected_claims", ActionCodec.claims(fact.affectedClaims()));
        }
        return facts;
    }

    private static ObjectNode finalBusiness(OrdinaryPolicy.Draft draft) {
        ObjectNode node = JsonNodeFactory.instance.objectNode(); node.put("policy", draft.policy()); node.put("phase", draft.phase());
        node.put("reason", draft.reason()); node.put("kind", draft.kind().name()); node.put("purpose", draft.purpose().name());
        node.put("domain", draft.domain().orElseThrow().name()); return node;
    }

    private static ObjectNode visitBusiness(PlanTrace.StageVisit visit) {
        ObjectNode node = JsonNodeFactory.instance.objectNode(); node.put("stage", visit.stage().name()); node.put("outcome", visit.outcome().name());
        node.put("reason", visit.reason()); return node;
    }

    private static boolean containsFields(JsonNode node, ObjectNode expected) {
        if (node.isObject()) {
            boolean same = true;
            for (var field : expected.properties()) if (!field.getValue().equals(node.get(field.getKey()))) same = false;
            if (same) return true;
        }
        for (JsonNode child : node) if (containsFields(child, expected)) return true;
        return false;
    }

    private static boolean containsText(JsonNode node, String expected) {
        if (node.isTextual() && expected.equals(node.textValue())) return true;
        for (JsonNode child : node) if (containsText(child, expected)) return true;
        return false;
    }

    private static ArrayNode arrayOf(String... values) {
        ArrayNode array = JsonNodeFactory.instance.arrayNode(); for (String value : values) array.add(value); return array;
    }
    private static JsonNode tree(byte[] bytes) { return FullJsonTree.parse(bytes, MATERIAL); }
    private static Obj jsonObject(String json) { return object(OpportunityJson.parseComplete(json.getBytes(StandardCharsets.UTF_8), MATERIAL), "fixture"); }
    private static IntegerValue integer(long value) { return new IntegerValue(BigInteger.valueOf(value)); }
    private static Obj without(Obj value, String key) { Map<String, Value> copy = new LinkedHashMap<>(value.members()); copy.remove(key); return new Obj(copy); }
    private static Obj obj(Object... pairs) {
        Map<String, Value> values = new LinkedHashMap<>();
        for (int i = 0; i < pairs.length; i += 2) values.put((String) pairs[i], (Value) pairs[i + 1]);
        return new Obj(values);
    }
}
