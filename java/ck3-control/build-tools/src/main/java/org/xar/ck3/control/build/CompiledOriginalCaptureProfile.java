package org.xar.ck3.control.build;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Set;

/** Manifest-selected original captures. This does not widen the separate closed finance profile. */
public final class CompiledOriginalCaptureProfile {
    public static final String DIRECTORY_SCHEMA = "xar.compiled-original-directory-manifest/v1";
    public enum InvocationKind { MAIN, REFERENCE_MAIN, JAVA_MAIN, SOURCE_EXPORT }
    public enum ArgumentKind { REPOSITORY, INTERPRETER, OUTPUT, SCRATCH, INPUT_FILE,
        INPUT_DIRECTORY, INPUT_DIRECTORY_ANCHOR, EXISTING_OWNED_DIRECTORY, MACHINE_ID, LITERAL }
    public enum DirectoryPreparation { EXISTING, CREATE_EMPTY }
    enum Context { CALLER, CHILD }

    public record Argument(ArgumentKind kind, String value, ControlBuild.FileRef fileRef) {
        public Argument {
            Objects.requireNonNull(kind); plain(value);
            if ((kind == ArgumentKind.INPUT_FILE) != (fileRef != null)) throw new IllegalArgumentException("Only input-file arguments carry exact refs");
            if (fileRef != null && !canonical(fileRef.path()).toString().equals(value)) throw new IllegalArgumentException("Input argument/ref disagree");
            if (kind == ArgumentKind.LITERAL && Path.of(value).isAbsolute()) throw new IllegalArgumentException("Absolute inputs need typed path roles");
        }
    }
    public record Selection(String binaryName, ControlBuild.FileRef compiledSourceRef,
            List<ControlBuild.FileRef> modulePomRefs, List<ControlBuild.FileRef> runtimeJarRefs) {
        public Selection {
            if (binaryName == null || !binaryName.matches("[A-Za-z_$][A-Za-z0-9_$]*(\\.[A-Za-z_$][A-Za-z0-9_$]*)*")
                    || binaryName.length() > 256) throw new IllegalArgumentException("Explicit binary name required");
            compiledSourceRef = ref(compiledSourceRef);
            if (!Path.of(compiledSourceRef.path()).getFileName().toString().contains("Capture")
                    || !compiledSourceRef.path().endsWith(".java")) throw new IllegalArgumentException("An explicit original Capture Java source is required");
            modulePomRefs = refs(modulePomRefs, 1, 8); runtimeJarRefs = refs(runtimeJarRefs, 0, 64);
            for (var jar : runtimeJarRefs) if (!jar.path().endsWith(".jar")) throw new IllegalArgumentException("Declared runtime libraries must be JARs");
        }
    }
    public record Profile(ControlBuild.FileRef captureReceiptRef, ControlBuild.FileRef testCompilationRef,
            ControlBuild.FileRef callerToolsReceiptRef, ControlBuild.FileRef producerToolsReceiptRef,
            Selection selection, InvocationKind invocation, ControlBuild.FileRef interpreterRef,
            List<Argument> arguments, List<DirectoryArgument> directories, List<ControlBuild.FileRef> referencedInputs,
            ControlBuild.FileRef referenceActualRef) {
        public Profile {
            captureReceiptRef = receipt(captureReceiptRef); callerToolsReceiptRef = receipt(callerToolsReceiptRef);
            producerToolsReceiptRef = receipt(producerToolsReceiptRef); testCompilationRef = ref(testCompilationRef);
            if (testCompilationRef.bytes() < 1 || testCompilationRef.bytes() > (4 << 20)) throw new IllegalArgumentException("Bounded genuine test manifest required");
            Objects.requireNonNull(selection); Objects.requireNonNull(invocation); arguments = List.copyOf(arguments);
            directories = List.copyOf(directories);
            referencedInputs = refs(referencedInputs, 0, 8192);
            if ((invocation == InvocationKind.REFERENCE_MAIN) != (referenceActualRef != null))
                throw new IllegalArgumentException("Only reference main requires an explicit reference actual pin");
            if (referenceActualRef != null) {
                referenceActualRef = ref(referenceActualRef);
                if (referenceActualRef.bytes() < 1 || referenceActualRef.bytes() > (2 << 20))
                    throw new IllegalArgumentException("Bounded reference actual pin required");
            }
            if (arguments.size() > 32) throw new IllegalArgumentException("Finite explicit original argv required");
            if (directories.size() > 16 || directories.stream().map(DirectoryArgument::path).distinct().count() != directories.size())
                throw new IllegalArgumentException("Finite distinct typed directory arguments required");
            var directoryArgs = arguments.stream().filter(item -> item.kind() == ArgumentKind.INPUT_DIRECTORY
                    || item.kind() == ArgumentKind.INPUT_DIRECTORY_ANCHOR || item.kind() == ArgumentKind.EXISTING_OWNED_DIRECTORY).toList();
            List<DirectoryArgument> declaredDirectories = directories;
            if (directoryArgs.stream().anyMatch(arg -> declaredDirectories.stream()
                    .filter(item -> item.kind() == arg.kind() && item.path().equals(arg.value())).count() != 1)
                    || directories.stream().filter(item -> item.kind() != ArgumentKind.EXISTING_OWNED_DIRECTORY).anyMatch(item -> directoryArgs.stream()
                        .noneMatch(arg -> arg.kind() == item.kind() && arg.value().equals(item.path()))))
                throw new IllegalArgumentException("Every directory argv needs exactly one typed initial inventory");
            if (invocation == InvocationKind.SOURCE_EXPORT) {
                if (!arguments.isEmpty() || interpreterRef != null || !directories.isEmpty() || !referencedInputs.isEmpty()) throw new IllegalArgumentException("Source export invokes source() only; no Python/bootstrap arguments");
            } else if (invocation == InvocationKind.MAIN || invocation == InvocationKind.REFERENCE_MAIN) {
                interpreterRef = ref(interpreterRef);
                for (ArgumentKind kind : List.of(ArgumentKind.REPOSITORY, ArgumentKind.INTERPRETER, ArgumentKind.OUTPUT)) {
                    if (arguments.stream().filter(item -> item.kind() == kind).count() != 1) throw new IllegalArgumentException("Main requires one typed repository/interpreter/output argument");
                }
            } else if (interpreterRef != null || arguments.stream().anyMatch(item -> item.kind() == ArgumentKind.INTERPRETER)
                    || arguments.stream().filter(item -> item.kind() == ArgumentKind.OUTPUT).count() != 1) {
                throw new IllegalArgumentException("Java main has no interpreter and exactly one typed output argument");
            }
        }
    }
    public record DirectoryEntry(String relative, SharedSourceFiles.DirectoryIdentity identity) {
        public DirectoryEntry {
            Objects.requireNonNull(identity); plain(relative); Path path = Path.of(relative);
            if (path.isAbsolute() || !path.equals(path.normalize()) || path.startsWith("..") || relative.equals("."))
                throw new IllegalArgumentException("Canonical relative directory entry required");
        }
    }
    /** Exact ordinary directory inventory, including empty directories and native identities. */
    public record DirectoryManifest(String schema, String machineId, String observedAtUtc, String root, SharedSourceFiles.DirectoryIdentity identity,
            List<DirectoryEntry> directories, List<SharedSourceFiles.Witness> files) {
        public DirectoryManifest {
            if (!DIRECTORY_SCHEMA.equals(schema) || machineId == null || machineId.isBlank()) throw new IllegalArgumentException("Versioned observed directory machine required");
            java.time.Instant.parse(observedAtUtc);
            Path boundary = canonical(root); Objects.requireNonNull(identity);
            directories = List.copyOf(directories); files = List.copyOf(files);
            if (directories.size() + files.size() > 4096
                    || directories.stream().map(DirectoryEntry::relative).distinct().count() != directories.size()
                    || files.stream().map(item -> item.source().path()).distinct().count() != files.size()
                    || files.stream().anyMatch(item -> !Path.of(item.source().path()).startsWith(boundary)
                        || Path.of(item.source().path()).equals(boundary))) throw new IllegalArgumentException("Finite distinct directory inventory required");
            long total = 0;
            for (var file : files) {
                if (file.source().bytes() < 0 || file.source().bytes() > (8L << 20)
                        || file.source().bytes() != file.nativeFile().logicalBytes()) throw new IllegalArgumentException("Exact bounded file witness required");
                total = Math.addExact(total, file.source().bytes());
            }
            if (total > (64L << 20)) throw new IllegalArgumentException("Finite directory input byte extent required");
        }
        public static DirectoryManifest measure(Path root, long maximumBytes) throws IOException {
            require(maximumBytes > 0 && maximumBytes <= (64L << 20), "Finite directory observation byte bound required");
            Path boundary = directory(root.toString()); SharedSourceFiles.plainAncestors(boundary);
            var identity = SharedSourceFiles.nativeDirectory(boundary);
            var dirs = new ArrayList<DirectoryEntry>(); var files = new ArrayList<SharedSourceFiles.Witness>(); long total = 0;
            try (var walk = Files.walk(boundary)) {
                var paths = walk.iterator(); int count = 0;
                while (paths.hasNext()) {
                    Path path = paths.next(); require(++count <= 4097, "Finite directory entries required");
                    SharedSourceFiles.plainAncestors(path);
                    if (path.equals(boundary)) continue;
                    if (Files.isDirectory(path, LinkOption.NOFOLLOW_LINKS)) {
                        dirs.add(new DirectoryEntry(boundary.relativize(path).toString(), SharedSourceFiles.nativeDirectory(path)));
                    } else {
                        require(Files.isRegularFile(path, LinkOption.NOFOLLOW_LINKS) && Files.size(path) <= (8L << 20), "Ordinary bounded directory file required");
                        total = Math.addExact(total, Files.size(path)); require(total <= maximumBytes, "Directory bytes exceed declared bound");
                        files.add(SharedSourceFiles.observe(path));
                    }
                }
            }
            require(identity.equals(SharedSourceFiles.nativeDirectory(boundary)), "Directory identity changed during observation");
            dirs.sort(java.util.Comparator.comparing(DirectoryEntry::relative)); files.sort(java.util.Comparator.comparing(item -> item.source().path()));
            return new DirectoryManifest(DIRECTORY_SCHEMA, WindowsJobProcess.currentMachineId(), java.time.Instant.now().toString(), boundary.toString(), identity, dirs, files);
        }
        public boolean sameInventory(DirectoryManifest other) {
            return machineId.equals(other.machineId()) && root.equals(other.root()) && identity.equals(other.identity())
                    && directories.equals(other.directories()) && files.equals(other.files());
        }
        public void verify() throws IOException { require(sameInventory(measure(Path.of(root), 64L << 20)), "Directory inventory or native identity changed"); }
        public void verifyRetained() throws IOException {
            require(machineId.equals(WindowsJobProcess.currentMachineId()), "Directory machine differs from actual observer");
            require(identity.equals(SharedSourceFiles.nativeDirectory(Path.of(root))), "Owned directory identity changed");
            for (var entry : directories) require(entry.identity().equals(SharedSourceFiles.nativeDirectory(Path.of(root).resolve(entry.relative()))), "Initial owned directory changed");
            for (var file : files) require(file.equals(SharedSourceFiles.observe(Path.of(file.source().path()))), "Initial owned file changed");
        }
    }
    public record DirectoryArgument(ArgumentKind kind, String path, DirectoryPreparation preparation, DirectoryManifest inputManifest) {
        public DirectoryArgument {
            path = canonical(path).toString(); Objects.requireNonNull(preparation);
            if (kind != ArgumentKind.INPUT_DIRECTORY && kind != ArgumentKind.INPUT_DIRECTORY_ANCHOR && kind != ArgumentKind.EXISTING_OWNED_DIRECTORY)
                throw new IllegalArgumentException("Explicit immutable input or mutable owned directory role required");
            if ((kind == ArgumentKind.INPUT_DIRECTORY) != (inputManifest != null)
                    || inputManifest != null && !inputManifest.root().equals(path)
                    || kind != ArgumentKind.EXISTING_OWNED_DIRECTORY && preparation != DirectoryPreparation.EXISTING)
                throw new IllegalArgumentException("Only full input directories carry inventory; only owned directories may be prepared");
        }
    }
    public record DirectoryBinding(String path, SharedSourceFiles.DirectoryIdentity identity) {
        public DirectoryBinding { path = canonical(path).toString(); Objects.requireNonNull(identity); }
    }
    public record Inventory(CompiledClassProvenance.Origin entrypoint, List<String> classRoots,
            List<ControlBuild.FileRef> runtimeClasses, List<ControlBuild.FileRef> runtimeResources,
            List<ControlBuild.FileRef> compiledSources) {
        public Inventory {
            Objects.requireNonNull(entrypoint); classRoots = List.copyOf(classRoots);
            runtimeClasses = List.copyOf(runtimeClasses); runtimeResources = List.copyOf(runtimeResources);
            compiledSources = List.copyOf(compiledSources);
        }
    }
    public record Proof(Profile profile, ControlBuild.FileRef javaExecutableRef,
            List<ControlBuild.FileRef> callerRuntime, List<ControlBuild.FileRef> compilerRuntime,
            Inventory inventory, List<ControlBuild.FileRef> originalSources, List<DirectoryBinding> directories,
            ReferenceBinding referenceBinding) {
        public Proof {
            Objects.requireNonNull(profile); javaExecutableRef = ref(javaExecutableRef);
            callerRuntime = List.copyOf(callerRuntime); compilerRuntime = List.copyOf(compilerRuntime);
            Objects.requireNonNull(inventory); originalSources = List.copyOf(originalSources); directories = List.copyOf(directories);
            if ((profile.invocation() == InvocationKind.REFERENCE_MAIN) != (referenceBinding != null)
                    || referenceBinding != null && !referenceBinding.actualRef().equals(profile.referenceActualRef()))
                throw new IllegalArgumentException("Proof reference branch differs from profile");
        }
        public List<String> childClasspath() {
            var result = new ArrayList<String>();
            callerRuntime.forEach(item -> result.add(item.path())); result.addAll(inventory.classRoots());
            profile.selection().runtimeJarRefs().forEach(item -> result.add(item.path()));
            return List.copyOf(result);
        }
    }
    private CompiledOriginalCaptureProfile() { }

