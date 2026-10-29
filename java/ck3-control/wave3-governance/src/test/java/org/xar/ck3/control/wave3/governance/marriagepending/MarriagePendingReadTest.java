package org.xar.ck3.control.wave3.governance.marriagepending;

import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.cfg.JsonNodeFeature;
import com.fasterxml.jackson.databind.json.JsonMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.util.TreeSet;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.wave3.governance.marriagepending.MarriagePendingModel.*;

final class MarriagePendingReadTest {
    private static final JsonMapper JSON = JsonMapper.builder().enable(DeserializationFeature.USE_BIG_INTEGER_FOR_INTS, DeserializationFeature.USE_BIG_DECIMAL_FOR_FLOATS).disable(JsonNodeFeature.STRIP_TRAILING_BIGDECIMAL_ZEROES).build();
    @Test void actualPendingProducerPlannerAndHandoffDifferential() throws Exception {
        JsonNode golden = golden(); assertTrue(golden.path("source_refs_unchanged").asBoolean());
        assertFalse(golden.path("machine_id").asText().isBlank()); assertFalse(golden.path("observed_at_utc").asText().isBlank());
        assertEquals(19, golden.path("cases").size()); assertEquals(MarriagePendingConsumerPort.RESULT_STEP, golden.path("result_step").asText());
        JsonNode consumed = golden.path("consumer_evidence");
        assertEquals("executed", consumed.path("service_status").asText());
        assertEquals(MarriagePendingConsumerPort.RESULT_STEP, consumed.path("service_selected_step").asText());
        assertEquals("marriage", consumed.path("result_status").asText()); assertTrue(consumed.path("result_material_result").asBoolean());
        assertEquals(JSON.readTree("[\"result\"]"), consumed.path("native_test_seam_calls"));
        assertEquals(consumed.path("original_pending_sha256"), consumed.path("turn_record_pending_sha256"));
        assertEquals(consumed.path("original_pending_sha256"), consumed.path("resolved_source_pending_sha256"));
        for (JsonNode vector : golden.path("cases")) {
            ObjectNode request = patched(golden.path("base_request"), vector.path("request_patch"));
            byte[] actual = MarriagePendingConsumerPort.apply(raw(request)); JsonNode result = JSON.readTree(actual);
            assertEquals(vector.path("expected_sha256").asText(), sha(raw(sorted(result))), vector.path("name").asText());
            assertEquals(vector.get("expected_selected_step"), result.path("planned").path("plan").get("selected_step"));
            assertEquals(vector.path("expected_handled").asBoolean(), result.path("handled").asBoolean());
            Decision decision = MarriagePendingReadPolicy.decide(MarriagePendingConsumerPort.decode(raw(request)));
            if (decision instanceof ReadResult) { assertEquals(MarriagePendingConsumerPort.RESULT_STEP, result.path("planned").path("plan").path("selected_step").asText()); }
            assertFalse(result.path("planned").path("plan").path("selected_step").asText().startsWith("submit-"));
        }
    }
    @Test void rawFloatBooleanAndStringCannotBecomeRevisionOrPid() throws Exception {
        String base = golden().path("base_request").toString();
        for (String token : new String[]{"true", "7.0", "\"7\"", "-1", "18446744073709551616"}) {
            String value = base.replaceFirst("\"native_revision\"\\s*:\\s*7", "\"native_revision\":" + token); assertNotEquals(base, value);
            assertThrows(IllegalArgumentException.class, () -> MarriagePendingConsumerPort.apply(raw(value)), token);
        }
        for (String token : new String[]{"true", "55.0", "\"55\"", "0", "null"}) {
            String value = base.replaceFirst("\"pid\"\\s*:\\s*55", "\"pid\":" + token); assertNotEquals(base, value);
            assertThrows(IllegalArgumentException.class, () -> MarriagePendingConsumerPort.apply(raw(value)), token);
        }
        ObjectNode bad = (ObjectNode) golden().path("base_request").deepCopy(); ((ObjectNode) bad.path("ledger").path("pending")).putNull("last_checked_native_revision");
        assertThrows(IllegalArgumentException.class, () -> MarriagePendingConsumerPort.apply(raw(bad)));
        ObjectNode unknown = (ObjectNode) golden().path("base_request").deepCopy(); unknown.put("query_qualified", true);
        assertThrows(IllegalArgumentException.class, () -> MarriagePendingConsumerPort.apply(raw(unknown)));
    }
    @Test void processBirthAndFullRevisionDomainAreTypedAndSourceBound() throws Exception {
        ObjectNode request = (ObjectNode) golden().path("base_request").deepCopy();
        Inputs inputs = MarriagePendingConsumerPort.decode(raw(request)); assertInstanceOf(WaitLater.class, MarriagePendingReadPolicy.decide(inputs));
        ((ObjectNode) request.path("bridge_identity")).put("creation_date", "new-born-same-pid");
        ReadResult decision = assertInstanceOf(ReadResult.class, MarriagePendingReadPolicy.decide(MarriagePendingConsumerPort.decode(raw(request)))); assertTrue(decision.coldRecovery());
        assertThrows(IllegalArgumentException.class, () -> new Inputs(inputs.ledger(), null, inputs.frame(), inputs.currentProcess()));
    }
    @Test void originalSourceProvenanceRemainsAvailable() throws Exception {
        String configured = System.getenv("XAR_REPO_ROOT");
        if (configured == null || configured.isBlank()) { configured = System.getProperty("xar.repo"); }
        Path root;
        if (configured != null && !configured.isBlank()) {
            root = Path.of(configured).toAbsolutePath().normalize();
            assertTrue(Files.isRegularFile(root.resolve("AGENTS.md")), "configured original producer repository root required");
        } else {
            root = Path.of("..").toAbsolutePath().normalize();
            while (root != null && !Files.isRegularFile(root.resolve("AGENTS.md"))) { root = root.getParent(); }
        }
        assertNotNull(root);
        for (JsonNode ref : golden().path("source_refs")) { byte[] raw = Files.readAllBytes(root.resolve(ref.path("path").asText())); assertEquals(ref.path("bytes").asLong(), raw.length); assertEquals(ref.path("sha256").asText(), sha(raw)); }
    }
    private static JsonNode golden() throws IOException {
        try (var input = MarriagePendingReadTest.class.getResourceAsStream("/marriagepending/original-producer-golden.json")) {
            assertNotNull(input, "shared storage/M7 actual original golden required; missing capture cannot skip green"); byte[] raw = input.readAllBytes(); StrictJson.parse(raw, 131_072); return JSON.readTree(raw);
        }
    }
    private static ObjectNode patched(JsonNode base, JsonNode changes) {
        ObjectNode result = (ObjectNode) base.deepCopy();
        for (JsonNode change : changes) { String path = change.path("path").asText(); int slash = path.lastIndexOf('/'); ObjectNode parent = slash == 0 ? result : (ObjectNode) result.at(path.substring(0, slash)); String key = path.substring(slash+1); if ("remove".equals(change.path("op").asText())) { parent.remove(key); } else { parent.set(key, change.get("value").deepCopy()); } }
        return result;
    }
    private static JsonNode sorted(JsonNode value) {
        if (value.isObject()) { ObjectNode result = JSON.createObjectNode(); TreeSet<String> names = new TreeSet<>(); value.fieldNames().forEachRemaining(names::add); names.forEach(name -> result.set(name, sorted(value.get(name)))); return result; }
        if (value.isArray()) { ArrayNode result = JSON.createArrayNode(); value.forEach(item -> result.add(sorted(item))); return result; } return value.deepCopy();
    }
    private static byte[] raw(JsonNode value) { return raw(value.toString()); }
    private static byte[] raw(String value) { return value.getBytes(StandardCharsets.UTF_8); }
    private static String sha(byte[] raw) throws java.security.NoSuchAlgorithmException { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)); }
}
