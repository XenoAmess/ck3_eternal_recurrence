package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;

import java.io.IOException;
import java.math.BigInteger;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.driver.DriverPlanningEvidence;
import org.xar.ck3.control.application.planning.OrdinaryPolicy;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.military.ActiveRetreatProposal;
import org.xar.ck3.control.application.planning.military.ActiveRetreatState;
import org.xar.ck3.control.application.planning.military.CurrentBattleRetreatModel;
import org.xar.ck3.control.application.planning.military.MilitaryPlanningDecision;
import org.xar.ck3.control.application.planning.military.OrdinaryActiveRetreatPolicy;
import org.xar.ck3.control.application.session.SessionPorts;
import org.xar.ck3.control.continuity.writer.ImmutableArtifactStore;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.military.battleretreat.BattleRetreatPolicy;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyRetreatDomain;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Actual held collector/writer/originals; does not invent a constructible RootRuntimeContext. */
final class RetreatHeldPlanningScopeTest {
    @TempDir Path temporary;

    @Test void domainReadInsideTheHeldPlanningRoundUsesNoNewPushOrImplicitEmptyState() throws Exception {
        try(var actual=new ActionWriterIntegrationFixture(temporary.resolve("held-domain"),false)) {
            bindOriginals(actual);
            var artifacts=new ImmutableArtifactStore(new ImmutableArtifactStore.Config(actual.root.resolve("artifacts"),
                    actual.writer.originalLockPath(),16*1024*1024),actual.writer.storageGuard());
            var domain=new ArmyRetreatDomain(artifacts,actual.archive,actual.frameLoader());
            actual.writer.locked(same->{
                try{return actual.collector.withPlanningRound(same,()->{
                    var ready=assertInstanceOf(SessionPorts.Ready.class,actual.collector.observe(same,actual.observationIdentity(),Instant.now().plusSeconds(20)));
                    var request=ready.request();int packets=actual.nativePacketReads(),queries=actual.nativeReadWrites();String head=same.head().digest();
                    IOException missing=assertThrows(IOException.class,()->actual.collector.currentPlanning(same,request,request.deadline(),(original,lease)->{
                        assertSame(request,original);actual.collector.requireHeldFrame(same,lease.frame());
                        return domain.read(same);
                    }));
                    assertTrue(missing.getMessage().contains("ACTIVE_RETREAT is not imported"));
                    assertEquals(packets,actual.nativePacketReads());assertEquals(queries,actual.nativeReadWrites());
                    assertEquals(head,same.head().digest());assertEquals(0,actual.nativeActionWrites());return null;
                });}catch(InterruptedException interrupted){Thread.currentThread().interrupt();throw new IOException(interrupted);}
            });
        }
    }

