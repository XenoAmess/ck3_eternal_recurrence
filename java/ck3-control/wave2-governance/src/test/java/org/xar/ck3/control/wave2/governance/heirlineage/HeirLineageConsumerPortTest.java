package org.xar.ck3.control.wave2.governance.heirlineage;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.governance.heirlineage.HeirLineagePolicy.AvailablePreview;
import org.xar.ck3.control.wave2.governance.heirlineage.HeirLineagePolicy.CharacterId;
import org.xar.ck3.control.wave2.governance.heirlineage.HeirLineagePolicy.Context;
import org.xar.ck3.control.wave2.governance.heirlineage.HeirLineagePolicy.DynastyId;
import org.xar.ck3.control.wave2.governance.heirlineage.HeirLineagePolicy.Opportunity;
import org.xar.ck3.control.wave2.governance.heirlineage.HeirLineagePolicy.PreviewObservation;

final class HeirLineageConsumerPortTest {
    @Test
    void actualOldProducerGoldenMatchesDecisionQueriesEvidenceAndRoundTrip() throws IOException {
        JsonNode golden = golden();
        assertEquals(8, golden.path("cases").size());
        assertEquals("8a1ba2993c1e18728094bcac5a472332bb2e976eb435ab6929d1e444bd76d8e9",
                golden.path("sources").get(0).path("sha256").textValue());
        int accepted = 0;
        int rejected = 0;
        for (JsonNode vector : golden.path("cases")) {
            byte[] request = StrictJson.canonical(vector.path("input"));
            byte[] original = request.clone();
            if (vector.has("expected_error")) {
                var error = assertThrows(IllegalArgumentException.class,
                        () -> HeirLineageConsumerPort.evaluate(request), vector.path("name").textValue());
                assertEquals(vector.path("expected_error").textValue(), error.getMessage());
                rejected++;
            } else {
                var actual = HeirLineageConsumerPort.evaluate(request);
                assertArrayEquals(StrictJson.canonical(vector.path("expected")), actual.result(),
                        vector.path("name").textValue());
                assertArrayEquals(StrictJson.canonical(vector.path("expected_queries")),
                        StrictJson.canonical(queryJson(actual.queries())));
                assertArrayEquals(actual.result(), StrictJson.canonical(StrictJson.parse(actual.result())));
                assertArrayEquals(actual.result(), HeirLineageConsumerPort.consume(request));
                accepted++;
            }
            assertArrayEquals(original, request);
        }
        assertEquals(6, accepted);
        assertEquals(2, rejected);
    }

    @Test
    void coreStopsAfterFirstPositiveAndPreservesDistinctExpectedAndNativeRevisions() {
        CharacterId heir = new CharacterId(10);
        CharacterId first = new CharacterId(11);
        CharacterId second = new CharacterId(12);
        DynastyId dynasty = new DynastyId(BigInteger.valueOf(200));
        Context context = new Context(BigInteger.valueOf(9), BigInteger.valueOf(7), BigInteger.valueOf(53220000), heir);
        AtomicInteger calls = new AtomicInteger();
        var selected = HeirLineagePolicy.chooseInPreferenceOrder(context, List.of(
                new Opportunity(0, first, heir, false, true, Optional.of(dynasty)),
                new Opportunity(1, second, heir, false, true, Optional.of(dynasty))), query -> {
                    calls.incrementAndGet();
                    assertEquals(BigInteger.valueOf(9), query.expectedRevision());
                    assertEquals(first, query.candidate());
                    return new PreviewObservation(BigInteger.valueOf(7), context.dateRaw(), heir, first,
                            new AvailablePreview(false, true, true, Optional.of(dynasty)));
                });
        assertEquals(1, calls.get());
        assertEquals(0, selected.orderedOrdinal().orElseThrow());
        assertEquals("native_main_dynasty_opportunity", selected.attempts().get(0).reason());
        assertThrows(UnsupportedOperationException.class, selected.attempts()::clear);
    }

    @Test
    void missingTranscriptIsNotNativeUnavailableAndCannotCreateAPositiveDecision() throws IOException {
        ObjectNode input = firstInput();
        input.putArray("previews");
        var error = assertThrows(ContractViolationException.class,
                () -> HeirLineageConsumerPort.consume(StrictJson.canonical(input)));
        assertTrue(error.getMessage().contains("observation required"));
    }

    @Test
    void dateSubjectCandidateAndEffectiveOptionDriftAreRejected() throws IOException {
        for (String field : List.of("date", "subject", "candidate", "effective")) {
            ObjectNode input = firstInput();
            ObjectNode observation = (ObjectNode) input.path("previews").get(2);
            ObjectNode preview = (ObjectNode) observation.get("native_child_house_preview");
            switch (field) {
                case "date" -> ((ObjectNode) observation.get("frame")).put("date_raw", 53220001);
                case "subject" -> preview.put("subject_character_id", 50331654);
                case "candidate" -> preview.put("candidate_character_id", 50331654);
                case "effective" -> preview.put("effective_matrilineal_if_accepted", true);
                default -> throw new IllegalStateException("unexpected test branch");
            }
            assertThrows(IllegalArgumentException.class,
                    () -> HeirLineageConsumerPort.consume(StrictJson.canonical(input)), field);
        }
    }

