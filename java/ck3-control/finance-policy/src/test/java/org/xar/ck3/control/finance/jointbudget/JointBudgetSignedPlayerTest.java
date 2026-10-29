package org.xar.ck3.control.finance.jointbudget;

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
import java.util.HashSet;
import java.util.Set;
import java.util.function.Consumer;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;

/** Original producer requests enter the real codec/Frame/selector/encoder path; no Frame DTO is fabricated. */
final class JointBudgetSignedPlayerTest {
    private static final ObjectMapper JSON = new ObjectMapper().enable(DeserializationFeature.USE_BIG_INTEGER_FOR_INTS);
    private static final List<BigInteger> PLAYERS = List.of(BigInteger.valueOf(-2), BigInteger.valueOf(Integer.MIN_VALUE),
            BigInteger.ZERO, BigInteger.valueOf(Integer.MAX_VALUE));

    @Test void nativeSignedPlayerSurvivesActualFrameProductionSelectionAndJsonRoundTrip() throws IOException {
        for (String name : List.of("observed-ids-synthetic-values", "actual-normalized-domain-proposal-minimum-reserve")) {
            for (BigInteger player : PLAYERS) {
                ObjectNode request = input(name); bindPlayer(request, JSON.getNodeFactory().numberNode(player));
                byte[] raw = JSON.writeValueAsBytes(request);
                var decoded = assertInstanceOf(JointBudgetSelector.AssessedInput.class, JointBudgetCodec.decode(raw));
                assertEquals(player, decoded.snapshot().frame().player());
                assertEquals(player, decoded.intake().frame().identity().player());
                for (var row : decoded.assessments()) assertEquals(player, row.frame().player());
                var result = JointBudgetSelector.select(decoded);
                byte[] response = JointBudgetCodec.encode(result);
                JsonNode wire = StrictJson.parse(response);
                assertTrue(wire.get("played_character_id").isIntegralNumber());
                assertEquals(player, wire.get("played_character_id").bigIntegerValue());
                assertEquals(decoded.snapshot().frame(), result.frame());
                assertFalse(result.formalActionReady()); assertTrue(wire.get("selected_step").isNull());
                assertArrayEquals(response, JointBudgetCodec.select(JSON.writeValueAsBytes(JSON.readTree(raw))));
                assertArrayEquals(response, StrictJson.canonical(StrictJson.parse(response)));
            }
        }
    }

    @Test void signedCharacterIdsSurviveClaimsCodecRoundTrip() throws IOException {
        for (BigInteger id : PLAYERS) {
            ObjectNode request = input("observed-ids-synthetic-values");
            bindPlayer(request, JSON.getNodeFactory().numberNode(-2));
            ObjectNode originalAssessment = (ObjectNode) request.get("assessments").get(0);
            Set<BigInteger> expected = new HashSet<>();
            originalAssessment.get("character_ids").forEach(value -> expected.add(value.bigIntegerValue()));
            expected.add(id);
            ((ArrayNode) originalAssessment.get("character_ids")).add(id);
            byte[] raw = JSON.writeValueAsBytes(request);
            var decoded = assertInstanceOf(JointBudgetSelector.AssessedInput.class, JointBudgetCodec.decode(raw));
            assertEquals(expected, decoded.assessments().get(0).claims().characterIds());
            var result = JointBudgetSelector.select(decoded);
            byte[] response = JointBudgetCodec.encode(result);
            JsonNode wire = StrictJson.parse(response);
            boolean found = false;
            for (JsonNode row : wire.get("evaluated")) {
                if (!originalAssessment.get("candidate_id").equals(row.get("candidate_id"))) continue;
                Set<BigInteger> retained = new HashSet<>();
                row.get("claims").get("character_ids").forEach(value -> retained.add(value.bigIntegerValue()));
                assertEquals(expected, retained); found = true;
            }
            assertTrue(found, "the original candidate's exact claims must survive selection and encoding");
            assertArrayEquals(response, JointBudgetCodec.select(raw));
        }
    }

