package org.xar.ck3.control.application.driver;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.capabilities.*;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.history.DriverReadHistoryRowProducer;
import org.xar.ck3.control.application.planning.PlanningObservation;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.finance.FinanceReadContracts;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture;
import org.xar.ck3.control.wave2.governance.succession.NativePlayerHeirObservation12004;

/** Sole central observer, installed Finance decoder, actual archive/Driver/writer and canonical replay.
 * Software packets confer no actual Game, native succession, cold restore or process-continuation credit. */
final class DriverRootReadCanonicalWriterTest {
    private static final String PROFILE="98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518";
    @TempDir Path directory;

    @Test void actualPublicRootReadAutomaticallyPublishesCompleteOriginalAndReplaysFromTheCanonicalWriter() throws Exception {
        var definitions=new AtomicReference<FinanceReadContracts>();var source=new AtomicReference<ExactRef>();
        try(var fixture=new ActionWriterIntegrationFixture(directory.resolve("public-root"),false,scenario(definitions,source))) {
            var finance=Objects.requireNonNull(definitions.get());var contract=finance.contract(FinanceReadContracts.Query.ROOT);
            var publisher=publisher(fixture,source.get());var initial=fixture.ready();
            var original=new AtomicReference<PlanningReadResult.Known<FinanceReadContracts.Packet>>();
            fixture.writer.locked(same->{
                initialize(fixture,same,initial.request().before());
                fixture.collector.current(same,initial.request().before(),Instant.now().plusSeconds(20),lease->{
                    var request=planning(lease.frame());int writes=fixture.scenarioReadWrites();
                    assertTrue(publisher.canonicalReadWitness(same,contract,query(contract,request,FinanceReadContracts.RootCapture.PUBLIC_QUERY)).isEmpty());
                    var result=finance.read(same,FinanceReadContracts.Query.ROOT,fixture.reads,request);
                    var known=known(result);original.set(known);assertEquals(writes+1,fixture.scenarioReadWrites());
                    assertTrue(DriverReadHistoryRowProducer.shouldRecord(known));
                    assertTrue(publisher.hasPending(same),"the actual central KnownReadObserver must enqueue this public read");
                    assertThrows(IllegalArgumentException.class,()->publisher.flushActualReads(same));return null;
                });
                var actual=publisher.flushActualReads(same).orElseThrow();assertEquals(1,actual.actual().head().sequence());
                assertFalse(publisher.hasPending(same));
                fixture.collector.current(same,initial.request().before(),Instant.now().plusSeconds(20),lease->{
                    var complete=lease.driver().driver();assertEquals(1,complete.commandHistory().size());
                    assertArrayEquals(complete.encode(),DriverStateSnapshot.decodeComplete(complete.encode()).encode());
                    var row=DriverReadHistoryRowProducer.decode(complete.commandHistory().getFirst().originalRow().json());
                    assertEquals(DriverReadHistoryRowProducer.Kind.CAMPAIGN_ROOT_CONTEXT,row.provenance().kind());
                    assertEquals(Optional.of(StrictJson.UINT64_MAX),row.provenance().querySequence());
                    assertEquals(original.get().originalReceipt(),row.provenance().originalReceipt());
                    assertEquals(FinanceReadContracts.rootArguments(FinanceReadContracts.RootCapture.PUBLIC_QUERY),row.provenance().arguments());
                    assertEquals(row,DriverReadHistoryRowProducer.decode(row.encode()));
                    Obj root=object(row.result().get("campaign_root_context"),"actual original ROOT");
                    assertEquals(object(original.get().value().originalResult().get("campaign_root_context"),"original packet ROOT"),root);
                    assertEquals(new Text("unknown"),object(root.get("player_heir_candidate_v1"),"raw optional component").get("SDK_parse_status"));
                    RawJson publicSnapshot=PublicSnapshotCodec.encode(PublicSnapshotCodec.export(lease.frame(),true));
                    Obj published=DriverJson.object(publicSnapshot.bytes(),RawJson.MAXIMUM_BYTES);
                    Obj publicRow=object(array(published.get("native_command_history"),"public history").getFirst(),"public original row");
                    Obj publicResult=object(publicRow.get("result"),"public ROOT result");
                    assertEquals(new Text(StrictJson.UINT64_MAX.toString()),publicResult.get("query_sequence"));
                    assertEquals(new Text("1"),publicResult.get("snapshot_revision"));
                    assertEquals(new Text("1"),object(publicResult.get("campaign_root_context"),"public ROOT").get("snapshot_revision"));
                    assertEquals(lease.frame().semantic(),PublicSnapshotCodec.decode(publicSnapshot));
                    var request=planning(lease.frame());var current=query(contract,request,FinanceReadContracts.RootCapture.PUBLIC_QUERY);
                    int writes=fixture.scenarioReadWrites();String head=same.head().digest();
                    var witness=publisher.canonicalReadWitness(same,contract,current).orElseThrow();var replay=witness.requireCurrent(same,contract,current);
                    assertEquals(original.get().receipt(),replay.receipt());assertEquals(original.get().originalReceipt(),replay.originalReceipt());
                    assertEquals(original.get().value().result(),replay.value().result());
                    assertEquals(original.get().value().originalResult(),replay.value().originalResult());
                    assertArrayEquals(original.get().value().originalFrame(),replay.value().originalFrame());
                    assertEquals(head,same.head().digest());assertEquals(writes,fixture.scenarioReadWrites());
                    assertEquals(0,fixture.nativeActionWrites());
                    assertTrue(publisher.canonicalReadWitness(same,contract,query(contract,request,FinanceReadContracts.RootCapture.INTERNAL_PRECLOCK_ORIGINALS)).isEmpty());
                    var changed=row.toJson().with("result",row.result().with("snapshot_revision",new Bool(true)));
                    assertThrows(IllegalArgumentException.class,()->DriverReadHistoryRowProducer.decode(DriverJson.encode(changed)));
                    var incomplete=new java.util.LinkedHashMap<>(row.result().members());incomplete.remove("query_sequence");
                    assertThrows(IllegalArgumentException.class,()->DriverReadHistoryRowProducer.decode(DriverJson.encode(row.toJson().with("result",new Obj(incomplete)))));
                    var changedRoot=root.with("snapshot_revision",new IntegerValue(BigInteger.TWO));
                    assertThrows(IllegalArgumentException.class,()->DriverReadHistoryRowProducer.decode(DriverJson.encode(row.toJson().with("result",row.result().with("campaign_root_context",changedRoot)))));
                    return null;
                });return null;
            });
        }
    }

