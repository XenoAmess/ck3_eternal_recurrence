package org.xar.ck3.control.application.planning.events;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.planning.OrdinaryPolicy;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.semantic.NativeActiveEvent;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave2.events.registered.RegisteredEventKnowledge;
import org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson;

/** Software DATA fixtures execute shared selection and persistence consumers, without native authority. */
final class EventGuiAvailabilityApplicationTest {
    @Test void observedTrueKeepsRawFalseThroughActualSelectionAndPersistedResult() throws java.io.IOException {
        var input = input(false, observed(true), true);
        var plan = PublicEventSelection.plan(input, 1, Optional.of(17), RegisteredEventKnowledge.load(), Optional.empty());
        assertEquals(new OpportunityJson.Text("select-event-option-1"), plan.get("selected_step"));
        JsonNode capture = node(plan).path("unhandled_event_fallback");
        assertFalse(capture.path("selection").path("enabled").booleanValue());
        assertEquals(observed(true), capture.path("selection").path("gui_availability"));
        var row = PublicEventResolution.ordinaryEvent(metadata(plan, input.snapshot()));
        assertFalse(node(row).path("visible_options").get(0).path("enabled").booleanValue());
        assertEquals(observed(true), node(row).path("selected_gui_availability"));
        assertEquals(row, PublicEventResolution.validateOrdinaryEvent(DriverJson.object(DriverJson.encode(row), 65536), 17, 1));
    }

    @Test void observedFalseBlocksExplicitChoiceAndFirstDisplayEvenWhenRawTrue() {
        var input = input(true, observed(false), true);
        assertThrows(IllegalArgumentException.class, () -> PublicEventSelection.plan(input, 1, Optional.empty(), RegisteredEventKnowledge.load(), Optional.empty()));
        var first = EventPolicies.firstDisplayedPlan(input, OrdinaryPolicy.Draft.empty(), node(input.currentWindow()), Optional.empty()).orElseThrow().plan();
        assertEquals(OpportunityJson.Nil.INSTANCE, first.get("selected_step"));
        assertTrue(node(first).path("unhandled_event_fallback").path("selection").path("enabled").booleanValue());
        assertEquals(observed(false), node(first).path("unhandled_event_fallback").path("selection").path("gui_availability"));
    }

    @Test void firstDisplayUsesActualV2ContextAndRetainsCaptureShape() {
        var input = input(false, observed(true), true);
        var first = EventPolicies.firstDisplayedPlan(input, OrdinaryPolicy.Draft.empty(), node(input.currentWindow()), Optional.empty()).orElseThrow().plan();
        assertEquals(new OpportunityJson.Text("select-event-option-1"), first.get("selected_step"));
        var row = PublicEventResolution.ordinaryEvent(metadata(first, input.snapshot()));
        assertEquals(observed(true), node(row).path("selected_gui_availability"));
        assertFalse(node(first).path("unhandled_event_fallback").path("window_context").path("options").get(0).path("enabled").booleanValue());
    }

    @Test void legacyAndUnobservedRetainRawFallbackWithoutInventingGuiTrue() throws java.io.IOException {
        for (boolean v2 : List.of(false, true)) {
            var input = input(true, unobserved(), v2);
            var plan = PublicEventSelection.plan(input, 1, Optional.empty(), RegisteredEventKnowledge.load(), Optional.empty());
            var row = PublicEventResolution.ordinaryEvent(metadata(plan, input.snapshot()));
            assertEquals(v2, row.members().containsKey("selected_gui_availability"));
            if (v2) assertEquals(unobserved(), node(row).path("selected_gui_availability"));
            assertThrows(IllegalArgumentException.class, () -> PublicEventSelection.plan(input(false, unobserved(), v2), 1, Optional.empty(), RegisteredEventKnowledge.load(), Optional.empty()));
        }
    }

