package org.xar.ck3.control.wave2.governance.marriagehandoff;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.cfg.JsonNodeFeature;
import com.fasterxml.jackson.databind.json.JsonMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HexFormat;
import java.util.TreeSet;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.wave2.governance.marriagehandoff.MarriageHandoffModel.*;

final class MarriageEpisodeHandoffTest {
    private static final ObjectMapper JSON = JsonMapper.builder()
            .enable(DeserializationFeature.USE_BIG_INTEGER_FOR_INTS, DeserializationFeature.USE_BIG_DECIMAL_FOR_FLOATS)
            .disable(JsonNodeFeature.STRIP_TRAILING_BIGDECIMAL_ZEROES).build();
    private static final String RESOURCE = "/marriagehandoff/original-producer-golden.json";

    @Test void originalProducerAndSharedConsumerGolden() throws Exception {
        JsonNode golden = golden();
        assertEquals("xar.java-family-marriage-episode-handoff-original-golden/v1", golden.path("schema").asText());
        assertFalse(golden.path("machine_id").asText().isBlank());
        assertFalse(golden.path("observed_at_utc").asText().isBlank());
        assertTrue(golden.path("source_refs_unchanged").asBoolean());
        assertEquals(9, golden.path("consumer_modules").size());
        assertEquals(10, golden.path("cases").size());
        for (JsonNode vector : golden.path("cases")) {
            ObjectNode request = patched(golden.path("base_request"), vector.path("request_patch"));
            Reduction reduction = MarriageHandoffConsumerPort.prepareOriginalWriterUpdate(raw(request));
            JsonNode actual = JSON.readTree(MarriageHandoffCodec.encodeResult(reduction));
            assertEquals(vector.path("expected_sha256").asText(), sha(raw(sorted(actual))), vector.path("name").asText());
            assertEquals(vector.get("expected_receipt"), actual.get("receipt"), vector.path("name").asText());
            assertEquals(vector.path("write_required").asBoolean(), actual.path("write_required").asBoolean());
            if (reduction instanceof Archived archived) {
                assertFalse(archived.receipt().ck3CommandSubmitted());
                byte[] committed = MarriageHandoffConsumerPort.ledgerForExistingConsumers(
                        MarriageHandoffConsumerPort.revalidateOriginalWriterUpdate(archived, raw(request.get("ledger"))));
                Ledger roundTrip = MarriageHandoffCodec.decodeLedger(committed);
                assertEquals(archived.after(), roundTrip);
                assertInstanceOf(Unchanged.class, MarriageEpisodeHandoff.reduce(new Request(true, archived.receipt().handoff(), roundTrip)), "same predecessor cannot be archived twice");
            }
        }
    }

    @Test void provenanceBindsActualSourceFiles() throws Exception {
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
        assertNotNull(root, "repository root required for original producer provenance");
        for (JsonNode source : golden().path("source_refs")) {
            Path path = root.resolve(source.path("path").asText());
            assertEquals(source.path("bytes").asLong(), Files.size(path), path.toString());
            assertEquals(source.path("sha256").asText(), sha(Files.readAllBytes(path)), path.toString());
        }
    }

    @Test void strictEntryRejectsCoercedIdentityAndWrongFieldsBeforeReduction() throws Exception {
        String base = new String(raw(golden().path("base_request")), StandardCharsets.UTF_8);
        for (String token : new String[]{"true", "101.0", "\"101\"", "0", "4294967296", "null"}) {
            String changed = base.replaceFirst("\"predecessor_character_id\"\\s*:\\s*101", "\"predecessor_character_id\":" + token);
            assertNotEquals(base, changed);
            assertThrows(IllegalArgumentException.class, () -> MarriageHandoffConsumerPort.prepareOriginalWriterUpdate(raw(changed)), token);
        }
        ObjectNode wrong = (ObjectNode) golden().path("base_request").deepCopy(); wrong.put("unexpected", true);
        assertThrows(IllegalArgumentException.class, () -> MarriageHandoffConsumerPort.prepareOriginalWriterUpdate(raw(wrong)));
        ObjectNode missing = (ObjectNode) golden().path("base_request").deepCopy(); ((ObjectNode) missing.get("ledger")).remove("pending");
        assertThrows(IllegalArgumentException.class, () -> MarriageHandoffConsumerPort.prepareOriginalWriterUpdate(raw(missing)));
        ObjectNode nullHistory = (ObjectNode) golden().path("base_request").deepCopy(); ((ObjectNode) nullHistory.get("ledger")).putNull("episode_history");
        assertThrows(IllegalArgumentException.class, () -> MarriageHandoffConsumerPort.prepareOriginalWriterUpdate(raw(nullHistory)));
        assertThrows(IllegalArgumentException.class, () -> MarriageHandoffConsumerPort.prepareOriginalWriterUpdate(raw(base.substring(0, base.length()-1) + ",\"schema\":\"duplicate\"}")));
        for (String token : new String[]{"true", "7.0", "\"7\""}) {
            String changed = base.replaceFirst("\"pre_native_revision\"\\s*:\\s*7", "\"pre_native_revision\":" + token);
            assertNotEquals(base, changed);
            assertThrows(IllegalArgumentException.class, () -> MarriageHandoffConsumerPort.prepareOriginalWriterUpdate(raw(changed)), token);
        }
    }

    @Test void staleOriginalWriterUpdateRejectsLostPendingAndOrderDoesNotCreateFalseTamper() throws Exception {
        ObjectNode request = (ObjectNode) golden().path("base_request").deepCopy();
        Archived proposal = assertInstanceOf(Archived.class, MarriageHandoffConsumerPort.prepareOriginalWriterUpdate(raw(request)));
        ObjectNode changed = (ObjectNode) request.get("ledger").deepCopy();
        ((ObjectNode) changed.get("pending")).put("candidate_character_id", 999);
        assertThrows(IllegalArgumentException.class, () -> MarriageHandoffConsumerPort.revalidateOriginalWriterUpdate(proposal, raw(changed)));
        assertEquals(proposal.after(), MarriageHandoffConsumerPort.revalidateOriginalWriterUpdate(proposal, raw(sorted(request.get("ledger")))));
    }

