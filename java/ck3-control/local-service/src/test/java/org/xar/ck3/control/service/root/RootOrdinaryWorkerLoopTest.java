package org.xar.ck3.control.service.root;

import java.math.BigInteger;
import java.time.Duration;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
import org.xar.ck3.control.application.session.BatchReport;
import org.xar.ck3.control.application.session.SessionClock;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;

import java.io.IOException;
import java.nio.file.Path;
import java.time.Clock;
import java.util.Set;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.checkpoint.*;
import org.xar.ck3.control.application.driver.*;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.application.planning.campaign.M7CampaignPolicies.RealmLifecycle;
import org.xar.ck3.control.application.session.*;
import org.xar.ck3.control.continuity.OriginalWindowReducer;
import org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.GameLifecycle;
import static org.xar.ck3.control.application.session.SessionPorts.*;

/** Data regressions and an actual software ActionDriver/Controller boundary; no CK3 is started. */
final class RootOrdinaryWorkerLoopTest {
    @TempDir Path temporary;
    private static final ExactRef HEAD = new ExactRef("fixture-ledger-head", 1, "1".repeat(64));
    private static final ExactRef NEXT = new ExactRef("fixture-next-ledger-head", 1, "2".repeat(64));

    @Test void firstReportWithHistoricalHeadIsNotNewProgress() {
        assertFalse(RootOrdinaryWorkerLoop.progressed(report(1, HEAD, false), Optional.empty()));
    }
    @Test void unchangedHistoricalHeadDoesNotKeepEmptyBatchesAlive() {
        assertFalse(RootOrdinaryWorkerLoop.progressed(report(1, HEAD, false), Optional.of(report(1, HEAD, false))));
    }
    @Test void actualChangedCanonicalHeadCountsAsProgress() {
        assertTrue(RootOrdinaryWorkerLoop.progressed(report(1, NEXT, false), Optional.of(report(1, HEAD, false))));
    }
    @Test void changedHeadFromDifferentGameCannotSupplyProgress() {
        assertFalse(RootOrdinaryWorkerLoop.progressed(report(2, NEXT, false), Optional.of(report(1, HEAD, false))));
    }
    @Test void dirtyUnsavedTailAloneDoesNotPretendGameplayProgress() {
        assertFalse(RootOrdinaryWorkerLoop.progressed(report(1, HEAD, true), Optional.of(report(1, HEAD, false))));
    }
    @Test void wholeMillisecondBatchContractRemainsExact() {
        assertThrows(IllegalArgumentException.class, () -> new RootOrdinaryWorkerLoop.Configuration(
                "worker", 2, Duration.ofNanos(1), Duration.ofSeconds(1), Duration.ofMillis(1), 2));
    }

    @Test void cleanWallBoundaryAllowsContinuation() {
        assertTrue(RootOrdinaryWorkerLoop.isCleanWallBoundary(BatchReport.Terminal.WALL_TIMEOUT, false));
    }
    @Test void quarantinedWallBoundaryRejects() {
        assertFalse(RootOrdinaryWorkerLoop.isCleanWallBoundary(BatchReport.Terminal.WALL_TIMEOUT, true));
    }
    @Test void turnBoundaryIsNotCleanWallBoundary() {
        assertFalse(RootOrdinaryWorkerLoop.isCleanWallBoundary(BatchReport.Terminal.TURN_BOUND, false));
    }
    @Test void actionUnknownIsNotCleanWallBoundary() {
        assertFalse(RootOrdinaryWorkerLoop.isCleanWallBoundary(BatchReport.Terminal.ACTION_UNKNOWN, false));
    }
    @Test void writerUnknownIsNotCleanWallBoundary() {
        assertFalse(RootOrdinaryWorkerLoop.isCleanWallBoundary(BatchReport.Terminal.WRITER_UNKNOWN, false));
    }
    @Test void readinessTimeoutIsNotCleanWallBoundary() {
        assertFalse(RootOrdinaryWorkerLoop.isCleanWallBoundary(BatchReport.Terminal.READINESS_TIMEOUT, false));
    }

