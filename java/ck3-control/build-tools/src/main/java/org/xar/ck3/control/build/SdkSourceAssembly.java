package org.xar.ck3.control.build;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.JsonNode;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashSet;
import java.util.HexFormat;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Locale;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.build.ControlBuild.FileRef;

/**
 * One exact source assembly for the existing SDK and cold producer.
 * This class never calls Python, launches a service, writes Git, loads Driver/SAVE,
 * emits the cold business packet, or grants import/HTTP/runtime qualification.
 * Actual packaging remains prepare_current_saved_campaign_cold_v1.compose_v1.
 */
public final class SdkSourceAssembly {
    public static final String REQUEST_SCHEMA = "xar.sdk-source-assembly-request/v1";
    public static final String REVIEW_SCHEMA = "xar.sdk-source-assembly-review/v1";
    public static final String ASSEMBLY_SCHEMA = "xar.sdk-source-assembly-actual/v1";
    private static final String PRODUCER = "tools/g2_saved_campaign/prepare_current_saved_campaign_cold_v1.py";
    private static final int MAX_FILES = 4096;
    private static final int MAX_LEAF = 8 * 1024 * 1024;
    private static final int MAX_METADATA = 2 * 1024 * 1024;
    private static final long MAX_OUTPUT = 64L * 1024 * 1024;
    private static final ObjectMapper JSON = ControlBuild.strictMapper();
    private SdkSourceAssembly() { }

    public enum SourceRole { SDK_SOURCE, SHARED_TRANSPORT, ORIGINAL_CONSUMER_TEST, PRODUCER, SUPPORT_RESOURCE }
    public enum InputOrigin { CURRENT_CANONICAL, FROZEN_SDK_SOURCE, STAGED_NEW_SOURCE }
    public enum ProtectedRole { FROZEN_SDK, FROZEN_HOST, FROZEN_RUNTIME }
    public enum AssemblyStatus { SOURCE_ASSEMBLED_NOT_IMPORTED, FAILED_PARTIAL_DO_NOT_REUSE }
    public enum NextStep { REAL_PRODUCER_COMPOSE_AND_OWNER_RECOMPOSE, ACTUAL_IMPORT_CLOSURE, SAME_HOST_CONSUMERS }
    public enum OverlayBase { ORIGINAL_SOURCE, PREVIOUS_SAME_OWNER_RESULT }
    public record Digest(long bytes, String sha256) {
        public Digest { if (bytes < 0 || bytes > MAX_LEAF || sha256 == null || !sha256.matches("[0-9a-f]{64}")) throw new IllegalArgumentException("bounded exact content digest required"); }
        public static Digest of(byte[] bytes) { return new Digest(bytes.length, SdkSourceAssembly.sha256(bytes)); }
    }
    /** Each domain patch is proven against its own original base before being merged. */
    public record Overlay(String owner, OverlayBase baseMode, FileRef patchRef, ExactSourcePatch.Syntax syntax,
                          String patchTarget, Digest standaloneBase, Digest standaloneResult) {
        public Overlay {
            if (owner == null || owner.isBlank() || baseMode == null || patchRef == null || patchRef.bytes() > 1024 * 1024 || syntax == null || standaloneBase == null || standaloneResult == null) throw new IllegalArgumentException("complete finite domain overlay required");
            ExactSourcePatch.patchPath(patchTarget);
        }
    }
    public record Source(String relativePath, SourceRole role, InputOrigin origin, FileRef original,
                         List<Overlay> overlays) {
        public Source {
            ExactSourcePatch.relative(relativePath);
            if (relativePath.startsWith(".assembly/") || relativePath.equals(".assembly") || role == null || origin == null || original == null || original.bytes() > MAX_LEAF) throw new IllegalArgumentException("exact source input required");
            overlays = List.copyOf(overlays);
            if (overlays.size() > 32) throw new IllegalArgumentException("finite ordered source overlays required");
        }
    }
    /** Import roots are relative to the new graph; original tests may still use the canonical test repo. */
    public record ImportRoute(String module, String relativeSource, ImportSourceLocation location, boolean requiredBeforeConsumer) {
        public ImportRoute {
            if (module == null || !module.matches("[A-Za-z_][A-Za-z0-9_]*(\\.[A-Za-z_][A-Za-z0-9_]*)*")) throw new IllegalArgumentException("qualified Python module required");
            ExactSourcePatch.relative(relativeSource);
            Objects.requireNonNull(location);
        }
    }
    public record ProtectedRoot(ProtectedRole role, String path) {
        public ProtectedRoot { Objects.requireNonNull(role); absolute(path); }
    }
    public record ProducerReuse(String relativeSource, String module, String callable,
                                String ownerRecomposeModule, String ownerRecomposeCallable) {
        public ProducerReuse {
            if (!PRODUCER.equals(relativeSource) || !"tools.g2_saved_campaign.prepare_current_saved_campaign_cold_v1".equals(module)
                    || !"compose_v1".equals(callable)
                    || !"tools.g2_saved_campaign.root_current_saved_campaign_cold_owner_v1".equals(ownerRecomposeModule)
                    || !"validate_current_saved_cold_owner_v1".equals(ownerRecomposeCallable)) {
                throw new IllegalArgumentException("reuse the one real compose and owner recompose, without a second business packager");
            }
        }
    }
    public record Deployment(String name, FileRef actualBuildReceipt, ControlBuild.TargetKind targetKind) {
        public Deployment {
            if (name == null || !name.matches("[a-z][a-z0-9-]{0,47}") || actualBuildReceipt == null || targetKind == null) throw new IllegalArgumentException("exact accepted deployment input required");
        }
    }
    public record Request(String schema, String machineId, String canonicalRepository,
                          String canonicalCommit, String canonicalTestRepository, String outputRoot,
                          String sdkInputRoot, String sdkRelativeRoot, List<String> importRoots,
                          List<String> approvedInputSourceRoots, List<ProtectedRoot> protectedRoots,
                          List<Source> sources, List<ImportRoute> importRoutes,
                          List<Deployment> deployments, ProducerReuse producerReuse,
                          long outputHardBytes) {
        public Request {
            if (!REQUEST_SCHEMA.equals(schema) || machineId == null || !machineId.matches("[a-z0-9][a-z0-9-]{2,127}")
                    || canonicalCommit == null || !canonicalCommit.matches("[0-9a-f]{40}") || outputHardBytes <= 0 || outputHardBytes > MAX_OUTPUT) throw new IllegalArgumentException("versioned finite assembly request required");
            absolute(canonicalRepository); absolute(canonicalTestRepository); absolute(outputRoot); absolute(sdkInputRoot); ExactSourcePatch.relative(sdkRelativeRoot);
            if (!"ck3_autonomous_player/src".equals(sdkRelativeRoot)) throw new IllegalArgumentException("SDK root means the existing repository's src directory");
            importRoots = List.copyOf(importRoots); approvedInputSourceRoots = List.copyOf(approvedInputSourceRoots);
            protectedRoots = List.copyOf(protectedRoots); sources = List.copyOf(sources); importRoutes = List.copyOf(importRoutes); deployments = List.copyOf(deployments);
            if (sources.isEmpty() || sources.size() > MAX_FILES || importRoots.isEmpty() || importRoots.size() > 16
                    || approvedInputSourceRoots.isEmpty() || approvedInputSourceRoots.size() > 32
                    || importRoutes.isEmpty() || importRoutes.size() > MAX_FILES || deployments.isEmpty() || deployments.size() > 16 || producerReuse == null) throw new IllegalArgumentException("complete bounded source/import/deployment closure required");
            for (String root : approvedInputSourceRoots) absolute(root);
            for (String root : importRoots) if (!root.equals(".")) ExactSourcePatch.relative(root);
            if (!importRoots.contains(".") || !importRoots.contains(sdkRelativeRoot)) throw new IllegalArgumentException("fresh repository and SDK import roots required");
            Set<ProtectedRole> roles = new HashSet<>();
            for (ProtectedRoot root : protectedRoots) if (!roles.add(root.role())) throw new IllegalArgumentException("duplicate frozen root role");
            if (!roles.equals(Set.of(ProtectedRole.FROZEN_SDK, ProtectedRole.FROZEN_HOST, ProtectedRole.FROZEN_RUNTIME))) throw new IllegalArgumentException("all three existing frozen roots must remain protected");
            Set<String> names = new HashSet<>();
            for (Source source : sources) if (!names.add(source.relativePath().toLowerCase(Locale.ROOT))) throw new IllegalArgumentException("duplicate/case-alias source output");
            if (sources.stream().noneMatch(source -> source.relativePath().equals(PRODUCER) && source.role() == SourceRole.PRODUCER)) throw new IllegalArgumentException("real graph producer must be part of the fresh closure");
        }
    }
    public record AppliedOverlay(String owner, OverlayBase baseMode, FileRef patchRef, Digest standaloneBase,
                                 Digest standaloneResult, Digest mergedBefore, Digest mergedAfter,
                                 int exactHunks) { }
    public record ReviewedSource(String relativePath, SourceRole role, InputOrigin origin,
                                 FileRef original, Digest result, List<AppliedOverlay> overlays) {
        public ReviewedSource { overlays = List.copyOf(overlays); }
    }
    public record DeploymentEvidence(String name, FileRef actualBuildReceipt,
                                     ControlBuild.TargetKind targetKind, String deploymentRoot,
                                     List<FileRef> completeFiles, List<FileRef> producerRuntime,
                                     FileRef javaExecutable, boolean residentHostObserved) {
        public DeploymentEvidence { completeFiles = List.copyOf(completeFiles); producerRuntime = List.copyOf(producerRuntime); if (residentHostObserved) throw new IllegalArgumentException("assembly never observes a resident host"); }
    }
    public record SdkInventory(String inputRoot, int originalFiles, long originalBytes,
                               String relativeContentSha256, List<String> excludedCacheDirectories) {
        public SdkInventory { excludedCacheDirectories = List.copyOf(excludedCacheDirectories); }
    }
    public record Quote(long sourceLogicalBytes, long metadataHardBytes, int sourceFiles,
                        int directoryCount, long outputHardBytes) {
        public Quote { if (sourceLogicalBytes < 0 || metadataHardBytes != MAX_METADATA || sourceFiles <= 0 || sourceFiles > MAX_FILES || directoryCount <= 0 || outputHardBytes > MAX_OUTPUT || Math.addExact(sourceLogicalBytes, metadataHardBytes) > outputHardBytes) throw new IllegalArgumentException("finite source assembly quote required"); }
    }
    public record Review(String schema, String machineId, String observedAtUtc, Request request,
                         FileRef requestRef, List<ReviewedSource> sourceClosure,
                         SdkInventory completeSdkInputInventory, List<DeploymentEvidence> deploymentClosure, String sourceSetSha256,
                         Quote quote, boolean importQualified, boolean producerPacketGenerated) {
        public Review {
            if (!REVIEW_SCHEMA.equals(schema) || request == null || requestRef == null || completeSdkInputInventory == null || !request.machineId().equals(machineId)
                    || sourceSetSha256 == null || !sourceSetSha256.matches("[0-9a-f]{64}") || quote == null || importQualified || producerPacketGenerated) throw new IllegalArgumentException("source review is not import or business packet qualification");
            Instant.parse(observedAtUtc); sourceClosure = List.copyOf(sourceClosure); deploymentClosure = List.copyOf(deploymentClosure);
        }
    }
    public record WritePermit(String machineId, String exactOutputRoot, String expiresAtUtc,
                              long allocationUpperLimitBytes, long allocationUnitBytes,
                              long perDirectoryGuardBytes, FileRef freshStorageEvidence) {
        public WritePermit {
            absolute(exactOutputRoot); Instant.parse(expiresAtUtc);
            if (machineId == null || machineId.isBlank() || allocationUpperLimitBytes <= 0 || allocationUpperLimitBytes > MAX_OUTPUT
                    || allocationUnitBytes <= 0 || allocationUnitBytes > 1024 * 1024 || perDirectoryGuardBytes < 0 || freshStorageEvidence == null) throw new IllegalArgumentException("actual same-machine finite storage permit required");
        }
    }
    /** Root/storage supplies this live port after a fresh capacity check. There is no JSON-only default. */
    public interface CapacityGate {
        WritePermit acquire(Review actualReview) throws IOException;
        void revalidate(WritePermit permit, long consumedAllocationUpperBytes) throws IOException;
    }
    public record OutputSource(String relativePath, SourceRole role, FileRef actual) {
        public OutputSource { ExactSourcePatch.relative(relativePath); Objects.requireNonNull(role); Objects.requireNonNull(actual); }
    }
    public enum ImportSourceLocation { FRESH_GRAPH, CANONICAL_ORIGINAL_TEST }
    public record ImportSource(String relativePath, ImportSourceLocation location, FileRef reference) {
        public ImportSource { ExactSourcePatch.relative(relativePath); Objects.requireNonNull(location); Objects.requireNonNull(reference); }
    }
    public record SelectedImportRoute(String module, String relativeSource, ImportSourceLocation location,
                                      FileRef physicalRef, boolean requiredBeforeConsumer) {
        public SelectedImportRoute { new ImportRoute(module, relativeSource, location, requiredBeforeConsumer); Objects.requireNonNull(physicalRef); }
    }
    public record Actual(String schema, String machineId, String startedAtUtc, String observedAtUtc,
                         AssemblyStatus status, FileRef reviewRef, String graphRoot, String sdkRoot,
                         String canonicalTestRepository, List<String> importRoots,
                         List<OutputSource> actualSourceClosure, List<ImportSource> importSourceClosure,
                         List<SelectedImportRoute> selectedImportRoutes, List<DeploymentEvidence> deploymentClosure,
                         List<ImportRoute> requiredImportRoutes, ProducerReuse producerReuse,
                         List<NextStep> unexecutedNextSteps, String sourceSetSha256,
                         FileRef storageEvidence, long chargedAllocationUpperBytes,
                         boolean actualImportsObserved, boolean runtimeQualified, String error) {
        public Actual {
            actualSourceClosure = List.copyOf(actualSourceClosure); importSourceClosure = List.copyOf(importSourceClosure); selectedImportRoutes = List.copyOf(selectedImportRoutes); deploymentClosure = List.copyOf(deploymentClosure);
            requiredImportRoutes = List.copyOf(requiredImportRoutes); importRoots = List.copyOf(importRoots); unexecutedNextSteps = List.copyOf(unexecutedNextSteps);
            absolute(graphRoot); absolute(sdkRoot); absolute(canonicalTestRepository); Instant.parse(startedAtUtc); Instant.parse(observedAtUtc);
            if (!ASSEMBLY_SCHEMA.equals(schema) || machineId == null || machineId.isBlank() || status == null || reviewRef == null || producerReuse == null
                    || storageEvidence == null || sourceSetSha256 == null || !sourceSetSha256.matches("[0-9a-f]{64}") || actualImportsObserved || runtimeQualified
                    || (status == AssemblyStatus.FAILED_PARTIAL_DO_NOT_REUSE) != (error != null)) throw new IllegalArgumentException("assembly cannot grant actual import/runtime qualification");
            if (status == AssemblyStatus.SOURCE_ASSEMBLED_NOT_IMPORTED && (actualSourceClosure.isEmpty() || importSourceClosure.isEmpty() || deploymentClosure.isEmpty())) throw new IllegalArgumentException("complete nonempty assembly closures required");
        }
    }

