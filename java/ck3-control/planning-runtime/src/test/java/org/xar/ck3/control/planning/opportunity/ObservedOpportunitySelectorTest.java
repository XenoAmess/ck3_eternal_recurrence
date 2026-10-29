package org.xar.ck3.control.planning.opportunity;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

import java.io.IOException;
import java.util.zip.GZIPInputStream;
import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.StreamReadFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.cfg.JsonNodeFeature;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;

final class ObservedOpportunitySelectorTest {
    private static Obj golden() throws IOException {
        try (var stream = ObservedOpportunitySelectorTest.class.getResourceAsStream("/opportunity/producer-golden-v1.json.gz")) {
            assertNotNull(stream, "actual Python producer golden must be committed; missing corpus is RED");
            byte[] compressed = stream.readNBytes(131073); assertTrue(compressed.length <= 131072, "compressed corpus bound");
            byte[] raw;
            try (var gzip = new GZIPInputStream(new java.io.ByteArrayInputStream(compressed))) {
                raw = gzip.readNBytes(524289); assertTrue(raw.length <= 524288, "decompressed corpus bound");
                assertEquals(-1, gzip.read(), "gzip must reach validated trailer, never truncated");
            }
            ObjectMapper mapper = new ObjectMapper(JsonFactory.builder().enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION).build())
                    .enable(DeserializationFeature.USE_BIG_DECIMAL_FOR_FLOATS).configure(JsonNodeFeature.STRIP_TRAILING_BIGDECIMAL_ZEROES, false);
            ObjectNode fixture;
            try (var parser = mapper.createParser(raw)) {
                JsonNode root = mapper.readTree(parser); assertTrue(root instanceof ObjectNode); fixture = (ObjectNode) root;
                assertNull(parser.nextToken(), "one corpus document");
            }
            JsonNode vectors = fixture.remove("cases"); assertNotNull(vectors); assertTrue(vectors.isArray());
            List<Value> decoded = new ArrayList<>();
            for (JsonNode vector : vectors) decoded.add(parse(mapper.writeValueAsBytes(vector)));
            return object(parse(mapper.writeValueAsBytes(fixture)), "golden metadata").with("cases", new Arr(decoded));
        }
    }
    private static List<Value> cases() throws IOException { return array(golden().get("cases"), "cases"); }
    private static Obj firstInput() throws IOException { return object(object(cases().getFirst(), "case").get("input"), "input"); }
    private static Obj proposal(Obj input, int index) { return object(array(input.get("proposals"), "proposals").get(index), "proposal"); }
    private static Obj replaceFirst(Obj input, Obj proposal) {
        List<Value> rows = new ArrayList<>(array(input.get("proposals"), "proposals")); rows.set(0, proposal);
        return input.with("proposals", new Arr(rows));
    }
    private static void rejects(Obj input) { assertThrows(IllegalArgumentException.class, () -> ObservedOpportunitySelector.select(encode(input))); }

    @Test void actualProducerCorpusMatchesEveryOutputAndRoundTrips() throws IOException {
        Obj fixture = golden(); assertEquals(new IntegerValue(BigInteger.valueOf(0)), fixture.get("original_test_failures"));
        assertEquals(new IntegerValue(BigInteger.valueOf(0)), fixture.get("original_test_errors"));
        assertTrue(integer(fixture.get("original_tests_run"), "tests").signum() > 0);
        assertTrue(cases().size() >= 24, "full producer corpus required");
        for (Value raw : cases()) {
            Obj vector = object(raw, "case"); byte[] input = encode(vector.get("input"));
            assertEquals(vector.get("input"), parse(input), text(vector.get("name"), "name") + " input JSON round trip");
            Value actual = parse(ObservedOpportunitySelector.select(input));
            assertEquals(vector.get("expected"), actual, text(vector.get("name"), "name"));
            Obj result = object(actual, "result"); assertEquals(new Bool(false), result.get("formal_action_ready"));
            assertEquals(Nil.INSTANCE, result.get("selected_step"));
            Obj request = object(vector.get("input"), "input");
            List<Value> proposals = array(request.get("proposals"), "proposals");
            List<Value> evaluated = array(result.get("evaluated"), "evaluated");
            for (int index = 0; index < proposals.size(); index++) {
                Obj normalized = object(parse(ObservedOpportunitySelector.normalizeProposal(encode(new Obj(Map.of(
                        "frame", result.get("frame"), "proposal", proposals.get(index)))))), "normalized");
                var expected = new java.util.LinkedHashMap<>(object(evaluated.get(index), "evaluation").members());
                expected.remove("reason"); assertEquals(new Obj(expected), normalized, "shortlist shared normalizer");
            }
        }
    }
    @Test void integerIdentityRejectsBooleanFloatStringMissingAndNull() throws IOException {
        Obj input = firstInput(); Obj snapshot = object(input.get("snapshot"), "snapshot");
        for (Value bad : List.of(new Bool(true), new DecimalValue("29829.0"), new Text("29829"), Nil.INSTANCE))
            rejects(input.with("snapshot", snapshot.with("native_revision", bad)));
        var fields = new java.util.LinkedHashMap<>(snapshot.members()); fields.remove("native_revision");
        rejects(input.with("snapshot", new Obj(fields)));
        rejects(input.with("max_active_wars", new Bool(false)));
        rejects(input.with("gold_reserve_raw", new DecimalValue("0.0")));
        rejects(input.with("snapshot", snapshot.with("played_character_gold", object(snapshot.get("played_character_gold"), "gold")
                .with("scale", new DecimalValue("100000.0")))));
    }
    @Test void sameFrameBindsEveryIdentityAndCannotHideExtras() throws IOException {
        Obj input = firstInput(); Obj proposal = proposal(input, 0); Obj frame = object(proposal.get("frame"), "frame");
        for (String key : List.of("played_character_id", "native_revision", "date_raw", "revision"))
            rejects(replaceFirst(input, proposal.with("frame", frame.with(key, new IntegerValue(integer(frame.get(key), key).add(BigInteger.ONE))))));
        for (String key : List.of("snapshot_id", "episode_run_id"))
            rejects(replaceFirst(input, proposal.with("frame", frame.with(key, new Text("changed")))));
        rejects(replaceFirst(input, proposal.with("frame", frame.with("extension", Nil.INSTANCE))));
        Obj commitments = object(input.get("commitments"), "commitments");
        rejects(input.with("commitments", commitments.with("frame", frame.with("revision", new IntegerValue(BigInteger.ONE)))));
    }
    @Test void claimsRejectDuplicateAndWrongTypesWhilePublicArmyZeroRemainsValid() throws IOException {
        Obj input = firstInput(); Obj proposal = proposal(input, 0);
        for (Value claims : List.of(new Arr(List.of(new IntegerValue(BigInteger.valueOf(-1)))),
                new Arr(List.of(new Bool(false))), new Arr(List.of(new IntegerValue(BigInteger.ZERO), new IntegerValue(BigInteger.ZERO))), Nil.INSTANCE))
            rejects(replaceFirst(input, proposal.with("army_ids", claims)));
        rejects(replaceFirst(input, proposal.with("character_ids", new Arr(List.of(new IntegerValue(BigInteger.valueOf(-1)))))));
        rejects(replaceFirst(input, proposal.with("commitment_keys", new Arr(List.of(new Text("same"), new Text("same"))))));
        for (Value vector : cases()) {
            Obj row = object(vector, "case");
            if (new Text("zero-public-army").equals(row.get("name")))
                assertEquals(row.get("expected"), parse(ObservedOpportunitySelector.select(encode(row.get("input")))));
        }
    }
    @Test void domainAndResourceGuardsRejectIncompleteWarMarriageAndLifestyle() throws IOException {
        Obj input = firstInput(); Obj proposal = proposal(input, 0);
        rejects(replaceFirst(input, proposal.with("domain_policy_ready", new Bool(false))));
        rejects(replaceFirst(input, proposal.with("domain", new Text("unrecognized"))));
        rejects(replaceFirst(input, proposal.with("war_slot_claim", new IntegerValue(BigInteger.TWO))));
        rejects(replaceFirst(input, proposal.with("gold_cost_raw", new IntegerValue(BigInteger.valueOf(-1)))));
        rejects(replaceFirst(input, proposal.with("domain", new Text("war"))));
        rejects(replaceFirst(input, proposal.with("domain", new Text("marriage"))));
        rejects(replaceFirst(input, proposal.with("domain", new Text("lifestyle"))));
        rejects(replaceFirst(input, proposal.with("projected_supply_margin_raw", new IntegerValue(BigInteger.ZERO))));
        rejects(replaceFirst(input, proposal.with("war_operation", new Text("entry"))));
    }
    @Test void requestAndParserRefuseDuplicateFieldsTrailingDocumentsAndInvalidUtf8() throws IOException {
        Obj input = firstInput(); rejects(input.with("unknown_request_argument", new Bool(true)));
        byte[] encoded = encode(input); String valid = new String(encoded, StandardCharsets.UTF_8);
        assertThrows(IllegalArgumentException.class, () -> ObservedOpportunitySelector.select((valid + " {}").getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class, () -> ObservedOpportunitySelector.select("{\"snapshot\":{},\"snapshot\":{}}".getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class, () -> ObservedOpportunitySelector.select(new byte[] {(byte) 0xc3, 0x28}));
        assertThrows(IllegalArgumentException.class, () -> ObservedOpportunitySelector.select(new byte[131073]));
        rejects(input.with("proposals", new Arr(List.of(proposal(input, 0), proposal(input, 0)))));
    }
    @Test void optionalEvidencePreservesMissingNullCollectionsAndExactDecimals() {
        Obj value = new Obj(Map.of("absent_marker", new Text("missing is not a member"), "null", Nil.INSTANCE,
                "empty", new Arr(List.of()), "decimal", new DecimalValue("12345678901234567890.125"),
                "integer", new IntegerValue(BigInteger.ONE.shiftLeft(100))));
        assertEquals(value, parse(encode(value)));
        assertEquals(new DecimalValue("1.0"), parse(encode(new DecimalValue("1.0"))));
        assertNull(value.get("missing")); assertNotEquals(value.get("empty"), value.get("null"));
    }
}

