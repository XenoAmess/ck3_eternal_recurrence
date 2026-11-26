package org.xar.ck3.control.service.root;

import static org.xar.ck3.control.contracts.StrictJson.require;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.time.Instant;
import java.util.Arrays;
import java.util.Optional;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.ActionIds;
import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.action.ActionState;
import org.xar.ck3.control.application.action.ActionTransitions;
import org.xar.ck3.control.application.action.CommandOrigin;
import org.xar.ck3.control.application.action.ContinuityActionJournal;
import org.xar.ck3.control.application.action.NativeActionPort.AckReceived;
import org.xar.ck3.control.application.advance.AdvancePlan;
import org.xar.ck3.control.application.advance.AdvancePolicy;
import org.xar.ck3.control.application.advance.AdvancePrimitives;
import org.xar.ck3.control.application.advance.LifeAdvanceComposite;
import org.xar.ck3.control.application.advance.ResumeCoreObservation;
import org.xar.ck3.control.application.driver.DriverObservationAssembler;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.nativebridge.FullSnapshotClockControlResult;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFramePublicCodec;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Replays only the running-state effect of one exact Full111 campaign resume. */
final class RootResumeCoreEvidence {
    private static final ExactCk3Build BUILD = ExactCk3Build.CK3_121003_STEAM_26785313_FULL111;
    private static final String RESUME = "resume-map";

    private RootResumeCoreEvidence() { }

    static boolean supports(ActionCommand parent, ActionCommand child) {
        if (!parent.operation().value().equals("life-advance") || !child.operation().value().equals(RESUME)
                || !BUILD.executableSha256().equalsIgnoreCase(parent.source().exactBuild())
                || !(parent.origin() instanceof CommandOrigin.Gameplay)
                || !(child.origin() instanceof CommandOrigin.Gameplay)) return false;
        var plan = AdvancePlan.decode(parent);
        return plan.clockMode() == AdvancePlan.ClockMode.CAMPAIGN_SENTINEL && plan.horizonDays() > 1
                && !plan.exactOneDay() && plan.dailyWatch().isEmpty();
    }

    static void requireOriginals(ActionReceipt parent, ActionReceipt child, ActionState.Attempt attempt, AckReceived acknowledged) {
        require(parent.state() instanceof ActionState.CompositeRunning running
                        && running.execution().handlerId().equals(LifeAdvanceComposite.HANDLER)
                        && !running.execution().children().isEmpty()
                        && reservedLast(parent, child, running.execution())
                        && parent.bodySha256().equals(ActionCodec.bodySha256(parent.command()))
                        && parent.sequence() < child.sequence()
                        && ActionTransitions.attempt(child.state()).filter(attempt::equals).isPresent()
                        && child.ack().filter(acknowledged::equals).isPresent(),
                "Core resume proof requires its actual running Life reservation and original acknowledged child");
    }

    private static boolean reservedLast(ActionReceipt parent, ActionReceipt child,
            org.xar.ck3.control.application.action.CompositeExecution execution) {
        var reserved = execution.children().getLast();
        return reserved.actionId().equals(child.command().actionId()) && reserved.bodySha256().equals(child.bodySha256())
                && child.command().actionId().equals(ActionIds.child(parent.command().actionId(),
                        execution.children().size(), child.command().operation()));
    }

    static void replay(ActionReceipt child, ResumeCoreObservation proof, DriverObservationAssembler.Complete before,
            Optional<WriterContracts.Head> head, ActionPorts.OutcomeArchive archive) {
        var parent = archive.loadReceipt(proof.parentReceipt());
        require(proof.parentReceipt().equals(archive.receiptReferenceOf(parent)),
                "Core resume proof changed its original Life receipt");
        var sample = archive.load(proof.coreAcknowledgement());
        require(sample instanceof AckReceived && proof.coreAcknowledgement().equals(archive.referenceOf(sample)),
                "Core resume proof changed its original sampled ACK");
        head.ifPresent(actual -> {
            var current = ContinuityActionJournal.lookup(actual.state(), parent.command().actionId(), archive);
            if (current.filter(parent::equals).isEmpty())
                ContinuityActionJournal.requireHistoricalReceipt(actual.state(), parent, archive);
        });
        var attempt = ActionTransitions.attempt(child.state()).orElseThrow();
        var acknowledged = child.ack().orElseThrow();
        requireOriginals(parent, child, attempt, acknowledged);
        try {
            verify(parent.command(), child.command(), attempt, acknowledged, (AckReceived) sample,
                    proof.observationDeadline(), before);
        } catch (IOException invalid) {
            throw new UncheckedIOException("original RESUME Core replay failed", invalid);
        }
    }

