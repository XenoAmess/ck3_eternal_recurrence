package org.xar.ck3.control.military.projectedcontact;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import org.xar.ck3.control.military.projectedcontact.ProjectedContactPolicy.Available;
import org.xar.ck3.control.military.projectedcontact.ProjectedContactPolicy.CapturedRow;
import org.xar.ck3.control.military.projectedcontact.ProjectedContactPolicy.QueryKey;
import org.xar.ck3.control.military.projectedcontact.ProjectedContactPolicy.QueryRequired;
import org.xar.ck3.control.military.projectedcontact.ProjectedContactPolicy.QueryRow;
import org.xar.ck3.control.military.projectedcontact.ProjectedContactPolicy.Request;
import org.xar.ck3.control.military.projectedcontact.ProjectedContactPolicy.Selection;
import org.xar.ck3.control.military.projectedcontact.ProjectedContactPolicy.Snapshot;

/** An immutable index of already validated effective history, with no candidate ranking or I/O.
 * The caller retains the existing restore/advance history projection and native authority.
 * Exact source identifiers are comparison operands, not authentication issued by this class.
 */
public final class SourceBoundContactIndex {
    /** Source identity must come from the current qualified provider, never a guessed local build. */
    public record SourceIdentity(String machineId, String buildVersion, String executableSha256,
                                 String producerSourceSha256, String consumerClosureSha256) {
        public SourceIdentity {
            nonempty(machineId, "machine ID"); nonempty(buildVersion, "build version");
            require(!machineId.equalsIgnoreCase("unknown") && !machineId.equalsIgnoreCase("unavailable")
                    && !buildVersion.equalsIgnoreCase("unknown") && !buildVersion.equalsIgnoreCase("unavailable"),
                    "unknown source must use Unknown context");
            sha(executableSha256); sha(producerSourceSha256); sha(consumerClosureSha256);
        }
    }

    /** Fences the existing effective-history projection; all indices remain exact integers. */
    public record HistoryIdentity(String restoredBranchIdentity, BigInteger latestCompletedAdvanceIndex,
                                  BigInteger observedHistoryTailIndex) {
        public HistoryIdentity {
            nonempty(restoredBranchIdentity, "restored branch identity");
            Objects.requireNonNull(latestCompletedAdvanceIndex, "advance index");
            Objects.requireNonNull(observedHistoryTailIndex, "history tail index");
            require(latestCompletedAdvanceIndex.signum() >= 0
                    && observedHistoryTailIndex.compareTo(latestCompletedAdvanceIndex) >= 0,
                    "history indices must be nonnegative and ordered");
        }
    }

    /** Every mutation attempt invalidates the old read cache, including an ACK with no poststate. */
    public enum Invalidation {
        NONE, ORDER_ATTEMPTED, REROUTE_ATTEMPTED, ACK_WITHOUT_POSTSTATE, UNKNOWN_COMMAND_RESULT,
        RESTORE, ADVANCE, MERGE_OR_SPLIT, FRAME_SOURCE_UNAVAILABLE
    }

    public sealed interface Context permits Current, Unknown { }
    public record Current(SourceIdentity source, Snapshot snapshot, HistoryIdentity history,
                          Invalidation invalidation) implements Context {
        public Current {
            Objects.requireNonNull(source, "source"); Objects.requireNonNull(snapshot, "snapshot");
            Objects.requireNonNull(history, "history"); Objects.requireNonNull(invalidation, "invalidation");
        }
    }
    public record Unknown(String reason) implements Context {
        public Unknown { nonempty(reason, "unknown reason"); }
    }

    public enum Outcome { AVAILABLE, QUERY_REQUIRED, CONTEXT_CHANGED, INVALIDATED, UNKNOWN_CONTEXT }
    public record Lookup(Selection selection, Outcome outcome, int inspectedRows) {
        public Lookup {
            Objects.requireNonNull(selection, "selection"); Objects.requireNonNull(outcome, "outcome");
            require(inspectedRows >= 0, "negative row count");
            require((selection instanceof Available) == (outcome == Outcome.AVAILABLE),
                    "available outcome and selection disagree");
        }
        public boolean authorizesCommandReplay() { return false; }
        public boolean actualArrivalObserved() { return false; }
    }

