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
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier;
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
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.contracts.source.IdentityBearingFileAttributes;
import static org.xar.ck3.control.application.session.SessionPorts.*;

/** Software canonical capture/admit and real bootstrap/transport boundary; no Managed or Game qualification. */
final class CleanCoverageBatchIntegrationTest {
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
    private Ready dirtyReady(ActionWriterIntegrationFixture fixture,Instant deadline)throws IOException,InterruptedException {
        var held=fixture.writer.activeSession();
        var observed=held.isPresent()
                ?fixture.collector.observe(held.orElseThrow(),fixture.observationIdentity(),deadline)
                :fixture.collector.observe(fixture.observationIdentity(),deadline);
        return assertInstanceOf(Ready.class,observed,()->"actual dirty-suffix observation: "+observed);
    }

    @FunctionalInterface private interface BootstrapWork<T> {
        T run(org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session same)throws IOException,InterruptedException;
    }
    private static <T>T inWriter(ActionWriterIntegrationFixture fixture,BootstrapWork<T> work)throws IOException {
        return fixture.writer.locked(same->{
            try {return work.run(same);}
            catch(InterruptedException interrupted) {
                Thread.currentThread().interrupt();
                var failure=new java.io.InterruptedIOException("software bootstrap interrupted");
                failure.initCause(interrupted);throw failure;
            }
        });
    }

    private record Restart(Inputs inputs, ContinuityBatchJournal.CleanRestartAdmission admission,
            byte[] originalPacket, String headDigest, long settledCycles) { }

    private Restart capture(ActionWriterIntegrationFixture fixture) throws Exception {
        var input=inputs(fixture);
        var observed=dirtyReady(fixture,Instant.now().plusSeconds(60));
        byte[] packet=Files.readAllBytes(Path.of(observed.semanticEvidence().orElseThrow().originalNativePacket().path()));
        input.controller().drainForCleanRestart(Instant.now().plusSeconds(30));
        var ticket=fixture.writer.locked(same->input.controller().captureCleanRestart(same,"io-phase-worker",0));
        var admission=fixture.writer.locked(same->input.batches().admitCleanRestart(same,ticket));
        return new Restart(input,admission,packet,fixture.writer.locked(same->same.head().digest()),
                fixture.writer.locked(same->same.head().state().settledCycles()));
    }

    private static DriverBootstrap.ExactArtifactReader reader(ActionWriterIntegrationFixture fixture,
            org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session same)throws IOException {
        // This real fixture seeds its original history in its external original-driver.json.
        // The public Bootstrap byte-reader port is not CAS-only; all other materials keep the real archive route.
        var baseline=ExactRef.fromJson(same.head().state().toJson().get(
                org.xar.ck3.control.continuity.writer.WriterContracts.DRIVER_HISTORY_BASELINE_FIELD));
        Path external=fixture.root.resolve("original-driver.json").toAbsolutePath().normalize();
        return (ref,max)->{
            int limit=Math.min(max,org.xar.ck3.control.continuity.writer.ImmutableArtifactStore.MAXIMUM_ARTIFACT_BYTES);
            if(ref.equals(baseline)) {
                Path actual=Path.of(ref.path()).toAbsolutePath().normalize();
                if(!actual.equals(external)||limit<=0||ref.bytes()<=0||ref.bytes()>limit)
                    throw new IOException("fixture's exact external history basis/path/bound differs");
                byte[] raw;
                try(var input=Files.newInputStream(actual)){raw=input.readNBytes(limit+1);}
                if(raw.length!=ref.bytes()||!DriverJson.sha256(raw).equals(ref.sha256()))
                    throw new IOException("fixture's external history basis bytes/SHA changed");
                Path expectedCas=fixture.root.resolve("artifacts").resolve(ref.sha256()+".bin").toAbsolutePath().normalize();
                System.out.println("SOFTWARE_BASELINE_DATA path="+actual+" ref_bytes="+ref.bytes()+" passed_max="+max
                        +" effective_max="+limit+" store_root="+expectedCas.getParent()+" matches_cas="+actual.equals(expectedCas));
                return raw;
            }
            return fixture.archive.readArtifact(same,ref,limit);
        };
    }

