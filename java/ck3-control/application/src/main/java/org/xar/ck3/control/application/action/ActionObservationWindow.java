package org.xar.ck3.control.application.action;

import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.util.Objects;
import java.util.function.Supplier;
import org.xar.ck3.control.contracts.StrictJson;

/** A fresh bounded read/collect window for the unchanged original command. It cannot mint submission authority. */
public final class ActionObservationWindow {
    public static final Duration MAXIMUM_WINDOW = Duration.ofMinutes(2);
    private record Window(String actionId, Instant deadline) { }
    private static final ThreadLocal<Window> CURRENT = new ThreadLocal<>();
    private static final ThreadLocal<Window> RECONCILIATION_LIMIT = new ThreadLocal<>();
    private ActionObservationWindow() { }
    public static Instant deadline(ActionCommand original) {
        Objects.requireNonNull(original); Window current = CURRENT.get();
        if (current == null) return original.deadline();
        StrictJson.require(current.actionId().equals(original.actionId()) && ActionScope.currentActionId().filter(original.actionId()::equals).isPresent(), "read-only observation window escaped its exact original action scope");
        return current.deadline();
    }
    /** Coordinator-private: only its exact canonical positive-ACK ARM callback may use the actual new physical lease.
     * The enclosing parent window is historical scheduling DATA, not the timestamp of this fresh observation.
     */
    static <T>T withPhysicalArmObservation(ActionReceipt original,GuardEvidence actual,Clock clock,Supplier<T> work) {
        Window previous=CURRENT.get();String actionId=original.command().actionId();
        StrictJson.require(previous!=null&&previous.actionId().equals(actionId)
                &&ActionScope.currentActionId().filter(actionId::equals).isPresent(),"physical ARM window escaped its actual coordinator child");
        StrictJson.require(actual.origin() instanceof CommandOrigin.Reconciliation
                &&actual.origin().requireReconciliation().pending().actionId().equals(actionId)
                &&actual.source().equals(original.command().source())&&actual.sessionId().equals(original.command().sessionId()),
                "physical ARM window requires its source-issued canonical observation guard");
        Instant now=clock.instant(),maximum=now.plus(MAXIMUM_WINDOW);
        Instant until=actual.validUntil().isBefore(maximum)?actual.validUntil():maximum;
        StrictJson.require(now.isBefore(until),"actual physical ARM observation guard expired");
        CURRENT.set(new Window(actionId,until));
        try{return work.get();}finally{CURRENT.set(previous);}
    }
    /** Cap the coordinator's read of this exact original action for the duration of the call. */
    public static ActionReceipt reconcileBefore(ActionCoordinatorPort actions, String actionId, Instant deadline) {
        Objects.requireNonNull(actions);
        StrictJson.text(actionId);
        Objects.requireNonNull(deadline);
        Window previous = RECONCILIATION_LIMIT.get();
        if (previous != null && previous.actionId().equals(actionId) && previous.deadline().isBefore(deadline)) {
            deadline = previous.deadline();
        }
        RECONCILIATION_LIMIT.set(new Window(actionId, deadline));
        try {
            return actions.reconcile(actionId);
        } finally {
            if (previous == null) RECONCILIATION_LIMIT.remove();
            else RECONCILIATION_LIMIT.set(previous);
        }
    }

    static <T> T reconcile(String actionId, Clock clock, Supplier<T> work) {
        Window previous = CURRENT.get(); Instant deadline = clock.instant().plus(MAXIMUM_WINDOW);
        if (previous != null && previous.deadline().isBefore(deadline)) deadline = previous.deadline();
        Window limit = RECONCILIATION_LIMIT.get();
        if (limit != null && limit.actionId().equals(actionId) && limit.deadline().isBefore(deadline)) {
            deadline = limit.deadline();
        }
        CURRENT.set(new Window(actionId, deadline));
        try { return work.get(); } finally { if (previous == null) CURRENT.remove(); else CURRENT.set(previous); }
    }
}
