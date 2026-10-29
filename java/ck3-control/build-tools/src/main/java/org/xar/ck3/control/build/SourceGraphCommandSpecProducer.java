package org.xar.ck3.control.build;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.List;
import java.util.HashSet;
import java.util.Locale;
import java.util.Set;
import java.util.Map;
import java.util.Objects;
import java.util.ArrayList;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HexFormat;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.annotation.JsonInclude;
import org.xar.ck3.control.build.ControlBuild.FileRef;

/** Typed mechanical spec generation only. The standing and SharedOwnedCommand still authorize execution. */
public final class SourceGraphCommandSpecProducer {
    private SourceGraphCommandSpecProducer() { }

    public record BindingIntent(String machineId, FileRef launcherSourceRef, FileRef standingRef,
            FileRef deliveryRef, SharedOwnedCommandBinding.AuthorityExpectation standingExpectation,
            SharedOwnedCommandBinding.AuthorityExpectation deliveryExpectation) { }

    /** Issuer metadata supplies temporary roots, runtime and the outer Java executable. */
    public record EntryIntent(BindingIntent binding, String owner, String coordinator, String slotId,
            String borrowedSlotId, String runId, FileRef executable, List<String> arguments, String cwd,
            Map<String,String> environment, List<FileRef> inputs, long timeoutSeconds, long memoryLimitBytes,
            WindowsJobProcess.RootExitDrainPolicy rootExitDrainPolicy,
            @JsonInclude(JsonInclude.Include.NON_NULL) SharedOwnedCommand.JavaInvocation javaInvocation) {
        public EntryIntent {
            Objects.requireNonNull(binding); arguments=List.copyOf(arguments);
            environment=Map.copyOf(environment); inputs=List.copyOf(inputs);
            validateInputs(executable,inputs);
        }
        public EntryIntent(BindingIntent binding,String owner,String coordinator,String slotId,String borrowedSlotId,String runId,
                FileRef executable,List<String> arguments,String cwd,Map<String,String> environment,List<FileRef> inputs,
                long timeoutSeconds,long memoryLimitBytes,WindowsJobProcess.RootExitDrainPolicy policy) {
            this(binding,owner,coordinator,slotId,borrowedSlotId,runId,executable,arguments,cwd,environment,inputs,
                    timeoutSeconds,memoryLimitBytes,policy,null);
        }
    }

    public record MsvcEntryIntent(EntryIntent command,MsvcAuxiliaryPolicy.ExecutionBinding msvcAuxiliaryBinding) {
        public MsvcEntryIntent {
            Objects.requireNonNull(command); Objects.requireNonNull(msvcAuxiliaryBinding);
            if(command.javaInvocation()!=null)
                throw new IllegalArgumentException("MSVC v3 and UTF8 Java-child v4 are distinct explicit routes");
        }
    }

