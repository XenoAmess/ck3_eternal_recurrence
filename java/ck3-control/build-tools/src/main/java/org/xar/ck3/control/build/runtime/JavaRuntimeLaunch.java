package org.xar.ck3.control.build.runtime;

import com.fasterxml.jackson.databind.JsonNode;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.TreeMap;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.ProjectStoragePolicy;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.build.runtime.JavaRuntimePackage.VerifiedPackage;
import org.xar.ck3.control.build.runtime.JavaRuntimePackageModel.Request;

/** Fixed Java command producer. Root retains the sole process and runtime-admission authority. */
public final class JavaRuntimeLaunch {
    private JavaRuntimeLaunch() { }

    /** Distinct finite-caller DATA; its exact request is never relabelled a startup or Saved request.
     * The accepted SERVICE must have been built with quarkus.package.main-class=finite-first-live. */
    public record FiniteFirstLiveInvocation(FileRef finiteRequest) {
        public static final String SCHEMA="xar.java-finite-first-live-invocation/v1";
        public FiniteFirstLiveInvocation {
            Objects.requireNonNull(finiteRequest);JavaRuntimePackageModel.absolute(finiteRequest.path());
            invocationText(finiteRequest.path());
            if(finiteRequest.bytes()<1||finiteRequest.bytes()>16384||!finiteRequest.sha256().matches("[0-9a-f]{64}"))
                throw new IllegalArgumentException("bounded exact finite caller request required");
        }
        public List<String> arguments(){return List.of(finiteRequest.path(),Long.toString(finiteRequest.bytes()),finiteRequest.sha256());}
        public byte[] encode()throws IOException {
            var mapper=ControlBuild.strictMapper();var row=mapper.createObjectNode();row.put("schema",SCHEMA);
            row.set("finite_request",mapper.valueToTree(finiteRequest));
            byte[] raw=mapper.writeValueAsBytes(row);
            if(raw.length<1||raw.length>65536)throw new IOException("bounded exact finite invocation JSON required");
            return raw;
        }
        public static FiniteFirstLiveInvocation decode(byte[] bytes)throws IOException {
            try {
                var row=invocationDocument(bytes);fields(row,Set.of("schema","finite_request"));
                if(!SCHEMA.equals(invocationText(row.get("schema"))))throw new IOException("exact finite caller invocation schema required");
                var ref=row.get("finite_request");fields(ref,Set.of("path","bytes","sha256"));
                if(!ref.get("bytes").isIntegralNumber()||!ref.get("bytes").canConvertToLong())
                    throw new IOException("exact finite request integer bytes required");
                return new FiniteFirstLiveInvocation(new FileRef(invocationText(ref.get("path")),ref.get("bytes").longValue(),invocationText(ref.get("sha256"))));
            }catch(IllegalArgumentException invalid){throw new IOException("invalid finite caller invocation",invalid);}
        }
        private static void fields(JsonNode node,Set<String> expected)throws IOException {
            if(node==null||!node.isObject())throw new IOException("exact finite invocation object required");
            var actual=new java.util.HashSet<String>();node.fieldNames().forEachRemaining(actual::add);
            if(!actual.equals(expected))throw new IOException("finite invocation missing or unknown fields");
        }
    }

