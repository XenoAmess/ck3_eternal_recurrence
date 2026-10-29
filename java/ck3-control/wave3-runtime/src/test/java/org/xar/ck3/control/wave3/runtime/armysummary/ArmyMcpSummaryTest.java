package org.xar.ck3.control.wave3.runtime.armysummary;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertInstanceOf;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;

class ArmyMcpSummaryTest {
    private static final int CORPUS_MAX_BYTES = 262_144;
    @Test void realProducerGoldenCoversAllRegisteredConsumersAndRoundTrips() throws IOException {
        JsonNode golden = golden(); int cases = 0; int registered = 0;
        assertEquals(17, golden.path("original_consumer_tests").path("passed").intValue());
        assertEquals(0, golden.path("original_consumer_tests").path("failed").intValue());
        assertEquals(0, golden.path("original_consumer_tests").path("skipped").intValue());
        assertFalse(golden.path("runtime_cutover").booleanValue());
        for (JsonNode item : golden.path("cases")) {
            byte[] input = bytes(item.path("input_json").textValue());
            byte[] actual;
            if (item.path("kind").textValue().equals("auto")) {
                ArmyMcpSummary.AutoTurn decoded = ArmyMcpSummaryCodec.decodeAutoTurn(input);
                actual = ArmyMcpSummaryCodec.encodeAutoResult(decoded);
                assertEquals(decoded, ArmyMcpSummaryCodec.decodeAutoTurn(input));
            } else {
                ArmyMcpSummary.Query decoded = ArmyMcpSummaryCodec.decodeQuery(input);
                actual = ArmyMcpSummaryCodec.encodeQueryResult(decoded);
                assertEquals(decoded, ArmyMcpSummaryCodec.fromServicePayload(object(StrictJson.parse(input))));
            }
            sameWire(item.path("expected"), StrictJson.parse(actual));
            assertTrue(actual.length < 4096, item.path("name").textValue());
            assertFalse(new String(actual, StandardCharsets.UTF_8).contains("army_strengths\""));
            if (item.path("name").textValue().startsWith("registered_")) { registered++; }
            cases++;
        }
        assertEquals(24, cases); assertEquals(4, registered);
    }

    @Test void wrongIntegerTokensAreRejectedBeforeCreatingTheTypedModel() {
        for (String token : List.of("true", "1.0", "\"1\"", "-1", "9007199254740992")) {
            assertThrows(ContractViolationException.class,
                    () -> query("{\"query_sequence\":" + token + ",\"army_strengths\":[]}"));
            assertThrows(ContractViolationException.class,
                    () -> query("{\"army_strengths\":[{\"army_id\":" + token + "}]}"));
        }
        assertEquals(0L, query("{\"query_sequence\":0,\"army_strengths\":[{\"army_id\":0}]}").querySequence());
    }

    @Test void requiredContainersAndConsumedTypesAreStrictWhileNullableMembersRemainNull() {
        for (String raw : List.of("{}", "{\"army_strengths\":null}", "{\"army_strengths\":{}}",
                "{\"army_strengths\":[null]}", "{\"accepted\":1,\"army_strengths\":[]}",
                "{\"army_ids\":false,\"army_strengths\":[]}", "{\"status\":true,\"army_strengths\":[]}")) {
            assertThrows(ContractViolationException.class, () -> query(raw));
        }
        for (String raw : List.of("{}", "{\"plan\":{},\"result\":null}",
                "{\"plan\":null,\"result\":{\"army_strengths\":[]}}")) {
            assertThrows(ContractViolationException.class, () -> ArmyMcpSummaryCodec.decodeAutoTurn(bytes(raw)));
        }
        ObjectNode summary = ArmyMcpSummaryCodec.summary(query("{\"army_strengths\":[{}]}"));
        assertTrue(summary.get("accepted").isNull()); assertTrue(summary.get("status").isNull());
        assertEquals(13, summary.get("armies").get(0).size());
        assertTrue(summary.get("army_ids").get(0).isNull());
    }

