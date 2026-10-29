package org.xar.ck3.control.build;

import com.fasterxml.jackson.databind.JsonNode;
import java.io.IOException;
import java.io.RandomAccessFile;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Objects;
import java.util.Set;

/** Exact existing helper interoperability; no UAC, retry, arbitrary command or directory EXE scan. */
public final class NativeBridgeDefender {
    private static final String SCHEMA = "xar.project-exe-exclusions.v1";
    private static final String CANDIDATE = "java-native-launch-reviewed-source";
    private static final String INJECTOR = "xar_ck3_bridge_injector";
    static final String BROKER_ARRAY_SCHEMA = "xar.project-exe-broker.receipt.v1";
    static final String BROKER_NULLABLE_SCHEMA = "xar.project-exe-broker.receipt.v2";
    private NativeBridgeDefender() { }
    @com.fasterxml.jackson.databind.annotation.JsonDeserialize(using=NativeRegistrationRuntimeCodec.class)
    public sealed interface Runtime permits HelperRuntime,ManifestRuntime {
        Path pythonBaseRoot();Path venvRoot();ControlBuild.FileRef python();ControlBuild.FileRef helper();
        List<ControlBuild.FileRef> references() throws IOException;
    }
    /** Historical exact six-field data. No new REGISTER execution is issued by this constructor. */
    public record HelperRuntime(Path pythonBaseRoot, Path venvRoot, ControlBuild.FileRef python,
            ControlBuild.FileRef helper, List<ControlBuild.FileRef> completePythonFiles,
            List<ControlBuild.FileRef> completeHelperSources) implements Runtime {
        public HelperRuntime {
            pythonBaseRoot = NativeBridgeBuild.absolute(pythonBaseRoot); venvRoot = NativeBridgeBuild.absolute(venvRoot);
            Objects.requireNonNull(python); Objects.requireNonNull(helper);
            completePythonFiles = NativeBridgeBuild.unique(completePythonFiles); completeHelperSources = NativeBridgeBuild.unique(completeHelperSources);
            if (pythonBaseRoot.startsWith(venvRoot) || venvRoot.startsWith(pythonBaseRoot)
                    || completePythonFiles.isEmpty() || completeHelperSources.isEmpty()) throw new IllegalArgumentException("Disjoint complete existing Python runtime roots required");
        }
        public List<ControlBuild.FileRef> references() throws IOException {
            var refs = new ArrayList<>(completePythonFiles); refs.addAll(completeHelperSources); refs.add(python); refs.add(helper); return NativeBridgeBuild.merge(refs);
        }
    }
    public enum HelperInterpreterRoute { HISTORICAL_VENV_REDIRECTOR, DIRECT_BASE }
    public record ManifestRuntime(String schema,Path pythonBaseRoot,Path venvRoot,ControlBuild.FileRef python,
            ControlBuild.FileRef helper,ControlBuild.FileRef inventoryRef) implements Runtime {
        public static final String SCHEMA="xar.native-register-manifest-runtime/v1";
        public static final String DIRECT_SCHEMA="xar.native-register-manifest-runtime/v2";
        public ManifestRuntime {
            if(!SCHEMA.equals(schema)&&!DIRECT_SCHEMA.equals(schema))throw new IllegalArgumentException("exact manifest runtime version required");
            pythonBaseRoot=NativeBridgeBuild.absolute(pythonBaseRoot);venvRoot=NativeBridgeBuild.absolute(venvRoot);
            Objects.requireNonNull(python);Objects.requireNonNull(helper);Objects.requireNonNull(inventoryRef);
            if(pythonBaseRoot.startsWith(venvRoot)||venvRoot.startsWith(pythonBaseRoot))
                throw new IllegalArgumentException("disjoint complete runtime roots required");
            if(DIRECT_SCHEMA.equals(schema)&&!Path.of(python.path()).equals(pythonBaseRoot.resolve("python.exe")))
                throw new IllegalArgumentException("version2 requires the exact reviewed base interpreter");
        }
        public HelperInterpreterRoute interpreterRoute(){
            return DIRECT_SCHEMA.equals(schema)?HelperInterpreterRoute.DIRECT_BASE:HelperInterpreterRoute.HISTORICAL_VENV_REDIRECTOR;
        }
        @Override public List<ControlBuild.FileRef> references()throws IOException{
            var refs=new ArrayList<>(NativeRegistrationRuntimeInventory.evidenceReferences(inventoryRef));
            refs.add(python);refs.add(helper);return NativeBridgeBuild.merge(refs);
        }
    }
    public record FileApiPin(String path, String sha256) { }
    public record ManifestFile(String path, long size, String sha256, String target, String targetId) { }
    public record TargetProvenance(String path, String sha256, String target, String targetId, String source) { }
    public record Manifest(String schema, String repo, String sourceDir, String buildDir, String configuration,
            List<String> requestedTargets, String externalCandidate, FileApiPin cmakeIndex,
            FileApiPin cmakeCodemodel, List<TargetProvenance> targetProvenance, List<ManifestFile> files) {
        public Manifest { requestedTargets = List.copyOf(requestedTargets); targetProvenance = List.copyOf(targetProvenance); files = List.copyOf(files); }
    }
    public record Graph(ControlBuild.FileRef index, ControlBuild.FileRef codemodel,
            ControlBuild.FileRef injectorTarget, String injectorTargetId, Path injectorSource,
            ControlBuild.FileRef bridgeDll, ControlBuild.FileRef injector, List<ControlBuild.FileRef> graphRefs) {
        public Graph { graphRefs = NativeBridgeBuild.unique(graphRefs); }
    }
    public enum ReadbackRoute { DIRECT_ADMIN, PROTECTED_SYSTEM_BROKER }
    public record Readback(ReadbackRoute route, ControlBuild.FileRef originalReceipt,
            String manifestSemanticSha256, List<String> before, List<String> after,
            List<ControlBuild.FileRef> supplementalEvidence) {
        public Readback { before = List.copyOf(before); after = List.copyOf(after); supplementalEvidence = NativeBridgeBuild.unique(supplementalEvidence); }
    }

