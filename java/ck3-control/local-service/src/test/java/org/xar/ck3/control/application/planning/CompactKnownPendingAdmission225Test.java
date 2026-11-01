package org.xar.ck3.control.application.planning;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.JsonNodeFactory;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.InputStream;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.math.BigInteger;
import java.net.URI;
import java.nio.charset.StandardCharsets;
import java.time.Clock;
import java.time.Duration;
import java.time.ZoneOffset;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.function.Consumer;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.FullJsonTree;
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Claims;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionModels.*;
import org.xar.ck3.control.nativebridge.capabilities.interactions.KnownPendingInteractionEffects;
import org.xar.ck3.control.nativebridge.capabilities.interactions.KnownPendingInteractionPlanCodec;
import org.xar.ck3.control.nativebridge.capabilities.interactions.KnownPendingInteractionPlans;
import org.xar.ck3.control.nativebridge.capabilities.interactions.KnownPendingInteractionPostcondition;
import org.xar.ck3.control.nativebridge.capabilities.interactions.KnownPendingInteractionRules;
import org.xar.ck3.control.nativebridge.capabilities.interactions.KnownPendingInteractionRules.Action;
import org.xar.ck3.control.nativebridge.capabilities.interactions.KnownPendingInteractionRules.Classification;
import org.xar.ck3.control.nativebridge.capabilities.interactions.PendingContextCodec;
import org.xar.ck3.control.service.root.RootOnlineDecisionSelector;
import org.xar.ck3.control.service.root.RootOrdinaryRuntimeConfiguration.DecisionProvider;
import org.xar.ck3.control.wave2.planning.jointshortlist.JointShortlist.Domain;

/** Source-derived software admission fixtures; no Complete/native/source authority, network or private test-jar. */
final class CompactKnownPendingAdmission225Test {
    private static final int LIMIT = 16 * 1024 * 1024, PENDING = -2_130_706_399;
    private static final String STEP = "reject-pending-character-interaction", CAP = "game.command." + STEP;
    private static final Claims EMPTY = new Claims(Set.of(), Set.of(), Set.of(), Set.of());
    private static final List<Obj> HISTORY = List.of(new Obj(Map.of("index", integer(1), "command", new Text("fixture-history"),
            "ok", new Bool(true), "result", new Obj(Map.of("business", new Text("retained-only-on-legacy"))))));

    @Test void actualTypedMarriageRejectRetainsFullProposalSnapshotAndExplicitlyStaleRoot() throws Exception {
        Fixture fixture = fixture(false);
        assertEquals(Classification.KNOWN_MARRIAGE, fixture.plan().classification());
        assertEquals("arrange-marriage-reject-only-v1", fixture.plan().ruleId());
        assertEquals(Optional.of(Action.REJECT), fixture.plan().selected());
        assertEquals(fixture.plan(), KnownPendingInteractionPlanCodec.decode(KnownPendingInteractionPlanCodec.encode(fixture.plan())));
        assertEquals(STEP, KnownPendingInteractionEffects.preparation().prepare(fixture.selected().command()).step());
        Wire wire = wire(fixture.request(), fixture.selected()); compact(wire);
        JsonNode data = wire.data(); ActionCommand command = fixture.selected().command();
        assertEquals(tree(ActionCodec.encodeCommand(command)), data.get("proposal"));
        assertEquals(command.actionId(), data.path("proposal_id").textValue());
        assertEquals(ActionCodec.bodySha256(command), data.path("body_sha256").textValue());
        assertEquals(fixture.request().deadline().toString(), data.path("planning_deadline").textValue());
        assertEquals("required_action_subset/v1", data.path("hello_capabilities_projection").textValue());
        assertEquals("retained_cache_only_not_used_for_marriage_reply_admission", data.path("root_context_scope").textValue());
        assertTrue(data.path("current_root_verified_for_request").isBoolean());
        assertFalse(data.path("current_root_verified_for_request").booleanValue());
        String dependencyScope = data.path("dependency_scope").asText().toLowerCase(java.util.Locale.ROOT);
        assertTrue(dependencyScope.contains("required") || dependencyScope.contains("subset"));
        assertEquals(array(CAP), data.get("required_capabilities"));
        assertEquals(array(STEP), data.get("required_routable_operations"));
        ObjectNode expectedSnapshot = (ObjectNode) toNode(fixture.request().observations().snapshot());
        ((ObjectNode) expectedSnapshot.path("diagnostics").get("hello")).set("capabilities", array(CAP));
        assertEquals(expectedSnapshot, data.get("snapshot"), "only the approved hello.capabilities technical field may change");
        assertEquals(toNode(fixture.request().observations().snapshot()).path("campaign_root_context_query"),
                data.path("snapshot").get("campaign_root_context_query"));
        assertEquals(facts(fixture.request()), data.get("action_facts"));
        assertEquals(core(fixture.selected().trace().finalPlan().orElseThrow()), data.get("final_plan"));
        JsonNode visits = data.get("planner_visits"); assertNotNull(visits); assertEquals(1, visits.size());
        assertEquals("FAMILY_AND_EDUCATION", visits.get(0).path("stage").textValue());
        assertEquals("REPLACED", visits.get(0).path("outcome").textValue());
        assertEquals("actual marriage reject selection", visits.get(0).path("reason").textValue());
        assertFalse(visits.get(0).has("evidence")); assertFalse(visits.get(0).has("source"));
    }