    public static Request readRequest(FileRef reference) throws IOException {
        return JSON.readValue(read(reference, MAX_METADATA), Request.class);
    }
    /** Recheck actual files for the one caller-owned SDK observer; this grants source integrity only. */
    public static Actual readActual(FileRef reference) throws IOException {
        Actual actual = JSON.readValue(read(reference, MAX_METADATA), Actual.class);
        Path root = Path.of(actual.graphRoot()).toAbsolutePath().normalize();
        SharedSourceFiles.plainAncestors(root);
        if (!actual.machineId().equals(WindowsJobProcess.currentMachineId())) throw new IOException("source assembly receipt belongs to a different machine");
        if (actual.status() != AssemblyStatus.SOURCE_ASSEMBLED_NOT_IMPORTED || !Path.of(reference.path()).equals(root.resolve(".assembly/ACTUAL.json"))) throw new IOException("complete actual fresh graph receipt required");
        Review declared = JSON.readValue(read(actual.reviewRef(), MAX_METADATA), Review.class);
        if (!declared.sourceSetSha256().equals(actual.sourceSetSha256()) || !Path.of(declared.request().outputRoot()).toAbsolutePath().normalize().equals(root)
                || !declared.request().importRoutes().equals(actual.requiredImportRoutes()) || !declared.deploymentClosure().equals(actual.deploymentClosure())) throw new IOException("source graph differs from its exact reviewed provenance");
        requireExactOutputSet(root, actual.actualSourceClosure());
        List<DigestRow> rows = actual.actualSourceClosure().stream().sorted(Comparator.comparing(OutputSource::relativePath))
                .map(row -> new DigestRow(row.relativePath(), content(row.actual()))).toList();
        if (!sha256(JSON.writeValueAsBytes(rows)).equals(actual.sourceSetSha256())) throw new IOException("actual graph source-set digest differs");
        Set<Path> fresh = new HashSet<>();
        for (OutputSource source : actual.actualSourceClosure()) {
            if (!Path.of(source.actual().path()).equals(root.resolve(source.relativePath()).normalize())) throw new IOException("actual graph source path differs");
            if (source.relativePath().endsWith(".py")) fresh.add(Path.of(source.actual().path()));
        }
        Set<Path> imports = new HashSet<>();
        for (ImportSource source : actual.importSourceClosure()) {
            source.reference().verify(); Path path = Path.of(source.reference().path());
            if (!imports.add(path)) throw new IOException("duplicate actual import source reference");
            if (source.location() == ImportSourceLocation.FRESH_GRAPH && !fresh.remove(path)) throw new IOException("fresh import is absent from complete graph source closure");
            if (source.location() == ImportSourceLocation.CANONICAL_ORIGINAL_TEST && !path.startsWith(Path.of(actual.canonicalTestRepository()))) throw new IOException("original test source origin differs");
        }
        if (!fresh.isEmpty()) throw new IOException("fresh Python graph source absent from import witness allowlist");
        Set<String> routeModules = new HashSet<>();
        for (SelectedImportRoute route : actual.selectedImportRoutes()) {
            if (!routeModules.add(route.module()) || actual.importSourceClosure().stream().noneMatch(row -> row.relativePath().equals(route.relativeSource())
                    && row.location() == route.location() && row.reference().equals(route.physicalRef()))) throw new IOException("selected import route lacks one exact physical source choice");
            if (actual.requiredImportRoutes().stream().noneMatch(expected -> expected.module().equals(route.module()) && expected.relativeSource().equals(route.relativeSource())
                    && expected.location() == route.location() && expected.requiredBeforeConsumer() == route.requiredBeforeConsumer())) throw new IOException("selected physical route differs from its declared import contract");
        }
        if (routeModules.size() != actual.requiredImportRoutes().size()) throw new IOException("complete selected import routes required");
        if (!Path.of(actual.sdkRoot()).equals(root.resolve("ck3_autonomous_player/src")) || !actual.importRoots().contains(actual.sdkRoot())) throw new IOException("selected SDK src directory/import root differs");
        for (String importRoot : actual.importRoots()) if (!Path.of(importRoot).toAbsolutePath().normalize().startsWith(root)) throw new IOException("source graph import roots must all belong to the selected fresh view");
        for (DeploymentEvidence deployment : actual.deploymentClosure()) {
            deployment.actualBuildReceipt().verify();
            ControlBuild.BuildReceipt accepted = ControlBuild.acceptedReceipt(Path.of(deployment.actualBuildReceipt().path()));
            if (!accepted.completeDeployment().equals(deployment.completeFiles()) || accepted.targetKind() != deployment.targetKind()
                    || !accepted.machineId().equals(actual.machineId())) throw new IOException("actual accepted deployment closure differs");
        }
        return actual;
    }
    /** Read-only preview: the complete graph is not copied and no process is started. */
    public static Review review(FileRef requestRef) throws IOException {
        Request request = readRequest(requestRef);
        return review(request, requestRef, WindowsJobProcess.currentMachineId());
    }
    static Review review(Request request, FileRef requestRef, String actualMachineId) throws IOException {
        if (!request.machineId().equals(actualMachineId)) throw new IOException("source assembly machine differs");
        if (!readRequest(requestRef).equals(request)) throw new IOException("in-memory request differs from its exact JSON reference");
        validateRoots(request);
        requestRef.verify();
        SdkInventory inventory = completeSdkInventory(request);
        List<ReviewedSource> sources = new ArrayList<>();
        long total = 0;
        Set<String> directories = new LinkedHashSet<>(); directories.add("."); directories.add(".assembly");
        for (Source source : request.sources().stream().sorted(Comparator.comparing(Source::relativePath)).toList()) {
            requireApprovedSource(request, source.original());
            validateSourceOrigin(request, source);
            byte[] original = read(source.original(), MAX_LEAF), merged = original;
            List<AppliedOverlay> applied = new ArrayList<>();
            for (int overlayIndex = 0; overlayIndex < source.overlays().size(); overlayIndex++) {
                Overlay overlay = source.overlays().get(overlayIndex);
                requireApprovedSource(request, overlay.patchRef());
                byte[] patch = read(overlay.patchRef(), 1024 * 1024);
                standaloneMaterial(source, original, overlayIndex);
                Digest prior = Digest.of(merged);
                ExactSourcePatch.Result changed = ExactSourcePatch.apply(merged, patch, overlay.syntax(), overlay.patchTarget());
                merged = changed.bytes();
                applied.add(new AppliedOverlay(overlay.owner(), overlay.baseMode(), overlay.patchRef(), overlay.standaloneBase(), overlay.standaloneResult(), prior, Digest.of(merged), changed.hunks()));
            }
            Digest result = Digest.of(merged); total = Math.addExact(total, result.bytes());
            if (total + MAX_METADATA > request.outputHardBytes()) throw new IOException("source closure exceeds finite graph quote");
            sources.add(new ReviewedSource(source.relativePath(), source.role(), source.origin(), source.original(), result, applied));
            String parent = source.relativePath();
            while (parent.contains("/")) { parent = parent.substring(0, parent.lastIndexOf('/')); directories.add(parent); }
        }
        validateImports(request, sources);
        List<DeploymentEvidence> deployments = deployments(request);
        verifyInputs(request);
        return new Review(REVIEW_SCHEMA, actualMachineId, Instant.now().toString(), request, requestRef, sources, inventory, deployments,
                sourceSetDigest(sources), new Quote(total, MAX_METADATA, sources.size(), directories.size(), request.outputHardBytes()), false, false);
    }