    public static void verifyHelperRuntime(Path repository, Runtime runtime) throws IOException {
        verifyRuntimeLocationAndHome(repository, runtime);
        if(runtime instanceof ManifestRuntime manifest){
            verifyManifestBindings(repository, manifest, NativeRegistrationRuntimeInventory.verify(manifest.inventoryRef()));
        }else{
            HelperRuntime historical=(HelperRuntime)runtime;
            var allPython = new ArrayList<>(NativeBridgeBuild.inventory(runtime.pythonBaseRoot()));
            allPython.addAll(NativeBridgeBuild.inventory(runtime.venvRoot()));
            NativeBridgeBuild.require(NativeBridgeBuild.merge(allPython).equals(historical.completePythonFiles()),
                    "Complete existing Python base/venv file closure differs");
            var sources = new ArrayList<>(NativeBridgeBuild.inventory(repository.resolve("tools/project_exe_broker")));
            sources.add(ControlBuild.FileRef.measure(repository.resolve("tools/register_project_exe_exclusions.py")));
            sources.add(ControlBuild.FileRef.measure(repository.resolve("tools/project_exe_exclusion_broker_client.py")));
            sources.add(ControlBuild.FileRef.measure(repository.resolve(NativeRegistrationRuntimeInventory.MACHINE_IDENTITY_SOURCE)));
            NativeBridgeBuild.require(NativeBridgeBuild.merge(sources).equals(historical.completeHelperSources()),
                    "Complete existing helper/client/broker source package differs");
        }
        NativeBridgeBuild.verify(runtime.references());
    }


    /** Selected from the actual full inventory; this constructor does not install or bootstrap packages. */
    public static ManifestRuntime directBaseRuntime(Path repository, ControlBuild.FileRef inventoryRef) throws IOException {
        var verified = NativeRegistrationRuntimeInventory.verify(inventoryRef);
        var inventory = verified.manifest();
        var roots = inventory.roots();
        var base = Path.of(roots.pythonBase());
        var selected = inventorySource(inventory, base.resolve("python.exe"));
        var runtime = new ManifestRuntime(ManifestRuntime.DIRECT_SCHEMA, base, Path.of(roots.venv()),
                selected, roots.helper(), inventoryRef);
        verifyRuntimeLocationAndHome(repository, runtime);
        verifyManifestBindings(repository, runtime, verified);
        NativeBridgeBuild.verify(runtime.references());
        return runtime;
    }

    static void requireDirectHelperRuntime(Runtime runtime) throws IOException {
        NativeBridgeBuild.require(runtime instanceof ManifestRuntime manifest
                && manifest.interpreterRoute() == HelperInterpreterRoute.DIRECT_BASE,
                "new registration requires explicit direct-base runtime v2; redirector v1 is historical read-only");
    }

    private static ControlBuild.FileRef inventorySource(NativeRegistrationRuntimeInventory.Manifest inventory,
            Path selectedPath) throws IOException {
        var matches = new ArrayList<ControlBuild.FileRef>();
        for (var pin : inventory.chunks()) {
            var chunk = ControlBuild.strictMapper().readValue(
                    NativeBridgeBuild.read(pin, NativeRegistrationRuntimeInventory.CHUNK_JSON_LIMIT),
                    NativeRegistrationRuntimeInventory.Chunk.class);
            for (var witness : chunk.files())
                if (Path.of(witness.source().path()).equals(selectedPath)) matches.add(witness.source());
        }
        NativeBridgeBuild.require(matches.size() == 1, "selected interpreter must occur exactly once in the complete inventory");
        return matches.getFirst();
    }

    private static void verifyRuntimeLocationAndHome(Path repository, Runtime runtime) throws IOException {
        boolean direct = runtime instanceof ManifestRuntime manifest
                && manifest.interpreterRoute() == HelperInterpreterRoute.DIRECT_BASE;
        Path interpreter = direct ? runtime.pythonBaseRoot().resolve("python.exe")
                : runtime.venvRoot().resolve("Scripts/python.exe");
        NativeBridgeBuild.require(runtime.venvRoot().equals(repository.resolve("tools/.venv"))
                && Path.of(runtime.python().path()).equals(interpreter)
                && Path.of(runtime.helper().path()).equals(repository.resolve("tools/register_project_exe_exclusions.py")),
                "Only the existing project helper and explicitly selected reviewed interpreter are permitted");
        Path configuration = runtime.venvRoot().resolve("pyvenv.cfg");
        List<String> homes = Files.readAllLines(configuration).stream().filter(line -> line.stripLeading().startsWith("home ="))
                .map(line -> line.substring(line.indexOf('=') + 1).strip()).toList();
        NativeBridgeBuild.require(homes.size() == 1
                && Path.of(homes.getFirst()).toAbsolutePath().normalize().equals(runtime.pythonBaseRoot()),
                "venv base installation is not the reviewed complete runtime");
    }

    private static void verifyManifestBindings(Path repository, ManifestRuntime runtime,
            NativeRegistrationRuntimeInventory.Verified verified) throws IOException {
        var roots = verified.manifest().roots();
        boolean direct = runtime.interpreterRoute() == HelperInterpreterRoute.DIRECT_BASE;
        NativeBridgeBuild.require(Path.of(roots.repository()).equals(repository)
                && Path.of(roots.pythonBase()).equals(runtime.pythonBaseRoot())
                && Path.of(roots.venv()).equals(runtime.venvRoot())
                && (direct || roots.python().equals(runtime.python())) && roots.helper().equals(runtime.helper()),
                "complete manifest runtime belongs to another canonical producer/root");
        if(direct)NativeBridgeBuild.require(inventorySource(verified.manifest(),
                runtime.pythonBaseRoot().resolve("python.exe")).equals(runtime.python()),
                "direct base interpreter differs from its actual complete inventory witness");
    }

    /** Parse the real CMake codemodel and complete selected target/dependency source graph. */
    public static Graph readGraph(NativeBridgeBuild.Request request) throws IOException {
        ConfiguredGraph configured = readConfiguredGraph(request);
        var dll = ControlBuild.FileRef.measure(configured.bridgeDll());
        var injector = ControlBuild.FileRef.measure(configured.injector());
        requirePe(dll, true); requirePe(injector, false);
        var refs = new ArrayList<>(configured.graphRefs());
        for (String name : List.of(".ninja_deps", ".ninja_log")) pin(request.buildRoot().resolve(name), refs);
        return new Graph(configured.index(), configured.codemodel(), configured.injectorTarget(),
                configured.injectorTargetId(), configured.injectorSource(), dll, injector, NativeBridgeBuild.merge(refs));
    }

