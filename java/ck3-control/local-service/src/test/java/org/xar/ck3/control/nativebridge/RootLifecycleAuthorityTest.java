package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.continuity.writer.WriterContracts.*;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayDeque;
import java.util.Arrays;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.effects.OriginalEvidencePort;
import org.xar.ck3.control.application.driver.*;
import org.xar.ck3.control.application.readiness.NativeReadinessCollector;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.service.root.*;

/** Original packet decoder -> actual Driver producer -> sole writer/archive -> terminal guards -> archived replay. No live package/Game grant. */
final class RootLifecycleAuthorityTest {
    @TempDir Path temporary;
    private static final String MACHINE="terminal-authority-fixture",PIPE="\\\\.\\pipe\\terminal-authority-fixture",SESSION="terminal-session";
    private static final String SHA="0".repeat(64);
    private static final GameGeneration GAME=new GameGeneration(42,new PythonOnlyUInt64(new BigInteger("9007199254740993")));
    private static final OperationKey READ=new OperationKey("query-current-timeline-blocker-context-v1");
    private enum Player { MISSING,NULL,DEAD,CHANGED,LIVING }
    private static byte[] bytes(String text){return text.getBytes(StandardCharsets.UTF_8);}
    private static byte[] packet(String text){try{return NativeWire.packet(bytes(text));}catch(IOException failure){throw new UncheckedIOException(failure);}}
    private static final class Replay implements NativePacketPort {
        final ArrayDeque<byte[]> incoming=new ArrayDeque<>();final Player player;final OperationKey readOperation;int reads,writes;boolean processChanged;String injectedState;
        Replay(Player player,OperationKey readOperation){this.player=player;this.readOperation=readOperation;incoming.add(packet("{\"type\":\"hello\",\"protocol_version\":1,\"pid\":42,\"connection_generation\":5,\"bridge_version\":\"terminal-fixture\",\"expected_ck3_sha256\":\""+SHA+"\",\"game_adapter_id\":\"fixture-adapter\",\"game_adapter_status\":\"ready\",\"ck3_build_match\":true,\"capabilities\":[\"game.state.snapshot\"]}"));incoming.add(packet("{\"type\":\"heartbeat\",\"protocol_version\":1,\"sequence\":1}"));}
        @Override public void awaitConnection(Instant deadline) { }
        @Override public void verify()throws IOException{if(processChanged)throw new IOException("actual held process was replaced");}
        @Override public byte[] readPacket(Instant deadline){reads++;return incoming.isEmpty()?packet("{\"type\":\"state_snapshot\",\"protocol_version\":1,\"snapshot_id\":\"terminal-snapshot-1\",\"revision\":7,\"state\":"+(injectedState==null?state(player):injectedState)+"}"):incoming.removeFirst();}
        @Override public void writePacket(byte[] framed,Instant deadline)throws IOException{writes++;var request=NativeWire.parse(Arrays.copyOfRange(framed,4,framed.length));assertEquals(readOperation.value(),NativeWire.text(request.get("step")));incoming.addFirst(packet("{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":\""+NativeWire.text(request.get("request_id"))+"\",\"ok\":true,\"result\":{\"actual_terminal_query\":true}}"));}
        @Override public void close() { }
    }
    private static String state(Player player){
        String current=switch(player){case MISSING->"";case NULL->"\"played_character\":null,";case DEAD->"\"played_character\":{\"character_id\":73,\"alive\":false},";case CHANGED->"\"played_character\":{\"character_id\":74,\"alive\":true},";case LIVING->"\"played_character\":{\"character_id\":73,\"alive\":true},";};
        return "{"+current+"\"paused\":true,\"map_ready\":true,\"speed\":1,\"date_raw\":1000,\"active_event\":null,\"pending_character_interaction\":null,\"one_life_terminal_reason\":null,\"one_life_terminal\":false,\"succession_reconciliation\":null,\"one_life_settlement\":null,\"active_wars\":[],\"player_armies\":[],\"diagnostics\":{\"bridge_pid\":42,\"connection_generation\":5}}";
    }
    private final class Fixture implements AutoCloseable {
        final Path root,sourceFile;final ExactRef reviewed;final G2Source source;final Replay packets;final NativeGameTransport transport;
        final ContinuityWriter writer;final NativeOutcomeArchive archive;final RootLifecycleAuthority authority;
        final StorageWriteGuardTestSupport storage;
        final OriginalEvidencePort originals;final RootLifecycleReadGuard guard;final ReadContract<RawJson> contract;
        final PlanningReadCoordinator queries;final AtomicInteger sourceChecks=new AtomicInteger();
        Fixture(Path root,Player player)throws IOException{this(root,player,READ,false);}
        Fixture(Path root,Player player,OperationKey readOperation)throws IOException{this(root,player,readOperation,false);}
        Fixture(Path root,Player player,OperationKey readOperation,boolean fullDriver)throws IOException{
            this.root=root;Files.createDirectory(root);sourceFile=root.resolve("source.java");Files.writeString(sourceFile,"actual finite software fixture source",StandardOpenOption.CREATE_NEW);reviewed=ref(sourceFile);
            var driverFile=root.resolve("driver.json");var driver=StrictJson.object();driver.put("format_version",2);driver.put("pipe_name",PIPE);driver.put("bridge_pid",42);driver.put("episode_character_id",73);driver.put("episode_run_id","old-episode");driver.putNull("last_checkpoint");var history=driver.putArray("command_history");for(String key:List.of("rollback_war_failure","managed_restore_transaction","succession_expectation","campaign_goal"))driver.putNull(key);
            if(fullDriver){var entry=history.addObject();entry.put("index",1);entry.put("command","retained-full-driver");entry.put("ok",false);entry.put("full_counter",new java.math.BigInteger("9".repeat(7000)));}
            Files.write(driverFile,DriverJson.encode(DriverJson.fromNode(driver)),StandardOpenOption.CREATE_NEW);ExactRef originalDriver=ref(driverFile);
            var seed=StrictJson.object();seed.put("schema","root.ck3.continuity-window/v1");seed.put("machine_id",MACHINE);seed.put("sequence",0);seed.put("window_id",1);seed.put("status","running");seed.put("target_days",10958);seed.put("target_years",30);seed.put("calendar_year_days",365.25);seed.put("start_date_raw",1000);seed.put("target_date_raw",263992);seed.put("last_settled_date_raw",1000);seed.put("last_settled_cycles",0);seed.put("manual_repair_count",0);seed.put("automatic_recovery_count",0);seed.put("binding_lineage_count",0);var game=seed.putObject("game_binding");game.put("pid",42);game.put("creation_date","2026-10-24T00:00:00Z");seed.putNull("latest_binding");seed.putNull("pending_cycle");seed.put("NEXT",1);seed.set("java_driver_history_baseline",originalDriver.toJson());
            byte[] initial=ContinuityJson.canonical(seed);Path snapshot=root.resolve("ROOT-CONTINUITY-WINDOW.json"),anchor=root.resolve("anchor.json");Files.write(snapshot,initial,StandardOpenOption.CREATE_NEW);Files.write(anchor,initial,StandardOpenOption.CREATE_NEW);Files.write(root.resolve("ROOT-CONTINUITY-WINDOW.lock"),new byte[0],StandardOpenOption.CREATE_NEW);Files.createDirectory(root.resolve("ROOT-CONTINUITY-WINDOW-EVENTS"));Files.createDirectory(root.resolve("artifacts"));
            var layout=new Layout(snapshot,ref(anchor),MACHINE);storage=StorageWriteGuardTestSupport.create(layout);
            var artifacts=new ImmutableArtifactStore(new ImmutableArtifactStore.Config(root.resolve("artifacts"),layout.lock(),8<<20),storage);
            writer=new ContinuityWriter(layout,List.of(reviewed),new TransitionAuthority(){@Override public String revalidate(ContinuityState old,Request request){throw new AssertionError("terminal read regression cannot commit");}@Override public ContinuityState reduce(ContinuityState old,Request request){throw new AssertionError("terminal read regression cannot reduce");}},Clock.systemUTC(),new ContinuityWriter.Extensions(List.of(),Optional.of(artifacts),Optional.empty()),storage);
            assertSame(storage,artifacts.storageGuard());assertSame(storage,writer.storageGuard());
            archive=new NativeOutcomeArchive(artifacts,writer);source=new G2Source(MACHINE,Instant.now().toString(),"software-fixture",reviewed);packets=new Replay(player,readOperation);transport=new NativeGameTransport(packets,new NativePipeEndpoint.Config(PIPE,MACHINE,GAME,SESSION,"terminal-fixture",SHA,"fixture-adapter"),32,64);
            var repository=new DriverFactsRepository(DriverFactsRepository.imported(originalDriver,Files.readAllBytes(driverFile),1,2,GAME,new OpportunityJson.Obj(fullDriver?Map.of("full_original_progress",new OpportunityJson.IntegerValue(new BigInteger("9".repeat(7000)))):Map.of())));
            var journal=new ContinuityActionJournal(writer,archive);var producer=new NativeDriverObservationProducer(repository,transport,source,raw->archive.preserveMaterial(RawJson.fullMaterial(raw)));
            var assembler=new DriverStateAssembler(new ActionSnapshotReader(journal),repository,producer);
            assembler.bindCapabilityObservation((actual,current)->{throw new AssertionError("physical snapshot must skip every capability/domain observation hook");});
            authority=new RootLifecycleAuthority(writer,archive,transport,assembler,new DriverObservationAssembler(),source,(same,held,actualSource,origin,diagnostics,deadline)->{
                writer.requireSession(same);assertEquals(source,actualSource);assertEquals(held,diagnostics.session().orElseThrow());archive.readArtifact(same,origin,MAX_PIN_BYTES);
                var pin=same.capturePin(reviewed,65536);same.verifyPin(pin);var body=StrictJson.object();body.put("schema","xar.java-root-native-source-proof/v2");body.put("machine_id",MACHINE);body.put("session_id",SESSION);body.set("source",reviewed.toJson());body.put("scope","software-fixture-only-no-live-package-grant");var proof=archive.preserveArtifact(same,StrictJson.canonical(body,65536),65536);
                return new NativeReadinessCollector.SourceQualification(proof,current->{writer.requireSession(current);assertSame(same,current);current.verifyPin(pin);sourceChecks.incrementAndGet();});
            },Clock.systemUTC(),Duration.ofSeconds(30));
            originals=(same,original,maximum)->archive.readArtifact(same,original,maximum);
            contract=new ReadContract<>("terminal-fixture/v1",readOperation,Optional.empty(),"terminal-fixture",ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE,ReadContract.WireProfile.G2_PRIVATE_QUERY,ReadContract.GuardMode.LIFECYCLE_TERMINAL_SESSION,reviewed,request->new NativeRequest(readOperation.value(),Optional.empty(),new RawJson(bytes("{}"))),receipt->receipt.original().originalResultToken().orElseThrow());
            var catalog=RootReadContractCatalog.staticOnly(List.of(contract));guard=new RootLifecycleReadGuard(authority,()->{try{return writer.borrowedSession();}catch(IOException error){throw new UncheckedIOException(error);}},archive,source,Clock.systemUTC(),"root-terminal-test",originals,catalog);
            queries=new PlanningReadCoordinator(catalog,journal,guard,transport,archive,Clock.systemUTC());
        }
        @Override public void close()throws IOException{
            try(storage){transport.close();}
        }
    }
    private static ExactRef ref(Path path)throws IOException{byte[] raw=Files.readAllBytes(path);return new ExactRef(path.toAbsolutePath().toString(),raw.length,ActionCodec.sha256(raw));}
    private static PlanningReadRequest request(Fixture f,LifecycleIdentity origin){return new PlanningReadRequest(new CommandOrigin.LifecycleTerminal(origin),f.source,SESSION,f.contract.operation(),new OpportunityJson.Obj(Map.of()),Instant.now().plusSeconds(20));}
    @Test void allRealTerminalPlayerTokensKeepOldDriverAndProducePhysicalArchivedGuards()throws Exception{
        for(Player player:List.of(Player.MISSING,Player.NULL,Player.DEAD,Player.CHANGED))try(Fixture f=new Fixture(temporary.resolve(player.name()),player,READ,player==Player.CHANGED)){
            AtomicReference<RootLifecycleAuthority.Lease> escaped=new AtomicReference<>();
            AtomicReference<GuardEvidence> retained=new AtomicReference<>();
            f.writer.locked(same->f.authority.withObserved(same,Instant.now().plusSeconds(20),lease->{
                escaped.set(lease);
                assertEquals(BigInteger.valueOf(73),lease.identity().subject().characterId());assertEquals("old-episode",lease.identity().subject().episodeRunId());assertEquals(2,lease.identity().subject().episodeEpoch());assertEquals(GAME,lease.identity().game());
                assertEquals(switch(player){case MISSING,NULL->LifecycleIdentity.TerminalReason.MISSING;case DEAD->LifecycleIdentity.TerminalReason.DEAD;case CHANGED->LifecycleIdentity.TerminalReason.CHANGED;default->throw new AssertionError();},lease.identity().terminalReason());

                // Verify Identity Branch Distinction
                if (player == Player.MISSING) assertTrue(lease.identity().currentPlayer() instanceof LifecycleIdentity.Missing);
                if (player == Player.NULL) assertTrue(lease.identity().currentPlayer() instanceof LifecycleIdentity.Null);

                // Verify Canonical Semantic Presence
                var semantic = lease.snapshot().semantic();
                if (player == Player.MISSING || player == Player.NULL) {
                    assertTrue(semantic.members().containsKey("played_character"));
                    assertEquals(OpportunityJson.Nil.INSTANCE, semantic.get("played_character"));
                }

                // Verify Codec Roundtrip
                var encoded = LifecycleIdentityCodec.encode(lease.identity());
                var bytes = StrictJson.canonical(encoded, 65536);
                var decoded = LifecycleIdentityCodec.decode(StrictJson.parse(bytes, 65536));
                assertEquals(lease.identity(), decoded);

                assertEquals(LifecycleOriginFactory.currentPlayer(DriverJson.object(lease.snapshot().actual().state().bytes(),DriverJson.MAX_NATIVE_BYTES)),lease.identity().currentPlayer());
                int reads=f.packets.reads;var binding=f.guard.verify(same.head(),request(f,lease.identity()),f.contract);assertEquals(reads,f.packets.reads,"nested terminal guard must not replace outer native/Driver observation");
                retained.set(binding.binding());
                assertInstanceOf(PlanningReadGuard.LifecycleTerminal.class,binding.readiness());assertThrows(IllegalStateException.class,binding::playerAlive);
                var replay=RootLifecycleGuardEvidence.replay(binding.binding(),f.archive.withSession(same),same,f.originals);assertEquals(lease.identity(),replay.identity());assertEquals(lease.snapshot().semantic(),replay.semantic());assertFalse(replay.closeAdmission().isPresent());assertEquals(0,same.head().state().sequence());lease.assertCurrent(same);return null;
            }));
            f.writer.locked(same->{assertThrows(IllegalArgumentException.class,()->escaped.get().assertCurrent(same));return null;});

            // Cold Replay Verification
            int readsBefore = f.packets.reads;
            int writesBefore = f.packets.writes;
            f.writer.locked(same->{
                var replay=RootLifecycleGuardEvidence.replay(retained.get(),f.archive.withSession(same),same,f.originals);
                assertEquals(escaped.get().identity(),replay.identity());
                assertEquals(escaped.get().snapshot().semantic(),replay.semantic());
                assertEquals(0,same.head().state().sequence());
                return null;
            });
            assertEquals(readsBefore, f.packets.reads, "cold replay must not read native");
            assertEquals(writesBefore, f.packets.writes, "cold replay must not write native");
            assertTrue(f.sourceChecks.get()>2);assertEquals(0,f.packets.writes);
        }
    }

