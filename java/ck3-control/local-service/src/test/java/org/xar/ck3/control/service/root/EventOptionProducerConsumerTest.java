package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.planning.events.EventSelectionPublicResult;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Software framed producer -> original verifier/archive -> public64 -> actual public response consumer. No Game authority. */
final class EventOptionProducerConsumerTest {
    @Test void originalUnknownTransportWithIndependentAppliedFrameProducesOneDurablePublicResult() throws InterruptedException {
        var produced = NativeEventPublicMaterialProducerTest.produced();
        RawJson nativeOriginal = produced.material().compatibleResult(); byte[] originalBytes = nativeOriginal.bytes();
        RawJson publicMaterial = EventSelectionPublicResult.encode(produced.receipt(), produced.material());
        var payload = EventOptionPublicResponse.capture(produced.receipt(), produced.archive(), Optional.of(publicMaterial));
        ObjectNode result = node(payload.original());
        assertEquals("9007199254740993", result.path("action_receipt").path("before").path("revision").textValue());
        assertEquals("9007199254740994", result.path("action_receipt").path("after").path("revision").textValue());
        assertEquals("APPLIED_CONFIRMED", result.path("action_receipt").path("canonical_outcome").textValue());
        assertTrue(result.path("action_receipt").path("old_instance_advanced").booleanValue());
        assertFalse(result.path("action_receipt").path("ack_received").booleanValue());
        assertTrue(result.path("action_receipt").path("native_ok").isNull());
        assertEquals(17, result.path("event_instance_id").intValue());
        assertEquals(1, result.path("option_number").intValue()); assertEquals(0, result.path("option_index").intValue());
        assertEquals(payload.original(), EventOptionPublicResponse.parse(payload.original()).original());
        assertArrayEquals(originalBytes, produced.material().compatibleResult().bytes());
        assertFalse(produced.receipt().eligibleAdvance());
        assertEquals(produced.receipt(), produced.archive().loadReceipt(produced.archive().receiptReferenceOf(produced.receipt())));
    }
    @Test void sameArchivedProducerRejectsMissingMaterialOrMismatchedMaterialIdentityWithoutAnotherNativeCall() throws InterruptedException {
        var produced = NativeEventPublicMaterialProducerTest.produced();
        assertThrows(IllegalArgumentException.class, () -> EventOptionPublicResponse.capture(produced.receipt(), produced.archive(), Optional.empty()));
        RawJson publicMaterial = EventSelectionPublicResult.encode(produced.receipt(), produced.material());
        for (String field : java.util.List.of("old_event_instance_id", "starting_revision", "ending_snapshot_id")) {
            ObjectNode changed = node(publicMaterial); ObjectNode selection = (ObjectNode) changed.get("event_selection");
            switch (field) {
                case "old_event_instance_id" -> selection.put(field, 18);
                case "starting_revision" -> selection.put(field, "1");
                case "ending_snapshot_id" -> selection.put(field, "different-software-after");
                default -> throw new AssertionError(field);
            }
            RawJson changedMaterial = new RawJson(DriverJson.encodeNode(changed));
            assertThrows(IllegalArgumentException.class, () -> EventOptionPublicResponse.capture(produced.receipt(), produced.archive(), Optional.of(changedMaterial)), field);
        }
        assertEquals(produced.receipt(), produced.archive().loadReceipt(produced.archive().receiptReferenceOf(produced.receipt())));
    }
    private static ObjectNode node(RawJson raw) { return (ObjectNode) OpportunityJson.toNode(DriverJson.object(raw.bytes(), EventOptionPublicResponse.MAXIMUM_RESPONSE_BYTES)); }
}