    private static ConfiguredGraph readConfiguredGraph(NativeBridgeBuild.Request request) throws IOException {
        Path reply = request.buildRoot().resolve(".cmake/api/v1/reply"); NativeBridgeBuild.plainDirectory(reply);
        List<Path> indexes;
        try (var stream = Files.list(reply)) { indexes = stream.filter(path -> path.getFileName().toString().startsWith("index-") && path.toString().endsWith(".json"))
                .sorted(Comparator.comparingLong(NativeBridgeDefender::modified)).toList(); }
        NativeBridgeBuild.require(!indexes.isEmpty(), "Actual CMake file-api reply missing");
        Path indexPath = indexes.getLast();
        if (indexes.size() > 1) NativeBridgeBuild.require(modified(indexes.get(indexes.size() - 2)) < modified(indexPath), "Ambiguous newest CMake index");
        var refs = new ArrayList<ControlBuild.FileRef>();
        var binding = request.compileSourceBindingRef() == null ? null : NativeBridgeBuild.sourceBinding(request);
        ControlBuild.FileRef index = pin(indexPath, refs); JsonNode indexJson = json(index);
        List<JsonNode> models = elements(indexJson.get("objects")).stream().filter(row -> textUnchecked(row, "kind").equals("codemodel")).toList();
        NativeBridgeBuild.require(models.size() == 1 && integer(models.getFirst().path("version"), "major") == 2, "Exact codemodel-v2 required");
        ControlBuild.FileRef modelRef = pin(replyPath(reply, text(models.getFirst(), "jsonFile")), refs); JsonNode model = json(modelRef);
        NativeBridgeBuild.require(path(text(model.path("paths"), "source")).equals(request.sourceRoot())
                && path(text(model.path("paths"), "build")).equals(request.buildRoot()), "Configured source/build roots differ");
        List<JsonNode> configurations = elements(model.get("configurations")).stream().filter(row -> Set.of("Release", "").contains(textUnchecked(row, "name"))).toList();
        NativeBridgeBuild.require(configurations.size() == 1, "Unique Release file-api configuration required");
        var byId = new HashMap<String, JsonNode>(); var byName = new HashMap<String, String>();
        for (JsonNode row : elements(configurations.getFirst().get("targets"))) {
            String id = text(row, "id"), name = text(row, "name");
            NativeBridgeBuild.require(byId.putIfAbsent(id, row) == null && byName.putIfAbsent(name, id) == null, "Ambiguous CMake target identity");
        }
        var pending = new ArrayDeque<String>();
        for (String target : NativeBridgeBuild.TARGETS) { NativeBridgeBuild.require(byName.containsKey(target), "Production bridge target is absent"); pending.add(byName.get(target)); }
        var visited = new HashSet<String>(); Path dll = null, injector = null; ControlBuild.FileRef injectorTarget = null; Path injectorSource = null;
        Set<Path> sources = request.completeSources().stream().map(row -> Path.of(row.path())).collect(java.util.stream.Collectors.toSet());
        while (!pending.isEmpty()) {
            String id = pending.removeFirst(); if (!visited.add(id)) continue; NativeBridgeBuild.require(visited.size() <= 512, "Bounded selected target graph required");
            JsonNode row = byId.get(id); NativeBridgeBuild.require(row != null, "Unknown target dependency");
            ControlBuild.FileRef targetPin = pin(replyPath(reply, text(row, "jsonFile")), refs); JsonNode target = json(targetPin);
            String name = text(target, "name"), type = text(target, "type"); NativeBridgeBuild.require(text(target, "id").equals(id) && name.equals(text(row, "name")), "Target identity differs");
            if (target.has("dependencies")) for (JsonNode dependency : elements(target.get("dependencies"))) pending.addLast(text(dependency, "id"));
            if (target.has("sources")) for (JsonNode source : elements(target.get("sources"))) {
                boolean generated = optionalBoolean(source, "isGenerated", false); Path sourcePath = Path.of(text(source, "path"));
                if (!sourcePath.isAbsolute()) sourcePath = request.sourceRoot().resolve(sourcePath).normalize();
                if (!generated) NativeBridgeBuild.require(sources.contains(sourcePath), "Configured target reads an unreviewed source outside complete frozen tree");
            }
            if (name.equals("xar_ck3_bridge") || name.equals(INJECTOR)) {
                NativeBridgeBuild.require(!optionalBoolean(target, "imported", false) && !optionalBoolean(target, "isGeneratorProvided", false), "Project output cannot be an imported/generated tool");
                List<JsonNode> artifacts = elements(target.get("artifacts")); String suffix = name.equals(INJECTOR) ? "xar_ck3_bridge_injector.exe" : "xar_ck3_bridge.dll";
                List<Path> matches = new ArrayList<>();
                for (JsonNode artifact : artifacts) { Path value = request.buildRoot().resolve(text(artifact, "path")).normalize(); if (value.getFileName().toString().equals(suffix)) matches.add(value); }
                NativeBridgeBuild.require(matches.size() == 1 && matches.getFirst().startsWith(request.buildRoot()), "Unique exact production artifact required");
                Path artifact = matches.getFirst();
                if (name.equals(INJECTOR)) {
                    NativeBridgeBuild.require(type.equals("EXECUTABLE"), "Injector target must be EXECUTABLE"); injector = artifact; injectorTarget = targetPin;
                    injectorSource = request.sourceRoot().resolve(text(target.path("paths"), "source")).normalize();
                    NativeBridgeBuild.require(injectorSource.startsWith(request.sourceRoot()), "Injector has external target source");
                } else { NativeBridgeBuild.require(type.equals("SHARED_LIBRARY"), "Bridge target must be SHARED_LIBRARY"); dll = artifact; }
            } else NativeBridgeBuild.require(!type.equals("EXECUTABLE"), "Unexpected executable dependency requires a new explicit producer contract");
        }
        NativeBridgeBuild.require(dll != null && injector != null && injectorTarget != null && injectorSource != null, "Research targets cannot replace real DLL and injector");
        Path cache = request.buildRoot().resolve("CMakeCache.txt"); pin(cache, refs); String cacheText = Files.readString(cache);
        NativeBridgeBuild.require(cacheText.contains("CMAKE_BUILD_TYPE:STRING=Release") && cacheText.contains("BUILD_TESTING:BOOL=OFF"), "Actual Release/testing cache differs");
        for (var definition : request.definitions()) NativeBridgeBuild.require(cacheText.contains(definition.option() + ":BOOL=" + definition.value()), "Actual selected boolean option differs");
        for (String file : List.of("build.ninja", "compile_commands.json")) pin(request.buildRoot().resolve(file), refs);
        for (JsonNode object : elements(indexJson.get("objects"))) if (text(object, "kind").equals("cmakeFiles")) {
            var cmakeFiles = pin(replyPath(reply, text(object, "jsonFile")), refs);
            var configureSources = new ArrayList<Path>();
            for (JsonNode input : elements(json(cmakeFiles).get("inputs"))) if (!optionalBoolean(input, "isGenerated", false)) {
                Path source = Path.of(text(input, "path")); if (!source.isAbsolute()) source = request.sourceRoot().resolve(source).normalize();
                configureSources.add(source);
            }
            refs.addAll(NativeBridgeBuild.sourceReferences(request, binding, configureSources));
        }
        NativeBridgeBuild.require(elements(indexJson.get("objects")).stream().anyMatch(row -> textUnchecked(row, "kind").equals("cmakeFiles")), "Complete actual CMake configure inputs missing");
        return new ConfiguredGraph(index, modelRef, injectorTarget, byName.get(INJECTOR), injectorSource, dll, injector, NativeBridgeBuild.merge(refs));
    }

