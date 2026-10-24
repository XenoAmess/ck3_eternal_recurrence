package org.xar.ck3.control.build;

import java.io.IOException;
import java.net.HttpURLConnection;
import java.net.Proxy;
import java.net.URI;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Instant;
import java.util.List;
import java.util.Objects;
import java.util.Set;

/** The existing Owner, limited to an explicitly tested software map vertical. */
public final class MapVerticalSoftwareHost {
    public enum Purpose { MAP_VERTICAL_SOFTWARE_ONLY }
    private static final Set<String> REQUIRED = Set.of("CampaignMapAdmission.java", "CampaignMapAdmissionComposer.java",
            "CampaignMapComposeRequest.java", "CampaignMapProtocol.java", "StrictJson.java",
            "CampaignMapAdmissionResource.java", "MapAdmissionProjectionCatalog.java",
            "CampaignMapAdmissionComposerTest.java", "CampaignMapComposeRequestTest.java", "StrictJsonBudgetTest.java",
            "CampaignMapAdmissionResourceContractTest.java", "CampaignMapAdmissionHttpContractTest.java", "ProjectionHttpTest.java");
    private static final String PROJECTION_PATH = "/v1/projections/call";
    private MapVerticalSoftwareHost() { }

    public record Config(MapAdmissionServiceOwner.Config service, ControlBuild.FileRef scopeRef,
            List<ControlBuild.FileRef> selectedMapSources, List<ControlBuild.FileRef> consumerSources) {
        public Config {
            Objects.requireNonNull(service); Objects.requireNonNull(scopeRef);
            selectedMapSources = List.copyOf(selectedMapSources); consumerSources = List.copyOf(consumerSources);
            if (selectedMapSources.size() != REQUIRED.size() || consumerSources.size() != 13
                    || !selectedMapSources.stream().map(r -> Path.of(r.path()).getFileName().toString())
                        .collect(java.util.stream.Collectors.toSet()).equals(REQUIRED)
                    || consumerSources.stream().distinct().count() != consumerSources.size()
                    || service.eventStateRoot() != null || service.stockGameRoot() != null
                    || service.evidenceGrantsManifest() != null || service.offlinePublishing() != null || service.artifactInput() != null || service.softwareFixture() != null) {
                throw new IllegalArgumentException("complete selected pure map scope and original consumers required");
            }
        }
    }
    public record Program(String schema, Purpose qualification, boolean normalQualified, boolean nativeAuthority,
            String machineId, String observedAtUtc, String deploymentRoot, List<ControlBuild.FileRef> files,
            List<ControlBuild.FileRef> sourceRefs, List<ControlBuild.FileRef> consumerSourceRefs,
            ControlBuild.FileRef captureRef, ControlBuild.FileRef baseMapProgramRef,
            ControlBuild.FileRef javaExecutableRef, MapAdmissionServiceOwner.ProcessWire process) { }
    public record WireObservation(String endpoint, ControlBuild.FileRef requestRef,
            ControlBuild.FileRef responseRef, int status, String producer, String version, String revision) { }
    public record RegressionProof(String schema, Purpose qualification, String machineId, String observedAtUtc,
            ControlBuild.FileRef captureRef, ControlBuild.FileRef programRef, ControlBuild.FileRef runningRef,
            MapAdmissionServiceOwner.ProcessWire hostProcess, List<ControlBuild.FileRef> sourceRefs,
            List<ControlBuild.FileRef> consumerSourceRefs, WireObservation direct, WireObservation projection,
            MapAdmissionCi.OriginalMapConsumerGroup consumers, boolean normalQualified, int gameCalls) { }

