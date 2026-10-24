package org.xar.ck3.control.build;

import com.fasterxml.jackson.databind.JsonNode;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Set;

/**
 * Shared compiled capture admission. This class never starts a process and never
 * grants normal build, service, SDK or Game admission. CompiledGoldenCapture calls
 * validate before and after the whole-tree Job invocation.
 */
public final class CompiledCaptureInputProfile {
    public enum Kind { QUALIFIED_TEST_CLASSES_V1 }

    /** Exact source-manifest04 launchers; a source change requires a new profile version. */
    public enum Launcher {
        GIFT_READ("giftreadtransport.GiftReadGoldenCapture", 7872,
                "c5191d76999843fcb55096c6fe802483378ddc91016cf2a8e2382cb0abf8d1d5", 3),
        GIFT_ROUTE("giftroute.GiftRouteGoldenCapture", 16080,
                "a331090030d34d532a6576c1022c2c6c4a63b2a47176a614496b8be082726a5f", 3),
        GIFT_PENDING_ROUTE("giftpendingroute.CaptureGiftPendingReadRouteGolden", 8528,
                "bd2a6c38dbcc1979393432467ec6d4854fa76d70e40c9ea57805e882fb47d087", 4),
        GIFT_PENDING_READERS("giftpendingreaders.CaptureGiftPendingReadersGolden", 6957,
                "e5228fd71f1ed1836dc217c2432539a00f9e665751c643063b28feaa0e5b9b04", 4);

        private final String suffix;
        private final long sourceBytes;
        private final String sourceSha256;
        private final int argumentCount;

        Launcher(String suffix, long sourceBytes, String sourceSha256, int argumentCount) {
            this.suffix = suffix;
            this.sourceBytes = sourceBytes;
            this.sourceSha256 = sourceSha256;
            this.argumentCount = argumentCount;
        }

        public String binaryName() { return PACKAGE + suffix; }
        public String sourceRelativePath() { return binaryName().replace('.', '/') + ".java"; }
        public int argumentCount() { return argumentCount; }
        public List<String> runtimeBinaryNames() {
            var names = new ArrayList<String>();
            names.add(binaryName());
            names.addAll(HELPER_CLASSES);
            return List.copyOf(names);
        }
    }

    private static final String PACKAGE = "org.xar.ck3.control.wave2.finance.";
    private static final String HELPER = PACKAGE + "capture.PythonStdinCapture";
    private static final String MODULE = "wave2-finance";
    private static final long HELPER_BYTES = 13931;
    private static final String HELPER_SHA256 = "e8302b05176baa52b3f732b29697c03ff19758c158f865943f8a50a796946534";
    private static final long PYTHON_BYTES = 254832;
    private static final String PYTHON_SHA256 = "d70fced7f461f38f9f224d8673fb74e96e4facb4283ff4e8697543b457fea8a0";
    private static final List<String> HELPER_CLASSES = List.of(HELPER, HELPER + "$Invocation",
            HELPER + "$Result", HELPER + "$Starter", HELPER + "$ProcessTree");

    /**
     * Metadata lives outside the unchanged seven-field capture row. Runtime class
     * references must also occur explicitly in that row's input_refs.
     * Caller and compiler tool receipts are separate: provenance is not inferred
     * by assuming that two different tool versions are the same runtime.
     */
    public record Profile(Kind profile, Launcher launcher,
            ControlBuild.FileRef captureReceiptRef, ControlBuild.FileRef testCompilationRef,
            ControlBuild.FileRef callerToolsReceiptRef, ControlBuild.FileRef producerToolsReceiptRef,
            String classRoot, List<ControlBuild.FileRef> runtimeClassRefs) {
        public Profile {
            Objects.requireNonNull(profile); Objects.requireNonNull(launcher);
            if (profile != Kind.QUALIFIED_TEST_CLASSES_V1) throw new IllegalArgumentException("Explicit compiled profile required");
            captureReceiptRef = canonical(captureReceiptRef);
            testCompilationRef = canonical(testCompilationRef);
            callerToolsReceiptRef = canonical(callerToolsReceiptRef);
            producerToolsReceiptRef = canonical(producerToolsReceiptRef);
            Path root = canonicalPath(classRoot);
            classRoot = root.toString();
            // Shape-only envelope bound; validate() delegates profile-specific 2/4 MiB admission to the shared completed readers.
            if (captureReceiptRef.bytes() < 1 || captureReceiptRef.bytes() > ControlBuild.BUILD_RECEIPT_ENVELOPE_MAX_BYTES
                    || callerToolsReceiptRef.bytes() < 1 || callerToolsReceiptRef.bytes() > ControlBuild.BUILD_RECEIPT_ENVELOPE_MAX_BYTES
                    || producerToolsReceiptRef.bytes() < 1 || producerToolsReceiptRef.bytes() > ControlBuild.BUILD_RECEIPT_ENVELOPE_MAX_BYTES
                    || testCompilationRef.bytes() < 1 || testCompilationRef.bytes() > (4 << 20)) {
                throw new IllegalArgumentException("Finite exact typed receipts and test compilation manifest required");
            }
            runtimeClassRefs = canonicalRefs(runtimeClassRefs, 6);
            if (runtimeClassRefs.size() != 6) throw new IllegalArgumentException("One main and all five helper binaries required");
            List<String> names = launcher.runtimeBinaryNames();
            for (int index = 0; index < names.size(); index++) {
                ControlBuild.FileRef ref = runtimeClassRefs.get(index);
                Path expected = root.resolve(names.get(index).replace('.', '/') + ".class");
                if (!Path.of(ref.path()).equals(expected) || ref.bytes() < 1 || ref.bytes() > 262144) {
                    throw new IllegalArgumentException("Ordered exact main/helper class paths required");
                }
            }
        }
    }