    @Test void enumProfilesAndPartialUnavailableObservationsRemainDistinct() {
        for (String field : List.of("status", "army_strengths_profile", "army_observed_phase_coverage")) {
            assertThrows(ContractViolationException.class, () -> query("{\"" + field + "\":\"unknown\",\"army_strengths\":[]}"));
        }
        ArmyMcpSummary.Query query = query("{\"accepted\":false,\"status\":\"partial\",\"army_strengths_profile\":\"observed_history_full_v1\","
                + "\"army_observed_phase_coverage\":\"exported_retained\",\"army_strengths\":[{\"status\":\"available\",\"current_soldiers\":0},"
                + "{\"status\":\"unavailable\",\"current_soldiers\":null,\"unavailable_reason\":\"regiment_generation_mismatch\"}]}");
        assertEquals(ArmyMcpSummary.QueryStatus.PARTIAL, query.status()); assertFalse(query.accepted());
        assertEquals(0L, query.armies().get(0).currentSoldiers()); assertNull(query.armies().get(1).currentSoldiers());
        assertEquals("regiment_generation_mismatch", query.armies().get(1).unavailableReason());
    }

    @Test void sourceObjectMissingMemberNeverFallsBackToTheQueriedRevision() {
        String suffix = ",\"queried_revision\":99,\"queried_native_revision\":98,\"army_strengths\":[]}";
        ArmyMcpSummary.Query empty = query("{\"source\":{}" + suffix);
        assertNull(empty.source().revision()); assertNull(empty.source().nativeRevision());
        for (String source : List.of("null", "false", "[]", "\"opaque\"")) {
            ArmyMcpSummary.Query fallback = query("{\"source\":" + source + suffix);
            assertEquals(99L, fallback.source().revision()); assertEquals(98L, fallback.source().nativeRevision());
        }
        assertThrows(ContractViolationException.class, () -> query("{\"source\":{\"revision\":1.0},\"army_strengths\":[]}"));
    }

    @Test void missingNullEmptyAndOrderedDuplicateArmyIdsPreserveTheirOwnMeanings() {
        String rows = "\"army_strengths\":[{\"army_id\":82},{\"army_id\":81}]";
        assertInstanceOf(ArmyMcpSummary.DerivedArmyIds.class, query("{" + rows + "}").armyIds());
        assertInstanceOf(ArmyMcpSummary.NullArmyIds.class, query("{\"army_ids\":null," + rows + "}").armyIds());
        assertEquals(0, ArmyMcpSummaryCodec.summary(query("{\"army_ids\":[]," + rows + "}")).get("army_ids").size());
        ObjectNode result = ArmyMcpSummaryCodec.summary(query("{\"army_ids\":[81,82,81,null]," + rows + "}"));
        assertEquals(81, result.get("army_ids").get(0).intValue()); assertEquals(81, result.get("army_ids").get(2).intValue());
        assertTrue(result.get("army_ids").get(3).isNull()); assertEquals(82, result.get("armies").get(0).get("army_id").intValue());
    }

    @Test void optionalTimingRejectsWrongFieldsTypesAndNestingWithoutReplacingBusiness() {
        String valid = "\"read_total_ns\":100,\"owner_query_ns\":80,\"baseline_read_ns\":60,\"rich_attach_ns\":5,\"serialize_ns\":10";
        for (String bad : List.of("null", "{}", "{" + valid + ",\"extra\":0}",
                "{" + valid.replace(":60", ":true") + "}", "{" + valid.replace(":80", ":80.0") + "}",
                "{" + valid.replace(":10", ":-1") + "}", "{" + valid.replace(":80", ":101") + "}",
                "{" + valid.replace(":5", ":81") + "}", "{" + valid.replace(":100", ":9007199254740992") + "}")) {
            ArmyMcpSummary.Query query = query("{\"accepted\":true,\"status\":\"available\",\"query_sequence\":7,"
                    + "\"army_native_timing_v1\":" + bad + ",\"army_strengths\":[]}");
            assertTrue(query.accepted()); assertEquals(7L, query.querySequence()); assertNull(query.nativeTiming());
            assertFalse(ArmyMcpSummaryCodec.summary(query).has("army_native_timing_v1"));
        }
        assertNotNull(query("{\"army_native_timing_v1\":{" + valid + "},\"army_strengths\":[]}").nativeTiming());
    }

