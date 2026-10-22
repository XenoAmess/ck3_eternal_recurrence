package org.xar.ck3.control.events.mandatorychoice;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.events.mandatorychoice.MandatoryChoiceModel.*;

import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.Optional;
import java.util.stream.Stream;
import java.util.stream.StreamSupport;
import org.junit.jupiter.api.DynamicTest;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestFactory;

final class MandatoryChoicePolicyTest {
    private static final ObjectMapper JSON = new ObjectMapper()
            .enable(DeserializationFeature.USE_BIG_INTEGER_FOR_INTS);

    @TestFactory
    Stream<DynamicTest> actualPythonProducerGoldenVectors() throws IOException {
        JsonNode golden = golden();
        assertEquals("xar.java-mandatory-choice-golden/v1", golden.path("schema").textValue());
        assertEquals(17, golden.path("cases").size());
        assertTrue(golden.path("provenance").path("producer_sha256").textValue().matches("[0-9a-f]{64}"));
        return StreamSupport.stream(golden.path("cases").spliterator(), false).map(row ->
                DynamicTest.dynamicTest(row.path("name").textValue(), () -> {
                    Optional<FrameBinding> expected = row.path("expected_frame").isNull() ? Optional.empty()
                            : Optional.of(MandatoryChoiceCodec.decodeFrame(bytes(row.get("expected_frame"))));
                    Mode mode = "unknown".equals(row.path("mode").textValue())
                            ? Mode.UNKNOWN_MANDATORY : Mode.EXISTING_NATIVE_DOMAIN;
                    byte[] encoded = MandatoryChoiceCodec.select(bytes(row.get("input")), mode, expected);
                    assertEquals(row.get("output"), JSON.readTree(encoded), "actual legacy producer output");
                    NativeWindow window = MandatoryChoiceCodec.decode(bytes(row.get("input")));
                    assertEquals(row.get("input"), JSON.readTree(MandatoryChoiceCodec.encodeWindow(window)),
                            "complete native evidence survives serialization");
                }));
    }

    @Test
    void wrongIntegerTokensAndFrameFieldsAreRejectedBeforeChoice() throws IOException {
        for (String name : new String[] {"game_pid", "connection_generation", "revision", "native_revision",
                "date_raw", "actor_character_id"}) {
            for (JsonNode invalid : new JsonNode[] {JSON.getNodeFactory().booleanNode(true),
                    JSON.getNodeFactory().numberNode(1.0), JSON.getNodeFactory().textNode("1")}) {
                ObjectNode input = base();
                ((ObjectNode) input.get("frame_binding")).set(name, invalid);
                assertThrows(IllegalArgumentException.class, () -> MandatoryChoiceCodec.decode(bytes(input)), name);
            }
            ObjectNode missing = base();
            ((ObjectNode) missing.get("frame_binding")).remove(name);
            assertThrows(IllegalArgumentException.class, () -> MandatoryChoiceCodec.decode(bytes(missing)), name);
        }
        ObjectNode unknown = base();
        ((ObjectNode) unknown.get("frame_binding")).put("epoch_alias", 1);
        assertThrows(IllegalArgumentException.class, () -> MandatoryChoiceCodec.decode(bytes(unknown)));
    }

    @Test
    void idsIndicesBooleansAndGeometryDoNotCoerce() throws IOException {
        for (String field : new String[] {"choice_id", "native_index", "rendered_index"}) {
            for (JsonNode invalid : new JsonNode[] {JSON.getNodeFactory().booleanNode(true),
                    JSON.getNodeFactory().numberNode(1.0)}) {
                ObjectNode input = base(); choice(input, 0).set(field, invalid);
                assertThrows(IllegalArgumentException.class, () -> MandatoryChoiceCodec.decode(bytes(input)), field);
            }
        }
        for (String field : new String[] {"visible", "enabled", "is_choice"}) {
            ObjectNode input = base(); choice(input, 0).put(field, 1);
            assertThrows(IllegalArgumentException.class, () -> MandatoryChoiceCodec.decode(bytes(input)), field);
        }
        ObjectNode input = base(); input.put("window_instance_id", true);
        assertThrows(IllegalArgumentException.class, () -> MandatoryChoiceCodec.decode(bytes(input)));
        ObjectNode geometry = base(); ((ObjectNode) choice(geometry, 0).get("bounds")).put("left", true);
        assertThrows(IllegalArgumentException.class, () -> MandatoryChoiceCodec.decode(bytes(geometry)));
        ObjectNode unknown = base(); choice(unknown, 0).put("enabled_alias", true);
        assertThrows(IllegalArgumentException.class, () -> MandatoryChoiceCodec.decode(bytes(unknown)));
    }