    private static final String FOUR_SHA="98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518";
    private static final String FOUR_ADAPTER="ck3-1.20.0.4-msvc-x64";
    private static NativePipeEndpoint.Config config(ActionWriterIntegrationFixture fixture,NativeObservationPort.TransportSession old) {
        return new NativePipeEndpoint.Config(fixture.physicalInputs().transport().pipeName(),old.machineId(),old.game(),old.sessionId(),
                "fixture",FOUR_SHA,FOUR_ADAPTER);
    }

    /** Software protocol DATA only: no Native permission, live Game or canonical admission is manufactured. */
    private static final class PhasePackets implements NativePacketPort {
        private record Call(String kind,Instant deadline) { }
        final java.util.ArrayList<Call> calls=new java.util.ArrayList<>();
        final java.util.ArrayDeque<byte[]> queue=new java.util.ArrayDeque<>();
        final byte[] originalPacket;final BigInteger generation;
        int pings,freshWrites;
        PhasePackets(NativeObservationPort.TransportSession old,byte[] originalPacket,boolean newer)throws IOException {
            this.originalPacket=originalPacket.clone();generation=old.connectionGeneration().add(newer?BigInteger.ONE:BigInteger.ZERO);
            var hello=StrictJson.object().put("type","hello").put("protocol_version",1).put("pid",old.game().pid())
                    .put("connection_generation",generation).put("bridge_version","fixture").put("expected_ck3_sha256",FOUR_SHA)
                    .put("expected_ck3_version","1.20.0.4").put("game_adapter_id",FOUR_ADAPTER)
                    .put("game_adapter_status","ready").put("ck3_build_match",true);
            hello.putArray("capabilities").add("game.state.snapshot").add(NativeFreshSnapshotPort.CAPABILITY);
            queue.add(NativeWire.packet(StrictJson.canonical(hello)));
        }
        @Override public void verify() { }
        @Override public void awaitConnection(Instant deadline) {calls.add(new Call("awaitConnection",deadline));}
        @Override public byte[] readPacket(Instant deadline)throws IOException {
            calls.add(new Call("readPacket",deadline));
            if(queue.isEmpty())throw new IOException("unexpected software packet read");return queue.removeFirst();
        }
        @Override public void writePacket(byte[] original,Instant deadline)throws IOException {
            var request=NativeWire.object(NativeWire.parse(java.util.Arrays.copyOfRange(original,4,original.length)));
            String type=NativeWire.text(request.get("type"));
            if(type.equals("ping")) {
                calls.add(new Call("write:ping",deadline));
                if(++pings!=1)throw new IOException("initial handshake was replayed");return;
            }
            calls.add(new Call("write:fresh",deadline));
            var keys=new java.util.HashSet<String>();request.properties().forEach(entry->keys.add(entry.getKey()));
            if(!keys.equals(Set.of("type","protocol_version","request_id","step","expected_revision"))
                    ||!type.equals("execute_step")||!NativeFreshSnapshotPort.STEP.equals(NativeWire.text(request.get("step")))
                    ||!BigInteger.ZERO.equals(request.get("expected_revision").bigIntegerValue())||++freshWrites!=1)
                throw new IOException("only one original software fresh READ is allowed");
            String id=NativeWire.text(request.get("request_id"));
            var previous=(NativeWire.Snapshot)NativeWire.decode(originalPacket);
            BigInteger revision=previous.revision().add(BigInteger.ONE);
            var snapshot=NativeWire.object(NativeWire.parse(java.util.Arrays.copyOfRange(originalPacket,4,originalPacket.length))).deepCopy();
            snapshot.put("snapshot_id","phase-independent-fresh").put("revision",revision).put("read_request_id",id);
            var state=NativeWire.object(snapshot.get("state"));
            NativeWire.object(state.get("diagnostics")).put("connection_generation",generation);
            queue.add(NativeWire.packet(StrictJson.canonical(snapshot)));
            var ack=StrictJson.object().put("type","command_result").put("protocol_version",1).put("request_id",id).put("ok",true);
            ack.putObject("result").put("schema",NativeFreshSnapshotPort.RESULT_SCHEMA).put("request_id",id)
                    .put("snapshot_id","phase-independent-fresh").put("revision",revision);
            queue.add(NativeWire.packet(StrictJson.canonical(ack)));
        }
        @Override public void close() { }
    }

