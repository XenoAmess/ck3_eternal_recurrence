package org.xar.ck3.control.g2.client;

import java.time.Duration;
import java.time.Instant;
import java.util.Objects;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicBoolean;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Request;

/**
 * Finite, sequential producer -> verified HTTP -> consumer continuation on one retained client.
 * No request prefetch, retry, policy filtering, process launch, action or ledger authority.
 * The caller keeps ownership of its existing client/host and outer finite Job.
 */
public final class G2ClientBatchSession {
    public static final int MAX_REQUESTS = 1024;

    public record Budget(int maximumRequests, Duration totalDeadline) {
        public Budget {
            Objects.requireNonNull(totalDeadline, "totalDeadline");
            if (maximumRequests < 1 || maximumRequests > MAX_REQUESTS
                    || totalDeadline.isZero() || totalDeadline.isNegative()) {
                throw new IllegalArgumentException("bounded request count and positive finite deadline required");
            }
            try { totalDeadline.toNanos(); }
            catch (ArithmeticException error) { throw new IllegalArgumentException("deadline exceeds monotonic range", error); }
        }
    }

    public sealed interface Next permits Evaluate, Complete { }
    public record Evaluate(G2Request request) implements Next {
        public Evaluate { Objects.requireNonNull(request, "request"); }
    }
    public enum Complete implements Next { INSTANCE }

    @FunctionalInterface public interface Producer {
        /** Called only after the preceding verified result was consumed. No automatic replay. */
        Next next(Optional<G2Evaluation> preceding);
    }
    @FunctionalInterface public interface Consumer {
        /** Persist/use the original verified result here before any dependent request is produced. */
        void accept(G2Evaluation evaluation);
    }

    public enum Stop { COMPLETE, REQUEST_BOUND, DEADLINE, INTERRUPTED, PRODUCER_FAILED, CLIENT_FAILED, CONSUMER_FAILED }

    /** Counters refer only to pure G2 evaluations; they assert no Game, save or Job terminal state. */
    public record Summary(String machineId, Instant startedAtUtc, Instant finishedAtUtc, long elapsedNanos, Stop stop,
            int submittedRequests, int verifiedResponses, int consumedResponses,
            Optional<String> lastRequestId, Optional<G2ClientException.Reason> clientFailureReason) {
        public Summary {
            StrictJson.text(machineId);
            Objects.requireNonNull(startedAtUtc, "startedAtUtc");
            Objects.requireNonNull(finishedAtUtc, "finishedAtUtc");
            Objects.requireNonNull(stop, "stop");
            Objects.requireNonNull(lastRequestId, "lastRequestId");
            Objects.requireNonNull(clientFailureReason, "clientFailureReason");
            if (elapsedNanos < 0 || submittedRequests < 0 || submittedRequests > MAX_REQUESTS
                    || verifiedResponses < 0 || verifiedResponses > submittedRequests
                    || consumedResponses < 0 || consumedResponses > verifiedResponses
                    || (stop == Stop.CLIENT_FAILED) != clientFailureReason.isPresent()) {
                throw new IllegalArgumentException("inconsistent batch counters or client failure");
            }
            lastRequestId.ifPresent(StrictJson::text);
            if (submittedRequests > 0 && lastRequestId.isEmpty()) {
                throw new IllegalArgumentException("submitted evaluation requires original request identity");
            }
            if (stop == Stop.COMPLETE && (submittedRequests != verifiedResponses || verifiedResponses != consumedResponses)) {
                throw new IllegalArgumentException("complete continuation requires each result verified and consumed");
            }
        }
    }

    /** Retains at most one response and original failure; complete outputs belong to the consumer. */
    public record Result(Summary summary, Optional<G2Evaluation> lastVerified, Optional<RuntimeException> failure) {
        public Result {
            Objects.requireNonNull(summary, "summary");
            Objects.requireNonNull(lastVerified, "lastVerified");
            Objects.requireNonNull(failure, "failure");
            boolean failed = summary.stop() == Stop.PRODUCER_FAILED || summary.stop() == Stop.CLIENT_FAILED
                    || summary.stop() == Stop.CONSUMER_FAILED;
            if (failed != failure.isPresent() || (summary.verifiedResponses() > 0) != lastVerified.isPresent()) {
                throw new IllegalArgumentException("original failure/last response must match summary");
            }
            if (summary.stop() == Stop.CLIENT_FAILED) {
                if (!(failure.orElseThrow() instanceof G2ClientException client)
                        || client.reason() != summary.clientFailureReason().orElseThrow()) {
                    throw new IllegalArgumentException("client failure must retain original typed exception");
                }
            }
        }
    }

