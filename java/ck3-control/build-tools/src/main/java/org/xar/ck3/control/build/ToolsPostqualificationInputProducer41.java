package org.xar.ck3.control.build;

import com.fasterxml.jackson.databind.JsonNode;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Objects;
import org.xar.ck3.control.build.ControlBuild.FileRef;

/**
 * Prepare real metadata after a successful current Tools build. This does not run Own,
 * JUnit, Maven, SDK or Game, and never grants adoption or a postqualification proof.
 * Failed created metadata is retained; callers must use new authorized output paths.
 */
public final class ToolsPostqualificationInputProducer41 {
    public static final String REQUEST_SCHEMA = "xar.control-ci-tools-postqualification-production-request/v1";
    public static final String RESULT_SCHEMA = "xar.control-ci-tools-postqualification-prepared/v1";
    private static final String OWN_OWNER = "/root/tools_c15";
    private static final int MAX_REQUEST_BYTES = 1 << 20;
    private ToolsPostqualificationInputProducer41() { }

    /** Original references before the new bounded manifest exists. No future FileRef is accepted. */
    public record OwnSources(FileRef producerSourceRef, FileRef materializedMapRef,
            FileRef historicalCompletedReceiptRef, FileRef genuineHistoricalCaptureRef,
            FileRef originalQuotaLeaseRef, FileRef originalQuotaRejectionRef,
            FileRef originalQuotaSourceMapRef) {
        public OwnSources {
            for (var ref : List.of(producerSourceRef, materializedMapRef, historicalCompletedReceiptRef,
                    genuineHistoricalCaptureRef, originalQuotaLeaseRef, originalQuotaRejectionRef,
                    originalQuotaSourceMapRef)) positive(ref);
        }
        public List<FileRef> originals() {
            return List.of(producerSourceRef, materializedMapRef, historicalCompletedReceiptRef,
                    genuineHistoricalCaptureRef, originalQuotaLeaseRef, originalQuotaRejectionRef,
                    originalQuotaSourceMapRef);
        }
        public ToolsInputPostqualification.FullOwnInputs complete(FileRef actualManifest) {
            return new ToolsInputPostqualification.FullOwnInputs(producerSourceRef, materializedMapRef,
                    historicalCompletedReceiptRef, genuineHistoricalCaptureRef, originalQuotaLeaseRef,
                    originalQuotaRejectionRef, originalQuotaSourceMapRef, actualManifest);
        }
    }

    /** Output paths are locations, not caller-invented FileRefs; machine/time are observed by this producer. */
    public record Request(String schema, FileRef resourcePlanRef, FileRef capacityReleaseRef,
            FileRef toolsReceiptRef, OwnSources own, List<FileRef> junitRuntime,
            String reviewAtUtc, String manifestOutput, String inputOutput) {
        public Request {
            if (!REQUEST_SCHEMA.equals(schema)) throw new IllegalArgumentException("Exact production request schema required");
            positive(resourcePlanRef); positive(capacityReleaseRef); positive(toolsReceiptRef);
            Objects.requireNonNull(own); Objects.requireNonNull(reviewAtUtc);
            Objects.requireNonNull(manifestOutput); Objects.requireNonNull(inputOutput);
            junitRuntime = List.copyOf(junitRuntime);
            if (junitRuntime.isEmpty() || junitRuntime.size() > 32)
                throw new IllegalArgumentException("Actual original JUnit runtime closure required");
        }
    }
    public record Prepared(String schema, String machineId, String observedAtUtc,
            FileRef requestRef, FileRef boundedManifestRef, FileRef inputRef,
            boolean postqualificationGranted) {
        public Prepared {
            if (!RESULT_SCHEMA.equals(schema) || postqualificationGranted)
                throw new IllegalArgumentException("Preparation grants no postqualification");
        }
    }

    /** CLI: requestPath requestBytes requestSha256. No discovery, alternate Own or fallback inputs. */
    public static void main(String[] args) throws IOException {
        if (args.length != 3 || !args[1].matches("[1-9][0-9]{0,6}"))
            throw new IOException("Exact bounded production-request path/bytes/SHA required");
        var ref = new FileRef(args[0], Long.parseLong(args[1]), args[2]);
        var prepared = produce(ref, Clock.systemUTC());
        System.out.println("PREPARED_ONLY_NOT_OWN_NOT_JUNIT_NOT_TOOLS_ADOPTION "
                + ControlBuild.strictMapper().writeValueAsString(prepared));
    }

