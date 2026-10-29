package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.time.Clock;
import java.util.Objects;
import java.util.function.Supplier;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.effects.OriginalEvidencePort;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;

/** The one existing Root catalog routes only active, exact original-intent pure reconciliation reads here. */
public final class RootReconciliationReadGuard implements PlanningReadCoordinator.ReadGuardPort {
    private final RootReconciliationAuthority authority;
    private final Supplier<ContinuityStorePort.Session> borrowed;
    private final ActionPorts.OutcomeArchive archive;
    private final G2Source source;
    private final Clock clock;
    private final String authorityId;
    private final OriginalEvidencePort originals;
    private final RootReadContractCatalog catalog;
    public RootReconciliationReadGuard(RootReconciliationAuthority authority,Supplier<ContinuityStorePort.Session> borrowed,
            ActionPorts.OutcomeArchive archive,G2Source source,Clock clock,String authorityId,
            OriginalEvidencePort originals,RootReadContractCatalog catalog) {
        this.authority=Objects.requireNonNull(authority);this.borrowed=Objects.requireNonNull(borrowed);
        this.archive=Objects.requireNonNull(archive);this.source=Objects.requireNonNull(source);this.clock=Objects.requireNonNull(clock);
        this.authorityId=StrictJson.text(authorityId);this.originals=Objects.requireNonNull(originals);this.catalog=Objects.requireNonNull(catalog);
    }
    @Override public PlanningReadGuard verify(WriterContracts.Head head,PlanningReadRequest request,ReadContract<?> contract) {
        StrictJson.require(request.origin() instanceof CommandOrigin.Reconciliation
                &&contract.guardMode()==ReadContract.GuardMode.RECONCILIATION_OBSERVATION
                &&catalog.containsIdentity(contract)&&request.operation().equals(contract.operation())
                &&source.equals(request.source())&&clock.instant().isBefore(request.deadline()),
                "only an identical installed active reconciliation read/source contract is eligible");
        try {
            var same=RootLifecycleReadGuard.session(borrowed,head);
            RootLifecycleReadGuard.pin(same,source.sourceRef());
            return authority.current(same,request.origin().requireReconciliation(),request.deadline(),lease->{
                GuardEvidence binding=authority.binding(lease,same,request,contract,head,authorityId);
                return new PlanningReadGuard(binding,new PlanningReadGuard.Reconciliation(),lease.identity().bindingSha256());
            });
        } catch(IOException failure) {throw new UncheckedIOException("actual original-pending reconciliation read unavailable",failure);}
    }
}

