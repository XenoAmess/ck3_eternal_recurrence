package org.xar.ck3.control.wave2.finance.capture;

import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.io.UncheckedIOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.FileAlreadyExistsException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Duration;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicReference;
import java.util.stream.Stream;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.Timeout;
import org.junit.jupiter.api.io.TempDir;
import static org.junit.jupiter.api.Assertions.*;

class PythonStdinCaptureTest {
    private static final Path REPOSITORY = Path.of(".").toAbsolutePath().normalize();
    private static final Path PYTHON = REPOSITORY.resolve("not-started-python.exe");

    @Test void explicitCallerAndHelperOriginsAreBothChecked(@TempDir Path wrongOrigin) throws Exception {
        Path caller = Path.of(PythonStdinCaptureTest.class.getProtectionDomain().getCodeSource().getLocation().toURI());
        Path helper = Path.of(PythonStdinCapture.class.getProtectionDomain().getCodeSource().getLocation().toURI());
        PythonStdinCapture.requireCompiledLauncher(PythonStdinCaptureTest.class, caller, helper);
        assertThrows(IOException.class, () -> PythonStdinCapture.requireCompiledLauncher(
                PythonStdinCaptureTest.class, caller, wrongOrigin));
        assertThrows(IOException.class, () -> PythonStdinCapture.requireCompiledLauncher(
                PythonStdinCaptureTest.class, wrongOrigin, helper));
    }

    @Test void bootstrapClassesAndRelativeOriginsNeverQualifyAsCaptureLaunchers() throws Exception {
        Path helper = Path.of(PythonStdinCapture.class.getProtectionDomain().getCodeSource().getLocation().toURI());
        assertThrows(IOException.class, () -> PythonStdinCapture.requireCompiledLauncher(String.class, helper, helper));
        assertThrows(IllegalArgumentException.class, () -> PythonStdinCapture.requireCompiledLauncher(
                PythonStdinCaptureTest.class, Path.of("relative"), helper));
    }

    @Test void actualJdkChildReceivesExactMultilineUtf8AndEofWithoutStartingPython() throws Exception {
        String script = "text = '''\"quoted\" \\path 中文'''\nprint(text)\n";
        AtomicReference<ProcessBuilder> observed = new AtomicReference<>();
        Path classes = Path.of(PythonStdinCaptureTest.class.getProtectionDomain().getCodeSource().getLocation().toURI());
        String previousRoot = System.setProperty(PythonStdinCapture.CLASS_ROOT_PROPERTY, classes.toString());
        try { PythonStdinCapture.requireCompiledLauncher(PythonStdinCaptureTest.class); }
        finally {
            if (previousRoot == null) { System.clearProperty(PythonStdinCapture.CLASS_ROOT_PROPERTY); }
            else { System.setProperty(PythonStdinCapture.CLASS_ROOT_PROPERTY, previousRoot); }
        }
        Path java = Path.of(System.getProperty("java.home"), "bin", System.getProperty("os.name").startsWith("Windows") ? "java.exe" : "java");
        var result = PythonStdinCapture.run(invocation(script, 1024), builder -> {
            observed.set(builder);
            // This fixture is Java, so default JUnit never invokes a Python oracle.
            return PythonStdinFixtureCommand.builder(java.toString(), classes.toString(),
                    PythonStdinEchoChild.class).directory(builder.directory())
                    .redirectError(builder.redirectError()).start();
        });
        assertEquals(List.of(PYTHON.toString(), "-B", "-X", "utf8", "-", "repo with spaces", "new-output.json"),
                observed.get().command());
        assertEquals(REPOSITORY.toFile(), observed.get().directory());
        assertEquals(ProcessBuilder.Redirect.INHERIT, observed.get().redirectError());
        assertArrayEquals(script.getBytes(StandardCharsets.UTF_8), result.stdout());
    }

    @Test void boundedReplyAndClosedStdinUseTheSameCaptureEntry() throws Exception {
        FixtureProcess exact = new FixtureProcess(new byte[] {1, 2, 3}, 0, true, false);
        var result = PythonStdinCapture.run(invocation("print('中文')\n", 3), ignored -> exact);
        assertTrue(exact.input.closed);
        assertArrayEquals("print('中文')\n".getBytes(StandardCharsets.UTF_8), exact.input.toByteArray());
        assertArrayEquals(new byte[] {1, 2, 3}, result.stdout());
        FixtureProcess oversized = new FixtureProcess(new byte[] {1, 2, 3, 4}, 0, true, false);
        assertThrows(IllegalStateException.class,
                () -> PythonStdinCapture.run(invocation("pass\n", 3), ignored -> oversized));
    }

