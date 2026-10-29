package org.xar.ck3.control.application.driver;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
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
import org.xar.ck3.control.application.planning.PlanningObservation;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.warexit.WarExitReads;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture;
import org.xar.ck3.control.nativebridge.capabilities.army.*;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;
import org.xar.ck3.control.wave2.military.combatwire.CombatSimulationInputsCodec;
import org.xar.ck3.control.wave2.military.combatwire.CombatPhaseInputsCodec;
import org.xar.ck3.control.wave2.military.combatwire.phaseevent.StockPhaseEventRuntime;
import org.xar.ck3.control.wave2.military.forecast.CombatObservationCache;

/** Real dynamic catalog, central read, writer, archive and M0 activation; software packets grant no live/cold-process credit. */
final class DriverDeclarationCanonicalWriterTest {
    @TempDir Path directory;
    @Test void actualDeclaredReadHistoryRebuildsTheAbsentHotLeaseThroughItsIdenticalInstalledFamilyWithoutNativeResubmission() throws Exception {
        var central=new AtomicReference<PlanningReadPort>();var dependencies=new AtomicReference<ArmyWarReads.IndependentDependencies>();
        var warOwner=new AtomicReference<ArmyWarReads>();var sourceRef=new AtomicReference<ExactRef>();
        PlanningReadPort borrowed=new PlanningReadPort(){
            @Override public <T> PlanningReadResult<T> read(ReadContract<T> contract,PlanningReadRequest request){throw new AssertionError("this physical chain must borrow the original writer");}
            @Override public <T> PlanningReadResult<T> read(ContinuityStorePort.Session same,ReadContract<T> contract,PlanningReadRequest request){return Objects.requireNonNull(central.get()).read(same,contract,request);}
        };
        var scenario=new ActionWriterIntegrationFixture.SoftwareReadScenario("0".repeat(64),"actual-dynamic-declaration-history",
                source->List.of(),request->declarations(),Optional.empty(),Set.of(),source->{
                    sourceRef.set(source);var actual=new ArmyWarReads(source,source,borrowed,()->Objects.requireNonNull(dependencies.get()));
                    warOwner.set(actual);return actual.families();
                });
        try(var f=new ActionWriterIntegrationFixture(directory.resolve("physical-declaration"),false,scenario)) {
            central.set(f.reads);var wars=Objects.requireNonNull(warOwner.get());var source=Objects.requireNonNull(sourceRef.get());
            var publisher=new DriverReadHistoryPublisher(f.driverAuthority(),f.archive,f.reads.catalog(),List.of(source));
            f.bindAdditionalTransitionAuthority(WriterContracts.DRIVER_READ_HISTORY_KIND,publisher);
            var session=new AtomicReference<ContinuityStorePort.Session>();var simulation=new CombatSimulationInputsCodec();
            var cache=new CombatObservationCache(simulation,new CombatPhaseInputsCodec(simulation,new StockPhaseEventRuntime()));
            var forecasts=new ArmyForecastReads(source,source,borrowed,cache,f.frameLoader(),f.archive,()->Objects.requireNonNull(session.get()));
            dependencies.set(new ArmyWarReads.IndependentDependencies(forecasts,publisher));var initial=f.ready();
            var retainedWarExitLease=new AtomicReference<WarExitReads.DeclarationLease>();var retainedPlan=new AtomicReference<PlanningRequest>();
            f.writer.locked(same->{
                session.set(same);
                try {
                    f.collector.current(same,initial.request().before(),Instant.now().plusSeconds(20),lease->{
                        var configuration=new DynamicCapabilities.Configuration(Optional.empty(),Optional.empty(),3,3,false,false);
                        var presentation=new CapabilitySessionPresentation(false,Optional.empty(),Optional.of(CapabilitySessionPresentation.RestoreKind.NEW_EPISODE),
                                CapabilitySessionPresentation.BindingState.ACTIVE_NEW,Optional.empty(),Optional.empty(),Optional.empty(),Optional.empty());
                        var policy=f.archive.preserveMaterial(new RawJson(DriverJson.encode(new Obj(Map.of("actual_software_start_policy",new Bool(true))))));
                        var produced=DriverCapabilityStateProducer.initializeNewEpisode(lease.frame(),lease.driver(),configuration,presentation,policy,f.archive.withSession(same));
                        f.driverAuthority().publishCapabilityInputs(same,lease.driver().stamp(),produced.expectedAuxiliarySha256(),produced);return null;
                    });
                    var original=new AtomicReference<PlanningReadResult.Known<ArmyWarReadCodec.Observation>>();
                    f.collector.current(same,initial.request().before(),Instant.now().plusSeconds(20),lease->{
                        var current=new ArmyRetreatFrames.Current(lease.frame(),Instant.now().plusSeconds(20));
                        int writes=f.scenarioReadWrites();assertTrue(wars.currentDeclarations(current).isEmpty());
                        assertTrue(wars.canonicalDeclarations(same,f.reads.catalog(),current).isEmpty());assertEquals(writes,f.scenarioReadWrites());
                        var call=new ArmyCalls.Frame(PublicMethod.QUERY_DECLARABLE_WARS,new ArmyCalls.Revision(new ArmyTypes.Present<>(current.context().before().frame().revision())));
                        var selected=new ArmyWarReads.Selection(call,current,Optional.empty());var contract=wars.contract(f.reads.catalog(),selected);
                        var request=new PlanningReadRequest(current.context().before(),current.context().source(),current.context().sessionId(),contract.operation(),ArmyWarReads.arguments(call),current.context().deadline());
                        // Invoke the actual central read directly, so the M0 hot cache is still absent when history is later consumed.
                        var result=f.reads.read(same,contract,request);
                        if(!(result instanceof PlanningReadResult.Known<ArmyWarReadCodec.Observation> known))throw new AssertionError(result);
                        assertInstanceOf(ArmyWarReadCodec.Declarations.class,known.value());original.set(known);
                        assertTrue(wars.currentDeclarations(current).isEmpty());publisher.enqueue(same,contract,known);
                        assertTrue(publisher.hasPending(same));assertThrows(IllegalArgumentException.class,()->publisher.flushActualReads(same));return null;
                    });
                    var committed=publisher.flushActualReads(same).orElseThrow();assertEquals(1,committed.actual().head().sequence());
                    f.collector.current(same,initial.request().before(),Instant.now().plusSeconds(20),lease->{
                        assertEquals(1,lease.driver().driver().commandHistory().size());
                        var roundtrip=DriverStateSnapshot.decodeComplete(lease.driver().driver().encode());assertArrayEquals(lease.driver().driver().encode(),roundtrip.encode());
                        var current=new ArmyRetreatFrames.Current(lease.frame(),Instant.now().plusSeconds(20));assertTrue(wars.currentDeclarations(current).isEmpty());
                        int writes=f.scenarioReadWrites();var rebuilt=wars.canonicalDeclarations(same,f.reads.catalog(),current).orElseThrow();
                        assertEquals(original.get().originalReceipt(),rebuilt.evidence());assertEquals(original.get().value(),rebuilt.value());
                        assertEquals("202-0--1",rebuilt.selected(current,"202-0--1").declarationId());
                        assertSame(rebuilt,wars.requireCurrentDeclarations(current));assertEquals(writes,f.scenarioReadWrites());
                        var again=wars.canonicalDeclarations(same,f.reads.catalog(),current).orElseThrow();assertEquals(rebuilt.evidence(),again.evidence());assertEquals(writes,f.scenarioReadWrites());
                        var call=new ArmyCalls.Frame(PublicMethod.QUERY_DECLARABLE_WARS,new ArmyCalls.Revision(new ArmyTypes.Present<>(current.context().before().frame().revision())));
                        var contract=wars.contract(f.reads.catalog(),new ArmyWarReads.Selection(call,current,Optional.empty()));
                        var currentQuery=new PlanningReadRequest(current.context().before(),current.context().source(),current.context().sessionId(),contract.operation(),ArmyWarReads.arguments(call),current.context().deadline());
                        var observation=new PlanningObservation(lease.frame().semantic(),List.of(),Set.of(),Set.of(),Optional.empty(),List.of(),Optional.empty(),Optional.empty(),false);
                        var planning=new PlanningRequest(current.context().before(),current.context().source(),current.context().sessionId(),current.context().deadline(),observation);
                        String head=same.head().digest();var witness=publisher.canonicalReadWitness(same,contract,currentQuery).orElseThrow();
                        var originalReceipt=original.get().receipt();byte[] originalPacket=originalReceipt.original().originalFrame().bytes();
                        var exit=WarExitReads.DeclarationLease.fromCurrentCanonicalRead(same,witness,contract,currentQuery,planning);
                        assertTrue(exit.matches(planning));assertEquals(originalReceipt,exit.originalRead());
                        assertEquals(BigInteger.valueOf(5),exit.querySequence());assertEquals(rebuilt.value().choices(),exit.declarations());
                        assertEquals(rebuilt.selected(current,"202-0--1"),exit.selected("202-0--1"));
                        assertArrayEquals(originalPacket,exit.originalRead().original().originalFrame().bytes());
                        assertTrue(exit.matches(planning.withHistory(List.of(new Obj(Map.of("history_only_projection",new Bool(true)))))));
                        var frame=planning.before().frame();var shiftedFrame=new JointBudgetSelector.ProposalFrame(frame.identity(),frame.snapshotId(),frame.revision().add(BigInteger.ONE),frame.episodeRunId());
                        var shiftedIdentity=new ObservationIdentity(planning.before().machineId(),planning.before().game(),shiftedFrame,planning.before().observationVersion());
                        var shiftedSnapshot=planning.observations().snapshot().with("revision",new IntegerValue(shiftedFrame.revision()));
                        var shiftedObservation=new PlanningObservation(shiftedSnapshot,List.of(),Set.of(),Set.of(),Optional.empty(),List.of(),Optional.empty(),Optional.empty(),false);
                        var shifted=new PlanningRequest(shiftedIdentity,planning.source(),planning.sessionId(),planning.deadline(),shiftedObservation);
                        assertFalse(exit.matches(shifted));
                        var changedSource=new G2Source(planning.source().machineId(),Instant.now().plusSeconds(1).toString(),planning.source().exactBuild(),planning.source().sourceRef());
                        assertFalse(exit.matches(new PlanningRequest(planning.before(),changedSource,planning.sessionId(),planning.deadline(),observation)));
                        assertFalse(exit.matches(new PlanningRequest(planning.before(),planning.source(),"wrong-physical-session",planning.deadline(),observation)));
                        assertThrows(IllegalArgumentException.class,()->WarExitReads.DeclarationLease.fromCurrentCanonicalRead(same,witness,contract,currentQuery,shifted));
                        assertEquals(head,same.head().digest());assertEquals(writes,f.scenarioReadWrites());
                        retainedWarExitLease.set(exit);retainedPlan.set(planning);
                        var wrong=new PlanningReadRequest(current.context().before(),current.context().source(),current.context().sessionId(),contract.operation(),ArmyWarReads.arguments(call).with("wrong_argument",new Bool(true)),current.context().deadline());
                        assertTrue(publisher.canonicalReadWitness(same,contract,wrong).isEmpty());assertEquals(writes,f.scenarioReadWrites());assertEquals(0,f.nativeActionWrites());return null;
                    });
                    return null;
                }finally{session.set(null);}
            });
            int nativeReads=f.scenarioReadWrites();assertFalse(Objects.requireNonNull(retainedWarExitLease.get()).matches(Objects.requireNonNull(retainedPlan.get())),"a retained canonical lease cannot outlive its actual borrowed writer Session");
            assertEquals(nativeReads,f.scenarioReadWrites());assertEquals(0,f.nativeActionWrites());
        }
    }
    private static RawJson declarations(){
        Obj choice=new Obj(Map.of("declaration_id",new Text("202-0--1"),"target_character_id",new IntegerValue(BigInteger.valueOf(202)),
                "casus_belli_index",new IntegerValue(BigInteger.ZERO),"casus_belli_key",new Text("claim_cb"),"configuration_index",new IntegerValue(BigInteger.valueOf(-1)),
                "claimant_character_id",new IntegerValue(BigInteger.valueOf(-1)),"target_title_ids",new Arr(List.of(new IntegerValue(BigInteger.ZERO),new IntegerValue(BigInteger.valueOf(17))))));
        return new RawJson(DriverJson.encode(new Obj(Map.of("step",new Text("query-declarable-wars"),"accepted",new Bool(true),"status",new Text("available"),
                "query_sequence",new IntegerValue(BigInteger.valueOf(5)),"declarable_wars",new Arr(List.of(choice))))));
    }
}