    @Test void actualOtherFinancePacketDoesNotGainPublicRootHistoryPolicy() throws Exception {
        var definitions=new AtomicReference<FinanceReadContracts>();var source=new AtomicReference<ExactRef>();
        try(var fixture=new ActionWriterIntegrationFixture(directory.resolve("other-finance"),false,scenario(definitions,source))) {
            var publisher=publisher(fixture,source.get());var initial=fixture.ready();
            fixture.writer.locked(same->{
                initialize(fixture,same,initial.request().before());
                fixture.collector.current(same,initial.request().before(),Instant.now().plusSeconds(20),lease->{
                    var actual=known(definitions.get().read(same,FinanceReadContracts.Query.CASH,fixture.reads,planning(lease.frame())));
                    assertFalse(DriverReadHistoryRowProducer.shouldRecord(actual));assertFalse(publisher.hasPending(same));return null;
                });
                assertTrue(publisher.flushActualReads(same).isEmpty());assertEquals(0,same.head().state().sequence());
                assertEquals(1,fixture.scenarioReadWrites());assertEquals(0,fixture.nativeActionWrites());return null;
            });
        }
    }

    @Test void strictOptionalHeirOriginalKeepsItsOwnUint64RevisionThroughTheActualPublicRootProducer() throws Exception {
        var definitions=new AtomicReference<FinanceReadContracts>();var source=new AtomicReference<ExactRef>();
        try(var fixture=new ActionWriterIntegrationFixture(directory.resolve("typed-optional-root"),false,scenario(definitions,source,true))) {
            var publisher=publisher(fixture,source.get());var initial=fixture.ready();
            fixture.writer.locked(same->{
                initialize(fixture,same,initial.request().before());
                fixture.collector.current(same,initial.request().before(),Instant.now().plusSeconds(20),lease->{
                    known(definitions.get().read(same,FinanceReadContracts.Query.ROOT,fixture.reads,planning(lease.frame())));return null;
                });
                publisher.flushActualReads(same).orElseThrow();
                fixture.collector.current(same,initial.request().before(),Instant.now().plusSeconds(20),lease->{
                    RawJson encoded=PublicSnapshotCodec.encode(PublicSnapshotCodec.export(lease.frame(),true));
                    Obj publicSnapshot=DriverJson.object(encoded.bytes(),RawJson.MAXIMUM_BYTES);
                    Obj row=object(array(publicSnapshot.get("native_command_history"),"actual history").getFirst(),"actual ROOT row");
                    Obj root=object(object(row.get("result"),"result").get("campaign_root_context"),"root");
                    Obj component=object(root.get(NativePlayerHeirObservation12004.COMPONENT),"strict original optional component");
                    assertEquals(new Text("1"),component.get("snapshot_revision"));
                    assertEquals(new Text("decimal-u64/v1"),row.get("xar_public_root_heir_revision"));
                    var missingMarker=new java.util.LinkedHashMap<>(row.members());missingMarker.remove("xar_public_root_heir_revision");
                    Obj noMarker=publicSnapshot.with("native_command_history",new Arr(List.of(new Obj(missingMarker))));
                    assertThrows(IllegalArgumentException.class,()->PublicSnapshotCodec.decode(new RawJson(DriverJson.encode(noMarker))));
                    Obj wrongMarker=publicSnapshot.with("native_command_history",new Arr(List.of(row.with("xar_public_root_heir_revision",new Text("unknown-representation")))));
                    assertThrows(IllegalArgumentException.class,()->PublicSnapshotCodec.decode(new RawJson(DriverJson.encode(wrongMarker))));
                    assertEquals(new Bool(true),object(component.get("observation"),"original optional observation").get("source_fixture"));
                    assertEquals(lease.frame().semantic(),PublicSnapshotCodec.decode(encoded));return null;
                });
                assertEquals(1,fixture.scenarioReadWrites());assertEquals(0,fixture.nativeActionWrites());return null;
            });
        }
    }