    private static final OperationKey DIRECT=new OperationKey("fixture-direct-history-rejection");
    private ActionWriterIntegrationFixture coverageFixture(String label,boolean loseAck)throws Exception {
        var held=new AtomicReference<ActionWriterIntegrationFixture>();
        var scenario=new ActionWriterIntegrationFixture.SoftwareActionScenario(DIRECT,"game.command."+DIRECT.value(),(command,attempt,dispatch)->{
            var actual=held.get();var ack=assertInstanceOf(NativeActionPort.AckReceived.class,dispatch);
            assertEquals(new Bool(false),DriverJson.object(ack.originalResultToken().orElseThrow().bytes(),DriverJson.MAX_NATIVE_BYTES).get("accepted"));
            return new ActionPorts.RejectionObserved(new ActionState.Rejected(attempt.requestId(),"source-qualified software rejection",actual.archive.referenceOf(dispatch)));
        },()->{},()->raw(new Obj(Map.of("accepted",new Bool(false),"fixture_direct_api",new Bool(true)))));
        var reads=new ActionWriterIntegrationFixture.SoftwareReadScenario(FOUR_SHA,FOUR_ADAPTER,ignored->List.of(),
                request->{throw new AssertionError("no extra ordinary READ");},Optional.of("1.20.0.4"),Set.of(NativeFreshSnapshotPort.CAPABILITY));
        var initialized=new ActionWriterIntegrationFixture.SoftwareActionScenario(DIRECT,"game.command."+DIRECT.value(),scenario.postcondition(),
                scenario.originalDispatch(),scenario.originalResult(),scenario.privatePermission(),true,scenario.originalPreparation());
        var fixture=new ActionWriterIntegrationFixture(root.resolve(label),loseAck,reads,List.of(initialized),List.of(),source->List.of(
                new org.xar.ck3.control.continuity.writer.DomainBodies.Registration(org.xar.ck3.control.continuity.writer.DomainBodies.Slot.FACTION,
                        DRIFT_SCHEMA,65536,List.of(source),(head,previous,request,raw)->{
                            assertTrue(previous.isEmpty());assertArrayEquals(DRIFT_BODY,raw);assertArrayEquals(DRIFT_BODY,request.producerInput());
                            return ActionCodec.sha256(raw);
                        })));held.set(fixture);fixture.configureSoftwareFreshRead179("success");return fixture;
    }
    private static DriverSnapshotFacts.Known known(ActionWriterIntegrationFixture fixture,Session same)throws IOException {
        return fixture.driverAuthority().withFrozenFacts(same,frozen->assertInstanceOf(DriverSnapshotFacts.Known.class,frozen.state()));
    }
    private static final class ActualRejectionMaterials implements DriverActionHistoryPublisher.MaterialSource {
        private final ActionWriterIntegrationFixture fixture;private int captures;
        ActualRejectionMaterials(ActionWriterIntegrationFixture actual){fixture=actual;}
        NativeRecordedEvidenceVerifier.Binding binding(){return new NativeRecordedEvidenceVerifier.Binding(DIRECT,fixture.observationSource().sourceRef(),(head,receipt,originals)->requireRejected(receipt,originals));}
        @Override public List<ExactRef> sources(){return List.of(fixture.observationSource().sourceRef());}
        @Override public void requireOwner(DriverStateAssembler authority,ActionJournal journal,ActionPorts.OutcomeArchive archive){assertSame(fixture.driverAuthority(),authority);assertSame(fixture.journal,journal);assertSame(fixture.archive,archive);}
        DriverActionHistoryCodec.OriginalMaterial material(ActionReceipt actual){
            var attempt=ActionTransitions.attempt(actual.state()).orElseThrow();var dispatch=ActionTransitions.dispatch(actual.state()).orElseThrow();
            var evidence=List.of(new DriverActionHistoryCodec.Evidence(DriverActionHistoryCodec.EvidenceKind.NATIVE_FRAME,attempt.guard().nativeEvidence()),
                    new DriverActionHistoryCodec.Evidence(DriverActionHistoryCodec.EvidenceKind.MATERIAL,fixture.archive.referenceOf(dispatch)));
            if(actual.command().actionId().startsWith("coverage-legacy")) {
                var ack=assertInstanceOf(NativeActionPort.AckReceived.class,dispatch);
                var result=fixture.archive.preserveMaterial(new RawJson(ack.originalResultToken().orElseThrow().bytes()));
                return new DriverActionHistoryCodec.Legacy(DriverActionHistoryCodec.Recording.ACCEPTED_RETURN,Optional.of(result),Optional.empty(),evidence,sources());
            }
            return new DriverActionHistoryCodec.CanonicalOnly(DriverActionHistoryCodec.CanonicalReason.DIRECT_API_WITHOUT_LEGACY_RECORDER,evidence,sources());
        }
        @Override public DriverActionHistoryCodec.OriginalMaterial capture(Session same,ActionReceipt actual,ActionPorts.OutcomeArchive originals)throws IOException {
            captures++;requireOriginal(same,actual,material(actual),originals);return material(actual);
        }
        @Override public void requireOriginal(Session same,ActionReceipt actual,DriverActionHistoryCodec.OriginalMaterial material,ActionPorts.OutcomeArchive originals)throws IOException {
            fixture.writer.requireSession(same);assertEquals(material(actual),material);
            var verifier=new NativeRecordedEvidenceVerifier(fixture.archive,fixture.journal::borrowedWriterSession,
                    (borrowed,ref,maximum)->fixture.archive.readArtifact(borrowed,ref,maximum),fixture.frameLoader(),List.of(binding()));
            verifier.verify(same.head(),actual);requireRejected(actual,originals);
        }
        private static void requireRejected(ActionReceipt actual,ActionPorts.OutcomeArchive originals){
            assertEquals(DIRECT,actual.command().operation());var state=assertInstanceOf(ActionState.Settled.class,actual.state());
            var rejected=assertInstanceOf(ActionState.Rejected.class,state.settlement());var ack=assertInstanceOf(NativeActionPort.AckReceived.class,state.dispatch());
            assertEquals(ack.requestId(),rejected.requestId());assertEquals(originals.referenceOf(ack),rejected.originalEvidence());
            assertEquals(ack,originals.load(rejected.originalEvidence()));assertEquals(new Bool(false),DriverJson.object(ack.originalResultToken().orElseThrow().bytes(),DriverJson.MAX_NATIVE_BYTES).get("accepted"));
        }
    }
    private static RawJson raw(Value value){return new RawJson(DriverJson.encode(value));}

