package org.xar.ck3.control.contracts.observation;

import java.math.BigInteger;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Objects;
import java.util.function.Supplier;

/**
 * Completed pure observations only, within one explicitly bound source/frame/writer version.
 * S, F and V must be the existing transitively immutable domain records. This helper does not
 * observe a Game, issue a writer version, schedule work, submit an action, persist or retry.
 * The original single coordinator supplies every WriterVersion and calls the invalidation hooks.
 */
public final class ObservationReuse<S extends Record, F extends Record, V extends Record> {
    public record WriterVersion(String authorityId, BigInteger version) {
        public WriterVersion {
            nonempty(authorityId, "writer authority"); Objects.requireNonNull(version);
            if (version.signum() < 0) throw new IllegalArgumentException("negative writer version");
        }
    }

    /** Original source and frame types retain their own integer domains and public/native revisions. */
    public record Scope<S extends Record, F extends Record>(S source, F frame, WriterVersion writerVersion) {
        public Scope { Objects.requireNonNull(source); Objects.requireNonNull(frame); Objects.requireNonNull(writerVersion); }
    }

    /** Digest covers the complete real projection input, including arguments and candidate order. */
    public record InputKey(String operation, String sha256) {
        public InputKey {
            nonempty(operation, "operation"); Objects.requireNonNull(sha256);
            if (!sha256.matches("[0-9a-f]{64}")) throw new IllegalArgumentException("canonical input SHA-256 required");
        }
    }

    public enum Invalidation { NONE, BEFORE_ACTION_SUBMISSION, POSTSTATE_VERSION_CHANGED,
        SOURCE_CHANGED, FRAME_CHANGED, UNKNOWN_OUTCOME, INCOMPLETE_OBSERVATION, CLOSED }

    /** A read lease, with no submission or freshness authority. Constructor is deliberately private. */
    public static final class Token<S extends Record, F extends Record> {
        private final Scope<S, F> scope;
        private Token(Scope<S, F> scope) { this.scope = scope; }
        public Scope<S, F> scope() { return scope; }
    }

    public sealed interface Outcome<V extends Record> permits Complete, Unknown, Unavailable { V value(); }
    public record Complete<V extends Record>(V value) implements Outcome<V> {
        public Complete { Objects.requireNonNull(value); }
    }
    public record Unknown<V extends Record>(V value, String reason) implements Outcome<V> {
        public Unknown { Objects.requireNonNull(value); nonempty(reason, "unknown reason"); }
    }
    public record Unavailable<V extends Record>(V value, String reason) implements Outcome<V> {
        public Unavailable { Objects.requireNonNull(value); nonempty(reason, "unavailable reason"); }
    }
    public record Read<V extends Record>(Outcome<V> outcome, boolean reused) {
        public Read { Objects.requireNonNull(outcome); }
    }

    private final String authorityId;
    private final int maximumEntries;
    private final Map<InputKey, V> completed = new LinkedHashMap<>();
    private Token<S, F> active;
    private WriterVersion latestVersion;
    private WriterVersion invalidatedAt;
    private Scope<S, F> incompleteScope;
    private boolean unresolvedAction;
    private boolean closed;
    private Invalidation lastInvalidation = Invalidation.NONE;

    public ObservationReuse(String authorityId, int maximumEntries) {
        nonempty(authorityId, "writer authority");
        if (maximumEntries < 1) throw new IllegalArgumentException("positive cache capacity required");
        this.authorityId = authorityId; this.maximumEntries = maximumEntries;
    }

    /** Caller has independently obtained and validated this scope; this call does not perform that work. */
    public synchronized Token<S, F> bindFresh(Scope<S, F> scope) {
        Objects.requireNonNull(scope); requireOpen(); requireAuthority(scope.writerVersion());
        if (unresolvedAction) throw new IllegalStateException("unknown action remains unresolved by the original owner");
        if (latestVersion != null && scope.writerVersion().version().compareTo(latestVersion.version()) < 0)
            throw new IllegalArgumentException("writer version regressed");
        if (invalidatedAt != null && scope.writerVersion().version().compareTo(invalidatedAt.version()) <= 0)
            throw new IllegalStateException("submission/poststate invalidation requires a newer external writer version");
        if (scope.equals(incompleteScope)) throw new IllegalStateException("incomplete observation cannot be replayed");
        if (active != null && active.scope().equals(scope)) return active;
        if (active != null) {
            lastInvalidation = active.scope().source().equals(scope.source())
                ? Invalidation.FRAME_CHANGED : Invalidation.SOURCE_CHANGED;
        }
        completed.clear(); active = new Token<>(scope); latestVersion = scope.writerVersion();
        return active;
    }

