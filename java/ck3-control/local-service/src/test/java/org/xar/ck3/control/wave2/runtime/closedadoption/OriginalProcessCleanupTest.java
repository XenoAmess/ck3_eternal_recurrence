package org.xar.ck3.control.wave2.runtime.closedadoption;

import static org.junit.jupiter.api.Assertions.*;

import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;
import java.time.Instant;
import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.function.Executable;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.contracts.StrictJson;

/** Real original Python writer and native Jobs; the reused SDK authority is explicitly synthetic. */
class OriginalProcessCleanupTest {
    @Test void closeMarkerIoFailureStillConsumesActualChildAndPreservesLockedIOException() throws Exception {
        lockedFailure(false);
    }
    @Test void closeMarkerIoFailureStillConsumesActualChildAndPreservesLockedError() throws Exception {
        lockedFailure(true);
    }
    private static void lockedFailure(boolean errorPrimary) throws Exception {
        var fixture = ClosedAdoptionTransactionTest.fixture();
        byte[] before = Files.readAllBytes(fixture.target().canonicalPath());
        var launched = new AtomicReference<WindowsFileWriterSession>();
        IOException refusal = new IOException("test-owned locked refusal before approval");
        AssertionError fatal = new AssertionError("test-owned locked Error before approval");
        Executable action = () -> OriginalWriterTransaction.execute(fixture.target(),fixture::material,target -> {
            var actual = WindowsFileWriterSession.start(ClosedAdoptionTransactionTest.settings(fixture),WindowsFileWriterSession.Mode.WRITER);
            launched.set(actual); return actual;
        },target -> {
            Path request = writerRequest(fixture);
            // This is a real filesystem failure in closeOwnedInput, and the real reader observes EOF exists.
            Files.createDirectory(request.resolveSibling(request.getFileName()+".closed"));
            if (errorPrimary) { throw fatal; }
            throw refusal;
        });
        try {
            Throwable observed = errorPrimary ? assertThrows(AssertionError.class,action) : assertThrows(IOException.class,action);
            assertSame(errorPrimary ? fatal : refusal,observed);
            assertTrue(java.util.Arrays.stream(observed.getSuppressed()).anyMatch(IOException.class::isInstance));
            var actual = launched.get(); var result = terminal(actual);
            assertNotEquals(0,result.exitCode()); assertFalse(result.passed());
            String stderr = transcript(actual,false);
            assertTrue(stderr.contains("one bounded complete Java writer protocol line"),stderr);
            assertArrayEquals(before,Files.readAllBytes(fixture.target().canonicalPath()));
            assertFalse(Files.exists(fixture.target().canonicalPath().resolveSibling("ROOT-CONTINUITY-WINDOW-EVENTS").resolve("00000241.json")));
            assertThrows(IOException.class,actual::awaitActualExit);
        } finally { finish(launched.get()); }
    }

    @Test void actualGuardErrorConsumesTerminalAndCannotBecomeSuccessOnSecondAwait() throws Exception {
        var fixture = ClosedAdoptionTransactionTest.fixture();
        var base = ClosedAdoptionTransactionTest.settings(fixture);
        var awaiting = new AtomicBoolean(); var launched = new AtomicReference<WindowsFileWriterSession>();
        AssertionError fatal = new AssertionError("test-owned actual capacity guard Error");
        var settings = settings(base,base.timeout(),base.leaseDeadline(),base.environment(),() -> {
            base.capacityGuard().run(); if (awaiting.get()) { throw fatal; }
        });
        try {
            assertSame(fatal,assertThrows(AssertionError.class,() -> OriginalWriterTransaction.execute(fixture.target(),fixture::material,target -> {
                var actual = WindowsFileWriterSession.start(settings,WindowsFileWriterSession.Mode.WRITER); launched.set(actual);
                return delegate(actual,() -> awaiting.set(true));
            })));
            var actual = launched.get(); terminal(actual); transcript(actual,true);
            // If the root already exited, its actual result may be passed; the original Error still forbids qualification.
            assertSame(fatal,assertThrows(AssertionError.class,actual::awaitActualExit));
            assertEquals(241,headSequence(fixture));
        } finally { finish(launched.get()); }
    }