    @Test void nonzeroExitAndEmptyStdoutStayFailures() {
        assertThrows(IllegalStateException.class, () -> PythonStdinCapture.run(invocation("pass\n", 8),
                ignored -> new FixtureProcess(new byte[] {1}, 7, true, false)));
        assertThrows(IllegalStateException.class, () -> PythonStdinCapture.run(invocation("pass\n", 8),
                ignored -> new FixtureProcess(new byte[0], 0, true, false)));
    }

    @Test void timeoutDestroysTheChildAndClosesStdin() {
        FixtureProcess child = new FixtureProcess(new byte[] {1}, 0, false, false);
        assertThrows(IllegalStateException.class, () -> PythonStdinCapture.run(invocation("pass\n", 8), ignored -> child));
        assertTrue(child.destroyed);
        assertTrue(child.input.closed);
    }

    @Test void stdinWriteFailureCannotBecomeAProducerPass() {
        FixtureProcess child = new FixtureProcess(new byte[] {1}, 0, true, true);
        IOException failure = assertThrows(IOException.class,
                () -> PythonStdinCapture.run(invocation("pass\n", 8), ignored -> child));
        assertInstanceOf(IOException.class, failure.getCause());
        assertTrue(child.input.closed);
    }

    @Test void resultAndInvocationRetainDefensiveCopies() throws Exception {
        List<String> arguments = new ArrayList<>(List.of("kept"));
        var invocation = new PythonStdinCapture.Invocation(PYTHON, REPOSITORY, "pass\n", arguments, Duration.ofSeconds(15), 8);
        arguments.clear();
        assertEquals(List.of("kept"), invocation.arguments());
        byte[] raw = new byte[] {1}; var result = new PythonStdinCapture.Result(raw); raw[0] = 2;
        byte[] returned = result.stdout(); returned[0] = 3;
        assertArrayEquals(new byte[] {1}, result.stdout());
        assertThrows(UnsupportedOperationException.class, () -> invocation.arguments().clear());
    }

    @Test void invalidInvocationsRejectBeforeAnyChildStart() {
        assertThrows(IllegalArgumentException.class, () -> invocation("", 1));
        assertThrows(IllegalArgumentException.class, () -> invocation("pass\n", 0));
        assertThrows(IllegalArgumentException.class, () -> invocation("pass\n", 98_305));
        assertThrows(IllegalArgumentException.class, () -> new PythonStdinCapture.Invocation(PYTHON, REPOSITORY,
                "pass\n", List.of(), Duration.ZERO, 1));
        assertThrows(IllegalArgumentException.class, () -> new PythonStdinCapture.Invocation(Path.of("relative-python"),
                REPOSITORY, "pass\n", List.of(), Duration.ofSeconds(1), 1));
        assertThrows(IllegalArgumentException.class,
                () -> PythonStdinCapture.requireCompiledLauncher(PythonStdinCaptureTest.class, Path.of("relative-classes")));
        assertThrows(IOException.class, () -> PythonStdinCapture.requireCompiledLauncher(String.class, REPOSITORY));
        assertThrows(IOException.class,
                () -> PythonStdinCapture.requireCompiledLauncher(PythonStdinCaptureTest.class, REPOSITORY));
    }

    @Test @Timeout(20)
    void normalMainExitStillStopsTheObservedRealJdkDescendant(@TempDir Path scratch) throws Exception {
        AtomicReference<ObservedProcess> started = new AtomicReference<>();
        try {
            var result = runTree("normal", scratch, Duration.ofSeconds(15), started);
            assertEquals("ok\n", new String(result.stdout(), StandardCharsets.UTF_8));
            assertFalse(started.get().destroyed, "the main fixture exited normally before cleanup");
            assertTreeStopped(started.get());
        } finally { stopFixture(started.get()); }
    }

    @Test @Timeout(20)
    void timeoutWaitsForTheRealJdkMainAndObservedDescendantToExit(@TempDir Path scratch) throws Exception {
        AtomicReference<ObservedProcess> started = new AtomicReference<>();
        try {
            IllegalStateException failure = assertThrows(IllegalStateException.class,
                    () -> runTree("timeout", scratch, Duration.ofSeconds(5), started));
            assertEquals(0, failure.getSuppressed().length, "timeout cleanup must finish successfully");
            assertTrue(started.get().destroyed);
            assertTrue(started.get().exitReadAfterDestroy, "destroy ACK must be followed by a successful waitFor");
            assertTreeStopped(started.get());
        } finally { stopFixture(started.get()); }
    }

