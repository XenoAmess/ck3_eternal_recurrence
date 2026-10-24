package org.xar.ck3.control.build;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.annotation.JsonNaming;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.net.HttpURLConnection;
import java.net.Proxy;
import java.net.URI;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Set;

/** Root-owned SOFTWARE fixture publication in the existing service generation. */
public final class RootSoftwareFixtureHandoff {
    public static final String PROPERTY = "xar.root.software-fixture.pending";
    public static final String SCOPE = "SOFTWARE_FIXTURE_ONLY";
    public static final String CONTEXT_PATH = "/v1/g2-research/context";
    private static final int MAX_METADATA = 1_048_576;
    private static final int MAX_FIXTURE = 8_388_608;
    private static final Set<String> SOURCE_NAMES = Set.of("G2SoftwareFixtureSourceProvider.java",
            "RootSoftwareFixtureLifecycle.java", "DeferredRootSoftwareFixtureProvider.java",
            "G2CallContextHost.java", "G2CallContextWire.java");
    private RootSoftwareFixtureHandoff() { }

    @JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy.class)
    public record Request(List<ControlBuild.FileRef> originalFixtureRefs,
            List<ControlBuild.FileRef> originalRequestRefs,
            ControlBuild.FileRef probeRequestRef, ControlBuild.FileRef probePayloadRef) {
        public Request {
            originalFixtureRefs = List.copyOf(originalFixtureRefs);
            originalRequestRefs = List.copyOf(originalRequestRefs);
            Objects.requireNonNull(probeRequestRef); Objects.requireNonNull(probePayloadRef);
            if (originalFixtureRefs.isEmpty() || originalFixtureRefs.size() > 4096
                    || originalRequestRefs.isEmpty() || originalRequestRefs.size() > 8
                    || originalFixtureRefs.stream().distinct().count() != originalFixtureRefs.size()
                    || originalRequestRefs.stream().distinct().count() != originalRequestRefs.size()
                    || !originalFixtureRefs.containsAll(originalRequestRefs)
                    || !originalRequestRefs.contains(probeRequestRef)) {
                throw new IllegalArgumentException("exact original fixtures and a contained original probe required");
            }
        }
    }

    @JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy.class)
    public record Pending(String schema, String scope, String machineId, String leaseDeadlineUtc,
            MapAdmissionServiceOwner.ProcessWire ownerProcess, ControlBuild.FileRef buildReceiptRef,
            ControlBuild.FileRef javaExecutableRef, List<ControlBuild.FileRef> sourceRefs,
            Request request, String workRoot) {
        public Pending {
            if (!"xar.root-software-fixture-pending/v1".equals(schema) || !SCOPE.equals(scope)
                    || machineId == null || machineId.isBlank()) throw new IllegalArgumentException("Root software descriptor required");
            Instant.parse(leaseDeadlineUtc); Objects.requireNonNull(ownerProcess);
            Objects.requireNonNull(buildReceiptRef); Objects.requireNonNull(javaExecutableRef);
            sourceRefs = List.copyOf(sourceRefs); Objects.requireNonNull(request);
            if (sourceRefs.size() != SOURCE_NAMES.size() || !Path.of(workRoot).isAbsolute()
                    || !Path.of(workRoot).normalize().toString().equals(Path.of(workRoot).toString())) {
                throw new IllegalArgumentException("fixed Root work root and complete provider source scope required");
            }
        }
    }

    @JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy.class)
    public record Activation(String schema, String scope, String machineId,
            MapAdmissionServiceOwner.ProcessWire ownerProcess,
            MapAdmissionServiceOwner.ProcessWire hostProcess,
            ControlBuild.FileRef programRef, ControlBuild.FileRef serviceEvidenceRef) {
        public Activation {
            if (!"xar.root-software-fixture-activation/v1".equals(schema) || !SCOPE.equals(scope)) {
                throw new IllegalArgumentException("Root software activation required");
            }
            Objects.requireNonNull(machineId); Objects.requireNonNull(ownerProcess);
            Objects.requireNonNull(hostProcess); Objects.requireNonNull(programRef); Objects.requireNonNull(serviceEvidenceRef);
        }
    }
    public record Prepared(Pending pending, ControlBuild.FileRef pendingRef) {
        public Prepared { Objects.requireNonNull(pending); Objects.requireNonNull(pendingRef); }
    }
    public record Admission(ControlBuild.FileRef originRef, ControlBuild.FileRef programRef, ControlBuild.FileRef buildReceiptRef,
            ControlBuild.FileRef serviceEvidenceRef, ControlBuild.FileRef probeRequestRef,
            ControlBuild.FileRef probePayloadRef, ControlBuild.FileRef actualProbeResponseRef,
            MapAdmissionServiceOwner.ProcessWire hostProcess, List<ControlBuild.FileRef> originalFixtureRefs,
            ControlBuild.FileRef pendingRef, ControlBuild.FileRef activationRef) {
        public Admission {
            Objects.requireNonNull(originRef); Objects.requireNonNull(programRef); Objects.requireNonNull(buildReceiptRef); Objects.requireNonNull(serviceEvidenceRef);
            Objects.requireNonNull(probeRequestRef); Objects.requireNonNull(probePayloadRef);
            Objects.requireNonNull(actualProbeResponseRef); Objects.requireNonNull(hostProcess);
            Objects.requireNonNull(pendingRef); Objects.requireNonNull(activationRef);
            originalFixtureRefs = List.copyOf(originalFixtureRefs);
        }
        public void verify() throws IOException {
            for (var ref : List.of(originRef, programRef, buildReceiptRef, serviceEvidenceRef, probeRequestRef,
                    probePayloadRef, actualProbeResponseRef, pendingRef, activationRef)) ref.verify();
            for (var ref : originalFixtureRefs) ref.verify();
        }
    }

    public static Path publication(Pending pending, String name) {
        if (!Set.of("projection-program-manifest.json", "projection-service-running.json",
                "software-fixture-activation.json", "software-fixture-origin.json",
                "software-fixture-probe-response.json").contains(name)) {
            throw new IllegalArgumentException("fixed owner publication name required");
        }
        return Path.of(pending.workRoot()).resolve("logs").resolve(name);
    }
    static Prepared prepare(Request request, Path workRoot, Instant deadline, String machine,
            ControlBuild.FileRef buildRef, ControlBuild.FileRef javaRef,
            List<ControlBuild.FileRef> sourcePins) throws IOException {
        List<ControlBuild.FileRef> sources = new ArrayList<>();
        for (String name : SOURCE_NAMES) {
            var matches = sourcePins.stream().filter(ref -> Path.of(ref.path()).getFileName().toString().equals(name)).toList();
            if (matches.size() != 1) throw new IOException("qualified deployment lacks one actual software provider source: " + name);
            sources.add(matches.getFirst());
        }
        Pending pending = new Pending("xar.root-software-fixture-pending/v1", SCOPE, machine, deadline.toString(),
                MapAdmissionServiceOwner.ProcessWire.from(WindowsJobProcess.exactProcess(ProcessHandle.current().pid())),
                buildRef, javaRef, sources, request, workRoot.toAbsolutePath().normalize().toString());
        verifyInputs(pending);
        for (String name : List.of("projection-program-manifest.json", "projection-service-running.json",
                "software-fixture-activation.json", "software-fixture-origin.json", "software-fixture-probe-response.json")) {
            if (Files.exists(publication(pending, name), LinkOption.NOFOLLOW_LINKS)) throw new IOException("software publication must be absent before the original host starts");
        }
        return new Prepared(pending, write(workRoot.resolve("logs/software-fixture-pending.json"), pending));
    }
    public static Pending readPending(ControlBuild.FileRef ref) throws IOException { return read(ref, Pending.class); }
    public static Activation readActivation(ControlBuild.FileRef ref) throws IOException { return read(ref, Activation.class); }
    public static void verifyInputs(Pending pending) throws IOException {
        if (!pending.sourceRefs().stream().map(ref -> Path.of(ref.path()).getFileName().toString()).collect(java.util.stream.Collectors.toSet()).equals(SOURCE_NAMES)) {
            throw new IOException("the exact selected software provider source scope is required");
        }
        if (!pending.machineId().equals(WindowsJobProcess.currentMachineId())
                || !Instant.now().isBefore(Instant.parse(pending.leaseDeadlineUtc()))
                || !pending.ownerProcess().equals(MapAdmissionServiceOwner.ProcessWire.from(
                        WindowsJobProcess.exactProcess(pending.ownerProcess().pid())))) {
            throw new IOException("original Root owner/machine/finite software lifetime unavailable");
        }
        pending.buildReceiptRef().verify(); pending.javaExecutableRef().verify();
        for (var ref : pending.sourceRefs()) ref.verify();
        for (var ref : pending.request().originalFixtureRefs()) bounded(ref, MAX_FIXTURE);
        bounded(pending.request().probePayloadRef(), MAX_FIXTURE);
    }
    public static void verifyActivation(Pending pending, Activation activation) throws IOException {
        verifyInputs(pending);
        if (!pending.machineId().equals(activation.machineId()) || !pending.ownerProcess().equals(activation.ownerProcess())
                || !Path.of(activation.programRef().path()).equals(publication(pending, "projection-program-manifest.json"))
                || !Path.of(activation.serviceEvidenceRef().path()).equals(publication(pending, "projection-service-running.json"))) {
            throw new IOException("actual projection publication differs from the trusted startup descriptor");
        }
        bounded(activation.programRef(), MAX_METADATA); bounded(activation.serviceEvidenceRef(), MAX_METADATA);
        var program = MapAdmissionServiceOwner.readProjectionProgram(readBytes(activation.programRef(), MAX_METADATA));
        List<ControlBuild.FileRef> sources;
        ControlBuild.FileRef build;
        ControlBuild.FileRef java;
        ProjectionCaptureScope.Qualification qualification;
        String programMachine;
        if (program instanceof MapAdmissionServiceOwner.ProjectionProgramManifestV3 full) {
            sources = full.sourceRefs(); build = full.buildReceiptRef(); java = full.javaExecutableRef(); qualification = full.qualification();
            programMachine = full.machineId();
        } else if (program instanceof MapAdmissionServiceOwner.ProjectionProgramManifest full) {
            sources = full.sourceRefs(); build = full.buildReceiptRef(); java = full.javaExecutableRef(); qualification = full.qualification();
            programMachine = full.machineId();
        } else throw new IOException("actual qualified projection program required");
        if (qualification != ProjectionCaptureScope.Qualification.FULL_SOFTWARE || !pending.machineId().equals(programMachine) || !build.equals(pending.buildReceiptRef())
                || !java.equals(pending.javaExecutableRef()) || !sources.containsAll(pending.sourceRefs())) {
            throw new IOException("software fixture cannot substitute a capture/map/foreign-source program");
        }
        var evidence = read(activation.serviceEvidenceRef(), MapAdmissionServiceOwner.ProjectionRunningReceipt.class);
        if (!"ACTUAL_RUNNING".equals(evidence.status()) || !pending.machineId().equals(evidence.machineId())
                || !activation.programRef().equals(evidence.programRef()) || !activation.hostProcess().equals(evidence.process())
                || !activation.hostProcess().equals(MapAdmissionServiceOwner.ProcessWire.from(
                        WindowsJobProcess.exactProcess(activation.hostProcess().pid())))) {
            throw new IOException("same actual host PID/birth and qualified program required");
        }
    }

    static Admission admit(Prepared prepared, MapAdmissionServiceOwner.ProjectionAdmission projection, int port) throws IOException {
        Pending pending = prepared.pending(); prepared.pendingRef().verify();
        Activation activation = new Activation("xar.root-software-fixture-activation/v1", SCOPE, pending.machineId(),
                pending.ownerProcess(), projection.processAfter(), projection.programRef(), projection.serviceEvidenceRef());
        verifyActivation(pending, activation);
        ControlBuild.FileRef activationRef = write(publication(pending, "software-fixture-activation.json"), activation);
        JsonNode original = ControlBuild.strictMapper().readTree(readBytes(pending.request().probeRequestRef(), MAX_FIXTURE));
        JsonNode milestone = original.get("milestone");
        if (milestone == null || !milestone.isTextual() || !milestone.textValue().matches("G2-M[0-7]")) throw new IOException("original G2 producer milestone required");
        byte[] payload = readBytes(pending.request().probePayloadRef(), MAX_FIXTURE);
        ByteArrayOutputStream body = new ByteArrayOutputStream();
        body.write("{\"milestone\":".getBytes(StandardCharsets.UTF_8));
        body.write(ControlBuild.strictMapper().writeValueAsBytes(milestone));
        body.write(",\"payload\":".getBytes(StandardCharsets.UTF_8)); body.write(payload); body.write('}');
        HttpURLConnection connection = (HttpURLConnection) URI.create("http://127.0.0.1:" + port + CONTEXT_PATH).toURL().openConnection(Proxy.NO_PROXY);
        byte[] response;
        int status;
        try {
            connection.setInstanceFollowRedirects(false); connection.setConnectTimeout(5000); connection.setReadTimeout(10000);
            connection.setRequestMethod("POST"); connection.setDoOutput(true); connection.setRequestProperty("Content-Type", "application/json");
            try (var output = connection.getOutputStream()) { output.write(body.toByteArray()); }
            status = connection.getResponseCode();
            try (var input = status == 200 ? connection.getInputStream() : connection.getErrorStream()) {
                response = input == null ? new byte[0] : input.readNBytes(65_537);
            }
            if (response.length > 65_536) throw new IOException("software context response exceeds its role budget");
            Files.write(publication(pending, "software-fixture-probe-response.json"), response, StandardOpenOption.CREATE_NEW);
            if (status != 200 || connection.getContentType() == null
                    || !connection.getContentType().toLowerCase(java.util.Locale.ROOT).split(";", 2)[0].strip().equals("application/json")
                    || !"java-quarkus-g2-call-context/v1".equals(connection.getHeaderField("X-Xar-Producer"))
                    || !"0.1.0".equals(connection.getHeaderField("X-Xar-Producer-Version"))
                    || !"xar.g2-call-context/v1".equals(connection.getHeaderField("X-Xar-Contract-Revision"))) {
                throw new IOException("original host software context probe unavailable or unidentified");
            }
        } finally { connection.disconnect(); }
        ContextResponse observed = ControlBuild.strictMapper().readValue(response, ContextResponse.class);
        ControlBuild.FileRef origin = ControlBuild.FileRef.measure(publication(pending, "software-fixture-origin.json"));
        if (!"xar.g2-call-context/v1".equals(observed.schema()) || !pending.machineId().equals(observed.source().machineId())
                || !origin.equals(observed.source().sourceRef())
                || !("SOFTWARE_FIXTURE@sha256:" + projection.programRef().sha256()).equals(observed.source().exactBuild())
                || !pending.request().probePayloadRef().sha256().equals(observed.payloadSha256())
                || observed.requestId() == null || !observed.requestId().startsWith("software:")) {
            throw new IOException("actual software context did not bind the original payload and same qualified program");
        }
        OriginWire written = read(origin, OriginWire.class);
        Set<String> declaredMilestones = new java.util.TreeSet<>();
        for (var ref : pending.request().originalRequestRefs()) {
            JsonNode value = ControlBuild.strictMapper().readTree(readBytes(ref, MAX_FIXTURE)).get("milestone");
            if (value == null || !value.isTextual() || !value.textValue().matches("G2-M[0-7]")) throw new IOException("original pure request milestone required");
            declaredMilestones.add(value.textValue());
        }
        if (!"xar.g2-software-fixture-origin/v1".equals(written.schema()) || !SCOPE.equals(written.scope())
                || !pending.machineId().equals(written.machineId()) || !projection.programRef().equals(written.programRef())
                || !pending.sourceRefs().equals(written.sourceRefs())
                || !pending.request().originalFixtureRefs().equals(written.originalFixtureRefs())
                || !pending.request().probeRequestRef().equals(written.probeRequestRef())
                || !pending.request().probePayloadRef().equals(written.probePayloadRef())
                || !milestone.textValue().equals(written.probeMilestone())
                || written.milestones().size() != declaredMilestones.size()
                || !declaredMilestones.equals(new java.util.TreeSet<>(written.milestones()))) {
            throw new IOException("actual origin differs from the original source-qualified software request");
        }
        verifyActivation(pending, activation); prepared.pendingRef().verify(); activationRef.verify();
        return new Admission(origin, projection.programRef(), pending.buildReceiptRef(), projection.serviceEvidenceRef(), pending.request().probeRequestRef(),
                pending.request().probePayloadRef(), ControlBuild.FileRef.measure(publication(pending, "software-fixture-probe-response.json")),
                activation.hostProcess(), pending.request().originalFixtureRefs(), prepared.pendingRef(), activationRef);
    }
    @JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy.class)
    private record ContextSource(String machineId, String observedAtUtc, String exactBuild, ControlBuild.FileRef sourceRef) { }
    @JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy.class)
    private record ContextResponse(String schema, ContextSource source, String requestId, String payloadSha256) { }
    @JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy.class)
    private record OriginWire(String schema, String scope, String machineId, String observedAtUtc,
            ControlBuild.FileRef programRef, List<ControlBuild.FileRef> sourceRefs,
            List<ControlBuild.FileRef> originalFixtureRefs, List<String> milestones,
            ControlBuild.FileRef probeRequestRef, ControlBuild.FileRef probePayloadRef, String probeMilestone) { }
    private static void bounded(ControlBuild.FileRef ref, int maximum) throws IOException {
        if (ref.bytes() < 1 || ref.bytes() > maximum) throw new IOException("bounded exact software input required");
        ref.verify();
    }
    private static byte[] readBytes(ControlBuild.FileRef ref, int maximum) throws IOException {
        bounded(ref, maximum);
        byte[] bytes;
        try (var input = Files.newInputStream(Path.of(ref.path()))) { bytes = input.readNBytes(maximum + 1); }
        if (bytes.length > maximum || bytes.length != ref.bytes()) throw new IOException("software input changed its declared extent");
        ref.verify(); return bytes;
    }
    private static <T> T read(ControlBuild.FileRef ref, Class<T> type) throws IOException {
        return ControlBuild.strictMapper().readValue(readBytes(ref, MAX_METADATA), type);
    }
    private static <T> ControlBuild.FileRef write(Path path, T value) throws IOException {
        byte[] bytes = ControlBuild.strictMapper().writeValueAsBytes(value);
        if (bytes.length == 0 || bytes.length > MAX_METADATA) throw new IOException("bounded software publication required");
        Files.write(path, bytes, StandardOpenOption.CREATE_NEW); return ControlBuild.FileRef.measure(path);
    }
}
