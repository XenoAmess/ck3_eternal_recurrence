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
import org.xar.ck3.control.continuity.writer.WriterContracts;

/** Actual software fresh protocol plus original Controller/writer capture boundary.
 * Does not construct ManagedGameSession, RootApplicationSession, guards, Received or completion proofs.
 * RootSession's catch/lock orchestration still needs its separately owned actual startup acceptance.
 */
final class CleanStopFreshCapture57BoundaryTest {
    @TempDir Path root;
    private record Inputs(ActionCommand observed,ContinuityBatchJournal batches,SessionController controller) { }
    private record Setup(ActionWriterIntegrationFixture fixture,Inputs input) implements AutoCloseable {
        @Override public void close() throws Exception {fixture.close();}
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
    private Ready dirtyReady(ActionWriterIntegrationFixture fixture,Instant deadline)throws IOException,InterruptedException {
        var held=fixture.writer.activeSession();
        var observed=held.isPresent()
                ?fixture.collector.observe(held.orElseThrow(),fixture.observationIdentity(),deadline)
                :fixture.collector.observe(fixture.observationIdentity(),deadline);
        return assertInstanceOf(Ready.class,observed,()->"actual dirty-suffix observation: "+observed);
    }

    private Setup setup(String mode)throws Exception {
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
        var exactScenario=new ActionWriterIntegrationFixture.SoftwareReadScenario(
                ExactCk3Build.CK3_12004.executableSha256(),"ck3-1.20.0.4-msvc-x64",scenario.contracts(),scenario.result(),
                Optional.of(ExactCk3Build.CK3_12004.version()),Set.of(NativeFreshSnapshotPort.CAPABILITY));
        var initialFrame=new ActionWriterIntegrationFixture.SoftwareActionScenario(new OperationKey("pause-map"),"game.command.pause-map",
                (command,attempt,dispatch)->new ActionPorts.Pending("original software ACK remains unresolved",List.of(attempt.guard().nativeEvidence())),
                ()->{},Optional.empty(),Optional.empty(),true,Optional.empty());
        var fixture=new ActionWriterIntegrationFixture(root.resolve("stop-fresh-"+mode),false,exactScenario,List.of(initialFrame),Duration.ofSeconds(60));
        try {
            fixture.configureSoftwareFreshRead179(mode);
            var input=inputs(fixture);var contract=installed.get();
            var publisher=new DriverReadHistoryPublisher(fixture.driverAuthority(),fixture.archive,fixture.reads.catalog(),List.of(contract.sourceRef()));
            fixture.bindAdditionalTransitionAuthority(WriterContracts.DRIVER_READ_HISTORY_KIND,publisher);
            fixture.writer.locked(same->{
                fixture.collector.current(same,input.observed().before(),Instant.now().plusSeconds(60),lease->{
                    var configuration=new DynamicCapabilities.Configuration(Optional.empty(),Optional.empty(),3,3,false,false);
                    var presentation=new CapabilitySessionPresentation(false,Optional.empty(),Optional.of(CapabilitySessionPresentation.RestoreKind.NEW_EPISODE),
                            CapabilitySessionPresentation.BindingState.ACTIVE_NEW,Optional.empty(),Optional.empty(),Optional.empty(),Optional.empty());
                    var policy=fixture.archive.preserveMaterial(new RawJson(StrictJson.canonical(StrictJson.object().put("actual_capture_read_start_policy",true))));
                    var produced=DriverCapabilityStateProducer.initializeNewEpisode(lease.frame(),lease.driver(),configuration,presentation,policy,fixture.archive.withSession(same));
                    fixture.driverAuthority().publishCapabilityInputs(same,lease.driver().stamp(),produced.expectedAuxiliarySha256(),produced);return null;
                });return null;
            });
            fixture.writer.locked(same->{
                fixture.collector.current(same,input.observed().before(),Instant.now().plusSeconds(60),lease->{
                    var request=new PlanningReadRequest(lease.frame().identity(),lease.frame().source(),lease.frame().sessionId(),contract.operation(),new Obj(java.util.Map.of()),Instant.now().plusSeconds(60));
                    var read=fixture.reads.read(same,contract,request);
                    var known=assertInstanceOf(PlanningReadResult.Known.class,read);
                    @SuppressWarnings("unchecked") var typed=(PlanningReadResult.Known<MilitaryReadObservation>)known;
                    publisher.enqueue(same,contract,typed);return null;
                });
                assertTrue(publisher.flushActualReads(same).isPresent(),"the original READ history publication must actually commit");return null;
            });
            assertTrue(known(fixture).observation().isEmpty(),"actual history CAS must invalidate old observation");
            assertEquals(0,fixture.nativeActionWrites());
            return new Setup(fixture,input);
        } catch(Exception|Error failure) {
            try{fixture.close();}catch(Exception close){failure.addSuppressed(close);}throw failure;
        }
    }
    private DriverSnapshotFacts.Known known(ActionWriterIntegrationFixture fixture)throws IOException {
        return fixture.writer.locked(same->fixture.driverAuthority().withFrozenFacts(same,
                frozen->assertInstanceOf(DriverSnapshotFacts.Known.class,frozen.state())));
    }

