package org.xar.ck3.control.wave2.runtime.decisionmetrics;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.net.SocketTimeoutException;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.OptionalLong;
import java.util.concurrent.atomic.AtomicInteger;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.metrics.DecisionMetricRecorder;
import org.xar.ck3.control.contracts.metrics.DecisionMetrics;
import org.xar.ck3.control.contracts.metrics.DecisionMetrics.Context;
import org.xar.ck3.control.contracts.metrics.DecisionMetrics.NativeObservation;
import org.xar.ck3.control.contracts.metrics.DecisionMetrics.SavedObservation;
import org.xar.ck3.control.contracts.metrics.DecisionMetrics.SavedWindow;
import org.xar.ck3.control.contracts.metrics.DecisionMetrics.Snapshot;
import org.xar.ck3.control.contracts.metrics.DecisionMetrics.Span;
import org.xar.ck3.control.contracts.metrics.DecisionMetrics.Stage;
import org.xar.ck3.control.contracts.metrics.DecisionMetrics.Terminal;
import org.xar.ck3.control.contracts.metrics.DecisionMetrics.Tick;
import org.xar.ck3.control.wave2.runtime.deadlinetransport.DeadlineTransport;
import org.xar.ck3.control.wave2.runtime.deadlinetransport.DeadlineTransportAdapter;
import org.xar.ck3.control.wave2.runtime.deadlinetransport.DeadlineTransportAdapter.OriginalDeadlineAuthority;
import org.xar.ck3.control.wave2.runtime.deadlinetransport.DeadlineTransportCodec;

/** Executes the real production adapter against the preserved original producer corpus, with zero native I/O. */
public final class DecisionMetricsRegression {
    private DecisionMetricsRegression() { }
    @FunctionalInterface private interface Checked { void run() throws Exception; }
    private static int checks;
    private static final String DOMAIN = "retained-test-jvm-domain";
    private static final String MACHINE = "synthetic-metrics-test-machine";
    private static final String SHA = "0".repeat(64);
    private static final Instant UTC = Instant.parse("2026-10-22T20:45:00Z");

