package org.xar.ck3.control.g2.context;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.fasterxml.jackson.databind.node.JsonNodeFactory;
import java.io.IOException;
import java.net.JarURLConnection;
import java.net.URISyntaxException;
import java.net.URL;
import java.nio.ByteBuffer;
import java.nio.channels.FileChannel;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Instant;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicLong;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.g2.common.Milestone;
import org.xar.ck3.control.g2.context.G2WindowsReadOnlyObservation.FileIdentity;
import org.xar.ck3.control.g2.context.G2WindowsReadOnlyObservation.FileObservation;
import org.xar.ck3.control.g2.context.G2WindowsReadOnlyObservation.FileRead;

/**
 * Root's real pre-call source capability. All configured paths originate at programmatic bootstrap.
 * The only input bytes retained here are the original Native owner row supplied at Native arrival.
 * No Driver/SAVE reader, Game submitter, process starter or authority minting exists in this class.
 */
public final class G2WindowsRootSources implements G2RetainedNativeSourceProvider.RootOwnedSources,
        G2CallContextProducer.Provider {
    public interface ObservationPort {
        String machineId();
        WindowsJobProcess.ProcessIdentity process(long pid);
        FileIdentity stat(Path path) throws IOException;
        FileObservation hash(Path path, long maximumBytes) throws IOException;
        FileRead read(Path path, long maximumBytes) throws IOException;
    }
    public record RuntimeSource(String anchorClass, ExactRef source) {
        public RuntimeSource { StrictJson.text(anchorClass); Objects.requireNonNull(source); }
    }
    public record Configuration(String machineId, String sessionId,
            G2RetainedNativeSourceProvider.GameIdentity game, String episodeRunId,
            String connectionGeneration, ExactRef executable, ExactRef launcherSettings,
            List<RuntimeSource> runtimeSources, Path evidenceRoot, long executableBudget,
            long runtimeFileBudget, int artifactBudget) {
        public Configuration {
            StrictJson.text(machineId); StrictJson.text(sessionId); Objects.requireNonNull(game);
            StrictJson.text(episodeRunId); StrictJson.text(connectionGeneration);
            Objects.requireNonNull(executable); Objects.requireNonNull(launcherSettings);
            runtimeSources = List.copyOf(runtimeSources); Objects.requireNonNull(evidenceRoot);
            if (!Path.of(executable.path()).getFileName().toString().equalsIgnoreCase("ck3.exe")
                    || !Path.of(launcherSettings.path()).getFileName().toString().equals("launcher-settings.json")) {
                throw new IllegalArgumentException("explicit CK3 EXE and launcher settings sources required");
            }
            if (!evidenceRoot.isAbsolute() || !evidenceRoot.normalize().equals(evidenceRoot)
                    || executableBudget < 1 || runtimeFileBudget < 1 || artifactBudget < 1
                    || artifactBudget > RootMcpEnvelope.OWNER_ROW_MAX_BYTES) { throw new IllegalArgumentException("explicit finite Root budgets/root required"); }
        }
    }
    public sealed interface CaptureResult permits Captured, CaptureUnavailable { }
    /** Opaque issuer identity prevents a capture from another owner/JVM being reconstructed from JSON. */
    public static final class Captured implements CaptureResult {
        private final G2WindowsRootSources issuer;
        private final G2RetainedNativeSourceProvider.Session session;
        private final ExactRef measurement;
        private final List<FileObservation> files;
        private final WindowsJobProcess.ProcessIdentity host;
        private Captured(G2WindowsRootSources issuer, G2RetainedNativeSourceProvider.Session session,
                ExactRef measurement, List<FileObservation> files, WindowsJobProcess.ProcessIdentity host) {
            this.issuer = issuer; this.session = session; this.measurement = measurement;
            this.files = List.copyOf(files); this.host = host;
        }
        public G2RetainedNativeSourceProvider.Session session() { return session; }
        public ExactRef executableObservation() { return measurement; }
    }
    public record CaptureUnavailable(G2CallContextProducer.Unavailable failure) implements CaptureResult {
        public CaptureUnavailable { Objects.requireNonNull(failure); }
    }
    public static final class NativeArrival {
        private final G2WindowsRootSources issuer;
        private final Captured capture;
        private final G2RetainedNativeSourceProvider.RetainedArtifact artifact;
        private NativeArrival(G2WindowsRootSources issuer, Captured capture,
                G2RetainedNativeSourceProvider.RetainedArtifact artifact) {
            this.issuer = issuer; this.capture = capture; this.artifact = artifact;
        }
        public ExactRef nativeObservation() { return artifact.nativeObservation(); }
    }
    /** One synchronous request; closing or consumption removes its source, including on exceptions. */
    public final class RequestScope implements AutoCloseable {
        private final Thread thread = Thread.currentThread();
        private final Milestone milestone;
        private final String payloadSha;
        private final NativeArrival arrival;
        private boolean consumed;
        private boolean closed;
        private RequestScope(Milestone milestone, ProjectionJson payload, NativeArrival arrival) {
            this.milestone = milestone; this.payloadSha = G2RetainedNativeSourceProvider.sha256(payload.bytes()); this.arrival = arrival;
        }
        @Override public void close() {
            if (Thread.currentThread() != thread) { throw new IllegalStateException("Root request scope belongs to its original JVM thread"); }
            if (!closed) {
                if (active.get() != this) { throw new IllegalStateException("Root request scope ownership changed"); }
                active.remove(); closed = true;
            }
        }
    }
    private static final List<Class<?>> ANCHORS = List.of(G2WindowsRootSources.class,
            G2WindowsReadOnlyObservation.class, G2RetainedNativeSourceProvider.class, G2CallContextProducer.class);
    private final Configuration config;
    private final ObservationPort observer;
    private final G2RetainedNativeSourceProvider delegate;
    private final ThreadLocal<RequestScope> active = new ThreadLocal<>();
    private final Map<ExactRef, FileObservation> retained = new HashMap<>();
    private final AtomicLong artifacts = new AtomicLong();

    public G2WindowsRootSources(Configuration config, ObservationPort observer) {
        this.config = Objects.requireNonNull(config); this.observer = Objects.requireNonNull(observer);
        this.delegate = new G2RetainedNativeSourceProvider(this,
                new G2RetainedNativeSourceProvider.Limits(config.artifactBudget(), StrictJson.EXPLICIT_MAX_BYTES));
    }
    /** Actual process/EXE/runtime capture must finish before the corresponding Native row arrives. */
    public CaptureResult captureBeforeNative() {
        try {
            if (!config.machineId().equals(observer.machineId())) { return unavailable(G2CallContextProducer.Reason.SOURCE_IDENTITY_CHANGED, "current machine differs from Root bootstrap"); }
            WindowsJobProcess.ProcessIdentity host = observer.process(ProcessHandle.current().pid());
            WindowsJobProcess.ProcessIdentity game = observer.process(config.game().pid());
            requireGame(game);
            FileObservation exe = observer.hash(Path.of(config.executable().path()), config.executableBudget());
            requireExact(config.executable(), exe);
            FileRead launcher = observer.read(Path.of(config.launcherSettings().path()), StrictJson.EXPLICIT_MAX_BYTES);
            requireExact(config.launcherSettings(), launcher.observation());
            JsonNode product = StrictJson.parse(ProjectionJson.object(launcher.bytes(), StrictJson.EXPLICIT_MAX_BYTES).bytes(), StrictJson.EXPLICIT_MAX_BYTES);
            String rawVersion = StrictJson.text(product.get("rawVersion"));
            StrictJson.text(product.get("version"));
            Map<String, RuntimeSource> runtime = new HashMap<>();
            for (RuntimeSource source : config.runtimeSources()) {
                if (runtime.put(source.anchorClass(), source) != null) { throw new IllegalArgumentException("unique runtime anchor required"); }
            }
            if (runtime.size() != ANCHORS.size()) { return unavailable(G2CallContextProducer.Reason.EXACT_BUILD_UNAVAILABLE, "all context runtime source anchors must be explicitly bound"); }
            java.util.ArrayList<FileObservation> files = new java.util.ArrayList<>();
            files.add(exe); files.add(launcher.observation());
            ArrayNode runtimeRows = JsonNodeFactory.instance.arrayNode();
            for (Class<?> anchor : ANCHORS) {
                RuntimeSource expected = runtime.get(anchor.getName());
                if (expected == null || !runtimePath(anchor).equals(Path.of(expected.source().path()).toAbsolutePath().normalize())) {
                    return unavailable(G2CallContextProducer.Reason.EXACT_BUILD_UNAVAILABLE, "loaded context class source differs from Root runtime source");
                }
                FileObservation actual = observer.hash(Path.of(expected.source().path()), config.runtimeFileBudget());
                requireExact(expected.source(), actual); files.add(actual);
                ObjectNode runtimeRow = StrictJson.object(); runtimeRow.put("anchor_class", anchor.getName());
                runtimeRow.set("source_ref", actual.reference().toJson()); runtimeRows.add(runtimeRow);
            }
            for (FileObservation source : files) { requireStable(source); }
            requireGame(observer.process(config.game().pid()));
            if (!host.equals(observer.process(ProcessHandle.current().pid()))) { throw new IOException("host process identity changed"); }
            ObjectNode measurement = StrictJson.object();
            measurement.put("schema", "xar.resume56-current-game-files-readonly-observation/v1");
            measurement.put("machine_id", config.machineId()); measurement.put("observed_at_utc", Instant.now().toString());
            measurement.put("provider", G2WindowsRootSources.class.getName());
            measurement.set("host_process", processJson(host)); measurement.set("game_process", processJson(game));
            measurement.set("runtime_sources", runtimeRows);
            ArrayNode observations = JsonNodeFactory.instance.arrayNode(); observations.add(fileJson("game_exe", exe));
            ObjectNode launcherRow = fileJson("launcher_settings", launcher.observation());
            launcherRow.put("version", product.get("version").textValue()); launcherRow.put("raw_version", rawVersion);
            observations.add(launcherRow); measurement.set("observations", observations);
            ExactRef receipt = retain("exe-observation", StrictJson.canonical(measurement, StrictJson.EXPLICIT_MAX_BYTES));
            G2RetainedNativeSourceProvider.Session session = new G2RetainedNativeSourceProvider.Session(config.machineId(), config.sessionId(),
                    config.game(), config.episodeRunId(), config.connectionGeneration(), exe.reference(), exe.identity().fileId(), exe.identity().mtimeNs());
            return new Captured(this, session, receipt, files, host);
        } catch (IOException | UnsupportedOperationException error) {
            return unavailable(G2CallContextProducer.Reason.EXACT_BUILD_UNAVAILABLE, "actual Windows process/file/runtime observation unavailable");
        } catch (RuntimeException error) {
            return unavailable(G2CallContextProducer.Reason.SOURCE_REJECTED, "Root bootstrap or actual source contract rejected");
        }
    }
    /** Call only at the real arrival seam; the bytes are retained exactly, never synthesized or restamped. */
    public NativeArrival retainNativeArrival(Captured capture, byte[] originalOwnerRow, String expectedTool) throws IOException {
        requireOwned(capture); StrictJson.text(expectedTool);
        if (originalOwnerRow.length < 1 || originalOwnerRow.length > config.artifactBudget()) { throw new IOException("bounded original Native row required"); }
        if (!current(capture)) { throw new IOException("current process/EXE/runtime identity differs before Native retention"); }
        ExactRef source = retain("native-arrival", originalOwnerRow.clone());
        return new NativeArrival(this, capture, new G2RetainedNativeSourceProvider.RetainedArtifact(
                capture.session, source, capture.measurement, expectedTool));
    }
    public RequestScope bindRequest(Milestone milestone, ProjectionJson originalPayload, NativeArrival arrival) {
        Objects.requireNonNull(milestone); G2CallContextProducer.requirePayloadToken(originalPayload);
        Objects.requireNonNull(arrival);
        if (arrival.issuer != this || arrival.capture.issuer != this) { throw new IllegalArgumentException("Native source belongs to another Root provider/JVM"); }
        if (active.get() != null) { throw new IllegalStateException("nested Root source request binding rejected"); }
        RequestScope scope = new RequestScope(milestone, originalPayload, arrival); active.set(scope); return scope;
    }
    @Override public G2CallContextProducer.Result context(Milestone milestone, ProjectionJson originalPayload) {
        Objects.requireNonNull(milestone); G2CallContextProducer.requirePayloadToken(originalPayload);
        RequestScope scope = active.get();
        if (scope == null || scope.closed || scope.consumed) {
            return new G2CallContextProducer.Unavailable(G2CallContextProducer.Reason.RETAINED_SOURCE_MISSING, "Root has no unconsumed same-JVM pre-call Native request binding");
        }
        if (scope.milestone != milestone || !scope.payloadSha.equals(G2RetainedNativeSourceProvider.sha256(originalPayload.bytes()))) {
            scope.consumed = true;
            return new G2CallContextProducer.Unavailable(G2CallContextProducer.Reason.SOURCE_REJECTED, "Root request binding differs from original milestone/payload bytes");
        }
        try { return delegate.context(milestone, originalPayload); }
        finally { scope.consumed = true; }
    }
    @Override public Optional<G2RetainedNativeSourceProvider.Session> currentSession() {
        RequestScope scope = active.get();
        if (scope == null || scope.closed) { return Optional.empty(); }
        try { return current(scope.arrival.capture) ? Optional.of(scope.arrival.capture.session) : Optional.empty(); }
        catch (IOException | RuntimeException unavailable) { return Optional.empty(); }
    }
    @Override public Optional<G2RetainedNativeSourceProvider.RetainedArtifact> selectedSource(Milestone milestone, ProjectionJson payload) {
        RequestScope scope = active.get();
        return scope != null && !scope.closed && !scope.consumed && scope.milestone == milestone
                && scope.payloadSha.equals(G2RetainedNativeSourceProvider.sha256(payload.bytes()))
                ? Optional.of(scope.arrival.artifact) : Optional.empty();
    }
    @Override public byte[] readExact(ExactRef reference, int maximumBytes) throws IOException {
        FileObservation expected;
        synchronized (retained) { expected = retained.get(reference); }
        if (expected == null || reference.bytes() > maximumBytes) { throw new IOException("reference is outside Root retained artifact registry/budget"); }
        FileRead actual = observer.read(Path.of(reference.path()), maximumBytes);
        if (!expected.equals(actual.observation())) { throw new IOException("retained artifact native identity/content changed"); }
        return actual.bytes();
    }
    private boolean current(Captured capture) throws IOException {
        requireOwned(capture);
        if (!config.machineId().equals(observer.machineId()) || !capture.host.equals(observer.process(ProcessHandle.current().pid()))) { return false; }
        requireGame(observer.process(config.game().pid()));
        for (FileObservation file : capture.files) { requireStable(file); }
        return true;
    }
    private void requireOwned(Captured capture) {
        if (capture == null || capture.issuer != this) { throw new IllegalArgumentException("capture belongs to another Root provider/JVM"); }
    }
    private void requireGame(WindowsJobProcess.ProcessIdentity game) throws IOException {
        if (game.pid() != config.game().pid() || !game.creationFiletimeDecimal().equals(config.game().creationFiletime())
                || !Path.of(game.executable()).toAbsolutePath().normalize().equals(Path.of(config.executable().path()).toAbsolutePath().normalize())) {
            throw new IOException("actual Game process birth/executable differs from Root bootstrap");
        }
    }
    private void requireStable(FileObservation observed) throws IOException {
        if (!observed.identity().equals(observer.stat(Path.of(observed.reference().path())))) { throw new IOException("source native identity changed"); }
    }
    private static void requireExact(ExactRef expected, FileObservation actual) throws IOException {
        if (!expected.equals(actual.reference())) { throw new IOException("actual source does not match Root exact reference"); }
    }
    private ExactRef retain(String kind, byte[] raw) throws IOException {
        G2WindowsReadOnlyObservation.plain(config.evidenceRoot());
        if (!Files.isDirectory(config.evidenceRoot(), LinkOption.NOFOLLOW_LINKS)) { throw new IOException("Root evidence directory must already exist"); }
        long ordinal = artifacts.incrementAndGet();
        if (ordinal < 1 || ordinal > StrictJson.MAX_SAFE_INTEGER) { throw new IOException("Root artifact sequence exhausted"); }
        Path path = config.evidenceRoot().resolve(kind + "-" + ProcessHandle.current().pid() + "-" + ordinal + ".json");
        try (FileChannel output = FileChannel.open(path, StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE)) {
            ByteBuffer bytes = ByteBuffer.wrap(raw); while (bytes.hasRemaining()) { output.write(bytes); } output.force(true);
        }
        FileRead readback = observer.read(path, config.artifactBudget());
        if (!Arrays.equals(raw, readback.bytes())) { throw new IOException("Root retained original readback differs"); }
        synchronized (retained) { retained.put(readback.observation().reference(), readback.observation()); }
        return readback.observation().reference();
    }
    /** Describes the actual loaded code location; Root still supplies and authorizes its exact ref. */
    public static Path runtimePath(Class<?> anchor) throws IOException {
        if (!ANCHORS.contains(anchor)) { throw new IOException("unknown Root runtime anchor"); }
        URL resource = anchor.getResource(anchor.getSimpleName() + ".class");
        try {
            if (resource != null && resource.getProtocol().equals("file")) { return Path.of(resource.toURI()).toAbsolutePath().normalize(); }
            if (resource != null && resource.getProtocol().equals("jar")
                    && resource.openConnection() instanceof JarURLConnection jar && jar.getJarFileURL().getProtocol().equals("file")) {
                return Path.of(jar.getJarFileURL().toURI()).toAbsolutePath().normalize();
            }
        } catch (URISyntaxException error) { throw new IOException("runtime resource URI unavailable", error); }
        throw new IOException("actual local class/JAR runtime source required");
    }
    private static ObjectNode fileJson(String label, FileObservation file) {
        ObjectNode row = file.reference().toJson(); row.put("label", label);
        row.put("volume_serial_decimal", file.identity().volumeSerial()); row.put("file_id_decimal", file.identity().fileId());
        row.put("creation_filetime_decimal", file.identity().creationFiletime()); row.put("mtime_ns_decimal", file.identity().mtimeNs());
        row.put("change_filetime_decimal", file.identity().changeFiletime()); row.put("stable_during_read", true); return row;
    }
    private static ObjectNode processJson(WindowsJobProcess.ProcessIdentity process) {
        ObjectNode row = StrictJson.object(); row.put("pid", process.pid());
        row.put("creation_filetime_decimal", process.creationFiletimeDecimal()); row.put("executable", process.executable()); return row;
    }
    private static CaptureUnavailable unavailable(G2CallContextProducer.Reason reason, String detail) {
        return new CaptureUnavailable(new G2CallContextProducer.Unavailable(reason, detail));
    }
}