    /** Returned only after the existing full reference reader; no import/runtime qualification. */
    public record ReferenceBinding(ControlBuild.FileRef actualRef, ControlBuild.FileRef reviewRef,
            ControlBuild.FileRef requestRef, ControlBuild.FileRef toolsBuildRef, String machineId,
            String graphRoot, String canonicalRepository, String sourceSetSha256,
            List<ControlBuild.FileRef> sourceRefs, List<ControlBuild.FileRef> inputRefs) {
        public ReferenceBinding {
            actualRef = ref(actualRef); reviewRef = ref(reviewRef); requestRef = ref(requestRef); toolsBuildRef = ref(toolsBuildRef);
            plain(machineId); graphRoot = canonical(graphRoot).toString(); canonicalRepository = canonical(canonicalRepository).toString();
            if (sourceSetSha256 == null || !sourceSetSha256.matches("[0-9a-f]{64}"))
                throw new IllegalArgumentException("Reference source-set digest required");
            sourceRefs = refs(sourceRefs, 1, 8192); inputRefs = refs(inputRefs, 1, 8192);
        }
    }

    /** Narrow projection of files the existing construction reference audit actually reads. */
    record ReferenceAuditInputs(ControlBuild.FileRef originalAuditRef, ControlBuild.FileRef separationAuditRef,
            List<ControlBuild.FileRef> originalSources, ControlBuild.FileRef selectedClientRef) {
        ReferenceAuditInputs {
            originalAuditRef = ref(originalAuditRef); separationAuditRef = ref(separationAuditRef);
            originalSources = refs(originalSources, 8, 8); selectedClientRef = ref(selectedClientRef);
        }
        List<ControlBuild.FileRef> checkedRefs() throws IOException {
            var inputs = new java.util.LinkedHashSet<ControlBuild.FileRef>();
            inputs.add(originalAuditRef); inputs.add(separationAuditRef);
            inputs.addAll(originalSources); inputs.add(selectedClientRef);
            var complete = refs(inputs.stream().sorted(java.util.Comparator.comparing(ControlBuild.FileRef::path)).toList(), 1, 11);
            for (var input : complete) input.verify();
            return complete;
        }
    }