    @Test void rootZeroWithRealLiveDescendantCannotReturnCommittedAndKeepsRawReadback() throws Exception {
        var fixture = ClosedAdoptionTransactionTest.fixture(); var base = ClosedAdoptionTransactionTest.settings(fixture);
        Path extension = fixture.root().resolve("test-owned-descendant-startup"); Files.createDirectory(extension);
        Files.writeString(extension.resolve("sitecustomize.py"),"""
                import subprocess,sys
                subprocess.Popen([sys.executable,'-S','-c','import time;time.sleep(30)'],
                    stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
                sys.stderr.write('test-owned finite descendant started\\n')
                sys.stderr.flush()
                """,StandardCharsets.UTF_8);
        Map<String,String> environment = new HashMap<>(base.environment());
        environment.put("PYTHONPATH",extension+java.io.File.pathSeparator+environment.getOrDefault("PYTHONPATH",""));
        var settings = settings(base,base.timeout(),base.leaseDeadline(),environment,base.capacityGuard());
        var launched = new AtomicReference<WindowsFileWriterSession>();
        try {
            IOException failure = assertThrows(IOException.class,() -> OriginalWriterTransaction.execute(fixture.target(),fixture::material,target -> {
                var actual = WindowsFileWriterSession.start(settings,WindowsFileWriterSession.Mode.WRITER); launched.set(actual); return actual;
            }));
            var actual = launched.get(); var result = terminal(actual);
            assertEquals(0,result.exitCode()); assertEquals("root_exited_with_live_children",result.stopReason());
            assertFalse(result.passed()); assertTrue(failure.getMessage().contains("actual Job did not pass"));
            assertTrue(transcript(actual,true).contains("test-owned finite descendant started"));
            assertSame(failure,assertThrows(IOException.class,actual::awaitActualExit));
            // Approval already committed: preserve UNKNOWN/post-commit evidence; this test never retries or rolls back.
            assertEquals(241,headSequence(fixture));
        } finally { finish(launched.get()); }
    }

    @Test void rootZeroAfterOwnMonotonicTimeoutCannotReturnCommitted() throws Exception { lateReturn(false); }
    @Test void rootZeroAfterOwnUtcLeaseCannotReturnCommitted() throws Exception { lateReturn(true); }
    private static void lateReturn(boolean expireLease) throws Exception {
        var fixture = ClosedAdoptionTransactionTest.fixture(); var base = ClosedAdoptionTransactionTest.settings(fixture);
        var settings = settings(base,expireLease ? base.timeout() : Duration.ofSeconds(5),
                expireLease ? Instant.now().plusSeconds(5) : base.leaseDeadline(),base.environment(),base.capacityGuard());
        var launched = new AtomicReference<WindowsFileWriterSession>(); var delayed = new AtomicBoolean();
        try {
            IOException failure = assertThrows(IOException.class,() -> OriginalWriterTransaction.execute(fixture.target(),fixture::material,target -> {
                var actual = WindowsFileWriterSession.start(settings,WindowsFileWriterSession.Mode.WRITER); launched.set(actual);
                return delegate(actual,() -> {
                    if (delayed.compareAndSet(false,true)) {
                        // Real readback and EOF have occurred; only the test caller delays consumption of the real exit.
                        long millis = expireLease ? Math.max(0,Duration.between(Instant.now(),settings.leaseDeadline()).toMillis()) : settings.timeout().toMillis();
                        Thread.sleep(millis+100);
                    }
                });
            }));
            var actual = launched.get(); var result = terminal(actual);
            assertTrue(result.passed()); assertEquals(0,result.exitCode()); assertNull(result.stopReason());
            assertTrue(failure.getMessage().contains("deadline expired before successful return"));
            transcript(actual,true); assertEquals(241,headSequence(fixture));
            assertSame(failure,assertThrows(IOException.class,actual::awaitActualExit));
        } finally { finish(launched.get()); }
    }

    @Test void applicationPreservesPostCommitPublicationErrorAndConsumesWriterStreams() throws Exception {
        var fixture = ClosedAdoptionTransactionTest.fixture();
        var commits = new AtomicInteger(); var qualifications = new AtomicInteger();
        AssertionError refusal = new AssertionError("test-owned post-commit publication Error");
        assertSame(refusal,assertThrows(AssertionError.class,() -> ClosedAdoptionApplication.runOriginal(
                fixture.target(),fixture::material,fixture::material,fixture::canonical,
                raw -> { throw refusal; },raw -> {
                    qualifications.incrementAndGet(); return ClosedAdoptionTransactionTest.publish(fixture.root().resolve("must-not-publish.json"),raw);
                },ClosedAdoptionTransactionTest.settings(fixture),value -> commits.incrementAndGet())));
        assertEquals(1,commits.get()); assertEquals(0,qualifications.get()); assertEquals(241,headSequence(fixture));
        Path request = writerRequest(fixture);
        Path terminal = request.resolveSibling(request.getFileName()+".terminal.json");
        var result = StrictJson.parse(Files.readAllBytes(terminal));
        assertEquals(ClosedAdoptionTransactionTest.MACHINE,result.get("machine_id").textValue());
        assertEquals(0,result.get("exit_code").intValue()); assertEquals(0,result.get("active_processes").intValue());
        assertNull(result.get("stop_reason").textValue());
        transcript(request.resolveSibling(request.getFileName()+".stdout.jsonl"),request.resolveSibling(request.getFileName()+".stderr.log"),true);
        try (var files = Files.list(fixture.root())) {
            assertFalse(files.anyMatch(path -> path.getFileName().toString().startsWith("closed-partial-cold_consumer-")));
        }
    }

