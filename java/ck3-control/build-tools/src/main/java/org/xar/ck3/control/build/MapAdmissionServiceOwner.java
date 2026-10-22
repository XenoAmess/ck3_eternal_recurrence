package org.xar.ck3.control.build;

import java.io.IOException;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.Proxy;
import java.net.URI;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Duration;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.TreeMap;

/** Shared Java service lifecycle; never depends on a Python or Java test runner. */
public final class MapAdmissionServiceOwner {
    public static final String PRODUCER = "java-quarkus-map-admission/v1";
    public static final String PRODUCER_VERSION = "0.1.0";
    public static final String COMPOSE_PATH = "/v1/map-admissions/compose";
    private static final long MEMORY_LIMIT = 512L << 20;
    private static final long OUTPUT_BUDGET = 16L << 20;
    static final int MAX_PROGRAM_MANIFEST_BYTES = 1 << 20;
    static final int MAX_SMALL_RECEIPT_BYTES = 1 << 16;

    private MapAdmissionServiceOwner() {}

    public record Config(Path buildReceipt, Path workRoot, Path javaExecutable,
                         Instant leaseDeadline, int port) {
        public Config {
            Objects.requireNonNull(buildReceipt);
            Objects.requireNonNull(workRoot);
            Objects.requireNonNull(javaExecutable);
            Objects.requireNonNull(leaseDeadline);
            if (port < 1 || port > 65535 || !leaseDeadline.isAfter(Instant.now())
                    || leaseDeadline.isAfter(Instant.now().plus(Duration.ofHours(2)))) {
                throw new IllegalArgumentException("explicit fresh finite service authority and TCP port required");
            }
        }
    }

    public record ProcessWire(long pid, String creationFiletime, String executable) {
        public ProcessWire {
            Objects.requireNonNull(creationFiletime);
            Objects.requireNonNull(executable);
            if (pid < 1 || pid > 0xffff_ffffL || !creationFiletime.matches("[1-9][0-9]{0,19}")
                    || new BigInteger(creationFiletime).compareTo(new BigInteger("18446744073709551615")) > 0
                    || !Path.of(executable).isAbsolute()) {
                throw new IllegalArgumentException("original native PID, exact decimal birth and absolute EXE required");
            }
        }

        static ProcessWire from(WindowsJobProcess.ProcessIdentity identity) {
            return new ProcessWire(identity.pid(), identity.creationFiletimeDecimal(), identity.executable());
        }
    }

    public record ServiceStatus(String schema, String service, String status,
                                int inputMaxBytes, int outputMaxBytes) {}

    public record ProducerIdentity(String schema, String producer, String producerVersion,
                                   String requestSchema, String implementation, String mavenGroupId,
                                   String mavenArtifactId, String mavenVersion) {}

    public record ProgramManifest(String schema, String machineId, String observedAtUtc,
                                  String deploymentRoot, List<ControlBuild.FileRef> files,
                                  List<ControlBuild.FileRef> sourceRefs,
                                  ControlBuild.FileRef buildReceiptRef,
                                  ControlBuild.FileRef javaExecutableRef,
                                  boolean compiledSourceMatchesOriginal,
                                  boolean runnerJarAloneIsNotDeploymentProof) {}

    public record RunningReceipt(String schema, String machineId, String observedAtUtc, String status,
                                 String producer, String producerVersion, String url,
                                 ControlBuild.FileRef programRef, List<ControlBuild.FileRef> sourceRefs,
                                 ProcessWire process) {}

    public record StartedReceipt(String schema, String machineId, String observedAtUtc,
                                 String leaseDeadlineUtc, ControlBuild.FileRef serviceEvidenceRef,
                                 ControlBuild.FileRef programRef, ProcessWire process,
                                 List<NativeTcpListener.ListenerOwner> listenerOwners,
                                 ServiceStatus readiness, ProducerIdentity producerIdentity,
                                 long jobMemoryLimitBytes, int gameRpcOrCampaignLedgerWrites) {}

    public record ClosedReceipt(String schema, String machineId, String observedAtUtc,
                                String status, ProcessWire originalProcess,
                                WindowsJobProcess.CommandResult originalChildResult,
                                int jobActiveFinal, long peakJobMemoryBytes,
                                int gameRpcOrCampaignLedgerWrites) {}

