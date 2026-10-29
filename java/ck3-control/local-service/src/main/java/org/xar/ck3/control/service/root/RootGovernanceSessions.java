package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.util.Objects;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.continuity.writer.ContinuityWriter;
import org.xar.ck3.control.nativebridge.capabilities.governance.GovernanceActionScope;

/** The outer action scope opens only this original writer; already borrowed callers use the explicit Session overload. */
final class RootGovernanceSessions implements GovernanceActionScope.SessionAccess {
    private final ContinuityWriter writer;
    RootGovernanceSessions(ContinuityWriter writer) { this.writer = Objects.requireNonNull(writer); }
    @Override public <T> T withSession(ActionCommand command, GovernanceActionScope.SessionWork<T> work)
            throws IOException, InterruptedException {
        Objects.requireNonNull(command); Objects.requireNonNull(work);
        try {
            return writer.locked(borrowed -> {
                writer.requireSession(borrowed);
                try { return work.run(borrowed); }
                catch (InterruptedException interrupted) { throw new InterruptedScope(interrupted); }
            });
        } catch (InterruptedScope interrupted) { Thread.currentThread().interrupt(); throw interrupted.actual; }
    }
    private static final class InterruptedScope extends RuntimeException {
        private static final long serialVersionUID = 1L;
        private final InterruptedException actual;
        InterruptedScope(InterruptedException actual) { super(actual); this.actual = actual; }
    }
}