    /** Materialization is gated independently; callers cannot obtain a capacity permit from this class. */
    public static Actual assemble(FileRef reviewRef, CapacityGate liveCapacityGate) throws IOException {
        Objects.requireNonNull(liveCapacityGate);
        Review declared = JSON.readValue(read(reviewRef, MAX_METADATA), Review.class);
        Review fresh = review(declared.request(), declared.requestRef(), WindowsJobProcess.currentMachineId());
        if (!fresh.sourceClosure().equals(declared.sourceClosure()) || !fresh.deploymentClosure().equals(declared.deploymentClosure())
                || !fresh.completeSdkInputInventory().equals(declared.completeSdkInputInventory())
                || !fresh.sourceSetSha256().equals(declared.sourceSetSha256()) || !fresh.quote().equals(declared.quote())) throw new IOException("fresh source/deployment review differs; refresh the exact assembly review");
        WritePermit permit = liveCapacityGate.acquire(fresh);
        validatePermit(permit, fresh);
        long required = allocatedUpper(fresh.quote(), fresh.sourceClosure(), permit);
        if (required > permit.allocationUpperLimitBytes()) throw new IOException("graph allocation upper exceeds live capacity permit");
        Path root = Path.of(fresh.request().outputRoot()).toAbsolutePath().normalize();
        if (Files.exists(root, LinkOption.NOFOLLOW_LINKS)) throw new IOException("fresh source graph destination already exists");
        long charged = Math.multiplyExact(fresh.quote().directoryCount(), permit.perDirectoryGuardBytes());
        String started = Instant.now().toString();
        List<OutputSource> outputs = new ArrayList<>();
        guard(liveCapacityGate, permit, charged);
        Files.createDirectory(root); Files.createDirectory(root.resolve(".assembly"));
        String failure = null;
        try {
            for (Source source : fresh.request().sources().stream().sorted(Comparator.comparing(Source::relativePath)).toList()) {
                ReviewedSource expected = fresh.sourceClosure().stream().filter(row -> row.relativePath().equals(source.relativePath())).findFirst().orElseThrow();
                byte[] bytes = material(source);
                if (!Digest.of(bytes).equals(expected.result())) throw new IOException("source changed between review and write: " + source.relativePath());
                charged = Math.addExact(charged, round(bytes.length, permit.allocationUnitBytes()));
                guard(liveCapacityGate, permit, charged);
                Path destination = root.resolve(source.relativePath()).normalize();
                Files.createDirectories(destination.getParent());
                Files.write(destination, bytes, StandardOpenOption.CREATE_NEW);
                FileRef actual = FileRef.measure(destination);
                if (!content(actual).equals(expected.result())) throw new IOException("fresh graph write readback differs");
                outputs.add(new OutputSource(source.relativePath(), source.role(), actual));
            }
            verifyInputs(fresh.request());
            if (!completeSdkInventory(fresh.request()).equals(fresh.completeSdkInputInventory())) throw new IOException("complete original SDK source inventory changed during materialization");
            for (Deployment deployment : fresh.request().deployments()) ControlBuild.acceptedReceipt(Path.of(deployment.actualBuildReceipt().path()));
            requireExactOutputSet(root, outputs);
            guard(liveCapacityGate, permit, charged);
        } catch (IOException | RuntimeException error) {
            failure = error.getClass().getSimpleName() + ": " + error.getMessage();
        }
        Actual actual = actualFor(fresh, reviewRef, outputs, permit, charged, started, failure);
        byte[] receipt = JSON.writerWithDefaultPrettyPrinter().writeValueAsBytes(actual);
        if (receipt.length > MAX_METADATA) throw new IOException("actual source closure receipt exceeds metadata reservation");
        guard(liveCapacityGate, permit, Math.addExact(charged, round(receipt.length, permit.allocationUnitBytes())));
        Files.write(root.resolve(".assembly/ACTUAL.json"), receipt, StandardOpenOption.CREATE_NEW);
        if (failure != null) throw new IOException("partial source graph retained, not reusable: " + failure);
        return actual;
    }
    private static Actual actualFor(Review fresh, FileRef reviewRef, List<OutputSource> outputs,
                                    WritePermit permit, long charged, String started, String failure) throws IOException {
        Path root = Path.of(fresh.request().outputRoot()).toAbsolutePath().normalize();
        List<String> imports = fresh.request().importRoots().stream().map(relative -> relative.equals(".") ? root.toString() : root.resolve(relative).toString()).toList();
        List<ImportSource> importSources = new ArrayList<>();
        for (OutputSource output : outputs) if (output.relativePath().endsWith(".py")) importSources.add(new ImportSource(output.relativePath(), ImportSourceLocation.FRESH_GRAPH, output.actual()));
        for (Source source : fresh.request().sources()) if (source.role() == SourceRole.ORIGINAL_CONSUMER_TEST && source.relativePath().endsWith(".py")
                && fresh.request().importRoutes().stream().anyMatch(route -> route.relativeSource().equals(source.relativePath()) && route.location() == ImportSourceLocation.CANONICAL_ORIGINAL_TEST)) {
            importSources.add(new ImportSource(source.relativePath(), ImportSourceLocation.CANONICAL_ORIGINAL_TEST, source.original()));
        }
        List<SelectedImportRoute> selected = failure == null ? selectedRoutes(fresh.request(), importSources) : List.of();
        return new Actual(ASSEMBLY_SCHEMA, fresh.machineId(), started, Instant.now().toString(),
                failure == null ? AssemblyStatus.SOURCE_ASSEMBLED_NOT_IMPORTED : AssemblyStatus.FAILED_PARTIAL_DO_NOT_REUSE,
                reviewRef, root.toString(), root.resolve(fresh.request().sdkRelativeRoot()).toString(), fresh.request().canonicalTestRepository(), imports,
                outputs, importSources, selected, fresh.deploymentClosure(), fresh.request().importRoutes(), fresh.request().producerReuse(),
                List.of(NextStep.REAL_PRODUCER_COMPOSE_AND_OWNER_RECOMPOSE, NextStep.ACTUAL_IMPORT_CLOSURE, NextStep.SAME_HOST_CONSUMERS),
                fresh.sourceSetSha256(), permit.freshStorageEvidence(), charged, false, false, failure);
    }

    public static final String VIEWS_SCHEMA = "xar.sdk-shared-source-views-request/v2";
    private static final String SOURCE32_EXPORTER_SHA256 = "8b6972ac2a82b30c92b531c640df0eb9aa6e43cc205ab9d7d23796d5739da432";
    /** This precise exporter binds SHA/blob and native volume/FileID; its links fields are observed snapshots. */
    public record Source32Reuse(FileRef baseFreezeRef, FileRef exporterSourceRef) {
        public Source32Reuse {
            if (baseFreezeRef == null || exporterSourceRef == null || baseFreezeRef.bytes() > MAX_METADATA
                    || !SOURCE32_EXPORTER_SHA256.equals(exporterSourceRef.sha256())) throw new IllegalArgumentException("the exact reviewed Source32 export contract is required; no configurable invariant weakening");
        }
    }
    record FrozenSourceRow(String relative, Digest content, String gitBlobSha1, String gitMode) { }
    public enum SourceViewRole { BASELINE, LEGACY, CONSUMER }
    public record Source32View(SourceViewRole role, FileRef assemblyActualRef, String sdkRoot,
                               FileRef sdkFreezeRef, FileRef source32AnchorRef) {
        public Source32View {
            Objects.requireNonNull(role); Objects.requireNonNull(assemblyActualRef); absolute(sdkRoot);
            if (sdkFreezeRef == null || sdkFreezeRef.bytes() > 1_048_576 || source32AnchorRef == null) throw new IllegalArgumentException("exact bounded existing SDK inventory and unchanged Source32 anchor required");
        }
    }
    public record FrozenSourceWitness(String relativePath, SharedSourceFiles.Witness before, SharedSourceFiles.NativeFile after) {
        public FrozenSourceWitness { ExactSourcePatch.relative(relativePath); Objects.requireNonNull(before); Objects.requireNonNull(after); }
    }
    public record Source32ReuseActual(String schema, String machineId, String observedAtUtc, Source32Reuse contract,
                                     String sourceRoot, int frozenSourceFiles, int reusedBaselineFiles,
                                     long reusedBaselineLogicalBytes, long existingReusedNativeAllocationBytes,
                                     List<FrozenSourceWitness> allOriginalSources,
                                     String invariantScope) {
        public Source32ReuseActual {
            allOriginalSources = List.copyOf(allOriginalSources); absolute(sourceRoot); Instant.parse(observedAtUtc);
            if (!"xar.sdk-source32-reuse-actual/v1".equals(schema) || machineId == null || machineId.isBlank() || contract == null
                    || frozenSourceFiles <= 0 || frozenSourceFiles != allOriginalSources.size() || reusedBaselineFiles < 0 || reusedBaselineFiles > frozenSourceFiles
                    || reusedBaselineLogicalBytes < 0 || existingReusedNativeAllocationBytes < 0 || invariantScope == null || invariantScope.isBlank()) throw new IllegalArgumentException("complete native immutable source reuse evidence required");
        }
    }
    private record FrozenReuseState(Source32Reuse contract, Path root, List<FrozenSourceRow> rows,
                                    FileRef originalNativeInventory,
                                    Map<String, SharedSourceFiles.Witness> originals,
                                    Map<String, SharedSourceFiles.Witness> reusableByOutput) { }
    public record LegacyConstraint(String nativeRelativePath, Digest originalNative,
                                    String fixtureRelativePath, Digest identicalPatchedFixture) {
        public LegacyConstraint { ExactSourcePatch.relative(nativeRelativePath); ExactSourcePatch.relative(fixtureRelativePath); Objects.requireNonNull(originalNative); Objects.requireNonNull(identicalPatchedFixture); }
    }
    public record ViewsRequest(String schema, String machineId, String groupRoot,
                               FileRef baselineReviewRef, FileRef legacyReviewRef, FileRef consumerReviewRef,
                               LegacyConstraint legacyConstraint, Source32Reuse source32Reuse, long cumulativePhysicalHardBytes) {
        public ViewsRequest {
            absolute(groupRoot);
            if (!VIEWS_SCHEMA.equals(schema) || machineId == null || machineId.isBlank() || baselineReviewRef == null || legacyReviewRef == null || consumerReviewRef == null
                    || legacyConstraint == null || source32Reuse == null || cumulativePhysicalHardBytes <= 0 || cumulativePhysicalHardBytes > MAX_OUTPUT) throw new IllegalArgumentException("exact three-review shared view and immutable-reuse request required");
        }
    }
    public record SharedQuote(String machineId, String groupRoot, long baselineCopyLogicalBytes,
                              int reusedBaselineSourceFiles, long reusedBaselineLogicalBytes,
                              long privateChangedLogicalBytes, long allViewLogicalBytes,
                              int sourcePathCount, int directories, long metadataHardBytes,
                              long cumulativePhysicalHardBytes) { }
    public interface SharedCapacityGate {
        WritePermit acquire(SharedQuote actualQuote, FileRef viewsRequestRef) throws IOException;
        void revalidate(WritePermit permit, long consumedAllocationUpperBytes) throws IOException;
    }
    public record PhysicalFile(SharedSourceFiles.NativeFile nativeFile, FileRef representative, List<String> pathAliases) {
        public PhysicalFile { pathAliases = List.copyOf(pathAliases); }
    }
    public record PhysicalCensus(long logicalBytesAcrossAllSourcePaths, int sourcePaths, int distinctNativeFiles,
                                 long nativeUniqueSourceAllocationBytes, long nativePerPathAllocationSumBytes,
                                 long nativeDataAllocationAvoidedByLinksBytes, List<PhysicalFile> uniqueFiles,
                                 String metadataScope) {
        public PhysicalCensus { uniqueFiles = List.copyOf(uniqueFiles); }
    }
    public record HardlinkAllocationActual(String schema, String machineId, String observedAtUtc,
                                           int hardlinkOperations, long allocatedGrowthBytes,
                                           List<SharedSourceFiles.LinkResult> allocationChanges, String scope) {
        public HardlinkAllocationActual {
            allocationChanges = List.copyOf(allocationChanges); Instant.parse(observedAtUtc);
            if (!"xar.sdk-hardlink-allocation-actual/v1".equals(schema) || machineId == null || machineId.isBlank()
                    || hardlinkOperations < 0 || allocatedGrowthBytes < 0 || allocationChanges.size() > hardlinkOperations || scope == null || scope.isBlank()) throw new IllegalArgumentException("bounded observed hardlink allocation accounting required");
            long actualGrowth = 0;
            for (var operation : allocationChanges) {
                if (operation.before().nativeFile().allocatedBytes() == operation.sourceAfter().nativeFile().allocatedBytes()) throw new IllegalArgumentException("allocation change journal must contain actual changes");
                actualGrowth = Math.addExact(actualGrowth, operation.allocatedGrowthBytes());
            }
            if (actualGrowth != allocatedGrowthBytes) throw new IllegalArgumentException("actual hardlink growth sum differs");
        }
    }
    private static final class LinkAccounting {
        private int operations;
        private long growth;
        private final List<SharedSourceFiles.LinkResult> changes = new ArrayList<>();
    }
    public enum SharedViewStatus { SOURCE_VIEWS_ASSEMBLED_NOT_IMPORTED }
    public record ViewsActual(String schema, String machineId, String observedAtUtc, SharedViewStatus status,
                              FileRef requestRef, FileRef baselineActualRef, FileRef legacyActualRef, FileRef consumerActualRef,
                              LegacyConstraint legacyConstraint, FileRef source32ReuseActualRef, FileRef hardlinkAllocationActualRef, List<Source32View> sdkSourceViews,
                              PhysicalCensus sourcePhysicalCensus,
                              int privateAtomicReplacements, FileRef storageEvidence,
                              long chargedAllocationUpperBytes, boolean sdkExecuted, boolean runtimeQualified) {
        public ViewsActual {
            sdkSourceViews = List.copyOf(sdkSourceViews);
            if (!"xar.sdk-shared-source-views-actual/v2".equals(schema) || machineId == null || machineId.isBlank() || status == null
                    || requestRef == null || baselineActualRef == null || legacyActualRef == null || consumerActualRef == null || legacyConstraint == null || sourcePhysicalCensus == null
                    || source32ReuseActualRef == null || hardlinkAllocationActualRef == null || sdkSourceViews.size() != 3 || privateAtomicReplacements < 0 || storageEvidence == null || chargedAllocationUpperBytes <= 0 || chargedAllocationUpperBytes > MAX_OUTPUT || sdkExecuted || runtimeQualified) throw new IllegalArgumentException("complete unexecuted source view provenance required");
            Instant.parse(observedAtUtc);
        }
    }
    private record ThreeReviews(Review baseline, Review legacy, Review consumer) { }