    private final Current origin;
    private final Map<QueryKey, List<CapturedRow>> byKey;
    private final int sourceRowsVisited;
    private final int indexedRows;

    private SourceBoundContactIndex(Current origin, List<QueryRow> effectiveRows) {
        this.origin = Objects.requireNonNull(origin, "origin");
        require(origin.invalidation() == Invalidation.NONE, "cannot build from an invalidated frame");
        List<QueryRow> rows = List.copyOf(effectiveRows);
        Map<QueryKey, List<CapturedRow>> staging = new HashMap<>();
        int count = 0;
        for (QueryRow value : rows) {
            if (value instanceof CapturedRow row && row.capture().equals(origin.snapshot().capture())) {
                staging.computeIfAbsent(row.key(), ignored -> new ArrayList<>()).add(row);
                count++;
            }
        }
        Map<QueryKey, List<CapturedRow>> immutable = new HashMap<>();
        staging.forEach((key, values) -> immutable.put(key, List.copyOf(values)));
        this.byKey = Map.copyOf(immutable);
        this.sourceRowsVisited = rows.size();
        this.indexedRows = count;
    }

    /** Input is the complete existing projection AFTER latest restore and completed advance.
     * No top-K, identity deduplication, sorting, or early history truncation occurs here.
     */
    public static SourceBoundContactIndex build(Current origin, List<QueryRow> effectiveRows) {
        return new SourceBoundContactIndex(origin, effectiveRows);
    }

    public int sourceRowsVisited() { return sourceRowsVisited; }
    public int indexedRows() { return indexedRows; }

    /** Exactly the old reverse selection for a stable context; other contexts require a fresh query.
     * The same Request/Scope.matches check retains current Province, owner and native revision.
     */
    public Lookup select(Context context, Request request) {
        Objects.requireNonNull(context, "current context"); Objects.requireNonNull(request, "request");
        if (context instanceof Unknown) { return missing(request, Outcome.UNKNOWN_CONTEXT); }
        Current current = (Current) context;
        if (current.invalidation() != Invalidation.NONE) { return missing(request, Outcome.INVALIDATED); }
        if (!current.source().equals(origin.source()) || !current.snapshot().equals(origin.snapshot())
                || !current.history().equals(origin.history())) {
            return missing(request, Outcome.CONTEXT_CHANGED);
        }
        List<CapturedRow> candidates = byKey.getOrDefault(request.key(), List.of());
        int inspected = 0;
        for (int index = candidates.size() - 1; index >= 0; index--) {
            CapturedRow row = candidates.get(index); inspected++;
            if (row.scope().matches(current.snapshot(), request)) {
                return new Lookup(new Available(request.key(), row.scope()), Outcome.AVAILABLE, inspected);
            }
        }
        return new Lookup(new QueryRequired(request.key()), Outcome.QUERY_REQUIRED, inspected);
    }

    /** Preserve every request occurrence and its original order, including duplicate keys. */
    public List<Lookup> selectAll(Context context, List<Request> requests) {
        Objects.requireNonNull(context, "current context");
        List<Request> ordered = List.copyOf(requests);
        List<Lookup> results = new ArrayList<>(ordered.size());
        for (Request request : ordered) { results.add(select(context, request)); }
        return List.copyOf(results);
    }

    private static Lookup missing(Request request, Outcome outcome) {
        return new Lookup(new QueryRequired(request.key()), outcome, 0);
    }
    private static void nonempty(String value, String name) {
        require(value != null && !value.isBlank() && value.length() <= 4096, "nonempty bounded " + name + " required");
    }
    private static void sha(String value) {
        require(value != null && value.matches("[0-9a-f]{64}"), "canonical SHA-256 required");
    }
    private static void require(boolean condition, String message) {
        if (!condition) { throw new IllegalArgumentException(message); }
    }
}
