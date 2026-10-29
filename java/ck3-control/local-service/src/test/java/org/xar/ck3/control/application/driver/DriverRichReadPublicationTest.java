package org.xar.ck3.control.application.driver;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.capabilities.*;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.history.DriverReadHistoryRowProducer;
import org.xar.ck3.control.application.history.DriverArmySummaryHistoryRowProducer;
import org.xar.ck3.control.nativebridge.history.OriginalDriverQueryHistorySettings;
import org.xar.ck3.control.application.history.DriverFailedReadHistoryRowProducer;
import org.xar.ck3.control.application.history.DriverReadHistoryFailureMaterial;
import org.xar.ck3.control.application.readiness.ReadinessAuthority;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture;
import org.xar.ck3.control.nativebridge.capabilities.army.*;

/** Actual software endpoint -> central originals -> installed Army service/projector -> sole writer -> complete Driver.
 * Empty Army scope proves the protocol, not any live Army/business result. No new Game fixture or authority is introduced. */
final class DriverRichReadPublicationTest {
    @TempDir Path directory;
    private static final String PROFILE="e".repeat(64);
    private record Installed(ArmyStrengthsContracts contracts,ArmyStrengthsPipeline pipeline) { }
    private record Scope(Session same,ReadinessAuthority.LeaseSnapshot lease) { }

