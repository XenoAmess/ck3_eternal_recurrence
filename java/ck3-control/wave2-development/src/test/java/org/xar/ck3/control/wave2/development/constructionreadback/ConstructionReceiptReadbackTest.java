package org.xar.ck3.control.wave2.development.constructionreadback;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionError;
import org.xar.ck3.control.contracts.projection.ProjectionProtocolException;
import org.xar.ck3.control.wave2.development.constructionreadback.ConstructionReceiptReadback.CurrentProcess;
import org.xar.ck3.control.wave2.development.constructionreadback.ConstructionReceiptReadback.PriorityReason;
import org.xar.ck3.control.wave2.development.constructionreadback.ConstructionReceiptReadback.Scope;
import org.xar.ck3.control.wave2.development.constructionreadback.ConstructionReceiptReadback.Snapshot;

class ConstructionReceiptReadbackTest {
    @Test
    void originalFourFunctionClosureAndRealRetainedReceiptsMatch() throws IOException {
        JsonNode golden = golden();
        assertEquals("xar.ck3.constructionreadback-golden/v1", golden.path("schema").textValue());
        assertEquals("xenoamess-full-tower-eb9d2c1186", golden.path("machine_id").textValue());
        assertEquals("unknown", golden.path("fixture_original_machine_id").textValue());
        assertEquals(22, golden.path("cases").size());
        assertEquals(6, golden.path("extraction_scope").size());
        assertEquals("90ff70251640abd243bea7a0194f057ab80b719899569e4ca3feaf53c29b9e3e",
                golden.path("source_refs").get(0).path("sha256").textValue());
        assertEquals("5d29d19d44c83a5425fb75b97ddb118a6c51a1e1f1f98184570850ad94a6a582",
                golden.path("source_refs").get(1).path("sha256").textValue());
        for (JsonNode row : golden.path("cases")) {
            byte[] before = StrictJson.canonical(row);
            JsonNode actual = StrictJson.parse(ConstructionReadbackJson.project(request(row)));
            assertEquals(row.get("expected"), actual, row.path("name").textValue());
            assertEquals(StrictJson.parse(before), row, "caller source containers are not changed");
        }
    }

    @Test
    void originalWindowsCreationComparisonRetainsPrecisionOffsetAndRawEquality() throws IOException {
        JsonNode rows = golden().path("time_cases");
        assertEquals(9, rows.size());
        for (JsonNode row : rows) {
            boolean result = ConstructionReceiptReadback.sameProcess(new CurrentProcess(BigInteger.valueOf(7),
                    row.path("first").textValue()), new Scope(BigInteger.valueOf(7),
                    row.path("second").textValue(), null, null));
            assertEquals(row.path("expected").booleanValue(), result, row.path("name").textValue());
        }
        assertFalse(ConstructionReceiptReadback.sameProcess(new CurrentProcess(BigInteger.valueOf(8),
                "20261015102214.187404+480"), new Scope(BigInteger.valueOf(7),
                "20261015102214.187404+480", null, null)));
    }

    @Test
    void fullPassOrderingIsPreservedBeforeOldestFirstMonthlySelection() throws IOException {
        assertEquals(PriorityReason.PROCESS_OR_FRAME_RECHECK, reason(named("later-process-recheck-outranks-oldest-monthly-watch")));
        assertEquals(PriorityReason.COMPLETED_INCOME_OR_CASH, reason(named("completed-income-outranks-monthly-watch")));
        assertEquals(PriorityReason.COMPLETED_PROVINCE_RECHECK, reason(named("completed-province-outranks-incomplete-watch")));
        assertEquals(PriorityReason.MONTHLY_COMPLETION_WATCH, reason(named("oldest-applied-prior-wins")));
        JsonNode selected = StrictJson.parse(ConstructionReadbackJson.project(request(named("oldest-applied-prior-wins"))));
        assertEquals("A", selected.path("action_request_id").textValue());
    }

    @Test
    void explicitNullCheckDateSuppressesPostDateFallbackAndImmutableListsStayImmutable() throws IOException {
        assertTrue(StrictJson.parse(ConstructionReadbackJson.project(request(named("null-last-check-suppresses-fallback")))).isNull());
        JsonNode missing = StrictJson.parse(ConstructionReadbackJson.project(request(named("missing-last-check-falls-back"))));
        assertEquals("A", missing.path("action_request_id").textValue());
        var ledger = ConstructionReadbackJson.ledger(named("oldest-applied-prior-wins").get("ledger"));
        assertThrows(UnsupportedOperationException.class, () -> ledger.appliedPrior().clear());
        assertThrows(UnsupportedOperationException.class,
                () -> ConstructionReceiptReadback.appliedReceipts(ledger, "E").clear());
    }