    @Test void forgedFullSnapshotDataIsRejectedByLifecycleOriginFactory() throws Exception {
        try(Fixture f=new Fixture(temporary.resolve("forged-data"),Player.CHANGED,READ,false)){
            f.writer.locked(same->f.authority.withObserved(same,Instant.now().plusSeconds(20),lease->{
                var observed = lease.snapshot();
                var actual = observed.actual();
                var facts = lease.freshFacts();
                var evidence = observed.originalEvidence();

                // Reproduce valid FullSnapshot
                var full = new DriverObservationAssembler().projectFull(actual, facts, evidence);

                // Verify valid projection works
                var validResult = LifecycleOriginFactory.project(full, lease.originalHello(), lease.identity().evidence().originalDriver(), lease.identity().evidence().completeSourceQualification());
                assertTrue(validResult instanceof LifecycleOriginFactory.Projected);
                assertEquals(lease.identity(), ((LifecycleOriginFactory.Projected)validResult).identity());

                // Forge 1: Change speed
                var members1 = new java.util.LinkedHashMap<>(full.semantic().members());
                members1.put("speed", new OpportunityJson.IntegerValue(BigInteger.TWO));
                var forged1 = new DriverObservationAssembler.FullSnapshot(actual, facts, new OpportunityJson.Obj(members1), evidence, DriverObservationAssembler.bindingSha256(new OpportunityJson.Obj(members1)));
                var res1 = LifecycleOriginFactory.project(forged1, lease.originalHello(), lease.identity().evidence().originalDriver(), lease.identity().evidence().completeSourceQualification());
                assertTrue(res1 instanceof LifecycleOriginFactory.Unavailable);

                // Forge 2: Remove played_character
                var members2 = new java.util.LinkedHashMap<>(full.semantic().members());
                members2.remove("played_character");
                var forged2 = new DriverObservationAssembler.FullSnapshot(actual, facts, new OpportunityJson.Obj(members2), evidence, DriverObservationAssembler.bindingSha256(new OpportunityJson.Obj(members2)));
                var res2 = LifecycleOriginFactory.project(forged2, lease.originalHello(), lease.identity().evidence().originalDriver(), lease.identity().evidence().completeSourceQualification());
                assertTrue(res2 instanceof LifecycleOriginFactory.Unavailable);

                // Forge 3: Change played_character to Bool
                var members3 = new java.util.LinkedHashMap<>(full.semantic().members());
                members3.put("played_character", new OpportunityJson.Bool(true));
                var forged3 = new DriverObservationAssembler.FullSnapshot(actual, facts, new OpportunityJson.Obj(members3), evidence, DriverObservationAssembler.bindingSha256(new OpportunityJson.Obj(members3)));
                var res3 = LifecycleOriginFactory.project(forged3, lease.originalHello(), lease.identity().evidence().originalDriver(), lease.identity().evidence().completeSourceQualification());
                assertTrue(res3 instanceof LifecycleOriginFactory.Unavailable);
                assertEquals(0,same.head().state().sequence());assertEquals(0,f.packets.writes);
                return null;
            }));
        }
    }
    @Test void completeDriverAndManifestReachFreshTerminalAuthorityAndColdGuardReplay()throws Exception{
        try(Fixture f=new Fixture(temporary.resolve("full-terminal-originals"),Player.CHANGED,READ,true)){
            var retained=new AtomicReference<GuardEvidence>();
            f.writer.locked(same->f.authority.withObserved(same,Instant.now().plusSeconds(20),lease->{
                assertEquals(BigInteger.valueOf(73),lease.identity().subject().characterId());
                assertEquals(new LifecycleIdentity.Character(BigInteger.valueOf(74),true),lease.identity().currentPlayer());
                assertEquals("old-episode",lease.identity().subject().episodeRunId());assertEquals(GAME,lease.identity().game());assertEquals(SESSION,lease.identity().sessionId());
                byte[] originalDriver=f.originals.read(same,lease.identity().evidence().originalDriver(),MAX_PIN_BYTES);
                byte[] manifest=f.originals.read(same,lease.identity().evidence().observationManifest(),MAX_PIN_BYTES);
                assertThrows(IllegalArgumentException.class,()->new RawJson(originalDriver));
                assertThrows(IllegalArgumentException.class,()->new RawJson(manifest));
                assertThrows(IllegalArgumentException.class,()->RawJson.fullMaterial(originalDriver).requireProtocolBound());
                var driverBody=DriverJson.object(originalDriver,DriverJson.MAX_NATIVE_BYTES);
                var entry=OpportunityJson.object(OpportunityJson.array(driverBody.get("command_history"),"complete original history").getFirst(),"original history row");
                assertEquals(7000,OpportunityJson.integer(entry.get("full_counter"),"complete original counter").toString().length());
                assertEquals(7000,OpportunityJson.integer(lease.snapshot().semantic().get("full_original_progress"),"complete semantic counter").toString().length());
                var guard=f.guard.verify(same.head(),request(f,lease.identity()),f.contract).binding();retained.set(guard);
                var replay=RootLifecycleGuardEvidence.replay(guard,f.archive.withSession(same),same,f.originals);
                assertEquals(lease.identity(),replay.identity());assertEquals(lease.snapshot().semantic(),replay.semantic());
                assertEquals(0,same.head().state().sequence());assertEquals(0,f.packets.writes);lease.assertCurrent(same);return null;
            }));
            int reads=f.packets.reads,writes=f.packets.writes;
            f.writer.locked(same->{
                var replay=RootLifecycleGuardEvidence.replay(retained.get(),f.archive.withSession(same),same,f.originals);
                assertEquals(retained.get().origin().requireLifecycleTerminal(),replay.identity());
                assertEquals(7000,OpportunityJson.integer(replay.semantic().get("full_original_progress"),"cold complete semantic counter").toString().length());
                assertEquals(reads,f.packets.reads);assertEquals(writes,f.packets.writes);assertEquals(0,same.head().state().sequence());return null;
            });
        }
    }
    @Test void closingTheLifecycleConsumerReleasesItsOriginalStorageAfterActualArchiveWrites()throws Exception{
        Fixture f=new Fixture(temporary.resolve("closed-storage"),Player.DEAD);
        try(f){
            f.writer.locked(same->f.authority.withObserved(same,Instant.now().plusSeconds(20),lease->null));
            assertTrue(f.storage.successfulBatches()>0);assertFalse(f.storage.hasUnknownWrite());
        }
        assertThrows(IOException.class,()->StorageWriteGuardTestSupport.forOriginalLock(f.storage.originalLock()));
        int writes=f.packets.writes;
        assertThrows(IOException.class,()->f.writer.locked(same->f.archive.preserveArtifact(same,
                bytes("closed lifecycle consumer"),65536)));
        assertEquals(writes,f.packets.writes);assertFalse(f.storage.hasUnknownWrite());
    }
    @Test void actualQueryProducerAndRegisteredTerminalConsumerShareOneFrozenScopeAndRoundTrip()throws Exception{
        try(Fixture f=new Fixture(temporary.resolve("query"),Player.CHANGED)){
            f.writer.locked(same->f.authority.withObserved(same,Instant.now().plusSeconds(20),lease->{
                var result=f.queries.read(same,f.contract,request(f,lease.identity()));var known=assertInstanceOf(PlanningReadResult.Known.class,result);assertTrue(known.value() instanceof RawJson);
                var receipt=known.receipt();assertEquals(receipt,f.archive.withSession(same).loadRead(f.archive.withSession(same).readReferenceOf(receipt)));
                for(var guard:List.of(receipt.before().binding(),receipt.after().binding()))RootLifecycleGuardEvidence.verify(guard,f.archive.withSession(same),same,f.originals);
                assertEquals(1,f.packets.writes);assertEquals(0,same.head().state().sequence());return null;
            }));
        }
    }
    @Test void livingSubjectExpiredDeadlineWrongFrameAndChangedPhysicalSourceNeverGrantTerminalRead()throws Exception{
        try(Fixture f=new Fixture(temporary.resolve("living"),Player.LIVING)){f.writer.locked(same->{assertThrows(IllegalArgumentException.class,()->f.authority.withObserved(same,Instant.now().plusSeconds(10),lease->null));return null;});}
        try(Fixture f=new Fixture(temporary.resolve("expiry"),Player.DEAD)){f.writer.locked(same->{int before=f.packets.reads;assertThrows(IllegalArgumentException.class,()->f.authority.withObserved(same,Instant.now(),lease->null));assertEquals(before,f.packets.reads);return null;});}
        try(Fixture f=new Fixture(temporary.resolve("process"),Player.DEAD)){f.packets.processChanged=true;f.writer.locked(same->{assertThrows(IOException.class,()->f.authority.withObserved(same,Instant.now().plusSeconds(20),lease->null));assertEquals(0,f.packets.writes);return null;});}
        try(Fixture f=new Fixture(temporary.resolve("source"),Player.CHANGED)){f.writer.locked(same->{assertThrows(IOException.class,()->f.authority.withObserved(same,Instant.now().plusSeconds(20),lease->{Files.writeString(f.sourceFile,"changed original source");return null;}));return null;});}
        try(Fixture f=new Fixture(temporary.resolve("wrong"),Player.DEAD)){f.writer.locked(same->f.authority.withObserved(same,Instant.now().plusSeconds(20),lease->{
            var original=lease.identity();var wrong=new LifecycleIdentity(original.machineId(),original.game(),original.sessionId(),original.connectionGeneration(),original.subject(),new LifecycleIdentity.Frame("another-snapshot",original.frame().revision(),original.frame().nativeRevision(),original.frame().dateRaw(),true,true),original.currentPlayer(),original.terminalReason(),original.evidence(),original.observedAt());
            int before=f.packets.reads;assertThrows(IllegalArgumentException.class,()->f.authority.current(same,wrong,Instant.now().plusSeconds(10),ignored->null));assertEquals(before,f.packets.reads);return null;
        }));}
    }
    @Test void aTerminalOriginCannotBorrowAnOrdinaryReadOrUninstalledContract()throws Exception{
        try(Fixture f=new Fixture(temporary.resolve("contracts"),Player.CHANGED)){f.writer.locked(same->f.authority.withObserved(same,Instant.now().plusSeconds(20),lease->{
            var ordinary=new ReadContract<>("ordinary/v1",READ,Optional.empty(),"fixture",ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE,ReadContract.WireProfile.G2_PRIVATE_QUERY,f.reviewed,req->new NativeRequest(READ.value(),Optional.empty(),new RawJson(bytes("{}"))),receipt->receipt.original().originalResultToken().orElseThrow());
            int writes=f.packets.writes;assertThrows(IllegalArgumentException.class,()->f.guard.verify(same.head(),request(f,lease.identity()),ordinary));assertEquals(writes,f.packets.writes);return null;
        }));}
    }
    @Test void terminalCampaignRootUsesTheSamePhysicalCatalogGuardAndArchiveWithoutBorrowingOrdinaryOrForeignContracts()throws Exception{
        var operation=new OperationKey("query-campaign-root-context-v1");
        try(Fixture f=new Fixture(temporary.resolve("terminal-campaign-root"),Player.CHANGED,operation)){
            f.writer.locked(same->f.authority.withObserved(same,Instant.now().plusSeconds(20),lease->{
                int packets=f.packets.reads;
                var request=request(f,lease.identity());
                var ordinary=new ReadContract<RawJson>("ordinary-campaign-root/v1",operation,Optional.empty(),"terminal-fixture",
                        ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE,ReadContract.WireProfile.G2_PRIVATE_QUERY,f.reviewed,
                        ignored->new NativeRequest(operation.value(),Optional.empty(),new RawJson(bytes("{}"))),receipt->receipt.original().originalResultToken().orElseThrow());
                var uninstalled=new ReadContract<RawJson>(f.contract.contractId(),operation,Optional.empty(),f.contract.permissionKey(),
                        f.contract.permissionMode(),f.contract.wireProfile(),f.contract.guardMode(),f.reviewed,
                        ignored->new NativeRequest(operation.value(),Optional.empty(),new RawJson(bytes("{}"))),receipt->receipt.original().originalResultToken().orElseThrow());
                assertThrows(IllegalArgumentException.class,()->f.guard.verify(same.head(),request,ordinary));
                assertThrows(IllegalArgumentException.class,()->f.guard.verify(same.head(),request,uninstalled));
                var otherSource=new G2Source(MACHINE,Instant.now().toString(),"another-exact-source",f.reviewed);
                var changedSource=new PlanningReadRequest(request.origin(),otherSource,request.sessionId(),operation,request.arguments(),request.deadline());
                assertThrows(IllegalArgumentException.class,()->f.guard.verify(same.head(),changedSource,f.contract));
                assertEquals(packets,f.packets.reads);assertEquals(0,f.packets.writes);
                var result=f.queries.read(same,f.contract,request);var known=assertInstanceOf(PlanningReadResult.Known.class,result);
                var receipt=known.receipt();assertEquals(operation,receipt.request().operation());
                assertEquals(receipt,f.archive.withSession(same).loadRead(f.archive.withSession(same).readReferenceOf(receipt)));
                for(var guard:List.of(receipt.before().binding(),receipt.after().binding()))
                    assertEquals(lease.identity(),RootLifecycleGuardEvidence.replay(guard,f.archive.withSession(same),same,f.originals).identity());
                assertEquals(1,f.packets.writes);assertEquals(0,same.head().state().sequence());return null;
            }));
        }
    }
    @Test void wrongNativeBooleanFabricatedOldSubjectAndNativeDigestCannotOpenTheRealTerminalReadScope()throws Exception{
        try(Fixture f=new Fixture(temporary.resolve("boolean"),Player.CHANGED)){f.packets.injectedState=state(Player.CHANGED).replace("\"alive\":true","\"alive\":1");f.writer.locked(same->{assertThrows(IllegalArgumentException.class,()->f.authority.withObserved(same,Instant.now().plusSeconds(20),lease->null));assertEquals(0,f.packets.writes);return null;});}
        try(Fixture f=new Fixture(temporary.resolve("subject"),Player.DEAD)){f.writer.locked(same->f.authority.withObserved(same,Instant.now().plusSeconds(20),lease->{
            var original=lease.identity();var old=original.subject();var forgedSubject=new LifecycleIdentity.Subject(old.characterId(),"invented-episode",old.episodeEpoch(),old.driverVersion());
            var wrong=new LifecycleIdentity(original.machineId(),original.game(),original.sessionId(),original.connectionGeneration(),forgedSubject,original.frame(),original.currentPlayer(),original.terminalReason(),original.evidence(),original.observedAt());
            int reads=f.packets.reads;assertThrows(IllegalArgumentException.class,()->f.authority.current(same,wrong,Instant.now().plusSeconds(20),ignored->null));assertEquals(reads,f.packets.reads);
            var refs=original.evidence();var changed=new ExactRef(refs.nativePacket().path(),refs.nativePacket().bytes(),"f".repeat(64));
            var wrongEvidence=new LifecycleIdentity.Evidence(changed,refs.helloPacket(),refs.observationManifest(),refs.originalDriver(),refs.completeSourceQualification());
            var wrongDigest=new LifecycleIdentity(original.machineId(),original.game(),original.sessionId(),original.connectionGeneration(),original.subject(),original.frame(),original.currentPlayer(),original.terminalReason(),wrongEvidence,original.observedAt());
            assertThrows(IllegalArgumentException.class,()->f.guard.verify(same.head(),request(f,wrongDigest),f.contract));assertEquals(reads,f.packets.reads);assertEquals(0,f.packets.writes);return null;
        }));}
    }
    @Test void canonicalDeathCompositeConsumesOnlyTerminalAuthorityAndArchivedSemanticTamperingIsRejected()throws Exception{
        try(Fixture f=new Fixture(temporary.resolve("composite"),Player.DEAD)){f.writer.locked(same->f.authority.withObserved(same,Instant.now().plusSeconds(20),lease->{
            OperationKey death=new OperationKey("death-terminal");CompositeActionPort handler=new CompositeActionPort(){
                @Override public String handlerId(){return "terminal-guard-software-test";}
                @Override public boolean supports(OperationKey operation){return operation.equals(death);}
                @Override public void validate(ActionCommand command){throw new AssertionError("guard cannot validate or run domain logic");}
                @Override public ActionPorts.PostconditionResult run(ActionCommand parent,Children children){throw new AssertionError("no native/domain mutation in authority test");}
                @Override public ActionPorts.PostconditionResult observe(ActionCommand parent,CompositeExecution retained){throw new AssertionError("no domain success from physical authority");}
            };
            var replayBinding=new org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier.Binding(death,f.reviewed,(head,receipt,archived)->{throw new AssertionError("guard does not grant domain settlement");});
            var installed=RootExecutableBindings.freeze(List.of(),RootReadContractCatalog.staticOnly(List.of()),List.of(new RootExecutableBindings.CompositeBinding(handler,ReadContract.GuardMode.LIFECYCLE_TERMINAL_SESSION,Optional.empty(),f.reviewed,f.reviewed)),List.of(replayBinding),List.of(),8);
            var actionGuard=new RootLifecycleActionGuard(f.authority,()->same,f.archive,f.source,Clock.systemUTC(),"terminal-test",f.originals,installed,(borrowed,command,actual,archive)->{throw new AssertionError("death composite cannot borrow modal Close qualification");});
            var values=List.<ProposalLifecycle.ExpectedValue>of(new ProposalLifecycle.ExpectedBoolean(new ProposalLifecycle.FieldKey("native.gameplay_verified"),false),new ProposalLifecycle.ExpectedBoolean(new ProposalLifecycle.FieldKey("timeline.advance_verified"),false),new ProposalLifecycle.ExpectedBoolean(new ProposalLifecycle.FieldKey("timeline.checkpoint_eligible"),false));
            var expected=new LifecycleExpectedPostcondition(lease.identity(),f.source,"terminal-test/v1",LifecycleExpectedPostcondition.Operation.DEATH_TERMINAL,values);
            var command=new ActionCommand("death-test",new CommandOrigin.LifecycleTerminal(lease.identity()),f.source,SESSION,death,new OpportunityJson.Obj(Map.of()),new CommandExpectation.LifecycleTerminal(expected),new JointBudgetSelector.Claims(Set.of(),Set.of(),Set.of(),Set.of()),Instant.now().plusSeconds(20));
            GuardEvidence original=actionGuard.verify(same.head(),command);assertInstanceOf(CommandOrigin.LifecycleTerminal.class,original.origin());assertThrows(IllegalStateException.class,command::before);assertEquals(0,f.packets.writes);
            var actualPort=new RootLifecycleObservationPort(f.authority,()->same);assertSame(lease.snapshot(),actualPort.current(command,command.deadline()));assertSame(lease.snapshot(),actualPort.next(command,lease.snapshot(),command.deadline()));
            var archived=f.archive.withSession(same);var ref=original.supportingEvidence().getFirst();var body=StrictJson.parse(archived.loadMaterial(ref).bytes(),65536);assertTrue(body.isObject());
            var changed=((com.fasterxml.jackson.databind.node.ObjectNode)body).deepCopy();ExactRef wrongSemantic=archived.preserveMaterial(new RawJson(bytes("{}")));changed.set("semantic",wrongSemantic.toJson());ExactRef changedRef=archived.preserveMaterial(new RawJson(StrictJson.canonical(changed,65536)));
            var tampered=new GuardEvidence(original.origin(),original.source(),original.sessionId(),original.connectionGeneration(),original.operation(),original.nativeEvidence(),original.capabilityEvidence(),original.authorityId(),original.observedAt(),original.validUntil(),List.of(changedRef));
            assertThrows(IllegalArgumentException.class,()->RootLifecycleGuardEvidence.verify(tampered,archived,same,f.originals));return null;
        }));}
    }