    @Test void freshArmyArtifactAndABComponentsPublishOnlyTheirActualFinalCompleteResults() throws Exception {
        var installed=new AtomicReference<Installed>();var sequence=new AtomicInteger();
        try(var fixture=new ActionWriterIntegrationFixture(directory.resolve("rich-ab"),false,scenario(installed,sequence,false))) {
            var publisher=publisher(fixture);var initial=fixture.ready();var scope=new AtomicReference<Scope>();
            var first=new AtomicReference<ArmyStrengthsService.Reply>();var second=new AtomicReference<ArmyStrengthsService.Reply>();
            var originals=new ArrayList<PlanningReadResult.Known<?>>();
            fixture.bindKnownReadObserver((same,contract,known)->{originals.add(known);publisher.enqueue(same,contract,known);});
            var service=service(fixture,publisher,installed.get(),scope);
            fixture.writer.locked(same->{
                initialize(fixture,same,initial.request().before());
                fixture.collector.current(same,initial.request().before(),Instant.now().plusSeconds(20),lease->{
                    scope.set(new Scope(same,lease));
                    try {
                        service.scalarControl().set(ArmyPrivateScalarControl.Mode.COMPARE,lease.frame().identity().frame().revision());
                        first.set(service.queryAutoCore());assertEquals(2,fixture.scenarioReadWrites());
                        assertCompletedCore(fixture,same,first.get());
                        assertTrue(publisher.hasPending(same));assertEquals(0,lease.driver().driver().commandHistory().size());
                        service.scalarControl().set(ArmyPrivateScalarControl.Mode.USE,lease.frame().identity().frame().revision());
                        second.set(service.queryAutoCore());assertEquals(3,fixture.scenarioReadWrites());
                        assertCompletedCore(fixture,same,second.get());
                        assertThrows(IllegalArgumentException.class,()->publisher.flushActualReads(same));
                    }finally{scope.set(null);}return null;
                });
                var committed=publisher.flushActualReads(same).orElseThrow();assertEquals(1,committed.actual().head().sequence());
                assertFalse(publisher.hasPending(same));assertEquals(3,originals.size());
                fixture.collector.current(same,initial.request().before(),Instant.now().plusSeconds(20),lease->{
                    var complete=lease.driver().driver();assertEquals(2,complete.commandHistory().size(),"A/B must not publish an intermediate scalar/rich row");
                    assertArrayEquals(complete.encode(),DriverStateSnapshot.decodeComplete(complete.encode()).encode());
                    List<ArmyStrengthsService.Reply> replies=List.of(first.get(),second.get());
                    int writes=fixture.scenarioReadWrites();String head=same.head().digest();
                    for(int i=0;i<2;i++) {
                        var row=DriverReadHistoryRowProducer.decode(complete.commandHistory().get(i).originalRow().json());
                        assertEquals(DriverReadHistoryRowProducer.Kind.ARMY_STRENGTHS,row.provenance().kind());
                        assertEquals(i==0?2:1,row.provenance().componentReceipts().size());
                        assertEquals(DriverJson.object(ArmyStrengthsService.encodeDriver(replies.get(i)).bytes(),RawJson.MAXIMUM_BYTES),row.result());
                        assertEquals(row,DriverReadHistoryRowProducer.decode(row.encode()));
                        var contract=fixture.reads.catalog().contracts().stream().filter(value->value.contractId().equals(row.provenance().contractId())).findFirst().orElseThrow();
                        replay(fixture,same,contract,row);
                    }
                    RawJson exported=PublicSnapshotCodec.encode(PublicSnapshotCodec.export(lease.frame(),true));
                    Obj publicSnapshot=DriverJson.object(exported.bytes(),RawJson.MAXIMUM_BYTES);
                    var publicRows=array(publicSnapshot.get("native_command_history"),"public full history");assertEquals(2,publicRows.size());
                    for(int i=0;i<2;i++) {
                        Obj publicRow=object(publicRows.get(i),"public rich row");Obj publicResult=object(publicRow.get("result"),"public complete Army result");
                        assertEquals(new Text(replies.get(i).original().sequence().toString()),publicResult.get("query_sequence"));
                    }
                    assertEquals(lease.frame().semantic(),PublicSnapshotCodec.decode(exported),"whole Snapshot must restore true uint64 role values without guessing fields");
                    assertEquals(writes,fixture.scenarioReadWrites());assertEquals(head,same.head().digest());assertEquals(0,fixture.nativeActionWrites());return null;
                });return null;
            });
        }
    }
    @Test void actualDisabledStorePublishesSummaryAcrossPublicCallsAndColdReplayDoesNotRecordAgain()throws Exception {
        var installed=new AtomicReference<Installed>();var sequence=new AtomicInteger();var admissions=new AtomicInteger();
        var storageScope=new AtomicReference<Scope>();var firstFrame=new AtomicReference<DriverObservationAssembler.Complete>();
        var io=new ArmyQueryHistoryStore.ArtifactIO(){
            @Override public long existingFlatBytes(Path leaf){throw new AssertionError("zero must not scan");}
            @Override public ArmyQueryHistoryStore.StoredFile writeExclusive(Path target,long maximum,ArmyQueryHistoryStore.WriteBody body){throw new AssertionError("zero must not write");}
        };
        // Real software store and settings, directly installed; this is not a Root configured Bound.
        var store=new ArmyQueryHistoryStore(new ArmyQueryHistoryStore.Settings(directory.resolve("never-created"),0),()->{admissions.incrementAndGet();var held=java.util.Objects.requireNonNull(storageScope.get());var pin=held.same().capturePin(held.lease().originalSourceQualification().orElseThrow(),WriterContracts.MAX_PIN_BYTES);held.same().verifyPin(pin);},io);
        try(var fixture=new ActionWriterIntegrationFixture(directory.resolve("summary-ab"),false,scenario(installed,sequence,false,Optional.of(store)))) {
            var publisher=publisher(fixture);var initial=fixture.ready();var scope=new AtomicReference<Scope>();
            var knowns=new ArrayList<PlanningReadResult.Known<?>>();
            fixture.bindKnownReadObserver((same,contract,known)->{knowns.add(known);publisher.enqueue(same,contract,known);});
            var service=service(fixture,publisher,installed.get(),scope);
            fixture.writer.locked(same->{
                initialize(fixture,same,initial.request().before());
                fixture.collector.current(same,initial.request().before(),Instant.now().plusSeconds(20),lease->{
                    scope.set(new Scope(same,lease));storageScope.set(scope.get());firstFrame.compareAndSet(null,lease.frame());try{
                        service.scalarControl().set(ArmyPrivateScalarControl.Mode.COMPARE,lease.frame().identity().frame().revision());
                        service.queryAutoCore();assertEquals(2,fixture.scenarioReadWrites());
                    }finally{scope.set(null);}return null;
                });publisher.flushActualReads(same).orElseThrow();assertEquals(1,same.head().state().sequence());return null;
            });
            var next=new AtomicReference<org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity>();
            fixture.writer.locked(same->{
                fixture.collector.current(same,initial.request().before(),Instant.now().plusSeconds(20),lease->{
                    next.set(lease.frame().identity());scope.set(new Scope(same,lease));storageScope.set(scope.get());firstFrame.compareAndSet(null,lease.frame());try{
                        assertTrue(next.get().frame().revision().compareTo(initial.request().before().frame().revision())>0);
                        service.scalarControl().set(ArmyPrivateScalarControl.Mode.USE,next.get().frame().revision());
                        service.queryAutoCore();assertEquals(3,fixture.scenarioReadWrites());
                    }finally{scope.set(null);}return null;
                });publisher.flushActualReads(same).orElseThrow();assertEquals(2,same.head().state().sequence());return null;
            });
            fixture.writer.locked(same->fixture.collector.current(same,next.get(),Instant.now().plusSeconds(20),lease->{
                publisher.requireReadOnlyExtension(same,knowns.getFirst().receipt().before().binding(),firstFrame.get(),lease.driver()).requireCurrent(same);
                var driver=lease.driver().driver();assertEquals(2,driver.commandHistory().size());assertEquals(3,knowns.size());
                int guards=admissions.get(),writes=fixture.scenarioReadWrites();String head=same.head().digest();
                for(int i=0;i<2;i++){
                    var row=DriverArmySummaryHistoryRowProducer.decode(driver.commandHistory().get(i).originalRow().json());
                    assertEquals(i==0?2:1,row.source().componentReceipts().size());assertEquals(new Bool(false),row.result().get("full_result_preserved"));
                    assertFalse(row.result().members().containsKey("army_strengths"));assertEquals(row,DriverArmySummaryHistoryRowProducer.decode(row.encode()));
                    var identical=fixture.reads.catalog().contracts().stream().filter(value->value.contractId().equals(row.source().original().contractId())).findFirst().orElseThrow();
                    var replay=DriverArmySummaryHistoryRowProducer.replayCanonical(fixture.archive.withSession(same),fixture.reads.catalog(),identical,row);
                    assertEquals(row.source().originalReceipt(),replay.originalReceipt());
                }
                var exported=PublicSnapshotCodec.encode(PublicSnapshotCodec.export(lease.frame(),true));
                assertEquals(lease.frame().semantic(),PublicSnapshotCodec.decode(exported));
                var rows=array(DriverJson.object(exported.bytes(),RawJson.MAXIMUM_BYTES).get("native_command_history"),"summary history");assertEquals(2,rows.size());
                for(int i=0;i<2;i++){
                    var original=DriverArmySummaryHistoryRowProducer.decode(driver.commandHistory().get(i).originalRow().json());
                    assertEquals(new Text(original.source().querySequence().toString()),object(object(rows.get(i),"public row").get("result"),"public summary").get("query_sequence"));
                }
                assertEquals(guards,admissions.get());assertEquals(writes,fixture.scenarioReadWrites());assertEquals(head,same.head().digest());
                assertFalse(java.nio.file.Files.exists(directory.resolve("never-created")));return null;
            }));
        }
    }
    @Test void unavailableWithoutAnOpaqueForwardedAttemptCannotManufactureAnErrorHistoryRow() throws Exception {
        var installed=new AtomicReference<Installed>();var sequence=new AtomicInteger();
        try(var fixture=new ActionWriterIntegrationFixture(directory.resolve("rich-failure"),false,scenario(installed,sequence,true))) {
            var publisher=publisher(fixture);fixture.bindKnownReadObserver(publisher::enqueue);var initial=fixture.ready();var scope=new AtomicReference<Scope>();
            var service=service(fixture,publisher,installed.get(),scope);
            fixture.writer.locked(same->{
                initialize(fixture,same,initial.request().before());
                fixture.collector.current(same,initial.request().before(),Instant.now().plusSeconds(20),lease->{
                    scope.set(new Scope(same,lease));
                    try {
                        service.scalarControl().set(ArmyPrivateScalarControl.Mode.COMPARE,lease.frame().identity().frame().revision());
                        assertThrows(RuntimeException.class,service::queryAutoCore);assertEquals(2,fixture.scenarioReadWrites());
                        assertFalse(publisher.hasPending(same));assertTrue(lease.driver().driver().commandHistory().isEmpty());
                    }finally{scope.set(null);}return null;
                });
                assertTrue(publisher.flushActualReads(same).isEmpty());assertEquals(0,same.head().state().sequence());
                assertEquals(0,fixture.nativeActionWrites());return null;
            });
        }
    }
    @Test void actualFailedAttemptAndServiceExceptionPublishOneErrorThenRequireAFreshSourceAndRefuseReadOnlyReuse()throws Exception {
        var installed=new AtomicReference<Installed>();var sequence=new AtomicInteger();
        try(var fixture=new ActionWriterIntegrationFixture(directory.resolve("actual-failed-history"),false,scenario(installed,sequence,true))){
            var publisher=publisher(fixture);var initial=fixture.ready();var scope=new AtomicReference<Scope>();
            var knowns=new ArrayList<PlanningReadResult.Known<?>>();var failed=new AtomicReference<PlanningReadResult.Unavailable<?>>();
            var token=new AtomicReference<PlanningReadCoordinator.FailedReadAttempt>();
            var queryFrame=new AtomicReference<DriverObservationAssembler.Complete>();
            fixture.bindKnownReadObserver(new PlanningReadCoordinator.KnownReadObserver(){
                @Override public void afterKnown(Session same,ReadContract<?> contract,PlanningReadResult.Known<?> actual){
                    knowns.add(actual);publisher.enqueue(same,contract,actual);
                }
                @Override public void afterUnavailable(Session same,ReadContract<?> contract,PlanningReadRequest request,
                        PlanningReadResult.Unavailable<?> actual,Optional<PlanningReadCoordinator.FailedReadAttempt> original){
                    assertTrue(original.isPresent());failed.set(actual);token.set(original.orElseThrow());
                    publisher.retainUnavailable(same,contract,request,actual,original);
                }
            });
            var service=service(fixture,publisher,installed.get(),scope);
            var surfaced=assertThrows(IllegalStateException.class,()->fixture.writer.locked(same->{
                initialize(fixture,same,initial.request().before());RuntimeException primary=null;
                try {
                    return fixture.collector.current(same,initial.request().before(),Instant.now().plusSeconds(20),lease->{
                        scope.set(new Scope(same,lease));queryFrame.set(lease.frame());
                        try {
                            service.scalarControl().set(ArmyPrivateScalarControl.Mode.COMPARE,lease.frame().identity().frame().revision());
                            return service.queryAutoCore();
                        }finally{scope.set(null);}
                    });
                }catch(RuntimeException original){primary=original;throw original;}
                finally {
                    // The exception leaves the actual immutable collector scope before the same writer publishes.
                    try{assertTrue(publisher.flushActualReads(same).isPresent());}
                    catch(IOException|RuntimeException|AssertionError publicationFailure){if(primary!=null)primary.addSuppressed(publicationFailure);else throw publicationFailure;}
                }
            }));
            assertEquals(0,surfaced.getSuppressed().length);assertNotNull(failed.get());assertNotNull(token.get());
            assertEquals(failed.get().reason(),surfaced.getMessage());assertEquals(1,knowns.size());assertEquals(2,fixture.scenarioReadWrites());
            fixture.writer.locked(same->{
                assertFalse(publisher.hasPending(same));var current=fixture.driverAuthority().withFrozenFacts(same,frozen->assertInstanceOf(DriverSnapshotFacts.Known.class,frozen.state()));
                assertTrue(current.observation().isEmpty());assertEquals(Nil.INSTANCE,current.auxiliary().get("capability_observed_native_source"));
                assertEquals(Nil.INSTANCE,current.auxiliary().get(DriverRuntimeCapabilities.AUXILIARY_KEY));
                assertEquals(1,current.driver().commandHistory().size());assertEquals(1,same.head().state().sequence());
                var actual=DriverFailedReadHistoryRowProducer.decode(current.driver().commandHistory().getFirst().originalRow().json());
                assertFalse(actual.ok());assertFalse(actual.toJson().members().containsKey("result"));
                assertEquals(DriverReadHistoryFailureMaterial.unavailableError(failed.get()),actual.error());
                assertEquals(List.of(knowns.getFirst().originalReceipt()),actual.source().componentReceipts());
                assertEquals(actual,DriverFailedReadHistoryRowProducer.decode(actual.encode()));
                String head=same.head().digest();int writes=fixture.scenarioReadWrites();
                assertEquals(actual,DriverFailedReadHistoryRowProducer.replayOriginals(fixture.archive.withSession(same),fixture.reads.catalog(),actual));
                var source=actual.source();var dropped=new ArrayList<>(source.supportingEvidence());
                assertTrue(dropped.remove(token.get().before().binding().capabilityEvidence()),"the actual before-guard capability original belongs to the complete closure");
                var incomplete=new DriverFailedReadHistoryRowProducer.Source(source.kind(),source.contractId(),source.requestId(),source.attempt(),source.beforeDriver(),
                        source.driverFacts(),source.nativeFrame(),source.componentReceipts(),dropped,source.producerSources());
                var wrong=new DriverFailedReadHistoryRowProducer.RawHistoryRow(actual.index(),actual.command(),false,actual.error(),incomplete);
                assertThrows(IllegalArgumentException.class,()->DriverFailedReadHistoryRowProducer.replayOriginals(fixture.archive.withSession(same),fixture.reads.catalog(),wrong));
                assertEquals(head,same.head().digest());assertEquals(writes,fixture.scenarioReadWrites());
                return null;
            });
            // Use the real shared cache producer for the new observation, rather than restoring an old before-frame.
            fixture.driverAuthority().bindCapabilityObservation((nativeFrame,known)->{
                try {
                    var originals=fixture.archive.withSession(fixture.writer.borrowedSession());var nativeRef=originals.preserveNativeFrame(nativeFrame);
                    var complete=new DriverObservationAssembler().assemble(nativeFrame,known.observation().orElseThrow(),nativeRef);
                    return DriverCapabilityStateProducer.refresh(assertInstanceOf(DriverObservationAssembler.Complete.class,complete),known,originals);
                }catch(IOException failure){throw new UncheckedIOException(failure);}
            });
            fixture.writer.locked(same->fixture.collector.current(same,initial.request().before(),Instant.now().plusSeconds(20),lease->{
                assertNotEquals(Nil.INSTANCE,lease.driver().auxiliary().get("capability_observed_native_source"));
                var refused=assertThrows(IllegalArgumentException.class,()->publisher.requireReadOnlyExtension(same,
                        knowns.getFirst().receipt().before().binding(),queryFrame.get(),lease.driver()));
                assertTrue(refused.getMessage().contains("failed read publication"),refused.getMessage());
                RawJson exported=PublicSnapshotCodec.encode(PublicSnapshotCodec.export(lease.frame(),true));
                var rows=array(DriverJson.object(exported.bytes(),RawJson.MAXIMUM_BYTES).get("native_command_history"),"whole failed history");
                assertEquals(1,rows.size());var row=object(rows.getFirst(),"actual public error row");
                assertEquals(new Bool(false),row.get("ok"));assertFalse(row.members().containsKey("result"));
                assertEquals(lease.frame().semantic(),PublicSnapshotCodec.decode(exported));
                assertEquals(2,fixture.scenarioReadWrites());assertEquals(0,fixture.nativeActionWrites());return null;
            }));
        }
    }
    @Test void nonemptyOriginalCoreReachesNextOrdinaryBalanceAndChangedNativeFrameClearsIt()throws Exception {
        var installed=new AtomicReference<Installed>();var sequence=new AtomicInteger();var active=new AtomicReference<Scope>();
        try(var fixture=new ActionWriterIntegrationFixture(directory.resolve("core-current"),false,coreScenario(installed,sequence,false))) {
            var publisher=publisher(fixture);var initial=coreScope(fixture);
            var originals=new ArrayList<PlanningReadResult.Known<?>>();var contracts=new ArrayList<ReadContract<?>>();
            var olderDrop=new AtomicReference<ArmyStrengthsReadValue.CoreAvailabilityInvalidation>();
            fixture.bindKnownReadObserver((same,contract,known)->{
                originals.add(known);contracts.add(contract);publisher.enqueue(same,contract,known);
            });
            var service=service(fixture,publisher,installed.get(),active);
            fixture.writer.locked(same->{
                initialize(fixture,same,initial.request().before());
                fixture.collector.current(same,initial.request().before(),Instant.now().plusSeconds(20),lease->{
                    active.set(new Scope(same,lease));
                    try {
                        assertEquals(2,service.queryAutoCore().original().rows().size());
                        var completed=fixture.driverAuthority().withFrozenFacts(same,frozen->
                                assertInstanceOf(DriverSnapshotFacts.Known.class,frozen.state()).auxiliary());
                        publisher.publishCompletedArmyCore(contracts.getFirst(),originals.getFirst());
                        fixture.driverAuthority().withFrozenFacts(same,frozen->{
                            assertEquals(completed,assertInstanceOf(DriverSnapshotFacts.Known.class,frozen.state()).auxiliary(),
                                    "same completed receipt must not mint another capability version");return null;
                        });
                    } finally { active.set(null); }
                    return null;
                });
                assertTrue(publisher.flushActualReads(same).isPresent());return null;
            });
            refreshCoreOnObservation(fixture,publisher);
            var next=fixture.ready();
            var balance=org.xar.ck3.control.application.planning.military.MilitaryPlanInputs.balance(next.request(),7).orElseThrow();
            assertEquals(BigInteger.ZERO,balance.friendlyCurrent(),"available zero soldiers must stay observed");
            assertEquals(BigInteger.valueOf(17),balance.enemyCurrent());assertTrue(balance.hostileOvermatch());
            assertEquals(List.of(new IntegerValue(BigInteger.ZERO)),array(balance.original().get("friendly_army_ids"),"Army 0"));
            var semantic=next.request().observations().snapshot();
            assertEquals(new Text("ordinary_core_v1"),semantic.get("army_strengths_profile"));
            assertEquals(originals.getFirst().receipt().request().before().frame().snapshotId(),
                    text(semantic.get("army_strengths_queried_snapshot_id"),"queried snapshot"));
            assertEquals(2,array(semantic.get("army_strengths"),"full Core").size());
            var actual=assertInstanceOf(ArmyStrengths.Read.class,originals.getFirst().value());
            var projection=actual.coreSemanticProjection();
            var subset=new ArmyStrengthsReadValue.CoreProjection(projection.profile(),ArmyStrengthsReadValue.Scope.SUBSET,
                    projection.status(),projection.querySequence(),projection.rows());
            assertEquals(ArmyStrengthsReadValue.cleared(),ArmyStrengthsReadValue.project(subset,actual.original()));
            var history=new ArmyStrengthsReadValue.CoreProjection(ArmyRequests.StrengthProfile.OBSERVED_HISTORY_FULL_V1,
                    projection.scope(),projection.status(),projection.querySequence(),projection.rows());
            assertEquals(ArmyStrengthsReadValue.cleared(),ArmyStrengthsReadValue.project(history,actual.original()));
            fixture.writer.locked(same->fixture.collector.current(same,next.request().before(),Instant.now().plusSeconds(20),lease->{
                assertEquals(lease.frame().semantic(),PublicSnapshotCodec.decode(PublicSnapshotCodec.encode(PublicSnapshotCodec.export(lease.frame(),true))));
                var originalSnapshot=lease.frame().semantic();
                var publicWire=DriverJson.object(PublicSnapshotCodec.encode(PublicSnapshotCodec.export(lease.frame(),true)).bytes(),RawJson.MAXIMUM_BYTES);
                assertEquals(new Text(actual.sequence().toString()),publicWire.get("army_strengths_query_sequence"));
                assertEquals(new Text(Long.toString(Long.MAX_VALUE)),object(array(publicWire.get("army_strengths"),"public Core").get(1),"public enemy").get("ai_base_power_raw"));
                assertBadCorePublic(publicWire.with("army_strengths_query_sequence",new IntegerValue(BigInteger.ONE)));
                assertBadCorePublic(publicWire.with("army_strengths_query_sequence",Nil.INSTANCE));
                var missing=new java.util.LinkedHashMap<>(publicWire.members());missing.remove("army_strengths_profile");assertBadCorePublic(new Obj(missing));
                var badRows=new ArrayList<Value>(array(publicWire.get("army_strengths"),"public Core"));
                Obj enemy=object(badRows.get(1),"enemy");
                badRows.set(1,enemy.with("ai_base_power_raw",new IntegerValue(BigInteger.ONE)));
                assertBadCorePublic(publicWire.with("army_strengths",new Arr(badRows)));
                badRows.set(1,enemy.with("ai_base_power_raw",new Text("9223372036854775808")));
                assertBadCorePublic(publicWire.with("army_strengths",new Arr(badRows)));
                var maxSequence=publicWire.with("army_strengths_query_sequence",new Text(org.xar.ck3.control.contracts.StrictJson.UINT64_MAX.toString()));
                assertEquals(new IntegerValue(org.xar.ck3.control.contracts.StrictJson.UINT64_MAX),
                        PublicSnapshotCodec.decode(new RawJson(DriverJson.encode(maxSequence))).get("army_strengths_query_sequence"));
                var drop=DriverSemanticReadState.coreInvalidation(lease.frame(),lease.driver(),Optional.of(originals.getFirst().originalReceipt()),fixture.archive.withSession(same)).orElseThrow();
                olderDrop.set(drop);
                var planningInputs=new org.xar.ck3.control.application.readiness.NativeReadinessCollector.PlanningInputs(
                        Set.of(),Set.of(),Optional.empty(),List.of(),Optional.empty(),Optional.empty(),false,Optional.empty(),Optional.of(drop));
                var restricted=planningInputs.planningSnapshot(lease.frame(),lease.driver());
                for(var field:ArmyStrengthsReadValue.cleared().members().entrySet())assertEquals(field.getValue(),restricted.get(field.getKey()));
                assertEquals(originalSnapshot,lease.frame().semantic(),"clear-only planning DATA cannot mutate Complete/raw");
                var wrongConnection=new ArmyStrengthsReadValue.CoreAvailabilityInvalidation(drop.receipt(),drop.before(),drop.source(),drop.sessionId(),drop.connectionGeneration().add(BigInteger.ONE));
                assertThrows(IllegalArgumentException.class,()->wrongConnection.planningSnapshot(lease.frame(),lease.driver()));
                var archived=fixture.archive.withSession(same);
                var replayedCore=ArmyStrengthsReadValue.replayFields(originals.getFirst().receipt(),archived);
                for(var field:replayedCore.members().entrySet())assertEquals(field.getValue(),lease.driver().auxiliary().get(field.getKey()));
                var outbound=originals.getFirst().receipt().original().outbound().orElseThrow().originalPacket();
                Obj actualWire=DriverJson.object(java.util.Arrays.copyOfRange(outbound,4,outbound.length),RawJson.MAXIMUM_BYTES);
                assertBadArchivedCore(archived,originals.getFirst().receipt(),actualWire.with("expected_revision",new Bool(true)));
                assertBadArchivedCore(archived,originals.getFirst().receipt(),actualWire.with("army_strengths_profile",new Text("private_auto_scalar_v1")));
                assertBadArchivedCore(archived,originals.getFirst().receipt(),actualWire.with("army_ids",new Arr(List.of(new IntegerValue(BigInteger.ZERO)))));

                for(String field:List.of("scope_role","war_ids")) {
                    var changedRows=new ArrayList<Value>(array(lease.driver().auxiliary().get("army_strengths"),"saved scope"));
                    var row=object(changedRows.get(1),"saved enemy");
                    changedRows.set(1,row.with(field,field.equals("scope_role")?new Text("active_war_ally"):new Arr(List.of())));
                    assertThrows(IllegalArgumentException.class,()->DriverSemanticReadState.replaySources(
                            lease.driver().auxiliary().with("army_strengths",new Arr(changedRows)),archived));
                }
                var savedRows=new ArrayList<Value>(array(lease.driver().auxiliary().get("army_strengths"),"saved Core"));
                savedRows.set(0,object(savedRows.get(0),"saved Army").with("current_soldiers",new IntegerValue(BigInteger.ONE)));
                Obj tampered=lease.driver().auxiliary().with("army_strengths",new Arr(savedRows));
                assertThrows(IllegalArgumentException.class,()->DriverSemanticReadState.replaySources(tampered,archived));
                assertBadCorePublic(publicWire.with("army_strengths_query_sequence",new Bool(true)));

                assertEquals(DriverSemanticReadState.clearForCold(lease.driver().auxiliary()),
                        DriverSemanticReadState.clearForCold(DriverSemanticReadState.clearForCold(lease.driver().auxiliary())));
                for(var field:ArmyStrengthsReadValue.cleared().members().entrySet())
                    assertEquals(field.getValue(),DriverSemanticReadState.clearForCold(lease.driver().auxiliary()).get(field.getKey()));
                var forged=new ArmyStrengths.Read(actual.profile(),actual.status(),actual.sequence().subtract(BigInteger.ONE),
                        actual.backendId(),actual.rows(),actual.timing(),actual.publishedScopeStatus(),actual.original());
                assertThrows(IllegalArgumentException.class,()->DriverSemanticReadState.apply(lease.frame(),lease.driver().auxiliary(),
                        contracts.getFirst(),new PlanningReadResult.Known<>(forged,originals.getFirst().receipt(),originals.getFirst().originalReceipt()),archived));
                return null;
            }));
            fixture.writer.locked(same->{
                fixture.collector.current(same,next.request().before(),Instant.now().plusSeconds(20),lease->{
                    active.set(new Scope(same,lease));try{service.queryAutoCore();}finally{active.set(null);}return null;
                });
                assertTrue(publisher.flushActualReads(same).isPresent());return null;
            });
            var later=fixture.ready();
            fixture.writer.locked(same->fixture.collector.current(same,later.request().before(),Instant.now().plusSeconds(20),lease->{
                assertNotEquals(olderDrop.get().receipt(),DriverSemanticReadState.armyCoreSource(lease.driver().auxiliary()).orElseThrow());
                var old=olderDrop.get();var frame=lease.frame();
                if(old.before().equals(frame.identity())&&old.source().equals(frame.source())&&old.sessionId().equals(frame.sessionId())
                        &&old.connectionGeneration().equals(frame.connectionGeneration()))
                    assertEquals(frame.semantic(),old.planningSnapshot(frame,lease.driver()));
                else assertThrows(IllegalArgumentException.class,()->old.planningSnapshot(frame,lease.driver()));
                var sameTargetOldReceipt=new ArmyStrengthsReadValue.CoreAvailabilityInvalidation(old.receipt(),frame.identity(),frame.source(),frame.sessionId(),frame.connectionGeneration());
                assertEquals(frame.semantic(),sameTargetOldReceipt.planningSnapshot(frame,lease.driver()),"old receipt cannot clear a later actual Known");
                return null;
            }));
            advanceCorePacket(fixture,later);
            var changed=fixture.ready();
            assertTrue(org.xar.ck3.control.application.planning.military.MilitaryPlanInputs.balance(changed.request(),7).isEmpty());
            for(var field:ArmyStrengthsReadValue.cleared().members().entrySet())assertEquals(field.getValue(),changed.request().observations().snapshot().get(field.getKey()));
            assertEquals(2,fixture.scenarioReadWrites());assertEquals(0,fixture.nativeActionWrites());
        }
    }

