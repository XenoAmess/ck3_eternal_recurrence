package org.xar.ck3.control.build;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Instant;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Objects;
import org.xar.ck3.control.build.ControlBuild.FileRef;

/** Post-reactor SDK source/configuration producer. It never starts or closes a host or Python. */
public final class SdkStageConfigurationProducer {
    public static final String SCHEMA = "xar.sdk-stage-production-inputs/v3";
    public static final String PLAN_SCHEMA = "xar.sdk-stage-production-plan/v1";
    private static final long MAX_METADATA = 2L << 20;
    private static final String CLIENT = "tools/g2_saved_campaign/java_map_admission_client_v1.py";
    private static final String CONTINUITY = "tools/g2_saved_campaign/current_saved_continuity_v1.py";
    private static final String OWNER = "tools/g2_saved_campaign/root_current_saved_campaign_cold_owner_v1.py";
    private static final String CLIENT_TEST = "tools/g2_saved_campaign/test_java_projection_client_v1.py";
    private SdkStageConfigurationProducer() { }

    public record ModulePath(String module, String relativeSource) {
        public ModulePath {
            if (module == null || !module.matches("[A-Za-z_][A-Za-z0-9_]*(?:[.][A-Za-z_][A-Za-z0-9_]*)*"))
                throw new IllegalArgumentException("Canonical module required");
            ExactSourcePatch.relative(relativeSource);
            if (!relativeSource.endsWith(".py")) throw new IllegalArgumentException("Actual Python source required");
        }
    }
    public record InterpreterInputs(FileRef pythonExecutable, FileRef basePythonExecutable,
            List<String> dependencyRoots, List<FileRef> dependencySources) {
        public InterpreterInputs {
            Objects.requireNonNull(pythonExecutable); Objects.requireNonNull(basePythonExecutable);
            dependencyRoots = List.copyOf(dependencyRoots); dependencySources = List.copyOf(dependencySources);
            if (dependencyRoots.isEmpty() || dependencyRoots.size() > 32 || dependencySources.isEmpty()
                    || dependencySources.size() > 20000 || dependencyRoots.stream().distinct().count() != dependencyRoots.size())
                throw new IllegalArgumentException("Explicit complete interpreter dependencies required");
            for (String root : dependencyRoots) absolute(root);
        }
    }
    public record FreshInputs(FileRef supportContractRef, List<FileRef> supportSources, FileRef executionCardRef,
            List<ModulePath> additionalModules, long commandMemoryBytes, int timeoutSeconds) {
        public FreshInputs {
            Objects.requireNonNull(supportContractRef); Objects.requireNonNull(executionCardRef);
            supportSources = List.copyOf(supportSources); additionalModules = List.copyOf(additionalModules);
            limits(commandMemoryBytes, timeoutSeconds, 900);
            if (supportSources.isEmpty() || supportSources.size() > 20000 || additionalModules.size() > 128
                    || additionalModules.stream().map(ModulePath::module).distinct().count() != additionalModules.size())
                throw new IllegalArgumentException("Explicit support and unique selected consumers required");
        }
    }
    public record CanonicalInputs(FileRef gitExecutable, FileRef workflowRef, FileRef reviewedWalRef,
            List<FileRef> canonicalSources, FileRef executionCardRef, long commandMemoryBytes, int timeoutSeconds) {
        public CanonicalInputs {
            Objects.requireNonNull(gitExecutable); Objects.requireNonNull(workflowRef);
            Objects.requireNonNull(reviewedWalRef); Objects.requireNonNull(executionCardRef);
            canonicalSources = List.copyOf(canonicalSources); limits(commandMemoryBytes, timeoutSeconds, 2100);
            if (canonicalSources.isEmpty() || canonicalSources.size() > 20000)
                throw new IllegalArgumentException("Original complete canonical source group required");
        }
    }
    /** Source facts before the qualified-tools stage; this interface grants no build or runtime authority. */
    public sealed interface SourceInputs permits ProductionPlan, ProductionInputs {
        String machineId(); String reviewAtUtc();
        FileRef baselineIntentRef(); FileRef legacyIntentRef(); FileRef consumerIntentRef();
        SdkSourceAssembly.LegacyConstraint legacyConstraint(); SdkSourceAssembly.Source32Reuse source32Reuse();
        long sharedViewPhysicalHardBytes(); long allocationUnitBytes(); long perDirectoryGuardBytes();
        FileRef producerGoldenPlanRef(); List<SdkSourceIntent.RequiredReactorSource> requiredReactorSources();
        InterpreterInputs interpreter(); FreshInputs fresh(); CanonicalInputs canonical();
        List<RootSoftwareChildBootstrap.Environment> bootstrapEnvironment();
    }
    /** A closed source plan deliberately has no qualified-tools or reactor receipt field. */
    public record ProductionPlan(String schema, String machineId, String reviewAtUtc,
            FileRef baselineIntentRef, FileRef legacyIntentRef, FileRef consumerIntentRef,
            SdkSourceAssembly.LegacyConstraint legacyConstraint, SdkSourceAssembly.Source32Reuse source32Reuse,
            long sharedViewPhysicalHardBytes, long allocationUnitBytes, long perDirectoryGuardBytes,
            FileRef producerGoldenPlanRef, List<SdkSourceIntent.RequiredReactorSource> requiredReactorSources,
            InterpreterInputs interpreter, FreshInputs fresh,
            CanonicalInputs canonical, List<RootSoftwareChildBootstrap.Environment> bootstrapEnvironment) implements SourceInputs {
        public ProductionPlan {
            if (!PLAN_SCHEMA.equals(schema)) throw new IllegalArgumentException("Exact pre-qualified SDK source-plan schema required");
            requiredReactorSources = List.copyOf(requiredReactorSources); bootstrapEnvironment = List.copyOf(bootstrapEnvironment);
            sourceShape(machineId, reviewAtUtc, baselineIntentRef, legacyIntentRef, consumerIntentRef, legacyConstraint,
                    source32Reuse, sharedViewPhysicalHardBytes, allocationUnitBytes, perDirectoryGuardBytes,
                    producerGoldenPlanRef, requiredReactorSources, interpreter, fresh, canonical, bootstrapEnvironment);
        }
    }
    public record ProductionInputs(String schema, String machineId, String reviewAtUtc,
            FileRef baselineIntentRef, FileRef legacyIntentRef, FileRef consumerIntentRef,
            SdkSourceAssembly.LegacyConstraint legacyConstraint, SdkSourceAssembly.Source32Reuse source32Reuse,
            long sharedViewPhysicalHardBytes, long allocationUnitBytes, long perDirectoryGuardBytes,
            FileRef producerGoldenPlanRef, FileRef qualifiedToolsBuildRef,
            List<SdkSourceIntent.RequiredReactorSource> requiredReactorSources,
            InterpreterInputs interpreter, FreshInputs fresh,
            CanonicalInputs canonical, List<RootSoftwareChildBootstrap.Environment> bootstrapEnvironment) implements SourceInputs {
        public ProductionInputs {
            if (!SCHEMA.equals(schema)) throw new IllegalArgumentException("Exact qualified SDK production-input schema required");
            Objects.requireNonNull(qualifiedToolsBuildRef);
            requiredReactorSources = List.copyOf(requiredReactorSources); bootstrapEnvironment = List.copyOf(bootstrapEnvironment);
            sourceShape(machineId, reviewAtUtc, baselineIntentRef, legacyIntentRef, consumerIntentRef, legacyConstraint,
                    source32Reuse, sharedViewPhysicalHardBytes, allocationUnitBytes, perDirectoryGuardBytes,
                    producerGoldenPlanRef, requiredReactorSources, interpreter, fresh, canonical, bootstrapEnvironment);
        }
    }
    public record BootstrapSelection(RootSoftwareChildBootstrap.ModuleSource client,
            RootSoftwareChildBootstrap.ModuleSource continuity, RootSoftwareChildBootstrap.ModuleSource owner,
            String graphRoot, String sdkRoot, String canonicalRepository,
            List<RootSoftwareChildBootstrap.Environment> environment, RootSoftwareChildBootstrap.SdkLineageBinding sdkLineageBinding) {
        public BootstrapSelection { environment = List.copyOf(environment); Objects.requireNonNull(sdkLineageBinding); }
    }
    @FunctionalInterface public interface BootstrapWriter {
        FileRef write(BootstrapSelection selection, RootSoftwareFixtureHandoff.Admission host, Path destination) throws IOException;
    }
    public record StageConfigs(FreshSdkFixtureStage.Config fresh, CanonicalColdWarmStage.Config canonical,
            FileRef viewsActualRef, FileRef selectedAssemblyActualRef, List<FileRef> inputRefs) {
        public StageConfigs { inputRefs = List.copyOf(inputRefs); }
    }