    @Test void typedOperationCapabilityAndCurrentContextBindingAreRequired() throws Exception {
        Fixture fixture = fixture(false); PlanningRequest request = fixture.request();
        PlanningObservation observed = request.observations();
        for (boolean missingOperation : List.of(true, false)) {
            Set<OperationKey> steps = missingOperation ? Set.of(new OperationKey("query-campaign-root-context-v1")) : observed.actionSteps();
            Set<String> caps = missingOperation ? observed.bridgeCapabilities() : Set.of("unrelated-capability");
            PlanningRequest changed = request(request, observed.snapshot(), steps, caps, observed.actionFacts());
            legacy(wire(changed, fixture.selected()), changed);
        }
        for (Consumer<ObjectNode> mutation : List.<Consumer<ObjectNode>>of(
                args -> ((ObjectNode) args.get("group_context")).put("connection_generation", 135),
                args -> ((ObjectNode) args.path("group_context").get("controls")).put("speed", 4),
                args -> ((ObjectNode) args.path("group_context").path("controls").get("pending")).put("sender_id", 502))) {
            ActionCommand changed = changed(fixture.selected().command(), mutation);
            legacy(wire(request, select(changed, fixture.selected().trace().finalPlan().orElseThrow().detail())), request);
        }
    }

    @Test void malformedSchemaProvenanceAndSourceBlockedRuleUseCompleteLegacy() throws Exception {
        Fixture fixture = fixture(false);
        for (Consumer<ObjectNode> mutation : List.<Consumer<ObjectNode>>of(
                args -> ((ObjectNode) args.path("known_pending_plan").get("java_policy_plan")).put("schema", "unsupported-v99"),
                args -> ((ObjectNode) nativeContext(args).get("provenance")).put("reply_validator_rva", "0x1"),
                args -> nativeContext(args).put("schema_version", 2),
                args -> ((ObjectNode) nativeContext(args).get("roles")).put("intermediary_character_id", 999),
                args -> ((ObjectNode) args.path("known_pending_plan").path("original_context_wrapper")).put("queried_revision", 499))) {
            ActionCommand changed = changed(fixture.selected().command(), mutation);
            legacy(wire(fixture.request(), select(changed, fixture.selected().trace().finalPlan().orElseThrow().detail())), fixture.request());
        }
        Fixture ordinary = fixture(true);
        assertEquals(Classification.ORDINARY, ordinary.plan().classification());
        assertEquals(STEP, KnownPendingInteractionEffects.preparation().prepare(ordinary.selected().command()).step());
        legacy(wire(ordinary.request(), ordinary.selected()), ordinary.request());
    }

