package org.xar.ck3.control.build;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.TreeMap;

/** Java CI orchestrator for the existing Python client and complete consumer regression. */
public final class MapAdmissionCi {
    private static final long COMMAND_MEMORY_LIMIT = 512L << 20;
    private MapAdmissionCi() {}

    public record Config(Path repoRoot, Path buildReceipt, Path workRoot, Path javaExecutable,
                         Path pythonExecutable, Instant leaseDeadline, int port, CiBootstrap.PipelineProfile pipelineProfile) {
        public Config(Path repoRoot, Path buildReceipt, Path workRoot, Path javaExecutable,
                Path pythonExecutable, Instant leaseDeadline, int port) {
            this(repoRoot, buildReceipt, workRoot, javaExecutable, pythonExecutable, leaseDeadline, port,
                    CiBootstrap.PipelineProfile.LEGACY);
        }
        public Config {
            Objects.requireNonNull(repoRoot);
            Objects.requireNonNull(buildReceipt);
            Objects.requireNonNull(workRoot);
            Objects.requireNonNull(javaExecutable);
            Objects.requireNonNull(pythonExecutable);
            Objects.requireNonNull(leaseDeadline);
            Objects.requireNonNull(pipelineProfile);
            if (port < 1 || port > 65535) { throw new IllegalArgumentException("bounded explicit TCP port required"); }
        }
    }

    public record CommandEvidence(WindowsJobProcess.CommandResult result,
                                  ControlBuild.FileRef stdoutRef, ControlBuild.FileRef stderrRef) {}

    public record OriginalMapConsumerGroup(CommandEvidence staticCheck, CommandEvidence regression) {
        public OriginalMapConsumerGroup { Objects.requireNonNull(staticCheck); Objects.requireNonNull(regression); }
    }
    public static final class OriginalMapConsumerGroupFailure extends IOException {
        private static final long serialVersionUID = 1L;
        private final transient CommandEvidence staticCheck, regression;
        private OriginalMapConsumerGroupFailure(CommandEvidence staticCheck, CommandEvidence regression, Throwable cause) {
            super("Original map consumer group failed; completed command evidence retained", cause);
            this.staticCheck = staticCheck; this.regression = regression;
        }
        public CommandEvidence staticCheck() { return staticCheck; }
        public CommandEvidence regression() { return regression; }
    }

    public static final class CommandQualificationFailure extends IOException {
        private static final long serialVersionUID = 1L;
        private final transient CommandEvidence evidence;
        private CommandQualificationFailure(CommandEvidence evidence, Throwable cause) {
            super("Python command completed but its original service/source closure changed", cause); this.evidence = evidence;
        }
        public CommandEvidence evidence() { return evidence; }
    }

    /** One existing service Owner and its original Python process environment. No alternate service or retry authority. */
    public static final class Session implements AutoCloseable {
        private final Config config;
        private final Path logs;
        private final Path scratch;
        private final Map<String, String> environment;
        private final MapAdmissionServiceOwner.Session service;
        private final MapVerticalSoftwareHost.Session borrowed;
        private final java.util.Set<String> submittedLabels = new java.util.HashSet<>();
        private boolean closed;

