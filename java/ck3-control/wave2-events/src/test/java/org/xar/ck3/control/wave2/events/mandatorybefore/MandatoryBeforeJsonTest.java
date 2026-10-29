package org.xar.ck3.control.wave2.events.mandatorybefore;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.wave2.events.mandatorybefore.MandatoryBeforeModel.*;

import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.zip.GZIPInputStream;
import java.util.stream.Stream;
import java.util.stream.StreamSupport;
import org.junit.jupiter.api.DynamicTest;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestFactory;
import org.xar.ck3.control.wave2.events.choiceplanning.ChoicePlanningJson;

final class MandatoryBeforeJsonTest {
    private static final ObjectMapper JSON = new ObjectMapper().enable(DeserializationFeature.USE_BIG_INTEGER_FOR_INTS);
    @TestFactory Stream<DynamicTest> unchangedActualPlannerAndBeforeWriterProducer() throws IOException {
        JsonNode golden = golden(); assertEquals(14, golden.path("cases").size());
        return StreamSupport.stream(golden.path("cases").spliterator(), false).map(row -> DynamicTest.dynamicTest(row.path("name").textValue(), () -> {
            byte[] request = JSON.writeValueAsBytes(row.get("request"));
            if (row.path("rejected").booleanValue()) { assertThrows(IllegalArgumentException.class, () -> MandatoryBeforeJson.produce(request)); }
            else { assertEquals(row.get("output"), JSON.readTree(MandatoryBeforeJson.produce(request))); }
        }));
    }
    @Test void proposalIsDetachedAndDoesNotAuthorizeWriteSubmitOrReplay() throws IOException {
        ObjectNode request = request(); Input input = MandatoryBeforeJson.decode(JSON.writeValueAsBytes(request));
        BeforeBody body = new BeforeBody(input); assertFalse(body.persistenceCommitted()); assertFalse(body.actionAuthorized());
        assertFalse(body.dispatchAttempted()); assertFalse(body.replayAllowed()); assertTrue(body.offlineFollowupRequired());
        ((ObjectNode) request.get("planned")).put("snapshot_id", "changed-after-decode");
        JsonNode encoded = JSON.readTree(MandatoryBeforeJson.encode(body));
        assertEquals("native:100", encoded.path("frame_binding").path("snapshot_id").textValue());
    }
    @Test void actualJavaPlannerOutputFeedsBeforeConsumerWithoutInventingAWriteReceipt() throws IOException {
        JsonNode plannerGolden;
        try (InputStream resource = MandatoryBeforeJsonTest.class.getResourceAsStream("/choiceplanning/producer-golden-v1.json.gz")) {
            if (resource == null) { throw new IOException("actual planner producer fixture required for consumer integration"); }
            try (InputStream input = new GZIPInputStream(resource)) {
                byte[] raw = input.readNBytes(102_401); if (raw.length > 102_400) { throw new IOException("planner fixture decompression bound"); }
                plannerGolden = JSON.readTree(raw);
            }
        }
        JsonNode actualPlannerRequest = null;
        for (JsonNode row : plannerGolden.path("cases")) {
            if ("actual_native_catalogue_order".equals(row.path("name").textValue())) { actualPlannerRequest = row.get("request"); }
        }
        assertNotNull(actualPlannerRequest, "the actual unchanged old planner sample must exist");
        JsonNode actualJavaPlan = JSON.readTree(ChoicePlanningJson.plan(JSON.writeValueAsBytes(actualPlannerRequest)));
        ObjectNode beforeRequest = request();
        assertEquals(beforeRequest.path("planned").get("plan"), actualJavaPlan, "both actual producers use the same original query/frame");
        ((ObjectNode) beforeRequest.get("planned")).set("plan", actualJavaPlan);
        BeforeBody body = new BeforeBody(MandatoryBeforeJson.decode(JSON.writeValueAsBytes(beforeRequest)));
        assertEquals(golden().path("cases").get(0).get("output"), JSON.readTree(MandatoryBeforeJson.encode(body)));
        assertFalse(body.persistenceCommitted()); assertFalse(body.actionAuthorized()); assertFalse(body.dispatchAttempted());
    }
    @Test void rawFloatOrBooleanFrameAndIdentityDoNotRoundTripAsIntegers() throws IOException {
        String original = JSON.writeValueAsString(request());
        for (String token : new String[] {"true", "20.0"}) {
            String invalid = original.replace("\"revision\":20", "\"revision\":" + token);
            assertNotEquals(original, invalid); assertThrows(IllegalArgumentException.class, () -> MandatoryBeforeJson.decode(invalid.getBytes(StandardCharsets.UTF_8)));
        }
        String invalidIdentity = original.replace("\"choice_id\":\"first-enabled\"", "\"choice_id\":true");
        assertThrows(IllegalArgumentException.class, () -> MandatoryBeforeJson.decode(invalidIdentity.getBytes(StandardCharsets.UTF_8)));
    }
    @Test void wrapperUnknownAndDuplicateKeysFailBeforeAnyConsumerCall() throws IOException {
        ObjectNode unknown = request(); unknown.put("authorization_pass", true);
        assertThrows(IllegalArgumentException.class, () -> MandatoryBeforeJson.decode(JSON.writeValueAsBytes(unknown)));
        String valid = JSON.writeValueAsString(request());
        assertThrows(IllegalArgumentException.class, () -> MandatoryBeforeJson.decode(("{\"schema\":\"duplicate\"," + valid.substring(1)).getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class, () -> MandatoryBeforeJson.decode((valid + " null").getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class, () -> MandatoryBeforeJson.decode(new byte[] {(byte) 0xc3, 0x28}));
    }
    private static JsonNode golden() throws IOException {
        try (InputStream resource = MandatoryBeforeJsonTest.class.getResourceAsStream("/mandatorybefore/producer-golden-v1.json.gz")) {
            if (resource == null) { throw new IOException("actual before-writer golden has not been captured"); }
            try (InputStream input = new GZIPInputStream(resource)) {
                byte[] raw = input.readNBytes(524_289); if (raw.length > 524_288) { throw new IOException("bounded golden decompression exceeded"); }
                return JSON.readTree(raw);
            }
        }
    }
    private static ObjectNode request() throws IOException { return (ObjectNode) golden().path("cases").get(0).get("request").deepCopy(); }
}