    @Test void signedCharacterClaimsRejectSentinelsAliasesTypesAndDuplicates() throws IOException {
        for (String token : List.of("-1", "-2147483649", "2147483648", "4294967294", "true", "false", "-2.0",
                "\"-2\"", "null", "{}", "[]")) {
            ObjectNode request = input("observed-ids-synthetic-values");
            ((ArrayNode) request.get("assessments").get(0).get("character_ids")).add(JSON.readTree(token));
            byte[] raw = JSON.writeValueAsBytes(request);
            assertThrows(IllegalArgumentException.class, () -> JointBudgetCodec.select(raw), token);
        }
        ObjectNode duplicate = input("observed-ids-synthetic-values");
        ((ArrayNode) duplicate.get("assessments").get(0).get("character_ids")).add(-2).add(-2);
        byte[] duplicateRaw = JSON.writeValueAsBytes(duplicate);
        assertThrows(IllegalArgumentException.class, () -> JointBudgetCodec.select(duplicateRaw));
        ObjectNode missing = input("observed-ids-synthetic-values");
        ((ObjectNode) missing.get("assessments").get(0)).remove("character_ids");
        byte[] missingRaw = JSON.writeValueAsBytes(missing);
        assertThrows(IllegalArgumentException.class, () -> JointBudgetCodec.select(missingRaw));
    }

    @Test void signedCharacterClaimsPreserveTheIndependentArmyDomainAndNativeAllyBounds() throws IOException {
        BigInteger wideArmy = BigInteger.ONE.shiftLeft(40);
        ObjectNode request = input("observed-ids-synthetic-values");
        ((ArrayNode) request.get("assessments").get(0).get("army_ids")).add(wideArmy);
        var decoded = assertInstanceOf(JointBudgetSelector.AssessedInput.class,
                JointBudgetCodec.decode(JSON.writeValueAsBytes(request)));
        assertEquals(Set.of(wideArmy), decoded.assessments().get(0).claims().armyIds());
        for (String key : List.of("army_ids", "ally_character_ids")) {
            ObjectNode invalid = input("observed-ids-synthetic-values");
            ((ArrayNode) invalid.get("assessments").get(0).get(key)).add(key.equals("army_ids") ? -2 : -1);
            byte[] raw = JSON.writeValueAsBytes(invalid);
            assertThrows(IllegalArgumentException.class, () -> JointBudgetCodec.select(raw), key);
        }
    }

    @Test void absentSentinelOutOfRangeAndNonIntegerJsonCannotEnterAnyFrame() throws IOException {
        for (String token : List.of("-1", "-2147483649", "2147483648", "true", "false", "-2.0", "0.0",
                "\"-2\"", "null", "{}", "[]")) {
            ObjectNode request = input("observed-ids-synthetic-values"); bindPlayer(request, JSON.readTree(token));
            byte[] raw = JSON.writeValueAsBytes(request);
            assertThrows(IllegalArgumentException.class, () -> JointBudgetCodec.select(raw), token);
        }
        for (String location : List.of("intake", "snapshot", "assessment")) {
            ObjectNode request = input("observed-ids-synthetic-values");
            bindPlayer(request, JSON.getNodeFactory().numberNode(-2));
            if (location.equals("intake")) ((ObjectNode) request.get("intake")).remove("played_character_id");
            else if (location.equals("snapshot")) ((ObjectNode) request.get("snapshot").get("played_character")).remove("character_id");
            else ((ObjectNode) request.get("assessments").get(0)).remove("played_character_id");
            byte[] raw = JSON.writeValueAsBytes(request);
            assertThrows(IllegalArgumentException.class, () -> JointBudgetCodec.select(raw), location);
        }
    }

