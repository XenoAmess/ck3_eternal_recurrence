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
import java.util.ArrayList;
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
    static final int MAX_PROJECTION_RUNNING_BYTES = 1 << 19;

    private MapAdmissionServiceOwner() {}

    public record Config(Path buildReceipt, Path workRoot, Path javaExecutable,
                         Instant leaseDeadline, int port, Path eventStateRoot, Path stockGameRoot, Path evidenceGrantsManifest,
                         ProjectionOfflineContext.Publishing offlinePublishing) {
        public Config(Path buildReceipt, Path workRoot, Path javaExecutable, Instant leaseDeadline, int port) {
            this(buildReceipt, workRoot, javaExecutable, leaseDeadline, port, null, null, null, null);
        }
        public Config(Path buildReceipt, Path workRoot, Path javaExecutable, Instant leaseDeadline, int port,
                Path eventStateRoot, Path stockGameRoot) {
            this(buildReceipt, workRoot, javaExecutable, leaseDeadline, port, eventStateRoot, stockGameRoot, null, null);
        }
        public Config(Path buildReceipt, Path workRoot, Path javaExecutable, Instant leaseDeadline, int port,
                Path eventStateRoot, Path stockGameRoot, Path evidenceGrantsManifest) {
            this(buildReceipt, workRoot, javaExecutable, leaseDeadline, port, eventStateRoot, stockGameRoot, evidenceGrantsManifest, null);
        }
        public Config {
            Objects.requireNonNull(buildReceipt);
            Objects.requireNonNull(workRoot);
            Objects.requireNonNull(javaExecutable);
            Objects.requireNonNull(leaseDeadline);
            if ((eventStateRoot == null) != (stockGameRoot == null)
                    || (eventStateRoot != null && (!eventStateRoot.isAbsolute() || !stockGameRoot.isAbsolute()
                        || eventStateRoot.normalize().equals(stockGameRoot.normalize())))) {
                throw new IllegalArgumentException("Explicit paired distinct absolute event source roots required");
            }
            if (evidenceGrantsManifest != null && (eventStateRoot == null || !evidenceGrantsManifest.isAbsolute()
                    || evidenceGrantsManifest.normalize().startsWith(stockGameRoot.normalize()))) {
                throw new IllegalArgumentException("Fixed absolute evidence manifest requires explicit paired event source roots");
            }
            if (offlinePublishing != null && (evidenceGrantsManifest == null
                    || (offlinePublishing.knowledgeRoot() != null && offlinePublishing.knowledgeRoot().normalize().startsWith(stockGameRoot.normalize())))) {
                throw new IllegalArgumentException("Explicit offline publishing requires fixed event roots and non-game knowledge/manifest roots");
            }
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


    public record ProjectionProgramManifest(String schema, String machineId, String observedAtUtc,
            String deploymentRoot, List<ControlBuild.FileRef> files, List<ControlBuild.FileRef> sourceRefs,
            ControlBuild.FileRef buildReceiptRef, ControlBuild.FileRef javaExecutableRef,
            boolean compiledSourceMatchesOriginal, boolean runnerJarAloneIsNotDeploymentProof,
            ProjectionDeploymentProof.Attestation projection, ObservedHostContext hostContext,
            ProjectionRuntimeSources.ConfiguredManifest runtimeSources, ProjectionOfflineContext.Observed offlineContext,
            ProjectionCaptureScope.Qualification qualification, ProjectionCaptureScope.Bound captureScope) {
        public ProjectionProgramManifest {
            if (!"xar.java-projection-complete-fastjar-deployment/v2".equals(schema) || machineId == null
                    || machineId.isBlank() || projection == null || !compiledSourceMatchesOriginal
                    || !runnerJarAloneIsNotDeploymentProof) throw new IllegalArgumentException("Qualified complete projection deployment required");
            if (qualification == null || (qualification == ProjectionCaptureScope.Qualification.TEST_COMPILED_CAPTURE_ONLY) != (captureScope != null)
                    || (captureScope != null && offlineContext != null)) throw new IllegalArgumentException("Explicit capture scope cannot grant offline publishing or normal software qualification");
            Instant.parse(observedAtUtc); files = List.copyOf(files); sourceRefs = List.copyOf(sourceRefs);
            Objects.requireNonNull(buildReceiptRef); Objects.requireNonNull(javaExecutableRef); Objects.requireNonNull(hostContext);
            if (offlineContext != null && (runtimeSources == null || !machineId.equals(offlineContext.context().machineId()))) {
                throw new IllegalArgumentException("Offline publishing proof requires fixed same-machine runtime source configuration");
            }
        }
    }

    public record ProjectionAdmission(ControlBuild.FileRef serviceEvidenceRef, ControlBuild.FileRef programRef,
            ProjectionDeploymentProof.Attestation attestation, ProcessWire processBefore, ProcessWire processAfter, ObservedHostContext hostContext) {
        public ProjectionAdmission {
            Objects.requireNonNull(serviceEvidenceRef); Objects.requireNonNull(programRef); Objects.requireNonNull(attestation); Objects.requireNonNull(hostContext);
            if (processBefore == null || !processBefore.equals(processAfter)) throw new IllegalArgumentException("Same actual kernel generation before and after qualification required");
        }
    }


    public record EventSourceRoots(String stateRoot, String stockGameRoot) {
        public EventSourceRoots {
            if (stateRoot == null || stockGameRoot == null || !Path.of(stateRoot).isAbsolute()
                    || !Path.of(stockGameRoot).isAbsolute() || Path.of(stateRoot).normalize().equals(Path.of(stockGameRoot).normalize())) {
                throw new IllegalArgumentException("Trusted event source roots must be distinct absolute paths");
            }
        }
    }

    public record HostContext(String schema, String machineId, String observedAtUtc, EventSourceRoots eventSources) {
        public HostContext {
            if (!"xar.projection-host-context/v1".equals(schema) || machineId == null || machineId.isBlank() || machineId.equals("unknown")) {
                throw new IllegalArgumentException("Actual qualified host context schema and machine required");
            }
            Instant.parse(observedAtUtc);
        }
    }

    public record ObservedHostContext(HostContext context, ControlBuild.FileRef responseRef) {
        public ObservedHostContext { Objects.requireNonNull(context); Objects.requireNonNull(responseRef); }
    }

    public record ProjectionRunningReceipt(String schema, String machineId, String observedAtUtc, String status,
            String producer, String producerVersion, String url, ControlBuild.FileRef programRef,
            List<ControlBuild.FileRef> sourceRefs, ProcessWire process, ObservedHostContext hostContext) {
        public ProjectionRunningReceipt {
            sourceRefs = List.copyOf(sourceRefs);
            if (sourceRefs.isEmpty() || sourceRefs.stream().map(ref -> Path.of(ref.path()).toAbsolutePath().normalize()).distinct().count() != sourceRefs.size()
                    || url == null || !url.matches("http://127\\.0\\.0\\.1:[1-9][0-9]{0,4}/v1/projections/call")) {
                throw new IllegalArgumentException("Unique complete source inventory and fixed loopback projection URL required");
            }
            int port = Integer.parseInt(url.substring("http://127.0.0.1:".length(), url.indexOf("/v1/projections/call")));
            if (port > 65535) throw new IllegalArgumentException("Bounded projection port required");
            if (!"xar.java-projection-service-running/v1".equals(schema) || !"ACTUAL_RUNNING".equals(status)
                    || !ProjectionDeploymentProof.PRODUCER.equals(producer) || !ProjectionDeploymentProof.VERSION.equals(producerVersion)
                    || hostContext == null || !hostContext.context().machineId().equals(machineId)) {
                throw new IllegalArgumentException("Exact projection running proof and same-machine observed host context required");
            }
            Instant.parse(observedAtUtc); Objects.requireNonNull(programRef); Objects.requireNonNull(process);
        }
    }

    public record ProjectionStartedReceipt(String schema, String machineId, String observedAtUtc, String leaseDeadlineUtc,
            ProjectionAdmission admission, List<NativeTcpListener.ListenerOwner> listenerOwners,
            ServiceStatus readiness, long jobMemoryLimitBytes, int gameRpcOrCampaignLedgerWrites) {
        public ProjectionStartedReceipt { listenerOwners = List.copyOf(listenerOwners); }
    }

    private record ServiceInputs(String machineId, String sourceRoot, String deploymentRoot,
            List<ControlBuild.FileRef> sourcePins, List<ControlBuild.FileRef> completeDeployment,
            ControlBuild.FileRef javaExecutableRef, ProjectionCaptureScope.Qualification qualification,
            ControlBuild.BuildReceipt verifiedReceipt, ControlBuild.CaptureBuildReceipt captureReceipt) {
        static ServiceInputs read(Path path, boolean capture) throws IOException {
            if (capture) {
                ControlBuild.CaptureBuildReceipt value = ControlBuild.acceptedCaptureReceipt(path);
                return new ServiceInputs(value.machineId(), value.sourceRoot(), value.deploymentRoot(), value.sourcePins(),
                        value.completeDeployment(), value.javaExecutableRef(), ProjectionCaptureScope.Qualification.TEST_COMPILED_CAPTURE_ONLY, null, value);
            }
            ControlBuild.BuildReceipt value = ControlBuild.acceptedReceipt(path);
            if (value.targetKind() != ControlBuild.TargetKind.SERVICE_FAST_JAR) throw new IOException("Actual service deployment required");
            return new ServiceInputs(value.machineId(), value.sourceRoot(), value.deploymentRoot(), value.sourcePins(),
                    value.completeDeployment(), value.javaExecutableRef(), ProjectionCaptureScope.Qualification.FULL_SOFTWARE, value, null);
        }
        ProjectionDeploymentProof.Attestation attest(ProjectionDeploymentProof.Identity identity,
                ProjectionDeploymentProof.CatalogInventory catalogs, String machine) throws IOException {
            return captureReceipt == null ? ProjectionDeploymentProof.attest(verifiedReceipt, identity, catalogs, machine)
                    : ProjectionDeploymentProof.attestCapture(captureReceipt, identity, catalogs, machine);
        }
    }

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
        private final ControlBuild.FileRef buildReceiptRef;
        private final ControlBuild.FileRef javaExecutableRef;
        private final ProjectionAdmission projection;
        private final ServiceInputs artifact;
        private final ProjectionCaptureScope.Bound captureScope;
        private boolean closed;

        private Session(Config config, WindowsJobProcess child,
                        ControlBuild.FileRef evidenceRef, ControlBuild.FileRef manifestRef,
                        List<ControlBuild.FileRef> sources, List<ControlBuild.FileRef> deployment,
                        String machine, ControlBuild.FileRef buildReceiptRef,
                        ControlBuild.FileRef javaExecutableRef, ProjectionAdmission projection,
                        ServiceInputs artifact, ProjectionCaptureScope.Bound captureScope) {
            this.config = config;
            this.child = child;
            this.identity = child.identity();
            this.evidenceRef = evidenceRef;
            this.manifestRef = manifestRef;
            this.sources = List.copyOf(sources);
            this.deployment = List.copyOf(deployment);
            this.machine = machine;
            this.buildReceiptRef = Objects.requireNonNull(buildReceiptRef);
            this.javaExecutableRef = Objects.requireNonNull(javaExecutableRef);
            this.projection = projection;
            this.artifact = artifact;
            this.captureScope = captureScope;
        }

        public ProjectionCaptureScope.Qualification qualification() { return artifact.qualification(); }
        public void requireFullSoftwareBuild() {
            if (captureScope != null) throw new IllegalStateException("Capture-only session cannot grant normal software/current/production qualification");
        }
        public ControlBuild.FileRef evidenceRef() { requireFullSoftwareBuild(); return evidenceRef; }
        public ControlBuild.FileRef manifestRef() { requireFullSoftwareBuild(); return manifestRef; }
        public WindowsJobProcess.ProcessIdentity identity() { return identity; }
        public ProjectionAdmission projectionAdmission() {
            if (projection == null) throw new IllegalStateException("This session did not qualify projection service");
            return projection;
        }

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
            if (evidenceRef != null) evidenceRef.verify();
            if (manifestRef != null) manifestRef.verify();
            if (captureScope != null) captureScope.verify();
            buildReceiptRef.verify();
            javaExecutableRef.verify();
            for (ControlBuild.FileRef reference : sources) { reference.verify(); }
            for (ControlBuild.FileRef reference : deployment) { reference.verify(); }
            if (projection != null) {
                projection.serviceEvidenceRef().verify(); projection.programRef().verify(); projection.hostContext().responseRef().verify();
                ProjectionProgramManifest originalProgram = ControlBuild.strictMapper().readValue(
                        Files.readAllBytes(Path.of(projection.programRef().path())), ProjectionProgramManifest.class);
                if (originalProgram.runtimeSources() != null) originalProgram.runtimeSources().initialSnapshotRef().verify();
                if (originalProgram.offlineContext() != null) {
                    originalProgram.offlineContext().responseRef().verify();
                    ProjectionOfflineContext.requireExpected(config, machine, getOfflineContext(config.port(), null));
                }
                requireContext(config, machine, getProjection(config.port(), "/v1/projections/context", HostContext.class));
                ProjectionDeploymentProof.Identity observed = getProjection(config.port(), "/v1/projections/identity", ProjectionDeploymentProof.Identity.class);
                ProjectionDeploymentProof.CatalogInventory catalogs = getProjection(config.port(), "/v1/projections/catalogs", ProjectionDeploymentProof.CatalogInventory.class);
                ServiceInputs accepted = ServiceInputs.read(config.buildReceipt(), captureScope != null);
                ProjectionDeploymentProof.Attestation current = accepted.attest(observed, catalogs, machine);
                if (captureScope != null) captureScope.requireCatalog(current);
                if (!projection.attestation().equals(current)) throw new IOException("Actual projection registration/profile/artifact closure changed");
            }
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

    public static Session start(Config requested) throws IOException { return startInternal(requested, false, null); }

    /** Same original Job, same JVM and same port; no leaf service or new native authority. */
    public static Session startWithProjection(Config requested) throws IOException { return startInternal(requested, true, null); }

    /** Same owner/JVM/Job, explicit request-limited pure-port capture; never publishes normal map/current evidence. */
    public static Session startForCapture(Config requested, Path captureRequestScope) throws IOException {
        Objects.requireNonNull(captureRequestScope);
        if (requested.offlinePublishing() != null) throw new IllegalArgumentException("Capture-only startup cannot enable offline knowledge publication");
        return startInternal(requested, true, captureRequestScope);
    }

    private static Session startInternal(Config requested, boolean qualifyProjection, Path captureScopePath) throws IOException {
        Config config = new Config(requested.buildReceipt().toRealPath(),
                requested.workRoot().toAbsolutePath().normalize(), requested.javaExecutable().toRealPath(),
                requested.leaseDeadline(), requested.port(),
                requested.eventStateRoot() == null ? null : requested.eventStateRoot().toRealPath(),
                requested.stockGameRoot() == null ? null : requested.stockGameRoot().toRealPath(),
                requested.evidenceGrantsManifest() == null ? null : requested.evidenceGrantsManifest().toAbsolutePath().normalize(), requested.offlinePublishing());
        ServiceInputs build = ServiceInputs.read(config.buildReceipt(), captureScopePath != null);
        String machine = WindowsJobProcess.currentMachineId();
        ProjectionCaptureScope.Bound captureScope = captureScopePath == null ? null : ProjectionCaptureScope.read(captureScopePath, machine);
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
        List<ControlBuild.FileRef> mapSources = captureScope == null ? mapSourcePins(build) : List.of();
        ControlBuild.FileRef manifestRef = captureScope == null ? publishProgramManifest(logs.resolve("program-manifest.json"), new ProgramManifest(
                "xar.java-map-complete-fastjar-deployment/v1", machine, Instant.now().toString(),
                deployment.toString(), List.copyOf(build.completeDeployment()), mapSources,
                buildRef, ControlBuild.FileRef.measure(config.javaExecutable()), true, true)) : null;
        Map<String, String> environment = new TreeMap<>(String.CASE_INSENSITIVE_ORDER);
        environment.putAll(System.getenv());
        environment.put("TEMP", scratch.toString());
        environment.put("TMP", scratch.toString());
        environment.remove("JAVA_TOOL_OPTIONS");
        environment.remove("JDK_JAVA_OPTIONS");
        List<String> arguments = new ArrayList<>(List.of("-Xms32m", "-Xmx256m", "-XX:MaxMetaspaceSize=96m",
                "-XX:ReservedCodeCacheSize=48m", "-XX:MaxDirectMemorySize=32m", "-Xss512k",
                "-Djava.io.tmpdir=" + scratch, "-Djna.tmpdir=" + scratch,
                "-Dquarkus.http.port=" + config.port(), "-Dquarkus.http.host=127.0.0.1",
                "-Dxar.projection.machine-id=" + machine));
        if (config.eventStateRoot() != null) {
            arguments.add("-Dxar.projection.event-source.state-root=" + config.eventStateRoot());
            arguments.add("-Dxar.projection.event-source.stock-game-root=" + config.stockGameRoot());
        }
        if (config.evidenceGrantsManifest() != null) {
            arguments.add("-Dxar.projection.event-source.evidence-grants=" + config.evidenceGrantsManifest());
        }
        arguments.add("-Dxar.projection.offline.enabled=" + (config.offlinePublishing() != null));
        if (captureScope != null) arguments.add("-Dxar.projection.capture-only=true");
        if (config.offlinePublishing() != null) {
            if (config.offlinePublishing().incidentRoot() != null) {
                arguments.add("-Dxar.projection.offline.incident-root=" + config.offlinePublishing().incidentRoot());
                arguments.add("-Dxar.projection.offline.knowledge-root=" + config.offlinePublishing().knowledgeRoot());
            }
        }
        arguments.add("-jar"); arguments.add(deployment.resolve("quarkus-run.jar").toString());
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
            ControlBuild.FileRef evidenceRef = null;
            if (captureScope == null) {
                evidenceRef = publish(logs.resolve("service-running.json"), new RunningReceipt(
                        "xar.java-map-service-running/v1", machine, Instant.now().toString(), "ACTUAL_RUNNING",
                        PRODUCER, PRODUCER_VERSION, "http://127.0.0.1:" + config.port() + COMPOSE_PATH,
                        manifestRef, mapSources, ProcessWire.from(identity)));
                publish(logs.resolve("service-started.json"), new StartedReceipt(
                        "xar.java-map-service-owner-started/v1", machine, Instant.now().toString(),
                        config.leaseDeadline().toString(), evidenceRef, manifestRef, ProcessWire.from(identity),
                        NativeTcpListener.owners(config.port()), readiness, producer, MEMORY_LIMIT, 0));
            }
            ProjectionAdmission projection = qualifyProjection
                    ? qualifyProjection(config, child, build, manifestRef, logs, machine, captureScope) : null;
            buildRef.verify(); build.javaExecutableRef().verify();
            Session session = new Session(config, child, evidenceRef, manifestRef,
                    build.sourcePins(), build.completeDeployment(), machine, buildRef, build.javaExecutableRef(), projection, build, captureScope);
            session.requireCurrent();
            return session;
        } catch (IOException | RuntimeException | Error failure) {
            try { closeFailedStartup(config, child, machine); }
            catch (IOException | RuntimeException | Error cleanup) { failure.addSuppressed(cleanup); }
            finally {
                try { child.close(); } catch (RuntimeException | Error cleanup) { failure.addSuppressed(cleanup); }
            }
            throw failure;
        }
    }

    static void closeFailedStartup(Config config, WindowsJobProcess child, String machine) throws IOException {
        try {
            if (child.isRunning()) child.terminate(75);
            WindowsJobProcess.CommandResult result = child.await(Duration.ofSeconds(10), Instant.now().plusSeconds(15), () -> {});
            publish(config.workRoot().resolve("logs/service-start-failed-closed.json"), new ClosedReceipt(
                    "xar.java-map-service-owner-closed/v1", machine, Instant.now().toString(), "START_FAILED_CLOSED",
                    ProcessWire.from(child.identity()), result, result.accounting().activeProcesses(),
                    result.accounting().peakJobMemoryBytes(), 0));
            if (result.accounting().activeProcesses() != 0) throw new IOException("Failed service startup retained a live process tree");
        } catch (InterruptedException error) {
            Thread.currentThread().interrupt(); throw new IOException("Failed service startup cleanup interrupted", error);
        }
    }


    /** Complete contracts and host source scope for the legacy map route; full graph remains in build/projection proofs. */
    private static List<ControlBuild.FileRef> mapSourcePins(ServiceInputs build) throws IOException {
        Path root = Path.of(build.sourceRoot()).toAbsolutePath().normalize();
        List<ControlBuild.FileRef> result = new ArrayList<>();
        for (ControlBuild.FileRef pin : build.sourcePins()) {
            String relative = root.relativize(Path.of(pin.path()).toAbsolutePath().normalize()).toString().replace('\\', '/');
            if (relative.equals("pom.xml") || relative.startsWith(".mvn/")
                    || relative.startsWith("contracts/") || relative.startsWith("local-service/")) result.add(pin);
        }
        for (String required : List.of("contracts/pom.xml", "local-service/pom.xml",
                "contracts/src/main/java/org/xar/ck3/control/contracts/CampaignMapAdmissionComposer.java",
                "local-service/src/main/java/org/xar/ck3/control/service/CampaignMapAdmissionResource.java")) {
            if (result.stream().noneMatch(ref -> root.relativize(Path.of(ref.path())).toString().replace('\\', '/').equals(required))) {
                throw new IOException("Legacy map proof lacks actual contracts/host source scope: " + required);
            }
        }
        return List.copyOf(result);
    }

    private static ProjectionAdmission qualifyProjection(Config config, WindowsJobProcess child, ServiceInputs build,
            ControlBuild.FileRef mapProgramRef, Path logs, String machine, ProjectionCaptureScope.Bound captureScope) throws IOException {
        WindowsJobProcess.ProcessIdentity before = WindowsJobProcess.exactProcess(child.identity().pid());
        if (!before.equals(child.identity())) throw new IOException("Original Java process generation changed before projection observation");
        ProjectionDeploymentProof.Identity observed = getProjection(config.port(), "/v1/projections/identity", ProjectionDeploymentProof.Identity.class);
        ProjectionDeploymentProof.CatalogInventory catalogs = getProjection(config.port(), "/v1/projections/catalogs", ProjectionDeploymentProof.CatalogInventory.class);
        Path contextPath = logs.resolve("projection-context-response.json");
        HostContext hostContext = get(config.port(), "/v1/projections/context", HostContext.class,
                ProjectionDeploymentProof.MAX_OBSERVATION_BYTES, true, contextPath);
        requireContext(config, machine, hostContext);
        ObservedHostContext contextProof = new ObservedHostContext(hostContext, ControlBuild.FileRef.measure(contextPath));
        ProjectionDeploymentProof.Attestation proof = build.attest(observed, catalogs, machine);
        if (captureScope != null) { captureScope.verify(); captureScope.requireCatalog(proof); }
        ProjectionRuntimeSources.ConfiguredManifest runtimeSources = null;
        if (config.evidenceGrantsManifest() != null) {
            Path grantsPath = logs.resolve("projection-initial-evidence-grants-response.json");
            ProjectionRuntimeSources.GrantsSnapshot grants = get(config.port(), "/v1/projections/evidence-grants",
                    ProjectionRuntimeSources.GrantsSnapshot.class, ProjectionRuntimeSources.MAX_RESPONSE_BYTES, true, grantsPath);
            ProjectionRuntimeSources.requireCurrentSnapshot(grants, machine, build.completeDeployment());
            runtimeSources = new ProjectionRuntimeSources.ConfiguredManifest(config.evidenceGrantsManifest().toString(),
                    ControlBuild.FileRef.measure(grantsPath), grants.grants().size());
        }
        ProjectionOfflineContext.Observed offlineContext = null;
        if (config.offlinePublishing() != null) {
            Path offlinePath = logs.resolve("offline-event-analysis-context-response.json");
            ProjectionOfflineContext.Context actual = getOfflineContext(config.port(), offlinePath);
            ProjectionOfflineContext.requireExpected(config, machine, actual);
            offlineContext = new ProjectionOfflineContext.Observed(actual, ControlBuild.FileRef.measure(offlinePath));
        }
        for (ControlBuild.FileRef sourcePin : build.sourcePins()) sourcePin.verify();
        for (ControlBuild.FileRef artifact : build.completeDeployment()) artifact.verify();
        build.javaExecutableRef().verify();
        WindowsJobProcess.ProcessIdentity after = WindowsJobProcess.exactProcess(before.pid());
        if (!before.equals(after) || !NativeTcpListener.owners(config.port()).equals(List.of(
                new NativeTcpListener.ListenerOwner(after.pid(), "127.0.0.1", config.port())))) {
            throw new IOException("Projection observation/source measurement lost original kernel/listener generation");
        }
        if (mapProgramRef != null) mapProgramRef.verify();
        ControlBuild.FileRef program = publishBounded(logs.resolve("projection-program-manifest.json"),
                new ProjectionProgramManifest("xar.java-projection-complete-fastjar-deployment/v2", machine, Instant.now().toString(),
                        build.deploymentRoot(), build.completeDeployment(), build.sourcePins(), ControlBuild.FileRef.measure(config.buildReceipt()),
                        build.javaExecutableRef(), true, true, proof, contextProof, runtimeSources, offlineContext, build.qualification(), captureScope), MAX_PROGRAM_MANIFEST_BYTES);
        ControlBuild.FileRef evidence = publishBounded(logs.resolve("projection-service-running.json"), new ProjectionRunningReceipt(
                "xar.java-projection-service-running/v1", machine, Instant.now().toString(), "ACTUAL_RUNNING",
                ProjectionDeploymentProof.PRODUCER, ProjectionDeploymentProof.VERSION,
                "http://127.0.0.1:" + config.port() + "/v1/projections/call",
                program, build.sourcePins(), ProcessWire.from(after), contextProof), MAX_PROJECTION_RUNNING_BYTES);
        ProjectionAdmission admission = new ProjectionAdmission(evidence, program, proof, ProcessWire.from(before), ProcessWire.from(after), contextProof);
        publishBounded(logs.resolve("projection-service-started.json"), new ProjectionStartedReceipt(
                "xar.java-projection-service-owner-started/v1", machine, Instant.now().toString(), config.leaseDeadline().toString(),
                admission, NativeTcpListener.owners(config.port()), expectedStatus(), MEMORY_LIMIT, 0), MAX_PROJECTION_RUNNING_BYTES);
        return admission;
    }

    static void requireContext(Config config, String machine, HostContext context) throws IOException {
        if (!machine.equals(context.machineId())) throw new IOException("Actual host context machine differs from original owner");
        EventSourceRoots expected = config.eventStateRoot() == null ? null
                : new EventSourceRoots(config.eventStateRoot().toString(), config.stockGameRoot().toString());
        if (expected == null ? context.eventSources() != null : context.eventSources() == null
                || !Path.of(expected.stateRoot()).normalize().equals(Path.of(context.eventSources().stateRoot()).normalize())
                || !Path.of(expected.stockGameRoot()).normalize().equals(Path.of(context.eventSources().stockGameRoot()).normalize())) {
            throw new IOException("Host event source context drifted from explicit paired launch roots");
        }
    }

    static <T> ControlBuild.FileRef publishProjectionRunning(Path path, T receipt) throws IOException {
        return publishBounded(path, receipt, MAX_PROJECTION_RUNNING_BYTES);
    }

    private static <T> T getProjection(int port, String endpoint, Class<T> type) throws IOException {
        return get(port, endpoint, type, ProjectionDeploymentProof.MAX_OBSERVATION_BYTES, true);
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
        return get(port, endpoint, type, 16384, false);
    }

    private static <T> T get(int port, String endpoint, Class<T> type, int maximumBytes, boolean projection) throws IOException {
        return get(port, endpoint, type, maximumBytes, projection, null);
    }

    private record HeaderContract(String producer, String version, String revision) {}

    private static ProjectionOfflineContext.Context getOfflineContext(int port, Path responsePath) throws IOException {
        return get(port, "/v1/offline-event-analysis/context", ProjectionOfflineContext.Context.class,
                ProjectionDeploymentProof.MAX_OBSERVATION_BYTES,
                new HeaderContract(ProjectionOfflineContext.PRODUCER, "0.1.0", ProjectionOfflineContext.CONTRACT), responsePath);
    }

    private static <T> T get(int port, String endpoint, Class<T> type, int maximumBytes, boolean projection, Path responsePath) throws IOException {
        return get(port, endpoint, type, maximumBytes, projection
                ? new HeaderContract(ProjectionDeploymentProof.PRODUCER, ProjectionDeploymentProof.VERSION, ProjectionDeploymentProof.CALL_SCHEMA)
                : null, responsePath);
    }

    private static <T> T get(int port, String endpoint, Class<T> type, int maximumBytes, HeaderContract expectedHeaders, Path responsePath) throws IOException {
        var connection = URI.create("http://127.0.0.1:" + port + endpoint).toURL().openConnection(Proxy.NO_PROXY);
        if (!(connection instanceof HttpURLConnection http)) {
            throw new IOException("original loopback HTTP connection required");
        }
        http.setConnectTimeout(2000);
        http.setReadTimeout(2000);
        try {
            http.setInstanceFollowRedirects(false);
            http.setRequestMethod("GET");
            http.setRequestProperty("Connection", "close");
            int status = http.getResponseCode();
            if (status != 200) { throw new IOException("Java host observation HTTP " + status + " at " + endpoint); }
            if (expectedHeaders != null && (!expectedHeaders.producer().equals(singleHeader(http, "X-Xar-Producer"))
                    || !expectedHeaders.version().equals(singleHeader(http, "X-Xar-Producer-Version"))
                    || !expectedHeaders.revision().equals(singleHeader(http, "X-Xar-Contract-Revision"))
                    || !projectionContentType(singleHeader(http, "Content-Type")))) {
                throw new IOException("Exact projection JSON producer/version/contract response headers required");
            }
            byte[] raw;
            try (InputStream stream = http.getInputStream()) { raw = stream.readNBytes(maximumBytes + 1); }
            if (raw.length == 0 || raw.length > maximumBytes) { throw new IOException("bounded original Java status response required"); }
            T value = ControlBuild.strictMapper().readValue(raw, type);
            if (responsePath != null) Files.write(responsePath, raw, StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE);
            return value;
        } finally {
            http.disconnect();
        }
    }


    private static boolean projectionContentType(String contentType) {
        String[] parts = contentType.toLowerCase(java.util.Locale.ROOT).split(";", -1);
        if (parts.length < 1 || parts.length > 2 || !parts[0].strip().equals("application/json")) return false;
        return parts.length == 1 || parts[1].strip().equals("charset=utf-8") || parts[1].strip().equals("charset=\"utf-8\"");
    }

    private static String singleHeader(HttpURLConnection http, String name) throws IOException {
        List<String> values = http.getHeaderFields().entrySet().stream()
                .filter(entry -> entry.getKey() != null && entry.getKey().equalsIgnoreCase(name))
                .flatMap(entry -> entry.getValue().stream()).toList();
        if (values.size() != 1) throw new IOException("Exactly one projection header required: " + name);
        return values.getFirst();
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
        try {
            long[] entries = {0};
            long bytes = ControlBuild.mutableInventoryBytes(root, path -> {
                if (++entries[0] > 10000) throw new IOException("bounded original service metadata tree required");
            });
            if (bytes > OUTPUT_BUDGET) throw new IOException("service output budget exhausted");
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
