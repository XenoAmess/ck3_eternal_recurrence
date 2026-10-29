package org.xar.ck3.control.wave2.finance.projection;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertInstanceOf;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.ServiceLoader;
import java.util.zip.GZIPInputStream;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionCall;
import org.xar.ck3.control.contracts.projection.ProjectionDispatcher;
import org.xar.ck3.control.contracts.projection.ProjectionError;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.contracts.projection.ProjectionOperation;
import org.xar.ck3.control.contracts.projection.ProjectionPortCatalog;
import org.xar.ck3.control.contracts.projection.ProjectionResult;
import org.xar.ck3.control.contracts.projection.ProjectionWire;
import org.xar.ck3.control.wave2.finance.holyloan.LoanFinancingCodec;
import org.xar.ck3.control.wave2.finance.rawcash.SdkProjectionJson;
import org.xar.ck3.control.wave2.finance.warcash.WarcashCodec;

final class FinanceProjectionPortTest {
    @Test void serviceLoadedWarcashPortCallsTheActualPolicyAndCheckedRequestsAreImmutable() throws Exception {
        byte[] raw = observedSingleRequest();
        ProjectionResult.Succeeded result = assertInstanceOf(ProjectionResult.Succeeded.class,
                dispatch(ProjectionOperation.WARCASH_EVALUATE, raw));
        assertArrayEquals(WarcashCodec.evaluate(raw), result.result().bytes());
        ObjectNode arguments = (ObjectNode) StrictJson.parse(raw).get("arguments");
        WarcashCodec.Request decoded = WarcashCodec.parse(raw);
        WarcashCodec.Request copied = new WarcashCodec.Request(decoded.operation(), arguments);
        arguments.removeAll(); copied.arguments().removeAll();
        assertEquals(StrictJson.parse(WarcashCodec.evaluate(raw)), WarcashCodec.evaluate(copied));
        assertThrows(IllegalArgumentException.class, () -> WarcashCodec.parse("{}".getBytes(StandardCharsets.UTF_8)));
    }

    @Test void floatingWarIdentitySurvivesTransportAndIsRejectedByTheRealIntegerDecoder() throws Exception {
        ObjectNode input = (ObjectNode) StrictJson.parse(observedSingleRequest());
        ((ObjectNode) input.get("arguments")).put("war_id", 1.0);
        byte[] raw = SdkProjectionJson.encode(input);
        assertTrue(new String(raw, StandardCharsets.UTF_8).contains("\"war_id\":1.0"));
        assertEquals("exact integer required; no boolean/float/string", assertThrows(
                org.xar.ck3.control.contracts.ContractViolationException.class, () -> WarcashCodec.evaluate(raw)).getMessage());
        ProjectionResult.Rejected result = assertInstanceOf(ProjectionResult.Rejected.class,
                dispatch(ProjectionOperation.WARCASH_EVALUATE, raw));
        assertEquals(ProjectionError.Code.DOMAIN_REJECTED, result.error().code());
    }

    @Test void optionalLoanNullAndRefusalRemainActualDomainValuesThroughTheSharedEnvelope() {
        byte[] absent = "{\"snapshot\":{},\"cash_resources\":null,\"cash_source_frame\":null}"
                .getBytes(StandardCharsets.UTF_8);
        ProjectionResult.Succeeded none = assertInstanceOf(ProjectionResult.Succeeded.class,
                dispatch(ProjectionOperation.HOLY_LOAN_PROJECT, absent));
        assertArrayEquals("null".getBytes(StandardCharsets.UTF_8), none.result().bytes());
        JsonNode envelope = StrictJson.parse(ProjectionWire.encodeResult(none));
        assertTrue(envelope.has("result") && envelope.get("result").isNull());
        byte[] refused = "{\"snapshot\":{},\"cash_resources\":{},\"cash_source_frame\":null}"
                .getBytes(StandardCharsets.UTF_8);
        ProjectionResult.Succeeded refusal = assertInstanceOf(ProjectionResult.Succeeded.class,
                dispatch(ProjectionOperation.HOLY_LOAN_PROJECT, refused));
        assertArrayEquals(LoanFinancingCodec.encode(LoanFinancingCodec.decodeAndProject(refused)), refusal.result().bytes());
        assertEquals("unavailable", StrictJson.parse(refusal.result().bytes()).path("status").textValue());
    }

    @Test void typedBoundariesRejectWrongShapesAndKeepRequestCopies() {
        byte[] wrongSnapshot = "{\"snapshot\":[],\"cash_resources\":null,\"cash_source_frame\":null}"
                .getBytes(StandardCharsets.UTF_8);
        ProjectionResult.Rejected invalid = assertInstanceOf(ProjectionResult.Rejected.class,
                dispatch(ProjectionOperation.HOLY_LOAN_PROJECT, wrongSnapshot));
        assertEquals(ProjectionError.Code.INVALID_PAYLOAD, invalid.error().code());
        ProjectionResult.Rejected incomplete = assertInstanceOf(ProjectionResult.Rejected.class,
                dispatch(ProjectionOperation.RAW_CASH_NORMALIZE, "{}".getBytes(StandardCharsets.UTF_8)));
        assertEquals(ProjectionError.Code.INVALID_PAYLOAD, incomplete.error().code());
        ObjectNode snapshot = StrictJson.object();
        LoanFinancingCodec.Request request = new LoanFinancingCodec.Request(snapshot,
                StrictJson.object().nullNode(), StrictJson.object().nullNode());
        snapshot.put("extension", true); ((ObjectNode) request.snapshot()).put("other", true);
        assertTrue(request.snapshot().isEmpty());
        assertInstanceOf(LoanFinancingCodec.NotProvided.class, LoanFinancingCodec.project(request));
    }

    private static ProjectionResult dispatch(ProjectionOperation operation, byte[] raw) {
        ProjectionDispatcher dispatcher = ProjectionDispatcher.fromCatalogs(ServiceLoader.load(ProjectionPortCatalog.class));
        ProjectionCall call = new ProjectionCall(new ProjectionCall.Identity("finance-port-test", operation),
                ProjectionJson.object(raw, ProjectionJson.MAX_BYTES));
        return dispatcher.dispatch(ProjectionWire.encodeCall(call));
    }

    private static byte[] observedSingleRequest() throws Exception {
        var stream = FinanceProjectionPortTest.class.getResourceAsStream("/warcash/original-v1.jsonl.gz");
        assertNotNull(stream, "actual original producer golden is required; missing data is not a skipped PASS");
        try (var reader = new BufferedReader(new InputStreamReader(new GZIPInputStream(stream), StandardCharsets.UTF_8))) {
            assertNotNull(reader.readLine(), "actual capture header required");
            String metadata;
            while ((metadata = reader.readLine()) != null) {
                JsonNode meta = StrictJson.parse(metadata.getBytes(StandardCharsets.UTF_8));
                String request = reader.readLine(), expected = reader.readLine();
                assertNotNull(request); assertNotNull(expected);
                JsonNode node = StrictJson.parse(request.getBytes(StandardCharsets.UTF_8));
                if ("result".equals(meta.path("expected_kind").textValue())
                        && WarcashCodec.REQUEST_SCHEMA.equals(node.path("schema").textValue())
                        && "observe_active_war_cash_resource_v1".equals(node.path("operation").textValue())) {
                    return request.getBytes(StandardCharsets.UTF_8);
                }
            }
        }
        throw new IllegalStateException("actual single-war producer vector is required");
    }
}
