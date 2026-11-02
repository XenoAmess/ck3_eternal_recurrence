package org.xar.ck3.control.application.checkpoint;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.List;
import java.util.Optional;
import java.security.MessageDigest;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.checkpoint.CheckpointPair.FileWitness;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.FileStatIdentity;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.FullJsonTree;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;

/** Public in-memory DATA at the file port; no filesystem qualification, Native, writer or Root authority. */
final class CheckpointVerificationResource305Test {
    @TempDir Path temporary;
    private record Fixture(CheckpointPair pair, byte[] driver, FileWitness ack) { }
    private static Fixture fixture(Path base) throws Exception {
        byte[] saveBytes = "save".getBytes(StandardCharsets.UTF_8);
        byte[] ackBytes = "ack".getBytes(StandardCharsets.UTF_8);
        var save = witness(base.resolve("save.ck3"), saveBytes, "1");
        var ack = witness(base.resolve("ack.json"), ackBytes, "3");
        var game = new GameGeneration(123, new PythonOnlyUInt64(BigInteger.valueOf(100)));
        var frame = new ProposalLifecycle.ObservationIdentity("test-machine-305", game,
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(29829),
                        BigInteger.ONE, BigInteger.valueOf(240)), "native:1", BigInteger.ONE, "episode-305"), 1);
        var checkpoint = StrictJson.object();
        checkpoint.put("status", "saved"); checkpoint.put("name", "xar_checkpoint.ck3");
        checkpoint.put("path", save.reference().path()); checkpoint.put("size", save.reference().bytes());
        checkpoint.put("sha256", save.reference().sha256()); checkpoint.put("date_raw", 240);
        checkpoint.put("history_index", 1); checkpoint.put("episode_character_id", 29829);
        checkpoint.put("episode_run_id", "episode-305"); checkpoint.put("strategy", "native-autosave-command-v1");
        checkpoint.put("java_action_id", "saved-305"); checkpoint.put("save_lineage_id", "lineage-305");
        checkpoint.set("java_game_generation", game.toJson());
        var document = StrictJson.object(); document.put("format_version", 2); document.put("pipe_name", "test-pipe-305");
        document.put("bridge_pid", 123); document.put("episode_character_id", 29829);
        document.put("episode_run_id", "episode-305"); document.putNull("managed_restore_transaction");
        var row = document.putArray("command_history").addObject(); row.put("index", 1);
        row.put("command", "save-checkpoint"); row.put("ok", true);
        row.putObject("result").set("checkpoint", checkpoint.deepCopy());
        document.set("last_checkpoint", checkpoint.deepCopy());
        byte[] raw = FullJsonTree.encode(document, DriverCheckpointStore.MAX_DRIVER_BYTES);
        var driver = witness(base.resolve("driver.json"), raw, "2");
        var pair = new CheckpointPair(save, driver, frame, "lineage-305", 1, "saved-305", ack.reference(), Instant.EPOCH);
        return new Fixture(pair, raw, ack);
    }
    private static FileWitness witness(Path path, byte[] bytes, String id) throws Exception {
        String sha = HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes));
        return new FileWitness(new ExactRef(path.toAbsolutePath().normalize().toString(), bytes.length, sha),
                new FileStatIdentity(BigInteger.valueOf(bytes.length), id, "1"));
    }
    private static DriverCheckpointStore store(CheckpointFiles files, Fixture fixture) {
        return new DriverCheckpointStore(files, Path.of(fixture.pair().driver().reference().path()), "test-pipe-305",
                new DriverCheckpointStore.SnapshotSupplier() {
                    @Override public <T> T withFrozen(DriverCheckpointStore.SnapshotWork<T> work) {
                        throw new AssertionError("verify must not persist or acquire a frozen publication callback");
                    }
                });
    }
    private static class MemoryFiles implements CheckpointFiles {
        final Fixture fixture;
        final List<String> events = new ArrayList<>();
        IOException observeFailure, readFailure, verifyFailure;
        MemoryFiles(Fixture fixture) { this.fixture = fixture; }
        @Override public Optional<FileWitness> observe(Path path) throws IOException {
            events.add("observe");
            assertEquals(Path.of(fixture.ack().reference().path()), path);
            if (observeFailure != null) throw observeFailure;
            return Optional.of(fixture.ack());
        }
        @Override public byte[] read(FileWitness expected, int maximumBytes) throws IOException {
            events.add("read"); assertSame(fixture.pair().driver(), expected);
            assertEquals(DriverCheckpointStore.MAX_DRIVER_BYTES, maximumBytes);
            if (readFailure != null) throw readFailure;
            return fixture.driver();
        }
        @Override public void verify(CheckpointPair pair) throws IOException {
            events.add("custom-verify"); assertSame(fixture.pair(), pair);
            if (verifyFailure != null) throw verifyFailure;
        }
        @Override public FileWitness replace(Path target, byte[] bytes) { throw new AssertionError("no mutation"); }
        @Override public FileWitness createNew(Path target, byte[] bytes) { throw new AssertionError("no mutation"); }
        @Override public FileWitness copyNew(FileWitness source, Path target) { throw new AssertionError("no mutation"); }
    }
    private static final class ScopedFiles extends MemoryFiles {
        final List<Scope> resources = new ArrayList<>();
        IOException firstVerifyFailure, closeFailure;
        ScopedFiles(Fixture fixture) { super(fixture); }
        @Override public CheckpointFiles.Verification beginVerification(CheckpointPair pair) {
            assertSame(fixture.pair(), pair);
            Scope resource = new Scope(resources.size() + 1, firstVerifyFailure, closeFailure);
            resources.add(resource); events.add("begin:" + resource.id); return resource;
        }
        @Override public Optional<FileWitness> observe(Path path) { throw new AssertionError("unscoped ACK read"); }
        @Override public byte[] read(FileWitness expected, int maximumBytes) { throw new AssertionError("unscoped Driver read"); }
        @Override public void verify(CheckpointPair pair) { throw new AssertionError("unscoped pair check"); }
        final class Scope implements CheckpointFiles.Verification {
            final int id;
            final IOException bodyError, closingError;
            int verifies;
            boolean closed;
            Scope(int id, IOException bodyError, IOException closingError) {
                this.id = id; this.bodyError = bodyError; this.closingError = closingError;
            }
            private void open() { assertFalse(closed, "consumer used a closed resource"); }
            @Override public Optional<FileWitness> observe(Path path) {
                open(); events.add("observe:" + id); assertEquals(Path.of(fixture.ack().reference().path()), path);
                return Optional.of(fixture.ack());
            }
            @Override public byte[] read(FileWitness expected, int maximumBytes) {
                open(); events.add("read:" + id); assertSame(fixture.pair().driver(), expected);
                assertEquals(DriverCheckpointStore.MAX_DRIVER_BYTES, maximumBytes); return fixture.driver();
            }
            @Override public void verify(CheckpointPair pair) throws IOException {
                open(); assertSame(fixture.pair(), pair); events.add("verify:" + id + ":" + ++verifies);
                if (verifies == 1 && bodyError != null) throw bodyError;
            }
            @Override public void close() throws IOException {
                assertFalse(closed, "consumer closed its resource more than once");
                closed = true; events.add("close:" + id);
                if (closingError != null) throw closingError;
            }
        }
    }

    @Test void defaultAdapterPreservesOverridesAndFailureIdentity() throws Exception {
        Fixture data = fixture(temporary);
        MemoryFiles files = new MemoryFiles(data);
        var adapter1 = files.beginVerification(data.pair());
        var adapter2 = files.beginVerification(data.pair());
        assertNotSame(adapter1, adapter2);
        assertEquals(List.of(), files.events);
        // This is only the transparent no-custody default, not Native closed-scope qualification.
        adapter1.close(); adapter2.close();
        assertEquals(List.of(), files.events);
        assertSame(data.ack(), adapter1.observe(Path.of(data.pair().nativeAckRef().path())).orElseThrow());
        assertEquals(List.of("observe"), files.events);
        assertSame(data.driver(), adapter1.read(data.pair().driver(), DriverCheckpointStore.MAX_DRIVER_BYTES));
        assertEquals(List.of("observe", "read"), files.events);
        adapter1.verify(data.pair());
        assertEquals(List.of("observe", "read", "custom-verify"), files.events);
        files.events.clear();
        IOException observeError = new IOException("observe-fail");
        files.observeFailure = observeError;
        assertSame(observeError, assertThrows(IOException.class, () -> adapter1.observe(Path.of(data.pair().nativeAckRef().path()))));
        files.observeFailure = null;
        IOException readError = new IOException("read-fail");
        files.readFailure = readError;
        assertSame(readError, assertThrows(IOException.class, () -> adapter1.read(data.pair().driver(), DriverCheckpointStore.MAX_DRIVER_BYTES)));
        files.readFailure = null;
        IOException verifyError = new IOException("verify-fail");
        files.verifyFailure = verifyError;
        assertSame(verifyError, assertThrows(IOException.class, () -> adapter1.verify(data.pair())));
        files.verifyFailure = null;
    }

    @Test void driverUsesOnlyOneScopedResourceAndOriginalOrder() throws Exception {
        Fixture data = fixture(temporary);
        ScopedFiles files = new ScopedFiles(data);
        DriverCheckpointStore store = store(files, data);
        store.verify(data.pair());
        assertEquals(1, files.resources.size());
        var resource = files.resources.getFirst();
        assertTrue(resource.closed);
        assertEquals(2, resource.verifies);
        assertEquals(List.of("begin:1", "verify:1:1", "observe:1", "read:1", "verify:1:2", "close:1"), files.events);
    }

    @Test void primaryCloseAndNextInvocationStayIndependent() throws Exception {
        Fixture data = fixture(temporary);
        ScopedFiles files = new ScopedFiles(data);
        DriverCheckpointStore store = store(files, data);
        IOException bodyError = new IOException("body-fail");
        IOException closeError = new IOException("close-fail");
        files.firstVerifyFailure = bodyError;
        files.closeFailure = closeError;
        var thrown = assertThrows(IOException.class, () -> store.verify(data.pair()));
        assertSame(bodyError, thrown);
        assertArrayEquals(new Throwable[] { closeError }, thrown.getSuppressed());
        assertEquals(1, files.resources.size());
        assertTrue(files.resources.getFirst().closed);
        assertEquals(List.of("begin:1", "verify:1:1", "close:1"), files.events);
        files.events.clear();
        files.firstVerifyFailure = null;
        files.closeFailure = null;
        store.verify(data.pair());
        assertEquals(2, files.resources.size());
        assertNotSame(files.resources.getFirst(), files.resources.get(1));
        assertTrue(files.resources.get(1).closed);
        assertEquals(List.of("begin:2", "verify:2:1", "observe:2", "read:2", "verify:2:2", "close:2"), files.events);
        files.events.clear();
        IOException closeOnly = new IOException("close-only-fail");
        files.closeFailure = closeOnly;
        var thrown2 = assertThrows(IOException.class, () -> store.verify(data.pair()));
        assertSame(closeOnly, thrown2);
        assertEquals(0, thrown2.getSuppressed().length);
        assertEquals(3, files.resources.size());
        assertNotSame(files.resources.get(1), files.resources.get(2));
        assertTrue(files.resources.get(2).closed);
        assertEquals(List.of("begin:3", "verify:3:1", "observe:3", "read:3", "verify:3:2", "close:3"), files.events);
    }
}