    /** Evidence of this narrow validation only; tests remain NOT_RUN. */
    public record Proof(Profile profile, ControlBuild.CaptureQualification qualification,
            ControlBuild.CaptureTestState tests, List<ControlBuild.FileRef> callerRuntimeClosure,
            List<ControlBuild.FileRef> compilerRuntimeClosure,
            List<ControlBuild.FileRef> compiledSourceRefs, List<ControlBuild.FileRef> originalSourceRefs,
            List<ControlBuild.FileRef> completeFinanceRuntimeClassRefs) {
        public Proof {
            Objects.requireNonNull(profile);
            if (qualification != ControlBuild.CaptureQualification.TEST_COMPILED_CAPTURE_ONLY
                    || tests != ControlBuild.CaptureTestState.NOT_RUN) {
                throw new IllegalArgumentException("Capture-only proof cannot claim executed tests");
            }
            callerRuntimeClosure = List.copyOf(callerRuntimeClosure);
            compilerRuntimeClosure = List.copyOf(compilerRuntimeClosure);
            compiledSourceRefs = List.copyOf(compiledSourceRefs);
            originalSourceRefs = List.copyOf(originalSourceRefs);
            completeFinanceRuntimeClassRefs = canonicalRefs(completeFinanceRuntimeClassRefs, 9);
            if (completeFinanceRuntimeClassRefs.size() != 9) {
                throw new IllegalArgumentException("All four finance mains and all five shared helper binaries required");
            }
        }
    }

    private CompiledCaptureInputProfile() { }

    /** Input tree must come from the shared strict parser; conversion also rejects unknown/coerced/missing fields. */
    public static Profile parse(JsonNode value) throws IOException {
        Objects.requireNonNull(value);
        try { return ControlBuild.strictMapper().treeToValue(value, Profile.class); }
        catch (RuntimeException error) { throw new IOException("Invalid typed compiled capture profile", error); }
    }