    public record Invocation(String schema, String machineId, FileRef executable, List<String> arguments,
            String cwd, Map<String,String> environment, List<String> unsetEnvironment, FileRef bindingRef, FileRef specRef,
            @JsonInclude(JsonInclude.Include.NON_NULL) SharedOwnedCommand.JavaInvocation javaInvocation) {
        public Invocation {
            if (!(javaInvocation==null?"xar.shared-owned-command-invocation/v2":"xar.shared-owned-command-invocation/v4").equals(schema))
                throw new IllegalArgumentException("Closed whole-entry invocation schema required");
            arguments=List.copyOf(arguments); environment=Map.copyOf(environment); unsetEnvironment=List.copyOf(unsetEnvironment);
            Objects.requireNonNull(executable); Objects.requireNonNull(bindingRef); Objects.requireNonNull(specRef);
        }
        public Invocation(String schema,String machineId,FileRef executable,List<String> arguments,String cwd,
                Map<String,String> environment,List<String> unsetEnvironment,FileRef bindingRef,FileRef specRef) {
            this(schema,machineId,executable,arguments,cwd,environment,unsetEnvironment,bindingRef,specRef,null);
        }
    }
    public enum RootProvider { ROOT_LAUNCHER, ROOT_PREPARER, NATIVE_VERIFIER, TOOLS }
    public record RootProviderBinding(RootProvider role,FileRef codeSource) {
        public RootProviderBinding { Objects.requireNonNull(role);Objects.requireNonNull(codeSource); }
    }
    public record RootClasspath(List<FileRef> roots,List<FileRef> effective) {
        public RootClasspath { roots=List.copyOf(roots);effective=List.copyOf(effective); }
    }
    /** This exact external authorization is read, never minted by the publisher. */
    public record RootRuntimeAuthorization(String schema,String status,String machineId,String owner,String reviewAtUtc,
            FileRef standingRef,FileRef deliveryRef,FileRef packageManifest,FileRef finiteInvocation,
            List<FileRef> completeExtraRuntime,RootClasspath outerClasspath,List<RootProviderBinding> providerBindings) {
        public RootRuntimeAuthorization {
            if(!"xar.root-prepared-launch-runtime-authorization/v1".equals(schema)
                    || !"ROOT_FINITE_SHARED_RUNTIME_AUTHORIZED".equals(status))
                throw new IllegalArgumentException("Explicit Root runtime authorization required");
            completeExtraRuntime=List.copyOf(completeExtraRuntime);providerBindings=List.copyOf(providerBindings);
            Objects.requireNonNull(outerClasspath);
        }
    }
    public record RootEntryIntent(EntryIntent command,SharedOwnedCommand.PreparedRootInputs preparedRoot) {
        public RootEntryIntent { Objects.requireNonNull(command);Objects.requireNonNull(preparedRoot); }
    }
    /** Contains no self-reference or physical argv. LaunchData is derived after this original exists. */
    public record RootInvocation(String schema,String machineId,FileRef bindingRef,FileRef specRef,
            SharedOwnedCommand.PreparedRootInputs preparedRoot) {
        public RootInvocation {
            if(!"xar.shared-owned-root-invocation/v1".equals(schema))
                throw new IllegalArgumentException("Distinct Root invocation schema required");
            Objects.requireNonNull(machineId);Objects.requireNonNull(bindingRef);Objects.requireNonNull(specRef);Objects.requireNonNull(preparedRoot);
        }
    }
    public record RootLaunchData(String schema,FileRef invocationRef,FileRef executable,List<String> arguments,
            String cwd,Map<String,String> environment,List<String> unsetEnvironment) {
        public RootLaunchData {
            if(!"xar.shared-owned-root-launch-data/v1".equals(schema))throw new IllegalArgumentException("Exact Root launch DATA required");
            arguments=List.copyOf(arguments);environment=Map.copyOf(environment);unsetEnvironment=List.copyOf(unsetEnvironment);
        }
    }
    private static void rootKeys(JsonNode value,Set<String> keys)throws IOException {
        if(value==null || !value.isObject() || value.size()!=keys.size())throw new IOException("Exact Root fields required");
        for(var field:value.properties())if(!keys.contains(field.getKey()))throw new IOException("Unknown Root field: "+field.getKey());
    }
    private static void rootRefs(JsonNode values)throws IOException {
        if(values==null || !values.isArray() || values.isEmpty() || values.size()>2048)throw new IOException("Bounded Root runtime refs required");
        for(JsonNode value:values)SharedOwnedCommand.strictFileRef(value);
    }
    static RootRuntimeAuthorization decodeRootAuthorization(JsonNode wire)throws IOException {
        rootKeys(wire,Set.of("schema","status","machine_id","owner","review_at_utc","standing_ref","delivery_ref",
                "package_manifest","finite_invocation","complete_extra_runtime","outer_classpath","provider_bindings"));
        for(String field:List.of("schema","status","machine_id","owner","review_at_utc"))text(wire,field);
        for(String field:List.of("standing_ref","delivery_ref","package_manifest","finite_invocation"))
            SharedOwnedCommand.strictFileRef(wire.get(field));
        var cp=wire.get("outer_classpath");rootKeys(cp,Set.of("roots","effective"));
        rootRefs(cp.get("roots"));rootRefs(cp.get("effective"));
        var extra=wire.get("complete_extra_runtime");
        if(extra==null || !extra.isArray() || extra.size()>2048)throw new IOException("Bounded explicit extra runtime required");
        for(JsonNode ref:extra)SharedOwnedCommand.strictFileRef(ref);
        var providers=wire.get("provider_bindings");
        if(providers==null || !providers.isArray() || providers.size()!=RootProvider.values().length)
            throw new IOException("All fixed Root providers required");
        for(JsonNode provider:providers) {
            rootKeys(provider,Set.of("role","code_source"));SharedOwnedCommand.strictFileRef(provider.get("code_source"));
            try {RootProvider.valueOf(text(provider,"role"));}catch(IllegalArgumentException invalid){throw new IOException("Unknown Root provider",invalid);}
        }
        var value=ControlBuild.strictMapper().treeToValue(wire,RootRuntimeAuthorization.class);
        var roles=new HashSet<RootProvider>();var paths=new HashSet<Path>();
        var effective=new HashSet<>(value.outerClasspath().effective());
        for(var provider:value.providerBindings())if(!roles.add(provider.role()) || !effective.contains(provider.codeSource()))
            throw new IOException("Unique actual fixed Root providers inside explicit effective runtime required");
        for(var pin:value.completeExtraRuntime())if(!paths.add(Path.of(pin.path()).toAbsolutePath().normalize()))
            throw new IOException("Duplicate Root extra runtime path");
        return value;
    }
    static RootInvocation decodeRootInvocation(JsonNode wire)throws IOException {
        rootKeys(wire,Set.of("schema","machine_id","binding_ref","spec_ref","prepared_root"));
        text(wire,"schema");text(wire,"machine_id");
        SharedOwnedCommand.strictFileRef(wire.get("binding_ref"));SharedOwnedCommand.strictFileRef(wire.get("spec_ref"));
        SharedOwnedCommand.decodePreparedRoot(wire.get("prepared_root"));
        return ControlBuild.strictMapper().treeToValue(wire,RootInvocation.class);
    }
    public static RootRuntimeAuthorization readRootAuthorization(RootInvocation invocation)throws Exception {
        var binding=SharedOwnedCommandBinding.read(invocation.bindingRef());
        var request=SharedOwnedCommand.parseRequest(exactJson(invocation.specRef(),1<<20));
        FileRef ref=invocation.preparedRoot().rootRuntimeAuthorizationRef();
        JsonNode wire=exactJson(ref,1<<20);
        rootKeys(wire,Set.of("schema","status","machine_id","owner","review_at_utc","standing_ref","delivery_ref",
                "package_manifest","finite_invocation","complete_extra_runtime","outer_classpath","provider_bindings"));
        for(String field:List.of("schema","status","machine_id","owner","review_at_utc"))text(wire,field);
        for(String field:List.of("standing_ref","delivery_ref","package_manifest","finite_invocation"))
            SharedOwnedCommand.strictFileRef(wire.get(field));
        var cpWire=wire.get("outer_classpath");rootKeys(cpWire,Set.of("roots","effective"));
        rootRefs(cpWire.get("roots"));rootRefs(cpWire.get("effective"));
        JsonNode extra=wire.get("complete_extra_runtime");
        if(extra==null || !extra.isArray() || extra.size()>2048)throw new IOException("Bounded explicit extra runtime required");
        for(JsonNode item:extra)SharedOwnedCommand.strictFileRef(item);
        var providers=wire.get("provider_bindings");
        if(providers==null || !providers.isArray() || providers.size()!=RootProvider.values().length)
            throw new IOException("All fixed Root provider roles required");
        for(JsonNode provider:providers) {
            rootKeys(provider,Set.of("role","code_source"));SharedOwnedCommand.strictFileRef(provider.get("code_source"));
            try { RootProvider.valueOf(text(provider,"role")); }
            catch(IllegalArgumentException invalid) { throw new IOException("Unknown fixed Root provider",invalid); }
        }
        SharedOwnedCommandBinding.verifyAuthority(wire,new SharedOwnedCommandBinding.AuthorityExpectation(
                "xar.root-prepared-launch-runtime-authorization/v1","ROOT_FINITE_SHARED_RUNTIME_AUTHORIZED"),binding.machineId());
        RootRuntimeAuthorization value=decodeRootAuthorization(wire);
        var standing=exactJson(binding.standingRef(),1<<20);
        var deadline=java.time.Instant.parse(text(standing,"review_at_utc"));var review=java.time.Instant.parse(value.reviewAtUtc());
        if(!value.machineId().equals(invocation.machineId()) || !value.owner().equals(request.owner())
                || !value.standingRef().equals(binding.standingRef()) || !value.deliveryRef().equals(binding.deliveryRef())
                || !value.packageManifest().equals(invocation.preparedRoot().packageManifest())
                || !value.finiteInvocation().equals(invocation.preparedRoot().invocation())
                || !java.time.Instant.now().isBefore(review) || review.isAfter(deadline))
            throw new IOException("Root runtime authority differs from the exact binding/owner/package/finite window");
        var runtime=declaredRuntime(standing,binding);
        var cp=value.outerClasspath();
        if(cp.roots().size()<runtime.size() || !cp.roots().subList(0,runtime.size()).equals(runtime))
            throw new IOException("Standing six-file runtime must retain its original classpath positions");
        var effective=rootEffectiveClasspath(cp.roots());
        if(!effective.equals(cp.effective()))throw new IOException("Root manifest-effective classpath differs");
        var allowed=new java.util.LinkedHashSet<FileRef>(runtime);
        for(FileRef pin:value.completeExtraRuntime())if(!allowed.add(pin))throw new IOException("Duplicate or standing-aliased extra runtime");
        if(!new HashSet<>(effective).equals(allowed))throw new IOException("Effective Root runtime is outside the explicit authorization");
        var roles=new HashSet<RootProvider>();
        for(var provider:value.providerBindings()) {
            if(!roles.add(provider.role()) || !allowed.contains(provider.codeSource()))
                throw new IOException("Unique fixed provider inside authorized runtime required");
        }
        for(FileRef pin:allowed)pin.verify();ref.verify();return value;
    }
    static List<FileRef> rootEffectiveClasspath(List<FileRef> roots)throws IOException {
        var result=new java.util.LinkedHashMap<String,FileRef>();var rootPaths=new HashSet<Path>();
        for(FileRef root:roots) {
            if(!rootPaths.add(Path.of(root.path()).toAbsolutePath().normalize()))throw new IOException("Duplicate Root classpath root");
            root.verify();var captured=CiBootstrap.JavaUtf8Invocation.captureClasspath(Path.of(root.path()));
            if(!(captured instanceof CiBootstrap.JavaUtf8Invocation.JarClasspath jar))
                throw new IOException("Root outer currently requires exact JAR roots");
            for(var item:jar.manifestClasspath()) {
                if(!(item instanceof CiBootstrap.JavaUtf8Invocation.FileClasspath file))
                    throw new IOException("Root manifest directories need separate explicit qualification");
                var pin=file.file();var exact=new FileRef(pin.path(),pin.bytes(),pin.sha256());
                FileRef previous=result.putIfAbsent(exact.path(),exact);
                if(previous!=null && !previous.equals(exact))throw new IOException("Manifest classpath source alias");
            }
        }
        return List.copyOf(result.values());
    }
    public static void requireRootProvider(RootRuntimeAuthorization authorization,RootProvider role,Class<?> type)throws Exception {
        if(type.getClassLoader()!=SourceGraphCommandSpecProducer.class.getClassLoader()
                || type.getProtectionDomain()==null || type.getProtectionDomain().getCodeSource()==null)
            throw new IOException("Actual fixed Root provider loader/source required");
        var location=type.getProtectionDomain().getCodeSource().getLocation();
        if(!"file".equals(location.getProtocol()))throw new IOException("Actual file JAR provider required");
        Path path=Path.of(location.toURI()).toRealPath();
        FileRef actual=FileRef.measure(path);RootProviderBinding found=null;
        for(var provider:authorization.providerBindings())if(provider.role()==role)found=provider;
        if(found==null || !actual.equals(found.codeSource()))throw new IOException("Actual fixed Root provider differs: "+role);
        try(var jar=new java.util.jar.JarFile(path.toFile(),false)) {
            if(jar.getJarEntry(type.getName().replace('.','/')+".class")==null)throw new IOException("Loaded Root class omitted by its actual JAR");
        }
        actual.verify();
    }
    /** The actual outer JVM must consume the exact admitted root order, including manifest expansion. */
    public static void requireRootOuterRuntime(RootRuntimeAuthorization authorization)throws IOException {
        String raw=System.getProperty("java.class.path");
        if(raw==null)throw new IOException("Actual outer classpath unavailable");
        var actual=new ArrayList<Path>();
        for(String item:raw.split(java.util.regex.Pattern.quote(java.io.File.pathSeparator),-1)) {
            if(item.isEmpty())throw new IOException("Implicit current-directory Root classpath rejected");
            actual.add(Path.of(item).toAbsolutePath().normalize());
        }
        var expected=authorization.outerClasspath().roots().stream().map(pin->Path.of(pin.path()).toAbsolutePath().normalize()).toList();
        if(!actual.equals(expected) || !rootEffectiveClasspath(authorization.outerClasspath().roots()).equals(authorization.outerClasspath().effective()))
            throw new IOException("Actual Root outer classpath differs from explicit runtime authorization");
    }
    private record RootEntryWire(LegacyEntryIntent command,SharedOwnedCommand.PreparedRootInputs preparedRoot) { }
    public static RootEntryIntent readRootEntryIntent(FileRef source)throws IOException {
        JsonNode wire=exactJson(source,1<<20);rootKeys(wire,Set.of("command","prepared_root"));
        SharedOwnedCommand.decodePreparedRoot(wire.get("prepared_root"));
        var command=wire.get("command");
        rootKeys(command,Set.of("binding","owner","coordinator","slot_id","borrowed_slot_id","run_id","executable",
                "arguments","cwd","environment","inputs","timeout_seconds","memory_limit_bytes","root_exit_drain_policy"));
        SharedOwnedCommand.strictFileRef(command.get("executable"));rootRefs(command.get("inputs"));
        var bound=command.get("binding");
        rootKeys(bound,Set.of("machine_id","launcher_source_ref","standing_ref","delivery_ref","standing_expectation","delivery_expectation"));
        for(String name:List.of("launcher_source_ref","standing_ref","delivery_ref"))SharedOwnedCommand.strictFileRef(bound.get(name));
        var value=ControlBuild.strictMapper().treeToValue(wire,RootEntryWire.class);
        return new RootEntryIntent(value.command().current(),value.preparedRoot());
    }
    public static RootInvocation readRootInvocation(FileRef exactRef)throws Exception {
        JsonNode wire=exactJson(exactRef,65536);rootKeys(wire,Set.of("schema","machine_id","binding_ref","spec_ref","prepared_root"));
        text(wire,"schema");text(wire,"machine_id");
        SharedOwnedCommand.strictFileRef(wire.get("binding_ref"));SharedOwnedCommand.strictFileRef(wire.get("spec_ref"));
        SharedOwnedCommand.decodePreparedRoot(wire.get("prepared_root"));
        var value=decodeRootInvocation(wire);
        var binding=SharedOwnedCommandBinding.read(value.bindingRef());
        var spec=exactJson(value.specRef(),1<<20);var request=SharedOwnedCommand.parseRequest(spec);
        if(!"xar.shared-owned-command-spec/v5".equals(request.schema())
                || !value.machineId().equals(binding.machineId())
                || !value.preparedRoot().equals(SharedOwnedCommand.decodePreparedRoot(spec.get("prepared_root"))))
            throw new IOException("Distinct Root spec/input binding required");
        SharedOwnedCommand.validateStanding(request,binding,exactJson(binding.standingRef(),1<<20));
        var authority=readRootAuthorization(value);
        for(Class<?> type:List.of(SourceGraphCommandSpecProducer.class,SharedOwnedCommand.class,SharedOwnedCommandBinding.class,
                ControlBuild.class,org.xar.ck3.control.build.runtime.JavaRuntimeLaunch.class))
            requireRootProvider(authority,RootProvider.TOOLS,type);
        exactRef.verify();return value;
    }
    public static RootLaunchData rootLaunchData(FileRef actualInvocation)throws Exception {
        var invocation=readRootInvocation(actualInvocation);var authority=readRootAuthorization(invocation);
        var binding=SharedOwnedCommandBinding.read(invocation.bindingRef());var standing=exactJson(binding.standingRef(),1<<20);
        var request=SharedOwnedCommand.parseRequest(exactJson(invocation.specRef(),1<<20));
        var legacy=invocation(binding,request,standing,invocation.bindingRef(),invocation.specRef());
        String temporary=binding.nativeTemporaryRoot().toString();
        var arguments=List.of("-Xms32m","-Xmx128m","-XX:+ExitOnOutOfMemoryError",
                "-Djava.io.tmpdir="+temporary,"-Djna.tmpdir="+temporary,"-cp",
                String.join(";",authority.outerClasspath().roots().stream().map(FileRef::path).toList()),
                "org.xar.ck3.control.service.root.RootRuntimeLaunchCommand","run-shared",
                actualInvocation.path(),Long.toString(actualInvocation.bytes()),actualInvocation.sha256());
        SharedOwnedCommand.requireLegacyAsciiJava(legacy.executable(),arguments);
        var environment=new java.util.TreeMap<String,String>(String.CASE_INSENSITIVE_ORDER);
        environment.put("TEMP",temporary);environment.put("TMP",temporary);
        var storage=ProjectStoragePolicy.currentConfiguration();
        environment.put(ProjectStoragePolicy.FORBID_SYSTEM_VOLUME_BULK,Boolean.toString(storage.forbidSystemVolumeBulk()));
        if(storage.forbidSystemVolumeBulk() && storage.preferredBulkRoot().isPresent())
            environment.put(ProjectStoragePolicy.PROJECT_STORAGE_ROOT,storage.preferredBulkRoot().orElseThrow().toString());
        return new RootLaunchData("xar.shared-owned-root-launch-data/v1",actualInvocation,legacy.executable(),arguments,
                legacy.cwd(),Map.copyOf(environment),legacy.unsetEnvironment());
    }
    public static RootLaunchData publishRootInvocation(Path bindingDestination,Path specDestination,Path invocationDestination,
            RootEntryIntent root,org.xar.ck3.control.build.runtime.JavaRuntimeLaunch.PreparedLaunch prepared)throws Exception {
        var entry=root.command();var input=root.preparedRoot();
        if(entry.javaInvocation()!=null || !entry.arguments().isEmpty() || !entry.environment().isEmpty())
            throw new IOException("Root prepared route cannot carry a second argv/environment/engine");
        requireExplicitInput(input.packageManifest(),entry.inputs());requireExplicitInput(input.invocation(),entry.inputs());
        requireExplicitInput(input.rootRuntimeAuthorizationRef(),entry.inputs());
        prepared.requireFiniteInputs(input.packageManifest(),input.invocation());
        Path bindingPath=newTarget(bindingDestination),specPath=newTarget(specDestination),invocationPath=newTarget(invocationDestination);
        if(Set.of(bindingPath,specPath,invocationPath).size()!=3)throw new IOException("Distinct Root metadata paths required");
        var binding=binding(entry);var standing=exactJson(binding.standingRef(),1<<20);
        var slot=SharedOwnedCommand.findSlot(standing,entry.slotId());
        var intent=new Intent(entry.binding().machineId(),entry.owner(),entry.coordinator(),entry.slotId(),entry.borrowedSlotId(),entry.runId(),
                entry.binding().standingRef(),entry.binding().launcherSourceRef(),entry.executable(),List.of(),entry.cwd(),Map.of(),
                entry.inputs(),entry.timeoutSeconds(),entry.memoryLimitBytes(),entry.rootExitDrainPolicy());
        var mapper=ControlBuild.strictMapper();ObjectNode spec=(ObjectNode)mapper.readTree(produce(new Slot(slot.slotId(),slot.outputRoot()),intent));
        spec.put("schema","xar.shared-owned-command-spec/v5");spec.set("prepared_root",mapper.valueToTree(input));
        byte[] specBytes=mapper.writeValueAsBytes(spec),bindingBytes=mapper.writeValueAsBytes(binding.toJson());
        SharedOwnedCommand.validateStanding(SharedOwnedCommand.parseRequest(spec),binding,standing);
        var value=new RootInvocation("xar.shared-owned-root-invocation/v1",binding.machineId(),
                plannedRef(bindingPath,bindingBytes),plannedRef(specPath,specBytes),input);
        byte[] wire=mapper.writeValueAsBytes(value);
        if(specBytes.length>1<<20 || wire.length>65536)throw new IOException("Root metadata bound exceeded");
        Files.write(bindingPath,bindingBytes,StandardOpenOption.CREATE_NEW,StandardOpenOption.WRITE);
        Files.write(specPath,specBytes,StandardOpenOption.CREATE_NEW,StandardOpenOption.WRITE);
        // Authorization is real input, read before publishing the final invocation; not self-issued status.
        var authority=readRootAuthorization(value);prepared.requireManagedOuterRuntime(authority.outerClasspath().effective());
        Files.write(invocationPath,wire,StandardOpenOption.CREATE_NEW,StandardOpenOption.WRITE);
        return rootLaunchData(FileRef.measure(invocationPath));
    }