    private void missingWithoutCommit(Setup setup)throws Exception {
        var fixture=setup.fixture();var controller=setup.input().controller();
        var head=fixture.writer.locked(same->same.head());byte[] original=fixture.ledgerBytes();
        assertThrows(OrdinaryCycleTransitions.MissingDriverObservation.class,
                ()->fixture.writer.locked(same->controller.captureCleanRestart(same,"fresh-stop-worker",7)));
        assertFalse(controller.isRunning(),"typed failure must release the Controller CAS");
        assertTrue(fixture.writer.activeSession().isEmpty(),"typed failure must exit the writer scope");
        assertEquals(head.digest(),fixture.writer.locked(same->same.head().digest()));
        assertEquals(head.state().sequence(),fixture.writer.locked(same->same.head().state().sequence()).longValue());
        assertArrayEquals(original,fixture.ledgerBytes(),"typed absence must not append a capture event");
        assertTrue(known(fixture).observation().isEmpty());
    }
    @Test void genuineFreshReadAndDriverJoinPermitSecondActualCaptureWithoutChangingDriverOrCredit()throws Exception {
        try(var setup=setup("success")) {
            var fixture=setup.fixture();var input=setup.input();var before=known(fixture);
            byte[] driverBytes=before.driver().encode();var initialHead=fixture.writer.locked(same->same.head());
            missingWithoutCommit(setup);
            Instant deadline=Instant.now().plusSeconds(15);
            var received=assertInstanceOf(NativeFreshSnapshotPort.Received.class,
                    fixture.physicalInputs().transport().readFreshFullState(deadline));
            NativeFreshSnapshotPort.verifyOriginal(received.acknowledgement(),received.originalFrame(),received.snapshotReceived());
            assertArrayEquals(fixture.softwareFreshSnapshot179(),received.originalFrame().originalPacket());
            assertArrayEquals(fixture.softwareFreshAck179(),received.acknowledgement().originalPacket());
            var complete=fixture.writer.locked(same->{
                var originals=fixture.archive.withSession(same);
                var ackRef=originals.preserve(received.acknowledgement());
                assertEquals(received.acknowledgement(),originals.load(ackRef));
                var nativeRef=originals.preserveNativeFrame(received.originalFrame());
                return fixture.driverAuthority().withFrozenRawObservation(received.originalFrame(),same,frozen->{
                    var joined=assertInstanceOf(DriverObservationAssembler.Complete.class,
                            fixture.physicalInputs().observationAssembler().assemble(received.originalFrame(),frozen.facts(),nativeRef));
                    assertEquals(received.originalFrame().session().game(),joined.identity().game());
                    assertEquals(received.originalFrame().snapshotId(),joined.identity().frame().snapshotId());
                    assertEquals(received.originalFrame().nativeRevision(),joined.identity().frame().identity().nativeRevision());
                    assertEquals(nativeRef,joined.originalEvidence());
                    return joined;
                });
            });
            assertTrue(fixture.writer.activeSession().isEmpty(),"raw observation callback must have exited before capture");
            var refreshed=known(fixture);assertTrue(refreshed.observation().isPresent());
            assertEquals(complete.identity().frame().snapshotId(),refreshed.observation().orElseThrow().snapshotId());
            assertArrayEquals(driverBytes,refreshed.driver().encode());assertEquals(before.stamp(),refreshed.stamp());
            assertEquals(before.actionRows(),refreshed.actionRows());assertEquals(before.auxiliary(),refreshed.auxiliary());
            assertEquals(before.loop(),refreshed.loop());assertEquals(before.originalHistoryBasis(),refreshed.originalHistoryBasis());
            assertEquals(initialHead.digest(),fixture.writer.locked(same->same.head().digest()),"READ and join do not append a capture event");
            var ticket=fixture.writer.locked(same->input.controller().captureCleanRestart(same,"fresh-stop-worker",7));
            var admitted=fixture.writer.locked(same->input.batches().admitCleanRestart(same,ticket));
            assertEquals(ticket,admitted.ticket());assertEquals(ticket,ContinuityBatchJournal.CleanRestartTicket.decode(ticket.encode()));
            assertArrayEquals(driverBytes,admitted.facts().driver().encode());assertEquals(before.stamp(),admitted.facts().stamp());
            assertEquals(before.actionRows(),admitted.facts().actionRows());assertEquals(before.auxiliary(),admitted.facts().auxiliary());
            assertEquals(before.loop(),admitted.facts().loop());assertTrue(admitted.facts().observation().isEmpty(),"durable capture deliberately excludes old receive custody");
            assertArrayEquals(driverBytes,fixture.archive.loadFullMaterial(admitted.manifest().fullDriver()).bytes());
            assertEquals(received.originalFrame().session(),admitted.manifest().previousTransport());
            assertEquals(received.originalFrame().nativeRevision(),admitted.manifest().nativeRevision());
            assertEquals("fresh-stop-worker",admitted.controller().batchPrefix());assertEquals(7,admitted.controller().nextBatchSequence());
            assertTrue(admitted.controller().savedPair().isEmpty());assertFalse(admitted.controller().dirty());
            assertEquals(0,admitted.controller().eligibleSinceSave());assertEquals(0,admitted.controller().totalCommittedDays());
            assertTrue(admitted.controller().usedBatches().isEmpty());assertTrue(admitted.controller().unsavedGameplayActions().isEmpty());
            assertFalse(admitted.controller().quarantined());assertFalse(admitted.controller().localUnresolved());
            fixture.writer.locked(same->{admitted.requireCurrent(same);
                assertEquals(initialHead.state().settledCycles(),same.head().state().settledCycles());
                assertEquals(initialHead.state().settledDateRaw(),same.head().state().settledDateRaw());return null;});
            assertEquals(1,fixture.softwareFreshWrites179());assertEquals(0,fixture.nativeActionWrites());
            assertFalse(input.controller().isRunning());assertTrue(fixture.writer.activeSession().isEmpty());
        }
    }

