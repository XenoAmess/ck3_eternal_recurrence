package org.xar.ck3.control.application.action;

import java.util.Optional;
import java.util.function.Supplier;
import org.xar.ck3.control.contracts.StrictJson;

/** The concrete unchanged command currently owned by the one coordinator, including a registered child before INTENT. */
public final class ActionCommandScope {
    private static final ThreadLocal<ActionCommand> CURRENT = new ThreadLocal<>();
    private ActionCommandScope() { }
    public static Optional<ActionCommand> current() {
        ActionCommand command = CURRENT.get();
        if (command != null) StrictJson.require(ActionScope.currentActionId().filter(command.actionId()::equals).isPresent(), "current command escaped its actual coordinator action scope");
        return Optional.ofNullable(command);
    }
    static <T> T within(ActionCommand command, Supplier<T> work) {
        ActionCommand previous = CURRENT.get(); CURRENT.set(command);
        try { return work.get(); } finally { if (previous == null) CURRENT.remove(); else CURRENT.set(previous); }
    }
}