    @Test void signedPlayerDoesNotChangeRevisionDateOrIndependentClaimEligibility() throws IOException {
        List<Consumer<ObjectNode>> invalid = List.of(
                request -> ((ObjectNode) request.get("snapshot")).put("native_revision", 0),
                request -> ((ObjectNode) request.get("snapshot")).put("date_raw", -1),
                request -> ((ArrayNode) request.get("assessments").get(0).get("character_ids")).set(0, JSON.getNodeFactory().numberNode(-1)),
                request -> ((ArrayNode) request.get("assessments").get(0).get("character_ids")).set(0, JSON.getNodeFactory().numberNode(2147483648L)),
                request -> ((ArrayNode) request.get("assessments").get(0).get("ally_character_ids")).add(-1));
        for (Consumer<ObjectNode> mutation : invalid) {
            ObjectNode request = input("observed-ids-synthetic-values"); bindPlayer(request, JSON.getNodeFactory().numberNode(-2));
            mutation.accept(request); byte[] raw = JSON.writeValueAsBytes(request);
            assertThrows(IllegalArgumentException.class, () -> JointBudgetCodec.select(raw));
        }
    }

    @Test void differentValidSignedPlayersStillFailTheActualSameFrameComparison() throws IOException {
        ObjectNode request = input("observed-ids-synthetic-values"); bindPlayer(request, JSON.getNodeFactory().numberNode(-2));
        ((ObjectNode) request.get("assessments").get(0)).put("played_character_id", 0);
        byte[] raw = JSON.writeValueAsBytes(request);
        assertThrows(IllegalArgumentException.class, () -> JointBudgetCodec.select(raw));
    }

    @Test void missingAssessmentsKeepSignedIdentityWithoutInventingAnAction() throws IOException {
        ObjectNode request = input("missing-assessments-is-not-zero-valued-choice");
        bindPlayer(request, JSON.getNodeFactory().numberNode(Integer.MIN_VALUE));
        var decoded = assertInstanceOf(JointBudgetSelector.MissingAssessments.class,
                JointBudgetCodec.decode(JSON.writeValueAsBytes(request)));
        var result = JointBudgetSelector.select(decoded);
        assertEquals(BigInteger.valueOf(Integer.MIN_VALUE), result.frame().player());
        assertEquals(JointBudgetSelector.Status.MISSING_ASSESSMENTS, result.status());
        assertFalse(result.formalActionReady()); assertNull(result.selectedCandidateId());
        assertEquals(BigInteger.valueOf(Integer.MIN_VALUE),
                StrictJson.parse(JointBudgetCodec.encode(result)).get("played_character_id").bigIntegerValue());
    }


    @Test void nativeAllyClaimsConstructorPreservesSignedIdentities() {
        for (BigInteger id : PLAYERS) {
            var claims = new JointBudgetSelector.Claims(Set.of(BigInteger.ONE.shiftLeft(40)),
                    Set.of(id), Set.of(id), Set.of());
            assertEquals(Set.of(id), claims.allyCharacterIds());
            assertEquals(Set.of(id), claims.characterIds());
            assertEquals(Set.of(BigInteger.ONE.shiftLeft(40)), claims.armyIds());
        }
        for (BigInteger bad : List.of(BigInteger.valueOf(-1), BigInteger.valueOf(Integer.MIN_VALUE).subtract(BigInteger.ONE),
                BigInteger.valueOf(Integer.MAX_VALUE).add(BigInteger.ONE), BigInteger.valueOf(4294967294L)))
            assertThrows(IllegalArgumentException.class, () -> new JointBudgetSelector.Claims(
                    Set.of(), Set.of(bad), Set.of(), Set.of()), bad.toString());
    }