    @Test void actualInternalPreclockRootUsesTheSameInstalledContractButNeverEnqueuesAPublicReadBarrier() throws Exception {
        var definitions=new AtomicReference<FinanceReadContracts>();var source=new AtomicReference<ExactRef>();
        try(var fixture=new ActionWriterIntegrationFixture(directory.resolve("internal-root"),false,scenario(definitions,source))) {
            var contract=definitions.get().contract(FinanceReadContracts.Query.ROOT);var publisher=publisher(fixture,source.get());var initial=fixture.ready();
            fixture.writer.locked(same->{
                initialize(fixture,same,initial.request().before());
                fixture.collector.current(same,initial.request().before(),Instant.now().plusSeconds(20),lease->{
                    var request=query(contract,planning(lease.frame()),FinanceReadContracts.RootCapture.INTERNAL_PRECLOCK_ORIGINALS);
                    var actual=known(fixture.reads.read(same,contract,request));
                    assertEquals(FinanceReadContracts.RootCapture.INTERNAL_PRECLOCK_ORIGINALS,FinanceReadContracts.rootCapture(actual.receipt().request().arguments()));
                    assertFalse(DriverReadHistoryRowProducer.shouldRecord(actual));assertFalse(publisher.hasPending(same));
                    assertThrows(IllegalArgumentException.class,()->DriverReadHistoryRowProducer.prepare(fixture.archive.withSession(same),fixture.reads.catalog(),contract,actual,1));
                    return null;
                });
                assertTrue(publisher.flushActualReads(same).isEmpty());assertEquals(0,same.head().state().sequence());
                assertEquals(1,fixture.scenarioReadWrites());assertEquals(0,fixture.nativeActionWrites());return null;
            });
        }
    }

