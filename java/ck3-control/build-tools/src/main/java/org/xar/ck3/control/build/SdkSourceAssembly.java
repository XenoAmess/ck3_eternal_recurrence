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

    public enum SourceRole { SDK_SOURCE, SHARED_TRANSPORT, ORIGINAL_CONSUMER_TEST, STAGED_CONSUMER_TEST, CONSUMER_SOURCE, PRODUCER, SUPPORT_RESOURCE }
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
            if ((role == SourceRole.STAGED_CONSUMER_TEST || role == SourceRole.CONSUMER_SOURCE) && origin != InputOrigin.STAGED_NEW_SOURCE) throw new IllegalArgumentException("staged consumers need explicit staged source provenance");
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
        return review(request, requestRef, actualMachineId, false);
    }
    private static Review review(Request request, FileRef requestRef, String actualMachineId, boolean referenceOnly) throws IOException {
        if (!request.machineId().equals(actualMachineId)) throw new IOException("source assembly machine differs");
        if (!referenceOnly && !readRequest(requestRef).equals(request)) throw new IOException("in-memory request differs from its exact JSON reference");
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
        List<DeploymentEvidence> deployments = referenceOnly ? List.of() : deployments(request);
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
                FileRef actual = exactLeaf(bytes, expected.result(), destination).source();
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

    public static final String VIEWS_SCHEMA = "xar.sdk-shared-source-views-request/v3";
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
                               LegacyConstraint legacyConstraint, Source32Reuse source32Reuse,
                               SdkDerivedSource32.SourcePurpose consumerSourcePurpose, SdkDerivedSource32.NativeDriverIntent consumerNativeDriverIntent,
                               long cumulativePhysicalHardBytes) {
        public ViewsRequest {
            absolute(groupRoot);
            if (!VIEWS_SCHEMA.equals(schema) || machineId == null || machineId.isBlank() || baselineReviewRef == null || legacyReviewRef == null || consumerReviewRef == null
                    || legacyConstraint == null || source32Reuse == null || consumerSourcePurpose == null || consumerNativeDriverIntent == null || cumulativePhysicalHardBytes <= 0 || cumulativePhysicalHardBytes > MAX_OUTPUT) throw new IllegalArgumentException("exact three-review shared view and immutable-reuse request required");
            if (consumerSourcePurpose == SdkDerivedSource32.SourcePurpose.PARENT_NATIVE_UNCHANGED
                    && !consumerNativeDriverIntent.parentContent().equals(consumerNativeDriverIntent.selectedContent()))
                throw new IllegalArgumentException("Parent-native source purpose requires unchanged exact native bytes");
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
            if (!"xar.sdk-shared-source-views-actual/v3".equals(schema) || machineId == null || machineId.isBlank() || status == null
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
            verifySource32View(binding, viewActuals.get(binding.role()), request.source32Reuse().baseFreezeRef(), request.consumerSourcePurpose(), request.consumerNativeDriverIntent());
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
                persistSource32View(SourceViewRole.BASELINE, baseline, baselineRef, frozen, request, liveGate, permit, charged),
                persistSource32View(SourceViewRole.LEGACY, legacyActual, legacyRef, frozen, request, liveGate, permit, charged),
                persistSource32View(SourceViewRole.CONSUMER, consumerActual, consumerRef, frozen, request, liveGate, permit, charged));
        PhysicalCensus census = physicalCensus(baseWitnesses, legacy, consumer);
        ViewsActual result = new ViewsActual("xar.sdk-shared-source-views-actual/v3", request.machineId(), Instant.now().toString(), SharedViewStatus.SOURCE_VIEWS_ASSEMBLED_NOT_IMPORTED,
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
        Map<String, SharedSourceFiles.Witness> reusable = new LinkedHashMap<>();
        String prefix = baseline.request().sdkRelativeRoot() + "/";
        for (ReviewedSource source : baseline.sourceClosure()) if (source.role() == SourceRole.SDK_SOURCE && source.relativePath().startsWith(prefix)) {
            SharedSourceFiles.Witness old = originals.get(source.relativePath().substring(prefix.length()));
            if (old != null && content(old.source()).equals(source.result())) reusable.put(source.relativePath(), old);
        }
        requireCurrentFrozenSources(root, originals);
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
    static void requireFrozenSet(Path root, Map<String, SharedSourceFiles.Witness> originals) throws IOException {
        Set<Path> expected = new HashSet<>(); for (SharedSourceFiles.Witness witness : originals.values()) expected.add(Path.of(witness.source().path()));
        Set<Path> actual = new HashSet<>();
        try (var entries = Files.walk(root)) {
            for (Path path : entries.toList()) {
                if (sdkSourceLeaf(root, path)) actual.add(path);
            }
        }
        if (!actual.equals(expected)) throw new IOException("original immutable SDK file set grew or changed");
    }
    static void requireCurrentFrozenSources(Path root, Map<String, SharedSourceFiles.Witness> originals) throws IOException {
        requireFrozenSet(root, originals); verifyWitnesses(originals);
    }
    private static void verifyFrozen(FrozenReuseState frozen) throws IOException {
        frozen.contract().baseFreezeRef().verify(); frozen.contract().exporterSourceRef().verify(); frozen.originalNativeInventory().verify();
        requireCurrentFrozenSources(frozen.root(), frozen.originals());
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
        return exactLeaf(bytes, expected.result(), destination);
    }
    static SharedSourceFiles.Witness exactLeaf(byte[] bytes, Digest expected, Path destination) throws IOException {
        if (!Digest.of(bytes).equals(expected)) throw new IOException("exact leaf source digest differs");
        SharedSourceFiles.plainAncestors(destination); Files.createDirectories(destination.getParent());
        Files.write(destination, bytes, StandardOpenOption.CREATE_NEW);
        SharedSourceFiles.Witness actual = SharedSourceFiles.observe(destination);
        if (!content(actual.source()).equals(expected)) throw new IOException("exact leaf write readback differs");
        return actual;
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
    private static Source32View persistSource32View(SourceViewRole role, Actual actual, FileRef actualRef, FrozenReuseState frozen, ViewsRequest request,
                                                    SharedCapacityGate gate, WritePermit permit, long[] charged) throws IOException {
        JsonNode original = JSON.readTree(read(frozen.contract().baseFreezeRef(), MAX_METADATA));
        boolean derived = role == SourceViewRole.CONSUMER && !sameSource32Content(actual, frozen.rows());
        if (!derived) requireExactSource32Content(actual, frozen.rows());
        if (!(original instanceof com.fasterxml.jackson.databind.node.ObjectNode object)) throw new IOException("original Source32 object required");
        FileRef anchor = JSON.treeToValue(original.get("source32_canonical_anchor"), FileRef.class); anchor.verify();
        var copy = object.deepCopy();
        copy.put("source_root", actual.sdkRoot()); copy.put("at_utc", Instant.now().toString());
        copy.put("actual_native_loaded", false); copy.put("runtime_admitted", false);
        copy.put("source_view_role", role.name()); copy.put("source_view_content", "EXACT_ORIGINAL_SOURCE32_CONTENT_AND_ANCHOR");
        copy.set("source_view_original_freeze_ref", JSON.valueToTree(frozen.contract().baseFreezeRef()));
        copy.set("source_view_assembly_actual_ref", JSON.valueToTree(actualRef));
        byte[] bytes = derived ? JSON.writeValueAsBytes(SdkDerivedSource32.derive(actual, actualRef, frozen.contract().baseFreezeRef(), request.consumerSourcePurpose(), request.consumerNativeDriverIntent())) : JSON.writeValueAsBytes(copy);
        if (bytes.length > 1_048_576) throw new IOException("SDK view inventory exceeds existing SDK ticket cap");
        charged[0] = Math.addExact(charged[0], round(bytes.length, permit.allocationUnitBytes())); sharedGuard(gate, permit, charged[0]);
        Path path = Path.of(actual.graphRoot()).resolve(".assembly/SDK-SOURCE32-VIEW.json"); Files.write(path, bytes, StandardOpenOption.CREATE_NEW);
        Source32View binding = new Source32View(role, actualRef, actual.sdkRoot(), FileRef.measure(path), anchor);
        verifySource32View(binding, actual, frozen.contract().baseFreezeRef(), request.consumerSourcePurpose(), request.consumerNativeDriverIntent()); return binding;
    }
    private static void requireExactSource32Content(Actual actual, List<FrozenSourceRow> original) throws IOException {
        if (!sameSource32Content(actual, original)) throw new IOException("this Source32 view preserves exact original SDK bytes/anchor; changed SDK content requires a separately explicit derived lineage");
    }
    private static boolean sameSource32Content(Actual actual, List<FrozenSourceRow> original) throws IOException {
        Map<String, Digest> expected = new LinkedHashMap<>(); for (FrozenSourceRow row : original) expected.put(row.relative(), row.content());
        Map<String, Digest> current = new LinkedHashMap<>(); String prefix = "ck3_autonomous_player/src/";
        for (OutputSource row : actual.actualSourceClosure()) if (row.relativePath().startsWith(prefix)) {
            row.actual().verify(); current.put(row.relativePath().substring(prefix.length()), content(row.actual()));
        }
        return current.equals(expected);
    }
    private static void verifySource32View(Source32View binding, Actual actual, FileRef originalRef, SdkDerivedSource32.SourcePurpose purpose, SdkDerivedSource32.NativeDriverIntent nativeIntent) throws IOException {
        if (!binding.sdkRoot().equals(actual.sdkRoot()) || !Path.of(binding.sdkFreezeRef().path()).equals(Path.of(actual.graphRoot()).resolve(".assembly/SDK-SOURCE32-VIEW.json"))) throw new IOException("SDK source inventory belongs to a different physical view");
        JsonNode original = JSON.readTree(read(originalRef, MAX_METADATA)), copy = JSON.readTree(read(binding.sdkFreezeRef(), 1_048_576));
        if (SdkDerivedSource32.SCHEMA.equals(jsonText(copy, "schema"))) {
            if (binding.role() != SourceViewRole.CONSUMER || !JSON.treeToValue(original.get("source32_canonical_anchor"), FileRef.class).equals(binding.source32AnchorRef())) throw new IOException("only consumer may declare a derived SDK with its real parent anchor");
            var declared = SdkDerivedSource32.read(binding.sdkFreezeRef());
            if (declared.sourcePurpose() != purpose || !declared.nativeDriverIntent().equals(nativeIntent)) throw new IOException("Derived source purpose or exact selected native intent differs from the shared request");
            SdkDerivedSource32.verify(binding.sdkFreezeRef(), actual, binding.assemblyActualRef(), originalRef); binding.source32AnchorRef().verify(); return;
        }
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
        Digest nativeBefore = baseRows.get(request.legacyConstraint().nativeRelativePath()).result();
        Digest nativeSelected = consumerRows.get(request.legacyConstraint().nativeRelativePath()).result();
        if (!nativeBefore.equals(request.consumerNativeDriverIntent().parentContent()) || !nativeSelected.equals(request.consumerNativeDriverIntent().selectedContent()))
            throw new IOException("Explicit current native source intent differs from the actual reviewed baseline or selected consumer");
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
    private static final List<String> SDK_CACHE_DIRECTORIES = List.of("__pycache__", ".mypy_cache", ".pytest_cache");
    /** One source domain for original inventory and frozen reuse. Excluded entries still pass ordinary/native path checks. */
    private static boolean sdkSourceLeaf(Path root, Path path) throws IOException {
        if (!path.startsWith(root)) throw new IOException("SDK source entry escaped its original root");
        SharedSourceFiles.plainAncestors(path);
        var attributes = Files.readAttributes(path, java.nio.file.attribute.BasicFileAttributes.class, LinkOption.NOFOLLOW_LINKS);
        if (attributes.isSymbolicLink() || (!attributes.isDirectory() && !attributes.isRegularFile())) throw new IOException("ordinary non-reparse SDK source entry required");
        if (attributes.isDirectory()) return false;
        Path relative = root.relativize(path);
        for (Path part : relative) if (SDK_CACHE_DIRECTORIES.contains(part.toString())) return false;
        String name = relative.toString().replace('\\', '/');
        if (name.endsWith(".pyc") || name.endsWith(".pyo")) throw new IOException("compiled Python cache outside an excluded cache directory is not a source leaf");
        return true;
    }
    private record InventoryRow(String relative, long bytes, String sha256) { }
    static SdkInventory completeSdkInventory(Request request) throws IOException {
        Path sdk = Path.of(request.sdkInputRoot()).toRealPath();
        List<String> cacheNames = SDK_CACHE_DIRECTORIES;
        List<InventoryRow> rows = new ArrayList<>(); Set<String> found = new HashSet<>();
        long bytes = 0;
        try (var paths = Files.walk(sdk)) {
            for (Path path : paths.toList()) {
                if (!sdkSourceLeaf(sdk, path)) continue;
                Path relative = sdk.relativize(path);
                String name = relative.toString().replace('\\', '/');
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
    static void validateSourceOrigin(Request request, Source source) throws IOException {
        Path actual = Path.of(source.original().path()).toRealPath();
        if (source.origin() == InputOrigin.CURRENT_CANONICAL && !actual.startsWith(Path.of(request.canonicalRepository()).toRealPath())) throw new IOException("canonical source origin differs");
        if (source.origin() == InputOrigin.FROZEN_SDK_SOURCE) {
            Path sdk = Path.of(request.protectedRoots().stream().filter(root -> root.role() == ProtectedRole.FROZEN_SDK).findFirst().orElseThrow().path()).toRealPath();
            if (!actual.startsWith(sdk)) throw new IOException("frozen SDK source origin differs");
        }
        if (source.origin() == InputOrigin.STAGED_NEW_SOURCE && actual.startsWith(Path.of(request.canonicalRepository()).toRealPath())) throw new IOException("new staged source cannot disguise an existing canonical input");
        if (source.role() == SourceRole.ORIGINAL_CONSUMER_TEST && (!actual.startsWith(Path.of(request.canonicalTestRepository()).toRealPath()) || source.relativePath().startsWith(request.sdkRelativeRoot() + "/"))) throw new IOException("original test import must not expose an old production SDK source");
        if ((source.role() == SourceRole.STAGED_CONSUMER_TEST || source.role() == SourceRole.CONSUMER_SOURCE) && (source.origin() != InputOrigin.STAGED_NEW_SOURCE || source.relativePath().startsWith(request.sdkRelativeRoot() + "/") || actual.startsWith(Path.of(request.canonicalTestRepository()).toRealPath()))) throw new IOException("staged consumers require a separate exact staged input outside the original test repository and SDK production root");
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
  /** Source data for original-reference captures. It can never be read as an ordinary SDK Actual. */
  public enum ReferencePurpose { REFERENCE_ORACLE_ONLY, LEGACY_REFERENCE_ONLY }
  public enum ReferenceInputKind { ORIGINAL_PRODUCER_SOURCE, COMPATIBILITY_ADAPTER }
  public record ReferenceSelection(String relativePath, ReferenceInputKind kind, FileRef parentSourceRef,
                  FileRef selectedSourceRef, FileRef auditRef) {
    public ReferenceSelection {
      ExactSourcePatch.relative(relativePath); Objects.requireNonNull(kind);
      if (kind == ReferenceInputKind.ORIGINAL_PRODUCER_SOURCE) Objects.requireNonNull(parentSourceRef);
      Objects.requireNonNull(selectedSourceRef); Objects.requireNonNull(auditRef);
    }
  }
  public record ReferenceRequest(String schema, String machineId, String ownerTask, ReferencePurpose purpose,
                 FileRef sourceTemplateRef, FileRef qualifiedToolsBuildRef, FileRef constructionRequestRef, String outputRoot,
                 List<String> approvedInputSourceRoots, List<Source> additionalSources,
                 List<ReferenceSelection> selections, List<ImportRoute> additionalImportRoutes) {
    public ReferenceRequest {
      if (!"xar.sdk-reference-request/v1".equals(schema) || machineId == null || machineId.isBlank()
          || ownerTask == null || !ownerTask.matches("/root/[a-z0-9_/-]+")
          || (purpose == ReferencePurpose.REFERENCE_ORACLE_ONLY) != (constructionRequestRef != null))
        throw new IllegalArgumentException("explicit reference-only source request required");
      Objects.requireNonNull(purpose); Objects.requireNonNull(sourceTemplateRef); Objects.requireNonNull(qualifiedToolsBuildRef);
      absolute(outputRoot); approvedInputSourceRoots = List.copyOf(approvedInputSourceRoots);
      additionalSources = List.copyOf(additionalSources); selections = List.copyOf(selections);
      additionalImportRoutes = List.copyOf(additionalImportRoutes);
      if (approvedInputSourceRoots.isEmpty() || approvedInputSourceRoots.size() > 32
          || additionalSources.size() > 128 || selections.size() > 32 || additionalImportRoutes.size() > 128)
        throw new IllegalArgumentException("bounded explicit reference inputs required");
    }
  }
  public record ReferenceReview(String schema, String machineId, String observedAtUtc, FileRef requestRef,
                 ReferenceRequest request, Review parentSourceReview, Quote quote,
                 String selectedSourceSetSha256) {
    public ReferenceReview {
      if (!"xar.sdk-reference-review/v1".equals(schema)) throw new IllegalArgumentException("reference review schema");
      Instant.parse(observedAtUtc); Objects.requireNonNull(requestRef); Objects.requireNonNull(request);
      Objects.requireNonNull(parentSourceReview); Objects.requireNonNull(quote);
      if (!machineId.equals(request.machineId()) || !parentSourceReview.deploymentClosure().isEmpty()
          || !selectedSourceSetSha256.matches("[0-9a-f]{64}"))
        throw new IllegalArgumentException("reference review cannot contain runtime deployment qualification");
    }
  }
  public record ReferenceActual(String schema, String machineId, ReferencePurpose purpose, String observedAtUtc,
                 String status, FileRef reviewRef, String graphRoot, String sdkRoot,
                 List<OutputSource> actualSourceClosure, List<String> importRoots, List<SelectedImportRoute> selectedImportRoutes,
                 String sourceSetSha256, FileRef storageEvidence, long chargedAllocationUpperBytes,
                 boolean actualImportsObserved, boolean runtimeQualified, boolean prepared) {
    public ReferenceActual {
      if (!"xar.sdk-reference-actual/v1".equals(schema) || !"REFERENCE_INPUTS_ASSEMBLED_NOT_IMPORTED".equals(status)
          || actualImportsObserved || runtimeQualified || prepared || chargedAllocationUpperBytes <= 0
          || !sourceSetSha256.matches("[0-9a-f]{64}"))
        throw new IllegalArgumentException("reference inputs grant no import, runtime or Prepared qualification");
      Objects.requireNonNull(purpose); Objects.requireNonNull(reviewRef); Objects.requireNonNull(storageEvidence);
      absolute(graphRoot); absolute(sdkRoot); Instant.parse(observedAtUtc);
      actualSourceClosure = List.copyOf(actualSourceClosure); importRoots = List.copyOf(importRoots); selectedImportRoutes = List.copyOf(selectedImportRoutes);
    }
  }
  public interface ReferenceCapacityGate {
    WritePermit acquire(ReferenceReview actualReview) throws IOException;
    void revalidate(WritePermit permit, long consumedAllocationUpperBytes) throws IOException;
  }
  public static ReferenceReview reviewReference(FileRef requestRef) throws IOException {
    ReferenceRequest reference = readReferenceRequest(requestRef);
    String machine = WindowsJobProcess.currentMachineId();
    if (!machine.equals(reference.machineId())) throw new IOException("reference request belongs to another machine");
    ControlBuild.BuildReceipt tools = ControlBuild.verifiedCompletedReceipt(reference.qualifiedToolsBuildRef());
    if (tools.targetKind() != ControlBuild.TargetKind.BUILD_TOOLS_RUNTIME)
      throw new IOException("reference source writer requires a completely qualified tools runtime");
    if (!ControlBuild.producerClosure().equals(tools.completeDeployment())
        || !SdkSourceAssembly.class.getProtectionDomain().getCodeSource().getLocation().equals(ControlBuild.class.getProtectionDomain().getCodeSource().getLocation()))
      throw new IOException("reference writer must execute the exact qualified tools deployment without class shadowing");
    Request template = readRequest(reference.sourceTemplateRef());
    if (!template.machineId().equals(machine)) throw new IOException("reference template machine differs");
    List<Source> sources = new ArrayList<>(template.sources()); sources.addAll(reference.additionalSources());
    List<ImportRoute> routes = new ArrayList<>(template.importRoutes()); routes.addAll(reference.additionalImportRoutes());
    Request contract = new Request(REQUEST_SCHEMA, machine, template.canonicalRepository(), template.canonicalCommit(),
        template.canonicalTestRepository(), reference.outputRoot(), template.sdkInputRoot(), template.sdkRelativeRoot(),
        template.importRoots(), reference.approvedInputSourceRoots(), template.protectedRoots(), sources, routes,
        template.deployments(), template.producerReuse(), template.outputHardBytes());
    for (ImportRoute route : routes) if (route.location() != ImportSourceLocation.FRESH_GRAPH)
      throw new IOException("reference import routes must select their physical fresh graph");
    if (reference.purpose() == ReferencePurpose.LEGACY_REFERENCE_ONLY) {
      if (!reference.selections().isEmpty()
          || !absolute(contract.sdkInputRoot()).equals(absolute(contract.protectedRoots().stream().filter(row -> row.role() == ProtectedRole.FROZEN_SDK).findFirst().orElseThrow().path()))
          || contract.sources().stream().anyMatch(row -> row.role() == SourceRole.SDK_SOURCE && (!row.overlays().isEmpty() || row.origin() != InputOrigin.FROZEN_SDK_SOURCE))
          || reference.additionalSources().stream().anyMatch(row -> row.role() == SourceRole.SDK_SOURCE || row.role() == SourceRole.STAGED_CONSUMER_TEST || row.role() == SourceRole.CONSUMER_SOURCE || !row.overlays().isEmpty()))
        throw new IOException("legacy reference preserves the original frozen SDK and original consumer sources");
    }
    // This private branch shares the full source/root/patch/import checks; it never accepts a Host.
    Review parent = review(contract, requestRef, machine, true);
    if (reference.purpose() == ReferencePurpose.LEGACY_REFERENCE_ONLY && parent.completeSdkInputInventory().originalFiles() != 1468)
      throw new IOException("legacy Source32 reference requires the exact complete 1468-source domain");
    Map<String, Source> byPath = new LinkedHashMap<>(); for (Source source : contract.sources()) byPath.put(source.relativePath(), source);
    Map<String, ReferenceSelection> selected = new LinkedHashMap<>();
    for (ReferenceSelection selection : reference.selections()) {
      Source source = byPath.get(selection.relativePath());
      boolean absent=template.sources().stream().noneMatch(row->row.relativePath().equals(selection.relativePath()));
      verifyReferenceParent(selection,source,absent);
      if(selected.put(selection.relativePath(),selection)!=null)throw new IOException("duplicate reference selection");
      requireApprovedSource(contract, selection.selectedSourceRef()); requireApprovedSource(contract, selection.auditRef());
      read(selection.selectedSourceRef(), MAX_LEAF); selection.auditRef().verify();
    }
    validateReferenceAudit(reference, parent);
    List<DigestRow> rows = new ArrayList<>(); long total = 0;
    for (ReviewedSource source : parent.sourceClosure()) {
      ReferenceSelection selection = selected.get(source.relativePath());
      Digest digest = selection == null ? source.result() : content(selection.selectedSourceRef());
      rows.add(new DigestRow(source.relativePath(), digest)); total = Math.addExact(total, digest.bytes());
    }
    Quote quote = new Quote(total, MAX_METADATA, rows.size(), parent.quote().directoryCount(), contract.outputHardBytes());
    requestRef.verify(); reference.sourceTemplateRef().verify();
    return new ReferenceReview("xar.sdk-reference-review/v1", machine, Instant.now().toString(), requestRef, reference,
        parent, quote, sha256(JSON.writeValueAsBytes(rows)));
  }
  public static FileRef writeReferenceReview(ReferenceReview review, Path output) throws IOException {
    SharedSourceFiles.plainAncestors(output);
    byte[] bytes = JSON.writerWithDefaultPrettyPrinter().writeValueAsBytes(review);
    if (bytes.length > MAX_METADATA) throw new IOException("reference review metadata bound exceeded");
    Files.write(output, bytes, StandardOpenOption.CREATE_NEW); return FileRef.measure(output);
  }
  public static ReferenceActual assembleReference(FileRef reviewRef, ReferenceCapacityGate gate) throws IOException {
    ReferenceReview declared = JSON.readValue(read(reviewRef, MAX_METADATA), ReferenceReview.class);
    ReferenceReview fresh = reviewReference(declared.requestRef());
    if (!fresh.request().equals(declared.request()) || !fresh.parentSourceReview().sourceClosure().equals(declared.parentSourceReview().sourceClosure())
        || !fresh.parentSourceReview().completeSdkInputInventory().equals(declared.parentSourceReview().completeSdkInputInventory())
        || !fresh.quote().equals(declared.quote()) || !fresh.selectedSourceSetSha256().equals(declared.selectedSourceSetSha256()))
      throw new IOException("reference sources changed after their exact review");
    WritePermit permit = Objects.requireNonNull(gate).acquire(fresh);
    Path root = absolute(fresh.request().outputRoot());
    if (!permit.machineId().equals(fresh.machineId()) || !absolute(permit.exactOutputRoot()).equals(root)
        || Files.exists(root, LinkOption.NOFOLLOW_LINKS)) throw new IOException("fresh exact reference output permit required");
    long charged = Math.addExact(round(MAX_METADATA, permit.allocationUnitBytes()),
        Math.multiplyExact(fresh.quote().directoryCount(), permit.perDirectoryGuardBytes()));
    for (ReviewedSource source : fresh.parentSourceReview().sourceClosure())
      charged = Math.addExact(charged, round(referenceDigest(fresh, source).bytes(), permit.allocationUnitBytes()));
    referenceGuard(gate, permit, charged); Files.createDirectory(root); Files.createDirectory(root.resolve(".assembly"));
    List<OutputSource> outputs = new ArrayList<>();
    for (Source source : fresh.parentSourceReview().request().sources().stream().sorted(Comparator.comparing(Source::relativePath)).toList()) {
      ReferenceSelection selection = fresh.request().selections().stream().filter(row -> row.relativePath().equals(source.relativePath())).findFirst().orElse(null);
      byte[] bytes = selection == null ? material(source) : read(selection.selectedSourceRef(), MAX_LEAF);
      ReviewedSource parent = fresh.parentSourceReview().sourceClosure().stream().filter(row -> row.relativePath().equals(source.relativePath())).findFirst().orElseThrow();
      if (!Digest.of(bytes).equals(referenceDigest(fresh, parent))) throw new IOException("reference source drift before write");
      referenceGuard(gate, permit, charged);
      Path destination = root.resolve(source.relativePath());
      FileRef actual = exactLeaf(bytes, referenceDigest(fresh, parent), destination).source();
      outputs.add(new OutputSource(source.relativePath(), source.role(), actual));
    }
    ReferenceReview post = reviewReference(fresh.requestRef());
    if (!post.selectedSourceSetSha256().equals(fresh.selectedSourceSetSha256())
        || !post.parentSourceReview().sourceClosure().equals(fresh.parentSourceReview().sourceClosure()))
      throw new IOException("reference source postcheck differs; partial output is not reusable");
    requireExactOutputSet(root, outputs); List<SelectedImportRoute> routes = new ArrayList<>();
    for (ImportRoute route : fresh.parentSourceReview().request().importRoutes()) {
      if (route.location() != ImportSourceLocation.FRESH_GRAPH) throw new IOException("reference routes must use the selected physical graph");
      OutputSource source = outputs.stream().filter(row -> row.relativePath().equals(route.relativeSource())).findFirst().orElseThrow();
      routes.add(new SelectedImportRoute(route.module(), route.relativeSource(), route.location(), source.actual(), route.requiredBeforeConsumer()));
    }
    ReferenceActual actual = new ReferenceActual("xar.sdk-reference-actual/v1", fresh.machineId(), fresh.request().purpose(),
        Instant.now().toString(), "REFERENCE_INPUTS_ASSEMBLED_NOT_IMPORTED", reviewRef, root.toString(),
        root.resolve(fresh.parentSourceReview().request().sdkRelativeRoot()).toString(), outputs,
        fresh.parentSourceReview().request().importRoots().stream().map(row -> row.equals(".") ? root.toString() : root.resolve(row).normalize().toString()).toList(), routes,
        fresh.selectedSourceSetSha256(), permit.freshStorageEvidence(), charged, false, false, false);
    byte[] receipt = JSON.writerWithDefaultPrettyPrinter().writeValueAsBytes(actual);
    if (receipt.length > MAX_METADATA) throw new IOException("reference actual metadata bound exceeded");
    referenceGuard(gate, permit, charged);
    Files.write(root.resolve(".assembly/REFERENCE-ACTUAL.json"), receipt, StandardOpenOption.CREATE_NEW);
    return readReferenceActual(FileRef.measure(root.resolve(".assembly/REFERENCE-ACTUAL.json")));
  }
  public static ReferenceActual readReferenceActual(FileRef reference) throws IOException {
    ReferenceActual actual = JSON.readValue(read(reference, MAX_METADATA), ReferenceActual.class);
    Path root = absolute(actual.graphRoot()); SharedSourceFiles.plainAncestors(root);
    if (!actual.machineId().equals(WindowsJobProcess.currentMachineId())
        || !Path.of(reference.path()).toAbsolutePath().normalize().equals(root.resolve(".assembly/REFERENCE-ACTUAL.json")))
      throw new IOException("exact same-machine reference actual receipt required");
    ReferenceReview review = JSON.readValue(read(actual.reviewRef(), MAX_METADATA), ReferenceReview.class);
    ReferenceReview fresh = reviewReference(review.requestRef());
    if (!fresh.request().equals(review.request()) || !fresh.parentSourceReview().sourceClosure().equals(review.parentSourceReview().sourceClosure())
        || !fresh.parentSourceReview().completeSdkInputInventory().equals(review.parentSourceReview().completeSdkInputInventory())
        || !fresh.quote().equals(review.quote()) || !fresh.selectedSourceSetSha256().equals(review.selectedSourceSetSha256())
        || actual.purpose() != fresh.request().purpose()
        || !absolute(actual.sdkRoot()).equals(root.resolve(fresh.parentSourceReview().request().sdkRelativeRoot()))
        || !fresh.selectedSourceSetSha256().equals(actual.sourceSetSha256()) || !absolute(fresh.request().outputRoot()).equals(root)
        || actual.actualSourceClosure().size() != fresh.parentSourceReview().sourceClosure().size())
      throw new IOException("reference actual origin or complete inventory differs");
    Set<String> seen = new HashSet<>();
    for (OutputSource source : actual.actualSourceClosure()) {
      if (!seen.add(source.relativePath()) || !absolute(source.actual().path()).equals(root.resolve(source.relativePath())))
        throw new IOException("reference output path differs or duplicates");
      source.actual().verify();
      ReviewedSource parent = fresh.parentSourceReview().sourceClosure().stream().filter(row -> row.relativePath().equals(source.relativePath())).findFirst().orElseThrow();
      if (source.role() != parent.role() || !content(source.actual()).equals(referenceDigest(fresh, parent)))
        throw new IOException("reference output content or role differs");
    }
    List<String> expectedImportRoots = fresh.parentSourceReview().request().importRoots().stream().map(row -> row.equals(".") ? root.toString() : root.resolve(row).normalize().toString()).toList();
    if (!expectedImportRoots.equals(actual.importRoots())) throw new IOException("reference physical import roots differ");
    List<SelectedImportRoute> expectedRoutes = new ArrayList<>();
    for (ImportRoute route : fresh.parentSourceReview().request().importRoutes()) {
      OutputSource source = actual.actualSourceClosure().stream().filter(row -> row.relativePath().equals(route.relativeSource())).findFirst().orElseThrow();
      expectedRoutes.add(new SelectedImportRoute(route.module(), route.relativeSource(), route.location(), source.actual(), route.requiredBeforeConsumer()));
    }
    if (!expectedRoutes.equals(actual.selectedImportRoutes())) throw new IOException("reference selected physical import routes differ");
    requireExactOutputSet(root, actual.actualSourceClosure());
    var storage=JSON.readValue(read(actual.storageEvidence(),131072),ControlBuild.CapacityRelease.class);
    Instant observed=Instant.parse(actual.observedAtUtc());
    if(!storage.machineId().equals(actual.machineId()) || !storage.ownerTask().equals(fresh.request().ownerTask())
        || observed.isBefore(Instant.parse(storage.observedAtUtc())) || !observed.isBefore(Instant.parse(storage.reviewAtUtc()))
        || storage.approvedOutputRoots().stream().noneMatch(path->root.startsWith(absolute(path)))
        || actual.chargedAllocationUpperBytes()>storage.parts().getOrDefault("artifacts",0L))
      throw new IOException("reference actual lacks its exact historical same-owner source write grant");
    actual.storageEvidence().verify(); return actual;
  }
  private static Digest referenceDigest(ReferenceReview review, ReviewedSource source) {
    return review.request().selections().stream().filter(row -> row.relativePath().equals(source.relativePath()))
        .findFirst().map(row -> content(row.selectedSourceRef())).orElse(source.result());
  }
  private static void referenceGuard(ReferenceCapacityGate gate, WritePermit permit, long charged) throws IOException {
    if (!permit.machineId().equals(WindowsJobProcess.currentMachineId())
        || !Instant.now().isBefore(Instant.parse(permit.expiresAtUtc())) || charged > permit.allocationUpperLimitBytes())
      throw new IOException("reference source write permit expired or exhausted");
    permit.freshStorageEvidence().verify(); gate.revalidate(permit, charged);
  }
  public static ReferenceRequest readReferenceRequest(FileRef reference) throws IOException {
    return JSON.readValue(read(reference,MAX_METADATA),ReferenceRequest.class);
  }
  static void verifyReferenceParent(ReferenceSelection selection,Source source,boolean absent) throws IOException {
    if(source==null || !source.overlays().isEmpty() || (absent
        ? selection.parentSourceRef()!=null || source.origin()!=InputOrigin.STAGED_NEW_SOURCE || !source.original().equals(selection.selectedSourceRef())
        : !source.original().equals(selection.parentSourceRef())))
      throw new IOException("reference selection must preserve an exact parent or explicit staged absence");
  }
  static void validateReferenceAudit(ReferenceRequest request, Review parent) throws IOException {
    if (request.purpose()==ReferencePurpose.LEGACY_REFERENCE_ONLY) return;
    FileRef binding=request.constructionRequestRef();
    var construction=ConstructionOracleAssemblyRequest.read(read(binding,16384));
    ConstructionOracleAssemblyRequest.assemble(construction,binding);
    if (!construction.machineId().equals(request.machineId())) throw new IOException("construction original request machine differs");
    for (var original:construction.referenceSources()) {
      original.sourceRef().verify();
      var found=parent.sourceClosure().stream().filter(row->row.relativePath().equals(original.repositoryTarget())).findFirst().orElseThrow(()->new IOException("original eight reference source missing"));
      if (!found.original().equals(original.sourceRef()) || !found.overlays().isEmpty() || !found.result().equals(content(original.sourceRef())))
        throw new IOException("original reference8 bytes or source differs");
    }
    construction.originalAuditRef().verify(); construction.separationAuditRef().verify();
    FileRef pins=construction.referenceSources().stream().filter(row->row.repositoryTarget().endsWith("/source-pins.json")).findFirst().orElseThrow().sourceRef();
    JsonNode originals=JSON.readTree(read(pins,65536));
    if (!originals.path("schema").asText().equals("xar.construction-python-oracle-source/v1")
        || !originals.path("machine_id").asText().equals(request.machineId()) || !originals.path("dependencies").isArray())
      throw new IOException("typed original dependency audit required");
    for (JsonNode dependency:originals.get("dependencies")) {
      String path=dependency.path("path").asText();
      Digest expected=new Digest(dependency.path("bytes").longValue(),dependency.path("sha256").asText());
      var found=parent.sourceClosure().stream().filter(row->row.relativePath().equals(path)).findFirst().orElseThrow(()->new IOException("original dependency missing"));
      var override=request.selections().stream().filter(row->row.relativePath().equals(path)).findFirst();
      Digest selected=override.isPresent()?content(override.orElseThrow().selectedSourceRef()):found.result();
      if (!expected.equals(selected)) throw new IOException("original reference dependency differs: "+path);
      String prefix=parent.request().sdkRelativeRoot()+"/";
      String module=path.startsWith(prefix)&&path.endsWith(".py")?path.substring(prefix.length(),path.length()-3).replace('/','.'):"";
      if(module.isEmpty() || parent.request().importRoutes().stream().noneMatch(row->row.module().equals(module)&&row.relativeSource().equals(path)&&row.location()==ImportSourceLocation.FRESH_GRAPH))
        throw new IOException("original reference dependency requires its exact physical import route: "+path);
    }
    for (ReferenceSelection selection:request.selections()) {
      if (selection.kind()==ReferenceInputKind.ORIGINAL_PRODUCER_SOURCE) {
        boolean match=false;
        for (JsonNode dependency:originals.get("dependencies")) if (dependency.path("path").asText().equals(selection.relativePath())
            && content(selection.selectedSourceRef()).equals(new Digest(dependency.path("bytes").longValue(),dependency.path("sha256").asText()))) match=true;
        if (!selection.auditRef().equals(pins) || !match) throw new IOException("original source selection lacks the exact original dependency audit");
      } else {
        String path=selection.relativePath();
        if (!path.equals("tools/g2_saved_campaign/java_map_admission_client_v1.py")
            && !path.equals("ck3_autonomous_player/src/xar_autoplayer/construction_formal_consumer.py"))
          throw new IOException("reference compatibility adapter is outside the existing construction/client seam");
        var plan=JSON.readValue(read(selection.auditRef(),MAX_METADATA),SdkSourceIntent.Plan.class);
        var chosen=plan.consumerSelections().stream().filter(row->row.relativePath().equals(path)).findFirst().orElseThrow(()->new IOException("selected adapter missing from owner intent"));
        var parentSource=parent.request().sources().stream().filter(row->row.relativePath().equals(path)).findFirst().orElseThrow();
        if (!plan.machineId().equals(request.machineId()) || chosen.role()!=parentSource.role() || (selection.parentSourceRef()==null
              ? chosen.kind()!=SdkSourceIntent.SelectionKind.ADD_SOURCE || chosen.expectedTemplateSource()!=null
              : chosen.kind()!=SdkSourceIntent.SelectionKind.REPLACE_CONTENT || chosen.expectedTemplateSource()==null
                || !chosen.expectedTemplateSource().original().equals(selection.parentSourceRef()))
            || !chosen.selectedSource().equals(selection.selectedSourceRef()))
          throw new IOException("reference adapter intent parent/selected source differs");
        if (path.startsWith("tools/") && !selection.selectedSourceRef().equals(construction.selectedClient().sourceRef()))
          throw new IOException("reference helper requires the explicitly selected155 client");
      }
    }
    for (String module:List.of("construction_python_oracle_v1","construction_java_fixture_v1","xar_autoplayer.construction_formal_consumer","tools.g2_saved_campaign.java_map_admission_client_v1"))
      if(parent.request().importRoutes().stream().noneMatch(row->row.module().equals(module)&&row.location()==ImportSourceLocation.FRESH_GRAPH))
        throw new IOException("reference requires each actual oracle/helper/adapter/client import route");
    for (String required:List.of("tools/g2_saved_campaign/java_map_admission_client_v1.py","ck3_autonomous_player/src/xar_autoplayer/construction_formal_consumer.py"))
      if(request.selections().stream().noneMatch(row->row.relativePath().equals(required)&&row.kind()==ReferenceInputKind.COMPATIBILITY_ADAPTER))
        throw new IOException("reference imports require the declared client and formal compatibility adapters");
  }
  static final class ReferenceGate implements ReferenceCapacityGate {
    private final FileRef permitRef; private final WritePermit permit; private final ReferenceRequest request;
    private final Path reviewPath; private final ControlBuild.CapacityRelease release; private final List<Path> roots;
    private final long initial, cap;
    ReferenceGate(FileRef permitRef,ReferenceRequest request,Path reviewPath) throws IOException {
      this.permitRef=permitRef; this.permit=JSON.readValue(read(permitRef,65536),WritePermit.class);
      this.request=request; this.reviewPath=reviewPath.toAbsolutePath().normalize();
      this.release=JSON.readValue(read(permit.freshStorageEvidence(),131072),ControlBuild.CapacityRelease.class);
      if(!request.machineId().equals(WindowsJobProcess.currentMachineId()) || !release.ownerTask().equals(request.ownerTask()) || !release.machineId().equals(request.machineId())
          || !permit.machineId().equals(request.machineId()) || !absolute(permit.exactOutputRoot()).equals(absolute(request.outputRoot()))
          || Instant.now().isBefore(Instant.parse(release.observedAtUtc()))
          || !Instant.now().isBefore(Instant.parse(release.reviewAtUtc()))
          || !Instant.now().isBefore(Instant.parse(permit.expiresAtUtc()))
          || Instant.parse(permit.expiresAtUtc()).isAfter(Instant.parse(release.reviewAtUtc())))
        throw new IOException("reference current grant owner/machine/root/window differs");
      if(release.approvedOutputRoots().stream().noneMatch(row->absolute(request.outputRoot()).startsWith(absolute(row)))
          || release.approvedOutputRoots().stream().noneMatch(row->this.reviewPath.startsWith(absolute(row)))
          || !absolute(System.getProperty("java.io.tmpdir")).startsWith(absolute(release.temporaryRoot()))
          || release.approvedOutputRoots().stream().noneMatch(row->absolute(System.getProperty("jna.tmpdir")).startsWith(absolute(row))))
        throw new IOException("reference output/review/ENTIRETMP outside actual grant");
      Path output=absolute(request.outputRoot()); SharedSourceFiles.plainAncestors(output); SharedSourceFiles.plainAncestors(this.reviewPath);
      if(!Files.isDirectory(output.getParent(),LinkOption.NOFOLLOW_LINKS) || !Files.isDirectory(this.reviewPath.getParent(),LinkOption.NOFOLLOW_LINKS)
          || Files.exists(output,LinkOption.NOFOLLOW_LINKS) || Files.exists(this.reviewPath,LinkOption.NOFOLLOW_LINKS))
        throw new IOException("fresh reference output and review in existing admitted parents required");
      List<Path> volumeScopes=new ArrayList<>();
      for(String scope:release.approvedOutputRoots()) volumeScopes.add(absolute(scope));
      volumeScopes.addAll(List.of(output,this.reviewPath,absolute(release.temporaryRoot()),
          absolute(System.getProperty("java.io.tmpdir")),absolute(System.getProperty("jna.tmpdir"))));
      for(Path scope:volumeScopes) if(release.volumes().keySet().stream().noneMatch(volume->absolute(volume).equals(scope.getRoot())))
        throw new IOException("reference volume budget missing for actual output/review/ENTIRETMP scope");
      long unit=Math.max(4096,Files.getFileStore(output.getParent()).getBlockSize());
      if(permit.allocationUnitBytes()<unit || permit.allocationUnitBytes()%unit!=0 || permit.perDirectoryGuardBytes()<4096)
        throw new IOException("reference permit must conservatively charge actual allocation and directories");
      release.policyRef().verify(); var policy=CiBootstrap.readPolicy(read(release.policyRef(),131072));
      for(var entry:release.volumes().entrySet()) {
        var volume=entry.getValue(); var override=release.quotaOverrides().get(entry.getKey());
        if(absolute(request.outputRoot()).getRoot().equals(absolute(entry.getKey()).getRoot())
            && volume.thisWritePeak()<Math.addExact(permit.allocationUpperLimitBytes(),MAX_METADATA))
          throw new IOException("volume reservation cannot cover the complete pending source packet");
        if(override!=null) new FileRef(override.sourceRef().path(),override.sourceRef().bytes(),override.sourceRef().sha256()).verify();
        if(!volume.equals(CiBootstrap.calculate(policy,volume.totalVolumeBytes(),volume.availableBytes(),volume.thisWritePeak(),
            volume.otherUnspentReservations(),volume.systemGrowthReserve(),volume.currentProjectUsageConservativeUpper(),
            override,Instant.parse(release.observedAtUtc()),Instant.parse(release.reviewAtUtc()))))
          throw new IOException("reference shared storage policy/volume reservation differs");
      }
      List<Path> scopes=new ArrayList<>();for(String row:release.approvedOutputRoots()) scopes.add(absolute(row));
      scopes.add(absolute(release.temporaryRoot())); List<Path> minimal=new ArrayList<>();
      for(Path path:scopes) if(scopes.stream().noneMatch(other->!other.equals(path)&&path.startsWith(other))&&!minimal.contains(path)) minimal.add(path);
      roots=List.copyOf(minimal); cap=release.parts().getOrDefault("artifacts",0L);
      initial=census(); if(Math.addExact(initial,Math.addExact(permit.allocationUpperLimitBytes(),MAX_METADATA))>cap)
        throw new IOException("whole occupied outputs/ENTIRETMP cannot admit the reserved reference packet");
      cheap(0);
    }
    private long census() throws IOException { long total=0;for(Path root:roots)total=Math.addExact(total,SharedOwnedCommand.allocated(root));return total; }
    private void cheap(long charged) throws IOException {
      permitRef.verify(); permit.freshStorageEvidence().verify(); release.policyRef().verify();
      if(!Instant.now().isBefore(Instant.parse(release.reviewAtUtc())) || !Instant.now().isBefore(Instant.parse(permit.expiresAtUtc())) || charged>permit.allocationUpperLimitBytes())
        throw new IOException("reference live grant expired/exhausted");
      for(var entry:release.volumes().entrySet())if(Files.getFileStore(absolute(entry.getKey())).getUsableSpace()<entry.getValue().requiredFree())
        throw new IOException("reference current volume reserve unavailable");
    }
    @Override public WritePermit acquire(ReferenceReview review) throws IOException {
      if(!review.request().equals(request))throw new IOException("reference writer differs from admitted request"); cheap(0);return permit;
    }
    @Override public void revalidate(WritePermit current,long charged) throws IOException {
      if(!current.equals(permit))throw new IOException("reference write permit changed");cheap(charged);
    }
    void finish() throws IOException {cheap(0);if(census()>cap)throw new IOException("whole reference outputs/ENTIRETMP exceed actual part cap");}
  }
  /** Current Root-issued CapacityRelease and actual owned-output census precede every metadata write. */
  public static void main(String[] args) throws IOException {
    if(args.length!=7)throw new IOException("reference-request path/bytes/sha permit path/bytes/sha new-review-path");
    FileRef requestRef=new FileRef(args[0],Long.parseLong(args[1]),args[2]);
    FileRef permitRef=new FileRef(args[3],Long.parseLong(args[4]),args[5]); Path output=Path.of(args[6]);
    ReferenceRequest request=readReferenceRequest(requestRef); ReferenceGate gate=new ReferenceGate(permitRef,request,output);
    ReferenceReview review=reviewReference(requestRef); gate.acquire(review);
    FileRef reviewRef=writeReferenceReview(review,output);
    ReferenceActual actual=assembleReference(reviewRef,gate);gate.finish();
    System.out.println(JSON.writeValueAsString(FileRef.measure(Path.of(actual.graphRoot()).resolve(".assembly/REFERENCE-ACTUAL.json"))));
  }

}
