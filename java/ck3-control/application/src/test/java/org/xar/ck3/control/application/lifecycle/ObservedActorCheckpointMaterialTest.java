package org.xar.ck3.control.application.lifecycle;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.checkpoint.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;

/**
 * Real file/Driver/anchor/seed DATA producer and cold readers. These cases do not create a native SAVE receipt,
 * SavedMaterial, ordinary Ready, Managed Game or private action qualification for a negative observed actor.
 */
public final class ObservedActorCheckpointMaterialTest {
    @TempDir Path temporary;
    private static final String PIPE="observed-actor-data-pipe";
    private static DriverStateSnapshot.Complete original(int actor,String opaque){
        String history="{\"index\":1,\"command\":\"retained-native-observation\",\"ok\":true,\"result\":{\"observed_actor\":"+actor+",\"opaque\":"+opaque+"}}";
        return DriverStateSnapshot.decodeComplete(("{\"format_version\":2,\"pipe_name\":\""+PIPE+"\",\"bridge_pid\":123,"
                +"\"episode_character_id\":"+actor+",\"episode_run_id\":\"observed-actor-episode\",\"last_checkpoint\":null,"
                +"\"command_history\":["+history+"],\"rollback_war_failure\":null,\"managed_restore_transaction\":null,"
                +"\"succession_expectation\":null,\"succession_lifecycle\":null,\"campaign_goal\":null,\"rollback_war_failures\":[]}").getBytes(StandardCharsets.UTF_8));
    }
    private static ProposalLifecycle.ObservationIdentity frame(int actor){
        var game=new GameGeneration(123,new PythonOnlyUInt64(new BigInteger("18446744073709551614")));
        var identity=new JointBudgetSelector.Frame(NativeCharacterId.of(actor).asBigInteger(),BigInteger.ONE,BigInteger.valueOf(240));
        return new ProposalLifecycle.ObservationIdentity("observed-actor-machine",game,
                new JointBudgetSelector.ProposalFrame(identity,"native-observed-actor",BigInteger.ONE,"observed-actor-episode"),1);
    }
    private record Produced(NativeCheckpointFiles files,DriverCheckpointStore store,CheckpointPair pair,
            DriverStateSnapshot.Complete original,AtomicReference<DriverStateSnapshot.Complete> current,Path root){ }
    private Produced produce(int actor,String opaque,String suffix)throws Exception{
        Path root=Files.createDirectories(temporary.resolve(suffix));var files=new NativeCheckpointFiles();
        Path save=root.resolve("xar_checkpoint.ck3");Files.writeString(save,"original saved input DATA, no Game action dispatched");
        var before=original(actor,opaque);var state=new AtomicReference<>(before);
        var store=new DriverCheckpointStore(files,root.resolve("full-driver.json"),PIPE,new DriverCheckpointStore.SnapshotSupplier(){
            public <T>T withFrozen(DriverCheckpointStore.SnapshotWork<T> work)throws IOException{
                synchronized(state){return work.run(state.get(),(expected,after)->{
                    if(!state.compareAndSet(expected,after))throw new IOException("actual frozen Driver DATA changed");
                });}
            }
        });
        var witness=files.observe(save).orElseThrow();String action="retained-anchor-"+suffix;
        var anchor=store.persist(action,witness,frame(actor),"observed-actor-lineage");
        var ack=files.createNew(root.resolve("retained-anchor-evidence.json"),"{\"native_receipt_qualification\":false}".getBytes(StandardCharsets.UTF_8));
        var pair=new CheckpointPair(witness,anchor.driver(),frame(actor),"observed-actor-lineage",anchor.historyIndex(),action,
                ack.reference(),Instant.parse("2026-10-24T05:00:00Z"));
        return new Produced(files,store,pair,before,state,root);
    }
    private SeedArtifact seed(Produced source,com.fasterxml.jackson.databind.JsonNode actor,String suffix)throws Exception{
        Path root=Files.createDirectories(source.root().resolve(suffix));
        var save=source.files().copyNew(source.pair().save(),root.resolve(SeedArtifact.NAME));
        var row=StrictJson.object();row.put("format_version",1);row.put("name",SeedArtifact.NAME);row.put("path",save.reference().path());
        row.put("size",save.reference().bytes());row.put("sha256",save.reference().sha256());row.put("date_raw",240);
        row.set("character_id",actor);row.put("source_run_id","observed-actor-episode");row.put("source_checkpoint_name","xar_checkpoint.ck3");row.put("immutable",true);
        var metadata=source.files().createNew(root.resolve("seed-metadata.json"),FullJsonTree.encode(row,65536));
        return SeedStore.decode(source.files(),save,metadata);
    }
    @Test void signedObservedIdentitySurvivesActualDriverAnchorPairAndImmutableSeedReaders()throws Exception{
        for(int actor:new int[]{0,-2,Integer.MIN_VALUE,Integer.MAX_VALUE,29829}){
            var actual=produce(actor,"null","actor-"+actor);var pair=actual.pair();
            actual.store().verify(pair);var decoded=CheckpointPairCodec.decode(CheckpointPairCodec.encode(pair));
            assertEquals(pair,decoded);assertEquals(BigInteger.valueOf(actor),decoded.frame().frame().identity().player());
            var saved=actual.store().readVerified(decoded);assertEquals(BigInteger.valueOf(actor),saved.session().actorId());
            assertArrayEquals(actual.original().commandHistory().getFirst().originalRow().json(),saved.commandHistory().getFirst().originalRow().json());
            byte[] full=actual.files().read(pair.driver(),DriverCheckpointStore.MAX_DRIVER_BYTES);
            assertArrayEquals(saved.encode(),actual.store().readArchivedSnapshot(pair,full).encode());
            assertArrayEquals(saved.encode(),actual.store().readVerifiedOriginal(pair,saved.session()).encode());
            var seed=seed(actual,NativeCharacterId.of(actor).toJson(),"seed");
            seed.requireCurrent(actual.files());assertEquals(BigInteger.valueOf(actor),seed.characterId());
            assertEquals(pair.save().reference().sha256(),seed.save().reference().sha256());
            assertNotEquals(pair.save().identity().fileId(),seed.save().identity().fileId());
            var retried=actual.store().persist(pair.saveActionId(),pair.save(),pair.frame(),pair.lineageId());
            assertEquals(pair.driver(),retried.driver());assertEquals(saved.commandHistory().size(),actual.current().get().commandHistory().size());
        }
    }
    @Test void opaqueLargeNumbersAndDecimalTokensKeepOriginalHistoryThroughTheSameStoreProducer()throws Exception{
        String integer="7".repeat(70001);String decimal="1."+"2".repeat(2000);
        var actual=produce(-2,"{\"integer\":"+integer+",\"decimal\":"+decimal+",\"negative_zero\":-0.0,\"ratio\":1.0,\"missing_vs_null\":null}","large-history");
        var saved=actual.store().readVerified(actual.pair());
        assertArrayEquals(actual.original().commandHistory().getFirst().originalRow().json(),saved.commandHistory().getFirst().originalRow().json());
        String row=new String(saved.commandHistory().getFirst().originalRow().json(),StandardCharsets.UTF_8);
        assertTrue(row.contains(integer));assertTrue(row.contains(decimal));assertTrue(row.contains("\"negative_zero\":-0.0"));
        assertTrue(row.contains("\"ratio\":1.0"));assertTrue(row.contains("\"missing_vs_null\":null"));
        assertArrayEquals(saved.encode(),actual.store().readArchivedSnapshot(actual.pair(),actual.files().read(actual.pair().driver(),DriverCheckpointStore.MAX_DRIVER_BYTES)).encode());
    }
    @Test void absentSentinelUnsignedAliasBooleanStringAndFloatCannotBecomeAStoredActor()throws Exception{
        var actual=produce(-2,"null","invalid-actors");
        List<String> wrong=List.of("-1","2147483648","-2147483649","4294967294","true","\"-2\"","-2.0","null");
        for(int index=0;index<wrong.size();index++){
            var actor=FullJsonTree.parse(wrong.get(index).getBytes(StandardCharsets.UTF_8),64);
            int item=index;
            assertThrows(IllegalArgumentException.class,()->seed(actual,actor,"bad-seed-"+item));
            byte[] original=actual.original().encode();var tree=(com.fasterxml.jackson.databind.node.ObjectNode)FullJsonTree.parse(original,DriverCheckpointStore.MAX_DRIVER_BYTES);
            tree.set("episode_character_id",actor);
            assertThrows(IllegalArgumentException.class,()->DriverStateSnapshot.decodeComplete(FullJsonTree.encode(tree,DriverCheckpointStore.MAX_DRIVER_BYTES)));
            var saved=actual.store().readVerified(actual.pair());
            var anchor=(com.fasterxml.jackson.databind.node.ObjectNode)FullJsonTree.parse(saved.encode(),DriverCheckpointStore.MAX_DRIVER_BYTES);
            ((com.fasterxml.jackson.databind.node.ObjectNode)anchor.get("last_checkpoint")).set("episode_character_id",actor);
            ((com.fasterxml.jackson.databind.node.ObjectNode)anchor.get("command_history").get(1).get("result").get("checkpoint")).set("episode_character_id",actor);
            var changed=actual.files().createNew(actual.root().resolve("bad-anchor-"+item+".json"),FullJsonTree.encode(anchor,DriverCheckpointStore.MAX_DRIVER_BYTES));
            var originalPair=actual.pair();
            var changedPair=new CheckpointPair(originalPair.save(),changed,originalPair.frame(),originalPair.lineageId(),
                    originalPair.historyIndex(),originalPair.saveActionId(),originalPair.nativeAckRef(),originalPair.observedAt());
            assertThrows(IllegalArgumentException.class,()->actual.store().readVerified(changedPair));
        }
        actual.store().verify(actual.pair());assertEquals(BigInteger.valueOf(-2),actual.current().get().session().actorId());
    }
}