    /** The caller must retain this owner until consumer completion or explicit Root close. */
    public static final class Session implements AutoCloseable {
        private final Config config;
        private final WindowsJobProcess child;
        private final WindowsJobProcess.ProcessIdentity identity;
        private final ControlBuild.FileRef evidenceRef;
        private final ControlBuild.FileRef manifestRef;
        private final List<ControlBuild.FileRef> sources;
        private final List<ControlBuild.FileRef> deployment;
        private final String machine;
        private boolean closed;

        private Session(Config config, WindowsJobProcess child,
                        ControlBuild.FileRef evidenceRef, ControlBuild.FileRef manifestRef,
                        List<ControlBuild.FileRef> sources, List<ControlBuild.FileRef> deployment,
                        String machine) {
            this.config = config;
            this.child = child;
            this.identity = child.identity();
            this.evidenceRef = evidenceRef;
            this.manifestRef = manifestRef;
            this.sources = List.copyOf(sources);
            this.deployment = List.copyOf(deployment);
            this.machine = machine;
        }

        public ControlBuild.FileRef evidenceRef() { return evidenceRef; }
        public ControlBuild.FileRef manifestRef() { return manifestRef; }
        public WindowsJobProcess.ProcessIdentity identity() { return identity; }

        /** Real kernel and native endpoint ownership; this cannot grant Game qualification. */
        public void requireCurrent() {
            if (closed || !Instant.now().isBefore(config.leaseDeadline()) || !child.isRunning()
                    || !WindowsJobProcess.exactProcess(identity.pid()).equals(identity)
                    || !NativeTcpListener.owners(config.port()).equals(List.of(
                            new NativeTcpListener.ListenerOwner(identity.pid(), "127.0.0.1", config.port())))) {
                throw new IllegalStateException("original live Java service generation/listener/finite authority required");
            }
            WindowsJobProcess.Accounting accounting = child.accounting();
            if (accounting.peakJobMemoryBytes() > MEMORY_LIMIT || accounting.memoryLimitBytes() != MEMORY_LIMIT) {
                throw new IllegalStateException("actual Java service exceeded its hard Job memory bound");
            }
            requireOutputBudget(config.workRoot());
        }

        /** Source/closure measurements run at boundaries, not once for every HTTP request. */
        public void verifyImmutableInputs() throws IOException {
            evidenceRef.verify();
            manifestRef.verify();
            for (ControlBuild.FileRef reference : sources) { reference.verify(); }
            for (ControlBuild.FileRef reference : deployment) { reference.verify(); }
            requireCurrent();
        }

        @Override
        public void close() {
            if (closed) { return; }
            closed = true;
            try {
                if (child.isRunning()) { child.terminate(75); }
                WindowsJobProcess.CommandResult result = child.await(Duration.ofSeconds(10),
                        Instant.now().plusSeconds(15), () -> {});
                int active = result.accounting().activeProcesses();
                long peak = result.accounting().peakJobMemoryBytes();
                if (active != 0 || peak > MEMORY_LIMIT) {
                    throw new IllegalStateException("original Java service tree did not close within its Job bound");
                }
                publish(config.workRoot().resolve("logs/service-closed.json"), new ClosedReceipt(
                        "xar.java-map-service-owner-closed/v1", machine, Instant.now().toString(),
                        "CLOSED", ProcessWire.from(identity), result, active, peak, 0));
            } catch (InterruptedException error) {
                Thread.currentThread().interrupt();
                throw new IllegalStateException("actual Java service closure was interrupted", error);
            } catch (IOException error) {
                throw new IllegalStateException("actual Java service closure evidence unavailable", error);
            } finally {
                child.close();
            }
        }
    }