    @Test void malformedNativeTextRevisionIsPreservedAsTextAcrossTheActualCentralRootAndPublicRoundtrip() throws Exception {
        var definitions=new AtomicReference<FinanceReadContracts>();var source=new AtomicReference<ExactRef>();
        try(var fixture=new ActionWriterIntegrationFixture(directory.resolve("raw-text-optional-root"),false,scenario(definitions,source,2))) {
            var publisher=publisher(fixture,source.get());var initial=fixture.ready();
            fixture.writer.locked(same->{
                initialize(fixture,same,initial.request().before());
                fixture.collector.current(same,initial.request().before(),Instant.now().plusSeconds(20),lease->{
                    var actual=known(definitions.get().read(same,FinanceReadContracts.Query.ROOT,fixture.reads,planning(lease.frame())));
                    Obj originalRoot=object(actual.value().originalResult().get("campaign_root_context"),"original ROOT");
                    assertEquals(new Text("1"),object(originalRoot.get(NativePlayerHeirObservation12004.COMPONENT),"raw malformed optional").get("snapshot_revision"));
                    assertEquals(new Text("unknown"),object(object(actual.value().result().get("campaign_root_context"),"normalized root").get(NativePlayerHeirObservation12004.COMPONENT),"normalized Unknown").get("SDK_parse_status"));
                    return null;
                });
                publisher.flushActualReads(same).orElseThrow();
                fixture.collector.current(same,initial.request().before(),Instant.now().plusSeconds(20),lease->{
                    RawJson encoded=PublicSnapshotCodec.encode(PublicSnapshotCodec.export(lease.frame(),true));
                    Obj publicSnapshot=DriverJson.object(encoded.bytes(),RawJson.MAXIMUM_BYTES);
                    Obj row=object(array(publicSnapshot.get("native_command_history"),"actual history").getFirst(),"actual ROOT row");
                    Obj root=object(object(row.get("result"),"result").get("campaign_root_context"),"root");
                    assertEquals(new Text("raw-json/v1"),row.get("xar_public_root_heir_revision"));
                    assertEquals(new Text("1"),object(root.get(NativePlayerHeirObservation12004.COMPONENT),"raw optional").get("snapshot_revision"));
                    Obj restored=PublicSnapshotCodec.decode(encoded);assertEquals(lease.frame().semantic(),restored);
                    Obj internalRow=object(array(restored.get("native_command_history"),"restored actual history").getFirst(),"restored actual row");
                    assertFalse(internalRow.members().containsKey("xar_public_root_heir_revision"));return null;
                });
                assertEquals(1,fixture.scenarioReadWrites());assertEquals(0,fixture.nativeActionWrites());return null;
            });
        }
    }

    @Test void explicitRootCaptureWrapperRejectsOldEmptyAliasUnknownContextAndNonObjectPublicArguments() {
        for(var capture:FinanceReadContracts.RootCapture.values())assertEquals(capture,FinanceReadContracts.rootCapture(FinanceReadContracts.rootArguments(capture)));
        assertThrows(IllegalArgumentException.class,()->FinanceReadContracts.rootCapture(new Obj(Map.of())));
        assertThrows(IllegalArgumentException.class,()->FinanceReadContracts.rootCapture(new Obj(Map.of("capture_context",new Text("INTERNAL_OBSERVATION"),"public_arguments",new Obj(Map.of())))));
        assertThrows(IllegalArgumentException.class,()->FinanceReadContracts.rootCapture(new Obj(Map.of("capture_context",new Text("PUBLIC_QUERY"),"public_arguments",Nil.INSTANCE))));
        assertThrows(IllegalArgumentException.class,()->FinanceReadContracts.rootCapture(FinanceReadContracts.rootArguments(FinanceReadContracts.RootCapture.PUBLIC_QUERY).with("alias",new Bool(true))));
    }

