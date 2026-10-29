package org.xar.ck3.control.nativebridge;

import java.io.IOException;
import java.math.BigInteger;
import java.nio.file.Path;
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
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.nativebridge.capabilities.army.*;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.junit.jupiter.api.Assertions.*;

/** Actual central ticket, transport queue, domain decoder and immutable archive under one real software writer/guard scope. */
final class ArmyDeclarationCollectionWriterTest {
    @TempDir Path directory;
    @Test void actualUnknownCollectsItsLateOriginalAndReplaysTheSameArchiveWithoutNativeResubmission() throws Exception {
        exercise("available");
    }
    @Test void actualRejectedOriginalClearsOnlyPendingAndDoesNotPublishADeclarationLease() throws Exception {
        exercise("native-rejected");
    }
    @Test void malformedPoppedOriginalRemainsInSoleCustodyAcrossRepeatedValidationFailures() throws Exception {
        exercise("malformed");
    }
    private void exercise(String mode) throws Exception {
        var central=new AtomicReference<PlanningReadPort>();var warOwner=new AtomicReference<ArmyWarReads>();var submissions=new AtomicInteger();
        var delegate=new Central(central);
        var scenario=new ActionWriterIntegrationFixture.SoftwareReadScenario("0".repeat(64),"actual-original-declaration-collection",
                source->List.of(),request->{
                    submissions.incrementAndGet();
                    try {return result(mode.equals("native-rejected")?"available":mode);} catch(IOException malformed) {throw new java.io.UncheckedIOException(malformed);}
                },Optional.empty(),Set.of(),source->{
                    var owner=new ArmyWarReads(source,source,delegate);warOwner.set(owner);return owner.families();
                });
        try(var f=new ActionWriterIntegrationFixture(directory.resolve(mode),false,scenario)) {
            central.set(f.reads);var owner=Objects.requireNonNull(warOwner.get());
            f.loseReadAckOnce();
            if(mode.equals("native-rejected"))f.rejectNextScenarioRead();
            var initial=f.ready();
            f.writer.locked(same->{
                f.collector.current(same,initial.request().before(),Instant.now().plusSeconds(20),lease->{
                    Instant originalDeadline=Instant.now().plusSeconds(2);
                    var held=new ArmyRetreatFrames.Current(lease.frame(),originalDeadline);
                    var call=new ArmyCalls.Frame(PublicMethod.QUERY_DECLARABLE_WARS,new ArmyCalls.Revision(new ArmyTypes.Present<>(held.context().before().frame().revision())));
                    var selected=new ArmyWarReads.Selection(call,held,Optional.empty());var contract=owner.contract(f.reads.catalog(),selected);
                    var unavailable=owner.read(same,contract,selected,Duration.ofSeconds(2));
                    assertInstanceOf(PlanningReadResult.Unavailable.class,unavailable);
                    var pending=owner.pendingDeclaration().orElseThrow();assertTrue(pending.originalRead().isPresent());assertTrue(pending.resultFrame().isEmpty());
                    String id=pending.originalUnknown().requestId();byte[] outbound=pending.originalUnknown().originalRequestPacket();
                    var collect=new ArmyCalls.Collect(new ArmyCalls.Revision(new ArmyTypes.Present<>(held.context().before().frame().revision())),id);
                    int reads=f.nativePacketReads();
                    assertInstanceOf(ArmyDeclarationCollection.Pending.class,owner.collectOriginal(same,collect,lease.frame(),Instant.now().plusSeconds(5)));
                    assertEquals(reads,f.nativePacketReads());assertEquals(1,submissions.get());
                    assertThrows(IllegalArgumentException.class,()->owner.collectOriginal(same,new ArmyCalls.Collect(collect.revision(),id+"-wrong"),lease.frame(),Instant.now().plusSeconds(5)));
                    var actual=lease.frame();var crossed=new org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete(actual.identity(),actual.source(),"another-physical-session",actual.connectionGeneration(),actual.semantic(),actual.originalEvidence(),actual.observedAt(),actual.fullBindingSha256());
                    assertThrows(IllegalArgumentException.class,()->owner.collectOriginal(same,collect,crossed,Instant.now().plusSeconds(5)));
                    assertSame(pending,owner.pendingDeclaration().orElseThrow());assertEquals(reads,f.nativePacketReads());
                    assertThrows(IllegalArgumentException.class,()->owner.read(same,contract,selected,Duration.ofSeconds(2)));
                    var nativeFrame=frame(id,mode);
                    f.releaseLateReadAck();
                    // Normal passive snapshot reception receives the late response; collection itself never pumps the pipe.
                    try {
                        f.physicalInputs().transport().observe(Instant.now().plusSeconds(5));
                        if(mode.equals("available"))Thread.sleep(Math.max(0,Duration.between(Instant.now(),originalDeadline).toMillis())+20);
                    } catch(InterruptedException interrupted) {Thread.currentThread().interrupt();throw new IOException("synthetic late response interrupted",interrupted);}
                    reads=f.nativePacketReads();int stableReads=reads;
                    if(mode.equals("malformed")) {
                        assertThrows(IllegalStateException.class,()->owner.collectOriginal(same,collect,lease.frame(),Instant.now().plusSeconds(5)));
                        var retained=owner.pendingDeclaration().orElseThrow();assertTrue(retained.resultFrame().isPresent());
                        assertEquals(OpportunityJson.parse(nativeFrame.bytes()),OpportunityJson.parse(retained.resultFrame().orElseThrow().originalFrame().bytes()));
                        assertThrows(IllegalStateException.class,()->owner.collectOriginal(same,collect,lease.frame(),Instant.now().plusSeconds(5)));
                        assertSame(retained,owner.pendingDeclaration().orElseThrow());assertTrue(owner.currentDeclarations(held).isEmpty());
                    } else {
                        var collected=owner.collectOriginal(same,collect,lease.frame(),Instant.now().plusSeconds(5));
                        assertEquals(mode,collected.status().wire());assertTrue(owner.pendingDeclaration().isEmpty());
                        if(collected instanceof ArmyDeclarationCollection.Available available) {
                            var live=owner.requireCurrentDeclarations(held);var evidence=live.evidence();var receipt=f.archive.loadRead(evidence);
                            assertEquals(live.originalRead().receipt(),receipt);assertEquals(live.originalRead().originalReceipt(),evidence);
                            var detached=ArmyWarReads.replayDeclarationLease(selected,receipt,evidence,f.archive);
                            assertThrows(IllegalStateException.class,detached::originalRead);
                            assertEquals(originalDeadline,receipt.request().deadline());assertEquals(id,receipt.requestId());
                            assertArrayEquals(outbound,receipt.original().outbound().orElseThrow().originalPacket());
                            assertEquals(OpportunityJson.parse(nativeFrame.bytes()),OpportunityJson.parse(receipt.original().originalFrame().bytes()));
                            assertEquals(available.nativeResultFrame(),receipt.original().originalFrame());
                            assertArrayEquals(NativeWire.packet(receipt.original().originalFrame().bytes()),receipt.original().originalPacket());
                            assertEquals(available.declarations(),contract.replay(receipt));
                            assertEquals(receipt,f.archive.loadRead(evidence));
                        } else assertTrue(owner.currentDeclarations(held).isEmpty());
                        assertThrows(IllegalArgumentException.class,()->owner.collectOriginal(same,collect,lease.frame(),Instant.now().plusSeconds(5)));
                    }
                    assertEquals(stableReads,f.nativePacketReads());assertEquals(1,submissions.get());assertEquals(0,f.nativeActionWrites());return null;
                });return null;
            });
        }
    }
    private static RawJson result(String mode) throws IOException {
        var full=OpportunityJson.object(OpportunityJson.parse(frame("synthetic-no-request",mode).bytes()),"synthetic result frame");
        return new RawJson(DriverJson.encode(full.get("result")));
    }
    private static RawJson frame(String id,String mode) throws IOException {
        var n=(com.fasterxml.jackson.databind.node.ObjectNode)NativeWire.parse(new byte[]{'{','}'});
        n.put("type","command_result").put("protocol_version",1).put("request_id",id).put("ok",!mode.equals("native-rejected"));
        if(mode.equals("native-rejected"))n.put("error","original declaration query rejected");
        else {
            var result=n.putObject("result").put("step","query-declarable-wars").put("accepted",true).put("status","available").put("query_sequence",5);
            if(mode.equals("malformed"))result.put("query_sequence",true);
            var choice=result.putArray("declarable_wars").addObject().put("declaration_id","202-0--1").put("target_character_id",202)
                    .put("casus_belli_index",0).put("casus_belli_key","claim_cb").put("configuration_index",-1).put("claimant_character_id",-1);
            choice.putArray("target_title_ids").add(0).add(17);
        }
        return new RawJson(DriverJson.encode(OpportunityJson.parse(n.toString().getBytes(java.nio.charset.StandardCharsets.UTF_8))));
    }
    private record Central(AtomicReference<PlanningReadPort> actual) implements PlanningReadPort {
        private PlanningReadPort current(){return Objects.requireNonNull(actual.get());}
        @Override public <T> PlanningReadResult<T> read(ReadContract<T> contract,PlanningReadRequest request){throw new AssertionError("original writer must be borrowed");}
        @Override public <T> PlanningReadResult<T> read(ContinuityStorePort.Session same,ReadContract<T> contract,PlanningReadRequest request){return current().read(same,contract,request);}
        @Override public <T> PlanningReadAttempt<T> readOriginal(ContinuityStorePort.Session same,ReadContract<T> contract,PlanningReadRequest request){return current().readOriginal(same,contract,request);}
        @Override public Optional<NativeActionPort.AckReceived> pollOriginal(ContinuityStorePort.Session same,PlanningReadCoordinator.OriginalRead<?> original)throws IOException{return current().pollOriginal(same,original);}
        @Override public <T> PlanningReadResult<T> adoptOriginal(ContinuityStorePort.Session same,PlanningReadCoordinator.OriginalRead<T> original,
                NativeActionPort.AckReceived ack,PlanningReadRequest current,OpportunityJson.Obj semantic)throws IOException{return current().adoptOriginal(same,original,ack,current,semantic);}
    }
}
