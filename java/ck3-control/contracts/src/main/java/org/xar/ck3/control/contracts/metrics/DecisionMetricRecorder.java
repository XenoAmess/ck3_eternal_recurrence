package org.xar.ck3.control.contracts.metrics;

import java.io.IOException;
import java.lang.management.ManagementFactory;
import java.lang.management.ThreadMXBean;
import java.net.SocketTimeoutException;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HexFormat;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.OptionalLong;
import java.util.UUID;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.metrics.DecisionMetrics.Context;
import org.xar.ck3.control.contracts.metrics.DecisionMetrics.Acknowledgements;
import org.xar.ck3.control.contracts.metrics.DecisionMetrics.NativeObservation;
import org.xar.ck3.control.contracts.metrics.DecisionMetrics.SavedWindow;
import org.xar.ck3.control.contracts.metrics.DecisionMetrics.Snapshot;
import org.xar.ck3.control.contracts.metrics.DecisionMetrics.Span;
import org.xar.ck3.control.contracts.metrics.DecisionMetrics.Stage;
import org.xar.ck3.control.contracts.metrics.DecisionMetrics.Terminal;
import org.xar.ck3.control.contracts.metrics.DecisionMetrics.Tick;

/** Thread-confined observer. No file path, native client, dispatcher, ledger or persistence authority is created. */
public final class DecisionMetricRecorder {
    public interface Clock { String domainId(); Tick now(); }
    @FunctionalInterface public interface Operation<T> { T run() throws IOException, InterruptedException; }
    /** The original receipt producer supplies its existing writer and exact readback route. */
    public interface ExistingReceiptWriter {
        ExactRef writeMetrics(Snapshot snapshot) throws IOException;
        byte[] readMetrics(ExactRef reference) throws IOException;
    }
    public record Persisted(Snapshot snapshot, ExactRef existingReceipt) {
        public Persisted { Objects.requireNonNull(snapshot); Objects.requireNonNull(existingReceipt); }
        public int savedDayCredit() { return 0; }
    }
    public static final class Token {
        private final DecisionMetricRecorder recorder;
        private final Stage stage;
        private final Tick began;
        private boolean completed;
        private Token(DecisionMetricRecorder recorder, Stage stage, Tick began) { this.recorder = recorder; this.stage = stage; this.began = began; }
    }
    public static final class SystemClock implements Clock {
        private final String domain = UUID.randomUUID().toString();
        private final long origin = System.nanoTime();
        private final Thread owner = Thread.currentThread();
        private final ThreadMXBean bean = ManagementFactory.getThreadMXBean();
        @Override public String domainId() { return domain; }
        @Override public Tick now() {
            StrictJson.require(Thread.currentThread() == owner, "metrics CPU clock belongs to retained owner thread");
            long cpu = bean.isCurrentThreadCpuTimeSupported() && bean.isThreadCpuTimeEnabled() ? bean.getCurrentThreadCpuTime() : -1;
            return new Tick(domain, System.nanoTime() - origin, Instant.now(), owner.threadId(), cpu < 0 ? OptionalLong.empty() : OptionalLong.of(cpu));
        }
    }
    private final Context context;
    private final Clock clock;
    private final Thread owner = Thread.currentThread();
    private final List<Span> spans = new ArrayList<>();
    private Optional<Acknowledgements> acknowledgements = Optional.empty();
    private Optional<NativeObservation> nativeObservation = Optional.empty();
    private Optional<SavedWindow> savedWindow = Optional.empty();
    private Token active;
    private long lastTick = -1;
    private boolean persistenceAttempted;

