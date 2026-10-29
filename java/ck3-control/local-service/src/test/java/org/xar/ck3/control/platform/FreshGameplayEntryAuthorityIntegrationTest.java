package org.xar.ck3.control.platform;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.sun.jna.platform.win32.Kernel32;
import com.sun.jna.platform.win32.WinBase;
import com.sun.jna.platform.win32.WinNT.HANDLE;
import com.sun.jna.ptr.IntByReference;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.time.*;
import java.util.*;
import java.util.concurrent.atomic.*;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.*;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.continuity.*;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.nativebridge.*;
import org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRulesRequests.Primitive;
import org.xar.ck3.control.service.root.RootAuthorityRouter;
import org.xar.ck3.control.service.root.RootOrdinaryRuntimeConfiguration;
import org.xar.ck3.control.application.session.*;
import static org.xar.ck3.control.application.session.SessionPorts.*;
import org.xar.ck3.control.application.checkpoint.*;
import org.xar.ck3.control.application.readiness.NativeDriverStamp;
import org.xar.ck3.control.application.readiness.NativeSemanticEvidenceVerifier;
import org.xar.ck3.control.application.planning.OrdinaryPlanCompletion;

/** Real Win32 software pipe/receiver/Driver/writer. No CK3, source qualification, SAVE or day credit. */
public final class FreshGameplayEntryAuthorityIntegrationTest {
    @TempDir Path root;
    private static final String SHA="98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518";
    private static final String ADAPTER="ck3-1.20.0.4-msvc-x64";
    private static Instant deadline(){return Instant.now().plusSeconds(25);}
    private ControlBuild.FileRef ref(String name){return new ControlBuild.FileRef(root.resolve(name).toAbsolutePath().toString(),1,SHA);}
    private NativeLaunchPlan plan(String pipe)throws IOException {
        Instant at=Instant.now();String machine=WindowsJobProcess.currentMachineId();
        var review=new LaunchSourceBinding.Review(machine,at,ref("configured-game.exe"),ref("bridge.dll"),ref("injector.exe"),
                new NativeLaunchEvidence.Inputs(ref("env.json"),ref("build.json"),ref("register.json")),root,List.of(ref("runtime.jar")));
        var profile=new NativeLaunchPlan.PreparedProfile(ref("manifest.json"),root.resolve("mod"),"mod/example.mod",List.of(ref("input")),List.of(ref("descriptor.mod")));
        return new NativeLaunchPlanCodec.Configuration("software-first-map","software-session",review,root,root.resolve("state"),
                root.resolve("evidence"),pipe,"entry-test",ADAPTER,new NativeLaunchPlan.NewGame(),false,
                NativeLaunchPlan.WindowPolicy.MINIMIZED_NO_ACTIVATE,Map.of(),128L<<20,32L<<20,at.plusSeconds(60),
                Duration.ofSeconds(1),Duration.ofSeconds(2),new SteamOfflineProbe.Plan(machine,ref("steam.exe"),at.plusSeconds(60)),profile,128).accept();
    }
    private record Actual(ContinuityWriter writer,NativeOutcomeArchive archive,FreshGameplayEntryAuthority entry,
            DriverBootstrap.Adopted driver,InitialDriverState.Produced produced,NativeActionPort.AckReceived start,NativeFreshSnapshotPort.Received read,ContinuityBatchJournal batches) { }
    private Actual actual(ManagedGameSession game)throws Exception {
        Path base=Files.createDirectory(root.resolve("ledger"));String machine=game.machineId();
        var paths=new WriterContracts.InitialLayout(base.resolve("ROOT-CONTINUITY-WINDOW.json"),base.resolve("anchor.json"),machine);
        Files.createFile(paths.lock());
        var plan=new FreshContinuityGenesis.Plan(machine,1,10958);
        byte[] genesis=FreshContinuityGenesis.encode(plan);Path request=base.resolve("genesis.json");Files.write(request,genesis);
        Path source=base.resolve("source.txt");Files.writeString(source,"software business only");
        var requestRef=new ExactRef(request.toString(),genesis.length,ActionCodec.sha256(genesis));
        byte[] sourceBytes=Files.readAllBytes(source);var sourceRef=new ExactRef(source.toString(),sourceBytes.length,ActionCodec.sha256(sourceBytes));
        var storage=StorageWriteGuardTestSupport.create(base,paths.lock(),256L<<20);
        var initialized=ContinuityWriter.initializeFresh(plan,requestRef,paths,storage);
        var artifacts=new ImmutableArtifactStore(new ImmutableArtifactStore.Config(base.resolve("artifacts"),paths.lock(),64L<<20),storage);
        var router=new RootAuthorityRouter();
        var writer=new ContinuityWriter(initialized.layout(),List.of(sourceRef),router,Clock.systemUTC(),
                new ContinuityWriter.Extensions(List.of(),Optional.of(artifacts),Optional.empty()),storage);
        var archive=new NativeOutcomeArchive(artifacts,writer);var journal=new ContinuityActionJournal(writer,archive);
        var start=assertInstanceOf(NativeActionPort.AckReceived.class,game.nativeTransport().frontendBootstrap(Primitive.START_BOOKMARK,deadline()));
        var read=assertInstanceOf(NativeFreshSnapshotPort.Received.class,game.nativeTransport().readFreshFullState(deadline()));
        NativeFreshSnapshotPort.verifyAfter(start,read);
        var policy = configuredOrdinaryPolicy();
        assertEquals(InitialEpisodePolicy.Lifecycle.ORDINARY_CAMPAIGN_SUCCESSION, policy.kind());
        assertTrue(policy.optionalSource().isEmpty());
        assertTrue(policy.optionalEnvironment().isEmpty());
        assertArrayEquals(StrictJson.canonical(NativeColdAdoptionProjection.Lifecycle.ordinaryVanilla().toJson()), policy.lifecycle().bytes());
        var produced=InitialDriverState.create(read.originalFrame(),game.nativeTransport().pipeName(),"software-episode",
                policy.kind(),policy.lifecycle());
        var decodedDriver = DriverStateSnapshot.decodeComplete(produced.driver().encode());
        var lifecycleSlot = decodedDriver.successionLifecycle();
        assertTrue(lifecycleSlot instanceof DriverStateSnapshot.Value);
        assertArrayEquals(policy.lifecycle().bytes(), ((DriverStateSnapshot.Value) lifecycleSlot).json());
        var adopted=DriverBootstrap.fresh(read,produced,game,writer,archive,new ActionSnapshotReader(journal),
                new G2Source(machine,Instant.now().toString(),"software-exact-12004",sourceRef),8,deadline());
        var entry=new FreshGameplayEntryAuthority(writer,archive);
        var cycles=new OrdinaryCycleTransitions(archive,new NativeSemanticEvidenceVerifier(archive::readArtifact),
                (same,owner,pair,proof)->{throw new AssertionError("test cannot qualify SAVE");},new OriginalWindowReducer.Policy(10958),writer::requireSession);
        var batches=new ContinuityBatchJournal(writer,cycles);var kinds=new HashSet<String>(cycles.kinds());kinds.add(ObservedGameplayEntry.KIND);
        router.seal(List.of(new RootAuthorityRouter.Binding(Set.of(ObservedGameplayEntry.KIND),entry),new RootAuthorityRouter.Binding(cycles.kinds(),cycles)),kinds);
        return new Actual(writer,archive,entry,adopted,produced,start,read,batches);
    }
    @Test void genuineStartReadDriverPublishesActualOriginAndReopensWithoutAnyAdditionalNativeWrite()throws Exception {
        var peer=new Peer("\\\\.\\pipe\\observed-entry-"+UUID.randomUUID());
        var generation=ManagedGameSession.generation(WindowsJobProcess.exactProcess(ProcessHandle.current().pid()));
        var actualPlan=plan(peer.pipe);peer.start();
        try(peer;var game=NativeGameAttachment.attach(new NativeGameAttachment.Request(actualPlan,generation,List.of(),128,32),deadline())) {
            var actual=actual(game);
            actual.entry().retain(game,actual.start(),actual.read(),actual.produced(),actual.driver());
            var committed=actual.writer().locked(actual.entry()::commitInitial);
            assertEquals(WriterContracts.Disposition.COMMITTED,committed.disposition());
            assertEquals(ContinuityState.Status.RUNNING,committed.head().status());
            assertEquals(53144328,committed.head().origin().startDateRaw());assertEquals(0,committed.head().settledCycles());
            assertEquals(73,committed.head().toJson().path("latest_binding").path("actor_character_id").longValue());
            assertEquals("software-episode",committed.head().toJson().path("latest_binding").path("episode_run_id").textValue());
            assertEquals(generation,GameGeneration.fromJson(committed.head().toJson().get("game_binding")));
            assertEquals(2,peer.writes.get());
            actual.writer().locked(same->{assertArrayEquals(committed.head().canonicalBytes(),same.head().state().canonicalBytes());
                actual.entry().commitInitial(same);assertEquals(committed.head().sequence(),same.head().state().sequence());return null;});
            assertEquals(2,peer.writes.get());
        }
    }
    @Test void substitutedInitialDriverRefusesBeforeEntryAndSameFileTamperRefusesCommit()throws Exception {
        var peer=new Peer("\\\\.\\pipe\\observed-entry-bad-"+UUID.randomUUID());
        var generation=ManagedGameSession.generation(WindowsJobProcess.exactProcess(ProcessHandle.current().pid()));
        var actualPlan=plan(peer.pipe);peer.start();
        try(peer;var game=NativeGameAttachment.attach(new NativeGameAttachment.Request(actualPlan,generation,List.of(),128,32),deadline())) {
            var actual=actual(game);
            var wrong=new InitialDriverState.Produced(actual.produced().driver(),new org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj(Map.of()));
            assertThrows(IllegalArgumentException.class,()->actual.entry().retain(game,actual.start(),actual.read(),wrong,actual.driver()));
            actual.entry().retain(game,actual.start(),actual.read(),actual.produced(),actual.driver());
            Path original=Path.of(actual.driver().seed().fullDriver().path());var modified=Files.getLastModifiedTime(original);Object id=org.xar.ck3.control.contracts.source.IdentityBearingFileAttributes.read(original).fileKey();assertInstanceOf(org.xar.ck3.control.contracts.source.IdentityBearingFileAttributes.WindowsFileIdentity.class,id);
            byte[] changed=Files.readAllBytes(original);changed[changed.length-1]^=1;Files.write(original,changed,StandardOpenOption.TRUNCATE_EXISTING);Files.setLastModifiedTime(original,modified);
            assertEquals(id,org.xar.ck3.control.contracts.source.IdentityBearingFileAttributes.read(original).fileKey());assertEquals(modified,Files.getLastModifiedTime(original));
            assertThrows(Exception.class,()->actual.writer().locked(actual.entry()::commitInitial));
            actual.writer().locked(same->{assertEquals(ContinuityState.Status.AWAITING_INITIAL_ENTRY,same.head().state().status());assertEquals(0,same.head().state().sequence());return null;});
            assertEquals(2,peer.writes.get());
        }
    }
    @Test void committedEntryRecoversItsFullDriverOnSameLivingProcessAndNewActualHelloWithoutStartOrEntryReplay()throws Exception {
        var peer=new Peer("\\\\.\\pipe\\observed-entry-recovery-"+UUID.randomUUID(),2,1,3);
        var generation=ManagedGameSession.generation(WindowsJobProcess.exactProcess(ProcessHandle.current().pid()));
        var launch=plan(peer.pipe);peer.start();
        try(peer) {
            Actual original;
            long committedSequence;
            try(var first=NativeGameAttachment.attach(new NativeGameAttachment.Request(launch,generation,List.of(),128,32),deadline())) {
                original=actual(first);original.entry().retainCurrentMap(first,original.read(),original.produced(),original.driver());
                committedSequence=original.writer().locked(original.entry()::commitInitial).head().sequence();
            }
            try(var second=NativeGameAttachment.attach(new NativeGameAttachment.Request(launch,generation,List.of(),128,32),deadline())) {
                assertEquals(generation,second.generation());
                var issuer=new FreshGameplayEntryAuthority(original.writer(),original.archive());
                original.writer().locked(same->{
                    var admission=issuer.admitRecovery(same,second);
                    assertInstanceOf(ObservedGameplayEntry.Origin.CurrentMap.class,admission.entry().origin());
                    assertFalse(admission.entry().toJson().has("start_ack"));
                    try {
                        var driver=DriverBootstrap.adoptInitialRecovery(admission,same,
                                new ActionSnapshotReader(new ContinuityActionJournal(original.writer(),original.archive())),
                                second.nativeTransport(),original.driver().source(),original.archive(),8,deadline());
                        driver.requireInitialRecovery(admission);
                        var after=driver.authority().withFrozenFacts(same,frozen->(DriverSnapshotFacts.Known)frozen.state());
                        assertArrayEquals(original.produced().driver().encode(),after.driver().encode());
                        assertEquals(admission.facts().stamp(),after.stamp());assertEquals(admission.facts().auxiliary(),after.auxiliary());
                        assertEquals(admission.facts().loop(),after.loop());assertEquals(admission.facts().actionRows(),after.actionRows());
                        assertTrue(driver.session().connectionGeneration().compareTo(original.driver().session().connectionGeneration())>0);
                        assertTrue(driver.first().identity().frame().revision().compareTo(original.driver().first().identity().frame().revision())>0);
                        assertEquals(original.driver().first().identity().frame().identity().player(),driver.first().identity().frame().identity().player());
                        assertEquals(original.driver().first().identity().frame().identity().dateRaw(),driver.first().identity().frame().identity().dateRaw());
                        assertEquals(BigInteger.valueOf(3),driver.first().identity().frame().identity().nativeRevision());
                        assertEquals(DriverBootstrap.AdoptionStatus.QUALIFICATION_REQUIRED,driver.status());
                        assertEquals(committedSequence,same.head().state().sequence());
                    }catch(InterruptedException interrupted){Thread.currentThread().interrupt();throw new IOException(interrupted);}
                    return null;
                });
            }
            assertEquals(3,peer.writes.get(),"one original START and two genuine full reads, no replay");
        }
    }
    @Test void regressedNativeRevisionOnNewConnectionRefusesWithoutReplayingStartOrChangingEntry()throws Exception {
        var peer=new Peer("\\\\.\\pipe\\observed-entry-regression-"+UUID.randomUUID(),2,3,1);
        var generation=ManagedGameSession.generation(WindowsJobProcess.exactProcess(ProcessHandle.current().pid()));
        var launch=plan(peer.pipe);peer.start();
        try(peer) {
            Actual original;
            long committedSequence;
            try(var first=NativeGameAttachment.attach(new NativeGameAttachment.Request(launch,generation,List.of(),128,32),deadline())) {
                original=actual(first);original.entry().retainCurrentMap(first,original.read(),original.produced(),original.driver());
                committedSequence=original.writer().locked(original.entry()::commitInitial).head().sequence();
            }
            try(var second=NativeGameAttachment.attach(new NativeGameAttachment.Request(launch,generation,List.of(),128,32),deadline())) {
                var issuer=new FreshGameplayEntryAuthority(original.writer(),original.archive());
                var failure=assertThrows(IllegalArgumentException.class,()->original.writer().locked(same->{
                    var admission=issuer.admitRecovery(same,second);
                    try {DriverBootstrap.adoptInitialRecovery(admission,same,
                            new ActionSnapshotReader(new ContinuityActionJournal(original.writer(),original.archive())),
                            second.nativeTransport(),original.driver().source(),original.archive(),8,deadline());}
                    catch(InterruptedException interrupted){Thread.currentThread().interrupt();throw new IOException(interrupted);}
                    return null;
                }));
                assertTrue(failure.getMessage().contains("regressed native revision"));
                original.writer().locked(same->{
                    assertEquals(committedSequence,same.head().state().sequence());
                    assertEquals(BigInteger.valueOf(3),ObservedGameplayEntry.decode(same.head().state().toJson().get(WriterContracts.GAMEPLAY_ENTRY_FIELD)).nativeRevision());
                    return null;
                });
            }
            assertEquals(3,peer.writes.get(),"the refused recovery cannot replay START or the full READ");
        }
    }
    @Test void laterDateOnNewConnectionWithoutCapturedProofRefusesRecovery()throws Exception {
        var peer=new Peer("\\\\.\\pipe\\observed-entry-date-regression-"+UUID.randomUUID(),2,new long[]{1,3},new long[]{53144328,53144352});
        var generation=ManagedGameSession.generation(WindowsJobProcess.exactProcess(ProcessHandle.current().pid()));
        var launch=plan(peer.pipe);peer.start();
        try(peer) {
            Actual original;
            long committedSequence;
            String committedDigest;
            try(var first=NativeGameAttachment.attach(new NativeGameAttachment.Request(launch,generation,List.of(),128,32),deadline())) {
                original=actual(first);
                original.entry().retainCurrentMap(first,original.read(),original.produced(),original.driver());
                var head=original.writer().locked(original.entry()::commitInitial).head();
                committedSequence=head.sequence();
                committedDigest=ContinuityJson.digest(head.toJson());
            }
            try(var second=NativeGameAttachment.attach(new NativeGameAttachment.Request(launch,generation,List.of(),128,32),deadline())) {
                var issuer=new FreshGameplayEntryAuthority(original.writer(),original.archive());
                var failure=assertThrows(IllegalArgumentException.class,()->original.writer().locked(same->{
                    var admission=issuer.admitRecovery(same,second);
                    try {
                        DriverBootstrap.adoptInitialRecovery(admission,same,
                                new ActionSnapshotReader(new ContinuityActionJournal(original.writer(),original.archive())),
                                second.nativeTransport(),original.driver().source(),original.archive(),8,deadline());
                    } catch(InterruptedException interrupted){Thread.currentThread().interrupt();throw new IOException(interrupted);}
                    return null;
                }));
                assertTrue(failure.getMessage().contains("changed actor/date"),"recovery must reject date change without captured proof");
                original.writer().locked(same->{
                    assertEquals(committedSequence,same.head().state().sequence());
                    assertEquals(committedDigest,same.head().digest());
                    return null;
                });
            }
            assertEquals(3,peer.writes.get(),"the refused recovery cannot replay START or the full READ");
        }
    }

