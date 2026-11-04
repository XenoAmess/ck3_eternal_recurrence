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

/** Software canonical capture/admit and real bootstrap/transport boundary; no Managed or Game qualification. */
final class CleanRestartReadOnlyIoPhaseTest {
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

    /** A local canonical material edge consumes a deliberately short, real initial operation deadline. */
    private static final class LocalPreparation implements DriverBootstrap.ExactArtifactReader {
        final DriverBootstrap.ExactArtifactReader originals;
        final ExactRef full;
        final Instant initialDeadline;
        final boolean stall;
        int fullReads;
        boolean preparationElapsed;
        LocalPreparation(DriverBootstrap.ExactArtifactReader originals,ExactRef full,Instant initialDeadline,boolean stall) {
            this.originals=originals;this.full=full;this.initialDeadline=initialDeadline;this.stall=stall;
        }
        @Override public byte[] read(ExactRef expected,int maximumBytes)throws IOException {
            byte[] raw=originals.read(expected,maximumBytes);
            if(expected.equals(full)&&fullReads++==0) {
                if(stall) {
                    long boundedEnd=System.nanoTime()+Duration.ofSeconds(5).toNanos();
                    while(Instant.now().isBefore(initialDeadline)) {
                        if(System.nanoTime()-boundedEnd>=0)throw new IOException("test clock did not reach its bounded initial deadline");
                        long millis=Math.max(1,Math.min(25,Duration.between(Instant.now(),initialDeadline).toMillis()+1));
                        try { Thread.sleep(millis); }
                        catch(InterruptedException interrupted) {
                            Thread.currentThread().interrupt();
                            var failure=new java.io.InterruptedIOException("local software preparation interrupted");
                            failure.initCause(interrupted);throw failure;
                        }
                    }
                }
                preparationElapsed=true;
            }
            return raw;
        }
    }

    @Test void deferredPhaseStartsAfterActualLocalExpiryAndAllPostLocalIoSharesIt()throws Exception {
        try(var fixture=fixture(root.resolve("deferred"))) {
            var restart=capture(fixture);
            var old=restart.admission().manifest().previousTransport();
            var replay=new PhasePackets(old,restart.originalPacket(),true);
            try(var transport=new NativeGameTransport(replay,config(fixture,old),16,32)) {
                var invocations=new java.util.concurrent.atomic.AtomicInteger();
                var phase=new java.util.concurrent.atomic.AtomicReference<Instant>();
                var phaseStartCall=new java.util.concurrent.atomic.AtomicInteger(-1);
                var initial=new java.util.concurrent.atomic.AtomicReference<Instant>();
                var prepared=new java.util.concurrent.atomic.AtomicReference<LocalPreparation>();
                var result=inWriter(fixture,same->{
                    initial.set(Instant.now().plusSeconds(3));
                    var originals=new LocalPreparation(reader(fixture,same),restart.admission().manifest().fullDriver(),initial.get(),true);
                    prepared.set(originals);
                    return DriverBootstrap.adoptCleanRestart(restart.admission(),same,new ActionSnapshotReader(fixture.journal),
                            transport,fixture.observationSource(),fixture.archive,originals,4,initial.get(),()->{
                                assertTrue(originals.preparationElapsed,"the supplier cannot run before canonical local material preparation");
                                assertFalse(Instant.now().isBefore(initial.get()),"the actual initial operation has elapsed");
                                assertEquals(1,invocations.incrementAndGet(),"one read-only phase, never a deadline per RPC");
                                phaseStartCall.set(replay.calls.size());
                                Instant value=Instant.now().plus(Duration.ofMinutes(10));phase.set(value);return value;
                            });
                });
                assertEquals(DriverBootstrap.AdoptionStatus.QUALIFICATION_REQUIRED,result.status());
                result.requireCleanRestart(restart.admission());
                assertEquals(restart.admission().manifest().dateRaw(),result.first().identity().frame().identity().dateRaw().longValueExact());
                assertEquals(fixture.observationSource(),result.source());
                assertEquals(old.game(),result.session().game());assertEquals(old.sessionId(),result.session().sessionId());
                assertTrue(result.session().connectionGeneration().compareTo(old.connectionGeneration())>0);
                assertTrue(prepared.get().fullReads>0);assertEquals(1,invocations.get());
                assertTrue(phaseStartCall.get()>0);assertTrue(replay.calls.size()-phaseStartCall.get()>=5,
                        "post-local HELLO plus fresh connection/write/two response reads must be actual consumers");
                for(var call:replay.calls.subList(0,phaseStartCall.get()))assertEquals(initial.get(),call.deadline(),call.kind());
                for(var call:replay.calls.subList(phaseStartCall.get(),replay.calls.size()))assertEquals(phase.get(),call.deadline(),call.kind());
                assertEquals(1,replay.pings,"the initial handshake is not resent after local preparation");
                assertEquals(1,replay.freshWrites);unchanged(fixture,restart);
            }
        }
    }

