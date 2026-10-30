package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.checkpoint.*;
import org.xar.ck3.control.application.driver.*;
import org.xar.ck3.control.application.capabilities.*;
import org.xar.ck3.control.application.planning.military.MilitaryReadObservation;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.application.planning.campaign.M7CampaignPolicies.RealmLifecycle;
import org.xar.ck3.control.application.session.*;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.OriginalWindowReducer;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.contracts.source.IdentityBearingFileAttributes;
import static org.xar.ck3.control.application.session.SessionPorts.*;

/** Existing software Driver -> actual archive/sole writer -> strict restart readers. No Managed/native admission is manufactured. */
final class CleanRestartCanonicalWriterTest {
    @TempDir Path root;
    private record Inputs(ActionCommand observed, ContinuityBatchJournal batches, SessionController controller) { }
    private ActionWriterIntegrationFixture fixture(Path directory)throws IOException {
        var initialFrame=new ActionWriterIntegrationFixture.SoftwareActionScenario(new OperationKey("pause-map"),"game.command.pause-map",
                (command,attempt,dispatch)->new ActionPorts.Pending("original software ACK remains unresolved",List.of(attempt.guard().nativeEvidence())),
                ()->{},Optional.empty(),Optional.empty(),true,Optional.empty());
        var reads=new ActionWriterIntegrationFixture.SoftwareReadScenario("0".repeat(64),"restart-read",ignored->List.of(),
                request->{throw new AssertionError("restart uses only the fixture's original query contract");});
        return new ActionWriterIntegrationFixture(directory,false,reads,List.of(initialFrame),Duration.ofSeconds(60));
    }
    private Inputs inputs(ActionWriterIntegrationFixture fixture)throws Exception {
        return inputs(fixture,"restart-before");
    }
    private Inputs inputs(ActionWriterIntegrationFixture fixture,String actionId)throws Exception {
        var ready=dirtyReady(fixture,Instant.now().plusSeconds(60));
        var request=ready.request();
        var source=request.source();
        var expected=new org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedPostcondition(1,request.before(),source,"paused/v1",List.of(new org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedBoolean(new org.xar.ck3.control.g2.planning.ProposalLifecycle.FieldKey("paused"),true)));
        var observed=new ActionCommand(actionId,request.before(),source,request.sessionId(),new OperationKey("pause-map"),new org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj(java.util.Map.of()),expected,
                new org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Claims(Set.of(),Set.of(),Set.of(),Set.of()),Instant.now().plus(Duration.ofMinutes(2)));
        var owner=new SessionIdentity(observed.origin().machineId(),observed.origin().game(),observed.sessionId());
        var cycles=new OrdinaryCycleTransitions(fixture.archive,(same,session,semantic)->{throw new AssertionError("restart metadata grants no semantic qualification");},
                (same,session,pair,proof)->{throw new AssertionError("restart does not SAVE");},new OriginalWindowReducer.Policy(10958),fixture.writer::requireSession);
        for(String kind:cycles.kinds())fixture.bindAdditionalTransitionAuthority(kind,cycles);
        var batches=new ContinuityBatchJournal(fixture.writer,cycles);
        return new Inputs(observed,batches,controller(fixture,batches,owner,observed.source().sourceRef()));
    }
    private SessionController controller(ActionWriterIntegrationFixture fixture,ContinuityBatchJournal batches,SessionIdentity owner,ExactRef source) {
        CheckpointFiles files=new CheckpointFiles() {
            public Optional<CheckpointPair.FileWitness> observe(Path path){throw new AssertionError("restart cannot inspect SAVE");}
            public byte[] read(CheckpointPair.FileWitness witness,int maximum){throw new AssertionError("restart cannot read SAVE");}
            public CheckpointPair.FileWitness replace(Path path,byte[] bytes){throw new AssertionError("restart cannot write SAVE");}
            public CheckpointPair.FileWitness createNew(Path path,byte[] bytes){throw new AssertionError("restart cannot create SAVE");}
            public CheckpointPair.FileWitness copyNew(CheckpointPair.FileWitness witness,Path path){throw new AssertionError("restart cannot copy SAVE");}
        };
        var snapshot=new DriverCheckpointStore.SnapshotSupplier(){
            public <T>T withFrozen(DriverCheckpointStore.SnapshotWork<T> work){throw new AssertionError("restart cannot invoke checkpoint supplier");}
        };
        var drivers=new DriverCheckpointStore(files,root.resolve("unused-driver.json"),"unused-checkpoint-pipe",snapshot);
        CheckpointRequest.ObservationPort readiness=deadline->{throw new AssertionError("restart cannot prepare SAVE");};
        var checkpoints=new CheckpointService(files,drivers,readiness,root.resolve("unused-checkpoint-evidence"),Clock.systemUTC(),
                (pair,receipt)->{throw new AssertionError("restart cannot adopt a SAVE");});
        var completion=new OrdinaryPlanCompletion.PlanningScope(){
            public <T>ScopeResult<T> inPlanningScope(ScopeWork<T> work)throws IOException,InterruptedException{return new ScopeResult<>(work.run(),Optional.empty());}
            public PlanningDisposition afterPlanning(PlanningRequest original,PlanningResult planned){throw new AssertionError("capture does not plan");}
            public ExecutionDisposition afterExecution(ActionReceipt receipt){throw new AssertionError("capture does not execute");}
        };
        var realm=new RealmLifecycle(source);
        var controller=new SessionController(owner,(actual,deadline)->new GameLifecycle.Running(owner.game(),source),
                (actual,deadline)->{throw new AssertionError("capture does not observe");},new OrdinaryPlanner(List.of(),Clock.systemUTC(),realm),
                fixture.coordinator,checkpoints,new CheckpointRequestFactory(root.resolve("unused.ck3"),readiness),batches,
                work->{throw new AssertionError("no incident was enqueued");},new SessionClock.SystemClock(),Optional.empty(),0,completion,
                (actual,parent,deadline)->{throw new AssertionError("capture cannot continue an episode");});
        controller.bindRetainedIncidents(List::of);controller.bindRestartDriver(fixture.physicalInputs().driverAssembler());return controller;
    }
    @Test void actualCanonicalCaptureRoundTripsWholeDriverAndControllerWithoutSaveOrCredit()throws Exception {
        try(var fixture=fixture(root.resolve("canonical"))){
            var input=inputs(fixture);
            var before=fixture.writer.locked(same->same.head().state());
            input.controller().drainForCleanRestart(Instant.now().plusSeconds(30));
            var ticket=fixture.writer.locked(same->input.controller().captureCleanRestart(same,"worker",7));
            assertEquals(ticket,ContinuityBatchJournal.CleanRestartTicket.decode(ticket.encode()));
            var admitted=fixture.writer.locked(same->input.batches().admitCleanRestart(same,ticket));
            assertEquals("worker",admitted.controller().batchPrefix());assertEquals(7,admitted.controller().nextBatchSequence());
            assertTrue(admitted.controller().savedPair().isEmpty());assertFalse(admitted.controller().dirty());
            assertEquals(input.observed().source(),admitted.manifest().source());
            fixture.writer.locked(same->{
                var actual=fixture.physicalInputs().driverAssembler().withFrozenFacts(same,frozen->(DriverSnapshotFacts.Known)frozen.state());
                assertArrayEquals(actual.driver().encode(),admitted.facts().driver().encode());assertEquals(actual.stamp(),admitted.facts().stamp());
                assertEquals(actual.actionRows(),admitted.facts().actionRows());assertEquals(actual.auxiliary(),admitted.facts().auxiliary());
                assertEquals(actual.loop(),admitted.facts().loop());admitted.requireCurrent(same);
                assertEquals(before.settledCycles(),same.head().state().settledCycles());assertEquals(before.settledDateRaw(),same.head().state().settledDateRaw());return null;
            });
            // This tests restoration DATA. Root additionally requires the actual new-HELLO DriverBootstrap binding.
            var replacement=controller(fixture,input.batches(),admitted.controller().owner(),input.observed().source().sourceRef());
            fixture.writer.locked(same->{replacement.restoreCleanRestart(same,admitted);return null;});
            assertFalse(replacement.isQuarantined());assertEquals(0,fixture.nativeActionWrites());
            var dirty=new ControllerRestartState(admitted.controller().owner(),"worker",8,Set.of("worker:7"),Set.of("unsaved-action"),
                    Optional.empty(),Optional.of(ticket.persistedHead()),3,true,false,false,0,Set.of("analyzed-batch"),false);
            assertEquals(dirty,ControllerRestartState.decode(dirty.encode()));
            assertTrue(ControllerRestartState.decode(dirty.encode()).dirty());assertTrue(ControllerRestartState.decode(dirty.encode()).savedPair().isEmpty());
            var independent=reopenInIndependentJvm(fixture.root);
            assertEquals(admitted.controller(),ControllerRestartState.decode(independent.get("controller").toString().getBytes(java.nio.charset.StandardCharsets.UTF_8)));
            assertEquals(ticket.sequence()+1,StrictJson.integer(independent.get("sequence"),1,StrictJson.MAX_SAFE_INTEGER));
            assertEquals(ticket.sequence()+1,fixture.sequence());assertEquals(0,fixture.nativeActionWrites());
        }
    }

