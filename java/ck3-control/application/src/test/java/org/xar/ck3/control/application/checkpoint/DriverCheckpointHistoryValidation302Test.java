package org.xar.ck3.control.application.checkpoint;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.checkpoint.CheckpointPair.FileWitness;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.FileStatIdentity;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.FullJsonTree;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;

/** Pure DATA and public file-port regression; no physical-file or private SAVE qualification. */
final class DriverCheckpointHistoryValidation302Test {
    private static final String ROOT = "D:/offline-data302/";
    private static byte[] bytes(String value) { return value.getBytes(StandardCharsets.UTF_8); }
    private static ObservationIdentity frame() {
        return new ObservationIdentity("test-machine-1", new GameGeneration(123, new PythonOnlyUInt64(BigInteger.valueOf(100))),
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(29829), BigInteger.ONE,
                        BigInteger.valueOf(240)), "native:1", BigInteger.ONE, "episode-1"), 1);
    }
    private static FileWitness witness(String name, byte[] raw, String id) {
        return new FileWitness(new ExactRef(ROOT + name, raw.length, DriverCheckpointStore.sha256(raw)),
                new FileStatIdentity(BigInteger.valueOf(raw.length), id, "100"));
    }
    private static final class Fixture implements CheckpointFiles {
        final FileWitness save = witness("save.ck3", bytes("save"), "1");
        final FileWitness ack = witness("ack.json", bytes("{}"), "2");
        final byte[] raw;
        final FileWitness driver;
        final CheckpointPair pair;
        final List<String> events = new ArrayList<>();
        final IOException late = new IOException("late source observation refused");
        boolean refuseLate;
        int saveReads;
        Fixture(String firstIndex, boolean managed, String lineage) {
            String checkpoint = "{\"status\":\"saved\",\"name\":\"xar_checkpoint.ck3\",\"path\":\"" + save.reference().path()
                    + "\",\"size\":4,\"sha256\":\"" + save.reference().sha256() + "\",\"date_raw\":240,\"history_index\":2,"
                    + "\"episode_character_id\":29829,\"episode_run_id\":\"episode-1\",\"strategy\":\"native-autosave-command-v1\","
                    + "\"java_action_id\":\"save-302\",\"save_lineage_id\":\"" + lineage + "\",\"java_game_generation\":"
                    + frame().game().toJson() + "}";
            raw = bytes("{\"format_version\":2,\"pipe_name\":\"test-pipe\",\"bridge_pid\":123,\"episode_character_id\":29829,"
                    + "\"episode_run_id\":\"episode-1\",\"command_history\":[{\"index\":" + firstIndex
                    + ",\"command\":\"opaque-old\",\"ok\":false,\"opaque\":[1.234567890123456789,-0.0,null,{\"unknown\":true}]},"
                    + "{\"index\":2,\"command\":\"save-checkpoint\",\"ok\":true,\"result\":{\"checkpoint\":" + checkpoint + "}}],"
                    + "\"last_checkpoint\":" + checkpoint + ",\"rollback_war_failure\":null,\"managed_restore_transaction\":"
                    + (managed ? "{\"pending\":true}" : "null")
                    + ",\"succession_expectation\":null,\"campaign_goal\":null,\"rollback_war_failures\":[]}");
            driver = witness("driver.json", raw, "3");
            pair = new CheckpointPair(save, driver, frame(), "lineage-302", 2, "save-302", ack.reference(),
                    Instant.parse("2026-11-02T00:00:00Z"));
        }
        DriverCheckpointStore store() {
            return new DriverCheckpointStore(this, Path.of(ROOT + "driver.json"), "test-pipe",
                    new DriverCheckpointStore.SnapshotSupplier() {
                        @Override public <T> T withFrozen(DriverCheckpointStore.SnapshotWork<T> work) {
                            throw new AssertionError("verification may not request a new snapshot");
                        }
                    });
        }
        @Override public Optional<FileWitness> observe(Path path) throws IOException {
            String name = path.getFileName().toString(); events.add("observe:" + name);
            if (name.equals("save.ck3")) {
                if (++saveReads > 1 && refuseLate) throw late;
                return Optional.of(save);
            }
            if (name.equals("driver.json")) return Optional.of(driver);
            if (name.equals("ack.json")) return Optional.of(ack);
            throw new AssertionError("unexpected DATA path " + path);
        }
        @Override public byte[] read(FileWitness expected, int maximumBytes) {
            assertEquals(driver, expected); assertTrue(raw.length <= maximumBytes);
            events.add("read:driver.json"); return raw.clone();
        }
        @Override public FileWitness replace(Path path, byte[] rawBytes) { throw new AssertionError("no publication"); }
        @Override public FileWitness createNew(Path path, byte[] rawBytes) { throw new AssertionError("no publication"); }
        @Override public FileWitness copyNew(FileWitness source, Path path) { throw new AssertionError("no publication"); }
    }
    private static List<String> prefix() {
        return List.of("observe:save.ck3", "observe:driver.json", "observe:ack.json", "read:driver.json");
    }
    @Test void validAnchorRetainsCompleteOpaqueHistoryAndExistingObservationOrder() throws IOException {
        Fixture input = new Fixture("1", false, "lineage-302");
        DriverCheckpointStore store = input.store(); store.verify(input.pair);
        assertEquals(List.of("observe:save.ck3", "observe:driver.json", "observe:ack.json", "read:driver.json",
                "observe:save.ck3", "observe:driver.json"), input.events);
        DriverStateSnapshot.Complete actual = store.readArchivedSnapshot(input.pair, input.raw);
        assertEquals(2, actual.commandHistory().size()); assertEquals("test-pipe", actual.session().pipeName());
        var row = FullJsonTree.parse(actual.commandHistory().getFirst().originalRow().json(), 16384);
        assertEquals("1.234567890123456789", row.get("opaque").get(0).asText());
        assertEquals("-0.0", row.get("opaque").get(1).asText());
        assertTrue(row.get("opaque").get(2).isNull()); assertTrue(row.get("opaque").get(3).get("unknown").booleanValue());
        assertInstanceOf(DriverStateSnapshot.Missing.class, actual.successionLifecycle());
    }
    @Test void managedRestoreFailurePrecedesMalformedHistory() {
        Fixture input = new Fixture("true", true, "lineage-302");
        var failure = assertThrows(IllegalArgumentException.class, () -> input.store().verify(input.pair));
        assertEquals("pending managed restore must be reconciled before SAVE", failure.getMessage());
        assertEquals(prefix(), input.events);
    }
    @Test void gapBooleanAndFloatIndicesStillFailThroughRealAnchorValidation() {
        for (String index : List.of("3", "true", "1.0")) {
            Fixture input = new Fixture(index, false, "lineage-302");
            assertThrows(IllegalArgumentException.class, () -> input.store().verify(input.pair), index);
            assertEquals(prefix(), input.events);
        }
    }
    @Test void anchorMismatchAndRequiredLateObservationRemainFailures() {
        Fixture wrong = new Fixture("1", false, "another-lineage");
        var mismatch = assertThrows(IllegalArgumentException.class, () -> wrong.store().verify(wrong.pair));
        assertEquals("physical SAVE, Driver, date, actor, episode, lineage, action and history agree", mismatch.getMessage());
        assertEquals(prefix(), wrong.events);
        Fixture late = new Fixture("1", false, "lineage-302"); late.refuseLate = true;
        assertSame(late.late, assertThrows(IOException.class, () -> late.store().verify(late.pair)));
        assertEquals(List.of("observe:save.ck3", "observe:driver.json", "observe:ack.json", "read:driver.json",
                "observe:save.ck3"), late.events);
    }
}