    private static BatchReport report(long gamePid, ExactRef head, boolean dirty) {
        var identity = new SessionIdentity("fixture-machine", new GameGeneration(gamePid,
                new PythonOnlyUInt64(BigInteger.valueOf(100))), "same-session-id");
        var tick = new SessionClock.Tick(0, Instant.parse("2026-10-28T00:00:00Z"));
        return new BatchReport(identity, "batch-01", BatchReport.Terminal.TURN_BOUND, "fixture boundary",
                tick, tick, List.of(), List.of(), List.of(), List.of(), List.of(), List.of(),
                Optional.empty(), Optional.empty(), Optional.empty(), Optional.empty(), Optional.of(head),
                0, dirty ? 1 : 0, dirty, List.of(), List.of(), List.of());
    }
    @Test void actualDirtyDeferredBatchHonorsWorkerStopWithoutSave()throws Exception {
        var actual=new java.util.concurrent.atomic.AtomicReference<ActionWriterIntegrationFixture>();
        var afterPacket=new java.util.concurrent.atomic.AtomicReference<byte[]>();
        var operation=new OperationKey("dirty-business-software-v1");
        var scenario=new ActionWriterIntegrationFixture.SoftwareActionScenario(operation,"game.command.dirty-business-software-v1",
                (command,attempt,dispatch)->{
                    try {
                        var after=dirtyReady(actual.get(),command.deadline());var semantic=after.semanticEvidence().orElseThrow();
                        var identity=after.request().before();
                        return new ActionPorts.EffectObserved(new ActionState.EffectObservation(identity,command.source(),command.sessionId(),
                                command.expected().observerSchema(),command.expected().values(),
                                new ObservationProvenance.Push(identity.frame().snapshotId(),identity.frame().identity().nativeRevision(),semantic.originalNativePacket()),
                                semantic.observedAt(),semantic.originalNativePacket(),List.of(semantic.semantic())));
                    }catch(Exception failure){throw new IllegalStateException(failure);}
                },()->actual.get().enqueueSoftwareNativePacket(afterPacket.get()),Optional.empty(),Optional.empty(),true);
        try(var fixture=new ActionWriterIntegrationFixture(temporary.resolve("actual-dirty"),false,scenario)) {
            actual.set(fixture);
            fixture.bindAdditionalArchivedVerifier(new org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier.Binding(operation,
                    fixture.observationSource().sourceRef(),(head,receipt,archive)->{
                assertEquals(operation,receipt.command().operation());var effect=receipt.applied().orElseThrow().observation();
                NativeWire.Snapshot original;
                try{original=assertInstanceOf(NativeWire.Snapshot.class,NativeWire.decode(archive.loadNativeFrame(effect.originalEvidence())));}
                catch(IOException failure){throw new java.io.UncheckedIOException(failure);}
                assertEquals(original.snapshotId(),effect.after().frame().snapshotId());
                assertEquals(original.revision(),effect.after().frame().identity().nativeRevision());
                var raw=org.xar.ck3.control.contracts.FullJsonTree.parse(original.state().value(),DriverJson.MAX_NATIVE_BYTES);
                assertTrue(raw.get("paused").booleanValue());
                assertEquals(1,effect.supportingEvidence().size());
                var retained=org.xar.ck3.control.contracts.FullJsonTree.parse(archive.loadMaterial(effect.supportingEvidence().getFirst()).bytes(),DriverJson.MAX_NATIVE_BYTES);
                assertEquals(effect.after().frame().snapshotId(),retained.get("snapshot_id").textValue());
                assertEquals(effect.after().frame().identity().nativeRevision(),retained.get("native_revision").bigIntegerValue());
                assertTrue(retained.get("paused").booleanValue());
            }));
            var initial=dirtyReady(fixture,Instant.now().plusSeconds(60));var semantic=initial.semanticEvidence().orElseThrow();
            var packet=(NativeWire.Snapshot)NativeWire.decode(java.nio.file.Files.readAllBytes(Path.of(semantic.originalNativePacket().path())));
            var post=StrictJson.object();post.put("type","state_snapshot");post.put("protocol_version",1);
            post.put("snapshot_id","dirty-business-snapshot-2");post.put("revision",packet.revision().add(BigInteger.ONE));
            post.set("state",org.xar.ck3.control.contracts.FullJsonTree.parse(packet.state().value(),DriverJson.MAX_NATIVE_BYTES));
            afterPacket.set(NativeWire.packet(org.xar.ck3.control.contracts.FullJsonTree.encode(post,DriverJson.MAX_NATIVE_BYTES)));
            var owner=fixture.observationIdentity();var source=fixture.observationSource().sourceRef();
            var verifier=new org.xar.ck3.control.application.readiness.NativeSemanticEvidenceVerifier((same,ref,max)->fixture.archive.readArtifact(same,ref,max));
            var cycles=new OrdinaryCycleTransitions(fixture.archive,verifier,(same,session,pair,proof)->{throw new AssertionError("dirty restart never saves");},
                    new OriginalWindowReducer.Policy(10958),fixture.writer::requireSession);cycles.bindTerminalFrameLoader(fixture.frameLoader());
            for(String kind:cycles.kinds())fixture.bindAdditionalTransitionAuthority(kind,cycles);
            var batches=new ContinuityBatchJournal(fixture.writer,cycles);
            var history=dirtyHistory(fixture,source);
            fixture.bindAdditionalTransitionAuthority(org.xar.ck3.control.continuity.writer.WriterContracts.DRIVER_ACTION_HISTORY_KIND,history);
            var controller=dirtyController(fixture,batches,owner,source,operation,history);
            var stop=new java.util.concurrent.atomic.AtomicBoolean();
            var reports=new java.util.concurrent.atomic.AtomicReference<BatchReport>();
            var next=new java.util.concurrent.atomic.AtomicLong(-1);
            var callbacks=new java.util.concurrent.atomic.AtomicInteger();
            var control=new RootOrdinaryWorkerLoop.Control(){
                public boolean stopRequested(){return stop.get();}
                public void onBatchCompleted(BatchReport report,long sequence){
                    assertEquals(1,report.turns().size(),()->report.terminal()+": "+report.detail());
                    var receipt=report.turns().getFirst().receipt();
                    assertEquals(ActionReceipt.Outcome.APPLIED_CONFIRMED,receipt.outcome());
                    assertTrue(receipt.settled());assertTrue(receipt.visibleGameplay());
                    assertTrue(report.dirtySinceSave());assertTrue(report.lastSavedPair().isEmpty());
                    assertFalse(controller.isQuarantined());assertEquals(1,fixture.nativeActionWrites());
                    reports.set(report);next.set(sequence);callbacks.incrementAndGet();stop.set(true);
                }
            };
            var limits=new RootOrdinaryWorkerLoop.Configuration("dirty-worker",1,Duration.ofSeconds(120),Duration.ofSeconds(25),Duration.ofMillis(10),16);
            var result=new RootOrdinaryWorkerLoop(limits,control).run(()->new RootOrdinaryWorkerLoop.BatchCurrent(controller,controller::runBatch),0);
            assertEquals(1,callbacks.get());assertEquals(1,next.get());assertEquals(1,result.nextBatchSequence());
            assertSame(reports.get(),result.lastReport().orElseThrow());
            assertEquals(BatchReport.Terminal.CHECKPOINT_DEFERRED,reports.get().terminal());
            var cycleState = fixture.writer.locked(same -> {
                assertEquals(0, same.head().state().settledCycles(), "no SAVE may create saved cycle credit");
                return same.head().state().toJson().get(OrdinaryCycleTransitions.STATE_FIELD);
            });
            assertTrue(cycleState.isObject());
            var completedCycles = cycleState.get("completed_cycles");
            assertTrue(completedCycles.isIntegralNumber());
            assertEquals(BigInteger.ONE, completedCycles.bigIntegerValue());
            assertTrue(cycleState.get("pending_receipt").isNull());
            assertEquals(RootOrdinaryWorkerLoop.StopReason.OPERATOR_STOP,result.stopReason(),()->result.failureDetail().orElse("no diagnostic"));

            controller.drainForCleanRestart(Instant.now().plusSeconds(30));
            var ticket = fixture.writer.locked(same -> controller.captureCleanRestart(same, "dirty-worker", 1));
            var admitted = fixture.writer.locked(same -> batches.admitCleanRestart(same, ticket));
            var captured = admitted.controller();

            assertTrue(captured.dirty());
            assertEquals(Set.of(reports.get().turns().getFirst().receipt().command().actionId()), captured.unsavedGameplayActions());
            assertEquals(Set.of("dirty-worker-0"), captured.usedBatches());
            assertEquals(1, captured.nextBatchSequence());
            assertTrue(captured.savedPair().isEmpty());
            assertFalse(captured.stopRequested());

            var replacement = dirtyController(fixture, batches, owner, source, operation, history);
            fixture.writer.locked(same -> { replacement.restoreCleanRestart(same, admitted); return null; });

            assertThrows(IllegalArgumentException.class, () -> {
                fixture.writer.locked(same -> { replacement.restoreCleanRestart(same, admitted); return null; });
            });

            assertEquals(1, fixture.nativeActionWrites());
        }
    }
    private Ready dirtyReady(ActionWriterIntegrationFixture fixture,Instant deadline)throws IOException,InterruptedException {
        var held=fixture.writer.activeSession();
        return assertInstanceOf(Ready.class,held.isPresent()
                ?fixture.collector.observe(held.orElseThrow(),fixture.observationIdentity(),deadline)
                :fixture.collector.observe(fixture.observationIdentity(),deadline));
    }
    private DriverActionHistoryPublisher dirtyHistory(ActionWriterIntegrationFixture fixture,ExactRef source) {
        var materials=new DriverActionHistoryPublisher.MaterialSource(){
            public void requireOwner(DriverStateAssembler authority,ActionJournal journal,ActionPorts.OutcomeArchive archive){
                assertSame(fixture.driverAuthority(),authority);assertSame(fixture.journal,journal);assertSame(fixture.archive,archive);
            }
            public List<ExactRef> sources(){return List.of(source);}
            private DriverActionHistoryCodec.CanonicalOnly material(ActionReceipt actual){
                var attempt=ActionTransitions.attempt(actual.state()).orElseThrow();
                return new DriverActionHistoryCodec.CanonicalOnly(DriverActionHistoryCodec.CanonicalReason.DIRECT_API_WITHOUT_LEGACY_RECORDER,List.of(
                        new DriverActionHistoryCodec.Evidence(DriverActionHistoryCodec.EvidenceKind.NATIVE_FRAME,attempt.guard().nativeEvidence()),
                        new DriverActionHistoryCodec.Evidence(DriverActionHistoryCodec.EvidenceKind.NATIVE_FRAME,actual.applied().orElseThrow().observation().originalEvidence()),
                        new DriverActionHistoryCodec.Evidence(DriverActionHistoryCodec.EvidenceKind.MATERIAL,fixture.archive.referenceOf(ActionTransitions.dispatch(actual.state()).orElseThrow()))),sources());
            }
            public DriverActionHistoryCodec.OriginalMaterial capture(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session same,ActionReceipt actual,ActionPorts.OutcomeArchive originals)throws IOException{
                var captured=material(actual);requireOriginal(same,actual,captured,originals);return captured;
            }
            public void requireOriginal(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session same,ActionReceipt actual,DriverActionHistoryCodec.OriginalMaterial captured,ActionPorts.OutcomeArchive originals)throws IOException{
                fixture.writer.requireSession(same);assertEquals(material(actual),captured);assertTrue(actual.settled());assertTrue(actual.visibleGameplay());
                assertEquals(actual,originals.loadReceipt(originals.receiptReferenceOf(actual)));
                ActionEffects.validate(actual.command(),ActionTransitions.attempt(actual.state()).orElseThrow(),ActionTransitions.dispatch(actual.state()).orElseThrow(),actual.applied().orElseThrow());
            }
        };
        return new DriverActionHistoryPublisher(fixture.driverAuthority(),fixture.journal,fixture.archive,materials,List.of(source));
    }
    private SessionController dirtyController(ActionWriterIntegrationFixture fixture,ContinuityBatchJournal batches,SessionIdentity owner,ExactRef source,OperationKey operation,DriverActionHistoryPublisher history) {
        CheckpointFiles files=new CheckpointFiles(){
            public Optional<CheckpointPair.FileWitness> observe(Path path){throw new AssertionError("dirty restart must not SAVE");}
            public byte[] read(CheckpointPair.FileWitness witness,int max){throw new AssertionError("dirty restart must not SAVE");}
            public CheckpointPair.FileWitness replace(Path path,byte[] bytes){throw new AssertionError("dirty restart must not SAVE");}
            public CheckpointPair.FileWitness createNew(Path path,byte[] bytes){throw new AssertionError("dirty restart must not SAVE");}
            public CheckpointPair.FileWitness copyNew(CheckpointPair.FileWitness witness,Path path){throw new AssertionError("dirty restart must not SAVE");}
        };
        var snapshots=new DriverCheckpointStore.SnapshotSupplier(){public <T>T withFrozen(DriverCheckpointStore.SnapshotWork<T> work){throw new AssertionError("no SAVE");}};
        var drivers=new DriverCheckpointStore(files,temporary.resolve("dirty-unused-driver.json"),"dirty-unused-pipe",snapshots);
        CheckpointRequest.ObservationPort observations=until->{throw new AssertionError("dirty restart must not SAVE");};
        var checkpoints=new CheckpointService(files,drivers,observations,temporary.resolve("dirty-unused-evidence"),Clock.systemUTC(),(pair,receipt)->{throw new AssertionError("no SAVE");});
        var realm=new RealmLifecycle(source);
        var policies=java.util.Arrays.stream(PlanningStage.values()).<OrdinaryPolicy>map(stage->{
            if(stage==PlanningStage.REALM_MEMBERSHIP_PUBLICATION)return realm;
            return new OrdinaryPolicy(){public PlanningStage stage(){return stage;}public ExactRef implementationSource(){return source;}
                public Decision evaluate(PlanningRequest input,Draft previous){
                    if(stage!=PlanningStage.ORDINARY_CORE)return new Keep("unrelated original stage");
                    var command=new ActionCommand("actual-dirty-unsaved-action",input.before(),input.source(),input.sessionId(),operation,
                            new org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj(java.util.Map.of()),
                            new org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedPostcondition(1,input.before(),input.source(),"paused/v1",List.of(
                                    new org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedBoolean(new org.xar.ck3.control.g2.planning.ProposalLifecycle.FieldKey("paused"),true))),
                            new org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Claims(Set.of(),Set.of(),Set.of(),Set.of()),input.deadline());
                    return new Replace(new Draft("actual-dirty-test","ordinary","real software effect",Kind.ORDINARY,Optional.of(command),Purpose.WORLD_ACTION,
                            Optional.empty(),new org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj(java.util.Map.of())),"real action");
                }};
        }).toList();
        var completion=new OrdinaryPlanCompletion.PlanningScope(){
            public <T>ScopeResult<T> inPlanningScope(ScopeWork<T> work)throws IOException,InterruptedException{return new ScopeResult<>(work.run(),Optional.empty());}
            public PlanningDisposition afterPlanning(PlanningRequest input,PlanningResult planned){return new OrdinaryPlanCompletion.Unchanged("no extra domain publication");}
            public ExecutionDisposition afterExecution(ActionReceipt receipt){
                try{fixture.writer.locked(same->{history.completed(same,receipt);return null;});}
                catch(IOException failure){throw new java.io.UncheckedIOException(failure);}
                return new OrdinaryPlanCompletion.Unchanged("original actual receipt history published");
            }
        };
        var controller=new SessionController(owner,(same,until)->new GameLifecycle.Running(owner.game(),source),(same,until)->{
                    var ready=dirtyReady(fixture,until);
                    return new Ready(ready.request(),CheckpointEligibility.UNAVAILABLE,ready.offlineAnalysis(),ready.semanticEvidence());
                },
                new OrdinaryPlanner(policies,Clock.systemUTC(),realm),fixture.coordinator,checkpoints,new CheckpointRequestFactory(temporary.resolve("dirty-unused.ck3"),observations),
                batches,work->{throw new AssertionError("no incident");},new SessionClock.SystemClock(),Optional.empty(),0,completion,
                (same,receipt,until)->{throw new AssertionError("no episode handoff");});
        controller.bindRetainedIncidents(List::of);controller.bindRestartDriver(fixture.driverAuthority());return controller;
    }


}