    private static JsonNode invocationDocument(byte[] raw)throws IOException {
        if(raw==null||raw.length<1||raw.length>65536)throw new IOException("bounded nonempty UTF-8 invocation required");
        String text=StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT)
                .onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(raw)).toString();
        JsonNode node=ControlBuild.strictMapper().readTree(text);
        if(node==null)throw new IOException("invocation JSON value required");
        return node;
    }
    private static String invocationText(JsonNode node) {
        if(node==null||!node.isTextual())throw new IllegalArgumentException("invocation string required");
        return invocationText(node.textValue());
    }
    private static String invocationText(String value) {
        if(value==null||value.isEmpty()||value.codePointCount(0,value.length())>32768)
            throw new IllegalArgumentException("bounded nonempty invocation text required");
        for(int index=0;index<value.length();index++) {
            char current=value.charAt(index);
            if(Character.isHighSurrogate(current)) {
                if(index+1>=value.length()||!Character.isLowSurrogate(value.charAt(index+1)))throw new IllegalArgumentException("unpaired invocation surrogate");
                index++;
            }else if(Character.isLowSurrogate(current))throw new IllegalArgumentException("unpaired invocation surrogate");
        }
        return value;
    }

    /** A manifest DTO cannot mint a launch. Both preparation and consumption revalidate its importer. */
    /** DATA only. The shared caller independently owns and admits these paths. */
    public record ManagedCommandPaths(Path stdout,Path stderr,Path temporaryRoot,Path nativeScratchRoot,long memoryLimitBytes) {
        public ManagedCommandPaths {
            for(Path value:List.of(stdout,stderr,temporaryRoot,nativeScratchRoot))
                JavaRuntimePackageModel.absolute(Objects.requireNonNull(value).toString());
            if(memoryLimitBytes<=0 || stdout.equals(stderr) || stdout.getParent()==null
                    || !stdout.getParent().equals(stderr.getParent()))
                throw new IllegalArgumentException("One owned output parent, distinct logs and finite memory required");
        }
    }

    public static final class PreparedLaunch {
        private final VerifiedPackage accepted;
        private final List<String> arguments;
        private final List<String> applicationArguments;
        private final java.util.Optional<FileRef> finiteInvocationSource;
        private final Map<String, String> environment;
        private final ProjectStoragePolicy.Configuration storage;
        private final List<SharedSourceFiles.Witness> invocationInputs;
        private PreparedLaunch(VerifiedPackage accepted, List<String> arguments, Map<String, String> environment,
                ProjectStoragePolicy.Configuration storage, List<SharedSourceFiles.Witness> invocationInputs,
                List<String> applicationArguments,java.util.Optional<FileRef> finiteInvocationSource) {
            this.accepted = accepted; this.arguments = List.copyOf(arguments); this.environment = environment; this.storage = storage;
            this.invocationInputs = List.copyOf(invocationInputs);
            this.applicationArguments=List.copyOf(applicationArguments);
            this.finiteInvocationSource=Objects.requireNonNull(finiteInvocationSource);
        }
        public FileRef executable() { return accepted.manifest().request().javaHome().executable(); }
        public List<String> arguments() { return arguments; }
        public Map<String, String> environment() { return environment; }
        public FileRef packageManifest() { return accepted.manifestRef(); }

        /** No process is started here. The sole Root launcher must independently admit this Job. */
        public WindowsJobProcess.CommandSpec command(Path stdout, Path stderr, long memoryLimitBytes) throws IOException {
            verifyInvocation(); accepted.verifyCurrent(); Request request = accepted.manifest().request(); requireStorageCurrent(storage); requireScratch(request);
            logPath(request, stdout); logPath(request, stderr);
            if (stdout.equals(stderr) || memoryLimitBytes < Math.addExact(request.launch().maximumHeapBytes(), 128L << 20)
                    || memoryLimitBytes > (32L << 30)) throw new IOException("distinct fresh logs and finite whole-JVM memory above the heap required");
            accepted.verifyCurrent();
            return new WindowsJobProcess.CommandSpec(Path.of(executable().path()), arguments,
                    Path.of(request.outputRoot()), environment, stdout, stderr, memoryLimitBytes);
        }

        public void requireFiniteInputs(FileRef manifest,FileRef invocation)throws IOException {
            if(!accepted.manifestRef().equals(manifest) || finiteInvocationSource.isEmpty()
                    || !finiteInvocationSource.orElseThrow().equals(invocation))
                throw new IOException("Same actual package and finite invocation required");
            verifyCurrent();
        }

        /** Extra outer JARs must be original/private members of this actual accepted package. */
        public void requireManagedOuterRuntime(List<FileRef> extra)throws IOException {
            verifyCurrent();
            for(FileRef ref:extra) {
                boolean found=false;
                for(var output:accepted.manifest().outputFiles()) {
                    String path=output.relativePath();
                    if(!path.startsWith("quarkus-app/") || !path.endsWith(".jar")
                            || path.equals("quarkus-app/quarkus/transformed-bytecode.jar")
                            || path.equals("quarkus-app/quarkus/generated-bytecode.jar"))continue;
                    if(ref.equals(output.original()) || ref.equals(output.actual().source()))found=true;
                }
                if(!found)throw new IOException("Extra outer JAR is outside the original accepted package: "+ref.path());
                ref.verify();
            }
            verifyCurrent();
        }

        /** Retained source/native identity checks for periodic custody; full package validation stays separate. */
        public List<SharedSourceFiles.Witness> retainManagedSources()throws IOException {
            verifyCurrent();
            var pins=new java.util.LinkedHashMap<String,SharedSourceFiles.Witness>();
            var manifest=SharedSourceFiles.observe(Path.of(accepted.manifestRef().path()));
            if(!manifest.source().equals(accepted.manifestRef()))throw new IOException("Actual package manifest changed");
            pins.put(manifest.source().path(),manifest);
            var all=new java.util.ArrayList<SharedSourceFiles.Witness>(accepted.manifest().originalInputs());
            for(var output:accepted.manifest().outputFiles())all.add(output.actual());
            all.addAll(invocationInputs);
            for(var witness:all) {
                var previous=pins.putIfAbsent(witness.source().path(),witness);
                if(previous!=null && !previous.equals(witness))throw new IOException("Conflicting retained package source");
                SharedSourceFiles.assertUnchanged(witness);
            }
            verifyCurrent();return List.copyOf(pins.values());
        }

        /** The formal Root producer owns the complete managed argv/environment; no caller edits it. */
        public WindowsJobProcess.CommandSpec managedCommand(FileRef manifest,FileRef invocation,ManagedCommandPaths paths)throws IOException {
            if(!accepted.manifestRef().equals(manifest) || finiteInvocationSource.isEmpty()
                    || !finiteInvocationSource.orElseThrow().equals(invocation))
                throw new IOException("Same actual package and finite invocation required");
            Request request=accepted.manifest().request();
            if(!paths.temporaryRoot().equals(Path.of(request.launch().temporaryRoot()))
                    || !paths.nativeScratchRoot().equals(Path.of(request.launch().nativeScratchRoot())))
                throw new IOException("Managed scratch paths differ from the accepted package");
            var original=command(paths.stdout(),paths.stderr(),paths.memoryLimitBytes());
            List<String> managed=managedArguments(request,applicationArguments,paths);
            var actualEnvironment=managedEnvironment(environment);
            verifyCurrent();
            return new WindowsJobProcess.CommandSpec(original.executable(),managed,original.cwd(),
                    Map.copyOf(actualEnvironment),original.stdout(),original.stderr(),original.memoryLimitBytes());
        }

        /** Recheck immediately before Root resumes the owned process; no ACK confers host readiness. */
        private void verifyInvocation() throws IOException { for (var input : invocationInputs) SharedSourceFiles.assertUnchanged(input); }
        public void verifyCurrent() throws IOException { verifyInvocation(); accepted.verifyCurrent(); requireStorageCurrent(storage); requireScratch(accepted.manifest().request()); }
    }

    public static PreparedLaunch prepare(VerifiedPackage accepted) throws IOException {
        Objects.requireNonNull(accepted); accepted.verifyCurrent();
        ProjectStoragePolicy.Configuration storage = ProjectStoragePolicy.currentConfiguration();
        Request request = accepted.manifest().request(); requireScratch(request);
        List<String> arguments = fixedArguments(request);
        Map<String, String> environment = sanitizedEnvironment(request, System.getenv(), storage);
        requireStorageCurrent(storage);
        accepted.verifyCurrent(); return new PreparedLaunch(accepted, arguments, environment, storage, List.of(),List.of(),java.util.Optional.empty());
    }

    /** One source roster consumed by the launcher and the actual SDK SourceIndex/default helper. */
    public static List<Class<?>> requiredInvocationSources() {
        return List.of(JavaRuntimeLaunch.class, RootStartupInvocation.class);
    }

    private static List<SharedSourceFiles.Witness> requireInvocationDeployment(VerifiedPackage accepted) throws IOException {
        var retained = new java.util.ArrayList<SharedSourceFiles.Witness>();
        for (Class<?> type : requiredInvocationSources()) {
            if (type.getClassLoader() != JavaRuntimeLaunch.class.getClassLoader()
                    || type.getProtectionDomain() == null || type.getProtectionDomain().getCodeSource() == null)
                throw new IOException("Root invocation class has no identical actual launcher class-loader/source: " + type.getName());
            var location = type.getProtectionDomain().getCodeSource().getLocation();
            if (location == null || !"file".equals(location.getProtocol())) throw new IOException("actual file JAR CodeSource required");
            final Path current;
            try { current = Path.of(location.toURI()).toRealPath(); }
            catch (java.net.URISyntaxException invalid) { throw new IOException("invalid actual invocation CodeSource", invalid); }
            var witness = SharedSourceFiles.observe(current);
            var providers = accepted.manifest().layout().applicationClasses().stream()
                    .filter(row -> row.binaryName().equals(type.getName())
                            && row.kind() == JavaRuntimePackageModel.ProviderKind.ORIGINAL).toList();
            if (providers.size() != 1) throw new IOException("actual imported package requires one original invocation provider: " + type.getName());
            String packaged = "quarkus-app/" + providers.getFirst().relativeJar();
            var files = accepted.manifest().outputFiles().stream().filter(row -> row.relativePath().equals(packaged)).toList();
            if (files.size() != 1) throw new IOException("actual invocation package JAR missing");
            var output = files.getFirst(); var actual = witness.source();
            boolean privateCopy = current.equals(Path.of(output.actual().source().path()).toRealPath())
                    && actual.equals(output.actual().source());
            boolean original = accepted.manifest().originalInputs().stream().anyMatch(input -> input.source().equals(actual));
            // SDK/Maven source JAR and private package copy have separate exact refs. Equal names never join them.
            if ((!privateCopy && !original) || actual.bytes() != output.original().bytes()
                    || !actual.sha256().equals(output.original().sha256()))
                throw new IOException("actual invocation class is outside the accepted original/private package closure: " + type.getName());
            output.original().verify(); output.actual().source().verify();
            try (var jar = new java.util.jar.JarFile(current.toFile(), false)) {
                if (jar.getJarEntry(type.getName().replace('.', '/') + ".class") == null)
                    throw new IOException("actual invocation CodeSource omitted its loaded class");
            }
            SharedSourceFiles.assertUnchanged(witness); retained.add(witness);
        }
        return List.copyOf(retained);
    }

    /** Explicit real Root routes. Distinct typed startup/Saved and finite inputs reach their build-selected Main. */
    public static PreparedLaunch prepareRoot(VerifiedPackage accepted, FileRef actualInvocation) throws IOException {
        Objects.requireNonNull(actualInvocation);
        var source = SharedSourceFiles.observe(Path.of(actualInvocation.path()));
        if (!source.source().equals(actualInvocation)) throw new IOException("Root invocation differs from its exact source");
        if (actualInvocation.bytes() < 1 || actualInvocation.bytes() > 65536) throw new IOException("bounded Root invocation required");
        byte[] raw=Files.readAllBytes(Path.of(actualInvocation.path()));
        var document=invocationDocument(raw);
        if(document.isObject()&&document.path("schema").isTextual()
                &&FiniteFirstLiveInvocation.SCHEMA.equals(document.get("schema").textValue()))
            return prepareFiniteFirstLive(accepted,source,FiniteFirstLiveInvocation.decode(raw));
        var invocation = RootStartupInvocation.decode(raw);
        var ordinary = prepare(accepted);
        for (String required : List.of("org.xar.ck3.control.service.root.RootQuarkusEntrypoint",
                "org.xar.ck3.control.service.root.RootApplicationMain",
                "org.xar.ck3.control.service.root.RootSavedNativeCoordinator")) {
            if (accepted.manifest().layout().applicationClasses().stream().noneMatch(row -> row.binaryName().equals(required)))
                throw new IOException("actual imported package lacks its explicit Root entry consumer: " + required);
        }
        var held = new java.util.ArrayList<SharedSourceFiles.Witness>(); held.add(source);
        held.addAll(requireInvocationDeployment(accepted));
        for (FileRef ref : invocation.sources()) {
            ref.verify(); var witness = SharedSourceFiles.observe(Path.of(ref.path()));
            if (!witness.source().equals(ref)) throw new IOException("Root startup input changed during preparation");
            held.add(witness);
        }
        var args = new java.util.ArrayList<>(ordinary.arguments); args.addAll(invocation.arguments());
        for (var witness : held) SharedSourceFiles.assertUnchanged(witness);
        ordinary.verifyCurrent();
        return new PreparedLaunch(accepted, args, ordinary.environment, ordinary.storage, held,invocation.arguments(),java.util.Optional.empty());
    }

    private static PreparedLaunch prepareFiniteFirstLive(VerifiedPackage accepted,SharedSourceFiles.Witness source,
            FiniteFirstLiveInvocation invocation)throws IOException {
        var ordinary=prepare(accepted);
        for(String required:List.of("org.xar.ck3.control.service.root.RootFiniteFirstLiveMain",
                "org.xar.ck3.control.service.root.RootFiniteFirstLiveRequest",
                "org.xar.ck3.control.service.root.RootFiniteFirstLiveWork"))
            if(accepted.manifest().layout().applicationClasses().stream().noneMatch(row->row.binaryName().equals(required)))
                throw new IOException("actual imported package lacks its finite caller: "+required);
        var held=new java.util.ArrayList<SharedSourceFiles.Witness>();held.add(source);
        held.addAll(requireInvocationDeployment(accepted));
        var ref=invocation.finiteRequest();ref.verify();var original=SharedSourceFiles.observe(Path.of(ref.path()));
        if(!original.source().equals(ref))throw new IOException("finite caller input differs from its exact original");
        held.add(original);var args=new java.util.ArrayList<>(ordinary.arguments);args.addAll(invocation.arguments());
        for(var witness:held)SharedSourceFiles.assertUnchanged(witness);ordinary.verifyCurrent();
        return new PreparedLaunch(accepted,args,ordinary.environment,ordinary.storage,held,invocation.arguments(),java.util.Optional.of(source.source()));
    }

    static List<String> fixedArguments(Request request) { return fixedArguments(request,List.of()); }

    private static List<String> fixedArguments(Request request,List<String> ownedDiagnostics) {
        Objects.requireNonNull(request); var launch=request.launch();Path root=Path.of(request.outputRoot());
        var result=new java.util.ArrayList<String>(List.of("-Xms"+launch.minimumHeapBytes(),"-Xmx"+launch.maximumHeapBytes(),
                "-Dfile.encoding=UTF-8","-Djava.io.tmpdir="+launch.temporaryRoot(),
                "-Djna.tmpdir="+launch.nativeScratchRoot(),"-Djna.nosys=true",
                "-Dquarkus.http.host=127.0.0.1","-Dquarkus.http.port="+launch.httpPort(),
                "-Dquarkus.log.console.stderr=true","-Dquarkus.banner.enabled=false",
                "-Dxar.application.mode="+launch.mode().name(),
                "-Dxar.application.configuration="+root.resolve(JavaRuntimePackage.HOST_CONFIGURATION_FILE),
                "-Dxar.runtime.package.manifest="+root.resolve(JavaRuntimePackage.MANIFEST_FILE)));
        result.addAll(ownedDiagnostics);
        result.add("-jar");result.add(root.resolve("quarkus-app/quarkus-run.jar").toString());
        return List.copyOf(result);
    }

    static Map<String,String> managedEnvironment(Map<String,String> prepared) {
        var result=new java.util.TreeMap<String,String>(String.CASE_INSENSITIVE_ORDER);
        result.putAll(prepared);result.put("PYTHONDONTWRITEBYTECODE","1");return Map.copyOf(result);
    }

    static List<String> managedArguments(Request request,List<String> applicationArguments,ManagedCommandPaths paths)throws IOException {
        if(applicationArguments.size()!=3)throw new IOException("Finite original exact-three arguments required");
        if(!paths.temporaryRoot().equals(Path.of(request.launch().temporaryRoot()))
                || !paths.nativeScratchRoot().equals(Path.of(request.launch().nativeScratchRoot())))
            throw new IOException("Managed scratch paths differ from the accepted package");
        Path out=paths.stdout().getParent();
        var result=new java.util.ArrayList<>(fixedArguments(request,List.of(
                "-XX:ErrorFile="+out.resolve("hs_err_pid%p.log"),
                "-XX:ReplayDataFile="+out.resolve("replay_pid%p.log"),"-XX:HeapDumpPath="+out)));
        result.addAll(applicationArguments);return List.copyOf(result);
    }

    /** Rebuild the Windows environment rather than trying to enumerate every possible injection key. */
    static Map<String, String> sanitizedEnvironment(Request request, Map<String, String> inherited,
            ProjectStoragePolicy.Configuration storage) throws IOException {
        Objects.requireNonNull(request); Objects.requireNonNull(inherited); Objects.requireNonNull(storage);
        Map<String, String> actual = new TreeMap<>(String.CASE_INSENSITIVE_ORDER);
        for (Map.Entry<String, String> entry : inherited.entrySet()) {
            String key = entry.getKey(), value = entry.getValue();
            if (key == null || value == null || key.indexOf('\0') >= 0 || value.indexOf('\0') >= 0
                    || actual.putIfAbsent(key, value) != null) throw new IOException("unambiguous Windows environment required");
        }
        String raw = actual.get("SystemRoot");
        if (raw == null || raw.isBlank()) throw new IOException("current Windows SystemRoot is unavailable");
        final Path systemRoot;
        try { JavaRuntimePackageModel.absolute(raw); systemRoot = Path.of(raw); }
        catch (IllegalArgumentException invalid) { throw new IOException("current Windows SystemRoot must be normalized and absolute", invalid); }
        String windir = actual.get("WINDIR");
        try {
            if (windir != null && !Path.of(windir).equals(systemRoot)) throw new IOException("conflicting Windows root environment");
        } catch (IllegalArgumentException invalid) { throw new IOException("invalid Windows root environment", invalid); }
        Map<String, String> result = new TreeMap<>(String.CASE_INSENSITIVE_ORDER);
        result.put("SystemRoot", systemRoot.toString()); result.put("WINDIR", systemRoot.toString());
        result.put("JAVA_HOME", request.javaHome().root());
        result.put("PATH", Path.of(request.javaHome().root()).resolve("bin") + ";" + systemRoot.resolve("System32") + ";" + systemRoot);
        result.put("TEMP", request.launch().temporaryRoot()); result.put("TMP", request.launch().temporaryRoot());
        // The child runs outside the checkout. Carry the parsed policy, including Git-local fallback,
        // rather than dropping it or copying an unvalidated inherited value.
        result.put(ProjectStoragePolicy.FORBID_SYSTEM_VOLUME_BULK, Boolean.toString(storage.forbidSystemVolumeBulk()));
        if (storage.forbidSystemVolumeBulk() && storage.preferredBulkRoot().isPresent()) {
            result.put(ProjectStoragePolicy.PROJECT_STORAGE_ROOT, storage.preferredBulkRoot().orElseThrow().toString());
        }
        return Map.copyOf(result);
    }

    private static void requireScratch(Request request) throws IOException {
        ProjectStoragePolicy.requireBulkOutput(Path.of(request.outputRoot()));
        for (Path directory : List.of(Path.of(request.launch().temporaryRoot()), Path.of(request.launch().nativeScratchRoot()))) {
            ProjectStoragePolicy.requireBulkOutput(directory);
            SharedSourceFiles.plainAncestors(directory);
            if (!Files.isDirectory(directory, LinkOption.NOFOLLOW_LINKS)) throw new IOException("Root must prepare the admitted plain JVM scratch directories");
        }
    }

    private static void logPath(Request request, Path path) throws IOException {
        Objects.requireNonNull(path); JavaRuntimePackageModel.absolute(path.toString());
        ProjectStoragePolicy.requireBulkOutput(path); SharedSourceFiles.plainAncestors(path);
        if (path.getParent() == null || !Files.isDirectory(path.getParent(), LinkOption.NOFOLLOW_LINKS)
                || Files.exists(path, LinkOption.NOFOLLOW_LINKS)) throw new IOException("Root must provide a fresh log in an admitted existing directory");
        for (String protectedRoot : List.of(request.outputRoot(), request.javaHome().root(), request.nativeInputs().sourceRoot()))
            if (path.startsWith(Path.of(protectedRoot))) throw new IOException("JVM log cannot modify an immutable package or input root");
    }

    private static void requireStorageCurrent(ProjectStoragePolicy.Configuration expected) throws IOException {
        if (!expected.equals(ProjectStoragePolicy.currentConfiguration())) {
            throw new IOException("Prepared Java launch storage policy changed; prepare a new exact command");
        }
    }
}
