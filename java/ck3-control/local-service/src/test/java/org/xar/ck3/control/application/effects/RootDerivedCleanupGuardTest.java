package org.xar.ck3.control.application.effects;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.readiness.ReadinessAuthority;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Actual packet/collector/writer and default-deny regressions; no private Root derived authority is fabricated. */
final class RootDerivedCleanupGuardTest {
    @TempDir Path temporary;
    private static void publish(ActionWriterIntegrationFixture fixture,java.util.function.Consumer<com.fasterxml.jackson.databind.node.ObjectNode> edit)throws Exception {
        var transport=fixture.physicalInputs().transport();
        var old=transport.currentSnapshot(Instant.now().plusSeconds(20));
        var state=NativeWire.object(NativeWire.parse(old.state().bytes()));edit.accept(state);
        var body=org.xar.ck3.control.contracts.StrictJson.object();
        body.put("type","state_snapshot").put("protocol_version",1).put("snapshot_id","cleanup-"+old.nativeRevision().add(java.math.BigInteger.ONE));
        body.put("revision",old.nativeRevision().add(java.math.BigInteger.ONE));body.set("state",state);
        byte[] packet=NativeWire.packet(org.xar.ck3.control.contracts.StrictJson.canonical(body));
        assertInstanceOf(NativeWire.Snapshot.class,NativeWire.decode(packet));
        fixture.enqueueSoftwareNativePacket(packet);
        var actual=transport.observe(Instant.now().plusSeconds(20));
        assertArrayEquals(packet,actual.originalPacket());
    }
    @Test void actualRunningPacketCanSupplyPhysicalDataAndReplayWithoutOrdinaryReadyOrNativeAction()throws Exception {
        try(var fixture=new ActionWriterIntegrationFixture(temporary.resolve("running"),false)){
            var expected=fixture.ready().request().before();
            publish(fixture,state->state.put("paused",false));
            int reads=fixture.nativeReadWrites(),actions=fixture.nativeActionWrites();
            fixture.writer.locked(same->{
                var head=same.head();
                fixture.collector.currentDerivedCleanup(same,expected,Instant.now().plusSeconds(20),lease->{
                    assertFalse(OpportunityJson.bool(lease.frame().semantic().get("paused"),"paused"));
                    RootGuardChecks.livingMap(lease);
                    assertThrows(IllegalArgumentException.class,()->RootGuardChecks.livingPaused(lease));
                    var archive=fixture.archive.withSession(same);
                    var replay=fixture.frameLoader().load(NativeEffectEvidence.basis(lease.frame()),archive);
                    assertEquals(lease.frame().identity(),replay.identity());
                    assertEquals(lease.frame().semantic(),replay.semantic());
                    assertEquals(head.digest(),same.head().digest());return null;
                });
                assertThrows(Exception.class,()->fixture.collector.current(same,expected,Instant.now().plusSeconds(20),lease->{throw new AssertionError("running DATA cannot become ordinary Ready");}));
                return null;
            });
            assertEquals(reads,fixture.nativeReadWrites());assertEquals(actions,fixture.nativeActionWrites());
        }
    }
    @Test void originalNonPausedSafetyChecksStillRejectActualBadNativeState()throws Exception {
        List<java.util.function.Consumer<com.fasterxml.jackson.databind.node.ObjectNode>> invalid=List.of(
                state->state.put("map_ready",false),
                state->((com.fasterxml.jackson.databind.node.ObjectNode)state.get("played_character")).put("alive",false),
                state->((com.fasterxml.jackson.databind.node.ObjectNode)state.get("played_character")).put("character_id",74));
        for(int index=0;index<invalid.size();index++){
            try(var fixture=new ActionWriterIntegrationFixture(temporary.resolve("invalid-"+index),false)){
                var expected=fixture.ready().request().before();var edit=invalid.get(index);
                publish(fixture,state->{state.put("paused",false);edit.accept(state);});
                fixture.writer.locked(same->{
                    assertThrows(Exception.class,()->fixture.collector.currentDerivedCleanup(same,expected,Instant.now().plusSeconds(20),
                            lease->{RootGuardChecks.livingMap(lease);return null;}));return null;
                });
                assertEquals(0,fixture.nativeActionWrites());
            }
        }
    }
    @Test void aStandaloneRunningPauseCannotBorrowTheReservedChildEntry()throws Exception {
        try(var fixture=new ActionWriterIntegrationFixture(temporary.resolve("standalone"),false)){
            var original=fixture.command("standalone-pause-no-parent");
            publish(fixture,state->state.put("paused",false));
            assertThrows(RuntimeException.class,()->fixture.coordinator.execute(original));
            assertEquals(0,fixture.nativeActionWrites());
            assertTrue(fixture.snapshot().actions().stream().noneMatch(receipt->receipt.command().actionId().equals(original.actionId())));
        }
    }
    @Test void oldOrdinaryAuthorityAndLambdaAdmissionCannotGrantPhysicalCleanup() {
        var callbacks=new AtomicInteger();
        ReadinessAuthority ordinary=new ReadinessAuthority(){
            @Override public<T>T current(ContinuityStorePort.Session same,ObservationIdentity expected,Instant callerDeadline,CheckedWork<T> work){
                throw new AssertionError("default physical method cannot fall back to ordinary current");
            }
        };
        assertThrows(IOException.class,()->ordinary.currentDerivedCleanup(null,null,Instant.now().plusSeconds(10),
                lease->{callbacks.incrementAndGet();return null;}));
        RootActionGuard.DerivedChildAdmission old=(same,head,child,lease,definition,archive)->{
            callbacks.incrementAndGet();throw new AssertionError("ordinary admission is not a physical source issuer");
        };
        assertThrows(IOException.class,()->old.verifyPhysical(null,null,null,null,null,null));
        assertEquals(0,callbacks.get());
    }
}