    @Test
    void strictEntryRejectsBoolFloatAndStringSubstitutesWithoutTreeNormalization() throws IOException {
        String raw = new String(request(named("watch-due-at-720")), StandardCharsets.UTF_8);
        for (String token : new String[]{"true", "101.0", "\"101\""}) {
            String changed = raw.replace("\"pid\":101", "\"pid\":" + token);
            assertThrows(ContractViolationException.class, () -> ConstructionReadbackJson.project(utf8(changed)), token);
        }
        String scope = new String(request(named("readonly-observation-lease")), StandardCharsets.UTF_8);
        for (String token : new String[]{"false", "0.0", "\"0\""}) {
            String changed = scope.replace("\"native_submit_calls\":0", "\"native_submit_calls\":" + token);
            assertThrows(ContractViolationException.class, () -> ConstructionReadbackJson.project(utf8(changed)), token);
        }
        assertThrows(ContractViolationException.class, () -> ConstructionReadbackJson.project(utf8(
                scope.replace("\"read_only\":true", "\"read_only\":1"))));
    }

    @Test
    void wrapperAndRequiredCurrentProcessCannotBeForgedByMissingOrExtraFields() throws IOException {
        String raw = new String(request(named("watch-due-at-720")), StandardCharsets.UTF_8);
        assertThrows(ContractViolationException.class, () -> ConstructionReadbackJson.project(utf8(raw + " {}")));
        assertThrows(ContractViolationException.class, () -> ConstructionReadbackJson.project(utf8(
                raw.replaceFirst("\\{", "{\"unexpected\":true,"))));
        assertThrows(ContractViolationException.class, () -> ConstructionReadbackJson.project(utf8(
                raw.replaceFirst("\\{", "{\"operation\":\"priority\","))));
        ObjectNode missing = (ObjectNode) StrictJson.parse(utf8(raw));
        missing.remove("process_identity");
        assertThrows(ContractViolationException.class,
                () -> ConstructionReadbackJson.project(StrictJson.canonical(missing)));
        ObjectNode empty = (ObjectNode) StrictJson.parse(utf8(raw));
        ((ObjectNode) empty.get("process_identity")).put("creation_time", "");
        assertThrows(ContractViolationException.class,
                () -> ConstructionReadbackJson.project(StrictJson.canonical(empty)));
        ObjectNode absentProcess = (ObjectNode) StrictJson.parse(request(named("null-applied-and-empty-prior")));
        absentProcess.putNull("process_identity");
        assertTrue(StrictJson.parse(ConstructionReadbackJson.project(StrictJson.canonical(absentProcess))).isNull(),
                "an empty ledger needs no process probe in the original source");
        absentProcess.set("ledger", named("watch-due-at-720").get("ledger"));
        ProjectionProtocolException unavailable = assertThrows(ProjectionProtocolException.class,
                () -> ConstructionReadbackJson.project(StrictJson.canonical(absentProcess)));
        assertEquals(ProjectionError.Code.OPERATION_UNAVAILABLE, unavailable.code());
        assertThrows(ContractViolationException.class,
                () -> ConstructionReadbackJson.project(new byte[]{(byte) 0xc3, 0x28}));
    }

    @Test
    void extensibleReceiptFieldsAreReturnedWithoutInventingMaterialOrReplayCredit() throws IOException {
        String raw = new String(request(named("watch-due-at-720")), StandardCharsets.UTF_8);
        String extended = raw.replace("\"action_request_id\":\"A\"",
                "\"action_request_id\":\"A\",\"sdk_extension\":{\"decimal\":1.25,\"null\":null,\"empty\":[]}");
        JsonNode output = StrictJson.parse(ConstructionReadbackJson.project(utf8(extended)));
        assertEquals(StrictJson.parse(utf8(extended)).path("ledger").path("applied").path("sdk_extension"),
                output.get("sdk_extension"));
        assertFalse(output.has("replay_allowed"));
        assertFalse(output.has("material_postcondition_verified"));
        assertEquals("in_progress", output.path("completion_status").textValue());
    }

    private static PriorityReason reason(JsonNode row) {
        JsonNode snapshot = row.get("snapshot");
        JsonNode process = row.get("process_identity");
        return ConstructionReceiptReadback.priorityReceipt(ConstructionReadbackJson.ledger(row.get("ledger")),
                new Snapshot(snapshot.path("episode_run_id").textValue(), snapshot.path("native_revision").bigIntegerValue(),
                        snapshot.path("date_raw").bigIntegerValue()),
                Optional.of(new CurrentProcess(process.path("pid").bigIntegerValue(), process.path("creation_time").textValue())))
                .orElseThrow().reason();
    }

    private static byte[] request(JsonNode row) {
        ObjectNode request = (ObjectNode) row.deepCopy();
        request.remove("name");
        request.remove("expected");
        request.put("schema", ConstructionReadbackJson.SCHEMA);
        return StrictJson.canonical(request);
    }

    private static JsonNode named(String name) throws IOException {
        for (JsonNode row : golden().path("cases")) {
            if (name.equals(row.path("name").textValue())) { return row; }
        }
        throw new IllegalStateException("missing readback golden: " + name);
    }

    private static JsonNode golden() throws IOException {
        try (InputStream stream = ConstructionReceiptReadbackTest.class.getResourceAsStream("/constructionreadback/golden.json")) {
            assertNotNull(stream, "original readback producer capture is required");
            return StrictJson.parse(stream.readAllBytes());
        }
    }

    private static byte[] utf8(String value) { return value.getBytes(StandardCharsets.UTF_8); }
}
