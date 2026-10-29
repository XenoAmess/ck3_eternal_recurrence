package org.xar.ck3.control.application.action;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.util.Objects;
import java.util.Optional;
import java.util.function.Supplier;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.contracts.StrictJson;

/** One synchronous forwarding adapter. It carries no source permission and cannot outlive the original call. */
final class DirectFixedWindowQueryInvocation {
    private static final ThreadLocal<Invocation> ACTIVE = new ThreadLocal<>();
    private static final class Invocation {
        final Session borrowed;
        final DirectFixedWindowQueryContinuation token;
        boolean claimed;
        Invocation(Session borrowed, DirectFixedWindowQueryContinuation token) {
            this.borrowed = borrowed; this.token = Objects.requireNonNull(token);
        }
    }
    private DirectFixedWindowQueryInvocation() { }
    static ActionReceipt forward(Session borrowed, DirectFixedWindowQueryContinuation token, Supplier<ActionReceipt> work)
            throws IOException {
        StrictJson.require(ACTIVE.get() == null, "nested direct query forwarding is unavailable");
        Invocation invocation = new Invocation(borrowed, token); ACTIVE.set(invocation);
        try {
            ActionReceipt actual = Objects.requireNonNull(work.get());
            StrictJson.require(invocation.claimed, "original central query reducer was not reached");
            return actual;
        } catch (UncheckedIOException failure) { throw failure.getCause(); }
        finally { ACTIVE.remove(); }
    }
    static Optional<DirectFixedWindowQueryContinuation> claim(Session same, String actionId) {
        Invocation invocation = ACTIVE.get();
        if (invocation == null) return Optional.empty();
        StrictJson.require(!invocation.claimed && invocation.token.actionId().equals(actionId)
                && (invocation.borrowed == null || invocation.borrowed == same),
                "direct query adapter crossed its original action/Session or was consumed twice");
        invocation.claimed = true; return Optional.of(invocation.token);
    }
}