    @Test void actualUnavailableRetainsOriginalFailureAndNextObservationDropsOnlyItsOlderCoreSource()throws Exception {
        var installed=new AtomicReference<Installed>();var sequence=new AtomicInteger();var active=new AtomicReference<Scope>();
        try(var fixture=new ActionWriterIntegrationFixture(directory.resolve("core-failed"),false,coreScenario(installed,sequence,true))) {
            var publisher=publisher(fixture);var initial=coreScope(fixture);
            var pending=new AtomicReference<ExactRef>();var knowns=new ArrayList<PlanningReadResult.Known<?>>();
            var failed=new AtomicReference<PlanningReadResult.Unavailable<?>>();
            fixture.bindKnownReadObserver(new PlanningReadCoordinator.KnownReadObserver(){
                @Override public void afterKnown(Session same,ReadContract<?> contract,PlanningReadResult.Known<?> known){
                    knowns.add(known);publisher.enqueue(same,contract,known);
                }
                @Override public void afterUnavailable(Session same,ReadContract<?> contract,PlanningReadRequest request,
                        PlanningReadResult.Unavailable<?> unavailable,Optional<PlanningReadCoordinator.FailedReadAttempt> original){
                    assertTrue(original.isPresent());var archive=fixture.archive.withSession(same);
                    try {
                        original.orElseThrow().requireOriginal(same,contract,request,unavailable,archive);failed.set(unavailable);
                        fixture.driverAuthority().withFrozenFacts(same,frozen->{
                        var known=assertInstanceOf(DriverSnapshotFacts.Known.class,frozen.state());
                        pending.set(publisher.armyCoreUnavailable(known.auxiliary()).orElseThrow());
                        assertEquals(knowns.getFirst().originalReceipt(),pending.get());return null;
                    }); }catch(IOException failure){throw new UncheckedIOException(failure);}
                    publisher.retainUnavailable(same,contract,request,unavailable,original);
                }
            });
            var service=service(fixture,publisher,installed.get(),active);
            fixture.writer.locked(same->{
                initialize(fixture,same,initial.request().before());
                fixture.collector.current(same,initial.request().before(),Instant.now().plusSeconds(20),lease->{
                    active.set(new Scope(same,lease));try{service.queryAutoCore();}finally{active.set(null);}return null;
                });
                assertTrue(publisher.flushActualReads(same).isPresent());return null;
            });
            var full=fixture.ready();assertTrue(org.xar.ck3.control.application.planning.military.MilitaryPlanInputs.balance(full.request(),7).isPresent());
            fixture.writer.locked(same->{
                assertThrows(IllegalStateException.class,()->fixture.collector.current(same,full.request().before(),Instant.now().plusSeconds(20),lease->{
                    active.set(new Scope(same,lease));try{return service.queryAutoCore();}finally{active.set(null);}
                }));
                assertNotNull(failed.get());assertNotNull(pending.get());
                assertTrue(publisher.flushActualReads(same).isPresent());return null;
            });
            refreshCoreOnObservation(fixture,publisher);
            var after=fixture.ready();assertTrue(org.xar.ck3.control.application.planning.military.MilitaryPlanInputs.balance(after.request(),7).isEmpty());
            assertEquals(Nil.INSTANCE,after.request().observations().snapshot().get("army_strengths_query_sequence"));
            fixture.writer.locked(same->fixture.collector.current(same,after.request().before(),Instant.now().plusSeconds(20),lease->{
                assertTrue(DriverSemanticReadState.armyCoreSource(lease.driver().auxiliary()).isEmpty());
                assertEquals(2,lease.driver().driver().commandHistory().size());
                assertFalse(DriverFailedReadHistoryRowProducer.decode(lease.driver().driver().commandHistory().getLast().originalRow().json()).ok());
                return null;
            }));
            assertEquals(2,fixture.scenarioReadWrites());assertEquals(0,fixture.nativeActionWrites());
        }
    }