    @Test void oneActualPhysicalSnapshotDispatchesLivingOrTerminalWithoutASecondObserveOrCapabilityHook()throws Exception{
        for(Player player:List.of(Player.LIVING,Player.MISSING,Player.NULL,Player.DEAD,Player.CHANGED))
            try(Fixture f=new Fixture(temporary.resolve("physical-"+player.name()),player)){
                f.writer.locked(same->f.authority.withSnapshot(same,Instant.now().plusSeconds(20),snapshot->{
                    int actualReads=f.packets.reads;
                    assertEquals(3,actualReads,"one original hello, heartbeat and Native snapshot are the complete physical input");
                    assertSame(snapshot.freshFacts(),snapshot.fullSnapshot().facts());
                    assertEquals(0,f.packets.writes);
                    assertEquals(player==Player.LIVING,snapshot.ordinary().isPresent());
                    assertEquals(player!=Player.LIVING,snapshot.terminalIdentity().isPresent());
                    if(player==Player.LIVING){
                        var data=snapshot.ordinary().orElseThrow();
                        assertEquals(BigInteger.valueOf(73),data.identity().frame().identity().player());
                        assertThrows(IllegalArgumentException.class,()->f.authority.withObserved(same,Instant.now().plusSeconds(10),ignored->null));
                    }else{
                        var terminal=snapshot.terminalIdentity().orElseThrow();
                        f.authority.current(same,terminal,Instant.now().plusSeconds(10),lease->{
                            assertSame(snapshot.fullSnapshot().actual(),lease.snapshot().actual());
                            lease.assertCurrent(same);return null;
                        });
                    }
                    f.authority.withSnapshot(same,Instant.now().plusSeconds(10),nested->{assertSame(snapshot,nested);return null;});
                    assertEquals(actualReads,f.packets.reads,"branching and nested consumers cannot trigger another Native observe");
                    assertThrows(IllegalArgumentException.class,()->f.authority.requireOutsideObservationScope(same));
                    snapshot.assertCurrent(same);return null;
                }));
            }
    }

