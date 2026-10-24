package org.xar.ck3.control.build;

import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.IOException;
import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.HashSet;
import java.util.HexFormat;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.zip.GZIPInputStream;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.SharedSourceFiles.Witness;

/** Create-only frozen Native sources. It never configures, compiles, registers or starts a game. */
public final class NativeCombinedSourceCut {
    private NativeCombinedSourceCut() { }
    private static final ObjectMapper JSON = RootNativePlanJson.mapper();
    private static final int MAX_FILES = 16000;
    private static final int MAX_METADATA = 16 << 20;
    private static final String NATIVE = "ck3_autonomous_player/native_bridge/";

    public record Content(long bytes, String sha256) {
        public Content {
            if (bytes < 0 || bytes > (16L << 20) || sha256 == null || !sha256.matches("[a-f0-9]{64}"))
                throw new IllegalArgumentException("Exact finite source content required");
        }
    }
    public record PreparationIdentity(String provider, String deviceId, String fileId, String modifyUnixNs, String changeUnixNs) { }
    public record BaseRow(String relativePath, long bytes, String sha256, Boolean sourceInput, PreparationIdentity identity) {
        public BaseRow {
            relative(relativePath); new Content(bytes, sha256); Objects.requireNonNull(sourceInput);
            Objects.requireNonNull(identity);
        }
    }
    public record BaseCensus(String schema, String machineId, String baseRoot, String observedAtUtc,
                             String selectionRule, List<BaseRow> rows) {
        public BaseCensus {
            if (!"xar.native-source-base-census/v1".equals(schema)) throw new IllegalArgumentException("Base census schema");
            absolute(baseRoot); Instant.parse(observedAtUtc); rows = List.copyOf(rows);
            if (rows.isEmpty() || rows.size() > MAX_FILES) throw new IllegalArgumentException("Complete bounded source rows required");
            Set<String> paths = new HashSet<>();
            for (BaseRow row : rows) if (!paths.add(key(row.relativePath()))) throw new IllegalArgumentException("Duplicate base source");
        }
    }
    public record Selected(String targetRelative, FileRef sourceRef) {
        public Selected { relative(targetRelative); Objects.requireNonNull(sourceRef); }
    }
    public record ExpectedRow(String relativePath, long bytes, String sha256) {
        public ExpectedRow { relative(relativePath); new Content(bytes, sha256); }
    }
    public record ExpectedFileSet(String schema, String machineId, int sourceCount, List<ExpectedRow> rows) { }
    public record Patch(String targetRelative, Content preimage, FileRef preimageRef, FileRef patchRef,
                        ExactSourcePatch.Syntax syntax, String patchTarget, Content postimage) {
        public Patch {
            relative(targetRelative); relative(patchTarget);
            Objects.requireNonNull(preimage); Objects.requireNonNull(patchRef);
            Objects.requireNonNull(syntax); Objects.requireNonNull(postimage);
            if (preimageRef != null && !content(preimageRef).equals(preimage)) throw new IllegalArgumentException("Original preimage pin differs");
        }
    }
    public enum CompositionSyntax { UNIFIED_DIFF, APPEND_EXACT }
    public record CompositionStep(String id, CompositionSyntax syntax, String patchTarget, FileRef patchRef,
                                  Content declaredPreimage, Content isolatedPostimage, Content compositionPreimage,
                                  Content compositionPostimage, String context, String appendUtf8) { }
    public record CmakeComposition(String schema, String machineId, String status, FileRef baseRef,
                                   List<CompositionStep> steps, FileRef finalRef,
                                   String constructionRefundMacroDefault) { }
    public record Request(String schema, String machineId, FileRef qualifiedToolsBuildRef, FileRef baseCensusRef, FileRef expectedFileSetRef, List<Selected> selectedFiles,
                          List<Patch> patches, FileRef cmakeCompositionRef, List<FileRef> provenanceRefs,
                          Path outputRoot, Path controlRoot, long sourceLogicalLimitBytes) {
        public Request {
            if (!"xar.native-combined-source-cut-request/v1".equals(schema)) throw new IllegalArgumentException("Cut request schema");
            Objects.requireNonNull(qualifiedToolsBuildRef); Objects.requireNonNull(baseCensusRef);
            Objects.requireNonNull(expectedFileSetRef); Objects.requireNonNull(cmakeCompositionRef);
            selectedFiles = List.copyOf(selectedFiles); patches = List.copyOf(patches); provenanceRefs = List.copyOf(provenanceRefs);
            outputRoot = absolute(outputRoot); controlRoot = absolute(controlRoot);
            if (overlap(outputRoot, controlRoot) || selectedFiles.size() > MAX_FILES || patches.size() > 256
                    || provenanceRefs.size() > 4096 || sourceLogicalLimitBytes < 4096 || sourceLogicalLimitBytes > (256L << 20))
                throw new IllegalArgumentException("Disjoint finite source/control roots required");
        }
    }
    public record Limits(String ownerTask, FileRef capacityEvidence, Instant deadline, long outputAllocationLimitBytes) {
        public Limits {
            if (ownerTask == null || !ownerTask.matches("/root(?:/[a-z0-9_-]+)*") || capacityEvidence == null || deadline == null
                    || outputAllocationLimitBytes < 4096 || outputAllocationLimitBytes > (1536L << 20))
                throw new IllegalArgumentException("Current finite Root source authority required");
        }
    }
    public record Spec(String schema, FileRef requestRef, Limits limits) { }
    public record Actual(String schema, String machineId, String observedAtUtc, FileRef requestRef,
                         FileRef producerToolsBuildRef, List<FileRef> completeToolsRuntime,
                         FileRef capacityRef, String packageRoot, String nativeSourceRoot,
                         List<FileRef> completePackageSources, List<FileRef> completeNativeSources,
                         List<Witness> inputWitnesses, long logicalBytes, long chargedBeforeActualBytes,
                         boolean sourceUnchanged, String qualification) { }
    public record EnvironmentInput(String schema, FileRef sourceActualRef, Path canonicalRepository,
                                   FileRef qualifiedToolsBuild, NativeBridgeBuild.Toolchain tools,
                                   List<NativeBridgeBuild.Definition> definitions, int parallelJobs, Path buildRoot, Path scratchRoot,
                                   NativeBridgeDefender.HelperRuntime defender, Path ownedControlRoot, Path requestOutput) { }
    private record Input(String relative, FileRef original, List<Patch> patches, Content expected) { }

