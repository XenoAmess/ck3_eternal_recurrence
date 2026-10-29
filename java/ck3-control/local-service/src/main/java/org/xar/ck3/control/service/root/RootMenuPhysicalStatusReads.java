package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.util.Objects;
import java.util.function.Supplier;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;

/** Pre-Driver menu routing for the one installed physical Status profile. This cannot issue ordinary readiness. */
public final class RootMenuPhysicalStatusReads implements PlanningReadCoordinator.ReadGuardPort {
    private final RootExecutableBindings bindings;
    private final G2Source source;
    private final Supplier<ContinuityStorePort.Session> borrowed;
    public RootMenuPhysicalStatusReads(RootExecutableBindings bindings,G2Source actualSource,
            Supplier<ContinuityStorePort.Session> actualBorrowed) {
        this.bindings=Objects.requireNonNull(bindings);source=Objects.requireNonNull(actualSource);
        borrowed=Objects.requireNonNull(actualBorrowed);
    }
    @Override public PlanningReadGuard verify(WriterContracts.Head head,PlanningReadRequest request,ReadContract<?> contract) {
        StrictJson.require(request.origin() instanceof CommandOrigin.PhysicalStatusOnly,
                "menu physical Status source cannot authorize another origin");
        var identity=((CommandOrigin.PhysicalStatusOnly)request.origin()).identity();
        StrictJson.require(bindings.readCatalog().containsIdentity(contract)&&request.source().equals(source)
                &&request.operation().equals(contract.operation())&&identity.source().equals(source)
                &&identity.transport().sessionId().equals(request.sessionId()),
                "menu physical Status crossed its actual installed descriptor/source/session");
        PhysicalStatusIdentity.requireProfile(contract);
        try {
            var same=RootLifecycleReadGuard.session(borrowed,head);
            RootLifecycleReadGuard.pin(same,contract.sourceRef());RootLifecycleReadGuard.pin(same,source.sourceRef());
            return bindings.requirePhysicalStatusAuthority(identity).verify(head,request,contract);
        }catch(IOException failure){throw new UncheckedIOException("actual pre-Driver physical Status source unavailable",failure);}
    }
}