        private Session(Config config, Path logs, Path scratch, Map<String, String> environment,
                MapAdmissionServiceOwner.Session service, boolean projection) {
            this(config, logs, scratch, environment, service, projection, null);
        }
        private Session(Config config, Path logs, Path scratch, Map<String, String> environment,
                MapAdmissionServiceOwner.Session service, boolean projection, MapVerticalSoftwareHost.Session borrowed) {
            this.config = config; this.logs = logs; this.scratch = scratch; this.service = service;
            this.borrowed = borrowed;
            this.environment = serviceEnvironment(environment, borrowed == null ? service.evidenceRef() : borrowed.runningRef(),
                    projection ? service.projectionAdmission().serviceEvidenceRef() : null);
        }
        public Config config() { return config; }
        public Path logs() { return logs; }
        public Path scratch() { return scratch; }
        public Map<String, String> environment() { requireOpen(); return environment; }
        public ControlBuild.FileRef evidenceRef() { requireOpen(); return borrowed == null ? service.evidenceRef() : borrowed.runningRef(); }
        public MapAdmissionServiceOwner.ProjectionAdmission projectionAdmission() { requireFullSession(); return service.projectionAdmission(); }
        public RootSoftwareFixtureHandoff.Admission softwareFixtureAdmission() { requireFullSession(); return service.softwareFixtureAdmission(); }
        private void requireFullSession() { requireOpen(); if (borrowed != null) throw new IllegalStateException("Limited map software cannot grant projection or SDK admission"); }
        public void requireCurrent() { requireOpen(); if (borrowed == null) service.requireCurrent(); else borrowed.requireCurrent(); }
        public void verifyImmutableInputs() throws IOException { requireOpen(); if (borrowed == null) service.verifyImmutableInputs(); else borrowed.verifyImmutableInputs(); }
        public CommandEvidence python(String label, List<String> arguments) throws IOException {
            requireOpen();
            if (label == null || !label.matches("[a-z0-9][a-z0-9-]{0,63}") || arguments == null || arguments.isEmpty()) {
                throw new IllegalArgumentException("finite explicit Python command identity required");
            }
            if (!submittedLabels.add(label)) throw new IllegalStateException("an original CI command label cannot be replayed or overwrite its evidence");
            verifyImmutableInputs();
            CommandEvidence actual = command(config, environment, logs, label, List.copyOf(arguments), this::requireCurrent);
            try { verifyImmutableInputs(); }
            catch (IOException | RuntimeException failure) { throw new CommandQualificationFailure(actual, failure); }
            return actual;
        }
        private void requireOpen() { if (closed) throw new IllegalStateException("original CI service session is closed"); }
        @Override public void close() {
            if (closed) return;
            closed = true; // A failed/unknown close never authorizes a second service submission.
            if (borrowed == null) service.close(); // The limited factory owns its sole outer close.
        }
    }

    /** Borrow one already-live, limited map software Host. Normal receipt admission remains unchanged. */
    public static Session borrowForMapVerticalSoftware(Config requested, MapVerticalSoftwareHost.Session limited) throws IOException {
        if (limited == null) throw new IllegalArgumentException("Explicit live limited map Host required before opening inputs");
        Config config = normalized(requested);
        if (limited.purpose() != MapVerticalSoftwareHost.Purpose.MAP_VERTICAL_SOFTWARE_ONLY
                || !ControlBuild.FileRef.measure(config.buildReceipt()).equals(limited.captureRef())
                || !Instant.now().isBefore(config.leaseDeadline())) throw new IOException("Exact current limited capture purpose and receipt required");
        limited.requireCurrent(); limited.verifyImmutableInputs();
        limited.runningRef().verify(); limited.programRef().verify();
        if (Files.exists(config.workRoot()) || config.workRoot().startsWith(config.repoRoot())) throw new IllegalArgumentException("New external borrowed CI metadata root required");
        Files.createDirectory(config.workRoot());
        Path logs = Files.createDirectory(config.workRoot().resolve("logs")), scratch = Files.createDirectory(config.workRoot().resolve("scratch"));
        return new Session(config, logs, scratch, pythonEnvironment(config, scratch), limited.owner(), false, limited);
    }

    static Map<String, String> serviceEnvironment(Map<String, String> base, ControlBuild.FileRef mapEvidence,
            ControlBuild.FileRef projectionEvidence) {
        var current = new TreeMap<String, String>(String.CASE_INSENSITIVE_ORDER); current.putAll(base);
        current.remove("XAR_JAVA_PROJECTION_SERVICE_EVIDENCE");
        current.put("XAR_JAVA_MAP_SERVICE_EVIDENCE", mapEvidence.path());
        if (projectionEvidence != null) current.put("XAR_JAVA_PROJECTION_SERVICE_EVIDENCE", projectionEvidence.path());
        return Map.copyOf(current);
    }

    /** Existing FULL projection entrypoint, now sharing the same finite CI session implementation as run(). */
    public static Session startWithProjection(Config requested, ProjectionArtifactInputOwner.Config artifactInput) throws IOException {
        if (artifactInput == null) throw new IllegalArgumentException("explicit Root-owned full artifact input configuration required");
        Config config = normalized(requested);
        ControlBuild.acceptedReceipt(config.buildReceipt());
        if (Files.exists(config.workRoot()) || config.workRoot().startsWith(config.repoRoot())) throw new IllegalArgumentException("new external CI metadata task root required");
        Files.createDirectory(config.workRoot());
        Path logs = Files.createDirectory(config.workRoot().resolve("logs"));
        Path scratch = Files.createDirectory(config.workRoot().resolve("scratch"));
        Map<String, String> environment = pythonEnvironment(config, scratch);
        var service = MapAdmissionServiceOwner.startWithProjection(serviceConfig(config, null, artifactInput));
        return retain(config, logs, scratch, environment, service, true);
    }