    public record Published(FileRef bindingRef, FileRef specRef, FileRef invocationRef) { }
    /** Internal result; Request and Preparation remain in the sole engine binary codec. */
    public record PreparedInvocation(Invocation invocation,SharedSourceFiles.Witness preparationRef,FileRef nativeEvidenceRef,
            CiBootstrap.JavaUtf8Invocation.Preparation preparation) { }
    private record Prepared(byte[] binding, byte[] spec, Invocation invocation) { }
    private record LegacyEntryIntent(BindingIntent binding,String owner,String coordinator,String slotId,String borrowedSlotId,String runId,
            FileRef executable,List<String> arguments,String cwd,Map<String,String> environment,List<FileRef> inputs,
            long timeoutSeconds,long memoryLimitBytes,WindowsJobProcess.RootExitDrainPolicy rootExitDrainPolicy) {
        EntryIntent current() { return new EntryIntent(binding,owner,coordinator,slotId,borrowedSlotId,runId,executable,arguments,cwd,
                environment,inputs,timeoutSeconds,memoryLimitBytes,rootExitDrainPolicy); }
    }
    private record MsvcEntryWire(LegacyEntryIntent command,MsvcAuxiliaryPolicy.ExecutionBinding msvcAuxiliaryBinding) {
        MsvcEntryWire { Objects.requireNonNull(command); Objects.requireNonNull(msvcAuxiliaryBinding); }
        MsvcEntryIntent current() { return new MsvcEntryIntent(command.current(),msvcAuxiliaryBinding); }
    }
    private record LegacyInvocation(String schema,String machineId,FileRef executable,List<String> arguments,String cwd,
            Map<String,String> environment,List<String> unsetEnvironment,FileRef bindingRef,FileRef specRef) {
        Invocation current() { return new Invocation(schema,machineId,executable,arguments,cwd,environment,unsetEnvironment,bindingRef,specRef); }
    }
    public enum JavaTargetKind { CLASS, JAR, SOURCE }
    /** An explicit caller intent; executable JAR manifests and source compilation use the sole engine. */
    public record JavaIntent(JavaTargetKind kind,FileRef primary,String mainClass,List<FileRef> classpath,
            List<CiBootstrap.JavaUtf8Invocation.Property> properties,List<String> arguments,List<String> asciiVmOptions,
            String sourceCompiledRoot,long maximumCompiledBytes) {
        public JavaIntent {
            Objects.requireNonNull(kind);Objects.requireNonNull(primary);classpath=List.copyOf(classpath);
            properties=List.copyOf(properties);arguments=List.copyOf(arguments);asciiVmOptions=List.copyOf(asciiVmOptions);
            if(kind==JavaTargetKind.JAR && (mainClass!=null || !classpath.isEmpty()))
                throw new IllegalArgumentException("JAR intent derives its main and complete manifest classpath from the original JAR");
            if(kind!=JavaTargetKind.JAR && (mainClass==null || mainClass.isBlank())) throw new IllegalArgumentException("Exact main class required");
            if(kind==JavaTargetKind.SOURCE ? sourceCompiledRoot==null || maximumCompiledBytes<1 || maximumCompiledBytes>(64L<<20)
                    :sourceCompiledRoot!=null || maximumCompiledBytes!=0) throw new IllegalArgumentException("Source-only compiled output bounds required");
        }
    }
    private record JavaEntry(LegacyEntryIntent entry,JavaIntent invocation,boolean utf8Outer) { }

