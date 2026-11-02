package org.xar.ck3.control.application.checkpoint;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.contracts.DecimalTokenNode;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.FileStatIdentity;
import org.xar.ck3.control.contracts.FullJsonTree;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;

/** Pure DATA plus controlled in-memory CheckpointFiles; no actual filesystem or Root authority. */
final class DriverAnchor339Test {
    private static final String SAVE_SHA = "b".repeat(64);
    private static final String ACTION = "save-1";
    private static final String LINEAGE = "lineage-1";
    private static final Path LABELS = Path.of("data-only-fixture").toAbsolutePath();
    private static final GameGeneration GAME = new GameGeneration(123,
            new PythonOnlyUInt64(new BigInteger("9007199254740993")));
    private static final ObservationIdentity FRAME = new ObservationIdentity("test-machine-1", GAME,
            new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(29829),
                    BigInteger.ONE, BigInteger.valueOf(240)), "native:1", BigInteger.ONE, "episode-1"), 1);
    private static final Instant AT = Instant.parse("2020-01-01T00:00:00Z");

    private static ObjectNode document(String opaque) {
        var checkpoint = StrictJson.object();
        checkpoint.put("status", "saved"); checkpoint.put("name", "xar_checkpoint.ck3");
        checkpoint.put("path", LABELS.resolve("save.ck3").toString()); checkpoint.put("size", 10);
        checkpoint.put("sha256", SAVE_SHA); checkpoint.put("date_raw", 240); checkpoint.put("history_index", 1);
        checkpoint.put("episode_character_id", 29829); checkpoint.put("episode_run_id", "episode-1");
        checkpoint.put("strategy", "native-autosave-command-v1"); checkpoint.put("java_action_id", ACTION);
        checkpoint.put("save_lineage_id", LINEAGE); checkpoint.set("java_game_generation", GAME.toJson());
        checkpoint.putNull("succession_lifecycle");
        var root = StrictJson.object();
        root.put("format_version", 2); root.put("pipe_name", "test-pipe"); root.put("bridge_pid", 123);
        root.put("episode_character_id", 29829); root.put("episode_run_id", "episode-1");
        var row = root.putArray("command_history").addObject();
        row.put("index", 1); row.put("command", "save-checkpoint"); row.put("ok", true);
        row.putObject("result").set("checkpoint", checkpoint.deepCopy());
        root.set("last_checkpoint", checkpoint);
        root.putNull("rollback_war_failure"); root.putNull("managed_restore_transaction");
        root.putNull("succession_expectation"); root.putNull("succession_lifecycle");
        root.putObject("campaign_goal").put("opaque", opaque); root.putArray("rollback_war_failures");
        return root;
    }

    private static byte[] encode(ObjectNode document) {
        return FullJsonTree.encode(document, DriverCheckpointStore.MAX_DRIVER_BYTES);
    }

    private static CheckpointPair pair(byte[] raw, String fileId) {
        var save = new CheckpointPair.FileWitness(new ExactRef(LABELS.resolve("save.ck3").toString(), 10, SAVE_SHA),
                new FileStatIdentity(BigInteger.TEN, "1", "0"));
        var driver = new CheckpointPair.FileWitness(new ExactRef(LABELS.resolve("driver.json").toString(),
                raw.length, DriverJson.sha256(raw)), new FileStatIdentity(BigInteger.valueOf(raw.length), fileId, "0"));
        return new CheckpointPair(save, driver, FRAME, LINEAGE, 1, ACTION,
                new ExactRef(LABELS.resolve("ack.bin").toString(), 10, "c".repeat(64)), AT);
    }

    private static DriverCheckpointStore store(CheckpointFiles files) {
        var snapshots = new DriverCheckpointStore.SnapshotSupplier() {
            @Override public <T> T withFrozen(DriverCheckpointStore.SnapshotWork<T> work) {
                throw new AssertionError("no snapshot supplier or publication");
            }
        };
        return new DriverCheckpointStore(files, LABELS.resolve("driver.json"), "test-pipe", snapshots);
    }

    private static final class MemoryFiles implements CheckpointFiles {
        private final CheckpointPair pair;
        private final byte[] raw;
        final List<String> events = new ArrayList<>();
        IOException finalVerifyFailure;
        int observations;
        MemoryFiles(CheckpointPair pair, byte[] raw) { this.pair=pair; this.raw=raw.clone(); }
        @Override public Optional<CheckpointPair.FileWitness> observe(Path path) throws IOException {
            events.add("observe:"+path.getFileName());
            observations++;
            if (observations==4 && finalVerifyFailure!=null) throw finalVerifyFailure;
            if (path.equals(Path.of(pair.save().reference().path()))) return Optional.of(pair.save());
            if (path.equals(Path.of(pair.driver().reference().path()))) return Optional.of(pair.driver());
            if (path.equals(Path.of(pair.nativeAckRef().path()))) return Optional.of(new CheckpointPair.FileWitness(
                    pair.nativeAckRef(), new FileStatIdentity(BigInteger.valueOf(pair.nativeAckRef().bytes()), "3", "0")));
            throw new AssertionError("unexpected file label "+path);
        }
        @Override public byte[] read(CheckpointPair.FileWitness expected, int maximum) {
            events.add("read:"+Path.of(expected.reference().path()).getFileName());
            assertEquals(pair.driver(), expected); assertEquals(DriverCheckpointStore.MAX_DRIVER_BYTES, maximum);
            return raw.clone();
        }
        @Override public CheckpointPair.FileWitness replace(Path path, byte[] bytes) { throw new AssertionError("no write"); }
        @Override public CheckpointPair.FileWitness createNew(Path path, byte[] bytes) { throw new AssertionError("no create"); }
        @Override public CheckpointPair.FileWitness copyNew(CheckpointPair.FileWitness from, Path path) { throw new AssertionError("no copy"); }
    }

    private static void strictFailure(byte[] raw) {
        var files = new MemoryFiles(pair(raw,"2"), raw);
        var strict = assertThrows(IllegalArgumentException.class, () -> DriverStateSnapshot.decodeComplete(raw));
        var archived = assertThrows(IllegalArgumentException.class, () -> store(files).readArchivedSnapshot(pair(raw,"2"),raw));
        assertEquals(strict.getMessage(),archived.getMessage());
        assertEquals(strict.getCause()==null?null:strict.getCause().getClass(),
                archived.getCause()==null?null:archived.getCause().getClass());
        assertTrue(files.events.isEmpty(),"archived DATA decoder has no file callbacks");
    }

    @Test void archivedAnchorSharesStrictParseWithoutChangingTokensSchemaOrOwnership() throws Exception {
        ObjectNode doc = document("opaque");
        var goal = (ObjectNode)doc.get("campaign_goal");
        goal.set("negative_zero",new DecimalTokenNode("-0.00"));
        goal.set("exponent",new DecimalTokenNode("1.2300e+9"));
        goal.put("wide_original",new BigInteger("18446744073709551616"));
        byte[] raw = (" \r\n"+new String(encode(doc),StandardCharsets.UTF_8)+" \n").getBytes(StandardCharsets.UTF_8);
        var expected = DriverStateSnapshot.decodeComplete(raw);
        var p = pair(raw,"2"); var files = new MemoryFiles(p,raw);
        var actual = store(files).readArchivedSnapshot(p,raw);
        assertEquals(expected,actual); assertArrayEquals(expected.encode(),actual.encode());
        String encoded = new String(actual.encode(),StandardCharsets.UTF_8);
        assertTrue(encoded.contains("-0.00")); assertTrue(encoded.contains("1.2300e+9"));
        assertTrue(encoded.contains("18446744073709551616"));
        assertTrue(files.events.isEmpty());
        byte[] retained = actual.encode();
        Arrays.fill(raw,(byte)0);
        byte[] borrowed = ((DriverStateSnapshot.Value)actual.campaignGoal()).json(); Arrays.fill(borrowed,(byte)0);
        assertArrayEquals(retained,actual.encode());

        strictFailure(new byte[]{(byte)0xc3,0x28});
        strictFailure("{\"format_version\":2,\"format_version\":2}".getBytes(StandardCharsets.UTF_8));
        strictFailure((new String(encode(document("opaque")),StandardCharsets.UTF_8)+" true").getBytes(StandardCharsets.UTF_8));
        var unknown=document("opaque");unknown.put("unknown_driver_field",1);strictFailure(encode(unknown));
        var missing=document("opaque");missing.remove("managed_restore_transaction");strictFailure(encode(missing));
        var fractional=document("opaque");((ObjectNode)fractional.get("command_history").get(0)).set("index",new DecimalTokenNode("1.0"));strictFailure(encode(fractional));
        strictFailure("[".repeat(66).concat("0").concat("]".repeat(66)).getBytes(StandardCharsets.UTF_8));

        byte[] valid=encode(document("opaque")); var originalPair=pair(valid,"2");
        byte[] invalid=valid.clone();invalid[0]=(byte)'!';
        var mismatch=assertThrows(IllegalArgumentException.class,()->store(new MemoryFiles(originalPair,valid)).readArchivedSnapshot(originalPair,invalid));
        assertEquals("archived complete saved Driver differs from the original physical pair",mismatch.getMessage());
        var wrong=document("opaque");
        ((ObjectNode)wrong.get("last_checkpoint")).put("java_action_id","wrong");
        ((ObjectNode)wrong.get("command_history").get(0).get("result").get("checkpoint")).put("java_action_id","wrong");
        byte[] badAnchor=encode(wrong);DriverStateSnapshot.decodeComplete(badAnchor);
        var anchor=assertThrows(IllegalArgumentException.class,()->store(new MemoryFiles(pair(badAnchor,"2"),badAnchor)).readArchivedSnapshot(pair(badAnchor,"2"),badAnchor));
        assertEquals("physical SAVE, Driver, date, actor, episode, lineage, action and history agree",anchor.getMessage());
        var typedNull=document("opaque");typedNull.putNull("last_checkpoint");
        byte[] nullAnchor=encode(typedNull);DriverStateSnapshot.decodeComplete(nullAnchor);
        assertEquals("required Driver object, missing/null are distinct",assertThrows(IllegalArgumentException.class,()->store(new MemoryFiles(pair(nullAnchor,"2"),nullAnchor)).readArchivedSnapshot(pair(nullAnchor,"2"),nullAnchor)).getMessage());
    }

    @Test void originalReadKeepsExactFileCallbacksSessionBeforeAnchorAndLateFailure() throws Exception {
        byte[] raw=encode(document("opaque")); var p=pair(raw,"2");
        var expected=DriverStateSnapshot.decodeComplete(raw);
        var files=new MemoryFiles(p,raw);
        assertEquals(expected,store(files).readVerifiedOriginal(p,expected.session()));
        assertEquals(List.of("observe:save.ck3","observe:driver.json","observe:ack.bin","read:driver.json","observe:save.ck3","observe:driver.json"),files.events);

        var late=new MemoryFiles(p,raw);var marker=new IOException("late-original-final-verify339");late.finalVerifyFailure=marker;
        assertSame(marker,assertThrows(IOException.class,()->store(late).readVerifiedOriginal(p,expected.session())));
        assertEquals(List.of("observe:save.ck3","observe:driver.json","observe:ack.bin","read:driver.json","observe:save.ck3"),late.events);

        var wrong=document("opaque");
        ((ObjectNode)wrong.get("last_checkpoint")).put("java_action_id","wrong");
        ((ObjectNode)wrong.get("command_history").get(0).get("result").get("checkpoint")).put("java_action_id","wrong");
        byte[] bad=encode(wrong);var badPair=pair(bad,"2");var wrongFiles=new MemoryFiles(badPair,bad);
        var other=new DriverStateSnapshot.Session("other-pipe",expected.session().bridgePid(),expected.session().actorId(),expected.session().episodeRunId());
        var failure=assertThrows(IllegalArgumentException.class,()->store(wrongFiles).readVerifiedOriginal(badPair,other));
        assertEquals("physical saved Driver differs from its actual verified source session",failure.getMessage());
        assertEquals(List.of("observe:save.ck3","observe:driver.json","observe:ack.bin","read:driver.json"),wrongFiles.events);

        var anchorFiles=new MemoryFiles(badPair,bad);
        assertEquals("physical SAVE, Driver, date, actor, episode, lineage, action and history agree",assertThrows(IllegalArgumentException.class,()->store(anchorFiles).readVerifiedOriginal(badPair,expected.session())).getMessage());
        assertEquals(wrongFiles.events,anchorFiles.events);
    }
}