    public static Session start(Config requested) throws IOException {
        Config config = new Config(requested.buildReceipt().toRealPath(),
                requested.workRoot().toAbsolutePath().normalize(), requested.javaExecutable().toRealPath(),
                requested.leaseDeadline(), requested.port());
        ControlBuild.BuildReceipt build = ControlBuild.acceptedReceipt(config.buildReceipt());
        if (build.targetKind() != ControlBuild.TargetKind.SERVICE_FAST_JAR) {
            throw new IllegalArgumentException("service admission requires the actual service fast-jar deployment");
        }
        String machine = WindowsJobProcess.currentMachineId();
        if (!ControlBuild.FileRef.measure(config.javaExecutable()).equals(build.javaExecutableRef())) {
            throw new IllegalArgumentException("service must use the exact qualified Java executable");
        }
        if (!machine.equals(build.machineId()) || Files.exists(config.workRoot(), LinkOption.NOFOLLOW_LINKS)) {
            throw new IllegalArgumentException("current machine and new service work root required");
        }
        Path deployment = Path.of(build.deploymentRoot().toString()).toRealPath();
        Path source = Path.of(build.sourceRoot().toString()).toRealPath();
        if (config.workRoot().startsWith(source) || config.workRoot().startsWith(deployment)
                || source.startsWith(config.workRoot()) || deployment.startsWith(config.workRoot())) {
            throw new IllegalArgumentException("service metadata must have an independent task root");
        }
        Path parent = config.workRoot().getParent().toRealPath();
        String systemRoot = Objects.requireNonNull(System.getenv("SystemRoot"));
        if (parent.getRoot().equals(Path.of(systemRoot).getRoot())
                || Files.getFileStore(parent).getUsableSpace() < OUTPUT_BUDGET) {
            throw new IllegalArgumentException("approved task volume and reserved service metadata capacity required");
        }
        if (!NativeTcpListener.owners(config.port()).isEmpty()) {
            throw new IllegalStateException("port already owned; existing services must not be displaced");
        }
        Files.createDirectory(config.workRoot());
        Path logs = Files.createDirectory(config.workRoot().resolve("logs"));
        Path scratch = Files.createDirectory(config.workRoot().resolve("scratch"));
        ControlBuild.FileRef buildRef = ControlBuild.FileRef.measure(config.buildReceipt());
        ControlBuild.FileRef manifestRef = publishProgramManifest(logs.resolve("program-manifest.json"), new ProgramManifest(
                "xar.java-map-complete-fastjar-deployment/v1", machine, Instant.now().toString(),
                deployment.toString(), List.copyOf(build.completeDeployment()), List.copyOf(build.sourcePins()),
                buildRef, ControlBuild.FileRef.measure(config.javaExecutable()), true, true));
        Map<String, String> environment = new TreeMap<>(String.CASE_INSENSITIVE_ORDER);
        environment.putAll(System.getenv());
        environment.put("TEMP", scratch.toString());
        environment.put("TMP", scratch.toString());
        environment.remove("JAVA_TOOL_OPTIONS");
        environment.remove("JDK_JAVA_OPTIONS");
        List<String> arguments = List.of("-Xms32m", "-Xmx256m", "-XX:MaxMetaspaceSize=96m",
                "-XX:ReservedCodeCacheSize=48m", "-XX:MaxDirectMemorySize=32m", "-Xss512k",
                "-Djava.io.tmpdir=" + scratch, "-Djna.tmpdir=" + scratch,
                "-Dquarkus.http.port=" + config.port(), "-jar", deployment.resolve("quarkus-run.jar").toString());
        WindowsJobProcess child = WindowsJobProcess.start(new WindowsJobProcess.CommandSpec(
                config.javaExecutable(), arguments, deployment, Map.copyOf(environment),
                logs.resolve("service.stdout.log"), logs.resolve("service.stderr.log"), MEMORY_LIMIT));
        try {
            WindowsJobProcess.ProcessIdentity identity = child.identity();
            ServiceStatus readiness;
            ProducerIdentity producer;
            long until = System.nanoTime() + Duration.ofSeconds(60).toNanos();
            while (true) {
                if (!child.isRunning() || !Instant.now().isBefore(config.leaseDeadline())
                        || System.nanoTime() >= until) {
                    throw new IllegalStateException("actual Java service readiness did not complete in authority");
                }
                requireOutputBudget(config.workRoot());
                try {
                    readiness = get(config.port(), "/v1/status", ServiceStatus.class);
                    producer = get(config.port(), "/v1/map-admissions/identity", ProducerIdentity.class);
                    if (!expectedStatus().equals(readiness) || !expectedProducer().equals(producer)) {
                        throw new IllegalArgumentException("exact Java status and producer identity required");
                    }
                    if (!NativeTcpListener.owners(config.port()).equals(List.of(
                            new NativeTcpListener.ListenerOwner(identity.pid(), "127.0.0.1", config.port())))
                            || !WindowsJobProcess.exactProcess(identity.pid()).equals(identity)) {
                        throw new IllegalArgumentException("original Java process must own the actual native endpoint");
                    }
                    break;
                } catch (IOException | IllegalArgumentException error) {
                    pause();
                }
            }
            for (ControlBuild.FileRef reference : build.sourcePins()) { reference.verify(); }
            for (ControlBuild.FileRef reference : build.completeDeployment()) { reference.verify(); }
            ControlBuild.FileRef evidenceRef = publish(logs.resolve("service-running.json"), new RunningReceipt(
                    "xar.java-map-service-running/v1", machine, Instant.now().toString(), "ACTUAL_RUNNING",
                    PRODUCER, PRODUCER_VERSION, "http://127.0.0.1:" + config.port() + COMPOSE_PATH,
                    manifestRef, List.copyOf(build.sourcePins()), ProcessWire.from(identity)));
            publish(logs.resolve("service-started.json"), new StartedReceipt(
                    "xar.java-map-service-owner-started/v1", machine, Instant.now().toString(),
                    config.leaseDeadline().toString(), evidenceRef, manifestRef, ProcessWire.from(identity),
                    NativeTcpListener.owners(config.port()), readiness, producer, MEMORY_LIMIT, 0));
            Session session = new Session(config, child, evidenceRef, manifestRef,
                    build.sourcePins(), build.completeDeployment(), machine);
            session.requireCurrent();
            return session;
        } catch (IOException | RuntimeException | Error failure) {
            child.close();
            throw failure;
        }
    }

