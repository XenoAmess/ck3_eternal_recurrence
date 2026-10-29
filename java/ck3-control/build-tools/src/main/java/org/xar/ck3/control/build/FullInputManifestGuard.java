package org.xar.ck3.control.build;

import com.fasterxml.jackson.databind.JsonNode;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import java.util.TreeMap;
import java.util.zip.GZIPOutputStream;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.SharedSourceFiles.Witness;

/** Complete immutable-input guard around the existing owned Windows Job command. */
public final class FullInputManifestGuard {
    private FullInputManifestGuard() { }
    public enum State { PASS, RED, REJECTED }
    public record Command(FileRef executable, List<String> arguments, Path cwd,
                          Map<String,String> environment, long memoryLimitBytes, long timeoutSeconds) { }
    public record Request(String machineId, FileRef manifestRef, String manifestSchema,
                          List<FileRef> additionalInputs, Command command, Path outputRoot, NativeBridgeRootGate.Limits authority, List<OutputScope> outputScopes, FileRef runtimeInventoryRef) {
        public Request(String machineId,FileRef manifestRef,String manifestSchema,List<FileRef> additionalInputs,Command command,Path outputRoot) {
            this(machineId,manifestRef,manifestSchema,additionalInputs,command,outputRoot,null,List.of(),null);
        }
    }
    public record OutputScope(String part, Path root, long allocationLimitBytes) { }
    public record Snapshot(String schema, String machineId, FileRef requestRef, FileRef manifestRef,
                           List<Witness> witnesses) { }
    public record Terminal(String schema, String machineId, String observedAtUtc, State status,
                           FileRef requestRef, FileRef manifestRef, int manifestFiles, int guardedFiles,
                           int verifiedBefore, int verifiedAfter, boolean childStarted,
                           WindowsJobProcess.CommandResult child, FileRef snapshotRef, String error) { }
    private static void require(boolean condition,String message) throws IOException {
        if (!condition) throw new IOException(message);
    }
    private static JsonNode object(JsonNode value) throws IOException {
        require(value != null && value.isObject(), "object required"); return value;
    }
    private static void keys(JsonNode value,Set<String> expected) throws IOException {
        object(value); Set<String> actual=new HashSet<>();value.fieldNames().forEachRemaining(actual::add);
        require(actual.equals(expected),"exact fields required: "+expected);
    }
    private static String text(JsonNode value,String key) throws IOException {
        JsonNode node=value.get(key); require(node!=null && node.isTextual() && !node.textValue().isBlank(),"text required: "+key);
        return node.textValue();
    }
    private static long number(JsonNode value,String key,long minimum,long maximum) throws IOException {
        JsonNode node=value.get(key);require(node!=null && node.isIntegralNumber() && node.canConvertToLong(),"integer required: "+key);
        long result=node.longValue();require(result>=minimum && result<=maximum,"integer range: "+key);return result;
    }
    private static Path path(String value) throws IOException {
        Path result=Path.of(value);require(result.isAbsolute(),"absolute path required");return result.toAbsolutePath().normalize();
    }
    private static FileRef ref(JsonNode value) throws IOException {
        keys(value,Set.of("path","bytes","sha256"));String hash=text(value,"sha256");require(hash.matches("[a-f0-9]{64}"),"SHA256 required");
        return new FileRef(path(text(value,"path")).toString(),number(value,"bytes",0,128L<<20),hash);
    }
    private static List<FileRef> refs(JsonNode value) throws IOException {
        require(value!=null && value.isArray() && value.size()<=20000,"bounded file array required");
        List<FileRef> result=new ArrayList<>();for(JsonNode entry:value)result.add(ref(entry));return List.copyOf(result);
    }
    public static Request parse(JsonNode value) throws IOException {
        String schema=text(value,"schema");boolean version2=schema.equals("xar.full-input-manifest-guard-request/v2");
        require(version2||schema.equals("xar.full-input-manifest-guard-request/v1"),"request schema");
        keys(value,version2?Set.of("schema","machine_id","manifest_ref","manifest_schema","additional_inputs","command","output_root","authority","output_scopes","runtime_inventory_ref")
                :Set.of("schema","machine_id","manifest_ref","manifest_schema","additional_inputs","command","output_root"));
        NativeBridgeRootGate.Limits authority=null;FileRef runtimeInventory=null;List<OutputScope> scopes=List.of();
        if(version2){
            require(value.get("authority")!=null&&value.get("authority").isObject(),"version2 requires explicit actual capacity authority");
            authority=RootNativePlanJson.mapper().treeToValue(value.get("authority"),NativeBridgeRootGate.Limits.class);
            JsonNode outputScopes=value.get("output_scopes");require(outputScopes!=null&&outputScopes.isArray()&&!outputScopes.isEmpty()&&outputScopes.size()<=16,"complete finite output scopes required");
            var parsedScopes=new ArrayList<OutputScope>();for(JsonNode scope:outputScopes){keys(scope,Set.of("part","root","allocation_limit_bytes"));
                parsedScopes.add(new OutputScope(text(scope,"part"),path(text(scope,"root")),number(scope,"allocation_limit_bytes",4096,1536L<<20)));}
            scopes=List.copyOf(parsedScopes);
            require(value.has("runtime_inventory_ref"),"version2 requires explicit nullable runtime inventory");
            if(!value.get("runtime_inventory_ref").isNull())runtimeInventory=ref(value.get("runtime_inventory_ref"));
        }
        String machine=text(value,"machine_id");require(machine.equals(WindowsJobProcess.currentMachineId()),"current machine required");
        JsonNode command=value.get("command");keys(command,Set.of("executable","arguments","cwd","environment","memory_limit_bytes","timeout_seconds"));
        JsonNode args=command.get("arguments");require(args!=null&&args.isArray()&&args.size()<=4096,"arguments required");List<String> arguments=new ArrayList<>();
        for(JsonNode arg:args){require(arg.isTextual()&&arg.textValue().indexOf(0)<0,"text argument required");arguments.add(arg.textValue());}
        JsonNode env=object(command.get("environment"));Map<String,String> environment=new TreeMap<>(String.CASE_INSENSITIVE_ORDER);
        for(var entry:env.properties()) {require(entry.getValue().isTextual(),"text environment value required");String key=entry.getKey();
            require(!Set.of("JAVA_TOOL_OPTIONS","JDK_JAVA_OPTIONS","_JAVA_OPTIONS","JDK_JAVAC_OPTIONS","TEMP","TMP").contains(key.toUpperCase(Locale.ROOT)),"controlled environment key");
            require(!version2||!key.equalsIgnoreCase("TMPDIR"),"version2 controls all native temporary variables");
            require(environment.put(key,entry.getValue().textValue())==null,"duplicate environment key");}
        Command parsed=new Command(ref(command.get("executable")),List.copyOf(arguments),path(text(command,"cwd")),Map.copyOf(environment),
                number(command,"memory_limit_bytes",16L<<20,version2?3L<<30:640L<<20),number(command,"timeout_seconds",1,version2?7200:170));
        if(version2)require(parsed.memoryLimitBytes()<=authority.memoryLimitBytes()&&parsed.timeoutSeconds()<=authority.timeoutSeconds(),"inner command exceeds exact authority limits");
        return new Request(machine,ref(value.get("manifest_ref")),text(value,"manifest_schema"),refs(value.get("additional_inputs")),parsed,path(text(value,"output_root")),authority,scopes,runtimeInventory);
    }
    private static List<FileRef> manifest(Request request) throws IOException {
        JsonNode value=ControlBuild.strictMapper().readTree(Files.readAllBytes(Path.of(request.manifestRef().path())));
        keys(value,Set.of("schema","machine_id","observed_at_utc","files"));
        require(text(value,"schema").equals(request.manifestSchema()),"exact configured manifest schema required");
        require(text(value,"machine_id").equals(request.machineId()),"manifest machine required");Instant.parse(text(value,"observed_at_utc"));
        List<FileRef> result=refs(value.get("files"));require(!result.isEmpty(),"nonempty manifest required");
        Set<String> paths=new HashSet<>();for(FileRef file:result)require(paths.add(file.path().toLowerCase(Locale.ROOT)),"duplicate manifest input");return result;
    }
    private static boolean sameRef(FileRef a,FileRef b) throws IOException {
        return path(a.path()).equals(path(b.path())) && a.bytes()==b.bytes() && a.sha256().equals(b.sha256());
    }
    private static Witness checked(FileRef ref) throws IOException {
        Witness witness=SharedSourceFiles.observe(Path.of(ref.path()));require(witness.source().equals(ref),"input bytes/SHA drift: "+ref.path());return witness;
    }
    private static void write(Path file,Object value) throws IOException {
        Files.write(file,ControlBuild.strictMapper().writeValueAsBytes(value),StandardOpenOption.CREATE_NEW);
    }
    /** Actual common-policy capacity and the sole shared native allocation census, without a second build authority. */
    private static final class OutputBudget {
        private static final long RESERVE=16L<<20;
        private final Request request;
        private final NativeBridgeRootGate.Limits limits;
        private final ControlBuild.CapacityRelease release;
        private final List<Path> roots;
        private OutputBudget(Request request) throws IOException {
            this.request=request;limits=request.authority();
            require(limits.capacityEvidence().bytes()>0&&limits.capacityEvidence().bytes()<=131072,"finite original capacity required");
            limits.capacityEvidence().verify();
            release=ControlBuild.strictMapper().readValue(Files.readAllBytes(path(limits.capacityEvidence().path())),ControlBuild.CapacityRelease.class);
            require(release.schema().equals("xar.java-control.capacity-release/v1")&&release.status().equals("RELEASED")
                    &&release.machineId().equals(request.machineId())&&release.ownerTask().equals(limits.ownerTask())
                    &&!limits.deadline().isAfter(Instant.parse(release.reviewAtUtc()))
                    &&limits.memoryLimitBytes()<=release.memoryLimitBytes()
                     ,"exact current full-input capacity/owner/limits required");
            List<Path> declared=new ArrayList<>();
            for(String value:release.approvedOutputRoots())declared.add(path(value));
            Path temporary=path(release.temporaryRoot());
            require(declared.stream().anyMatch(temporary::startsWith),"entire temporary root must be admitted");
            roots=declared.stream().distinct().filter(root->declared.stream().noneMatch(parent->!parent.equals(root)&&root.startsWith(parent))).toList();
            require(!roots.isEmpty()&&roots.size()<=16,"finite complete output roots required");
            for(Path root:roots){require(root.getParent()!=null,"whole-volume output scope forbidden");SharedSourceFiles.plainAncestors(root);}
            require(roots.stream().anyMatch(request.outputRoot()::startsWith)&&roots.stream().anyMatch(request.command().cwd()::startsWith),
                    "guard output and mutable build cwd must be admitted");
            String javaTemporary=System.getProperty("java.io.tmpdir"),jnaTemporary=System.getProperty("jna.tmpdir");
            require(javaTemporary!=null&&jnaTemporary!=null&&path(javaTemporary).startsWith(temporary)
                    &&path(jnaTemporary).startsWith(temporary),"guard JVM temporary roots escaped actual capacity");
            require(release.policyRef().bytes()>0&&release.policyRef().bytes()<=131072,"finite original policy required");
            var byPart=new java.util.HashMap<String,Long>();long entire=0;var scopePaths=new HashSet<Path>();
            for(OutputScope scope:request.outputScopes()){require(roots.contains(scope.root())&&scopePaths.add(scope.root()),"exact distinct admitted root scope required");
                byPart.merge(scope.part(),scope.allocationLimitBytes(),Math::addExact);entire=Math.addExact(entire,scope.allocationLimitBytes());}
            require(scopePaths.equals(Set.copyOf(roots))&&entire==limits.outputAllocationLimitBytes(),"complete exact scope denominator differs");
            for(var part:byPart.entrySet())require(part.getValue()<=release.parts().getOrDefault(part.getKey(),0L),"output scope exceeds its own financial partition");
            var policy=CiBootstrap.readPolicy(Files.readAllBytes(path(release.policyRef().path())));release.policyRef().verify();
            for(var entry:release.volumes().entrySet()){
                var volume=entry.getValue();var override=release.quotaOverrides().get(entry.getKey());
                if(override!=null){require(override.task().equals(release.ownerTask())&&!Instant.parse(override.reviewAtUtc()).isAfter(Instant.parse(release.reviewAtUtc())),"quota override owner/window differs");
                    new FileRef(override.sourceRef().path(),override.sourceRef().bytes(),override.sourceRef().sha256()).verify();}
                require(volume.equals(CiBootstrap.calculate(policy,volume.totalVolumeBytes(),volume.availableBytes(),volume.thisWritePeak(),
                        volume.otherUnspentReservations(),volume.systemGrowthReserve(),volume.currentProjectUsageConservativeUpper(),override,
                        Instant.parse(release.observedAtUtc()),Instant.parse(release.reviewAtUtc()))),"shared volume calculation differs");
            }
            for(Path root:roots){var volume=release.volumes().entrySet().stream().filter(entry->pathRoot(entry.getKey()).equals(root.getRoot())).findFirst()
                    .orElseThrow(()->new IOException("output volume lacks exact capacity"));
                require(volume.getValue().thisWritePeak()>=limits.outputAllocationLimitBytes(),"volume peak does not cover whole output bound");}
            check(0);
        }
        private static Path pathRoot(String text){return Path.of(text).toAbsolutePath().normalize().getRoot();}
        private void immutable(FileRef input)throws IOException{
            Path original=path(input.path());require(!original.startsWith(request.outputRoot()),"immutable input overlaps this new guard output");
        }
        private void check(long pending) throws IOException {
            Instant now=Instant.now();
            require(!now.isBefore(Instant.parse(release.observedAtUtc()))&&now.isBefore(limits.deadline())
                    &&now.isBefore(Instant.parse(release.reviewAtUtc())),"full-input capacity window expired or future dated");
            limits.capacityEvidence().verify();release.policyRef().verify();
            for(var volume:release.volumes().entrySet())require(Files.getFileStore(path(volume.getKey())).getUsableSpace()>=volume.getValue().requiredFree(),"current volume reserve unavailable");
            long allocated=0;
            for(OutputScope scope:request.outputScopes()){
                long actual=NativeBridgeRootGate.allocation(List.of(scope.root()),limits.deadline());allocated=Math.addExact(allocated,actual);
                long reserved=request.outputRoot().startsWith(scope.root())?Math.addExact(pending,RESERVE):0;
                require(Math.addExact(actual,reserved)<=scope.allocationLimitBytes(),"one output scope exceeded its own hard partition");
            }
            require(pending>=0&&Math.addExact(Math.addExact(allocated,pending),RESERVE)<=limits.outputAllocationLimitBytes(),"whole build/output/TMP allocation plus terminal reserve exceeded");
        }
        /** Consume only the originally reserved control partition for the terminal, including a real build-partition failure. */
        private void finish(long pending) throws IOException {
            require(pending>0&&pending<=1L<<20,"finite terminal bytes required");limits.capacityEvidence().verify();
            OutputScope scope=request.outputScopes().stream().filter(value->request.outputRoot().startsWith(value.root())).findFirst()
                    .orElseThrow(()->new IOException("original terminal scope missing"));
            long actual=NativeBridgeRootGate.allocation(List.of(scope.root()),limits.deadline());
            require(Math.addExact(actual,pending)<=scope.allocationLimitBytes(),"original reserved terminal partition exhausted");
        }
    }
    public static Terminal execute(FileRef requestRef) throws IOException,InterruptedException {
        Witness requestWitness=checked(requestRef);
        Request request=parse(ControlBuild.strictMapper().readTree(Files.readAllBytes(Path.of(requestRef.path()))));
        SharedSourceFiles.assertUnchanged(requestWitness);
        SharedSourceFiles.plainAncestors(request.outputRoot());
        require(Files.isDirectory(request.outputRoot(),LinkOption.NOFOLLOW_LINKS),"fresh guard output directory must be prepared by caller");
        Path terminalPath=request.outputRoot().resolve("manifest-terminal.json");require(!Files.exists(terminalPath,LinkOption.NOFOLLOW_LINKS),"guard output already used");
        if(request.authority()!=null)try(var entries=Files.list(request.outputRoot())){require(entries.findAny().isEmpty(),"version2 requires fresh empty guard output; UNKNOWN is never replayed");}
        OutputBudget budget=request.authority()==null?null:new OutputBudget(request);
        if(budget!=null){budget.immutable(requestRef);budget.immutable(request.manifestRef());}
        List<Witness> witnesses=new ArrayList<>();int count=0,before=0,after=0;boolean started=false;WindowsJobProcess.CommandResult child=null;FileRef snapshotRef=null;State state=State.REJECTED;String error=null;
        try {
            witnesses.add(requestWitness);witnesses.add(checked(request.manifestRef()));
            List<FileRef> declared=manifest(request);count=declared.size();List<FileRef> all=new ArrayList<>(declared);all.addAll(request.additionalInputs());all.add(request.command().executable());
            if(request.runtimeInventoryRef()!=null)all.addAll(NativeRegistrationRuntimeInventory.verify(request.runtimeInventoryRef()).references());
            Set<String> declaredPaths=new HashSet<>();for(FileRef input:all){String identity=path(input.path()).toString().toLowerCase(Locale.ROOT);require(!identity.startsWith(request.outputRoot().toString().toLowerCase(Locale.ROOT)+"\\"),"immutable input inside mutable guard output");
                if(budget!=null)budget.immutable(input);
                if(!declaredPaths.add(identity)) {FileRef prior=witnesses.stream().map(Witness::source).filter(r->r.path().equalsIgnoreCase(input.path())).findFirst().orElseThrow();require(sameRef(prior,input),"conflicting duplicate input");
                    if(!prior.path().equals(input.path()) && witnesses.stream().noneMatch(w->w.source().path().equals(input.path()))) {
                        Witness alias=checked(input);Witness original=witnesses.stream().filter(w->w.source().equals(prior)).findFirst().orElseThrow();
                        require(original.nativeFile().equals(alias.nativeFile()),"case alias native identity differs");witnesses.add(alias);
                    }
                    continue;}
                witnesses.add(checked(input));}
            for(Witness witness:witnesses)SharedSourceFiles.assertUnchanged(witness);before=witnesses.size();
            if(budget!=null)budget.check(16L<<20);
            Path snapshot=request.outputRoot().resolve("manifest-witnesses.json.gz");
            try(var gzip=new GZIPOutputStream(Files.newOutputStream(snapshot,StandardOpenOption.CREATE_NEW))){gzip.write(ControlBuild.strictMapper().writeValueAsBytes(new Snapshot("xar.full-input-manifest-witnesses/v1",request.machineId(),requestRef,request.manifestRef(),List.copyOf(witnesses))));}snapshotRef=FileRef.measure(snapshot);
            Map<String,String> env=new TreeMap<>(String.CASE_INSENSITIVE_ORDER);env.putAll(System.getenv());env.putAll(request.command().environment());env.put("PYTHONDONTWRITEBYTECODE","1");
            for(String key:List.of("JAVA_TOOL_OPTIONS","JDK_JAVA_OPTIONS","_JAVA_OPTIONS","JDK_JAVAC_OPTIONS"))env.remove(key);
            if(budget!=null)for(String key:List.of("TEMP","TMP","TMPDIR"))env.put(key,System.getProperty("java.io.tmpdir"));
            var spec=new WindowsJobProcess.CommandSpec(Path.of(request.command().executable().path()),request.command().arguments(),request.command().cwd(),env,
                    request.outputRoot().resolve("command.stdout.log"),request.outputRoot().resolve("command.stderr.log"),request.command().memoryLimitBytes());
            try(WindowsJobProcess process=WindowsJobProcess.start(spec,WindowsJobProcess.ConsoleMode.NO_WINDOW)) {
                started=true;long[] next={System.nanoTime()+5_000_000_000L};String[] drift={null};
                Runnable monitor=()->{if(drift[0]!=null)return;if(System.nanoTime()<next[0])return;next[0]=System.nanoTime()+5_000_000_000L;
                    try{if(budget!=null)budget.check(0);
                        for(Witness witness:witnesses){if(budget==null)SharedSourceFiles.assertUnchanged(witness);
                            else require(SharedSourceFiles.nativeFile(path(witness.source().path())).equals(witness.nativeFile()),"native input identity changed while build active");}
                    }catch(IOException failure){drift[0]=failure.toString();process.terminate(125);}};
                Instant commandDeadline=Instant.now().plusSeconds(request.command().timeoutSeconds());
                if(request.authority()!=null&&request.authority().deadline().isBefore(commandDeadline))commandDeadline=request.authority().deadline();
                child=process.await(Duration.ofSeconds(request.command().timeoutSeconds()),commandDeadline,monitor);
                if(drift[0]!=null)throw new IOException("input drift while child active: "+drift[0]);
            }
            for(Witness witness:witnesses){SharedSourceFiles.assertUnchanged(witness);after++;}
            if(request.runtimeInventoryRef()!=null)NativeRegistrationRuntimeInventory.verify(request.runtimeInventoryRef());
            if(budget!=null)budget.check(0);
            require(child.accounting().activeProcesses()==0,"actual Job0 required");
            if(budget!=null)require(child.accounting().memoryLimitBytes()==request.command().memoryLimitBytes(),"actual inner Job memory limit differs from request");
            state=child.passed()?State.PASS:State.RED;
        } catch(IOException|RuntimeException failure) {error=failure.toString();state=started?State.RED:State.REJECTED;}
        Terminal terminal=new Terminal(budget==null?"xar.full-input-manifest-guard-terminal/v1":"xar.full-input-manifest-guard-terminal/v2",request.machineId(),Instant.now().toString(),state,requestRef,request.manifestRef(),count,witnesses.size(),before,after,started,child,snapshotRef,error);
        if(budget!=null){budget.finish(1L<<20);if(child!=null)write(request.outputRoot().resolve("command-result.json"),child);}
        write(terminalPath,terminal);return terminal;
    }
    public static void main(String[]args) throws Exception {
        if(args.length!=3)throw new IllegalArgumentException("REQUEST_PATH EXACT_BYTES SHA256");
        FileRef request=new FileRef(path(args[0]).toString(),Long.parseLong(args[1]),args[2]);
        Terminal terminal=execute(request);System.out.println(ControlBuild.strictMapper().writeValueAsString(terminal));
        if(terminal.status()!=State.PASS)System.exit(1);
    }
}

