package org.xar.ck3.control.events.vanilla;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.events.vanilla.VanillaOptionProjection.OptionContract;
import org.xar.ck3.control.events.vanilla.VanillaOptionProjection.Request;
import org.xar.ck3.control.events.vanilla.VanillaOptionProjection.Result;
import org.xar.ck3.control.events.vanilla.VanillaOptionProjection.Status;

final class VanillaOptionProjectionTest {
    private static final ObjectMapper JSON = new ObjectMapper();

    private static JsonNode golden() throws IOException {
        try (InputStream stream = VanillaOptionProjectionTest.class.getResourceAsStream("/vanilla/option-projection-golden-v1.json")) {
            assertNotNull(stream, "committed real producer golden is required");
            return JSON.readTree(stream);
        }
    }
    private static ObjectNode baseline() throws IOException {
        return golden().get("cases").get(0).get("request").deepCopy();
    }
    private static Request decode(JsonNode node) throws IOException {
        return VanillaProjectionCodec.decode(JSON.writeValueAsBytes(node));
    }
    private static void rejects(JsonNode node) throws IOException {
        byte[] bytes = JSON.writeValueAsBytes(node);
        assertThrows(IllegalArgumentException.class, () -> VanillaProjectionCodec.decode(bytes));
    }

    @Test void matchesActualRegistryProducerAndSharedLeafForAllFifteenCases() throws IOException {
        JsonNode corpus = golden();
        assertEquals("xar.ck3.vanilla-option-projection-golden/v1", corpus.get("schema").textValue());
        assertEquals(15, corpus.get("cases").size());
        for (JsonNode row : corpus.get("cases")) {
            Request request = decode(row.get("request"));
            Result result = VanillaOptionProjection.project(request);
            Map<String, Boolean> leafChecks = new LinkedHashMap<>(result.checks());
            assertTrue(leafChecks.remove("registry_exact_build"), row.get("name").textValue());
            assertTrue(leafChecks.remove("registry_source_index_binding"), row.get("name").textValue());
            assertEquals(row.get("expected").get("checks"), JSON.valueToTree(leafChecks), row.get("name").textValue());
            JsonNode encoded = JSON.readTree(VanillaProjectionCodec.encode(result));
            assertEquals(row.get("expected").get("selected_option"), encoded.get("selected_option"), row.get("name").textValue());
            boolean all = leafChecks.values().stream().allMatch(Boolean::booleanValue);
            assertEquals(all ? Status.PROJECTION_READY : Status.BLOCKED, result.status(), row.get("name").textValue());
            assertFalse(result.actionAuthorized());
            assertFalse(result.semanticDecisionReady());
        }
    }

    @Test void serializationRoundTripsImmutableTypedInputAndKeepsDisplayOrder() throws IOException {
        for (JsonNode row : golden().get("cases")) {
            Request original = decode(row.get("request"));
            Request roundTrip = VanillaProjectionCodec.decode(VanillaProjectionCodec.encode(original));
            assertEquals(original, roundTrip);
            assertEquals(VanillaOptionProjection.project(original), VanillaOptionProjection.project(roundTrip));
            assertThrows(UnsupportedOperationException.class, () -> original.options().clear());
        }
    }

    @Test void integerIdentityAndVersionTokensRejectBoolFloatStringNullAndOverflow() throws IOException {
        List<JsonNode> bad = List.of(JSON.getNodeFactory().booleanNode(true), JSON.getNodeFactory().numberNode(1.0),
            JSON.getNodeFactory().textNode("1"), JSON.getNodeFactory().nullNode(), JSON.getNodeFactory().numberNode(Long.MAX_VALUE));
        for (JsonNode value : bad) {
            ObjectNode version = baseline(); version.set("schema_version", value); rejects(version);
            ObjectNode count = baseline(); count.set("snapshot_option_count", value); rejects(count);
            ObjectNode nativeIndex = baseline();
            ((ObjectNode) nativeIndex.get("options").get(0)).set("native_option_index", value); rejects(nativeIndex);
            ObjectNode renderedIndex = baseline();
            ((ObjectNode) renderedIndex.get("options").get(0)).set("rendered_index", value); rejects(renderedIndex);
        }
    }