    @Test void timingBoundaryKeepsSerializerIndependentAndZeroValuesExact() {
        ArmyMcpSummary.NativeTiming zeros = new ArmyMcpSummary.NativeTiming(0, 0, 0, 0, 0);
        assertEquals(0, zeros.readTotalNs());
        ArmyMcpSummary.NativeTiming separate = new ArmyMcpSummary.NativeTiming(100, 80, 80, 80, 1000);
        assertEquals(1000, separate.serializeNs());
        assertThrows(ContractViolationException.class, () -> new ArmyMcpSummary.NativeTiming(79, 80, 60, 5, 10));
        assertThrows(ContractViolationException.class, () -> new ArmyMcpSummary.NativeTiming(100, 80, 81, 5, 10));
    }

    @Test void exactNumericInterfaceDoesNotRoundInt64ScalarsOrIdentities() {
        assertEquals(StrictJson.MAX_SAFE_INTEGER, query("{\"army_strengths\":[{\"army_id\":9007199254740991}]}").armies().get(0).armyId());
        assertEquals(-StrictJson.MAX_SAFE_INTEGER, query("{\"army_strengths\":[{\"current_supply_raw\":-9007199254740991}]}").armies().get(0).currentSupplyRaw());
        assertThrows(ContractViolationException.class, () -> query("{\"army_strengths\":[{\"ai_base_power_raw\":9223372036854775807}]}"));
        assertThrows(ContractViolationException.class, () -> query("{\"army_strengths\":[{\"army_id\":\"18446744073709551615\"}]}"));
    }

    @Test void richInProcessObservationsAreNeitherClonedNorExportedNorMutated() {
        ObjectNode input = object(StrictJson.parse(bytes("{\"army_strengths\":[{\"army_id\":81}],\"army_ids\":[81]}")));
        String journal = "旅人保留日志".repeat(100_000);
        input.put("actual_army_observed_phase_consumption_12004", journal);
        object(input.get("army_strengths").get(0)).put("retained_phase_journal", journal);
        ArmyMcpSummary.Query query = ArmyMcpSummaryCodec.fromServicePayload(input);
        input.put("accepted", false); object(input.get("army_strengths").get(0)).put("army_id", 99);
        assertEquals(81L, query.armies().get(0).armyId());
        byte[] wire = ArmyMcpSummaryCodec.encodeQueryResult(query);
        assertTrue(wire.length < 4096); assertFalse(new String(wire, StandardCharsets.UTF_8).contains("journal"));
        assertEquals(journal, input.get("actual_army_observed_phase_consumption_12004").textValue());
        assertThrows(UnsupportedOperationException.class, () -> query.armies().clear());
        List<Long> mutable = new ArrayList<>(); mutable.add(81L); mutable.add(null);
        ArmyMcpSummary.ExplicitArmyIds ids = new ArmyMcpSummary.ExplicitArmyIds(mutable); mutable.clear();
        assertEquals(2, ids.values().size()); assertThrows(UnsupportedOperationException.class, () -> ids.values().clear());
    }

    @Test void duplicateTrailingMalformedUtf8AndByteCapsFailClosed() {
        assertThrows(ContractViolationException.class, () -> query("{\"army_strengths\":[],\"army_strengths\":[]}"));
        assertThrows(ContractViolationException.class, () -> query("{\"army_strengths\":[]} true"));
        assertThrows(ContractViolationException.class, () -> ArmyMcpSummaryCodec.decodeQuery(new byte[]{(byte) 0xc3, 0x28}));
        assertThrows(ContractViolationException.class, () -> ArmyMcpSummaryCodec.decodeQuery(new byte[ArmyMcpSummaryCodec.MAX_INPUT_BYTES + 1]));
        ArmyMcpSummary.Query tooLarge = query("{\"army_strengths\":[{\"unavailable_reason\":\"" + "x".repeat(32_000) + "\"}]}" );
        assertThrows(ContractViolationException.class, () -> ArmyMcpSummaryCodec.encodeAutoResult(new ArmyMcpSummary.AutoTurn(
                "executed", "x".repeat(32_000), new ArmyMcpSummary.Plan("x".repeat(32_000), "phase"), tooLarge)));
    }