    private static Session retain(Config config, Path logs, Path scratch, Map<String, String> environment,
            MapAdmissionServiceOwner.Session service, boolean projection) {
        try { return new Session(config, logs, scratch, environment, service, projection); }
        catch (RuntimeException | Error primary) {
            try { service.close(); } catch (RuntimeException | Error cleanup) { primary.addSuppressed(cleanup); }
            throw primary;
        }
    }

    private static Config normalized(Config requested) throws IOException {
        return new Config(requested.repoRoot().toRealPath(), requested.buildReceipt().toRealPath(),
                requested.workRoot().toAbsolutePath().normalize(), requested.javaExecutable().toRealPath(),
                requested.pythonExecutable().toRealPath(), requested.leaseDeadline(), requested.port(), requested.pipelineProfile());
    }

    /** Both consumer routes carry the original absolute lease and its admitted profile into the Owner. */
    static MapAdmissionServiceOwner.Config serviceConfig(Config config, RootSoftwareFixtureHandoff.Request fixture,
            ProjectionArtifactInputOwner.Config artifactInput) {
        return new MapAdmissionServiceOwner.Config(config.buildReceipt(), config.workRoot().resolve("service"),
                config.javaExecutable(), config.leaseDeadline(), config.port(), null, null, null, null,
                artifactInput, fixture, config.pipelineProfile());
    }

    private static Map<String, String> pythonEnvironment(Config config, Path scratch) {
        Map<String, String> environment = new TreeMap<>(String.CASE_INSENSITIVE_ORDER); environment.putAll(System.getenv());
        String modulePath = config.repoRoot() + System.getProperty("path.separator") + config.repoRoot().resolve("ck3_autonomous_player/src");
        String inherited = environment.get("PYTHONPATH");
        environment.put("PYTHONPATH", inherited == null || inherited.isBlank() ? modulePath : modulePath + System.getProperty("path.separator") + inherited);
        environment.put("MYPYPATH", modulePath); environment.put("PYTHONDONTWRITEBYTECODE", "1");
        environment.put("TEMP", scratch.toString()); environment.put("TMP", scratch.toString()); environment.put("RUNNER_TEMP", scratch.toString());
        return Map.copyOf(environment);
    }

    public record AcceptanceReceipt(String schema, String machineId, String startedAtUtc,
                                    String observedAtUtc, String status, String error,
                                    ControlBuild.FileRef buildReceiptRef,
                                    List<ControlBuild.FileRef> pythonSourceRefs,
                                    List<CommandEvidence> commands,
                                    int completeNewPythonModulesStaticChecked,
                                    int actualHttpTestMethods, int nestedOriginalConsumerLineages,
                                    int gameNativeRpcOrCampaignLedgerWrites,
                                     boolean sameHostRetainedForRequestedSdk,
                                    boolean hostedCiCannotClaimFrozenN46ActualRuntime) {}

    /** Build validation is delegated to the sole shared ControlBuild producer/reader. */
    public static void run(Config requested) throws IOException {
        runConsumers(requested, null, false);
    }

    /** Complete the same original static/HTTP group, transferring its one live Owner to the caller. */
    public static Session retainForSoftwareFixtures(Config requested, RootSoftwareFixtureHandoff.Request fixture) throws IOException {
        if (fixture == null) throw new IllegalArgumentException("Explicit original software fixture inputs required before starting a service");
        return runConsumers(requested, fixture, true);
    }

