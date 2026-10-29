package org.xar.ck3.control.wave3.planning.pendingfamilyclaims;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import static org.xar.ck3.control.wave3.planning.pendingfamilyclaims.PendingFamilyClaims.*;

import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.StreamReadFeature;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.cfg.JsonNodeFeature;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.zip.GZIPInputStream;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.wave2.planning.jointintake.FormalProposalIntake;

final class PendingFamilyClaimsTest {
    private record Corpus(Obj metadata, List<Obj> cases, List<Obj> consumers) {
        private Corpus { cases = List.copyOf(cases); consumers = List.copyOf(consumers); }
    }
    private static Corpus corpus() throws IOException {
        try (var resource = PendingFamilyClaimsTest.class.getResourceAsStream("/pendingfamilyclaims/producer-golden-v1.json.gz")) {
            assertNotNull(resource, "actual producer corpus missing: fail, never skip");
            byte[] compressed = resource.readNBytes(49153); assertTrue(compressed.length <= 49152);
            byte[] raw;
            try (var gzip = new GZIPInputStream(new ByteArrayInputStream(compressed))) {
                raw = gzip.readNBytes(524289); assertTrue(raw.length <= 524288);
                assertEquals(-1, gzip.read(), "complete validated gzip trailer required");
            }
            ObjectMapper mapper = new ObjectMapper(JsonFactory.builder().enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION).build())
                    .enable(DeserializationFeature.USE_BIG_INTEGER_FOR_INTS).enable(DeserializationFeature.USE_BIG_DECIMAL_FOR_FLOATS)
                    .configure(JsonNodeFeature.STRIP_TRAILING_BIGDECIMAL_ZEROES, false);
            ObjectNode document;
            try (var parser = mapper.createParser(raw)) {
                JsonNode value = mapper.readTree(parser); assertTrue(value instanceof ObjectNode); document = (ObjectNode) value; assertNull(parser.nextToken());
            }
            JsonNode cases = document.remove("cases"), consumers = document.remove("consumers");
            return new Corpus(object(parse(mapper.writeValueAsBytes(document)), "metadata"), vectors(cases, mapper), vectors(consumers, mapper));
        }
    }
    private static List<Obj> vectors(JsonNode values, ObjectMapper mapper) throws IOException {
        assertNotNull(values); assertTrue(values.isArray()); List<Obj> result = new ArrayList<>();
        for (JsonNode value : values) result.add(object(parse(mapper.writeValueAsBytes(value)), "vector"));
        return List.copyOf(result);
    }
    private static Obj request(String name) throws IOException {
        return corpus().cases().stream().filter(row -> new Text(name).equals(row.get("name"))).map(row -> object(row.get("input"), "input")).findFirst().orElseThrow();
    }
    private static void rejects(Obj request) { assertThrows(IllegalArgumentException.class, () -> PendingFamilyClaimsCodec.project(encode(request))); }
    private static BigInteger id(long value) { return BigInteger.valueOf(value); }

    @Test void unchangedOriginalProducersMatchEveryCompleteClaim() throws IOException {
        Corpus corpus = corpus(); assertEquals(37, corpus.cases().size());
        assertEquals(new IntegerValue(id(4)), corpus.metadata().get("original_tests_run"));
        assertEquals(new IntegerValue(BigInteger.ZERO), corpus.metadata().get("original_test_errors"));
        assertEquals(new IntegerValue(BigInteger.ZERO), corpus.metadata().get("original_test_failures"));
        int accepted = 0, rejected = 0;
        for (Obj row : corpus.cases()) {
            Obj input = object(row.get("input"), "input"); byte[] raw = encode(input), original = raw.clone();
            if (new Bool(true).equals(row.get("accepted"))) {
                assertEquals(row.get("expected"), parse(PendingFamilyClaimsCodec.project(raw)), text(row.get("name"), "name")); accepted++;
            } else { rejects(input); rejected++; }
            assertArrayEquals(original, raw); assertEquals(input, parse(encode(input)), "JSON type-domain round trip");
        }
        assertEquals(16, accepted); assertEquals(21, rejected);
    }

    @Test void actualQueryCommitmentsReachTheExistingCollectorAndSelector() throws IOException {
        Corpus corpus = corpus(); assertEquals(2, corpus.consumers().size());
        for (Obj row : corpus.consumers()) {
            Obj claims = object(parse(PendingFamilyClaimsCodec.project(encode(row.get("claims_request")))), "claims");
            assertEquals(row.get("expected_claims"), claims);
            Obj intake = object(row.get("intake_request"), "intake request"), sources = object(intake.get("sources"), "sources"), commitments = object(sources.get("existing_commitments"), "commitments");
            for (Map.Entry<String, Value> field : claims.members().entrySet()) assertEquals(field.getValue(), commitments.get(field.getKey()), "real query claim union");
            Obj actual = object(parse(FormalProposalIntake.collectHistoricalV1(encode(intake))), "historical intake projection");
            assertThrows(IllegalArgumentException.class, () -> FormalProposalIntake.collect(encode(intake)), "production v2 must reject a v1 request");
            Obj current = intake.with("schema", new Text(FormalProposalIntake.REQUEST_SCHEMA));
            Obj migrated = object(parse(FormalProposalIntake.collect(encode(current))), "current typed intake projection");
            assertEquals(actual, migrated, "real pending query commitments must reach both explicit historical and current selector consumers");
            assertEquals(current, parse(encode(current)), "current request wire round trip");
            assertEquals(row.get("expected_analysis"), actual.get("analysis"), text(row.get("name"), "consumer"));
            assertEquals(new Bool(false), actual.get("resource_reservation_performed"));
            assertEquals(new Bool(true), row.get("ledger_unchanged")); assertEquals(new Bool(false), row.get("submission_enabled"));
        }
    }

    @Test void strictIntegerAndBooleanTokensRemainDifferentFromNumericEquality() throws IOException {
        Obj input = request("family-historical-conservative"), pending = object(input.get("pending"), "pending");
        for (Value bad : List.of(new Bool(true), new DecimalValue("38822.0"), new Text("38822"), Nil.INSTANCE)) {
            Obj changed = input.with("pending", pending.with("heir_character_id", bad));
            byte[] raw = encode(changed);
            if (bad instanceof DecimalValue) assertTrue(new String(raw, StandardCharsets.UTF_8).contains("\"heir_character_id\":38822.0"));
            assertThrows(IllegalArgumentException.class, () -> PendingFamilyClaimsCodec.project(raw));
        }
        for (Value bad : List.of(new IntegerValue(BigInteger.ONE), Nil.INSTANCE, new Text("false")))
            rejects(input.with("pending", pending.with("preproposal_realm_alliance_attempt_if_accepted", bad)));
        Obj observed = object(input.get("frame"), "frame");
        for (String field : List.of("played_character_id", "native_revision", "date_raw", "revision")) rejects(input.with("frame", observed.with(field, new Bool(true))));
    }

    @Test void missingHistoricalFlagAndExplicitNullKeepDifferentMeanings() throws IOException {
        Obj input = request("family-historical-conservative");
        Optional<FamilyPending> historical = PendingFamilyClaimsCodec.decodeFamilyPending(encode(input.get("pending")));
        assertEquals(AllianceIntent.HISTORICAL_CONSERVATIVE, historical.orElseThrow().allianceIntent());
        rejects(input.with("pending", object(input.get("pending"), "pending").with("preproposal_realm_alliance_attempt_if_accepted", Nil.INSTANCE)));
        assertEquals(Optional.empty(), PendingFamilyClaimsCodec.decodeFamilyPending(encode(Nil.INSTANCE)));
        assertEquals(Optional.empty(), PendingFamilyClaimsCodec.decodeChildPending(encode(Nil.INSTANCE)));
        Map<String, Value> missing = new java.util.LinkedHashMap<>(input.members()); missing.remove("pending"); rejects(new Obj(missing));
        Obj extension = input.with("pending", object(input.get("pending"), "pending").with("opaque_rate", new DecimalValue("1.5")));
        assertArrayEquals(PendingFamilyClaimsCodec.project(encode(input)), PendingFamilyClaimsCodec.project(encode(extension)));
    }

    @Test void typedClaimsKeepActorAvailableAndScopeMismatchDoesNotClearUnknown() {
        ActorEpisode scope = new ActorEpisode(id(10), "episode");
        ChildPending child = new ChildPending(scope, id(20), id(30), id(10), List.of(new AlliancePair(id(10), id(40), true), new AlliancePair(id(40), id(10), true), new AlliancePair(id(10), id(10), true), new AlliancePair(id(50), id(60), true)));
        Claims claimed = childDefault(scope, Optional.of(child));
        assertEquals(List.of(id(20), id(30)), claimed.characterIds()); assertEquals(List.of(id(40)), claimed.allyCharacterIds());
        assertEquals(List.of("player-child-default-marriage:20"), claimed.commitmentKeys());
        assertThrows(IllegalArgumentException.class, () -> childDefault(new ActorEpisode(id(10), "other"), Optional.of(child)));
        assertThrows(IllegalArgumentException.class, () -> family(scope, Optional.of(new FamilyPending(scope, id(20), id(20), id(40), AllianceIntent.EXPLICIT_ATTEMPT))));
        assertThrows(IllegalArgumentException.class, () -> new Claims(List.of(id(40), id(40)), List.of(), List.of()));
        assertEquals(List.of(id(20), id(30)), claimed.characterIds());
    }

    @Test void familyRecipientOverlapAndArbitraryPrecisionRemainExact() throws IOException {
        Obj request = request("family-recipient-is-candidate");
        FamilyPending family = PendingFamilyClaimsCodec.decodeFamilyPending(encode(request.get("pending"))).orElseThrow();
        Claims claims = PendingFamilyClaims.family(family.scope(), Optional.of(family)); assertEquals(2, claims.characterIds().size());
        Obj large = object(parse(PendingFamilyClaimsCodec.project(encode(request("family-exact-large-identity")))), "large claims");
        assertEquals(new IntegerValue(BigInteger.ONE.shiftLeft(80)), array(large.get("character_ids"), "characters").getFirst());
        assertEquals(large, parse(encode(large)));
    }

    @Test void exactEnvelopeAndMalformedTransportRejectAtTheActualBoundary() throws IOException {
        Obj input = request("family-historical-conservative"); rejects(input.with("extra", new Bool(true)));
        rejects(input.with("schema", new Text("other"))); rejects(input.with("operation", new Text("unknown")));
        rejects(input.with("frame", object(input.get("frame"), "frame").with("extra", Nil.INSTANCE)));
        String raw = new String(encode(input), StandardCharsets.UTF_8);
        for (byte[] malformed : List.of((raw + "{}").getBytes(StandardCharsets.UTF_8), "{\"schema\":1,\"schema\":2}".getBytes(StandardCharsets.UTF_8), new byte[] {(byte) 0xc3, 0x28}, new byte[131073]))
            assertThrows(IllegalArgumentException.class, () -> PendingFamilyClaimsCodec.project(malformed));
    }
}