    /**
     * Complete shared readers run here; parsing or constructor validation alone
     * can never grant .class admission. Reinvoke this API after child Job0.
     */
    public static Proof validate(Profile profile, String cwd, List<String> command, String outputPath,
            List<ControlBuild.FileRef> sourceRefs, List<ControlBuild.FileRef> inputRefs) throws IOException {
        Objects.requireNonNull(profile);
        sourceRefs = canonicalRefs(sourceRefs, 64);
        inputRefs = canonicalRefs(inputRefs, 64);
        rejectCompiledSources(sourceRefs);
        for (ControlBuild.FileRef ref : List.of(profile.callerToolsReceiptRef(), profile.producerToolsReceiptRef(),
                profile.captureReceiptRef(), profile.testCompilationRef())) ref.verify();

        ControlBuild.BuildReceipt callerTools = ControlBuild.verifiedCompletedReceipt(profile.callerToolsReceiptRef());
        ControlBuild.BuildReceipt compilerTools = ControlBuild.verifiedCompletedReceipt(profile.producerToolsReceiptRef());
        requireTools(callerTools); requireTools(compilerTools);
        requireLoadedCallerClosure(callerTools.completeDeployment());

        ControlBuild.CaptureBuildReceipt capture = ControlBuild.verifiedCompletedCaptureReceipt(profile.captureReceiptRef());
        require(capture.testCompilationRef().equals(profile.testCompilationRef()), "Profile manifest differs from accepted capture producer");
        require(capture.producerRuntimePins().equals(compilerTools.completeDeployment()),
                "Capture compiler producer closure differs from its independently accepted complete tool deployment");
        require(capture.machineId().equals(callerTools.machineId()) && capture.machineId().equals(compilerTools.machineId()),
                "Caller, compiler and capture machine identities differ");
        requireExactCommand(profile, command, capture.javaExecutableRef());
        requireRowOutput(command, outputPath);
        ControlBuild.FileRef interpreter = requireCaptureArguments(profile.launcher(), cwd, command, inputRefs);
        Set<ControlBuild.FileRef> expectedInputs = new HashSet<>(profile.runtimeClassRefs()); expectedInputs.add(interpreter);
        require(Set.copyOf(inputRefs).equals(expectedInputs), "Compiled finance input_refs are exactly the six runtime classes and actual interpreter");

        byte[] manifestBytes = readPinned(profile.testCompilationRef(), 4 << 20);
        ControlBuild.TestCompilationManifest manifest = ControlBuild.strictMapper().readValue(manifestBytes,
                ControlBuild.TestCompilationManifest.class);
        require(manifest.machineId().equals(capture.machineId())
                && manifest.tests() == ControlBuild.CaptureTestState.NOT_RUN, "Actual same-machine NOT_RUN compilation required");
        Path snapshot = canonicalExistingDirectory(capture.compiledSourceRoot());
        Path module = canonicalExistingDirectory(snapshot.resolve(MODULE).toString());
        Path classRoot = canonicalExistingDirectory(profile.classRoot());
        List<ControlBuild.FileRef> completeClasses = validateFinanceCompilation(manifest, classRoot,
                module, capture.compiledSourcePins());

        Path testSources = module.resolve("src/test/java");
        ControlBuild.FileRef main = exactRef(capture.compiledSourcePins(), testSources.resolve(profile.launcher().sourceRelativePath()));
        ControlBuild.FileRef helper = exactRef(capture.compiledSourcePins(), testSources.resolve(HELPER.replace('.', '/') + ".java"));
        require(main.bytes() == profile.launcher().sourceBytes && main.sha256().equals(profile.launcher().sourceSha256)
                && helper.bytes() == HELPER_BYTES && helper.sha256().equals(HELPER_SHA256),
                "Compiled launchers/helper differ from immutable original-capture source-manifest04 contract");
        List<ControlBuild.FileRef> compiledSources = List.of(main, helper);
        List<ControlBuild.FileRef> originalSources = new ArrayList<>();
        Path sourceRoot = canonicalExistingDirectory(capture.sourceRoot());
        for (ControlBuild.FileRef source : compiledSources) {
            Path originalPath = sourceRoot.resolve(snapshot.relativize(Path.of(source.path())));
            ControlBuild.FileRef original = exactRef(capture.sourcePins(), originalPath);
            require(original.bytes() == source.bytes() && original.sha256().equals(source.sha256()),
                    "Original and compiled source provenance differ");
            require(sourceRefs.contains(source) && sourceRefs.contains(original),
                    "Both original and compiled Java sources must be explicit source_refs");
            originalSources.add(original);
        }
        requireManifestClasses(profile, manifest, main, helper, classRoot, module, capture.compiledSourcePins());
        Set<ControlBuild.FileRef> declaredClasses = new HashSet<>();
        for (ControlBuild.FileRef ref : inputRefs) if (ref.path().endsWith(".class")) declaredClasses.add(ref);
        require(declaredClasses.equals(Set.copyOf(profile.runtimeClassRefs())),
                "Every and only this main/helper class must occur explicitly in input_refs");
        Set<ControlBuild.FileRef> qualifiedJavaSources = new HashSet<>(compiledSources); qualifiedJavaSources.addAll(originalSources);
        Path repository = canonicalExistingDirectory(cwd);
        for (ControlBuild.FileRef ref : sourceRefs) {
            require(ref.bytes() <= (8L << 20) && (qualifiedJavaSources.contains(ref) || Path.of(ref.path()).startsWith(repository)),
                    "Only the exact original/compiled Java sources or finite repository source closure may be hashed");
            ref.verify();
        }
        for (ControlBuild.FileRef ref : inputRefs) ref.verify();
        for (ControlBuild.FileRef ref : List.of(profile.callerToolsReceiptRef(), profile.producerToolsReceiptRef(),
                profile.captureReceiptRef(), profile.testCompilationRef())) ref.verify();
        return new Proof(profile, capture.qualification(), capture.tests(), callerTools.completeDeployment(),
                compilerTools.completeDeployment(), compiledSources, originalSources, completeClasses);
    }

