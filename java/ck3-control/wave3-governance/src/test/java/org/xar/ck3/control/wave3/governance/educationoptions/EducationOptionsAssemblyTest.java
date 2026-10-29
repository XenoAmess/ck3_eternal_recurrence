package org.xar.ck3.control.wave3.governance.educationoptions;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionOperation;
import static org.junit.jupiter.api.Assertions.*;

/** Real registered domain codec/application/encoder against frozen original helpers and Service source spans. */
final class EducationOptionsAssemblyTest {
    private static final ObjectMapper JSON = new ObjectMapper().enable(DeserializationFeature.USE_BIG_INTEGER_FOR_INTS);
    private static final EducationOptionsProjectionPort PORT = new EducationOptionsProjectionPort();
    private static JsonNode golden() throws IOException {
        try (var input = EducationOptionsAssemblyTest.class.getResourceAsStream("/educationoptions/legacy-golden-v1.json")) {
            assertNotNull(input, "unchanged original helper and Service consumer capture is mandatory");
            return StrictJson.parse(input.readAllBytes(), 196_608);
        }
    }
    private static byte[] invoke(byte[] raw) { return PORT.encode(PORT.project(PORT.decode(raw))); }
    private static byte[] helper(String mode, JsonNode context) throws IOException {
        ObjectNode wrapper = StrictJson.object(); wrapper.put("schema", EducationOptionsOperation.SCHEMA).put("operation", mode);
        ObjectNode payload = wrapper.putObject("payload"); payload.set("context", context); payload.set("interaction_key", context.get("interaction_key")); payload.set("context_status", context.get("status"));
        return JSON.writeValueAsBytes(wrapper);
    }
    private static JsonNode bothHelpers(JsonNode context) throws IOException {
        ObjectNode projection = StrictJson.object();
        if (context.has("education_option_rows")) { projection.set("education_option_rows", JSON.readTree(invoke(helper("validate_rows", context)))); }
        if (context.has("education_request_materialization")) { projection.set("education_request_materialization", JSON.readTree(invoke(helper("validate_materialization", context)))); }
        return projection;
    }
    @Test void originalBothHelpersRunThroughTypedHostPortWithAllRawTokenCases() throws IOException {
        int count = 0, retained = 0;
        for (JsonNode sample : golden().path("cases")) {
            JsonNode context = JSON.readTree(sample.path("input_json").textValue()).get("context");
            if (sample.path("name").textValue().startsWith("retained-")) { retained++; assertTrue(sample.path("accepted").booleanValue()); }
            if (sample.path("name").textValue().equals("flag-float")) {
                assertTrue(new String(helper("validate_rows", context), StandardCharsets.UTF_8).contains("\"flag_full_u32\":1.0"), "raw negative float must reach the operation codec");
            }
            if (sample.path("accepted").booleanValue()) { assertEquals(sample.path("projection"), bothHelpers(context), sample.path("name").textValue()); }
            else { assertThrows(IllegalArgumentException.class, () -> bothHelpers(context), sample.path("name").textValue()); }
            count++;
        }
        assertTrue(count >= 25); assertEquals(6, retained);
    }
    @Test void originalServiceSelectedKeysAndAllOffAttemptConsumersCompareCompleteJson() throws IOException {
        JsonNode fixture = golden(); assertTrue(fixture.path("consumer_cases").isArray(), "source-bound actual consumer vectors are mandatory");
        assertTrue(fixture.path("consumer_cases").size() >= 13, "six retained and named independent consumer branches required");
        int retained = 0;
        for (JsonNode sample : fixture.get("consumer_cases")) {
            if (sample.path("name").textValue().startsWith("retained-")) { retained++; }
            byte[] raw = sample.path("input_json").textValue().getBytes(StandardCharsets.UTF_8);
            assertEquals(sample.get("expected"), JSON.readTree(invoke(raw)), sample.path("name").textValue());
        }
        assertEquals(6, retained);
        assertEquals("a8ebc680c41732a567eb1df2831fe210d7b0dc9f72f5418f1885f4b89a5e664e", fixture.path("original_Service_source_ref").path("sha256").textValue());
    }
    @Test void registrationCapsAndStrictModeBoundaryStayExplicit() {
        assertEquals(ProjectionOperation.EDUCATION_OPTIONS, PORT.operation());
        assertEquals(2_097_152, PORT.inputMaximumBytes()); assertEquals(2_097_152, PORT.outputMaximumBytes());
        assertThrows(IllegalArgumentException.class, () -> invoke("{\"schema\":\"xar.java.education-options.operation/v1\",\"operation\":\"unknown\",\"payload\":{}}".getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class, () -> invoke(new byte[2_097_153]));
        assertThrows(IllegalArgumentException.class, () -> invoke("{\"schema\":1,\"schema\":2}".getBytes(StandardCharsets.UTF_8)));
        assertThrows(org.xar.ck3.control.contracts.projection.ProjectionDomainRejection.class, () -> invoke("{\"schema\":\"xar.java.education-options.operation/v1\",\"operation\":\"request_attempts\",\"payload\":{\"observations\":[],\"ordered_observation_indices\":[0]}}".getBytes(StandardCharsets.UTF_8)));
    }
}