    @Test void actualInterruptedFirstBatchResumesOnlyWithJournalProofAndPreservesConsumedBatch()throws Exception {
        var peer=new Peer("\\\\.\\pipe\\observed-entry-initial-interruption-"+UUID.randomUUID(),2,1,3);
        var generation=ManagedGameSession.generation(WindowsJobProcess.exactProcess(ProcessHandle.current().pid()));
        var launch=plan(peer.pipe);peer.start();
        try(peer) {
            Actual original;
            SessionIdentity owner;
            try(var first=NativeGameAttachment.attach(new NativeGameAttachment.Request(launch,generation,List.of(),128,32),deadline())) {
                original=actual(first);original.entry().retainCurrentMap(first,original.read(),original.produced(),original.driver());
                original.writer().locked(original.entry()::commitInitial);
                owner=new SessionIdentity(first.machineId(),first.generation(),first.sessionId());
                original.batches().commit(new JournalInput(owner,"software-batch-0",JournalKind.BATCH_STARTED,Optional.empty(),Optional.empty(),Optional.empty(),List.of()));
                original.batches().commit(new JournalInput(owner,"software-batch-0",JournalKind.BATCH_INTERRUPTED,Optional.empty(),Optional.empty(),Optional.empty(),List.of()));
            }
            try(var second=NativeGameAttachment.attach(new NativeGameAttachment.Request(launch,generation,List.of(),128,32),deadline())) {
                var issuer=new FreshGameplayEntryAuthority(original.writer(),original.archive());
                original.writer().locked(same->{
                    assertThrows(IllegalArgumentException.class,()->issuer.admitRecovery(same,second));
                    var proof=original.batches().admitInitialNoDispatchRecovery(same,owner);
                    assertEquals("software-batch-0",proof.consumedBatchId());assertEquals(1,proof.nextBatchSequence());
                    var admission=issuer.admitRecovery(same,second,proof);
                    try {
                        var driver=DriverBootstrap.adoptInitialRecovery(admission,same,
                                new ActionSnapshotReader(new ContinuityActionJournal(original.writer(),original.archive())),
                                second.nativeTransport(),original.driver().source(),original.archive(),8,deadline());
                        driver.requireInitialNoDispatchRecovery(proof);
                        var controller=initialRecoveryController(original,owner,driver);
                        assertThrows(IllegalArgumentException.class,()->controller.restoreInitialNoDispatchRecovery(same,proof));
                        var known=driver.authority().withFrozenFacts(same,frozen->(DriverSnapshotFacts.Known)frozen.state());
                        var frame=driver.first();var archive=original.archive().withSession(same);
                        var semantic=archive.preserveMaterial(new RawJson(DriverJson.encode(frame.semantic())));
                        var stamp=archive.preserveMaterial(new RawJson(NativeDriverStamp.encode(frame,known)));
                        var evidence=new SemanticEvidence(frame.identity(),semantic,frame.originalEvidence(),stamp,driver.currentDriverEvidence(),frame.observedAt());
                        original.batches().commitInitialNoDispatchRecovery(same,proof,evidence);
                        admission.requireCurrent(same);controller.restoreInitialNoDispatchRecovery(same,proof);
                        assertThrows(IllegalArgumentException.class,()->controller.restoreInitialNoDispatchRecovery(same,proof));
                        assertArrayEquals(original.produced().driver().encode(),known.driver().encode());
                        assertEquals(0,same.head().state().settledCycles());assertEquals(53144328,same.head().state().settledDateRaw());
                        var ticket=controller.captureCleanRestart(same,proof.batchPrefix(),proof.nextBatchSequence());
                        var restored=original.batches().admitCleanRestart(same,ticket).controller();
                        assertEquals(Set.of("software-batch-0"),restored.usedBatches());assertEquals(1,restored.nextBatchSequence());
                        assertFalse(restored.dirty());assertTrue(restored.unsavedGameplayActions().isEmpty());assertTrue(restored.savedPair().isEmpty());
                    }catch(InterruptedException interrupted){Thread.currentThread().interrupt();throw new IOException(interrupted);}
                    return null;
                });
            }
            assertEquals(3,peer.writes.get(),"recovery performs no new START, action or SAVE");
        }
    }
    @Test void actualRepeatedNoDispatchFailuresRetainEveryBatchAndAdvanceRestartSequence()throws Exception {
        var peer=new Peer("\\\\.\\pipe\\observed-entry-repeated-interruption-"+UUID.randomUUID(),3,1,3,5);
        var generation=ManagedGameSession.generation(WindowsJobProcess.exactProcess(ProcessHandle.current().pid()));
        var launch=plan(peer.pipe);peer.start();
        try(peer) {
            Actual original;
            SessionIdentity owner;
            try(var first=NativeGameAttachment.attach(new NativeGameAttachment.Request(launch,generation,List.of(),128,32),deadline())) {
                original=actual(first);original.entry().retainCurrentMap(first,original.read(),original.produced(),original.driver());
                original.writer().locked(original.entry()::commitInitial);
                owner=new SessionIdentity(first.machineId(),first.generation(),first.sessionId());
                original.batches().commit(new JournalInput(owner,"software-batch-0",JournalKind.BATCH_STARTED,Optional.empty(),Optional.empty(),Optional.empty(),List.of()));
                original.batches().commit(new JournalInput(owner,"software-batch-0",JournalKind.BATCH_INTERRUPTED,Optional.empty(),Optional.empty(),Optional.empty(),List.of()));
            }
            byte[] originalEntry=original.writer().locked(same->StrictJson.canonical(same.head().state().toJson().get(WriterContracts.GAMEPLAY_ENTRY_FIELD)));
            ContinuityBatchJournal.InitialNoDispatchRecovery proof0;
            try(var second=NativeGameAttachment.attach(new NativeGameAttachment.Request(launch,generation,List.of(),128,32),deadline())) {
                var issuer=new FreshGameplayEntryAuthority(original.writer(),original.archive());
                proof0=original.writer().locked(same->{
                    var proof=original.batches().admitInitialNoDispatchRecovery(same,owner);
                    assertEquals(List.of("software-batch-0"),proof.consumedBatchIds());assertEquals(1,proof.nextBatchSequence());
                    var admission=issuer.admitRecovery(same,second,proof);
                    try {
                        var driver=DriverBootstrap.adoptInitialRecovery(admission,same,
                                new ActionSnapshotReader(new ContinuityActionJournal(original.writer(),original.archive())),
                                second.nativeTransport(),original.driver().source(),original.archive(),8,deadline());
                        driver.requireInitialNoDispatchRecovery(proof);
                        var known=driver.authority().withFrozenFacts(same,frozen->(DriverSnapshotFacts.Known)frozen.state());
                        var frame=driver.first();var archive=original.archive().withSession(same);
                        var semantic=archive.preserveMaterial(new RawJson(DriverJson.encode(frame.semantic())));
                        var stamp=archive.preserveMaterial(new RawJson(NativeDriverStamp.encode(frame,known)));
                        var evidence=new SemanticEvidence(frame.identity(),semantic,frame.originalEvidence(),stamp,driver.currentDriverEvidence(),frame.observedAt());
                        original.batches().commitInitialNoDispatchRecovery(same,proof,evidence);
                        admission.requireCurrent(same);
                        assertArrayEquals(original.produced().driver().encode(),known.driver().encode());
                    }catch(InterruptedException interrupted){Thread.currentThread().interrupt();throw new IOException(interrupted);}
                    return proof;
                });
            }
            original.batches().commit(new JournalInput(owner,"software-batch-1",JournalKind.BATCH_STARTED,Optional.empty(),Optional.empty(),Optional.empty(),List.of()));
            original.batches().commit(new JournalInput(owner,"software-batch-1",JournalKind.BATCH_INTERRUPTED,Optional.empty(),Optional.empty(),Optional.empty(),List.of()));
            try(var third=NativeGameAttachment.attach(new NativeGameAttachment.Request(launch,generation,List.of(),128,32),deadline())) {
                var issuer=new FreshGameplayEntryAuthority(original.writer(),original.archive());
                original.writer().locked(same->{
                    assertThrows(IOException.class,()->proof0.requireCurrent(same));
                    assertThrows(IllegalArgumentException.class,()->issuer.admitRecovery(same,third));
                    var proof1=original.batches().admitInitialNoDispatchRecovery(same,owner);
                    assertEquals(List.of("software-batch-0","software-batch-1"),proof1.consumedBatchIds());
                    assertEquals("software-batch-1",proof1.consumedBatchId());assertEquals(2,proof1.nextBatchSequence());
                    var admission=issuer.admitRecovery(same,third,proof1);
                    try {
                        var driver=DriverBootstrap.adoptInitialRecovery(admission,same,
                                new ActionSnapshotReader(new ContinuityActionJournal(original.writer(),original.archive())),
                                third.nativeTransport(),original.driver().source(),original.archive(),8,deadline());
                        driver.requireInitialNoDispatchRecovery(proof1);
                        var controller=initialRecoveryController(original,owner,driver);
                        assertThrows(IllegalArgumentException.class,()->controller.restoreInitialNoDispatchRecovery(same,proof1));
                        var known=driver.authority().withFrozenFacts(same,frozen->(DriverSnapshotFacts.Known)frozen.state());
                        var frame=driver.first();var archive=original.archive().withSession(same);
                        var semantic=archive.preserveMaterial(new RawJson(DriverJson.encode(frame.semantic())));
                        var stamp=archive.preserveMaterial(new RawJson(NativeDriverStamp.encode(frame,known)));
                        var evidence=new SemanticEvidence(frame.identity(),semantic,frame.originalEvidence(),stamp,driver.currentDriverEvidence(),frame.observedAt());
                        original.batches().commitInitialNoDispatchRecovery(same,proof1,evidence);
                        admission.requireCurrent(same);controller.restoreInitialNoDispatchRecovery(same,proof1);
                        assertThrows(IllegalArgumentException.class,()->controller.restoreInitialNoDispatchRecovery(same,proof1));
                        assertThrows(IOException.class,()->proof0.requireCurrent(same));
                        assertArrayEquals(original.produced().driver().encode(),known.driver().encode());
                        assertArrayEquals(originalEntry,StrictJson.canonical(same.head().state().toJson().get(WriterContracts.GAMEPLAY_ENTRY_FIELD)));
                        assertEquals(0,same.head().state().settledCycles());assertEquals(53144328,same.head().state().settledDateRaw());
                        var ticket=controller.captureCleanRestart(same,proof1.batchPrefix(),proof1.nextBatchSequence());
                        var restored=original.batches().admitCleanRestart(same,ticket).controller();
                        assertEquals(Set.of("software-batch-0","software-batch-1"),restored.usedBatches());assertEquals(2,restored.nextBatchSequence());
                        assertFalse(restored.dirty());assertTrue(restored.unsavedGameplayActions().isEmpty());assertTrue(restored.savedPair().isEmpty());
                    }catch(InterruptedException interrupted){Thread.currentThread().interrupt();throw new IOException(interrupted);}
                    return null;
                });
            }
            assertEquals(4,peer.writes.get(),"two recoveries perform only three full READs and the original START; no action or SAVE");
        }
    }


