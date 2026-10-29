package org.xar.ck3.control.g2.context;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.channels.FileChannel;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.concurrent.atomic.AtomicReference;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.g2.common.G2Request;
import org.xar.ck3.control.g2.common.G2Wire;
import org.xar.ck3.control.g2.common.Milestone;
import org.xar.ck3.control.g2.context.G2WindowsReadOnlyObservation.FileIdentity;
import org.xar.ck3.control.g2.context.G2WindowsReadOnlyObservation.FileObservation;
import org.xar.ck3.control.g2.context.G2WindowsReadOnlyObservation.FileRead;

/** Real Windows I/O tests plus explicitly synthetic Native/Game fixtures; no Game is inspected. */
public final class G2WindowsRootSourcesChecks {
    private static final int LIMIT = 65_536;
    private static final long GAME_PID = 424_242L;
    private static final String BIRTH = "134371791166449916";
    private static final String VERSION = "synthetic-product-no-game";
    private static final List<Class<?>> ANCHORS = List.of(G2WindowsRootSources.class,
            G2WindowsReadOnlyObservation.class, G2RetainedNativeSourceProvider.class, G2CallContextProducer.class);
    private static final byte[] PAYLOAD = utf8("{\"operation\":\"source-test\",\"input\":{\"decimal\":1.0,\"uint64\":18446744073709551615,\"null\":null,\"empty\":[],\"path\":\"synthetic:/never-read-Driver-or-SAVE\"}}");
    private static int checks;
    private G2WindowsRootSourcesChecks() { }
    public static void main(String[] args) throws Exception {
        if (args.length != 1) { throw new IllegalArgumentException("one admitted new test output directory required"); }
        Path root = Path.of(args[0]).toAbsolutePath().normalize(); Files.createDirectory(root);
        G2CallContextChecks.main(new String[0]);
        nativeRead(root.resolve("native"));
        successfulChain(root.resolve("chain"));
        requestIsolation(root.resolve("isolation"));
        sourceFailures(root.resolve("failures"));
        System.out.println("G2 Windows Root context checks PASS " + checks + "; actual native process/file I/O; synthetic Game/Native only; no Game authority");
    }
    public static void nativeRead(Path root) throws IOException {
        Files.createDirectory(root);
        G2WindowsReadOnlyObservation nativePort = new G2WindowsReadOnlyObservation();
        WindowsJobProcess.ProcessIdentity host = nativePort.process(ProcessHandle.current().pid());
        check(host.pid() == ProcessHandle.current().pid() && host.creationFiletimeDecimal().matches("[1-9][0-9]*"), "actual same-JVM process PID/creation");
        check(!nativePort.machineId().isBlank(), "actual stable machine identity");
        Path file = root.resolve("known-source.json"); byte[] raw = utf8("{\"identity\":\"18446744073709551617\",\"empty\":[],\"null\":null}"); Files.write(file, raw);
        FileRead read = nativePort.read(file, LIMIT);
        check(Arrays.equals(raw, read.bytes()), "actual held-handle bytes preserved");
        check(read.observation().reference().sha256().equals(G2RetainedNativeSourceProvider.sha256(raw)), "actual file hash");
        check(read.observation().identity().equals(nativePort.stat(file)), "native stable FileID/volume/ctime/mtime/change");
        check(nativePort.hash(file, LIMIT).equals(read.observation()), "stream-only and retained reads match");
        byte[] mutable = read.bytes(); mutable[0] = 0;
        check(read.bytes()[0] == '{', "returned byte arrays cannot mutate retained facts");
        ioRejects(() -> nativePort.read(file, 1));
        ioRejects(() -> nativePort.read(root.resolve("missing.json"), LIMIT));
        ioRejects(() -> nativePort.read(root, LIMIT));
        try (FileChannel writer = FileChannel.open(file, StandardOpenOption.WRITE)) {
            check(writer.isOpen(), "actual conflicting write handle held");
            ioRejects(() -> nativePort.read(file, LIMIT));
        }
        Path deep = root;
        while (deep.toString().length() < 330) { deep = deep.resolve("native-long-path-ordinary-file-component"); Files.createDirectory(deep); }
        Path longFile = deep.resolve("source.json"); Files.write(longFile, raw);
        check(Arrays.equals(nativePort.read(longFile, LIMIT).bytes(), raw), "actual extended Windows path stable read beyond MAX_PATH");
    }
    public static void successfulChain(Path root) throws Exception {
        Fixture fixture = new Fixture(root);
        G2WindowsRootSources.Captured capture = fixture.capture();
        byte[] original = fixture.nativeRow(Instant.now().toString());
        G2WindowsRootSources.NativeArrival arrival = fixture.owner.retainNativeArrival(capture, original, "ck3_semantic_snapshot");
        check(Arrays.equals(original, fixture.owner.readExact(arrival.nativeObservation(), LIMIT)), "actual original Native row retained without re-encoding");
        check(arrival.nativeObservation().sha256().equals(G2RetainedNativeSourceProvider.sha256(original)), "retained original exact ref");
        ProjectionJson payload = payload();
        unavailable(fixture.owner.context(Milestone.M1, payload), G2CallContextProducer.Reason.RETAINED_SOURCE_MISSING);
        G2CallContextProducer.RootBinding rootBinding = new G2CallContextProducer.RootBinding(); rootBinding.install(fixture.owner); rootBinding.install(fixture.owner);
        G2CallContextProducer.Context context;
        try (G2WindowsRootSources.RequestScope scope = fixture.owner.bindRequest(Milestone.M1, payload, arrival)) {
            check(scope != null, "explicit request scope");
            context = available(rootBinding.context(Milestone.M1, payload));
            unavailable(rootBinding.context(Milestone.M1, payload), G2CallContextProducer.Reason.RETAINED_SOURCE_MISSING);
        }
        check(context.source().machineId().equals(fixture.port.machineId()), "actual machine originates in native observation");
        check(context.source().sourceRef().equals(arrival.nativeObservation()), "source refers to original native bytes");
        check(context.source().exactBuild().equals(VERSION + "@sha256:" + fixture.exe.sha256()), "product version and actual fixture EXE hash match Native hello");
        check(context.payloadSha256().equals(G2RetainedNativeSourceProvider.sha256(PAYLOAD)), "request preserves raw decimal/uint64/null/empty payload SHA");
        check(context.equals(G2CallContextWire.decodeContext(G2CallContextWire.encodeContext(context))), "producer to context JSON consumer roundtrip");
        G2Request request = new G2Request(context.requestId(), Milestone.M1, context.source(), payload);
        check(request.equals(G2Wire.decodeRequest(G2Wire.encodeRequest(request))), "producer to actual evaluate envelope consumer roundtrip");
        unavailable(fixture.owner.context(Milestone.M1, payload), G2CallContextProducer.Reason.RETAINED_SOURCE_MISSING);
        ioRejects(() -> fixture.owner.readExact(new ExactRef("synthetic:/not-in-registry", 1, "0".repeat(64)), LIMIT));
        check(fixture.port.readPaths.stream().noneMatch(path -> path.toString().contains("Driver") || path.toString().contains("SAVE")), "payload path never creates file read authority");
    }
    public static void requestIsolation(Path root) throws Exception {
        Fixture fixture = new Fixture(root); G2WindowsRootSources.Captured capture = fixture.capture();
        G2WindowsRootSources.NativeArrival arrival = fixture.owner.retainNativeArrival(capture, fixture.nativeRow(Instant.now().toString()), "ck3_semantic_snapshot");
        ProjectionJson payload = payload();
        try (G2WindowsRootSources.RequestScope scope = fixture.owner.bindRequest(Milestone.M1, payload, arrival)) {
            check(scope != null, "payload scope");
            unavailable(fixture.owner.context(Milestone.M1, ProjectionJson.object(utf8("{}"), LIMIT)), G2CallContextProducer.Reason.SOURCE_REJECTED);
            unavailable(fixture.owner.context(Milestone.M1, payload), G2CallContextProducer.Reason.RETAINED_SOURCE_MISSING);
        }
        try (G2WindowsRootSources.RequestScope scope = fixture.owner.bindRequest(Milestone.M1, payload, arrival)) {
            check(scope != null, "milestone scope");
            unavailable(fixture.owner.context(Milestone.M6, payload), G2CallContextProducer.Reason.SOURCE_REJECTED);
        }
        try (G2WindowsRootSources.RequestScope scope = fixture.owner.bindRequest(Milestone.M1, payload, arrival)) {
            check(scope != null, "cross-thread scope");
            AtomicReference<G2CallContextProducer.Result> result = new AtomicReference<>();
            Thread thread = new Thread(() -> result.set(fixture.owner.context(Milestone.M1, payload)), "root-source-isolation-test");
            thread.start(); thread.join(5_000);
            check(!thread.isAlive(), "finite same-JVM worker ended");
            unavailable(result.get(), G2CallContextProducer.Reason.RETAINED_SOURCE_MISSING);
            rejects(() -> fixture.owner.bindRequest(Milestone.M1, payload, arrival));
            available(fixture.owner.context(Milestone.M1, payload));
        }
        Fixture other = new Fixture(root.resolve("other"));
        rejects(() -> other.owner.bindRequest(Milestone.M1, payload, arrival));
        ioOrArgumentRejects(() -> other.owner.retainNativeArrival(capture, fixture.nativeRow(Instant.now().toString()), "ck3_semantic_snapshot"));
    }
    public static void sourceFailures(Path root) throws Exception {
        Files.createDirectory(root);
        Fixture changed = new Fixture(root.resolve("changed-artifact"));
        G2WindowsRootSources.Captured cap = changed.capture();
        G2WindowsRootSources.NativeArrival arrival = changed.owner.retainNativeArrival(cap, changed.nativeRow(Instant.now().toString()), "ck3_semantic_snapshot");
        Files.write(Path.of(arrival.nativeObservation().path()), utf8("{}"));
        try (G2WindowsRootSources.RequestScope scope = changed.owner.bindRequest(Milestone.M1, payload(), arrival)) {
            check(scope != null, "artifact mutation scope");
            unavailable(changed.owner.context(Milestone.M1, payload()), G2CallContextProducer.Reason.SOURCE_IDENTITY_CHANGED);
        }
        Fixture birth = new Fixture(root.resolve("process-replaced")); cap = birth.capture();
        arrival = birth.owner.retainNativeArrival(cap, birth.nativeRow(Instant.now().toString()), "ck3_semantic_snapshot"); birth.port.changedBirth = true;
        try (G2WindowsRootSources.RequestScope scope = birth.owner.bindRequest(Milestone.M1, payload(), arrival)) {
            check(scope != null, "process replacement scope");
            unavailable(birth.owner.context(Milestone.M1, payload()), G2CallContextProducer.Reason.CURRENT_SESSION_UNAVAILABLE);
        }
        Fixture replaced = new Fixture(root.resolve("file-replaced")); cap = replaced.capture();
        arrival = replaced.owner.retainNativeArrival(cap, replaced.nativeRow(Instant.now().toString()), "ck3_semantic_snapshot");
        Path exePath = Path.of(replaced.exe.path()); byte[] exeBytes = Files.readAllBytes(exePath);
        Files.move(exePath, exePath.resolveSibling("original-ck3.exe")); Files.write(exePath, exeBytes);
        try (G2WindowsRootSources.RequestScope scope = replaced.owner.bindRequest(Milestone.M1, payload(), arrival)) {
            check(scope != null, "same-byte file replacement scope");
            unavailable(replaced.owner.context(Milestone.M1, payload()), G2CallContextProducer.Reason.CURRENT_SESSION_UNAVAILABLE);
        }
        Fixture stale = new Fixture(root.resolve("stale-native")); cap = stale.capture();
        arrival = stale.owner.retainNativeArrival(cap, stale.nativeRow("2000-01-01T00:00:01Z"), "ck3_semantic_snapshot");
        try (G2WindowsRootSources.RequestScope scope = stale.owner.bindRequest(Milestone.M1, payload(), arrival)) {
            check(scope != null, "stale native scope");
            unavailable(stale.owner.context(Milestone.M1, payload()), G2CallContextProducer.Reason.SOURCE_REJECTED);
        }
        Fixture mismatch = new Fixture(root.resolve("bad-native")); cap = mismatch.capture();
        String badText = new String(mismatch.nativeRow(Instant.now().toString()), StandardCharsets.UTF_8).replace("\"bridge_pid\":424242", "\"bridge_pid\":true");
        int start = badText.indexOf("\"result\":") + "\"result\":".length();
        int end = badText.indexOf(",\"mcp_result_projection_json_utf8_bytes\":");
        badText = badText.substring(0, end) + ",\"mcp_result_projection_json_utf8_bytes\":" + utf8(badText.substring(start, end)).length + "}";
        byte[] bad = utf8(badText);
        arrival = mismatch.owner.retainNativeArrival(cap, bad, "ck3_semantic_snapshot");
        try (G2WindowsRootSources.RequestScope scope = mismatch.owner.bindRequest(Milestone.M1, payload(), arrival)) {
            check(scope != null, "strict native integer scope");
            unavailable(mismatch.owner.context(Milestone.M1, payload()), G2CallContextProducer.Reason.SOURCE_REJECTED);
        }
        Fixture noRuntime = new Fixture(root.resolve("runtime-missing"));
        G2WindowsRootSources unsupported = new G2WindowsRootSources(noRuntime.config(List.of()), noRuntime.port);
        captureUnavailable(unsupported.captureBeforeNative(), G2CallContextProducer.Reason.EXACT_BUILD_UNAVAILABLE);
        Fixture drift = new Fixture(root.resolve("exe-drift")); Files.write(Path.of(drift.exe.path()), utf8("changed"));
        captureUnavailable(drift.owner.captureBeforeNative(), G2CallContextProducer.Reason.EXACT_BUILD_UNAVAILABLE);
        Fixture unavailable = new Fixture(root.resolve("native-unavailable")); unavailable.port.unsupported = true;
        captureUnavailable(unavailable.owner.captureBeforeNative(), G2CallContextProducer.Reason.EXACT_BUILD_UNAVAILABLE);
    }
    private static final class Fixture {
        private final Path root;
        private final FixturePort port = new FixturePort();
        private final ExactRef exe;
        private final ExactRef launcher;
        private final List<G2WindowsRootSources.RuntimeSource> runtime = new ArrayList<>();
        private final G2WindowsRootSources owner;
        private Fixture(Path root) throws IOException {
            this.root = root; Files.createDirectory(root); Files.createDirectory(root.resolve("evidence"));
            Path exeFile = root.resolve("ck3.exe"); Files.write(exeFile, utf8("synthetic EXE bytes; this is not a Game executable"));
            Path launcherFile = root.resolve("launcher-settings.json");
            Files.write(launcherFile, utf8("{\"rawVersion\":\"" + VERSION + "\",\"version\":\"synthetic launcher product\"}"));
            exe = port.hash(exeFile, LIMIT).reference(); launcher = port.hash(launcherFile, LIMIT).reference(); port.exe = exeFile;
            for (Class<?> anchor : ANCHORS) {
                Path path = G2WindowsRootSources.runtimePath(anchor);
                runtime.add(new G2WindowsRootSources.RuntimeSource(anchor.getName(), port.hash(path, 16 * 1024 * 1024).reference()));
            }
            owner = new G2WindowsRootSources(config(runtime), port);
        }
        private G2WindowsRootSources.Configuration config(List<G2WindowsRootSources.RuntimeSource> sources) {
            return new G2WindowsRootSources.Configuration(port.machineId(), "synthetic-session-no-game",
                    new G2RetainedNativeSourceProvider.GameIdentity(GAME_PID, BIRTH), "synthetic-episode-no-game", "9007199254740993",
                    exe, launcher, sources, root.resolve("evidence"), LIMIT, 16 * 1024 * 1024, LIMIT);
        }
        private G2WindowsRootSources.Captured capture() {
            G2WindowsRootSources.CaptureResult result = owner.captureBeforeNative();
            check(result instanceof G2WindowsRootSources.Captured, "actual files/synthetic Game capture expected: " + result);
            return (G2WindowsRootSources.Captured) result;
        }
        private byte[] nativeRow(String ended) {
            String result = "{\"meta\":{},\"content\":[],\"is_error\":false,\"result_type\":\"complete\",\"structured_content\":{\"snapshot_id\":\"synthetic-no-game\",\"revision\":42,\"native_revision\":43,\"date_raw\":123,\"episode_run_id\":\"synthetic-episode-no-game\",\"diagnostics\":{\"bridge_pid\":424242,\"connection_generation\":9007199254740993,\"hello\":{\"pid\":424242,\"connection_generation\":9007199254740993,\"ck3_build_match\":true,\"expected_ck3_version\":\"" + VERSION + "\",\"expected_ck3_sha256\":\"" + exe.sha256() + "\"}}}}";
            return utf8("{\"started_at_utc\":\"2000-01-01T00:00:00Z\",\"ended_at_utc\":\"" + ended + "\",\"elapsed_seconds\":1.0,\"request\":{\"sequence\":23,\"tool\":\"ck3_semantic_snapshot\",\"arguments\":{}},\"result\":" + result + ",\"mcp_result_projection_json_utf8_bytes\":" + utf8(result).length + "}");
        }
    }
    private static final class FixturePort implements G2WindowsRootSources.ObservationPort {
        private final G2WindowsReadOnlyObservation nativePort = new G2WindowsReadOnlyObservation();
        private final List<Path> readPaths = new ArrayList<>();
        private Path exe;
        private boolean changedBirth;
        private boolean unsupported;
        @Override public String machineId() { return nativePort.machineId(); }
        @Override public WindowsJobProcess.ProcessIdentity process(long pid) {
            if (unsupported) { throw new UnsupportedOperationException("synthetic unsupported observation"); }
            return pid == GAME_PID ? new WindowsJobProcess.ProcessIdentity(pid, changedBirth ? "134371791166449917" : BIRTH, exe.toString()) : nativePort.process(pid);
        }
        @Override public FileIdentity stat(Path path) throws IOException { return nativePort.stat(path); }
        @Override public FileObservation hash(Path path, long maximumBytes) throws IOException { readPaths.add(path); return nativePort.hash(path, maximumBytes); }
        @Override public FileRead read(Path path, long maximumBytes) throws IOException { readPaths.add(path); return nativePort.read(path, maximumBytes); }
    }
    private static ProjectionJson payload() { return ProjectionJson.object(PAYLOAD, LIMIT); }
    private static byte[] utf8(String value) { return value.getBytes(StandardCharsets.UTF_8); }
    private static G2CallContextProducer.Context available(G2CallContextProducer.Result result) {
        check(result instanceof G2CallContextProducer.Available, "available expected: " + result); return ((G2CallContextProducer.Available) result).context();
    }
    private static void unavailable(G2CallContextProducer.Result result, G2CallContextProducer.Reason reason) {
        check(result instanceof G2CallContextProducer.Unavailable value && value.reason() == reason, "typed unavailable " + reason + " expected: " + result);
    }
    private static void captureUnavailable(G2WindowsRootSources.CaptureResult result, G2CallContextProducer.Reason reason) {
        check(result instanceof G2WindowsRootSources.CaptureUnavailable value && value.failure().reason() == reason, "capture typed unavailable " + reason + " expected: " + result);
    }
    @FunctionalInterface private interface IoAction { void run() throws IOException; }
    private static void ioRejects(IoAction action) { try { action.run(); } catch (IOException expected) { checks++; return; } throw new AssertionError("actual I/O rejection expected"); }
    private static void ioOrArgumentRejects(IoAction action) { try { action.run(); } catch (IOException | IllegalArgumentException expected) { checks++; return; } throw new AssertionError("ownership rejection expected"); }
    private static void rejects(Runnable action) { try { action.run(); } catch (IllegalArgumentException | IllegalStateException expected) { checks++; return; } throw new AssertionError("ownership rejection expected"); }
    private static void check(boolean condition, String detail) { if (!condition) { throw new AssertionError(detail); } checks++; }
}