    static void requireReferenceInputClosure(List<ControlBuild.FileRef> declared,
            List<ControlBuild.FileRef> required) throws IOException {
        Objects.requireNonNull(declared); Objects.requireNonNull(required);
        require(declared.containsAll(required), "Complete reference reader metadata input closure required");
    }

    /** Typed preparation API for request producers; it never starts a child or creates a view. */
    public static ReferenceBinding readReferenceBinding(ControlBuild.FileRef reference) throws IOException {
        reference = ref(reference);
        var actual = SdkSourceAssembly.readReferenceActual(reference);
        require(actual.purpose() == SdkSourceAssembly.ReferencePurpose.REFERENCE_ORACLE_ONLY,
                "Only original-reference oracle inputs admit an external repository interpreter");
        var witness = SharedSourceFiles.observe(Path.of(actual.reviewRef().path()));
        require(witness.source().equals(actual.reviewRef()), "Reference review differs from actual pin");
        var review = ControlBuild.strictMapper().readValue(CompiledGoldenCapture.readPinned(actual.reviewRef(), 2 << 20),
                SdkSourceAssembly.ReferenceReview.class);
        SharedSourceFiles.assertUnchanged(witness);
        var fresh = SdkSourceAssembly.reviewReference(review.requestRef());
        require(review.machineId().equals(actual.machineId()) && review.request().purpose() == actual.purpose()
                && review.selectedSourceSetSha256().equals(actual.sourceSetSha256())
                && fresh.request().equals(review.request())
                && fresh.parentSourceReview().request().equals(review.parentSourceReview().request())
                && fresh.selectedSourceSetSha256().equals(actual.sourceSetSha256()), "Typed reference review differs from actual");
        var inputs = new java.util.LinkedHashSet<ControlBuild.FileRef>();
        inputs.addAll(List.of(reference, actual.reviewRef(), review.requestRef(), actual.storageEvidence(),
                review.request().sourceTemplateRef(), review.request().qualifiedToolsBuildRef(), review.request().constructionRequestRef()));
        var construction = ConstructionOracleAssemblyRequest.read(
                CompiledGoldenCapture.readPinned(review.request().constructionRequestRef(), 16384));
        inputs.addAll(new ReferenceAuditInputs(construction.originalAuditRef(), construction.separationAuditRef(),
                construction.referenceSources().stream().map(ConstructionOracleAssemblyRequest.ReferenceSource::sourceRef).toList(),
                construction.selectedClient().sourceRef()).checkedRefs());
        var tools = ControlBuild.verifiedCompletedReceipt(review.request().qualifiedToolsBuildRef());
        requireTools(tools);
        inputs.addAll(tools.sourcePins()); inputs.addAll(tools.compiledSourcePins());
        inputs.addAll(tools.producerRuntimePins()); inputs.addAll(tools.completeDeployment());
        inputs.add(tools.capacityReleaseRef()); inputs.add(tools.javaExecutableRef());
        inputs.add(tools.mavenToolchain().distributionLauncherRef());
        if (tools.mavenToolchain().explicitOverrideRef() != null) inputs.add(tools.mavenToolchain().explicitOverrideRef());
        inputs.add(review.parentSourceReview().requestRef());
        for (var source : review.parentSourceReview().sourceClosure()) {
            inputs.add(source.original()); for (var overlay : source.overlays()) inputs.add(overlay.patchRef());
        }
        for (var selection : review.request().selections()) {
            if (selection.parentSourceRef() != null) inputs.add(selection.parentSourceRef());
            inputs.add(selection.selectedSourceRef()); inputs.add(selection.auditRef());
        }
        for (var input : inputs) input.verify();
        var sources = actual.actualSourceClosure().stream().map(SdkSourceAssembly.OutputSource::actual)
                .sorted(java.util.Comparator.comparing(ControlBuild.FileRef::path)).toList();
        reference.verify(); SharedSourceFiles.assertUnchanged(witness);
        return new ReferenceBinding(reference, actual.reviewRef(), review.requestRef(), review.request().qualifiedToolsBuildRef(),
                actual.machineId(), actual.graphRoot(), directory(fresh.parentSourceReview().request().canonicalRepository()).toString(),
                actual.sourceSetSha256(), sources, inputs.stream().sorted(java.util.Comparator.comparing(ControlBuild.FileRef::path)).toList());
    }

