package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.time.Instant;
import java.util.Arrays;
import java.util.HashMap;
import java.util.Map;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.checkpoint.CheckpointFiles;
import org.xar.ck3.control.application.checkpoint.CheckpointPair;
import org.xar.ck3.control.application.checkpoint.DriverCheckpointStore;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.FileStatIdentity;
import org.xar.ck3.control.contracts.FullJsonTree;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;

/**
 * Pure historical DATA selection against the unchanged public archived Driver decoder.
 * No Root/writer/Session/issuer is constructed. Ref/file-witness DTOs grant no physical permission.
 * Archive read order, late archive IO, whole SAVE verification and runtime speed remain untested.
 */
final class SavedDriverReplay315Test {
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

    private static DriverCheckpointStore store() {
        var noFiles = new CheckpointFiles() {
            @Override public Optional<CheckpointPair.FileWitness> observe(Path path) { throw new AssertionError("no IO"); }
            @Override public byte[] read(CheckpointPair.FileWitness witness, int maximum) { throw new AssertionError("no IO"); }
            @Override public CheckpointPair.FileWitness replace(Path path, byte[] raw) { throw new AssertionError("no IO"); }
            @Override public CheckpointPair.FileWitness createNew(Path path, byte[] raw) { throw new AssertionError("no IO"); }
            @Override public CheckpointPair.FileWitness copyNew(CheckpointPair.FileWitness from, Path path) { throw new AssertionError("no IO"); }
        };
        var noSnapshots = new DriverCheckpointStore.SnapshotSupplier() {
            @Override public <T> T withFrozen(DriverCheckpointStore.SnapshotWork<T> work) throws IOException {
                throw new AssertionError("no supplier or publication");
            }
        };
        return new DriverCheckpointStore(noFiles, LABELS.resolve("driver.json"), "test-pipe", noSnapshots);
    }

    private static DriverStateSnapshot.Complete select(DriverCheckpointStore store, CheckpointPair pair, byte[] raw,
            Map<CheckpointPair, Map.Entry<byte[], DriverStateSnapshot.Complete>> validated) throws Exception {
        Method method = CanonicalSaveReceiptVerifier.class.getDeclaredMethod("readSavedDriver",
                DriverCheckpointStore.class, CheckpointPair.class, byte[].class, Map.class);
        method.setAccessible(true);
        try { return (DriverStateSnapshot.Complete) method.invoke(null, store, pair, raw, validated); }
        catch (InvocationTargetException wrapped) {
            if (wrapped.getCause() instanceof Exception failure) throw failure;
            if (wrapped.getCause() instanceof Error failure) throw failure;
            throw new AssertionError(wrapped.getCause());
        }
    }

    private static void sameFull(DriverStateSnapshot.Complete expected, DriverStateSnapshot.Complete actual) {
        assertEquals(expected, actual);
        assertEquals(expected.session(), actual.session());
        assertArrayEquals(expected.encode(), actual.encode());
    }

    private static void sameFailure(DriverCheckpointStore store, CheckpointPair pair, byte[] raw,
            Map<CheckpointPair, Map.Entry<byte[], DriverStateSnapshot.Complete>> validated) {
        Exception expected = assertThrows(Exception.class, () -> store.readArchivedSnapshot(pair, raw));
        Exception actual = assertThrows(Exception.class, () -> select(store, pair, raw, validated));
        assertEquals(expected.getClass(), actual.getClass());
        assertEquals(expected.getMessage(), actual.getMessage());
    }

    @Test void validatedDataReuseAndChangedOriginalsMatchPublicDecoder() throws Exception {
        var store = store(); byte[] original = encode(document("original")); var pair = pair(original, "2");
        var first = store.readArchivedSnapshot(pair, original);
        var independent = store.readArchivedSnapshot(pair, original.clone());
        byte[] expected = independent.encode();
        Map<CheckpointPair, Map.Entry<byte[], DriverStateSnapshot.Complete>> validated = new HashMap<>();
        validated.put(pair, Map.entry(original.clone(), first));
        byte[] input = original.clone(); var reused = select(store, pair, input, validated);
        assertSame(first, reused); sameFull(independent, reused);
        Arrays.fill(input, (byte) 0); Arrays.fill(original, (byte) 0);
        assertArrayEquals(expected, reused.encode());
        byte[] retainedRaw = validated.get(pair).getKey();
        assertArrayEquals(encode(document("original")), retainedRaw);

        byte[] changed = encode(document("changed")); var changedPair = pair(changed, "3");
        var changedOracle = store.readArchivedSnapshot(changedPair, changed);
        var changedResult = select(store, changedPair, changed.clone(), validated);
        assertNotSame(first, changedResult); sameFull(changedOracle, changedResult);
        assertFalse(Arrays.equals(expected, changedResult.encode()));
        Arrays.fill(changed, (byte) 0); sameFull(changedOracle, changedResult);

        // Different source witness DATA, same bytes: public decoder accepts; it grants no physical lease.
        var otherWitness = pair(retainedRaw, "4"); assertNotEquals(pair, otherWitness);
        var witnessResult = select(store, otherWitness, retainedRaw.clone(), validated);
        assertNotSame(first, witnessResult); sameFull(store.readArchivedSnapshot(otherWitness, retainedRaw), witnessResult);
        var fresh = select(store, pair, retainedRaw.clone(), new HashMap<>());
        assertNotSame(first, fresh); sameFull(independent, fresh);
        assertSame(first, select(store, pair, retainedRaw.clone(), validated));
        assertArrayEquals(expected, first.encode());
    }

    @Test void changedOrInvalidOriginalsKeepDecoderFailures() throws Exception {
        var store = store(); byte[] raw = encode(document("original")); var pair = pair(raw, "2");
        Map<CheckpointPair, Map.Entry<byte[], DriverStateSnapshot.Complete>> validated = new HashMap<>();
        validated.put(pair, Map.entry(raw.clone(), store.readArchivedSnapshot(pair, raw)));
        sameFailure(store, pair, encode(document("changed")), validated);
        byte[] malformed = "not json".getBytes(StandardCharsets.UTF_8);
        sameFailure(store, pair(malformed, "3"), malformed, validated);
        var incomplete = document("original"); incomplete.remove("managed_restore_transaction");
        byte[] absent = encode(incomplete); sameFailure(store, pair(absent, "3"), absent, validated);
        var wrongSource = document("original"); wrongSource.put("bridge_pid", 124);
        byte[] foreign = encode(wrongSource); sameFailure(store, pair(foreign, "3"), foreign, validated);
        var wrongAnchor = document("original");
        ((ObjectNode) wrongAnchor.get("last_checkpoint")).put("java_action_id", "another-save");
        ((ObjectNode) wrongAnchor.get("command_history").get(0).get("result").get("checkpoint"))
                .put("java_action_id", "another-save");
        byte[] different = encode(wrongAnchor); sameFailure(store, pair(different, "3"), different, validated);
        sameFull(store.readArchivedSnapshot(pair, raw), select(store, pair, raw.clone(), validated));
        assertArrayEquals(raw, validated.get(pair).getKey());
    }
}