    @Test void missingNullWrongVersionAndChangedObservationReject() throws java.io.IOException {
        var input = input(false, observed(true), true);
        var plan = PublicEventSelection.plan(input, 1, Optional.empty(), RegisteredEventKnowledge.load(), Optional.empty());
        var prepared = metadata(plan, input.snapshot());
        var row = PublicEventResolution.ordinaryEvent(prepared);
        for (String field : List.of("gui_observation_version", "selected_gui_availability")) {
            ObjectNode changed = node(row); changed.remove(field);
            assertThrows(IllegalArgumentException.class, () -> PublicEventResolution.validateOrdinaryEvent(opportunity(changed), 17, 1));
            ObjectNode nulled = node(row); nulled.putNull(field);
            assertThrows(IllegalArgumentException.class, () -> PublicEventResolution.validateOrdinaryEvent(opportunity(nulled), 17, 1));
        }
        ObjectNode decimal = node(row); decimal.put("gui_observation_version", 2.0);
        assertThrows(IllegalArgumentException.class, () -> PublicEventResolution.validateOrdinaryEvent(opportunity(decimal), 17, 1));
        ObjectNode unknown = node(row); ((ObjectNode) unknown.get("selected_gui_availability")).put("is_valid", "true");
        assertThrows(IllegalArgumentException.class, () -> PublicEventResolution.validateOrdinaryEvent(opportunity(unknown), 17, 1));
        ObjectNode changed = node(plan); ((ObjectNode) changed.get("selected_native_event_option")).set("gui_availability", observed(false));
        assertThrows(IllegalArgumentException.class, () -> PublicEventResolution.ordinaryEvent(metadata(opportunity(changed), input.snapshot())));
        ObjectNode missing = node(input.currentWindow()); ((ObjectNode) missing.get("options").get(0)).remove("gui_availability");
        assertThrows(IllegalArgumentException.class, () -> PublicEventSelection.plan(withWindow(input, missing), 1, Optional.empty(), RegisteredEventKnowledge.load(), Optional.empty()));
    }

    @Test void eligibleScoringPreservesRawFlagsAndOriginalTieRules() {
        ObjectNode event = StrictJson.object();
        event.putArray("options").add(StrictJson.object().put("option_number", 2).put("enabled", false).put("strategy_score", 4))
            .add(StrictJson.object().put("option_number", 1).put("enabled", true).put("strategy_score", 1));
        JsonNode original = event.deepCopy();
        assertEquals(Optional.of(BigInteger.ONE), NativeActiveEvent.chooseOptionNumber(event));
        assertEquals(Optional.of(BigInteger.TWO), NativeActiveEvent.chooseEligibleOptionNumber(event));
        assertEquals(original, event);
        ((ObjectNode)event.get("options").get(0)).put("strategy_score", -0.0);
        ((ObjectNode)event.get("options").get(1)).put("strategy_score", 0.0);
        assertEquals(Optional.of(BigInteger.ONE), NativeActiveEvent.chooseEligibleOptionNumber(event));
        ((ObjectNode)event.get("options").get(0)).put("strategy_score", BigInteger.TEN.pow(400));
        assertThrows(ArithmeticException.class, () -> NativeActiveEvent.chooseEligibleOptionNumber(event));
        assertEquals(Optional.of(BigInteger.ONE), NativeActiveEvent.chooseOptionNumber(event));
    }

    @Test void retainedNativeFalseRawTrueCannotReachPublicSelection() throws Exception {
        byte[] original = resource("callback-false-raw-enabled.v2.json", "aecedbaae3c7765e2a392cbe2c7945ce9d6b384ca97c4c76b65b1d62c32c726b");
        var input = nativeInput(original);
        assertThrows(IllegalArgumentException.class, () -> PublicEventSelection.plan(input, 1, Optional.empty(), RegisteredEventKnowledge.load(), Optional.empty()));
        var first = EventPolicies.firstDisplayedPlan(input, OrdinaryPolicy.Draft.empty(), node(input.currentWindow()), Optional.empty()).orElseThrow().plan();
        assertEquals(OpportunityJson.Nil.INSTANCE, first.get("selected_step"));
        assertTrue(node(first).path("unhandled_event_fallback").path("selection").path("enabled").booleanValue());
        assertEquals(node(input.currentWindow()), node(first).path("unhandled_event_fallback").path("window_context"));
    }

