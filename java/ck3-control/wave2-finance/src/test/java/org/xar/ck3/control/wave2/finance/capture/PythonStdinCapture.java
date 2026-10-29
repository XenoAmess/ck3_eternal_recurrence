package org.xar.ck3.control.wave2.finance.capture;

import java.io.IOException;
import java.net.URISyntaxException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.TimeoutException;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicReference;

/**
 * Shared offline producer transport. Capture has one deadline; cleanup has a
 * separate five-second wait budget for the child and every descendant seen here.
 * ProcessHandle polling cannot establish complete tree custody: an unobserved
 * descendant may outlive an exiting parent. The qualified outer Job owner must
 * still prove actual Job membership and zero active processes.
 */
public final class PythonStdinCapture {
    public static final String CLASS_ROOT_PROPERTY = "xar.capture.classRoot";
    private static final Duration CLEANUP_TIMEOUT = Duration.ofSeconds(5);
    private PythonStdinCapture() { }

    public record Invocation(Path python, Path repository, String script,
            List<String> arguments, Duration timeout, int maxOutputBytes) {
        public Invocation {
            Objects.requireNonNull(python); Objects.requireNonNull(repository);
            Objects.requireNonNull(script); Objects.requireNonNull(arguments); Objects.requireNonNull(timeout);
            if (!python.isAbsolute() || !repository.isAbsolute() || script.isEmpty()
                    || script.getBytes(StandardCharsets.UTF_8).length > 262_144
                    || timeout.isZero() || timeout.isNegative() || timeout.compareTo(Duration.ofSeconds(90)) > 0
                    || maxOutputBytes < 1 || maxOutputBytes > 98_304) {
                throw new IllegalArgumentException("finite absolute-path Python stdin invocation required");
            }
            arguments = List.copyOf(arguments);
        }
    }

    public record Result(byte[] stdout) {
        public Result { stdout = stdout.clone(); }
        @Override public byte[] stdout() { return stdout.clone(); }
    }

    @FunctionalInterface
    interface Starter { Process start(ProcessBuilder builder) throws IOException; }

    /** Observe the actual compiled origin; build/source/artifact qualification stays with the outer owner. */
    public static void requireCompiledLauncher(Class<?> launcher) throws IOException {
        String configured = System.getProperty(CLASS_ROOT_PROPERTY);
        if (configured == null || configured.isBlank()) {
            throw new IllegalArgumentException("explicit " + CLASS_ROOT_PROPERTY + " required for compiled capture");
        }
        requireCompiledLauncher(launcher, Path.of(configured));
    }

    /**
     * Maven keeps a caller's test classes separate from this shared test jar.
     * The outer compiled-capture owner must independently pin both inventories.
     * This origin check grants no source, build, artifact or capture qualification.
     */
    public static void requireCompiledLauncher(Class<?> launcher, Path launcherRoot,
            Path helperRoot) throws IOException {
        Objects.requireNonNull(launcher); Objects.requireNonNull(launcherRoot); Objects.requireNonNull(helperRoot);
        if (!launcherRoot.isAbsolute() || !helperRoot.isAbsolute()) {
            throw new IllegalArgumentException("explicit absolute launcher and helper origins required");
        }
        Path caller = launcherRoot.toRealPath(), helper = helperRoot.toRealPath();
        if (!Files.isDirectory(caller)) { throw new IOException("compiled launcher directory required"); }
        requireOrigin(launcher, caller);
        for (Class<?> type : List.of(PythonStdinCapture.class, Invocation.class, Result.class,
                Starter.class, ProcessTree.class)) { requireOrigin(type, helper); }
    }

    private static void requireOrigin(Class<?> type, Path expected) throws IOException {
        var source = type.getProtectionDomain().getCodeSource();
        if (type.getClassLoader() != PythonStdinCapture.class.getClassLoader() || source == null
                || source.getLocation() == null || !source.getLocation().getProtocol().equals("file")) {
            throw new IOException("same compiled class loader and explicit file origin required: " + type.getName());
        }
        Path origin;
        try { origin = Path.of(source.getLocation().toURI()).toRealPath(); }
        catch (URISyntaxException error) { throw new IOException("invalid compiled origin", error); }
        if (!origin.equals(expected)) { throw new IOException("compiled origin differs: " + type.getName()); }
        String entry = type.getName().replace('.', '/') + ".class";
        if (Files.isDirectory(origin)) {
            Path file = origin.resolve(entry).toRealPath();
            if (!file.startsWith(origin) || !Files.isRegularFile(file) || Files.size(file) < 1
                    || Files.size(file) > 262_144) { throw new IOException("finite actual compiled class required"); }
        } else {
            if (!Files.isRegularFile(origin) || Files.size(origin) > 16_777_216) {
                throw new IOException("finite shared helper test jar required");
            }
            try (var jar = new java.util.jar.JarFile(origin.toFile())) {
                var file = jar.getJarEntry(entry);
                if (file == null || file.isDirectory() || file.getSize() < 1 || file.getSize() > 262_144) {
                    throw new IOException("finite actual helper jar class required: " + type.getName());
                }
            }
        }
    }

