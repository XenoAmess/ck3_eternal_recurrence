package org.xar.ck3.control.application.lifecycle;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.checkpoint.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;

/** Real temporary SAVE/Driver/metadata bytes exercise the production freezer and strict reader. */
public final class SeedStoreImmutableTest {
    @TempDir Path temporary;
    private record Fixture(NativeCheckpointFiles files,SeedStore seeds,CheckpointPair pair,ActionReceipt applied,Path history,Path metadata,Path seed) { }
    private Fixture fixture() throws Exception {
        var files=new NativeCheckpointFiles();Path saves=Files.createDirectory(temporary.resolve("saves"));
        Path state=Files.createDirectory(temporary.resolve("state"));Files.createDirectory(state.resolve("native-session"));Files.createDirectory(state.resolve("strategy"));
        Path save=saves.resolve("xar_checkpoint.ck3");Files.writeString(save,"actual temporary seed input");
        var game=new GameGeneration(123,new PythonOnlyUInt64(new BigInteger("133000000000000001")));
        var frame=new ObservationIdentity("test-machine-1",game,new JointBudgetSelector.ProposalFrame(
                new JointBudgetSelector.Frame(BigInteger.valueOf(29829),BigInteger.ONE,BigInteger.valueOf(240)),"native:1",BigInteger.ONE,"episode-1"),1);
        var initial=DriverStateSnapshot.decodeComplete(("{\"format_version\":2,\"pipe_name\":\"test-pipe\",\"bridge_pid\":123,\"episode_character_id\":29829,\"episode_run_id\":\"episode-1\","
                +"\"command_history\":[],\"last_checkpoint\":null,\"rollback_war_failure\":null,\"managed_restore_transaction\":null,\"succession_expectation\":null,\"succession_lifecycle\":null,\"campaign_goal\":null,\"rollback_war_failures\":[]}").getBytes(StandardCharsets.UTF_8));
        var current=new AtomicReference<>(initial);var drivers=new DriverCheckpointStore(files,state.resolve("driver.json"),"test-pipe",new DriverCheckpointStore.SnapshotSupplier(){
            public <T>T withFrozen(DriverCheckpointStore.SnapshotWork<T> work)throws java.io.IOException {
                synchronized(current){return work.run(current.get(),(before,after)->{assertTrue(current.compareAndSet(before,after));});}
            }
        });
        var saveRef=files.observe(save).orElseThrow();var anchor=drivers.persist("save-seed-1",saveRef,frame,"lineage-1");
        byte[] packet="{\"ok\":true}".getBytes(StandardCharsets.UTF_8);var ackRef=files.createNew(state.resolve("ack.json"),packet).reference();
        var pair=new CheckpointPair(saveRef,anchor.driver(),frame,"lineage-1",anchor.historyIndex(),"save-seed-1",ackRef,Instant.now());
        var source=new G2Source("test-machine-1","2026-10-23T15:00:00Z","test-build",ackRef);
        var ready=new CheckpointRequest.Readiness(frame,source,"session-1","lineage-1",true,true,true,"actual_test_frame",ackRef,Instant.now());
        var proposed=new CheckpointRequestFactory(save,deadline->ready).prepare(frame,source,"session-1",Optional.empty(),Instant.now().plusSeconds(20)).saveCommand();
        var command=new ActionCommand("save-seed-1",proposed.before(),proposed.source(),proposed.sessionId(),proposed.operation(),proposed.arguments(),proposed.expected(),proposed.claims(),proposed.deadline());
        var guard=new GuardEvidence(frame,source,"session-1",BigInteger.ONE,command.operation(),ackRef,ackRef,"test-guard",Instant.now(),command.deadline());
        var attempt=new ActionState.Attempt("request-seed-1",Instant.now(),guard,new NativeRequest("save-checkpoint","game.save-checkpoint",new RawJson("{}".getBytes(StandardCharsets.UTF_8))));
        var ack=new NativeActionPort.AckReceived(attempt.requestId(),true,Optional.of(new RawJson(packet)),new RawJson(packet),packet);
        var effect=new ActionState.EffectObservation(frame,source,"session-1",CheckpointRequestFactory.OBSERVER_SCHEMA,List.of(),"independent-read",Instant.now(),ackRef,
                List.of(pair.save().reference(),pair.driver().reference(),ackRef));
        var receipt=new ActionReceipt(1,1,command,ActionCodec.bodySha256(command),new ActionState.Settled(attempt,ack,new ActionState.Applied(effect)));
        return new Fixture(files,new SeedStore(files,drivers,state,saves,bytes->assertTrue(bytes>0)),pair,receipt,
                state.resolve("strategy/one-life-history.json"),state.resolve("native-session/episode-seed.json"),saves.resolve(SeedArtifact.NAME));
    }
    @Test void firstFreezeRoundTripPinsActualSeedAndMetadataAndNeverOverwrites() throws Exception {
        var fixture=fixture();var adopted=assertInstanceOf(SeedAdoption.Available.class,fixture.seeds().freezeFirst(fixture.pair(),fixture.applied()));
        assertEquals(SeedAdoption.Origin.FIRST_FREEZE,adopted.origin());assertEquals(fixture.pair().save().reference().sha256(),adopted.artifact().save().reference().sha256());
        assertNotEquals(fixture.pair().save().identity().fileId(),adopted.artifact().save().identity().fileId());adopted.artifact().requireCurrent(fixture.files());
        var existing=assertInstanceOf(SeedAdoption.Available.class,fixture.seeds().freezeFirst(fixture.pair(),fixture.applied()));
        assertEquals(SeedAdoption.Origin.EXISTING,existing.origin());assertEquals(adopted.artifact().save(),existing.artifact().save());assertEquals(adopted.artifact().metadata(),existing.artifact().metadata());
    }
    @Test void orphanAndMalformedHistoryCannotBePromotedOrOverwritten() throws Exception {
        var fixture=fixture();Files.writeString(fixture.history(),"{\"episodes\":null}");
        var invalid=assertInstanceOf(SeedAdoption.Unavailable.class,fixture.seeds().freezeFirst(fixture.pair(),fixture.applied()));
        assertEquals(SeedAdoption.Reason.HISTORY_UNREADABLE,invalid.reason());assertFalse(Files.exists(fixture.seed()));assertFalse(Files.exists(fixture.metadata()));
        Files.writeString(fixture.history(),"{\"episodes\":[]}");Files.writeString(fixture.seed(),"orphan original");
        var orphan=assertInstanceOf(SeedAdoption.Unavailable.class,fixture.seeds().freezeFirst(fixture.pair(),fixture.applied()));
        assertEquals(SeedAdoption.Reason.ORPHAN_SEED,orphan.reason());assertEquals("orphan original",Files.readString(fixture.seed()));assertFalse(Files.exists(fixture.metadata()));
    }
    @Test void actualPriorEpisodesRefuseANewFirstLifeSeed() throws Exception {
        var fixture=fixture();Files.writeString(fixture.history(),"{\"episodes\":[{\"terminal\":\"retained\"}]}");
        var unavailable=assertInstanceOf(SeedAdoption.Unavailable.class,fixture.seeds().freezeFirst(fixture.pair(),fixture.applied()));
        assertEquals(SeedAdoption.Reason.PRIOR_EPISODES,unavailable.reason());assertFalse(Files.exists(fixture.seed()));
    }
    @Test void changedMetadataCannotKeepAnExistingSeedArtifactQualified() throws Exception {
        var fixture=fixture();var adopted=assertInstanceOf(SeedAdoption.Available.class,fixture.seeds().freezeFirst(fixture.pair(),fixture.applied()));
        String metadata=Files.readString(fixture.metadata());Files.writeString(fixture.metadata(),metadata.replace("\"character_id\":29829","\"character_id\":true"));
        assertThrows(Exception.class,()->adopted.artifact().requireCurrent(fixture.files()));assertInstanceOf(SeedAdoption.Unknown.class,fixture.seeds().read());
    }
}
