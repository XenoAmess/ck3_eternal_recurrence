package org.xar.ck3.control.application.driver;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.session.SessionPorts;
import org.xar.ck3.control.application.capabilities.*;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.effects.RootGuardEvidence;
import org.xar.ck3.control.application.planning.military.MilitaryReadObservation;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.planning.ProposalLifecycleCodec;
import org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Real writer/archive/collector with explicit software Native packet edges. No live CK3 qualification is claimed. */
final class DriverReadHistoryWriterTest {
    private static final String STEP="preview-move-army-0-to-4",CAP="game.command.preview-move-army-N-to-N";
    @TempDir Path temporary;
    @Test void actualArchivedQueriesPublishOnlyAfterFreezeAndReplayTheCompleteZeroAndMultipleReadLineage() throws Exception {
        var installed=new AtomicReference<ReadContract<MilitaryReadObservation>>();
        var scenario=new ActionWriterIntegrationFixture.SoftwareReadScenario("0".repeat(64),"actual-read-history-regression",source->{
            java.util.function.Function<PlanningReadReceipt,MilitaryReadObservation> decoder=DriverReadHistoryWriterTest::decode;
            var contract=new ReadContract<MilitaryReadObservation>("physical-original-route-preview",new OperationKey(STEP),Optional.of(CAP),CAP,
                    ReadContract.PermissionMode.ADVERTISED_CAPABILITY,ReadContract.WireProfile.EXECUTE_STEP,ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,source,
                    (request,id)->new NativeRequest(STEP,Optional.of(CAP),new RawJson(new byte[]{'{','}'})),decoder,decoder,
                    (original,value,current,semantic)->StrictJson.require(current.before().equals(original.request().before())
                            &&current.source().equals(original.request().source())&&current.sessionId().equals(original.request().sessionId())
                            &&current.arguments().equals(original.request().arguments()),"software route native operands changed"));
            installed.set(contract);return List.of(contract);
        },request->new RawJson(DriverJson.encode(new Obj(Map.of("step",new Text(STEP),"accepted",new Bool(true),"status",new Text("available"),
                "route_preview",new Obj(Map.of("army_id",new IntegerValue(BigInteger.ZERO),"origin_province_id",new IntegerValue(BigInteger.ONE),"target_province_id",new IntegerValue(BigInteger.valueOf(4)),
                        "status",new Text("available"),"route_province_ids",new Arr(List.of(new IntegerValue(BigInteger.ONE),new IntegerValue(BigInteger.valueOf(4)))))))))));
        try(var fixture=new ActionWriterIntegrationFixture(temporary.resolve("physical"),false,scenario)) {
            var initial=fixture.ready();var contract=installed.get();
            var publisher=new DriverReadHistoryPublisher(fixture.driverAuthority(),fixture.archive,fixture.reads.catalog(),List.of(contract.sourceRef()));
            fixture.bindAdditionalTransitionAuthority(WriterContracts.DRIVER_READ_HISTORY_KIND,publisher);
            fixture.bindAdditionalTransitionAuthority("fixture_non_read",new WriterContracts.TransitionAuthority(){
                @Override public String revalidate(ContinuityState before,WriterContracts.Request request){throw new AssertionError("actual Head required");}
                @Override public String revalidate(WriterContracts.Head before,WriterContracts.Request request){return ContinuityJson.digest(before.state().toJson());}
                @Override public ContinuityState reduce(ContinuityState before,WriterContracts.Request request){
                    var next=before.toJson();next.put("manual_repair_count",next.get("manual_repair_count").longValue()+1);return ContinuityState.fromJson(next,before.machineId());
                }
            });
            fixture.writer.locked(same->{
                fixture.collector.current(same,initial.request().before(),Instant.now().plusSeconds(20),lease->{
                    var configuration=new DynamicCapabilities.Configuration(Optional.empty(),Optional.empty(),3,3,false,false);
                    var session=new CapabilitySessionPresentation(false,Optional.empty(),Optional.of(CapabilitySessionPresentation.RestoreKind.NEW_EPISODE),
                            CapabilitySessionPresentation.BindingState.ACTIVE_NEW,Optional.empty(),Optional.empty(),Optional.empty(),Optional.empty());
                    var policy=fixture.archive.preserveMaterial(new RawJson("{\"actual_software_start_policy\":true}".getBytes(java.nio.charset.StandardCharsets.UTF_8)));
                    var produced=DriverCapabilityStateProducer.initializeNewEpisode(lease.frame(),lease.driver(),configuration,session,policy,fixture.archive.withSession(same));
                    fixture.driverAuthority().publishCapabilityInputs(same,lease.driver().stamp(),produced.expectedAuxiliarySha256(),produced);return null;
                });
                var originals=new ArrayList<PlanningReadResult.Known<MilitaryReadObservation>>();
                var queryFrame=new AtomicReference<Complete>();var originalGuard=new AtomicReference<GuardEvidence>();
                var zero=new AtomicReference<DriverReadHistoryPublisher.ReadOnlyExtension>();long originalVersion=fixture.driverAuthority().withFrozenFacts(same,frozen->((DriverSnapshotFacts.Known)frozen.state()).stamp().driverVersion());
                fixture.collector.current(same,initial.request().before(),Instant.now().plusSeconds(20),lease->{
                    for(int index=0;index<2;index++) {
                        var request=new PlanningReadRequest(lease.frame().identity(),lease.frame().source(),lease.frame().sessionId(),contract.operation(),new Obj(Map.of()),Instant.now().plusSeconds(20));
                        var result=fixture.reads.read(same,contract,request);
                        if(!(result instanceof PlanningReadResult.Known<MilitaryReadObservation> known))throw new AssertionError(result);
                        originals.add(known);
                        if(index==0) {
                            originalGuard.set(known.receipt().after().binding());queryFrame.set(RootGuardEvidence.loadFrame(originalGuard.get(),fixture.archive,fixture.frameLoader()));
                            zero.set(publisher.requireReadOnlyExtension(same,originalGuard.get(),queryFrame.get(),lease.driver()));
                            assertTrue(zero.get().eventSources().isEmpty());
                        }
                        publisher.enqueue(same,contract,known);
                    }
                    assertEquals(0,same.head().state().sequence());assertTrue(publisher.hasPending(same));
                    assertThrows(IllegalArgumentException.class,()->publisher.flushActualReads(same));
                    assertEquals(0,same.head().state().sequence());return null;
                });
                var first=publisher.flushActualReads(same).orElseThrow();assertEquals(0,first.predecessor().state().sequence());assertEquals(1,first.actual().head().sequence());
                assertFalse(publisher.hasPending(same));assertTrue(publisher.flushActualReads(same).isEmpty());
                assertThrows(IllegalArgumentException.class,()->zero.get().requireCurrent(same));
                fixture.collector.current(same,initial.request().before(),Instant.now().plusSeconds(20),lease->{
                    assertEquals(2,lease.driver().driver().commandHistory().size());assertEquals(originalVersion+1,lease.driver().stamp().driverVersion());
                    var proof=publisher.requireReadOnlyExtension(same,originalGuard.get(),queryFrame.get(),lease.driver()).requireCurrent(same);
                    assertEquals(1,proof.eventSources().size());
                    var current=new PlanningReadRequest(lease.frame().identity(),lease.frame().source(),lease.frame().sessionId(),contract.operation(),new Obj(Map.of()),Instant.now().plusSeconds(20));
                    int writes=fixture.scenarioReadWrites();var witness=publisher.canonicalReadWitness(same,contract,current).orElseThrow();
                    var replayed=witness.requireCurrent(same,contract,current);assertEquals(originals.getLast().originalReceipt(),replayed.originalReceipt());
                    assertEquals(originals.getLast().receipt(),replayed.receipt());assertEquals(writes,fixture.scenarioReadWrites());
                    var wrongArguments=new PlanningReadRequest(current.origin(),current.source(),current.sessionId(),current.operation(),new Obj(Map.of("different_public_argument",new Bool(true))),current.deadline());
                    assertTrue(publisher.canonicalReadWitness(same,contract,wrongArguments).isEmpty());assertEquals(writes,fixture.scenarioReadWrites());
                    var result=fixture.reads.read(same,contract,current);
                    if(!(result instanceof PlanningReadResult.Known<MilitaryReadObservation> known))throw new AssertionError(result);
                    publisher.enqueue(same,contract,known);return null;
                });
                publisher.flushActualReads(same).orElseThrow();
                var retained=new AtomicReference<DriverReadHistoryPublisher.ReadOnlyExtension>();
                var nonRead=new AtomicReference<WriterContracts.Request>();
                fixture.collector.current(same,initial.request().before(),Instant.now().plusSeconds(20),lease->{
                    assertEquals(3,lease.driver().driver().commandHistory().size());assertEquals(originalVersion+2,lease.driver().stamp().driverVersion());
                    var proof=publisher.requireReadOnlyExtension(same,originalGuard.get(),queryFrame.get(),lease.driver()).requireCurrent(same);
                    assertEquals(2,proof.eventSources().size());assertNotEquals(proof.queryDriver(),proof.currentDriver());
                    var details=StrictJson.object().put("evidence_id","actual-non-read-proof-invalidation");details.set("source",ProposalLifecycleCodec.source(lease.frame().source()));
                    nonRead.set(new WriterContracts.Request("fixture_non_read",StrictJson.canonical(details),List.of(contract.sourceRef())));retained.set(proof);return null;
                });
                same.commit(same.preview(nonRead.get()));assertThrows(IllegalArgumentException.class,()->retained.get().requireCurrent(same));
                assertEquals(0,fixture.nativeActionWrites());return null;
            });
        }
    }
    @Test void largeDefinitionAndDecoderRemainMetadataWhileActualReadDataCommits() throws Exception {
        String code="final class ControlledReadDefinition { /*"+"x".repeat(ContinuityJson.TRANSPORT_MAX_BYTES)+"*/ }\n";
        var installed=new AtomicReference<ReadContract<MilitaryReadObservation>>();
        var scenario=new ActionWriterIntegrationFixture.SoftwareReadScenario("0".repeat(64),"large-source-small-read-data",source->{
            java.util.function.Function<PlanningReadReceipt,MilitaryReadObservation> decoder=DriverReadHistoryWriterTest::decode;
            var contract=new ReadContract<MilitaryReadObservation>("physical-original-route-preview",new OperationKey(STEP),Optional.of(CAP),CAP,
                    ReadContract.PermissionMode.ADVERTISED_CAPABILITY,ReadContract.WireProfile.EXECUTE_STEP,ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,source,
                    (request,id)->new NativeRequest(STEP,Optional.of(CAP),new RawJson(new byte[]{'{','}'})),decoder,decoder,
                    (original,value,current,semantic)->StrictJson.require(current.before().equals(original.request().before())
                            &&current.source().equals(original.request().source())&&current.sessionId().equals(original.request().sessionId())
                            &&current.arguments().equals(original.request().arguments()),"software route native operands changed"));
            installed.set(contract);return List.of(contract);
        },request->new RawJson(DriverJson.encode(new Obj(Map.of("step",new Text(STEP),"accepted",new Bool(true),"status",new Text("available"),
                "route_preview",new Obj(Map.of("army_id",new IntegerValue(BigInteger.ZERO),"origin_province_id",new IntegerValue(BigInteger.ONE),"target_province_id",new IntegerValue(BigInteger.valueOf(4)),
                        "status",new Text("available"),"route_province_ids",new Arr(List.of(new IntegerValue(BigInteger.ONE),new IntegerValue(BigInteger.valueOf(4)))))))))),
                Optional.empty(),java.util.Set.of(),ignored->List.of(),Optional.of(code));
        try(var fixture=new ActionWriterIntegrationFixture(temporary.resolve("large-code-physical"),false,scenario)) {
            var contract=installed.get();var largeSource=contract.sourceRef();
            assertEquals(code,java.nio.file.Files.readString(Path.of(largeSource.path())));
            assertEquals(java.nio.file.Files.size(Path.of(largeSource.path())),largeSource.bytes());
            assertTrue(largeSource.bytes()>262144);assertEquals(262144,ContinuityJson.TRANSPORT_MAX_BYTES);
            var publisher=new DriverReadHistoryPublisher(fixture.driverAuthority(),fixture.archive,fixture.reads.catalog(),List.of(largeSource));
            var captured=new AtomicReference<WriterContracts.Request>();
            fixture.bindAdditionalTransitionAuthority(WriterContracts.DRIVER_READ_HISTORY_KIND,new WriterContracts.TransitionAuthority(){
                @Override public String revalidate(ContinuityState before,WriterContracts.Request request){throw new AssertionError("actual Head required");}
                @Override public String revalidate(WriterContracts.Head before,WriterContracts.Request request)throws java.io.IOException {
                    captured.set(request);return publisher.revalidate(before,request);
                }
                @Override public ContinuityState reduce(ContinuityState before,WriterContracts.Request request){return publisher.reduce(before,request);}
            });
            var initial=assertInstanceOf(SessionPorts.Ready.class,fixture.collector.observe(fixture.observationIdentity(),Instant.now().plusSeconds(60)));
            fixture.writer.locked(same->{
                fixture.collector.current(same,initial.request().before(),Instant.now().plusSeconds(60),lease->{
                    var configuration=new DynamicCapabilities.Configuration(Optional.empty(),Optional.empty(),3,3,false,false);
                    var session=new CapabilitySessionPresentation(false,Optional.empty(),Optional.of(CapabilitySessionPresentation.RestoreKind.NEW_EPISODE),
                            CapabilitySessionPresentation.BindingState.ACTIVE_NEW,Optional.empty(),Optional.empty(),Optional.empty(),Optional.empty());
                    var policy=fixture.archive.preserveMaterial(new RawJson("{\"actual_software_start_policy\":true}".getBytes(java.nio.charset.StandardCharsets.UTF_8)));
                    var produced=DriverCapabilityStateProducer.initializeNewEpisode(lease.frame(),lease.driver(),configuration,session,policy,fixture.archive.withSession(same));
                    fixture.driverAuthority().publishCapabilityInputs(same,lease.driver().stamp(),produced.expectedAuxiliarySha256(),produced);return null;
                });
                fixture.collector.current(same,initial.request().before(),Instant.now().plusSeconds(60),lease->{
                    var request=new PlanningReadRequest(lease.frame().identity(),lease.frame().source(),lease.frame().sessionId(),contract.operation(),new Obj(Map.of()),Instant.now().plusSeconds(60));
                    var result=fixture.reads.read(same,contract,request);
                    if(!(result instanceof PlanningReadResult.Known<MilitaryReadObservation> known))throw new AssertionError(result);
                    publisher.enqueue(same,contract,known);assertEquals(0,same.head().state().sequence());return null;
                });
                var committed=publisher.flushActualReads(same).orElseThrow();
                assertEquals(0,committed.predecessor().state().sequence());assertEquals(1,committed.actual().head().sequence());
                assertEquals(1,same.head().state().sequence());assertFalse(publisher.hasPending(same));
                var request=captured.get();assertNotNull(request);assertFalse(request.evidence().contains(largeSource));
                assertTrue(request.evidence().stream().allMatch(ref->ref.bytes()<=ContinuityJson.TRANSPORT_MAX_BYTES));
                var details=request.detailsObject();var rows=details.get("read_rows");assertEquals(1,rows.size());var metadata=rows.get(0);
                assertEquals(largeSource,org.xar.ck3.control.contracts.ExactRef.fromJson(metadata.get("definition_source")));
                assertEquals(largeSource,org.xar.ck3.control.contracts.ExactRef.fromJson(metadata.get("decoder_source")));
                var rowRef=org.xar.ck3.control.contracts.ExactRef.fromJson(metadata.get("row"));
                var readRef=org.xar.ck3.control.contracts.ExactRef.fromJson(metadata.get("read"));
                assertTrue(request.evidence().containsAll(List.of(rowRef,readRef)));
                var row=org.xar.ck3.control.application.history.DriverReadHistoryRowProducer.decode(fixture.archive.withSession(same).loadMaterial(rowRef).bytes());
                assertFalse(row.provenance().supportingEvidence().isEmpty());
                assertTrue(request.evidence().containsAll(row.provenance().supportingEvidence()));
                assertEquals(largeSource,row.provenance().definitionSource());assertEquals(largeSource,row.provenance().decoderSource());
                assertEquals(details,same.head().state().toJson().get(WriterContracts.DRIVER_READ_HISTORY_FIELD));
                fixture.driverAuthority().withFrozenFacts(same,frozen->{
                    var known=assertInstanceOf(DriverSnapshotFacts.Known.class,frozen.state());assertEquals(1,known.driver().commandHistory().size());return null;
                });
                assertEquals(0,fixture.nativeActionWrites());assertEquals(1,fixture.scenarioReadWrites());
                System.out.println("LARGE_CODE_SMALL_DATA_COMMITTED source_bytes="+largeSource.bytes()+" row_bytes="+rowRef.bytes()+" read_bytes="+readRef.bytes()+" provenance="+row.provenance().supportingEvidence()+" sequence="+same.head().state().sequence());
                return null;
            });
        }
    }
    private static MilitaryReadObservation decode(PlanningReadReceipt receipt) {
        Obj raw=DriverJson.object(receipt.original().originalResultToken().orElseThrow().bytes(),DriverJson.MAX_NATIVE_BYTES);var frame=receipt.request().before().frame();
        Obj result=raw.with("queried_snapshot_id",new Text(frame.snapshotId())).with("queried_revision",new IntegerValue(frame.revision()))
                .with("queried_native_revision",new IntegerValue(frame.identity().nativeRevision())).with("queried_connection_generation",new IntegerValue(receipt.before().binding().connectionGeneration()))
                .with("queried_episode_run_id",new Text(frame.episodeRunId()));return new MilitaryReadObservation(MilitaryReadObservation.Kind.ROUTE_PREVIEW,result);
    }
}
