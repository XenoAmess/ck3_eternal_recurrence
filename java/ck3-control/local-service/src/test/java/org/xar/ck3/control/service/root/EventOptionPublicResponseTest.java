package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.charset.StandardCharsets;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Wire-only fixtures make no canonical archive, native call, writer or gameplay qualification claim. */
final class EventOptionPublicResponseTest {
    @Test void everyNonappliedOutcomeRetainsAckSeparatelyWithoutConsumption() {
        for (ActionReceipt.Outcome outcome : ActionReceipt.Outcome.values()) {
            if (outcome == ActionReceipt.Outcome.APPLIED_CONFIRMED) continue;
            for (boolean ack : List.of(false, true)) {
                ObjectNode n = packet(outcome, ack); RawJson input = raw(n);
                assertEquals(input, EventOptionPublicResponse.parse(input).original());
                assertFalse(n.get("event_material_result_available").booleanValue());
                assertTrue(n.get("action_receipt").get("after").isNull());
                assertEquals(ack, n.get("action_receipt").get("ack_received").booleanValue());
            }
        }
    }
    @Test void ackOnlyCannotClaimAppliedMaterialOrOldWindowConsumption() {
        ObjectNode unknown = packet(ActionReceipt.Outcome.UNRESOLVED, true);
        ((ObjectNode) unknown.get("action_receipt")).put("old_instance_advanced", true);
        assertThrows(IllegalArgumentException.class, () -> EventOptionPublicResponse.parse(raw(unknown)));
        ObjectNode marked = packet(ActionReceipt.Outcome.UNRESOLVED, true);
        marked.put("event_material_result_available", true);
        assertThrows(IllegalArgumentException.class, () -> EventOptionPublicResponse.parse(raw(marked)));
        ObjectNode applied = packet(ActionReceipt.Outcome.APPLIED_CONFIRMED, true);
        assertThrows(IllegalArgumentException.class, () -> EventOptionPublicResponse.parse(raw(applied)));
    }
    @Test void exactOptionAndCanonicalWideFrameIdentityRoundTrip() {
        ObjectNode n = packet(ActionReceipt.Outcome.UNRESOLVED, false);
        ObjectNode before = (ObjectNode) n.get("action_receipt").get("before");
        before.put("revision", "18446744073709551615");
        before.put("native_revision", "18446744073709551615");
        before.put("date_raw", "18446744073709551615");
        assertEquals(raw(n), EventOptionPublicResponse.parse(raw(n)).original());
        ObjectNode wrong = n.deepCopy(); wrong.put("option_index", 0);
        assertThrows(IllegalArgumentException.class, () -> EventOptionPublicResponse.parse(raw(wrong)));
        ObjectNode wrongStep = n.deepCopy(); wrongStep.put("step", "select-event-option-1");
        assertThrows(IllegalArgumentException.class, () -> EventOptionPublicResponse.parse(raw(wrongStep)));
    }
    @Test void appliedWireUsesSoleMaterialInverseAndBindsTheExactOriginalInstanceAndFrames() {
        ObjectNode n = packet(ActionReceipt.Outcome.APPLIED_CONFIRMED, true);
        n.put("event_material_result_available", true).put("event_material_wire_encoding", EventOptionPublicResponse.MATERIAL_ENCODING)
                .put("progress_status", "postcondition");
        ObjectNode receipt = (ObjectNode) n.get("action_receipt");
        receipt.put("old_instance_advanced", true);
        ObjectNode after = ((ObjectNode) receipt.get("before")).deepCopy(); after.put("snapshot_id", "wire-only-after").put("revision", "18");
        receipt.set("after", after);
        n.set("event_selection", StrictJson.object().put("selected_option_number", 3).put("selected_native_option_index", 2)
                .put("old_event_instance_id", 812).put("postcondition_verified", true).put("status", "event_instance_advanced")
                .put("starting_revision", "17").put("ending_revision", "18").put("starting_snapshot_id", "wire-only-frame")
                .put("ending_snapshot_id", "wire-only-after").put("episode_run_id", "wire-only-episode")
                .put("connection_generation", "18446744073709551615"));
        assertEquals(raw(n), EventOptionPublicResponse.parse(raw(n)).original());
        ObjectNode otherInstance = n.deepCopy(); ((ObjectNode) otherInstance.get("event_selection")).put("old_event_instance_id", 813);
        assertThrows(IllegalArgumentException.class, () -> EventOptionPublicResponse.parse(raw(otherInstance)));
        ObjectNode otherFrame = n.deepCopy(); ((ObjectNode) otherFrame.get("event_selection")).put("ending_revision", "19");
        assertThrows(IllegalArgumentException.class, () -> EventOptionPublicResponse.parse(raw(otherFrame)));
        ObjectNode numericWide = n.deepCopy(); ((ObjectNode) numericWide.get("event_selection")).put("connection_generation", 1);
        assertThrows(IllegalArgumentException.class, () -> EventOptionPublicResponse.parse(raw(numericWide)));
    }
    @Test void malformedPresenceTypesAndUnsafeExtensionIntegersRefuseWireAdmission() {
        for (String field : List.of("sequence", "settled", "ack_received", "native_ok", "old_instance_advanced", "before", "after", "original_receipt")) {
            ObjectNode n = packet(ActionReceipt.Outcome.UNRESOLVED, true);
            ((ObjectNode) n.get("action_receipt")).remove(field);
            assertThrows(IllegalArgumentException.class, () -> EventOptionPublicResponse.parse(raw(n)), field);
        }
        ObjectNode unsafe = packet(ActionReceipt.Outcome.UNRESOLVED, false);
        unsafe.put("unknown_identity", new java.math.BigInteger("9007199254740993"));
        assertThrows(IllegalArgumentException.class, () -> EventOptionPublicResponse.parse(raw(unsafe)));
        for (String token : List.of("01", "+1", "-0", "18446744073709551616")) {
            ObjectNode n = packet(ActionReceipt.Outcome.UNRESOLVED, false);
            ((ObjectNode) n.get("action_receipt").get("before")).put("revision", token);
            assertThrows(IllegalArgumentException.class, () -> EventOptionPublicResponse.parse(raw(n)), token);
        }
        ObjectNode numericWide = packet(ActionReceipt.Outcome.UNRESOLVED, false);
        ((ObjectNode) numericWide.get("action_receipt").get("before")).put("revision", 1);
        assertThrows(IllegalArgumentException.class, () -> EventOptionPublicResponse.parse(raw(numericWide)));
        ObjectNode wrongBoolean = packet(ActionReceipt.Outcome.UNRESOLVED, false);
        ((ObjectNode) wrongBoolean.get("action_receipt")).put("ack_received", 1);
        assertThrows(IllegalArgumentException.class, () -> EventOptionPublicResponse.parse(raw(wrongBoolean)));
    }
    private static ObjectNode packet(ActionReceipt.Outcome outcome, boolean ack) {
        ObjectNode n = StrictJson.object().put("step", "select-event-option-3").put("option_number", 3)
                .put("option_index", 2).put("event_instance_id", 812).put("event_material_result_available", false)
                .put("status", outcome == ActionReceipt.Outcome.UNRESOLVED ? "action_state_unknown" : "event_action_not_applied");
        ObjectNode r = n.putObject("action_receipt").put("schema", EventOptionPublicResponse.RECEIPT_SCHEMA)
                .put("action_id", "wire-only-event-action").put("command_body_sha256", "a".repeat(64)).put("sequence", "1")
                .put("canonical_outcome", outcome.name()).put("settled", outcome != ActionReceipt.Outcome.UNRESOLVED)
                .put("ack_received", ack).put("machine_id", "synthetic-machine").put("session_id", "synthetic-session");
        if (ack) r.put("native_ok", true); else r.putNull("native_ok");
        r.putNull("old_instance_advanced").putNull("after");
        r.set("before", StrictJson.object().put("snapshot_id", "wire-only-frame").put("episode_run_id", "wire-only-episode")
                .put("revision", "17").put("native_revision", "41").put("date_raw", "24000").put("actor_character_id", 707));
        r.set("original_receipt", new ExactRef("wire-only-not-an-archive-proof", 1, "b".repeat(64)).toJson());
        return n;
    }
    private static RawJson raw(ObjectNode value) { return new RawJson(value.toString().getBytes(StandardCharsets.UTF_8)); }
}
