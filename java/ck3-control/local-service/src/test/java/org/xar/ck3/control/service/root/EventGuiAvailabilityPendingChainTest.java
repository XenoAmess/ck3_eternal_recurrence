package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Path;
import java.time.Instant;
import java.util.Set;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.action.PlanningReadRequest;
import org.xar.ck3.control.application.action.PlanningReadResult;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.planning.events.PendingUiEvent;
import org.xar.ck3.control.application.planning.events.EventPolicies;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.events.GuiAvailabilityObservation;
import org.xar.ck3.control.nativebridge.capabilities.events.EventWindowModels;
import org.xar.ck3.control.nativebridge.capabilities.events.EventWindowRead;
import org.xar.ck3.control.wave2.events.registered.RegisteredEventKnowledge;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Existing real software writer/read fixture through explicit v2 preparation and fresh-read recheck. No Game. */
final class EventGuiAvailabilityPendingChainTest {
    private static final Instant DEADLINE = Instant.parse("2030-01-01T00:00:00Z");
    @TempDir Path temporary;
    @BeforeAll static void originalInputs() throws Exception { PendingUiEventPreparationTest.originalProducers(); }

    @Test void rawFalseObservedTruePreparesSerializesAndRechecksTheOriginalPrivateChoice() throws Exception {
        try (var disk = new CoaSourceArchiveBoundaryTest.Fixture(temporary.resolve("v2-private"), 16 * 1024 * 1024)) {
            disk.writer.locked(session -> {
                var fixture = new PendingUiEventPreparationTest.Inputs(disk, disk.archive.withSession(session), session);
                var current = fixture.event(true); var context = v2(fixture.eventContext(false), true);
                var first = prepare(fixture, current, context, 1, "v2-private-same-intent");
                var presentation = assertInstanceOf(EventActionPreparation.EventPresentation.class, first.presentation());
                assertFalse(presentation.selected().enabled());
                assertEquals(new GuiAvailabilityObservation.Observed(true), presentation.selected().guiAvailability());
                assertEquals("select-event-option-4", first.command().operation().value());
                var restored = ActionCodec.decodeCommand(ActionCodec.encodeCommand(first.command()));
                assertEquals(first.command(), restored);
                assertEquals("select-event-option-4", EventActionPreparation.prepare(restored).step());
                var fresh = prepare(fixture, current, context, 2, "v2-private-same-intent");
                EventActionPreparation.requirePendingUiEventCurrent(first, fresh);
                var changed = context.deepCopy(); ((ObjectNode)changed.get("options").get(0)).put("enabled", true);
                var different = prepare(fixture, current, changed, 3, "v2-private-same-intent");
                assertThrows(IllegalArgumentException.class, () -> EventActionPreparation.requirePendingUiEventCurrent(first, different));
                return null;
            });
        }
    }

    @Test void rawTrueObservedFalseRejectsBeforePrivatePreparedAndKeepsTheOriginalDiagnosis() throws Exception {
        try (var disk = new CoaSourceArchiveBoundaryTest.Fixture(temporary.resolve("v2-private-reject"), 16 * 1024 * 1024)) {
            disk.writer.locked(session -> {
                var fixture = new PendingUiEventPreparationTest.Inputs(disk, disk.archive.withSession(session), session);
                var current = fixture.event(true); var context = v2(fixture.eventContext(true), false);
                var rejected = assertThrows(EventActionPreparation.PendingSelectionRejected.class,
                    () -> prepare(fixture, current, context, 1, "v2-rejected"));
                var capture = DriverJson.toNode(rejected.diagnosis()).path("unhandled_event_fallback");
                assertTrue(capture.path("selection").path("enabled").booleanValue());
                assertFalse(capture.path("selection").path("gui_availability").path("is_valid").booleanValue());
                assertFalse(DriverJson.toNode(rejected.diagnosis()).path("selected_step").isTextual());
                assertTrue(rejected.originalRead().bytes() > 0);
                return null;
            });
        }
    }

    @Test void explicitV2FixturePreparationRetainsItsActualContractAndGuiChoice() throws Exception {
        try (var disk = new CoaSourceArchiveBoundaryTest.Fixture(temporary.resolve("v2-fixture"), 16 * 1024 * 1024)) {
            disk.writer.locked(session -> {
                var fixture = new PendingUiEventPreparationTest.Inputs(disk, disk.archive.withSession(session), session);
                var current = fixture.event(true);
                var read = read(fixture, current, v2(fixture.eventContext(false), true), 1);
                var data = new EventRuntimeInstaller.FixtureEventData(current.frame(), read, EventWindowModels.Build.TOURS,
                    current.history(), steps(), current.bridgeCapabilities(), List.of(read.originalReceipt(), disk.pin), Optional.empty());
                var origin = new EventRuntimeInstaller.FixtureDecisionOrigin("software-fixture-parent", disk.pin, Optional.empty(), List.of(), Optional.empty());
                var command = EventRuntimeInstaller.prepareFixtureEventData(data, origin, Optional.of(4), "v2-fixture-choice", DEADLINE, RegisteredEventKnowledge.load(), fixture.trusted);
                assertEquals("select-event-option-4", command.operation().value());
                var option = DriverJson.toNode(command.arguments()).path("selected_native_event_option");
                assertFalse(option.path("enabled").booleanValue()); assertTrue(option.path("gui_availability").path("is_valid").booleanValue());
                assertEquals(command, ActionCodec.decodeCommand(ActionCodec.encodeCommand(command)));
                assertEquals("native/event-window-v2", read.receipt().contractId());
                return null;
            });
        }
    }