    private static Session runConsumers(Config requested, RootSoftwareFixtureHandoff.Request fixture, boolean retain) throws IOException {
        Config config = normalized(requested);
        ControlBuild.verifiedCompletedReceipt(ControlBuild.FileRef.measure(config.buildReceipt()));
        String machine = WindowsJobProcess.currentMachineId();
        String started = Instant.now().toString();
        if (Files.exists(config.workRoot()) || config.workRoot().startsWith(config.repoRoot())) {
            throw new IllegalArgumentException("new external CI metadata task root required");
        }
        Files.createDirectory(config.workRoot());
        Path logs = Files.createDirectory(config.workRoot().resolve("logs"));
        Path scratch = Files.createDirectory(config.workRoot().resolve("scratch"));
        Path clientPath = config.repoRoot().resolve("tools/g2_saved_campaign/java_map_admission_client_v1.py");
        Path regressionPath = config.repoRoot().resolve("tools/g2_saved_campaign/test_java_map_admission_v1.py");
        List<ControlBuild.FileRef> pythonSources = List.of(
                ControlBuild.FileRef.measure(clientPath), ControlBuild.FileRef.measure(regressionPath));
        Map<String, String> environment = pythonEnvironment(config, scratch);
        List<CommandEvidence> commands = new ArrayList<>();
        String failure = null;
        boolean completed = false;
        Session service = null;
        try {
            List<String> staticArguments = originalStaticArguments(config);
            CommandEvidence staticCheck = command(config, environment, logs, "whole-modules-static",
                    staticArguments, () -> {});
            commands.add(staticCheck);
            if (!staticCheck.result().passed()) {
                throw new IllegalStateException("whole Python client/regression strict command failed");
            }
            var ownerConfig = serviceConfig(config, fixture, null);
            service = retain(config, logs, scratch, environment, fixture == null
                    ? MapAdmissionServiceOwner.start(ownerConfig) : MapAdmissionServiceOwner.startWithProjection(ownerConfig), fixture != null);
            {
                service.verifyImmutableInputs();
                CommandEvidence regression;
                try {
                    regression = service.python("actual-java-all-consumers", originalConsumerArguments());
                } catch (CommandQualificationFailure failureAfterExecution) {
                    commands.add(failureAfterExecution.evidence()); throw failureAfterExecution;
                }
                commands.add(regression);
                if (!regression.result().passed()) {
                    throw new IllegalStateException("actual Java HTTP -> Python client -> original consumers failed");
                }
                String summary = Files.readString(Path.of(regression.stderrRef().path()), StandardCharsets.UTF_8);
                requireOriginalConsumerSummary(summary);
                service.verifyImmutableInputs();
            }
            for (ControlBuild.FileRef source : pythonSources) { source.verify(); }
            if (!retain) { service.close(); service = null; }
            completed = true;
        } catch (IOException | RuntimeException error) {
            failure = error.getClass().getName() + ": " + error.getMessage();
        } finally {
            if (!completed && service != null) {
                try { service.close(); }
                catch (RuntimeException cleanup) { failure = (failure == null ? "" : failure + "; ") + "Original service closure failed: " + cleanup.getMessage(); }
            }
            if (!completed && failure == null) {
                failure = "execution did not reach complete validation and service closure";
            }
            try { MapAdmissionServiceOwner.publish(logs.resolve("actual.json"), new AcceptanceReceipt(
                    "xar.java-map-portable-CI-actual/v2", machine, started, Instant.now().toString(),
                    failure == null ? "PASS" : "RED", failure,
                    ControlBuild.FileRef.measure(config.buildReceipt()), pythonSources, List.copyOf(commands),
                    commands.isEmpty() || !commands.getFirst().result().passed() ? 0 : 2,
                    failure == null ? 6 : 0, failure == null ? 3 : 0, 0, completed && retain, true)); }
            catch (IOException | RuntimeException publicationFailure) {
                if (service != null) try { service.close(); } catch (RuntimeException cleanup) { publicationFailure.addSuppressed(cleanup); }
                throw publicationFailure;
            }
        }
        if (failure != null) { throw new IllegalStateException(failure); }
        return service;
    }

    static List<String> originalStaticArguments(Config config) {
        return List.of("-B", "-X", "utf8", "-m", "mypy", "--strict", "--strict-equality", "--explicit-package-bases",
                "--follow-imports=silent", "--no-incremental", "--cache-dir", "nul",
                config.repoRoot().resolve("tools/g2_saved_campaign/java_map_admission_client_v1.py").toString(),
                config.repoRoot().resolve("tools/g2_saved_campaign/test_java_map_admission_v1.py").toString());
    }
    static List<String> originalConsumerArguments() {
        return List.of("-B", "-X", "utf8", "-m", "unittest", "-v", "tools.g2_saved_campaign.test_java_map_admission_v1");
    }
    static void requireOriginalConsumerSummary(String summary) {
        if (!summary.contains("\nRan 6 tests in ") || !summary.stripTrailing().endsWith("\nOK"))
            throw new IllegalStateException("All six actual tests, zero skips/expected failures, required");
    }