    private static final String DRIFT_SCHEMA="xar.clean-coverage-head-drift/v1";
    private static final byte[] DRIFT_BODY=ContinuityJson.canonical(StrictJson.object().put("schema",DRIFT_SCHEMA).put("prepared_only",true));

    private Restart mixedCapture(ActionWriterIntegrationFixture fixture)throws Exception {
        Inputs input=inputs(fixture); // install real cycle authority before the first event
        var materials=new ActualRejectionMaterials(fixture);
        fixture.bindAdditionalArchivedVerifier(materials.binding());
        var publisher=new DriverActionHistoryPublisher(fixture.driverAuthority(),fixture.journal,fixture.archive,materials,List.of(fixture.observationSource().sourceRef()));
        fixture.bindAdditionalTransitionAuthority(org.xar.ck3.control.continuity.writer.WriterContracts.DRIVER_ACTION_HISTORY_KIND,publisher);
        for(String id:List.of("coverage-canonical","coverage-legacy")) {
            var actual=fixture.coordinator.execute(fixture.command(id));
            assertEquals(ActionReceipt.Outcome.REJECTED_CONFIRMED,actual.outcome());
            fixture.writer.locked(same->{assertInstanceOf(DriverActionHistoryPublisher.Published.class,publisher.completed(same,actual));return null;});
        }
        var observed=dirtyReady(fixture,Instant.now().plusSeconds(60));
        byte[] packet=Files.readAllBytes(Path.of(observed.semanticEvidence().orElseThrow().originalNativePacket().path()));
        input.controller().drainForCleanRestart(Instant.now().plusSeconds(30));
        var ticket=fixture.writer.locked(same->input.controller().captureCleanRestart(same,"mixed-coverage-worker",0));
        var admission=fixture.writer.locked(same->input.batches().admitCleanRestart(same,ticket));
        assertEquals(2,admission.facts().actionRows().size());
        assertEquals(1L,admission.facts().actionRows().stream().filter(row->row.coverageSource() instanceof DriverSnapshotFacts.CanonicalOnly).count());
        assertEquals(1L,admission.facts().actionRows().stream().filter(row->row.coverageSource() instanceof DriverSnapshotFacts.LegacyHistoryRow).count());
        return new Restart(input,admission,packet,fixture.writer.locked(same->same.head().digest()),
                fixture.writer.locked(same->same.head().state().settledCycles()));
    }