    @Test void warArmyUnresolvedFactsAndUnknownHelloShapesCannotBorrowThisAdmission() throws Exception {
        Fixture fixture = fixture(false); PlanningRequest original = fixture.request();
        for (String field : List.of("active_wars", "player_armies")) {
            Obj snapshot = original.observations().snapshot().with(field, new Arr(List.of(new Obj(Map.of("id", integer(17))))));
            PlanningRequest changed = request(original, snapshot, original.observations().actionSteps(), original.observations().bridgeCapabilities(), original.observations().actionFacts());
            legacy(wire(changed, fixture.selected()), changed);
        }
        ExternalFact unknown = new ExternalFact("unresolved-fixture", "d".repeat(64), original.before(), ExternalState.UNKNOWN,
                UnknownScope.GLOBAL, Domain.marriage, EMPTY, PlanningFixtures.SOURCE);
        PlanningRequest unresolved = request(original, original.observations().snapshot(), original.observations().actionSteps(),
                original.observations().bridgeCapabilities(), List.of(unknown));
        legacy(wire(unresolved, fixture.selected()), unresolved);
        ObjectNode snapshot = (ObjectNode) toNode(original.observations().snapshot());
        ((ObjectNode) snapshot.path("diagnostics").get("hello")).put("capabilities", "unknown-registry-shape");
        PlanningRequest malformed = request(original, app(snapshot), original.observations().actionSteps(), original.observations().bridgeCapabilities(), original.observations().actionFacts());
        legacy(wire(malformed, fixture.selected()), malformed);
    }

    @Test void unknownCurrentFactsOverTheCompleteWireBudgetCauseWholeFallbackWithoutCropping() throws Exception {
        Fixture fixture = fixture(false); String huge = "unfamiliar-current-fact:" + "界".repeat(30000);
        Obj snapshot = fixture.request().observations().snapshot().with("future_business_fact", new Text(huge));
        PlanningRequest request = request(fixture.request(), snapshot, fixture.request().observations().actionSteps(),
                fixture.request().observations().bridgeCapabilities(), fixture.request().observations().actionFacts());
        Wire wire = wire(request, fixture.selected()); legacy(wire, request);
        assertEquals(huge, wire.data().path("snapshot").path("future_business_fact").textValue()); assertTrue(wire.bytes().length > 65536);
    }

    @Test void domainAnnotationsRemainInJavaAndDoNotReplaceTheCompleteOriginalKnownPlan() throws Exception {
        Fixture fixture = fixture(false); Obj annotation = new Obj(Map.of("other_domain", new Text("annotation:" + "x".repeat(100000))));
        PlanningResult.ActionSelected annotated = select(fixture.selected().command(), annotation);
        Wire wire = wire(fixture.request(), annotated); compact(wire);
        assertEquals(tree(ActionCodec.encodeCommand(fixture.selected().command())), wire.data().get("proposal"));
        assertFalse(wire.data().path("final_plan").has("detail"));
        assertEquals(annotation, annotated.trace().finalPlan().orElseThrow().detail());
    }

    @Test void formattingAndPublicCodecRoundtripKeepAllOriginalCommandAndSnapshotInputsImmutable() throws Exception {
        Fixture fixture = fixture(false); ActionCommand command = fixture.selected().command();
        byte[] before = ActionCodec.encodeCommand(command), snapshot = encode(fixture.request().observations().snapshot());
        ActionCommand cold = ActionCodec.decodeCommand(before);
        Wire first = wire(fixture.request(), select(cold, fixture.selected().trace().finalPlan().orElseThrow().detail())); compact(first);
        assertArrayEquals(before, ActionCodec.encodeCommand(command)); assertArrayEquals(before, ActionCodec.encodeCommand(cold));
        assertArrayEquals(snapshot, encode(fixture.request().observations().snapshot()));
        assertEquals(command.expected(), cold.expected()); assertEquals(command.claims(), cold.claims());
        assertEquals(command.arguments(), cold.arguments()); assertEquals(ActionCodec.bodySha256(command), ActionCodec.bodySha256(cold));
    }