    @Test @Timeout(20)
    void nonzeroRealJdkMainStillStopsItsObservedDescendant(@TempDir Path scratch) throws Exception {
        AtomicReference<ObservedProcess> started = new AtomicReference<>();
        try {
            IllegalStateException failure = assertThrows(IllegalStateException.class,
                    () -> runTree("nonzero", scratch, Duration.ofSeconds(15), started));
            assertEquals("producer exit 7", failure.getMessage());
            assertEquals(0, failure.getSuppressed().length, "nonzero cleanup must finish successfully");
            assertFalse(started.get().destroyed);
            assertTreeStopped(started.get());
        } finally { stopFixture(started.get()); }
    }

    @Test @Timeout(20)
    void outputCapFailureStillStopsTheRealJdkObservedDescendant(@TempDir Path scratch) throws Exception {
        AtomicReference<ObservedProcess> started = new AtomicReference<>();
        try {
            IllegalStateException failure = assertThrows(IllegalStateException.class,
                    () -> runTree("oversized", scratch, Duration.ofSeconds(15), started));
            assertEquals("producer stdout missing or exceeds finite capture budget", failure.getMessage());
            assertEquals(0, failure.getSuppressed().length, "output-cap cleanup must finish successfully");
            assertFalse(started.get().destroyed);
            assertTreeStopped(started.get());
        } finally { stopFixture(started.get()); }
    }

    private static PythonStdinCapture.Result runTree(String mode, Path scratch, Duration timeout,
            AtomicReference<ObservedProcess> started) throws Exception {
        Path classes = Path.of(PythonStdinCaptureTest.class.getProtectionDomain().getCodeSource().getLocation().toURI());
        Path java = Path.of(System.getProperty("java.home"), "bin", System.getProperty("os.name").startsWith("Windows") ? "java.exe" : "java");
        Path release = scratch.resolve("descendant-observed");
        var invocation = new PythonStdinCapture.Invocation(PYTHON, REPOSITORY, "pass\n", List.of(), timeout, 64);
        return PythonStdinCapture.run(invocation, builder -> {
            Process actual = PythonStdinFixtureCommand.builder(java.toString(), classes.toString(),
                    PythonStdinTreeChild.class, mode, release.toString(), java.toString(), classes.toString())
                    .directory(builder.directory()).redirectError(builder.redirectError()).start();
            ObservedProcess observed = new ObservedProcess(actual, release);
            started.set(observed);
            return observed;
        });
    }

    private static void assertTreeStopped(ObservedProcess child) throws InterruptedException {
        assertNotNull(child);
        assertFalse(child.observed.isEmpty(), "handshake requires a descendant observed by the shared helper");
        assertTrue(child.waitFor(0, TimeUnit.NANOSECONDS), "main process actual exit");
        assertFalse(child.isAlive());
        assertTrue(child.observed.stream().noneMatch(ProcessHandle::isAlive), "observed descendant actual exit");
    }

    private static void stopFixture(ObservedProcess child) throws InterruptedException {
        if (child == null) { return; }
        // Failure cleanup for the test itself; assertions above run before this.
        for (ProcessHandle handle : child.observed) { if (handle.isAlive()) { handle.destroyForcibly(); } }
        if (child.isAlive()) { child.destroyForcibly(); }
        child.waitFor(2, TimeUnit.SECONDS);
        for (ProcessHandle handle : child.observed) {
            long deadline = System.nanoTime() + TimeUnit.SECONDS.toNanos(2);
            while (handle.isAlive() && System.nanoTime() < deadline) { TimeUnit.MILLISECONDS.sleep(2); }
        }
    }

    /** Delegates actual JDK process behavior; only the observation handshake is added. */
    private static final class ObservedProcess extends Process {
        private final Process actual;
        private final Path release;
        private volatile List<ProcessHandle> observed = List.of();
        private volatile boolean destroyed;
        private volatile boolean exitReadAfterDestroy;
        private ObservedProcess(Process actual, Path release) { this.actual = actual; this.release = release; }
        @Override public OutputStream getOutputStream() { return actual.getOutputStream(); }
        @Override public InputStream getInputStream() { return actual.getInputStream(); }
        @Override public InputStream getErrorStream() { return actual.getErrorStream(); }
        @Override public int waitFor() throws InterruptedException { return actual.waitFor(); }
        @Override public boolean waitFor(long timeout, TimeUnit unit) throws InterruptedException {
            boolean exited = actual.waitFor(timeout, unit);
            if (destroyed && exited) { exitReadAfterDestroy = true; }
            return exited;
        }
        @Override public int exitValue() { return actual.exitValue(); }
        @Override public boolean isAlive() { return actual.isAlive(); }
        @Override public void destroy() { destroyed = true; actual.destroy(); }
        @Override public Process destroyForcibly() { destroyed = true; actual.destroyForcibly(); return this; }
        @Override public Stream<ProcessHandle> descendants() {
            List<ProcessHandle> snapshot;
            try (var handles = actual.descendants()) { snapshot = handles.toList(); }
            if (!snapshot.isEmpty()) {
                observed = snapshot;
                try { Files.writeString(release, "observed", StandardOpenOption.CREATE_NEW); }
                catch (FileAlreadyExistsException alreadyReleased) { /* same observation handshake */ }
                catch (IOException error) { throw new UncheckedIOException(error); }
            }
            return snapshot.stream();
        }
    }

