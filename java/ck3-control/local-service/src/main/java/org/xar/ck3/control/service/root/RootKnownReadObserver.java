package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.CommandOrigin;
import org.xar.ck3.control.application.action.PlanningReadCoordinator;
import org.xar.ck3.control.application.action.PlanningReadResult;
import org.xar.ck3.control.application.driver.DriverCapabilityRuntime;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.ContinuityWriter;

/** The actual ordinary cache observer is installed once on the same preexisting query coordinator. */
final class RootKnownReadObserver implements PlanningReadCoordinator.KnownReadObserver {
    private final ContinuityWriter writer;
    private volatile DriverCapabilityRuntime actual;
    private RootDeferredAuthorities.ReadGuard initialReads;
    RootKnownReadObserver(ContinuityWriter writer) { this.writer = Objects.requireNonNull(writer); }
    synchronized void initial(RootDeferredAuthorities.ReadGuard exactEntryGate) {
        if (initialReads != null || actual != null) throw new IllegalStateException("initial query observer gate already installed");
        initialReads = Objects.requireNonNull(exactEntryGate);
    }
    synchronized void bind(DriverCapabilityRuntime runtime) {
        if (actual != null) throw new IllegalStateException("ordinary cache observer already installed"); actual = Objects.requireNonNull(runtime);
    }
    @Override public void afterKnown(ContinuityStorePort.Session borrowed, org.xar.ck3.control.application.action.ReadContract<?> identicalInstalled,
            PlanningReadResult.Known<?> received) {
        try {
            writer.requireSession(borrowed); DriverCapabilityRuntime runtime = actual;
            if(runtime==null&&RootFixtureQualifiedScope.optional().isPresent())runtime=RootFixtureQualifiedScope.required().capabilities(borrowed);
            if(received.receipt().archiveVersion()==org.xar.ck3.control.application.action.PlanningReadReceipt.ArchiveVersion.PHYSICAL_STATUS_V3)return;
            if (runtime != null) { runtime.afterKnown(borrowed, identicalInstalled, received); return; }
            // Menus have no Driver cache. Initial entry's exact-contract scoped guard and its
            // own private Staged.retainRoot producer own the only pre-promotion gameplay read.
            if (received.receipt().request().origin() instanceof CommandOrigin.Frontend) return;
            if (initialReads != null && initialReads.bootstrapOnly()) return;
            throw new IOException("actual ordinary Driver cache observer is not installed");
        } catch (IOException failure) { throw new UncheckedIOException(failure); }
    }
    @Override public void afterUnavailable(ContinuityStorePort.Session borrowed,
            org.xar.ck3.control.application.action.ReadContract<?> identicalInstalled,
            org.xar.ck3.control.application.action.PlanningReadRequest request,PlanningReadResult.Unavailable<?> received) {
        try {
            writer.requireSession(borrowed);DriverCapabilityRuntime runtime=actual;
            if(runtime==null&&RootFixtureQualifiedScope.optional().isPresent())runtime=RootFixtureQualifiedScope.required().capabilities(borrowed);
            if(identicalInstalled.guardMode()==org.xar.ck3.control.application.action.ReadContract.GuardMode.STATUS_ONLY)return;
            if(runtime!=null){runtime.afterUnavailable(borrowed,identicalInstalled,request,received);return;}
            if(request.origin() instanceof CommandOrigin.Frontend)return;
            if(initialReads!=null&&initialReads.bootstrapOnly())return;
            throw new IOException("actual ordinary unavailable-query observer is not installed");
        }catch(IOException failure){throw new UncheckedIOException(failure);}
    }
    @Override public void afterUnavailable(ContinuityStorePort.Session borrowed,
            org.xar.ck3.control.application.action.ReadContract<?> identicalInstalled,
            org.xar.ck3.control.application.action.PlanningReadRequest request,PlanningReadResult.Unavailable<?> received,
            Optional<PlanningReadCoordinator.FailedReadAttempt> attempted) {
        try {
            writer.requireSession(borrowed);
            org.xar.ck3.control.application.reads.PlanningPublicReadCollection.afterUnavailable(borrowed,identicalInstalled,request,received,attempted);
            if(identicalInstalled.guardMode()==org.xar.ck3.control.application.action.ReadContract.GuardMode.STATUS_ONLY)return;
            DriverCapabilityRuntime runtime=actual;
            if(runtime==null&&RootFixtureQualifiedScope.optional().isPresent())runtime=RootFixtureQualifiedScope.required().capabilities(borrowed);
            if(runtime!=null){runtime.afterUnavailable(borrowed,identicalInstalled,request,received,attempted);return;}
            if(request.origin() instanceof CommandOrigin.Frontend)return;
            if(initialReads!=null&&initialReads.bootstrapOnly())return;
            throw new IOException("actual ordinary unavailable-query observer is not installed");
        }catch(IOException failure){throw new UncheckedIOException(failure);}
    }
}