    @Test void unknownRecordsStayUnresolvedAndDecimalExtensionPreservesJsonNumberKind() throws Exception {
        ObjectNode request = (ObjectNode) golden().path("base_request").deepCopy();
        ObjectNode pending = (ObjectNode) request.path("ledger").path("pending"); pending.put("status", "UNKNOWN"); pending.put("submission_state", "may_have_submitted");
        Archived proposal = assertInstanceOf(Archived.class, MarriageHandoffConsumerPort.prepareOriginalWriterUpdate(raw(request)));
        JsonNode result = JSON.readTree(MarriageHandoffCodec.encodeResult(proposal));
        JsonNode archived = result.path("ledger").path("episode_history").get(result.path("ledger").path("episode_history").size()-1);
        assertEquals(pending, archived.path("pending"));
        assertEquals("UNKNOWN", archived.path("pending").path("status").asText());
        assertFalse(result.path("receipt").path("ck3_command_submitted").asBoolean());
        String decimal = "{\"schema\":\"xar.ck3.first-heir-marriage-formal.v1\",\"pending\":null,\"resolved\":null,\"sdk_extension\":{\"decimal\":1.0}}";
        byte[] roundTrip = MarriageHandoffCodec.encodeLedger(MarriageHandoffCodec.decodeLedger(raw(decimal)));
        assertTrue(new String(roundTrip, StandardCharsets.UTF_8).contains("1.0"));
        assertTrue(JSON.readTree(roundTrip).path("sdk_extension").path("decimal").isFloatingPointNumber());
        String opaque = decimal.replace("\"decimal\":1.0", "\"status\":0,\"played_character_id\":1.0,\"episode_run_id\":[],\"material_result\":5");
        assertEquals(JSON.readTree(opaque), JSON.readTree(MarriageHandoffCodec.encodeLedger(MarriageHandoffCodec.decodeLedger(raw(opaque)))));
        String badRecord = decimal.replace("\"pending\":null", "\"pending\":{\"played_character_id\":1.0}");
        assertThrows(IllegalArgumentException.class, () -> MarriageHandoffCodec.decodeLedger(raw(badRecord)));
    }

    @Test void signedDeclaredHistoryPreservesNativeIdsWithoutRelaxingTypedHandoffRequests() throws Exception {
        ObjectNode ledger=JSON.createObjectNode().put("schema",LEDGER_SCHEMA);ledger.putNull("pending");ledger.putNull("resolved");
        ObjectNode entry=ledger.putArray("episode_history").addObject().put("source","committed_natural_successor_publication")
                .put("predecessor_character_id",101);
        for(long actor:new long[]{Integer.MIN_VALUE,-2,0,Integer.MAX_VALUE,4294967295L}) {
            entry.put("successor_character_id",actor);
            assertEquals(JSON.readTree(raw(ledger)),JSON.readTree(MarriageHandoffCodec.encodeLedger(MarriageHandoffCodec.decodeLedger(raw(ledger)))));
        }
        for(String token:new String[]{"true","1.0","\"-2\"","-1","-2147483649","4294967296"}) {
            entry.set("successor_character_id",JSON.readTree(token));
            assertThrows(IllegalArgumentException.class,()->MarriageHandoffCodec.decodeLedger(raw(ledger)),token);
        }
        ObjectNode request=(ObjectNode)golden().get("base_request").deepCopy();
        ((ObjectNode)request.get("handoff")).put("successor_character_id",-2);
        assertThrows(IllegalArgumentException.class,()->MarriageHandoffConsumerPort.prepareOriginalWriterUpdate(raw(request)));
    }

    private static JsonNode golden() throws IOException {
        try (var input = MarriageEpisodeHandoffTest.class.getResourceAsStream(RESOURCE)) {
            assertNotNull(input, "actual original-producer golden must be captured by storage/M7; missing evidence cannot skip green");
            byte[] raw = input.readAllBytes(); StrictJson.parse(raw, MarriageHandoffCodec.MAXIMUM_BYTES); return JSON.readTree(raw);
        }
    }
    private static ObjectNode patched(JsonNode base, JsonNode changes) {
        ObjectNode result = (ObjectNode) base.deepCopy();
        for (JsonNode change : changes) {
            String path = change.path("path").asText(); int slash = path.lastIndexOf('/');
            ObjectNode parent = slash == 0 ? result : (ObjectNode) result.at(path.substring(0, slash)); String field = path.substring(slash+1);
            if ("remove".equals(change.path("op").asText())) { parent.remove(field); }
            else { parent.set(field, change.get("value").deepCopy()); }
        }
        return result;
    }
    private static JsonNode sorted(JsonNode value) {
        if (value.isObject()) {
            ObjectNode result = JSON.createObjectNode(); TreeSet<String> names = new TreeSet<>(); value.fieldNames().forEachRemaining(names::add);
            names.forEach(name -> result.set(name, sorted(value.get(name)))); return result;
        }
        if (value.isArray()) { ArrayNode result = JSON.createArrayNode(); value.forEach(item -> result.add(sorted(item))); return result; }
        return value.deepCopy();
    }
    private static byte[] raw(JsonNode value) { return raw(value.toString()); }
    private static byte[] raw(String value) { return value.getBytes(StandardCharsets.UTF_8); }
    private static String sha(byte[] raw) throws NoSuchAlgorithmException { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)); }
}