    @Test void actualVisibleUnsavedActionSurvivesCanonicalCaptureAndControllerRestoreWithoutSave()throws Exception {
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
        var readScenario=new ActionWriterIntegrationFixture.SoftwareReadScenario("0".repeat(64),"actual-dirty-read",ignored->List.of(),
                request->{throw new AssertionError("dirty suffix uses only the fixture's original query contract");});
        try(var fixture=new ActionWriterIntegrationFixture(root.resolve("actual-dirty"),false,readScenario,List.of(scenario),Duration.ofSeconds(60))) {
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
            var report=controller.autoTurn(Instant.now().plusSeconds(600)).execution();
            assertEquals(BatchReport.Terminal.TURN_BOUND,report.terminal(),()->report.detail()+"; actual receipts="+report.turns().stream().map(turn->turn.receipt().state() instanceof ActionState.Unknown unknown?unknown.reason():turn.receipt().state().getClass().getSimpleName()).toList());assertEquals(1,report.turns().size());
            var receipt=report.turns().getFirst().receipt();assertTrue(receipt.settled());assertTrue(receipt.visibleGameplay());assertFalse(receipt.eligibleAdvance());
            assertTrue(report.dirtySinceSave());assertEquals(0,report.committedSavedDays());assertTrue(report.lastSavedPair().isEmpty());
            controller.drainForCleanRestart(Instant.now().plusSeconds(30));
            var ticket=fixture.writer.locked(same->controller.captureCleanRestart(same,"dirty-worker",1));
            var admitted=fixture.writer.locked(same->batches.admitCleanRestart(same,ticket));var captured=admitted.controller();
            assertTrue(captured.dirty());assertEquals(Set.of(receipt.command().actionId()),captured.unsavedGameplayActions());
            assertEquals(0,captured.eligibleSinceSave());assertEquals(0,captured.totalCommittedDays());assertTrue(captured.savedPair().isEmpty());
            assertEquals(1,admitted.facts().actionRows().size());assertEquals(receipt.command().actionId(),admitted.facts().actionRows().getFirst().actionId());
            assertInstanceOf(DriverSnapshotFacts.CanonicalOnly.class,admitted.facts().actionRows().getFirst().coverageSource());
            var replacement=dirtyController(fixture,batches,owner,source,operation,history);
            fixture.writer.locked(same->{replacement.restoreCleanRestart(same,admitted);return null;});
            var second=fixture.writer.locked(same->replacement.captureCleanRestart(same,"dirty-worker",1));
            var restored=fixture.writer.locked(same->batches.admitCleanRestart(same,second));
            assertEquals(captured.dirty(),restored.controller().dirty());assertEquals(captured.unsavedGameplayActions(),restored.controller().unsavedGameplayActions());
            assertEquals(captured.usedBatches(),restored.controller().usedBatches());assertEquals(captured.eligibleSinceSave(),restored.controller().eligibleSinceSave());
            assertEquals(captured.savedPair(),restored.controller().savedPair());assertEquals(captured.completedAnalysisIds(),restored.controller().completedAnalysisIds());
            assertArrayEquals(admitted.facts().driver().encode(),restored.facts().driver().encode());
            assertEquals(admitted.facts().actionRows(),restored.facts().actionRows());
            assertEquals(receipt,fixture.coordinator.execute(receipt.command()));assertEquals(1,fixture.nativeActionWrites());
            batches.commit(new JournalInput(owner,"dirty-worker-1",JournalKind.BATCH_STARTED,Optional.empty(),Optional.empty(),Optional.empty(),List.of()));
            batches.commit(new JournalInput(owner,"dirty-worker-1",JournalKind.BATCH_INTERRUPTED,Optional.empty(),Optional.empty(),Optional.empty(),List.of()));
            var suffix=fixture.writer.locked(same->batches.admitInitialNoDispatchRecovery(same,owner));
            assertTrue(suffix.capturedController().orElseThrow().dirty());
            assertEquals(captured.unsavedGameplayActions(),suffix.capturedController().orElseThrow().unsavedGameplayActions());
            assertEquals(2,suffix.nextBatchSequence());
            var current=dirtyReady(fixture,Instant.now().plusSeconds(60)).semanticEvidence().orElseThrow();
            fixture.writer.locked(same->{batches.finishInitialNoDispatchRecovery(same,suffix,current);return null;});
            var settledHead=fixture.writer.locked(same->same.head().digest());
            var retained=fixture.writer.locked(same->batches.admitInitialNoDispatchRecovery(same,owner));
            fixture.writer.locked(same->{batches.finishInitialNoDispatchRecovery(same,retained,current);return null;});
            assertEquals(settledHead,fixture.writer.locked(same->same.head().digest()),"committed recovery is returned without another mutation");
            batches.commit(new JournalInput(owner,"dirty-worker-2",JournalKind.BATCH_STARTED,Optional.empty(),Optional.empty(),Optional.empty(),List.of()));
            batches.commit(new JournalInput(owner,"dirty-worker-2",JournalKind.BATCH_INTERRUPTED,Optional.empty(),Optional.empty(),Optional.empty(),List.of()));
            var repeated=fixture.writer.locked(same->batches.admitInitialNoDispatchRecovery(same,owner));
            assertEquals(3,repeated.nextBatchSequence());
            fixture.writer.locked(same->{batches.finishInitialNoDispatchRecovery(same,repeated,current);return null;});
            for(int next=3;next<=5;next++) {
                String deferred="dirty-worker-"+next;
                batches.commit(new JournalInput(owner,deferred,JournalKind.BATCH_STARTED,Optional.empty(),Optional.empty(),Optional.empty(),List.of()));
                batches.commit(new JournalInput(owner,deferred,JournalKind.BATCH_DEFERRED,Optional.empty(),Optional.empty(),Optional.empty(),List.of()));
            }
            var closed=fixture.writer.locked(same->batches.admitInitialNoDispatchRecovery(same,owner));
            assertEquals(6,closed.nextBatchSequence());
            var closedHead=fixture.writer.locked(same->same.head().digest());
            fixture.writer.locked(same->{batches.finishInitialNoDispatchRecovery(same,closed,current);return null;});
            assertEquals(closedHead,fixture.writer.locked(same->same.head().digest()),"DEFERRED has already closed the batch and needs no recovery write");
            batches.commit(new JournalInput(owner,"dirty-worker-6",JournalKind.BATCH_STARTED,Optional.empty(),Optional.empty(),Optional.empty(),List.of()));
            batches.commit(new JournalInput(owner,"dirty-worker-6",JournalKind.BATCH_INTERRUPTED,Optional.empty(),Optional.empty(),Optional.empty(),List.of()));
            var interruptedAfterDeferred=fixture.writer.locked(same->batches.admitInitialNoDispatchRecovery(same,owner));
            assertEquals(7,interruptedAfterDeferred.nextBatchSequence());
            fixture.writer.locked(same->{batches.finishInitialNoDispatchRecovery(same,interruptedAfterDeferred,current);return null;});
            var finalRetained=fixture.writer.locked(same->batches.admitInitialNoDispatchRecovery(same,owner));
            fixture.writer.locked(same->{batches.finishInitialNoDispatchRecovery(same,finalRetained,current);return null;});
            var afterRecovery=dirtyController(fixture,batches,owner,source,operation,history);
            fixture.writer.locked(same->{afterRecovery.restoreInitialNoDispatchRecovery(same,finalRetained);return null;});
            var recoveredTicket=fixture.writer.locked(same->afterRecovery.captureCleanRestart(same,"dirty-worker",7));
            var recovered=fixture.writer.locked(same->batches.admitCleanRestart(same,recoveredTicket));
            assertTrue(recovered.controller().dirty());assertEquals(captured.unsavedGameplayActions(),recovered.controller().unsavedGameplayActions());
            assertTrue(recovered.controller().usedBatches().containsAll(captured.usedBatches()));assertTrue(recovered.controller().usedBatches().contains("dirty-worker-1"));
            for(int next=2;next<=6;next++)assertTrue(recovered.controller().usedBatches().contains("dirty-worker-"+next));
            assertEquals(7,recovered.controller().nextBatchSequence());
            assertEquals(captured.savedPair(),recovered.controller().savedPair());assertEquals(captured.totalCommittedDays(),recovered.controller().totalCommittedDays());
            assertEquals(1,fixture.nativeActionWrites());
        }
    }
    private com.fasterxml.jackson.databind.JsonNode reopenInIndependentJvm(Path fixtureRoot)throws Exception {
        Path arguments=root.resolve("restart-child.args"),output=root.resolve("restart-child.json"),log=root.resolve("restart-child.log");
        String classpath=System.getProperty("surefire.test.class.path",System.getProperty("java.class.path")).replace('\\','/');
        String options="-Xms16m\n-Xmx256m\n\"-Djna.tmpdir="+root.toAbsolutePath().normalize().toString().replace('\\','/')+"\"\n\"-Djava.io.tmpdir="+root.toAbsolutePath().normalize().toString().replace('\\','/')+"\"\n-cp\n\""+classpath+"\"\n"
                +RestartChild.class.getName()+"\n\""+fixtureRoot.toString().replace('\\','/')+"\"\n\""+output.toString().replace('\\','/')+"\"\n";
        Files.writeString(arguments,options);
        var process=new ProcessBuilder(Path.of(System.getProperty("java.home"),"bin","java.exe").toString(),"@"+arguments)
                .redirectErrorStream(true).redirectOutput(log.toFile()).start();
        try {
            assertTrue(process.waitFor(180,java.util.concurrent.TimeUnit.SECONDS),"independent restart consumer timed out: "+log);
            assertEquals(0,process.exitValue(),()->{try{return Files.readString(log);}catch(IOException failure){return failure.toString();}});
            return StrictJson.parse(Files.readAllBytes(output));
        }finally {
            try {
                if(process.isAlive()){process.destroyForcibly();assertTrue(process.waitFor(10,java.util.concurrent.TimeUnit.SECONDS),"child cleanup incomplete");}
            }finally {
                String scratch=System.getProperty("xar.scratch");
                if(scratch!=null&&!scratch.isBlank()) {
                    Path retained=Path.of(scratch).toAbsolutePath().normalize().resolve("java-clean-restart").resolve(java.util.UUID.randomUUID().toString());
                    Files.createDirectories(retained);
                    for(Path original:List.of(arguments,output,log))if(Files.isRegularFile(original))
                        Files.copy(original,retained.resolve(original.getFileName()));
                    System.out.println("Independent restart evidence retained at "+retained);
                }
            }
        }
    }
    /** Real independent software writer/archive admission and reducer; no Managed/native capability is manufactured. */
    public static final class RestartChild {
        private RestartChild() { }
        private static ExactRef reference(Path path)throws IOException {
            byte[] raw=Files.readAllBytes(path);
            return new ExactRef(path.toAbsolutePath().normalize().toString(),raw.length,
                    ActionCodec.sha256(raw));
        }
        public static void main(String[] arguments)throws Exception {
            if(arguments.length!=2)throw new IllegalArgumentException("fixture root and output required");
            Path fixtureRoot=Path.of(arguments[0]);
            var document=ContinuityJson.parseObject(Files.readAllBytes(fixtureRoot.resolve("ROOT-CONTINUITY-WINDOW.json")),ContinuityJson.LEDGER_MAX_BYTES);
            String machine=StrictJson.text(document.get("machine_id"));
            var layout=new org.xar.ck3.control.continuity.writer.WriterContracts.Layout(fixtureRoot.resolve("ROOT-CONTINUITY-WINDOW.json"),reference(fixtureRoot.resolve("anchor.json")),machine);
            try(var storage=org.xar.ck3.control.continuity.writer.StorageWriteGuardTestSupport.create(layout)) {
                var store=new org.xar.ck3.control.continuity.writer.ImmutableArtifactStore(new org.xar.ck3.control.continuity.writer.ImmutableArtifactStore.Config(fixtureRoot.resolve("artifacts"),layout.lock(),16*1024*1024),storage);
                var current=new java.util.concurrent.atomic.AtomicReference<OrdinaryCycleTransitions>();
                var authority=new org.xar.ck3.control.continuity.writer.WriterContracts.TransitionAuthority() {
                    public String revalidate(org.xar.ck3.control.continuity.ContinuityState state,org.xar.ck3.control.continuity.writer.WriterContracts.Request request){throw new AssertionError("detached head forbidden");}
                    public String revalidate(org.xar.ck3.control.continuity.writer.WriterContracts.Head head,org.xar.ck3.control.continuity.writer.WriterContracts.Request request)throws IOException {
                        assertEquals(OrdinaryCycleTransitions.BATCH_KIND,request.kind());return current.get().revalidate(head,request);
                    }
                    public org.xar.ck3.control.continuity.ContinuityState reduce(org.xar.ck3.control.continuity.ContinuityState state,org.xar.ck3.control.continuity.writer.WriterContracts.Request request)throws IOException {
                        assertEquals(OrdinaryCycleTransitions.BATCH_KIND,request.kind());return current.get().reduce(state,request);
                    }
                };
                var writer=new org.xar.ck3.control.continuity.writer.ContinuityWriter(layout,List.of(reference(fixtureRoot.resolve("reviewed-fixture-source.txt"))),authority,Clock.systemUTC(),
                        new org.xar.ck3.control.continuity.writer.ContinuityWriter.Extensions(List.of(),Optional.of(store),Optional.empty()),storage);
                var archive=new org.xar.ck3.control.continuity.writer.NativeOutcomeArchive(store,writer);
                var verifier=new org.xar.ck3.control.application.readiness.NativeSemanticEvidenceVerifier((same,ref,maximum)->archive.readArtifact(same,ref,maximum));
                var cycles=new OrdinaryCycleTransitions(archive,verifier,(same,session,pair,proof)->{throw new AssertionError("restart cannot SAVE");},new OriginalWindowReducer.Policy(10958),writer::requireSession);
                current.set(cycles);var batches=new ContinuityBatchJournal(writer,cycles);
                var admitted=writer.locked(same->batches.admitCleanRestart(same,ContinuityBatchJournal.CleanRestartTicket.fromCapturedHead(same.head(),same.persistedHead()).orElseThrow()));
                var result=StrictJson.object();result.set("controller",StrictJson.parse(admitted.controller().encode()));
                batches.commit(new JournalInput(admitted.controller().owner(),admitted.controller().batchPrefix()+"-"+admitted.controller().nextBatchSequence(),JournalKind.BATCH_STARTED,
                        Optional.empty(),Optional.empty(),Optional.empty(),List.of()));
                writer.locked(same->{assertThrows(IllegalArgumentException.class,()->batches.admitCleanRestart(same,admitted.ticket()));result.put("sequence",same.head().state().sequence());return null;});
                Files.write(Path.of(arguments[1]),StrictJson.canonical(result));
            }
        }
    }
    private Ready dirtyReady(ActionWriterIntegrationFixture fixture,Instant deadline)throws IOException,InterruptedException {
        var held=fixture.writer.activeSession();
        var observed=held.isPresent()
                ?fixture.collector.observe(held.orElseThrow(),fixture.observationIdentity(),deadline)
                :fixture.collector.observe(fixture.observationIdentity(),deadline);
        return assertInstanceOf(Ready.class,observed,()->"actual dirty-suffix observation: "+observed);
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
        var drivers=new DriverCheckpointStore(files,root.resolve("dirty-unused-driver.json"),"dirty-unused-pipe",snapshots);
        CheckpointRequest.ObservationPort observations=until->{throw new AssertionError("dirty restart must not SAVE");};
        var checkpoints=new CheckpointService(files,drivers,observations,root.resolve("dirty-unused-evidence"),Clock.systemUTC(),(pair,receipt)->{throw new AssertionError("no SAVE");});
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
        var controller=new SessionController(owner,(same,until)->new GameLifecycle.Running(owner.game(),source),(same,until)->dirtyReady(fixture,until),
                new OrdinaryPlanner(policies,Clock.systemUTC(),realm),fixture.coordinator,checkpoints,new CheckpointRequestFactory(root.resolve("dirty-unused.ck3"),observations),
                batches,work->{throw new AssertionError("no incident");},new SessionClock.SystemClock(),Optional.empty(),0,completion,
                (same,receipt,until)->{throw new AssertionError("no episode handoff");});
        controller.bindRetainedIncidents(List::of);controller.bindRestartDriver(fixture.driverAuthority());return controller;
    }

