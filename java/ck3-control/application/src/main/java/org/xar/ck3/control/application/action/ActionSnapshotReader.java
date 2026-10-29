package org.xar.ck3.control.application.action;

import java.util.Optional;
import java.util.function.Function;

/** Read-only lease borrowed from the active writer transaction, never a second OS lock or writer. */
public final class ActionSnapshotReader {
    public interface Lease {
        ActionJournal.Snapshot snapshot();
        Optional<String> activeActionId();
        Optional<ActionReceipt> find(String actionId);
        void assertCurrent();
    }
    private final ActionJournal journal;
    public ActionSnapshotReader(ActionJournal journal) { this.journal = java.util.Objects.requireNonNull(journal); }
    public Optional<ActionReceipt> find(String actionId) { return journal.locked(locked -> locked.find(actionId)); }
    public <T> T withFrozen(Function<Lease, T> operation) {
        return journal.locked(locked -> frozen(locked, operation));
    }
    public <T> T withFrozen(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session borrowed, Function<Lease, T> operation) {
        return journal.locked(borrowed, locked -> frozen(locked, operation));
    }
    private <T> T frozen(ActionJournal.LockedJournal locked, Function<Lease, T> operation) {
            ActionJournal.Snapshot frozen = locked.snapshot(); java.util.concurrent.atomic.AtomicBoolean active = new java.util.concurrent.atomic.AtomicBoolean(true);
            Lease lease = new Lease() {
                private void alive() { if (!active.get()) throw new IllegalStateException("action snapshot lease is closed"); }
                @Override public ActionJournal.Snapshot snapshot() { alive(); return frozen; }
                @Override public Optional<String> activeActionId() { alive(); return ActionScope.currentActionId(); }
                @Override public Optional<ActionReceipt> find(String actionId) { alive(); return locked.find(actionId); }
                @Override public void assertCurrent() {
                    alive(); ActionJournal.Snapshot current = locked.snapshot();
                    org.xar.ck3.control.contracts.StrictJson.require(current.ledgerSequence() == frozen.ledgerSequence() && current.headSha256().equals(frozen.headSha256()), "writer head changed during Driver freeze");
                }
            };
            try { return operation.apply(lease); } finally { active.set(false); }
    }
}