    @FunctionalInterface private interface BeforeAwait { void run() throws InterruptedException; }
    private static OriginalWriterTransaction.ManagedProcess delegate(WindowsFileWriterSession actual, BeforeAwait before) {
        return new OriginalWriterTransaction.ManagedProcess() {
            @Override public InputStream stdout() { return actual.stdout(); }
            @Override public OutputStream stdin() { return actual.stdin(); }
            @Override public void closeOwnedInput() throws IOException { actual.closeOwnedInput(); }
            @Override public OriginalWriterTransaction.ActualExit awaitActualExit() throws IOException, InterruptedException {
                before.run(); return actual.awaitActualExit();
            }
        };
    }
    private static WindowsFileWriterSession.Settings settings(WindowsFileWriterSession.Settings base, Duration timeout,
            Instant deadline, Map<String,String> environment, Runnable guard) {
        return new WindowsFileWriterSession.Settings(base.python(),base.repo(),base.outputRoot(),base.memoryLimitBytes(),
                timeout,deadline,environment,base.mechanicalSource(),base.coldOwnerSource(),guard);
    }
    private static Path writerRequest(ClosedAdoptionTransactionTest.Fixture fixture) throws IOException {
        try (var files = Files.list(fixture.root())) {
            var requests = files.filter(path -> path.getFileName().toString().startsWith("closed-partial-writer-")
                    && path.getFileName().toString().endsWith(".request.jsonl")).toList();
            assertEquals(1,requests.size()); return requests.get(0);
        }
    }
    private static long headSequence(ClosedAdoptionTransactionTest.Fixture fixture) throws IOException {
        return StrictJson.parse(Files.readAllBytes(fixture.target().canonicalPath())).get("sequence").longValue();
    }
    private static WindowsJobProcess.CommandResult terminal(WindowsFileWriterSession actual) throws IOException {
        assertNotNull(actual); var result = actual.actualCommandResult().orElseThrow();
        assertTrue(result.identity().pid()>0); assertTrue(Long.parseUnsignedLong(result.identity().creationFiletimeDecimal())>0);
        assertEquals(0,result.accounting().activeProcesses()); assertEquals(WindowsJobProcess.REQUIRED_FLAGS,result.accounting().limitFlags());
        var row = StrictJson.parse(Files.readAllBytes(actual.terminalPath()));
        assertEquals(ClosedAdoptionTransactionTest.MACHINE,row.get("machine_id").textValue());
        assertEquals(result.identity().pid(),row.get("pid").longValue());
        assertEquals(result.identity().creationFiletimeDecimal(),row.get("creation_filetime").textValue());
        assertEquals(result.exitCode(),row.get("exit_code").intValue()); assertEquals(0,row.get("active_processes").intValue());
        assertEquals(result.stopReason(),row.get("stop_reason").isNull() ? null : row.get("stop_reason").textValue());
        Instant.parse(row.get("observed_at_utc").textValue()); return result;
    }
    private static String transcript(WindowsFileWriterSession actual, boolean approved) throws IOException {
        return transcript(actual.stdoutPath(),actual.stderrPath(),approved);
    }
    private static String transcript(Path stdout, Path stderr, boolean approved) throws IOException {
        Path request = stdout.resolveSibling(stdout.getFileName().toString().replace(".stdout.jsonl",""));
        byte[] requests = Files.readAllBytes(request), replies = Files.readAllBytes(stdout), errors = Files.readAllBytes(stderr);
        assertTrue(requests.length>0 && requests.length<=WindowsFileWriterSession.MAX_WRITER_STREAM_BYTES);
        assertTrue(replies.length>0 && replies.length<=WindowsFileWriterSession.MAX_WRITER_STREAM_BYTES); assertTrue(errors.length<=1_048_576);
        var sent = new ByteArrayInputStream(requests); var received = new ByteArrayInputStream(replies);
        assertEquals("xar.java-original-closed-partial-writer-request/v1",OriginalWriterTransaction.read(sent).get("schema").textValue());
        assertEquals("xar.java-original-writer-locked/v1",OriginalWriterTransaction.read(received).get("schema").textValue());
        if (approved) {
            assertTrue(OriginalWriterTransaction.read(sent).get("approved").booleanValue());
            var readback = OriginalWriterTransaction.read(received);
            assertEquals("xar.java-original-closed-partial-writer-readback/v1",readback.get("schema").textValue());
            assertFalse(readback.get("original_actions_replayed").booleanValue()); assertFalse(readback.get("raw_pending_modified").booleanValue());
        }
        assertEquals(0,sent.available()); assertEquals(0,received.available());
        String errorText = new String(errors,StandardCharsets.UTF_8); assertArrayEquals(errors,errorText.getBytes(StandardCharsets.UTF_8));
        return errorText;
    }
    private static void finish(WindowsFileWriterSession actual) {
        if (actual != null && actual.actualCommandResult().isEmpty()) {
            OriginalProcessCleanup.suppressing(actual,new AssertionError("test-owned final cleanup"));
        }
    }
}
