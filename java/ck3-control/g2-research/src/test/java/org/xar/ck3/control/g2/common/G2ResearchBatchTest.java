package org.xar.ck3.control.g2.common;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.OptionalLong;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.contracts.metrics.BatchDecisionMetrics;
import org.xar.ck3.control.contracts.metrics.DecisionMetricRecorder;
import org.xar.ck3.control.contracts.metrics.DecisionMetrics;
import org.xar.ck3.control.contracts.metrics.DecisionMetrics.Terminal;

class G2ResearchBatchTest {
    @Test void actualEngineBatchRetainsAdmissionAndInterRequestGapsAndSeparatesUnavailableBusinessObservations() {
        FakeClock clock = new FakeClock(); AtomicInteger calls = new AtomicInteger();
        G2ResearchBatch batch = batch(clock, input -> {
            calls.incrementAndGet(); clock.advance(20); return response(input);
        });
        clock.advance(10);
        G2ResearchBatch.Evaluation first = batch.evaluate(request("ordinary"));
        clock.advance(50);
        batch.evaluate(request("war"));
        clock.advance(30);
        BatchDecisionMetrics.Batch result = batch.finish();
        assertEquals(2, calls.get()); assertEquals(130, result.window().totalWallNanos());
        assertEquals(40, result.requests().stream().flatMap(value -> value.spans().stream()).mapToLong(DecisionMetrics.Span::wallNanos).sum());
        assertEquals(request("ordinary").source(), first.response().source());
        for (DecisionMetrics.Snapshot metrics : result.requests()) {
            assertEquals(List.of(DecisionMetrics.Stage.DOMAIN_EVALUATION), metrics.spans().stream().map(DecisionMetrics.Span::stage).toList());
            assertTrue(metrics.acknowledgements().isEmpty()); assertTrue(metrics.nativeObservation().isEmpty());
            assertTrue(metrics.savedWindow().isEmpty()); assertFalse(metrics.speedupClaimAllowed());
        }
        assertFalse(result.speedupClaimAllowed()); assertFalse(result.replayAllowed());
        assertEquals(result, BatchDecisionMetrics.decode(BatchDecisionMetrics.encode(result)));
        assertThrows(IllegalArgumentException.class, batch::finish);
        assertThrows(IllegalArgumentException.class, () -> batch.evaluate(request("third")));
    }

    @Test void actualIdentityMismatchPreservesUnknownStageAndOriginalFailureThenRefusesContinuation() {
        FakeClock clock = new FakeClock(); AtomicInteger calls = new AtomicInteger();
        G2ResearchBatch batch = batch(clock, input -> {
            calls.incrementAndGet(); clock.advance(7);
            return response(request("drifted"));
        });
        G2Exception failure = assertThrows(G2Exception.class, () -> batch.evaluate(request("original")));
        assertEquals(G2HttpError.Code.SOURCE_MISMATCH, failure.code());
        clock.advance(11); BatchDecisionMetrics.Batch metrics = batch.finish();
        assertEquals(Terminal.UNKNOWN, metrics.window().terminal()); assertEquals(18, metrics.window().totalWallNanos());
        assertEquals(Terminal.UNKNOWN, metrics.requests().getFirst().spans().getFirst().terminal());
        assertThrows(IllegalArgumentException.class, () -> batch.evaluate(request("original")));
        assertEquals(1, calls.get()); assertEquals(metrics, BatchDecisionMetrics.decode(BatchDecisionMetrics.encode(metrics)));
    }

    @Test void duplicateRequestNeverInvokesProducerTwiceAndPortableProvenanceDoesNotRelabelMeasurementMachine() {
        FakeClock clock = new FakeClock(); AtomicInteger calls = new AtomicInteger();
        G2ResearchBatch batch = batch(clock, input -> { calls.incrementAndGet(); return response(input); });
        batch.evaluate(request("same"));
        assertThrows(IllegalArgumentException.class, () -> batch.evaluate(request("same")));
        G2Source other = new G2Source("another-machine", source().observedAtUtc(), source().exactBuild(), source().sourceRef());
        var portable = batch.evaluate(new G2Request("other", Milestone.M0, other, json()));
        assertEquals(other, portable.response().source());
        assertEquals("metrics-fixture", portable.metrics().context().machineId());
        assertEquals(2, calls.get()); assertEquals(2, batch.finish().requests().size());
    }

