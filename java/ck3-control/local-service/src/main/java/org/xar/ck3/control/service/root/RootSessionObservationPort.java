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
        return core.withBorrowed(()->observeBorrowed(core.activeBorrowedSession(),expected,deadline));
    }
    private SessionPorts.Observation observeBorrowed(ContinuityStorePort.Session same,SessionPorts.SessionIdentity expected,Instant deadline) throws IOException,InterruptedException {
        writer.requireSession(same);
        StrictJson.require(ordinary.identity().equals(expected),"session observer crossed its actual physical owner");
        var pending=lifecycleRuntime.pending(same,expected);
        if(pending.isPresent())return pending.orElseThrow();
        SessionPorts.Observation observed=ordinary.observe(same,expected,deadline);
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