    public static ProductionInputs readInputs(FileRef ref) throws IOException {
        if (ref.bytes() < 1 || ref.bytes() > MAX_METADATA) throw new IOException("Bounded production intent required");
        ref.verify(); ProductionInputs result = ControlBuild.strictMapper().readValue(Files.readAllBytes(Path.of(ref.path())), ProductionInputs.class);
        ref.verify(); inputRefs(result); return result;
    }
    public static ProductionPlan decodePlan(byte[] bytes) throws IOException {
        Objects.requireNonNull(bytes);
        if (bytes.length < 1 || bytes.length > MAX_METADATA) throw new IOException("Bounded SDK source plan required");
        return ControlBuild.strictMapper().readValue(bytes, ProductionPlan.class);
    }
    public static ProductionPlan readPlan(FileRef ref) throws IOException {
        Objects.requireNonNull(ref);
        if (ref.bytes() < 1 || ref.bytes() > MAX_METADATA) throw new IOException("Bounded SDK source plan required");
        SharedSourceFiles.plainAncestors(Path.of(ref.path())); ref.verify();
        ProductionPlan plan = decodePlan(Files.readAllBytes(Path.of(ref.path())));
        planInputRefs(plan); ref.verify(); return plan;
    }
    public static FileRef writePlan(ProductionPlan plan, Path destination, FreshSdkFixtureStage.ResourceGuard guard) throws IOException {
        Objects.requireNonNull(plan); Objects.requireNonNull(guard);
        requireDestination(destination);
        requirePlanMachine(plan); check(plan, guard, 0); planInputRefs(plan);
        ProjectStoragePolicy.requireBulkOutput(destination.toAbsolutePath().normalize().getParent());
        SharedSourceFiles.plainAncestors(destination); FileRef ref = write(plan, destination, plan, guard);
        if (!readPlan(ref).equals(plan)) throw new IOException("SDK source-plan serialization roundtrip differs");
        check(plan, guard, 0); return ref;
    }
    /** Only the completed native-bound tools receipt can fill this field after the actual qualified-tools stage. */
    public static ProductionInputs bindQualifiedTools(ProductionPlan plan, FileRef actualQualifiedToolsBuildRef,
            FreshSdkFixtureStage.ResourceGuard guard) throws IOException {
        Objects.requireNonNull(plan); Objects.requireNonNull(actualQualifiedToolsBuildRef); Objects.requireNonNull(guard);
        requirePlanMachine(plan); check(plan, guard, 0);
        // Validate the actual build before constructing an object that carries the qualified receipt.
        List<FileRef> tools = qualifiedToolsInputs(actualQualifiedToolsBuildRef, plan.machineId());
        List<FileRef> originals = planInputRefs(plan);
        var inputs = new ProductionInputs(SCHEMA, plan.machineId(), plan.reviewAtUtc(), plan.baselineIntentRef(),
                plan.legacyIntentRef(), plan.consumerIntentRef(), plan.legacyConstraint(), plan.source32Reuse(),
                plan.sharedViewPhysicalHardBytes(), plan.allocationUnitBytes(), plan.perDirectoryGuardBytes(),
                plan.producerGoldenPlanRef(), actualQualifiedToolsBuildRef, plan.requiredReactorSources(),
                plan.interpreter(), plan.fresh(), plan.canonical(), plan.bootstrapEnvironment());
        inputRefs(inputs); for (FileRef original : originals) original.verify(); for (FileRef tool : tools) tool.verify();
        check(plan, guard, 0); return inputs;
    }
    public static FileRef bindAndWriteInputs(FileRef planRef, FileRef actualQualifiedToolsBuildRef, Path destination,
            FreshSdkFixtureStage.ResourceGuard guard) throws IOException {
        requireDestination(destination);
        ProductionPlan plan = readPlan(planRef);
        ProductionInputs inputs = bindQualifiedTools(plan, actualQualifiedToolsBuildRef, guard);
        planRef.verify(); ProjectStoragePolicy.requireBulkOutput(destination.toAbsolutePath().normalize().getParent());
        FileRef actual = writeInputs(inputs, destination, guard);
        planRef.verify(); actualQualifiedToolsBuildRef.verify(); return actual;
    }
    /** Source-intent owner/Root supplies actual typed inputs; this emits one new local input, never qualification. */
    public static FileRef writeInputs(ProductionInputs inputs, Path destination, FreshSdkFixtureStage.ResourceGuard guard) throws IOException {
        Objects.requireNonNull(guard); check(inputs, guard, 0);
        if (!inputs.machineId().equals(WindowsJobProcess.currentMachineId())) throw new IOException("Author production inputs on their actual executing machine");
        inputRefs(inputs); SharedSourceFiles.plainAncestors(destination);
        FileRef ref = write(inputs, destination, inputs, guard);
        if (!readInputs(ref).equals(inputs)) throw new IOException("SDK production intent serialization roundtrip differs");
        check(inputs, guard, 0); return ref;
    }
    /** Includes templates, all original/overlay inputs, immutable SDK contract and complete test fixtures. */
    public static List<FileRef> inputRefs(ProductionInputs inputs) throws IOException {
        List<FileRef> refs = new ArrayList<>(qualifiedToolsInputs(inputs.qualifiedToolsBuildRef(), inputs.machineId()));
        refs.addAll(sourceInputRefs(inputs)); return unique(refs);
    }
    /** Verifies only real source/fixture originals; no build is claimed by a pre-qualified plan. */
    public static List<FileRef> planInputRefs(ProductionPlan plan) throws IOException {
        return sourceInputRefs(Objects.requireNonNull(plan));
    }
    private static List<FileRef> sourceInputRefs(SourceInputs inputs) throws IOException {
        List<FileRef> refs = new ArrayList<>();
        refs.addAll(List.of(inputs.baselineIntentRef(), inputs.legacyIntentRef(), inputs.consumerIntentRef(),
                inputs.source32Reuse().baseFreezeRef(), inputs.source32Reuse().exporterSourceRef(), inputs.producerGoldenPlanRef(),
                inputs.interpreter().pythonExecutable(), inputs.interpreter().basePythonExecutable(), inputs.fresh().supportContractRef(),
                inputs.fresh().executionCardRef(), inputs.canonical().gitExecutable(), inputs.canonical().workflowRef(),
                inputs.canonical().reviewedWalRef(), inputs.canonical().executionCardRef()));
        refs.addAll(inputs.interpreter().dependencySources()); refs.addAll(inputs.fresh().supportSources());
        refs.addAll(inputs.canonical().canonicalSources());
        var requirements = new java.util.TreeMap<String, SdkSourceIntent.RequiredReactorSource>();
        for (FileRef template : List.of(inputs.baselineIntentRef(), inputs.legacyIntentRef(), inputs.consumerIntentRef())) {
            var resolved = SdkSourceIntent.resolve(template); SdkSourceAssembly.Request request = resolved.request(); refs.addAll(resolved.inputRefs());
            for (var required : resolved.requiredReactorSources()) {
                var prior = requirements.putIfAbsent(required.relativePath().toLowerCase(Locale.ROOT), required);
                if (prior != null && !prior.equals(required)) throw new IOException("Conflicting source-intent reactor requirements");
            }
            if (!request.machineId().equals(inputs.machineId())) throw new IOException("Template belongs to a different machine");
            for (var source : request.sources()) {
                refs.add(source.original()); for (var overlay : source.overlays()) refs.add(overlay.patchRef());
            }
        }
        if (!inputs.requiredReactorSources().equals(List.copyOf(requirements.values())))
            throw new IOException("Production inputs must retain every exact source-intent reactor requirement");
        var golden = FreshSdkFixtureStage.readProducerGoldenSources(inputs.producerGoldenPlanRef());
        FreshSdkFixtureStage.requireDeclaredProducerMachine(golden, inputs.machineId());
        refs.addAll(FreshSdkFixtureStage.producerGoldenMetadataInputs(golden)); refs.addAll(FreshSdkFixtureStage.producerGoldenInputs(golden));
        List<FileRef> result = unique(refs); for (var ref : result) ref.verify(); return result;
    }

