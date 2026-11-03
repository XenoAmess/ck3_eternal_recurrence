package org.xar.ck3.control.application.lifecycle;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.lang.reflect.InvocationTargetException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.checkpoint.CheckpointPair.FileWitness;
import org.xar.ck3.control.application.checkpoint.NativeCheckpointFiles;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.FullJsonTree;

/** Invokes only the existing static DATA guard. No Composite, private seed constructor or authority is created. */
final class SeedMapSharedGuardSignedBoundaryTest {
    @TempDir Path temporary;
    private static final BigInteger DATE=BigInteger.valueOf(120);

    @Test void actualSharedGuardAcceptsMatchingSignedSeedBoundaries() throws Exception {
        var files=new NativeCheckpointFiles();
        assertMatches(seed(files,temporary.resolve("positive-control"),BigInteger.valueOf(73)));
        long[] actors={Integer.MIN_VALUE,-2,0,Integer.MAX_VALUE};
        for(int index=0;index<actors.length;index++) {
            var actor=BigInteger.valueOf(actors[index]);
            var actual=seed(files,temporary.resolve("signed-"+index),actor);
            assertEquals(actor,actual.characterId());
            assertMatches(actual);
        }
    }

    @Test void actualSharedGuardRejectsInvalidOrDifferentActorDateAndUnreadyMap() throws Exception {
        var files=new NativeCheckpointFiles();
        assertMatches(seed(files,temporary.resolve("positive-control"),BigInteger.valueOf(73)));
        var actual=seed(files,temporary.resolve("negative-seed"),BigInteger.valueOf(-2));
        assertMatches(actual);

        var invalidActors=List.of("-2147483649","-1","2147483648","4294967294","4294967295",
                "\"-2\"","true","null","-2.0","\"INVALID\"");
        for(String token:invalidActors) {
            var state=map(actual);
            LifecycleJson.object(state.get("played_character")).set("character_id",token(token));
            assertRejected(state,actual);
        }
        for(long actor:new long[]{Integer.MIN_VALUE,0,73,Integer.MAX_VALUE}) {
            var state=map(actual);
            LifecycleJson.object(state.get("played_character")).put("character_id",BigInteger.valueOf(actor));
            assertRejected(state,actual);
        }
        for(String token:List.of("121","-1","\"120\"","true","null","120.0")) {
            var state=map(actual);state.set("date_raw",token(token));
            assertRejected(state,actual);
        }
        for(String flag:List.of("paused","map_ready")) {
            var state=map(actual);state.put(flag,false);
            assertRejected(state,actual);
        }
        var dead=map(actual);LifecycleJson.object(dead.get("played_character")).put("alive",false);
        assertRejected(dead,actual);
        var wrongPaused=map(actual);wrongPaused.put("paused","true");assertRejected(wrongPaused,actual);
        var wrongMap=map(actual);wrongMap.putNull("map_ready");assertRejected(wrongMap,actual);
        var wrongAlive=map(actual);LifecycleJson.object(wrongAlive.get("played_character")).put("alive",1);
        assertRejected(wrongAlive,actual);
    }

    private static SeedArtifact seed(NativeCheckpointFiles files,Path directory,BigInteger actor) throws Exception {
        Files.createDirectories(directory);
        var save=createSmall(files,directory.resolve(SeedArtifact.NAME),bytes("small seed-map guard DATA"));
        var metadata=LifecycleJson.row().put("format_version",1).put("name",SeedArtifact.NAME)
                .put("path",save.reference().path()).put("size",save.reference().bytes()).put("sha256",save.reference().sha256())
                .put("date_raw",DATE).put("character_id",actor).put("source_run_id","episode-1")
                .put("source_checkpoint_name","xar_checkpoint.ck3").put("immutable",true);
        var original=createSmall(files,directory.resolve("episode-seed.json"),LifecycleJson.bytes(metadata));
        var actual=SeedStore.decode(files,save,original);
        actual.requireCurrent(files);
        assertEquals(actor,actual.characterId());assertEquals(DATE,actual.dateRaw());
        return actual;
    }

    private static ObjectNode map(SeedArtifact seed) {
        var state=LifecycleJson.row().put("paused",true).put("map_ready",true).put("date_raw",seed.dateRaw());
        state.putObject("played_character").put("character_id",seed.characterId()).put("alive",true);
        return state;
    }

    private static void assertMatches(SeedArtifact seed) {
        var state=map(seed);byte[] original=LifecycleJson.bytes(state);
        assertDoesNotThrow(()->checkSeed(state,seed));
        assertArrayEquals(original,LifecycleJson.bytes(state),"the shared DATA guard must not rewrite the native map");
    }

    private static void assertRejected(ObjectNode state,SeedArtifact seed) {
        assertThrows(ContractViolationException.class,()->checkSeed(state,seed));
    }

    /** Reflection is limited to this existing pure static method; infrastructure failures never count as contract rejection. */
    private static void checkSeed(ObjectNode state,SeedArtifact seed) {
        try {
            var holder=Class.forName("org.xar.ck3.control.application.lifecycle.LifecycleComposites$JsonNodeCheck");
            var guard=holder.getDeclaredMethod("checkSeed",ObjectNode.class,SeedArtifact.class);
            guard.setAccessible(true);
            guard.invoke(null,state,seed);
        } catch(InvocationTargetException failure) {
            Throwable actual=failure.getCause();
            if(actual instanceof RuntimeException contract)throw contract;
            if(actual instanceof Error error)throw error;
            throw new AssertionError("shared DATA guard threw an unexpected checked exception",actual);
        } catch(ReflectiveOperationException failure) {
            throw new AssertionError("existing shared DATA guard could not be invoked",failure);
        }
    }

    private static FileWitness createSmall(NativeCheckpointFiles files,Path path,byte[] original) throws Exception {
        assertTrue(original.length>0&&original.length<4096,"own seed fixture files must remain below 4KiB");
        return files.createNew(path,original);
    }
    private static JsonNode token(String original) {return FullJsonTree.parse(bytes(original),128);}
    private static byte[] bytes(String original) {return original.getBytes(StandardCharsets.UTF_8);}
}