    @Test void detachedPublicSnapshotDataCannotReenterItsSourceQualifiedWriterScope()throws Exception{
        try(Fixture f=new Fixture(temporary.resolve("physical-detached"),Player.LIVING)){
            var escaped=new AtomicReference<RootLifecycleAuthority.SnapshotLease>();
            f.writer.locked(same->f.authority.withSnapshot(same,Instant.now().plusSeconds(20),actual->{escaped.set(actual);return null;}));
            f.writer.locked(other->{assertThrows(IllegalArgumentException.class,()->escaped.get().assertCurrent(other));return null;});
            assertEquals(0,f.packets.writes);
        }
    }


    @Test void fourOriginalSemanticUsesTheSameRawProducerWithoutAnyCapabilityOrDomainHook()throws Exception{
        try(Fixture f=new Fixture(temporary.resolve("physical-sem"),Player.LIVING)){
            f.writer.locked(same->{
                var owner=new org.xar.ck3.control.application.session.SessionPorts.SessionIdentity(MACHINE,GAME,SESSION);
                var actual=f.authority.withSnapshot(same,Instant.now().plusSeconds(20),physical->{
                    var evidence=f.authority.semantic(same,owner,physical);
                    assertEquals(evidence,f.authority.semantic(same,owner,Instant.now().plusSeconds(10)));
                    assertEquals(3,f.packets.reads,"both SEM entry points must borrow this exact physical capture");return evidence;
                });
                var verifier=new org.xar.ck3.control.application.readiness.NativeSemanticEvidenceVerifier(
                        (borrowed,ref,maximum)->f.archive.readArtifact(borrowed,ref,maximum));
                assertEquals(actual.frame(),verifier.verify(same,owner,actual).frame());
                assertEquals(3,f.packets.reads,"full original SEM replay cannot collect another Native snapshot");
                assertEquals(0,f.packets.writes);
                f.authority.requireOutsideObservationScope(same);return null;
            });
        }
    }

