package org.xar.ck3.control.wave2.planning.jointshortlist;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.function.Consumer;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

final class JointShortlistTest {
    private static final ObjectMapper JSON = new ObjectMapper().enable(DeserializationFeature.USE_BIG_INTEGER_FOR_INTS);

    @Test void comparesActualOriginalProducerProjectionWithoutCopyingReservation() throws IOException {
        JsonNode fixture = fixture(); assertEquals(9, fixture.get("cases").size());
        int accepted = 0; int rejected = 0;
        for (JsonNode scenario : fixture.get("cases")) {
            byte[] raw = JSON.writeValueAsBytes(scenario.get("input"));
            if (scenario.has("expected_preparation")) {
                JsonNode actual = JSON.readTree(JointShortlistCodec.compare(raw));
                assertEquals(scenario.get("expected_preparation"), actual, scenario.get("name").textValue());
                assertFalse(actual.get("reservation_created").booleanValue()); accepted++;
            } else {
                assertThrows(IllegalArgumentException.class, () -> JointShortlistCodec.compare(raw), scenario.get("name").textValue()); rejected++;
            }
        }
        assertEquals(5, accepted); assertEquals(4, rejected);
    }

    @Test void fullFrameAndCommonValueRemainNecessaryBeforeTypedSelectorPort() throws IOException {
        List<Consumer<ObjectNode>> mutations = List.of(
                root -> ((ObjectNode) root.get("intake")).put("episode_run_id", "other-episode"),
                root -> ((ObjectNode) root.get("assessments").get(0)).put("snapshot_id", "other-snapshot"),
                root -> ((ObjectNode) root.get("existing_commitments").get("frame")).put("revision", 999),
                root -> ((ObjectNode) root.get("assessments").get(0)).remove("common_value_policy"),
                root -> ((ObjectNode) root.get("existing_commitments")).remove("pending_war_slots"),
                root -> ((ObjectNode) root.get("existing_commitments")).put("pending_war_slots", 2),
                root -> root.put("unexpected", true),
                root -> root.remove("max_active_wars"));
        for (Consumer<ObjectNode> mutation : mutations) {
            ObjectNode input = input("six-valued-rows-gift-wins"); mutation.accept(input);
            byte[] raw = JSON.writeValueAsBytes(input);
            assertThrows(IllegalArgumentException.class, () -> JointShortlistCodec.compare(raw));
        }
    }

    @Test void rawFloatAndBooleanCannotBecomeIntegerThroughNormalization() throws IOException {
        String raw = JSON.writeValueAsString(input("six-valued-rows-gift-wins"));
        String floating = raw.replaceFirst("\"benefit_units\":2", "\"benefit_units\":2.0");
        assertTrue(floating.contains("\"benefit_units\":2.0"));
        assertThrows(IllegalArgumentException.class, () -> JointShortlistCodec.compare(floating.getBytes(StandardCharsets.UTF_8)));
        String bool = raw.replaceFirst("\"benefit_units\":2", "\"benefit_units\":true");
        assertThrows(IllegalArgumentException.class, () -> JointShortlistCodec.compare(bool.getBytes(StandardCharsets.UTF_8)));
        String nullValue = raw.replaceFirst("\"benefit_units\":2", "\"benefit_units\":null");
        assertThrows(IllegalArgumentException.class, () -> JointShortlistCodec.compare(nullValue.getBytes(StandardCharsets.UTF_8)));
    }

    @Test void opaqueObservedEvidenceCanContainDecimalWithoutChangingIntegerFields() throws IOException {
        ObjectNode input = input("six-valued-rows-gift-wins");
        ((ObjectNode) input.get("observed_proposals").get(0).get("evidence")).put("opaque_decimal_observation", 1.5);
        JointShortlist.Prepared prepared = JointShortlistCodec.decode(JSON.writeValueAsBytes(input));
        assertEquals(JointShortlist.Phase.assessed_comparison_prepared, prepared.phase());
        assertNotNull(prepared.analyze().selectedCandidateId());
    }

    @Test void earlyUnpricedResultDoesNotRequireTreasuryOrGrantFutureReadiness() throws IOException {
        ObjectNode input = input("unpriced-specific-observation-gaps");
        ((ObjectNode) input.get("snapshot")).remove("played_character_gold");
        input.putNull("existing_commitments"); input.putNull("gold_reserve_raw");
        JointShortlist.Prepared prepared = JointShortlistCodec.decode(JSON.writeValueAsBytes(input));
        assertEquals(JointShortlist.Phase.fewer_than_five_priced_legal_candidates, prepared.phase());
        assertNull(prepared.analyze()); assertFalse(prepared.reservationCreated()); assertFalse(prepared.formalActionReady());
        assertEquals(7, prepared.unpricedCandidates().size());
        assertThrows(UnsupportedOperationException.class, () -> prepared.unpricedCandidates().clear());
    }

