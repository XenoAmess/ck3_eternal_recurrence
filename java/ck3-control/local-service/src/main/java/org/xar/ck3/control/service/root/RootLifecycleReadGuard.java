package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.time.Clock;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import java.util.function.Supplier;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.effects.OriginalEvidencePort;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;

/** Only the three installed lifecycle read contracts may inspect a terminal old episode. */
public final class RootLifecycleReadGuard implements PlanningReadCoordinator.ReadGuardPort {
    private static final Set<String> READS=Set.of("query-player-prisoner-collection-private-v1","query-current-timeline-blocker-context-v1",
            "query-campaign-root-context-v1");
    private final RootLifecycleAuthority authority;private final Supplier<ContinuityStorePort.Session> borrowed;
    private final ActionPorts.OutcomeArchive archive;private final G2Source source;private final Clock clock;
    private final String authorityId;private final OriginalEvidencePort originals;private final RootReadContractCatalog catalog;
    public RootLifecycleReadGuard(RootLifecycleAuthority authority,Supplier<ContinuityStorePort.Session> borrowed,
            ActionPorts.OutcomeArchive archive,G2Source source,Clock clock,String authorityId,OriginalEvidencePort originals,RootReadContractCatalog catalog){
        this.authority=Objects.requireNonNull(authority);this.borrowed=Objects.requireNonNull(borrowed);this.archive=Objects.requireNonNull(archive);
        this.source=Objects.requireNonNull(source);this.clock=Objects.requireNonNull(clock);this.authorityId=StrictJson.text(authorityId);
        this.originals=Objects.requireNonNull(originals);this.catalog=Objects.requireNonNull(catalog);
    }
    @Override public PlanningReadGuard verify(WriterContracts.Head head,PlanningReadRequest request,ReadContract<?> contract){
        StrictJson.require(request.origin() instanceof CommandOrigin.LifecycleTerminal&&contract.guardMode()==ReadContract.GuardMode.LIFECYCLE_TERMINAL_SESSION
                &&catalog.containsIdentity(contract)&&contract.operation().equals(request.operation())&&READS.contains(request.operation().value())
                &&source.equals(request.source()),"only the exact installed dedicated terminal read/source contract is admitted");
        try{
            var session=session(borrowed,head);pin(session,source.sourceRef());pin(session,contract.sourceRef());var same=archive.withSession(session);
            return authority.current(session,request.origin().requireLifecycleTerminal(),request.deadline(),lease->{
                contract.requiredCapability().ifPresent(cap->StrictJson.require(lease.bridgeCapabilities().contains(cap),"received Native hello did not advertise the actual lifecycle query"));
                GuardEvidence binding=RootLifecycleGuardEvidence.binding(lease,source,request.sessionId(),request.operation(),request.deadline(),head,authorityId,clock,session,same,originals,Optional.empty());
                return new PlanningReadGuard(binding,new PlanningReadGuard.LifecycleTerminal(),lease.identity().bindingSha256());
            });
        }catch(IOException failure){throw new UncheckedIOException("actual terminal read source unavailable",failure);}
    }
    static ContinuityStorePort.Session session(Supplier<ContinuityStorePort.Session> supplier,WriterContracts.Head head)throws IOException{
        var same=Objects.requireNonNull(supplier.get());var actual=same.head();StrictJson.require(actual.digest().equals(head.digest())&&actual.documents().equals(head.documents())
                &&actual.absent().equals(head.absent())&&actual.indexRepairs().equals(head.indexRepairs())&&actual.snapshotNeedsRecovery()==head.snapshotNeedsRecovery(),"terminal guard does not hold the current writer Head");return same;
    }
    static void pin(ContinuityStorePort.Session same,org.xar.ck3.control.contracts.ExactRef ref)throws IOException{
        StrictJson.require(ref.bytes()>0&&java.nio.file.Path.of(ref.path()).isAbsolute(),"terminal callable must have an exact physical installed source");same.verifyPin(same.capturePin(ref,WriterContracts.MAX_PIN_BYTES));
    }
}