    @Test void refreshWithoutAttemptAndFailedComparisonCannotLeaveAnOlderCoreAvailable()throws Exception {
        for(boolean comparisonFailure:List.of(false,true)) {
            var installed=new AtomicReference<Installed>();var sequence=new AtomicInteger();var active=new AtomicReference<Scope>();
            try(var fixture=new ActionWriterIntegrationFixture(directory.resolve("core-refresh-"+comparisonFailure),false,
                    coreComparisonScenario(installed,sequence,comparisonFailure))) {
                var publisher=publisher(fixture);
                var completedReads=new ArrayList<PlanningReadResult.Known<?>>();var completedContracts=new ArrayList<ReadContract<?>>();
                fixture.bindKnownReadObserver((same,contract,known)->{completedReads.add(known);completedContracts.add(contract);publisher.enqueue(same,contract,known);});
                var initial=coreScope(fixture);var service=service(fixture,publisher,installed.get(),active);
                fixture.writer.locked(same->{
                    initialize(fixture,same,initial.request().before());
                    fixture.collector.current(same,initial.request().before(),Instant.now().plusSeconds(20),lease->{
                        active.set(new Scope(same,lease));
                        try {
                            service.queryAutoCore();
                            var older=completedReads.getLast();var contract=completedContracts.getLast();
                            assertThrows(RuntimeException.class,()->service.queryAutoCore(Optional.of(
                                    lease.frame().identity().frame().revision().add(BigInteger.ONE))));
                            publisher.publishCompletedArmyCore(contract,older);
                            fixture.driverAuthority().withFrozenFacts(same,frozen->{
                                var known=assertInstanceOf(DriverSnapshotFacts.Known.class,frozen.state());
                                var drop=publisher.armyCoreUnavailable(known.auxiliary());
                                assertEquals(Optional.of(older.originalReceipt()),drop,"reusing an older completed result cannot undo refresh invalidation");
                                var target=DriverSemanticReadState.coreInvalidation(lease.frame(),known,drop,fixture.archive.withSession(same)).orElseThrow();
                                assertEquals(Nil.INSTANCE,target.planningSnapshot(lease.frame(),known).get("army_strengths_query_sequence"));return null;
                            });
                            service.queryAutoCore();
                        }finally{active.set(null);}return null;
                    });
                    publisher.flushActualReads(same).orElseThrow();return null;
                });
                refreshCoreOnObservation(fixture,publisher);var ready=fixture.ready();
                assertTrue(org.xar.ck3.control.application.planning.military.MilitaryPlanInputs.balance(ready.request(),7).isPresent());
                fixture.writer.locked(same->{
                    fixture.collector.current(same,ready.request().before(),Instant.now().plusSeconds(20),lease->{
                        var oldSource=DriverSemanticReadState.armyCoreSource(lease.driver().auxiliary()).orElseThrow();
                        int writes=fixture.scenarioReadWrites();active.set(new Scope(same,lease));
                        try {
                            if(comparisonFailure){
                                service.scalarControl().set(ArmyPrivateScalarControl.Mode.COMPARE,lease.frame().identity().frame().revision());
                                assertThrows(RuntimeException.class,service::queryAutoCore);
                            } else assertThrows(RuntimeException.class,()->service.queryAutoCore(Optional.of(
                                    lease.frame().identity().frame().revision().add(BigInteger.ONE))));
                        }finally{active.set(null);}
                        assertEquals(writes+(comparisonFailure?2:0),fixture.scenarioReadWrites());
                        fixture.driverAuthority().withFrozenFacts(same,frozen->{
                            var known=assertInstanceOf(DriverSnapshotFacts.Known.class,frozen.state());
                            assertEquals(Optional.of(oldSource),DriverSemanticReadState.armyCoreSource(known.auxiliary()),
                                    "a failed refresh cannot publish an intermediate component");
                            var drop=publisher.armyCoreUnavailable(known.auxiliary());
                            assertEquals(Optional.of(oldSource),drop,"refresh starts before contract/Native dispatch");
                            var target=DriverSemanticReadState.coreInvalidation(lease.frame(),known,drop,fixture.archive.withSession(same)).orElseThrow();
                            var fields=target.planningSnapshot(lease.frame(),known);
                            for(var field:ArmyStrengthsReadValue.cleared().members().entrySet())assertEquals(field.getValue(),fields.get(field.getKey()));
                            return null;
                        });return null;
                    });
                    publisher.flushActualReads(same);return null;
                });
                refreshCoreOnObservation(fixture,publisher);var unavailable=fixture.ready();
                assertTrue(org.xar.ck3.control.application.planning.military.MilitaryPlanInputs.balance(unavailable.request(),7).isEmpty());
                assertEquals(Nil.INSTANCE,unavailable.request().observations().snapshot().get("army_strengths_query_sequence"));
                assertEquals(0,fixture.nativeActionWrites());
            }
        }
    }
    private ActionWriterIntegrationFixture.SoftwareReadScenario coreComparisonScenario(AtomicReference<Installed> installed,
            AtomicInteger sequence,boolean drift)throws IOException {
        var base=coreScenario(installed,sequence,false);
        return new ActionWriterIntegrationFixture.SoftwareReadScenario(base.profileSha256(),base.adapterId(),base.contracts(),request->{
            Obj body=DriverJson.object(base.result().apply(request).bytes(),RawJson.MAXIMUM_BYTES);
            if(drift&&sequence.get()==3) {
                var rows=new ArrayList<Value>(array(body.get("army_strengths"),"actual Core rows"));
                rows.set(1,object(rows.get(1),"enemy").with("current_soldiers",new IntegerValue(BigInteger.valueOf(18))));
                body=body.with("army_strengths",new Arr(rows));
            }
            return new RawJson(DriverJson.encode(body));
        },base.expectedCk3Version(),base.extraHelloCapabilities(),base.dynamicFamilies());
    }

