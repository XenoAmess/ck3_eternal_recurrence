package org.xar.ck3.control.application.action;

import java.util.Optional;
import java.util.function.Supplier;

/** Read-only current custody marker for Driver SAVE. Only the coordinator package can enter a scope. */
public final class ActionScope {
    private static final ThreadLocal<String> CURRENT = new ThreadLocal<>();
    private ActionScope() { }
    public static Optional<String> currentActionId() { return Optional.ofNullable(CURRENT.get()); }
    static <T> T run(String actionId, Supplier<T> operation) {
        String previous = CURRENT.get(); CURRENT.set(actionId);
        try { return operation.get(); } finally { if (previous == null) CURRENT.remove(); else CURRENT.set(previous); }
    }
}