    static ReferenceBinding requireReferenceBinding(CompiledOriginalCapture.Request request) throws IOException {
        if (request.profile().invocation() != InvocationKind.REFERENCE_MAIN) return null;
        var binding = readReferenceBinding(request.profile().referenceActualRef());
        require(binding.machineId().equals(request.machineId()) && binding.graphRoot().equals(request.cwd()),
                "Reference graph and machine must equal the original request");
        require(binding.toolsBuildRef().equals(request.profile().callerToolsReceiptRef()),
                "Reference assembly and capture must use the same qualified tools build");
        require(request.sourceRefs().containsAll(binding.sourceRefs()), "Complete actual reference sources required");
        requireReferenceInputClosure(request.inputRefs(), binding.inputRefs());
        return binding;
    }

    static void requireInterpreter(Path repository, ControlBuild.FileRef interpreter) throws IOException {
        require(Path.of(interpreter.path()).equals(repository.resolve("tools/.venv/Scripts/python.exe")),
                "Use the exact existing repository interpreter");
        interpreter.verify();
    }

    static Proof validate(CompiledOriginalCapture.Request request, Context context) throws IOException {
        Profile profile = request.profile();
        ReferenceBinding reference = requireReferenceBinding(request);
        for (var item : List.of(profile.captureReceiptRef(), profile.testCompilationRef(),
                profile.callerToolsReceiptRef(), profile.producerToolsReceiptRef())) item.verify();
        var caller = ControlBuild.verifiedCompletedReceipt(profile.callerToolsReceiptRef());
        var compiler = ControlBuild.verifiedCompletedReceipt(profile.producerToolsReceiptRef());
        requireTools(caller); requireTools(compiler);
        require(ControlBuild.producerClosure().equals(caller.completeDeployment()), "Actually loaded tool closure differs from caller qualification");
        if (context == Context.CALLER) CompiledCaptureInputProfile.requireLoadedCallerClosure(caller.completeDeployment());
        var capture = ControlBuild.verifiedCompletedCaptureReceipt(profile.captureReceiptRef());
        require(capture.testCompilationRef().equals(profile.testCompilationRef())
                && capture.producerRuntimePins().equals(compiler.completeDeployment()), "Independent compiler provenance differs");
        require(capture.machineId().equals(caller.machineId()) && capture.machineId().equals(compiler.machineId()), "Caller/compiler/capture machine mismatch");
        var manifest = ControlBuild.strictMapper().readValue(CompiledGoldenCapture.readPinned(profile.testCompilationRef(), 4 << 20),
                ControlBuild.TestCompilationManifest.class);
        require(manifest.machineId().equals(capture.machineId()) && manifest.tests() == ControlBuild.CaptureTestState.NOT_RUN,
                "Actual same-machine NOT_RUN compiler manifest required");
        Path snapshot = directory(capture.compiledSourceRoot()), originalRoot = directory(capture.sourceRoot());
        Inventory inventory = inventory(snapshot, capture.compiledSourcePins(), manifest, profile.selection());
        var originals = new ArrayList<ControlBuild.FileRef>();
        for (var compiled : inventory.compiledSources()) {
            Path original = originalRoot.resolve(snapshot.relativize(Path.of(compiled.path())));
            var matching = capture.sourcePins().stream().filter(item -> Path.of(item.path()).equals(original)).toList();
            require(matching.size() == 1 && matching.getFirst().bytes() == compiled.bytes()
                    && matching.getFirst().sha256().equals(compiled.sha256()), "Original/compiled Java source origins differ");
            originals.add(matching.getFirst());
            require(request.sourceRefs().contains(compiled) && request.sourceRefs().contains(matching.getFirst()),
                    "Every admitted test-class source has explicit original and compiled source refs");
        }
        Set<ControlBuild.FileRef> qualifiedJava = new HashSet<>(inventory.compiledSources()); qualifiedJava.addAll(originals);
        Path repository = directory(request.cwd());
        for (var source : request.sourceRefs()) {
            String name = source.path().toLowerCase(java.util.Locale.ROOT);
            require(!name.endsWith(".class") && !name.endsWith(".jar") && !name.endsWith(".exe") && !name.endsWith(".dll"),
                    "Binary artifacts cannot masquerade as sources");
            require(qualifiedJava.contains(source) || Path.of(source.path()).startsWith(repository), "Source is outside original Java/repository closure");
            source.verify();
        }
        Set<ControlBuild.FileRef> expectedInputs = new HashSet<>(inventory.runtimeClasses()); expectedInputs.addAll(inventory.runtimeResources());
        expectedInputs.addAll(profile.referencedInputs());
        if (reference != null) expectedInputs.addAll(reference.inputRefs());
        for (var jar : profile.selection().runtimeJarRefs()) {
            require(capture.completeDeployment().contains(jar), "Runtime JAR absent from genuine complete capture deployment");
            expectedInputs.add(jar);
        }
        if (profile.interpreterRef() != null) {
            requireInterpreter(reference == null ? repository : directory(reference.canonicalRepository()), profile.interpreterRef());
            expectedInputs.add(profile.interpreterRef());
        }
        for (Argument arg : profile.arguments()) {
            switch (arg.kind()) {
                case REPOSITORY -> require(arg.value().equals(repository.toString()), "Repository argument differs from cwd");
                case INTERPRETER -> require(arg.value().equals(profile.interpreterRef().path()), "Interpreter argument differs from exact pin");
                case OUTPUT -> require(arg.value().equals(request.outputPath()), "Original main output differs from declared output");
                case INPUT_FILE -> expectedInputs.add(arg.fileRef());
                case MACHINE_ID -> require(arg.value().equals(capture.machineId()), "Machine argument differs from real producer identity");
                case SCRATCH -> { canonical(arg.value()); }
                case INPUT_DIRECTORY, INPUT_DIRECTORY_ANCHOR, EXISTING_OWNED_DIRECTORY -> { /* Typed directory binding below. */ }
                case LITERAL -> { /* Existing original argv only; no generated Python implementation. */ }
            }
        }
        var bindings = new ArrayList<DirectoryBinding>();
        for (var argument : profile.directories()) {
            if (argument.kind() == ArgumentKind.INPUT_DIRECTORY) {
                argument.inputManifest().verify(); argument.inputManifest().files().forEach(item -> expectedInputs.add(item.source()));
            }
            bindings.add(new DirectoryBinding(argument.path(), SharedSourceFiles.nativeDirectory(directory(argument.path()))));
        }
        require(Set.copyOf(request.inputRefs()).equals(expectedInputs), "Input refs differ from actual selected module class inventory, declared JARs and original argv inputs");
        for (var input : request.inputRefs()) input.verify();
        Proof proof = new Proof(profile, capture.javaExecutableRef(), caller.completeDeployment(), compiler.completeDeployment(), inventory, originals, bindings, reference);
        if (context == Context.CHILD) requireClasspath(proof.childClasspath());
        request.profile().captureReceiptRef().verify(); request.profile().testCompilationRef().verify();
        return proof;
    }