    @Test void actualCleanCaptureThenOpenBatchPreservesKnownAndControllerWithoutRewindingEntry()throws Exception {
        capturedOpenBatchRecovery(false);
    }
    @Test void actualCapturedNativeFrontierRefusesAReadThatOnlyTheOldEntryWouldAccept()throws Exception {
        capturedOpenBatchRecovery(true);
    }
    @Test void actualCapturedRecoveryKeepsAdvancedUnsavedDateOnTheNextConnection()throws Exception {
        capturedOpenBatchRecovery(false,true);
    }
    private void capturedOpenBatchRecovery(boolean regressed)throws Exception {
        capturedOpenBatchRecovery(regressed,false);
    }
    private void capturedOpenBatchRecovery(boolean regressed,boolean advancedDate)throws Exception {
        String pipe="\\\\.\\pipe\\observed-entry-captured-open-"+UUID.randomUUID();
        var peer=advancedDate?new Peer(pipe,4,new long[]{1,3,5,7},new long[]{53144328,53144328,53144352,53144352})
                :new Peer(pipe,3,1,3,regressed?2:5);
        var advancedCapture=new AtomicReference<ContinuityBatchJournal.CleanRestartAdmission>();
        var generation=ManagedGameSession.generation(WindowsJobProcess.exactProcess(ProcessHandle.current().pid()));
        var launch=plan(peer.pipe);peer.start();
        try(peer) {
            Actual original;SessionIdentity owner;
            try(var first=NativeGameAttachment.attach(new NativeGameAttachment.Request(launch,generation,List.of(),128,32),deadline())) {
                original=actual(first);original.entry().retainCurrentMap(first,original.read(),original.produced(),original.driver());
                original.writer().locked(original.entry()::commitInitial);owner=new SessionIdentity(first.machineId(),first.generation(),first.sessionId());
                original.batches().commit(new JournalInput(owner,"software-batch-0",JournalKind.BATCH_STARTED,Optional.empty(),Optional.empty(),Optional.empty(),List.of()));
                original.batches().commit(new JournalInput(owner,"software-batch-0",JournalKind.BATCH_INTERRUPTED,Optional.empty(),Optional.empty(),Optional.empty(),List.of()));
            }
            ContinuityBatchJournal.CleanRestartAdmission baseline;
            try(var second=NativeGameAttachment.attach(new NativeGameAttachment.Request(launch,generation,List.of(),128,32),deadline())) {
                var issuer=new FreshGameplayEntryAuthority(original.writer(),original.archive());
                baseline=original.writer().locked(same->{
                    var proof=original.batches().admitInitialNoDispatchRecovery(same,owner);
                    var admission=issuer.admitRecovery(same,second,proof);
                    try {
                        var driver=DriverBootstrap.adoptInitialRecovery(admission,same,
                                new ActionSnapshotReader(new ContinuityActionJournal(original.writer(),original.archive())),
                                second.nativeTransport(),original.driver().source(),original.archive(),8,deadline());
                        original.batches().commitInitialNoDispatchRecovery(same,proof,recoverySemantic(original,same,driver));
                        var controller=initialRecoveryController(original,owner,driver);controller.restoreInitialNoDispatchRecovery(same,proof);
                        var ticket=controller.captureCleanRestart(same,proof.batchPrefix(),proof.nextBatchSequence());
                        return original.batches().admitCleanRestart(same,ticket);
                    }catch(InterruptedException interrupted){Thread.currentThread().interrupt();throw new IOException(interrupted);}
                });
            }
            assertEquals(BigInteger.valueOf(3),baseline.manifest().nativeRevision());
            assertEquals(Set.of("software-batch-0"),baseline.controller().usedBatches());
            original.batches().commit(new JournalInput(owner,"software-batch-1",JournalKind.BATCH_STARTED,Optional.empty(),Optional.empty(),Optional.empty(),List.of()));
            try(var third=NativeGameAttachment.attach(new NativeGameAttachment.Request(launch,generation,List.of(),128,32),deadline())) {
                var issuer=new FreshGameplayEntryAuthority(original.writer(),original.archive());
                original.writer().locked(same->{
                    assertThrows(IOException.class,()->baseline.requireCurrent(same));
                    var proof=original.batches().admitInitialNoDispatchRecovery(same,owner);
                    assertEquals(baseline.manifest(),proof.capturedManifest().orElseThrow());
                    assertEquals(baseline.controller(),proof.capturedController().orElseThrow());
                    assertArrayEquals(DriverSnapshotFacts.encodeKnownOriginal(baseline.facts()).bytes(),DriverSnapshotFacts.encodeKnownOriginal(proof.capturedFacts().orElseThrow()).bytes());
                    assertEquals(List.of("software-batch-0","software-batch-1"),proof.consumedBatchIds());assertEquals(2,proof.nextBatchSequence());
                    var admission=issuer.admitRecovery(same,third,proof);
                    assertArrayEquals(DriverSnapshotFacts.encodeKnownOriginal(baseline.facts()).bytes(),DriverSnapshotFacts.encodeKnownOriginal(admission.facts()).bytes());
                    String before=same.head().digest();
                    if(regressed) {
                        assertThrows(IllegalArgumentException.class,()->DriverBootstrap.adoptInitialRecovery(admission,same,
                                new ActionSnapshotReader(new ContinuityActionJournal(original.writer(),original.archive())),
                                third.nativeTransport(),baseline.manifest().source(),original.archive(),8,deadline()));
                        assertEquals(before,same.head().digest());
                        assertEquals("BATCH_STARTED",same.head().state().toJson().path(WriterContracts.ORDINARY_BATCH_BOUNDARY_FIELD).path("boundary").textValue());
                        return null;
                    }
                    try {
                        var driver=DriverBootstrap.adoptInitialRecovery(admission,same,
                                new ActionSnapshotReader(new ContinuityActionJournal(original.writer(),original.archive())),
                                third.nativeTransport(),baseline.manifest().source(),original.archive(),8,deadline());
                        driver.requireInitialNoDispatchRecovery(proof);
                        var known=driver.authority().withFrozenFacts(same,frozen->(DriverSnapshotFacts.Known)frozen.state());
                        assertArrayEquals(baseline.facts().driver().encode(),known.driver().encode());
                        assertEquals(baseline.facts().stamp(),known.stamp());assertEquals(baseline.facts().actionRows(),known.actionRows());
                        assertEquals(baseline.facts().auxiliary(),known.auxiliary());assertEquals(baseline.facts().loop(),known.loop());
                        assertEquals(baseline.manifest().source(),driver.source());
                        assertEquals(BigInteger.valueOf(5),driver.first().identity().frame().identity().nativeRevision());
                        assertEquals(BigInteger.valueOf(advancedDate?53144352:53144328),driver.first().identity().frame().identity().dateRaw());
                        var controller=initialRecoveryController(original,owner,driver);
                        assertThrows(IllegalArgumentException.class,()->controller.restoreInitialNoDispatchRecovery(same,proof));
                        var evidence=recoverySemantic(original,same,driver);
                        original.batches().commitInitialNoDispatchRecovery(same,proof,evidence);
                        admission.requireCurrent(same);
                        var retainedProof=original.batches().admitInitialNoDispatchRecovery(same,owner);
                        retainedProof.requireCurrent(same);
                        assertEquals(List.of("software-batch-0","software-batch-1"),retainedProof.consumedBatchIds());
                        assertEquals(2,retainedProof.nextBatchSequence());
                        assertEquals(baseline.manifest(),retainedProof.capturedManifest().orElseThrow());
                        assertEquals(baseline.controller(),retainedProof.capturedController().orElseThrow());
                        assertArrayEquals(DriverSnapshotFacts.encodeKnownOriginal(baseline.facts()).bytes(),DriverSnapshotFacts.encodeKnownOriginal(retainedProof.capturedFacts().orElseThrow()).bytes());
                        assertThrows(IllegalArgumentException.class,()->controller.restoreInitialNoDispatchRecovery(same,retainedProof));
                        var headSeq=same.head().state().sequence();var headDigest=same.head().digest();var persistedHead=same.persistedHead();var writesBefore=peer.writes.get();
                        original.batches().finishInitialNoDispatchRecovery(same,retainedProof,evidence);
                        assertEquals(headSeq,same.head().state().sequence());
                        assertEquals(headDigest,same.head().digest());
                        assertEquals(persistedHead,same.persistedHead());
                        assertEquals(writesBefore,peer.writes.get());
                        var controller2=initialRecoveryController(original,owner,driver);
                        controller2.restoreInitialNoDispatchRecovery(same,retainedProof);
                        assertThrows(IllegalArgumentException.class,()->controller2.restoreInitialNoDispatchRecovery(same,retainedProof));
                        var ticket=controller2.captureCleanRestart(same,retainedProof.batchPrefix(),retainedProof.nextBatchSequence());
                        var captured=original.batches().admitCleanRestart(same,ticket);advancedCapture.set(captured);
                        var restored=captured.controller();var retained=baseline.controller();
                        assertEquals(Set.of("software-batch-0","software-batch-1"),restored.usedBatches());assertEquals(2,restored.nextBatchSequence());
                        assertEquals(retained.owner(),restored.owner());assertEquals(retained.batchPrefix(),restored.batchPrefix());
                        assertEquals(retained.unsavedGameplayActions(),restored.unsavedGameplayActions());assertEquals(retained.savedPair(),restored.savedPair());
                        assertEquals(retained.eligibleSinceSave(),restored.eligibleSinceSave());assertEquals(retained.dirty(),restored.dirty());
                        assertEquals(retained.quarantined(),restored.quarantined());assertEquals(retained.localUnresolved(),restored.localUnresolved());
                        assertEquals(retained.totalCommittedDays(),restored.totalCommittedDays());assertEquals(retained.completedAnalysisIds(),restored.completedAnalysisIds());
                        assertEquals(retained.stopRequested(),restored.stopRequested());
                        assertEquals(0,same.head().state().settledCycles());assertEquals(53144328,same.head().state().settledDateRaw());
                    }catch(InterruptedException interrupted){Thread.currentThread().interrupt();throw new IOException(interrupted);}
                    return null;
                });
            }
            if(advancedDate) {
                var current=advancedCapture.get();assertNotNull(current);
                assertEquals(53144352,current.manifest().dateRaw());
                assertEquals(0,current.controller().totalCommittedDays());
                original.batches().commit(new JournalInput(owner,"software-batch-2",JournalKind.BATCH_STARTED,Optional.empty(),Optional.empty(),Optional.empty(),List.of()));
                try(var fourth=NativeGameAttachment.attach(new NativeGameAttachment.Request(launch,generation,List.of(),128,32),deadline())) {
                    var issuer=new FreshGameplayEntryAuthority(original.writer(),original.archive());
                    original.writer().locked(same->{
                        assertEquals(53144328,same.head().state().settledDateRaw());
                        var proof=original.batches().admitInitialNoDispatchRecovery(same,owner);
                        assertEquals(current.manifest(),proof.capturedManifest().orElseThrow());
                        assertEquals(53144352,proof.capturedManifest().orElseThrow().dateRaw());
                        assertEquals(List.of("software-batch-0","software-batch-1","software-batch-2"),proof.consumedBatchIds());
                        assertEquals(3,proof.nextBatchSequence());
                        var admission=issuer.admitRecovery(same,fourth,proof);
                        try {
                            var driver=DriverBootstrap.adoptInitialRecovery(admission,same,
                                    new ActionSnapshotReader(new ContinuityActionJournal(original.writer(),original.archive())),
                                    fourth.nativeTransport(),current.manifest().source(),original.archive(),8,deadline());
                            driver.requireInitialNoDispatchRecovery(proof);
                            var known=driver.authority().withFrozenFacts(same,frozen->(DriverSnapshotFacts.Known)frozen.state());
                            assertArrayEquals(current.facts().driver().encode(),known.driver().encode());
                            assertEquals(current.facts().stamp(),known.stamp());assertEquals(current.facts().originalHistoryBasis(),known.originalHistoryBasis());
                            assertEquals(current.facts().actionRows(),known.actionRows());assertEquals(current.facts().auxiliary(),known.auxiliary());
                            assertEquals(current.facts().loop(),known.loop());
                            assertEquals(BigInteger.valueOf(53144352),driver.first().identity().frame().identity().dateRaw());
                            assertEquals(BigInteger.valueOf(7),driver.first().identity().frame().identity().nativeRevision());
                            original.batches().finishInitialNoDispatchRecovery(same,proof,recoverySemantic(original,same,driver));
                            admission.requireCurrent(same);
                            var controller=initialRecoveryController(original,owner,driver);controller.restoreInitialNoDispatchRecovery(same,proof);
                            var ticket=controller.captureCleanRestart(same,proof.batchPrefix(),proof.nextBatchSequence());
                            var captured=original.batches().admitCleanRestart(same,ticket);
                            var restored=captured.controller();var retained=current.controller();
                            assertEquals(Set.of("software-batch-0","software-batch-1","software-batch-2"),restored.usedBatches());
                            assertEquals(3,restored.nextBatchSequence());
                            assertEquals(retained.owner(),restored.owner());assertEquals(retained.batchPrefix(),restored.batchPrefix());
                            assertEquals(retained.unsavedGameplayActions(),restored.unsavedGameplayActions());assertEquals(retained.savedPair(),restored.savedPair());
                            assertEquals(retained.eligibleSinceSave(),restored.eligibleSinceSave());assertEquals(retained.dirty(),restored.dirty());
                            assertEquals(retained.quarantined(),restored.quarantined());assertEquals(retained.localUnresolved(),restored.localUnresolved());
                            assertEquals(retained.totalCommittedDays(),restored.totalCommittedDays());assertEquals(retained.completedAnalysisIds(),restored.completedAnalysisIds());
                            assertEquals(retained.stopRequested(),restored.stopRequested());
                            assertEquals(53144352,captured.manifest().dateRaw());assertEquals(0,same.head().state().settledCycles());
                            assertEquals(53144328,same.head().state().settledDateRaw());
                        }catch(InterruptedException interrupted){Thread.currentThread().interrupt();throw new IOException(interrupted);}
                        return null;
                    });
                }
            }
            assertEquals(advancedDate?5:4,peer.writes.get(),"captured open-batch recovery never repeats START, SAVE or an action");
        }
    }
    private SemanticEvidence recoverySemantic(Actual original,ContinuityStorePort.Session same,DriverBootstrap.Adopted driver)throws IOException {
        var known=driver.authority().withFrozenFacts(same,frozen->(DriverSnapshotFacts.Known)frozen.state());
        var frame=driver.first();var archive=original.archive().withSession(same);
        var semantic=archive.preserveMaterial(new RawJson(DriverJson.encode(frame.semantic())));
        var stamp=archive.preserveMaterial(new RawJson(NativeDriverStamp.encode(frame,known)));
        return new SemanticEvidence(frame.identity(),semantic,frame.originalEvidence(),stamp,driver.currentDriverEvidence(),frame.observedAt());
    }