    @Test void fabricatedUnknownOrIntentCannotAcquireFreshNativeDataOrAReconciliationQueryLease()throws Exception{
        try(Fixture f=new Fixture(temporary.resolve("reconcile-no-canonical"),Player.LIVING)){
            var catalog=RootReadContractCatalog.staticOnly(List.of());
            var binding=new ReconciliationPendingBinding(f.writer,f.archive,f.originals);
            var loader=new org.xar.ck3.control.application.effects.DriverFrameEvidenceLoader(new DriverObservationAssembler());
            var reconciliation=new RootReconciliationAuthority(f.writer,f.archive,f.authority,binding,f.originals,loader,catalog,
                    (original,current,data,deadline)->List.of(),Clock.systemUTC());
            f.writer.locked(same->f.authority.withSnapshot(same,Instant.now().plusSeconds(20),physical->{
                var actual=physical.ordinary().orElseThrow();
                var op=new OperationKey("pause-map");
                var expected=new ProposalLifecycle.ExpectedPostcondition(1,actual.identity(),f.source,"paused/v1",
                        List.of(new ProposalLifecycle.ExpectedBoolean(new ProposalLifecycle.FieldKey("paused"),true)));
                var command=new ActionCommand("not-a-canonical-pending",actual.identity(),f.source,SESSION,op,new OpportunityJson.Obj(Map.of()),
                        expected,new JointBudgetSelector.Claims(Set.of(),Set.of(),Set.of(),Set.of()),Instant.now().plusSeconds(20));
                var guard=new GuardEvidence(actual.identity(),f.source,SESSION,actual.connectionGeneration(),op,actual.originalEvidence(),
                        physical.originalHello(),"constructed-data-only",actual.observedAt(),Instant.now().plusSeconds(20));
                var attempt=new ActionState.Attempt("invented-request",actual.observedAt().minusMillis(1),guard,new NativeRequest(op.value(),Optional.of("game.command.pause-map"),new RawJson(bytes("{}"))));
                var unknown=new ActionReceipt(1,1,command,ActionCodec.bodySha256(command),
                        new ActionState.Unknown(Optional.of(attempt),Optional.empty(),"constructed unresolved data",List.of(actual.originalEvidence())));
                var intent=new ActionReceipt(1,1,command,ActionCodec.bodySha256(command),new ActionState.IntentDurable());
                int reads=f.packets.reads;
                assertThrows(IOException.class,()->reconciliation.withObserved(same,unknown,Instant.now().plusSeconds(10),lease->null));
                assertThrows(IOException.class,()->reconciliation.withObserved(same,intent,Instant.now().plusSeconds(10),lease->null));
                var dataOnly=ReconciliationIdentity.fromCanonical(unknown,actual.identity(),f.source,SESSION,actual.connectionGeneration(),
                        f.reviewed,physical.originalDriver(),new ReconciliationIdentity.Evidence(actual.originalEvidence(),physical.originalHello(),
                                physical.originalHeartbeat(),physical.freshFacts().semanticFactsEvidence(),physical.originalDriver(),physical.sourceQualification().proof()),actual.observedAt());
                assertThrows(IllegalArgumentException.class,()->reconciliation.current(same,dataOnly,Instant.now().plusSeconds(10),lease->null));
                assertEquals(reads,f.packets.reads,"canonical membership must fail before another Native observation");
                assertEquals(0,f.packets.writes);
                assertEquals(0,same.head().state().sequence());return null;
            }));
        }
    }

