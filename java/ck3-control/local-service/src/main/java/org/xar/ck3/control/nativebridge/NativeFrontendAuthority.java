package org.xar.ck3.control.nativebridge;

import java.io.IOException;
import java.time.Instant;
import java.util.Objects;
import org.xar.ck3.control.application.action.FrontendIdentity;
import org.xar.ck3.control.application.effects.FrontendAuthority;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRouteAdmission.FrameMode;

/** Concrete authority over the same Root sequence; detached LeaseSnapshot values are never permissions. */
public final class NativeFrontendAuthority implements FrontendAuthority {
    private final FrontendObservationSequence sequence;
    public NativeFrontendAuthority(FrontendObservationSequence sameSequence) { sequence = Objects.requireNonNull(sameSequence); }
    /** Same sole authority and typed frontend lease; no gameplay actor, episode or Ready is manufactured. */
    public <T> T withSourceBoundFrontendRead(ContinuityStorePort.Session borrowed, FrameMode mode, Instant deadline,
            CheckedWork<T> work) throws IOException {
        return sequence.withSourceBoundFrontendRead(borrowed, mode, deadline, work);
    }
    public void requireOutsideSourceBoundFrontendRead() { sequence.requireOutsideSourceBoundFrontendRead(); }
    @Override public <T> T currentSourceBoundRead(ContinuityStorePort.Session borrowed, FrontendIdentity expected,
            Instant deadline, CheckedWork<T> work) throws IOException {
        return sequence.currentSourceBoundRead(borrowed, expected, deadline, work);
    }
    @Override public <T> T current(ContinuityStorePort.Session borrowed, FrontendIdentity expected,
            Instant deadline, CheckedWork<T> work) throws IOException {
        return sequence.current(borrowed, expected, deadline, work);
    }
}
