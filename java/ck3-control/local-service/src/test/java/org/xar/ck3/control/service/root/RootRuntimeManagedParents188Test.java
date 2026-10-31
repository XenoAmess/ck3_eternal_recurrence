package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.continuity.writer.StorageWriteGuard.*;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.checkpoint.CheckpointFiles;
import org.xar.ck3.control.application.checkpoint.CheckpointPair.FileWitness;
import org.xar.ck3.control.application.checkpoint.NativeCheckpointFiles;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.FreshContinuityGenesis;
import org.xar.ck3.control.continuity.writer.ContinuityWriter;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;

/** Actual finite D software file operations; no Game, SourceSession, or transition authority. */
class RootRuntimeManagedParents188Test {
    @TempDir Path directory;
    private final List<RootRuntimeStorageGuard> guards = new ArrayList<>();

    @AfterEach void closeGuards() throws IOException {
        IOException failure = null;
        for (int i = guards.size() - 1; i >= 0; i--) try { guards.get(i).close(); }
        catch (IOException rejected) { if (failure == null) failure = rejected; else failure.addSuppressed(rejected); }
        if (failure != null) throw failure;
    }

    private final class Fixture {
        final Path state;
        final WriterContracts.InitialLayout initial;
        final RootRuntimeStorageGuard guard;
        final CheckpointFiles files;
        Fixture(String name, long cap, CheckpointFiles actualFiles) throws IOException {
            Path base = Files.createDirectory(directory.resolve(name));
            state = Files.createDirectory(base.resolve("state"));
            Path continuity = Files.createDirectory(state.resolve("continuity"));
            Path artifacts = Files.createDirectory(base.resolve("artifacts"));
            String machine = WindowsJobProcess.currentMachineId();
            var plan = new FreshContinuityGenesis.Plan(machine, 1, 10958);
            byte[] request = FreshContinuityGenesis.encode(plan);
            Path requestPath = Files.write(base.resolve("fresh-genesis-request.json"), request);
            var ref = new ExactRef(requestPath.toString(), request.length, DriverJson.sha256(request));
            initial = new WriterContracts.InitialLayout(continuity.resolve("snapshot.json"), continuity.resolve("anchor.json"), machine);
            AtomicReference<ContinuityWriter> writer = new AtomicReference<>();
            guard = RootRuntimeStorageGuard.ordinary(initial, artifacts, () -> {
                ContinuityWriter actual = writer.get();
                if (actual == null) throw new IOException("writer not constructed");
                return actual;
            }, List.of(state, continuity, artifacts), cap, Clock.systemUTC());
            guards.add(guard);
            var initialized = ContinuityWriter.initializeFresh(plan, ref, initial, guard);
            writer.set(new ContinuityWriter(initialized.layout(), List.of(ref), new WriterContracts.TransitionAuthority() {
                @Override public String revalidate(ContinuityState old, WriterContracts.Request input) { throw new AssertionError("storage-only fixture"); }
                @Override public ContinuityState reduce(ContinuityState old, WriterContracts.Request input) { throw new AssertionError("storage-only fixture"); }
            }, Clock.systemUTC(), guard));
            files = guard.checkpointFiles(actualFiles);
            guard.requireCompleteAdmission();
        }
    }

    private static long charged(RootRuntimeStorageGuard guard) {
        return guard.accounting().roots().stream().mapToLong(RootRuntimeStorageGuard.RootAccounting::measuredChargedUpperBytes).sum();
    }
    private static long outstanding(RootRuntimeStorageGuard guard) {
        return guard.accounting().roots().stream().mapToLong(RootRuntimeStorageGuard.RootAccounting::outstandingPeakBytes).sum();
    }