    static void requireCompiledLauncher(Class<?> launcher, Path configuredRoot) throws IOException {
        Objects.requireNonNull(launcher); Objects.requireNonNull(configuredRoot);
        if (!configuredRoot.isAbsolute()) { throw new IllegalArgumentException("absolute compiled capture root required"); }
        Path root = configuredRoot.toRealPath();
        if (!Files.isDirectory(root)) { throw new IOException("compiled capture directory required"); }
        ClassLoader loader = PythonStdinCapture.class.getClassLoader();
        for (Class<?> type : List.of(launcher, PythonStdinCapture.class, Invocation.class, Result.class,
                Starter.class, ProcessTree.class)) {
            var source = type.getProtectionDomain().getCodeSource();
            if (type.getClassLoader() != loader || source == null || source.getLocation() == null
                    || !source.getLocation().getProtocol().equals("file")) {
                throw new IOException("same compiled capture class loader and file origin required: " + type.getName());
            }
            Path origin;
            try { origin = Path.of(source.getLocation().toURI()).toRealPath(); }
            catch (URISyntaxException error) { throw new IOException("invalid compiled capture origin", error); }
            if (!origin.equals(root)) { throw new IOException("compiled capture origin differs from explicit root: " + type.getName()); }
            Path file = root.resolve(type.getName().replace('.', '/') + ".class").toRealPath();
            if (!file.startsWith(root) || !Files.isRegularFile(file) || Files.size(file) < 1 || Files.size(file) > 262_144) {
                throw new IOException("finite actual compiled capture class required: " + type.getName());
            }
        }
    }

    public static Result run(Invocation invocation) throws IOException, InterruptedException {
        return run(invocation, ProcessBuilder::start);
    }

    static Result run(Invocation invocation, Starter starter) throws IOException, InterruptedException {
        Objects.requireNonNull(invocation); Objects.requireNonNull(starter);
        List<String> command = new ArrayList<>(List.of(invocation.python().toString(), "-B", "-X", "utf8", "-"));
        command.addAll(invocation.arguments());
        Process child = starter.start(new ProcessBuilder(command).directory(invocation.repository().toFile())
                .redirectError(ProcessBuilder.Redirect.INHERIT));
        long deadline = System.nanoTime() + invocation.timeout().toNanos();
        ExecutorService tasks = Executors.newVirtualThreadPerTaskExecutor();
        ProcessTree tree = new ProcessTree(child);
        List<Future<?>> operations = new ArrayList<>();
        Throwable failure = null;
        try {
            operations.add(tasks.submit(tree::track));
            var input = tasks.submit(() -> {
                try (var stream = child.getOutputStream()) { stream.write(invocation.script().getBytes(StandardCharsets.UTF_8)); }
                return Boolean.TRUE;
            });
            operations.add(input);
            var output = tasks.submit(() -> child.getInputStream().readNBytes(invocation.maxOutputBytes() + 1));
            operations.add(output);
            try {
                if (!child.waitFor(remaining(deadline), TimeUnit.NANOSECONDS)) {
                    throw new IllegalStateException("producer stdin capture timed out");
                }
                input.get(remaining(deadline), TimeUnit.NANOSECONDS);
                byte[] bytes = output.get(remaining(deadline), TimeUnit.NANOSECONDS);
                if (child.exitValue() != 0) { throw new IllegalStateException("producer exit " + child.exitValue()); }
                if (bytes.length == 0 || bytes.length > invocation.maxOutputBytes()) {
                    throw new IllegalStateException("producer stdout missing or exceeds finite capture budget");
                }
                return new Result(bytes);
            } catch (ExecutionException error) {
                throw new IOException("producer stdin/stdout transport failed", error.getCause());
            } catch (TimeoutException error) {
                throw new IllegalStateException("producer stdin capture timed out", error);
            }
        } catch (IOException | InterruptedException | RuntimeException | Error error) {
            failure = error;
            if (error instanceof InterruptedException) { Thread.currentThread().interrupt(); }
            throw error;
        } finally {
            IOException cleanupFailure = cleanup(child, tree, tasks, operations);
            if (cleanupFailure != null) {
                if (failure != null) { failure.addSuppressed(cleanupFailure); }
                else { throw cleanupFailure; }
            }
        }
    }