    @Test void cleanRestartAcceptsActualCanonicalAndLegacyRowsInOneFrozenChain()throws Exception {
        try(var fixture=coverageFixture("mixed-pass",false)) {
            var captured=mixedCapture(fixture);var old=captured.admission().manifest().previousTransport();
            int worldWrites=fixture.nativeActionWrites();assertEquals(2,worldWrites);
            var replay=new PhasePackets(old,captured.originalPacket(),true);
            try(var transport=new NativeGameTransport(replay,config(fixture,old),16,32)) {
                var calls=new java.util.concurrent.atomic.AtomicInteger();
                var result=inWriter(fixture,same->{
                    var adopted=DriverBootstrap.adoptCleanRestart(captured.admission(),same,new ActionSnapshotReader(fixture.journal),transport,
                            fixture.observationSource(),fixture.archive,reader(fixture,same),4,Instant.now().plusSeconds(30),()->{
                                assertEquals(1,calls.incrementAndGet());return Instant.now().plusSeconds(30);
                            });
                    var actualRows=adopted.authority().withFrozenFacts(same,frozen->assertInstanceOf(DriverSnapshotFacts.Known.class,frozen.state()).actionRows());
                    // Bootstrap follows the real journal head/previous chain, newest durable receipt first.
                    var expectedRows=captured.admission().facts().actionRows().stream()
                            .sorted(java.util.Comparator.comparingLong(DriverSnapshotFacts.ActionRow::durableSequence).reversed()).toList();
                    assertEquals(expectedRows,actualRows);
                    return adopted;
                });
                result.requireCleanRestart(captured.admission());assertEquals(DriverBootstrap.AdoptionStatus.QUALIFICATION_REQUIRED,result.status());
                assertEquals(1,calls.get());assertEquals(1,replay.freshWrites);assertEquals(1,replay.pings);
                assertEquals(captured.headDigest(),fixture.writer.locked(same->same.head().digest()));
                assertEquals(worldWrites,fixture.nativeActionWrites());
                long cycles=fixture.writer.locked(same->same.head().state().settledCycles());assertEquals(captured.settledCycles(),cycles);
                System.out.println("SOFTWARE_CLEAN_MIXED canonical=1 legacy=1 receipts=2 new_world_writes=0 head_unchanged=true");
            }
        }
    }