    static List<FileRef> qualifiedToolsInputs(FileRef ref, String machineId) throws IOException {
        var build = ControlBuild.verifiedCompletedReceipt(ref);
        if (build.targetKind() != ControlBuild.TargetKind.BUILD_TOOLS_RUNTIME || !machineId.equals(build.machineId())
                || !ControlBuild.producerClosure().equals(build.completeDeployment()))
            throw new IOException("Current complete qualified tools required before Views");
        try {
            Path archive = Path.of(ControlBuild.class.getProtectionDomain().getCodeSource().getLocation().toURI()).toRealPath();
            for (Class<?> type : List.of(SdkStageConfigurationProducer.class, SdkDerivedSource32.class))
                if (!Files.isRegularFile(archive) || !archive.equals(Path.of(type.getProtectionDomain().getCodeSource().getLocation().toURI()).toRealPath()))
                    throw new IOException("SDK producer/emitter must share the qualified tools archive");
        } catch (java.net.URISyntaxException invalid) { throw new IOException("Actual executing tools archive URI required", invalid); }
        List<FileRef> refs = new ArrayList<>(List.of(ref, build.capacityReleaseRef(), build.javaExecutableRef(),
                build.mavenToolchain().distributionLauncherRef()));
        if (build.mavenToolchain().explicitOverrideRef() != null) refs.add(build.mavenToolchain().explicitOverrideRef());
        refs.addAll(build.sourcePins()); refs.addAll(build.compiledSourcePins()); refs.addAll(build.completeDeployment());
        refs.addAll(build.producerRuntimePins());
        List<FileRef> result = unique(refs); for (FileRef input : result) input.verify(); return result;
    }

