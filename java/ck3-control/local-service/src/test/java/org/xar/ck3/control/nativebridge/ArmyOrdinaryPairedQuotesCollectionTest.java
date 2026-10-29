package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.nativebridge.capabilities.army.*;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.service.root.ArmyOrdinaryPairedQuotes;

/** Real software writer/central read ticket/transport/archive -> actual PairedQuotes first phase.
 * Synthetic native packets do not qualify ManagedGame, a private Root context or an executed action. */
final class ArmyOrdinaryPairedQuotesCollectionTest {
    @TempDir Path directory;
    @Test void originalUnknownWaitsThenCollectsPastItsOriginalDeadlineWithoutAnotherDeclarationQuery() throws Exception { exercise("available"); }
    @Test void actualTransportRetainsItsOriginalRejectedSoftwareResponseWithoutAnotherDeclarationQuery() throws Exception { exercise("native-rejected"); }
    @Test void poppedMalformedAckRetainsSoleCustodyAndNeverBecomesACommandQuote() throws Exception { exercise("malformed"); }

    private void exercise(String mode) throws Exception {
        var central=new AtomicReference<PlanningReadPort>();var owning=new AtomicReference<ArmyWarReads>();var submitted=new AtomicInteger();
        var produced=new AtomicReference<RawJson>();
        var delegate=new Central(central);
        var scenario=new ActionWriterIntegrationFixture.SoftwareReadScenario("0".repeat(64),"actual-paired-declaration-collection",
                source->List.of(),request->{submitted.incrementAndGet();var value=result(mode);produced.set(value);return value;},
                Optional.empty(),Set.of(),source->{var war=new ArmyWarReads(source,source,delegate);owning.set(war);return war.families();});
        try(var f=new ActionWriterIntegrationFixture(directory.resolve(mode),false,scenario)) {
            central.set(f.reads);if(mode.equals("native-rejected"))f.rejectNextScenarioRead();
            f.loseReadAckOnce();var wars=Objects.requireNonNull(owning.get());var initial=f.ready();
            f.writer.locked(same->{
                f.collector.current(same,initial.request().before(),Instant.now().plusSeconds(20),lease->{
                    var actual=lease.frame();Instant originalDeadline=Instant.now().plusMillis(250);
                    var originalContext=new ArmyTypes.Context(actual.identity(),actual.source(),actual.sessionId(),originalDeadline);
                    assertThrows(IllegalStateException.class,()->ArmyOrdinaryPairedQuotes.currentDeclarationOriginal(same,wars,f.reads.catalog(),originalContext,actual,Clock.systemUTC()));
                    var pending=wars.pendingDeclaration().orElseThrow();String requestId=pending.originalUnknown().requestId();
                    var originalRequest=pending.request();byte[] outbound=pending.originalUnknown().originalRequestPacket();
                    var timeout=pending.originalTimeout();assertFalse(timeout.isNegative());assertFalse(timeout.isZero());assertEquals(1,submitted.get());
                    var continuation=new ArmyTypes.Context(actual.identity(),actual.source(),actual.sessionId(),Instant.now().plusSeconds(5));
                    int packetReads=f.nativePacketReads();
                    var waiting=assertThrows(IllegalStateException.class,()->ArmyOrdinaryPairedQuotes.currentDeclarationOriginal(same,wars,f.reads.catalog(),continuation,actual,Clock.systemUTC()));
                    assertTrue(waiting.getMessage().contains("pending"));assertSame(pending,wars.pendingDeclaration().orElseThrow());
                    assertEquals(packetReads,f.nativePacketReads());assertEquals(1,submitted.get());
                    var foreign=new ArmyTypes.Context(actual.identity(),actual.source(),actual.sessionId()+"-foreign",continuation.deadline());
                    assertThrows(IllegalArgumentException.class,()->ArmyOrdinaryPairedQuotes.currentDeclarationOriginal(same,wars,f.reads.catalog(),foreign,actual,Clock.systemUTC()));
                    var expired=new ArmyTypes.Context(actual.identity(),actual.source(),actual.sessionId(),Instant.now().minusSeconds(1));
                    assertThrows(IllegalArgumentException.class,()->ArmyOrdinaryPairedQuotes.currentDeclarationOriginal(same,wars,f.reads.catalog(),expired,actual,Clock.systemUTC()));
                    assertSame(pending,wars.pendingDeclaration().orElseThrow());assertEquals(1,submitted.get());
                    f.releaseLateReadAck();
                    try {
                        f.physicalInputs().transport().observe(Instant.now().plusSeconds(5));
                        Thread.sleep(Math.max(0,Duration.between(Instant.now(),originalDeadline).toMillis())+20);
                    } catch(InterruptedException interrupted){Thread.currentThread().interrupt();throw new IOException("late original fixture interrupted",interrupted);}
                    int stableReads=f.nativePacketReads();
                    if(mode.equals("malformed")) {
                        assertThrows(IllegalStateException.class,()->ArmyOrdinaryPairedQuotes.currentDeclarationOriginal(same,wars,f.reads.catalog(),continuation,actual,Clock.systemUTC()));
                        var retained=wars.pendingDeclaration().orElseThrow();assertTrue(retained.resultFrame().isPresent());
                        assertEquals(produced.get(),retained.resultFrame().orElseThrow().originalResultToken().orElseThrow());
                        assertThrows(IllegalStateException.class,()->ArmyOrdinaryPairedQuotes.currentDeclarationOriginal(same,wars,f.reads.catalog(),continuation,actual,Clock.systemUTC()));
                        assertSame(retained,wars.pendingDeclaration().orElseThrow());assertTrue(wars.currentDeclarations(new ArmyRetreatFrames.Current(actual,continuation.deadline())).isEmpty());
                    } else if(mode.equals("native-rejected")) {
                        var rejected=assertThrows(IllegalStateException.class,()->ArmyOrdinaryPairedQuotes.currentDeclarationOriginal(same,wars,f.reads.catalog(),continuation,actual,Clock.systemUTC()));
                        assertTrue(rejected.getMessage().contains("native-rejected"));assertTrue(wars.pendingDeclaration().isEmpty());
                        assertTrue(wars.currentDeclarations(new ArmyRetreatFrames.Current(actual,continuation.deadline())).isEmpty());
                    } else {
                        var known=ArmyOrdinaryPairedQuotes.currentDeclarationOriginal(same,wars,f.reads.catalog(),continuation,actual,Clock.systemUTC());
                        assertTrue(wars.pendingDeclaration().isEmpty());assertEquals(originalRequest,known.receipt().request());
                        assertEquals(originalDeadline,known.receipt().request().deadline());assertEquals(requestId,known.receipt().requestId());
                        assertEquals(produced.get(),known.receipt().original().originalResultToken().orElseThrow());
                        assertArrayEquals(outbound,known.receipt().original().outbound().orElseThrow().originalPacket());
                        assertTrue(known.receipt().adoption().isPresent(),"an expired original requires explicit central late-read provenance, not a rewritten time");
                        assertEquals(continuation.deadline(),known.receipt().adoption().orElseThrow().currentRequest().deadline());
                        assertEquals(known.receipt(),f.archive.loadRead(known.originalReceipt()));
                        var selected=new ArmyWarReads.Selection(new ArmyCalls.Frame(PublicMethod.QUERY_DECLARABLE_WARS,ArmyOrdinaryPairedQuotes.revision(actual)),new ArmyRetreatFrames.Current(actual,originalDeadline),Optional.empty());
                        var originalContract=wars.contract(f.reads.catalog(),selected);
                        var query=new ArmyOrdinaryPreflight.Query<>(ArmyOrdinaryPreflight.Role.DECLARATIONS,originalContract,originalRequest,ArmyWarReadCodec::encode);
                        var accepted=ArmyOrdinaryPreflight.accept(query,known,actual,f.archive);
                        assertEquals(accepted,ArmyOrdinaryPreflight.replayOne(query,actual,known.originalReceipt(),f.archive));
                        var next=new ArmyTypes.Context(actual.identity(),actual.source(),actual.sessionId(),Instant.now().plusSeconds(5));
                        assertSame(known,ArmyOrdinaryPairedQuotes.currentDeclarationOriginal(same,wars,f.reads.catalog(),next,actual,Clock.systemUTC()),"an already-collected private current source must not trigger a new DECL");
                        var choice=new ArmyCalls.Declaration(PublicMethod.DECLARE_WAR,ArmyOrdinaryPairedQuotes.revision(actual),"202-0--1");
                        var dependent=ArmyOrdinaryPairedQuotes.declarationFinal(wars,f.reads.catalog(),choice,actual,next.deadline(),known.receipt(),f.archive);
                        assertEquals(ArmyOrdinaryPreflight.Role.DECLARATION_FINAL_ROLES,dependent.role());
                        assertEquals(next.deadline(),dependent.request().deadline());assertEquals(actual.identity(),dependent.request().before());
                        assertEquals(actual.source(),dependent.request().source());assertEquals(actual.sessionId(),dependent.request().sessionId());
                        assertEquals(originalDeadline,f.archive.loadRead(known.originalReceipt()).request().deadline());
                        assertEquals(timeout,pending.originalTimeout());
                        // Only the different dependent contract was built. Executing it and a command still needs actual current Root guards.
                    }
                    assertEquals(stableReads,f.nativePacketReads());assertEquals(1,submitted.get());assertEquals(1,f.scenarioReadWrites());
                    assertEquals(0,f.nativeActionWrites());return null;
                });return null;
            });
        }
    }
    private static RawJson result(String mode) {
        var n=org.xar.ck3.control.contracts.StrictJson.object().put("step","query-declarable-wars").put("accepted",true).put("status","available").put("query_sequence",5);
        if(mode.equals("malformed"))n.put("query_sequence",true);
        var choice=n.putArray("declarable_wars").addObject().put("declaration_id","202-0--1").put("target_character_id",202)
                .put("casus_belli_index",0).put("casus_belli_key","claim_cb").put("configuration_index",-1).put("claimant_character_id",-1);
        choice.putArray("target_title_ids").add(0).add(17);
        return new RawJson(DriverJson.encode(OpportunityJson.parse(n.toString().getBytes(java.nio.charset.StandardCharsets.UTF_8))));
    }
    /** Actual central native transport/archive delegation; it supplies no fake read result or private qualification. */
    private record Central(AtomicReference<PlanningReadPort> actual) implements PlanningReadPort {
        private PlanningReadPort current(){return Objects.requireNonNull(actual.get());}
        @Override public <T> PlanningReadResult<T> read(ReadContract<T> contract,PlanningReadRequest request){throw new AssertionError("original writer must be borrowed");}
        @Override public <T> PlanningReadResult<T> read(Session same,ReadContract<T> contract,PlanningReadRequest request){return current().read(same,contract,request);}
        @Override public <T> PlanningReadAttempt<T> readOriginal(Session same,ReadContract<T> contract,PlanningReadRequest request){return current().readOriginal(same,contract,request);}
        @Override public Optional<NativeActionPort.AckReceived> pollOriginal(Session same,PlanningReadCoordinator.OriginalRead<?> original)throws IOException{return current().pollOriginal(same,original);}
        @Override public <T> PlanningReadResult<T> adoptOriginal(Session same,PlanningReadCoordinator.OriginalRead<T> original,NativeActionPort.AckReceived ack,
                PlanningReadRequest current,OpportunityJson.Obj semantic)throws IOException{return current().adoptOriginal(same,original,ack,current,semantic);}
    }
}