    /** Method reference is the ScopeGuard used by immutable candidate/history indexes. */
    public synchronized void requireCurrent(Token<S, F> token) {
        requireOpen();
        if (token == null || token != active) throw new IllegalStateException("observation lease is stale or belongs to another owner");
    }

    /**
     * Pure projection only. A concurrent miss may compute twice; it cannot cause a native read or action.
     * Work happens outside the monitor, and invalidation during work rejects the late result.
     */
    public Read<V> read(Token<S, F> token, InputKey key, Supplier<Outcome<V>> projection) {
        Objects.requireNonNull(key); Objects.requireNonNull(projection);
        synchronized (this) {
            requireCurrent(token); V value = completed.get(key);
            if (value != null) return new Read<>(new Complete<>(value), true);
        }
        final Outcome<V> outcome;
        try { outcome = Objects.requireNonNull(projection.get()); }
        catch (RuntimeException | Error failure) {
            synchronized (this) {
                if (token == active) { incompleteScope = token.scope(); revoke(Invalidation.INCOMPLETE_OBSERVATION); }
            }
            throw failure;
        }
        synchronized (this) {
            requireCurrent(token);
            if (outcome instanceof Complete<V> known) {
                if (completed.size() == maximumEntries && !completed.containsKey(key))
                    completed.remove(completed.keySet().iterator().next());
                completed.put(key, known.value());
            } else {
                incompleteScope = token.scope(); revoke(Invalidation.INCOMPLETE_OBSERVATION);
            }
            return new Read<>(outcome, false);
        }
    }

    /** Called by the one original coordinator before its durable submission/dispatch boundary. */
    public synchronized void beforeSubmit(WriterVersion observedWriterVersion) {
        requireInvalidationVersion(observedWriterVersion); invalidatedAt = observedWriterVersion;
        revoke(Invalidation.BEFORE_ACTION_SUBMISSION);
    }

    public synchronized void afterPoststateVersionChange(WriterVersion previousVersion,
            WriterVersion observedPoststateVersion) {
        requireOpen(); requireAuthority(previousVersion); requireAuthority(observedPoststateVersion);
        if (observedPoststateVersion.version().compareTo(previousVersion.version()) <= 0)
            throw new IllegalArgumentException("poststate writer version must advance");
        requireInvalidationVersion(observedPoststateVersion); invalidatedAt = previousVersion;
        revoke(Invalidation.POSTSTATE_VERSION_CHANGED);
    }

    public synchronized void unknownOutcome(WriterVersion observedWriterVersion) {
        requireInvalidationVersion(observedWriterVersion); invalidatedAt = observedWriterVersion;
        unresolvedAction = true; revoke(Invalidation.UNKNOWN_OUTCOME);
    }

    /** A boundary observed drift while validating an input; it does not bind the changed input. */
    public synchronized void observedDrift(Token<S, F> token, Invalidation reason) {
        requireCurrent(token);
        if (reason != Invalidation.SOURCE_CHANGED && reason != Invalidation.FRAME_CHANGED)
            throw new IllegalArgumentException("source/frame drift reason required");
        incompleteScope = token.scope(); revoke(reason);
    }

    /** Only the original owner may call after independently settling its unknown action; never retries it. */
    public synchronized void ownerSettledUnknown(WriterVersion settledWriterVersion) {
        requireOpen(); requireAuthority(settledWriterVersion);
        if (!unresolvedAction || invalidatedAt == null
                || settledWriterVersion.version().compareTo(invalidatedAt.version()) <= 0)
            throw new IllegalStateException("fresh externally settled writer version required");
        latestVersion = settledWriterVersion; unresolvedAction = false;
        // No token is restored. Caller must separately supply an independently fresh scope.
    }

    public synchronized int retainedEntryCount() { return completed.size(); }
    public synchronized Invalidation lastInvalidation() { return lastInvalidation; }
    public synchronized void close() { revoke(Invalidation.CLOSED); closed = true; }

    private void requireInvalidationVersion(WriterVersion version) {
        requireOpen(); requireAuthority(version);
        if (latestVersion != null && version.version().compareTo(latestVersion.version()) < 0)
            throw new IllegalArgumentException("writer invalidation version regressed");
        latestVersion = version;
    }
    private void requireAuthority(WriterVersion version) {
        Objects.requireNonNull(version);
        if (!authorityId.equals(version.authorityId())) throw new IllegalArgumentException("different writer authority");
    }
    private void requireOpen() { if (closed) throw new IllegalStateException("observation reuse is closed"); }
    private void revoke(Invalidation reason) { active = null; completed.clear(); lastInvalidation = reason; }
    private static void nonempty(String value, String name) {
        if (value == null || value.isBlank()) throw new IllegalArgumentException(name + " is required");
    }
}