    @Test void admittedCaptureSurvivesActualDomainImportWithoutPromotingANewTicket()throws Exception {
        String schema="xar.sdk-restart-domain-fixture/v1";
        byte[] original=ContinuityJson.canonical(StrictJson.parse("{\"schema\":\"xar.sdk-restart-domain-fixture/v1\",\"generation\":1}".getBytes(java.nio.charset.StandardCharsets.UTF_8)));
        var action=new ActionWriterIntegrationFixture.SoftwareActionScenario(new OperationKey("pause-map"),"game.command.pause-map",
                (command,attempt,dispatch)->new ActionPorts.Pending("original software ACK remains unresolved",List.of(attempt.guard().nativeEvidence())),
                ()->{},Optional.empty(),Optional.empty(),true,Optional.empty());
        var reads=new ActionWriterIntegrationFixture.SoftwareReadScenario("d".repeat(64),"sdk-restart-domain-fixture",source->List.of(),
                request->{throw new AssertionError("domain continuation cannot query Native");});
        try(var fixture=new ActionWriterIntegrationFixture(root.resolve("domain-continuation"),false,reads,List.of(action),List.of(),source->List.of(
                new org.xar.ck3.control.continuity.writer.DomainBodies.Registration(org.xar.ck3.control.continuity.writer.DomainBodies.Slot.FACTION,schema,65536,List.of(source),
                        (head,previous,request,raw)->{assertTrue(previous.isEmpty());assertArrayEquals(original,raw);assertArrayEquals(original,request.producerInput());return ActionCodec.sha256(raw);})) )) {
            var input=inputs(fixture);var ticket=fixture.writer.locked(same->input.controller().captureCleanRestart(same,"domain-worker",0));
            var admitted=fixture.writer.locked(same->input.batches().admitCleanRestart(same,ticket));
            fixture.writer.locked(same->{
                var scoped=fixture.archive.withSession(same);var body=scoped.preserveMaterial(new RawJson(original));
                var imported=new org.xar.ck3.control.continuity.writer.DomainBodies.ImportRequest(org.xar.ck3.control.continuity.writer.DomainBodies.Slot.FACTION,schema,body,original,
                        List.of(input.observed().source().sourceRef()),"sdk-real-domain-continuation");
                var prepared=same.previewImport(imported);var committed=same.commitImport(prepared);same.requireCommitted(prepared,committed);
                assertEquals(ticket.sequence()+1,same.head().state().sequence());
                admitted.requireCurrent(same);
                assertTrue(ContinuityBatchJournal.CleanRestartTicket.fromCapturedHead(same.head(),same.persistedHead()).isEmpty());
                var forged=new ContinuityBatchJournal.CleanRestartTicket(same.persistedHead(),same.head().state().sequence(),same.head().digest(),ticket.manifest());
                assertThrows(IllegalArgumentException.class,()->input.batches().admitCleanRestart(same,forged));return null;
            });
            assertEquals(0,fixture.nativeActionWrites());
        }
    }

