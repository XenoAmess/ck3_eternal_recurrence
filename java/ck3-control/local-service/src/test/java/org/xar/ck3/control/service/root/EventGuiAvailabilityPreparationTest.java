package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.planning.events.PublicEventResolution;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.events.GuiAvailabilityObservation;
import org.xar.ck3.control.nativebridge.capabilities.events.EventWindowModels;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import com.fasterxml.jackson.databind.node.ObjectNode;

/** Constructor checks on software presentation DATA, with no read/submit token or actual Game. */
final class EventGuiAvailabilityPreparationTest {
    @Test void preparationAcceptsObservedTrueWithRawFalseAndRetainsBothFields() {
        var option = option(false, new GuiAvailabilityObservation.Observed(true));
        var context = context(option);
        var result = new EventActionPreparation.EventPresentation(context, option);
        assertSame(option, result.selected()); assertFalse(result.selected().enabled());
        assertEquals(new GuiAvailabilityObservation.Observed(true), result.selected().guiAvailability());
        assertEquals(17, result.instanceId());
    }
    @Test void preparationRejectsObservedFalseEvenWithRawTrue() {
        var option = option(true, new GuiAvailabilityObservation.Observed(false));
        assertThrows(IllegalArgumentException.class, () -> new EventActionPreparation.EventPresentation(context(option), option));
    }
    @Test void preparationPreservesRawFallbackAndOriginalContextMembership() {
        for (GuiAvailabilityObservation observation : List.of(new GuiAvailabilityObservation.LegacyNotReported(),
                new GuiAvailabilityObservation.Unobserved(GuiAvailabilityObservation.Reason.NATIVE_READ_UNAVAILABLE))) {
            var yes = option(true, observation);
            assertEquals(observation, new EventActionPreparation.EventPresentation(context(yes), yes).selected().guiAvailability());
            var no = option(false, observation);
            assertThrows(IllegalArgumentException.class, () -> new EventActionPreparation.EventPresentation(context(no), no));
        }
        var original = option(false, new GuiAvailabilityObservation.Observed(true));
        var changed = option(true, new GuiAvailabilityObservation.Observed(true));
        assertThrows(IllegalArgumentException.class, () -> new EventActionPreparation.EventPresentation(context(original), changed));
    }
    @Test void actualPublicResponseCodecRetainsGuiObservationAndRejectsAnInvalidReplacement() {
        var original = ordinaryRow(false);
        var base = EventOptionPublicResponse.parse(raw(packet()));
        var output = EventResolutionPublicResponse.append(base, original);
        assertEquals(output.original(), EventResolutionPublicResponse.parse(output.original()).original());
        ObjectNode encoded = (ObjectNode) DriverJson.toNode(DriverJson.object(output.original().bytes(), 1048576));
        JsonNodeCheck.originalRawFalseAndObservedTrue(encoded);
        ObjectNode selected = (ObjectNode) encoded.get("ordinary_events").get(0);
        ((ObjectNode)selected.get("selected_gui_availability")).put("is_valid", false);
        assertThrows(IllegalArgumentException.class, () -> EventResolutionPublicResponse.parse(raw(encoded)));
    }
    private static final class JsonNodeCheck {
        private JsonNodeCheck() { }
        static void originalRawFalseAndObservedTrue(ObjectNode packet) {
            var selected = packet.path("ordinary_events").get(0);
            assertFalse(selected.path("visible_options").get(0).path("enabled").booleanValue());
            assertTrue(selected.path("selected_gui_availability").path("is_valid").booleanValue());
            assertEquals(2, selected.path("gui_observation_version").intValue());
            assertFalse(packet.path("event_material_result_available").booleanValue());
            assertTrue(packet.path("action_receipt").path("old_instance_advanced").isNull());
        }
    }
    private static OpportunityJson.Obj ordinaryRow(boolean rawEnabled) {
        var row = StrictJson.object().put("event_index", 1).put("event_instance_id", 17).putNull("title").put("selected_option_number", 1)
            .put("selected_option_index", 0).put("selected_visible_text", "first").put("strategy", "user-first-displayed-event-v1").put("source", "native")
            .put("gui_observation_version", 2);
        row.putArray("visible_options").add(StrictJson.object().put("index", 0).put("option_number", 1).put("label", "first").put("enabled", rawEnabled));
        row.putObject("selected_gui_availability").put("status", "observed").put("is_valid", true);
        return PublicEventResolution.validateOrdinaryEvent(DriverJson.object(DriverJson.encodeNode(row), 16384), 17, 1);
    }
    private static ObjectNode packet() {
        var packet = StrictJson.object().put("step", "select-event-option-1").put("option_number", 1).put("option_index", 0).put("event_instance_id", 17)
            .put("event_material_result_available", false).put("status", "action_state_unknown");
        var receipt = packet.putObject("action_receipt").put("schema", EventOptionPublicResponse.RECEIPT_SCHEMA).put("action_id", "wire-only-action")
            .put("command_body_sha256", "a".repeat(64)).put("sequence", "1").put("canonical_outcome", ActionReceipt.Outcome.UNRESOLVED.name()).put("settled", false)
            .put("ack_received", true).put("native_ok", true).put("machine_id", "synthetic-machine").put("session_id", "synthetic-session").putNull("old_instance_advanced").putNull("after");
        receipt.set("before", StrictJson.object().put("snapshot_id", "wire-only-before").put("episode_run_id", "wire-only-episode").put("revision", "17")
            .put("native_revision", "41").put("date_raw", "24000").put("actor_character_id", 73));
        receipt.set("original_receipt", new ExactRef("wire-only-not-canonical-proof", 1, "b".repeat(64)).toJson());
        return packet;
    }
    private static RawJson raw(ObjectNode value) { return new RawJson(DriverJson.encodeNode(value)); }
    private static EventWindowModels.Option option(boolean raw, GuiAvailabilityObservation observation) {
        return new EventWindowModels.Option(0, 0, raw, false, false, "first", "", List.of(), observation);
    }
    private static EventWindowModels.Available context(EventWindowModels.Option option) {
        var binding = new EventWindowModels.Binding(EventWindowModels.Build.CROZIER4, BigInteger.valueOf(9), 741221, 17);
        var scope = new EventWindowModels.Scope(4, "character", 0, new EventWindowModels.CharacterIdentity(73), Optional.empty());
        return new EventWindowModels.Available(binding, new EventWindowModels.Definition("gui_fixture.0001", 20001, 1), scope, List.of(), List.of(option),
            new EventWindowModels.Readiness(true, true, true, true, true, false, false), new RawJson("{\"software_fixture\":true}".getBytes(StandardCharsets.UTF_8)));
    }
}