    @Test void fixedDeadlineStillExpiresAndInitialHelloRefusesBeforeLocalPreparation()throws Exception {
        try(var fixture=fixture(root.resolve("legacy"))) {
            var restart=capture(fixture);var old=restart.admission().manifest().previousTransport();
            var replay=new PhasePackets(old,restart.originalPacket(),true);
            try(var transport=new NativeGameTransport(replay,config(fixture,old),16,32)) {
                var initial=Instant.now().plusSeconds(3);
                var prepared=new java.util.concurrent.atomic.AtomicReference<LocalPreparation>();
                var failure=assertThrows(IOException.class,()->inWriter(fixture,same->{
                    var originals=new LocalPreparation(reader(fixture,same),restart.admission().manifest().fullDriver(),initial,true);
                    prepared.set(originals);
                    return DriverBootstrap.adoptCleanRestart(restart.admission(),same,new ActionSnapshotReader(fixture.journal),
                            transport,fixture.observationSource(),fixture.archive,originals,4,initial);
                }));
                assertTrue(prepared.get().preparationElapsed);assertTrue(failure.getMessage().contains("deadline"));
                assertEquals(1,replay.pings);assertEquals(0,replay.freshWrites);unchanged(fixture,restart);
            }
            var refused=new PhasePackets(old,restart.originalPacket(),true);
            try(var transport=new NativeGameTransport(refused,config(fixture,old),16,32)) {
                var reads=new java.util.concurrent.atomic.AtomicInteger();var supplierCalls=new java.util.concurrent.atomic.AtomicInteger();
                assertThrows(IOException.class,()->inWriter(fixture,same->DriverBootstrap.adoptCleanRestart(restart.admission(),same,
                        new ActionSnapshotReader(fixture.journal),transport,fixture.observationSource(),fixture.archive,
                        (ref,max)->{reads.incrementAndGet();return reader(fixture,same).read(ref,max);},4,Instant.now().minusSeconds(1),
                        ()->{supplierCalls.incrementAndGet();return Instant.now().plusSeconds(60);} )));
                assertEquals(0,reads.get());assertEquals(0,supplierCalls.get());assertTrue(refused.calls.isEmpty());
                assertEquals(0,refused.pings);assertEquals(0,refused.freshWrites);unchanged(fixture,restart);
            }
        }
    }

    @Test void invalidDeferredPhaseAndOldHelloGenerationNeverReachFreshReadOrCredit()throws Exception {
        for(String mode:List.of("null-result","throw","old-generation")) {
            try(var fixture=fixture(root.resolve(mode))) {
                var restart=capture(fixture);var old=restart.admission().manifest().previousTransport();
                var replay=new PhasePackets(old,restart.originalPacket(),!mode.equals("old-generation"));
                try(var transport=new NativeGameTransport(replay,config(fixture,old),16,32)) {
                    var calls=new java.util.concurrent.atomic.AtomicInteger();
                    var marker=new IllegalStateException("original new read-only phase failed");
                    org.junit.jupiter.api.function.Executable attempt=()->inWriter(fixture,same->DriverBootstrap.adoptCleanRestart(
                            restart.admission(),same,new ActionSnapshotReader(fixture.journal),transport,fixture.observationSource(),fixture.archive,
                            reader(fixture,same),4,Instant.now().plusSeconds(30),()->{
                                calls.incrementAndGet();if(mode.equals("throw"))throw marker;return null;
                            }));
                    if(mode.equals("throw"))assertSame(marker,assertThrows(IllegalStateException.class,attempt));
                    else if(mode.equals("null-result"))assertThrows(NullPointerException.class,attempt);
                    else assertThrows(ContractViolationException.class,attempt);
                    assertEquals(mode.equals("old-generation")?0:1,calls.get());
                    assertEquals(mode.equals("old-generation")?0:1,replay.pings);
                    assertEquals(0,replay.freshWrites);unchanged(fixture,restart);
                }
            }
        }
    }

    private static void unchanged(ActionWriterIntegrationFixture fixture,Restart restart)throws IOException {
        assertEquals(restart.headDigest(),fixture.writer.locked(same->same.head().digest()));
        long actualCycles=fixture.writer.locked(same->same.head().state().settledCycles());
        assertEquals(restart.settledCycles(),actualCycles);
        assertEquals(0,fixture.nativeActionWrites());
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
}
