package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.util.Objects;

/** The one Core mints this access object; frozen public bindings follow its actual committed host switch. */
public final class RootSessionAccess {
    private final RootApplicationAssembly.Core owner;
    private final RootCoreBoundPorts deferred;
    RootSessionAccess(RootApplicationAssembly.Core owner) { this.owner = Objects.requireNonNull(owner); deferred = null; }
    /** Pre-Core typed registration only; every invocation resolves the same once-bound real Core. */
    RootSessionAccess(RootCoreBoundPorts actual) { owner = null; deferred = Objects.requireNonNull(actual); }
    private RootApplicationAssembly.Core owner() throws IOException { return owner != null ? owner : deferred.requireCore(); }
    /** The returned owner still revalidates its host, writer and source under its own call lock before any work. */
    public RootApplicationSession current() throws IOException { return owner().currentForAccess(); }
    /** Retained replacement queries use Core's exact private attempt route; current() remains strict. */
    public RootCheckpointPublicCalls.RestoreCall restoreCheckpointPublic(RootCheckpointPublicCalls.Request request,java.time.Instant deadline)
            throws IOException,InterruptedException {
        return owner().restoreCheckpointPublic(Objects.requireNonNull(request),Objects.requireNonNull(deadline));
    }
    /** Source-owned Host binding only; this access object has no public constructor. */
    public void requireHost(org.xar.ck3.control.service.OrdinarySessionHost actual)throws IOException {
        owner().requirePublicHost(Objects.requireNonNull(actual));
    }
    public org.xar.ck3.control.application.session.BatchReport batch(String sessionId,org.xar.ck3.control.application.session.BatchLimits limits)
            throws IOException,InterruptedException {
        org.xar.ck3.control.contracts.StrictJson.text(sessionId);Objects.requireNonNull(limits);
        return withCurrent(actual->{
            org.xar.ck3.control.contracts.StrictJson.require(actual.identity().sessionId().equals(sessionId),"batch request belongs to another current Root session");
            return actual.batch(limits);
        });
    }
    @FunctionalInterface public interface Work<T> {
        T run(RootApplicationSession actualCurrent) throws IOException, InterruptedException;
    }
    public <T> T withCurrent(Work<T> work) throws IOException, InterruptedException {
        // Never hold the Core monitor while acquiring a session's call lock: restore publishes in the opposite order.
        return Objects.requireNonNull(work).run(current());
    }
}