    /** Actual compiled-module inventory sub-boundary; no accepted build is manufactured by callers/tests. */
    static Inventory inventory(Path snapshot, List<ControlBuild.FileRef> compiledSources,
            ControlBuild.TestCompilationManifest manifest, Selection selection) throws IOException {
        var roots = new ArrayList<String>(); var classes = new ArrayList<ControlBuild.FileRef>();
        var sources = new ArrayList<ControlBuild.FileRef>(); var resources = new ArrayList<ControlBuild.FileRef>();
        CompiledClassProvenance.Origin entry = null;
        for (var pom : selection.modulePomRefs()) {
            require(compiledSources.contains(pom), "Selected module POM is not an actual compiler input");
            var modules = manifest.modules().stream().filter(item -> item.modulePomRef().equals(pom)).toList();
            require(modules.size() == 1, "Exactly one actual compiler module selected");
            var moduleRecord = modules.getFirst(); moduleRecord.compilerInputsRef().verify(); moduleRecord.compilerCreatedFilesRef().verify();
            Path module = Path.of(pom.path()).getParent(), root = directory(moduleRecord.classOutputRoot());
            require(module.startsWith(snapshot) && !module.equals(snapshot), "Module must belong to the genuine capture snapshot");
            require(!roots.contains(root.toString()), "Repeated class roots forbidden"); roots.add(root.toString());
            var tests = manifest.notRunTests().stream().filter(item -> Path.of(item.sourceRef().path()).startsWith(module.resolve("src/test/java"))).toList();
            require(!tests.isEmpty(), "Selected module has no actual compiled test inventory");
            Set<Path> expectedFiles = new HashSet<>();
            for (var test : tests) {
                require(compiledSources.contains(test.sourceRef()), "Test source absent from actual compiled inputs");
                sources.add(test.sourceRef());
                for (var file : test.compiledClassRefs()) {
                    require(expectedFiles.add(Path.of(file.path())), "Repeated compiler-created class");
                    var origin = CompiledClassProvenance.attest(root, file, module, CompiledClassProvenance.SourceSet.TEST, compiledSources);
                    require(origin.sourceRef().equals(test.sourceRef()), "Class SourceFile differs from its real compiler source");
                    classes.add(file);
                    if (origin.binaryName().equals(selection.binaryName())) {
                        require(entry == null && origin.sourceRef().equals(selection.compiledSourceRef()), "Ambiguous or foreign entrypoint source");
                        entry = origin;
                    }
                }
            }
            var resourcePlan = CompiledTestResourceOrigins.read(snapshot, pom, compiledSources);
            int count = 0; Set<Path> actualFiles = new HashSet<>();
            try (var walk = Files.walk(root)) {
                for (Path file : walk.toList()) {
                    require(++count <= 8192 && !Files.isSymbolicLink(file), "Finite canonical compiled output required");
                    if (Files.isRegularFile(file, LinkOption.NOFOLLOW_LINKS) && file.toString().endsWith(".class")) {
                        require(file.toRealPath().equals(file), "Compiled class alias rejected"); actualFiles.add(file);
                    } else if (Files.isRegularFile(file, LinkOption.NOFOLLOW_LINKS)) {
                        require(file.toRealPath().equals(file), "Classpath resource alias rejected");
                        var copy = resourcePlan.attest(root, file);
                        resources.add(copy.outputRef()); if (!sources.contains(copy.sourceRef())) sources.add(copy.sourceRef());
                    }
                }
            }
            require(actualFiles.equals(expectedFiles), "Classpath directory contains classes outside actual manifest inventory");
        }
        require(entry != null && classes.size() <= 4096 && classes.stream().map(ControlBuild.FileRef::path).distinct().count() == classes.size(),
                "Exactly one real entrypoint in finite distinct selected test-class closure required");
        return new Inventory(entry, roots,
                classes.stream().sorted(java.util.Comparator.comparing(ControlBuild.FileRef::path)).toList(),
                resources.stream().sorted(java.util.Comparator.comparing(ControlBuild.FileRef::path)).toList(),
                sources.stream().sorted(java.util.Comparator.comparing(ControlBuild.FileRef::path)).toList());
    }