    @Test void reconciliationFamiliesRejectOrdinaryContractsCouncilStatusAndUnrelatedQueries()throws Exception{
        try(Fixture f=new Fixture(temporary.resolve("reconcile-families"),Player.LIVING)){
            assertThrows(IllegalArgumentException.class,()->new RootReconciliationAuthority.AllowedRead(f.contract,
                    new OpportunityJson.Obj(Map.of()),RootReconciliationAuthority.QueryKind.ORDINARY_INTERACTION));
            var unrelated=new ReadContract<>("unrelated-reconciliation/v1",READ,Optional.empty(),"fixture",
                    ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE,ReadContract.WireProfile.G2_PRIVATE_QUERY,
                    ReadContract.GuardMode.RECONCILIATION_OBSERVATION,f.reviewed,
                    request->new NativeRequest(READ.value(),Optional.empty(),new RawJson(bytes("{}"))),
                    receipt->receipt.original().originalResultToken().orElseThrow());
            assertThrows(IllegalArgumentException.class,()->new RootReconciliationAuthority.AllowedRead(unrelated,
                    new OpportunityJson.Obj(Map.of()),RootReconciliationAuthority.QueryKind.COMMANDER_CANDIDATES));
            var council=new ReadContract<>("actual-council-status/v1",new OperationKey("private-council-application-main-status-v1"),
                    Optional.empty(),"fixture",ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE,ReadContract.WireProfile.COUNCIL_MAILBOX_STATUS,
                    f.reviewed,request->new NativeRequest("private-council-application-main-status-v1",Optional.empty(),new RawJson(bytes("{}"))),
                    receipt->receipt.original().originalResultToken().orElseThrow());
            assertThrows(IllegalArgumentException.class,()->new RootReconciliationAuthority.AllowedRead(council,
                    new OpportunityJson.Obj(Map.of()),RootReconciliationAuthority.QueryKind.ORDINARY_INTERACTION));
            assertEquals(0,f.packets.reads);assertEquals(0,f.packets.writes);
        }
    }

