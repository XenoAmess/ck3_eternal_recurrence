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
    private NativeBridgeDefender() { }
    public record HelperRuntime(Path pythonBaseRoot, Path venvRoot, ControlBuild.FileRef python,
            ControlBuild.FileRef helper, List<ControlBuild.FileRef> completePythonFiles,
            List<ControlBuild.FileRef> completeHelperSources) {
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

    public static void verifyHelperRuntime(Path repository, HelperRuntime runtime) throws IOException {
        NativeBridgeBuild.require(runtime.venvRoot().equals(repository.resolve("tools/.venv"))
                && Path.of(runtime.python().path()).equals(runtime.venvRoot().resolve("Scripts/python.exe"))
                && Path.of(runtime.helper().path()).equals(repository.resolve("tools/register_project_exe_exclusions.py")), "Only the existing project helper and canonical repository interpreter are permitted");
        var allPython = new ArrayList<>(NativeBridgeBuild.inventory(runtime.pythonBaseRoot())); allPython.addAll(NativeBridgeBuild.inventory(runtime.venvRoot()));
        NativeBridgeBuild.require(NativeBridgeBuild.merge(allPython).equals(runtime.completePythonFiles()), "Complete existing Python base/venv file closure differs");
        Path configuration = runtime.venvRoot().resolve("pyvenv.cfg");
        List<String> homes = Files.readAllLines(configuration).stream().filter(line -> line.stripLeading().startsWith("home ="))
                .map(line -> line.substring(line.indexOf('=') + 1).strip()).toList();
        NativeBridgeBuild.require(homes.size() == 1 && Path.of(homes.getFirst()).toAbsolutePath().normalize().equals(runtime.pythonBaseRoot()), "venv base installation is not the reviewed complete runtime");
        var sources = new ArrayList<>(NativeBridgeBuild.inventory(repository.resolve("tools/project_exe_broker")));
        sources.add(ControlBuild.FileRef.measure(repository.resolve("tools/register_project_exe_exclusions.py")));
        sources.add(ControlBuild.FileRef.measure(repository.resolve("tools/project_exe_exclusion_broker_client.py")));
        NativeBridgeBuild.require(NativeBridgeBuild.merge(sources).equals(runtime.completeHelperSources()), "Complete existing helper/client/broker source package differs");
        NativeBridgeBuild.verify(runtime.references());
    }

    /** Parse the real CMake codemodel and complete selected target/dependency source graph. */
    public static Graph readGraph(NativeBridgeBuild.Request request) throws IOException {
        Path reply = request.buildRoot().resolve(".cmake/api/v1/reply"); NativeBridgeBuild.plainDirectory(reply);
        List<Path> indexes;
        try (var stream = Files.list(reply)) { indexes = stream.filter(path -> path.getFileName().toString().startsWith("index-") && path.toString().endsWith(".json"))
                .sorted(Comparator.comparingLong(NativeBridgeDefender::modified)).toList(); }
        NativeBridgeBuild.require(!indexes.isEmpty(), "Actual CMake file-api reply missing");
        Path indexPath = indexes.getLast();
        if (indexes.size() > 1) NativeBridgeBuild.require(modified(indexes.get(indexes.size() - 2)) < modified(indexPath), "Ambiguous newest CMake index");
        var refs = new ArrayList<ControlBuild.FileRef>(); ControlBuild.FileRef index = pin(indexPath, refs); JsonNode indexJson = json(index);
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
        var visited = new HashSet<String>(); ControlBuild.FileRef dll = null, injector = null, injectorTarget = null; Path injectorSource = null;
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
                ControlBuild.FileRef artifact = ControlBuild.FileRef.measure(matches.getFirst()); requirePe(artifact, name.equals("xar_ck3_bridge"));
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
        for (String file : List.of("build.ninja", "compile_commands.json", ".ninja_deps", ".ninja_log")) pin(request.buildRoot().resolve(file), refs);
        for (JsonNode object : elements(indexJson.get("objects"))) if (text(object, "kind").equals("cmakeFiles")) {
            var cmakeFiles = pin(replyPath(reply, text(object, "jsonFile")), refs);
            for (JsonNode input : elements(json(cmakeFiles).get("inputs"))) if (!optionalBoolean(input, "isGenerated", false)) {
                Path source = Path.of(text(input, "path")); if (!source.isAbsolute()) source = request.sourceRoot().resolve(source).normalize(); pin(source, refs);
            }
        }
        NativeBridgeBuild.require(elements(indexJson.get("objects")).stream().anyMatch(row -> textUnchecked(row, "kind").equals("cmakeFiles")), "Complete actual CMake configure inputs missing");
        return new Graph(index, modelRef, injectorTarget, byName.get(INJECTOR), injectorSource, dll, injector, NativeBridgeBuild.merge(refs));
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
        return List.of(request.defender().python().path(), "-B", "-X", "utf8", request.defender().helper().path(),
                "--manifest", manifest.path(), "--receipt", receipt.toString());
    }
    public static Readback readVerified(ControlBuild.FileRef receipt, ControlBuild.FileRef manifestPin,
            ControlBuild.FileRef expectedInjector) throws IOException {
        JsonNode manifest = json(manifestPin), result = json(receipt);
        NativeBridgeBuild.require(text(manifest, "schema").equals(SCHEMA) && text(result, "schema").equals(SCHEMA)
                && text(result, "status").equals("verified") && bool(result, "admin_token")
                && !bool(result, "settings_success_is_runtime_trust") && !bool(result, "partial_mutation")
                && bool(result, "observed_prior_settings_preserved"), "Actual administrative verified readback required; ACK/disabled/ordinary empty arrays are insufficient");
        String semantic = NativeProjectExeUac.semanticSha(manifest);
        NativeBridgeBuild.require(semantic.equals(text(result, "manifest_sha256")) && manifest.get("files").equals(result.get("files")), "Actual receipt manifest and EXE identities differ");
        List<JsonNode> files = elements(manifest.get("files")); NativeBridgeBuild.require(files.size() == 1, "Only the built injector may be registered");
        JsonNode file = files.getFirst(); NativeBridgeBuild.require(text(file, "path").equals(expectedInjector.path()) && integer(file, "size") == expectedInjector.bytes()
                && text(file, "sha256").equals(expectedInjector.sha256()) && text(file, "target").equals(INJECTOR), "Exact built injector receipt required");
        List<String> before = strings(result.get("before")), after = strings(result.get("after"));
        NativeBridgeBuild.require(paths(after).containsAll(paths(before)) && paths(after).contains(expectedInjector.path().replace('/', '\\').toLowerCase(Locale.ROOT))
                && strings(result.get("verified_requested_paths")).equals(List.of(expectedInjector.path()))
                && strings(result.get("missing_requested_paths")).isEmpty(), "Settings readback lost prior paths or exact injector exclusion");
        ReadbackRoute route = ReadbackRoute.DIRECT_ADMIN; List<ControlBuild.FileRef> extra = List.of();
        if (result.has("broker_schema")) {
            route = ReadbackRoute.PROTECTED_SYSTEM_BROKER;
            NativeBridgeBuild.require(text(result, "broker_schema").equals("xar.project-exe-broker.receipt.v1") && text(result, "system_token_sid").equals("S-1-5-18"), "Actual protected SYSTEM receipt required");
            JsonNode identity = object(result.get("broker_identity"));
            NativeBridgeBuild.require(bool(identity, "runtime_verified") && bool(identity, "protected_code") && text(identity, "actual_token_sid").equals("S-1-5-18"), "Broker code/token origin unverified");
            for (String setting : List.of("ExclusionPath", "ExclusionExtension", "ExclusionProcess")) {
                List<String> old = strings(result.path("before_settings").get(setting)), current = strings(result.path("after_settings").get(setting));
                if (setting.equals("ExclusionPath")) NativeBridgeBuild.require(old.equals(before) && current.equals(after), "Broker path arrays disagree");
                else NativeBridgeBuild.require(new HashSet<>(old).equals(new HashSet<>(current)), "Broker changed nonpath exclusions");
            }
            NativeBridgeBuild.require(bool(result, "observed_extensions_unchanged") && bool(result, "observed_processes_unchanged"), "Broker nonpath preservation evidence missing");
            extra = verifyBrokerProof(receipt, manifestPin, result, identity);
        } else NativeBridgeBuild.require(text(result, "readback_visibility").equals("same administrative token and WMI client for before/after")
                && text(result, "namespace").equals("root\\Microsoft\\Windows\\Defender"), "Direct same-admin WMI source is missing");
        expectedInjector.verify(); receipt.verify(); manifestPin.verify(); return new Readback(route, receipt, semantic, before, after, extra);
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
