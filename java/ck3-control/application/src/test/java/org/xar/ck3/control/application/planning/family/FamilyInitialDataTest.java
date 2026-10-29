package org.xar.ck3.control.application.planning.family;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.charset.StandardCharsets;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.continuity.writer.DomainBodies.Slot;
import org.xar.ck3.control.contracts.StrictJson;

final class FamilyInitialDataTest {
    @Test void threeTypedInitialBodiesReachTheExistingFullDomainConsumerWithoutInventedFacts() {
        var documents = FamilyInitialData.fresh();
        assertEquals(List.of(Slot.FAMILY, Slot.CHILD_MATRILINEAL, Slot.DEFAULT_MARRIAGE), documents.bodies().stream().map(FamilyInitialData.Body::slot).toList());
        for (var body : documents.bodies()) {
            byte[] raw = FamilyInitialData.encode(body);
            assertEquals(body, FamilyInitialData.decode(body.slot(), raw));
            assertArrayEquals(raw, FamilyInitialData.encode(FamilyInitialData.decode(body.slot(), raw)));
            var actual = FamilyDomainSource.validate(body.slot(), raw);
            assertEquals(3, actual.members().size());
            assertEquals(org.xar.ck3.control.planning.opportunity.OpportunityJson.Nil.INSTANCE, actual.get("pending"));
            assertEquals(org.xar.ck3.control.planning.opportunity.OpportunityJson.Nil.INSTANCE, actual.get("resolved"));
            assertFalse(actual.members().containsKey("episode_history"));
        }
    }
    @Test void absentHistoryAndExplicitEmptyHistoryRemainDistinctAcrossSerde() {
        for (var body : FamilyInitialData.fresh().bodies()) {
            var empty = new FamilyInitialData.Body(body.slot(), FamilyInitialData.History.EMPTY);
            assertNotEquals(body, empty);
            assertEquals(empty, FamilyInitialData.decode(body.slot(), FamilyInitialData.encode(empty)));
            assertTrue(StrictJson.parse(FamilyInitialData.encode(empty), 4096).get("episode_history").isArray());
            assertFalse(java.util.Arrays.equals(FamilyInitialData.encode(body), FamilyInitialData.encode(empty)));
        }
    }
    @Test void missingNullWrongTypesExistingRecordsAndAdditionalFactsCannotBecomeInitialData() {
        for (var body : FamilyInitialData.fresh().bodies()) {
            for (String field : List.of("schema", "pending", "resolved")) {
                var missing = (com.fasterxml.jackson.databind.node.ObjectNode)StrictJson.parse(FamilyInitialData.encode(body), 4096);
                missing.remove(field);
                assertThrows(IllegalArgumentException.class, () -> FamilyInitialData.decode(body.slot(), StrictJson.canonical(missing)));
            }
            for (String field : List.of("pending", "resolved"))
                for (String value : List.of("true", "1", "1.0", "[]", "{}", "\"null\"")) {
                    String raw = new String(FamilyInitialData.encode(body), StandardCharsets.UTF_8)
                            .replace("\"" + field + "\":null", "\"" + field + "\":" + value);
                    assertThrows(IllegalArgumentException.class, () -> FamilyInitialData.decode(body.slot(), raw.getBytes(StandardCharsets.UTF_8)));
                }
            for (String value : List.of("null", "{}", "true", "[{}]")) {
                String raw = new String(FamilyInitialData.encode(body), StandardCharsets.UTF_8);
                raw = raw.substring(0, raw.lastIndexOf('}')) + ",\"episode_history\":" + value + "}";
                byte[] invalid = raw.getBytes(StandardCharsets.UTF_8);
                assertThrows(IllegalArgumentException.class, () -> FamilyInitialData.decode(body.slot(), invalid));
            }
            var extra = (com.fasterxml.jackson.databind.node.ObjectNode)StrictJson.parse(FamilyInitialData.encode(body), 4096);
            extra.put("episode_run_id", "invented");
            assertThrows(IllegalArgumentException.class, () -> FamilyInitialData.decode(body.slot(), StrictJson.canonical(extra)));
        }
        assertThrows(IllegalArgumentException.class, () -> new FamilyInitialData.Documents(FamilyInitialData.fresh().childMatrilineal(),
                FamilyInitialData.fresh().family(), FamilyInitialData.fresh().defaultMarriage()));
        assertThrows(IllegalArgumentException.class, () -> FamilyInitialData.decode(Slot.CHILD_MATRILINEAL,
                FamilyInitialData.encode(FamilyInitialData.fresh().family())));
    }
}