    @Test void terminalGuardCannotClaimAFutureOrDifferentWriterHistoryPoint()throws Exception{
        try(Fixture f=new Fixture(temporary.resolve("guard-history"),Player.DEAD)){
            f.writer.locked(same->f.authority.withObserved(same,Instant.now().plusSeconds(20),lease->{
                var guard=f.guard.verify(same.head(),request(f,lease.identity()),f.contract).binding();
                var bound=f.archive.withSession(same);var ref=guard.supportingEvidence().getFirst();
                var row=(com.fasterxml.jackson.databind.node.ObjectNode)StrictJson.parse(bound.loadMaterial(ref).bytes(),65536);
                row.set("writer_point",StrictJson.object().put("sequence",1).put("digest","f".repeat(64)));
                var changed=bound.preserveMaterial(new RawJson(StrictJson.canonical(row,65536)));
                var forged=new GuardEvidence(guard.origin(),guard.source(),guard.sessionId(),guard.connectionGeneration(),guard.operation(),
                        guard.nativeEvidence(),guard.capabilityEvidence(),guard.authorityId(),guard.observedAt(),guard.validUntil(),List.of(changed));
                assertThrows(IOException.class,()->RootLifecycleGuardEvidence.verify(forged,bound,same,f.originals));
                assertEquals(0,same.head().state().sequence());return null;
            }));
        }
    }

    @Test void preAdoptionAuthorityCanBeConstructedButCannotObserveUsingASubstituteDriver()throws Exception{
        try(Fixture f=new Fixture(temporary.resolve("pre-adoption"),Player.LIVING)){
            var resolves=new AtomicInteger();
            RootLifecycleAuthority.ActualDriverAuthority missing=borrowed->{
                f.writer.requireSession(borrowed);resolves.incrementAndGet();throw new IOException("actual runtime has no adopted Driver");
            };
            var beforeAdoption=new RootLifecycleAuthority(f.writer,f.archive,f.transport,missing,new DriverObservationAssembler(),f.source,
                    (same,session,source,packet,diagnostics,deadline)->{throw new AssertionError("missing adopted Driver must fail before physical/source observation");},
                    Clock.systemUTC(),Duration.ofSeconds(30));
            f.writer.locked(same->{
                assertThrows(IOException.class,()->beforeAdoption.withSnapshot(same,Instant.now().plusSeconds(20),snapshot->null));
                assertEquals(1,resolves.get());assertEquals(0,f.packets.reads);assertEquals(0,f.packets.writes);return null;
            });
        }
    }

}
