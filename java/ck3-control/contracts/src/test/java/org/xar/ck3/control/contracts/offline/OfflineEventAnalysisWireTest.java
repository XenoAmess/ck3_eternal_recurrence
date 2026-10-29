package org.xar.ck3.control.contracts.offline;

import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import static org.xar.ck3.control.contracts.offline.OfflineEventAnalysisContract.*;
import static org.junit.jupiter.api.Assertions.*;

class OfflineEventAnalysisWireTest {
    private static ExactRef ref() { return new ExactRef(Path.of("captured-source.json").toAbsolutePath().toString(), 1, "a".repeat(64)); }
    private static String batch() {
        return "{\"schema\":\"" + BATCH_REQUEST_SCHEMA + "\",\"batch_id\":\"offline-1\",\"manifest_ref\":" + ref().toJson()
                + ",\"captured_refs\":[]}";
    }
    @Test void largerMetadataRoleDoesNotUseOrWidenOriginalDocumentLimits() {
        String expanded = "{ " + " ".repeat(1_048_576) + batch().substring(1);
        byte[] raw = expanded.getBytes(StandardCharsets.UTF_8);
        assertTrue(raw.length > StrictJson.EXPLICIT_MAX_BYTES); assertTrue(raw.length < MAX_METADATA_BYTES);
        assertEquals("offline-1", OfflineEventAnalysisWire.decodeBatch(raw).batchId());
        assertThrows(IllegalArgumentException.class, () -> StrictJson.parse(raw, StrictJson.EXPLICIT_MAX_BYTES));
        assertEquals(65536, StrictJson.INPUT_MAX_BYTES); assertEquals(1048576, StrictJson.EXPLICIT_MAX_BYTES);
        var oversized = assertThrows(OfflineEventAnalysisWire.InvalidRequest.class, () -> OfflineEventAnalysisWire.decodeBatch(new byte[MAX_METADATA_BYTES + 1]));
        assertTrue(oversized.oversized());
    }
    @Test void exactReferenceTokensAndAllRequiredFieldsAreValidatedBeforeDispatch() {
        for (String wrong : List.of("true", "1.0", "1e0", "\"1\"", "null", "-1", "9007199254740992")) {
            byte[] raw = batch().replace("\"bytes\":1", "\"bytes\":" + wrong).getBytes(StandardCharsets.UTF_8);
            assertThrows(OfflineEventAnalysisWire.InvalidRequest.class, () -> OfflineEventAnalysisWire.decodeBatch(raw));
        }
        for (String changed : List.of(batch().replace("\"captured_refs\":[]", "\"captured_refs\":null"),
                batch().replace("\"captured_refs\":[]", "\"extra\":false,\"captured_refs\":[]"),
                batch().replace("\"batch_id\":\"offline-1\"", "\"batch_id\":\"offline-1\",\"batch_id\":\"offline-1\""),
                batch().replace("offline-1", "../escape"))) {
            assertThrows(OfflineEventAnalysisWire.InvalidRequest.class, () -> OfflineEventAnalysisWire.decodeBatch(changed.getBytes(StandardCharsets.UTF_8)));
        }
        assertThrows(OfflineEventAnalysisWire.InvalidRequest.class, () -> OfflineEventAnalysisWire.decodeBatch(batch().getBytes(StandardCharsets.UTF_16LE)));
    }
    @Test void immutableCapturedInventoryAndErrorNullArePreservedOnWire() {
        List<ExactRef> original = new ArrayList<>(List.of(ref()));
        var result = new CaptureResult("capture-1", original); original.clear();
        var encoded = OfflineEventAnalysisWire.parseMetadataObject(OfflineEventAnalysisWire.encode(result));
        assertEquals(ref(), ExactRef.fromJson(encoded.path("source_refs").get(0)));
        assertThrows(UnsupportedOperationException.class, () -> result.sourceRefs().clear());
        var error = new OfflineEventAnalysisContract.Error(Optional.empty(), ErrorCode.INVALID_REQUEST, "invalid request");
        var rejected = OfflineEventAnalysisWire.parseMetadataObject(OfflineEventAnalysisWire.encode(error));
        StrictJson.object(rejected, java.util.Set.of("schema", "batch_id", "code", "message"));
        assertEquals(ERROR_SCHEMA, rejected.path("schema").textValue());
        assertEquals("invalid-request", rejected.path("code").textValue());
        assertEquals("invalid request", rejected.path("message").textValue());
        assertTrue(rejected.has("batch_id")); assertTrue(rejected.get("batch_id").isNull());
    }
    @Test void realDomainResultConsumerRetainsOpaqueDecimalAndUnicodeBytes() {
        String result = "{\"schema\":\"" + BATCH_RESULT_SCHEMA + "\",\"batch_id\":\"batch-1\",\"machine_id\":\"fixture-machine\",\"observed_at_utc\":\"2026-10-22T17:00:00Z\","
                + "\"idempotent\":true,\"report_ref\":" + ref().toJson() + ",\"report\":{\"decimal\":1.0,\"exponent\":0e0,\"text\":\"汉🙂\"},\"outputs\":[],\"grants_manifest\":"
                + "{\"path\":" + ref().toJson().get("path") + ",\"bytes\":1,\"sha256\":\"" + "a".repeat(64) + "\",\"grants\":0,\"added\":0},\"Game_MCP_OBS_calls\":0,\"timeline_writer_calls\":0}";
        byte[] raw = result.getBytes(StandardCharsets.UTF_8);
        assertArrayEquals(raw, OfflineEventAnalysisWire.validateBatchResult(raw, "batch-1"));
        assertThrows(IllegalArgumentException.class, () -> OfflineEventAnalysisWire.validateBatchResult(raw, "another-batch"));
        assertThrows(IllegalArgumentException.class, () -> OfflineEventAnalysisWire.validateBatchResult(result.replace("\"Game_MCP_OBS_calls\":0", "\"Game_MCP_OBS_calls\":true").getBytes(StandardCharsets.UTF_8), "batch-1"));
    }
}