    public static StageConfigs produce(ProductionInputs inputs, FileRef acceptedReactorRef,
            RootSoftwareFixtureHandoff.Admission host, Path artifactRoot, SdkSourceAssembly.SharedCapacityGate gate,
            BootstrapWriter bootstrapWriter, FreshSdkFixtureStage.ResourceGuard guard) throws IOException {
        Objects.requireNonNull(host); Objects.requireNonNull(gate); Objects.requireNonNull(bootstrapWriter); Objects.requireNonNull(guard);
        check(inputs, guard, 0); List<FileRef> originalInputs = inputRefs(inputs);
        acceptedReactorRef.verify(); var reactor = ControlBuild.verifiedCompletedReceipt(acceptedReactorRef);
        if (!inputs.machineId().equals(WindowsJobProcess.currentMachineId()) || !reactor.machineId().equals(inputs.machineId())
                || reactor.targetKind() != ControlBuild.TargetKind.SERVICE_FAST_JAR)
            throw new IOException("This machine's current accepted service reactor is required");
        requireReactorSources(inputs.requiredReactorSources(), Path.of(reactor.sourceRoot()), reactor.sourcePins());
        requireReactorSources(inputs.requiredReactorSources(), Path.of(reactor.compiledSourceRoot()), reactor.compiledSourcePins());
        if (!host.buildReceiptRef().equals(acceptedReactorRef)) throw new IOException("Admitted host must use this exact newly accepted reactor");
        List<FileRef> hostInputs = hostInputs(host); for (var ref : hostInputs) ref.verify();
        Path output = artifactRoot.toAbsolutePath().normalize();
        Path artifacts = output.getParent().toRealPath();
        if (!artifacts.getFileName().toString().equals("artifacts") || Files.exists(output)) throw new IOException("New direct pipeline artifact child required");
        SharedSourceFiles.plainAncestors(output);
        List<SdkSourceAssembly.Request> templates = new ArrayList<>();
        for (var ref : List.of(inputs.baselineIntentRef(), inputs.legacyIntentRef(), inputs.consumerIntentRef())) templates.add(SdkSourceIntent.resolve(ref).request());
        String repository = templates.getFirst().canonicalTestRepository();
        for (var template : templates) if (!Path.of(template.canonicalTestRepository()).toRealPath().equals(Path.of(repository).toRealPath()))
            throw new IOException("One canonical test repository required for all views");
        requireIndependentOutput(output, templates, inputs.interpreter().dependencyRoots());
        check(inputs, guard, 8192); Files.createDirectory(output);
        Path metadata = output.resolve("metadata"), group = output.resolve("views");
        Files.createDirectory(metadata); Files.createDirectory(group);
        List<FileRef> reviews = new ArrayList<>(), generated = new ArrayList<>();
        List<String> names = List.of("baseline", "legacy", "consumer");
        for (int index = 0; index < 3; index++) {
            check(inputs, guard, MAX_METADATA);
            var request = rebind(templates.get(index), group.resolve(names.get(index)), acceptedReactorRef, reactor.targetKind());
            FileRef requestRef = write(request, metadata.resolve(names.get(index) + "-request.json"), inputs, guard);
            var review = SdkSourceAssembly.review(requestRef);
            check(inputs, guard, MAX_METADATA);
            FileRef reviewRef = SdkSourceAssembly.writeReview(review, metadata.resolve(names.get(index) + "-review.json"));
            reviews.add(reviewRef); generated.add(requestRef); generated.add(reviewRef);
        }
        var parent = ControlBuild.strictMapper().readTree(Files.readAllBytes(Path.of(inputs.source32Reuse().baseFreezeRef().path())));
        var parentRoot = parent.get("source_root");
        if (parentRoot == null || !parentRoot.isTextual() || !Path.of(parentRoot.textValue()).isAbsolute()) throw new IOException("SDK root required");
        inputs.source32Reuse().baseFreezeRef().verify();
        var ni = nativeDriverIntent(templates.get(2).sources(),
                FileRef.measure(Path.of(parentRoot.textValue()).resolve("xar_autoplayer/bridge/native_driver.py")));
        var request = new SdkSourceAssembly.ViewsRequest(SdkSourceAssembly.VIEWS_SCHEMA, inputs.machineId(), group.toString(),
                reviews.get(0), reviews.get(1), reviews.get(2), inputs.legacyConstraint(), inputs.source32Reuse(),
                SdkDerivedSource32.SourcePurpose.FULL_SOFTWARE, ni, inputs.sharedViewPhysicalHardBytes());
        FileRef viewsRequestRef = write(request, metadata.resolve("views-request.json"), inputs, guard); generated.add(viewsRequestRef);
        SdkSourceAssembly.assembleViews(viewsRequestRef, boundedGate(inputs, gate, guard));
        check(inputs, guard, 0);
        FileRef viewsRef = FileRef.measure(group.resolve(".assembly/SHARED-VIEWS-ACTUAL.json"));
        var views = SdkSourceAssembly.readViewsActual(viewsRef);
        FileRef consumerRef = views.consumerActualRef(); var consumer = SdkSourceAssembly.readActual(consumerRef);
        if (consumer.deploymentClosure().stream().noneMatch(value -> value.actualBuildReceipt().equals(acceptedReactorRef)
                && value.targetKind() == reactor.targetKind() && value.completeFiles().equals(reactor.completeDeployment())))
            throw new IOException("New consumer view did not retain this exact accepted reactor");
        var lineageBinding = source32Binding(inputs, views, consumer, metadata, generated, ni, guard);
        BootstrapSelection selection = selection(inputs, consumer, repository, lineageBinding);
        var golden = FreshSdkFixtureStage.readProducerGoldenSources(inputs.producerGoldenPlanRef());
        FileRef test = selectedSource(consumer, CLIENT_TEST);
        FreshSdkFixtureStage.requireDeclaredProducerCohort(golden, content(selection.client().source()), java.util.Optional.of(content(test)));
        check(inputs, guard, 1L << 20);
        Path bootstrapPath = metadata.resolve("root-bootstrap.json");
        FileRef bootstrapRef = bootstrapWriter.write(selection, host, bootstrapPath);
        if (!Path.of(bootstrapRef.path()).toRealPath().equals(bootstrapPath.toRealPath())) throw new IOException("Bootstrap callback must create its exact owned destination");
        requireBootstrap(inputs, selection, host, bootstrapRef);
        generated.addAll(RootSoftwareChildBootstrap.inputRefs(RootSoftwareChildBootstrap.readConfiguration(bootstrapRef)));
        List<FreshSdkFixtureStage.ExpectedModule> additional = new ArrayList<>();
        for (ModulePath module : inputs.fresh().additionalModules()) additional.add(new FreshSdkFixtureStage.ExpectedModule(module.module(), selectedSource(consumer, module.relativeSource())));
        var interpreter = inputs.interpreter(); var fresh = inputs.fresh(); var canonical = inputs.canonical();
        var coldSource = selectedSource(consumer, "tools/g2_saved_campaign/test_current_saved_campaign_cold_v1.py");
        int coldParents = FreshSdkFixtureStage.coldParents(new SdkSourceAssembly.Digest(coldSource.bytes(), coldSource.sha256()));
        var freshConfig = new FreshSdkFixtureStage.Config(FreshSdkFixtureStage.SCHEMA, inputs.machineId(), inputs.reviewAtUtc(), repository,
                artifacts.resolve("fresh-sdk-fixtures").toString(), interpreter.pythonExecutable(), interpreter.basePythonExecutable(), viewsRef, consumerRef,
                acceptedReactorRef, fresh.supportContractRef(), fresh.supportSources(), interpreter.dependencyRoots(), interpreter.dependencySources(),
                fresh.executionCardRef(), additional, bootstrapRef, inputs.producerGoldenPlanRef(), fresh.commandMemoryBytes(), fresh.timeoutSeconds(), coldParents);
        var canonicalConfig = new CanonicalColdWarmStage.Config(CanonicalColdWarmStage.SCHEMA, inputs.machineId(), inputs.reviewAtUtc(), repository,
                artifacts.resolve("canonical-thirty").toString(), interpreter.pythonExecutable(), canonical.gitExecutable(), canonical.workflowRef(), canonical.reviewedWalRef(),
                canonical.canonicalSources(), interpreter.dependencyRoots(), interpreter.dependencySources(), canonical.executionCardRef(),
                CanonicalColdWarmStage.BootstrapMode.ROOT_SOFTWARE_FIXTURE, bootstrapRef, canonical.commandMemoryBytes(), canonical.timeoutSeconds());
        for (FileRef ref : originalInputs) ref.verify(); for (FileRef ref : hostInputs) ref.verify(); acceptedReactorRef.verify();
        for (FileRef ref : generated) ref.verify(); requireBootstrap(inputs, selection, host, bootstrapRef); check(inputs, guard, 0);
        List<FileRef> custody = new ArrayList<>(originalInputs); custody.addAll(hostInputs); custody.addAll(generated);
        custody.addAll(List.of(acceptedReactorRef, viewsRef, consumerRef, bootstrapRef));
        return new StageConfigs(freshConfig, canonicalConfig, viewsRef, consumerRef, unique(custody));
    }