    private record Fixture(PlanningRequest request, PlanningResult.ActionSelected selected, KnownPendingInteractionRules.Plan plan) { }
    private record Wire(byte[] bytes, JsonNode data) { }

    private static Fixture fixture(boolean ordinary) throws Exception {
        ObjectNode resource;
        try (InputStream input = CompactKnownPendingAdmission225Test.class.getResourceAsStream("/compact-knownpending225/native-marriage-input.json")) {
            assertNotNull(input, "source-derived sanitized input fixture is mandatory"); resource = (ObjectNode) tree(input.readAllBytes());
        }
        PlanningRequest baseline = PlanningFixtures.request(PlanningFixtures.snapshot(), List.of(), Set.of());
        ObservationIdentity before = new ObservationIdentity(baseline.before().machineId(), PlanningFixtures.GAME,
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(29829), BigInteger.valueOf(576), BigInteger.valueOf(53146272)),
                        "fixture:576", BigInteger.valueOf(500), "episode-1"), 1);
        G2Source source = new G2Source(before.machineId(), PlanningFixtures.NOW.toString(), Build.CROZIER4.sha256(), PlanningFixtures.SOURCE);
        ObjectNode snapshot = (ObjectNode) toNode(PlanningFixtures.snapshot());
        snapshot.put("snapshot_id", "fixture:576").put("revision", 500).put("native_revision", 576).put("date_raw", 53146272)
                .put("speed", 5).put("local_player_id", 1).put("episode_character_id", 29829).put("one_life_terminal", false).put("episode_identity_pending", false);
        for (String key : List.of("active_event", "one_life_terminal_reason", "driver_state_error", "episode_transition_error", "cold_candidate_rejection", "top_exclusive_modal_choice_hint")) snapshot.putNull(key);
        snapshot.putObject("pending_character_interaction").put("instance_id", PENDING).put("sender_character_id", 501).put("auto_accept_notification", false);
        ((ObjectNode) snapshot.get("played_character")).putNull("betrothed_id").putArray("spouse_ids");
        ObjectNode diagnostics = (ObjectNode) snapshot.get("diagnostics"); diagnostics.put("connection_generation", 134);
        diagnostics.putObject("hello").put("expected_ck3_version", Build.CROZIER4.version()).put("expected_ck3_sha256", Build.CROZIER4.sha256())
                .set("capabilities", array(CAP, "alpha.unrelated.registry", "zeta.unrelated.registry"));
        snapshot.set("campaign_root_context_query", resource.get("retained_root_cache"));
        snapshot.set("unknown_current", toNode(new Obj(Map.of("precise", new DecimalValue("-1.230000000000000000000e-17"), "signed_zero", new DecimalValue("-0.000"), "new_fact", new Text("preserve-all-current-facts")))));
        ExternalFact settled = new ExternalFact("settled-fixture", "b".repeat(64), before, ExternalState.SEND_CONFIRMED,
                UnknownScope.GLOBAL, Domain.marriage, EMPTY, PlanningFixtures.SOURCE);
        var observed = new PlanningObservation(app(snapshot), HISTORY, Set.of(new OperationKey(STEP), new OperationKey("accept-pending-character-interaction")),
                Set.of(CAP, "alpha.unrelated.registry", "zeta.unrelated.registry"), Optional.empty(), List.of(settled), Optional.empty(), Optional.empty(), false);
        PlanningRequest request = new PlanningRequest(before, source, baseline.sessionId(), baseline.deadline(), observed);
        Context context = new Context(before, source, request.sessionId(), BigInteger.valueOf(134), Build.CROZIER4, request.deadline(),
                new ControlFrame(true, true, true, 5, 1L, 29829, "episode-1", false,
                        new PendingSummary(new PendingId(PENDING), NativeCharacterId.of(501), false), null, List.of()));
        ObjectNode wrapper = (ObjectNode) resource.get("original_context_wrapper");
        if (ordinary) {
            ObjectNode nativeContext = (ObjectNode) wrapper.get("pending_character_interaction_context");
            ((ObjectNode) nativeContext.get("definition")).put("canonical_key", "spar_with_knight_interaction");
            ((ObjectNode) nativeContext.get("roles")).put("secondary_actor_character_id", -1).put("secondary_recipient_character_id", -1);
            ((ObjectNode) nativeContext.get("send_options")).put("exclusive", true).put("definition_count", 0).put("context_count", 0).putArray("rows");
            ((ObjectNode) nativeContext.get("terms")).put("special_data_present", false);
            ((ObjectNode) nativeContext.path("terms").get("special_war_binding")).put("reason", "special_war_binding_not_applicable");
            ((ArrayNode) nativeContext.path("readiness").get("not_ready_reasons")).set(0, JsonNodeFactory.instance.textNode("special_war_binding_not_applicable"));
        }
        var decoded = PendingContextCodec.decode(new RawJson(FullJsonTree.encode(wrapper, LIMIT)), context, new PendingId(PENDING));
        var plan = KnownPendingInteractionRules.evaluate(new KnownPendingInteractionRules.Input(decoded, context, List.of(), Optional.of(List.of()),
                Optional.empty(), Optional.empty(), Set.of(STEP, "accept-pending-character-interaction")));
        assertEquals(Optional.of(Action.REJECT), plan.selected());
        Obj artifact = KnownPendingInteractionPlans.encode(request, context, plan, Optional.of(app(wrapper)));
        ObjectNode args = JsonNodeFactory.instance.objectNode().put("mutation_kind", "PENDING_REPLY").put("pending_id", PENDING).put("accept", false).put("acknowledge", false);
        args.set("group_context", resource.get("group_context_blueprint")); args.set("known_pending_plan", toNode(artifact));
        ActionCommand command = new ActionCommand("pending-fixture-225", before, source, request.sessionId(), new OperationKey(STEP), app(args),
                KnownPendingInteractionPostcondition.expected(before, source, plan),
                new Claims(Set.of(), Set.of(), Set.of(BigInteger.valueOf(29829), BigInteger.valueOf(501)),
                        Set.of("pending-interaction:" + PENDING)), request.deadline());
        return new Fixture(request, select(command, artifact), plan);
    }

    private static PlanningResult.ActionSelected select(ActionCommand command, Obj detail) {
        var draft = new OrdinaryPolicy.Draft("one-life-turn-v1", "pending_arrange_marriage_reject_only",
                "execute the exact same-frame known pending reply; require independent lifecycle and material observations",
                OrdinaryPolicy.Kind.FOREGROUND, Optional.of(command), OrdinaryPolicy.Purpose.WORLD_ACTION, Optional.empty(), detail);
        var visit = new PlanTrace.StageVisit(PlanningStage.FAMILY_AND_EDUCATION, PlanTrace.Outcome.REPLACED, "actual marriage reject selection", Optional.empty(), Optional.of(detail));
        return new PlanningResult.ActionSelected(command, new PlanTrace(command.before(), List.of(visit), Optional.of(draft)));
    }
    private static PlanningRequest request(PlanningRequest old, Obj snapshot, Set<OperationKey> steps, Set<String> caps, List<ExternalFact> facts) {
        return new PlanningRequest(old.before(), old.source(), old.sessionId(), old.deadline(),
                new PlanningObservation(snapshot, old.observations().history(), steps, caps, Optional.empty(), facts, Optional.empty(), Optional.empty(), false));
    }
    private static ActionCommand changed(ActionCommand command, Consumer<ObjectNode> mutation) {
        ObjectNode args = (ObjectNode) toNode(command.arguments()); mutation.accept(args);
        return new ActionCommand(command.actionId(), command.before(), command.source(), command.sessionId(), command.operation(), app(args), command.expected(), command.claims(), command.deadline());
    }
    private static ObjectNode nativeContext(ObjectNode args) { return (ObjectNode) args.path("known_pending_plan").path("original_context_wrapper").get("pending_character_interaction_context"); }
    private static Wire wire(PlanningRequest request, PlanningResult.ActionSelected selected) throws Exception {
        var selector = new RootOnlineDecisionSelector(new DecisionProvider(URI.create("http://127.0.0.1:1/v1"), "fixture-model", Duration.ofSeconds(10), 1, Duration.ZERO),
                Clock.fixed(PlanningFixtures.NOW, ZoneOffset.UTC), raw -> { throw new AssertionError("no archive expected"); });
        Method method = RootOnlineDecisionSelector.class.getDeclaredMethod("requestPayload", PlanningRequest.class, PlanningResult.ActionSelected.class, String.class); method.setAccessible(true);
        byte[] bytes;
        try { bytes = (byte[]) method.invoke(selector, request, selected, ActionCodec.bodySha256(selected.command())); }
        catch (InvocationTargetException failure) { if (failure.getCause() instanceof Exception exception) throw exception; if (failure.getCause() instanceof Error error) throw error; throw failure; }
        JsonNode outer = tree(bytes); return new Wire(bytes, tree(outer.path("messages").get(1).path("content").textValue().getBytes(StandardCharsets.UTF_8)));
    }
    private static void compact(Wire wire) {
        assertEquals("xar.model-known-pending-admission/v1", wire.data().path("decision_context_schema").textValue());
        assertEquals("known_marriage_reject_admission/v1", wire.data().path("decision_scope").textValue());
        assertTrue(wire.bytes().length <= 65536); assertFalse(wire.data().has("history")); assertFalse(wire.data().has("history_projection_schema"));
    }
    private static void legacy(Wire wire, PlanningRequest request) {
        assertFalse(wire.data().has("decision_context_schema")); assertEquals("xar.model-root-history-dictionary/v1", wire.data().path("history_projection_schema").textValue());
        assertEquals(toNode(request.observations().snapshot()), wire.data().get("snapshot"));
        assertEquals(toNode(new Arr(new ArrayList<Value>(request.observations().history()))), wire.data().get("history"));
    }
    private static ObjectNode core(OrdinaryPolicy.Draft draft) {
        ObjectNode node = JsonNodeFactory.instance.objectNode().put("policy", draft.policy()).put("phase", draft.phase()).put("reason", draft.reason()).put("kind", draft.kind().name()).put("purpose", draft.purpose().name());
        if (draft.domain().isPresent()) node.put("domain", draft.domain().orElseThrow().name()); else node.putNull("domain"); return node;
    }
    private static ArrayNode facts(PlanningRequest request) {
        ArrayNode result = JsonNodeFactory.instance.arrayNode();
        for (ExternalFact fact : request.observations().actionFacts()) result.addObject().put("action_id", fact.actionId()).put("body_sha256", fact.bodySha256()).put("state", fact.state().name())
                .put("unresolved", fact.unresolved()).put("scope", fact.scope().name()).put("domain", fact.domain().name()).set("affected_claims", ActionCodec.claims(fact.affectedClaims()));
        return result;
    }
    private static Obj app(JsonNode node) { return object(OpportunityJson.parseComplete(FullJsonTree.encode(node, LIMIT), LIMIT), "fixture object"); }
    private static JsonNode tree(byte[] raw) { return FullJsonTree.parse(raw, LIMIT); }
    private static ArrayNode array(String... strings) { ArrayNode result = JsonNodeFactory.instance.arrayNode(); for (String value : strings) result.add(value); return result; }
    private static IntegerValue integer(long value) { return new IntegerValue(BigInteger.valueOf(value)); }
}
