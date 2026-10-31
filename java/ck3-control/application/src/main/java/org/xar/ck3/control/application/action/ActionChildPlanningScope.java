package org.xar.ck3.control.application.action;

import java.io.IOException;
import java.time.Instant;
import java.util.Optional;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.StrictJson;

/** Read-only identification of the actual running parent while its bounded Children callback owns the same writer. */
public final class ActionChildPlanningScope {
    public record Parent(String actionId, String bodySha256, String handlerId) { }
    /** Canonical DATA freshly read inside the real held scope. Keeping or constructing this record grants no custody. */
    public record FixtureCursor(ActionReceipt parent,CompositeExecution execution,java.util.List<ActionReceipt> recordedChildren) {
        public FixtureCursor {java.util.Objects.requireNonNull(parent);java.util.Objects.requireNonNull(execution);recordedChildren=java.util.List.copyOf(recordedChildren);}
    }
    @FunctionalInterface interface Work<T> { T run() throws InterruptedException; }
    private record Held(ActionJournal.LockedJournal journal, ContinuityStorePort.Session session, Parent parent, boolean continuation,Instant deadline) {
        private Held {java.util.Objects.requireNonNull(deadline);}
    }
    private static final ThreadLocal<Held> CURRENT = new ThreadLocal<>();
    private ActionChildPlanningScope() { }
    public static Optional<Parent> current(ContinuityStorePort.Session same, WriterContracts.Head actualHead) throws IOException {
        Held held = CURRENT.get(); if (held == null) return Optional.empty();
        StrictJson.require(held.session() == same && ActionScope.currentActionId().filter(held.parent().actionId()::equals).isPresent(), "child planning scope escaped its original writer or parent");
        var head = same.head(); StrictJson.require(head.digest().equals(actualHead.digest()) && head.documents().equals(actualHead.documents()), "child planning needs the actual original writer Head");
        ActionReceipt parent = held.journal().find(held.parent().actionId()).orElseThrow();
        StrictJson.require(parent.bodySha256().equals(held.parent().bodySha256()) && execution(parent, held).handlerId().equals(held.parent().handlerId()), "only the actual running canonical parent owns this child planning scope");
        return Optional.of(held.parent());
    }
    /** Original entry DATA only while the actual running parent has not reserved a child. */
    public static Optional<GuardEvidence> entryGuard(ContinuityStorePort.Session same, WriterContracts.Head actualHead,
            ActionCommand exactParent) throws IOException {
        if (CURRENT.get() == null) return Optional.empty();
        Parent active = current(same, actualHead).orElseThrow();
        StrictJson.require(active.actionId().equals(exactParent.actionId())
                && active.bodySha256().equals(ActionCodec.bodySha256(exactParent)), "entry guard crossed its exact parent");
        Held held = CURRENT.get();
        ActionReceipt canonical = held.journal().find(active.actionId()).orElseThrow();
        if (held.continuation() || !(canonical.state() instanceof ActionState.CompositeRunning running)
                || !running.execution().children().isEmpty()) return Optional.empty();
        return Optional.of(running.execution().guard());
    }
    /** Child observations must sample fresh state, never borrow the parent's retained entry. */
    public static boolean isReservedChild(ContinuityStorePort.Session same, WriterContracts.Head actualHead,
            ActionCommand exactCommand) throws IOException {
        java.util.Objects.requireNonNull(exactCommand);
        Held held = CURRENT.get();
        if (held == null || held.parent().actionId().equals(exactCommand.actionId())) return false;
        return reservedParent(same, actualHead, exactCommand).isPresent();
    }
    /** Identifies only the exact child already reserved by this original running parent's Children callback. */
    public static Optional<Parent> reservedParent(ContinuityStorePort.Session same, WriterContracts.Head actualHead,
            ActionCommand exactChild) throws IOException {
        java.util.Objects.requireNonNull(exactChild);
        Held held = CURRENT.get(); if (held == null) return Optional.empty();
        StrictJson.require(held.session() == same
                && ActionScope.currentActionId().filter(exactChild.actionId()::equals).isPresent(),
                "reserved child scope escaped its original writer or exact child action");
        var head = same.head();
        StrictJson.require(head.digest().equals(actualHead.digest()) && head.documents().equals(actualHead.documents()),
                "reserved child needs the actual original writer Head");
        ActionReceipt parent = held.journal().find(held.parent().actionId()).orElseThrow();
        StrictJson.require(parent.bodySha256().equals(held.parent().bodySha256())
                && execution(parent, held).handlerId().equals(held.parent().handlerId()),
                "only the actual running canonical parent owns its reserved child scope");
        var children = execution(parent, held).children();
        StrictJson.require(!children.isEmpty(), "parent has not reserved any child");
        var reserved = children.getLast();
        StrictJson.require(reserved.actionId().equals(exactChild.actionId())
                && reserved.bodySha256().equals(ActionCodec.bodySha256(exactChild))
                && exactChild.actionId().equals(ActionIds.child(parent.command().actionId(), children.size(), exactChild.operation()))
                && exactChild.sessionId().equals(parent.command().sessionId())
                && exactChild.source().equals(parent.command().source()),
                "reserved child changed its canonical ordinal, complete body, source or session");
        return Optional.of(held.parent());
    }
    /** Revalidates the private Held, actual original writer and current canonical parent on every invocation. */
    public static FixtureCursor fixtureCurrent(ContinuityStorePort.Session same,WriterContracts.Head actualHead,
            ActionCommand exactParent,String actualHandlerId)throws IOException {
        Parent active=current(same,actualHead).orElseThrow(()->new IOException("no actual fixture composite planning scope is active"));
        return fixtureCursor(CURRENT.get(),active,exactParent,actualHandlerId);
    }
    /** Only the actual original parent scope or its already source-validated continuation supplies this cutoff. */
    public static Instant fixtureDeadline(ContinuityStorePort.Session same,WriterContracts.Head actualHead,
            ActionCommand exactParent,String actualHandlerId)throws IOException {
        fixtureCurrent(same,actualHead,exactParent,actualHandlerId);return CURRENT.get().deadline();
    }
    /** The child guard must name the complete exact child already reserved by this very parent's Children. */
    public static FixtureCursor fixtureReservedChild(ContinuityStorePort.Session same,WriterContracts.Head actualHead,
            ActionCommand exactChild,ActionCommand exactParent,String actualHandlerId)throws IOException {
        Parent active=reservedParent(same,actualHead,exactChild).orElseThrow(()->new IOException("no actual fixture reserved-child scope is active"));
        return fixtureCursor(CURRENT.get(),active,exactParent,actualHandlerId);
    }
    private static FixtureCursor fixtureCursor(Held held,Parent active,ActionCommand exactParent,String actualHandlerId){
        java.util.Objects.requireNonNull(exactParent);StrictJson.text(actualHandlerId);FixturePlan.requireParent(exactParent);
        ActionReceipt canonical=held.journal().find(active.actionId()).orElseThrow();
        StrictJson.require(active.actionId().equals(exactParent.actionId())&&active.handlerId().equals(actualHandlerId)
                &&java.util.Arrays.equals(ActionCodec.encodeCommand(canonical.command()),ActionCodec.encodeCommand(exactParent)),
                "fixture scope changed its exact original parent or installed handler");
        CompositeExecution cursor=execution(canonical,held);var children=new java.util.ArrayList<ActionReceipt>();
        for(var reserved:cursor.children())held.journal().find(reserved.actionId()).ifPresent(receipt->{
            StrictJson.require(receipt.bodySha256().equals(reserved.bodySha256()),"fixture scope canonical child body changed");children.add(receipt);
        });
        return new FixtureCursor(canonical,cursor,children);
    }
    private static CompositeExecution execution(ActionReceipt parent, Held held) {
        if (parent.state() instanceof ActionState.CompositeRunning running) return running.execution();
        StrictJson.require(held.continuation() && parent.state() instanceof ActionState.CompositeUnknown
                && (parent.command().origin() instanceof CommandOrigin.LifecycleTerminal
                    && parent.command().lifecycleExpected().operation() == LifecycleExpectedPostcondition.Operation.CONTINUE_SUCCESSOR
                    ||FixturePlan.isParent(parent.command())&&FixturePlan.requireParent(parent.command())!=null),
                "unresolved composite has no source-owned successor continuation scope");
        return ((ActionState.CompositeUnknown) parent.state()).execution();
    }
    static <T> T withinContinuation(ActionJournal.LockedJournal journal, ActionCommand parent, String handlerId,Instant actualTokenDeadline, Work<T> work) throws InterruptedException {
        StrictJson.require(CURRENT.get() == null, "nested continuation scope is unavailable");
        CURRENT.set(new Held(journal, journal.writerSession(), new Parent(parent.actionId(), ActionCodec.bodySha256(parent), handlerId), true,actualTokenDeadline));
        try { return work.run(); } finally { CURRENT.remove(); }
    }
    static <T> T within(ActionJournal.LockedJournal journal, ActionCommand parent, String handlerId, Work<T> work) throws InterruptedException {
        Held previous = CURRENT.get();
        StrictJson.require(previous == null || CompositeContinuationNesting.authorizesPlanning(parent), "nested composite planning scope is unavailable");
        CURRENT.set(new Held(journal, journal.writerSession(), new Parent(parent.actionId(), ActionCodec.bodySha256(parent), handlerId), false,parent.deadline()));
        try { return work.run(); } finally { if (previous == null) CURRENT.remove(); else CURRENT.set(previous); }
    }
}