    static Manifest manifest(NativeBridgeBuild.Request request, Graph graph) {
        return new Manifest(SCHEMA, request.canonicalRepository().toString(), request.sourceRoot().toString(), request.buildRoot().toString(), "Release",
                List.of(INJECTOR), CANDIDATE, new FileApiPin(graph.index().path(), graph.index().sha256()),
                new FileApiPin(graph.codemodel().path(), graph.codemodel().sha256()),
                List.of(new TargetProvenance(graph.injectorTarget().path(), graph.injectorTarget().sha256(), INJECTOR, graph.injectorTargetId(), graph.injectorSource().toString())),
                List.of(new ManifestFile(graph.injector().path(), graph.injector().bytes(), graph.injector().sha256(), INJECTOR, graph.injectorTargetId())));
    }
    public static ControlBuild.FileRef writeManifest(NativeBridgeBuild.Request request, Graph graph, Path output) throws IOException {
        NativeBridgeBuild.inside(request.stageRoot(), output); return NativeBridgeBuild.writeNew(output, manifest(request, graph));
    }
    public static void verifyManifest(NativeBridgeBuild.Request request, Graph graph, ControlBuild.FileRef ref) throws IOException {
        NativeBridgeBuild.require(ref != null && Path.of(ref.path()).equals(request.stageRoot().resolve("manifest.json")), "Exact registration manifest output missing");
        Manifest declared = ControlBuild.strictMapper().readValue(NativeBridgeBuild.read(ref, 1 << 20), Manifest.class);
        NativeBridgeBuild.require(declared.equals(manifest(request, graph)), "Original CMake manifest or exact injector changed");
    }
    public static List<String> command(NativeBridgeBuild.Request request, ControlBuild.FileRef manifest, Path receipt) {
        Objects.requireNonNull(manifest); NativeBridgeBuild.absolute(receipt);
        if (!Path.of(manifest.path()).equals(request.stageRoot().resolve("manifest.json")) || !receipt.equals(request.stageRoot().resolve("helper-receipt.json")))
            throw new IllegalArgumentException("Only the exact stage manifest and receipt are permitted");
        var command = new ArrayList<String>(); command.add(request.defender().python().path());
        if (request.defender() instanceof ManifestRuntime runtime && runtime.interpreterRoute() == HelperInterpreterRoute.DIRECT_BASE)
            command.addAll(List.of("-E", "-s"));
        command.addAll(List.of("-B", "-X", "utf8", request.defender().helper().path(),
                "--manifest", manifest.path(), "--receipt", receipt.toString()));
        return List.copyOf(command);
    }
    public static Readback readVerified(ControlBuild.FileRef receipt, ControlBuild.FileRef manifestPin,
            ControlBuild.FileRef expectedInjector) throws IOException {
        return readBuiltVerified(receipt, manifestPin, expectedInjector, INJECTOR, expectedInjector);
    }
    /** Ordinary helper/broker receipt consumer. This never executes the historical direct-UAC CLI. */
    public static Readback readBuiltFixtureVerified(ControlBuild.FileRef receipt, ControlBuild.FileRef manifest,
            ControlBuild.FileRef executable, NativeFixtureBuild.FixtureTarget target) throws IOException {
        return readBuiltFixtureVerified(receipt, manifest, executable, target, executable);
    }
    /** Caller separately qualifies the original-to-retained executable map through NativeFixtureBuild. */
    public static Readback readBuiltFixtureVerified(ControlBuild.FileRef receipt, ControlBuild.FileRef manifest,
            ControlBuild.FileRef executable, NativeFixtureBuild.FixtureTarget target,
            ControlBuild.FileRef retainedExecutable) throws IOException {
        Objects.requireNonNull(target);
        var readback = readBuiltVerified(receipt, manifest, executable, target.targetName(), retainedExecutable);
        NativeBridgeBuild.require(readback.route() == ReadbackRoute.PROTECTED_SYSTEM_BROKER,
                "Ordinary fixture broker reader cannot import a direct-UAC receipt");
        return readback;
    }
    private static Readback readBuiltVerified(ControlBuild.FileRef receipt, ControlBuild.FileRef manifestPin,
            ControlBuild.FileRef executable, String exactTarget, ControlBuild.FileRef readableExecutable) throws IOException {
        var common = requireBuiltReceipt(receipt, manifestPin, executable, exactTarget, readableExecutable);
        JsonNode result = common.result(); String semantic = common.semantic();
        List<String> before = common.before(), after = common.after();
        ReadbackRoute route = ReadbackRoute.DIRECT_ADMIN; List<ControlBuild.FileRef> extra = List.of();
        if (result.has("broker_schema")) {
            route = ReadbackRoute.PROTECTED_SYSTEM_BROKER;
            String brokerSchema = text(result, "broker_schema");
            NativeBridgeBuild.require((BROKER_ARRAY_SCHEMA.equals(brokerSchema) || BROKER_NULLABLE_SCHEMA.equals(brokerSchema))
                    && text(result, "system_token_sid").equals("S-1-5-18"), "Actual protected SYSTEM receipt required");
            JsonNode identity = object(result.get("broker_identity"));
            Set<String> identityKeys = new HashSet<>(); identity.fieldNames().forEachRemaining(identityKeys::add);
            NativeBridgeBuild.require(identityKeys.equals(Set.of("installation_id", "owner_sid", "request_id", "request_sha256",
                    "manifest_bytes_sha256", "policy_sha256", "runtime_manifest_sha256", "runtime_verified",
                    "protected_code", "request_owner_sid", "actual_token_sid"))
                    && bool(identity, "runtime_verified") && bool(identity, "protected_code")
                    && text(identity, "actual_token_sid").equals("S-1-5-18"), "Broker code/token origin unverified");
            NativeProjectExeUac.requireCanonicalSid(text(identity, "owner_sid"));
            if (BROKER_NULLABLE_SCHEMA.equals(brokerSchema)) {
                NativeProjectExeUac.qualifyProtectedBrokerSettings(result);
            } else {
                NativeBridgeBuild.require((!result.has("settings_readback_schema")
                        || "xar.project-exe-three-settings-readback/v1".equals(text(result, "settings_readback_schema")))
                        && !result.has("before_property_observations") && !result.has("after_property_observations")
                        && !result.has("nullable_observation_scope"), "Broker version1 is array-only historical evidence");
                for (String setting : List.of("ExclusionPath", "ExclusionExtension", "ExclusionProcess")) {
                    List<String> old = strings(result.path("before_settings").get(setting)), current = strings(result.path("after_settings").get(setting));
                    if (setting.equals("ExclusionPath")) NativeBridgeBuild.require(old.equals(before) && current.equals(after), "Broker path arrays disagree");
                    else NativeBridgeBuild.require(new HashSet<>(old).equals(new HashSet<>(current)), "Broker changed nonpath exclusions");
                }
            }
            NativeBridgeBuild.require(bool(result, "observed_extensions_unchanged") && bool(result, "observed_processes_unchanged"), "Broker nonpath preservation evidence missing");
            extra = verifyBrokerProof(receipt, manifestPin, result, identity);
        } else NativeBridgeBuild.require(text(result, "readback_visibility").equals("same administrative token and WMI client for before/after")
                && text(result, "namespace").equals("root\\Microsoft\\Windows\\Defender"), "Direct same-admin WMI source is missing");
        readableExecutable.verify(); receipt.verify(); manifestPin.verify(); return new Readback(route, receipt, semantic, before, after, extra);
    }

