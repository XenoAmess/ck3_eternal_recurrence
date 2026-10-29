package org.xar.ck3.control.g2.context;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.nio.file.StandardOpenOption;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.Instant;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.List;
import java.util.Objects;
import java.util.regex.Pattern;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.build.WindowsPreloadCustody;

/** Original saved-load log readiness. This is neither Native identity nor business evidence. */
public final class RootSavedLoadReadiness {
    private RootSavedLoadReadiness() { }
    public static final long MAX_LOG_BYTES = 64L << 20;
    private static final int MAX_LINE_BYTES = 32 << 10;
    private static final Pattern SETUP = Pattern.compile("\\[\\d{2}:\\d{2}:\\d{2}\\]\\[D\\]\\[gameapplication\\.cpp:\\d+\\]: Setup completion \\(history loaded\\): \\d+\\.\\d+ seconds");
    private static final Pattern IN_GAME = Pattern.compile("\\[\\d{2}:\\d{2}:\\d{2}\\]\\[D\\]\\[gameapplication\\.cpp:\\d+\\]: Setting idler 'In Game' with init options");
    public record ArchivedLog(String originalPath, ControlBuild.FileRef retained,
            SharedSourceFiles.NativeFile identity) { }
    public record Marker(long line, String text) { }
    public record Ready(ControlBuild.FileRef log, SharedSourceFiles.NativeFile nativeFile,
            Instant epoch, Instant observedAt, Marker setup, Marker inGame) { }
    /** Minted only by actual fixed-path preparation; cannot be reconstructed from JSON. */
    public static final class Prepared {
        private final Thread thread = Thread.currentThread();
        private final Path log;
        private final SharedSourceFiles.DirectoryIdentity directory;
        private final Instant epoch;
        private final List<ArchivedLog> archived;
        private Prepared(Path log, SharedSourceFiles.DirectoryIdentity directory,
                Instant epoch, List<ArchivedLog> archived) {
            this.log = log; this.directory = directory; this.epoch = epoch; this.archived = List.copyOf(archived);
        }
        public Path log() { return log; }
        public Instant epoch() { return epoch; }
        public List<ArchivedLog> archived() { return archived; }
        private void verify() throws IOException {
            if (Thread.currentThread() != thread || !directory.equals(SharedSourceFiles.nativeDirectory(log.getParent())))
                throw new IOException("Original prepared profile/log directory changed or owner thread differs");
        }
    }
    /** Called inside the genuine approved pre-CREATE stage. No process is created here. */
    public static Prepared prepare(Path exactProfileRoot, Path freshEvidenceRoot) throws IOException {
        Objects.requireNonNull(exactProfileRoot); Objects.requireNonNull(freshEvidenceRoot);
        SharedSourceFiles.plainAncestors(exactProfileRoot); SharedSourceFiles.plainAncestors(freshEvidenceRoot);
        Path profile = exactProfileRoot.toRealPath(), evidence = freshEvidenceRoot.toRealPath();
        if (!Files.isDirectory(profile) || !Files.isDirectory(evidence)) throw new IOException("Actual profile/evidence directories required");
        Path logs = profile.resolve("logs"); Files.createDirectories(logs); SharedSourceFiles.plainAncestors(logs);
        Path archive = evidence.resolve("prelaunch-logs"); Files.createDirectory(archive);
        List<ArchivedLog> retained = new ArrayList<>();
        // Same three fixed names as runtime._clear_isolated_runtime_logs. Preserve originals rather than delete them.
        for (String name : List.of("debug.log", "error.log", "gui_warnings.log")) {
            Path source = logs.resolve(name); SharedSourceFiles.plainAncestors(source);
            if (Files.exists(source)) {
                SharedSourceFiles.Witness before = SharedSourceFiles.observe(source);
                Path destination = archive.resolve(name);
                Files.move(source, destination, StandardCopyOption.ATOMIC_MOVE);
                SharedSourceFiles.Witness after = SharedSourceFiles.observe(destination);
                if (!before.nativeFile().identityKey().equals(after.nativeFile().identityKey())
                        || before.source().bytes() != after.source().bytes()
                        || !before.source().sha256().equals(after.source().sha256()))
                    throw new IOException("Original engine log changed during atomic retention");
                retained.add(new ArchivedLog(source.toString(), after.source(), after.nativeFile()));
            }
        }
        for (String name : List.of("debug.log", "error.log", "gui_warnings.log"))
            if (Files.exists(logs.resolve(name))) throw new IOException("Engine log survived original prelaunch preparation");
        Instant epoch = Instant.now();
        Files.write(archive.resolve("retained.json"), ControlBuild.strictMapper().writeValueAsBytes(retained), StandardOpenOption.CREATE_NEW);
        return new Prepared(logs.resolve("debug.log"), SharedSourceFiles.nativeDirectory(logs), epoch, retained);
    }
    public static Ready await(Prepared prepared, WindowsJobProcess originalGame,
            WindowsPreloadCustody.Lease originalLease, RootNativeRuntimeBinding runtime, Instant deadline)
            throws IOException, InterruptedException {
        Objects.requireNonNull(prepared); Objects.requireNonNull(originalGame); Objects.requireNonNull(originalLease);
        Objects.requireNonNull(runtime); Objects.requireNonNull(deadline);
        if (deadline.isAfter(runtime.request().reviewAt())) throw new IOException("Saved-load deadline exceeds actual Root binding");
        while (true) {
            verify(prepared, originalGame, originalLease, runtime, deadline);
            Ready ready = readComplete(prepared);
            verify(prepared, originalGame, originalLease, runtime, deadline);
            if (ready != null) return ready;
            Thread.sleep(Math.min(250, Math.max(1, java.time.Duration.between(Instant.now(), deadline).toMillis())));
        }
    }
    private static void verify(Prepared prepared, WindowsJobProcess game, WindowsPreloadCustody.Lease lease,
            RootNativeRuntimeBinding runtime, Instant deadline) throws IOException {
        prepared.verify(); runtime.verify(); lease.verify();
        if (!Instant.now().isBefore(deadline) || !game.isRunning() || !game.identity().equals(lease.targetIdentity()))
            throw new IOException("Original saved-load target exited, changed or missed readiness deadline; no repeated CREATE/injection");
    }
    static Ready readComplete(Prepared prepared) throws IOException {
        prepared.verify(); Path path = prepared.log;
        if (!Files.exists(path)) return null;
        SharedSourceFiles.plainAncestors(path);
        SharedSourceFiles.NativeFile before = SharedSourceFiles.nativeFile(path);
        if (before.logicalBytes() > MAX_LOG_BYTES) throw new IOException("Saved-load log exceeds finite original-readiness limit");
        if (Files.getLastModifiedTime(path).toInstant().isBefore(prepared.epoch)) return null;
        MessageDigest digest;
        try { digest = MessageDigest.getInstance("SHA-256"); }
        catch (NoSuchAlgorithmException impossible) { throw new IllegalStateException(impossible); }
        Marker setup = null, inGame = null; long bytes = 0, lineNumber = 0;
        ByteArrayOutputStream line = new ByteArrayOutputStream();
        try (var input = Files.newInputStream(path)) {
            byte[] buffer = new byte[16 << 10];
            for (int count; (count = input.read(buffer)) >= 0;) {
                if (count == 0) continue; bytes = Math.addExact(bytes, count);
                if (bytes > MAX_LOG_BYTES) throw new IOException("Saved-load log grew beyond finite limit");
                digest.update(buffer, 0, count);
                for (int index = 0; index < count; index++) {
                    int value = buffer[index] & 255;
                    if (value == '\n') {
                        lineNumber++; String text = line.toString(StandardCharsets.UTF_8);
                        if (text.endsWith("\r")) text = text.substring(0, text.length() - 1);
                        if (setup == null && SETUP.matcher(text).matches()) setup = new Marker(lineNumber, text);
                        if (inGame == null && IN_GAME.matcher(text).matches()) inGame = new Marker(lineNumber, text);
                        line.reset();
                    } else {
                        if (line.size() >= MAX_LINE_BYTES) throw new IOException("Unbounded engine-log line refused");
                        line.write(value);
                    }
                }
            }
        }
        SharedSourceFiles.NativeFile after = SharedSourceFiles.nativeFile(path);
        if (!before.identityKey().equals(after.identityKey())) throw new IOException("Engine log identity replaced while observing saved-load readiness");
        if (!before.equals(after) || bytes != after.logicalBytes()) return null;
        if (setup == null || inGame == null) return null;
        return new Ready(new ControlBuild.FileRef(path.toString(), bytes, HexFormat.of().formatHex(digest.digest())),
                after, prepared.epoch, Instant.now(), setup, inGame);
    }
}