    private static void requireTools(ControlBuild.BuildReceipt receipt) throws IOException {
        require(receipt.targetKind() == ControlBuild.TargetKind.BUILD_TOOLS_RUNTIME
                && receipt.mavenToolchain().selection() == ControlBuild.MavenSelection.DEFAULT_COMMAND, "Accepted default full tools build required");
    }
    static void requireClasspath(List<String> expected) throws IOException {
        var actual = new ArrayList<String>();
        for (String item : System.getProperty("java.class.path", "").split(java.io.File.pathSeparator, -1)) actual.add(canonical(item).toRealPath().toString());
        require(actual.equals(expected) && new HashSet<>(actual).size() == actual.size(), "Actual child classpath differs from complete declared qualified closure");
    }
    static Path canonical(String value) {
        plain(value); Path path = Path.of(value);
        if (!path.isAbsolute() || !path.equals(path.toAbsolutePath().normalize())) throw new IllegalArgumentException("Absolute canonical path required");
        return path;
    }
    static Path directory(String value) throws IOException {
        Path path = canonical(value); require(Files.isDirectory(path, LinkOption.NOFOLLOW_LINKS) && path.toRealPath().equals(path), "Actual canonical directory required"); return path;
    }
    static ControlBuild.FileRef ref(ControlBuild.FileRef value) {
        Objects.requireNonNull(value); return new ControlBuild.FileRef(canonical(value.path()).toString(), value.bytes(), value.sha256());
    }
    static List<ControlBuild.FileRef> refs(List<ControlBuild.FileRef> values, int minimum, int maximum) {
        Objects.requireNonNull(values); var result = values.stream().map(CompiledOriginalCaptureProfile::ref).toList();
        if (result.size() < minimum || result.size() > maximum || result.stream().map(ControlBuild.FileRef::path).distinct().count() != result.size()
                || result.stream().anyMatch(item -> item.bytes() < 0 || item.bytes() > (8L << 20))) throw new IllegalArgumentException("Finite distinct pinned refs required");
        return result;
    }
    /** Shape only; validate() uses the shared typed 2/4 MiB completed receipt readers. */
    private static ControlBuild.FileRef receipt(ControlBuild.FileRef value) {
        value = ref(value); if (value.bytes() < 1 || value.bytes() > ControlBuild.BUILD_RECEIPT_ENVELOPE_MAX_BYTES) throw new IllegalArgumentException("Bounded actual receipt required"); return value;
    }
    private static void plain(String value) {
        if (value == null || value.isEmpty() || value.length() > 4096 || value.codePoints().anyMatch(point -> point < 32 || point == 127)) throw new IllegalArgumentException("Plain finite text required");
    }
    static void require(boolean condition, String message) throws IOException { if (!condition) throw new IOException(message); }
}