    private record BuiltReceipt(JsonNode result, String semantic, List<String> before, List<String> after) { }
    private static BuiltReceipt requireBuiltReceipt(ControlBuild.FileRef receipt, ControlBuild.FileRef manifestPin,
            ControlBuild.FileRef expectedInjector, String expectedTarget) throws IOException {
        return requireBuiltReceipt(receipt, manifestPin, expectedInjector, expectedTarget, expectedInjector);
    }
    private static BuiltReceipt requireBuiltReceipt(ControlBuild.FileRef receipt, ControlBuild.FileRef manifestPin,
            ControlBuild.FileRef expectedInjector, String expectedTarget, ControlBuild.FileRef readableExecutable) throws IOException {
        JsonNode manifest = json(manifestPin), result = json(receipt);
        NativeBridgeBuild.require(text(manifest, "schema").equals(SCHEMA) && text(result, "schema").equals(SCHEMA)
                && text(result, "status").equals("verified") && bool(result, "admin_token")
                && !bool(result, "settings_success_is_runtime_trust") && !bool(result, "partial_mutation")
                && bool(result, "observed_prior_settings_preserved"), "Actual administrative verified readback required; ACK/disabled/ordinary empty arrays are insufficient");
        String semantic = NativeProjectExeUac.semanticSha(manifest);
        NativeBridgeBuild.require(semantic.equals(text(result, "manifest_sha256")) && manifest.get("files").equals(result.get("files")), "Actual receipt manifest and EXE identities differ");
        List<JsonNode> files = elements(manifest.get("files")); NativeBridgeBuild.require(files.size() == 1, "Only the exact selected project EXE may be registered");
        JsonNode file = files.getFirst(); NativeBridgeBuild.require(text(file, "path").equals(expectedInjector.path()) && integer(file, "size") == expectedInjector.bytes()
                && text(file, "sha256").equals(expectedInjector.sha256()) && text(file, "target").equals(expectedTarget), "Exact built project EXE receipt required");
        List<String> before = strings(result.get("before")), after = strings(result.get("after"));
        NativeBridgeBuild.require(paths(after).containsAll(paths(before)) && paths(after).contains(expectedInjector.path().replace('/', '\\').toLowerCase(Locale.ROOT))
                && strings(result.get("verified_requested_paths")).equals(List.of(expectedInjector.path()))
                && strings(result.get("missing_requested_paths")).isEmpty(), "Settings readback lost prior paths or the exact project EXE exclusion");
        NativeBridgeBuild.require(expectedInjector.bytes() == readableExecutable.bytes()
                && expectedInjector.sha256().equals(readableExecutable.sha256()), "Retained executable bytes differ from original manifest identity");
        readableExecutable.verify(); receipt.verify(); manifestPin.verify();
        return new BuiltReceipt(result, semantic, before, after);
    }
    /** The same original built-manifest checks, limited to a caller's qualified single fixture. */
    static void requireDirectBuiltFixtureReceipt(ControlBuild.FileRef receipt, ControlBuild.FileRef manifest,
            ControlBuild.FileRef executable, String exactTarget) throws IOException {
        requireDirectBuiltFixtureReceipt(receipt, manifest, executable, exactTarget, executable);
    }
    /** Historical caller first qualifies the original-to-retained executable map through NativeFixtureBuild. */
    static void requireDirectBuiltFixtureReceipt(ControlBuild.FileRef receipt, ControlBuild.FileRef manifest,
            ControlBuild.FileRef executable, String exactTarget, ControlBuild.FileRef retainedExecutable) throws IOException {
        var common = requireBuiltReceipt(receipt, manifest, executable, exactTarget, retainedExecutable); JsonNode result = common.result();
        NativeBridgeBuild.require(!result.has("broker_schema")
                && text(result, "readback_visibility").equals("same administrative token and WMI client for before/after")
                && text(result, "namespace").equals("root\\Microsoft\\Windows\\Defender"),
                "Built fixture requires the one actual same-owner direct administrative helper");
    }
    private static List<ControlBuild.FileRef> verifyBrokerProof(ControlBuild.FileRef receipt, ControlBuild.FileRef manifest,
            JsonNode result, JsonNode identity) throws IOException {
        Path stageRoot = Path.of(receipt.path()).getParent(); List<Path> roots;
        try (var stream = Files.list(stageRoot)) { roots = stream.filter(path -> path.getFileName().toString().startsWith("broker-proof-")).toList(); }
        NativeBridgeBuild.require(roots.size() == 1, "One actual existing helper broker proof directory required"); Path root = roots.getFirst();
        List<ControlBuild.FileRef> refs = NativeBridgeBuild.inventory(root);
        Set<String> required = Set.of("installed-policy.json", "installed-runtime-seal.json", "installed-manifest.json", "task-readback.json", "manifest.json", "request.json", "protected-worker-receipt.json", "proof.json");
        NativeBridgeBuild.require(refs.size() == required.size() && refs.stream().allMatch(pin -> required.contains(Path.of(pin.path()).getFileName().toString())), "Complete original broker proof set differs");
        JsonNode policy = json(ControlBuild.FileRef.measure(root.resolve("installed-policy.json")));
        JsonNode seal = json(ControlBuild.FileRef.measure(root.resolve("installed-runtime-seal.json")));
        JsonNode request = json(ControlBuild.FileRef.measure(root.resolve("request.json")));
        JsonNode proof = json(ControlBuild.FileRef.measure(root.resolve("proof.json")));
        ControlBuild.FileRef requestPin = ControlBuild.FileRef.measure(root.resolve("request.json")), policyPin = ControlBuild.FileRef.measure(root.resolve("installed-policy.json"));
        ControlBuild.FileRef sealPin = ControlBuild.FileRef.measure(root.resolve("installed-runtime-seal.json"));
        NativeBridgeBuild.require(json(ControlBuild.FileRef.measure(root.resolve("protected-worker-receipt.json"))).equals(result)
                && json(ControlBuild.FileRef.measure(root.resolve("manifest.json"))).equals(json(manifest))
                && text(proof, "status").equals("verified") && text(proof, "copied_receipt_bytes_sha256").equals(receipt.sha256())
                && text(identity, "request_sha256").equals(requestPin.sha256()) && text(identity, "policy_sha256").equals(policyPin.sha256())
                && text(identity, "runtime_manifest_sha256").equals(sealPin.sha256()) && text(identity, "manifest_bytes_sha256").equals(manifest.sha256())
                && text(identity, "installation_id").equals(text(policy, "installation_id")) && text(identity, "installation_id").equals(text(seal, "installation_id"))
                && text(identity, "request_id").equals(text(request, "request_id")) && text(identity, "owner_sid").equals(text(policy, "owner_sid"))
                && text(identity, "request_owner_sid").equals(text(policy, "owner_sid")), "Broker receipt is not bound to original request/policy/seal/raw bytes");
        JsonNode copiedPins = object(proof.get("pins"));
        Set<String> copiedNames = new HashSet<>(); copiedPins.fieldNames().forEachRemaining(copiedNames::add);
        var expectedNames = new HashSet<>(required); expectedNames.remove("proof.json");
        NativeBridgeBuild.require(copiedNames.equals(expectedNames), "Broker proof must bind all seven original copied leaves");
        for (var ref : refs) if (!Path.of(ref.path()).getFileName().toString().equals("proof.json")) {
            JsonNode pin = object(copiedPins.get(Path.of(ref.path()).getFileName().toString()));
            NativeBridgeBuild.require(Path.of(text(pin, "path")).equals(Path.of(ref.path()))
                    && integer(pin, "size") == ref.bytes() && text(pin, "sha256").equals(ref.sha256()),
                    "Broker copied original differs from its protected proof pin");
        }
        for (var ref : refs) ref.verify();
        return refs;
    }
    static void requirePe(ControlBuild.FileRef file, boolean dll) throws IOException {
        NativeBridgeBuild.require(file.bytes() >= 64 && file.bytes() <= (64L << 20), "Bounded actual PE output required"); SharedSourceFiles.plainAncestors(Path.of(file.path())); file.verify();
        try (var input = new RandomAccessFile(file.path(), "r")) {
            NativeBridgeBuild.require(input.readUnsignedByte() == 'M' && input.readUnsignedByte() == 'Z', "Output lacks MZ signature");
            input.seek(60); long offset = Integer.toUnsignedLong(Integer.reverseBytes(input.readInt()));
            NativeBridgeBuild.require(offset >= 64 && offset <= file.bytes() - 24, "PE header offset outside file"); input.seek(offset);
            NativeBridgeBuild.require(input.readInt() == 0x50450000 && Short.toUnsignedInt(Short.reverseBytes(input.readShort())) == 0x8664, "Actual x64 PE image required");
            input.seek(offset + 22); int characteristics = Short.toUnsignedInt(Short.reverseBytes(input.readShort()));
            NativeBridgeBuild.require(((characteristics & 0x2000) != 0) == dll, "DLL/EXE PE role differs");
        }
        file.verify();
    }