    private static JsonNode exactJson(FileRef ref, int maximum) throws IOException {
        Objects.requireNonNull(ref);
        if (ref.bytes()>maximum) throw new IOException("Finite mechanical metadata bound exceeded");
        ref.verify(); byte[] bytes;
        try(var input=Files.newInputStream(Path.of(ref.path()))) {
            bytes=input.readNBytes(Math.toIntExact(ref.bytes()+1));
        }
        ref.verify(); return decodeExact(ref,bytes);
    }
    static JsonNode decodeExact(FileRef ref,byte[] bytes) throws IOException {
        FileRef readBody=plannedRef(Path.of(ref.path()),bytes);
        if(bytes.length!=ref.bytes() || !readBody.sha256().equals(ref.sha256()))
            throw new IOException("Actually decoded metadata bytes differ from exact pin");
        return ControlBuild.strictMapper().readTree(bytes);
    }
    private static String text(JsonNode value,String name) throws IOException {
        JsonNode field=value.get(name);
        if(field==null || !field.isTextual() || field.textValue().isBlank())
            throw new IOException("Exact nonempty standing string required: "+name);
        return field.textValue();
    }
    private static List<FileRef> refs(JsonNode value) throws IOException {
        if(value==null || !value.isArray()) throw new IOException("Exact runtime/executable array required");
        List<FileRef> result=new ArrayList<>();
        for(JsonNode entry:value) result.add(SharedOwnedCommand.strictFileRef(entry));
        return List.copyOf(result);
    }
    private static Path newTarget(Path destination) throws IOException {
        if(destination==null || !destination.isAbsolute()) throw new IOException("Absolute fresh metadata destination required");
        Path target=destination.toAbsolutePath().normalize(), parent=target.getParent();
        if(parent==null || !Files.isDirectory(parent)) throw new IOException("Existing admitted metadata parent required");
        SharedSourceFiles.plainAncestors(parent);
        if(Files.exists(target)) throw new java.nio.file.FileAlreadyExistsException(target.toString());
        return target;
    }
    private static FileRef plannedRef(Path path,byte[] bytes) throws IOException {
        try { return new FileRef(path.toString(),bytes.length,HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes))); }
        catch(NoSuchAlgorithmException error) { throw new IOException("SHA-256 unavailable",error); }
    }

    private static List<FileRef> declaredRuntime(JsonNode standing,SharedOwnedCommandBinding binding) throws IOException {
        List<FileRef> runtime=refs(standing.get("runtime_closure"));
        JsonNode delivery=exactJson(binding.deliveryRef(),1<<20);
        SharedOwnedCommandBinding.verifyAuthority(delivery,binding.deliveryExpectation(),binding.machineId());
        if(runtime.size()!=6 || !runtime.equals(refs(delivery.get("complete_runtime"))))
            throw new IOException("Complete exact six-file declared runtime required");
        for(FileRef ref:runtime) ref.verify();
        SharedOwnedCommand.strictFileRef(standing.get("qualified_tools_ref")).verify();
        SharedOwnedCommand.strictFileRef(standing.get("qualified_own_readback_ref")).verify();
        return runtime;
    }

    private static Invocation invocation(SharedOwnedCommandBinding binding,SharedOwnedCommand.Request request,
            JsonNode standing,FileRef bindingRef,FileRef specRef) throws Exception {
        SharedOwnedCommand.validateStanding(request,binding,standing);
        if(!Files.isDirectory(binding.nativeTemporaryRoot())) throw new IOException("Approved native TMP root must exist");
        SharedSourceFiles.plainAncestors(binding.nativeTemporaryRoot());
        List<FileRef> runtime=declaredRuntime(standing,binding);
        FileRef java=null;
        for(FileRef executable:refs(standing.get("allowed_executables"))) {
            if(Path.of(executable.path()).getFileName().toString().equalsIgnoreCase("java.exe")) {
                if(java!=null) throw new IOException("One exact allowed outer Java executable required");
                java=executable;
            }
        }
        if(java==null) throw new IOException("Standing has no allowed outer Java executable");
        java.verify();
        String classpath=String.join(";",runtime.stream().map(FileRef::path).toList());
        String temporary=binding.nativeTemporaryRoot().toString();
        List<String> arguments=List.of("-Xms32m","-Xmx128m","-XX:+ExitOnOutOfMemoryError",
                "-Djava.io.tmpdir="+temporary,"-Djna.tmpdir="+temporary,"-cp",classpath,
                SharedOwnedCommand.class.getName(),"run",bindingRef.path(),Long.toString(bindingRef.bytes()),bindingRef.sha256(),
                specRef.path(),Long.toString(specRef.bytes()),specRef.sha256());
        return new Invocation("xar.shared-owned-command-invocation/v2",binding.machineId(),java,arguments,
                request.cwd().toString(),Map.of("TMP",temporary,"TEMP",temporary),
                List.of("JAVA_TOOL_OPTIONS","JDK_JAVA_OPTIONS","_JAVA_OPTIONS","JDK_JAVAC_OPTIONS"),bindingRef,specRef);
    }

    private static SharedOwnedCommandBinding binding(EntryIntent entry) throws Exception {
        Objects.requireNonNull(entry); BindingIntent intended=Objects.requireNonNull(entry.binding());
        JsonNode standing=exactJson(intended.standingRef(),1<<20);
        SharedOwnedCommandBinding.verifyAuthority(standing,intended.standingExpectation(),intended.machineId());
        SharedOwnedCommandBinding binding=new SharedOwnedCommandBinding(SharedOwnedCommandBinding.SCHEMA,intended.machineId(),
                intended.launcherSourceRef(),intended.standingRef(),intended.deliveryRef(),
                Path.of(text(standing,"native_tmp_root")),Path.of(text(standing,"private_temporary_aggregate_root")),
                intended.standingExpectation(),intended.deliveryExpectation());
        return binding;
    }
    private static Prepared prepare(EntryIntent entry,Path bindingDestination,Path specDestination,boolean outerUtf8) throws Exception {
        return prepare(entry,bindingDestination,specDestination,outerUtf8,null);
    }
    private static Prepared prepare(EntryIntent entry,Path bindingDestination,Path specDestination,boolean outerUtf8,
            MsvcAuxiliaryPolicy.ExecutionBinding auxiliary) throws Exception {
        BindingIntent intended=entry.binding();SharedOwnedCommandBinding binding=binding(entry);
        JsonNode standing=exactJson(intended.standingRef(),1<<20);
        byte[] bindingBytes=ControlBuild.strictMapper().writeValueAsBytes(binding.toJson());
        if(!binding.equals(SharedOwnedCommandBinding.parse(ControlBuild.strictMapper().readTree(bindingBytes))))
            throw new IOException("Actual strict binding roundtrip differs");
        var actualSlot=SharedOwnedCommand.findSlot(standing,entry.slotId());
        Intent child=new Intent(intended.machineId(),entry.owner(),entry.coordinator(),entry.slotId(),entry.borrowedSlotId(),
                entry.runId(),intended.standingRef(),intended.launcherSourceRef(),entry.executable(),entry.arguments(),entry.cwd(),
                entry.environment(),entry.inputs(),entry.timeoutSeconds(),entry.memoryLimitBytes(),entry.rootExitDrainPolicy());
        Slot slot=new Slot(actualSlot.slotId(),actualSlot.outputRoot());
        if(auxiliary!=null && entry.javaInvocation()!=null) throw new IOException("One explicit child completion route required");
        byte[] spec=auxiliary!=null?produceMsvc(slot,child,auxiliary):
                entry.javaInvocation()==null?produce(slot,child):produceJava(slot,child,entry.javaInvocation());
        var parsed=SharedOwnedCommand.parseRequest(ControlBuild.strictMapper().readTree(spec));
        Invocation invocation=invocation(binding,parsed,standing,plannedRef(bindingDestination,bindingBytes),plannedRef(specDestination,spec));
        if(outerUtf8) invocation=publishOuterUtf8(invocation,binding,parsed,standing,actualSlot);
        else SharedOwnedCommand.requireLegacyAsciiJava(invocation.executable(),invocation.arguments());
        return new Prepared(bindingBytes,spec,invocation);
    }

    private static List<String> expectedOuterVmOptions(SharedOwnedCommandBinding binding) {
        String temporary=binding.nativeTemporaryRoot().toString();
        return List.of("-Xms32m","-Xmx128m","-XX:+ExitOnOutOfMemoryError","-Djava.io.tmpdir="+temporary,"-Djna.tmpdir="+temporary);
    }

    private static CiBootstrap.JavaUtf8Invocation.Request outerRequest(SharedOwnedCommandBinding binding,
            SharedOwnedCommand.Request command,JsonNode standing,FileRef bindingRef,FileRef specRef) throws Exception {
        List<FileRef> runtime=declaredRuntime(standing,binding);
        var carrier=SharedOwnedCommand.javaCarrier(runtime);
        Path origin=Path.of(SharedOwnedCommand.class.getProtectionDomain().getCodeSource().getLocation().toURI()).toAbsolutePath().normalize();
        if(runtime.stream().noneMatch(pin->Path.of(pin.path()).toAbsolutePath().normalize().equals(origin)))
            throw new IOException("Actual packaged SharedOwnedCommand origin must be in the original declared runtime");
        var target=new CiBootstrap.JavaUtf8Invocation.ClassTarget(SharedOwnedCommand.class.getName(),
                CiBootstrap.JavaUtf8Invocation.captureClasspath(origin),carrier.classpath());
        var slot=SharedOwnedCommand.findSlot(standing,command.slotId());
        Path evidence=SharedOwnedCommand.javaEvidenceRoot(slot.outputRoot(),command.owner(),command.runId(),true);
        var request=new CiBootstrap.JavaUtf8Invocation.Request(target,List.of(),
                List.of("run",bindingRef.path(),Long.toString(bindingRef.bytes()),bindingRef.sha256(),
                        specRef.path(),Long.toString(specRef.bytes()),specRef.sha256()),
                CiBootstrap.JavaUtf8Invocation.captureOutputRoot(evidence));
        SharedOwnedCommand.requireJavaEvidenceRoot(request,evidence);return request;
    }

    private static Invocation publishOuterUtf8(Invocation legacy,SharedOwnedCommandBinding binding,
            SharedOwnedCommand.Request command,JsonNode standing,SharedOwnedCommand.Slot slot) throws Exception {
        var request=outerRequest(binding,command,standing,legacy.bindingRef(),legacy.specRef());
        Path root=Path.of(request.evidenceRoot().path());
        var publication=CiBootstrap.JavaUtf8Invocation.publish(request,request.evidenceRoot(),"whole-entry-java-utf8.bin",pending->{
            long allocated=SharedOwnedCommand.allocated(slot.outputRoot());
            if(Math.addExact(allocated,pending)>slot.outputCapBytes()) throw new IOException("Outer UTF8 preparation exceeds original slot output cap");
        });
        var options=expectedOuterVmOptions(binding);var carrier=SharedOwnedCommand.javaCarrier(declaredRuntime(standing,binding));
        var launch=CiBootstrap.JavaUtf8Invocation.launch(publication,carrier,options);
        if(!launch.logicalRequest().equals(request)) throw new IOException("Published outer UTF8 logical request differs");
        try(var quoted=JavaUtf8NativeCustody.acquire(launch,carrier)) {
            long pending=Math.addExact(CiBootstrap.JavaUtf8Invocation.maximumOutputBytes(request),quoted.maximumEvidenceBytes(Path.of(legacy.executable().path())));
            if(Math.addExact(SharedOwnedCommand.allocated(slot.outputRoot()),pending)>slot.outputCapBytes()) throw new IOException("Outer native continuity proof and engine preparation exceed original slot");
        }
        return new Invocation("xar.shared-owned-command-invocation/v4",legacy.machineId(),legacy.executable(),launch.physicalArguments(),
                legacy.cwd(),legacy.environment(),legacy.unsetEnvironment(),legacy.bindingRef(),legacy.specRef(),
                new SharedOwnedCommand.JavaInvocation(SharedSourceFiles.observe(Path.of(publication.envelope().path())),options));
    }

    private static CiBootstrap.JavaUtf8Invocation.Request outerLogical(SharedOwnedCommandBinding binding,
            SharedOwnedCommand.Request request,JsonNode standing,FileRef bindingRef,FileRef specRef,
            SharedOwnedCommand.JavaInvocation invocation) throws Exception {
        var expected=outerRequest(binding,request,standing,bindingRef,specRef);
        var actual=CiBootstrap.JavaUtf8Invocation.read(invocation.publication());
        if(!expected.equals(actual)) throw new IOException("Exact outer UTF8 target/arguments/evidence root changed");
        return actual;
    }

    /** Produces all metadata before CREATE_NEW publication and never starts a process. */
    public static Published publishInvocation(Path bindingDestination,Path specDestination,Path invocationDestination,
            EntryIntent entry) throws Exception {
        return publishInvocation(bindingDestination,specDestination,invocationDestination,entry,false);
    }
    /** Explicit UTF8 outer mode; its sibling evidence directory must already be issuer-admitted. */
    public static Published publishUtf8Invocation(Path bindingDestination,Path specDestination,Path invocationDestination,
            EntryIntent entry) throws Exception {
        return publishInvocation(bindingDestination,specDestination,invocationDestination,entry,true);
    }
    public static Published publishMsvcInvocation(Path bindingDestination,Path specDestination,Path invocationDestination,
            MsvcEntryIntent entry) throws Exception {
        return publishMsvcInvocation(bindingDestination,specDestination,invocationDestination,entry,false);
    }
    /** The optional UTF8 outer uses the original Host carrier; the explicit MSVC child remains v3. */
    public static Published publishMsvcInvocation(Path bindingDestination,Path specDestination,Path invocationDestination,
            MsvcEntryIntent entry,boolean outerUtf8) throws Exception {
        Objects.requireNonNull(entry);
        return publishInvocation(bindingDestination,specDestination,invocationDestination,entry.command(),outerUtf8,entry.msvcAuxiliaryBinding());
    }
    /** Publishes an explicitly selected CLASS/JAR/SOURCE child envelope, then the strict whole-entry metadata. */
    public static Published publishJavaInvocation(Path bindingDestination,Path specDestination,Path invocationDestination,
            EntryIntent base,JavaIntent intended,boolean outerUtf8) throws Exception {
        newTarget(bindingDestination);newTarget(specDestination);newTarget(invocationDestination);
        if(base.javaInvocation()!=null || !base.arguments().isEmpty()) throw new IOException("One explicit logical Java child intent required");
        var binding=binding(base);JsonNode standing=exactJson(base.binding().standingRef(),1<<20);
        var slot=SharedOwnedCommand.findSlot(standing,base.slotId());
        Intent empty=new Intent(base.binding().machineId(),base.owner(),base.coordinator(),base.slotId(),base.borrowedSlotId(),base.runId(),
                base.binding().standingRef(),base.binding().launcherSourceRef(),base.executable(),List.of(),base.cwd(),base.environment(),
                base.inputs(),base.timeoutSeconds(),base.memoryLimitBytes(),base.rootExitDrainPolicy());
        var preliminary=SharedOwnedCommand.parseRequest(ControlBuild.strictMapper().readTree(produce(new Slot(slot.slotId(),slot.outputRoot()),empty)));
        SharedOwnedCommand.validateStanding(preliminary,binding,standing);
        if(!Path.of(base.executable().path()).getFileName().toString().equalsIgnoreCase("java.exe")) throw new IOException("Java child intent needs allowed java.exe");
        requireExplicitInput(intended.primary(),base.inputs());intended.primary().verify();
        var cp=new ArrayList<CiBootstrap.JavaUtf8Invocation.ClasspathPin>();
        for(FileRef pin:intended.classpath()) { requireExplicitInput(pin,base.inputs());pin.verify();cp.add(CiBootstrap.JavaUtf8Invocation.captureClasspath(Path.of(pin.path()))); }
        Path evidence=SharedOwnedCommand.javaEvidenceRoot(slot.outputRoot(),base.owner(),base.runId(),false);
        if(intended.kind()==JavaTargetKind.SOURCE && !Path.of(intended.sourceCompiledRoot()).toAbsolutePath().normalize().equals(evidence.resolve("compiled-source")))
            throw new IOException("Source compilation must stay in its exact separately admitted child evidence subtree");
        CiBootstrap.JavaUtf8Invocation.Target target=switch(intended.kind()) {
            case CLASS -> new CiBootstrap.JavaUtf8Invocation.ClassTarget(intended.mainClass(),
                    CiBootstrap.JavaUtf8Invocation.captureClasspath(Path.of(intended.primary().path())),List.copyOf(cp));
            case JAR -> CiBootstrap.JavaUtf8Invocation.captureJar(Path.of(intended.primary().path()));
            case SOURCE -> new CiBootstrap.JavaUtf8Invocation.SourceTarget(CiBootstrap.JavaUtf8Invocation.captureFile(Path.of(intended.primary().path())),
                    intended.mainClass(),List.copyOf(cp),CiBootstrap.JavaUtf8Invocation.captureOutputRoot(Path.of(intended.sourceCompiledRoot())),intended.maximumCompiledBytes());
        };
        var request=new CiBootstrap.JavaUtf8Invocation.Request(target,intended.properties(),intended.arguments(),
                CiBootstrap.JavaUtf8Invocation.captureOutputRoot(evidence));
        SharedOwnedCommand.requireJavaEvidenceRoot(request,evidence);
        var publication=CiBootstrap.JavaUtf8Invocation.publish(request,request.evidenceRoot(),"child-java-utf8.bin",pending->{
            if(Math.addExact(SharedOwnedCommand.allocated(slot.outputRoot()),pending)>slot.outputCapBytes())
                throw new IOException("Child UTF8 preparation exceeds original slot output cap");
        });
        var descriptor=new SharedOwnedCommand.JavaInvocation(SharedSourceFiles.observe(Path.of(publication.envelope().path())),intended.asciiVmOptions());
        var inputs=new ArrayList<>(base.inputs());inputs.add(descriptor.fileRef());
        EntryIntent entry=new EntryIntent(base.binding(),base.owner(),base.coordinator(),base.slotId(),base.borrowedSlotId(),base.runId(),
                base.executable(),List.of(),base.cwd(),base.environment(),inputs,base.timeoutSeconds(),base.memoryLimitBytes(),base.rootExitDrainPolicy(),descriptor);
        return publishInvocation(bindingDestination,specDestination,invocationDestination,entry,outerUtf8);
    }
    private static void requireExplicitInput(FileRef expected,List<FileRef> inputs) throws IOException {
        int found=0;for(FileRef input:inputs) if(inputPathKey(expected).equals(inputPathKey(input))
                && expected.bytes()==input.bytes() && expected.sha256().equals(input.sha256())) found++;
        if(found!=1) throw new IOException("Every Java primary/classpath source must be one exact explicit input");
    }
    private static Published publishInvocation(Path bindingDestination,Path specDestination,Path invocationDestination,
            EntryIntent entry,boolean outerUtf8) throws Exception {
        return publishInvocation(bindingDestination,specDestination,invocationDestination,entry,outerUtf8,null);
    }
    private static Published publishInvocation(Path bindingDestination,Path specDestination,Path invocationDestination,
            EntryIntent entry,boolean outerUtf8,MsvcAuxiliaryPolicy.ExecutionBinding auxiliary) throws Exception {
        Path bindingPath=newTarget(bindingDestination),specPath=newTarget(specDestination),invocationPath=newTarget(invocationDestination);
        if(Set.of(bindingPath,specPath,invocationPath).size()!=3) throw new IOException("Three distinct immutable metadata paths required");
        Prepared prepared=prepare(entry,bindingPath,specPath,outerUtf8,auxiliary);
        byte[] wire=ControlBuild.strictMapper().writeValueAsBytes(prepared.invocation());
        if(wire.length>65536) throw new IOException("Finite whole-entry invocation bound exceeded");
        Files.write(bindingPath,prepared.binding(),StandardOpenOption.CREATE_NEW,StandardOpenOption.WRITE);
        Files.write(specPath,prepared.spec(),StandardOpenOption.CREATE_NEW,StandardOpenOption.WRITE);
        Files.write(invocationPath,wire,StandardOpenOption.CREATE_NEW,StandardOpenOption.WRITE);
        FileRef bindingRef=FileRef.measure(bindingPath),specRef=FileRef.measure(specPath),invocationRef=FileRef.measure(invocationPath);
        if(!bindingRef.equals(prepared.invocation().bindingRef()) || !specRef.equals(prepared.invocation().specRef())
                || !readInvocation(invocationRef).equals(prepared.invocation()))
            throw new IOException("Published immutable whole-entry readback differs");
        return new Published(bindingRef,specRef,invocationRef);
    }

    /** Rejects missing JNA flags, stale temporary bindings and changed argv before a child. */
    public static Invocation readInvocation(FileRef exactRef) throws Exception {
        JsonNode wire=exactJson(exactRef,65536);
        Invocation value=text(wire,"schema").equals("xar.shared-owned-command-invocation/v2")
                ?ControlBuild.strictMapper().treeToValue(wire,LegacyInvocation.class).current()
                :ControlBuild.strictMapper().treeToValue(wire,Invocation.class);
        SharedOwnedCommandBinding binding=SharedOwnedCommandBinding.read(value.bindingRef());
        var request=SharedOwnedCommand.parseRequest(exactJson(value.specRef(),1<<20));
        JsonNode standing=exactJson(binding.standingRef(),1<<20);
        Invocation expected=invocation(binding,request,standing,value.bindingRef(),value.specRef());
        if(value.javaInvocation()==null) {
            if(!value.equals(expected)) throw new IOException("Whole-entry argv/executable/TMP/refs differ from exact standing");
            SharedOwnedCommand.requireLegacyAsciiJava(value.executable(),value.arguments());
        } else {
            var actual=outerLogical(binding,request,standing,value.bindingRef(),value.specRef(),value.javaInvocation());
            var carrier=SharedOwnedCommand.javaCarrier(declaredRuntime(standing,binding));
            var inspected=CiBootstrap.JavaUtf8Invocation.inspect(value.arguments(),carrier,value.javaInvocation().asciiVmOptions());
            if(!actual.equals(inspected)) throw new IOException("Outer UTF8 logical request differs from exact binding/spec/runtime");
            var launch=CiBootstrap.JavaUtf8Invocation.launch(value.javaInvocation().publication(),carrier,expectedOuterVmOptions(binding));
            Invocation rederived=new Invocation("xar.shared-owned-command-invocation/v4",expected.machineId(),expected.executable(),
                    launch.physicalArguments(),expected.cwd(),expected.environment(),expected.unsetEnvironment(),expected.bindingRef(),expected.specRef(),value.javaInvocation());
            if(!value.javaInvocation().asciiVmOptions().equals(expectedOuterVmOptions(binding)) || !value.equals(rederived))
                throw new IOException("Outer UTF8 startup options/physical arguments differ");
        }
        exactRef.verify(); return value;
    }

    /** Actual outer engine preparation is separate from request acceptance and the Shared child terminal. */
    /** The original owning launcher retains this across its original WJP; no process or extra wrapper is created here. */
    public static JavaUtf8NativeCustody.Held acquireInvocationCustody(FileRef exactRef) throws Exception {
        var value=readInvocation(exactRef);
        if(value.javaInvocation()==null) throw new IOException("Explicit UTF8 invocation required");
        var binding=SharedOwnedCommandBinding.read(value.bindingRef());
        var standing=exactJson(binding.standingRef(),1<<20);
        var carrier=SharedOwnedCommand.javaCarrier(declaredRuntime(standing,binding));
        var launch=CiBootstrap.JavaUtf8Invocation.launch(value.javaInvocation().publication(),carrier,value.javaInvocation().asciiVmOptions());
        return JavaUtf8NativeCustody.acquire(launch,carrier);
    }
    /** Readback is historical observation and cannot recreate a live Held execution capability. */
    public static PreparedInvocation readPreparedInvocation(FileRef exactRef,FileRef nativeEvidenceRef) throws Exception {
        Invocation value=readInvocation(exactRef);
        if(value.javaInvocation()==null) throw new IOException("Historical ASCII invocation carries no UTF8 preparation claim");
        var binding=SharedOwnedCommandBinding.read(value.bindingRef());var standing=exactJson(binding.standingRef(),1<<20);
        var carrier=SharedOwnedCommand.javaCarrier(declaredRuntime(standing,binding));
        var publication=value.javaInvocation().publication();var launch=CiBootstrap.JavaUtf8Invocation.launch(publication,carrier,value.javaInvocation().asciiVmOptions());
        var sources=SharedOwnedCommand.readNativeEvidence(nativeEvidenceRef);
        JavaUtf8NativeCustody.requireCurrent(sources,launch,carrier);
        if(!Path.of(sources.identity().executable()).equals(Path.of(value.executable().path()))) throw new IOException("Original outer executable differs");
        var preparation=CiBootstrap.JavaUtf8Invocation.preparationPath(launch.logicalRequest());
        var pin=SharedSourceFiles.observe(preparation);
        var actual=CiBootstrap.JavaUtf8Invocation.inspectPreparation(CiBootstrap.JavaUtf8Invocation.captureFile(preparation),publication);
        SharedSourceFiles.assertUnchanged(pin);exactRef.verify();return new PreparedInvocation(value,pin,nativeEvidenceRef,actual);
    }

    public static void main(String[] arguments) throws Exception {
        boolean utf8=arguments.length==7 && arguments[0].equals("utf8");int start=utf8?1:0;
        boolean java=arguments.length==7 && arguments[0].equals("java");if(java) start=1;
        boolean msvc=arguments.length==7 && (arguments[0].equals("msvc") || arguments[0].equals("msvc-utf8"));
        boolean msvcUtf8=msvc && arguments[0].equals("msvc-utf8");if(msvc) start=1;
        if(arguments.length!=6 && !utf8 && !java && !msvc) throw new IOException("[utf8|java|msvc|msvc-utf8] entry.json exact-bytes exact-sha256 binding.json spec.json invocation.json required");
        FileRef entryRef=new FileRef(arguments[start],Long.parseLong(arguments[start+1]),arguments[start+2]);
        JsonNode entryWire=exactJson(entryRef,1<<20);
        Published result;
        if(msvc) {
            MsvcEntryIntent entry=decodeMsvcEntryIntent(entryWire);
            result=publishMsvcInvocation(Path.of(arguments[start+3]),Path.of(arguments[start+4]),Path.of(arguments[start+5]),entry,msvcUtf8);
        } else if(java) {
            JavaEntry declared=ControlBuild.strictMapper().treeToValue(entryWire,JavaEntry.class);
            result=publishJavaInvocation(Path.of(arguments[start+3]),Path.of(arguments[start+4]),Path.of(arguments[start+5]),
                    declared.entry().current(),declared.invocation(),declared.utf8Outer());
        } else {
            EntryIntent entry=entryWire.has("java_invocation")?ControlBuild.strictMapper().treeToValue(entryWire,EntryIntent.class)
                    :ControlBuild.strictMapper().treeToValue(entryWire,LegacyEntryIntent.class).current();
            result=publishInvocation(Path.of(arguments[start+3]),Path.of(arguments[start+4]),Path.of(arguments[start+5]),entry,utf8);
        }
        entryRef.verify(); System.out.println("WHOLE_ENTRY_METADATA_ONLY invocation="+result.invocationRef().path()+" sha256="+result.invocationRef().sha256());
    }

    static MsvcEntryIntent decodeMsvcEntryIntent(JsonNode wire) throws IOException {
        if(wire==null || !wire.isObject()) throw new IOException("Exact MSVC entry object required");
        return ControlBuild.strictMapper().treeToValue(wire,MsvcEntryWire.class).current();
    }

    /** One issuer slot root, distinct from the command's owner/run output directory. */
    public record Slot(String slotId, Path outputRoot) {
        public Slot {
            if (slotId == null || slotId.isBlank() || outputRoot == null || !outputRoot.isAbsolute())
                throw new IllegalArgumentException("Exact slot id and absolute slot root required");
            outputRoot = outputRoot.toAbsolutePath().normalize();
        }
    }

    /** Output root is deliberately absent: every phase derives it from its exact slot, owner and run. */
    public record Intent(String machineId, String owner, String coordinator, String slotId,
            String borrowedSlotId, String runId, FileRef standingRef, FileRef launcherSourceRef,
            FileRef executable, List<String> arguments, String cwd, Map<String,String> environment,
            List<FileRef> inputs, long timeoutSeconds, long memoryLimitBytes,
            WindowsJobProcess.RootExitDrainPolicy rootExitDrainPolicy) {
        public Intent {
            arguments = List.copyOf(arguments);
            environment = Map.copyOf(environment);
            inputs = List.copyOf(inputs);
            validateInputs(executable, inputs);
        }
    }

    /** Matches Windows normalized path identity, reserving the automatically guarded executor first.
     * Conflicting or identical duplicate refs are rejected; none are silently removed. */
    public static void validateInputs(FileRef executable, List<FileRef> inputs) {
        Objects.requireNonNull(executable, "executable"); Objects.requireNonNull(inputs, "inputs");
        Set<String> seen = new HashSet<>();
        seen.add(inputPathKey(executable));
        for (FileRef input : inputs) {
            if (!seen.add(inputPathKey(Objects.requireNonNull(input, "input"))))
                throw new IllegalArgumentException("Input path duplicates reserved executable or another input: " + input.path());
        }
    }

    private static String inputPathKey(FileRef ref) {
        return Path.of(ref.path()).toAbsolutePath().normalize().toString().replace((char) 92, (char) 47).toLowerCase(Locale.ROOT);
    }

    /** Closed existing twenty-field v2 wire, parsed by the actual mechanical consumer before return. */
    public static byte[] produce(Slot slot, Intent intent) throws IOException {
        SharedOwnedCommand.requireLegacyAsciiJava(intent.executable(),intent.arguments());
        return produce(slot,intent,null);
    }
    public static byte[] produceJava(Slot slot,Intent intent,SharedOwnedCommand.JavaInvocation javaInvocation) throws IOException {
        Objects.requireNonNull(javaInvocation,"Explicit sole-engine Java publication required");
        return produce(slot,intent,javaInvocation);
    }
    /** Legacy v2 and UTF8 Java-child v4 remain unchanged; only this producer opts into MSVC v3. */
    public static byte[] produceMsvc(Slot slot,Intent intent,MsvcAuxiliaryPolicy.ExecutionBinding auxiliary) throws IOException {
        Objects.requireNonNull(auxiliary); auxiliary.requireRequest(intent.executable(),intent.inputs());
        if(intent.rootExitDrainPolicy()!=WindowsJobProcess.RootExitDrainPolicy.DEFAULT_FIVE_SECONDS)
            throw new IOException("Explicit MSVC auxiliary policy replaces the default drain choice");
        var mapper=ControlBuild.strictMapper();ObjectNode wire=(ObjectNode)mapper.readTree(produce(slot,intent));
        wire.put("schema","xar.shared-owned-command-spec/v3");wire.set("msvc_auxiliary_binding",mapper.valueToTree(auxiliary));
        byte[] bytes=mapper.writeValueAsBytes(wire);if(bytes.length>1<<20)throw new IOException("MSVC spec exceeds existing1MiB bound");
        var request=SharedOwnedCommand.parseRequest(mapper.readTree(bytes));
        if(!auxiliary.equals(request.msvcAuxiliaryBinding()))throw new IOException("Explicit MSVC producer/consumer roundtrip differs");
        return bytes;
    }
    private static byte[] produce(Slot slot,Intent intent,SharedOwnedCommand.JavaInvocation javaInvocation) throws IOException {
        Objects.requireNonNull(slot, "slot"); Objects.requireNonNull(intent, "intent");
        if (!slot.slotId().equals(intent.slotId()) || intent.timeoutSeconds() <= 0 || intent.memoryLimitBytes() <= 0)
            throw new IOException("Exact slot assignment and positive finite child bounds required");
        validateInputs(intent.executable(), intent.inputs());
        Path output = SharedOwnedCommand.commandOutputRoot(slot.outputRoot(), intent.owner(), intent.runId());
        var mapper = ControlBuild.strictMapper();
        ObjectNode value = mapper.valueToTree(intent);
        value.put("schema", javaInvocation==null?"xar.shared-owned-command-spec/v2":"xar.shared-owned-command-spec/v4");
        if(javaInvocation!=null) value.set("java_invocation",mapper.valueToTree(javaInvocation));
        value.put("output_root", output.toString());
        value.putNull("operation_card_ref");
        value.put("temporary_policy", "SLOT_PRIVATE");
        // Nullable fields must stay present even if a mapper's default inclusion policy evolves.
        if (intent.borrowedSlotId() == null) value.putNull("borrowed_slot_id");
        var parsed = SharedOwnedCommand.parseRequest(value);
        SharedOwnedCommand.requireCommandOutputRoot(parsed.outputRoot(), slot.outputRoot(), parsed.owner(), parsed.runId());
        if (!parsed.outputRoot().equals(output))
            throw new IOException("Generated command layout differs from actual mechanical parser");
        byte[] bytes = mapper.writeValueAsBytes(value);
        if (bytes.length > 1 << 20) throw new IOException("Generated spec exceeds existing1MiB bound");
        SharedOwnedCommand.parseRequest(mapper.readTree(bytes));
        return bytes;
    }

    /** Publishes one immutable spec in an existing admitted metadata parent. Never starts a child. */
    public static FileRef publish(Path destination, Slot slot, Intent intent) throws IOException {
        byte[] bytes = produce(slot, intent);
        if (destination == null || !destination.isAbsolute())
            throw new IOException("Absolute fresh metadata destination required");
        Path target = destination.toAbsolutePath().normalize();
        Path parent = target.getParent();
        if (parent == null || !Files.isDirectory(parent))
            throw new IOException("Existing admitted metadata parent required");
        SharedSourceFiles.plainAncestors(parent);
        Files.write(target, bytes, StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE);
        FileRef exact = FileRef.measure(target);
        if (!java.util.Arrays.equals(bytes, Files.readAllBytes(target)))
            throw new IOException("Immutable generated spec readback differs");
        exact.verify();
        return exact;
    }
}