    static SdkSourceAssembly.Request rebind(SdkSourceAssembly.Request original, Path output, FileRef reactor, ControlBuild.TargetKind kind) {
        return new SdkSourceAssembly.Request(original.schema(), original.machineId(), original.canonicalRepository(), original.canonicalCommit(),
                original.canonicalTestRepository(), output.toAbsolutePath().normalize().toString(), original.sdkInputRoot(), original.sdkRelativeRoot(),
                original.importRoots(), original.approvedInputSourceRoots(), original.protectedRoots(), original.sources(), original.importRoutes(),
                List.of(new SdkSourceAssembly.Deployment("current-reactor", reactor, kind)), original.producerReuse(), original.outputHardBytes());
    }
    static void requireReactorSources(List<SdkSourceIntent.RequiredReactorSource> required, Path sourceRoot, List<FileRef> pins) throws IOException {
        Path root = sourceRoot.toAbsolutePath().normalize();
        for (var requirement : required) {
            Path expected = root.resolve(requirement.relativePath()).normalize(); FileRef selected = null;
            if (!expected.startsWith(root)) throw new IOException("Reactor requirement escaped its explicit source root");
            for (FileRef pin : pins) if (Path.of(pin.path()).toAbsolutePath().normalize().equals(expected)) {
                if (selected != null) throw new IOException("Duplicate actual reactor source pin"); selected = pin;
            }
            if (selected == null || !content(selected).equals(requirement.content()))
                throw new IOException("Required Java/test/resource source absent or different in actual reactor: " + requirement.relativePath());
            selected.verify();
        }
    }
    static void requireIndependentOutput(Path output, List<SdkSourceAssembly.Request> templates, List<String> dependencies) throws IOException {
        List<String> roots = new ArrayList<>(dependencies);
        for (var template : templates) {
            roots.addAll(List.of(template.canonicalRepository(), template.canonicalTestRepository(), template.sdkInputRoot()));
            roots.addAll(template.approvedInputSourceRoots());
            for (var protectedRoot : template.protectedRoots()) roots.add(protectedRoot.path());
        }
        for (String value : roots) {
            Path source = absolute(value).toRealPath();
            if (output.startsWith(source) || source.startsWith(output)) throw new IOException("SDK production output overlaps a source, dependency or protected frozen root");
        }
    }
    static SdkDerivedSource32.NativeDriverIntent nativeDriverIntent(List<SdkSourceAssembly.Source> sources, FileRef base) throws IOException {
        var rows = sources.stream().filter(v -> v.relativePath().equals("ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py")).toList();
        if (rows.size() != 1 || rows.getFirst().role() != SdkSourceAssembly.SourceRole.SDK_SOURCE
                || rows.getFirst().origin() != SdkSourceAssembly.InputOrigin.FROZEN_SDK_SOURCE || !FileRef.measure(Path.of(rows.getFirst().original().path())).equals(base))
            throw new IOException("Native source mismatch");
        base.verify(); var source = rows.getFirst(); source.original().verify(); var before = content(base);
        return new SdkDerivedSource32.NativeDriverIntent(before, source.overlays().isEmpty() ? before : source.overlays().getLast().standaloneResult());
    }