    public static final String DECLARED_SCHEMA = "xar.project-exe-declared-path-exclusions/v1";
    public enum DeclaredOutputState { ABSENT }
    public record DeclaredOutput(String path, String target, String targetId, DeclaredOutputState expectedState) {
        public DeclaredOutput {
            if (path == null || !Path.of(path).isAbsolute() || !Path.of(path).equals(Path.of(path).toAbsolutePath().normalize())
                    || !INJECTOR.equals(target) || targetId == null || targetId.isBlank() || expectedState != DeclaredOutputState.ABSENT
                    || !Path.of(path).getFileName().toString().equals(INJECTOR + ".exe")
                    || path.chars().anyMatch(character -> character == '*' || character == '?' || character == '%'))
                throw new IllegalArgumentException("One exact absent project injector declaration required");
        }
    }
    public record ConfiguredGraph(ControlBuild.FileRef index, ControlBuild.FileRef codemodel,
            ControlBuild.FileRef injectorTarget, String injectorTargetId, Path injectorSource,
            Path bridgeDll, Path injector, List<ControlBuild.FileRef> graphRefs) {
        public ConfiguredGraph { graphRefs = NativeBridgeBuild.unique(graphRefs); }
        public DeclaredOutput output() {
            return new DeclaredOutput(injector.toString(), INJECTOR, injectorTargetId, DeclaredOutputState.ABSENT);
        }
    }
    public record DeclaredSource(String schema, String machineId, ControlBuild.FileRef declarationRequestRef,
            ControlBuild.FileRef configureActualRef, List<ControlBuild.FileRef> configuredGraphRefs,
            ControlBuild.FileRef producerToolsBuildRef) {
        public DeclaredSource {
            if (!"xar.native-declared-output-source/v1".equals(schema)) throw new IllegalArgumentException("Declared source version required");
            Objects.requireNonNull(machineId); Objects.requireNonNull(declarationRequestRef);
            Objects.requireNonNull(configureActualRef); Objects.requireNonNull(producerToolsBuildRef);
            configuredGraphRefs = NativeBridgeBuild.unique(configuredGraphRefs);
            if (configuredGraphRefs.isEmpty()) throw new IllegalArgumentException("Actual configured graph witnesses required");
        }
    }
    public record DeclaredManifest(String schema, String machineId, String repo, String sourceDir, String buildDir,
            String configuration, List<String> requestedTargets, String externalCandidate,
            ControlBuild.FileRef sourceDeclarationRef, List<ControlBuild.FileRef> completeSourceRefs,
            FileApiPin cmakeIndex, FileApiPin cmakeCodemodel, List<TargetProvenance> targetProvenance,
            List<ControlBuild.FileRef> configuredGraphRefs, List<DeclaredOutput> declaredOutputs) {
        public DeclaredManifest {
            if (!DECLARED_SCHEMA.equals(schema)) throw new IllegalArgumentException("Declared path manifest version required");
            requestedTargets = List.copyOf(requestedTargets); completeSourceRefs = NativeBridgeBuild.unique(completeSourceRefs);
            configuredGraphRefs = NativeBridgeBuild.unique(configuredGraphRefs); targetProvenance = List.copyOf(targetProvenance);
            declaredOutputs = List.copyOf(declaredOutputs); Objects.requireNonNull(sourceDeclarationRef);
            if (!requestedTargets.equals(List.of(INJECTOR)) || declaredOutputs.size() != 1
                    || !Path.of(declaredOutputs.getFirst().path()).equals(Path.of(buildDir).resolve(INJECTOR + ".exe")))
                throw new IllegalArgumentException("Only the declared injector output path is admitted");
        }
    }
    /** Configured target identity is evidence; this method does not qualify a compiled binary. */
    public static ConfiguredGraph readDeclaredGraph(NativeBridgeBuild.Request request) throws IOException {
        ConfiguredGraph graph = readConfiguredGraph(request);
        requireAbsent(graph.output());
        return graph;
    }
    static void requireAbsent(DeclaredOutput output) throws IOException {
        Path path = Path.of(output.path()); NativeBridgeBuild.plainDirectory(path.getParent());
        NativeBridgeBuild.require(Files.notExists(path, LinkOption.NOFOLLOW_LINKS),
                "Declared exact output must be proven absent; present, reparse and unknown are rejected");
    }
    public static DeclaredManifest declaredManifest(NativeBridgeBuild.Request request, ConfiguredGraph graph,
            ControlBuild.FileRef declaration) throws IOException {
        declaration.verify(); NativeBridgeBuild.verify(request.completeSources()); NativeBridgeBuild.verify(graph.graphRefs()); requireAbsent(graph.output());
        return new DeclaredManifest(DECLARED_SCHEMA, request.machineId(), request.canonicalRepository().toString(),
                request.sourceRoot().toString(), request.buildRoot().toString(), "Release", List.of(INJECTOR), CANDIDATE,
                declaration, request.completeSources(),
                new FileApiPin(graph.index().path(), graph.index().sha256()), new FileApiPin(graph.codemodel().path(), graph.codemodel().sha256()),
                List.of(new TargetProvenance(graph.injectorTarget().path(), graph.injectorTarget().sha256(), INJECTOR,
                        graph.injectorTargetId(), graph.injectorSource().toString())), graph.graphRefs(), List.of(graph.output()));
    }
    /** Passive candidate producer. The Root-reviewed plan remains the action authorization boundary. */
    public static ControlBuild.FileRef writeDeclaredSource(ControlBuild.FileRef requestPin,
            ControlBuild.FileRef configureActual, Path output) throws IOException {
        NativeBridgeBuild.Request request = NativeBridgeBuild.readRequest(requestPin);
        NativeBridgeBuild.require((NativeBridgeBuild.REQUEST_SCHEMA.equals(request.schema()) || NativeBridgeBuild.BOUND_REQUEST_SCHEMA.equals(request.schema()))
                && request.stage() == NativeBridgeBuild.Stage.ENV
                && request.machineId().equals(WindowsJobProcess.currentMachineId()),
                "Exact complete declared source request required");
        NativeBridgeBuild.validateSources(request);
        var before = NativeBridgeBuild.observeRequestSources(request);
        NativeProjectExeUac.requireConfiguredDeclaration(configureActual, request);
        ConfiguredGraph graph = readDeclaredGraph(request);
        var value = new DeclaredSource("xar.native-declared-output-source/v1", request.machineId(),
                requestPin, configureActual, graph.graphRefs(), request.qualifiedToolsBuild());
        var result = writeDeclarationCandidate(request, output, value);
        NativeBridgeBuild.assertLiveSourceBinding(request, before); return result;
    }
    public static ControlBuild.FileRef writeDeclaredManifest(ControlBuild.FileRef sourceDeclaration, Path output) throws IOException {
        var source = RootNativePlanJson.mapper().readValue(NativeBridgeBuild.read(sourceDeclaration, 32 << 20), DeclaredSource.class);
        NativeBridgeBuild.Request request = NativeBridgeBuild.readRequest(source.declarationRequestRef());
        NativeBridgeBuild.require(source.machineId().equals(request.machineId())
                && source.producerToolsBuildRef().equals(request.qualifiedToolsBuild()),
                "Declared manifest source closure changed");
        NativeBridgeBuild.validateSources(request);
        var before = NativeBridgeBuild.observeRequestSources(request);
        NativeProjectExeUac.requireConfiguredDeclaration(source.configureActualRef(), request);
        ConfiguredGraph graph = readDeclaredGraph(request);
        NativeBridgeBuild.require(source.configuredGraphRefs().equals(graph.graphRefs()), "Configured declaration graph changed");
        var result = writeDeclarationCandidate(request, output, declaredManifest(request, graph, sourceDeclaration));
        NativeBridgeBuild.assertLiveSourceBinding(request, before); return result;
    }
    private static ControlBuild.FileRef writeDeclarationCandidate(NativeBridgeBuild.Request request, Path output, Object value) throws IOException {
        NativeBridgeBuild.inside(request.scratchRoot(), output); NativeBridgeBuild.plainDirectory(output.getParent());
        NativeBridgeBuild.require(!output.startsWith(request.sourceRoot()) && !output.startsWith(request.buildRoot()),
                "Declaration candidate cannot modify source/build");
        Files.write(output, RootNativePlanJson.mapper().writerWithDefaultPrettyPrinter().writeValueAsBytes(value),
                java.nio.file.StandardOpenOption.CREATE_NEW, java.nio.file.StandardOpenOption.WRITE);
        return ControlBuild.FileRef.measure(output);
    }
    /** New schema cannot be imported as a FileRef, built manifest or Native BUILD/REGISTER actual. */
    static Readback readDeclaredVerified(ControlBuild.FileRef receiptPin, ControlBuild.FileRef manifestPin,
            DeclaredOutput expected) throws IOException {
        JsonNode manifest = json(manifestPin), result = json(receiptPin);
        var typed = ControlBuild.strictMapper().treeToValue(manifest, DeclaredManifest.class);
        NativeBridgeBuild.require(typed.declaredOutputs().equals(List.of(expected))
                && DECLARED_SCHEMA.equals(text(result, "schema")) && "verified".equals(text(result, "status"))
                && bool(result, "admin_token") && !result.has("broker_schema") && !bool(result, "settings_success_is_runtime_trust")
                && !bool(result, "partial_mutation") && bool(result, "observed_prior_settings_preserved")
                && "DECLARED_PROJECT_EXE_PATH_ONLY".equals(text(result, "proof_scope"))
                && !result.has("files") && manifest.get("declared_outputs").equals(result.get("declared_outputs"))
                && NativeProjectExeUac.semanticSha(manifest).equals(text(result, "manifest_sha256")),
                "Exact declared-path-only administrator receipt required");
        var before = strings(result.get("before")); var after = strings(result.get("after"));
        NativeBridgeBuild.require(paths(after).containsAll(paths(before))
                && paths(after).contains(expected.path().replace('/', '\\').toLowerCase(Locale.ROOT))
                && strings(result.get("verified_requested_paths")).equals(List.of(expected.path()))
                && strings(result.get("missing_requested_paths")).isEmpty()
                && text(result, "readback_visibility").equals("same administrative token and WMI client for before/after")
                && text(result, "namespace").equals("root\\Microsoft\\Windows\\Defender"),
                "Fresh same-admin declared path and preserved prior paths required");
        requireAbsent(expected); receiptPin.verify(); manifestPin.verify();
        return new Readback(ReadbackRoute.DIRECT_ADMIN, receiptPin, NativeProjectExeUac.semanticSha(manifest), before, after, List.of());
    }