    @Test void retainedNativeTrueRawFalseReachesPublicSelectionAndDurableOrdinaryRow() throws Exception {
        byte[] original = resource("raw-disabled-fallback-valid.v2.json", "cedf65a62fc28ece6ee7a8bf013c05a2a964a11442a9683951cf8d0c4c4e4dde");
        var input = nativeInput(original);
        var selected = PublicEventSelection.plan(input, 1, Optional.empty(), RegisteredEventKnowledge.load(), Optional.empty());
        assertFalse(node(selected).path("selected_native_event_option").path("enabled").booleanValue());
        assertTrue(node(selected).path("selected_native_event_option").path("fallback").booleanValue());
        assertEquals("Not today", node(selected).path("selected_native_event_option").path("unavailable_reason").textValue());
        var row = PublicEventResolution.ordinaryEvent(metadata(selected, input.snapshot()));
        int instance = node(input.currentWindow()).path("current_event_instance_id").intValue();
        assertEquals(row, PublicEventResolution.validateOrdinaryEvent(DriverJson.object(DriverJson.encode(row), 65536), instance, 1));
        assertFalse(node(row).path("visible_options").get(0).path("enabled").booleanValue());
        assertEquals(node(input.currentWindow()).path("options").get(0).path("gui_availability"), node(row).path("selected_gui_availability"));
        assertArrayEquals(original, resource("raw-disabled-fallback-valid.v2.json", "cedf65a62fc28ece6ee7a8bf013c05a2a964a11442a9683951cf8d0c4c4e4dde"));
    }