    @Test void sourceProvenanceRejectsIncompleteOrUntypedActualImportClosure() throws IOException {
        ObjectNode complete = object(golden());
        ObjectNode absent = complete.deepCopy(); absent.remove("source_provenance");
        assertThrows(AssertionError.class, () -> assertSourceProvenance(absent));
        ObjectNode boolCount = complete.deepCopy();
        object(boolCount.get("source_provenance")).put("recorded_repo_sources", true);
        assertThrows(AssertionError.class, () -> assertSourceProvenance(boolCount));
        ObjectNode unchecked = complete.deepCopy();
        object(unchecked.get("source_provenance")).put("source_pre_post_equal", false);
        assertThrows(AssertionError.class, () -> assertSourceProvenance(unchecked));
        ObjectNode uncovered = complete.deepCopy();
        object(uncovered.get("source_provenance")).putArray("unrecorded_repo_sources").add("unobserved.py");
        assertThrows(AssertionError.class, () -> assertSourceProvenance(uncovered));
        ObjectNode floatBytes = complete.deepCopy();
        object(floatBytes.get("source_refs").get(0)).put("bytes", 1.0);
        assertThrows(AssertionError.class, () -> assertSourceProvenance(floatBytes));
        ObjectNode badHash = complete.deepCopy();
        object(badHash.get("source_refs").get(0)).put("sha256", "not-a-source-hash");
        assertThrows(AssertionError.class, () -> assertSourceProvenance(badHash));
        ObjectNode duplicate = complete.deepCopy();
        ((com.fasterxml.jackson.databind.node.ArrayNode) duplicate.get("source_refs")).add(duplicate.get("source_refs").get(0).deepCopy());
        assertThrows(AssertionError.class, () -> assertSourceProvenance(duplicate));
    }

    private static ArmyMcpSummary.Query query(String raw) { return ArmyMcpSummaryCodec.decodeQuery(bytes(raw)); }
    private static byte[] bytes(String raw) { return raw.getBytes(StandardCharsets.UTF_8); }
    private static ObjectNode object(JsonNode node) { return assertInstanceOf(ObjectNode.class, node); }
    private static JsonNode golden() throws IOException {
        try (InputStream input = ArmyMcpSummaryTest.class.getResourceAsStream("/armysummary/producer-golden.json")) {
            assertNotNull(input, "real producer golden must be captured and committed; no skip or Python fallback");
            byte[] raw = input.readNBytes(CORPUS_MAX_BYTES + 1);
            if (raw.length > CORPUS_MAX_BYTES) { throw new IOException("Army producer corpus exceeds262144 bytes"); }
            JsonNode result = StrictJson.parse(raw, CORPUS_MAX_BYTES);
            assertSourceProvenance(result); return result;
        }
    }

