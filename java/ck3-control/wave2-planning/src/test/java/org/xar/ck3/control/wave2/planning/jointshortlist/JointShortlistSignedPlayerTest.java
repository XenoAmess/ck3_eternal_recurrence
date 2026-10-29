package org.xar.ck3.control.wave2.planning.jointshortlist;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.math.BigInteger;
import java.util.List;
import java.util.function.Consumer;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.finance.jointbudget.JointBudgetCodec;

/** Source-derived producer inputs exercise prepare -> proposal normalizer -> Frame -> budget -> JSON. */
final class JointShortlistSignedPlayerTest {
    private static final ObjectMapper JSON = new ObjectMapper().enable(DeserializationFeature.USE_BIG_INTEGER_FOR_INTS);
    private static final List<BigInteger> PLAYERS = List.of(BigInteger.valueOf(-2), BigInteger.valueOf(Integer.MIN_VALUE),
            BigInteger.ZERO, BigInteger.valueOf(Integer.MAX_VALUE));

    @Test void normalObservedProposalAndPricedReadbackPreserveTheSignedNativePlayerAcrossBothPolicies() throws IOException {
        for (BigInteger player : PLAYERS) {
            ObjectNode request = input("priced-war-current-readback");
            assertFalse(request.get("observed_proposals").isEmpty(), "the real normalization path must remain present");
            bindPlayer(request, JSON.getNodeFactory().numberNode(player)); byte[] raw = JSON.writeValueAsBytes(request);
            var prepared = JointShortlistCodec.decode(raw);
            assertEquals(player, prepared.frame().player());
            assertNotNull(prepared.assessedInput());
            assertEquals(player, prepared.assessedInput().snapshot().frame().player());
            assertEquals(player, prepared.assessedInput().intake().frame().identity().player());
            for (var row : prepared.assessedInput().assessments()) assertEquals(player, row.frame().player());
            var analysis = prepared.analyze(); assertNotNull(analysis);
            assertEquals(player, analysis.frame().player());
            JsonNode budgetWire = JSON.readTree(JointBudgetCodec.encode(analysis));
            assertTrue(budgetWire.get("played_character_id").isIntegralNumber());
            assertEquals(player, budgetWire.get("played_character_id").bigIntegerValue());
            byte[] response = JointShortlistCodec.compare(raw); JsonNode wire = JSON.readTree(response);
            assertTrue(wire.get("frame").get("played_character_id").isIntegralNumber());
            assertEquals(player, wire.get("frame").get("played_character_id").bigIntegerValue());
            assertEquals(player, wire.get("analysis").get("played_character_id").bigIntegerValue());
            assertFalse(wire.get("reservation_created").booleanValue());
            assertFalse(wire.get("formal_action_ready").booleanValue()); assertTrue(wire.get("selected_step").isNull());
            assertArrayEquals(response, JointShortlistCodec.compare(JSON.writeValueAsBytes(JSON.readTree(raw))));
        }
    }

    @Test void unpricedProducerStillRetainsSignedPlayerWithoutBecomingExecutable() throws IOException {
        for (BigInteger player : PLAYERS) {
            ObjectNode request = input("unpriced-specific-observation-gaps");
            assertFalse(request.get("observed_proposals").isEmpty());
            bindPlayer(request, JSON.getNodeFactory().numberNode(player));
            byte[] raw = JSON.writeValueAsBytes(request); var prepared = JointShortlistCodec.decode(raw);
            assertEquals(JointShortlist.Phase.fewer_than_five_priced_legal_candidates, prepared.phase());
            assertEquals(player, prepared.frame().player()); assertNull(prepared.analyze());
            assertFalse(prepared.formalActionReady()); assertFalse(prepared.reservationCreated());
            JsonNode wire = JSON.readTree(JointShortlistCodec.compare(raw));
            assertEquals(player, wire.get("frame").get("played_character_id").bigIntegerValue());
            assertTrue(wire.get("analysis").isNull());
        }
    }

    @Test void invalidSignedDomainAndNonIntegerPublicJsonDoNotReachShortlistPreparation() throws IOException {
        for (String token : List.of("-1", "-2147483649", "2147483648", "true", "false", "-2.0", "0.0",
                "\"-2\"", "null", "{}", "[]")) {
            ObjectNode request = input("priced-war-current-readback"); bindPlayer(request, JSON.readTree(token));
            byte[] raw = JSON.writeValueAsBytes(request);
            assertThrows(IllegalArgumentException.class, () -> JointShortlistCodec.compare(raw), token);
        }
        ObjectNode missing = input("priced-war-current-readback"); bindPlayer(missing, JSON.getNodeFactory().numberNode(-2));
        ((ObjectNode) missing.get("snapshot")).remove("played_character_id");
        byte[] raw = JSON.writeValueAsBytes(missing);
        assertThrows(IllegalArgumentException.class, () -> JointShortlistCodec.compare(raw));
    }

    @Test void fullFrameRevisionDateAndIndependentClaimsRemainStrict() throws IOException {
        List<Consumer<ObjectNode>> invalid = List.of(
                request -> ((ObjectNode) request.get("snapshot")).put("native_revision", 0),
                request -> ((ObjectNode) request.get("snapshot")).put("revision", 0),
                request -> ((ObjectNode) request.get("snapshot")).put("date_raw", -1),
                request -> ((ObjectNode) request.get("assessments").get(0)).put("played_character_id", 0),
                request -> ((ObjectNode) request.get("existing_commitments").get("frame")).put("played_character_id", 0),
                request -> ((ObjectNode) request.get("observed_proposals").get(0).get("frame")).put("played_character_id", 0),
                request -> ((ArrayNode) request.get("assessments").get(0).get("character_ids")).set(0, JSON.getNodeFactory().numberNode(-2)),
                request -> ((ArrayNode) request.get("assessments").get(0).get("ally_character_ids")).add(0));
        for (Consumer<ObjectNode> mutation : invalid) {
            ObjectNode request = input("priced-war-current-readback"); bindPlayer(request, JSON.getNodeFactory().numberNode(-2));
            mutation.accept(request); byte[] raw = JSON.writeValueAsBytes(request);
            assertThrows(IllegalArgumentException.class, () -> JointShortlistCodec.compare(raw));
        }
    }

    /** Rebind only public actor/frame observations. Independent candidate IDs and resource claims remain original. */
    private static void bindPlayer(JsonNode node, JsonNode value) {
        if (node instanceof ObjectNode object) {
            if (object.has("played_character_id")) object.set("played_character_id", value);
            if (object.get("played_character") instanceof ObjectNode played) played.set("character_id", value);
            if (object.has("actor_character_id")) object.set("actor_character_id", value);
        }
        if (node.isContainerNode()) for (JsonNode child : node) bindPlayer(child, value);
    }

    private static ObjectNode input(String name) throws IOException {
        try (InputStream stream = JointShortlistSignedPlayerTest.class.getResourceAsStream("/jointshortlist/original-producer-golden.json")) {
            if (stream == null) throw new IOException("original producer golden required");
            for (JsonNode scenario : JSON.readTree(stream).get("cases"))
                if (name.equals(scenario.get("name").textValue())) return (ObjectNode) scenario.get("input").deepCopy();
        }
        throw new IOException("original producer case missing: " + name);
    }
}