    private SessionController initialRecoveryController(Actual actual,SessionIdentity owner,DriverBootstrap.Adopted driver) {
        CheckpointFiles files=new CheckpointFiles() {
            public Optional<CheckpointPair.FileWitness> observe(Path path){throw new AssertionError("no SAVE inspection");}
            public byte[] read(CheckpointPair.FileWitness witness,int maximum){throw new AssertionError("no SAVE read");}
            public CheckpointPair.FileWitness replace(Path path,byte[] bytes){throw new AssertionError("no SAVE write");}
            public CheckpointPair.FileWitness createNew(Path path,byte[] bytes){throw new AssertionError("no SAVE create");}
            public CheckpointPair.FileWitness copyNew(CheckpointPair.FileWitness witness,Path path){throw new AssertionError("no SAVE copy");}
        };
        var snapshot=new DriverCheckpointStore.SnapshotSupplier(){
            public <T>T withFrozen(DriverCheckpointStore.SnapshotWork<T> work){throw new AssertionError("no checkpoint supplier");}
        };
        var drivers=new DriverCheckpointStore(files,root.resolve("unused-driver.json"),"unused-pipe",snapshot);
        CheckpointRequest.ObservationPort readiness=until->{throw new AssertionError("no SAVE preparation");};
        var checkpoints=new CheckpointService(files,drivers,readiness,root.resolve("unused-checkpoints"),Clock.systemUTC(),
                (pair,receipt)->{throw new AssertionError("no SAVE adoption");});
        var completion=new OrdinaryPlanCompletion.PlanningScope(){
            public <T>ScopeResult<T> inPlanningScope(ScopeWork<T> work)throws IOException,InterruptedException{return new ScopeResult<>(work.run(),Optional.empty());}
            public PlanningDisposition afterPlanning(org.xar.ck3.control.application.planning.PlanningRequest original,org.xar.ck3.control.application.planning.PlanningResult planned){throw new AssertionError("no plan");}
            public ExecutionDisposition afterExecution(ActionReceipt receipt){throw new AssertionError("no execute");}
        };
        var commands=new ActionCoordinatorPort(){
            public ActionReceipt execute(ActionCommand command){throw new AssertionError("no dispatch");}
            public ActionReceipt reconcile(String action){throw new AssertionError("no replay");}
        };
        var controller=new SessionController(owner,(identity,until)->new GameLifecycle.Running(owner.game(),driver.currentDriverEvidence()),
                (identity,until)->{throw new AssertionError("no new observation");},
                new org.xar.ck3.control.application.planning.OrdinaryPlanner(List.of(),Clock.systemUTC(),
                        new org.xar.ck3.control.application.planning.campaign.M7CampaignPolicies.RealmLifecycle(driver.source().sourceRef())),
                commands,checkpoints,new CheckpointRequestFactory(root.resolve("unused.ck3"),readiness),actual.batches(),
                input->{throw new AssertionError("no new incident");},new SessionClock.SystemClock(),Optional.empty(),0,completion,
                (identity,parent,until)->{throw new AssertionError("no episode continuation");});
        controller.bindRetainedIncidents(List::of);controller.bindRestartDriver(driver.authority());return controller;
    }

