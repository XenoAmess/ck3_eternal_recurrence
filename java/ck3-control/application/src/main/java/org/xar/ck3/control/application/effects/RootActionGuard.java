package org.xar.ck3.control.application.effects;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.time.Clock;
import java.util.Map;
import java.util.Objects;
import java.util.function.Supplier;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.readiness.ReadinessAuthority;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;

/** Gameplay branch of the sole Root guard. Frontend/lifecycle permission needs its own real provider. */
public final class RootActionGuard implements ActionPorts.GuardPort {
    @FunctionalInterface public interface DerivedChildAdmission {
        /** Actual durable parent, child reservation, source/preflight replay and domain claim must produce this immutable original proof. */
        ExactRef verify(ContinuityStorePort.Session borrowed, WriterContracts.Head actualHead, ActionCommand child,
                ReadinessAuthority.LeaseSnapshot actualFrame, ExecutableStepBindings.InstalledStep actualDefinition,
                ActionPorts.OutcomeArchive archive) throws IOException;
        /** Actual physical DATA is separate from ordinary Ready; only the installed source may qualify this branch. */
        default ExactRef verifyPhysical(ContinuityStorePort.Session borrowed, WriterContracts.Head actualHead, ActionCommand child,
                ReadinessAuthority.PhysicalReadLease actualFrame, ExecutableStepBindings.InstalledStep actualDefinition,
                ActionPorts.OutcomeArchive archive) throws IOException {
            throw new IOException("actual source-owned physical derived-child admission is not installed");
        }
    }
    private final ReadinessAuthority authority;
    private final Supplier<ContinuityStorePort.Session> borrowedSession;
    private final ActionPorts.OutcomeArchive archive;
    private final G2Source expectedSource;
    private final Clock clock;
    private final String authorityId;
    private final OriginalEvidencePort originals;
    private final RootExecutableBindings installed;
    private final DerivedChildAdmission derivedChildren;
    public RootActionGuard(ReadinessAuthority authority, Supplier<ContinuityStorePort.Session> borrowedSession,
            ActionPorts.OutcomeArchive archive, G2Source expectedSource, Clock clock, String authorityId, OriginalEvidencePort originals, RootExecutableBindings installed) {
        this(authority,borrowedSession,archive,expectedSource,clock,authorityId,originals,installed,
                (borrowed,head,child,frame,definition,original) -> { throw new IOException("actual derived-child admission is not installed"); });
    }
    public RootActionGuard(ReadinessAuthority authority, Supplier<ContinuityStorePort.Session> borrowedSession,
            ActionPorts.OutcomeArchive archive, G2Source expectedSource, Clock clock, String authorityId, OriginalEvidencePort originals,
            RootExecutableBindings installed, DerivedChildAdmission derivedChildren) {
        this.authority = Objects.requireNonNull(authority); this.borrowedSession = Objects.requireNonNull(borrowedSession);
        this.archive = Objects.requireNonNull(archive); this.expectedSource = Objects.requireNonNull(expectedSource);
        this.clock = Objects.requireNonNull(clock); this.authorityId = StrictJson.text(authorityId); this.installed = Objects.requireNonNull(installed);
        this.originals = Objects.requireNonNull(originals);
        this.derivedChildren = Objects.requireNonNull(derivedChildren);
    }
    @Override public GuardEvidence verify(WriterContracts.Head actualLockedHead, ActionCommand command) {
        Objects.requireNonNull(command); Objects.requireNonNull(actualLockedHead);
        if(command.expectation() instanceof CommandExpectation.OperatorRebind)return installed.verifyOperatorAuthority(actualLockedHead,command);
        StrictJson.require(command.source().equals(expectedSource), "Root action source changed");
        StrictJson.require(command.origin() instanceof CommandOrigin.Gameplay, "frontend action requires the independent frontend authority");
        var definition = installed.resolve(command.operation(), command.origin()).orElseThrow(() -> new IllegalArgumentException("operation has no installed real action/composite producer"));
        StrictJson.require((definition.kind() == ExecutableStepBindings.Kind.ACTION || definition.kind() == ExecutableStepBindings.Kind.COMPOSITE)
                && definition.guardMode() == ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP, "ordinary guard cannot authorize an installed read/frontend operation");
        try {
            var session = RootGuardChecks.session(borrowedSession, actualLockedHead);
            if(RootExecutableBindings.isPublicPauseParent(command)) {
                var actual=installed.requirePublicPauseAuthority(command);
                GuardEvidence binding=Objects.requireNonNull(actual.verifyParent(actualLockedHead,command));
                StrictJson.require(command.origin().acceptsGuard(binding.origin())&&binding.source().equals(command.source())
                        &&binding.sessionId().equals(command.sessionId())&&binding.operation().equals(command.operation()),
                        "actual public pause issuer changed its exact parent guard");
                return binding;
            }
            var sameWriterArchive = archive.withSession(session);
            boolean reservedPause = definition.kind() == ExecutableStepBindings.Kind.ACTION
                    && command.operation().value().equals("pause-map")
                    && ActionChildPlanningScope.reservedParent(session,actualLockedHead,command).isPresent();
            boolean publicPauseChild=false;
            if(reservedPause) {
                var reserved=ActionChildPlanningScope.reservedParent(session,actualLockedHead,command).orElseThrow();
                var parent=ContinuityActionJournal.lookup(actualLockedHead.state(),reserved.actionId(),sameWriterArchive).orElseThrow();
                publicPauseChild=RootExecutableBindings.isPublicPauseParent(parent.command());
            }
            final boolean sourceOwnedPublicPause=publicPauseChild;
            if(reservedPause) {
                var running = authority.currentDerivedCleanup(session,command.before(),command.deadline(),physical -> {
                    if(!sourceOwnedPublicPause&&org.xar.ck3.control.planning.opportunity.OpportunityJson.bool(physical.frame().semantic().get("paused"),"paused"))
                        return java.util.Optional.<GuardEvidence>empty();
                    // The public source owns its exact first map-unavailable attempt and at most one qualified retry.
                    // Internal Life/Battle cleanup retains every original living/map qualification.
                    if(!sourceOwnedPublicPause)RootGuardChecks.livingMap(physical);
                    ExactRef proof=verifyProof(session,derivedChildren.verifyPhysical(session,actualLockedHead,command,physical,definition,sameWriterArchive));
                    definition.requiredCapability().ifPresent(cap -> StrictJson.require(physical.bridgeCapabilities().contains(cap),
                            "actual bridge did not advertise the installed cleanup capability"));
                    GuardEvidence binding=RootGuardChecks.binding(physical,command.origin(),command.source(),command.sessionId(),command.operation(),
                            command.deadline(),sameWriterArchive,clock,actualLockedHead,authorityId,session,originals);
                    return java.util.Optional.of(withDerived(binding,proof));
                });
                if(running.isPresent())return running.orElseThrow();
                // A paused physical DATA frame cannot grant ordinary Ready. Its scope is now closed.
            }
            return authority.current(session, command.before(), command.deadline(), lease -> {
                RootGuardChecks.livingPaused(lease);
                java.util.Optional<ExactRef> derived = java.util.Optional.empty();
                if (!lease.executableSteps().contains(command.operation())) {
                    StrictJson.require(definition.kind() == ExecutableStepBindings.Kind.ACTION, "a composite cannot borrow a derived native-child permit");
                    derived = java.util.Optional.of(verifyProof(session,derivedChildren.verify(session,actualLockedHead,command,lease,definition,sameWriterArchive)));
                }
                definition.requiredCapability().ifPresent(cap -> StrictJson.require(lease.bridgeCapabilities().contains(cap), "actual bridge did not advertise the installed action capability"));
                GuardEvidence binding=RootGuardChecks.binding(lease, command.origin(), command.source(), command.sessionId(), command.operation(), command.deadline(), sameWriterArchive, clock, actualLockedHead, authorityId, session, originals);
                if (derived.isEmpty()) return binding;
                return withDerived(binding,derived.orElseThrow());
            });
        } catch (IOException failure) { throw new UncheckedIOException("actual Root action authority unavailable", failure); }
    }
    private ExactRef verifyProof(ContinuityStorePort.Session session,ExactRef actual) throws IOException {
        ExactRef proof=Objects.requireNonNull(actual);
        StrictJson.require(proof.bytes()>0&&proof.bytes()<=16*1024*1024,"actual bounded derived-child original proof required");
        byte[] raw=originals.read(session,proof,16*1024*1024);
        StrictJson.require(raw.length==proof.bytes()&&ActionCodec.sha256(raw).equals(proof.sha256()),"actual derived-child proof differs from canonical immutable original");
        session.verifyPin(session.capturePin(proof,16*1024*1024));return proof;
    }
    private static GuardEvidence withDerived(GuardEvidence binding,ExactRef proof) {
        var supporting=new java.util.LinkedHashSet<>(binding.supportingEvidence());supporting.add(proof);
        return new GuardEvidence(binding.origin(),binding.source(),binding.sessionId(),binding.connectionGeneration(),binding.operation(),
                binding.nativeEvidence(),binding.capabilityEvidence(),binding.authorityId(),binding.observedAt(),binding.validUntil(),java.util.List.copyOf(supporting));
    }
}

