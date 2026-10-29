package org.xar.ck3.control.governance.council;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.governance.council.CouncilModels.*;

final class CouncilActionCodecProducerTest {
    private static ObjectNode fixture(String name) throws Exception {
        String root = System.getProperty("xar.repository.root"); assertNotNull(root, "actual retained producer repository required");
        return CouncilCodec.object(StrictJson.parse(Files.readAllBytes(Path.of(root,
                "ck3_autonomous_player/tests/fixtures/native_12002/governance/" + name + ".json"))).get("result"));
    }
    private static CouncilActionCodec.Request request() {
        return new CouncilActionCodec.Request("assign-13", new Frame("native:13", BigInteger.valueOf(13), BigInteger.valueOf(13), 53175816, 16777217),
                Position.STEWARD, 16777232, java.util.OptionalInt.of(16777218));
    }
    @Test void genuineHelperAckRequiresIndependentLaterIncumbentReceiptAndRoundTrips() throws Exception {
        ObjectNode helper = CouncilCodec.object(fixture("council-private-ack").get("council_assign_councillor_ack"));
        var ack = CouncilActionCodec.decodeAck(StrictJson.canonical(helper), request());
        assertEquals(CouncilActionCodec.AckStatus.HELPER_INVOKED_VERIFICATION_PENDING, ack.status());
        assertFalse(ack.queueAcceptanceObserved()); assertTrue(ack.verificationPending());
        ObjectNode original = CouncilCodec.object(fixture("council-private-receipt").get("council_assign_councillor_receipt"));
        var receipt = CouncilActionCodec.decodeReceipt(StrictJson.canonical(original), ack);
        assertEquals(CouncilActionCodec.ReceiptStatus.APPLIED, receipt.status()); assertTrue(receipt.postNativeRevision().compareTo(request().frame().nativeRevision()) > 0);
        assertEquals(original, StrictJson.parse(receipt.original().bytes()));
        assertEquals(receipt, CouncilActionCodec.decodeReceipt(receipt.original().bytes(), ack));
    }
    @Test void wrongBooleanKindsCandidateAndSameFrameMaterialCannotSettle() throws Exception {
        ObjectNode helper = CouncilCodec.object(fixture("council-private-ack").get("council_assign_councillor_ack"));
        helper.put("queue_acceptance_observed", 0);
        assertThrows(IllegalArgumentException.class, () -> CouncilActionCodec.decodeAck(StrictJson.canonical(helper), request()));
        helper.put("queue_acceptance_observed", false).put("candidate_character_id", 16777233);
        assertThrows(IllegalArgumentException.class, () -> CouncilActionCodec.decodeAck(StrictJson.canonical(helper), request()));
        var ack = CouncilActionCodec.decodeAck(StrictJson.canonical(fixture("council-private-ack").get("council_assign_councillor_ack")), request());
        ObjectNode receipt = CouncilCodec.object(fixture("council-private-receipt").get("council_assign_councillor_receipt"));
        receipt.put("post_native_revision", 13);
        assertThrows(IllegalArgumentException.class, () -> CouncilActionCodec.decodeReceipt(StrictJson.canonical(receipt), ack));
        receipt.remove("post_native_revision");
        assertThrows(IllegalArgumentException.class, () -> CouncilActionCodec.decodeReceipt(StrictJson.canonical(receipt), ack));
    }
    @Test void privateWireDoesNotInventPublicFieldsOrCarryCachedPointers() {
        ObjectNode privateFields = CouncilActionCodec.wireFields(request(), true);
        assertEquals(1, privateFields.size()); assertEquals(16777232, privateFields.get("candidate_character_id").intValue());
        ObjectNode publicFields = CouncilActionCodec.wireFields(request(), false);
        assertEquals("native:13", publicFields.get("expected_snapshot_id").textValue());
        assertEquals(13, publicFields.get("expected_native_revision").intValue());
        assertFalse(publicFields.has("request_id")); assertFalse(publicFields.has("expected_revision"));
    }
}