    @Test void negativeFreshAckCannotSupplyObservationOrTicket()throws Exception {
        failedFreshReadCannotCapture("negative-ack");
    }
    @Test void missingFreshAckCannotSupplyObservationOrTicket()throws Exception {
        failedFreshReadCannotCapture("missing-ack");
    }
    private void failedFreshReadCannotCapture(String mode)throws Exception {
        try(var setup=setup(mode)) {
            var fixture=setup.fixture();var before=known(fixture);missingWithoutCommit(setup);
            var head=fixture.writer.locked(same->same.head());byte[] original=fixture.ledgerBytes();
            var unavailable=assertInstanceOf(NativeFreshSnapshotPort.Unavailable.class,
                    fixture.physicalInputs().transport().readFreshFullState(Instant.now().plusSeconds(5)));
            fixture.writer.locked(same->{
                var originals=fixture.archive.withSession(same);
                var originalDispatch=originals.preserve(unavailable.dispatch());
                assertEquals(unavailable.dispatch(),originals.load(originalDispatch));
                unavailable.originalFrame().ifPresent(originals::preserveNativeFrame);return null;
            });
            assertTrue(unavailable.originalFrame().isPresent(),"controlled original packet exists but is not a successful READ");
            assertEquals(1,fixture.softwareFreshWrites179());assertEquals(0,fixture.nativeActionWrites());
            assertEquals(head.digest(),fixture.writer.locked(same->same.head().digest()));assertArrayEquals(original,fixture.ledgerBytes());
            var after=known(fixture);assertTrue(after.observation().isEmpty());
            assertArrayEquals(before.driver().encode(),after.driver().encode());assertEquals(before.stamp(),after.stamp());
            assertEquals(before.actionRows(),after.actionRows());assertEquals(before.auxiliary(),after.auxiliary());assertEquals(before.loop(),after.loop());
            // A received packet without its qualifying ACK cannot be turned into a second capture.
            missingWithoutCommit(setup);
        }
    }
    @Test void unresolvedOriginalRemainsRejectedWithoutFreshReadOrCaptureEvent()throws Exception {
        try(var setup=setup("success")) {
            var fixture=setup.fixture();var command=fixture.command("original-unresolved-before-stop");
            var original=fixture.coordinator.execute(command);
            assertInstanceOf(ActionState.Unknown.class,original.state(),"actual software coordinator must retain its original unresolved ACK");
            assertEquals(1,fixture.nativeActionWrites());
            var head=fixture.writer.locked(same->same.head());byte[] bytes=fixture.ledgerBytes();
            var failure=assertThrows(IllegalArgumentException.class,()->fixture.writer.locked(same->
                    setup.input().controller().captureCleanRestart(same,"fresh-stop-worker",7)));
            assertEquals(head.digest(),fixture.writer.locked(same->same.head().digest()));assertArrayEquals(bytes,fixture.ledgerBytes());
            assertEquals(original,fixture.journal.locked(locked->locked.find(command.actionId()).orElseThrow()));
            assertEquals(1,fixture.nativeActionWrites());assertEquals(0,fixture.softwareFreshWrites179());
            assertFalse(setup.input().controller().isRunning());assertTrue(fixture.writer.activeSession().isEmpty());
        }
    }
}