    @Test void knownReadWithoutCanonicalPublicationRetainsExactCaptureTicket()throws Exception {
        try(var fixture=fixture(root.resolve("retained-marker"))){
            var input=inputs(fixture);var ticket=fixture.writer.locked(same->input.controller().captureCleanRestart(same,"worker",0));
            var boundary=fixture.writer.locked(same->same.head().state().toJson().get(org.xar.ck3.control.continuity.writer.WriterContracts.ORDINARY_BATCH_BOUNDARY_FIELD));
            var request=new PlanningReadRequest(input.observed().before(),input.observed().source(),input.observed().sessionId(),fixture.readContract.operation(),
                    new org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj(java.util.Map.of()),Instant.now().plusSeconds(60));
            assertInstanceOf(PlanningReadResult.Known.class,fixture.reads.read(fixture.readContract,request));
            fixture.writer.locked(same->{
                assertEquals(boundary,same.head().state().toJson().get(org.xar.ck3.control.continuity.writer.WriterContracts.ORDINARY_BATCH_BOUNDARY_FIELD));
                assertEquals(ticket.sequence(),same.head().state().sequence());
                assertEquals(ticket,ContinuityBatchJournal.CleanRestartTicket.fromCapturedHead(same.head(),same.persistedHead()).orElseThrow());
                assertEquals(ticket,input.batches().admitCleanRestart(same,ticket).ticket());return null;
            });
            assertEquals(0,fixture.nativeActionWrites());
        }
    }
    @Test void capturedReadSuffixRetainsActualPublishedDriverWithoutReplayingReads()throws Exception {
        String step="preview-move-army-0-to-4",capability="game.command.preview-move-army-N-to-N";
        var installed=new java.util.concurrent.atomic.AtomicReference<ReadContract<MilitaryReadObservation>>();
        var scenario=new ActionWriterIntegrationFixture.SoftwareReadScenario("0".repeat(64),"captured-actual-read-history",source->{
            java.util.function.Function<PlanningReadReceipt,MilitaryReadObservation> decode=receipt->{
                Obj raw=DriverJson.object(receipt.original().originalResultToken().orElseThrow().bytes(),DriverJson.MAX_NATIVE_BYTES);
                var frame=receipt.request().before().frame();
                Obj value=raw.with("queried_snapshot_id",new Text(frame.snapshotId())).with("queried_revision",new IntegerValue(frame.revision()))
                        .with("queried_native_revision",new IntegerValue(frame.identity().nativeRevision()))
                        .with("queried_connection_generation",new IntegerValue(receipt.before().binding().connectionGeneration()))
                        .with("queried_episode_run_id",new Text(frame.episodeRunId()));
                return new MilitaryReadObservation(MilitaryReadObservation.Kind.ROUTE_PREVIEW,value);
            };
            var contract=new ReadContract<MilitaryReadObservation>("actual-captured-route-read",new OperationKey(step),Optional.of(capability),capability,
                    ReadContract.PermissionMode.ADVERTISED_CAPABILITY,ReadContract.WireProfile.EXECUTE_STEP,ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,source,
                    (request,id)->new NativeRequest(step,Optional.of(capability),new RawJson(new byte[]{'{','}'})),decode,decode,
                    (original,value,current,semantic)->StrictJson.require(current.before().equals(original.request().before())
                            &&current.source().equals(original.request().source())&&current.sessionId().equals(original.request().sessionId())
                            &&current.arguments().equals(original.request().arguments()),"software original READ operands changed"));
            installed.set(contract);return List.of(contract);
        },request->new RawJson(DriverJson.encode(new Obj(java.util.Map.of("step",new Text(step),"accepted",new Bool(true),"status",new Text("available"),
                "route_preview",new Obj(java.util.Map.of("army_id",new IntegerValue(BigInteger.ZERO),"origin_province_id",new IntegerValue(BigInteger.ONE),
                "target_province_id",new IntegerValue(BigInteger.valueOf(4)),"status",new Text("available"),
                "route_province_ids",new Arr(List.of(new IntegerValue(BigInteger.ONE),new IntegerValue(BigInteger.valueOf(4)))))))))));
        var initialFrame=new ActionWriterIntegrationFixture.SoftwareActionScenario(new OperationKey("pause-map"),"game.command.pause-map",
                (command,attempt,dispatch)->new ActionPorts.Pending("original software ACK remains unresolved",List.of(attempt.guard().nativeEvidence())),
                ()->{},Optional.empty(),Optional.empty(),true,Optional.empty());
        String domainSchema="xar.actual-phase2-domain/v1";
        byte[] domainOriginal=ContinuityJson.canonical(StrictJson.object().put("schema",domainSchema).put("prepared_only",true));
        try(var fixture=new ActionWriterIntegrationFixture(root.resolve("actual-read-suffix"),false,scenario,List.of(initialFrame),List.of(),source->List.of(
                new org.xar.ck3.control.continuity.writer.DomainBodies.Registration(org.xar.ck3.control.continuity.writer.DomainBodies.Slot.FACTION,domainSchema,65536,List.of(source),
                        (head,previous,request,raw)->{assertTrue(previous.isEmpty());assertArrayEquals(domainOriginal,raw);assertArrayEquals(domainOriginal,request.producerInput());return ActionCodec.sha256(raw);})) )) {
            var input=inputs(fixture);var contract=installed.get();
            var publisher=new DriverReadHistoryPublisher(fixture.driverAuthority(),fixture.archive,fixture.reads.catalog(),List.of(contract.sourceRef()));
            fixture.bindAdditionalTransitionAuthority(org.xar.ck3.control.continuity.writer.WriterContracts.DRIVER_READ_HISTORY_KIND,publisher);
            fixture.writer.locked(same->{
                fixture.collector.current(same,input.observed().before(),Instant.now().plusSeconds(60),lease->{
                    var configuration=new DynamicCapabilities.Configuration(Optional.empty(),Optional.empty(),3,3,false,false);
                    var session=new CapabilitySessionPresentation(false,Optional.empty(),Optional.of(CapabilitySessionPresentation.RestoreKind.NEW_EPISODE),
                            CapabilitySessionPresentation.BindingState.ACTIVE_NEW,Optional.empty(),Optional.empty(),Optional.empty(),Optional.empty());
                    var policy=fixture.archive.preserveMaterial(new RawJson(StrictJson.canonical(StrictJson.object().put("actual_capture_read_start_policy",true))));
                    var produced=DriverCapabilityStateProducer.initializeNewEpisode(lease.frame(),lease.driver(),configuration,session,policy,fixture.archive.withSession(same));
                    fixture.driverAuthority().publishCapabilityInputs(same,lease.driver().stamp(),produced.expectedAuxiliarySha256(),produced);return null;
                });return null;
            });
            var ticket=fixture.writer.locked(same->input.controller().captureCleanRestart(same,"read-worker",0));
            var captured=fixture.writer.locked(same->input.batches().admitCleanRestart(same,ticket));
            byte[] captureOriginal=Files.readAllBytes(Path.of(ticket.manifest().path()));
            var owner=captured.controller().owner();
            input.batches().commit(new JournalInput(owner,"read-worker-0",JournalKind.BATCH_STARTED,Optional.empty(),Optional.empty(),Optional.empty(),List.of()));
            fixture.writer.locked(same->{
                for(int count:List.of(2,1)) {
                    fixture.collector.current(same,input.observed().before(),Instant.now().plusSeconds(60),lease->{
                        for(int ordinal=0;ordinal<count;ordinal++) {
                            var request=new PlanningReadRequest(lease.frame().identity(),lease.frame().source(),lease.frame().sessionId(),contract.operation(),new Obj(java.util.Map.of()),Instant.now().plusSeconds(60));
                            var result=fixture.reads.read(same,contract,request);
                            if(!(result instanceof PlanningReadResult.Known<MilitaryReadObservation> known))throw new AssertionError(result);
                            publisher.enqueue(same,contract,known);
                        }
                        return null;
                    });assertTrue(publisher.flushActualReads(same).isPresent());
                }
                return null;
            });
            var domainRef=fixture.writer.locked(same->{
                var body=fixture.archive.withSession(same).preserveMaterial(new RawJson(domainOriginal));
                var imported=new org.xar.ck3.control.continuity.writer.DomainBodies.ImportRequest(org.xar.ck3.control.continuity.writer.DomainBodies.Slot.FACTION,domainSchema,body,domainOriginal,
                        List.of(input.observed().source().sourceRef()),"actual-phase2-pending");
                var prepared=same.previewImport(imported);var committed=same.commitImport(prepared);same.requireCommitted(prepared,committed);return body;
            });
            input.batches().commit(new JournalInput(owner,"read-worker-0",JournalKind.BATCH_INTERRUPTED,Optional.empty(),Optional.empty(),Optional.empty(),List.of()));
            int readWrites=fixture.scenarioReadWrites();
            String beforeRecovery=fixture.writer.locked(same->same.head().digest());
            var recovered=fixture.writer.locked(same->input.batches().admitInitialNoDispatchRecovery(same,owner));
            fixture.writer.locked(same->{
                assertEquals(beforeRecovery,same.head().digest());
                var domain=assertInstanceOf(org.xar.ck3.control.continuity.writer.DomainBodies.Available.class,same.readDomain(org.xar.ck3.control.continuity.writer.DomainBodies.Slot.FACTION));
                assertEquals(domainRef,domain.reference().payload());assertArrayEquals(domainOriginal,domain.canonicalBody());return null;
            });
            var retained=recovered.retainedFacts().orElseThrow();
            var latest=fixture.writer.locked(same->fixture.driverAuthority().withFrozenFacts(same,frozen->(DriverSnapshotFacts.Known)frozen.state()));
            assertArrayEquals(latest.driver().encode(),retained.driver().encode());assertEquals(latest.stamp(),retained.stamp());
            assertEquals(latest.auxiliary(),retained.auxiliary());assertEquals(latest.loop(),retained.loop());assertEquals(latest.actionRows(),retained.actionRows());
            assertEquals(captured.facts().stamp().driverVersion()+2,retained.stamp().driverVersion());
            assertEquals(captured.facts().driver().commandHistory().size()+3,retained.driver().commandHistory().size());
            assertArrayEquals(captured.facts().driver().encode(),recovered.capturedFacts().orElseThrow().driver().encode());
            assertEquals(captured.manifest(),recovered.capturedManifest().orElseThrow());
            assertArrayEquals(captureOriginal,Files.readAllBytes(Path.of(ticket.manifest().path())));
            assertArrayEquals(retained.driver().encode(),fixture.archive.loadFullMaterial(recovered.retainedFullDriver().orElseThrow()).bytes());
            assertEquals(captured.controller(),recovered.capturedController().orElseThrow());
            assertEquals(List.of("read-worker-0"),recovered.consumedBatchIds());assertEquals(1,recovered.nextBatchSequence());
            assertEquals(readWrites,fixture.scenarioReadWrites());assertEquals(0,fixture.nativeActionWrites());
            fixture.writer.locked(same->{
                recovered.requireCurrent(same);
                var publication=same.head().state().toJson().get(org.xar.ck3.control.continuity.writer.WriterContracts.DRIVER_READ_HISTORY_FIELD);
                var row=ExactRef.fromJson(publication.get("read_rows").get(0).get("row"));
                Files.writeString(Path.of(row.path()),"{}");
                assertThrows(IOException.class,()->recovered.requireCurrent(same));return null;
            });
        }
    }
    @Test void restartCaptureRetainsLargeActualKnownAndKeepsOrdinaryTransportBound()throws Exception {
        String step="preview-move-army-0-to-4",capability="game.command.preview-move-army-N-to-N";
        var installed=new java.util.concurrent.atomic.AtomicReference<ReadContract<MilitaryReadObservation>>();
        var scenario=new ActionWriterIntegrationFixture.SoftwareReadScenario("0".repeat(64),"captured-actual-read-history",source->{
            java.util.function.Function<PlanningReadReceipt,MilitaryReadObservation> decode=receipt->{
                Obj raw=DriverJson.object(receipt.original().originalResultToken().orElseThrow().bytes(),DriverJson.MAX_NATIVE_BYTES);
                var frame=receipt.request().before().frame();
                Obj value=raw.with("queried_snapshot_id",new Text(frame.snapshotId())).with("queried_revision",new IntegerValue(frame.revision()))
                        .with("queried_native_revision",new IntegerValue(frame.identity().nativeRevision()))
                        .with("queried_connection_generation",new IntegerValue(receipt.before().binding().connectionGeneration()))
                        .with("queried_episode_run_id",new Text(frame.episodeRunId()));
                return new MilitaryReadObservation(MilitaryReadObservation.Kind.ROUTE_PREVIEW,value);
            };
            var contract=new ReadContract<MilitaryReadObservation>("actual-captured-route-read",new OperationKey(step),Optional.of(capability),capability,
                    ReadContract.PermissionMode.ADVERTISED_CAPABILITY,ReadContract.WireProfile.EXECUTE_STEP,ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,source,
                    (request,id)->new NativeRequest(step,Optional.of(capability),new RawJson(new byte[]{'{','}'})),decode,decode,
                    (original,value,current,semantic)->StrictJson.require(current.before().equals(original.request().before())
                            &&current.source().equals(original.request().source())&&current.sessionId().equals(original.request().sessionId())
                            &&current.arguments().equals(original.request().arguments()),"software original READ operands changed"));
            installed.set(contract);return List.of(contract);
        },request->new RawJson(DriverJson.encode(new Obj(java.util.Map.of("step",new Text(step),"accepted",new Bool(true),"status",new Text("available"),"controlled_known_DATA",new Text("x".repeat(49152)),
                "route_preview",new Obj(java.util.Map.of("army_id",new IntegerValue(BigInteger.ZERO),"origin_province_id",new IntegerValue(BigInteger.ONE),
                "target_province_id",new IntegerValue(BigInteger.valueOf(4)),"status",new Text("available"),
                "route_province_ids",new Arr(List.of(new IntegerValue(BigInteger.ONE),new IntegerValue(BigInteger.valueOf(4)))))))))));
        var initialFrame=new ActionWriterIntegrationFixture.SoftwareActionScenario(new OperationKey("pause-map"),"game.command.pause-map",
                (command,attempt,dispatch)->new ActionPorts.Pending("original software ACK remains unresolved",List.of(attempt.guard().nativeEvidence())),
                ()->{},Optional.empty(),Optional.empty(),true,Optional.empty());
        try(var fixture=new ActionWriterIntegrationFixture(root.resolve("large-known-restart"),false,scenario,List.of(initialFrame),Duration.ofSeconds(60))) {
            var input=inputs(fixture);var contract=installed.get();
            var publisher=new DriverReadHistoryPublisher(fixture.driverAuthority(),fixture.archive,fixture.reads.catalog(),List.of(contract.sourceRef()));
            fixture.bindAdditionalTransitionAuthority(org.xar.ck3.control.continuity.writer.WriterContracts.DRIVER_READ_HISTORY_KIND,publisher);
            fixture.writer.locked(same->{
                fixture.collector.current(same,input.observed().before(),Instant.now().plusSeconds(60),lease->{
                    var configuration=new DynamicCapabilities.Configuration(Optional.empty(),Optional.empty(),3,3,false,false);
                    var session=new CapabilitySessionPresentation(false,Optional.empty(),Optional.of(CapabilitySessionPresentation.RestoreKind.NEW_EPISODE),
                            CapabilitySessionPresentation.BindingState.ACTIVE_NEW,Optional.empty(),Optional.empty(),Optional.empty(),Optional.empty());
                    var policy=fixture.archive.preserveMaterial(new RawJson(StrictJson.canonical(StrictJson.object().put("actual_capture_read_start_policy",true))));
                    var produced=DriverCapabilityStateProducer.initializeNewEpisode(lease.frame(),lease.driver(),configuration,session,policy,fixture.archive.withSession(same));
                    fixture.driverAuthority().publishCapabilityInputs(same,lease.driver().stamp(),produced.expectedAuxiliarySha256(),produced);return null;
                });return null;
            });
            var before=fixture.writer.locked(same->fixture.driverAuthority().withFrozenFacts(same,frozen->(DriverSnapshotFacts.Known)frozen.state()));
            fixture.writer.locked(same->{
                fixture.collector.current(same,input.observed().before(),Instant.now().plusSeconds(60),lease->{
                    for(int ordinal=0;ordinal<6;ordinal++) {
                        var request=new PlanningReadRequest(lease.frame().identity(),lease.frame().source(),lease.frame().sessionId(),contract.operation(),new Obj(java.util.Map.of()),Instant.now().plusSeconds(60));
                        var result=fixture.reads.read(same,contract,request);
                        if(!(result instanceof PlanningReadResult.Known<MilitaryReadObservation> known))throw new AssertionError(result);
                        publisher.enqueue(same,contract,known);
                    }
                    return null;
                });assertTrue(publisher.flushActualReads(same).isPresent());return null;
            });
            // Publication deliberately clears old receive custody; use the real collector for a current observation.
            dirtyReady(fixture,Instant.now().plusSeconds(60));
            var current=fixture.writer.locked(same->fixture.driverAuthority().withFrozenFacts(same,frozen->(DriverSnapshotFacts.Known)frozen.state()));
            assertEquals(before.driver().commandHistory().size()+6,current.driver().commandHistory().size());
            assertTrue(current.observation().isPresent());assertTrue(current.driver().encode().length>ContinuityJson.TRANSPORT_MAX_BYTES);
            var durable=new DriverSnapshotFacts.Known(current.driver(),current.stamp(),current.originalHistoryBasis(),current.actionRows(),current.auxiliary(),current.loop(),Optional.empty());
            byte[] expected=DriverSnapshotFacts.encodeKnownOriginal(durable).bytes();
            assertTrue(expected.length>ContinuityJson.TRANSPORT_MAX_BYTES);
            var ticket=fixture.writer.locked(same->input.controller().captureCleanRestart(same,"large-known-worker",0));
            var admitted=fixture.writer.locked(same->input.batches().admitCleanRestart(same,ticket));
            assertTrue(admitted.manifest().driverFacts().bytes()>ContinuityJson.TRANSPORT_MAX_BYTES);
            assertArrayEquals(expected,fixture.archive.loadFullMaterial(admitted.manifest().driverFacts()).bytes());
            assertArrayEquals(current.driver().encode(),fixture.archive.loadFullMaterial(admitted.manifest().fullDriver()).bytes());
            assertArrayEquals(current.driver().encode(),admitted.facts().driver().encode());assertEquals(current.stamp(),admitted.facts().stamp());
            assertEquals(current.auxiliary(),admitted.facts().auxiliary());assertEquals(current.loop(),admitted.facts().loop());
            assertEquals(current.actionRows(),admitted.facts().actionRows());assertEquals(current.originalHistoryBasis(),admitted.facts().originalHistoryBasis());
            var head=fixture.writer.locked(same->same.head().digest());
            var ordinary=StrictJson.object().put("evidence_id","ordinary-transport-does-not-inherit-known-material").put("source","actual-ordinary-transport-test");
            var ordinaryRequest=new org.xar.ck3.control.continuity.writer.WriterContracts.Request("fixture.ordinary_transport",ContinuityJson.canonical(ordinary),List.of(admitted.manifest().driverFacts()));
            assertThrows(IOException.class,()->fixture.writer.locked(same->same.preview(ordinaryRequest)));
            Files.writeString(Path.of(admitted.manifest().driverFacts().path()),"{}");
            assertThrows(IOException.class,()->fixture.writer.locked(same->input.batches().admitCleanRestart(same,ticket)));
            assertEquals(head,fixture.writer.locked(same->same.head().digest()));
            assertEquals(6,fixture.scenarioReadWrites());assertEquals(0,fixture.nativeActionWrites());
        }
    }

