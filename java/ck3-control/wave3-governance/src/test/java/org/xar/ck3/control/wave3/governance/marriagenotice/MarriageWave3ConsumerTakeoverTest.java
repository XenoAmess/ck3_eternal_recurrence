package org.xar.ck3.control.wave3.governance.marriagenotice;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.util.TreeSet;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionPort;
import org.xar.ck3.control.contracts.projection.ProjectionDomainRejection;
import org.xar.ck3.control.wave2.governance.betrothal.MarriageProjectionJson;

/** Differential fixtures cross the registered operation and the actual legacy-result JSON shape. */
class MarriageWave3ConsumerTakeoverTest {
    private static JsonNode golden(String leaf) throws Exception {
        String name = leaf.equals("marriagepending") ? "original-producer-golden.json" : "python-golden-v1.json";
        try (var input = MarriageWave3ConsumerTakeoverTest.class.getResourceAsStream("/" + leaf + "/" + name)) {
            assertNotNull(input, "actual original producer golden required; missing capture cannot pass by skip");
            return MarriageProjectionJson.value(input.readAllBytes(), 262_144);
        }
    }
    private static byte[] bytes(JsonNode value) { return MarriageProjectionJson.bytes(value, 525_312); }
    private static <I, O> ObjectNode call(ProjectionPort<I, O> port, JsonNode request) {
        byte[] result = port.encode(port.project(port.decode(bytes(request))));
        assertTrue(result.length <= port.outputMaximumBytes());
        return (ObjectNode) MarriageProjectionJson.value(result, port.outputMaximumBytes());
    }
    private static ObjectNode patch(JsonNode base, JsonNode changes) {
        ObjectNode result = base.deepCopy();
        for (JsonNode change : changes) {
            JsonNode parent = result, path = change.get("path");
            for (int index = 0; index < path.size() - 1; index++) {
                JsonNode key = path.get(index); parent = key.isIntegralNumber() ? parent.get(key.intValue()) : parent.get(key.textValue());
            }
            JsonNode key = path.get(path.size() - 1);
            if (parent instanceof ObjectNode object) {
                if (change.path("remove").asBoolean(false)) { object.remove(key.textValue()); }
                else { object.set(key.textValue(), change.get("value").deepCopy()); }
            } else if (parent instanceof ArrayNode array) {
                if (change.path("remove").asBoolean(false)) { array.remove(key.intValue()); }
                else { array.set(key.intValue(), change.get("value").deepCopy()); }
            } else { fail("invalid original producer patch"); }
        }
        return result;
    }
    private static ObjectNode notice(String stage) {
        ObjectNode root = StrictJson.object(); root.put("schema", MarriageWave3ProjectionCatalog.ContinuePort.SCHEMA);
        root.put("stage", stage); return root;
    }
    @Test void sourceReviewPreservesTheOriginalAppliedAndObjectIdentityDecision() throws Exception {
        JsonNode golden = golden("marriagenotice");
        for (JsonNode vector : golden.path("review_cases")) {
            ObjectNode input = patch(golden.get("base_review_request"), vector.get("patches"));
            ObjectNode actual = call(new MarriageWave3ProjectionCatalog.ReviewPort(), input);
            assertEquals(vector.get("applied"), actual.get("applied"), vector.path("name").asText());
            assertEquals(vector.get("expected"), actual.get("evidence"));
            if (!actual.path("applied").asBoolean()) { assertEquals(input.get("historical_evidence"), actual.get("evidence")); }
        }
    }
    @Test void allOriginalContinuationVectorsUseTheSamePrepareCallbackCompletePath() throws Exception {
        JsonNode golden = golden("marriagenotice"); var port = new MarriageWave3ProjectionCatalog.ContinuePort();
        for (JsonNode vector : golden.path("continue_cases")) {
            ObjectNode input = patch(golden.get("base_continue_request"), vector.get("patches"));
            ObjectNode classify = notice("classify"); classify.set("plan", input.get("plan"));
            assertEquals(vector.get("expected_blocked"), call(port, classify).get("blocked"));
            ObjectNode prepare = notice("prepare"); prepare.set("input", input); ObjectNode first = call(port, prepare);
            JsonNode actual;
            if (first.path("status").asText().equals("projection")) {
                assertEquals(1, vector.path("callback_calls").size(), vector.path("name").asText());
                assertEquals(vector.path("callback_calls").get(0), first.get("projection"));
                ObjectNode complete = notice("complete"); complete.set("input", input); complete.set("ordinary_plan", vector.get("ordinary_plan"));
                actual = call(port, complete).get("plan");
            } else {
                assertEquals("unchanged", first.path("status").asText());
                assertEquals(0, vector.path("callback_calls").size()); actual = first.get("plan");
            }
            assertEquals(vector.get("expected"), actual, vector.path("name").asText());
        }
    }
    @Test void originalFixedPairValueResultIsConsumedAsTheOriginalChoiceShape() throws Exception {
        JsonNode golden = golden("betrothalvalue"); var port = new MarriageWave3ProjectionCatalog.ValuePort();
        assertEquals(14, golden.path("original_tests_run").intValue());
        for (JsonNode vector : golden.path("cases")) {
            ObjectNode request = patch(golden.get("base_request"), vector.get("patches"));
            if (vector.path("expected_error").asBoolean()) { assertThrows(IllegalArgumentException.class, () -> call(port, request)); }
            else { assertEquals(patch(golden.get("base_expected"), vector.get("expected_patches")), call(port, request), vector.path("name").asText()); }
        }
    }
    @Test void originalFormalFrameRefusalIsExplicitDomainButWrongInputIsDecodeRejection() throws Exception {
        ObjectNode request = golden("betrothalvalue").get("base_request").deepCopy();
        ((ObjectNode) request.get("snapshot")).put("paused", false);
        var port = new MarriageWave3ProjectionCatalog.ValuePort();
        var input = port.decode(bytes(request));
        assertThrows(ProjectionDomainRejection.class, () -> port.project(input));
        request.put("schema", "unknown");
        assertThrows(IllegalArgumentException.class, () -> port.decode(bytes(request)));
    }
    private static ObjectNode pending(String stage, JsonNode request) {
        ObjectNode root = StrictJson.object(); root.put("schema", MarriageWave3ProjectionCatalog.PendingPort.SCHEMA);
        root.put("stage", stage); root.set("request", request); return root;
    }
    private static ObjectNode pointerPatch(JsonNode base, JsonNode changes) {
        ObjectNode result = base.deepCopy();
        for (JsonNode change : changes) {
            String path = change.path("path").asText(); int slash = path.lastIndexOf('/');
            ObjectNode parent = (ObjectNode) result.at(path.substring(0, slash)); String key = path.substring(slash + 1).replace("~1", "/").replace("~0", "~");
            if (change.path("op").asText().equals("remove")) { parent.remove(key); }
            else { parent.set(key, change.get("value").deepCopy()); }
        }
        return result;
    }
    private static JsonNode sorted(JsonNode node) {
        if (node.isObject()) {
            ObjectNode result = StrictJson.object(); TreeSet<String> keys = new TreeSet<>(); node.fieldNames().forEachRemaining(keys::add);
            keys.forEach(key -> result.set(key, sorted(node.get(key)))); return result;
        }
        if (node.isArray()) { ArrayNode result = new ArrayNode(com.fasterxml.jackson.databind.node.JsonNodeFactory.instance); node.forEach(item -> result.add(sorted(item))); return result; }
        return node;
    }
    @Test void pendingPreparationOnlyAsksForIdentityOnTheOriginalSameEpisodePath() throws Exception {
        JsonNode golden = golden("marriagepending"); var port = new MarriageWave3ProjectionCatalog.PendingPort();
        assertEquals(19, golden.path("cases").size());
        for (JsonNode vector : golden.path("cases")) {
            ObjectNode request = pointerPatch(golden.get("base_request"), vector.get("request_patch"));
            ObjectNode withoutLookup = request.deepCopy(); withoutLookup.putNull("bridge_identity");
            ObjectNode actual = call(port, pending("prepare", withoutLookup));
            if (actual.path("status").asText().equals("bridge_identity_required")) {
                assertFalse(request.get("bridge_identity").isNull(), "source fixture must provide actual identity only for this branch");
                actual = call(port, pending("complete", request));
            }
            assertEquals("applied", actual.path("status").asText()); actual.remove("status");
            String hash = HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes(sorted(actual))));
            assertEquals(vector.path("expected_sha256").asText(), hash, vector.path("name").asText());
            assertEquals(vector.get("expected_selected_step"), actual.path("planned").path("plan").get("selected_step"));
        }
    }
    @Test void completionCannotInventProcessIdentityOrRelaxClosedOperationFields() throws Exception {
        JsonNode source = golden("marriagepending").get("base_request"); var port = new MarriageWave3ProjectionCatalog.PendingPort();
        ObjectNode missingIdentity = source.deepCopy(); missingIdentity.putNull("bridge_identity");
        assertThrows(IllegalArgumentException.class, () -> call(port, pending("complete", missingIdentity)));
        ObjectNode unexpected = pending("prepare", source); unexpected.put("matched", true);
        assertThrows(IllegalArgumentException.class, () -> port.decode(bytes(unexpected)));
        ObjectNode wrong = notice("complete"); wrong.set("input", golden("marriagenotice").get("base_continue_request"));
        assertThrows(IllegalArgumentException.class, () -> new MarriageWave3ProjectionCatalog.ContinuePort().decode(bytes(wrong)));
    }
}
