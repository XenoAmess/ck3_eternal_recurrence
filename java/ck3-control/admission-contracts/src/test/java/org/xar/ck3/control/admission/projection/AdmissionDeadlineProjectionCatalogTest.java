package org.xar.ck3.control.admission.projection;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertInstanceOf;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.ServiceLoader;
import java.util.stream.Stream;
import org.junit.jupiter.api.DynamicTest;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestFactory;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionCall;
import org.xar.ck3.control.contracts.projection.ProjectionDispatcher;
import org.xar.ck3.control.contracts.projection.ProjectionError;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.contracts.projection.ProjectionOperation;
import org.xar.ck3.control.contracts.projection.ProjectionPortCatalog;
import org.xar.ck3.control.contracts.projection.ProjectionResult;
import org.xar.ck3.control.contracts.projection.ProjectionWire;

final class AdmissionDeadlineProjectionCatalogTest {
    private static final JsonNode GOLDEN = loadGolden();

    @TestFactory Stream<DynamicTest> serviceLoadedActualProducerVectors() {
        List<DynamicTest> tests = new ArrayList<>();
        for (JsonNode entry : GOLDEN.get("cases")) {
            tests.add(DynamicTest.dynamicTest(entry.get("name").textValue(), () -> {
                ProjectionResult result = evaluate(entry);
                if (entry.at("/outcome/status").textValue().equals("rejected")) {
                    assertInstanceOf(ProjectionResult.Rejected.class, result);
                } else {
                    JsonNode observed = success(result);
                    if (entry.get("operation").textValue().startsWith("configure")) {
                        sameJson(GOLDEN.at("/configurations/" + entry.get("configuration_id").textValue() + "/configuration"),
                                observed.get("configuration"));
                        observed = observed.get("summary");
                    } else if (entry.get("operation").textValue().equals("no_configuration")) {
                        observed = observed.get("cap");
                    } else if (!entry.get("operation").textValue().equals("endpoint")) {
                        observed = observed.get("cap");
                    }
                    sameJson(entry.at("/outcome/value"), observed);
                }
            }));
        }
        assertEquals(24, tests.size(), "mandatory original producer corpus");
        return tests.stream();
    }

    @Test void profilesKeepFiniteOriginalBudgetsAndActualServiceProvider() {
        for (ProjectionOperation operation : List.of(ProjectionOperation.CAMPAIGN_DEADLINE_CONFIGURE,
                ProjectionOperation.CAMPAIGN_DEADLINE_CAP, ProjectionOperation.CAMPAIGN_DEADLINE_ENDPOINT)) {
            var profiles = dispatcher().profiles().stream().filter(profile -> profile.operation() == operation).toList();
            assertEquals(1, profiles.size());
            assertEquals(65_536, profiles.get(0).inputMaximumBytes());
            assertEquals(16_384, profiles.get(0).outputMaximumBytes());
            ProjectionResult.Rejected oversized = assertInstanceOf(ProjectionResult.Rejected.class,
                    dispatch(operation, bytes("{\"padding\":\"" + "x".repeat(65_536) + "\"}")));
            assertEquals(ProjectionError.Code.PAYLOAD_TOO_LARGE, oversized.error().code());
        }
    }

    @Test void originalRawFloatAndExponentTokensCannotBecomeIntegerOperands() {
        String raw = new String(StrictJson.canonical(capRequest()), StandardCharsets.UTF_8);
        for (String field : List.of("date_raw", "proposed_target_raw")) {
            long valid = field.equals("date_raw") ? 53_144_328 : 53_144_352;
            String marker = "\"" + field + "\":" + valid;
            assertTrue(raw.contains(marker));
            for (String invalid : List.of("true", valid + ".0", valid + "e0", "\"" + valid + "\"", "null")) {
                String bad = raw.replace(marker, "\"" + field + "\":" + invalid);
                assertTrue(bad.contains("\"" + field + "\":" + invalid));
                invalidPayload(ProjectionOperation.CAMPAIGN_DEADLINE_CAP, bytes(bad));
            }
        }
        String founding = "{\"founding\":{\"campaign_id\":\"software-fixture\",\"months\":360,"
                + "\"start_date\":\"1066.9.15\",\"start_date_raw\":53144328.0},\"previous_configuration\":null}";
        invalidPayload(ProjectionOperation.CAMPAIGN_DEADLINE_CONFIGURE, bytes(founding));
    }

    @Test void nativeExtensionsRemainExtensibleWithoutLaunderingSelectedFields() {
        ObjectNode request = capRequest();
        ((ObjectNode) request.get("starting")).put("native_cash_balance", 17.25);
        // JsonNode.toString retains the original decimal token; StrictJson canonical deliberately does not.
        JsonNode cap = success(dispatch(ProjectionOperation.CAMPAIGN_DEADLINE_CAP, bytes(request.toString()))).get("cap");
        assertEquals(53_144_352, cap.get("target_date_raw").intValue());
        ObjectNode endpoint = endpointRequest();
        ((ObjectNode) endpoint.get("starting")).put("native_cash_balance", 17.25);
        JsonNode result = success(dispatch(ProjectionOperation.CAMPAIGN_DEADLINE_ENDPOINT, bytes(endpoint.toString())));
        assertEquals(0, result.get("elapsed_days").intValue());
        assertTrue(result.get("actions").isEmpty());
        assertTrue(!result.get("calendar_progress_verified").booleanValue());
        assertTrue(!result.get("business_success_inferred").booleanValue());
    }

