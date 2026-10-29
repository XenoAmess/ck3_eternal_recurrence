package org.xar.ck3.control.wave3.governance.projection;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertInstanceOf;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.stream.Stream;
import java.util.stream.StreamSupport;
import org.junit.jupiter.api.DynamicTest;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestFactory;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionCall;
import org.xar.ck3.control.contracts.projection.ProjectionError;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.contracts.projection.ProjectionOperation;
import org.xar.ck3.control.contracts.projection.ProjectionResult;
import org.xar.ck3.control.contracts.projection.RegisteredProjection;
import org.xar.ck3.control.wave3.governance.crowncooldown.CrownCooldownCodec;

/** Actual registered decode/core/encode composition; no HTTP, native or SDK authority is claimed. */
final class GovernanceProjectionPortsTest {
    private static RegisteredProjection port(ProjectionOperation operation) {
        return new GovernanceWave3ProjectionCatalog().registrations().stream()
                .filter(entry -> entry.operation() == operation).findFirst().orElseThrow();
    }
    private static ProjectionResult call(ProjectionOperation operation, JsonNode payload) {
        return port(operation).execute(new ProjectionCall(new ProjectionCall.Identity("gov-port-test", operation),
                ProjectionJson.object(raw(payload), 65_536)));
    }
    private static JsonNode succeeded(ProjectionOperation operation, JsonNode payload) {
        ProjectionResult result = call(operation, payload);
        assertInstanceOf(ProjectionResult.Succeeded.class, result);
        return StrictJson.parse(((ProjectionResult.Succeeded) result).result().bytes());
    }
    private static ProjectionError.Code rejected(ProjectionOperation operation, JsonNode payload) {
        ProjectionResult result = call(operation, payload);
        assertInstanceOf(ProjectionResult.Rejected.class, result);
        return ((ProjectionResult.Rejected) result).error().code();
    }

    @TestFactory
    Stream<DynamicTest> allOriginalLiteralAndClockValuesPassTheRegisteredTypedBoundary() throws IOException {
        JsonNode golden = golden();
        assertEquals(23, golden.get("literal_cases").size());
        assertEquals(12, golden.get("clock_cases").size());
        Stream<DynamicTest> literals = stream(golden.get("literal_cases")).map(row -> DynamicTest.dynamicTest(
                "literal-" + row.get("name").textValue(), () -> assertEquals(row.get("expected"),
                        succeeded(ProjectionOperation.GOVERNANCE_CROWN_DURATION_SCALE, row.get("request")))));
        Stream<DynamicTest> fullClocks = stream(golden.get("clock_cases")).map(row -> DynamicTest.dynamicTest(
                "full-clock-" + row.get("name").textValue(), () -> assertEquals(row.get("expected"),
                        succeeded(ProjectionOperation.GOVERNANCE_CROWN_CLOCK_INTERPRET, row.get("request")))));
        Stream<DynamicTest> normalized = stream(golden.get("clock_cases")).map(row -> DynamicTest.dynamicTest(
                "normalized-clock-" + row.get("name").textValue(), () -> {
                    ObjectNode request = (ObjectNode) row.get("request").deepCopy();
                    request.remove("turn_tick_observation");
                    request.put("schema", CrownCooldownCodec.NORMALIZED_CLOCK_SCHEMA);
                    assertEquals(row.get("expected"),
                            succeeded(ProjectionOperation.GOVERNANCE_CROWN_NORMALIZED_CLOCK_INTERPRET, request));
                }));
        return Stream.of(literals, fullClocks, normalized).flatMap(value -> value);
    }

    @Test
    void integerTokenErrorsStayAtDecodeAndKnownNativeArithmeticRefusalIsExplicitDomainRejection() {
        ObjectNode literal = StrictJson.object().put("schema", CrownCooldownCodec.LITERAL_SCHEMA)
                .put("token_id", true).put("literal_i32", 3);
        assertEquals(ProjectionError.Code.INVALID_PAYLOAD,
                rejected(ProjectionOperation.GOVERNANCE_CROWN_DURATION_SCALE, literal));
        ObjectNode request = clock(false); ((ObjectNode) request.get("raw_observation")).put("remaining_raw", 11);
        assertEquals(ProjectionError.Code.DOMAIN_REJECTED,
                rejected(ProjectionOperation.GOVERNANCE_CROWN_NORMALIZED_CLOCK_INTERPRET, request));
    }

    @Test
    void normalizedHelperDoesNotSupplyTheFullQuerySameTickProof() {
        ObjectNode normalized = clock(true);
        assertTrue(succeeded(ProjectionOperation.GOVERNANCE_CROWN_NORMALIZED_CLOCK_INTERPRET, normalized)
                .get("calendar_deadline_ready").booleanValue());
        ObjectNode full = normalized.deepCopy();
        full.put("schema", CrownCooldownCodec.CLOCK_SCHEMA); full.putNull("turn_tick_observation");
        assertEquals(ProjectionError.Code.DOMAIN_REJECTED,
                rejected(ProjectionOperation.GOVERNANCE_CROWN_CLOCK_INTERPRET, full));
    }

    private static ObjectNode clock(boolean projected) {
        ObjectNode request = StrictJson.object().put("schema", CrownCooldownCodec.NORMALIZED_CLOCK_SCHEMA).put("date_raw", 1000);
        ObjectNode observation = request.putObject("raw_observation");
        observation.put("read_available", true).put("present", true).put("timed", true)
                .put("expiry_raw", 110).put("current_clock_raw", 100).put("remaining_raw", 10)
                .put("expiry_type", "signed32_scalar_clock_counter")
                .put("remaining_unit", projected ? "scalar_clock_step_calendar_projected" : "scalar_clock_step_calendar_unqualified");
        if (projected) { observation.put("retry_date_raw", 1120); } else { observation.putNull("retry_date_raw"); }
        return request;
    }
    private static JsonNode golden() throws IOException {
        try (InputStream input = GovernanceProjectionPortsTest.class.getResourceAsStream("/crowncooldown/original-producer-golden.json")) {
            assertNotNull(input, "actual complete original producer fixture is mandatory");
            byte[] raw = input.readNBytes(65_537); assertTrue(raw.length > 0 && raw.length <= 65_536);
            return StrictJson.parse(raw);
        }
    }
    private static Stream<JsonNode> stream(JsonNode rows) { return StreamSupport.stream(rows.spliterator(), false); }
    private static byte[] raw(JsonNode value) { return value.toString().getBytes(StandardCharsets.UTF_8); }
}