    @Test void capturedRecoveryRetainsLargeSemanticDataAndKeepsOrdinaryTransportBound()throws Exception {
        try(var fixture=fixture(root.resolve("large-semantic-recovery"))) {
            var first=dirtyReady(fixture,Instant.now().plusSeconds(60));var owner=fixture.observationIdentity();
            var verifier=new org.xar.ck3.control.application.readiness.NativeSemanticEvidenceVerifier((same,ref,max)->fixture.archive.readArtifact(same,ref,max));
            var cycles=new OrdinaryCycleTransitions(fixture.archive,verifier,
                    (same,session,pair,proof)->{throw new AssertionError("large semantic recovery cannot SAVE");},
                    new OriginalWindowReducer.Policy(10958),fixture.writer::requireSession);
            cycles.bindTerminalFrameLoader(fixture.frameLoader());for(String kind:cycles.kinds())fixture.bindAdditionalTransitionAuthority(kind,cycles);
            var batches=new ContinuityBatchJournal(fixture.writer,cycles);
            var controller=controller(fixture,batches,owner,first.request().source().sourceRef());
            var ticket=fixture.writer.locked(same->controller.captureCleanRestart(same,"large-worker",0));
            var captured=fixture.writer.locked(same->batches.admitCleanRestart(same,ticket));
            batches.commit(new JournalInput(owner,"large-worker-0",JournalKind.BATCH_STARTED,Optional.empty(),Optional.empty(),Optional.empty(),List.of()));
            batches.commit(new JournalInput(owner,"large-worker-0",JournalKind.BATCH_INTERRUPTED,Optional.empty(),Optional.empty(),Optional.empty(),List.of()));
            var admission=fixture.writer.locked(same->batches.admitInitialNoDispatchRecovery(same,owner));
            var nativeOriginal=first.semanticEvidence().orElseThrow().originalNativePacket();
            var nativeFrame=(NativeWire.Snapshot)NativeWire.decode(Files.readAllBytes(Path.of(nativeOriginal.path())));
            var packet=StrictJson.object();packet.put("type","state_snapshot");packet.put("protocol_version",1);
            packet.put("snapshot_id","actual-large-semantic");packet.put("revision",nativeFrame.revision().add(BigInteger.ONE));
            var state=FullJsonTree.parse(nativeFrame.state().value(),DriverJson.MAX_NATIVE_BYTES);
            ((com.fasterxml.jackson.databind.node.ObjectNode)state).put("controlled_semantic_DATA","x".repeat(266240));packet.set("state",state);
            fixture.enqueueSoftwareNativePacket(NativeWire.packet(FullJsonTree.encode(packet,DriverJson.MAX_NATIVE_BYTES)));
            var semantic=dirtyReady(fixture,Instant.now().plusSeconds(60)).semanticEvidence().orElseThrow();
            assertTrue(semantic.semantic().bytes()>ContinuityJson.TRANSPORT_MAX_BYTES);
            assertTrue(semantic.semantic().bytes()<=org.xar.ck3.control.continuity.writer.WriterContracts.MAX_PIN_BYTES);
            var before=fixture.writer.locked(same->same.head().state());
            fixture.writer.locked(same->{batches.finishInitialNoDispatchRecovery(same,admission,semantic);return null;});
            var after=fixture.writer.locked(same->same.head().state());
            assertEquals(before.sequence()+1,after.sequence());assertEquals(org.xar.ck3.control.continuity.ContinuityState.Status.RUNNING,after.status());
            assertEquals(before.settledCycles(),after.settledCycles());assertEquals(before.settledDateRaw(),after.settledDateRaw());
            var retained=fixture.writer.locked(same->batches.admitInitialNoDispatchRecovery(same,owner));
            var retainedDigest=fixture.writer.locked(same->same.head().digest());
            fixture.writer.locked(same->{batches.finishInitialNoDispatchRecovery(same,retained,semantic);return null;});
            assertEquals(retainedDigest,fixture.writer.locked(same->same.head().digest()));
            var ordinary=StrictJson.object().put("evidence_id","ordinary-transport-does-not-inherit-full-semantic").put("source","actual-ordinary-transport-test");
            var ordinaryRequest=new org.xar.ck3.control.continuity.writer.WriterContracts.Request("fixture.ordinary_transport",ContinuityJson.canonical(ordinary),List.of(semantic.semantic()));
            assertThrows(IOException.class,()->fixture.writer.locked(same->same.preview(ordinaryRequest)));
            batches.commit(new JournalInput(owner,"large-worker-1",JournalKind.BATCH_STARTED,Optional.empty(),Optional.empty(),Optional.empty(),List.of()));
            batches.commit(new JournalInput(owner,"large-worker-1",JournalKind.BATCH_INTERRUPTED,Optional.empty(),Optional.empty(),Optional.empty(),List.of()));
            var next=fixture.writer.locked(same->batches.admitInitialNoDispatchRecovery(same,owner));
            assertEquals(2,next.nextBatchSequence());var interrupted=fixture.writer.locked(same->same.head().digest());
            Files.writeString(Path.of(semantic.semantic().path()),"{}");
            assertThrows(IOException.class,()->fixture.writer.locked(same->{batches.finishInitialNoDispatchRecovery(same,next,semantic);return null;}));
            assertEquals(interrupted,fixture.writer.locked(same->same.head().digest()));
            assertEquals(captured.controller(),next.capturedController().orElseThrow());assertEquals(0,fixture.nativeActionWrites());
        }
    }
    @Test void aLaterActualCanonicalBatchHeadCannotReuseTheEarlierRestartTicket()throws Exception {
        try(var fixture=fixture(root.resolve("changed-head"))){
            var input=inputs(fixture);var ticket=fixture.writer.locked(same->input.controller().captureCleanRestart(same,"worker",0));
            input.batches().commit(new JournalInput(input.controller().identity(),"later-batch",JournalKind.BATCH_STARTED,
                    Optional.empty(),Optional.empty(),Optional.empty(),List.of()));
            assertThrows(IllegalArgumentException.class,()->fixture.writer.locked(same->input.batches().admitCleanRestart(same,ticket)));
            assertEquals(0,fixture.nativeActionWrites());
        }
    }
    @Test void sameFileIdentityAndTimestampCannotHideTamperedRestartOriginals()throws Exception {
        try(var fixture=fixture(root.resolve("tampered"))){
            var input=inputs(fixture);var ticket=fixture.writer.locked(same->input.controller().captureCleanRestart(same,"worker",0));
            var admitted=fixture.writer.locked(same->input.batches().admitCleanRestart(same,ticket));
            Path target=Path.of(admitted.manifest().driverFacts().path());var identity=IdentityBearingFileAttributes.read(target);
            byte[] original=Files.readAllBytes(target),corrupt=original.clone();corrupt[corrupt.length-1]^=1;
            byte[] canonical=Files.readAllBytes(Path.of(ticket.persistedHead().path()));
            Files.write(target,corrupt);Files.setLastModifiedTime(target,identity.lastModifiedTime());
            var after=IdentityBearingFileAttributes.read(target);assertEquals(identity.fileKey(),after.fileKey());
            assertEquals(identity.size(),after.size());assertEquals(identity.lastModifiedTime(),after.lastModifiedTime());
            assertThrows(Exception.class,()->fixture.writer.locked(same->input.batches().admitCleanRestart(same,ticket)));
            // The issued admission retains verified immutable DATA; a new admission above still rejects the altered original.
            assertDoesNotThrow(()->fixture.writer.locked(same->{admitted.requireCurrent(same);return null;}));
            assertArrayEquals(canonical,Files.readAllBytes(Path.of(ticket.persistedHead().path())));assertEquals(0,fixture.nativeActionWrites());
        }
    }
    @Test void unknownAfterCapturePreventsInitialRecoveryAdmission() throws Exception {
        try (var fixture = fixture(root.resolve("unknown-after-capture"))) {
            var input = inputs(fixture);
            var ticket = fixture.writer.locked(same -> input.controller().captureCleanRestart(same, "worker", 0));
            assertEquals(ticket, fixture.writer.locked(same -> input.batches().admitCleanRestart(same, ticket)).ticket());
            var headBefore = fixture.writer.locked(same -> same.head().digest());
            assertEquals(0,fixture.nativeActionWrites());

            var receipt = fixture.coordinator.execute(input.observed());
            assertInstanceOf(ActionState.Unknown.class, receipt.state(), () -> "expected unresolved original action after capture");
            assertEquals(1, fixture.nativeActionWrites(), () -> "expected exactly one native write for the unknown action");

            var headAfterUnknown = fixture.writer.locked(same -> same.head().digest());
            assertNotEquals(headBefore, headAfterUnknown, () -> "the original UNKNOWN must remain canonically recorded");

            assertThrows(IllegalArgumentException.class, () -> fixture.writer.locked(same -> input.batches().admitInitialNoDispatchRecovery(same, input.controller().identity())));
            assertEquals(headAfterUnknown, fixture.writer.locked(same -> same.head().digest()), () -> "rejected recovery must not change canonical head");
            assertEquals(1, fixture.nativeActionWrites(), () -> "rejected recovery must not trigger additional native writes");
        }
    }

    @Test void originalUnknownWalPreventsCaptureWithoutAnotherNativeWriteOrJournalEvent()throws Exception {
        try(var fixture=fixture(root.resolve("unknown"))){
            var input=inputs(fixture,"unresolved-original");var command=input.observed();
            var actual=fixture.coordinator.execute(command);assertInstanceOf(ActionState.Unknown.class,actual.state(),()->"actual original unknown producer: "+actual.state());assertEquals(1,fixture.nativeActionWrites());
            var before=fixture.writer.locked(same->same.head().digest());
            assertThrows(IllegalArgumentException.class,()->fixture.writer.locked(same->input.controller().captureCleanRestart(same,"worker",0)));
            assertEquals(before,fixture.writer.locked(same->same.head().digest()));assertEquals(1,fixture.nativeActionWrites());
            assertEquals(actual,fixture.reopenAndReturnExisting(command));assertEquals(1,fixture.nativeActionWrites());
        }
    }
}