    /** Validate shared provenance and actual native sharing before the caller selects either view. */
    public static ViewsActual readViewsActual(FileRef reference) throws IOException {
        ViewsActual actual = JSON.readValue(read(reference, MAX_METADATA), ViewsActual.class);
        ViewsRequest request = JSON.readValue(read(actual.requestRef(), MAX_METADATA), ViewsRequest.class);
        Path group = Path.of(request.groupRoot()).toAbsolutePath().normalize(); SharedSourceFiles.plainAncestors(group);
        if (!Path.of(reference.path()).equals(group.resolve(".assembly/SHARED-VIEWS-ACTUAL.json")) || !request.machineId().equals(actual.machineId())
                || !request.legacyConstraint().equals(actual.legacyConstraint())) throw new IOException("shared source receipt differs from exact group request");
        Actual baseline = readActual(actual.baselineActualRef()), legacy = readActual(actual.legacyActualRef()), consumer = readActual(actual.consumerActualRef());
        Set<Path> roots = new HashSet<>();
        for (Actual view : List.of(baseline, legacy, consumer)) if (!Path.of(view.graphRoot()).getParent().equals(group) || !roots.add(Path.of(view.graphRoot())) || !view.machineId().equals(actual.machineId())) throw new IOException("shared actual views require distinct exact same-parent roots");
        if (!baseline.reviewRef().equals(request.baselineReviewRef()) || !legacy.reviewRef().equals(request.legacyReviewRef()) || !consumer.reviewRef().equals(request.consumerReviewRef())) throw new IOException("shared view actual/review lineage differs");
        Map<String, SharedSourceFiles.Witness> base = witnesses(baseline.actualSourceClosure()), old = witnesses(legacy.actualSourceClosure()), fresh = witnesses(consumer.actualSourceClosure());
        requireConstraint(actual.legacyConstraint(), old, fresh);
        if (!Path.of(actual.source32ReuseActualRef().path()).equals(group.resolve(".assembly/SOURCE32-REUSE-ACTUAL.json"))) throw new IOException("immutable source evidence must belong to the same exact shared group");
        readSource32ReuseActual(actual.source32ReuseActualRef(), request.source32Reuse(), actual.machineId());
        if (!Path.of(actual.hardlinkAllocationActualRef().path()).equals(group.resolve(".assembly/HARDLINK-ALLOCATION-ACTUAL.json"))) throw new IOException("hardlink allocation evidence must belong to its shared group");
        HardlinkAllocationActual allocation = JSON.readValue(read(actual.hardlinkAllocationActualRef(), MAX_METADATA), HardlinkAllocationActual.class);
        if (!allocation.machineId().equals(actual.machineId())) throw new IOException("hardlink allocation machine differs");
        Map<SourceViewRole, Actual> viewActuals = Map.of(SourceViewRole.BASELINE, baseline, SourceViewRole.LEGACY, legacy, SourceViewRole.CONSUMER, consumer);
        Map<SourceViewRole, FileRef> viewRefs = Map.of(SourceViewRole.BASELINE, actual.baselineActualRef(), SourceViewRole.LEGACY, actual.legacyActualRef(), SourceViewRole.CONSUMER, actual.consumerActualRef());
        Set<SourceViewRole> roles = new HashSet<>();
        for (Source32View binding : actual.sdkSourceViews()) {
            if (!roles.add(binding.role()) || !viewRefs.get(binding.role()).equals(binding.assemblyActualRef())) throw new IOException("one exact SDK source binding for each selected view required");
            verifySource32View(binding, viewActuals.get(binding.role()), request.source32Reuse().baseFreezeRef());
        }
        if (!physicalCensus(base, old, fresh).equals(actual.sourcePhysicalCensus())) throw new IOException("actual shared source physical census changed");
        actual.storageEvidence().verify(); return actual;
    }