    public static void main(String[] arguments) throws Exception { run(); }
    public static void run() throws Exception {
        checks = 0;
        roundtrip(); strictInputs(); clocks(); nativeSuccess(); originalTransportCorpusWithMetrics(); nativeUnknown(); nativeTimeout(); wrongRequest();
        persistence(); savedDays();
        System.out.println("DecisionMetricsRegression PASS " + checks + " checks; native=0 Driver=0 SAVE=0; complete-batch baseline unavailable");
    }
    private static void roundtrip() {
        long large = 9_007_199_254_740_993L;
        Span span = new Span(Stage.QUEUED, tick(large, UTC, OptionalLong.empty()), tick(large + 17, UTC.minusSeconds(2), OptionalLong.empty()), Terminal.RETURNED);
        Snapshot value = new Snapshot(context("request"), List.of(span), Optional.empty(), Optional.empty(), Optional.empty());
        Snapshot copy = DecisionMetrics.decode(DecisionMetrics.encode(value));
        check(copy.equals(value), "all typed fields roundtrip exactly"); check(copy.spans().get(0).wallNanos() == 17, "large decimal preserves one-nanosecond precision");
        check(copy.spans().get(0).utcRegressed(), "UTC rollback remains diagnostic"); check(copy.spans().get(0).cpuNanos().isEmpty(), "CPU unavailable is not zero");
        check(!copy.speedupClaimAllowed() && !copy.replayAllowed(), "request projection cannot grant speedup or replay");
    }
    private static void strictInputs() throws Exception {
        Snapshot empty = new Snapshot(context("request"), List.of(), Optional.empty(), Optional.empty(), Optional.empty());
        ObjectNode original = (ObjectNode) StrictJson.parse(DecisionMetrics.encode(empty));
        for (String field : List.of("spans", "acknowledgements", "native_observation", "saved_window")) {
            ObjectNode missing = original.deepCopy(); missing.remove(field); expect(IllegalArgumentException.class, () -> DecisionMetrics.decode(raw(missing)), "missing " + field);
        }
        ObjectNode unknown = original.deepCopy(); unknown.put("claimed_saved_days", 5);
        expect(IllegalArgumentException.class, () -> DecisionMetrics.decode(raw(unknown)), "unknown field");
        ObjectNode nullSpans = original.deepCopy(); nullSpans.putNull("spans");
        expect(IllegalArgumentException.class, () -> DecisionMetrics.decode(raw(nullSpans)), "null array differs from empty");
        Span span = new Span(Stage.QUEUED, tick(1, UTC, OptionalLong.empty()), tick(3, UTC, OptionalLong.empty()), Terminal.RETURNED);
        ObjectNode timed = (ObjectNode) StrictJson.parse(DecisionMetrics.encode(new Snapshot(context("request"), List.of(span), Optional.empty(), Optional.empty(), Optional.empty())));
        for (String token : List.of("true", "1", "1.0", "\"01\"", "null", "\"9223372036854775808\"")) {
            ObjectNode bad = timed.deepCopy(); ((ObjectNode) bad.at("/spans/0/began")).set("elapsed_nanos", StrictJson.parse(bytes(token)));
            expect(IllegalArgumentException.class, () -> DecisionMetrics.decode(raw(bad)), "invalid monotonic type/token " + token);
        }
        expect(IllegalArgumentException.class, () -> DecisionMetrics.decode(bytes("{\"schema\":\"x\",\"schema\":\"x\"}")), "duplicate field");
    }
    private static void clocks() throws Exception {
        expect(IllegalArgumentException.class, () -> new Span(Stage.QUEUED, tick(2, UTC, OptionalLong.empty()), tick(1, UTC, OptionalLong.empty()), Terminal.RETURNED), "monotonic rollback");
        expect(IllegalArgumentException.class, () -> new Span(Stage.DOMAIN_EVALUATION, tick(1, UTC, OptionalLong.of(4)), tick(2, UTC, OptionalLong.of(3)), Terminal.RETURNED), "CPU rollback");
        expect(IllegalArgumentException.class, () -> new Span(Stage.QUEUED, tick(1, UTC, OptionalLong.empty()),
                new Tick("other-jvm", 2, UTC, Thread.currentThread().threadId(), OptionalLong.empty()), Terminal.RETURNED), "cross JVM monotonic values");
        FakeClock clock = new FakeClock(); DecisionMetricRecorder recorder = recorder("request", clock);
        var queued = recorder.start(Stage.QUEUED); clock.nanos = 1000; recorder.finish(queued, Terminal.RETURNED);
        var evaluation = recorder.start(Stage.DOMAIN_EVALUATION); clock.nanos = 1030; clock.cpu = 5; recorder.finish(evaluation, Terminal.RETURNED);
        check(recorder.snapshot().spans().get(0).wallNanos() == 1000 && recorder.snapshot().spans().get(0).cpuNanos().orElseThrow() == 0, "queued wall and thread CPU separate");
        check(recorder.snapshot().spans().get(1).wallNanos() == 30 && recorder.snapshot().spans().get(1).cpuNanos().orElseThrow() == 5, "evaluation wall and CPU separate");
        expect(IllegalArgumentException.class, () -> recorder.finish(evaluation, Terminal.RETURNED), "stage cannot finish twice");
        var active = recorder.start(Stage.DOMAIN_EVALUATION);
        expect(IllegalArgumentException.class, recorder::snapshot, "incomplete stage not serialized"); clock.nanos = 100;
        expect(IllegalArgumentException.class, () -> recorder.finish(active, Terminal.RETURNED), "actual recorder rejects rollback");
    }
    private static void nativeSuccess() throws Exception {
        JsonNode row = originalCase("changed-speed-five-day");
        var request = DeadlineTransportCodec.prepare(raw(row.get("request")));
        FakeClock clock = new FakeClock(); var metrics = recorder(request.invocationId(), clock);
        var invocation = new DeadlineTransportAdapter.Invocation(request); AtomicInteger calls = new AtomicInteger();
        OriginalDeadlineAuthority authority = value -> {
            check(value == request, "measured original authority retains the identical prepared request");
            calls.incrementAndGet(); clock.nanos += 500; return raw(row.get("completion"));
        };
        DeadlineTransport.Observation observation = invocation.run(authority, metrics);
        check(invocation.state() == DeadlineTransportAdapter.State.OBSERVED && calls.get() == 1, "actual consumer calls original authority once");
        check(observation.completion().current().dateRaw() - request.starting().dateRaw() == 5 * 24, "original corpus validates five observed game days");
        var snapshot = metrics.snapshot(); NativeObservation nativeMetric = snapshot.nativeObservation().orElseThrow();
        check(nativeMetric.observedGameDays() == 5 && nativeMetric.savedDayCredit() == 0 && snapshot.savedWindow().isEmpty(), "observed days do not become saved days");
        check(nativeMetric.commandCount() == observation.completion().ownActions().size(), "actual native action count preserved separately");
        check(snapshot.spans().get(0).stage() == Stage.NATIVE_AUTHORITY && snapshot.spans().get(0).wallNanos() == 500, "original authority aggregate span measured");
        check(snapshot.spans().get(1).stage() == Stage.NATIVE_ACK_OBSERVATION && snapshot.spans().get(2).stage() == Stage.POSTSTATE_VALIDATION && snapshot.spans().get(3).stage() == Stage.GAME_DATE_OBSERVATION, "ACK/poststate/game-date stages distinct");
        check(DecisionMetrics.decode(DecisionMetrics.encode(snapshot)).equals(snapshot), "actual consumer metrics persisted JSON domain roundtrip");
        expect(IllegalStateException.class, () -> invocation.run(authority, metrics), "observed action cannot replay");
        check(calls.get() == 1, "measured observed replay never calls its original authority again");
    }
    private static void nativeUnknown() throws Exception {
        JsonNode row = originalCase("changed-speed-five-day"); var request = DeadlineTransportCodec.prepare(raw(row.get("request")));
        var metrics = recorder(request.invocationId(), new FakeClock()); var invocation = new DeadlineTransportAdapter.Invocation(request);
        AtomicInteger calls = new AtomicInteger();
        OriginalDeadlineAuthority authority = value -> {
            check(value == request, "unknown original authority retains the identical prepared request");
            calls.incrementAndGet(); ObjectNode completion = (ObjectNode) row.get("completion").deepCopy();
            ((ObjectNode) completion.get("current_frame")).put("paused", false); return raw(completion);
        };
        expect(DeadlineTransportAdapter.UnknownOutcomeException.class, () -> invocation.run(authority, metrics), "invalid actual poststate is UNKNOWN");
        check(invocation.state() == DeadlineTransportAdapter.State.UNKNOWN && metrics.snapshot().nativeObservation().isEmpty(), "ACK/return cannot grant native poststate or days");
        check(metrics.snapshot().spans().get(2).terminal() == Terminal.UNKNOWN, "failed poststate span retained");
        check(metrics.snapshot().acknowledgements().isPresent() && metrics.snapshot().spans().get(1).terminal() == Terminal.RETURNED, "returned ACKs retained independently of failed poststate");
        expect(IllegalStateException.class, () -> invocation.run(authority, metrics), "UNKNOWN action never replayed");
        check(calls.get() == 1, "no duplicate original authority call");
        expect(IllegalArgumentException.class, () -> new Snapshot(context("request"), List.of(), Optional.empty(), Optional.of(new NativeObservation(1, 1, 24, 48, SHA)), Optional.empty()), "raw ACK metric lacks validated poststate");
    }
    /** Both public invocation forms consume the same preserved production corpus; this form adds observations only. */
    private static void originalTransportCorpusWithMetrics() throws Exception {
        for (JsonNode row : originalCorpus().get("transport_cases")) {
            var request = DeadlineTransportCodec.prepare(raw(row.get("request")));
            var invocation = new DeadlineTransportAdapter.Invocation(request);
            var metrics = recorder(request.invocationId(), new FakeClock());
            AtomicInteger calls = new AtomicInteger(); boolean failed = row.at("/outcome/status").textValue().equals("failed");
            OriginalDeadlineAuthority authority = value -> {
                check(value == request, "whole original corpus retains the identical prepared request"); calls.incrementAndGet();
                if (failed) throw new IOException(row.at("/outcome/error").textValue());
                return raw(row.get("completion"));
            };
            if (failed) {
                expect(DeadlineTransportAdapter.UnknownOutcomeException.class, () -> invocation.run(authority, metrics),
                        "original corpus authority failure remains UNKNOWN with metrics");
                check(invocation.state() == DeadlineTransportAdapter.State.UNKNOWN && metrics.snapshot().nativeObservation().isEmpty(),
                        "failed original corpus cannot grant poststate or game-day observations");
            } else {
                var observed = invocation.run(authority, metrics);
                check(row.at("/outcome/value").equals(StrictJson.parse(DeadlineTransportCodec.encodeClock(observed.completion().clock()))),
                        "measured invocation preserves the whole original deadline observation " + row.get("id").textValue());
                check(invocation.state() == DeadlineTransportAdapter.State.OBSERVED && !observed.replayAllowed()
                                && !observed.nativeAdmissionGranted() && observed.savedDayCredit() == 0,
                        "metrics cannot broaden the original observation's permissions");
            }
            expect(IllegalStateException.class, () -> invocation.run(authority, metrics), "every original corpus invocation remains single use");
            check(calls.get() == 1, "whole original corpus calls its original authority exactly once");
            var snapshot = metrics.snapshot();
            check(snapshot.savedWindow().isEmpty() && DecisionMetrics.decode(DecisionMetrics.encode(snapshot)).equals(snapshot),
                    "every original corpus metric snapshot roundtrips without saved-day credit");
        }
    }
    private static void nativeTimeout() throws Exception {
        JsonNode row = originalCase("changed-speed-five-day"); var request = DeadlineTransportCodec.prepare(raw(row.get("request")));
        var metrics = recorder(request.invocationId(), new FakeClock()); var invocation = new DeadlineTransportAdapter.Invocation(request);
        AtomicInteger calls = new AtomicInteger();
        OriginalDeadlineAuthority authority = value -> {
            check(value == request, "timed-out original authority retains the identical prepared request");
            calls.incrementAndGet(); throw new SocketTimeoutException("synthetic original authority timeout");
        };
        expect(DeadlineTransportAdapter.UnknownOutcomeException.class, () -> invocation.run(authority, metrics), "native timeout retained as unknown effects");
        check(invocation.state() == DeadlineTransportAdapter.State.UNKNOWN && metrics.snapshot().spans().get(0).terminal() == Terminal.TIMED_OUT, "timeout duration distinct from effect outcome");
        check(metrics.snapshot().nativeObservation().isEmpty() && metrics.snapshot().savedWindow().isEmpty(), "timeout supplies neither game nor saved days");
        expect(IllegalStateException.class, () -> invocation.run(authority, metrics), "timed-out original invocation cannot replay");
        check(calls.get() == 1, "timeout has one original authority call despite unknown effects");
    }
    private static void wrongRequest() throws Exception {
        JsonNode row = originalCase("changed-speed-five-day"); var request = DeadlineTransportCodec.prepare(raw(row.get("request")));
        var invocation = new DeadlineTransportAdapter.Invocation(request); AtomicInteger calls = new AtomicInteger();
        OriginalDeadlineAuthority authority = value -> { calls.incrementAndGet(); return raw(row.get("completion")); };
        expect(IllegalArgumentException.class, () -> invocation.run(authority, recorder("wrong", new FakeClock())), "metrics identity bound before submission");
        check(calls.get() == 0 && invocation.state() == DeadlineTransportAdapter.State.PREPARED, "wrong identity never dispatches");
        expect(NullPointerException.class, () -> invocation.run(authority, null), "explicit measured invocation requires its typed recorder");
        check(calls.get() == 0 && invocation.state() == DeadlineTransportAdapter.State.PREPARED, "missing recorder grants no unmeasured fallback");
    }
    private static void persistence() throws Exception {
        for (int mode = 0; mode < 4; mode++) {
            var metrics = recorder("request", new FakeClock()); AtomicInteger writes = new AtomicInteger(); final int variant = mode;
            DecisionMetricRecorder.ExistingReceiptWriter writer = new DecisionMetricRecorder.ExistingReceiptWriter() {
                private byte[] stored;
                @Override public ExactRef writeMetrics(Snapshot snapshot) throws IOException {
                    writes.incrementAndGet(); stored = DecisionMetrics.encode(snapshot);
                    if (variant == 3) { throw new SocketTimeoutException("existing writer result unknown"); }
                    return new ExactRef("existing-producer-receipt", stored.length, DecisionMetricRecorder.sha256(stored));
                }
                @Override public byte[] readMetrics(ExactRef ref) throws IOException {
                    if (variant == 1) { return bytes("{}"); }
                    if (variant == 2) { throw new IOException("exact readback unavailable"); }
                    return stored.clone();
                }
            };
            if (mode == 0) { check(metrics.persist(writer).savedDayCredit() == 0, "exact persisted readback remains observational"); }
            else { expect(mode == 1 ? IllegalArgumentException.class : IOException.class, () -> metrics.persist(writer), "persistence failure cannot grant complete receipt"); }
            expect(IllegalArgumentException.class, () -> metrics.persist(writer), "persistence intent never auto-retried");
            check(writes.get() == 1, "one existing writer call only");
            check(metrics.snapshot().spans().get(0).stage() == Stage.PERSISTENCE, "persistence segment retained on actual local receipt");
            if (mode != 0) { check(metrics.snapshot().spans().get(0).terminal() != Terminal.RETURNED, "failed persistence has real terminal outcome"); }
        }
    }
    private static void savedDays() throws Exception {
        ExactRef first = new ExactRef("existing-canonical-proof-before", 1, SHA), second = new ExactRef("existing-canonical-proof-after", 1, SHA);
        SavedWindow window = new SavedWindow(new SavedObservation(MACHINE, 24, first, first), new SavedObservation(MACHINE, 72, second, second));
        check(window.observedSavedDays() == 2, "two verified saved dates separate from native observed five days");
        expect(IllegalArgumentException.class, () -> new SavedWindow(window.after(), window.before()), "saved date rollback rejected");
        expect(IllegalArgumentException.class, () -> new SavedWindow(window.before(), new SavedObservation("other-machine", 72, second, second)), "saved source machine binding");
        expect(IllegalArgumentException.class, () -> new SavedWindow(window.before(), new SavedObservation(MACHINE, 25, second, second)), "partial raw day rejected");
    }
    private static JsonNode originalCase(String id) throws IOException {
        for (JsonNode row : originalCorpus().get("transport_cases")) {
            if (id.equals(row.get("id").textValue())) return row;
        }
        throw new IOException("original corpus case missing: " + id);
    }
    private static JsonNode originalCorpus() throws IOException {
        try (InputStream source = DecisionMetricsRegression.class.getResourceAsStream("/deadlinetransport/producer-golden.json")) {
            if (source == null) { throw new IOException("preserved original producer corpus unavailable; cannot skip"); }
            byte[] bytes = source.readNBytes(196_609); StrictJson.require(bytes.length <= 196_608, "exact existing corpus budget");
            return StrictJson.parse(bytes, 196_608);
        }
    }
    private static Context context(String request) { return new Context(MACHINE, "retained-scope", "complete-batch-not-yet-measured", request, DOMAIN); }
    private static DecisionMetricRecorder recorder(String request, FakeClock clock) { return new DecisionMetricRecorder(context(request), clock); }
    private static Tick tick(long nanos, Instant utc, OptionalLong cpu) { return new Tick(DOMAIN, nanos, utc, Thread.currentThread().threadId(), cpu); }
    private static byte[] bytes(String text) { return text.getBytes(StandardCharsets.UTF_8); }
    private static byte[] raw(JsonNode value) { return value.toString().getBytes(StandardCharsets.UTF_8); }
    private static void check(boolean condition, String message) { if (!condition) { throw new IllegalStateException(message); } checks++; }
    private static void expect(Class<? extends Throwable> type, Checked action, String message) throws Exception {
        try { action.run(); } catch (Throwable failure) {
            if (type.isInstance(failure)) { checks++; return; }
            throw new IllegalStateException(message + ": wrong exception " + failure.getClass().getName(), failure);
        }
        throw new IllegalStateException(message + ": expected rejection");
    }
    private static final class FakeClock implements DecisionMetricRecorder.Clock {
        private long nanos; private long cpu;
        @Override public String domainId() { return DOMAIN; }
        @Override public Tick now() { return tick(nanos, UTC, OptionalLong.of(cpu)); }
    }
}

