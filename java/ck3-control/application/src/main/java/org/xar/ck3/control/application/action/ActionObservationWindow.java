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
    private ActionObservationWindow() { }
    public static Instant deadline(ActionCommand original) {
        Objects.requireNonNull(original); Window current = CURRENT.get();
        if (current == null) return original.deadline();
        StrictJson.require(current.actionId().equals(original.actionId()) && ActionScope.currentActionId().filter(original.actionId()::equals).isPresent(), "read-only observation window escaped its exact original action scope");
        return current.deadline();
    }
    static <T> T reconcile(String actionId, Clock clock, Supplier<T> work) {
        Window previous = CURRENT.get(); Instant deadline = clock.instant().plus(MAXIMUM_WINDOW);
        if (previous != null && previous.deadline().isBefore(deadline)) deadline = previous.deadline();
        CURRENT.set(new Window(actionId, deadline));
        try { return work.get(); } finally { if (previous == null) CURRENT.remove(); else CURRENT.set(previous); }
    }
}