    @Test void legacyFixtureWorksAndV2ContractCannotCarryALegacyProjection() throws Exception {
        try (var disk = new CoaSourceArchiveBoundaryTest.Fixture(temporary.resolve("fixture-versions"), 16 * 1024 * 1024)) {
            disk.writer.locked(session -> {
                var fixture = new PendingUiEventPreparationTest.Inputs(disk, disk.archive.withSession(session), session);
                var current = fixture.event(true);
                var legacy = read(fixture, current, fixture.eventContext(true), 1, false);
                var data = new EventRuntimeInstaller.FixtureEventData(current.frame(), legacy, EventWindowModels.Build.TOURS,
                    current.history(), steps(), current.bridgeCapabilities(), List.of(legacy.originalReceipt(), disk.pin), Optional.empty());
                var origin = new EventRuntimeInstaller.FixtureDecisionOrigin("software-fixture-parent", disk.pin, Optional.empty(), List.of(), Optional.empty());
                var command = EventRuntimeInstaller.prepareFixtureEventData(data, origin, Optional.of(4), "legacy-fixture-choice", DEADLINE, RegisteredEventKnowledge.load(), fixture.trusted);
                assertEquals("native/event-window-v1", legacy.receipt().contractId());
                assertEquals("select-event-option-4", command.operation().value());
                assertFalse(DriverJson.toNode(command.arguments()).path("selected_native_event_option").has("gui_availability"));
                var gui = read(fixture, current, v2(fixture.eventContext(true), true), 2);
                OpportunityJson.Obj changedResult = gui.value().result().with("current_event_window_context", legacy.value().result().get("current_event_window_context"));
                var forgedProjection = new PlanningReadResult.Known<>(new EventPolicies.ReadPublication(changedResult, gui.value().snapshot()), gui.receipt(), gui.originalReceipt());
                var wrong = new EventRuntimeInstaller.FixtureEventData(current.frame(), forgedProjection, EventWindowModels.Build.TOURS,
                    current.history(), steps(), current.bridgeCapabilities(), List.of(gui.originalReceipt(), disk.pin), Optional.empty());
                var rejected = assertThrows(IllegalArgumentException.class, () -> EventRuntimeInstaller.prepareFixtureEventData(wrong, origin,
                    Optional.of(4), "changed-version-projection", DEADLINE, RegisteredEventKnowledge.load(), fixture.trusted));
                assertEquals("fixture event read contract differs from its original window version", rejected.getMessage());
                return null;
            });
        }
    }

    private static ObjectNode v2(ObjectNode context, boolean firstValid) {
        context.put("schema", "current-event-window-context-v2").put("schema_version", 2);
        for (JsonNode value : context.get("options")) ((ObjectNode)value).putObject("gui_availability").put("status", "observed").put("is_valid", true);
        ((ObjectNode)context.get("options").get(0).get("gui_availability")).put("is_valid", firstValid);
        return context;
    }
    private static EventActionPreparation.PendingPrepared prepare(PendingUiEventPreparationTest.Inputs fixture, PendingUiEvent.Current current,
            ObjectNode context, long sequence, String actionId) throws IOException {
        var read = read(fixture, current, context, sequence);
        return PendingUiEventPreparation.event(current, read, EventWindowModels.Build.TOURS, steps(), actionId, DEADLINE, RegisteredEventKnowledge.load(), fixture.trusted);
    }
    private static PlanningReadResult.Known<EventPolicies.ReadPublication> read(PendingUiEventPreparationTest.Inputs fixture, PendingUiEvent.Current current,
            ObjectNode context, long sequence) throws IOException {
        return read(fixture, current, context, sequence, true);
    }
    private static PlanningReadResult.Known<EventPolicies.ReadPublication> read(PendingUiEventPreparationTest.Inputs fixture, PendingUiEvent.Current current,
            ObjectNode context, long sequence, boolean guiObservation) throws IOException {
        EventWindowRead.Admission admission = request -> assertEquals(current.frame().identity(), request.before());
        var contract = guiObservation ? EventWindowRead.contractWithGuiObservation(fixture.disk.pin, admission) : EventWindowRead.contract(fixture.disk.pin, admission);
        var request = new PlanningReadRequest(current.frame().identity(), fixture.disk.source, current.frame().sessionId(), contract.operation(), current.frame().semantic(), DEADLINE);
        var nativeRequest = contract.prepare(request, "v2-flag-check");
        var fields = StrictJson.parse(nativeRequest.additionalFields().bytes(), 65536);
        if (guiObservation) { assertTrue(fields.path("gui_observation_version").isIntegralNumber()); assertEquals(2, fields.path("gui_observation_version").intValue()); }
        else assertFalse(fields.has("gui_observation_version"));
        var result = StrictJson.object().put("step", EventWindowRead.STEP).put("accepted", true).put("status", "available")
            .put("query_sequence", sequence).put("snapshot_revision", 17).put("backend_id", "native-headless");
        result.set("current_event_window_context", context);
        return fixture.read(current, contract, request, result);
    }
    private static Set<OperationKey> steps() { return Set.of(new OperationKey("select-event-option-1"), new OperationKey("select-event-option-2"),
        new OperationKey("select-event-option-3"), new OperationKey("select-event-option-4")); }
}