    private static void assertSourceProvenance(JsonNode golden) {
        JsonNode provenance = golden.path("source_provenance");
        assertTrue(provenance.isObject()); assertEquals(8, provenance.size());
        assertEquals("xar.ck3.measured-repo-import-closure/v1", provenance.path("schema").textValue());
        assertEquals("repo-python-excluding-interpreter-prefixes/v1", provenance.path("scope").textValue());
        assertEquals(0, nonnegativeCount(provenance.path("initial_repo_sources")));
        int afterImports = nonnegativeCount(provenance.path("after_imports_repo_sources"));
        int afterSuite = nonnegativeCount(provenance.path("after_suite_repo_sources"));
        int recorded = nonnegativeCount(provenance.path("recorded_repo_sources"));
        assertTrue(afterImports > 0 && afterSuite > 0 && afterImports <= recorded && afterSuite <= recorded);
        assertTrue(provenance.path("source_pre_post_equal").isBoolean());
        assertTrue(provenance.path("source_pre_post_equal").booleanValue());
        assertTrue(provenance.path("unrecorded_repo_sources").isArray());
        assertEquals(0, provenance.path("unrecorded_repo_sources").size());
        JsonNode refs = golden.path("source_refs"); assertTrue(refs.isArray());
        Set<String> paths = new HashSet<>(); String previous = null;
        for (JsonNode ref : refs) {
            assertTrue(ref.isObject()); assertEquals(3, ref.size());
            assertTrue(ref.path("path").isTextual());
            String path = ref.path("path").textValue();
            assertTrue(!path.isBlank() && !path.startsWith("/") && !path.contains("\\") && !path.contains(":"));
            assertTrue(!List.of(path.split("/")).contains(".."));
            assertTrue(path.endsWith(".py") && !path.contains("/.venv/"));
            assertTrue(paths.add(path));
            if (previous != null) { assertTrue(previous.compareTo(path) < 0, "actual refs must be sorted and unique"); }
            previous = path;
            // Empty package __init__.py is an actual source and has a valid SHA-256.
            assertTrue(ref.path("bytes").isIntegralNumber() && ref.path("bytes").canConvertToLong()
                    && ref.path("bytes").longValue() >= 0);
            assertTrue(ref.path("sha256").isTextual() && ref.path("sha256").textValue().matches("[0-9a-f]{64}"));
        }
        assertEquals(recorded, paths.size());
        assertTrue(paths.containsAll(Set.of(
                "tools/ck3_live_run_id.py",
                "ck3_autonomous_player/src/xar_autoplayer/bridge/army_strengths_mcp_result.py",
                "ck3_autonomous_player/src/xar_autoplayer/bridge/army_native_timing_summary_v1.py",
                "ck3_autonomous_player/src/xar_autoplayer/bridge/army_strengths_profile_contract.py",
                "ck3_autonomous_player/src/xar_autoplayer/bridge/mcp_server.py",
                "ck3_autonomous_player/src/xar_autoplayer/bridge/service.py",
                "ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py",
                "ck3_autonomous_player/src/xar_autoplayer/bridge/war_contract.py",
                "ck3_autonomous_player/tests/unit/test_army_strengths_mcp_result_serialization_performance.py",
                "ck3_autonomous_player/tests/unit/test_army_profile_mcp_compact_regression.py",
                "ck3_autonomous_player/tests/unit/test_army_auto_scalar_projection_v1.py",
                "ck3_autonomous_player/tests/unit/test_native_bridge_driver.py",
                "ck3_autonomous_player/tests/unit/test_army_profile_cache_regression.py")));
    }
    private static int nonnegativeCount(JsonNode value) {
        assertTrue(value.isIntegralNumber() && value.canConvertToInt());
        int count = value.intValue(); assertTrue(count >= 0); return count;
    }

    private static void sameWire(JsonNode expected, JsonNode actual) {
        assertEquals("complete", expected.path("resultType").textValue(), "actual MCP 2.0.0 producer discriminator");
        assertEquals("complete", actual.path("resultType").textValue());
        assertEquals(4, expected.size(), "complete producer wire fields are mandatory");
        assertEquals(4, actual.size());
        assertEquals(expected.get("isError"), actual.get("isError"));
        assertEquals(expected.get("content").size(), actual.get("content").size());
        assertEquals("text", actual.get("content").get(0).get("type").textValue());
        assertArrayEquals(StrictJson.canonical(expected.get("structuredContent")), StrictJson.canonical(actual.get("structuredContent")));
        assertArrayEquals(StrictJson.canonical(actual.get("structuredContent")), StrictJson.canonical(
                StrictJson.parse(bytes(actual.get("content").get(0).get("text").textValue()))));
        assertArrayEquals(StrictJson.canonical(expected.get("structuredContent")), StrictJson.canonical(
                StrictJson.parse(bytes(expected.get("content").get(0).get("text").textValue()))));
        assertEquals(expected.size(), actual.size());
    }
}

