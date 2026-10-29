package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.util.Objects;

/** One in-memory construction attempt attached to an actual retained Root restore.
 * Entered, failed and unknown construction never authorizes another runtime/observer bind. */
final class RetainedRuntimeCreation<T> {
    @FunctionalInterface interface Producer<T> { T create() throws IOException; }
    private enum Phase { FRESH, ENTERED, COMPLETE, FAILED_OR_UNKNOWN }
    private Phase phase = Phase.FRESH;
    private T retained;

    synchronized T obtain(Producer<T> producer) throws IOException {
        Objects.requireNonNull(producer);
        if (phase == Phase.COMPLETE) return retained;
        if (phase != Phase.FRESH)
            throw new IOException("Original restored runtime construction entered or failed; observer binding cannot replay");
        phase = Phase.ENTERED;
        try {
            T actual = Objects.requireNonNull(producer.create(), "actual restored runtime producer returned null");
            retained = actual;
            phase = Phase.COMPLETE;
            return actual;
        } catch (IOException | RuntimeException | Error failure) {
            phase = Phase.FAILED_OR_UNKNOWN;
            throw failure;
        }
    }
}