    @Test void actualHistoricalReadIntervalSurvivesAnOutsideIntentWhileCurrentEligibilityRefusesIt() throws Exception {
        var definitions=new AtomicReference<FinanceReadContracts>();var source=new AtomicReference<ExactRef>();
        var original=new AtomicReference<PlanningReadResult.Known<FinanceReadContracts.Packet>>();
        var queryHeld=new AtomicReference<DriverObservationAssembler.Complete>();
        var escaped=new AtomicReference<DriverReadHistoryPublisher.HistoricalReadOnlyExtension>();
        try(var fixture=new ActionWriterIntegrationFixture(directory.resolve("historical-root-interval"),false,scenario(definitions,source))) {
            var publisher=publisher(fixture,source.get());var initial=fixture.ready();
            fixture.writer.locked(same->{
                initialize(fixture,same,initial.request().before());
                fixture.collector.current(same,initial.request().before(),Instant.now().plusSeconds(20),lease->{
                    queryHeld.set(lease.frame());
                    original.set(known(definitions.get().read(same,FinanceReadContracts.Query.ROOT,fixture.reads,planning(lease.frame()))));
                    return null;
                });
                assertTrue(publisher.hasPending(same));publisher.flushActualReads(same).orElseThrow();
                assertEquals(1,same.head().state().sequence());return null;
            });
            // The actual fixture's command producer observes the post-READ frame outside a borrowed writer lock.
            // Its ready() must not attempt a nested writer session; the later intent does not dispatch the command.
            ActionCommand intent=fixture.command("historical-root-interval-intent");
            fixture.writer.locked(same->{
                var targetGuard=new AtomicReference<GuardEvidence>();
                var targetHeld=new AtomicReference<DriverObservationAssembler.Complete>();
                var historical=new AtomicReference<DriverReadHistoryPublisher.HistoricalReadOnlyExtension>();
                var current=new AtomicReference<DriverReadHistoryPublisher.ReadOnlyExtension>();
                fixture.collector.current(same,intent.before(),Instant.now().plusSeconds(20),lease->{
                    var cash=known(definitions.get().read(same,FinanceReadContracts.Query.CASH,fixture.reads,planning(lease.frame())));
                    assertFalse(DriverReadHistoryRowProducer.shouldRecord(cash));assertFalse(publisher.hasPending(same));
                    targetGuard.set(cash.receipt().before().binding());targetHeld.set(lease.frame());
                    int reads=fixture.scenarioReadWrites(),nativeReads=fixture.nativeReadWrites();String head=same.head().digest();
                    var proof=publisher.requireHistoricalReadOnlyExtension(same,original.get().receipt(),targetGuard.get(),targetHeld.get());
                    historical.set(proof);escaped.set(proof);
                    current.set(publisher.requireReadOnlyExtension(same,original.get().receipt().before().binding(),queryHeld.get(),lease.driver()));
                    assertEquals(original.get().receipt(),proof.originalRead());
                    assertEquals(original.get().originalReceipt(),proof.originalReceipt());
                    assertEquals(queryHeld.get(),proof.queryObserved());assertEquals(lease.frame(),proof.targetObserved());
                    assertEquals(same.head().state().sequence(),proof.targetWriterPoint().sequence());
                    assertEquals(same.head().digest(),proof.targetWriterPoint().digest());assertEquals(1,proof.eventSources().size());
                    proof.requireHistorical(same);current.get().requireCurrent(same);
                    assertThrows(Exception.class,()->publisher.requireHistoricalReadOnlyExtension(same,original.get().receipt(),original.get().receipt().before().binding(),targetHeld.get()));
                    assertThrows(Exception.class,()->publisher.requireHistoricalReadOnlyExtension(same,original.get().receipt(),targetGuard.get(),queryHeld.get()));
                    assertThrows(Exception.class,()->publisher.requireHistoricalReadOnlyExtension(same,cash.receipt(),targetGuard.get(),targetHeld.get()));
                    var held=targetHeld.get();
                    var changedSource=new org.xar.ck3.control.g2.common.G2Source(held.identity().machineId(),Instant.EPOCH.toString(),"different-software-source",source.get());
                    var wrongSource=new DriverObservationAssembler.Complete(held.identity(),changedSource,held.sessionId(),held.connectionGeneration(),
                            held.semantic(),held.originalEvidence(),held.observedAt(),held.fullBindingSha256());
                    assertThrows(Exception.class,()->publisher.requireHistoricalReadOnlyExtension(same,original.get().receipt(),targetGuard.get(),wrongSource));

                    assertEquals(head,same.head().digest());assertEquals(reads,fixture.scenarioReadWrites());
                    assertEquals(nativeReads,fixture.nativeReadWrites());assertEquals(0,fixture.nativeActionWrites());return null;
                });
                assertTrue(publisher.flushActualReads(same).isEmpty());
                long target=historical.get().targetWriterPoint().sequence();
                fixture.journal.locked(same,locked->locked.append(intent,ActionCodec.bodySha256(intent),new ActionState.IntentDurable()));
                assertEquals(target+1,same.head().state().sequence());
                int reads=fixture.scenarioReadWrites(),nativeReads=fixture.nativeReadWrites();String head=same.head().digest();
                var replay=historical.get().requireHistorical(same);
                assertEquals(historical.get().targetWriterPoint(),replay.targetWriterPoint());
                assertEquals(historical.get().eventSources(),replay.eventSources());
                assertEquals(historical.get().queryDriver(),replay.queryDriver());assertEquals(historical.get().targetDriver(),replay.targetDriver());
                assertThrows(Exception.class,()->current.get().requireCurrent(same));
                assertEquals(head,same.head().digest());assertEquals(reads,fixture.scenarioReadWrites());
                assertEquals(nativeReads,fixture.nativeReadWrites());assertEquals(0,fixture.nativeActionWrites());return null;
            });
            fixture.writer.locked(same->{assertThrows(Exception.class,()->escaped.get().requireHistorical(same));return null;});
        }
    }

