package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.io.InterruptedIOException;
import java.time.Instant;
import java.util.Objects;
import org.xar.ck3.control.application.driver.*;
import org.xar.ck3.control.application.readiness.NativeReadinessCollector;
import org.xar.ck3.control.application.session.SessionPorts;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.ContinuityWriter;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.NativeGameTransport;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** One ordinary observer and the existing lifecycle policy share the owned physical session; no terminal gameplay identity is fabricated. */
final class RootSessionObservationPort implements SessionPorts.ObservationPort {
    private final ContinuityWriter writer;
    private final RootApplicationAssembly.Core core;
    private final NativeReadinessCollector ordinary;
    private final RootLifecycleAuthority terminal;
    private final TerminalLifecycleDecisionProducer decisions;
    private final DriverStateAssembler driver;
    private final NativeGameTransport transport;
    private final RootLifecycleRuntimeFactory.Installed lifecycleRuntime;
    RootSessionObservationPort(RootApplicationAssembly.Core core,NativeReadinessCollector ordinary,RootLifecycleAuthority terminal,
            TerminalLifecycleDecisionProducer decisions,DriverStateAssembler driver,NativeGameTransport transport,
            RootLifecycleRuntimeFactory.Installed actualLifecycleRuntime) {
        this.core=Objects.requireNonNull(core);this.writer=core.writer();this.ordinary=Objects.requireNonNull(ordinary);this.terminal=Objects.requireNonNull(terminal);
        this.decisions=Objects.requireNonNull(decisions);this.driver=Objects.requireNonNull(driver);this.transport=Objects.requireNonNull(transport);
        lifecycleRuntime=Objects.requireNonNull(actualLifecycleRuntime);
        StrictJson.require(lifecycleRuntime.physical()==terminal&&lifecycleRuntime.terminalDecisions()==decisions,
                "terminal observation must retain the same actual lifecycle factory products");
    }
    @Override public SessionPorts.SemanticEvidence requireOperatorRebound(SessionPorts.SessionIdentity expected,
            org.xar.ck3.control.application.action.ActionReceipt actual,Instant deadline)throws IOException,InterruptedException {
        StrictJson.require(ordinary.identity().equals(expected),"operator rebound crossed the actual installed physical observer");
        return core.operatorAuthority().requireOperatorRebound(expected,actual,deadline);
    }
    /** Only the installed source's private canonical successor token may precede the Controller's quarantine gate. */
    @Override public java.util.Optional<SessionPorts.PendingSuccessorUi> pendingSuccessorUi(SessionPorts.SessionIdentity expected,Instant deadline)
            throws IOException,InterruptedException {
        Objects.requireNonNull(expected);Objects.requireNonNull(deadline);
        return core.withBorrowed(()->{
            var same=core.activeBorrowedSession();writer.requireSession(same);
            StrictJson.require(ordinary.identity().equals(expected),"pending successor probe crossed its actual owned physical session");
            var actual=Objects.requireNonNull(lifecycleRuntime.pendingSuccessorUi(same,expected,deadline));
            actual.ifPresent(value->{value.requireOwner(expected);StrictJson.require(!value.token().deadline().isAfter(deadline),
                    "private successor continuation exceeded the original caller deadline");});
            return actual;
        });
    }
    /** A transported continuation consumes only its already issued same-Journal private ticket. */
    @Override public java.util.Optional<SessionPorts.PendingSuccessorUi> pendingTransportSuccessorUi(SessionPorts.SessionIdentity expected,
            org.xar.ck3.control.application.session.ContinuityBatchJournal.ReboundTransport actualTicket,Instant deadline)
            throws IOException,InterruptedException {
        Objects.requireNonNull(expected);Objects.requireNonNull(actualTicket);Objects.requireNonNull(deadline);
        return core.withBorrowed(()->{
            var same=core.activeBorrowedSession();writer.requireSession(same);
            StrictJson.require(ordinary.identity().equals(expected),"transported successor crossed its actual installed physical observer");
            var actual=Objects.requireNonNull(lifecycleRuntime.pendingTransportedSuccessorUi(same,expected,actualTicket,deadline));
            actual.ifPresent(value->{value.requireOwner(expected);StrictJson.require(!value.token().deadline().isAfter(deadline),
                    "transported private successor continuation exceeded its original caller deadline");});
            return actual;
        });
    }
    @Override public SessionPorts.Observation observe(SessionPorts.SessionIdentity expected,Instant deadline) throws IOException,InterruptedException {
        return observe(expected,deadline,deadline);
    }
    @Override public SessionPorts.Observation observe(SessionPorts.SessionIdentity expected,Instant readinessDeadline,Instant planningDeadline) throws IOException,InterruptedException {
        return core.withBorrowed(()->observeBorrowed(core.activeBorrowedSession(),expected,readinessDeadline,planningDeadline));
    }
    /** Actual post-RETAIN observation barrier; the received packet itself remains immutable. */
    @Override public SessionPorts.Observation observeAfter(SessionPorts.SessionIdentity expected,
            org.xar.ck3.control.application.action.ActionReceipt actualTerminal,Instant readinessDeadline,Instant planningDeadline)
            throws IOException,InterruptedException {
        Objects.requireNonNull(expected);Objects.requireNonNull(actualTerminal);
        Objects.requireNonNull(readinessDeadline);Objects.requireNonNull(planningDeadline);
        return core.withBorrowed(()->{
            var same=core.activeBorrowedSession();writer.requireSession(same);
            StrictJson.require(ordinary.identity().equals(expected),"after-SEM observer crossed its installed physical owner");
            var archive=core.archive().withSession(same);var head=same.head();
            var found=core.journal().locked(same,locked->locked.find(actualTerminal.command().actionId()));
            var canonical=found.orElseThrow(()->new IOException("after-SEM barrier has no canonical original action"));
            StrictJson.require(canonical.equals(actualTerminal)&&actualTerminal.outcome()==org.xar.ck3.control.application.action.ActionReceipt.Outcome.APPLIED_CONFIRMED,
                    "after-SEM barrier requires the exact canonical confirmed original");
            var command=actualTerminal.command();
            StrictJson.require(command.sessionId().equals(expected.sessionId())&&command.before().machineId().equals(expected.machineId())
                    &&command.before().game().equals(expected.game()),"after-SEM original crossed its owned session/Game");
            var cycle=StrictJson.object(head.state().toJson().get(org.xar.ck3.control.continuity.writer.WriterContracts.ORDINARY_CYCLE_FIELD),
                    java.util.Set.of("schema","session","basis_cycles","completed_cycles","head","pending_receipt","retained_legacy_pending_digest","origin_frame","episode_origin"));
            var receiptRef=archive.receiptReferenceOf(actualTerminal);
            StrictJson.require("xar.java-ordinary-cycle-state/v2".equals(cycle.path("schema").asText())
                    &&org.xar.ck3.control.application.session.OrdinaryCycleTransitions.sessionFromJson(cycle.get("session")).equals(expected)
                    &&org.xar.ck3.control.contracts.ExactRef.fromJson(cycle.get("pending_receipt")).equals(receiptRef),
                    "after-SEM barrier is not this actual retained pending cycle");
            var terminal=terminalBarrier(actualTerminal,archive);
            var before=command.before();var after=terminal.frame();
            StrictJson.require(after.machineId().equals(before.machineId())&&after.game().equals(before.game())
                    &&after.observationVersion()==before.observationVersion()
                    &&after.frame().episodeRunId().equals(before.frame().episodeRunId())
                    &&after.frame().identity().player().equals(before.frame().identity().player())
                    &&!terminal.observedAt().isAfter(Instant.now()),"after-SEM terminal changed its original actor/episode or actual time");
            var pin=same.capturePin(receiptRef,org.xar.ck3.control.continuity.writer.WriterContracts.MAX_PIN_BYTES);
            ordinary.discardPlanningCaptureAtOrBefore(same,terminal.observedAt());
            var retained=transport.latestObservedSnapshot();
            if(retained.isEmpty()||!retained.orElseThrow().observedAt().isAfter(terminal.observedAt())
                    ||retained.orElseThrow().nativeRevision().compareTo(after.frame().identity().nativeRevision())<0) {
                var queried=transport.readFreshFullState(readinessDeadline);
                if(!(queried instanceof org.xar.ck3.control.nativebridge.NativeFreshSnapshotPort.Received received)) {
                    var unavailable=(org.xar.ck3.control.nativebridge.NativeFreshSnapshotPort.Unavailable)queried;
                    var original=archive.preserve(unavailable.dispatch());
                    throw new IOException("actual after-SEM READ unavailable; original="+original+"; "+unavailable.reason());
                }
                org.xar.ck3.control.nativebridge.NativeFreshSnapshotPort.verifyOriginal(
                        received.acknowledgement(),received.originalFrame(),received.snapshotReceived());
                var packet=received.originalFrame();
                StrictJson.require(packet.session().machineId().equals(expected.machineId())&&packet.session().game().equals(expected.game())
                        &&packet.session().sessionId().equals(expected.sessionId())
                        &&packet.observedAt().isAfter(terminal.observedAt())
                        &&packet.nativeRevision().compareTo(after.frame().identity().nativeRevision())>=0,
                        "actual after-SEM READ did not follow the original terminal in this owned Game");
                archive.preserve(received.acknowledgement());archive.preserveNativeFrame(packet);
                transport.acceptedSnapshotRevision(packet).requireOriginal(transport.currentSnapshot(readinessDeadline));
            }
            same.verifyPin(pin);StrictJson.require(head.digest().equals(same.head().digest()),"after-SEM original changed during its independent READ");
            var result=observeBorrowed(same,expected,readinessDeadline,planningDeadline);
            if(result instanceof SessionPorts.Ready ready) {
                var semantic=ready.semanticEvidence().orElseThrow(()->new IOException("after-SEM observation has no actual archived semantic evidence"));
                var frame=semantic.frame();
                StrictJson.require(semantic.observedAt().isAfter(terminal.observedAt())
                        &&frame.machineId().equals(after.machineId())&&frame.game().equals(after.game())
                        &&frame.frame().episodeRunId().equals(after.frame().episodeRunId())
                        &&frame.frame().identity().player().equals(after.frame().identity().player())
                        &&frame.frame().identity().nativeRevision().compareTo(after.frame().identity().nativeRevision())>=0
                        &&frame.frame().identity().dateRaw().compareTo(after.frame().identity().dateRaw())>=0,
                        "actual after-SEM Ready reused an earlier terminal packet or changed its original owner");
            }
            same.verifyPin(pin);return result;
        });
    }
    private record TerminalBarrier(org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity frame,Instant observedAt) { }
    private TerminalBarrier terminalBarrier(org.xar.ck3.control.application.action.ActionReceipt receipt,
            org.xar.ck3.control.application.action.ActionPorts.OutcomeArchive archive) {
        var semantic=org.xar.ck3.control.application.action.ActionEffects.observation(receipt);
        if(semantic.isPresent()) {
            var effect=semantic.orElseThrow();
            StrictJson.require(effect.sessionId().equals(receipt.command().sessionId())&&effect.source().equals(receipt.command().source()),
                    "after-SEM terminal lost its actual original source/session");
            return new TerminalBarrier(effect.after(),effect.observedAt());
        }
        if(receipt.state() instanceof org.xar.ck3.control.application.action.ActionState.Settled settled
                &&settled.settlement() instanceof org.xar.ck3.control.application.action.ActionState.ControlApplied control)
            return new TerminalBarrier(control.read().after().binding().observed(),control.read().after().binding().observedAt());
        if(receipt.state() instanceof org.xar.ck3.control.application.action.ActionState.CompositeSettled settled
                &&settled.settlement() instanceof org.xar.ck3.control.application.action.ActionState.SwaySchedulerCompleted scheduler) {
            var proof=scheduler.proof();proof.validateParent(receipt.command());var actual=core.frameLoader().load(proof.finalFrame(),archive);
            StrictJson.require(actual.sessionId().equals(receipt.command().sessionId())&&actual.source().equals(receipt.command().source())
                    &&actual.originalEvidence().equals(proof.finalFrame().nativeFrame()),"after-SEM Sway terminal lost its actual original source");
            return new TerminalBarrier(actual.identity(),actual.observedAt());
        }
        throw new IllegalArgumentException("actual original action has no supported ordinary terminal barrier");
    }
    private SessionPorts.Observation observeBorrowed(ContinuityStorePort.Session same,SessionPorts.SessionIdentity expected,Instant deadline,Instant planningDeadline) throws IOException,InterruptedException {
        writer.requireSession(same);
        StrictJson.require(ordinary.identity().equals(expected),"session observer crossed its actual physical owner");
        var pending=lifecycleRuntime.pending(same,expected);
        if(pending.isPresent())return pending.orElseThrow();
        SessionPorts.Observation observed=ordinary.observe(same,expected,deadline,planningDeadline);
        if(observed instanceof SessionPorts.TerminalReady)return observed;
        boolean terminalReady=observed instanceof SessionPorts.Ready ready
                &&ready.checkpointEligibility()==SessionPorts.CheckpointEligibility.TERMINAL_PENDING;
        if(observed instanceof SessionPorts.Ready&&!terminalReady&&!mayBeTerminal(same,expected))return observed;
        // Raw tokens only choose which actual observer to ask. They never authorize a lifecycle operation.
        if(!terminalReady&&!mayBeTerminal(same,expected))return observed;
        try {
            return lifecycleRuntime.observeTerminal(same,expected,deadline);
        } catch(InterruptedIOException interrupted) {
            Thread.currentThread().interrupt();throw new InterruptedException(interrupted.getMessage());
        } catch(IOException|IllegalArgumentException|IllegalStateException unavailable) {
            var evidence=observed instanceof SessionPorts.Waiting waiting?waiting.evidence()
                    :observed instanceof SessionPorts.Ready ready?ready.semanticEvidence().orElseThrow().semantic()
                    :((SessionPorts.ObservationUnavailable)observed).evidence();
            return new SessionPorts.ObservationUnavailable("actual terminal observation unavailable: "+unavailable.getMessage(),evidence);
        }
    }
    private boolean mayBeTerminal(ContinuityStorePort.Session same,SessionPorts.SessionIdentity expected)throws IOException {
        writer.requireSession(same);var received=transport.latestObservedSnapshot();if(received.isEmpty())return false;
        var actual=received.orElseThrow();
        if(!actual.session().machineId().equals(expected.machineId())||!actual.session().game().equals(expected.game())
                ||!actual.session().sessionId().equals(expected.sessionId()))return false;
        final OpportunityJson.Obj raw;
        try{raw=DriverJson.object(actual.state().bytes(),DriverJson.MAX_NATIVE_BYTES);}catch(IllegalArgumentException invalid){return false;}
        return driver.withFrozenFacts(same,frozen->{
            if(!(frozen.state() instanceof DriverSnapshotFacts.Known known))return false;
            if(!raw.members().containsKey("played_character")||raw.get("played_character")==OpportunityJson.Nil.INSTANCE)return true;
            if(!(raw.get("played_character") instanceof OpportunityJson.Obj player))return false;
            try {
                var actor=OpportunityJson.integer(player.get("character_id"),"character_id");
                return !OpportunityJson.bool(player.get("alive"),"alive")||!actor.equals(known.driver().session().actorId());
            }catch(IllegalArgumentException invalid){return false;}
        });
    }
}