    private static EventDecisionInput input(boolean raw, ObjectNode gui, boolean v2) {
        var before = new ObservationIdentity("gui-fixture", new GameGeneration(42, new PythonOnlyUInt64(BigInteger.valueOf(123))),
            new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(73), BigInteger.valueOf(9), BigInteger.valueOf(741221)), "gui-frame", BigInteger.valueOf(1009), "gui-episode"), 1);
        var source = new G2Source("gui-fixture", "2026-10-30T00:00:00Z", "1.20.0.4", new ExactRef("software-data-only", 1, "a".repeat(64)));
        ObjectNode snapshot = StrictJson.object().put("snapshot_id", "gui-frame").put("revision", 1009).put("native_revision", 9).put("date_raw", 741221)
            .put("episode_run_id", "gui-episode").put("paused", true).put("map_ready", true);
        snapshot.putObject("diagnostics").put("connection_generation", 5).put("bridge_pid", 42);
        snapshot.putObject("played_character").put("character_id", 73).put("alive", true);
        ObjectNode event = snapshot.putObject("active_event").put("instance_id", 17).put("option_count", 1).put("source", "native").put("title", "fixture");
        event.putArray("options").add(StrictJson.object().put("index", 0).put("option_number", 1).put("label", "first").put("enabled", raw));
        ObjectNode context = StrictJson.object().put("schema", v2 ? "current-event-window-context-v2" : "current-event-window-context-v1")
            .put("schema_version", v2 ? 2 : 1).put("status", "available").put("snapshot_revision", 9).put("date_raw", 741221)
            .put("current_event_instance_id", 17).put("event_definition_key", "gui_fixture.0001");
        ObjectNode row = context.putArray("options").addObject().put("rendered_index", 0).put("native_option_index", 0).put("shown", true)
            .put("enabled", raw).put("resolved_name", "first");
        if (v2) row.set("gui_availability", gui);
        return new EventDecisionInput(before, source, "gui-session", opportunity(snapshot), List.of(), Set.of(new OperationKey("select-event-option-1")), Set.of(),
            Instant.parse("2030-01-01T00:00:00Z"), retained(context), Optional.empty());
    }
    private static EventDecisionInput withWindow(EventDecisionInput input, ObjectNode window) {
        return new EventDecisionInput(input.before(), input.source(), input.sessionId(), input.snapshot(), input.history(), input.actionSteps(), input.bridgeCapabilities(), input.deadline(), retained(window), input.focus());
    }
    private static OpportunityJson.Obj metadata(OpportunityJson.Obj plan, OpportunityJson.Obj snapshot) {
        var active = (OpportunityJson.Obj) snapshot.get("active_event");
        var normalized = opportunity((ObjectNode)NativeActiveEvent.normalize(DriverJson.toNode(active), "native"));
        return plan.with("public_event_resolution", new OpportunityJson.Obj(java.util.Map.of("schema", new OpportunityJson.Text("xar.public-event-resolution/v1"),
            "selection_strategy", new OpportunityJson.Text("user-first-displayed-event-v1"), "normalized_active_event", normalized,
            "event_instance_id", active.get("instance_id"), "option_number", new OpportunityJson.IntegerValue(BigInteger.ONE),
            "selected_step", new OpportunityJson.Text("select-event-option-1"))));
    }
    private static byte[] resource(String name, String sha) throws Exception {
        try (var stream = EventGuiAvailabilityApplicationTest.class.getResourceAsStream("/event-gui-v2/" + name)) {
            assertNotNull(stream, "actual frozen Native serializer input required");
            byte[] raw = stream.readAllBytes();
            assertEquals(sha, java.util.HexFormat.of().formatHex(java.security.MessageDigest.getInstance("SHA-256").digest(raw)));
            return raw;
        }
    }
    private static EventDecisionInput nativeInput(byte[] nativeContext) {
        ObjectNode context = (ObjectNode) StrictJson.parse(nativeContext, 65536);
        ObjectNode row = (ObjectNode) context.get("options").get(0);
        var initial = input(row.get("enabled").booleanValue(), (ObjectNode) row.get("gui_availability"), true);
        ObjectNode snapshot = node(initial.snapshot());
        snapshot.put("native_revision", context.get("snapshot_revision").bigIntegerValue()).put("date_raw", context.get("date_raw").bigIntegerValue());
        ((ObjectNode)snapshot.get("played_character")).put("character_id", 42);
        ObjectNode active = (ObjectNode) snapshot.get("active_event");
        active.put("instance_id", context.get("current_event_instance_id").bigIntegerValue());
        ((ObjectNode)active.get("options").get(0)).put("label", row.get("resolved_name").textValue());
        var identity = initial.before();
        var before = new ObservationIdentity(identity.machineId(), identity.game(), new JointBudgetSelector.ProposalFrame(
            new JointBudgetSelector.Frame(BigInteger.valueOf(42), context.get("snapshot_revision").bigIntegerValue(), context.get("date_raw").bigIntegerValue()),
            identity.frame().snapshotId(), identity.frame().revision(), identity.frame().episodeRunId()), identity.observationVersion());
        return new EventDecisionInput(before, initial.source(), initial.sessionId(), opportunity(snapshot), initial.history(), initial.actionSteps(),
            initial.bridgeCapabilities(), initial.deadline(), retained(context), initial.focus());
    }
    private static ObjectNode observed(boolean valid) { return StrictJson.object().put("status", "observed").put("is_valid", valid); }
    private static ObjectNode unobserved() { return StrictJson.object().put("status", "unobserved").put("reason", "native_binding_unavailable"); }
    private static ObjectNode node(OpportunityJson.Obj value) { return (ObjectNode) DriverJson.toNode(value); }
    private static ObjectNode node(RetainedJson.ObjectValue value) { return (ObjectNode) StrictJson.parse(RetainedJson.encode(value), 65536); }
    private static OpportunityJson.Obj opportunity(ObjectNode value) { return DriverJson.object(DriverJson.encodeNode(value), 65536); }
    private static RetainedJson.ObjectValue retained(ObjectNode value) { return RetainedJson.object(RetainedJson.parse(DriverJson.encodeNode(value))); }
}