    static CoreFrame.Prefix verify(ActionCommand parent, ActionCommand child, ActionState.Attempt attempt,
            AckReceived resume, AckReceived sample, Instant deadline, DriverObservationAssembler.Complete before)
            throws IOException {
        require(supports(parent, child), "Core resume confirmation requires an original Full111 multi-day Life");
        var plan = AdvancePlan.decode(parent);
        require(parent.source().equals(child.source()) && parent.sessionId().equals(child.sessionId())
                        && parent.claims().equals(child.claims())
                        && parent.before().game().equals(child.before().game())
                        && parent.before().frame().episodeRunId().equals(child.before().frame().episodeRunId())
                        && parent.before().frame().identity().player().equals(child.before().frame().identity().player())
                        && parent.before().frame().identity().dateRaw().equals(plan.startingDateRaw())
                        && child.before().frame().identity().dateRaw().equals(plan.startingDateRaw())
                        && parent.deadline().equals(child.deadline()) && !deadline.isAfter(child.deadline())
                        && child.arguments().members().isEmpty()
                        && child.expected().equals(AdvancePrimitives.expected(child.before(), child.source(),
                                child.operation(), child.arguments())),
                "Core resume proof crossed the original Life, child or deadline");
        require(before.identity().equals(child.before()) && before.source().equals(child.source())
                        && before.sessionId().equals(child.sessionId())
                        && before.connectionGeneration().equals(attempt.guard().connectionGeneration())
                        && before.originalEvidence().equals(attempt.guard().nativeEvidence())
                        && AdvancePolicy.truth(before.semantic(), "paused") && AdvancePolicy.truth(before.semantic(), "map_ready"),
                "Core resume proof requires the original paused Full starting frame");

        var result = FullSnapshotClockControlResult.decode(resume, RESUME);
        var resumeToken = NativeWire.object(NativeWire.parse(resume.originalResultToken().orElseThrow().bytes()));
        var profile = ExactCk3Build.florinCoreFullBuild(NativeWire.text(resumeToken.get("game_version")),
                NativeWire.text(resumeToken.get("executable_sha256")), NativeWire.text(resumeToken.get("adapter_id")));
        var outbound = NativeWire.decodeExecuteRequest(resume.outbound().orElseThrow().originalPacket());
        require(profile.orElse(null) == BUILD && result.queueStatus().equals("submitted")
                        && resume.requestId().equals(attempt.requestId())
                        && outbound.expectedRevision().filter(child.before().frame().identity().nativeRevision()::equals).isPresent()
                        && Arrays.equals(outbound.normalizedAdditionalFields().value(), attempt.preparedRequest().additionalFields().bytes()),
                "Core resume proof requires the actual queued Full111 child and unchanged prepared outbound");
        var write = resume.custody().orElseThrow();
        write.verify(resume, attempt.guard());
        require(!write.writeEntered().observedAt().isBefore(attempt.submittedAt()),
                "RESUME write predates its canonical attempt");

        var core = CoreFramePublicCodec.decodeOutcome(sample);
        require(core instanceof CoreFrame.Partial && core.build() == BUILD,
                "Core resume proof requires an available Full111 prefix");
        var read = sample.custody().orElseThrow();
        read.verify(sample);
        require(!resume.requestId().equals(sample.requestId())
                        && write.session().equals(read.session()) && write.custodyEpoch().equals(read.custodyEpoch())
                        && read.writeEntered().order().compareTo(write.responseReceived().order()) > 0
                        && !read.writeEntered().observedAt().isBefore(write.responseReceived().observedAt())
                        && read.responseReceived().observedAt().isBefore(deadline),
                "Core resume sample must follow the actual ACK in its original held connection and time window");

        var prefix = ((CoreFrame.Partial) core).prefix();
        var date = BigInteger.valueOf(prefix.dateRaw());
        var player = OpportunityJson.integer(before.semantic().get("local_player_id"), "original Full local_player_id");
        require(!prefix.paused() && prefix.mapReady() && prefix.hasPlayedCharacter() && prefix.playedCharacterAlive()
                        && prefix.speed() == plan.speed() && player.equals(BigInteger.valueOf(prefix.localPlayerId()))
                        && child.before().frame().identity().player().equals(BigInteger.valueOf(prefix.playedCharacterId()))
                        && date.compareTo(plan.startingDateRaw()) >= 0 && date.compareTo(plan.targetDateRaw()) <= 0,
                "Core resume sample lacks the running original actor, clock speed or date range");
        return prefix;
    }
}