    @Test void wireRequiresExactVersionFieldsAndDecimalStringsWithoutErasingNullOrUnknownObservations() {
        FakeClock clock = new FakeClock(); clock.value = 9_007_199_254_740_993L;
        G2ResearchBatch batch = batch(clock, G2ResearchBatchTest::response);
        batch.evaluate(request("large")); clock.advance(17);
        BatchDecisionMetrics.Batch original = batch.finish(); byte[] encoded = BatchDecisionMetrics.encode(original);
        assertEquals(original, BatchDecisionMetrics.decode(encoded));
        assertArrayEquals(encoded, BatchDecisionMetrics.encode(BatchDecisionMetrics.decode(encoded)));
        String text = new String(encoded, StandardCharsets.UTF_8);
        assertTrue(text.contains("\"elapsed_nanos\":\"9007199254740993\""));
        for (String invalid : List.of(text.replace("xar.batch-decision-metrics/v1", "xar.batch-decision-metrics/v0"),
                text.replace("\"elapsed_nanos\":\"9007199254740993\"", "\"elapsed_nanos\":9007199254740993"),
                text.replace("\"elapsed_nanos\":\"9007199254740993\"", "\"elapsed_nanos\":true"),
                text.replace("\"requests\":[", "\"extra\":null,\"requests\":["),
                text.replace("\"acknowledgements\":null,", ""),
                text.replace("\"saved_window\":null", "\"saved_window\":[]"))) {
            assertThrows(IllegalArgumentException.class, () -> BatchDecisionMetrics.decode(invalid.getBytes(StandardCharsets.UTF_8)));
        }
    }

    @Test void windowRejectsResetClockOutOfRangeStagesAndReturnedBatchHidingUnknownRequest() {
        FakeClock clock = new FakeClock(); G2ResearchBatch batch = batch(clock, G2ResearchBatchTest::response);
        clock.advance(20); batch.evaluate(request("one")); clock.advance(30);
        BatchDecisionMetrics.Batch original = batch.finish();
        var old = original.requests().getFirst(); var span = old.spans().getFirst();
        var unknown = new DecisionMetrics.Snapshot(old.context(), List.of(new DecisionMetrics.Span(span.stage(), span.began(), span.ended(), Terminal.UNKNOWN)),
                Optional.empty(), Optional.empty(), Optional.empty());
        assertThrows(IllegalArgumentException.class, () -> new BatchDecisionMetrics.Batch(original.context(), original.window(), List.of(unknown)));
        var reset = new DecisionMetrics.Tick("reset-domain", 0, Instant.EPOCH, Thread.currentThread().threadId(), OptionalLong.empty());
        assertThrows(IllegalArgumentException.class, () -> new BatchDecisionMetrics.Window(reset, original.window().ended(), Terminal.RETURNED));
        var lateBegin = new DecisionMetrics.Tick("clock", 21, Instant.EPOCH, Thread.currentThread().threadId(), OptionalLong.empty());
        assertThrows(IllegalArgumentException.class, () -> new BatchDecisionMetrics.Batch(original.context(),
                new BatchDecisionMetrics.Window(lateBegin, original.window().ended(), Terminal.RETURNED), original.requests()));
    }

    private static G2ResearchBatch batch(FakeClock clock, java.util.function.Function<G2Request, G2Response> evaluate) {
        G2Domain domain = new G2Domain() {
            @Override public Milestone milestone() { return Milestone.M0; }
            @Override public G2Response evaluate(G2Request request) { return evaluate.apply(request); }
        };
        return new G2ResearchBatch(new G2ResearchEngine(List.of(domain)),
                new BatchDecisionMetrics.Context("metrics-fixture", "g2-host-test", "retained-batch", clock.domainId()), clock);
    }
    private static G2Request request(String id) { return new G2Request(id, Milestone.M0, source(), json()); }
    private static G2Source source() {
        return new G2Source("metrics-fixture", "2026-10-23T00:00:00Z", "synthetic-no-game",
                new ExactRef("D:/not-opened/metrics-fixture.json", 1, "1".repeat(64)));
    }
    private static G2Response response(G2Request request) { return new G2Response(request.requestId(), request.milestone(), request.source(), json()); }
    private static ProjectionJson json() { return ProjectionJson.object("{}".getBytes(StandardCharsets.UTF_8), 16); }
    private static final class FakeClock implements DecisionMetricRecorder.Clock {
        private long value;
        @Override public String domainId() { return "clock"; }
        @Override public DecisionMetrics.Tick now() {
            return new DecisionMetrics.Tick(domainId(), value, Instant.EPOCH, Thread.currentThread().threadId(), OptionalLong.empty());
        }
        private void advance(long nanos) { value += nanos; }
    }
}