    @Test void cleanRestartRejectsRowSourceSupportAndReadTimeHeadDriftBeforeIo()throws Exception {
        try(var fixture=coverageFixture("mixed-faults",false)) {
            var captured=mixedCapture(fixture);var old=captured.admission().manifest().previousTransport();
            var sourceRef=((DriverSnapshotFacts.CanonicalOnly)captured.admission().facts().actionRows().stream()
                    .filter(row->row.coverageSource() instanceof DriverSnapshotFacts.CanonicalOnly).findFirst().orElseThrow().coverageSource()).originalSource();
            var evidence=fixture.writer.locked(same->{
                var source=DriverActionHistoryCodec.decode(fixture.archive.withSession(same).loadMaterial(sourceRef));
                return source.material().evidence().stream().filter(item->item.kind()==DriverActionHistoryCodec.EvidenceKind.NATIVE_FRAME).findFirst().orElseThrow().reference();
            });
            int worldWrites=fixture.nativeActionWrites();
            for(String mode:List.of("source","support","head")) {
                var fired=new java.util.concurrent.atomic.AtomicBoolean();var phaseCalls=new java.util.concurrent.atomic.AtomicInteger();
                var replay=new PhasePackets(old,captured.originalPacket(),true);
                try(var transport=new NativeGameTransport(replay,config(fixture,old),16,32)) {
                    Exception failure=assertThrows(Exception.class,()->inWriter(fixture,same->{
                        var actual=fixture.archive.withSession(same);
                        var faulted=(ActionPorts.OutcomeArchive)java.lang.reflect.Proxy.newProxyInstance(actual.getClass().getClassLoader(),
                                new Class<?>[]{ActionPorts.OutcomeArchive.class},(proxy,method,args)->{
                                    Object value;
                                    try {value=method.invoke(actual,args);}
                                    catch(java.lang.reflect.InvocationTargetException original){throw original.getCause();}
                                    boolean sourceRead=method.getName().equals("loadMaterial")&&args!=null&&args.length==1&&sourceRef.equals(args[0]);
                                    boolean supportingRead=method.getName().equals("loadNativeFrame")&&args!=null&&args.length==1&&evidence.equals(args[0]);
                                    if(mode.equals("source")&&sourceRead&&fired.compareAndSet(false,true))return new RawJson(new byte[]{'{','}'});
                                    if(mode.equals("support")&&supportingRead&&fired.compareAndSet(false,true))return new byte[]{1};
                                    if(mode.equals("head")&&sourceRead&&fired.compareAndSet(false,true)) {
                                        var body=actual.preserveMaterial(new RawJson(DRIFT_BODY));
                                        var request=new org.xar.ck3.control.continuity.writer.DomainBodies.ImportRequest(
                                                org.xar.ck3.control.continuity.writer.DomainBodies.Slot.FACTION,DRIFT_SCHEMA,body,DRIFT_BODY,
                                                List.of(fixture.observationSource().sourceRef()),"clean-coverage-read-time-head-drift");
                                        var prepared=same.previewImport(request);var committed=same.commitImport(prepared);same.requireCommitted(prepared,committed);
                                    }
                                    return value;
                                });
                        return DriverBootstrap.adoptCleanRestart(captured.admission(),same,new ActionSnapshotReader(fixture.journal),transport,
                                fixture.observationSource(),faulted,reader(fixture,same),4,Instant.now().plusSeconds(30),()->{
                                    phaseCalls.incrementAndGet();return Instant.now().plusSeconds(30);
                                });
                    }));
                    assertTrue(fired.get(),"the exact declared DATA fault must actually fire: "+mode);
                    assertTrue(failure instanceof IOException||failure instanceof IllegalArgumentException||failure instanceof java.io.UncheckedIOException,
                            "an unrelated harness/reflection failure cannot witness rejection: "+failure);
                    assertEquals(0,phaseCalls.get(),mode);assertEquals(0,replay.freshWrites,mode);assertEquals(worldWrites,fixture.nativeActionWrites());
                    String head=fixture.writer.locked(same->same.head().digest());
                    if(mode.equals("head")) {
                        assertNotEquals(captured.headDigest(),head);
                        assertTrue(failure.getMessage().contains("clean coverage writer changed"),()->"wrong head rejection: "+failure);
                    } else assertEquals(captured.headDigest(),head);
                }
            }
        }
    }
}
