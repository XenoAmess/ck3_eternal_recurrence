package org.xar.ck3.control.application.action;

import java.io.IOException;
import java.time.Instant;
import java.util.Objects;
import java.util.concurrent.atomic.AtomicBoolean;
import org.xar.ck3.control.contracts.presentation.PresentationRequest;
import org.xar.ck3.control.contracts.presentation.PresentationIntent;

/** A one-use original writer permit, not a public capability or serializable qualification. */
public final class PresentationPermit implements PhysicalSubmission {
    @FunctionalInterface interface Check { void verify() throws IOException; }
    private final PresentationRequest exact; private final PresentationIntent deferred; private final Instant deadline; private final Check check;
    private final AtomicBoolean consumed = new AtomicBoolean();
    PresentationPermit(PresentationRequest exact, Instant deadline, Check check) {
        this.deferred = null; this.exact = Objects.requireNonNull(exact); this.deadline = Objects.requireNonNull(deadline); this.check = Objects.requireNonNull(check);
    }
    PresentationPermit(PresentationIntent intent,Check immutableOwnerCheck) {
        exact=null;deferred=Objects.requireNonNull(intent);deadline=intent.deadline();check=Objects.requireNonNull(immutableOwnerCheck);
    }
    public void consume(PresentationIntent.Prepared actual,Instant actualDeadline) throws IOException {
        if(!consumed.compareAndSet(false,true))throw new IOException("original presentation permit already consumed; no replay");
        if(deferred==null||!deadline.equals(actualDeadline)||!java.util.Arrays.equals(deferred.encode(),actual.intent().encode()))
            throw new IOException("deferred presentation changed its durable intent");
        check.verify();
    }
    public void consume(PresentationRequest request, Instant actualDeadline) throws IOException {
        if (!consumed.compareAndSet(false, true)) throw new IOException("original presentation permit is already consumed");
        if (exact==null || !deadline.equals(actualDeadline) || !java.util.Arrays.equals(exact.encode(), Objects.requireNonNull(request).encode()))
            throw new IOException("presentation permit changed its exact original prepared request or deadline");
        check.verify();
    }
}
