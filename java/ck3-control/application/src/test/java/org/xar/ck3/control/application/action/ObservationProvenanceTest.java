package org.xar.ck3.control.application.action;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

final class ObservationProvenanceTest {
    private static final ExactRef PACKET = new ExactRef("D:/software-vector/original.packet", 37, "a".repeat(64));
    @Test void pushAndQueryRoundTripWithoutInventingARequestId() {
        var push = new ObservationProvenance.Push("snapshot-2", new BigInteger("9007199254740993"), PACKET);
        assertEquals(push, ObservationProvenanceCodec.decode(ObservationProvenanceCodec.encode(push)));
        assertEquals("9007199254740993", ObservationProvenanceCodec.encode(push).get("native_revision").textValue());
        assertFalse(ObservationProvenanceCodec.encode(push).has("request_id"));
        var query = new ObservationProvenance.Query("actual-read");
        assertEquals(query, ObservationProvenanceCodec.decode(ObservationProvenanceCodec.encode(query)));
        assertFalse(query.independentOf("actual-read")); assertTrue(query.independentOf("mutation"));
    }
    @Test void wrongTypesMissingFieldsAndNoncanonicalRevisionsAreRejected() {
        var valid = ObservationProvenanceCodec.encode(new ObservationProvenance.Push("snapshot", BigInteger.ONE, PACKET));
        for (String token : new String[] {"true", "1", "1.0", "null", "\"01\"", "\"-1\""}) {
            var changed = valid.deepCopy(); changed.set("native_revision", StrictJson.parse(token.getBytes(java.nio.charset.StandardCharsets.UTF_8)));
            assertThrows(IllegalArgumentException.class, () -> ObservationProvenanceCodec.decode(changed));
        }
        var missing = valid.deepCopy(); missing.remove("original_packet");
        assertThrows(IllegalArgumentException.class, () -> ObservationProvenanceCodec.decode(missing));
        var queryWithPush = ObservationProvenanceCodec.encode(new ObservationProvenance.Query("query")); queryWithPush.set("original_packet", PACKET.toJson());
        assertThrows(IllegalArgumentException.class, () -> ObservationProvenanceCodec.decode(queryWithPush));
    }
}