    static ServiceStatus expectedStatus() {
        return new ServiceStatus("xar.ck3.control.service-status/v1", "ck3-control", "ready", 65536, 16384);
    }

    static ProducerIdentity expectedProducer() {
        return new ProducerIdentity("xar.java-map-admission-producer-identity/v1", PRODUCER, PRODUCER_VERSION,
                "xar.java-campaign-map-compose-request/v1", "org.xar.ck3.control.service.CampaignMapAdmissionResource",
                "org.xar.ck3.control", "ck3-control-local-service", "0.1.0-SNAPSHOT");
    }

    private static <T> T get(int port, String endpoint, Class<T> type) throws IOException {
        var connection = URI.create("http://127.0.0.1:" + port + endpoint).toURL().openConnection(Proxy.NO_PROXY);
        if (!(connection instanceof HttpURLConnection http)) {
            throw new IOException("original loopback HTTP connection required");
        }
        http.setConnectTimeout(2000);
        http.setReadTimeout(2000);
        try {
            http.setRequestMethod("GET");
            http.setRequestProperty("Connection", "close");
            if (http.getResponseCode() != 200) { throw new IOException("Java status HTTP 200 required"); }
            byte[] raw;
            try (InputStream stream = http.getInputStream()) { raw = stream.readNBytes(16385); }
            if (raw.length > 16384) { throw new IOException("bounded original Java status response required"); }
            return ControlBuild.strictMapper().readValue(raw, type);
        } finally {
            http.disconnect();
        }
    }

    static <T> ControlBuild.FileRef publish(Path path, T receipt) throws IOException {
        return publishBounded(path, receipt, MAX_SMALL_RECEIPT_BYTES);
    }

    /** Matches the existing frozen Python program_ref reader's 1 MiB domain. */
    static ControlBuild.FileRef publishProgramManifest(Path path, ProgramManifest manifest) throws IOException {
        return publishBounded(path, manifest, MAX_PROGRAM_MANIFEST_BYTES);
    }

    private static <T> ControlBuild.FileRef publishBounded(Path path, T receipt, int maximum) throws IOException {
        Objects.requireNonNull(receipt);
        byte[] raw = ControlBuild.strictMapper().writerWithDefaultPrettyPrinter().writeValueAsBytes(receipt);
        if (raw.length > maximum) { throw new IOException("complete service evidence exceeded its role-specific bound: " + maximum); }
        Files.write(path, raw, StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE);
        return ControlBuild.FileRef.measure(path);
    }

    private static void requireOutputBudget(Path root) {
        try (var paths = Files.walk(root)) {
            long bytes = 0;
            long entries = 0;
            for (Path path : paths.toList()) {
                if (++entries > 10000 || Files.isSymbolicLink(path)) {
                    throw new IllegalStateException("bounded original service metadata tree required");
                }
                if (Files.isRegularFile(path, LinkOption.NOFOLLOW_LINKS)) {
                    bytes = Math.addExact(bytes, Files.size(path));
                }
                if (bytes > OUTPUT_BUDGET) { throw new IllegalStateException("service output budget exhausted"); }
            }
        } catch (IOException error) {
            throw new IllegalStateException("actual service output budget unavailable", error);
        }
    }

    private static void pause() {
        try { Thread.sleep(100); }
        catch (InterruptedException error) {
            Thread.currentThread().interrupt();
            throw new IllegalStateException("Java service readiness interrupted", error);
        }
    }
}