    private static void assertBadArchivedCore(ActionPorts.OutcomeArchive archive,PlanningReadReceipt actual,Obj outgoing) {
        byte[] body=DriverJson.encode(outgoing);
        byte[] packet=java.nio.ByteBuffer.allocate(body.length+4).order(java.nio.ByteOrder.LITTLE_ENDIAN).putInt(body.length).put(body).array();
        var original=actual.original();
        var changed=new NativeActionPort.AckReceived(original.requestId(),original.nativeOk(),original.originalResultToken(),
                original.originalFrame(),original.originalPacket(),Optional.of(new NativeActionPort.OutboundPacket(original.requestId(),packet)),original.custody());
        var retained=new PlanningReadReceipt(actual.request(),actual.contractId(),actual.requestId(),actual.before(),actual.after(),
                changed,actual.adoption(),actual.archiveVersion());
        var failure=assertThrows(RuntimeException.class,()->{
            archive.preserve(changed);archive.preserveRead(retained);
            ArmyStrengthsReadValue.replayFields(retained,archive);
        });
        assertTrue(failure instanceof IllegalArgumentException||failure instanceof UncheckedIOException io
                &&"exact JSON integer required, rejecting boolean/float/string".equals(io.getCause().getMessage()),
                "original archive/wire contract must reject the changed packet");
    }
    private static com.fasterxml.jackson.databind.node.ObjectNode coreObject(byte[] raw) {
        return assertInstanceOf(com.fasterxml.jackson.databind.node.ObjectNode.class,org.xar.ck3.control.contracts.StrictJson.parse(raw));
    }
    private static void assertBadCorePublic(Obj publicData) {
        assertThrows(IllegalArgumentException.class,()->PublicSnapshotCodec.decode(new RawJson(DriverJson.encode(publicData))));
    }
    private ActionWriterIntegrationFixture.SoftwareReadScenario coreScenario(AtomicReference<Installed> installed,AtomicInteger sequence,boolean failSecond)throws IOException {
        var base=scenario(installed,sequence,failSecond);
        return new ActionWriterIntegrationFixture.SoftwareReadScenario(base.profileSha256(),base.adapterId(),base.contracts(),request->{
            var body=DriverJson.object(base.result().apply(request).bytes(),RawJson.MAXIMUM_BYTES);
            return new RawJson(DriverJson.encode(body.with("army_strengths",new Arr(List.of(coreRow(0,0,"player",0,0),coreRow(2,3,"active_war_enemy",17,Long.MAX_VALUE))))));
        },base.expectedCk3Version(),base.extraHelloCapabilities(),base.dynamicFamilies());
    }
    private static Obj coreRow(int army,int carmy,String role,int current,long power) {
        var row=new java.util.LinkedHashMap<String,Value>();
        row.put("status",new Text("available"));row.put("army_id",new IntegerValue(BigInteger.valueOf(army)));
        row.put("native_carmy_id",new IntegerValue(BigInteger.valueOf(carmy)));row.put("scope_role",new Text(role));
        row.put("war_ids",new Arr(List.of(new IntegerValue(BigInteger.valueOf(7)))));
        row.put("regiment_count",new IntegerValue(BigInteger.ONE));row.put("current_soldiers",new IntegerValue(BigInteger.valueOf(current)));
        row.put("maximum_soldiers",new IntegerValue(BigInteger.valueOf(20)));row.put("ai_base_power_raw",new IntegerValue(BigInteger.valueOf(power)));
        row.put("ai_base_power_scale",new IntegerValue(BigInteger.valueOf(100000)));row.put("unavailable_reason",Nil.INSTANCE);return new Obj(row);
    }
    private static org.xar.ck3.control.application.session.SessionPorts.Ready coreScope(ActionWriterIntegrationFixture fixture)throws Exception {
        var first=fixture.ready();var raw=coreRaw(fixture,first);
        var state=coreObject(raw.state().value());
        var player=org.xar.ck3.control.contracts.StrictJson.object().put("army_id",0).put("controllable",true).put("owner_character_id",73).put("current_province_id",30);
        var enemy=org.xar.ck3.control.contracts.StrictJson.object().put("army_id",2).put("controllable",false).put("owner_character_id",74).put("current_province_id",31);
        state.putArray("player_armies").add(player);
        var war=org.xar.ck3.control.contracts.StrictJson.object().put("war_id",7).put("player_side","attacker").put("player_relative_war_score",0);
        war.putArray("allied_armies").add(player);war.putArray("enemy_armies").add(enemy);state.putArray("active_wars").add(war);
        enqueueCorePacket(fixture,raw,state);return fixture.ready();
    }
    private static org.xar.ck3.control.nativebridge.NativeWire.Snapshot coreRaw(ActionWriterIntegrationFixture fixture,
            org.xar.ck3.control.application.session.SessionPorts.Ready ready)throws IOException {
        byte[] original=fixture.writer.locked(same->fixture.collector.current(same,ready.request().before(),Instant.now().plusSeconds(20),
                lease->fixture.archive.withSession(same).loadNativeFrame(lease.frame().originalEvidence())));
        return assertInstanceOf(org.xar.ck3.control.nativebridge.NativeWire.Snapshot.class,org.xar.ck3.control.nativebridge.NativeWire.decode(original));
    }
    private static void enqueueCorePacket(ActionWriterIntegrationFixture fixture,org.xar.ck3.control.nativebridge.NativeWire.Snapshot raw,
            com.fasterxml.jackson.databind.node.ObjectNode state)throws IOException {
        var next=org.xar.ck3.control.contracts.StrictJson.object().put("type","state_snapshot").put("protocol_version",1).put("snapshot_id",raw.snapshotId()).put("revision",raw.revision().add(BigInteger.ONE));
        next.set("state",state);fixture.enqueueSoftwareNativePacket(org.xar.ck3.control.nativebridge.NativeWire.packet(org.xar.ck3.control.contracts.StrictJson.canonical(next)));
    }
    private static void advanceCorePacket(ActionWriterIntegrationFixture fixture,org.xar.ck3.control.application.session.SessionPorts.Ready current)throws IOException {
        var raw=coreRaw(fixture,current);enqueueCorePacket(fixture,raw,coreObject(raw.state().value()));
    }
    private static void assertCompletedCore(ActionWriterIntegrationFixture fixture,Session same,ArmyStrengthsService.Reply reply)throws IOException {
        fixture.driverAuthority().withFrozenFacts(same,frozen->{
            var known=assertInstanceOf(DriverSnapshotFacts.Known.class,frozen.state());
            assertEquals(new IntegerValue(reply.original().sequence()),known.auxiliary().get("army_strengths_query_sequence"),
                    "only the selected final rich/scalar component may publish Core");
            assertEquals(fixture.archive.withSession(same).readReferenceOf(reply.original().original()),
                    DriverSemanticReadState.armyCoreSource(known.auxiliary()).orElseThrow());
            return null;
        });
    }
    private static void refreshCoreOnObservation(ActionWriterIntegrationFixture fixture,DriverReadHistoryPublisher publisher) {
        fixture.driverAuthority().bindCapabilityObservation((nativeFrame,known)->{
            try {
                var originals=fixture.archive.withSession(fixture.writer.borrowedSession());var source=originals.preserveNativeFrame(nativeFrame);
                var frame=assertInstanceOf(DriverObservationAssembler.Complete.class,new DriverObservationAssembler().assemble(nativeFrame,known.observation().orElseThrow(),source));
                return DriverCapabilityStateProducer.refreshAfterUnavailableArmyCore(frame,known,publisher.armyCoreUnavailable(known.auxiliary()),originals);
            }catch(IOException failure){throw new UncheckedIOException(failure);}
        });
    }

