package org.xar.ck3.control.build;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import org.xar.ck3.control.build.ControlBuild.FileRef;

/** Fixed read-only Git CLI observations through the existing suspended-child Windows Job owner.
 * No loose/pack/index parsing, Git mutation, JVM launch or invented clean state.
 * The caller must separately admit the existing command directory and complete finite stdout/stderr quote.
 */
public final class FormalReleaseGit {
    public enum Phase { PREPARE,BEFORE_WRITE,AFTER_READBACK }
    public enum Operation { ROOT,HEAD,STATUS,TAGS,REGISTRY_ID,REGISTRY_TYPE,REGISTRY_BLOB,HEAD_END }
    public static final long STDERR_MAXIMUM=16384;
    private FormalReleaseGit(){ }
    public record Execution(String machineId,String reviewAtUtc,Path repository,FileRef gitExecutable,
            Path commandRoot,long memoryLimitBytes){
        public Execution{
            if(machineId==null||!machineId.matches("[a-z0-9][a-z0-9-]{0,63}")||machineId.equals("unknown"))
                throw new IllegalArgumentException("exact actual Git machine required");
            Instant.parse(reviewAtUtc);Objects.requireNonNull(gitExecutable);
            for(Path path:List.of(repository,commandRoot))if(!path.isAbsolute()||!path.normalize().equals(path)||path.getParent()==null)
                throw new IllegalArgumentException("normalized absolute Git paths required");
            if(repository.startsWith(commandRoot)||commandRoot.startsWith(repository)
                    ||memoryLimitBytes<64L<<20||memoryLimitBytes>512L<<20)
                throw new IllegalArgumentException("disjoint admitted command directory and bounded Git Job memory required");
            if(!Path.of(gitExecutable.path()).getFileName().toString().equalsIgnoreCase("git.exe"))
                throw new IllegalArgumentException("actual pinned Git CLI executable required");
        }
    }
    /** Exact runtime log reservation; it grants no storage or process authority. */
    public record CaptureOutput(Phase phase,Operation operation,Path stdout,Path stderr,long maximumStdoutBytes,long maximumStderrBytes){
        public CaptureOutput{Objects.requireNonNull(phase);Objects.requireNonNull(operation);Objects.requireNonNull(stdout);Objects.requireNonNull(stderr);}
        public long maximumLogicalBytes(){return Math.addExact(maximumStdoutBytes,maximumStderrBytes);}
    }
    public record CommandEvidence(Phase phase,Operation operation,List<String> arguments,
            WindowsJobProcess.CommandResult terminal,FileRef stdout,FileRef stderr){
        public CommandEvidence{Objects.requireNonNull(phase);Objects.requireNonNull(operation);arguments=List.copyOf(arguments);
            Objects.requireNonNull(terminal);Objects.requireNonNull(stdout);Objects.requireNonNull(stderr);
            if(!terminal.passed())throw new IllegalArgumentException("actual exit0 Job0 terminal required");}
    }
    public static final class Snapshot {
        private final String head;private final byte[] registry;private final String status;private final List<String> tags;
        private final List<CommandEvidence> evidence;
        private Snapshot(String head,byte[] registry,String status,List<String> tags,List<CommandEvidence> evidence){
            this.head=head;this.registry=registry.clone();this.status=status;this.tags=List.copyOf(tags);this.evidence=List.copyOf(evidence);
        }
        public String head(){return head;}
        public byte[] registryBytes(){return registry.clone();}
        public String observedStatus(){return status;}
        public List<String> observedTagsAtHead(){return tags;}
        public List<CommandEvidence> evidence(){return evidence;}
    }
    public static final class Session implements AutoCloseable {
        private final Execution execution;private final SharedSourceFiles.Witness executable;
        private final ProjectStoragePolicy.Configuration storage;
        private final SharedSourceFiles.DirectoryIdentity repositoryIdentity,commandRootIdentity;
        private final List<SharedSourceFiles.Witness> captured=new ArrayList<>();private int nextPhase;private boolean closed;
        private Session(Execution execution,SharedSourceFiles.Witness executable,SharedSourceFiles.DirectoryIdentity repositoryIdentity,
                SharedSourceFiles.DirectoryIdentity commandRootIdentity,ProjectStoragePolicy.Configuration storage){
            this.storage=storage;this.execution=execution;this.executable=executable;this.repositoryIdentity=repositoryIdentity;this.commandRootIdentity=commandRootIdentity;
        }
        public Path repository(){return execution.repository();}
        public String machineId(){return execution.machineId();}
        public Execution execution(){return execution;}
        /** Every command already closed its sole Job; this marks the read session terminal. */
        @Override public synchronized void close(){closed=true;}
        public List<CaptureOutput> captureQuote(){return quote(execution);}
        public void verifyCapturedOriginals()throws IOException{
            if(closed)throw new IOException("Git read session is closed");
            requireCurrent(execution);
            if(!storage.equals(explicitStorage(System::getProperty,System::getenv)))throw new IOException("actual explicit project storage policy changed during Git session");
            requireOutput(storage,execution.commandRoot());SharedSourceFiles.assertUnchanged(executable);
            if(!SharedSourceFiles.nativeDirectory(execution.repository()).equals(repositoryIdentity)
                    ||!SharedSourceFiles.nativeDirectory(execution.commandRoot()).equals(commandRootIdentity))
                throw new IOException("actual Git repository or admitted command directory identity drifted");
            for(var original:captured)SharedSourceFiles.assertUnchanged(original);
        }
        /** Current physical volume policy guard; no new child, directory or write. */
        public void requireOutputRoot(Path output)throws IOException{
            verifyCapturedOriginals();requireOutput(storage,output);
        }
        public synchronized Snapshot capture(FormalReleaseProducer.Mode mode,String version,Phase phase)throws IOException,InterruptedException{
            Objects.requireNonNull(mode);Objects.requireNonNull(phase);
            if(phase.ordinal()!=nextPhase)throw new IOException("Git phases must execute once in PREPARE, BEFORE_WRITE, AFTER_READBACK order");
            nextPhase++;verifyCapturedOriginals();var evidence=new ArrayList<CommandEvidence>();
            byte[] root=run(Operation.ROOT,phase,evidence),headBytes=run(Operation.HEAD,phase,evidence),
                    statusBytes=run(Operation.STATUS,phase,evidence),tagsBytes=run(Operation.TAGS,phase,evidence),
                    registryId=run(Operation.REGISTRY_ID,phase,evidence),registryType=run(Operation.REGISTRY_TYPE,phase,evidence),
                    registry=run(Operation.REGISTRY_BLOB,phase,evidence),headEnd=run(Operation.HEAD_END,phase,evidence);
            Path observedRoot=Path.of(line(root)).toRealPath();
            if(!observedRoot.equals(execution.repository().toRealPath()))throw new IOException("actual Git top-level differs from the requested original");
            String head=line(headBytes);
            if(!head.matches("[0-9a-f]{40}")||!head.equals(line(headEnd)))throw new IOException("actual full Git HEAD changed during fixed read commands");
            if(!line(registryId).equals(FormalReleaseDescriptor.REGISTRY_BLOB)||!line(registryType).equals("blob"))
                throw new IOException("actual HEAD native compatibility registry object differs");
            FormalReleaseDescriptor.requireRegistry(registry);
            String status=FormalReleaseDescriptor.decode(statusBytes);
            List<String> tags=FormalReleaseDescriptor.decode(tagsBytes).lines().filter(value->!value.isEmpty()).toList();
            if(mode==FormalReleaseProducer.Mode.PUBLISH_RELEASE){
                if(!status.isEmpty())throw new IOException("publication release requires actual clean worktree");
                if(!tags.contains("v"+version))throw new IOException("publication release requires descriptor v"+version+" tag on actual HEAD");
            }
            verifyCapturedOriginals();return new Snapshot(head,registry,status,tags,evidence);
        }
        public void requireSame(Snapshot original,FormalReleaseProducer.Mode mode,String version,Phase phase)throws IOException,InterruptedException{
            Objects.requireNonNull(original);Snapshot actual=capture(mode,version,phase);
            if(!original.head().equals(actual.head())||!Arrays.equals(original.registryBytes(),actual.registryBytes()))
                throw new IOException("actual Git HEAD/registry changed after private release preparation");
        }
        private byte[] run(Operation operation,Phase phase,List<CommandEvidence> evidence)throws IOException,InterruptedException{
            verifyCapturedOriginals();CaptureOutput output=quote(execution).stream().filter(row->row.phase()==phase&&row.operation()==operation).findFirst().orElseThrow();
            for(Path target:List.of(output.stdout(),output.stderr()))if(Files.exists(target,LinkOption.NOFOLLOW_LINKS))
                throw new IOException("Git capture targets are CREATE_NEW-only immutable originals");
            List<String> arguments=arguments(execution.repository(),operation);
            var environment=new java.util.TreeMap<String,String>(System.getenv());
            environment.keySet().removeIf(key->key.toUpperCase(java.util.Locale.ROOT).startsWith("GIT_"));
            environment.put("GIT_OPTIONAL_LOCKS","0");environment.put("GIT_TERMINAL_PROMPT","0");
            environment.put("GIT_PAGER","cat");environment.put("LC_ALL","C");environment.put("LANG","C");
            var specification=new WindowsJobProcess.CommandSpec(Path.of(execution.gitExecutable().path()),arguments,
                    execution.repository(),environment,output.stdout(),output.stderr(),execution.memoryLimitBytes());
            WindowsJobProcess.CommandResult terminal;
            try(var child=WindowsJobProcess.start(specification)){
                try{terminal=child.await(Duration.ofSeconds(30),Instant.parse(execution.reviewAtUtc()),()->{
                    try{verifyCapturedOriginals();requireBound(output.stdout(),output.maximumStdoutBytes());requireBound(output.stderr(),output.maximumStderrBytes());}
                    catch(IOException invalid){throw new CaptureFailure(invalid);}
                });}catch(CaptureFailure invalid){throw invalid.original;}
            }
            requireBound(output.stdout(),output.maximumStdoutBytes());requireBound(output.stderr(),output.maximumStderrBytes());
            var stdout=SharedSourceFiles.observe(output.stdout());var stderr=SharedSourceFiles.observe(output.stderr());
            captured.add(stdout);captured.add(stderr);
            if(!terminal.passed())throw new IOException("actual managed Git command did not terminate exit0/Job0: "+operation+" / "+terminal);
            byte[] bytes=Files.readAllBytes(output.stdout());SharedSourceFiles.assertUnchanged(stdout);SharedSourceFiles.assertUnchanged(stderr);
            evidence.add(new CommandEvidence(phase,operation,arguments,terminal,stdout.source(),stderr.source()));verifyCapturedOriginals();return bytes;
        }
    }
    private static final class CaptureFailure extends RuntimeException {
        private static final long serialVersionUID=1L;
        private final IOException original;private CaptureFailure(IOException original){super(original);this.original=original;}
    }
    public static Session open(Execution execution)throws IOException{
        Objects.requireNonNull(execution);requireCurrent(execution);
        var storage=explicitStorage(System::getProperty,System::getenv);requireOutput(storage,execution.commandRoot());
        SharedSourceFiles.plainAncestors(execution.repository());SharedSourceFiles.plainAncestors(execution.commandRoot());
        if(!Files.isDirectory(execution.repository(),LinkOption.NOFOLLOW_LINKS)||!Files.isDirectory(execution.commandRoot(),LinkOption.NOFOLLOW_LINKS))
            throw new IOException("existing actual repository and separately admitted empty command directory required");
        try(var entries=Files.list(execution.commandRoot())){if(entries.findAny().isPresent())throw new IOException("fresh Git command directory required");}
        var executable=SharedSourceFiles.observe(Path.of(execution.gitExecutable().path()));
        if(!executable.source().equals(execution.gitExecutable()))throw new IOException("actual Git CLI source pin differs");
        return new Session(execution,executable,SharedSourceFiles.nativeDirectory(execution.repository()),SharedSourceFiles.nativeDirectory(execution.commandRoot()),storage);
    }
    public static List<CaptureOutput> quote(Execution execution){
        var result=new ArrayList<CaptureOutput>();
        for(Phase phase:Phase.values())for(Operation operation:Operation.values()){
            String stem=phase.name().toLowerCase(java.util.Locale.ROOT)+"-"+operation.name().toLowerCase(java.util.Locale.ROOT);
            result.add(new CaptureOutput(phase,operation,execution.commandRoot().resolve(stem+".stdout"),execution.commandRoot().resolve(stem+".stderr"),
                    maximum(operation),STDERR_MAXIMUM));
        }
        return List.copyOf(result);
    }
    static List<String> arguments(Path repository,Operation operation){
        var result=new ArrayList<String>(List.of("--no-pager","--no-optional-locks","-c","core.fsmonitor=false","-C",repository.toString()));
        String registry="HEAD:"+FormalReleaseDescriptor.REGISTRY_PATH;
        result.addAll(switch(operation){
            case ROOT->List.of("rev-parse","--show-toplevel");
            case HEAD,HEAD_END->List.of("rev-parse","--verify","HEAD");
            case STATUS->List.of("status","--porcelain=v1","--untracked-files=all","--ignore-submodules=none");
            case TAGS->List.of("tag","--points-at","HEAD");
            case REGISTRY_ID->List.of("rev-parse","--verify",registry);
            case REGISTRY_TYPE->List.of("cat-file","-t",registry);
            case REGISTRY_BLOB->List.of("cat-file","blob",registry);
        });
        return List.copyOf(result);
    }
    private static long maximum(Operation operation){return switch(operation){case STATUS->1L<<20;case TAGS->65536;case REGISTRY_BLOB->65536;default->4096;};}
    private static String line(byte[] bytes)throws IOException{
        String value=FormalReleaseDescriptor.decode(bytes);if(value.endsWith("\n"))value=value.substring(0,value.length()-1);
        if(value.endsWith("\r"))value=value.substring(0,value.length()-1);
        if(value.isEmpty()||value.indexOf('\n')>=0||value.indexOf('\r')>=0||value.indexOf('\0')>=0)throw new IOException("one exact nonempty Git output line required");
        return value;
    }
    private static void requireBound(Path target,long maximum)throws IOException{
        if(Files.exists(target,LinkOption.NOFOLLOW_LINKS)){
            SharedSourceFiles.plainAncestors(target);
            if(!Files.isRegularFile(target,LinkOption.NOFOLLOW_LINKS)||Files.size(target)>maximum)throw new IOException("managed Git capture exceeds admitted finite output");
        }
    }
    /** Explicit process configuration avoids the older Git-local ProcessBuilder fallback entirely. */
    static ProjectStoragePolicy.Configuration explicitStorage(java.util.function.Function<String,String> properties,
            java.util.function.Function<String,String> environment)throws IOException{
        Objects.requireNonNull(properties);Objects.requireNonNull(environment);
        var observed=new java.util.HashMap<String,String>();
        for(String key:List.of(ProjectStoragePolicy.FORBID_SYSTEM_VOLUME_BULK,ProjectStoragePolicy.PROJECT_STORAGE_ROOT,ProjectStoragePolicy.AUTOPLAYER_STATE_DIR)){
            String value=properties.apply(key);if(value==null)value=environment.apply(key);
            if(value!=null)observed.put(key,value);
        }
        if(!observed.containsKey(ProjectStoragePolicy.FORBID_SYSTEM_VOLUME_BULK))
            throw new IOException("explicit project system-volume policy required for managed Git outputs");
        return ProjectStoragePolicy.configuration(observed::get,key->null);
    }
    private static void requireOutput(ProjectStoragePolicy.Configuration storage,Path output)throws IOException{
        if(!storage.forbidSystemVolumeBulk())return;
        String system=System.getenv("SystemRoot");
        if(system==null||system.isBlank())throw new IOException("actual SystemRoot required for physical output volume guard");
        ProjectStoragePolicy.requireBulkOutput(storage,output,Path.of(system));
    }
    private static void requireCurrent(Execution execution)throws IOException{
        if(!execution.machineId().equals(WindowsJobProcess.currentMachineId())||!Instant.parse(execution.reviewAtUtc()).isAfter(Instant.now()))
            throw new IOException("actual current machine and unexpired Git command execution required");
    }
}

