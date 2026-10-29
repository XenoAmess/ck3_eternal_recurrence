package org.xar.ck3.control.wave3.planning.m5peacetimeassembly;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HexFormat;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.zip.GZIPInputStream;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave2.finance.rawcash.SdkProjectionJson;

final class PeacetimeAssemblyTest {
    private record SourcePin(long bytes, String sha256) { }
    private static final Map<String, SourcePin> ORIGINAL_SOURCES = Map.ofEntries(
            Map.entry("ck3_autonomous_player/src/xar_autoplayer/m5_peacetime_proposal_sources_v1.py", new SourcePin(23932, "d724320f112bbb3e91779990b5ebfbaf55cbb2a2bd392b74819497938d074ac8")),
            Map.entry("ck3_autonomous_player/src/xar_autoplayer/m5_formal_proposal_collector.py", new SourcePin(36154, "6488c6f3ab6d930e37d8f9730285214ebbc700a8a6ec968124826b81b1c8172e")),
            Map.entry("ck3_autonomous_player/src/xar_autoplayer/m5_observed_opportunity_selector.py", new SourcePin(41486, "30d833e42dbbc50cbff66867256df44bc3c0f38b2529cb11f247f80511aadf5c")),
            Map.entry("ck3_autonomous_player/src/xar_autoplayer/m5_joint_dispatch.py", new SourcePin(13766, "e2c79f323034c3916cf87277b8fe24a64f71e659af5777821147c1991cd7e69d")),
            Map.entry("ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py", new SourcePin(1658411, "40a625c6448f753ffa920d6a7780e5687dde7bca28e5b6ab07237ad588efd8cb")),
            Map.entry("ck3_autonomous_player/src/xar_autoplayer/construction_formal_consumer.py", new SourcePin(40508, "90ff70251640abd243bea7a0194f057ab80b719899569e4ca3feaf53c29b9e3e")),
            Map.entry("ck3_autonomous_player/src/xar_autoplayer/faction_gift_pending_v1.py", new SourcePin(13656, "2152c3e2c7f48bad6864c06d43a6e32e731736a72e65df5b134250a156450293")),
            Map.entry("ck3_autonomous_player/src/xar_autoplayer/family_marriage_formal_consumer.py", new SourcePin(61603, "c6d55a12b4450909641dbffe5b12e900878f29cde406aadd4a6d185bd78039b0")),
            Map.entry("ck3_autonomous_player/src/xar_autoplayer/player_child_default_formal_consumer.py", new SourcePin(30642, "ffcab3e798ec3eae3a73d4d09a7c921de010bafcb6380e144370f88c50e17dad")),
            Map.entry("ck3_autonomous_player/tests/unit/test_m5_peacetime_proposal_sources_v1.py", new SourcePin(70537, "f6c49d48bf9fee0f47a85aba2fc787e4cd9196332baac31814bc59e8fc953e6b")),
            Map.entry("ck3_autonomous_player/tests/unit/test_m5_child_default_pending_commitments.py", new SourcePin(5192, "9930e41ebf0a0d09b1950752116e3abffcde3d6fac63bf9176470cdf5360ab38")));
    private static JsonNode golden() throws IOException {
        try (InputStream stream = PeacetimeAssemblyTest.class.getResourceAsStream("/m5peacetimeassembly/producer-golden-v1.json.gz")) {
            if (stream == null) throw new IOException("original full query/Driver/collector golden required; no skip or fallback");
            try (GZIPInputStream decompressed = new GZIPInputStream(stream)) {
                byte[] raw = decompressed.readNBytes(1_048_577);
                if (raw.length > 1_048_576) throw new IOException("bounded original golden exceeds 1MiB decoded");
                return StrictJson.parse(raw, 1_048_576);
            }
        }
    }
    private static byte[] bytes(JsonNode node) {
        return SdkProjectionJson.encode(node, 131_072);
    }
    private static String hash(JsonNode node) {
        try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(StrictJson.canonical(node, 131_072))); }
        catch (NoSuchAlgorithmException error) { throw new IllegalStateException(error); }
    }
    private static ObjectNode validInput() throws IOException { return M5CompactWireFixtures.currentAssembly(golden().get("cases").get(0).get("input")); }

    @Test void completeOriginalQueryThroughNativeDriverAndActualCollectorMatches() throws IOException {
        JsonNode captured = golden();
        assertEquals("xar.java.peacetime-assembly-producer-golden.v1", captured.get("schema").textValue());
        assertTrue(captured.get("original_tests_run").intValue() > 20); assertEquals(0, captured.get("original_failures").intValue());
        assertEquals(0, captured.get("original_errors").intValue()); assertEquals(0, captured.get("game_rpc_count").intValue());
        assertEquals(0, captured.get("original_skipped").intValue()); assertEquals(0, captured.get("original_expected_failures").intValue());
        assertEquals(0, captured.get("original_unexpected_successes").intValue()); assertEquals("MATCH", captured.get("source_postcheck").textValue());
        assertEquals(0, captured.get("canonical_ledger_write_count").intValue()); assertFalse(captured.get("production_cutover").booleanValue());
        Set<String> sourcePaths = new HashSet<>();
        for (JsonNode source : captured.get("sources")) {
            assertEquals(Set.of("path", "bytes", "sha256"), source.properties().stream().map(Map.Entry::getKey).collect(java.util.stream.Collectors.toSet()));
            String path = source.get("path").textValue(); assertTrue(sourcePaths.add(path), "duplicate original source pin");
            SourcePin pin = ORIGINAL_SOURCES.get(path); assertNotNull(pin, path);
            assertEquals(pin.bytes(), source.get("bytes").longValue(), path);
            assertEquals(pin.sha256(), source.get("sha256").textValue(), path);
        }
        assertEquals(ORIGINAL_SOURCES.keySet(), sourcePaths);
        assertEquals(13, captured.get("cases").size());
        for (JsonNode sample : captured.get("cases")) {
            byte[] historicalInput = bytes(sample.get("input")); assertTrue(sample.get("actual_native_driver_entry_executed").booleanValue());
            if (!sample.get("accepted").booleanValue()) {
                IllegalArgumentException rejected = assertThrows(IllegalArgumentException.class, () -> PeacetimeAssembly.compose(PeacetimeAssemblyCodec.decodeHistoricalV1(historicalInput)), sample.get("name").textValue());
                assertEquals(sample.get("failure").get("message").textValue(), rejected.getMessage(), sample.get("name").textValue());
                assertThrows(IllegalArgumentException.class, () -> PeacetimeAssemblyCodec.decode(historicalInput)); continue;
            }
            byte[] input = bytes(M5CompactWireFixtures.currentAssembly(sample.get("input")));
            assertThrows(IllegalArgumentException.class, () -> PeacetimeAssemblyCodec.decode(historicalInput));
            assertThrows(IllegalArgumentException.class, () -> PeacetimeAssemblyCodec.decodeHistoricalV1(input));
            assertTrue(sample.get("capture_failure_closure_reads").isEmpty());
            for (String domain : List.of("construction", "faction", "family", "child_default"))
                assertEquals(2, sample.get("producer_ledger_read_counts").get(domain).intValue());
            if (sample.get("name").textValue().equals("later-frame-releases-prior-building")) {
                assertTrue(sample.get("process_fixture_read_count").intValue() >= 2);
                assertEquals("observed", sample.get("input").get("construction_process").get("kind").textValue());
            }
            JsonNode source = StrictJson.parse(PeacetimeAssembly.assemble(input), 131_072);
            assertEquals(sample.get("source_sha256").textValue(), hash(M5CompactWireFixtures.historicalSourceView(source)), sample.get("name").textValue());
            OpportunityJson.Obj typedSource = OpportunityJson.object(OpportunityJson.parse(PeacetimeAssembly.assemble(input)), "source");
            OpportunityJson.Obj domains = OpportunityJson.object(typedSource.get("domains"), "domains");
            assertEquals(sample.get("domain_order"), new ObjectMapper().valueToTree(List.copyOf(domains.members().keySet())));
            assertTrue(sample.get("actual_collector_executed").booleanValue());
            JsonNode intake = StrictJson.parse(PeacetimeAssembly.assembleAndCollect(input), 131_072), expected = sample.get("collector");
            assertEquals(expected.get("collected_domains"), intake.get("collected_domains"));
            assertEquals(expected.get("collected_candidate_ids"), intake.get("collected_candidate_ids"));
            assertEquals(expected.get("analysis_sha256").textValue(), hash(intake.get("analysis")), sample.get("name").textValue());
            assertFalse(intake.get("formal_action_ready").booleanValue()); assertFalse(intake.get("resource_reservation_performed").booleanValue());
        }
    }

    @Test void ledgerReadbacksUseActualStructureAndMissingNullAreDistinct() throws IOException {
        for (String domain : List.of("construction", "faction", "family", "child_default")) {
            ObjectNode input = validInput(); ((ObjectNode) input.get("ledgers_after").get(domain)).put("changed_field", 1);
            assertThrows(IllegalArgumentException.class, () -> PeacetimeAssembly.assemble(bytes(input)), domain);
        }
        ObjectNode input = validInput(); ((ObjectNode) input.get("ledgers_after").get("family")).remove("pending");
        assertThrows(IllegalArgumentException.class, () -> PeacetimeAssembly.assemble(bytes(input)));
        ObjectNode booleanAlias = validInput();
        ((ObjectNode) booleanAlias.get("ledgers_before").get("construction")).put("historical_value", 1);
        ((ObjectNode) booleanAlias.get("ledgers_after").get("construction")).put("historical_value", true);
        assertThrows(IllegalArgumentException.class, () -> PeacetimeAssembly.assemble(bytes(booleanAlias)));
    }

    @Test void scopeAndWalletCannotBeReplacedWithCallerGreenFlags() throws IOException {
        ObjectNode input = validInput(); input.put("ledgerStable", true);
        assertThrows(IllegalArgumentException.class, () -> PeacetimeAssembly.assemble(bytes(input)));
        ObjectNode wallet = validInput(); ((ObjectNode) wallet.get("reader").get("snapshot").get("played_character_gold")).put("raw", 39_999_999);
        assertThrows(IllegalArgumentException.class, () -> PeacetimeAssembly.assemble(bytes(wallet)));
        ObjectNode domainWallet = validInput(); ((ObjectNode) domainWallet.get("construction").get("world")).put("player_gold_raw", 40_000_000.0);
        assertThrows(IllegalArgumentException.class, () -> PeacetimeAssembly.assemble(bytes(domainWallet)));
        ObjectNode expected = validInput(); expected.put("expected_revision", true);
        assertThrows(IllegalArgumentException.class, () -> PeacetimeAssembly.assemble(bytes(expected)));
        for (String raw : List.of("{}", "[]", "null", "{} {}", "{\"schema\":1,\"schema\":1}")) assertThrows(IllegalArgumentException.class, () -> PeacetimeAssembly.assemble(raw.getBytes(StandardCharsets.UTF_8)));
    }

    @Test void sourcePreservesDomainReservesAndDoesNotPerformReservation() throws IOException {
        JsonNode result = StrictJson.parse(PeacetimeAssembly.assemble(bytes(validInput())), 131_072);
        assertEquals(0, result.get("gold_reserve_raw").intValue()); assertEquals(0, result.get("max_active_wars").intValue());
        assertEquals(20_000_000, result.get("producer").get("domain_minimum_gold_reserves_raw").get("building").intValue());
        assertEquals(10_000_000, result.get("producer").get("domain_minimum_gold_reserves_raw").get("diplomacy").intValue());
        assertFalse(result.get("producer").get("formal_action_ready").booleanValue());
        OpportunityJson.Value typed = OpportunityJson.parse(bytes(result));
        assertEquals(typed, OpportunityJson.parse(OpportunityJson.encode(typed)));
    }

    private static void refusedAtEveryEntry(ObjectNode input) {
        byte[] raw = bytes(input);
        assertThrows(IllegalArgumentException.class, () -> PeacetimeAssemblyCodec.decode(raw));
        assertThrows(IllegalArgumentException.class, () -> PeacetimeAssembly.assemble(raw));
        assertThrows(IllegalArgumentException.class, () -> PeacetimeAssembly.assembleAndCollect(raw));
        OpportunityJson.Obj rows = OpportunityJson.object(OpportunityJson.parse(bytes(input.get("ledgers_before"))), "ledgers");
        assertThrows(IllegalArgumentException.class, () -> new PeacetimeAssembly.Ledgers(
                OpportunityJson.object(rows.get("construction"), "construction"), OpportunityJson.object(rows.get("faction"), "faction"),
                OpportunityJson.object(rows.get("family"), "family"), OpportunityJson.object(rows.get("child_default"), "child_default")));
    }
    private static ObjectNode ledger(ObjectNode input, String side, String domain) {
        return (ObjectNode) input.get("ledgers_" + side).get(domain);
    }

    @Test void normalizedLedgerMandatoryFieldsCannotBeReplacedByMatchingMalformedObjects() throws IOException {
        Map<String, List<String>> required = Map.of(
                "construction", List.of("schema", "pending", "applied", "applied_prior"),
                "faction", List.of("schema", "format_version", "pending", "resolved_request_outcomes"),
                "family", List.of("schema", "pending", "resolved"),
                "child_default", List.of("schema", "pending", "resolved"));
        for (var entry : required.entrySet()) for (String field : entry.getValue()) {
            ObjectNode input = validInput();
            for (String side : List.of("before", "after")) ledger(input, side, entry.getKey()).remove(field);
            refusedAtEveryEntry(input);
        }
        ObjectNode emptyFaction = validInput();
        for (String side : List.of("before", "after")) ledger(emptyFaction, side, "faction").removeAll();
        refusedAtEveryEntry(emptyFaction);
    }

    @Test void normalizedLedgerSchemasAndBasicTypesRemainStrict() throws IOException {
        for (String domain : List.of("construction", "faction", "family", "child_default")) {
            ObjectNode schema = validInput();
            for (String side : List.of("before", "after")) ledger(schema, side, domain).put("schema", "wrong-ledger");
            refusedAtEveryEntry(schema);
            ObjectNode pending = validInput();
            for (String side : List.of("before", "after")) ledger(pending, side, domain).putArray("pending");
            refusedAtEveryEntry(pending);
        }
        for (JsonNode wrongVersion : List.<JsonNode>of(new ObjectMapper().valueToTree(true), new ObjectMapper().valueToTree(1.0), new ObjectMapper().valueToTree("1"))) {
            ObjectNode input = validInput();
            for (String side : List.of("before", "after")) ledger(input, side, "faction").set("format_version", wrongVersion);
            refusedAtEveryEntry(input);
        }
        for (String domain : List.of("family", "child_default")) {
            ObjectNode input = validInput();
            for (String side : List.of("before", "after")) ledger(input, side, domain).put("resolved", false);
            refusedAtEveryEntry(input);
        }
        ObjectNode prior = validInput(), applied = validInput(), factionExtra = validInput(), outcome = validInput();
        for (String side : List.of("before", "after")) {
            ledger(prior, side, "construction").putArray("applied_prior").add(1);
            ledger(applied, side, "construction").put("applied", false);
            ledger(factionExtra, side, "faction").put("undeclared", true);
            ((ObjectNode) ledger(outcome, side, "faction").get("resolved_request_outcomes")).put("request-1", "UNKNOWN");
        }
        for (ObjectNode input : List.of(prior, applied, factionExtra, outcome)) refusedAtEveryEntry(input);
    }

    @Test void permittedOpaqueExtensionsKeepDecimalTokensAndReachActualCollector() throws IOException {
        ObjectNode input = validInput();
        for (String domain : List.of("construction", "family", "child_default")) for (String side : List.of("before", "after")) {
            ObjectNode extension = ledger(input, side, domain).putObject("retained_extension");
            extension.put("decimal", 1.0); extension.putNull("nullable"); extension.putArray("empty");
        }
        ((ObjectNode) input.get("construction")).put("retained_extension", 1.0);
        PeacetimeAssembly.Inputs decoded = PeacetimeAssemblyCodec.decode(bytes(input));
        OpportunityJson.Obj extension = OpportunityJson.object(decoded.before().construction().get("retained_extension"), "extension");
        assertInstanceOf(OpportunityJson.DecimalValue.class, extension.get("decimal"));
        assertEquals(decoded.before().construction(), OpportunityJson.parse(OpportunityJson.encode(decoded.before().construction())));
        OpportunityJson.Obj source = OpportunityJson.object(OpportunityJson.parse(PeacetimeAssembly.assemble(bytes(input))), "source");
        OpportunityJson.Obj domains = OpportunityJson.object(source.get("domains"), "domains");
        OpportunityJson.Obj query = OpportunityJson.object(OpportunityJson.object(domains.get("building"), "building").get("query"), "query");
        assertInstanceOf(OpportunityJson.DecimalValue.class, query.get("retained_extension"));
        assertEquals(source, OpportunityJson.parse(OpportunityJson.encode(source)));
        JsonNode intake = StrictJson.parse(PeacetimeAssembly.assembleAndCollect(bytes(input)), 131_072);
        assertEquals(golden().get("cases").get(0).get("collector").get("collected_candidate_ids"), intake.get("collected_candidate_ids"));
        assertFalse(intake.get("formal_action_ready").booleanValue());
    }

    @Test void selectedPayloadsAreValidatedByTheRealCollector() throws IOException {
        ObjectNode input = validInput(); ((ObjectNode) input.get("construction").get("candidate")).remove("building_type_id");
        byte[] request = bytes(input);
        OpportunityJson.Obj source = OpportunityJson.object(OpportunityJson.parse(PeacetimeAssembly.assemble(request)), "source");
        assertNotNull(OpportunityJson.object(source.get("domains"), "domains").get("building"));
        assertThrows(IllegalArgumentException.class, () -> PeacetimeAssembly.assembleAndCollect(request));
    }
}
