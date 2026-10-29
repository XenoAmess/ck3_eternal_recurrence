package org.xar.ck3.control.application.effects;

import java.io.IOException;
import java.time.Clock;
import java.time.Instant;
import java.util.Objects;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.action.council.CouncilContinuationPorts;
import org.xar.ck3.control.application.readiness.ReadinessAuthority;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;

/** Fresh observation custody for one already submitted Council helper. It cannot authorize a new action. */
public final class RootCouncilContinuationGuard implements CouncilContinuationPorts.GuardPort {
    private final ReadinessAuthority readiness;
    private final ActionPorts.OutcomeArchive archive;
    private final G2Source source;
    private final Clock clock;
    private final String authorityId;
    private final OriginalEvidencePort originals;
    private final RootExecutableBindings installed;
    public RootCouncilContinuationGuard(ReadinessAuthority actualReadiness, ActionPorts.OutcomeArchive sameArchive,
            G2Source exactSource, Clock clock, String authorityId, OriginalEvidencePort originals, RootExecutableBindings actualInstalled) {
        readiness = Objects.requireNonNull(actualReadiness); archive = Objects.requireNonNull(sameArchive); source = Objects.requireNonNull(exactSource);
        this.clock = Objects.requireNonNull(clock); this.authorityId = StrictJson.text(authorityId); this.originals = Objects.requireNonNull(originals); installed = Objects.requireNonNull(actualInstalled);
    }
    @Override public GuardEvidence current(ContinuityStorePort.Session same, WriterContracts.Head head, ActionReceipt originalParent, Instant deadline) throws IOException {
        Objects.requireNonNull(originalParent); Objects.requireNonNull(deadline); RootGuardChecks.session(() -> same, head);
        var command = originalParent.command();
        StrictJson.require(command.operation().value().equals("private-assign-councillor-v1") && command.origin() instanceof CommandOrigin.Gameplay
                && command.source().equals(source) && originalParent.state() instanceof ActionState.AckReceived,
                "only the actual live private Council ACK may request a new continuation; UNKNOWN is collect-only");
        var attempt = ((ActionState.AckReceived) originalParent.state()).attempt(); var ack = ((ActionState.AckReceived) originalParent.state()).dispatch();
        StrictJson.require(ack.nativeOk() && ack.outbound().isPresent() && ack.requestId().equals(attempt.requestId())
                && attempt.preparedRequest().step().equals(command.operation().value()) && attempt.guard().authorityId().equals(authorityId),
                "original Council ACK/outbound/attempt/authority custody is unavailable");
        Instant observationDeadline = ActionObservationWindow.deadline(command);
        Instant effectiveDeadline = deadline.isBefore(observationDeadline) ? deadline : observationDeadline;
        StrictJson.require(clock.instant().isBefore(effectiveDeadline), "Council continuation deadline expired");
        var sameArchive = archive.withSession(same);
        var canonical = ContinuityActionJournal.lookup(head.state(), command.actionId(), sameArchive).orElseThrow(() -> new IllegalArgumentException("canonical original Council action is absent"));
        StrictJson.require(canonical.equals(originalParent) && ack.equals(sameArchive.load(sameArchive.referenceOf(ack)))
                && attempt.preparedRequest().equals(sameArchive.loadRequest(sameArchive.requestReferenceOf(attempt.preparedRequest()))), "detached or changed original Council parent/packet/request");
        RootGuardEvidence.body(attempt.guard(), sameArchive);
        var binding = installed.actualActionBinding(command.operation()).orElseThrow(() -> new IllegalArgumentException("original exact Council callable was not retained"));
        var descriptor = installed.resolve(command.operation()).orElseThrow(() -> new IllegalArgumentException("original exact Council descriptor was not retained"));
        StrictJson.require(descriptor.kind() == ExecutableStepBindings.Kind.ACTION && descriptor.guardMode() == ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP
                && descriptor.implementationSource().equals(binding.producerSource())
                && installed.actualArchivedVerifier(command.operation()).isPresent(), "original Council callable has no exact gameplay/archive binding");
        RootGuardChecks.source(same, source.sourceRef()); RootGuardChecks.source(same, binding.producerSource()); RootGuardChecks.source(same, descriptor.decoderSource());
        return readiness.current(same, command.before(), effectiveDeadline, actual -> {
            RootGuardChecks.session(() -> same, head); RootGuardChecks.livingPaused(actual);
            var before = attempt.guard().observed(); var current = actual.frame().identity();
            StrictJson.require(current.machineId().equals(before.machineId()) && current.game().equals(before.game())
                    && current.frame().episodeRunId().equals(before.frame().episodeRunId()) && current.frame().identity().player().equals(before.frame().identity().player())
                    && current.frame().identity().nativeRevision().compareTo(before.frame().identity().nativeRevision()) >= 0
                    && actual.frame().connectionGeneration().equals(attempt.guard().connectionGeneration()), "Council continuation changed the original held Game/actor/episode/connection");
            descriptor.requiredCapability().ifPresent(cap -> StrictJson.require(actual.bridgeCapabilities().contains(cap), "original Council capability is no longer advertised"));
            // A pending helper need not still appear in the ordinary executable action set.
            return RootGuardChecks.binding(actual, command.origin(), source, command.sessionId(), command.operation(), effectiveDeadline,
                    sameArchive, clock, head, authorityId, same, originals);
        });
    }
}