    public DecisionMetricRecorder(Context context, Clock clock) {
        this.context = Objects.requireNonNull(context); this.clock = Objects.requireNonNull(clock);
        StrictJson.require(context.clockDomainId().equals(clock.domainId()), "actual local clock domain must match metric context");
    }
    public Context context() { owner(); return context; }
    public Token start(Stage stage) {
        owner(); StrictJson.require(active == null && !persistenceAttempted, "no overlapping stages or measurements after persistence intent");
        active = new Token(this, Objects.requireNonNull(stage), tick()); return active;
    }
    public Span finish(Token token, Terminal terminal) {
        owner(); StrictJson.require(token != null && token.recorder == this && active == token && !token.completed, "same active local stage token required");
        Tick ended = tick(); Span span = new Span(token.stage, token.began, ended, terminal);
        token.completed = true; active = null; spans.add(span); return span;
    }
    public <T> T measure(Stage stage, Operation<T> operation) throws IOException, InterruptedException {
        Token token = start(stage);
        try { T result = operation.run(); finish(token, Terminal.RETURNED); return result; }
        catch (IOException | InterruptedException | RuntimeException | Error failure) {
            if (!token.completed) {
                try { finish(token, failure instanceof SocketTimeoutException ? Terminal.TIMED_OUT : Terminal.UNKNOWN); }
                catch (RuntimeException clockFailure) { failure.addSuppressed(clockFailure); active = null; token.completed = true; }
            }
            throw failure;
        }
    }
    /** Pure G2/domain work uses the same recorder without introducing a checked transport boundary. */
    public <T> T measurePure(Stage stage, java.util.function.Supplier<T> operation) {
        Token token = start(stage);
        try { T result = operation.get(); finish(token, Terminal.RETURNED); return result; }
        catch (RuntimeException | Error failure) {
            if (!token.completed) {
                try { finish(token, Terminal.UNKNOWN); }
                catch (RuntimeException clockFailure) { failure.addSuppressed(clockFailure); active = null; token.completed = true; }
            }
            throw failure;
        }
    }
    public void acknowledged(Acknowledgements observation) {
        owner(); StrictJson.require(acknowledgements.isEmpty() && !persistenceAttempted, "native ACK observation recorded once");
        StrictJson.require(spans.stream().anyMatch(span -> span.stage() == Stage.NATIVE_ACK_OBSERVATION && span.terminal() == Terminal.RETURNED),
                "returned primitive decoder required for ACK observation");
        acknowledgements = Optional.of(Objects.requireNonNull(observation));
    }
    public void nativeObserved(NativeObservation observation) {
        owner(); StrictJson.require(nativeObservation.isEmpty() && !persistenceAttempted, "native observation recorded once");
        StrictJson.require(spans.stream().anyMatch(span -> span.stage() == Stage.POSTSTATE_VALIDATION && span.terminal() == Terminal.RETURNED),
                "ACK cannot stand in for completed poststate validation");
        nativeObservation = Optional.of(Objects.requireNonNull(observation));
    }
    public void savedObserved(SavedWindow window) {
        owner(); StrictJson.require(savedWindow.isEmpty() && !persistenceAttempted, "saved window recorded once");
        StrictJson.require(window.before().machineId().equals(context.machineId()), "saved metric belongs to current machine");
        savedWindow = Optional.of(window);
    }
    public Snapshot snapshot() {
        owner(); StrictJson.require(active == null, "incomplete stage cannot be serialized as complete");
        return new Snapshot(context, spans, acknowledgements, nativeObservation, savedWindow);
    }
    /** One writer attempt only. A failure/timeout after intent is UNKNOWN and is never retried here. */
    public Persisted persist(ExistingReceiptWriter writer) throws IOException, InterruptedException {
        owner(); Objects.requireNonNull(writer); StrictJson.require(!persistenceAttempted, "metrics persistence outcome unknown or already completed; replay forbidden");
        Token token = start(Stage.PERSISTENCE); Snapshot before = new Snapshot(context, spans, acknowledgements, nativeObservation, savedWindow);
        persistenceAttempted = true;
        try {
            ExactRef reference = writer.writeMetrics(before); byte[] expected = DecisionMetrics.encode(before);
            byte[] actual = writer.readMetrics(reference);
            StrictJson.require(reference.bytes() == actual.length && reference.sha256().equals(sha256(actual))
                    && Arrays.equals(expected, actual) && DecisionMetrics.decode(actual).equals(before), "writer ACK lacks exact persisted metric readback");
            finish(token, Terminal.RETURNED); return new Persisted(before, reference);
        } catch (IOException | RuntimeException | Error failure) {
            if (!token.completed) { try { finish(token, failure instanceof SocketTimeoutException ? Terminal.TIMED_OUT : Terminal.UNKNOWN); }
                catch (RuntimeException clockFailure) { failure.addSuppressed(clockFailure); active = null; token.completed = true; } }
            throw failure;
        }
    }
    public static String sha256(byte[] raw) {
        try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)); }
        catch (NoSuchAlgorithmException impossible) { throw new IllegalStateException(impossible); }
    }
    private Tick tick() {
        Tick tick = clock.now(); StrictJson.require(tick.clockDomainId().equals(context.clockDomainId()) && tick.threadId() == owner.threadId()
                && tick.elapsedNanos() >= lastTick, "metric tick changed clock domain/thread or regressed");
        lastTick = tick.elapsedNanos(); return tick;
    }
    private void owner() { StrictJson.require(Thread.currentThread() == owner, "metrics belongs to original retained owner thread"); }
}