    private InitialEpisodePolicy configuredOrdinaryPolicy() throws IOException {
        Path configDir = Files.createDirectory(root.resolve("config"));
        Path policyFile = configDir.resolve("policy.json");
        var lifecycleNode = NativeColdAdoptionProjection.Lifecycle.ordinaryVanilla().toJson();
        var policyRoot = StrictJson.object();
        policyRoot.set("succession_lifecycle", lifecycleNode);
        Files.write(policyFile, StrictJson.canonical(policyRoot));

        Path configFile = configDir.resolve("runtime.json");
        var configRoot = StrictJson.object();
        configRoot.put("schema", "xar.java-ordinary-runtime-configuration/v1");
        configRoot.put("machine_id", WindowsJobProcess.currentMachineId());
        configRoot.put("state_dir", root.resolve("state").toString());
        configRoot.put("stock_game_root", root.resolve("stock").toString());
        configRoot.put("native_implementation", root.resolve("native.dll").toString());
        configRoot.put("launch_plan_file", root.resolve("launch.json").toString());
        configRoot.put("initial_policy_file", policyFile.toString());
        configRoot.put("campaign_deadline_file", root.resolve("deadline.json").toString());
        configRoot.put("formal_war_budget", root.resolve("budget.json").toString());
        configRoot.put("formal_war_model", root.resolve("model.json").toString());
        var buildNode = StrictJson.object();
        buildNode.put("version", "1.20.0.4");
        buildNode.put("exe_sha256", SHA);
        configRoot.set("configured_build", buildNode);
        configRoot.put("authority_id", "test-authority");
        Files.write(configFile, StrictJson.canonical(configRoot));

        var config = RootOrdinaryRuntimeConfiguration.read(configFile);
        return config.initialPolicy();
    }

