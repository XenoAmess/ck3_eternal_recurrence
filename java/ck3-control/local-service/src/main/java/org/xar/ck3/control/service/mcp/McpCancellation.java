package org.xar.ck3.control.service.mcp;

import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;

/** A cooperative request signal. It never interrupts a thread, cancels a native write, or asserts rollback. */
public final class McpCancellation {
    private boolean requested;
    private Optional<String> reason = Optional.empty();
    private final List<Runnable> listeners = new ArrayList<>();
    public synchronized boolean requested() { return requested; }
    public synchronized Optional<String> reason() { return reason; }
    public void onRequest(Runnable listener) {
        Objects.requireNonNull(listener);
        synchronized (this) { if (!requested) { listeners.add(listener); return; } }
        listener.run();
    }
    void request(Optional<String> actualReason) {
        List<Runnable> notify;
        synchronized (this) {
            if (requested) return;
            requested = true; reason = Objects.requireNonNull(actualReason);
            notify = List.copyOf(listeners); listeners.clear();
        }
        for (Runnable listener : notify) {
            try { listener.run(); }
            catch (RuntimeException failure) {
                // Another listener must still see the stop request. A failed listener proves no world-state change.
                System.err.println("MCP cooperative cancellation listener failed: " + failure.getClass().getName());
            }
        }
    }
}