    static RootSoftwareChildBootstrap.SdkLineageBinding source32Binding(ProductionInputs inputs,
            SdkSourceAssembly.ViewsActual views, SdkSourceAssembly.Actual consumer, Path metadata,
            List<FileRef> generated, SdkDerivedSource32.NativeDriverIntent ni, FreshSdkFixtureStage.ResourceGuard guard) throws IOException {
        var matches = views.sdkSourceViews().stream().filter(value -> value.role() == SdkSourceAssembly.SourceViewRole.CONSUMER).toList();
        if (matches.size() != 1) throw new IOException("Exactly one consumer SDK view required");
        var view = matches.getFirst();
        if (!view.assemblyActualRef().equals(views.consumerActualRef())
                || !Path.of(view.sdkRoot()).toRealPath().equals(Path.of(consumer.sdkRoot()).toRealPath()))
            throw new IOException("SDK lineage must match the selected consumer");
        generated.addAll(List.of(view.sdkFreezeRef(), view.source32AnchorRef(), view.assemblyActualRef()));
        view.sdkFreezeRef().verify();
        var header = ControlBuild.strictMapper().readTree(Files.readAllBytes(Path.of(view.sdkFreezeRef().path())));
        String schema = header.path("schema").asText();
        if ("root.ck3.final-sdk-freeze/v1".equals(schema))
            return new RootSoftwareChildBootstrap.SdkLineageBinding(RootSoftwareChildBootstrap.SdkLineageKind.ORIGINAL_SOURCE32,
                    view.sdkFreezeRef(), null);
        if (!SdkDerivedSource32.SCHEMA.equals(schema)) throw new IOException("Closed original/derived SDK lineage required");
        check(inputs, guard, MAX_METADATA);
        FileRef emission = SdkDerivedSource32.emitVerified(view.sdkFreezeRef(), inputs.qualifiedToolsBuildRef(),
                metadata.resolve("consumer-sdk-java-verification.json"));
        var verified = SdkDerivedSource32.readVerifiedEmission(emission);
        if (!verified.lineageRef().equals(view.sdkFreezeRef()) || !verified.assemblyActualRef().equals(views.consumerActualRef())
                || !verified.machineId().equals(inputs.machineId()) || verified.runtimeAdmitted() || verified.nativeRestoreAdmitted()
                || verified.sourcePurpose() != SdkDerivedSource32.SourcePurpose.FULL_SOFTWARE || !verified.nativeDriverIntent().equals(ni)
                || !Path.of(verified.sdkRoot()).toRealPath().equals(Path.of(consumer.sdkRoot()).toRealPath())
                || !verified.parentFreezeRef().equals(inputs.source32Reuse().baseFreezeRef())
                || !verified.parentAnchorRef().equals(view.source32AnchorRef()))
            throw new IOException("Actual Java SDK proof differs from selected consumer/parent");
        generated.addAll(List.of(emission, verified.parentFreezeRef(), verified.parentAnchorRef(), verified.assemblyActualRef(),
                verified.sdkNativeDriverRef()));
        check(inputs, guard, 0);
        return new RootSoftwareChildBootstrap.SdkLineageBinding(RootSoftwareChildBootstrap.SdkLineageKind.DERIVED_SOURCE32,
                view.sdkFreezeRef(), emission);
    }

