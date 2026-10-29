package org.xar.ck3.control.wave2.planning.scoreinputs;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertInstanceOf;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.JsonNode;
import java.io.IOException;
import java.io.InputStream;
import java.util.List;
import java.util.ServiceLoader;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionCall;
import org.xar.ck3.control.contracts.projection.ProjectionError;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.contracts.projection.ProjectionOperation;
import org.xar.ck3.control.contracts.projection.ProjectionPortCatalog;
import org.xar.ck3.control.contracts.projection.ProjectionResult;
import org.xar.ck3.control.contracts.projection.RegisteredProjection;
import org.xar.ck3.control.wave2.finance.rawcash.SdkProjectionJson;

final class ScoreInputsProjectionCatalogTest {
    @Test void packagedDomainCatalogDiscoversOneCashOperationWithOriginalRoleBudgets() {
        List<ScoreInputsProjectionCatalog> providers = ServiceLoader.load(ProjectionPortCatalog.class).stream()
                .filter(provider -> provider.type().equals(ScoreInputsProjectionCatalog.class))
                .map(provider -> (ScoreInputsProjectionCatalog) provider.get()).toList();
        assertEquals(1, providers.size(), "real packaged descriptor is required");
        List<RegisteredProjection> registrations = providers.get(0).registrations();
        assertEquals(1, registrations.size());
        assertEquals(ProjectionOperation.SCORE_CASH_METRICS, registrations.getFirst().operation());
        assertEquals(65_536, registrations.getFirst().inputMaximumBytes());
        assertEquals(65_536, registrations.getFirst().outputMaximumBytes());
    }

    @Test void allOriginalCashProducerVectorsPassThroughTheRealTypedRegistration() throws IOException {
        JsonNode golden;
        try (InputStream input = getClass().getResourceAsStream("/scoreinputs/cash-producer-golden.json")) {
            assertNotNull(input, "actual original eight-test/twelve-case corpus is mandatory; never skipped");
            byte[] raw = input.readAllBytes();
            golden = StrictJson.parse(raw);
            CashMetricsGoldenCapture.validateOutput(raw, golden.path("machine_id").asText());
        }
        assertEquals(8, golden.path("original_test_count").intValue());
        assertEquals(0, golden.path("original_test_skipped").intValue());
        assertEquals(12, golden.path("cases").size());
        RegisteredProjection port = new ScoreInputsProjectionCatalog().registrations().getFirst();
        for (JsonNode row : golden.path("cases")) {
            byte[] raw = SdkProjectionJson.encode(row.get("request"));
            ProjectionCall call = new ProjectionCall(new ProjectionCall.Identity("cashmetrics-consumer:1",
                    ProjectionOperation.SCORE_CASH_METRICS), ProjectionJson.object(raw, 65_536));
            ProjectionResult result = port.execute(call);
            if (row.path("expected").path("status").textValue().equals("rejected")) {
                ProjectionResult.Rejected rejected = assertInstanceOf(ProjectionResult.Rejected.class, result, row.path("id").textValue());
                assertTrue(Set.of(ProjectionError.Code.INVALID_PAYLOAD, ProjectionError.Code.DOMAIN_REJECTED).contains(rejected.error().code()));
                assertEquals(call.identity(), rejected.identity().orElseThrow());
            } else {
                ProjectionResult.Succeeded succeeded = assertInstanceOf(ProjectionResult.Succeeded.class, result, row.path("id").textValue());
                assertEquals(row.path("expected").get("value"), StrictJson.parse(succeeded.result().bytes()), row.path("id").textValue());
                assertEquals(2, StrictJson.parse(succeeded.result().bytes()).size());
            }
        }
    }
}
