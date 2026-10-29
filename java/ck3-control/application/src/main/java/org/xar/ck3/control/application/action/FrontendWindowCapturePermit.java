package org.xar.ck3.control.application.action;

import java.io.IOException;
import java.time.Instant;
import java.util.Objects;
import java.util.concurrent.atomic.AtomicBoolean;
import org.xar.ck3.control.contracts.presentation.FrontendWindowCaptureRequest;

/** A one-use original writer permit for the actual Win32 frontend capture plane. */
public final class FrontendWindowCapturePermit implements PhysicalSubmission {
    private final FrontendWindowCaptureRequest exact; private final Instant deadline; private final PresentationPermit.Check check;
    private final AtomicBoolean consumed = new AtomicBoolean();
    FrontendWindowCapturePermit(FrontendWindowCaptureRequest exact, Instant deadline, PresentationPermit.Check check) {
        this.exact = Objects.requireNonNull(exact); this.deadline = Objects.requireNonNull(deadline); this.check = Objects.requireNonNull(check);
    }
    public void consume(FrontendWindowCaptureRequest request, Instant actualDeadline) throws IOException {
        if (!consumed.compareAndSet(false, true)) throw new IOException("original frontend capture permit is already consumed");
        if (!deadline.equals(actualDeadline) || !java.util.Arrays.equals(exact.encode(), Objects.requireNonNull(request).encode()))
            throw new IOException("frontend capture permit changed its exact original request or deadline");
        check.verify();
    }
}