    /** Instances can only be minted by this live Session after the real software regressions. */
    public static final class MapVerticalSoftwareResult {
        private final Session session;
        private final ControlBuild.FileRef proofRef;
        private MapVerticalSoftwareResult(Session session, ControlBuild.FileRef proofRef) {
            this.session = session; this.proofRef = proofRef;
        }
        public Purpose purpose() { return Purpose.MAP_VERTICAL_SOFTWARE_ONLY; }
        public ControlBuild.FileRef proofRef() { return proofRef; }
        public ControlBuild.FileRef captureRef() { return session.captureRef(); }
        public ControlBuild.FileRef programRef() { return session.programRef(); }
        public ControlBuild.FileRef runningRef() { return session.runningRef(); }
        public void verifyCurrent() throws IOException { session.requireCurrent(); session.verifyImmutableInputs(); proofRef.verify(); }
    }
    public static final class Exchange {
        private final Session session;
        private final WireObservation observation;
        private Exchange(Session session, WireObservation observation) { this.session = session; this.observation = observation; }
        public WireObservation observation() { return observation; }
        public byte[] responseBytes() throws IOException { observation.responseRef().verify(); return Files.readAllBytes(Path.of(observation.responseRef().path())); }
    }

    public static final class Session implements AutoCloseable {
        private final Config config;
        private final ControlBuild.FileRef capture;
        private final ControlBuild.CaptureBuildReceipt base;
        private final MapAdmissionServiceOwner.Session owner;
        private final ControlBuild.FileRef program;
        private final ControlBuild.FileRef running;
        private MapVerticalSoftwareResult result;
        private int exchanges;
        private boolean closed;
        private Session(Config config, ControlBuild.FileRef capture, ControlBuild.CaptureBuildReceipt base,
                MapAdmissionServiceOwner.Session owner, ControlBuild.FileRef program, ControlBuild.FileRef running) {
            this.config = config; this.capture = capture; this.base = base; this.owner = owner;
            this.program = program; this.running = running;
        }
        public Purpose purpose() { return Purpose.MAP_VERTICAL_SOFTWARE_ONLY; }
        public ControlBuild.FileRef captureRef() { return capture; }
        public ControlBuild.FileRef programRef() { return program; }
        public ControlBuild.FileRef runningRef() { return running; }
        public MapAdmissionServiceOwner.ProjectionAdmission projectionAdmission() { throw new IllegalStateException("MAP_ONLY_CAPTURE grants no full projection admission"); }
        public MapOnlyProjectionProof.Admission mapOnlyCaptureAdmission() { return owner.mapOnlyCaptureAdmission(); }
        public WindowsJobProcess.ProcessIdentity identity() { return owner.identity(); }
        MapAdmissionServiceOwner.Session owner() { return owner; }
        public void requireCurrent() {
            if (closed || !Instant.now().isBefore(config.service().leaseDeadline())) throw new IllegalStateException("finite map software Session is closed or expired");
            owner.requireCurrent();
        }
        public void verifyImmutableInputs() throws IOException {
            requireCurrent(); capture.verify(); config.scopeRef().verify(); program.verify(); running.verify();
            owner.verifyImmutableInputs();
            for (var ref : config.selectedMapSources()) ref.verify();
            for (var ref : config.consumerSources()) ref.verify();
            for (var ref : base.completeDeployment()) ref.verify();
            if (result != null) result.proofRef().verify();
        }
        public Exchange post(String endpoint, ControlBuild.FileRef request) throws IOException {
            requireCurrent(); verifyImmutableInputs();
            boolean direct = MapAdmissionServiceOwner.COMPOSE_PATH.equals(endpoint);
            if (!direct && !PROJECTION_PATH.equals(endpoint)) throw new IllegalArgumentException("only the original two pure map HTTP routes are available");
            if (request.bytes() < 1 || request.bytes() > (direct ? 65_536 : ProjectionDeploymentProof.MAX_ENVELOPE_BYTES)) {
                throw new IOException("map software request exceeds its original route budget");
            }
            request.verify();
            HttpURLConnection connection = (HttpURLConnection) URI.create("http://127.0.0.1:" + config.service().port() + endpoint).toURL().openConnection(Proxy.NO_PROXY);
            byte[] bytes; int status; String producer; String version; String revision;
            try {
                connection.setInstanceFollowRedirects(false); connection.setConnectTimeout(5000); connection.setReadTimeout(15000);
                connection.setRequestMethod("POST"); connection.setDoOutput(true); connection.setRequestProperty("Content-Type", "application/json");
                try (var output = connection.getOutputStream()) { output.write(Files.readAllBytes(Path.of(request.path()))); }
                status = connection.getResponseCode();
                try (var input = status == 200 ? connection.getInputStream() : connection.getErrorStream()) {
                    bytes = input == null ? new byte[0] : input.readNBytes(65_537);
                }
                producer = connection.getHeaderField("X-Xar-Producer"); version = connection.getHeaderField("X-Xar-Producer-Version"); revision = connection.getHeaderField("X-Xar-Contract-Revision");
                if (bytes.length > 65_536) throw new IOException("map software response exceeds finite evidence budget");
                Path path = config.service().workRoot().resolve("logs/map-software-exchange-" + (++exchanges) + ".json");
                Files.write(path, bytes, StandardOpenOption.CREATE_NEW);
                if (status != 200 || connection.getContentType() == null || !connection.getContentType().startsWith("application/json")
                        || !(direct ? MapAdmissionServiceOwner.PRODUCER : ProjectionDeploymentProof.PRODUCER).equals(producer)
                        || !(direct ? MapAdmissionServiceOwner.PRODUCER_VERSION : ProjectionDeploymentProof.VERSION).equals(version)
                        || !(direct ? "xar.java-campaign-map-compose-request/v1" : ProjectionDeploymentProof.CALL_SCHEMA).equals(revision)) {
                    throw new IOException("actual original map HTTP call failed its fixed producer contract");
                }
                request.verify(); verifyImmutableInputs();
                return new Exchange(this, new WireObservation(endpoint, request, ControlBuild.FileRef.measure(path), status, producer, version, revision));
            } finally { connection.disconnect(); }
        }
        public MapVerticalSoftwareResult qualify(MapAdmissionCi.Config consumersConfig,
                Exchange direct, Exchange projection) throws IOException {
            verifyImmutableInputs(); Objects.requireNonNull(consumersConfig);
            if (result != null || direct.session != this || projection.session != this
                    || !MapAdmissionServiceOwner.COMPOSE_PATH.equals(direct.observation.endpoint())
                    || !PROJECTION_PATH.equals(projection.observation.endpoint())) throw new IllegalArgumentException("one original direct and registered map exchange from this Session required once");
            MapAdmissionCi.OriginalMapConsumerGroup consumers;
            try (MapAdmissionCi.Session borrowed = MapAdmissionCi.borrowForMapVerticalSoftware(consumersConfig, this)) {
                consumers = MapAdmissionCi.runOriginalMapConsumerGroup(borrowed);
            }
            for (var command : List.of(consumers.staticCheck(), consumers.regression())) {
                if (!command.result().passed() || command.result().accounting().activeProcesses() != 0) throw new IOException("actual complete map consumers did not finish successfully");
                command.stdoutRef().verify(); command.stderrRef().verify();
            }
            String summary = Files.readString(Path.of(consumers.regression().stderrRef().path()));
            if (!summary.contains("\nRan 6 tests in ") || !summary.stripTrailing().endsWith("\nOK") || summary.contains("skipped=")) throw new IOException("all original six map consumers with zero skips required");
            ControlBuild.FileRef proof = publish(config.service().workRoot().resolve("logs/map-software-qualified.json"),
                    new RegressionProof("xar.map-vertical-software-qualified/v1", purpose(), base.machineId(), Instant.now().toString(),
                            capture, program, running, MapAdmissionServiceOwner.ProcessWire.from(identity()), config.selectedMapSources(),
                            config.consumerSources(), direct.observation, projection.observation, consumers, false, 0));
            result = new MapVerticalSoftwareResult(this, proof); result.verifyCurrent(); return result;
        }
        public MapVerticalSoftwareResult qualification() {
            requireCurrent(); if (result == null) throw new IllegalStateException("map software regression group has not qualified"); return result;
        }
        @Override public void close() throws IOException { if (!closed) { closed = true; owner.close(); } }
    }