    /** Shared inventory sub-boundary, also exercised with genuine-derived negative manifests by integration CI. */
    static List<ControlBuild.FileRef> validateFinanceCompilation(ControlBuild.TestCompilationManifest manifest,
            Path classRoot, Path module, List<ControlBuild.FileRef> compiledSources) throws IOException {
        ControlBuild.FileRef pom = exactRef(compiledSources, module.resolve("pom.xml"));
        List<ControlBuild.ModuleTestCompilation> modules = manifest.modules().stream()
                .filter(item -> item.modulePomRef().equals(pom)).toList();
        require(modules.size() == 1 && modules.getFirst().classOutputRoot().equals(classRoot.toString()),
                "Exact compiled finance module and its actual canonical test output required");
        modules.getFirst().compilerInputsRef().verify(); modules.getFirst().compilerCreatedFilesRef().verify();
        var result = new ArrayList<ControlBuild.FileRef>();
        var expectedSources = new ArrayList<ControlBuild.FileRef>();
        Path sources = module.resolve("src/test/java");
        for (Launcher launcher : Launcher.values()) {
            ControlBuild.FileRef source = exactRef(compiledSources, sources.resolve(launcher.sourceRelativePath()));
            require(source.bytes() == launcher.sourceBytes && source.sha256().equals(launcher.sourceSha256),
                    "A finance capture main differs from the original source-manifest04 contract");
            expectedSources.add(source);
        }
        ControlBuild.FileRef helper = exactRef(compiledSources, sources.resolve(HELPER.replace('.', '/') + ".java"));
        require(helper.bytes() == HELPER_BYTES && helper.sha256().equals(HELPER_SHA256),
                "The complete finance helper differs from its immutable source contract");
        expectedSources.add(helper);
        for (ControlBuild.FileRef source : expectedSources) {
            List<ControlBuild.NotRunTestCompilation> entries = manifest.notRunTests().stream()
                    .filter(item -> item.sourceRef().equals(source)).toList();
            require(entries.size() == 1 && entries.getFirst().state() == ControlBuild.CaptureTestState.NOT_RUN,
                    "Exactly one actual NOT_RUN compilation entry per capture source required");
            List<String> names = source.equals(helper) ? HELPER_CLASSES : List.of(Launcher.values()[expectedSources.indexOf(source)].binaryName());
            List<ControlBuild.FileRef> observed = entries.getFirst().compiledClassRefs();
            require(observed.size() == names.size(), "Exact complete finance capture binary count required");
            for (String name : names) {
                Path expected = classRoot.resolve(name.replace('.', '/') + ".class");
                List<ControlBuild.FileRef> matches = observed.stream().filter(ref -> Path.of(ref.path()).equals(expected)).toList();
                require(matches.size() == 1, "Actual compiler inventory must contain the expected finance binary exactly once");
                ControlBuild.FileRef ref = matches.getFirst();
                var origin = CompiledClassProvenance.attest(classRoot, ref, module,
                        CompiledClassProvenance.SourceSet.TEST, compiledSources);
                require(origin.sourceRef().equals(source) && origin.binaryName().equals(name),
                        "Finance binary internal name/SourceFile must match its exact compiler input");
                result.add(ref);
            }
        }
        require(result.size() == 9 && result.stream().map(ControlBuild.FileRef::path).distinct().count() == 9,
                "The accepted manifest must bind all nine distinct finance capture binaries");
        return List.copyOf(result);
    }