    private static PythonStdinCapture.Invocation invocation(String script, int maxOutputBytes) {
        return new PythonStdinCapture.Invocation(PYTHON, REPOSITORY, script,
                List.of("repo with spaces", "new-output.json"), Duration.ofSeconds(15), maxOutputBytes);
    }

    private static final class TrackingInput extends ByteArrayOutputStream {
        private boolean closed;
        @Override public void close() throws IOException { closed = true; super.close(); }
    }

    private static final class FixtureProcess extends Process {
        private final TrackingInput input = new TrackingInput();
        private final InputStream output;
        private final int exit;
        private final boolean completed;
        private final boolean failInput;
        private boolean destroyed;
        private FixtureProcess(byte[] output, int exit, boolean completed, boolean failInput) {
            this.output = new ByteArrayInputStream(output); this.exit = exit; this.completed = completed; this.failInput = failInput;
        }
        @Override public OutputStream getOutputStream() {
            if (!failInput) { return input; }
            return new OutputStream() {
                @Override public void write(int value) throws IOException { throw new IOException("fixture stdin refused"); }
                @Override public void close() throws IOException { input.close(); }
            };
        }
        @Override public InputStream getInputStream() { return output; }
        @Override public InputStream getErrorStream() { return InputStream.nullInputStream(); }
        @Override public int waitFor() { return exit; }
        @Override public boolean waitFor(long timeout, TimeUnit unit) { return completed || destroyed; }
        @Override public int exitValue() { return exit; }
        @Override public boolean isAlive() { return !completed && !destroyed; }
        @Override public void destroy() { destroyed = true; }
        @Override public Process destroyForcibly() { destroy(); return this; }
        @Override public Stream<ProcessHandle> descendants() { return Stream.empty(); }
    }
}

/** One finite JVM command for every real test fixture child and descendant. */
final class PythonStdinFixtureCommand {
    private PythonStdinFixtureCommand() { }
    static ProcessBuilder builder(String java, String classes, Class<?> main, String... arguments) {
        List<String> command = new ArrayList<>(List.of(java, "-Xms8m", "-Xmx24m", "-Xss512k",
                "-XX:+UseSerialGC", "-XX:ActiveProcessorCount=2", "-XX:CICompilerCount=2",
                "-XX:MaxMetaspaceSize=32m", "-XX:CompressedClassSpaceSize=8m",
                "-XX:ReservedCodeCacheSize=16m", "-cp", classes, main.getName()));
        command.addAll(List.of(arguments));
        return new ProcessBuilder(command);
    }
}

final class PythonStdinEchoChild {
    private PythonStdinEchoChild() { }
    public static void main(String[] args) throws IOException {
        System.out.write(System.in.readAllBytes()); System.out.flush();
    }
}

/** Tiny JDK-only fixture. Its leaf is released only after the helper observes it. */
final class PythonStdinTreeChild {
    private PythonStdinTreeChild() { }
    public static void main(String[] args) throws Exception {
        if (args.length == 1 && args[0].equals("leaf")) { Thread.sleep(30_000); return; }
        System.in.readAllBytes();
        Process leaf = PythonStdinFixtureCommand.builder(args[2], args[3],
                PythonStdinTreeChild.class, "leaf").redirectOutput(ProcessBuilder.Redirect.DISCARD)
                .redirectError(ProcessBuilder.Redirect.DISCARD).start();
        leaf.getOutputStream().close();
        Path release = Path.of(args[1]);
        long deadline = System.nanoTime() + TimeUnit.SECONDS.toNanos(12);
        while (!Files.exists(release)) {
            if (System.nanoTime() >= deadline) { throw new IllegalStateException("descendant was not observed"); }
            TimeUnit.MILLISECONDS.sleep(2);
        }
        System.out.write(args[0].equals("oversized") ? new byte[65] : "ok\n".getBytes(StandardCharsets.UTF_8));
        System.out.flush();
        if (args[0].equals("nonzero")) { System.exit(7); }
        if (args[0].equals("timeout")) { Thread.sleep(30_000); }
    }
}
