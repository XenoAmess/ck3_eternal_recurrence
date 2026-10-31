package org.xar.ck3.control.application.action;

import java.util.List;
import java.util.Optional;
import java.util.function.Function;
import org.xar.ck3.control.contracts.ExactRef;

/** Implemented on the original authoritative writer transaction and original byte-zero lock. */
public interface ActionJournal {
    <T> T locked(Function<LockedJournal, T> operation);
    /** Borrow an already-held original session. This overload must never acquire another OS lock. */
    default <T> T locked(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session borrowed, Function<LockedJournal, T> operation) {
        throw new IllegalStateException("borrowed original writer scope is unavailable");
    }
    interface LockedJournal {
        default org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session writerSession() {
            throw new IllegalStateException("actual original writer session is unavailable");
        }
        default org.xar.ck3.control.continuity.writer.WriterContracts.Head head() {
            try { return writerSession().head(); }
            catch (java.io.IOException failure) { throw new java.io.UncheckedIOException(failure); }
        }
        Optional<ActionReceipt> find(String actionId);
        /** Only the canonical journal can derive this proof from its complete chain under the held writer lock. */
        default Optional<ActionState.IntentAbandoned> abandonableIntent(ActionReceipt original) { return Optional.empty(); }
        List<ActionReceipt> unresolved();
        /** Must check ActionTransitions under this lock and return only after durable writer commit. */
        ActionReceipt append(ActionCommand command, String bodySha256, ActionState next);
        default Snapshot snapshot() { throw new IllegalStateException("complete durable action snapshot is unavailable"); }
    }
    sealed interface LegacyHistoryBasis permits MissingHistoryBasis, NullHistoryBasis, BoundHistoryBasis { }
    record MissingHistoryBasis() implements LegacyHistoryBasis { }
    record NullHistoryBasis() implements LegacyHistoryBasis { }
    record BoundHistoryBasis(ExactRef originalDriverHistory) implements LegacyHistoryBasis {
        public BoundHistoryBasis { java.util.Objects.requireNonNull(originalDriverHistory); }
    }
    record Snapshot(long ledgerSequence, String headSha256, List<ActionReceipt> actions, LegacyHistoryBasis originalHistory) {
        public Snapshot {
            org.xar.ck3.control.contracts.StrictJson.safe(ledgerSequence, 0);
            org.xar.ck3.control.contracts.StrictJson.require(headSha256 != null && headSha256.matches("[0-9a-f]{64}"), "exact canonical ledger head SHA required");
            actions = List.copyOf(actions); java.util.Objects.requireNonNull(originalHistory);
        }
    }
}