    private static void requireManifestClasses(Profile profile, ControlBuild.TestCompilationManifest manifest,
            ControlBuild.FileRef main, ControlBuild.FileRef helper, Path classRoot, Path module,
            List<ControlBuild.FileRef> compiledSources) throws IOException {
        List<ControlBuild.NotRunTestCompilation> selected = manifest.notRunTests().stream()
                .filter(item -> item.sourceRef().equals(main) || item.sourceRef().equals(helper)).toList();
        require(selected.size() == 2, "Exactly two actual compiler input entries required");
        Set<ControlBuild.FileRef> expected = Set.copyOf(profile.runtimeClassRefs());
        Set<ControlBuild.FileRef> observed = new HashSet<>();
        for (ControlBuild.NotRunTestCompilation entry : selected) {
            require(entry.state() == ControlBuild.CaptureTestState.NOT_RUN, "Compiler inventory must not claim JUnit results");
            for (ControlBuild.FileRef ref : entry.compiledClassRefs()) {
                require(observed.add(ref), "Repeated class provenance entry");
                var origin = CompiledClassProvenance.attest(classRoot, ref, module,
                        CompiledClassProvenance.SourceSet.TEST, compiledSources);
                require(origin.sourceRef().equals(entry.sourceRef()), "Actual binary SourceFile differs from recorded compiler input");
                require(profile.launcher().runtimeBinaryNames().contains(origin.binaryName()), "Unexpected runtime binary name");
            }
        }
        require(observed.equals(expected), "Actual complete main/helper compiler-created binaries differ from the six outer inputs");
    }

    /** Strict compiled invocation; a second path, source launch, wildcard or option injection is rejected. */
    static void requireExactCommand(Profile profile, List<String> command, ControlBuild.FileRef javaExecutable) throws IOException {
        command = List.copyOf(command);
        require(command.size() == 7 + profile.launcher().argumentCount(), "Exact finite compiled launcher argument count required");
        List<String> prefix = List.of(javaExecutable.path(), "-Xms16m", "-Xmx64m",
                "-Dxar.capture.classRoot=" + profile.classRoot(), "-cp", profile.classRoot(), profile.launcher().binaryName());
        require(command.subList(0, 7).equals(prefix), "Compiled command differs from pinned Java, single class root or known launcher");
        for (String item : command) require(item != null && !item.isEmpty()
                && item.codePoints().noneMatch(point -> point < 32 || point == 127), "Plain finite command arguments required");
        javaExecutable.verify();
    }

    static void requireRowOutput(List<String> command, String outputPath) throws IOException {
        Path output = canonicalPath(outputPath);
        require(!command.isEmpty() && command.getLast().equals(output.toString()),
                "Actual compiled launcher output must equal the unchanged capture row output_path");
    }

    private static ControlBuild.FileRef requireCaptureArguments(Launcher launcher, String cwd, List<String> command,
            List<ControlBuild.FileRef> inputRefs) throws IOException {
        Path repository = canonicalExistingDirectory(cwd);
        ControlBuild.FileRef interpreter = new ControlBuild.FileRef(repository.resolve("tools/.venv/Scripts/python.exe").toString(),
                PYTHON_BYTES, PYTHON_SHA256);
        int pythonIndex = launcher.argumentCount() == 3 ? 7 : 8;
        int repositoryIndex = launcher.argumentCount() == 3 ? 8 : 7;
        require(command.get(pythonIndex).equals(interpreter.path()) && command.get(repositoryIndex).equals(repository.toString()),
                "Actual Python/repository positional arguments must match the outer cwd and existing exact interpreter profile");
        require(inputRefs.contains(interpreter), "The actually invoked pinned interpreter must be an explicit input_ref");
        interpreter.verify();
        canonicalPath(command.getLast());
        if (launcher.argumentCount() == 4) canonicalPath(command.get(9));
        return interpreter;
    }

    private static void requireTools(ControlBuild.BuildReceipt tools) throws IOException {
        require(tools.targetKind() == ControlBuild.TargetKind.BUILD_TOOLS_RUNTIME
                && tools.mavenToolchain().selection() == ControlBuild.MavenSelection.DEFAULT_COMMAND,
                "Default full-verify build-tools qualification required separately from capture-only receipt");
    }

