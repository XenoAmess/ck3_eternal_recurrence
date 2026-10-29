package org.xar.ck3.control.wave2.governance.succession;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.xar.ck3.control.contracts.FullJsonTree;
import java.io.IOException;
import java.io.InputStream;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.util.List;
import java.util.Set;
import java.util.stream.Stream;
import java.util.stream.StreamSupport;
import org.junit.jupiter.api.DynamicTest;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestFactory;

final class SuccessionContractTest {
    @TestFactory
    Stream<DynamicTest> originalProducerToRetainedReaderAndReconciliationGolden() throws IOException {
        JsonNode golden = golden(); assertEquals(18, golden.get("cases").size());
        assertTrue(golden.get("source_refs_unchanged").booleanValue()); assertTrue(golden.get("machine_id").isTextual());
        assertTrue(golden.get("original_unittest").get("whole_module").booleanValue());
        assertTrue(golden.get("original_unittest").get("tests").intValue() >= 15);
        assertEquals(golden.get("original_unittest").get("discovered_tests").intValue(), golden.get("original_unittest").get("tests").intValue());
        assertEquals(golden.get("original_unittest").get("tests").intValue(), golden.get("original_unittest").get("discovered_test_ids").size());
        assertEquals(0, golden.get("original_unittest").get("failures").intValue()); assertEquals(0, golden.get("original_unittest").get("errors").intValue());
        assertEquals(0, golden.get("original_unittest").get("skipped").intValue());
        assertTrue(golden.get("original_unittest").get("operating_compound_function_executed").booleanValue());
        return StreamSupport.stream(golden.get("cases").spliterator(), false).map(row -> DynamicTest.dynamicTest(row.get("name").textValue(), () -> {
            byte[] request = raw(row.get("request")); byte[] result = SuccessionConsumerPort.apply(request);
            assertEquals(row.get("expected"), SuccessionCodec.parse(result));
            assertEquals(row.get("request"), SuccessionCodec.parse(request), "caller document unchanged");
            String operation = row.get("request").get("operation").textValue();
            if (operation.equals("freeze") || operation.equals("normalize")) {
                assertEquals(row.get("expected"), SuccessionCodec.parse(SuccessionCodec.normalize(result)), "persistent expectation consumer round trip");
            } else if (operation.equals("operating")) {
                JsonNode output = SuccessionCodec.parse(result); assertFalse(output.get("submission_authorized").booleanValue());
                assertFalse(output.get("ordinary_priority_override").booleanValue()); assertEquals(0, output.get("queries_performed").intValue());
                assertTrue(output.get("action_candidates").isEmpty());
            }
        }));
    }
    @Test
    void actualDriverServiceFixtureRequestsUseTheSameJavaProducerAndRetainedConsumers() throws Exception {
        JsonNode source = golden(); JsonNode result = source.get("consumer_unittest");
        assertEquals("test_native_driver_retains_restores_and_reconciles_expectation", result.get("method").textValue());
        assertEquals(1, result.get("tests").intValue()); assertEquals(0, result.get("failures").intValue());
        assertEquals(0, result.get("errors").intValue()); assertEquals(0, result.get("skipped").intValue());
        Set<String> reached = new java.util.HashSet<>();
        for (JsonNode witnessed : source.get("actual_driver_consumer_requests")) {
            JsonNode request = witnessed.get("request"); reached.add(request.get("operation").textValue());
            assertEquals(witnessed.get("expected"), SuccessionCodec.parse(SuccessionConsumerPort.apply(raw(request))));
        }
        assertEquals(Set.of("freeze", "normalize", "reconcile"), reached);
        JsonNode rootRequests = source.get("actual_root_consumer_requests"); assertTrue(rootRequests.size() >= 4);
        for (JsonNode witnessed : rootRequests) { assertEquals(witnessed.get("expected"), SuccessionCodec.parse(SuccessionConsumerPort.apply(raw(witnessed.get("request"))))); }
        JsonNode rootConsumers = source.get("actual_root_consumer_outputs");
        assertEquals("unchanged", rootConsumers.get("invalidation").get("status").textValue());
        JsonNode warm = rootConsumers.get("warm_publication_refresh"); assertEquals("source_epoch_refresh_required", warm.get("status").textValue());
        assertTrue(warm.get("state").get("expectation").isNull()); assertTrue(warm.get("state").get("reconciliation").isNull());
        assertEquals(0, warm.get("queries_performed").intValue()); assertFalse(warm.get("submission_authorized").booleanValue());
        int retained = 0;
        for (JsonNode sample : source.get("cases")) {
            JsonNode consumers = sample.get("actual_consumers"); if (consumers.isNull()) { continue; }
            retained++;
            JsonNode actual = SuccessionCodec.parse(SuccessionConsumerPort.apply(raw(sample.get("request"))));
            JsonNode wal = consumers.get("binding_refresh_wal"); assertTrue(wal.get("accepted").booleanValue()); assertEquals(actual, wal.get("output"));
            JsonNode prefix = consumers.get("readonly_prefix_driver_flags");
            if (prefix.get("accepted").booleanValue()) { assertEquals(actual, prefix.get("output").get("succession_expectation")); }
            else { assertEquals("normalize_uint64_and_extensible_title", sample.get("name").textValue(), "the original readonly-prefix JSON contract retains its safe-integer boundary"); }
        }
        assertEquals(5, retained);
    }
    @Test
    void actualProducerAndConsumerSourcePinsRemainBoundToTheSourceCheckout() throws Exception {
        Path root = repositoryRoot();
        for (JsonNode ref : golden().get("source_refs")) {
            Path path = root.resolve(ref.get("path").textValue()).normalize(); assertTrue(path.startsWith(root));
            byte[] bytes = Files.readAllBytes(path); assertEquals(ref.get("bytes").longValue(), bytes.length, path.toString());
            assertEquals(ref.get("sha256").textValue(), HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)), path.toString());
        }
    }
    @Test
    void expectationExactFieldsAndRequiredNullsCannotDisappear() throws IOException {
        ObjectNode expectation = expectation();
        for (String field : List.of("schema", "status", "binding", "expectation_state", "predecessor_character_id", "expected_successor_character_id", "title_expectations", "risk_state", "unavailable_reason")) {
            ObjectNode broken = expectation.deepCopy(); broken.remove(field); assertThrows(IllegalArgumentException.class, () -> SuccessionCodec.normalize(raw(broken)), field);
        }
        ObjectNode extra = expectation.deepCopy(); extra.put("saved", true); assertThrows(IllegalArgumentException.class, () -> SuccessionCodec.normalize(raw(extra)));
        for (String field : Set.of("snapshot_id", "revision", "native_revision", "date_raw", "episode_run_id", "episode_character_id")) {
            ObjectNode missing = expectation.deepCopy(); ((ObjectNode) missing.get("binding")).remove(field); assertThrows(IllegalArgumentException.class, () -> SuccessionCodec.normalize(raw(missing)), field);
        }
        ObjectNode empty = expectation.deepCopy(); empty.putArray("title_expectations"); assertThrows(IllegalArgumentException.class, () -> SuccessionCodec.normalize(raw(empty)));
    }
    @Test
    void rawIntegerBoundariesRejectBooleansFloatsStringsAndOverflowBeforeReserialization() throws IOException {
        String original = new String(raw(expectation()), StandardCharsets.UTF_8);
        for (String token : List.of("true", "7.0", "\"7\"", "-1", "18446744073709551616")) {
            // Raw 7.0 goes straight to the production parser, never through a normalizing JSON tree.
            String request = original.replace("\"revision\":7", "\"revision\":" + token);
            assertFalse(request.equals(original), "golden revision seam exists");
            assertThrows(IllegalArgumentException.class, () -> SuccessionCodec.normalize(request.getBytes(StandardCharsets.UTF_8)), token);
        }
        for (String token : List.of("true", "100.0", "\"100\"", "0", "2147483648")) {
            String request = original.replace("\"predecessor_character_id\":100", "\"predecessor_character_id\":" + token);
            assertThrows(IllegalArgumentException.class, () -> SuccessionCodec.normalize(request.getBytes(StandardCharsets.UTF_8)), token);
        }
        ObjectNode maximum = expectation(); ObjectNode binding = (ObjectNode) maximum.get("binding");
        binding.put("revision", new BigInteger("18446744073709551615")); binding.put("native_revision", new BigInteger("9223372036854775809")); binding.put("date_raw", Integer.MIN_VALUE);
        assertEquals(maximum, SuccessionCodec.parse(SuccessionCodec.normalize(raw(maximum))));
    }
    @Test
    void episodeActorOrderPrimaryAndHeirStateCannotDrift() throws IOException {
        ObjectNode source = expectation();
        ObjectNode episode = source.deepCopy(); ((ObjectNode) episode.get("binding")).put("episode_character_id", 101);
        assertThrows(IllegalArgumentException.class, () -> SuccessionCodec.normalize(raw(episode)));
        ObjectNode selfHeir = source.deepCopy(); selfHeir.put("expected_successor_character_id", 100);
        assertThrows(IllegalArgumentException.class, () -> SuccessionCodec.normalize(raw(selfHeir)));
        ObjectNode primary = source.deepCopy(); ((ObjectNode) primary.get("title_expectations").get(1)).put("primary", true);
        assertThrows(IllegalArgumentException.class, () -> SuccessionCodec.normalize(raw(primary)));
        ObjectNode duplicate = source.deepCopy(); ((ObjectNode) duplicate.get("title_expectations").get(1).get("title")).put("title_id", 10);
        assertThrows(IllegalArgumentException.class, () -> SuccessionCodec.normalize(raw(duplicate)));
        ObjectNode noHeir = source.deepCopy(); noHeir.put("expectation_state", "no_primary_heir").put("risk_state", "no_primary_heir");
        assertThrows(IllegalArgumentException.class, () -> SuccessionCodec.normalize(raw(noHeir)));
        ObjectNode rowExtra = source.deepCopy(); ((ObjectNode) rowExtra.get("title_expectations").get(0)).putNull("capital_province_id");
        assertThrows(IllegalArgumentException.class, () -> SuccessionCodec.normalize(raw(rowExtra)), "capital is only accepted and removed at original bundle boundary");
    }
    @Test
    void postTransitionNeedsTheOriginalPausedChangedActorAndExactBundleFrame() throws IOException {
        ObjectNode base = request("reconcile_actual_successor_and_additional_title");
        for (String field : List.of("snapshot_id", "revision", "native_revision", "date_raw")) {
            ObjectNode changed = base.deepCopy(); ObjectNode snapshot = (ObjectNode) changed.get("post_snapshot");
            if (field.equals("snapshot_id")) { snapshot.put(field, "other"); } else { snapshot.put(field, snapshot.get(field).bigIntegerValue().add(BigInteger.ONE)); }
            assertThrows(IllegalArgumentException.class, () -> SuccessionConsumerPort.apply(raw(changed)), field);
        }
        ObjectNode notTerminal = base.deepCopy(); ((ObjectNode) notTerminal.get("post_snapshot")).put("one_life_terminal", false);
        assertThrows(IllegalArgumentException.class, () -> SuccessionConsumerPort.apply(raw(notTerminal)));
        ObjectNode noChange = base.deepCopy(); ((ObjectNode) noChange.get("post_snapshot").get("played_character")).put("character_id", 100);
        assertThrows(IllegalArgumentException.class, () -> SuccessionConsumerPort.apply(raw(noChange)));
        ObjectNode dead = base.deepCopy(); ((ObjectNode) dead.get("post_snapshot").get("played_character")).put("alive", false);
        assertThrows(IllegalArgumentException.class, () -> SuccessionConsumerPort.apply(raw(dead)));
        ObjectNode stale = base.deepCopy(); ((ObjectNode) stale.get("post_snapshot")).put("date_raw", 1); ((ObjectNode) stale.get("post_turn_bundle").get("binding")).put("date_raw", 1);
        assertThrows(IllegalArgumentException.class, () -> SuccessionConsumerPort.apply(raw(stale)));
    }
    @Test
    void extensibleSdkFieldsRemainDeclaredProjectionsAndRanksRetainIntegerTokenSemantics() throws IOException {
        ObjectNode request = request("operating_retained_same_frame_estate"); ObjectNode snapshot = (ObjectNode) request.get("snapshot");
        snapshot.putObject("future_sdk_component").put("measurement", 1.25);
        ObjectNode title = (ObjectNode) snapshot.get("succession_expectation").get("title_expectations").get(2).get("title");
        title.putObject("future_title_metadata").put("value", 2.50); title.put("tier_raw", 4);
        JsonNode equal = SuccessionCodec.parse(SuccessionConsumerPort.apply(raw(request))); assertEquals(12, equal.get("estate").get("equal_or_higher_rank_titles_to_other_heirs").get(0).intValue());
        assertTrue(equal.get("estate").get("title_expectations").get(2).get("title").has("future_title_metadata"));
        String floating = new String(raw(request), StandardCharsets.UTF_8).replace("\"tier_raw\":4,\"tier_key\":\"county\"", "\"tier_raw\":4.0,\"tier_key\":\"county\"");
        assertFalse(floating.equals(new String(raw(request), StandardCharsets.UTF_8)));
        JsonNode unknown = SuccessionCodec.parse(SuccessionConsumerPort.apply(floating.getBytes(StandardCharsets.UTF_8)));
        assertTrue(unknown.get("estate").get("equal_or_higher_rank_titles_to_other_heirs").isEmpty());
        assertEquals(12, unknown.get("estate").get("other_heir_title_rank_unavailable").get(0).intValue());
        assertFalse(unknown.get("actual_land_loss_or_realm_exit_inferred").booleanValue());
    }
    @Test
    void wrapperAndUtf8BoundariesRejectAmbiguousInputs() throws IOException {
        ObjectNode request = request("freeze_original_complete_current_rows");
        for (String field : List.of("schema", "operation", "turn_bundle", "episode_run_id", "episode_character_id")) {
            ObjectNode missing = request.deepCopy(); missing.remove(field); assertThrows(IllegalArgumentException.class, () -> SuccessionConsumerPort.apply(raw(missing)));
        }
        ObjectNode authority = request.deepCopy(); authority.put("submission_authorized", true); assertThrows(IllegalArgumentException.class, () -> SuccessionConsumerPort.apply(raw(authority)));
        String valid = new String(raw(request), StandardCharsets.UTF_8);
        String duplicate = valid.substring(0, valid.length() - 1) + ",\"episode_character_id\":100}";
        assertThrows(IllegalArgumentException.class, () -> SuccessionConsumerPort.apply(duplicate.getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class, () -> SuccessionConsumerPort.apply((valid + "{}").getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class, () -> SuccessionConsumerPort.apply(new byte[] {(byte) 0xc3, (byte) 0x28}));
        assertThrows(IllegalArgumentException.class, () -> SuccessionConsumerPort.apply(new byte[SuccessionCodec.MAX_BYTES + 1]));
        assertThrows(IllegalArgumentException.class, () -> SuccessionConsumerPort.apply("{\"x\":\"\\ud800\"}".getBytes(StandardCharsets.UTF_8)));
    }
    @Test
    void domainCollectionsAndOpaqueTitleBytesAreDefensiveCopies() throws IOException {
        SuccessionModel.Expectation value = SuccessionCodec.decodeExpectation(raw(expectation()));
        assertThrows(UnsupportedOperationException.class, () -> value.titleExpectations().clear());
        byte[] before = value.primary().title().original().bytes(); byte[] exposed = value.primary().title().original().bytes(); exposed[0] = 0;
        assertEquals(new String(before, StandardCharsets.UTF_8), new String(value.primary().title().original().bytes(), StandardCharsets.UTF_8));
    }
    @Test void opaqueTitleMetadataSurvivesSuccessionCodec() throws IOException {
        byte[] freezeRequest = ("""
        {
          "schema": "xar.java-succession-request/v1",
          "operation": "freeze",
          "turn_bundle": {
            "schema": "xar.ck3.turn-bundle/v1",
            "status": "available",
            "binding": {
              "snapshot_id": "opaque-estate",
              "revision": 7,
              "native_revision": 9,
              "date_raw": 100
            },
            "succession_state": {
              "status": "available",
              "value": {
                "primary_title_heir_character_id": {
                  "status": "available",
                  "value": 101
                },
                "partition": {
                  "status": "available",
                  "value": {
                    "title_heirs": [
                      {
                        "title": {
                          "title_id": 10,
                          "tier_raw": 2,
                          "tier_key": "county",
                          "opaque": {
                            "negative_zero": -0.0,
                            "huge": 1e999,
                            "integral": 9007199254740993,
                            "nullable": null
                          }
                        },
                        "first_heir_character_id": 101,
                        "primary": true
                      }
                    ],
                    "risk_state": "single_successor"
                  }
                }
              }
            },
            "ruler_state": {
              "status": "available",
              "value": {
                "character_id": 100,
                "alive": true
              }
            }
          },
          "episode_run_id": "opaque-episode",
          "episode_character_id": 100
        }
        """).getBytes(StandardCharsets.UTF_8);

        byte[] frozen = SuccessionConsumerPort.apply(freezeRequest);
        SuccessionModel.Expectation decoded = SuccessionCodec.decodeExpectation(frozen);
        byte[] encoded = SuccessionCodec.encodeExpectation(decoded);
        byte[] normalized = SuccessionCodec.normalize(encoded);
        ObjectNode normalizeRequest = SuccessionCodec.objectNode()
                .put("schema", SuccessionConsumerPort.SCHEMA).put("operation", "normalize");
        normalizeRequest.set("expectation", FullJsonTree.parse(normalized, SuccessionCodec.MAX_BYTES));
        byte[] consumerNormalized = SuccessionConsumerPort.apply(FullJsonTree.encode(normalizeRequest, SuccessionCodec.MAX_BYTES));

        JsonNode frozenTree = FullJsonTree.parse(frozen, SuccessionCodec.MAX_BYTES);
        JsonNode normalizedTree = FullJsonTree.parse(normalized, SuccessionCodec.MAX_BYTES);
        JsonNode consumerNormalizedTree = FullJsonTree.parse(consumerNormalized, SuccessionCodec.MAX_BYTES);

        JsonNode frozenTitle = frozenTree.get("title_expectations").get(0).get("title").get("opaque");
        assertEquals("-0.0", frozenTitle.get("negative_zero").toString());
        assertEquals("1e999", frozenTitle.get("huge").toString());
        assertEquals("9007199254740993", frozenTitle.get("integral").toString());
        assertTrue(frozenTitle.get("nullable").isNull());
        assertFalse(frozenTitle.has("missing"));

        JsonNode normalizedTitle = normalizedTree.get("title_expectations").get(0).get("title").get("opaque");
        assertEquals("-0.0", normalizedTitle.get("negative_zero").toString());
        assertEquals("1e999", normalizedTitle.get("huge").toString());
        assertEquals("9007199254740993", normalizedTitle.get("integral").toString());
        assertTrue(normalizedTitle.get("nullable").isNull());
        assertFalse(normalizedTitle.has("missing"));

        JsonNode consumerNormalizedTitle = consumerNormalizedTree.get("title_expectations").get(0).get("title").get("opaque");
        assertEquals("-0.0", consumerNormalizedTitle.get("negative_zero").toString());
        assertEquals("1e999", consumerNormalizedTitle.get("huge").toString());
        assertEquals("9007199254740993", consumerNormalizedTitle.get("integral").toString());
        assertTrue(consumerNormalizedTitle.get("nullable").isNull());
        assertFalse(consumerNormalizedTitle.has("missing"));

        ObjectNode snapshot = SuccessionCodec.objectNode();
        snapshot.put("snapshot_id", "opaque-estate");
        snapshot.put("revision", 7);
        snapshot.put("native_revision", 9);
        snapshot.put("date_raw", 100);
        snapshot.put("episode_run_id", "opaque-episode");
        snapshot.put("episode_character_id", 100);
        snapshot.put("paused", true);
        snapshot.put("map_ready", true);
        snapshot.put("one_life_terminal", false);
        snapshot.putNull("one_life_terminal_reason");
        ObjectNode played = snapshot.putObject("played_character");
        played.put("character_id", 100);
        played.put("alive", true);
        ObjectNode lifecycle = snapshot.putObject("succession_lifecycle");
        lifecycle.put("lifecycle", "ordinary_campaign_succession");
        snapshot.putNull("active_event");
        snapshot.putNull("pending_character_interaction");
        snapshot.set("succession_expectation", normalizedTree);

        ObjectNode operatingRequest = SuccessionCodec.objectNode()
                .put("schema", SuccessionConsumerPort.SCHEMA).put("operation", "operating");
        operatingRequest.set("snapshot", snapshot);
        operatingRequest.putNull("previous_expectation");
        byte[] operating = SuccessionConsumerPort.apply(FullJsonTree.encode(operatingRequest, SuccessionCodec.MAX_BYTES));
        JsonNode operatingTree = FullJsonTree.parse(operating, SuccessionCodec.MAX_BYTES);

        JsonNode operatingTitle = operatingTree.get("estate").get("title_expectations").get(0).get("title").get("opaque");
        assertEquals("-0.0", operatingTitle.get("negative_zero").toString());
        assertEquals("1e999", operatingTitle.get("huge").toString());
        assertEquals("9007199254740993", operatingTitle.get("integral").toString());
        assertTrue(operatingTitle.get("nullable").isNull());
        assertFalse(operatingTitle.has("missing"));
        for (JsonNode opaque : List.of(frozenTitle, normalizedTitle, consumerNormalizedTitle, operatingTitle)) {
            for (String field : List.of("negative_zero", "huge")) {
                assertTrue(opaque.get(field).isFloatingPointNumber(), field);
                assertFalse(opaque.get(field).isIntegralNumber(), field);
            }
            assertTrue(opaque.get("integral").isIntegralNumber());
            assertEquals(new BigInteger("9007199254740993"), opaque.get("integral").bigIntegerValue());
        }

        assertEquals("available", operatingTree.get("status").textValue());
        assertEquals(0, operatingTree.get("queries_performed").intValue());
        assertFalse(operatingTree.get("submission_authorized").booleanValue());
        assertFalse(operatingTree.get("ordinary_priority_override").booleanValue());
        assertEquals(0, operatingTree.get("action_candidates").size());

        List<String> identityPointers = List.of("/episode_character_id",
                "/turn_bundle/succession_state/value/partition/value/title_heirs/0/first_heir_character_id",
                "/turn_bundle/succession_state/value/partition/value/title_heirs/0/title/title_id");
        List<Double> equalLookingFloats = List.of(100.0, 101.0, 10.0);
        var nodes = com.fasterxml.jackson.databind.node.JsonNodeFactory.instance;
        for (int index = 0; index < identityPointers.size(); index++) {
            String pointer = identityPointers.get(index);
            int separator = pointer.lastIndexOf('/');
            for (JsonNode invalid : List.of(nodes.booleanNode(true), nodes.numberNode(equalLookingFloats.get(index)),
                    nodes.numberNode(2_147_483_648L))) {
                ObjectNode bad = (ObjectNode) FullJsonTree.parse(freezeRequest, SuccessionCodec.MAX_BYTES).deepCopy();
                ObjectNode parent = (ObjectNode) bad.at(pointer.substring(0, separator));
                parent.set(pointer.substring(separator + 1), invalid);
                assertThrows(IllegalArgumentException.class,
                        () -> SuccessionConsumerPort.apply(FullJsonTree.encode(bad, SuccessionCodec.MAX_BYTES)), pointer + " " + invalid);
            }
        }
    }

    private static ObjectNode expectation() throws IOException { return (ObjectNode) request("normalize_complete_retained_expectation").get("expectation"); }
    private static Path repositoryRoot() {
        String configured = System.getenv("XAR_REPO_ROOT");
        if (configured == null || configured.isBlank()) { configured = System.getProperty("xar.repo"); }
        Path root = configured == null || configured.isBlank() ? Path.of("..").toAbsolutePath().normalize() : Path.of(configured).toAbsolutePath().normalize();
        if (configured == null || configured.isBlank()) { while (root != null && !Files.isRegularFile(root.resolve("AGENTS.md"))) { root = root.getParent(); } }
        assertNotNull(root, "actual original producer repository required");
        assertTrue(Files.isRegularFile(root.resolve("AGENTS.md")), "configured original source checkout required"); return root;
    }
    private static ObjectNode request(String name) throws IOException { for (JsonNode row : golden().get("cases")) { if (row.get("name").textValue().equals(name)) { return (ObjectNode) row.get("request").deepCopy(); } } throw new IllegalArgumentException(name); }
    private static JsonNode golden() throws IOException {
        try (InputStream input = SuccessionContractTest.class.getResourceAsStream("/succession/original-producer-golden.json")) {
            assertNotNull(input, "committed original-producer golden required; no default Python invocation or skipped seam"); return SuccessionCodec.parse(input.readAllBytes());
        }
    }
    private static byte[] raw(JsonNode value) { return SuccessionCodec.encode(value); }
}
