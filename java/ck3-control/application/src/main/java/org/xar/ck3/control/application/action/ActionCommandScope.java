package org.xar.ck3.control.application.action;

import java.util.Optional;
import java.util.Objects;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import java.util.function.Supplier;
import org.xar.ck3.control.contracts.StrictJson;

/** The concrete unchanged command currently owned by the one coordinator, including a registered child before INTENT. */
public final class ActionCommandScope {
    private static final ThreadLocal<ActionCommand> CURRENT = new ThreadLocal<>();
    private record ValidationContext(ContinuityStorePort.Session session, ActionCommand command, GuardEvidence guard) { }
    private static final ThreadLocal<ValidationContext> VALIDATION = new ThreadLocal<>();
    private ActionCommandScope() { }
    public static Optional<ActionCommand> current() {
        ActionCommand command = CURRENT.get();
        if (command != null) StrictJson.require(ActionScope.currentActionId().filter(command.actionId()::equals).isPresent(), "current command escaped its actual coordinator action scope");
        return Optional.ofNullable(command);
    }
    /** The already verified initial guard is DATA only during this exact pre-INTENT validation callback. */
    public static Optional<GuardEvidence> validationGuard(ActionCommand command, ContinuityStorePort.Session same) {
        ValidationContext held=VALIDATION.get();if(held==null)return Optional.empty();
        StrictJson.require(held.session()==same && current().filter(command::equals).isPresent()
                && held.command().equals(command), "validation guard escaped its actual writer or command scope");
        GuardEvidence guard=held.guard();
        StrictJson.require(guard.observed().equals(command.before()) && guard.source().equals(command.source())
                && guard.sessionId().equals(command.sessionId()) && guard.operation().equals(command.operation()),
                "validation guard differs from its exact selected command");
        return Optional.of(guard);
    }
    static void withinValidation(ActionJournal.LockedJournal locked, ActionCommand command, GuardEvidence guard, Runnable work) {
        Objects.requireNonNull(locked);Objects.requireNonNull(command);Objects.requireNonNull(guard);Objects.requireNonNull(work);
        ValidationContext previous=VALIDATION.get();
        VALIDATION.set(new ValidationContext(locked.writerSession(),command,guard));
        try {work.run();} finally {if(previous==null)VALIDATION.remove();else VALIDATION.set(previous);}
    }
    static <T> T within(ActionCommand command, Supplier<T> work) {
        ActionCommand previous = CURRENT.get(); CURRENT.set(command);
        try { return work.get(); } finally { if (previous == null) CURRENT.remove(); else CURRENT.set(previous); }
    }
}