    /** One baseline copy and two hardlink views. No SDK process is started by this producer. */
    public static ViewsActual assembleViews(FileRef viewsRequestRef, SharedCapacityGate liveGate) throws IOException {
        Objects.requireNonNull(liveGate);
        ViewsRequest request = JSON.readValue(read(viewsRequestRef, MAX_METADATA), ViewsRequest.class);
        ThreeReviews reviews = threeReviews(request);
        FrozenReuseState frozen = inspectSource32Reuse(request, reviews.baseline());
        SharedSourceFiles.plainAncestors(Path.of(request.groupRoot()));
        Path group = Path.of(request.groupRoot()).toRealPath();
        SharedSourceFiles.plainAncestors(group);
        try (var entries = Files.list(group)) { if (entries.findAny().isPresent()) throw new IOException("shared source group must be an independently admitted empty directory"); }
        SharedQuote quote = sharedQuote(request, reviews, frozen);
        WritePermit permit = liveGate.acquire(quote, viewsRequestRef);
        if (!permit.machineId().equals(request.machineId()) || !Path.of(permit.exactOutputRoot()).toRealPath().equals(group)) throw new IOException("shared source permit exact group/machine differs");
        permit.freshStorageEvidence().verify();
        long forecast = sharedUpper(quote, reviews, frozen, permit);
        if (forecast > permit.allocationUpperLimitBytes() || forecast > request.cumulativePhysicalHardBytes()) throw new IOException("shared source actual allocation upper exceeds the cumulative live permit");
        sharedGuard(liveGate, permit, 0);
        Files.createDirectory(group.resolve(".assembly"));
        long[] charged = {permit.perDirectoryGuardBytes()};
        LinkAccounting linkAccounting = new LinkAccounting();
        Actual baseline = assembleReusedBaseline(reviews.baseline(), request.baselineReviewRef(), frozen, liveGate, permit, charged, linkAccounting);
        FileRef baselineRef = persistView(baseline, liveGate, permit, charged);
        Path legacyRoot = Path.of(reviews.legacy().request().outputRoot()), consumerRoot = Path.of(reviews.consumer().request().outputRoot());
        Map<String, SharedSourceFiles.Witness> baseWitnesses = witnesses(baseline.actualSourceClosure());
        Map<String, SharedSourceFiles.Witness> legacy = linkView(baseline, reviews.legacy(), liveGate, permit, charged, linkAccounting);
        Map<String, SharedSourceFiles.Witness> consumer = linkView(baseline, reviews.consumer(), liveGate, permit, charged, linkAccounting);
        verifyWitnesses(baseWitnesses); verifyWitnesses(legacy); verifyWitnesses(consumer);
        verifyFrozen(frozen);
        int changes = patchView(reviews.legacy(), legacyRoot, legacy, baseWitnesses, consumer, liveGate, permit, charged);
        verifyWitnesses(baseWitnesses); verifyWitnesses(consumer);
        verifyFrozen(frozen);
        changes += patchView(reviews.consumer(), consumerRoot, consumer, baseWitnesses, legacy, liveGate, permit, charged);
        verifyWitnesses(baseWitnesses); verifyWitnesses(legacy); verifyWitnesses(consumer);
        verifyFrozen(frozen);
        requireConstraint(request.legacyConstraint(), legacy, consumer);
        Actual legacyActual = actualFor(reviews.legacy(), request.legacyReviewRef(), outputSources(reviews.legacy(), legacy), permit, charged[0], baseline.startedAtUtc(), null);
        Actual consumerActual = actualFor(reviews.consumer(), request.consumerReviewRef(), outputSources(reviews.consumer(), consumer), permit, charged[0], baseline.startedAtUtc(), null);
        FileRef legacyRef = persistView(legacyActual, liveGate, permit, charged), consumerRef = persistView(consumerActual, liveGate, permit, charged);
        baselineRef.verify();
        FileRef reuseActualRef = persistSource32ReuseActual(frozen, baseWitnesses, legacy, consumer, group, request.machineId(), liveGate, permit, charged);
        FileRef allocationActualRef = persistLinkAccounting(linkAccounting, group, request.machineId(), liveGate, permit, charged);
        List<Source32View> sdkViews = List.of(
                persistSource32View(SourceViewRole.BASELINE, baseline, baselineRef, frozen, liveGate, permit, charged),
                persistSource32View(SourceViewRole.LEGACY, legacyActual, legacyRef, frozen, liveGate, permit, charged),
                persistSource32View(SourceViewRole.CONSUMER, consumerActual, consumerRef, frozen, liveGate, permit, charged));
        PhysicalCensus census = physicalCensus(baseWitnesses, legacy, consumer);
        ViewsActual result = new ViewsActual("xar.sdk-shared-source-views-actual/v2", request.machineId(), Instant.now().toString(), SharedViewStatus.SOURCE_VIEWS_ASSEMBLED_NOT_IMPORTED,
                viewsRequestRef, baselineRef, legacyRef, consumerRef, request.legacyConstraint(), reuseActualRef, allocationActualRef, sdkViews, census, changes, permit.freshStorageEvidence(), forecast, false, false);
        byte[] metadata = JSON.writeValueAsBytes(result);
        if (metadata.length > MAX_METADATA) throw new IOException("shared source physical census exceeds its metadata reservation");
        charged[0] = Math.addExact(charged[0], round(metadata.length, permit.allocationUnitBytes()));
        sharedGuard(liveGate, permit, charged[0]);
        Files.write(group.resolve(".assembly/SHARED-VIEWS-ACTUAL.json"), metadata, StandardOpenOption.CREATE_NEW);
        return result;
    }
    private static FrozenReuseState inspectSource32Reuse(ViewsRequest request, Review baseline) throws IOException {
        Source32Reuse contract = request.source32Reuse();
        requireApprovedSource(baseline.request(), contract.baseFreezeRef()); requireApprovedSource(baseline.request(), contract.exporterSourceRef());
        contract.exporterSourceRef().verify();
        JsonNode value = JSON.readTree(read(contract.baseFreezeRef(), MAX_METADATA));
        if (!"root.ck3.final-sdk-freeze/v1".equals(jsonText(value, "schema")) || !"FINAL_SOURCE_FROZEN".equals(jsonText(value, "status"))
                || !request.machineId().equals(jsonText(value, "machine_id"))) throw new IOException("exact original Source32 source freeze and same machine required");
        Path declaredRoot = Path.of(jsonText(value, "source_root")); SharedSourceFiles.plainAncestors(declaredRoot);
        Path root = declaredRoot.toRealPath();
        Path protectedSdk = Path.of(baseline.request().protectedRoots().stream().filter(item -> item.role() == ProtectedRole.FROZEN_SDK).findFirst().orElseThrow().path()).toRealPath();
        if (!root.equals(protectedSdk)) throw new IOException("reuse root must be the exact explicitly protected immutable SDK");
        List<FrozenSourceRow> rows = frozenRows(value);
        FileRef originalNativeInventory = JSON.treeToValue(value.get("immutable_ntfs_inventory"), FileRef.class);
        requireApprovedSource(baseline.request(), originalNativeInventory);
        Map<String, LegacySourceIdentity> oldNative = originalNativeInventory(originalNativeInventory, root, request.machineId(), rows);
        Map<String, SharedSourceFiles.Witness> originals = new LinkedHashMap<>();
        for (FrozenSourceRow row : rows) {
            SharedSourceFiles.Witness actual = SharedSourceFiles.observe(root.resolve(row.relative()));
            if (!content(actual.source()).equals(row.content())) throw new IOException("an original frozen source leaf differs");
            requireOriginalNativeIdentity(actual, oldNative.get(row.relative()));
            originals.put(row.relative(), actual);
        }
        requireFrozenSet(root, originals);
        Map<String, SharedSourceFiles.Witness> reusable = new LinkedHashMap<>();
        String prefix = baseline.request().sdkRelativeRoot() + "/";
        for (ReviewedSource source : baseline.sourceClosure()) if (source.role() == SourceRole.SDK_SOURCE && source.relativePath().startsWith(prefix)) {
            SharedSourceFiles.Witness old = originals.get(source.relativePath().substring(prefix.length()));
            if (old != null && content(old.source()).equals(source.result())) reusable.put(source.relativePath(), old);
        }
        verifyWitnesses(originals);
        return new FrozenReuseState(contract, root, rows, originalNativeInventory, originals, reusable);
    }
    private record LegacySourceIdentity(String volumeSerialDecimal, String fileIdHex) { }
    /** The old exporter compares only its actual volume32/FileID64 key; links/allocation are snapshots. */
    private static Map<String, LegacySourceIdentity> originalNativeInventory(FileRef reference, Path root, String machine,
                                                                             List<FrozenSourceRow> expected) throws IOException {
        JsonNode value = JSON.readTree(read(reference, MAX_METADATA));
        if (!machine.equals(jsonText(value, "machine_id")) || !Path.of(jsonText(value, "source_root")).toRealPath().equals(root)) throw new IOException("original native inventory source root/machine differs");
        Map<String, FrozenSourceRow> rows = new LinkedHashMap<>(); for (FrozenSourceRow row : expected) rows.put(row.relative(), row);
        JsonNode files = value.get("files"); if (files == null || !files.isArray() || files.size() != rows.size()) throw new IOException("complete original native source inventory required");
        Map<String, LegacySourceIdentity> result = new LinkedHashMap<>();
        for (JsonNode row : files) {
            String relative = jsonText(row, "relative"); FrozenSourceRow content = rows.get(relative); JsonNode id = row.get("file_identity");
            if (content == null || !new Digest(jsonInteger(row, "bytes"), jsonText(row, "sha256")).equals(content.content()) || id == null
                    || jsonInteger(id, "bytes") != content.content().bytes()) throw new IOException("original native source inventory content differs");
            long volume = jsonInteger(id, "volume_serial"); String fileId = jsonText(id, "file_id");
            if (volume > 0xffff_ffffL || !fileId.matches("[0-9a-f]{16}") || result.put(relative, new LegacySourceIdentity(Long.toString(volume), fileId)) != null) throw new IOException("unique exact original volume32/FileID64 required");
        }
        if (!result.keySet().equals(rows.keySet())) throw new IOException("complete original native inventory file set required"); return result;
    }
    private static void requireOriginalNativeIdentity(SharedSourceFiles.Witness actual, LegacySourceIdentity original) throws IOException {
        if (original == null || !actual.nativeFile().legacyVolumeSerialDecimal().equals(original.volumeSerialDecimal())
                || !actual.nativeFile().legacyFileIdHex().equals(original.fileIdHex())) throw new IOException("original frozen volume/FileID identity changed");
    }
    /** The supported old files contract has no link-count/change-time invariant fields to discard. */
    static List<FrozenSourceRow> frozenRows(JsonNode value) throws IOException {
        JsonNode files = value.get("files");
        if (files == null || !files.isArray() || files.isEmpty() || files.size() > MAX_FILES) throw new IOException("complete finite Source32 files array required");
        List<FrozenSourceRow> result = new ArrayList<>(); Set<String> names = new HashSet<>(); long bytes = 0;
        for (JsonNode row : files) {
            Set<String> fields = new HashSet<>(); row.fieldNames().forEachRemaining(fields::add);
            if (!row.isObject() || !fields.equals(Set.of("relative", "bytes", "sha256", "git_blob_sha1", "git_mode"))) throw new IOException("unreviewed frozen identity fields must not be ignored or weakened");
            String relative = jsonText(row, "relative"); ExactSourcePatch.relative(relative);
            String blob = jsonText(row, "git_blob_sha1"), mode = jsonText(row, "git_mode");
            if (!blob.matches("[0-9a-f]{40}") || !Set.of("100644", "100755").contains(mode) || !names.add(relative.toLowerCase(Locale.ROOT))) throw new IOException("ordinary unique frozen source rows required");
            Digest digest = new Digest(jsonInteger(row, "bytes"), jsonText(row, "sha256")); bytes = Math.addExact(bytes, digest.bytes());
            result.add(new FrozenSourceRow(relative, digest, blob, mode));
        }
        if (jsonInteger(value, "source_file_count") != result.size() || jsonInteger(value, "source_bytes") != bytes) throw new IOException("full Source32 file/byte totals differ");
        result.sort(Comparator.comparing(FrozenSourceRow::relative)); return List.copyOf(result);
    }
    private static String jsonText(JsonNode value, String field) throws IOException {
        JsonNode item = value.get(field); if (item == null || !item.isTextual() || item.textValue().isEmpty()) throw new IOException("required exact text field: " + field); return item.textValue();
    }
    private static long jsonInteger(JsonNode value, String field) throws IOException {
        JsonNode item = value.get(field); if (item == null || !item.isIntegralNumber() || !item.canConvertToLong() || item.longValue() < 0) throw new IOException("required exact nonnegative integer field: " + field); return item.longValue();
    }
    private static void requireFrozenSet(Path root, Map<String, SharedSourceFiles.Witness> originals) throws IOException {
        Set<Path> expected = new HashSet<>(); for (SharedSourceFiles.Witness witness : originals.values()) expected.add(Path.of(witness.source().path()));
        Set<Path> actual = new HashSet<>();
        try (var entries = Files.walk(root)) {
            for (Path path : entries.toList()) {
                SharedSourceFiles.plainAncestors(path);
                if (Files.isDirectory(path, LinkOption.NOFOLLOW_LINKS)) continue;
                if (!Files.isRegularFile(path, LinkOption.NOFOLLOW_LINKS)) throw new IOException("ordinary complete immutable source tree required");
                actual.add(path);
            }
        }
        if (!actual.equals(expected)) throw new IOException("original immutable SDK file set grew or changed");
    }
    private static void verifyFrozen(FrozenReuseState frozen) throws IOException {
        frozen.contract().baseFreezeRef().verify(); frozen.contract().exporterSourceRef().verify(); frozen.originalNativeInventory().verify();
        requireFrozenSet(frozen.root(), frozen.originals()); verifyWitnesses(frozen.originals());
    }
    /** Mechanical baseline leaf operation: reuse only proven equal bytes; all other data is private/create-new. */
    static SharedSourceFiles.Witness baselineLeaf(Source source, ReviewedSource expected, Path destination,
                                                  Optional<SharedSourceFiles.Witness> reuse) throws IOException {
        if (!source.overlays().isEmpty() || !expected.relativePath().equals(source.relativePath())) throw new IOException("unpatched exact baseline leaf required");
        if (reuse.isPresent()) {
            SharedSourceFiles.Witness original = reuse.orElseThrow(); SharedSourceFiles.assertUnchanged(original);
            if (!content(original.source()).equals(expected.result())) throw new IOException("immutable reuse content differs from canonical baseline");
            return SharedSourceFiles.link(Path.of(original.source().path()), destination);
        }
        byte[] bytes = read(source.original(), MAX_LEAF);
        if (!Digest.of(bytes).equals(expected.result())) throw new IOException("canonical private baseline bytes changed");
        SharedSourceFiles.plainAncestors(destination); Files.createDirectories(destination.getParent());
        Files.write(destination, bytes, StandardOpenOption.CREATE_NEW); SharedSourceFiles.Witness actual = SharedSourceFiles.observe(destination);
        if (!content(actual.source()).equals(expected.result())) throw new IOException("private canonical baseline readback differs"); return actual;
    }
    private static Actual assembleReusedBaseline(Review review, FileRef reviewRef, FrozenReuseState frozen,
                                                 SharedCapacityGate gate, WritePermit permit, long[] charged, LinkAccounting accounting) throws IOException {
        Path root = Path.of(review.request().outputRoot()); SharedSourceFiles.plainAncestors(root);
        charged[0] = Math.addExact(charged[0], Math.multiplyExact((long) review.quote().directoryCount() + review.quote().sourceFiles(), permit.perDirectoryGuardBytes()));
        sharedGuard(gate, permit, charged[0]); Files.createDirectory(root); Files.createDirectory(root.resolve(".assembly"));
        String started = Instant.now().toString(); Map<String, ReviewedSource> expected = reviewedMap(review); List<OutputSource> outputs = new ArrayList<>();
        for (Source source : review.request().sources()) {
            SharedSourceFiles.Witness reused = frozen.reusableByOutput().get(source.relativePath());
            if (reused == null) charged[0] = Math.addExact(charged[0], round(expected.get(source.relativePath()).result().bytes(), permit.allocationUnitBytes()));
            sharedGuard(gate, permit, charged[0]);
            SharedSourceFiles.Witness actual;
            if (reused == null) actual = baselineLeaf(source, expected.get(source.relativePath()), root.resolve(source.relativePath()), Optional.empty());
            else {
                SharedSourceFiles.assertUnchanged(reused);
                if (!content(reused.source()).equals(expected.get(source.relativePath()).result())) throw new IOException("immutable baseline content differs");
                sharedGuard(gate, permit, Math.addExact(charged[0], permit.allocationUnitBytes()));
                var operation = SharedSourceFiles.linkObserved(Path.of(reused.source().path()), root.resolve(source.relativePath()));
                recordLinkAccounting(accounting, operation, gate, permit, charged); actual = operation.destinationAfter();
            }
            outputs.add(new OutputSource(source.relativePath(), source.role(), actual.source()));
        }
        verifyInputs(review.request()); verifyFrozen(frozen);
        if (!completeSdkInventory(review.request()).equals(review.completeSdkInputInventory())) throw new IOException("canonical SDK inventory changed while the immutable baseline was assembled");
        for (Deployment deployment : review.request().deployments()) ControlBuild.acceptedReceipt(Path.of(deployment.actualBuildReceipt().path()));
        requireExactOutputSet(root, outputs); sharedGuard(gate, permit, charged[0]);
        return actualFor(review, reviewRef, outputs, permit, charged[0], started, null);
    }
    private static FileRef persistSource32ReuseActual(FrozenReuseState frozen, Map<String, SharedSourceFiles.Witness> baseline,
                                                      Map<String, SharedSourceFiles.Witness> legacy, Map<String, SharedSourceFiles.Witness> consumer,
                                                      Path group, String machine, SharedCapacityGate gate, WritePermit permit, long[] charged) throws IOException {
        verifyFrozen(frozen); Map<String, Long> addedLinks = new LinkedHashMap<>();
        for (var view : List.of(baseline, legacy, consumer)) for (var witness : view.values()) addedLinks.merge(witness.nativeFile().identityKey(), 1L, Math::addExact);
        List<FrozenSourceWitness> all = new ArrayList<>();
        for (FrozenSourceRow row : frozen.rows()) {
            SharedSourceFiles.Witness before = frozen.originals().get(row.relative()), after = SharedSourceFiles.observe(Path.of(before.source().path()));
            SharedSourceFiles.assertUnchanged(before);
            long expectedLinks = Math.addExact(before.nativeFile().linkCount(), addedLinks.getOrDefault(before.nativeFile().identityKey(), 0L));
            if (after.nativeFile().linkCount() != expectedLinks) throw new IOException("original source link change is not exactly accounted by the explicit new views");
            all.add(new FrozenSourceWitness(row.relative(), before, after.nativeFile()));
        }
        Map<String, Long> existingAllocation = new LinkedHashMap<>();
        for (var witness : frozen.reusableByOutput().values()) existingAllocation.put(witness.nativeFile().identityKey(), witness.nativeFile().allocatedBytes());
        Source32ReuseActual actual = new Source32ReuseActual("xar.sdk-source32-reuse-actual/v1", machine, Instant.now().toString(), frozen.contract(), frozen.root().toString(), all.size(),
                frozen.reusableByOutput().size(), frozen.reusableByOutput().values().stream().mapToLong(w -> w.source().bytes()).sum(), existingAllocation.values().stream().mapToLong(Long::longValue).sum(), all,
                "Exact reviewed Source32 exporter binds bytes/SHA and volume/FileID; files rows have no link-count/change-time/allocation invariant. All original bytes, volume/FileID128, creation FILETIME and last-write FILETIME are unchanged. Link counts are verified against exactly the newly surviving view aliases; before/after allocation, link count and change FILETIME are retained. Actual positive hardlink allocation changes are separately recorded and charged, without claiming an unobserved resident-promotion cause or credit for released bytes. Existing reused allocation is not new physical credit.");
        byte[] bytes = JSON.writeValueAsBytes(actual); if (bytes.length > MAX_METADATA) throw new IOException("original-source identity readback exceeds its metadata reservation");
        charged[0] = Math.addExact(charged[0], round(bytes.length, permit.allocationUnitBytes())); sharedGuard(gate, permit, charged[0]);
        Path path = group.resolve(".assembly/SOURCE32-REUSE-ACTUAL.json"); Files.write(path, bytes, StandardOpenOption.CREATE_NEW); return FileRef.measure(path);
    }
    private static Source32ReuseActual readSource32ReuseActual(FileRef reference, Source32Reuse expected, String machine) throws IOException {
        Source32ReuseActual actual = JSON.readValue(read(reference, MAX_METADATA), Source32ReuseActual.class);
        if (!actual.machineId().equals(machine) || !actual.contract().equals(expected)) throw new IOException("immutable source reuse provenance differs");
        JsonNode declaredFreeze = JSON.readTree(read(expected.baseFreezeRef(), MAX_METADATA)); expected.exporterSourceRef().verify();
        if (!Path.of(actual.sourceRoot()).toRealPath().equals(Path.of(jsonText(declaredFreeze, "source_root")).toRealPath()) || !jsonText(declaredFreeze, "machine_id").equals(machine)) throw new IOException("immutable source evidence root/machine differs from original freeze");
        Map<String, Digest> declaredFiles = new LinkedHashMap<>(); for (FrozenSourceRow row : frozenRows(declaredFreeze)) declaredFiles.put(row.relative(), row.content());
        FileRef nativeInventoryRef = JSON.treeToValue(declaredFreeze.get("immutable_ntfs_inventory"), FileRef.class);
        Map<String, LegacySourceIdentity> oldNative = originalNativeInventory(nativeInventoryRef, Path.of(actual.sourceRoot()).toRealPath(), machine, frozenRows(declaredFreeze));
        Map<String, SharedSourceFiles.Witness> originals = new LinkedHashMap<>();
        for (FrozenSourceWitness row : actual.allOriginalSources()) {
            Path path = Path.of(actual.sourceRoot()).resolve(row.relativePath());
            if (!path.equals(Path.of(row.before().source().path())) || !content(row.before().source()).equals(declaredFiles.get(row.relativePath()))
                    || originals.put(row.relativePath(), row.before()) != null) throw new IOException("original frozen source witness path/content differs");
            SharedSourceFiles.assertUnchanged(row.before());
            requireOriginalNativeIdentity(row.before(), oldNative.get(row.relativePath()));
            if (!SharedSourceFiles.nativeFile(path).equals(row.after())) throw new IOException("frozen source native metadata changed after shared materialization");
        }
        if (!originals.keySet().equals(declaredFiles.keySet())) throw new IOException("complete original immutable source witnesses required");
        requireFrozenSet(Path.of(actual.sourceRoot()), originals); return actual;
    }
    /** Existing Source32 content and canonical anchor, with only an explicit new physical view address. */
    private static Source32View persistSource32View(SourceViewRole role, Actual actual, FileRef actualRef, FrozenReuseState frozen,
                                                    SharedCapacityGate gate, WritePermit permit, long[] charged) throws IOException {
        JsonNode original = JSON.readTree(read(frozen.contract().baseFreezeRef(), MAX_METADATA));
        requireExactSource32Content(actual, frozen.rows());
        if (!(original instanceof com.fasterxml.jackson.databind.node.ObjectNode object)) throw new IOException("original Source32 object required");
        FileRef anchor = JSON.treeToValue(original.get("source32_canonical_anchor"), FileRef.class); anchor.verify();
        var copy = object.deepCopy();
        copy.put("source_root", actual.sdkRoot()); copy.put("at_utc", Instant.now().toString());
        copy.put("actual_native_loaded", false); copy.put("runtime_admitted", false);
        copy.put("source_view_role", role.name()); copy.put("source_view_content", "EXACT_ORIGINAL_SOURCE32_CONTENT_AND_ANCHOR");
        copy.set("source_view_original_freeze_ref", JSON.valueToTree(frozen.contract().baseFreezeRef()));
        copy.set("source_view_assembly_actual_ref", JSON.valueToTree(actualRef));
        byte[] bytes = JSON.writeValueAsBytes(copy); if (bytes.length > 1_048_576) throw new IOException("SDK view inventory exceeds existing SDK ticket cap");
        charged[0] = Math.addExact(charged[0], round(bytes.length, permit.allocationUnitBytes())); sharedGuard(gate, permit, charged[0]);
        Path path = Path.of(actual.graphRoot()).resolve(".assembly/SDK-SOURCE32-VIEW.json"); Files.write(path, bytes, StandardOpenOption.CREATE_NEW);
        Source32View binding = new Source32View(role, actualRef, actual.sdkRoot(), FileRef.measure(path), anchor);
        verifySource32View(binding, actual, frozen.contract().baseFreezeRef()); return binding;
    }
    private static void requireExactSource32Content(Actual actual, List<FrozenSourceRow> original) throws IOException {
        Map<String, Digest> expected = new LinkedHashMap<>(); for (FrozenSourceRow row : original) expected.put(row.relative(), row.content());
        Map<String, Digest> current = new LinkedHashMap<>(); String prefix = "ck3_autonomous_player/src/";
        for (OutputSource row : actual.actualSourceClosure()) if (row.relativePath().startsWith(prefix)) {
            row.actual().verify(); current.put(row.relativePath().substring(prefix.length()), content(row.actual()));
        }
        if (!current.equals(expected)) throw new IOException("this Source32 view preserves exact original SDK bytes/anchor; changed SDK content requires a separately explicit derived lineage");
    }
    private static void verifySource32View(Source32View binding, Actual actual, FileRef originalRef) throws IOException {
        if (!binding.sdkRoot().equals(actual.sdkRoot()) || !Path.of(binding.sdkFreezeRef().path()).equals(Path.of(actual.graphRoot()).resolve(".assembly/SDK-SOURCE32-VIEW.json"))) throw new IOException("SDK source inventory belongs to a different physical view");
        JsonNode original = JSON.readTree(read(originalRef, MAX_METADATA)), copy = JSON.readTree(read(binding.sdkFreezeRef(), 1_048_576));
        List<FrozenSourceRow> rows = frozenRows(original); requireExactSource32Content(actual, rows);
        if (!rows.equals(frozenRows(copy)) || !actual.machineId().equals(jsonText(copy, "machine_id")) || !binding.sdkRoot().equals(jsonText(copy, "source_root"))
                || !jsonText(original, "business_source_commit").equals(jsonText(copy, "business_source_commit"))
                || !JSON.treeToValue(original.get("source32_canonical_anchor"), FileRef.class).equals(binding.source32AnchorRef())
                || !JSON.treeToValue(copy.get("source32_canonical_anchor"), FileRef.class).equals(binding.source32AnchorRef())
                || !JSON.treeToValue(copy.get("source_view_assembly_actual_ref"), FileRef.class).equals(binding.assemblyActualRef())
                || !JSON.treeToValue(copy.get("source_view_original_freeze_ref"), FileRef.class).equals(originalRef)
                || !binding.role().name().equals(jsonText(copy, "source_view_role"))) throw new IOException("exact Source32 content/anchor/physical-view binding differs");
        binding.source32AnchorRef().verify();
    }
    private static ThreeReviews threeReviews(ViewsRequest request) throws IOException {
        Review baseline = freshReview(request.baselineReviewRef()), legacy = freshReview(request.legacyReviewRef()), consumer = freshReview(request.consumerReviewRef());
        SharedSourceFiles.plainAncestors(Path.of(request.groupRoot()));
        Path group = Path.of(request.groupRoot()).toRealPath(); Set<Path> roots = new HashSet<>();
        for (Review review : List.of(baseline, legacy, consumer)) {
            Path root = Path.of(review.request().outputRoot()).toAbsolutePath().normalize();
            if (!review.machineId().equals(request.machineId()) || !root.getParent().equals(group) || !roots.add(root) || Files.exists(root, LinkOption.NOFOLLOW_LINKS)) throw new IOException("three distinct new same-parent source views required");
        }
        if (baseline.request().sources().stream().anyMatch(source -> !source.overlays().isEmpty())) throw new IOException("shared baseline must contain exact unpatched source inputs");
        Map<String, Source> original = sourceMap(baseline.request());
        for (Review view : List.of(legacy, consumer)) {
            Map<String, Source> selected = sourceMap(view.request());
            if (!selected.keySet().containsAll(original.keySet())) throw new IOException("source view omitted an immutable baseline input");
            for (var row : original.entrySet()) if (!selected.get(row.getKey()).original().equals(row.getValue().original()) || selected.get(row.getKey()).role() != row.getValue().role()) throw new IOException("source view replaced an original base instead of declaring its exact overlays");
            for (Source source : selected.values()) if (!original.containsKey(source.relativePath()) && source.origin() != InputOrigin.STAGED_NEW_SOURCE) throw new IOException("view-only source needs an exact staged input");
        }
        Map<String, ReviewedSource> baseRows = reviewedMap(baseline), legacyRows = reviewedMap(legacy);
        Map<String, ReviewedSource> consumerRows = reviewedMap(consumer);
        if (!legacyRows.keySet().equals(baseRows.keySet())) throw new IOException("pure legacy producer may not add consumer-only sources");
        if (!baseRows.containsKey(request.legacyConstraint().nativeRelativePath()) || !baseRows.containsKey(request.legacyConstraint().fixtureRelativePath())) throw new IOException("explicit native and fixture inputs are required in the shared baseline");
        for (var row : legacyRows.entrySet()) if (!row.getKey().equals(request.legacyConstraint().fixtureRelativePath()) && !row.getValue().result().equals(baseRows.get(row.getKey()).result())) throw new IOException("pure legacy view permits only the necessary fixture repair");
        if (!legacyRows.get(request.legacyConstraint().nativeRelativePath()).result().equals(request.legacyConstraint().originalNative())
                || !legacyRows.get(request.legacyConstraint().fixtureRelativePath()).result().equals(request.legacyConstraint().identicalPatchedFixture())
                || !consumerRows.get(request.legacyConstraint().fixtureRelativePath()).result().equals(request.legacyConstraint().identicalPatchedFixture())) throw new IOException("legacy native or identical two-view fixture requirement differs");
        return new ThreeReviews(baseline, legacy, consumer);
    }
    private static Review freshReview(FileRef reference) throws IOException {
        Review declared = JSON.readValue(read(reference, MAX_METADATA), Review.class);
        Review actual = review(declared.requestRef());
        if (!declared.sourceClosure().equals(actual.sourceClosure()) || !declared.deploymentClosure().equals(actual.deploymentClosure())
                || !declared.completeSdkInputInventory().equals(actual.completeSdkInputInventory()) || !declared.sourceSetSha256().equals(actual.sourceSetSha256()) || !declared.quote().equals(actual.quote())) throw new IOException("shared view exact review is stale");
        return actual;
    }
    private static SharedQuote sharedQuote(ViewsRequest request, ThreeReviews reviews, FrozenReuseState frozen) {
        Map<String, ReviewedSource> baseline = reviewedMap(reviews.baseline()); long changed = 0, all = reviews.baseline().quote().sourceLogicalBytes();
        for (Review view : List.of(reviews.legacy(), reviews.consumer())) {
            all = Math.addExact(all, view.quote().sourceLogicalBytes());
            for (ReviewedSource source : view.sourceClosure()) if (!baseline.containsKey(source.relativePath()) || !baseline.get(source.relativePath()).result().equals(source.result())) changed = Math.addExact(changed, source.result().bytes());
        }
        long reused = frozen.reusableByOutput().values().stream().mapToLong(witness -> witness.source().bytes()).sum();
        return new SharedQuote(request.machineId(), request.groupRoot(), Math.subtractExact(reviews.baseline().quote().sourceLogicalBytes(), reused), frozen.reusableByOutput().size(), reused, changed, all,
                reviews.baseline().sourceClosure().size() + reviews.legacy().sourceClosure().size() + reviews.consumer().sourceClosure().size(),
                1 + reviews.baseline().quote().directoryCount() + reviews.legacy().quote().directoryCount() + reviews.consumer().quote().directoryCount(), 6L * MAX_METADATA + 3L * 1_048_576, request.cumulativePhysicalHardBytes());
    }
    private static long sharedUpper(SharedQuote quote, ThreeReviews reviews, FrozenReuseState frozen, WritePermit permit) {
        long total = Math.addExact(Math.multiplyExact((long) quote.directories() + quote.sourcePathCount(), permit.perDirectoryGuardBytes()), round(quote.metadataHardBytes(), permit.allocationUnitBytes()));
        Map<String, ReviewedSource> baseline = reviewedMap(reviews.baseline());
        for (ReviewedSource source : baseline.values()) if (!frozen.reusableByOutput().containsKey(source.relativePath())) total = Math.addExact(total, round(source.result().bytes(), permit.allocationUnitBytes()));
        for (Review view : List.of(reviews.legacy(), reviews.consumer())) for (ReviewedSource source : view.sourceClosure()) if (!baseline.containsKey(source.relativePath()) || !baseline.get(source.relativePath()).result().equals(source.result())) total = Math.addExact(total, round(source.result().bytes(), permit.allocationUnitBytes()));
        // Reserve one actual-volume allocation unit for each link operation; a larger observed change rejects.
        total = Math.addExact(total, Math.multiplyExact((long) frozen.reusableByOutput().size() + 2L * baseline.size(), permit.allocationUnitBytes()));
        return total;
    }
    private static Map<String, SharedSourceFiles.Witness> linkView(Actual baseline, Review view, SharedCapacityGate gate, WritePermit permit, long[] charged, LinkAccounting accounting) throws IOException {
        Path root = Path.of(view.request().outputRoot()); SharedSourceFiles.plainAncestors(root);
        charged[0] = Math.addExact(charged[0], Math.multiplyExact((long) view.quote().directoryCount() + view.quote().sourceFiles(), permit.perDirectoryGuardBytes())); sharedGuard(gate, permit, charged[0]);
        Files.createDirectory(root); Files.createDirectory(root.resolve(".assembly"));
        Map<String, SharedSourceFiles.Witness> result = new LinkedHashMap<>();
        for (OutputSource source : baseline.actualSourceClosure()) {
            sharedGuard(gate, permit, Math.addExact(charged[0], permit.allocationUnitBytes()));
            var operation = SharedSourceFiles.linkObserved(Path.of(source.actual().path()), root.resolve(source.relativePath()));
            recordLinkAccounting(accounting, operation, gate, permit, charged);
            result.put(source.relativePath(), operation.destinationAfter());
        }
        return result;
    }
    private static void recordLinkAccounting(LinkAccounting accounting, SharedSourceFiles.LinkResult operation,
                                               SharedCapacityGate gate, WritePermit permit, long[] charged) throws IOException {
        long growth = operation.allocatedGrowthBytes();
        if (growth > permit.allocationUnitBytes()) throw new IOException("actual hardlink allocation growth exceeds its pre-reserved native allocation unit: " + operation);
        accounting.operations = Math.addExact(accounting.operations, 1); accounting.growth = Math.addExact(accounting.growth, growth);
        if (operation.before().nativeFile().allocatedBytes() != operation.sourceAfter().nativeFile().allocatedBytes()) accounting.changes.add(operation);
        charged[0] = Math.addExact(charged[0], growth); sharedGuard(gate, permit, charged[0]);
    }
    private static FileRef persistLinkAccounting(LinkAccounting accounting, Path group, String machine,
                                                 SharedCapacityGate gate, WritePermit permit, long[] charged) throws IOException {
        HardlinkAllocationActual actual = new HardlinkAllocationActual("xar.sdk-hardlink-allocation-actual/v1", machine, Instant.now().toString(), accounting.operations, accounting.growth, accounting.changes,
                "Every successful hardlink observes before and after bytes/native identity/mtime and exactly +1 link. Only actual allocation changes are listed; unchanged-allocation operations are counted. Positive allocation deltas are charged once at the operation, negative deltas give no budget credit. No causal resident-promotion inference is claimed.");
        byte[] bytes = JSON.writeValueAsBytes(actual); if (bytes.length > MAX_METADATA) throw new IOException("actual hardlink allocation journal exceeds its reservation");
        charged[0] = Math.addExact(charged[0], round(bytes.length, permit.allocationUnitBytes())); sharedGuard(gate, permit, charged[0]);
        Path path = group.resolve(".assembly/HARDLINK-ALLOCATION-ACTUAL.json"); Files.write(path, bytes, StandardOpenOption.CREATE_NEW); return FileRef.measure(path);
    }
    private static int patchView(Review review, Path root, Map<String, SharedSourceFiles.Witness> current,
                                 Map<String, SharedSourceFiles.Witness> baseline, Map<String, SharedSourceFiles.Witness> sibling,
                                 SharedCapacityGate gate, WritePermit permit, long[] charged) throws IOException {
        int replaced = 0;
        Map<String, ReviewedSource> reviewed = reviewedMap(review);
        for (Source source : review.request().sources()) {
            ReviewedSource desired = reviewed.get(source.relativePath());
            SharedSourceFiles.Witness linked = current.get(source.relativePath());
            if (linked != null && content(linked.source()).equals(desired.result())) continue;
            byte[] complete = material(source);
            if (!Digest.of(complete).equals(desired.result())) throw new IOException("view changed after its exact source review");
            charged[0] = Math.addExact(charged[0], round(complete.length, permit.allocationUnitBytes())); sharedGuard(gate, permit, charged[0]);
            Path destination = root.resolve(source.relativePath());
            SharedSourceFiles.plainAncestors(destination);
            if (linked == null) {
                Files.createDirectories(destination.getParent()); Files.write(destination, complete, StandardOpenOption.CREATE_NEW);
                current.put(source.relativePath(), SharedSourceFiles.observe(destination));
            } else {
                List<SharedSourceFiles.Witness> protectedSources = new ArrayList<>();
                if (baseline.containsKey(source.relativePath())) protectedSources.add(baseline.get(source.relativePath()));
                if (sibling.containsKey(source.relativePath())) protectedSources.add(sibling.get(source.relativePath()));
                current.put(source.relativePath(), SharedSourceFiles.replacePrivate(destination, root.resolve(".assembly"), complete, protectedSources)); replaced++;
            }
            verifyWitnesses(baseline);
            if (sibling.containsKey(source.relativePath())) SharedSourceFiles.assertUnchanged(sibling.get(source.relativePath()));
        }
        requireExactOutputSet(root, outputSources(review, current));
        return replaced;
    }
    private static void requireConstraint(LegacyConstraint constraint, Map<String, SharedSourceFiles.Witness> legacy, Map<String, SharedSourceFiles.Witness> consumer) throws IOException {
        if (!content(legacy.get(constraint.nativeRelativePath()).source()).equals(constraint.originalNative())
                || !content(legacy.get(constraint.fixtureRelativePath()).source()).equals(constraint.identicalPatchedFixture())
                || !content(consumer.get(constraint.fixtureRelativePath()).source()).equals(constraint.identicalPatchedFixture())) throw new IOException("actual two-view native/fixture readback differs");
    }
    private static FileRef persistView(Actual actual, SharedCapacityGate gate, WritePermit permit, long[] charged) throws IOException {
        byte[] bytes = JSON.writeValueAsBytes(actual);
        if (bytes.length > MAX_METADATA) throw new IOException("view actual metadata cap exceeded");
        charged[0] = Math.addExact(charged[0], round(bytes.length, permit.allocationUnitBytes())); sharedGuard(gate, permit, charged[0]);
        Path path = Path.of(actual.graphRoot()).resolve(".assembly/ACTUAL.json"); Files.write(path, bytes, StandardOpenOption.CREATE_NEW); return FileRef.measure(path);
    }
    private static void sharedGuard(SharedCapacityGate gate, WritePermit permit, long consumed) throws IOException {
        if (!Instant.now().isBefore(Instant.parse(permit.expiresAtUtc())) || consumed > permit.allocationUpperLimitBytes()) throw new IOException("shared source view capacity expired/exhausted");
        gate.revalidate(permit, consumed);
    }
    private static Map<String, Source> sourceMap(Request request) { Map<String, Source> result = new LinkedHashMap<>(); for (Source source : request.sources()) result.put(source.relativePath(), source); return result; }
    private static Map<String, ReviewedSource> reviewedMap(Review review) { Map<String, ReviewedSource> result = new LinkedHashMap<>(); for (ReviewedSource source : review.sourceClosure()) result.put(source.relativePath(), source); return result; }
    private static Map<String, SharedSourceFiles.Witness> witnesses(List<OutputSource> sources) throws IOException { Map<String, SharedSourceFiles.Witness> result = new LinkedHashMap<>(); for (OutputSource source : sources) result.put(source.relativePath(), SharedSourceFiles.observe(Path.of(source.actual().path()))); return result; }
    private static void verifyWitnesses(Map<String, SharedSourceFiles.Witness> witnesses) throws IOException { for (SharedSourceFiles.Witness witness : witnesses.values()) SharedSourceFiles.assertUnchanged(witness); }
    private static List<OutputSource> outputSources(Review review, Map<String, SharedSourceFiles.Witness> witnesses) { List<OutputSource> result = new ArrayList<>(); for (ReviewedSource source : review.sourceClosure()) result.add(new OutputSource(source.relativePath(), source.role(), witnesses.get(source.relativePath()).source())); return List.copyOf(result); }
    static PhysicalCensus physicalCensus(Map<String, SharedSourceFiles.Witness> baseline, Map<String, SharedSourceFiles.Witness> legacy, Map<String, SharedSourceFiles.Witness> consumer) throws IOException {
        Map<String, List<SharedSourceFiles.Witness>> unique = new LinkedHashMap<>(); long logical = 0, perPath = 0, physical = 0; int paths = 0;
        for (Map<String, SharedSourceFiles.Witness> view : List.of(baseline, legacy, consumer)) for (SharedSourceFiles.Witness prior : view.values()) {
            SharedSourceFiles.assertUnchanged(prior); SharedSourceFiles.Witness actual = SharedSourceFiles.observe(Path.of(prior.source().path()));
            logical = Math.addExact(logical, actual.source().bytes()); perPath = Math.addExact(perPath, actual.nativeFile().allocatedBytes()); paths++;
            unique.computeIfAbsent(actual.nativeFile().identityKey(), ignored -> new ArrayList<>()).add(actual);
        }
        List<PhysicalFile> files = new ArrayList<>();
        for (List<SharedSourceFiles.Witness> aliases : unique.values()) {
            SharedSourceFiles.Witness first = aliases.getFirst(); physical = Math.addExact(physical, first.nativeFile().allocatedBytes());
            files.add(new PhysicalFile(first.nativeFile(), first.source(), aliases.stream().map(witness -> witness.source().path()).toList()));
        }
        return new PhysicalCensus(logical, paths, files.size(), physical, perPath, Math.subtractExact(perPath, physical), files,
                "Actual source-file allocation from native FILE_STANDARD_INFO, deduplicated by native volume/FileID/creation identity. This excludes .assembly metadata and directories; their upper reservation is charged separately and is not called measured savings.");
    }

