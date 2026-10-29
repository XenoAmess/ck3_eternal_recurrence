package org.xar.ck3.control.application.action;

/** Registered fixture producer. Implementing this interface supplies no read, guard or submission authority. */
public interface FixtureCompositeActionPort extends CompositeActionPort.OriginalContinuation {
    /** Rechecked by the one coordinator before it reserves each exact new child. */
    void requireFixtureChild(ActionCommand parent,CompositeExecution canonicalCursor,ActionCommand child);
    /** Pure observed qualification before the separate real Entry preview/commit. This grants no parent completion. */
    void requireFixtureBusiness(ActionCommand parent,CompositeExecution canonicalCursor,FixtureBusinessEvidence actual);
    /** The same installed source replays its business proof, including full original qualification and entry inputs. */
    void requireFixtureCompletion(ActionCommand parent,CompositeExecution canonicalCursor,FixtureBusinessObservation actual);
}