    public static Prepared produce(FileRef requestRef, Clock clock) throws IOException {
        Objects.requireNonNull(clock);
        var witness = SharedSourceFiles.observe(Path.of(requestRef.path()));
        if (!witness.source().equals(requestRef)) throw new IOException("Original request identity changed");
        var request = ControlBuild.strictMapper().readValue(read(requestRef, MAX_REQUEST_BYTES), Request.class);
        var plan = ControlBuild.strictMapper().readValue(read(request.resourcePlanRef(), MAX_REQUEST_BYTES), CiBootstrap.Plan.class);
        String machine = WindowsJobProcess.currentMachineId();
        Instant observed = clock.instant(), review = Instant.parse(request.reviewAtUtc());
        if (!review.toString().equals(request.reviewAtUtc()) || !observed.isBefore(review)
                || !machine.equals(plan.machineId()) || review.isAfter(CiBootstrap.pipelineTiming(plan).workDeadline()))
            throw new IOException("Actual current same-machine resource plan and original finite deadline required");
        Path root = Path.of(plan.workRoot()).toAbsolutePath().normalize();
        Path manifest = output(request.manifestOutput(), root), target = output(request.inputOutput(), root);
        if (manifest.equals(target)) throw new IOException("Distinct fresh manifest and typed input outputs required");
        var completed = ControlBuild.verifiedCompletedReceipt(request.toolsReceiptRef());
        if (completed.targetKind() != ControlBuild.TargetKind.BUILD_TOOLS_RUNTIME
                || completed.sourceLimitProfile() != ControlBuild.SourceLimitProfile.STANDARD_8_MIB
                || !machine.equals(completed.machineId()) || !completed.completeDeployment().equals(ControlBuild.producerClosure()))
            throw new IOException("Exact verified completed Tools archive and its running closure are required");
        request.capacityReleaseRef().verify();
        for (var ref : request.own().originals()) ref.verify();
        for (var ref : request.junitRuntime()) ref.verify();
        ControlBuild.revalidateCiResources(plan, Path.of(request.capacityReleaseRef().path()), 1L << 20);
        List<FileRef> bulk = completeBulkInputs(request.own().materializedMapRef(), completed);
        if (bulk.size() <= 512 || bulk.size() > 2048)
            throw new IOException("Actual full Own closure must provide513..2048 original inputs; no generated substitutes");
        SharedSourceFiles.assertUnchanged(witness);
        var bounded = BoundedSourceInputGuard.prepare(new BoundedSourceInputGuard.PreparationRequest(
                manifest, OWN_OWNER, review, bulk), clock);
        var input = new ToolsInputPostqualification.Input(ToolsInputPostqualification.INPUT_SCHEMA,
                machine, observed.toString(), review.toString(), request.resourcePlanRef(), request.capacityReleaseRef(),
                request.toolsReceiptRef(), request.own().complete(bounded.manifestRef()),
                request.junitRuntime(), bulk);
        SharedSourceFiles.assertUnchanged(witness);
        var actual = ControlCi.writeToolsPostqualificationInput(input, target);
        SharedSourceFiles.assertUnchanged(witness);
        for (var ref : request.own().originals()) ref.verify();
        request.toolsReceiptRef().verify(); bounded.manifestRef().verify(); actual.verify();
        return new Prepared(RESULT_SCHEMA, machine, clock.instant().toString(), requestRef,
                bounded.manifestRef(), actual, false);
    }