    private static final class Peer implements AutoCloseable {
        final String pipe;final int connections;final long[] revisions,dates;final AtomicInteger writes=new AtomicInteger();final AtomicReference<Throwable> failure=new AtomicReference<>();Thread thread;
        Peer(String pipe){this(pipe,1);}
        Peer(String pipe,int connections){this(pipe,connections,1,1);}
        Peer(String pipe,int connections,long firstRevision,long secondRevision){this(pipe,connections,firstRevision,secondRevision,secondRevision);}
        Peer(String pipe,int connections,long firstRevision,long secondRevision,long thirdRevision){this(pipe,connections,new long[]{firstRevision,secondRevision,thirdRevision},new long[]{53144328,53144328,53144328});}
        Peer(String pipe,int connections,long[] revisions,long[] dates){
            if(connections<1||revisions.length<connections||dates.length<connections)throw new IllegalArgumentException("finite per-connection software observations required");
            this.pipe=pipe;this.connections=connections;this.revisions=revisions.clone();this.dates=dates.clone();
        }
        void start(){thread=new Thread(()->{try{run();}catch(Throwable thrown){failure.set(thrown);}},"first-map-software-peer");thread.setDaemon(true);thread.start();}
        void finish()throws Exception{thread.join(2000);assertFalse(thread.isAlive(),"software peer must finish");if(failure.get()!=null)throw new AssertionError(failure.get());}
        @Override public void close()throws Exception{finish();}
        void run()throws Exception {
            for(int connection=1;connection<=connections;connection++){
            HANDLE client;Instant until=deadline();
            do{client=Kernel32.INSTANCE.CreateFile(pipe,0xC0000000,0,null,3,0,null);if(client!=null&&!WinBase.INVALID_HANDLE_VALUE.equals(client))break;Thread.sleep(10);}while(Instant.now().isBefore(until));
            if(client==null||WinBase.INVALID_HANDLE_VALUE.equals(client))throw new IOException("software peer connection timeout");
            try {
                var hello=StrictJson.object().put("type","hello").put("protocol_version",1).put("pid",ProcessHandle.current().pid()).put("connection_generation",6+connection)
                        .put("bridge_version","entry-test").put("expected_ck3_sha256",SHA).put("expected_ck3_version","1.20.0.4").put("game_adapter_id",ADAPTER)
                        .put("game_adapter_status","ready").put("ck3_build_match",true);
                hello.putArray("capabilities").add("game.state.snapshot").add(NativeFreshSnapshotPort.CAPABILITY).add(Primitive.START_BOOKMARK.capability());write(client,hello);
                for(int i=connection==1?0:1;i<2;i++){
                    var request=(ObjectNode)StrictJson.parse(read(client),StrictJson.EXPLICIT_MAX_BYTES);writes.incrementAndGet();String id=StrictJson.text(request.get("request_id"));String step=StrictJson.text(request.get("step"));
                    var ack=StrictJson.object().put("type","command_result").put("protocol_version",1).put("request_id",id).put("ok",true);
                    if(i==0){if(!Primitive.START_BOOKMARK.operation().value().equals(step))throw new IOException("wrong real START");ack.putObject("result").put("step",step).put("accepted",true).put("status","acknowledged_verification_pending").put("backend_id","native-headless");}
                    else{
                        if(!NativeFreshSnapshotPort.STEP.equals(step))throw new IOException("wrong real full read");
                        long nativeRevision=revisions[connection-1];
                        var state=StrictJson.object().put("paused",true).put("map_ready",true).put("speed",3).put("date_raw",dates[connection-1]).put("one_life_terminal",false).put("episode_identity_pending",false);
                        state.putObject("played_character").put("character_id",73).put("alive",true);state.putNull("active_event").putNull("pending_character_interaction").putNull("one_life_terminal_reason");
                        state.putArray("active_wars");state.putArray("player_armies");state.putObject("diagnostics").put("bridge_pid",ProcessHandle.current().pid()).put("connection_generation",6+connection);
                        var snapshot=StrictJson.object().put("type","state_snapshot").put("protocol_version",1).put("snapshot_id","native:"+nativeRevision).put("revision",nativeRevision).put("read_request_id",id);snapshot.set("state",state);write(client,snapshot);
                        ack.putObject("result").put("schema",NativeFreshSnapshotPort.RESULT_SCHEMA).put("request_id",id).put("snapshot_id","native:"+nativeRevision).put("revision",nativeRevision);
                    }write(client,ack);
                }
            }finally{Kernel32.INSTANCE.CloseHandle(client);}
            }
        }
        private static byte[] read(HANDLE client)throws IOException{byte[] prefix=read(client,4);int count=ByteBuffer.wrap(prefix).order(ByteOrder.LITTLE_ENDIAN).getInt();if(count<1||count>1<<20)throw new IOException("software packet size");return read(client,count);}
        private static byte[] read(HANDLE client,int count)throws IOException{byte[] result=new byte[count];int offset=0;while(offset<count){byte[] rest=new byte[count-offset];var got=new IntByReference();if(!Kernel32.INSTANCE.ReadFile(client,rest,rest.length,got,null)||got.getValue()<1)throw new IOException("software read "+Kernel32.INSTANCE.GetLastError());System.arraycopy(rest,0,result,offset,got.getValue());offset+=got.getValue();}return result;}
        private static void write(HANDLE client,ObjectNode value)throws IOException{byte[] json=StrictJson.canonical(value);byte[] packet=ByteBuffer.allocate(4+json.length).order(ByteOrder.LITTLE_ENDIAN).putInt(json.length).put(json).array();int offset=0;while(offset<packet.length){byte[] rest=Arrays.copyOfRange(packet,offset,packet.length);var sent=new IntByReference();if(!Kernel32.INSTANCE.WriteFile(client,rest,rest.length,sent,null)||sent.getValue()<1)throw new IOException("software write "+Kernel32.INSTANCE.GetLastError());offset+=sent.getValue();}}
    }
}