    @Test
    void uint64ValuesStayExactAndOutOfRangeIsRejected() throws IOException {
        BigInteger maximum = new BigInteger("18446744073709551615");
        ObjectNode input = base(); ((ObjectNode) input.get("frame_binding")).put("native_revision", maximum);
        input.put("window_instance_id", maximum); choice(input, 0).put("choice_id", maximum);
        NativeWindow window = MandatoryChoiceCodec.decode(bytes(input));
        assertEquals(maximum, window.frame().nativeRevision());
        assertEquals(new IntegerIdentity(maximum), window.windowInstanceId().value());
        assertEquals(maximum, JSON.readTree(MandatoryChoiceCodec.encodeWindow(window)).get("window_instance_id").bigIntegerValue());
        ((ObjectNode) input.get("frame_binding")).put("native_revision", maximum.add(BigInteger.ONE));
        assertThrows(IllegalArgumentException.class, () -> MandatoryChoiceCodec.decode(bytes(input)));
        ObjectNode zeroPid = base(); ((ObjectNode) zeroPid.get("frame_binding")).put("game_pid", 0);
        assertThrows(IllegalArgumentException.class, () -> MandatoryChoiceCodec.decode(bytes(zeroPid)));
    }

    @Test
    void duplicateKeysTrailingInputMalformedUtf8AndUnknownFieldsAreRejected() throws IOException {
        String valid = JSON.writeValueAsString(base());
        byte[] duplicate = ("{\"window_type\":\"generic\"," + valid.substring(1)).getBytes(StandardCharsets.UTF_8);
        assertThrows(IllegalArgumentException.class, () -> MandatoryChoiceCodec.decode(duplicate));
        assertThrows(IllegalArgumentException.class,
                () -> MandatoryChoiceCodec.decode((valid + " {}").getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class, () -> MandatoryChoiceCodec.decode(new byte[] {(byte) 0xc3, 0x28}));
        ObjectNode unknown = base(); unknown.put("accept_as_success", true);
        assertThrows(IllegalArgumentException.class, () -> MandatoryChoiceCodec.decode(bytes(unknown)));
        ObjectNode missing = base(); missing.remove("choices");
        assertThrows(IllegalArgumentException.class, () -> MandatoryChoiceCodec.decode(bytes(missing)));
    }

    @Test
    void missingNullAndEmptyRemainDistinctAndCollectionsAreImmutable() throws IOException {
        ObjectNode absent = base(); choice(absent, 0).remove("action_token"); absent.remove("source_identity");
        NativeWindow absentWindow = MandatoryChoiceCodec.decode(bytes(absent));
        assertEquals(Presence.MISSING, ((NativeChoice) absentWindow.choices().getFirst()).actionToken().presence());
        assertEquals(Presence.MISSING, absentWindow.sourceIdentity().presence());
        ObjectNode nullable = base(); choice(nullable, 0).putNull("action_token"); nullable.putNull("source_identity");
        NativeWindow nullWindow = MandatoryChoiceCodec.decode(bytes(nullable));
        assertEquals(Presence.NULL, ((NativeChoice) nullWindow.choices().getFirst()).actionToken().presence());
        assertEquals(Presence.NULL, nullWindow.sourceIdentity().presence());
        ObjectNode empty = base(); empty.set("choices", JSON.createArrayNode());
        NativeWindow emptyWindow = MandatoryChoiceCodec.decode(bytes(empty));
        assertTrue(emptyWindow.choices().isEmpty());
        assertEquals(Status.MECHANISM_UNAVAILABLE,
                MandatoryChoicePolicy.selectUnknownMandatory(emptyWindow, Optional.empty()).status());
        assertThrows(UnsupportedOperationException.class, () -> absentWindow.choices().clear());
        assertEquals(absent, JSON.readTree(MandatoryChoiceCodec.encodeWindow(absentWindow)));
        assertEquals(nullable, JSON.readTree(MandatoryChoiceCodec.encodeWindow(nullWindow)));
    }

    @Test
    void nativeSourceAndEpisodeSurviveAndRecommendationHasNoSubmissionCredit() throws IOException {
        ObjectNode input = base(); byte[] raw = bytes(input);
        NativeWindow window = MandatoryChoiceCodec.decode(raw); raw[0] = 0;
        Decision decision = MandatoryChoicePolicy.selectUnknownMandatory(window, Optional.of(window.frame()));
        assertEquals(Status.RECOMMENDED, decision.status());
        assertEquals("native-1128-offline", decision.evidence().window().frame().episodeRunId());
        assertEquals("0xabcd", ((TextIdentity) window.windowInstanceId().value()).value());
        assertEquals("0123456789abcdef0123456789abcdef", window.queryId().value());
        assertEquals(input.get("source_identity"), JSON.readTree(window.sourceIdentity().value().json()));
        assertFalse(decision.dispatchAttempted()); assertFalse(decision.commandAcknowledged());
        assertFalse(decision.originalWindowAdvancedVerified()); assertFalse(decision.materialEffectsVerified());
        assertFalse(decision.replayAllowed());
        assertThrows(UnsupportedOperationException.class, () -> decision.evidence().excluded().clear());
        assertEquals(input, JSON.readTree(MandatoryChoiceCodec.encodeWindow(window)));
    }

    @Test
    void utf32TieOrderMatchesPythonInsteadOfJavaUtf16() throws IOException {
        ObjectNode input = base(); ObjectNode first = choice(input, 0); ObjectNode second = choice(input, 1);
        first.put("choice_id", "😀"); second.put("choice_id", "\ue000");
        second.set("bounds", first.get("bounds").deepCopy());
        Decision decision = MandatoryChoicePolicy.selectUnknownMandatory(MandatoryChoiceCodec.decode(bytes(input)), Optional.empty());
        assertEquals("\ue000", ((TextIdentity) decision.selectedChoice().orElseThrow().identity()).value());
    }

    @Test
    void interactionNotificationsRemainWithDedicatedLeftReplyPolicyEvenIfRightIsEnabled() throws IOException {
        ObjectNode input = base(); input.put("window_type", "pending_character_interaction");
        choice(input, 0).put("enabled", false);
        NativeWindow window = MandatoryChoiceCodec.decode(bytes(input));
        for (Mode mode : Mode.values()) {
            Decision decision = MandatoryChoicePolicy.select(window, Optional.empty(), mode);
            assertEquals(Status.MECHANISM_UNAVAILABLE, decision.status());
            assertEquals("pending_interaction_requires_dedicated_left_reply_policy", decision.reason());
            assertTrue(decision.selectedChoice().isEmpty());
        }
    }

    private static JsonNode golden() throws IOException {
        try (InputStream input = MandatoryChoicePolicyTest.class.getResourceAsStream("/mandatorychoice/producer-golden-v1.json")) {
            if (input == null) { throw new IOException("committed producer golden is missing"); }
            return JSON.readTree(input);
        }
    }
    private static ObjectNode base() throws IOException { return (ObjectNode) golden().path("cases").get(0).get("input").deepCopy(); }
    private static ObjectNode choice(ObjectNode input, int index) { return (ObjectNode) ((ArrayNode) input.get("choices")).get(index); }
    private static byte[] bytes(JsonNode node) throws IOException { return JSON.writeValueAsBytes(node); }
}