    @Test void missingNullEmptyAndUnknownRemainDifferentContracts() throws IOException {
        ObjectNode missing = baseline(); missing.remove("contract"); rejects(missing);
        ObjectNode nullContract = baseline(); nullContract.putNull("contract"); rejects(nullContract);
        ObjectNode nullDisabled = baseline(); ((ObjectNode) nullDisabled.get("contract")).putNull("disabled_native_option_indices"); rejects(nullDisabled);
        ObjectNode missingDisabled = baseline(); ((ObjectNode) missingDisabled.get("contract")).remove("disabled_native_option_indices"); rejects(missingDisabled);
        ObjectNode unknown = baseline(); unknown.put("allow_fallback", true); rejects(unknown);
        ObjectNode nestedUnknown = baseline(); ((ObjectNode) nestedUnknown.get("options").get(0)).put("unsafe", true); rejects(nestedUnknown);
        ObjectNode empty = baseline(); ((ObjectNode) empty.get("contract")).putArray("snapshot_option_counts");
        assertFalse(VanillaOptionProjection.project(decode(empty)).checks().get("snapshot_option_count"));
    }

    @Test void analyzedSourceWithoutOccurrenceContractNeverBecomesKnownRecommendation() throws IOException {
        ObjectNode node = baseline();
        ((ObjectNode) node.get("binding")).put("registry_state", "source_analyzed_no_occurrence_contract");
        node.putNull("contract");
        Request request = decode(node);
        Result result = VanillaOptionProjection.project(request);
        assertEquals(Status.NOT_REGISTERED, result.status());
        assertTrue(result.checks().isEmpty());
        assertEquals(null, result.selectedOption());
        assertEquals(request, VanillaProjectionCodec.decode(VanillaProjectionCodec.encode(request)));
        assertFalse(result.actionAuthorized());
    }

    @Test void sourceDriftAndUnsupportedExactBuildCannotGrantProjectionReady() throws IOException {
        ObjectNode drift = baseline();
        ((ObjectNode) drift.get("binding").get("source_anchors").get(0)).put("indexed_sha256", "A".repeat(64));
        Result result = VanillaOptionProjection.project(decode(drift));
        assertEquals(Status.BLOCKED, result.status());
        assertEquals(List.of("registry_source_index_binding"), result.failedChecks());
        ObjectNode build = baseline(); ((ObjectNode) build.get("binding")).put("ck3_build", "9.9.9");
        assertFalse(VanillaOptionProjection.project(decode(build)).checks().get("registry_exact_build"));
        ObjectNode empty = baseline(); ((ObjectNode) empty.get("binding")).putArray("source_anchors");
        assertFalse(VanillaOptionProjection.project(decode(empty)).checks().get("registry_source_index_binding"));
    }

    @Test void malformedBytesDuplicateKeysAndTrailingValuesAreRejected() throws IOException {
        byte[] original = JSON.writeValueAsBytes(baseline());
        String json = new String(original, StandardCharsets.UTF_8);
        byte[] duplicate = json.replace("\"schema_version\":1", "\"schema_version\":1,\"schema_version\":1").getBytes(StandardCharsets.UTF_8);
        assertTrue(duplicate.length > original.length);
        assertThrows(IllegalArgumentException.class, () -> VanillaProjectionCodec.decode(duplicate));
        assertThrows(IllegalArgumentException.class, () -> VanillaProjectionCodec.decode((json + " {}").getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class, () -> VanillaProjectionCodec.decode(new byte[] {(byte) 0xc3, 0x28}));
        assertThrows(IllegalArgumentException.class, () -> VanillaProjectionCodec.decode(new byte[65_537]));
    }

    @Test void disabledSubsetDuplicateIndicesAndWrongNativeNumberAreRealBlockedBranches() throws IOException {
        Request base = decode(baseline());
        OptionContract c = base.contract();
        OptionContract disabled = new OptionContract(c.optionCount(), c.nativeOptionIndices(), c.selectedNativeOptionIndex(),
            c.selectedOptionNumber(), List.of(c.selectedNativeOptionIndex()), c.snapshotOptionCounts());
        assertFalse(VanillaOptionProjection.project(new Request(base.binding(), disabled, base.options(), base.snapshotOptionCount()))
            .checks().get("disabled_option_contract"));
        List<Integer> duplicate = new ArrayList<>(c.nativeOptionIndices()); duplicate.set(1, duplicate.get(0));
        OptionContract repeated = new OptionContract(c.optionCount(), duplicate, c.selectedNativeOptionIndex(),
            c.selectedOptionNumber(), c.disabledNativeOptionIndices(), c.snapshotOptionCounts());
        assertFalse(VanillaOptionProjection.project(new Request(base.binding(), repeated, base.options(), base.snapshotOptionCount()))
            .checks().get("native_option_indices_exact"));
        ObjectNode mapping = baseline(); ((ObjectNode) mapping.get("contract")).put("selected_option_number", 25);
        assertFalse(VanillaOptionProjection.project(decode(mapping)).checks().get("selected_option_mapping"));
        ObjectNode shown = baseline(); ((ObjectNode) shown.get("options").get(0)).put("shown", 1); rejects(shown);
    }
}