    private ActionWriterIntegrationFixture.SoftwareReadScenario scenario(AtomicReference<Installed> target,AtomicInteger sequence,boolean rejectSecond) throws IOException {
        return scenario(target,sequence,rejectSecond,Optional.empty());
    }
    private ActionWriterIntegrationFixture.SoftwareReadScenario scenario(AtomicReference<Installed> target,AtomicInteger sequence,boolean rejectSecond,
            Optional<ArmyQueryHistoryStore> store) throws IOException {
        OriginalDriverQueryHistorySettings.DirectorySelection selection=store.isPresent()?new OriginalDriverQueryHistorySettings.Directory(directory.toAbsolutePath()):new OriginalDriverQueryHistorySettings.Disabled();
        byte[] settings=OriginalDriverQueryHistorySettings.encodeRequest(new OriginalDriverQueryHistorySettings.Request(
                "controlled-software-writer",Instant.EPOCH,Instant.EPOCH.plusSeconds(3600),
                new OriginalDriverQueryHistorySettings.JavaConfigured(selection,0,OriginalDriverQueryHistorySettings.Admission.ROOT_STORAGE)));
        Path settingsPath=directory.resolve("actual-settings-"+store.isPresent()+".json");java.nio.file.Files.write(settingsPath,settings);
        var settingsRef=new ExactRef(settingsPath.toString(),settings.length,ActionCodec.sha256(settings));
        return new ActionWriterIntegrationFixture.SoftwareReadScenario(PROFILE,"actual-rich-army",ignored->List.of(),request->{
            int number=sequence.incrementAndGet();var fields=DriverJson.object(request.additionalFields().bytes(),262144);
            var out=new java.util.LinkedHashMap<String,Value>();out.put("step",new Text(ArmyStrengths.STEP));out.put("accepted",new Bool(true));
            out.put("status",new Text("available"));out.put("query_sequence",rejectSecond&&number==2?new Bool(true):new IntegerValue(org.xar.ck3.control.contracts.StrictJson.UINT64_MAX.subtract(BigInteger.valueOf(3L-number))));
            out.put("backend_id",new Text("native-headless"));out.put("army_strengths_profile",fields.get("army_strengths_profile"));
            out.put("army_observed_phase_coverage",new Text("not_requested"));out.put("army_strengths",new Arr(List.of()));return new RawJson(DriverJson.encode(new Obj(out)));
        },Optional.empty(),Set.of(ArmyStrengths.CAPABILITY,ArmyPrivateScalarControl.CAPABILITY),source->{
            var normalizers=new ArmyStrengthsFamilies.Registry();normalizers.freeze();var pipeline=new ArmyStrengthsPipeline();pipeline.freeze();
            var contracts=new ArmyStrengthsContracts(source,source,normalizers,pipeline,List.of(source,settingsRef),store,settingsRef);target.set(new Installed(contracts,pipeline));return contracts.families();
        });
    }
    private static DriverReadHistoryPublisher publisher(ActionWriterIntegrationFixture fixture) throws IOException {
        var publisher=new DriverReadHistoryPublisher(fixture.driverAuthority(),fixture.archive,fixture.reads.catalog(),List.of(fixture.observationSource().sourceRef()));
        fixture.bindAdditionalTransitionAuthority(WriterContracts.DRIVER_READ_HISTORY_KIND,publisher);
        publisher.bindArmyCorePublication(fixture.driverAuthority(),fixture.archive,()->{
            try{return fixture.writer.borrowedSession();}
            catch(IOException failure){throw new UncheckedIOException("actual fixture borrowed writer unavailable",failure);}
        });return publisher;
    }
    private static ArmyStrengthsService service(ActionWriterIntegrationFixture fixture,DriverReadHistoryPublisher publisher,Installed installed,AtomicReference<Scope> active) {
        ArmyStrengthsService.Current current=()->{
            Scope scope=java.util.Objects.requireNonNull(active.get(),"current must borrow its original collector scope");
            try{return fixture.collector.borrowCurrent(scope.same(),scope.lease().frame().identity(),scope.lease().validUntil(),actual->
                new ArmyStrengthsService.CurrentFrame(ArmyStrengthsCodec.snapshot(new ArmyRetreatFrames.Current(actual.frame(),actual.validUntil()).context(),
                        new RawJson(DriverJson.encode(actual.frame().semantic()))),fixture.physicalInputs().transport().originalHello()));
            }catch(IOException failure){throw new UncheckedIOException(failure);}
        };
        var gate=new ArmyPrivateScalarControl(current,ignored->java.util.Objects.requireNonNull(active.get()).lease().originalSourceQualification().orElseThrow());
        return new ArmyStrengthsService(current,fixture.reads,fixture.reads.catalog(),installed.contracts(),new ArmyStrengthsCache(),installed.pipeline(),gate,publisher);
    }
    private static <T> void replay(ActionWriterIntegrationFixture fixture,Session same,ReadContract<T> actual,DriverReadHistoryRowProducer.RawHistoryRow row) {
        var replay=DriverReadHistoryRowProducer.replayCanonical(fixture.archive.withSession(same),fixture.reads.catalog(),actual,row);
        assertEquals(row.provenance().originalReceipt(),replay.originalReceipt());
        var projected=actual.projectOriginalHistory(replay.receipt());
        assertEquals(DriverJson.object(projected.fullResult().bytes(),RawJson.MAXIMUM_BYTES),row.result());
    }
    private static void initialize(ActionWriterIntegrationFixture fixture,Session same,
            org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity initial) throws IOException {
        fixture.collector.current(same,initial,Instant.now().plusSeconds(20),lease->{
            var configuration=new DynamicCapabilities.Configuration(Optional.empty(),Optional.empty(),3,3,false,false);
            var presentation=new CapabilitySessionPresentation(false,Optional.empty(),Optional.of(CapabilitySessionPresentation.RestoreKind.NEW_EPISODE),
                    CapabilitySessionPresentation.BindingState.ACTIVE_NEW,Optional.empty(),Optional.empty(),Optional.empty(),Optional.empty());
            var policy=fixture.archive.preserveMaterial(new RawJson(DriverJson.encode(new Obj(Map.of("actual_software_start_policy",new Bool(true))))));
            var produced=DriverCapabilityStateProducer.initializeNewEpisode(lease.frame(),lease.driver(),configuration,presentation,policy,fixture.archive.withSession(same));
            fixture.driverAuthority().publishCapabilityInputs(same,lease.driver().stamp(),produced.expectedAuxiliarySha256(),produced);return null;
        });
    }
}