    private static ActionWriterIntegrationFixture.SoftwareReadScenario scenario(AtomicReference<FinanceReadContracts> target,AtomicReference<ExactRef> source) throws IOException {
        return scenario(target,source,false);
    }
    private static ActionWriterIntegrationFixture.SoftwareReadScenario scenario(AtomicReference<FinanceReadContracts> target,AtomicReference<ExactRef> source,boolean strictOptional) throws IOException {
        return scenario(target,source,strictOptional?1:0);
    }
    private static ActionWriterIntegrationFixture.SoftwareReadScenario scenario(AtomicReference<FinanceReadContracts> target,AtomicReference<ExactRef> source,int optionalMode) throws IOException {
        RawJson packet=switch(optionalMode){case 0->packet();case 1->packetWithStrictOptional();case 2->packetWithMalformedOptionalRevision();default->throw new IllegalArgumentException("unknown software optional variant");};
        return new ActionWriterIntegrationFixture.SoftwareReadScenario(PROFILE,"actual-root-read-history",ref->{
            source.set(ref);var definitions=new FinanceReadContracts(query->{
                String permission="game.command."+query.operation().value();return new FinanceReadContracts.Registration(ref,
                    new FinanceReadContracts.Permission(Optional.of(permission),permission,ReadContract.PermissionMode.ADVERTISED_CAPABILITY,ReadContract.WireProfile.EXECUTE_STEP));
            });
            target.set(definitions);return List.of(definitions.contract(FinanceReadContracts.Query.ROOT),definitions.contract(FinanceReadContracts.Query.CASH));
        },request->{
            if(request.step().equals(FinanceReadContracts.Query.CASH.operation().value())) {
                Obj fields=DriverJson.object(request.additionalFields().bytes(),RawJson.MAXIMUM_BYTES);
                assertEquals(Set.of("expected_snapshot_revision"),fields.members().keySet());
                return new RawJson(DriverJson.encode(new Obj(Map.of("step",new Text(request.step()),"accepted",new Bool(true)))));
            }
            assertEquals(FinanceReadContracts.Query.ROOT.operation().value(),request.step());
            assertTrue(request.additionalFields().objectFieldNames().isEmpty(),"typed public/internal capture wrapper must never leak into native additional fields");return packet;
        },Optional.of("1.20.0.4"),Set.of());
    }
    private static RawJson packet() throws IOException {
        try(var input=DriverRootReadCanonicalWriterTest.class.getResourceAsStream("campaign-root-native-v1-fixture.json")) {
            if(input==null)throw new IOException("exact ROOT software packet resource missing");return new RawJson(input.readAllBytes());
        }
    }
    private static RawJson packetWithStrictOptional() throws IOException {
        var core=new NativePlayerHeirObservation12004.Core(ActionWriterIntegrationFixture.INITIAL_DATE_RAW,true,0,0,true,true,73,true);
        var observation=new NativePlayerHeirObservation12004.Observation(true,null,true,true,core,core,true,true,73,74,true,true,true,
                new NativePlayerHeirObservation12004.Lineage(1,2),null);
        var component=new NativePlayerHeirObservation12004.Component(BigInteger.ONE,true,observation);
        Obj result=DriverJson.object(packet().bytes(),RawJson.MAXIMUM_BYTES);
        Obj root=object(result.get("campaign_root_context"),"software original root");
        Obj encoded=DriverJson.object(NativePlayerHeirObservation12004.encodeComponent(component),RawJson.MAXIMUM_BYTES);
        return new RawJson(DriverJson.encode(result.with("campaign_root_context",root.with(NativePlayerHeirObservation12004.COMPONENT,encoded))));
    }
    private static RawJson packetWithMalformedOptionalRevision() throws IOException {
        Obj result=DriverJson.object(packetWithStrictOptional().bytes(),RawJson.MAXIMUM_BYTES);
        Obj root=object(result.get("campaign_root_context"),"strict software root");
        Obj component=object(root.get(NativePlayerHeirObservation12004.COMPONENT),"original typed component").with("snapshot_revision",new Text("1"));
        return new RawJson(DriverJson.encode(result.with("campaign_root_context",root.with(NativePlayerHeirObservation12004.COMPONENT,component))));
    }
    private static DriverReadHistoryPublisher publisher(ActionWriterIntegrationFixture fixture,ExactRef source) throws IOException {
        var publisher=new DriverReadHistoryPublisher(fixture.driverAuthority(),fixture.archive,fixture.reads.catalog(),List.of(source));
        fixture.bindAdditionalTransitionAuthority(WriterContracts.DRIVER_READ_HISTORY_KIND,publisher);
        fixture.bindKnownReadObserver(publisher::enqueue);return publisher;
    }
    private static PlanningReadResult.Known<FinanceReadContracts.Packet> known(PlanningReadResult<FinanceReadContracts.Packet> result) {
        if(result instanceof PlanningReadResult.Known<FinanceReadContracts.Packet> known)return known;throw new AssertionError(result);
    }
    private static PlanningReadRequest query(ReadContract<FinanceReadContracts.Packet> contract,PlanningRequest request,FinanceReadContracts.RootCapture capture) {
        return new PlanningReadRequest(request.before(),request.source(),request.sessionId(),contract.operation(),FinanceReadContracts.rootArguments(capture),request.deadline());
    }
    private static PlanningRequest planning(DriverObservationAssembler.Complete frame) {
        var observation=new PlanningObservation(frame.semantic(),List.of(),Set.of(),Set.of(),Optional.empty(),List.of(),Optional.empty(),Optional.empty(),false);
        return new PlanningRequest(frame.identity(),frame.source(),frame.sessionId(),Instant.now().plusSeconds(20),observation);
    }
    private static void initialize(ActionWriterIntegrationFixture fixture,ContinuityStorePort.Session same,
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