    private static ControlBuild.FileRef pin(Path path, List<ControlBuild.FileRef> refs) throws IOException { SharedSourceFiles.plainAncestors(path); var pin = ControlBuild.FileRef.measure(path); refs.add(pin); return pin; }
    private static Path replyPath(Path root, String relative) throws IOException { Path path = root.resolve(relative).normalize(); NativeBridgeBuild.require(path.startsWith(root) && !path.equals(root), "CMake reply path escaped root"); return path; }
    private static long modified(Path path) { try { return Files.getLastModifiedTime(path, LinkOption.NOFOLLOW_LINKS).toMillis(); } catch (IOException error) { throw new java.io.UncheckedIOException(error); } }
    private static Path path(String value) { return Path.of(value).toAbsolutePath().normalize(); }
    private static JsonNode json(ControlBuild.FileRef pin) throws IOException { return object(ControlBuild.strictMapper().readTree(NativeBridgeBuild.read(pin, 16 << 20))); }
    private static JsonNode object(JsonNode value) throws IOException { NativeBridgeBuild.require(value != null && value.isObject(), "Native JSON object required"); return value; }
    private static List<JsonNode> elements(JsonNode value) throws IOException { NativeBridgeBuild.require(value != null && value.isArray(), "Native JSON array required"); var result = new ArrayList<JsonNode>(); value.forEach(result::add); return List.copyOf(result); }
    private static String text(JsonNode value, String key) throws IOException { JsonNode field = object(value).get(key); NativeBridgeBuild.require(field != null && field.isTextual(), "Native string field required: " + key); return field.textValue(); }
    private static String textUnchecked(JsonNode value, String key) { try { return text(value, key); } catch (IOException error) { throw new java.io.UncheckedIOException(error); } }
    private static long integer(JsonNode value, String key) throws IOException { JsonNode field = object(value).get(key); NativeBridgeBuild.require(field != null && field.isIntegralNumber() && field.canConvertToLong(), "Exact JSON integer required: " + key); return field.longValue(); }
    private static boolean bool(JsonNode value, String key) throws IOException { JsonNode field = object(value).get(key); NativeBridgeBuild.require(field != null && field.isBoolean(), "Exact JSON boolean required: " + key); return field.booleanValue(); }
    private static boolean optionalBoolean(JsonNode value, String key, boolean missing) throws IOException { return value.has(key) ? bool(value, key) : missing; }
    private static List<String> strings(JsonNode value) throws IOException { var result = new ArrayList<String>(); for (JsonNode row : elements(value)) { NativeBridgeBuild.require(row.isTextual(), "Native string array required"); result.add(row.textValue()); } return List.copyOf(result); }
    private static Set<String> paths(List<String> values) { return values.stream().map(value -> value.replace('/', '\\').toLowerCase(Locale.ROOT)).collect(java.util.stream.Collectors.toSet()); }
}