    @Test void nativeAllyClaimsSurviveActualCodecSelectionAndConflict() throws IOException {
        for (BigInteger id : PLAYERS) {
            ObjectNode request = input("observed-ids-synthetic-values");
            ((ArrayNode) request.get("assessments").get(0).get("ally_character_ids")).removeAll().add(id);
            var decoded = assertInstanceOf(JointBudgetSelector.AssessedInput.class,
                    JointBudgetCodec.decode(JSON.writeValueAsBytes(request)));
            assertEquals(Set.of(id), decoded.assessments().get(0).claims().allyCharacterIds());
            byte[] selected = JointBudgetCodec.select(JSON.writeValueAsBytes(request));
            JsonNode row = StrictJson.parse(selected).get("evaluated").get(0);
            assertEquals(id, row.get("claims").get("ally_character_ids").get(0).bigIntegerValue());
            assertFalse(StrictJson.parse(selected).get("formal_action_ready").booleanValue());
            assertTrue(StrictJson.parse(selected).get("selected_step").isNull());
            assertArrayEquals(selected, StrictJson.canonical(StrictJson.parse(selected)));
            ((ArrayNode) request.get("commitments").get("ally_character_ids")).removeAll().add(id);
            JsonNode blocked = StrictJson.parse(JointBudgetCodec.select(JSON.writeValueAsBytes(request)));
            assertEquals("existing_commitment_conflict", blocked.get("evaluated").get(0).get("reason").textValue());
        }
    }

    @Test void nativeAllyClaimsRejectWrongLiteralTokensMissingAndDuplicateValues() throws IOException {
        for (String token : List.of("-1", "-2147483649", "2147483648", "4294967294", "true", "false",
                "1.0", "\"0\"", "null", "{}", "[]")) {
            ObjectNode request = input("observed-ids-synthetic-values");
            ((ArrayNode) request.get("assessments").get(0).get("ally_character_ids")).removeAll().add("__m7_claim_token__");
            String literal = new String(JSON.writeValueAsBytes(request), java.nio.charset.StandardCharsets.UTF_8)
                    .replace("\"__m7_claim_token__\"", token);
            assertTrue(literal.contains("\"ally_character_ids\":[" + token + "]"));
            byte[] raw = literal.getBytes(java.nio.charset.StandardCharsets.UTF_8);
            assertThrows(IllegalArgumentException.class, () -> JointBudgetCodec.select(raw), token);
        }
        ObjectNode duplicate = input("observed-ids-synthetic-values");
        ((ArrayNode) duplicate.get("assessments").get(0).get("ally_character_ids")).removeAll().add(-2).add(-2);
        byte[] repeated = JSON.writeValueAsBytes(duplicate);
        assertThrows(IllegalArgumentException.class, () -> JointBudgetCodec.select(repeated));
        ObjectNode missing = input("observed-ids-synthetic-values");
        ((ObjectNode) missing.get("assessments").get(0)).remove("ally_character_ids");
        byte[] absent = JSON.writeValueAsBytes(missing);
        assertThrows(IllegalArgumentException.class, () -> JointBudgetCodec.select(absent));
    }

    private static void bindPlayer(ObjectNode request, JsonNode value) {
        ObjectNode intake = (ObjectNode) request.get("intake"); intake.set("played_character_id", value);
        ObjectNode snapshot = (ObjectNode) request.get("snapshot");
        if (snapshot.has("played_character_id")) snapshot.set("played_character_id", value);
        else ((ObjectNode) snapshot.get("played_character")).set("character_id", value);
        for (JsonNode row : request.get("assessments")) ((ObjectNode) row).set("played_character_id", value);
        for (JsonNode row : intake.get("candidates")) {
            if (row.get("observed_proposal") instanceof ObjectNode proposal)
                ((ObjectNode) proposal.get("frame")).set("played_character_id", value);
        }
    }

    private static ObjectNode input(String name) throws IOException {
        try (InputStream stream = JointBudgetSignedPlayerTest.class.getResourceAsStream("/jointbudget/legacy-producer-golden.json")) {
            if (stream == null) throw new IOException("original producer golden required");
            for (JsonNode scenario : JSON.readTree(stream).get("cases"))
                if (name.equals(scenario.get("name").textValue())) return (ObjectNode) scenario.get("input").deepCopy();
        }
        throw new IOException("original producer case missing: " + name);
    }
}

