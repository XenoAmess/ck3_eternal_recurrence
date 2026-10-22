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
                         Path pythonExecutable, Instant leaseDeadline, int port) {
        public Config {
            Objects.requireNonNull(repoRoot);
            Objects.requireNonNull(buildReceipt);
            Objects.requireNonNull(workRoot);
            Objects.requireNonNull(javaExecutable);
            Objects.requireNonNull(pythonExecutable);
            Objects.requireNonNull(leaseDeadline);
            if (port < 1 || port > 65535) { throw new IllegalArgumentException("bounded explicit TCP port required"); }
        }
    }

    public record CommandEvidence(WindowsJobProcess.CommandResult result,
                                  ControlBuild.FileRef stdoutRef, ControlBuild.FileRef stderrRef) {}

    public record AcceptanceReceipt(String schema, String machineId, String startedAtUtc,
                                    String observedAtUtc, String status, String error,
                                    ControlBuild.FileRef buildReceiptRef,
                                    List<ControlBuild.FileRef> pythonSourceRefs,
                                    List<CommandEvidence> commands,
                                    int completeNewPythonModulesStaticChecked,
                                    int actualHttpTestMethods, int nestedOriginalConsumerLineages,
                                    int gameNativeRpcOrCampaignLedgerWrites,
                                    boolean hostedCiCannotClaimFrozenN46ActualRuntime) {}

    /** Build validation is delegated to the sole shared ControlBuild producer/reader. */
    public static void run(Config requested) throws IOException {
        Config config = new Config(requested.repoRoot().toRealPath(), requested.buildReceipt().toRealPath(),
                requested.workRoot().toAbsolutePath().normalize(), requested.javaExecutable().toRealPath(),
                requested.pythonExecutable().toRealPath(), requested.leaseDeadline(), requested.port());
        ControlBuild.acceptedReceipt(config.buildReceipt());
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
        Map<String, String> environment = new TreeMap<>(String.CASE_INSENSITIVE_ORDER);
        environment.putAll(System.getenv());
        String modulePath = config.repoRoot() + System.getProperty("path.separator")
                + config.repoRoot().resolve("ck3_autonomous_player/src");
        String inheritedPythonPath = environment.get("PYTHONPATH");
        String runtimeModulePath = inheritedPythonPath == null || inheritedPythonPath.isBlank()
                ? modulePath : modulePath + System.getProperty("path.separator") + inheritedPythonPath;
        environment.put("PYTHONPATH", runtimeModulePath);
        environment.put("MYPYPATH", modulePath);
        environment.put("PYTHONDONTWRITEBYTECODE", "1");
        environment.put("TEMP", scratch.toString());
        environment.put("TMP", scratch.toString());
        environment.put("RUNNER_TEMP", scratch.toString());
        List<CommandEvidence> commands = new ArrayList<>();
        String failure = null;
        boolean completed = false;
        try {
            List<String> staticArguments = List.of("-B", "-X", "utf8", "-m", "mypy", "--strict",
                    "--strict-equality", "--explicit-package-bases", "--follow-imports=silent",
                    "--no-incremental", "--cache-dir", "nul", clientPath.toString(), regressionPath.toString());
            CommandEvidence staticCheck = command(config, environment, logs, "whole-modules-static",
                    staticArguments, () -> {});
            commands.add(staticCheck);
            if (!staticCheck.result().passed()) {
                throw new IllegalStateException("whole Python client/regression strict command failed");
            }
            try (MapAdmissionServiceOwner.Session service = MapAdmissionServiceOwner.start(
                    new MapAdmissionServiceOwner.Config(config.buildReceipt(), config.workRoot().resolve("service"),
                            config.javaExecutable(), config.leaseDeadline(), config.port()))) {
                environment.put("XAR_JAVA_MAP_SERVICE_EVIDENCE", service.evidenceRef().path());
                service.verifyImmutableInputs();
                CommandEvidence regression = command(config, environment, logs, "actual-java-all-consumers",
                        List.of("-B", "-X", "utf8", "-m", "unittest", "-v",
                                "tools.g2_saved_campaign.test_java_map_admission_v1"), service::requireCurrent);
                commands.add(regression);
                if (!regression.result().passed()) {
                    throw new IllegalStateException("actual Java HTTP -> Python client -> original consumers failed");
                }
                String summary = Files.readString(Path.of(regression.stderrRef().path()), StandardCharsets.UTF_8);
                if (!summary.contains("\nRan 6 tests in ") || !summary.stripTrailing().endsWith("\nOK")) {
                    throw new IllegalStateException("all six actual tests, zero skips/expected failures, required");
                }
                service.verifyImmutableInputs();
            }
            for (ControlBuild.FileRef source : pythonSources) { source.verify(); }
            completed = true;
        } catch (IOException | RuntimeException error) {
            failure = error.getClass().getName() + ": " + error.getMessage();
        } finally {
            if (!completed && failure == null) {
                failure = "execution did not reach complete validation and service closure";
            }
            MapAdmissionServiceOwner.publish(logs.resolve("actual.json"), new AcceptanceReceipt(
                    "xar.java-map-portable-CI-actual/v1", machine, started, Instant.now().toString(),
                    failure == null ? "PASS" : "RED", failure,
                    ControlBuild.FileRef.measure(config.buildReceipt()), pythonSources, List.copyOf(commands),
                    commands.isEmpty() || !commands.getFirst().result().passed() ? 0 : 2,
                    failure == null ? 6 : 0, failure == null ? 3 : 0, 0, true));
        }
        if (failure != null) { throw new IllegalStateException(failure); }
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