    static void requireLoadedCallerClosure(List<ControlBuild.FileRef> qualified) throws IOException {
        require(ControlBuild.producerClosure().equals(qualified), "Actual caller tool archive/lib closure differs from full-verify qualification");
        Set<Path> expected = new HashSet<>();
        for (ControlBuild.FileRef ref : qualified) {
            Path path = canonicalPath(ref.path());
            require(path.toRealPath().equals(path) && expected.add(path), "Canonical distinct tool runtime paths required");
            ref.verify();
        }
        Set<Path> classpath = new HashSet<>();
        for (String entry : System.getProperty("java.class.path", "").split(java.io.File.pathSeparator, -1)) {
            Path path = canonicalPath(entry);
            require(Files.isRegularFile(path) && path.toRealPath().equals(path) && classpath.add(path),
                    "Tool classpath must name only canonical distinct qualified archives");
        }
        require(classpath.equals(expected), "Full caller classpath differs from qualified deployment closure");
        Set<Path> loaded = new HashSet<>();
        List<Class<?>> symbols = List.of(CompiledCaptureInputProfile.class, ControlBuild.class, WindowsJobProcess.class,
                CompiledClassProvenance.class, com.fasterxml.jackson.annotation.JsonProperty.class,
                com.fasterxml.jackson.core.JsonFactory.class, com.fasterxml.jackson.databind.ObjectMapper.class,
                com.sun.jna.Native.class, com.sun.jna.platform.win32.Kernel32.class);
        for (Class<?> symbol : symbols) {
            var origin = symbol.getProtectionDomain().getCodeSource();
            require(symbol.getClassLoader() == ControlBuild.class.getClassLoader() && origin != null
                    && origin.getLocation() != null && origin.getLocation().getProtocol().equals("file"),
                    "Known shared runtime symbols must use the qualified file loader");
            try {
                Path path = Path.of(origin.getLocation().toURI()).toRealPath();
                require(expected.contains(path), "Actually loaded shared symbol is outside the qualified runtime closure");
                loaded.add(path);
            } catch (java.net.URISyntaxException error) { throw new IOException("Invalid loaded shared runtime origin", error); }
        }
        require(loaded.equals(expected), "This version requires evidence for every qualified runtime archive");
    }

    private static void rejectCompiledSources(List<ControlBuild.FileRef> sourceRefs) throws IOException {
        for (ControlBuild.FileRef ref : sourceRefs) {
            String name = Path.of(ref.path()).getFileName().toString().toLowerCase(java.util.Locale.ROOT);
            require(!name.endsWith(".class") && !name.endsWith(".jar") && !name.endsWith(".exe") && !name.endsWith(".dll"),
                    "Binary artifacts never belong to source_refs");
        }
    }

    private static ControlBuild.FileRef exactRef(List<ControlBuild.FileRef> refs, Path expected) throws IOException {
        List<ControlBuild.FileRef> matches = refs.stream().filter(ref -> Path.of(ref.path()).equals(expected)).toList();
        require(matches.size() == 1, "Exactly one pinned source at expected module/source-set path required");
        matches.getFirst().verify(); return matches.getFirst();
    }

    private static byte[] readPinned(ControlBuild.FileRef ref, int maximum) throws IOException {
        ref.verify();
        require(ref.bytes() >= 1 && ref.bytes() <= maximum, "Finite pinned JSON required");
        byte[] raw;
        try (var input = Files.newInputStream(Path.of(ref.path()))) { raw = input.readNBytes(maximum + 1); }
        require(raw.length == ref.bytes() && raw.length <= maximum, "Pinned JSON changed size while reading");
        try {
            String sha256 = java.util.HexFormat.of().formatHex(java.security.MessageDigest.getInstance("SHA-256").digest(raw));
            require(sha256.equals(ref.sha256()), "Read JSON bytes differ from exact pinned content");
        } catch (java.security.NoSuchAlgorithmException error) { throw new IllegalStateException(error); }
        ref.verify(); return raw;
    }

    private static List<ControlBuild.FileRef> canonicalRefs(List<ControlBuild.FileRef> refs, int maximum) {
        Objects.requireNonNull(refs);
        if (refs.size() > maximum) throw new IllegalArgumentException("Finite exact reference list required");
        List<ControlBuild.FileRef> result = refs.stream().map(CompiledCaptureInputProfile::canonical).toList();
        if (result.stream().map(ControlBuild.FileRef::path).distinct().count() != result.size()) {
            throw new IllegalArgumentException("Duplicate/conflicting reference paths are forbidden");
        }
        return result;
    }

    private static ControlBuild.FileRef canonical(ControlBuild.FileRef ref) {
        Objects.requireNonNull(ref);
        return new ControlBuild.FileRef(canonicalPath(ref.path()).toString(), ref.bytes(), ref.sha256());
    }

    private static Path canonicalPath(String value) {
        Objects.requireNonNull(value);
        Path raw = Path.of(value);
        if (!raw.isAbsolute() || !raw.equals(raw.toAbsolutePath().normalize())) {
            throw new IllegalArgumentException("Absolute lexical canonical paths required; aliases are forbidden");
        }
        return raw;
    }

    private static Path canonicalExistingDirectory(String value) throws IOException {
        Path path = canonicalPath(value);
        require(Files.isDirectory(path) && path.toRealPath().equals(path), "Actual canonical directory required");
        return path;
    }

    private static void require(boolean condition, String message) throws IOException {
        if (!condition) throw new IOException(message);
    }
}