    @Test void pendingIntentIsReadBeforeTheNoArmyAndUnsupportedCapabilityBranches() throws Exception {
        try(var actual=new ActionWriterIntegrationFixture(temporary.resolve("held-pending"),false)) {
            bindOriginals(actual);
            actual.writer.locked(same->{
                try{return actual.collector.withPlanningRound(same,()->{
                    var ready=assertInstanceOf(SessionPorts.Ready.class,actual.collector.observe(same,actual.observationIdentity(),Instant.now().plusSeconds(20)));
                    var request=ready.request();assertEquals(new OpportunityJson.Arr(List.of()),request.observations().snapshot().get("player_armies"));
                    var source=ActiveRetreatProposal.SourceFrame.read(request.observations().snapshot());
                    var args=new BattleRetreatPolicy.RetreatOrder(0,source.revision(),17,0,BattleRetreatPolicy.Scope.FULL_SIDE,2,"software-pending-token");
                    var order=new ActiveRetreatProposal.Order(source,73,args,List.of(0),List.of(),List.of(2),new OpportunityJson.Obj(java.util.Map.of()));
                    var pending=ActiveRetreatState.reduce(ActiveRetreatState.State.initial(),new ActiveRetreatState.StartOrder(order));
                    var reads=new AtomicInteger();var observations=new AtomicInteger();
                    OrdinaryActiveRetreatPolicy.StateReader stateReader=current->{
                        try{return actual.collector.currentPlanning(same,current,current.deadline(),(original,lease)->{
                            actual.collector.requireHeldFrame(same,lease.frame());reads.incrementAndGet();
                            return new OrdinaryActiveRetreatPolicy.KnownDomain(original.before(),pending);
                        });}catch(IOException failure){throw new java.io.UncheckedIOException(failure);}
                    };
                    var port=new OrdinaryActiveRetreatPolicy.RetreatReadPort(){
                        @Override public OrdinaryActiveRetreatPolicy.ReadResult preview(PlanningRequest ignored,int selected,int target){throw new AssertionError("pending intent cannot preview a replacement");}
                        @Override public OrdinaryActiveRetreatPolicy.ReadResult observe(PlanningRequest original){observations.incrementAndGet();return new OrdinaryActiveRetreatPolicy.ReadCompleted(original.before(),source,List.of(original.source().sourceRef()));}
                    };
                    ExactRef definition=request.source().sourceRef();
                    var policy=new OrdinaryActiveRetreatPolicy(definition,stateReader,ignored->{throw new AssertionError("pending intent must precede model/capability checks");},
                            new CurrentBattleRetreatModel(),port,(a,b,c)->{throw new AssertionError("pending read cannot submit a world action");});
                    var draft=new OrdinaryPolicy.Draft("software-retreat-policy","software-no-armies","pending read",OrdinaryPolicy.Kind.ORDINARY,Optional.empty(),OrdinaryPolicy.Purpose.DATE_ADVANCE,Optional.empty(),new OpportunityJson.Obj(java.util.Map.of()));
                    int packets=actual.nativePacketReads(),queries=actual.nativeReadWrites();String head=same.head().digest();
                    var decision=assertInstanceOf(MilitaryPlanningDecision.ApplicationDecision.class,policy.review(request,draft));
                    assertInstanceOf(OrdinaryPolicy.Refresh.class,decision.decision());assertEquals(1,reads.get());assertEquals(1,observations.get());
                    assertEquals(order,pending.pending().orElseThrow());assertTrue(pending.claimed(ActiveRetreatState.ClaimKey.of(order)));
                    assertEquals(packets,actual.nativePacketReads());assertEquals(queries,actual.nativeReadWrites());assertEquals(head,same.head().digest());return null;
                });}catch(InterruptedException interrupted){Thread.currentThread().interrupt();throw new IOException(interrupted);}
            });
        }
    }

    @Test void heldPlanningSourceOrSessionDriftRejectsBeforeTheDomainCallback() throws Exception {
        try(var actual=new ActionWriterIntegrationFixture(temporary.resolve("held-drift"),false)) {
            bindOriginals(actual);
            actual.writer.locked(same->{
                try{return actual.collector.withPlanningRound(same,()->{
                    var request=assertInstanceOf(SessionPorts.Ready.class,actual.collector.observe(same,actual.observationIdentity(),Instant.now().plusSeconds(20))).request();
                    int packets=actual.nativePacketReads();var called=new AtomicInteger();
                    var wrong=new PlanningRequest(request.before(),request.source(),request.sessionId()+"-other",request.deadline(),request.observations());
                    assertThrows(IllegalArgumentException.class,()->actual.collector.currentPlanning(same,wrong,wrong.deadline(),(original,lease)->called.incrementAndGet()));
                    assertEquals(0,called.get());assertEquals(packets,actual.nativePacketReads());assertEquals(0,actual.nativeActionWrites());return null;
                });}catch(InterruptedException interrupted){Thread.currentThread().interrupt();throw new IOException(interrupted);}
            });
        }
    }

    private static void bindOriginals(ActionWriterIntegrationFixture actual) {
        actual.collector.bindPlanningEvidence((same,request,lease)->DriverPlanningEvidence.requireEquivalent(same,request,lease,actual.physicalInputs().originals()));
    }
}