    private final G2JavaClient client;
    private final String machineId;
    private final AtomicBoolean running = new AtomicBoolean();

    public G2ClientBatchSession(G2JavaClient client, String machineId) {
        this.client = Objects.requireNonNull(client, "client");
        this.machineId = StrictJson.text(machineId);
    }

    /**
     * Synchronous callbacks stay inside the caller's existing bounded execution owner.
     * The whole-batch clock includes producer, HTTP and consumer work; each HTTP call
     * receives only the remaining time. Callback code is not interrupted by a new thread.
     */
    public Result run(Budget budget, Producer producer, Consumer consumer) {
        Objects.requireNonNull(budget, "budget");
        Objects.requireNonNull(producer, "producer");
        Objects.requireNonNull(consumer, "consumer");
        if (!running.compareAndSet(false, true)) throw new IllegalStateException("batch session already running");
        Instant started = Instant.now();
        long tick = System.nanoTime();
        long totalNanos = budget.totalDeadline().toNanos();
        int submitted = 0, verified = 0, consumed = 0;
        G2Evaluation preceding = null;
        String lastRequestId = null;
        try {
            while (true) {
                if (Thread.currentThread().isInterrupted()) return result(started, tick, Stop.INTERRUPTED, submitted, verified, consumed, lastRequestId, preceding, null);
                if (remaining(totalNanos, tick) <= 0) return result(started, tick, Stop.DEADLINE, submitted, verified, consumed, lastRequestId, preceding, null);
                Next next;
                try { next = Objects.requireNonNull(producer.next(Optional.ofNullable(preceding)), "producer next"); }
                catch (RuntimeException failure) { return result(started, tick, Stop.PRODUCER_FAILED, submitted, verified, consumed, lastRequestId, preceding, failure); }
                if (Thread.currentThread().isInterrupted()) return result(started, tick, Stop.INTERRUPTED, submitted, verified, consumed, lastRequestId, preceding, null);
                if (remaining(totalNanos, tick) <= 0) return result(started, tick, Stop.DEADLINE, submitted, verified, consumed, lastRequestId, preceding, null);
                if (next == Complete.INSTANCE) return result(started, tick, Stop.COMPLETE, submitted, verified, consumed, lastRequestId, preceding, null);
                G2Request request = ((Evaluate) next).request();
                lastRequestId = request.requestId();
                if (submitted >= budget.maximumRequests()) return result(started, tick, Stop.REQUEST_BOUND, submitted, verified, consumed, lastRequestId, preceding, null);
                G2Evaluation evaluated;
                try {
                    long left = remaining(totalNanos, tick);
                    if (left <= 0) return result(started, tick, Stop.DEADLINE, submitted, verified, consumed, lastRequestId, preceding, null);
                    evaluated = client.evaluateWithEvidence(request, Duration.ofNanos(left));
                    submitted++;
                    verified++;
                    preceding = evaluated;
                } catch (G2ClientException failure) {
                    if (failure.evidence().actualHttpInvoked()) submitted++;
                    return result(started, tick, Stop.CLIENT_FAILED, submitted, verified, consumed, lastRequestId, preceding, failure);
                }
                try { consumer.accept(evaluated); consumed++; }
                catch (RuntimeException failure) { return result(started, tick, Stop.CONSUMER_FAILED, submitted, verified, consumed, lastRequestId, preceding, failure); }
            }
        } finally { running.set(false); }
    }

    private static long remaining(long totalNanos, long tick) { return totalNanos - (System.nanoTime() - tick); }

    private Result result(Instant started, long tick, Stop stop, int submitted, int verified, int consumed,
            String lastRequestId, G2Evaluation preceding, RuntimeException failure) {
        Optional<G2ClientException.Reason> reason = failure instanceof G2ClientException client
                ? Optional.of(client.reason()) : Optional.empty();
        // A producer/consumer may itself throw a client exception; it is still a callback failure.
        if (stop != Stop.CLIENT_FAILED) reason = Optional.empty();
        Summary summary = new Summary(machineId, started, Instant.now(), Math.max(0, System.nanoTime() - tick), stop,
                submitted, verified, consumed, Optional.ofNullable(lastRequestId), reason);
        return new Result(summary, Optional.ofNullable(preceding), Optional.ofNullable(failure));
    }
}