    public static FileRef materialize(FileRef requestRef, Limits limits) throws IOException {
        Request request = JSON.readValue(read(requestRef, MAX_METADATA), Request.class);
        require(request.machineId().equals(WindowsJobProcess.currentMachineId()), "Current machine required");
        var producer = ControlBuild.verifiedCompletedReceipt(request.qualifiedToolsBuildRef());
        require(producer.targetKind() == ControlBuild.TargetKind.BUILD_TOOLS_RUNTIME
                && producer.completeDeployment().equals(ControlBuild.producerClosure()), "Exact accepted C16 source writer runtime required");
        try (ReleaseGuard guard = new ReleaseGuard(request, limits)) {
            require(!Files.exists(request.outputRoot(), LinkOption.NOFOLLOW_LINKS), "New exact source root required");
            require(Files.isDirectory(request.outputRoot().getParent(), LinkOption.NOFOLLOW_LINKS)
                    && Files.isDirectory(request.controlRoot(), LinkOption.NOFOLLOW_LINKS), "Admitted existing parents required");
            Path terminal = request.controlRoot().resolve("NATIVE-SOURCE-ACTUAL.json");
            require(!Files.exists(terminal, LinkOption.NOFOLLOW_LINKS), "Source control already used");
            BaseCensus base = readBase(request.baseCensusRef());
            require(base.machineId().equals(request.machineId()), "Base census machine differs");
            var witnesses = new ArrayList<Witness>();
            var witnessPaths = new HashSet<String>();
            observe(requestRef, witnesses, witnessPaths); observe(request.baseCensusRef(), witnesses, witnessPaths);
            observe(request.qualifiedToolsBuildRef(), witnesses, witnessPaths);
            for (FileRef runtime : producer.completeDeployment()) observe(runtime, witnesses, witnessPaths);
            observe(request.expectedFileSetRef(), witnesses, witnessPaths);
            observe(request.cmakeCompositionRef(), witnesses, witnessPaths);
            for (FileRef ref : request.provenanceRefs()) observe(ref, witnesses, witnessPaths);
            byte[] cmake = verifyCmake(request.cmakeCompositionRef(), witnesses, witnessPaths);
            Map<String, Input> files = new HashMap<>();
            for (BaseRow row : base.rows()) {
                if (!row.sourceInput()) continue; // Historical inventory of generated artifacts is not a source input.
                String relative = NATIVE + row.relativePath();
                FileRef source = new FileRef(Path.of(base.baseRoot()).resolve(row.relativePath()).toString(), row.bytes(), row.sha256());
                files.put(key(relative), new Input(relative, source, List.of(), new Content(row.bytes(), row.sha256())));
            }
            Set<String> selected = new HashSet<>();
            for (Selected row : request.selectedFiles()) {
                require(selected.add(key(row.targetRelative())), "One final selected body per target required");
                observe(row.sourceRef(), witnesses, witnessPaths);
                files.put(key(row.targetRelative()), new Input(row.targetRelative(), row.sourceRef(), List.of(), content(row.sourceRef())));
            }
            for (Patch patch : request.patches()) {
                String key = key(patch.targetRelative()); Input input = files.get(key);
                require(input != null && input.expected().equals(patch.preimage()), "Patch whole preimage differs from current winner");
                if (patch.preimageRef() != null) observe(patch.preimageRef(), witnesses, witnessPaths);
                observe(patch.patchRef(), witnesses, witnessPaths);
                var patches = new ArrayList<>(input.patches()); patches.add(patch);
                files.put(key, new Input(input.relative(), input.original(), List.copyOf(patches), patch.postimage()));
            }
            require(files.size() <= MAX_FILES, "Complete source file bound");
            ExpectedFileSet expected = JSON.readValue(readGzip(request.expectedFileSetRef(), 4 << 20), ExpectedFileSet.class);
            require("xar.native-combined-expected-file-set/v1".equals(expected.schema()) && expected.machineId().equals(request.machineId())
                    && expected.sourceCount() == files.size() && expected.rows().size() == files.size(), "Complete expected package domain differs");
            Set<String> expectedPaths = new HashSet<>();
            for (ExpectedRow row : expected.rows()) {
                Input input = files.get(key(row.relativePath()));
                require(expectedPaths.add(key(row.relativePath())) && input != null
                        && input.expected().equals(new Content(row.bytes(), row.sha256())), "Complete expected source set/content differs");
            }
            Input cmakeInput = files.get(key(NATIVE + "CMakeLists.txt"));
            require(cmakeInput != null && cmakeInput.expected().equals(content(cmake)), "Final selected CMake is not the strictly composed winner");
            List<Input> ordered = files.values().stream().sorted(Comparator.comparing(Input::relative)).toList();
            long logical = 0, charge = 0; Set<Path> directories = new HashSet<>(); directories.add(request.outputRoot());
            for (Input input : ordered) {
                logical = Math.addExact(logical, input.expected().bytes());
                charge = Math.addExact(charge, round(input.expected().bytes(), guard.unit));
                for (Path parent = request.outputRoot().resolve(input.relative()).getParent(); parent.startsWith(request.outputRoot()); parent = parent.getParent())
                    directories.add(parent);
                observe(input.original(), witnesses, witnessPaths);
            }
            require(logical <= request.sourceLogicalLimitBytes(), "Complete logical source bound exceeded");
            charge = Math.addExact(charge, Math.multiplyExact(directories.size(), 4096L));
            guard.reserve(Math.addExact(charge, MAX_METADATA));
            for (Witness witness : witnesses) SharedSourceFiles.assertUnchanged(witness);
            Map<String, byte[]> validatedPatchedBodies = new HashMap<>();
            for (Input input : ordered) if (!input.patches().isEmpty())
                validatedPatchedBodies.put(key(input.relative()), materializedBytes(input));
            Files.createDirectory(request.outputRoot());
            var outputs = new ArrayList<FileRef>();
            for (Input input : ordered) {
                guard.cheap(); byte[] bytes = validatedPatchedBodies.get(key(input.relative()));
                if (bytes == null) bytes = materializedBytes(input);
                require(content(bytes).equals(input.expected()), "Selected complete body differs");
                Path target = request.outputRoot().resolve(input.relative());
                Files.createDirectories(target.getParent()); SharedSourceFiles.plainAncestors(target.getParent());
                Files.write(target, bytes, StandardOpenOption.CREATE_NEW);
                FileRef output = FileRef.measure(target); require(content(output).equals(input.expected()), "Source write readback differs");
                outputs.add(output);
            }
            for (Witness witness : witnesses) SharedSourceFiles.assertUnchanged(witness);
            List<FileRef> all = NativeBridgeBuild.inventory(request.outputRoot());
            outputs.sort(Comparator.comparing(FileRef::path)); require(all.equals(outputs), "Exact final source set differs");
            Path nativeRoot = request.outputRoot().resolve(NATIVE);
            List<FileRef> nativeSources = NativeBridgeBuild.inventory(nativeRoot);
            guard.check();
            Actual actual = new Actual("xar.native-combined-source-cut-actual/v1", request.machineId(), Instant.now().toString(),
                    requestRef, request.qualifiedToolsBuildRef(), producer.completeDeployment(), limits.capacityEvidence(), request.outputRoot().toString(), nativeRoot.toString(),
                    all, nativeSources, List.copyOf(witnesses), logical, guard.charge(), true,
                    "FROZEN_SOURCE_ONLY_NOT_ENV_BUILD_REGISTER_NATIVE_TEST_OR_GAME");
            byte[] encoded = JSON.writeValueAsBytes(actual); require(encoded.length <= MAX_METADATA, "Source Actual bound");
            Files.write(terminal, encoded, StandardOpenOption.CREATE_NEW); guard.check();
            return FileRef.measure(terminal);
        }
    }
    private static byte[] materializedBytes(Input input) throws IOException {
        byte[] bytes = read(input.original(), MAX_METADATA);
        for (Patch patch : input.patches()) {
            require(content(bytes).equals(patch.preimage()), "Actual patch preimage drift");
            bytes = ExactSourcePatch.apply(bytes, read(patch.patchRef(), 1 << 20), patch.syntax(), patch.patchTarget()).bytes();
            require(content(bytes).equals(patch.postimage()), "Actual patch output differs");
        }
        require(content(bytes).equals(input.expected()), "Complete selected body differs before writes"); return bytes;
    }

