package org.xar.ck3.control.planning.opportunity;

import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.StreamReadFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.ByteArrayInputStream;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.zip.GZIPInputStream;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.projection.ProjectionDomainRejection;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Native signed actor correction over the original producer corpus; no negative-ID Game observation is asserted. */
final class ObservedOpportunitySignedActorTest {
    private static Obj originalInput() throws Exception {
        byte[] compressed;
        try (var source = ObservedOpportunitySignedActorTest.class.getResourceAsStream("/opportunity/producer-golden-v1.json.gz")) {
            assertNotNull(source, "original producer corpus is mandatory");
            compressed = source.readNBytes(5582);
        }
        assertEquals(5581, compressed.length);
        assertEquals("21e48118933fb2bcff3b5714cc54ff4769f625cf530ad52ea08df029822c3d3d",
                HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(compressed)));
        byte[] raw;
        try (var gzip = new GZIPInputStream(new ByteArrayInputStream(compressed))) {
            raw = gzip.readNBytes(524289); assertTrue(raw.length <= 524288);
            assertEquals(-1, gzip.read(), "complete CRC-checked original corpus required");
        }
        var mapper = new ObjectMapper(JsonFactory.builder()
                .enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION).build());
        try (var parser = mapper.createParser(raw)) {
            JsonNode fixture = mapper.readTree(parser);
            assertNull(parser.nextToken());
            assertEquals(0, fixture.required("original_test_failures").intValue());
            assertEquals(0, fixture.required("original_test_errors").intValue());
            JsonNode input = fixture.required("cases").get(0).required("input");
            noDecimal(input); // This retained producer case contains integers only; no decimal token is rewritten here.
            return object(parse(mapper.writeValueAsBytes(input)), "original input");
        }
    }

    private static void noDecimal(JsonNode node) {
        assertFalse(node.isFloatingPointNumber(), "select an integer-only original producer fixture");
        node.forEach(ObservedOpportunitySignedActorTest::noDecimal);
    }

    private static Obj actor(Obj input, Value actor) {
        Obj snapshot = object(input.get("snapshot"), "snapshot");
        snapshot = snapshot.with("played_character_id", actor).with("played_character",
                object(snapshot.get("played_character"), "played").with("character_id", actor));
        Obj committed = object(input.get("commitments"), "commitments");
        committed = committed.with("frame", object(committed.get("frame"), "committed frame").with("played_character_id", actor));
        List<Value> proposals = new ArrayList<>();
        for (Value value : array(input.get("proposals"), "proposals")) {
            Obj proposal = object(value, "proposal");
            proposals.add(proposal.with("frame", object(proposal.get("frame"), "proposal frame").with("played_character_id", actor)));
        }
        return input.with("snapshot", snapshot).with("commitments", committed).with("proposals", new Arr(proposals));
    }

    @Test void signedActorSurvivesActualSelectAndTheNormalProposalPath() throws Exception {
        Obj original = originalInput();
        Value originalChoice = object(parse(ObservedOpportunitySelector.select(encode(original))), "original result").get("selected_candidate_id");
        for (int id : new int[] {Integer.MIN_VALUE, -2, 0, Integer.MAX_VALUE}) {
            var identity = new IntegerValue(BigInteger.valueOf(id));
            Obj request = actor(original, identity);
            Obj snapshot = object(request.get("snapshot"), "snapshot");
            Obj frame = object(parse(ObservedOpportunitySelector.observedFrame(encode(snapshot))), "observed frame");
            assertEquals(identity, frame.get("played_character_id"));
            for (Value proposal : array(request.get("proposals"), "proposals")) {
                Obj normalized = object(parse(ObservedOpportunitySelector.normalizeProposal(
                        encode(new Obj(Map.of("frame", frame, "proposal", proposal))))), "normalized");
                assertEquals(identity, object(normalized.get("frame"), "normalized frame").get("played_character_id"));
                assertEquals(normalized, parse(encode(normalized)));
            }
            Obj selected = object(parse(ObservedOpportunitySelector.select(encode(request))), "selected");
            assertEquals(identity, object(selected.get("frame"), "selected frame").get("played_character_id"));
            assertEquals(originalChoice, selected.get("selected_candidate_id"));
            assertEquals(new Bool(false), selected.get("formal_action_ready"));
            assertEquals(Nil.INSTANCE, selected.get("selected_step"));
            assertTrue(new String(encode(selected), StandardCharsets.UTF_8).contains("\"played_character_id\":" + id));
        }
    }

    @Test void actorRejectsSentinelOverflowAndNonIntegerTokens() throws Exception {
        Obj original = originalInput();
        for (Value bad : List.of(new IntegerValue(BigInteger.valueOf(-1)),
                new IntegerValue(BigInteger.valueOf(Integer.MIN_VALUE).subtract(BigInteger.ONE)),
                new IntegerValue(BigInteger.valueOf(Integer.MAX_VALUE).add(BigInteger.ONE)),
                new Bool(true), new DecimalValue("-2.0"), new Text("-2"), Nil.INSTANCE)) {
            Obj rejected = actor(original, bad);
            assertThrows(ProjectionDomainRejection.class, () -> ObservedOpportunitySelector.select(encode(rejected)));
        }
    }

    @Test void signedActorDoesNotRelaxCharacterBoundsOrRevisionGuards() throws Exception {
        Obj request = actor(originalInput(), new IntegerValue(BigInteger.valueOf(-2)));
        List<Value> proposals = new ArrayList<>(array(request.get("proposals"), "proposals"));
        Obj proposal = object(proposals.getFirst(), "proposal");
        for (String key : List.of("character_ids", "ally_character_ids")) {
            for (long id : new long[] {-1, 2147483648L}) {
                proposals.set(0, proposal.with(key, new Arr(List.of(new IntegerValue(BigInteger.valueOf(id))))));
                Obj rejected = request.with("proposals", new Arr(proposals));
                assertThrows(ProjectionDomainRejection.class, () -> ObservedOpportunitySelector.select(encode(rejected)));
            }
        }
        Obj snapshot = object(request.get("snapshot"), "snapshot").with("native_revision", new IntegerValue(BigInteger.ZERO));
        assertThrows(ProjectionDomainRejection.class,
                () -> ObservedOpportunitySelector.select(encode(request.with("snapshot", snapshot))));
    }


    @Test void signedResourceCharacterClaimsSurviveNormalizerSelectorAndConflict() throws Exception {
        Obj original = originalInput();
        Obj first = object(array(original.get("proposals"), "proposals").getFirst(), "proposal");
        assertFalse(new Text("marriage").equals(first.get("domain")));
        assertFalse(new Text("lifestyle").equals(first.get("domain")));
        for (String key : List.of("ally_character_ids", "character_ids")) {
            for (int id : new int[] {Integer.MIN_VALUE, -2, 0, Integer.MAX_VALUE}) {
                var identity = new IntegerValue(BigInteger.valueOf(id));
                Obj proposal = first.with(key, new Arr(List.of(identity)));
                List<Value> proposals = new ArrayList<>(array(original.get("proposals"), "proposals")); proposals.set(0, proposal);
                Obj request = original.with("proposals", new Arr(proposals));
                Obj normalized = object(parse(ObservedOpportunitySelector.normalizeProposal(
                        encode(new Obj(Map.of("frame", proposal.get("frame"), "proposal", proposal))))), "normalized");
                assertEquals(new Arr(List.of(identity)), normalized.get(key));
                Obj selected = object(parse(ObservedOpportunitySelector.select(encode(request))), "selected");
                Obj evaluated = object(array(selected.get("evaluated"), "evaluated").getFirst(), "evaluated proposal");
                assertEquals(new Arr(List.of(identity)), evaluated.get(key));
                assertEquals(new Bool(false), selected.get("formal_action_ready"));
                assertEquals(Nil.INSTANCE, selected.get("selected_step"));
                assertEquals(selected, parse(encode(selected)));
                Obj committed = object(request.get("commitments"), "commitments").with(key, new Arr(List.of(identity)));
                Obj blocked = object(parse(ObservedOpportunitySelector.select(encode(request.with("commitments", committed)))), "blocked");
                assertEquals(new Text("existing_commitment_conflict"),
                        object(array(blocked.get("evaluated"), "evaluated").getFirst(), "blocked proposal").get("reason"));
            }
        }
    }

    @Test void resourceCharacterClaimsRejectSentinelAliasesWrongTokensDuplicatesAndMissing() throws Exception {
        Obj original = originalInput();
        Obj first = object(array(original.get("proposals"), "proposals").getFirst(), "proposal");
        List<Value> bad = List.of(new IntegerValue(BigInteger.valueOf(-1)),
                new IntegerValue(BigInteger.valueOf(Integer.MIN_VALUE).subtract(BigInteger.ONE)),
                new IntegerValue(BigInteger.valueOf(Integer.MAX_VALUE).add(BigInteger.ONE)),
                new IntegerValue(BigInteger.valueOf(4294967294L)), new Bool(true), new Bool(false),
                new DecimalValue("1.0"), new Text("0"), Nil.INSTANCE, new Arr(List.of()), new Obj(Map.of()));
        for (String key : List.of("ally_character_ids", "character_ids")) {
            for (Value value : bad) {
                Obj proposal = first.with(key, new Arr(List.of(value)));
                List<Value> proposals = new ArrayList<>(array(original.get("proposals"), "proposals")); proposals.set(0, proposal);
                Obj request = original.with("proposals", new Arr(proposals));
                assertThrows(ProjectionDomainRejection.class, () -> ObservedOpportunitySelector.select(encode(request)), key + value);
            }
            Obj duplicate = first.with(key, new Arr(List.of(new IntegerValue(BigInteger.valueOf(-2)),
                    new IntegerValue(BigInteger.valueOf(-2)))));
            List<Value> rows = new ArrayList<>(array(original.get("proposals"), "proposals")); rows.set(0, duplicate);
            Obj repeated = original.with("proposals", new Arr(rows));
            assertThrows(ProjectionDomainRejection.class, () -> ObservedOpportunitySelector.select(encode(repeated)));
            var absent = new LinkedHashMap<>(first.members()); absent.remove(key);
            rows.set(0, new Obj(absent)); Obj missing = original.with("proposals", new Arr(rows));
            assertThrows(ProjectionDomainRejection.class, () -> ObservedOpportunitySelector.select(encode(missing)));
        }
    }

    @Test void existingNestedActorFallbackKeepsTheOriginalSignedValue() throws Exception {
        Obj request = actor(originalInput(), new IntegerValue(BigInteger.valueOf(Integer.MIN_VALUE)));
        Obj snapshot = object(request.get("snapshot"), "snapshot");
        var absent = new LinkedHashMap<>(snapshot.members()); absent.remove("played_character_id");
        for (Obj material : List.of(new Obj(absent), snapshot.with("played_character_id", Nil.INSTANCE))) {
            Obj frame = object(parse(ObservedOpportunitySelector.observedFrame(encode(material))), "frame");
            assertEquals(new IntegerValue(BigInteger.valueOf(Integer.MIN_VALUE)), frame.get("played_character_id"));
        }
        var missing = new LinkedHashMap<>(absent); missing.remove("played_character");
        assertThrows(ProjectionDomainRejection.class, () -> ObservedOpportunitySelector.observedFrame(encode(new Obj(missing))));
    }
}


