package org.xar.ck3.control.wave2.runtime.closedadoption;

import com.fasterxml.jackson.databind.JsonNode;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.Objects;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.runtime.clockreader.ClockPinnedFiles;
import org.xar.ck3.control.wave2.runtime.clockreader.ClockPinnedFiles.Pin;
import static org.junit.jupiter.api.Assertions.*;

/** Reuses the actual original writer fixture. Its SDK authority and all Clock Game facts remain synthetic. */
public final class ClockOriginalWriterLockFixture {
    private ClockOriginalWriterLockFixture() { }

    @FunctionalInterface public interface HookFactory {
        PreparedHook prepare(Path canonicalPath, Pin expectedHead) throws IOException, InterruptedException;
    }
    @FunctionalInterface public interface CloseCustody { void close() throws IOException; }
    public record PreparedHook(OriginalWriterTransaction.LockedRecheck hook, CloseCustody custody) implements AutoCloseable {
        public PreparedHook { Objects.requireNonNull(hook); Objects.requireNonNull(custody); }
        @Override public void close() throws IOException { custody.close(); }
    }
    public record Rejection(IOException failure, int sourceChecks, int lockedChecks, WindowsJobProcess.CommandResult actualExit) {
        public Rejection { Objects.requireNonNull(failure); Objects.requireNonNull(actualExit); }
    }

    /** The actual original writer must reach its locked frame, re-evaluate its own sources, and then refuse this hook. */
    public static Rejection assertRejected(HookFactory factory) throws IOException, InterruptedException {
        Objects.requireNonNull(factory);
        var fixture = ClosedAdoptionTransactionTest.fixture();
        Path canonical = fixture.target().canonicalPath(); byte[] before = Files.readAllBytes(canonical);
        Pin expectedHead = ClockPinnedFiles.capture(canonical.toAbsolutePath(), ClockPinnedFiles.hash(before), 65_536);
        AtomicInteger sourceChecks = new AtomicInteger(), lockedChecks = new AtomicInteger();
        AtomicReference<WindowsFileWriterSession> launched = new AtomicReference<>();
        Throwable pending = null;
        try (PreparedHook prepared = factory.prepare(canonical, expectedHead)) {
            ClosedAdoptionMaterial.CurrentSource current = () -> { sourceChecks.incrementAndGet(); return fixture.material(); };
            IOException failure = assertThrows(IOException.class, () -> OriginalWriterTransaction.execute(fixture.target(), current,
                    target -> {
                        assertEquals(fixture.target(), target);
                        var actual = WindowsFileWriterSession.start(ClosedAdoptionTransactionTest.settings(fixture),
                                WindowsFileWriterSession.Mode.WRITER);
                        launched.set(actual); return actual;
                    }, target -> {
                        lockedChecks.incrementAndGet();
                        if (sourceChecks.get() < 2) { throw new IOException("original source/cache/reducer recheck did not precede the Clock hook"); }
                        prepared.hook().verify(target);
                    }));
            assertTrue(sourceChecks.get() >= 2); assertEquals(1, lockedChecks.get());
            WindowsFileWriterSession actual = launched.get(); assertNotNull(actual, "the actual original writer must have started");
            var exit = actual.actualCommandResult().orElseThrow();
            assertNotEquals(0, exit.exitCode(), "the actual original writer must reject EOF without an approval frame");
            assertEquals(0, exit.accounting().activeProcesses()); assertTrue(Files.isRegularFile(actual.terminalPath()));
            assertArrayEquals(before, Files.readAllBytes(canonical), "the actual original canonical head must remain byte-for-byte unchanged");
            assertFalse(Files.exists(canonical.resolveSibling("ROOT-CONTINUITY-WINDOW-EVENTS").resolve("00000241.json")));
            assertNoApproval(fixture.root());
            return new Rejection(failure, sourceChecks.get(), lockedChecks.get(), exit);
        } catch (IOException | InterruptedException | RuntimeException | AssertionError failure) {
            pending = failure; throw failure;
        } finally {
            WindowsFileWriterSession actual = launched.get();
            if (actual != null && actual.actualCommandResult().isEmpty()) {
                try { actual.closeOwnedInput(); actual.awaitActualExit(); }
                catch (IOException | InterruptedException | RuntimeException cleanup) {
                    if (pending != null) { pending.addSuppressed(cleanup); } else { throw cleanup; }
                }
            }
        }
    }

    private static void assertNoApproval(Path root) throws IOException {
        try (var paths = Files.list(root)) {
            List<Path> requests = paths.filter(path -> path.getFileName().toString().startsWith("closed-partial-writer-")
                    && path.getFileName().toString().endsWith(".request.jsonl")).toList();
            assertEquals(1, requests.size()); Path request = requests.get(0);
            assertTrue(Files.size(request) <= WindowsFileWriterSession.MAX_WRITER_STREAM_BYTES);
            List<String> frames = Files.readAllLines(request, StandardCharsets.UTF_8);
            assertEquals(1, frames.size(), "only the original start request may have been sent");
            JsonNode frame = StrictJson.parse(frames.get(0).getBytes(StandardCharsets.UTF_8), OriginalWriterTransaction.MAX_PROTOCOL_BYTES);
            assertEquals("xar.java-original-closed-partial-writer-request/v1", StrictJson.text(frame.get("schema")));
            assertFalse(frame.has("approved"), "Clock refusal must happen before the approval frame is sent");
        }
    }
}
