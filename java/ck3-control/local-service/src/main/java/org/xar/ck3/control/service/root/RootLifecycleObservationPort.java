package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.time.Instant;
import java.util.Objects;
import java.util.function.Supplier;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.CommandOrigin;
import org.xar.ck3.control.application.lifecycle.LifecycleObservationPort;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.contracts.StrictJson;

/** The lifecycle service receives actual terminal snapshots through the same physical authority, never a gameplay adapter. */
public final class RootLifecycleObservationPort implements LifecycleObservationPort {
    private final RootLifecycleAuthority authority;
    private final Supplier<ContinuityStorePort.Session> borrowed;
    public RootLifecycleObservationPort(RootLifecycleAuthority authority,Supplier<ContinuityStorePort.Session> borrowed){this.authority=Objects.requireNonNull(authority);this.borrowed=Objects.requireNonNull(borrowed);}
    @Override public Snapshot current(ActionCommand parent,Instant deadline){
        StrictJson.require(parent.origin() instanceof CommandOrigin.LifecycleTerminal,"actual lifecycle snapshot requires its terminal command origin");
        try{return authority.current(Objects.requireNonNull(borrowed.get()),parent.lifecycleBefore(),deadline,lease->{
            StrictJson.require(lease.snapshot().source().equals(parent.source())&&lease.identity().sessionId().equals(parent.sessionId()),"actual lifecycle snapshot crossed its command source/session");return lease.snapshot();
        });}catch(IOException failure){throw new UncheckedIOException("actual terminal observation unavailable",failure);}
    }
    @Override public Snapshot next(ActionCommand parent,Snapshot previous,Instant deadline){
        Objects.requireNonNull(previous);Snapshot actual=current(parent,deadline);
        StrictJson.require(previous.actual().session().equals(actual.actual().session())&&previous.source().equals(actual.source())
                &&previous.facts().driver().session().equals(actual.facts().driver().session())
                &&actual.actual().nativeRevision().compareTo(previous.actual().nativeRevision())>=0
                &&actual.revision().compareTo(previous.revision())>=0&&!actual.actual().observedAt().isBefore(previous.actual().observedAt()),"actual lifecycle next observation regressed or crossed physical old-episode scope");return actual;
    }
}