    @Test void ordinaryManagedParentsAndFailureAccounting() throws IOException {
        var raw = new NativeCheckpointFiles();
        long cap = 128L * 1024L;
        Fixture normal = new Fixture("normal", cap, raw);
        byte[] body = new byte[8192];
        for (int i = 0; i < body.length; i++) body[i] = (byte) (i % 127);
        Path target = normal.state.resolve("new-a/new-b/pair.json");
        assertFalse(Files.exists(target.getParent().getParent()));
        long before = charged(normal.guard);
        var witness = normal.files.createNew(target, body);
        raw.verify(witness);
        assertTrue(Files.isDirectory(target.getParent().getParent()));
        assertTrue(Files.isDirectory(target.getParent()));
        assertArrayEquals(body, normal.files.read(witness, body.length));
        assertEquals(DriverJson.sha256(body), witness.reference().sha256());
        long nativeFileCharge = SharedSourceFiles.nativeFile(target).allocatedBytes();
        assertTrue(nativeFileCharge > 0);
        assertEquals(2L * RootRuntimeStorageContract.DIRECTORY_GUARD + nativeFileCharge, charged(normal.guard) - before,
                "both new directories and the actual file allocation must be retained");
        assertEquals(RootRuntimeStorageGuard.Status.ADMITTED, normal.guard.accounting().status());
        assertEquals(0, normal.guard.accounting().unresolvedWrites());
        assertEquals(0, outstanding(normal.guard));
        System.out.println("PASS188 ordinary two-parent actual file and exact directory/file allocation");

        // Finite budget still rejects the file. Any completed parent mkdir remains accounted.
        Path oversized = normal.state.resolve("budget-a/budget-b/too-large.bin");
        long beforeBudget = charged(normal.guard);
        assertThrows(IOException.class, () -> normal.files.createNew(oversized, new byte[256 * 1024]));
        assertFalse(Files.exists(oversized));
        long completedDirectories = (Files.isDirectory(oversized.getParent()) ? 1L : 0L)
                + (Files.isDirectory(oversized.getParent().getParent()) ? 1L : 0L);
        assertEquals(beforeBudget + completedDirectories * RootRuntimeStorageContract.DIRECTORY_GUARD, charged(normal.guard));
        assertTrue(charged(normal.guard) <= cap);
        assertEquals(0, normal.guard.accounting().unresolvedWrites());
        assertEquals(0, outstanding(normal.guard));

        // Existing explicit plans never acquire implicit DirectoryCreate phases.
        Path explicit = normal.state.resolve("explicit-a/explicit-b/reject.bin");
        var plan = new WritePlan(normal.initial.lock(), List.of(new FileCreate(explicit, body.length)));
        assertThrows(IOException.class, () -> normal.guard.write(plan, () -> normal.files.createNew(explicit, body)));
        assertFalse(Files.exists(explicit));
        assertFalse(Files.exists(explicit.getParent().getParent()));
        System.out.println("PASS188 finite budget and explicit missing-directory plan remain enforced");

        // Actual software file creation followed by a lost method return, using the existing file port seam.
        AtomicInteger physicalCreates = new AtomicInteger();
        CheckpointFiles lostReturn = new CheckpointFiles() {
            @Override public Optional<FileWitness> observe(Path path) throws IOException { return raw.observe(path); }
            @Override public byte[] read(FileWitness expected, int maximumBytes) throws IOException { return raw.read(expected, maximumBytes); }
            @Override public FileWitness replace(Path path, byte[] bytes) throws IOException { return raw.replace(path, bytes); }
            @Override public FileWitness copyNew(FileWitness source, Path path) throws IOException { return raw.copyNew(source, path); }
            @Override public FileWitness createNew(Path path, byte[] bytes) throws IOException {
                physicalCreates.incrementAndGet();
                raw.createNew(path, bytes);
                throw new IOException("software file exists but its createNew return was lost");
            }
        };
        Fixture unknown = new Fixture("unknown", cap, lostReturn);
        Path lost = unknown.state.resolve("lost-a/lost-b/lost.bin");
        long beforeLost = charged(unknown.guard);
        assertThrows(IOException.class, () -> unknown.files.createNew(lost, body));
        assertArrayEquals(body, Files.readAllBytes(lost));
        assertTrue(charged(unknown.guard) >= beforeLost + 2L * RootRuntimeStorageContract.DIRECTORY_GUARD);
        assertEquals(RootRuntimeStorageGuard.Status.UNKNOWN_WRITE, unknown.guard.accounting().status());
        assertTrue(unknown.guard.accounting().unresolvedWrites() > 0);
        assertTrue(outstanding(unknown.guard) > 0);
        Path next = unknown.state.resolve("next-a/next-b/blocked.bin");
        assertThrows(IOException.class, () -> unknown.files.createNew(next, body));
        assertFalse(Files.exists(next.getParent().getParent()));
        assertEquals(1, physicalCreates.get());
        System.out.println("PASS188 lost-return UNKNOWN retains directory charge and forbids a second physical write");
    }
}