    @Test void exactOuterFieldsAndStoredScheduleCannotBeReplaced() {
        ObjectNode missing = capRequest(); missing.remove("configuration");
        invalidPayload(ProjectionOperation.CAMPAIGN_DEADLINE_CAP, StrictJson.canonical(missing));
        ObjectNode unknown = capRequest(); unknown.put("alias", "not accepted");
        invalidPayload(ProjectionOperation.CAMPAIGN_DEADLINE_CAP, StrictJson.canonical(unknown));
        ObjectNode forged = capRequest();
        ((ArrayNode) forged.at("/configuration/boundary_raws")).set(1, StrictJson.parse(bytes("53145072")));
        invalidPayload(ProjectionOperation.CAMPAIGN_DEADLINE_CAP, StrictJson.canonical(forged));
        ObjectNode absent = StrictJson.object();
        absent.putNull("configuration"); absent.putNull("starting"); absent.putNull("proposed_target_raw");
        assertTrue(success(dispatch(ProjectionOperation.CAMPAIGN_DEADLINE_CAP, StrictJson.canonical(absent))).get("cap").isNull());
    }

    @Test void endpointCannotGrantProgressFromAnAdvanceCapOrWrongSource() {
        ObjectNode request = endpointRequest();
        request.set("cap", success(dispatch(ProjectionOperation.CAMPAIGN_DEADLINE_CAP,
                StrictJson.canonical(capRequest()))).get("cap"));
        invalidPayload(ProjectionOperation.CAMPAIGN_DEADLINE_ENDPOINT, StrictJson.canonical(request));
        ObjectNode wrongDate = endpointRequest();
        ((ObjectNode) wrongDate.get("starting")).put("date_raw", 53_144_328);
        invalidPayload(ProjectionOperation.CAMPAIGN_DEADLINE_ENDPOINT, StrictJson.canonical(wrongDate));
    }

    private static ProjectionResult evaluate(JsonNode entry) {
        String operation = entry.get("operation").textValue();
        ObjectNode request = StrictJson.object();
        if (operation.startsWith("configure")) {
            request.set("founding", entry.get("founding")); request.set("previous_configuration", entry.get("prior_configuration"));
            return dispatch(ProjectionOperation.CAMPAIGN_DEADLINE_CONFIGURE, StrictJson.canonical(request));
        }
        if (operation.equals("no_configuration")) {
            request.putNull("configuration"); request.putNull("starting"); request.putNull("proposed_target_raw");
        } else {
            request.set("configuration", GOLDEN.at("/configurations/" + entry.get("configuration_id").textValue() + "/configuration"));
            request.set("starting", entry.get("starting")); request.set("proposed_target_raw", entry.get("proposed_target_raw"));
        }
        ProjectionResult capped = dispatch(ProjectionOperation.CAMPAIGN_DEADLINE_CAP, StrictJson.canonical(request));
        if (!operation.equals("endpoint") || capped instanceof ProjectionResult.Rejected) { return capped; }
        ObjectNode endpoint = StrictJson.object(); endpoint.set("starting", entry.get("starting"));
        endpoint.set("result_step", entry.get("result_step")); endpoint.set("cap", success(capped).get("cap"));
        return dispatch(ProjectionOperation.CAMPAIGN_DEADLINE_ENDPOINT, StrictJson.canonical(endpoint));
    }

    private static ObjectNode capRequest() {
        ObjectNode request = StrictJson.object(); request.set("configuration", GOLDEN.at("/configurations/main/configuration").deepCopy());
        request.putObject("starting").put("date_raw", 53_144_328); request.put("proposed_target_raw", 53_144_352); return request;
    }

    private static ObjectNode endpointRequest() {
        ObjectNode capInput = capRequest(); ((ObjectNode) capInput.get("starting")).put("date_raw", 53_407_128);
        capInput.put("proposed_target_raw", 53_407_152);
        ObjectNode request = StrictJson.object(); request.set("starting", capInput.get("starting")); request.put("result_step", "life-advance");
        request.set("cap", success(dispatch(ProjectionOperation.CAMPAIGN_DEADLINE_CAP, StrictJson.canonical(capInput))).get("cap"));
        return request;
    }

    private static void invalidPayload(ProjectionOperation operation, byte[] raw) {
        ProjectionResult.Rejected rejected = assertInstanceOf(ProjectionResult.Rejected.class, dispatch(operation, raw));
        assertEquals(ProjectionError.Code.INVALID_PAYLOAD, rejected.error().code());
    }
    private static void sameJson(JsonNode expected, JsonNode observed) { assertArrayEquals(StrictJson.canonical(expected), StrictJson.canonical(observed)); }
    private static JsonNode success(ProjectionResult result) {
        return StrictJson.parse(assertInstanceOf(ProjectionResult.Succeeded.class, result).result().bytes());
    }
    private static ProjectionDispatcher dispatcher() { return ProjectionDispatcher.fromCatalogs(ServiceLoader.load(ProjectionPortCatalog.class)); }
    private static ProjectionResult dispatch(ProjectionOperation operation, byte[] raw) {
        ProjectionCall call = new ProjectionCall(new ProjectionCall.Identity("deadline-port-test", operation), ProjectionJson.object(raw, ProjectionJson.MAX_BYTES));
        return dispatcher().dispatch(ProjectionWire.encodeCall(call));
    }
    private static JsonNode loadGolden() {
        try (InputStream input = AdmissionDeadlineProjectionCatalogTest.class.getResourceAsStream("/deadlinecredit/producer-golden.json")) {
            assertNotNull(input, "actual producer golden required; no skipped qualification"); return StrictJson.parse(input.readAllBytes());
        } catch (IOException error) { throw new IllegalStateException("cannot read actual deadline producer vectors", error); }
    }
    private static byte[] bytes(String value) { return value.getBytes(StandardCharsets.UTF_8); }
}