    static BootstrapSelection selection(ProductionInputs inputs, SdkSourceAssembly.Actual consumer, String repository,
            RootSoftwareChildBootstrap.SdkLineageBinding sdkLineageBinding) throws IOException {
        var client = new RootSoftwareChildBootstrap.ModuleSource("tools.g2_saved_campaign.java_map_admission_client_v1", selectedSource(consumer, CLIENT));
        var continuity = new RootSoftwareChildBootstrap.ModuleSource("tools.g2_saved_campaign.current_saved_continuity_v1", selectedSource(consumer, CONTINUITY));
        var owner = new RootSoftwareChildBootstrap.ModuleSource("tools.g2_saved_campaign.root_current_saved_campaign_cold_owner_v1", selectedSource(consumer, OWNER));
        var environment = environment(inputs.bootstrapEnvironment(), consumer.graphRoot(), repository, client.source());
        return new BootstrapSelection(client, continuity, owner, consumer.graphRoot(), consumer.sdkRoot(), repository, environment, sdkLineageBinding);
    }
    static List<RootSoftwareChildBootstrap.Environment> environment(List<RootSoftwareChildBootstrap.Environment> extra,
            String graph, String repository, FileRef client) throws IOException {
        var values = new LinkedHashMap<String, String>();
        values.put("XAR_CROWN_JAVA_RUNTIME_SOURCE_ROOT", graph); values.put("XAR_CROWN_JAVA_SHARED_CLIENT_SOURCE", client.path());
        values.put("XAR_CROWN_ORIGINAL_REPOSITORY", repository);
        for (String name : List.of("XAR_CURRENT_SAVED_BASIS_TEST_SOURCE_ROOT", "XAR_CURRENT_SAVED_CLOSURE_TEST_SOURCE_ROOT", "XAR_CURRENT_SAVED_CONTINUITY_TEST_SOURCE_ROOT")) values.put(name, graph);
        for (var item : extra) {
            String prior = values.putIfAbsent(item.name(), item.value());
            if (prior != null && !Path.of(prior).toAbsolutePath().normalize().equals(Path.of(item.value()).toAbsolutePath().normalize()))
                throw new IOException("Before-import fixture environment must select this actual source graph");
        }
        String nativeWire = values.get("CK3_M7_FORMAL_NATIVE_WIRE_DIR");
        if (nativeWire == null || !Files.isDirectory(absolute(nativeWire))) throw new IOException("Explicit existing M7 original native-wire fixture directory required");
        List<RootSoftwareChildBootstrap.Environment> result = new ArrayList<>();
        for (var entry : values.entrySet()) result.add(new RootSoftwareChildBootstrap.Environment(entry.getKey(), entry.getValue()));
        return List.copyOf(result);
    }
    static FileRef selectedSource(SdkSourceAssembly.Actual actual, String relative) throws IOException {
        FileRef found = null;
        for (var source : actual.actualSourceClosure()) if (source.relativePath().equals(relative)) {
            if (found != null) throw new IOException("Duplicate selected source"); found = source.actual();
        }
        if (found == null || !Path.of(found.path()).equals(Path.of(actual.graphRoot()).resolve(relative).normalize()))
            throw new IOException("Required actual selected source absent: " + relative);
        found.verify(); return found;
    }
    private static void requireBootstrap(ProductionInputs inputs, BootstrapSelection selected, RootSoftwareFixtureHandoff.Admission host, FileRef ref) throws IOException {
        var value = RootSoftwareChildBootstrap.readConfiguration(ref);
        if (!value.machineId().equals(inputs.machineId()) || !value.client().equals(selected.client()) || !value.continuity().equals(selected.continuity())
                || !value.owner().equals(selected.owner()) || !value.environment().equals(selected.environment())
                || !value.sdkLineageBinding().equals(selected.sdkLineageBinding())
                || !value.fixtureOriginRef().equals(host.originRef()) || !value.probeRequestRef().equals(host.probeRequestRef())
                || !value.probePayloadRef().equals(host.probePayloadRef()) || !value.originalFixtureRefs().equals(host.originalFixtureRefs())
                || !value.serviceProof().serviceEvidenceRef().equals(host.serviceEvidenceRef()))
            throw new IOException("Bootstrap callback must bind the selected actual source cohort to this admitted host");
        for (FileRef input : RootSoftwareChildBootstrap.inputRefs(value)) input.verify();
    }
    private static List<FileRef> hostInputs(RootSoftwareFixtureHandoff.Admission host) {
        List<FileRef> refs = new ArrayList<>(List.of(host.buildReceiptRef(), host.originRef(), host.programRef(), host.serviceEvidenceRef(), host.probeRequestRef(),
                host.probePayloadRef(), host.actualProbeResponseRef(), host.pendingRef(), host.activationRef()));
        refs.addAll(host.originalFixtureRefs()); return unique(refs);
    }
    static SdkSourceAssembly.SharedCapacityGate boundedGate(ProductionInputs inputs, SdkSourceAssembly.SharedCapacityGate gate, FreshSdkFixtureStage.ResourceGuard guard) {
        return new SdkSourceAssembly.SharedCapacityGate() {
            @Override public SdkSourceAssembly.WritePermit acquire(SdkSourceAssembly.SharedQuote quote, FileRef request) throws IOException {
                check(inputs, guard, 0); var permit = gate.acquire(quote, request);
                if (!permit.machineId().equals(inputs.machineId()) || permit.allocationUnitBytes() != inputs.allocationUnitBytes()
                        || permit.perDirectoryGuardBytes() != inputs.perDirectoryGuardBytes() || permit.allocationUpperLimitBytes() > inputs.sharedViewPhysicalHardBytes()
                        || Instant.parse(permit.expiresAtUtc()).isAfter(Instant.parse(inputs.reviewAtUtc())))
                    throw new IOException("Live shared allocation differs from the explicit production input contract");
                return permit;
            }
            @Override public void revalidate(SdkSourceAssembly.WritePermit permit, long consumed) throws IOException {
                check(inputs, guard, 0); gate.revalidate(permit, consumed);
            }
        };
    }
    private static FileRef write(Object value, Path path, SourceInputs inputs, FreshSdkFixtureStage.ResourceGuard guard) throws IOException {
        byte[] raw = ControlBuild.strictMapper().writeValueAsBytes(value);
        if (raw.length > MAX_METADATA) throw new IOException("Bounded SDK production metadata required");
        check(inputs, guard, raw.length); Files.write(path, raw, StandardOpenOption.CREATE_NEW); return FileRef.measure(path);
    }
    private static void check(SourceInputs inputs, FreshSdkFixtureStage.ResourceGuard guard, long pending) throws IOException {
        if (!Instant.now().isBefore(Instant.parse(inputs.reviewAtUtc()))) throw new IOException("SDK production input deadline expired"); guard.revalidate(pending);
    }
    private static void requirePlanMachine(ProductionPlan plan) throws IOException {
        if (!plan.machineId().equals(WindowsJobProcess.currentMachineId()))
            throw new IOException("SDK source plan belongs to another executing machine");
    }
    private static void requireDestination(Path destination) throws IOException {
        Objects.requireNonNull(destination);
        if (!destination.isAbsolute() || !destination.normalize().equals(destination) || destination.getParent() == null)
            throw new IOException("Absolute normalized SDK metadata destination required");
    }
    private static void sourceShape(String machineId, String reviewAtUtc,
            FileRef baselineIntentRef, FileRef legacyIntentRef, FileRef consumerIntentRef,
            SdkSourceAssembly.LegacyConstraint legacyConstraint, SdkSourceAssembly.Source32Reuse source32Reuse,
            long sharedViewPhysicalHardBytes, long allocationUnitBytes, long perDirectoryGuardBytes,
            FileRef producerGoldenPlanRef, List<SdkSourceIntent.RequiredReactorSource> requiredReactorSources,
            InterpreterInputs interpreter, FreshInputs fresh, CanonicalInputs canonical,
            List<RootSoftwareChildBootstrap.Environment> bootstrapEnvironment) {
        if (machineId == null || !machineId.matches("[a-z0-9][a-z0-9-]{2,127}"))
            throw new IllegalArgumentException("Versioned same-machine SDK production intent required");
        Instant.parse(reviewAtUtc);
        Objects.requireNonNull(baselineIntentRef); Objects.requireNonNull(legacyIntentRef);
        Objects.requireNonNull(consumerIntentRef); Objects.requireNonNull(legacyConstraint);
        Objects.requireNonNull(source32Reuse); Objects.requireNonNull(producerGoldenPlanRef);
        if (requiredReactorSources.size() > 512 || requiredReactorSources.stream().map(value -> value.relativePath().toLowerCase(Locale.ROOT)).distinct().count() != requiredReactorSources.size())
            throw new IllegalArgumentException("Unique bounded actual reactor source requirements required");
        Objects.requireNonNull(interpreter); Objects.requireNonNull(fresh); Objects.requireNonNull(canonical);
        if (sharedViewPhysicalHardBytes < 1 || sharedViewPhysicalHardBytes > 64L << 20
                || allocationUnitBytes < 1 || allocationUnitBytes > 1L << 20 || perDirectoryGuardBytes < 0
                || perDirectoryGuardBytes > 1L << 20 || bootstrapEnvironment.size() > 7
                || bootstrapEnvironment.stream().map(RootSoftwareChildBootstrap.Environment::name).distinct().count() != bootstrapEnvironment.size())
            throw new IllegalArgumentException("Explicit bounded shared allocation and unique fixture environment required");
    }
    private static List<FileRef> unique(List<FileRef> refs) {
        var values = new LinkedHashMap<String, FileRef>();
        for (FileRef ref : refs) {
            String key = absolute(ref.path()).normalize().toString().toLowerCase(Locale.ROOT);
            FileRef prior = values.putIfAbsent(key, ref);
            if (prior != null && !prior.equals(ref)) throw new IllegalArgumentException("Conflicting exact source reference");
        }
        return List.copyOf(values.values());
    }
    private static SdkSourceAssembly.Digest content(FileRef ref) { return new SdkSourceAssembly.Digest(ref.bytes(), ref.sha256()); }
    private static Path absolute(String value) {
        Path path = Path.of(value); if (!path.isAbsolute()) throw new IllegalArgumentException("Absolute explicit source path required"); return path.toAbsolutePath().normalize();
    }
    private static void limits(long memory, int timeout, int maximum) {
        if (memory < 64L << 20 || memory > 1536L << 20 || timeout < 1 || timeout > maximum)
            throw new IllegalArgumentException("Finite explicit child resources required");
    }
}