    static byte[] verifyCmake(FileRef ref, List<Witness> witnesses, Set<String> seen) throws IOException {
        CmakeComposition plan = JSON.readValue(read(ref, 1 << 20), CmakeComposition.class);
        require("xar.native-cmake-strict-composition/v1".equals(plan.schema()) && !plan.steps().isEmpty()
                && plan.machineId().equals(WindowsJobProcess.currentMachineId()), "Exact same-machine CMake composition required");
        observe(plan.baseRef(), witnesses, seen); observe(plan.finalRef(), witnesses, seen);
        byte[] current = read(plan.baseRef(), 8 << 20); Map<Content, byte[]> known = new HashMap<>(); known.put(content(current), current);
        for (CompositionStep step : plan.steps()) {
            require(content(current).equals(step.compositionPreimage()), "Composition parent differs");
            if (step.syntax() == CompositionSyntax.UNIFIED_DIFF) {
                require(step.appendUtf8() == null && step.patchRef() != null && step.declaredPreimage() != null,
                        "Explicit patch branch required");
                byte[] original = known.get(step.declaredPreimage()); require(original != null, "Original owner preimage not reconstructed");
                observe(step.patchRef(), witnesses, seen); byte[] patch = read(step.patchRef(), 1 << 20);
                byte[] isolated = ExactSourcePatch.apply(original, patch, ExactSourcePatch.Syntax.UNIFIED_DIFF, step.patchTarget()).bytes();
                require(content(isolated).equals(step.isolatedPostimage()), "Original owner isolated result differs");
                known.put(content(isolated), isolated);
                current = ExactSourcePatch.apply(current, patch, ExactSourcePatch.Syntax.UNIFIED_DIFF, step.patchTarget()).bytes();
            } else {
                require(step.syntax() == CompositionSyntax.APPEND_EXACT && step.patchRef() == null && step.appendUtf8() != null,
                        "Explicit exact append branch required");
                byte[] append = step.appendUtf8().getBytes(java.nio.charset.StandardCharsets.UTF_8);
                byte[] next = java.util.Arrays.copyOf(current, Math.addExact(current.length, append.length));
                System.arraycopy(append, 0, next, current.length, append.length); current = next;
            }
            require(content(current).equals(step.compositionPostimage()), "Composite output differs");
            known.put(content(current), current);
        }
        require(content(current).equals(content(plan.finalRef())) && java.util.Arrays.equals(current, read(plan.finalRef(), 8 << 20)),
                "Complete final CMake body differs from replay");
        return current;
    }
    private static BaseCensus readBase(FileRef pin) throws IOException {
        return JSON.readValue(readGzip(pin, 4 << 20), BaseCensus.class);
    }
    private static byte[] readGzip(FileRef pin, int maximum) throws IOException {
        pin.verify(); byte[] raw;
        try (InputStream in = new GZIPInputStream(Files.newInputStream(Path.of(pin.path())))) {
            raw = in.readNBytes(maximum + 1); require(raw.length <= maximum && in.read() == -1, "Finite full source census required");
        }
        pin.verify(); return raw;
    }
    public static Actual readAcceptedSource(FileRef pin) throws IOException {
        Actual actual = JSON.readValue(read(pin, MAX_METADATA), Actual.class);
        require("xar.native-combined-source-cut-actual/v1".equals(actual.schema()) && actual.sourceUnchanged()
                && actual.machineId().equals(WindowsJobProcess.currentMachineId()), "Exact same-machine frozen source Actual required");
        var producer = ControlBuild.verifiedCompletedReceipt(actual.producerToolsBuildRef());
        require(producer.completeDeployment().equals(actual.completeToolsRuntime()), "Frozen source producer runtime differs");
        Request request = JSON.readValue(read(actual.requestRef(), MAX_METADATA), Request.class);
        require(Path.of(pin.path()).toAbsolutePath().normalize().equals(request.controlRoot().resolve("NATIVE-SOURCE-ACTUAL.json"))
                && Path.of(actual.packageRoot()).equals(request.outputRoot())
                && Path.of(actual.nativeSourceRoot()).equals(request.outputRoot().resolve(NATIVE))
                && NativeBridgeBuild.inventory(request.outputRoot()).equals(actual.completePackageSources())
                && NativeBridgeBuild.inventory(Path.of(actual.nativeSourceRoot())).equals(actual.completeNativeSources()),
                "Full frozen source package/native inventory differs");
        return actual;
    }
    /** Only creates the typed ENV input; the original C16 production entrypoint owns ENV execution. */
    public static FileRef writeEnvironmentRequest(EnvironmentInput input) throws IOException {
        require("xar.native-combined-environment-input/v2".equals(input.schema()), "Typed environment input v2 required");
        require(input.defender() == null, "ENV cannot carry a REGISTER helper runtime");
        require(input.parallelJobs() >= 1 && input.parallelJobs() <= 4, "Finite admitted native parallelism 1..4 required");
        Actual source = readAcceptedSource(input.sourceActualRef());
        var tools = ControlBuild.verifiedCompletedReceipt(input.qualifiedToolsBuild());
        require(tools.targetKind() == ControlBuild.TargetKind.BUILD_TOOLS_RUNTIME
                && tools.completeDeployment().equals(ControlBuild.producerClosure()), "Same accepted complete C16 tools runtime required");
        for (FileRef ref : input.tools().references()) ref.verify();
        for (NativeBridgeBuild.Definition definition : input.definitions()) {
            if (definition.option().equals("XAR_CK3_ENABLE_CONSTRUCTION_REFUND_SOURCE12004"))
                require(definition.value().name().equals("OFF"), "Offline fixture build cannot enable the refund private route");
        }
        var request = new NativeBridgeBuild.Request(NativeBridgeBuild.REQUEST_SCHEMA, source.machineId(), NativeBridgeBuild.Stage.ENV,
                input.canonicalRepository(), Path.of(source.nativeSourceRoot()), source.completeNativeSources(), input.buildRoot(), input.scratchRoot(),
                input.qualifiedToolsBuild(), input.tools(), input.definitions(), input.parallelJobs(), null, null, input.defender());
        return NativeBridgeBuild.writeRequest(request, input.ownedControlRoot(), input.requestOutput());
    }
    private static void observe(FileRef ref, List<Witness> result, Set<String> seen) throws IOException {
        String path = key(Path.of(ref.path()).toAbsolutePath().normalize().toString());
        if (!seen.add(path)) {
            Witness prior = result.stream().filter(w -> key(w.source().path()).equals(path)).findFirst().orElseThrow();
            require(content(prior.source()).equals(content(ref)), "Conflicting duplicate source pin"); return;
        }
        Witness witness = SharedSourceFiles.observe(Path.of(ref.path()));
        require(Path.of(witness.source().path()).equals(Path.of(ref.path()).toAbsolutePath().normalize())
                && content(witness.source()).equals(content(ref)), "Fresh source identity/content differs"); result.add(witness);
    }
    private static byte[] read(FileRef ref, int max) throws IOException {
        require(ref.bytes() <= max, "Pinned source bound exceeded"); ref.verify(); byte[] raw = Files.readAllBytes(Path.of(ref.path())); ref.verify(); return raw;
    }
    private static Content content(FileRef ref) { return new Content(ref.bytes(), ref.sha256()); }
    private static Content content(byte[] bytes) {
        try { return new Content(bytes.length, HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes))); }
        catch (NoSuchAlgorithmException impossible) { throw new IllegalStateException(impossible); }
    }
    private static String key(String value) { return value.replace('\\', '/').toLowerCase(Locale.ROOT); }
    private static void relative(String value) {
        if (value == null || value.isBlank() || value.indexOf('\\') >= 0 || value.startsWith("/") || value.indexOf(':') >= 0
                || java.util.Arrays.stream(value.split("/", -1)).anyMatch(v -> v.isBlank() || v.equals(".") || v.equals("..")))
            throw new IllegalArgumentException("Plain relative source path required");
    }
    private static Path absolute(String value) { return absolute(Path.of(value)); }
    private static Path absolute(Path value) {
        if (value == null || !value.isAbsolute()) throw new IllegalArgumentException("Absolute source path required"); return value.normalize();
    }
    private static boolean overlap(Path left, Path right) { return left.startsWith(right) || right.startsWith(left); }
    private static long round(long value, long unit) { return Math.multiplyExact(Math.floorDiv(Math.addExact(value, unit - 1), unit), unit); }
    private static void require(boolean value, String message) throws IOException { if (!value) throw new IOException(message); }

    /** Current common capacity release plus actual native allocation; no JSON-only default grant. */
    private static final class ReleaseGuard implements AutoCloseable {
        private final Request request;
        private final Limits limits;
        private final ControlBuild.CapacityRelease release;
        private final long unit;
        private final List<Path> roots;
        private long nextExpensiveCheck;
        private ReleaseGuard(Request request, Limits limits) throws IOException {
            this.request = request; this.limits = limits;
            release = JSON.readValue(read(limits.capacityEvidence(), 131072), ControlBuild.CapacityRelease.class);
            require(release.machineId().equals(request.machineId()) && release.ownerTask().equals(limits.ownerTask())
                    && !limits.deadline().isAfter(Instant.parse(release.reviewAtUtc())), "Current exact source owner/window required");
            for (Path root : List.of(request.outputRoot(), request.controlRoot())) {
                SharedSourceFiles.plainAncestors(root);
                require(release.approvedOutputRoots().stream().map(Path::of).anyMatch(root::startsWith), "Source/control root not admitted");
            }
            Path temporary = Path.of(release.temporaryRoot()).toAbsolutePath().normalize();
            require(Path.of(System.getProperty("java.io.tmpdir")).toAbsolutePath().normalize().startsWith(temporary), "Source JVM temporary root outside grant");
            Path jna = Path.of(System.getProperty("jna.tmpdir")).toAbsolutePath().normalize();
            require(release.approvedOutputRoots().stream().map(Path::of).anyMatch(jna::startsWith), "Source JNA temporary root outside grant");
            List<Path> declared = List.of(request.outputRoot(), request.controlRoot(), temporary);
            roots = declared.stream().distinct().filter(p -> declared.stream().noneMatch(other -> !other.equals(p) && p.startsWith(other))).toList();
            require(limits.outputAllocationLimitBytes() <= release.parts().getOrDefault("build", 0L), "Source bound exceeds Root build allocation");
            unit = Math.max(4096, Files.getFileStore(request.outputRoot().getParent()).getBlockSize());
            release.policyRef().verify(); var policy = CiBootstrap.readPolicy(read(release.policyRef(), 131072));
            for (var entry : release.volumes().entrySet()) {
                var volume = entry.getValue(); var override = release.quotaOverrides().get(entry.getKey());
                if (override != null) new FileRef(override.sourceRef().path(), override.sourceRef().bytes(), override.sourceRef().sha256()).verify();
                require(volume.equals(CiBootstrap.calculate(policy, volume.totalVolumeBytes(), volume.availableBytes(), volume.thisWritePeak(),
                        volume.otherUnspentReservations(), volume.systemGrowthReserve(), volume.currentProjectUsageConservativeUpper(), override,
                        Instant.parse(release.observedAtUtc()), Instant.parse(release.reviewAtUtc()))), "Current shared volume formula differs");
            }
            for (Path root : roots) {
                var volume = release.volumes().entrySet().stream()
                        .filter(row -> Path.of(row.getKey()).toAbsolutePath().normalize().getRoot().equals(root.getRoot()))
                        .findFirst().orElseThrow(() -> new IOException("Source/control/ENTIRETMP volume not budgeted"));
                require(volume.getValue().thisWritePeak() >= limits.outputAllocationLimitBytes(), "Current volume cannot cover this complete source allowance");
            }
            check();
        }
        private long charge() throws IOException {
            long total = 0; for (Path root : roots) total = Math.addExact(total, SharedOwnedCommand.allocated(root)); return total;
        }
        private void reserve(long needed) throws IOException {
            require(Math.addExact(charge(), needed) <= limits.outputAllocationLimitBytes(), "Complete source/control reservation cannot fit"); check();
        }
        private void check() throws IOException {
            nextExpensiveCheck = 0; cheap();
            require(charge() <= limits.outputAllocationLimitBytes(), "Actual source/control/ENTIRETMP allocation cap exhausted");
        }
        private void cheap() throws IOException {
            require(!Instant.now().isBefore(Instant.parse(release.observedAtUtc())) && Instant.now().isBefore(limits.deadline())
                    && Instant.now().isBefore(Instant.parse(release.reviewAtUtc())), "Source authority expired or future dated");
            if (nextExpensiveCheck != 0 && System.nanoTime() - nextExpensiveCheck < 0) return;
            nextExpensiveCheck = System.nanoTime() + 1_000_000_000L;
            limits.capacityEvidence().verify(); release.policyRef().verify();
            for (var entry : release.volumes().entrySet()) require(Files.getFileStore(Path.of(entry.getKey())).getUsableSpace() >= entry.getValue().requiredFree(),
                    "Current volume reserve unavailable");
        }
        @Override public void close() { }
    }

    public static void main(String[] args) throws IOException {
        if (args.length == 4 && args[0].equals("env-request")) {
            var pin = new FileRef(args[1], Long.parseLong(args[2]), args[3]);
            System.out.println(JSON.writeValueAsString(writeEnvironmentRequest(JSON.readValue(read(pin, MAX_METADATA), EnvironmentInput.class))));
            return;
        }
        require(args.length == 3, "SPEC_PATH EXACT_BYTES SHA256 or env-request INPUT_PATH EXACT_BYTES SHA256 required");
        FileRef ref = new FileRef(args[0], Long.parseLong(args[1]), args[2]);
        Spec spec = JSON.readValue(read(ref, 131072), Spec.class);
        require("xar.native-combined-source-cut-execution/v1".equals(spec.schema()), "Source execution schema required");
        System.out.println(JSON.writeValueAsString(materialize(spec.requestRef(), spec.limits())));
    }
}