    public static Session open(Config config) throws IOException {
        ControlBuild.FileRef capture = ControlBuild.FileRef.measure(config.service().buildReceipt());
        ControlBuild.CaptureBuildReceipt base = ControlBuild.verifiedCompletedCaptureReceipt(capture);
        if (!base.machineId().equals(WindowsJobProcess.currentMachineId())) throw new IOException("actual same-machine capture base required");
        var scope = ProjectionCaptureScope.read(Path.of(config.scopeRef().path()), base.machineId());
        if (!scope.scopeRef().equals(config.scopeRef()) || !scope.request().operations().equals(List.of("map-admission-compose"))) throw new IOException("explicit map-only original request scope required");
        Path source = Path.of(base.sourceRoot()), compiled = Path.of(base.compiledSourceRoot());
        for (var ref : config.selectedMapSources()) {
            ref.verify(); Path path = Path.of(ref.path());
            if (!path.startsWith(source) || !base.sourcePins().contains(ref)) throw new IOException("map source differs from actual captured original graph");
            Path expected = compiled.resolve(source.relativize(path));
            if (base.compiledSourcePins().stream().noneMatch(r -> Path.of(r.path()).equals(expected) && r.bytes() == ref.bytes() && r.sha256().equals(ref.sha256()))) throw new IOException("map source does not match the actually compiled graph");
        }
        for (var ref : config.consumerSources()) ref.verify();
        MapAdmissionServiceOwner.Session owner = MapAdmissionServiceOwner.startMapOnlyCapture(config.service(), Path.of(config.scopeRef().path()));
        try {
            var map = owner.mapOnlyCaptureAdmission(); Path logs = config.service().workRoot().resolve("logs");
            ControlBuild.FileRef program = publish(logs.resolve("map-software-program.json"), new Program(
                    "xar.java-map-vertical-software-program/v2", Purpose.MAP_VERTICAL_SOFTWARE_ONLY, false, false,
                    base.machineId(), Instant.now().toString(), base.deploymentRoot(), base.completeDeployment(), config.selectedMapSources(),
                    config.consumerSources(), capture, map.programRef(), base.javaExecutableRef(), MapAdmissionServiceOwner.ProcessWire.from(owner.identity())));
            ControlBuild.FileRef running = publish(logs.resolve("map-software-running.json"), new MapAdmissionServiceOwner.RunningReceipt(
                    "xar.java-map-service-running/v1", base.machineId(), Instant.now().toString(), "ACTUAL_RUNNING",
                    MapAdmissionServiceOwner.PRODUCER, MapAdmissionServiceOwner.PRODUCER_VERSION,
                    "http://127.0.0.1:" + config.service().port() + MapAdmissionServiceOwner.COMPOSE_PATH,
                    program, config.selectedMapSources(), MapAdmissionServiceOwner.ProcessWire.from(owner.identity())));
            Session result = new Session(config, capture, base, owner, program, running); result.verifyImmutableInputs(); return result;
        } catch (IOException | RuntimeException | Error failure) {
            try { owner.close(); } catch (RuntimeException | Error close) { failure.addSuppressed(close); } throw failure;
        }
    }
    private static <T> ControlBuild.FileRef publish(Path path, T value) throws IOException {
        byte[] raw = ControlBuild.strictMapper().writeValueAsBytes(value);
        if (raw.length < 1 || raw.length > 1_048_576) throw new IOException("bounded software map publication required");
        Files.write(path, raw, StandardOpenOption.CREATE_NEW); return ControlBuild.FileRef.measure(path);
    }
}