    /** Same complete original group, using this Session's guarded command path and unique labels. */
    public static OriginalMapConsumerGroup runOriginalMapConsumerGroup(Session session) throws IOException {
        Objects.requireNonNull(session); session.verifyImmutableInputs();
        Path base = session.config().repoRoot().resolve("tools/g2_saved_campaign");
        var sources = List.of(ControlBuild.FileRef.measure(base.resolve("java_map_admission_client_v1.py")),
                ControlBuild.FileRef.measure(base.resolve("test_java_map_admission_v1.py")));
        CommandEvidence strict = null, regression = null; boolean regressionStarted = false;
        try {
            strict = session.python("whole-modules-static", originalStaticArguments(session.config()));
            if (!strict.result().passed()) throw new IllegalStateException("Whole original Python modules strict command failed");
            regressionStarted = true;
            regression = session.python("actual-java-all-consumers", originalConsumerArguments());
            if (!regression.result().passed()) throw new IllegalStateException("Actual Java HTTP original consumer command failed");
            requireOriginalConsumerSummary(Files.readString(Path.of(regression.stderrRef().path()), StandardCharsets.UTF_8));
            for (var source : sources) source.verify(); session.verifyImmutableInputs();
            return new OriginalMapConsumerGroup(strict, regression);
        } catch (CommandQualificationFailure failure) {
            if (regressionStarted) regression = failure.evidence(); else strict = failure.evidence();
            throw new OriginalMapConsumerGroupFailure(strict, regression, failure);
        } catch (IOException | RuntimeException failure) {
            throw new OriginalMapConsumerGroupFailure(strict, regression, failure);
        }
    }

    private static CommandEvidence command(Config config, Map<String, String> environment,
            Path logs, String label, List<String> arguments, Runnable guard) throws IOException {
        Path stdout = logs.resolve(label + ".stdout.log");
        Path stderr = logs.resolve(label + ".stderr.log");
        WindowsJobProcess.CommandResult result;
        try (WindowsJobProcess child = WindowsJobProcess.start(new WindowsJobProcess.CommandSpec(
                config.pythonExecutable(), arguments, config.repoRoot(), Map.copyOf(environment),
                stdout, stderr, COMMAND_MEMORY_LIMIT))) {
            try {
                result = child.await(Duration.ofMinutes(5), config.leaseDeadline(), () -> {
                guard.run();
                try {
                    if (Files.size(stdout) + Files.size(stderr) > (4L << 20)) {
                        throw new IllegalStateException("four MiB per-command log budget exhausted");
                    }
                } catch (IOException error) { throw new IllegalStateException("command log budget unavailable", error); }
                });
                if (Files.size(stdout) + Files.size(stderr) > (4L << 20)) {
                    throw new IOException("actual completed child exceeded its four MiB log budget");
                }
            } catch (InterruptedException error) {
                Thread.currentThread().interrupt();
                throw new IOException("actual Java CI child wait interrupted", error);
            }
        }
        return new CommandEvidence(result, ControlBuild.FileRef.measure(stdout), ControlBuild.FileRef.measure(stderr));
    }

    public static void main(String[] arguments) throws IOException {
        Map<String, String> values = new HashMap<>();
        List<String> allowed = List.of("--repo-root", "--build-receipt", "--work-root", "--java-executable",
                "--python-executable", "--lease-deadline", "--port");
        if (arguments.length != allowed.size() * 2) {
            throw new IllegalArgumentException("all seven explicit CI configuration fields are required; no skip");
        }
        for (int index = 0; index < arguments.length; index += 2) {
            if (!allowed.contains(arguments[index]) || values.putIfAbsent(arguments[index], arguments[index + 1]) != null) {
                throw new IllegalArgumentException("unknown or duplicate Java CI configuration field");
            }
        }
        if (values.size() != allowed.size()) { throw new IllegalArgumentException("missing Java CI configuration field"); }
        run(new Config(Path.of(values.get("--repo-root")), Path.of(values.get("--build-receipt")),
                Path.of(values.get("--work-root")), Path.of(values.get("--java-executable")),
                Path.of(values.get("--python-executable")), Instant.parse(values.get("--lease-deadline")),
                Integer.parseInt(values.get("--port"))));
    }
}