    @Test
    void requestOptionMustMatchOriginalNormalizedPreviewAndDoesNotCoerce() throws IOException {
        ObjectNode input = firstInput();
        ObjectNode preview = (ObjectNode) input.path("previews").get(2).get("native_child_house_preview");
        preview.put("requested_matrilineal_option", true);
        assertThrows(ContractViolationException.class,
                () -> HeirLineageConsumerPort.consume(StrictJson.canonical(input)));
        for (String raw : List.of("1", "0", "1.0", "\"false\"", "null")) {
            String original = new String(StrictJson.canonical(firstInput()), StandardCharsets.UTF_8);
            // The original token is sent directly: 1.0 is never normalized through a JSON tree.
            String mutated = original.replace("\"requested_matrilineal_option\":false",
                    "\"requested_matrilineal_option\":" + raw);
            assertThrows(ContractViolationException.class,
                    () -> HeirLineageConsumerPort.consume(mutated.getBytes(StandardCharsets.UTF_8)), raw);
        }
    }

    @Test
    void revisionAndIdentityTokensRejectBooleanFloatStringAndOutOfNativeRange() throws IOException {
        String input = new String(StrictJson.canonical(firstInput()), StandardCharsets.UTF_8);
        for (String raw : List.of("true", "7.0", "\"7\"", "null")) {
            String mutated = input.replace("\"native_revision\":7", "\"native_revision\":" + raw);
            assertThrows(ContractViolationException.class,
                    () -> HeirLineageConsumerPort.consume(mutated.getBytes(StandardCharsets.UTF_8)), raw);
        }
        for (String raw : List.of("true", "50331653.0", "\"50331653\"", "0", "4294967296")) {
            String mutated = input.replace("\"candidate_character_id\":50331653",
                    "\"candidate_character_id\":" + raw);
            assertThrows(ContractViolationException.class,
                    () -> HeirLineageConsumerPort.consume(mutated.getBytes(StandardCharsets.UTF_8)), raw);
        }
        assertEquals(4_294_967_295L, new CharacterId(4_294_967_295L).value());
        assertThrows(IllegalArgumentException.class, () -> new CharacterId(4_294_967_296L));
    }

    @Test
    void missingNullableDynastyIsDifferentFromObservedNullAndUnknownStatusIsRejected() throws IOException {
        ObjectNode missing = firstInput();
        ((ObjectNode) missing.path("projection").path("rows").get(2)).remove("played_dynasty_id");
        assertThrows(ContractViolationException.class,
                () -> HeirLineageConsumerPort.consume(StrictJson.canonical(missing)));
        ObjectNode unavailable = firstInput();
        ((ObjectNode) unavailable.path("previews").get(2).get("native_child_house_preview"))
                .put("status", "not_requested");
        assertThrows(ContractViolationException.class,
                () -> HeirLineageConsumerPort.consume(StrictJson.canonical(unavailable)));
    }

    @Test
    void exactWrapperRejectsMissingUnknownDuplicateAndMalformedTokens() throws IOException {
        ObjectNode extra = firstInput();
        extra.put("qualified", true);
        assertThrows(ContractViolationException.class,
                () -> HeirLineageConsumerPort.consume(StrictJson.canonical(extra)));
        ObjectNode missing = firstInput();
        missing.remove("legality");
        assertThrows(ContractViolationException.class,
                () -> HeirLineageConsumerPort.consume(StrictJson.canonical(missing)));
        assertThrows(ContractViolationException.class, () -> HeirLineageConsumerPort.consume(
                "{\"choices\":[],\"choices\":[]}".getBytes(StandardCharsets.UTF_8)));
        assertThrows(ContractViolationException.class, () -> HeirLineageConsumerPort.consume(new byte[] {(byte) 0xc3, 0x28}));
        assertThrows(ContractViolationException.class, () -> HeirLineageConsumerPort.consume(new byte[65537]));
    }

    @Test
    void duplicateNativePreviewIdentityIsRejectedBeforeDecision() throws IOException {
        ObjectNode input = firstInput();
        ArrayNode previews = (ArrayNode) input.get("previews");
        previews.add(previews.get(2).deepCopy());
        assertThrows(ContractViolationException.class,
                () -> HeirLineageConsumerPort.consume(StrictJson.canonical(input)));
    }

    @Test
    void outputAndQueriesRemainImmutableAndContainNoBirthOrSubmissionClaim() throws IOException {
        var result = HeirLineageConsumerPort.evaluate(StrictJson.canonical(firstInput()));
        byte[] original = result.result();
        byte[] changed = result.result();
        changed[0] = 0;
        assertArrayEquals(original, result.result());
        assertThrows(UnsupportedOperationException.class, result.queries()::clear);
        JsonNode body = StrictJson.parse(original);
        assertFalse(body.has("birth"));
        assertFalse(body.has("material_result"));
        assertFalse(body.has("qualified"));
        assertTrue(body.path("choice").path("unpriced").toString().contains("future_child_identity_and_dynasty"));
    }

    private static ObjectNode firstInput() throws IOException {
        return (ObjectNode) golden().path("cases").get(0).path("input").deepCopy();
    }

    private static JsonNode golden() throws IOException {
        try (InputStream input = HeirLineageConsumerPortTest.class.getResourceAsStream("/heirlineage/producer-golden.json")) {
            if (input == null) { throw new IOException("committed actual producer golden required; no skip/fallback"); }
            return StrictJson.parse(input.readAllBytes());
        }
    }

    private static ArrayNode queryJson(List<HeirLineagePolicy.PreviewQuery> queries) {
        ArrayNode result = StrictJson.object().putArray("queries");
        for (var query : queries) {
            ObjectNode value = result.addObject();
            value.put("expected_revision", query.expectedRevision());
            value.put("subject_character_id", query.subject().value());
            value.put("candidate_character_id", query.candidate().value());
            value.put("request_matrilineal_option", query.requestMatrilinealOption());
        }
        return result;
    }
}