    @Test void warCurrentReadbackRetainsRaisedSupplyButDoesNotInventFutureSupply() throws IOException {
        byte[] raw = JSON.writeValueAsBytes(input("priced-war-current-readback"));
        JointShortlist.Prepared prepared = JointShortlistCodec.decode(raw);
        assertNotNull(prepared.currentWarResources()); assertFalse(prepared.currentWarResources().futureSupplyReady());
        JsonNode result = JSON.readTree(JointShortlistCodec.compare(raw));
        assertTrue(result.get("current_war_resources").get("actor_current_raised_supply").get(0).has("native_carmy_id"));
        assertEquals("war:29097-11-0", prepared.analyze().selectedCandidateId());
        assertFalse(prepared.formalActionReady());
    }

    @Test void currentReadbackCannotChangeActorDeclarationOrSupplyIdentity() throws IOException {
        List<Consumer<ObjectNode>> mutations = List.of(
                root -> ((ObjectNode) root.get("marriage_projection").get("rows").get(0)).put("actor_character_id", 999),
                root -> ((ObjectNode) root.get("marriage_projection").get("rows").get(0)).put("candidate_character_id", 999),
                root -> ((ObjectNode) root.get("war_current").get("readiness")).put("current_raised_supply_ready", false),
                root -> ((ObjectNode) root.get("war_current")).put("queried_native_revision", 999),
                root -> ((ObjectNode) root.get("war_current").get("m5_war_primary_current").get("declaration")).put("claimant_character_id", true),
                root -> ((ObjectNode) root.get("war_current").get("m5_war_primary_current").get("actor_current_raised_supply").get(0)).put("army_id", 999),
                root -> ((ObjectNode) root.get("war_current").get("m5_war_primary_current").get("actor_current_raised_supply").get(0)).putNull("current_supply_raw"),
                root -> ((ObjectNode) root.get("war_current").get("m5_war_primary_current").get("actor_current_raised_supply").get(0)).put("current_supply_scale", 100));
        for (Consumer<ObjectNode> mutation : mutations) {
            ObjectNode input = input("priced-war-current-readback"); mutation.accept(input);
            byte[] raw = JSON.writeValueAsBytes(input);
            assertThrows(IllegalArgumentException.class, () -> JointShortlistCodec.compare(raw));
        }
    }

    @Test void duplicateKeysAndRequestSerializationRoundTripsAreChecked() throws IOException {
        byte[] raw = JSON.writeValueAsBytes(input("six-valued-rows-gift-wins"));
        byte[] first = JointShortlistCodec.compare(raw);
        byte[] roundTrip = JointShortlistCodec.compare(JSON.writeValueAsBytes(JSON.readTree(raw)));
        assertEquals(JSON.readTree(first), JSON.readTree(roundTrip));
        String duplicated = new String(raw, StandardCharsets.UTF_8).replaceFirst("\\{", "{\"max_active_wars\":1,");
        assertThrows(IllegalArgumentException.class, () -> JointShortlistCodec.compare(duplicated.getBytes(StandardCharsets.UTF_8)));
        String trailing = new String(raw, StandardCharsets.UTF_8) + " {}";
        assertThrows(IllegalArgumentException.class, () -> JointShortlistCodec.compare(trailing.getBytes(StandardCharsets.UTF_8)));
        // Existing shared immutable JSON codec is the only opaque evidence domain used at the boundary.
        assertTrue(OpportunityJson.parse(first) instanceof OpportunityJson.Obj);
    }

    private static ObjectNode input(String name) throws IOException {
        for (JsonNode row : fixture().get("cases")) {
            if (row.get("name").textValue().equals(name)) { return (ObjectNode) row.get("input").deepCopy(); }
        }
        throw new IOException("required actual original-producer fixture is absent: " + name);
    }
    private static JsonNode fixture() throws IOException {
        try (InputStream stream = JointShortlistTest.class.getResourceAsStream("/jointshortlist/original-producer-golden.json")) {
            if (stream == null) { throw new IOException("committed actual original-producer golden required; not a skipped test"); }
            return JSON.readTree(stream);
        }
    }
}
