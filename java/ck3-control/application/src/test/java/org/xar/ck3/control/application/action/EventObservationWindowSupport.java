package org.xar.ck3.control.application.action;

import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.function.Supplier;

/** Test-only entry through the existing package-confined coordinator observation scope. */
public final class EventObservationWindowSupport {
    private EventObservationWindowSupport() { }
    public static <T> T reconcile(ActionCommand command, Instant now, Supplier<T> work) {
        return ActionScope.run(command.actionId(), () -> ActionObservationWindow.reconcile(
            command.actionId(), Clock.fixed(now, ZoneOffset.UTC), work));
    }
}