    private static IOException cleanup(Process child, ProcessTree tree, ExecutorService tasks,
            List<Future<?>> operations) {
        long deadline = System.nanoTime() + CLEANUP_TIMEOUT.toNanos();
        boolean interrupted = Thread.interrupted();
        IOException failure = null;
        tree.stop.set(true);
        operations.forEach(operation -> operation.cancel(true));
        // Also observe after a normal/nonzero parent exit. Previously this entire
        // branch was skipped when the main process had already terminated.
        boolean exited = false;
        do {
            try {
                tree.observe();
                if (child.isAlive()) { child.destroyForcibly(); }
                for (ProcessHandle descendant : tree.snapshot()) {
                    if (descendant.isAlive()) { descendant.destroyForcibly(); }
                }
                long budget = deadline - System.nanoTime();
                if (budget <= 0) { break; }
                boolean parentExited = child.waitFor(Math.min(budget, TimeUnit.MILLISECONDS.toNanos(20)),
                        TimeUnit.NANOSECONDS);
                boolean descendantsExited = tree.snapshot().stream().noneMatch(ProcessHandle::isAlive);
                exited = parentExited && descendantsExited;
                if (!exited && parentExited) { TimeUnit.MILLISECONDS.sleep(2); }
            } catch (InterruptedException error) {
                interrupted = true;
            } catch (RuntimeException error) {
                failure = append(failure, "producer process cleanup failed", error);
                break;
            }
        } while (!exited && System.nanoTime() < deadline);
        if (!exited) { failure = append(failure, "producer or observed descendants did not exit within cleanup deadline", null); }
        // Closing a process pipe can itself wait for a blocked writer. Keep pipe
        // closing on daemon virtual threads and never use unbounded executor.close().
        List<Future<?>> closes = new ArrayList<>();
        closes.add(tasks.submit(() -> { child.getOutputStream().close(); return Boolean.TRUE; }));
        closes.add(tasks.submit(() -> { child.getInputStream().close(); return Boolean.TRUE; }));
        closes.add(tasks.submit(() -> { child.getErrorStream().close(); return Boolean.TRUE; }));
        tasks.shutdown();
        boolean terminated = false;
        while (!terminated && System.nanoTime() < deadline) {
            try { terminated = tasks.awaitTermination(Math.max(1, deadline - System.nanoTime()), TimeUnit.NANOSECONDS); }
            catch (InterruptedException error) { interrupted = true; }
        }
        if (!terminated) {
            tasks.shutdownNow();
            failure = append(failure, "producer transport tasks did not stop within cleanup deadline", null);
        }
        for (Future<?> close : closes) {
            if (!close.isDone()) { continue; }
            try { close.get(); }
            catch (InterruptedException error) { interrupted = true; }
            catch (ExecutionException error) { failure = append(failure, "producer pipe close failed", error.getCause()); }
        }
        RuntimeException observationFailure = tree.observationFailure.get();
        if (observationFailure != null) { failure = append(failure, "producer descendant observation failed", observationFailure); }
        // The tracker may have been finishing its final snapshot when cleanup
        // started. Confirm its retained handles again after task termination.
        if (child.isAlive() || tree.snapshot().stream().anyMatch(ProcessHandle::isAlive)) {
            failure = append(failure, "producer or observed descendants remain alive after transport cleanup", null);
        }
        if (interrupted) {
            failure = append(failure, "producer cleanup was interrupted", null);
            Thread.currentThread().interrupt();
        }
        return failure;
    }

    private static IOException append(IOException existing, String message, Throwable cause) {
        IOException next = new IOException(message, cause);
        if (existing == null) { return next; }
        existing.addSuppressed(next);
        return existing;
    }

    private static final class ProcessTree {
        private final Process root;
        private final ConcurrentHashMap<Long, ProcessHandle> descendants = new ConcurrentHashMap<>();
        private final AtomicBoolean stop = new AtomicBoolean();
        private final AtomicReference<RuntimeException> observationFailure = new AtomicReference<>();

        private ProcessTree(Process root) { this.root = root; }

        private void observe() {
            try (var current = root.descendants()) {
                current.forEach(handle -> descendants.putIfAbsent(handle.pid(), handle));
            }
            // Retain handles seen before a parent's exit; reparenting must not
            // discard descendants that this invocation already observed.
            for (ProcessHandle parent : snapshot()) {
                try (var current = parent.descendants()) {
                    current.forEach(handle -> descendants.putIfAbsent(handle.pid(), handle));
                }
            }
        }

        private List<ProcessHandle> snapshot() { return List.copyOf(descendants.values()); }

        private void track() {
            try {
                while (!stop.get()) {
                    observe();
                    if (!root.isAlive()) { return; }
                    TimeUnit.MILLISECONDS.sleep(2);
                }
            } catch (InterruptedException error) {
                Thread.currentThread().interrupt();
            } catch (RuntimeException error) {
                observationFailure.compareAndSet(null, error);
            }
        }
    }

    private static long remaining(long deadline) throws TimeoutException {
        long value = deadline - System.nanoTime();
        if (value <= 0) { throw new TimeoutException("producer deadline elapsed"); }
        return value;
    }
}