    /** Same complete closure consumed by unchanged24c lines199..216; no receipt/manifest substituted for bodies. */
    public static List<FileRef> completeBulkInputs(FileRef mapRef, ControlBuild.BuildReceipt build) throws IOException {
        JsonNode map = ControlBuild.strictMapper().readTree(read(mapRef, 1 << 20));
        if (!"xar.integrated-host-tools-source-map/v1".equals(text(map, "schema"))
                || !build.machineId().equals(text(map, "machine_id")))
            throw new IOException("Actual same-machine integrated materialized map required");
        int tools = count(map, "tools_sources"), host = count(map, "host_overlay_sources");
        JsonNode rows = map.required("sources");
        if (!rows.isArray() || tools < 1 || host < 1 || tools > 512 || host > 512
                || Math.addExact(tools, host) > 512 || rows.size() != Math.addExact(tools, host))
            throw new IOException("Exact bounded complete Tools and Host roster required");
        var bulk = new ArrayList<FileRef>(); var selected = new ArrayList<FileRef>(); int hosts = 0;
        Path source = Path.of(build.sourceRoot());
        for (JsonNode row : rows) {
            FileRef ref = ControlBuild.strictMapper().treeToValue(row.required("materialized_ref"), FileRef.class);
            ref.verify(); bulk.add(ref);
            switch (text(row, "group")) {
                case "TOOLS" -> {
                    Path expected = source.resolve(text(row, "target_relative")).normalize();
                    if (!expected.startsWith(source) || !expected.equals(Path.of(ref.path())))
                        throw new IOException("Materialized Tools target differs from the actual build");
                    selected.add(ref);
                }
                case "HOST" -> hosts++;
                default -> throw new IOException("Only original Tools and Host groups are valid");
            }
        }
        selected.sort(Comparator.comparing(FileRef::path));
        if (hosts != host || selected.size() != tools || !selected.equals(build.sourcePins()))
            throw new IOException("Materialized source roster does not equal this successful build");
        if (build.workpackageAccountingRef() == null) throw new IOException("Actual conservative accounting is missing");
        bulk.addAll(build.compiledSourcePins()); bulk.addAll(build.completeDeployment());
        bulk.add(build.workpackageAccountingRef());
        Path reports = Path.of(build.deploymentRoot()).resolve("surefire-reports");
        ControlCi.requireJUnit(reports, build);
        try (var paths = Files.list(reports)) {
            for (Path path : paths.filter(p -> p.getFileName().toString().matches("TEST-.*\\.xml")).sorted().toList())
                bulk.add(FileRef.measure(path));
        }
        var unique = new LinkedHashMap<String, FileRef>();
        for (FileRef ref : bulk) {
            Path path = Path.of(ref.path()).toAbsolutePath().normalize();
            var canonical = new FileRef(path.toString(), ref.bytes(), ref.sha256());
            var prior = unique.putIfAbsent(path.toString().toLowerCase(Locale.ROOT), canonical);
            if (prior != null && !prior.equals(canonical)) throw new IOException("Conflicting original input identity");
        }
        mapRef.verify();
        return BoundedSourceInputGuard.canonicalInputs(List.copyOf(unique.values()));
    }
    private static byte[] read(FileRef ref, int maximum) throws IOException {
        positive(ref);
        if (ref.bytes() > maximum) throw new IOException("Pinned metadata exceeds its existing bound");
        byte[] bytes;
        try (var input = Files.newInputStream(Path.of(ref.path()))) {
            bytes = input.readNBytes(Math.toIntExact(ref.bytes()) + 1);
        }
        BoundedSourceInputGuard.verifyReadBytes(ref, bytes, maximum); ref.verify(); return bytes;
    }
    private static Path output(String value, Path root) throws IOException {
        Path path = Path.of(value);
        if (!path.isAbsolute() || !path.equals(path.normalize()) || !path.startsWith(root) || path.equals(root)
                || Files.exists(path) || path.getParent() == null || !Files.isDirectory(path.getParent()))
            throw new IOException("Fresh output in an existing authorized task directory required");
        ProjectStoragePolicy.requireBulkOutput(path); return path;
    }
    private static String text(JsonNode node, String field) throws IOException {
        JsonNode value = node.required(field);
        if (!value.isTextual()) throw new IOException("Exact textual field required: " + field);
        return value.textValue();
    }
    private static int count(JsonNode node, String field) throws IOException {
        JsonNode value = node.required(field);
        if (!value.isIntegralNumber() || !value.canConvertToInt()) throw new IOException("Exact integral count required: " + field);
        return value.intValue();
    }
    private static void positive(FileRef ref) {
        if (ref == null || ref.bytes() < 1) throw new IllegalArgumentException("Existing positive original FileRef required");
    }
}
