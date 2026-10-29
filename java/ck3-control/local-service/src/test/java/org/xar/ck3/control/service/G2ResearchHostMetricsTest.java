package org.xar.ck3.control.service;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;

import java.nio.charset.StandardCharsets;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.metrics.BatchDecisionMetrics;
import org.xar.ck3.control.contracts.metrics.DecisionMetricRecorder;
import org.xar.ck3.control.contracts.metrics.DecisionMetrics;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.g2.common.G2Domain;
import org.xar.ck3.control.g2.common.G2Exception;
import org.xar.ck3.control.g2.common.G2HttpError;
import org.xar.ck3.control.g2.common.G2Request;
import org.xar.ck3.control.g2.common.G2ResearchEngine;
import org.xar.ck3.control.g2.common.G2Response;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.common.Milestone;

class G2ResearchHostMetricsTest {
    @Test void actualHostMeasuredRouteCarriesTheExistingResponseAndCompletePureMetrics() {
        G2ResearchHost host = host(input -> new G2Response(input.requestId(), input.milestone(), input.source(), input.payload()));
        G2Request input = request();
        G2ResearchHost.MeasuredEvaluation result = host.evaluateMeasured(input);
        assertEquals(input.requestId(), result.response().requestId());
        assertEquals(input.source(), result.response().source());
        assertEquals(WindowsJobProcess.currentMachineId(), result.metrics().context().machineId());
        assertEquals(1, result.metrics().requests().size());
        assertEquals(DecisionMetrics.Stage.DOMAIN_EVALUATION, result.metrics().requests().getFirst().spans().getFirst().stage());
        assertEquals(result.metrics(), BatchDecisionMetrics.decode(BatchDecisionMetrics.encode(result.metrics())));
        assertFalse(result.metrics().requests().getFirst().acknowledgements().isPresent());
        assertFalse(result.metrics().speedupClaimAllowed());
        assertEquals(result.response(), host.evaluate(input));
    }

    @Test void callerRetainedHostBatchPreservesOriginalDomainFailureAndCanReadUnknownTerminal() {
        G2ResearchHost host = host(input -> { throw new G2Exception(G2HttpError.Code.DOMAIN_REJECTED, "fixture"); });
        DecisionMetricRecorder.SystemClock clock = new DecisionMetricRecorder.SystemClock();
        assertThrows(IllegalArgumentException.class, () -> host.beginBatch(
                new BatchDecisionMetrics.Context("host-metrics-fixture", "host-test", "batch", clock.domainId()), clock));
        var batch = host.beginBatch(new BatchDecisionMetrics.Context(WindowsJobProcess.currentMachineId(), "host-test", "batch", clock.domainId()), clock);
        assertEquals(G2HttpError.Code.DOMAIN_REJECTED, assertThrows(G2Exception.class, () -> batch.evaluate(request())).code());
        var result = batch.finish();
        assertEquals(DecisionMetrics.Terminal.UNKNOWN, result.window().terminal());
        assertEquals(DecisionMetrics.Terminal.UNKNOWN, result.requests().getFirst().spans().getFirst().terminal());
        assertThrows(IllegalArgumentException.class, () -> batch.evaluate(request()));
    }

    private static G2ResearchHost host(java.util.function.Function<G2Request, G2Response> evaluate) {
        G2Domain domain = new G2Domain() {
            @Override public Milestone milestone() { return Milestone.M0; }
            @Override public G2Response evaluate(G2Request request) { return evaluate.apply(request); }
        };
        return new G2ResearchHost(new G2ResearchEngine(List.of(domain)));
    }
    private static G2Request request() {
        G2Source source = new G2Source("host-metrics-fixture", "2026-10-23T00:00:00Z", "synthetic-no-game",
                new ExactRef("D:/not-opened/host-metrics-fixture.json", 1, "1".repeat(64)));
        return new G2Request("host-metrics", Milestone.M0, source, ProjectionJson.object("{}".getBytes(StandardCharsets.UTF_8), 16));
    }
}
