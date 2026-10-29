package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.time.Clock;
import java.util.Objects;
import java.util.Optional;
import java.util.function.Supplier;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.effects.OriginalEvidencePort;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;

/** The sole dispatch may authorize three canonical lifecycle composites and one independently qualified modal Close. */
public final class RootLifecycleActionGuard implements ActionPorts.GuardPort {
    @FunctionalInterface public interface CloseAdmission {
        /** Root installs the actual M3 typed Modal.canContinue/source verifier, preserving its complete original proof. */
        ExactRef verify(ContinuityStorePort.Session same,ActionCommand actual,RootLifecycleAuthority.Lease lease,
                ActionPorts.OutcomeArchive archive)throws IOException;
    }
    private final RootLifecycleAuthority authority;private final Supplier<ContinuityStorePort.Session> borrowed;
    private final ActionPorts.OutcomeArchive archive;private final G2Source source;private final Clock clock;
    private final String authorityId;private final OriginalEvidencePort originals;private final RootExecutableBindings installed;
    private final CloseAdmission closeAdmission;
    public RootLifecycleActionGuard(RootLifecycleAuthority authority,Supplier<ContinuityStorePort.Session> borrowed,ActionPorts.OutcomeArchive archive,
            G2Source source,Clock clock,String authorityId,OriginalEvidencePort originals,RootExecutableBindings installed,CloseAdmission closeAdmission){
        this.authority=Objects.requireNonNull(authority);this.borrowed=Objects.requireNonNull(borrowed);this.archive=Objects.requireNonNull(archive);
        this.source=Objects.requireNonNull(source);this.clock=Objects.requireNonNull(clock);this.authorityId=StrictJson.text(authorityId);
        this.originals=Objects.requireNonNull(originals);this.installed=Objects.requireNonNull(installed);this.closeAdmission=Objects.requireNonNull(closeAdmission);
    }
    @Override public GuardEvidence verify(WriterContracts.Head head,ActionCommand command){
        if(command.expectation() instanceof CommandExpectation.OperatorRebind)return installed.verifyOperatorAuthority(head,command);
        StrictJson.require(command.origin() instanceof CommandOrigin.LifecycleTerminal&&command.source().equals(source),
                "only a source-bound canonical lifecycle operation can enter terminal action authority");
        LifecycleExpectedPostcondition.Operation operation=command.lifecycleExpected().operation();
        boolean close=switch(operation){case DEATH_TERMINAL,CONTINUE_SUCCESSOR,START_NEXT_EPISODE->false;case CLOSE_DEATH_MODAL->true;};
        StrictJson.require(operation.key().equals(command.operation()),"terminal guard changed its exact typed lifecycle operation");
        var producer=installed.resolve(command.operation(), command.origin()).orElseThrow(()->new IllegalArgumentException("terminal operation has no actual installed callable"));
        StrictJson.require(producer.guardMode()==ReadContract.GuardMode.LIFECYCLE_TERMINAL_SESSION
                &&producer.kind()==(close?ExecutableStepBindings.Kind.ACTION:ExecutableStepBindings.Kind.COMPOSITE),"terminal native/canonical operation crossed its exact installed kind");
        try{
            var session=RootLifecycleReadGuard.session(borrowed,head);RootLifecycleReadGuard.pin(session,source.sourceRef());
            RootLifecycleReadGuard.pin(session,producer.implementationSource());RootLifecycleReadGuard.pin(session,producer.decoderSource());
            var same=archive.withSession(session);
            return authority.current(session,command.origin().requireLifecycleTerminal(),command.deadline(),lease->{
                producer.requiredCapability().ifPresent(cap->StrictJson.require(lease.bridgeCapabilities().contains(cap),"actual hello did not advertise the installed terminal native operation"));
                if(operation!=LifecycleExpectedPostcondition.Operation.DEATH_TERMINAL)StrictJson.require(lease.snapshot().paused()&&lease.snapshot().mapReady(),"this lifecycle operation requires the actual paused map");
                Optional<ExactRef> admission=Optional.empty();
                if(close){ExactRef actual=Objects.requireNonNull(closeAdmission.verify(session,command,lease,same));RootLifecycleGuardEvidence.exact(actual,same.loadMaterial(actual).bytes());RootLifecycleReadGuard.pin(session,actual);admission=Optional.of(actual);}
                lease.assertCurrent(session);
                return RootLifecycleGuardEvidence.binding(lease,source,command.sessionId(),command.operation(),command.deadline(),head,authorityId,clock,session,same,originals,admission);
            });
        }catch(IOException failure){throw new UncheckedIOException("actual terminal action source unavailable",failure);}
    }
}
