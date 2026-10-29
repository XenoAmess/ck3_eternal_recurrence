package org.xar.ck3.control.wave2.development;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.zip.GZIPInputStream;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.projection.ProjectionCall;
import org.xar.ck3.control.contracts.projection.ProjectionError;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.contracts.projection.ProjectionOperation;
import org.xar.ck3.control.contracts.projection.ProjectionResult;
import org.xar.ck3.control.contracts.projection.RegisteredProjection;

/** Original bad tokens reach the actual catalog; only the reviewed input-validator calls become public refusals. */
final class ConstructionInputValidationTest {
    private static final ObjectMapper JSON = new ObjectMapper();

    @Test
    void identityTokensAndMissingSelectedFieldAreExplicitRefusals() {
        for (String token : List.of("true", "31254.0", "\"31254\"")) {
            rejected(ProjectionOperation.CONSTRUCTION_INTENT,
                    "{\"schema\":\"xar.ck3.construction-intent-java-request/v1\",\"operation\":\"consumed\",\"receipt\":{\"actor_character_id\":" + token + "}}");
        }
        rejected(ProjectionOperation.CONSTRUCTION_INTENT, """
                {"schema":"xar.ck3.construction-intent-java-request/v1","operation":"selected",
                 "selected_step":null,"pending_action":null,"typed_result":null}
                """);
    }

    @Test
    void immutableIncomePairAndMode3TargetRejectFloatingTokens() {
        rejected(ProjectionOperation.CONSTRUCTION_INCOME, """
                {"schema":"xar.ck3.construction-income-java-request/v1","operation":"receipt_income_sample",
                 "snapshot":{},"observation":[false,1.0],"prior_receipt":{},"cold_recheck":false,"completed":false}
                """);
        rejected(ProjectionOperation.CONSTRUCTION_INCOME, """
                {"schema":"xar.ck3.construction-income-java-request/v1","operation":"receipt_income_sample",
                 "snapshot":{},"observation":[false,1],"prior_receipt":{},"cold_recheck":false,"completed":false}
                """);
        rejected(ProjectionOperation.CONSTRUCTION_MODE3, """
                {"schema":"xar.construction-mode3-input.v1","world":{},"source_frame":{},
                 "build":{"game_version":"1.20.0.4","executable_sha256":"98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518"},
                 "barony_title_id":1.0,"province_id":1}
                """);
    }

    @Test
    void originalBudgetFixtureRejectsFloatingHorizonAtTheExactInputValidator() throws IOException {
        try (InputStream raw = ConstructionInputValidationTest.class.getResourceAsStream("/constructioneconomy/original-producer-golden.json.gz")) {
            assertNotNull(raw, "required actual original producer evidence is not a skip");
            try (GZIPInputStream input = new GZIPInputStream(raw)) {
                byte[] expanded = input.readNBytes(160_001);
                assertTrue(expanded.length <= 160_000);
                for (JsonNode vector : JSON.readTree(expanded).path("cases")) {
                    if (!"negative_net_raised_once".equals(vector.path("name").textValue())) { continue; }
                    ObjectNode request = ((ObjectNode) vector.get("request")).deepCopy();
                    request.put("schema", "xar.ck3.construction-monthly-budget-input.v1");
                    String body = JSON.writeValueAsString(request);
                    assertTrue(body.contains("\"horizon_months\":4"));
                    rejected(ProjectionOperation.CONSTRUCTION_ECONOMY_BUDGET,
                            body.replace("\"horizon_months\":4", "\"horizon_months\":1.0"));
                    return;
                }
                fail("the original budget input must be present");
            }
        }
    }

    @Test
    void theNarrowAdapterNeverConvertsOrdinaryAlgorithmOrIndexFailures() {
        IllegalArgumentException algorithm = new IllegalArgumentException("internal algorithm invariant");
        assertSame(algorithm, assertThrows(IllegalArgumentException.class,
                () -> ConstructionInputValidation.read(() -> { throw algorithm; })));
        IndexOutOfBoundsException indexing = new IndexOutOfBoundsException("internal indexing failure");
        assertSame(indexing, assertThrows(IndexOutOfBoundsException.class,
                () -> ConstructionInputValidation.check(() -> { throw indexing; })));
    }

    private static void rejected(ProjectionOperation operation, String body) {
        RegisteredProjection port = new ConstructionProjectionCatalog().registrations().stream()
                .filter(candidate -> candidate.operation() == operation).findFirst().orElseThrow();
        ProjectionCall.Identity identity = new ProjectionCall.Identity("construction-input-regression", operation);
        ProjectionResult.Rejected rejected = assertInstanceOf(ProjectionResult.Rejected.class, port.execute(
                new ProjectionCall(identity, ProjectionJson.object(body.getBytes(StandardCharsets.UTF_8), ProjectionJson.MAX_BYTES))));
        assertEquals(identity, rejected.identity().orElseThrow());
        assertEquals(ProjectionError.Code.DOMAIN_REJECTED, rejected.error().code());
    }
}
