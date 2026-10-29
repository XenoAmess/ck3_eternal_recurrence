package org.xar.ck3.control.wave3.governance.crownretry;

import java.math.BigInteger;
import java.util.Objects;
import java.util.Optional;

/** Exact reuse predicate and bounded horizon calculation; no state I/O or action. */
public final class CrownRetryPolicy {
    private CrownRetryPolicy() { }
    public record ContextKey(BigInteger bridgePid, String episodeRunId) { }
    public record Frame(ContextKey context, boolean playedCharacterObject,
            BigInteger actorCharacterId, BigInteger dateRaw) { }
    public record Hint(ContextKey sourceContext, BigInteger actorCharacterId,
            BigInteger retryDateRaw, String lawKey, String originalWire) {
        public Hint { Objects.requireNonNull(originalWire); }
    }
    public record State(boolean pendingPresent, Hint retry) { }

    public static Optional<Hint> matchingRetry(Frame frame, State state, String lawKey) {
        Objects.requireNonNull(frame); Objects.requireNonNull(state);
        Hint hint = state.retry();
        if (state.pendingPresent() || hint == null || hint.sourceContext() == null
                || !hint.sourceContext().equals(frame.context()) || !frame.playedCharacterObject()
                || !Objects.equals(hint.actorCharacterId(), frame.actorCharacterId())
                || frame.dateRaw() == null || hint.retryDateRaw() == null
                || lawKey != null && !lawKey.equals(hint.lawKey())) {
            return Optional.empty();
        }
        return Optional.of(hint);
    }

    public static Optional<Hint> matchingFutureRetry(Frame frame, State state, String lawKey) {
        return matchingRetry(frame, state, lawKey).filter(hint -> hint.retryDateRaw().compareTo(frame.dateRaw()) > 0);
    }

    public static BigInteger horizonDays(Frame frame, State state, BigInteger requestedDays,
            boolean queryEnabled, boolean pausedQueryEnabled) {
        Objects.requireNonNull(requestedDays);
        if (requestedDays.signum() <= 0) { throw new IllegalArgumentException("positive horizon days required"); }
        if (!queryEnabled || !pausedQueryEnabled || state == null) { return requestedDays; }
        Optional<Hint> retry = matchingFutureRetry(frame, state, null);
        if (retry.isEmpty()) { return requestedDays; }
        BigInteger delta = retry.orElseThrow().retryDateRaw().subtract(frame.dateRaw());
        BigInteger[] parts = delta.divideAndRemainder(BigInteger.valueOf(24));
        BigInteger days = parts[0].add(parts[1].signum() == 0 ? BigInteger.ZERO : BigInteger.ONE);
        return requestedDays.min(days);
    }
}