    public static FileRef writeReview(Review review, Path destination) throws IOException {
        byte[] bytes = JSON.writeValueAsBytes(review);
        if (bytes.length > MAX_METADATA) throw new IOException("source review metadata exceeds finite cap");
        Files.write(destination, bytes, StandardOpenOption.CREATE_NEW);
        return FileRef.measure(destination);
    }
    /** Prove each owner's explicit patch chain without storing a second source tree. */
    static byte[] standaloneMaterial(Source source, byte[] original, int throughIndex) throws IOException {
        if (throughIndex < 0 || throughIndex >= source.overlays().size()) throw new IOException("exact overlay position required");
        String owner = source.overlays().get(throughIndex).owner();
        byte[] domain = original;
        boolean predecessor = false;
        for (int index = 0; index <= throughIndex; index++) {
            Overlay overlay = source.overlays().get(index);
            if (!overlay.owner().equals(owner)) continue;
            if (overlay.baseMode() == OverlayBase.ORIGINAL_SOURCE) domain = original;
            else if (!predecessor) throw new IOException("same-owner source predecessor is absent");
            if (!Digest.of(domain).equals(overlay.standaloneBase())) throw new IOException("domain standalone source base differs: " + source.relativePath());
            domain = ExactSourcePatch.apply(domain, read(overlay.patchRef(), 1024 * 1024), overlay.syntax(), overlay.patchTarget()).bytes();
            if (!Digest.of(domain).equals(overlay.standaloneResult())) throw new IOException("domain standalone source result differs: " + source.relativePath());
            predecessor = true;
        }
        return domain;
    }
    private static byte[] material(Source source) throws IOException {
        byte[] bytes = read(source.original(), MAX_LEAF);
        for (Overlay overlay : source.overlays()) bytes = ExactSourcePatch.apply(bytes, read(overlay.patchRef(), 1024 * 1024), overlay.syntax(), overlay.patchTarget()).bytes();
        return bytes;
    }
    private static List<DeploymentEvidence> deployments(Request request) throws IOException {
        List<DeploymentEvidence> result = new ArrayList<>(); Set<String> names = new HashSet<>(); boolean host = false;
        for (Deployment deployment : request.deployments()) {
            if (!names.add(deployment.name())) throw new IOException("duplicate external deployment name");
            deployment.actualBuildReceipt().verify();
            ControlBuild.BuildReceipt actual = ControlBuild.acceptedReceipt(Path.of(deployment.actualBuildReceipt().path()));
            if (actual.targetKind() != deployment.targetKind() || !actual.machineId().equals(request.machineId())) throw new IOException("actual deployment kind/machine differs");
            host |= actual.targetKind() == ControlBuild.TargetKind.SERVICE_FAST_JAR;
            result.add(new DeploymentEvidence(deployment.name(), deployment.actualBuildReceipt(), actual.targetKind(), actual.deploymentRoot(),
                    actual.completeDeployment(), actual.producerRuntimePins(), actual.javaExecutableRef(), false));
        }
        if (!host) throw new IOException("one full accepted shared-host deployment closure is required; target/classes is insufficient");
        return List.copyOf(result);
    }
    private static void validateImports(Request request, List<ReviewedSource> sources) throws IOException {
        Set<String> names = new HashSet<>(); Set<String> modules = new HashSet<>();
        for (ReviewedSource source : sources) names.add(source.relativePath());
        for (ImportRoute route : request.importRoutes()) {
            if (!names.contains(route.relativeSource()) || !modules.add(route.module())) throw new IOException("import route source absent or duplicate");
            boolean matches = false;
            for (String root : request.importRoots()) {
                String prefix = root.equals(".") ? "" : root + "/";
                matches |= route.relativeSource().equals(prefix + route.module().replace('.', '/') + ".py")
                        || route.relativeSource().equals(prefix + route.module().replace('.', '/') + "/__init__.py");
            }
            if (!matches) throw new IOException("declared module does not map to its fresh import root: " + route.module());
            if (route.location() == ImportSourceLocation.CANONICAL_ORIGINAL_TEST && sources.stream().noneMatch(source -> source.relativePath().equals(route.relativeSource()) && source.role() == SourceRole.ORIGINAL_CONSUMER_TEST)) throw new IOException("canonical import route must explicitly select an original test input");
        }
        if (request.importRoutes().stream().noneMatch(route -> route.module().equals(request.producerReuse().module()) && route.relativeSource().equals(PRODUCER) && route.requiredBeforeConsumer())) throw new IOException("actual producer import route required");
    }
    private static List<SelectedImportRoute> selectedRoutes(Request request, List<ImportSource> imports) throws IOException {
        List<SelectedImportRoute> result = new ArrayList<>();
        for (ImportRoute route : request.importRoutes()) {
            List<ImportSource> matches = imports.stream().filter(source -> source.relativePath().equals(route.relativeSource()) && source.location() == route.location()).toList();
            if (matches.size() != 1) throw new IOException("selected import route needs one exact physical file: " + route.module());
            result.add(new SelectedImportRoute(route.module(), route.relativeSource(), route.location(), matches.getFirst().reference(), route.requiredBeforeConsumer()));
        }
        return List.copyOf(result);
    }
    private static void validateRoots(Request request) throws IOException {
        SharedSourceFiles.plainAncestors(Path.of(request.outputRoot()));
        SharedSourceFiles.plainAncestors(Path.of(request.canonicalRepository()));
        SharedSourceFiles.plainAncestors(Path.of(request.sdkInputRoot()));
        Path output = Path.of(request.outputRoot()).toAbsolutePath().normalize();
        Path canonical = Path.of(request.canonicalRepository()).toRealPath();
        if (output.startsWith(canonical) || canonical.startsWith(output)) throw new IOException("fresh graph must be outside the canonical source checkout");
        if (!Files.isDirectory(output.getParent())) throw new IOException("live storage owner must first provide the exact existing output parent");
        for (ProtectedRoot protectedRoot : request.protectedRoots()) {
            Path frozen = Path.of(protectedRoot.path()).toRealPath();
            if (output.startsWith(frozen) || frozen.startsWith(output)) throw new IOException("fresh graph overlaps an existing frozen SDK/host/runtime");
        }
        Path sdkInput = Path.of(request.sdkInputRoot()).toRealPath();
        Path frozenSdk = Path.of(request.protectedRoots().stream().filter(root -> root.role() == ProtectedRole.FROZEN_SDK).findFirst().orElseThrow().path()).toRealPath();
        if (!sdkInput.equals(canonical.resolve(request.sdkRelativeRoot()).toRealPath()) && !sdkInput.equals(frozenSdk)) throw new IOException("SDK inventory must use current canonical SDK sources or the explicit frozen SDK source tree");
        for (String inputRoot : request.approvedInputSourceRoots()) {
            Path input = Path.of(inputRoot).toRealPath();
            if (output.startsWith(input) || input.startsWith(output)) throw new IOException("source graph cannot overlap an input source root");
        }
    }
    private record InventoryRow(String relative, long bytes, String sha256) { }
    private static SdkInventory completeSdkInventory(Request request) throws IOException {
        Path sdk = Path.of(request.sdkInputRoot()).toRealPath();
        List<String> cacheNames = List.of("__pycache__", ".mypy_cache", ".pytest_cache");
        List<InventoryRow> rows = new ArrayList<>(); Set<String> found = new HashSet<>();
        long bytes = 0;
        try (var paths = Files.walk(sdk)) {
            for (Path path : paths.toList()) {
                Path relative = sdk.relativize(path); boolean cached = false;
                for (Path part : relative) cached |= cacheNames.contains(part.toString());
                if (cached || Files.isDirectory(path, LinkOption.NOFOLLOW_LINKS)) continue;
                if (Files.isSymbolicLink(path) || !Files.isRegularFile(path, LinkOption.NOFOLLOW_LINKS)) throw new IOException("ordinary complete SDK source file required");
                String name = relative.toString().replace('\\', '/');
                if (name.endsWith(".pyc") || name.endsWith(".pyo")) throw new IOException("compiled Python cache outside an excluded cache directory is not a source leaf");
                FileRef actual = FileRef.measure(path);
                if (!found.add(name.toLowerCase(Locale.ROOT)) || rows.size() >= MAX_FILES || actual.bytes() > MAX_LEAF) throw new IOException("complete SDK inventory aliases or exceeds bounds");
                bytes = Math.addExact(bytes, actual.bytes());
                if (bytes > MAX_OUTPUT) throw new IOException("complete SDK source byte bound exceeded");
                rows.add(new InventoryRow(name, actual.bytes(), actual.sha256()));
            }
        }
        Set<String> requested = new HashSet<>();
        for (Source source : request.sources()) {
            if (source.role() != SourceRole.SDK_SOURCE || source.origin() == InputOrigin.STAGED_NEW_SOURCE) continue;
            String prefix = request.sdkRelativeRoot() + "/";
            if (!source.relativePath().startsWith(prefix)) throw new IOException("SDK source output is outside its one new import root");
            String relative = source.relativePath().substring(prefix.length());
            if (!Path.of(source.original().path()).toRealPath().equals(sdk.resolve(relative).toRealPath()) || !requested.add(relative.toLowerCase(Locale.ROOT))) throw new IOException("SDK source inventory mapping differs");
        }
        if (rows.isEmpty() || !found.equals(requested)) throw new IOException("request omitted or added an original SDK source leaf");
        rows.sort(Comparator.comparing(InventoryRow::relative));
        return new SdkInventory(sdk.toString(), rows.size(), bytes, sha256(JSON.writeValueAsBytes(rows)), cacheNames);
    }
    private static void validateSourceOrigin(Request request, Source source) throws IOException {
        Path actual = Path.of(source.original().path()).toRealPath();
        if (source.origin() == InputOrigin.CURRENT_CANONICAL && !actual.startsWith(Path.of(request.canonicalRepository()).toRealPath())) throw new IOException("canonical source origin differs");
        if (source.origin() == InputOrigin.FROZEN_SDK_SOURCE) {
            Path sdk = Path.of(request.protectedRoots().stream().filter(root -> root.role() == ProtectedRole.FROZEN_SDK).findFirst().orElseThrow().path()).toRealPath();
            if (!actual.startsWith(sdk)) throw new IOException("frozen SDK source origin differs");
        }
        if (source.origin() == InputOrigin.STAGED_NEW_SOURCE && actual.startsWith(Path.of(request.canonicalRepository()).toRealPath())) throw new IOException("new staged source cannot disguise an existing canonical input");
        if (source.role() == SourceRole.ORIGINAL_CONSUMER_TEST && (!actual.startsWith(Path.of(request.canonicalTestRepository()).toRealPath()) || source.relativePath().startsWith(request.sdkRelativeRoot() + "/"))) throw new IOException("original test import must not expose an old production SDK source");
    }
    private static void requireApprovedSource(Request request, FileRef reference) throws IOException {
        SharedSourceFiles.plainAncestors(Path.of(reference.path()));
        Path path = Path.of(reference.path()).toRealPath(); boolean allowed = false;
        for (String inputRoot : request.approvedInputSourceRoots()) allowed |= path.startsWith(Path.of(inputRoot).toRealPath());
        if (!allowed) throw new IOException("source/patch is outside the explicitly approved source roots");
    }
    private static void verifyInputs(Request request) throws IOException {
        for (Source source : request.sources()) {
            source.original().verify();
            for (Overlay overlay : source.overlays()) overlay.patchRef().verify();
        }
    }
    private static void validatePermit(WritePermit permit, Review review) throws IOException {
        if (!permit.machineId().equals(review.machineId()) || !Path.of(permit.exactOutputRoot()).toAbsolutePath().normalize().equals(Path.of(review.request().outputRoot()).toAbsolutePath().normalize())
                || !Instant.now().isBefore(Instant.parse(permit.expiresAtUtc()))) throw new IOException("live graph permit machine/root/time differs");
        permit.freshStorageEvidence().verify();
    }
    private static void guard(CapacityGate gate, WritePermit permit, long consumed) throws IOException {
        if (!Instant.now().isBefore(Instant.parse(permit.expiresAtUtc())) || consumed > permit.allocationUpperLimitBytes()) throw new IOException("source graph capacity lease expired or was exhausted");
        gate.revalidate(permit, consumed);
    }
    private static long allocatedUpper(Quote quote, List<ReviewedSource> sources, WritePermit permit) {
        long total = Math.multiplyExact(quote.directoryCount(), permit.perDirectoryGuardBytes());
        total = Math.addExact(total, round(quote.metadataHardBytes(), permit.allocationUnitBytes()));
        for (ReviewedSource source : sources) total = Math.addExact(total, round(source.result().bytes(), permit.allocationUnitBytes()));
        return total;
    }
    private static long round(long bytes, long unit) { return Math.multiplyExact(Math.floorDiv(Math.addExact(bytes, unit - 1), unit), unit); }
    private static void requireExactOutputSet(Path root, List<OutputSource> outputs) throws IOException {
        Set<Path> expected = new HashSet<>(); for (OutputSource source : outputs) { expected.add(Path.of(source.actual().path())); source.actual().verify(); }
        Set<Path> actual = new HashSet<>();
        try (var paths = Files.walk(root)) {
            for (Path path : paths.filter(Files::isRegularFile).toList()) if (!path.startsWith(root.resolve(".assembly"))) actual.add(path);
        }
        if (!actual.equals(expected)) throw new IOException("fresh source graph has missing or unrecorded files");
    }
    private record DigestRow(String relativePath, Digest result) { }
    private static String sourceSetDigest(List<ReviewedSource> sources) throws IOException {
        List<DigestRow> rows = sources.stream().sorted(Comparator.comparing(ReviewedSource::relativePath)).map(row -> new DigestRow(row.relativePath(), row.result())).toList();
        return sha256(JSON.writeValueAsBytes(rows));
    }
    private static byte[] read(FileRef reference, int maximum) throws IOException {
        if (reference.bytes() > maximum || Files.size(Path.of(reference.path())) > maximum) throw new IOException("finite source assembly input exceeded");
        byte[] bytes = Files.readAllBytes(Path.of(reference.path()));
        if (bytes.length > maximum || bytes.length != reference.bytes() || !sha256(bytes).equals(reference.sha256())) throw new IOException("exact source/patch/reference changed");
        return bytes;
    }
    private static Digest content(FileRef reference) { return new Digest(reference.bytes(), reference.sha256()); }
    private static Path absolute(String value) { if (value == null || !Path.of(value).isAbsolute()) throw new IllegalArgumentException("absolute source assembly path required"); return Path.of(value).toAbsolutePath().normalize(); }
    private static String sha256(byte[] bytes) {
        try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)); }
        catch (NoSuchAlgorithmException error) { throw new IllegalStateException(error); }
    }
}
