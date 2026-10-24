package org.xar.ck3.control.build;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.channels.FileChannel;
import java.nio.channels.FileLock;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.TreeMap;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.build.SharedSourceFiles.Witness;
import org.xar.ck3.control.build.WindowsJobProcess;

/** One shared mechanical command caller. The child has a hard Job; the outer is a reservation. */
public final class SharedOwnedCommand {
    private final SharedOwnedCommandBinding binding;
    private final FileRef bindingRef;
    private final Witness bindingBefore;
    private final Path SOURCE;
    private final String MACHINE;
    private final FileRef STANDING;
    private final FileRef DELIVERY;
    private static final ObjectMapper JSON = ControlBuild.strictMapper();
    private static final Set<String> SPEC_KEYS = Set.of("schema","machine_id","owner","coordinator","slot_id","borrowed_slot_id","run_id",
            "standing_ref","launcher_source_ref","executable","arguments","cwd","environment","inputs","output_root",
            "timeout_seconds","memory_limit_bytes","root_exit_drain_policy","operation_card_ref","temporary_policy");
    public enum Status { PASS, RED, REJECTED }
    public record Outcome(Status status, FileRef terminalRef) {
        public Outcome { if(status==null || terminalRef==null) throw new IllegalArgumentException("Actual terminal outcome required"); }
        public int exitCode() { return status == Status.PASS ? 0 : 1; }
    }
    record BindingEvidence(String schema,String machineId,FileRef bindingRef) { }
    enum TemporaryPolicy { SLOT_PRIVATE, HOST_FIXTURE_32_MIB }
    enum Check { MATCH, FAILED, NOT_REACHED }
    record Request(String schema,String machineId,String owner,String coordinator,String slotId,String borrowedSlotId,String runId,
                   FileRef standingRef,FileRef launcherSourceRef,FileRef operationCardRef,TemporaryPolicy temporaryPolicy,FileRef executable,List<String> arguments,Path cwd,
                   Map<String,String> environment,List<FileRef> inputs,Path outputRoot,long timeoutSeconds,
                   long memoryLimitBytes,WindowsJobProcess.RootExitDrainPolicy rootExitDrainPolicy) { }
    record Slot(String slotId,Path outputRoot,long outputCapBytes,long workerMemoryLimitBytes,
                long outerMemoryBudgetBytes,long timeoutSeconds) { }
    record Outer(String pidDecimal,long reservedMemoryBytes,boolean hardJobEnforced,String scope) { }
    record Terminal(String schema,String machineId,String observedAtUtc,Status status,String owner,String slotId,
                    String borrowedSlotId,FileRef requestRef,FileRef standingRef,FileRef launcherSourceRef,
                    List<FileRef> completeRuntime,Outer outer,boolean childStarted,WindowsJobProcess.CommandResult child,
                    WindowsJobProcess.JobDiagnosticOutcome diagnostic,Check inputPrecheck,Check inputPostcheck,Check runtimePostcheck,
                    String failure,List<Witness> inputBefore,List<String> effectiveArguments,FileRef stdoutRef,
                    FileRef stderrRef,long outputNativeBytesWithDirectoryGuard,int gameRpcCalls,
                    int actualDriverOrSaveBodyReads) { }
    private Request request;
    private FileRef requestRef;
    private Slot primary;
    private Slot borrowed;
    private Instant deadline;
    private List<FileRef> runtime = List.of();
    private final List<Witness> inputBefore = new ArrayList<>();

    private SharedOwnedCommand(FileRef bindingRef,SharedOwnedCommandBinding binding,Witness bindingBefore) throws IOException {
        this.bindingRef=bindingRef; this.binding=binding; this.bindingBefore=bindingBefore; SOURCE=path(binding.launcherSourceRef().path());
        MACHINE=binding.machineId(); STANDING=binding.standingRef(); DELIVERY=binding.deliveryRef();
    }

    /** Runs one exact request in an independently scoped instance. This method never exits the caller JVM. */
    public static Outcome execute(FileRef bindingRef,FileRef requestRef) throws Exception {
        require(bindingRef!=null,"exact binding ref required");
        Witness before=SharedSourceFiles.observe(path(bindingRef.path()));
        SharedOwnedCommandBinding binding=SharedOwnedCommandBinding.read(bindingRef);
        SharedSourceFiles.assertUnchanged(before);
        return new SharedOwnedCommand(bindingRef,binding,before).invoke(requestRef);
    }

    public static void main(String[] args) throws Exception {
        if(args.length!=7 || !args[0].equals("run"))
            throw new IOException("run BINDING_PATH EXACT_BYTES SHA256 SPEC_PATH EXACT_BYTES SHA256 required");
        FileRef bindingRef=cliRef(args[1],args[2],args[3]), requestRef=cliRef(args[4],args[5],args[6]);
        Outcome outcome=execute(bindingRef,requestRef);
        if(outcome.exitCode()!=0) System.exit(outcome.exitCode());
    }

    static FileRef cliRef(String pathText,String bytesText,String sha256) throws IOException {
        final long bytes;
        try { bytes=Long.parseLong(bytesText); } catch(NumberFormatException error) { throw new IOException("Exact reference byte count required",error); }
        require(Long.toString(bytes).equals(bytesText),"canonical reference bytes required");
        return new FileRef(path(pathText).toString(),bytes,sha256);
    }

    private Outcome invoke(FileRef exactRequestRef) throws Exception {
        require(exactRequestRef!=null,"exact request ref required");
        requestRef=exactRequestRef; requestRef.verify(); require(requestRef.bytes()<=1048576,"spec larger than1MiB");
        request=parseRequest(parse(path(requestRef.path()))); authorize();
        List<FileChannel> channels=new ArrayList<>(); List<FileLock> locks=new ArrayList<>();
        try {
            List<Slot> slots=new ArrayList<>(List.of(primary)); if(borrowed!=null) slots.add(borrowed);
            slots.sort(Comparator.comparing(Slot::slotId));
            for(Slot slot:slots) {
                SharedSourceFiles.plainAncestors(slot.outputRoot()); Files.createDirectories(slot.outputRoot());
                FileChannel channel=FileChannel.open(slot.outputRoot().resolve(".shared-owned-command.lock"),StandardOpenOption.CREATE,StandardOpenOption.WRITE);
                channels.add(channel); FileLock lock=channel.tryLock();
                require(lock!=null,"slot already claimed: "+slot.slotId()); locks.add(lock);
            }
            return run();
        } finally {
            for(int index=locks.size()-1;index>=0;index--) locks.get(index).close();
            for(int index=channels.size()-1;index>=0;index--) channels.get(index).close();
        }
    }

    static Request parseRequest(JsonNode value) throws IOException {
        exactKeys(value,SPEC_KEYS); require(text(value,"schema").equals("xar.shared-owned-command-spec/v2"),"spec schema mismatch");
        List<FileRef> inputs=new ArrayList<>();
        for(JsonNode entry:array(value,"inputs")) inputs.add(ref(entry));
        require(inputs.size()<=512,"at most 512 explicit input refs");
        List<String> arguments=texts(array(value,"arguments"));
        require(arguments.size()<=4096,"at most 4096 argv entries");
        Map<String,String> environment=new TreeMap<>(String.CASE_INSENSITIVE_ORDER);
        JsonNode environmentNode=object(value,"environment");
        for(var entry:environmentNode.properties()) {
            require(entry.getValue().isTextual(),"environment values must be strings");
            require(environment.put(entry.getKey(),entry.getValue().textValue())==null,"case-duplicate environment key");
        }
        String borrowedId=nullableText(value,"borrowed_slot_id");
        WindowsJobProcess.RootExitDrainPolicy policy;
        try { policy=WindowsJobProcess.RootExitDrainPolicy.valueOf(text(value,"root_exit_drain_policy")); }
        catch(IllegalArgumentException error) { throw new IOException("unknown typed root exit drain policy",error); }
        return new Request(text(value,"schema"),text(value,"machine_id"),text(value,"owner"),text(value,"coordinator"),
                text(value,"slot_id"),borrowedId,text(value,"run_id"),ref(object(value,"standing_ref")),ref(object(value,"launcher_source_ref")),
                nullableRef(value,"operation_card_ref"),temporaryPolicy(value),ref(object(value,"executable")),arguments,path(text(value,"cwd")),Map.copyOf(environment),List.copyOf(inputs),
                path(text(value,"output_root")),integer(value,"timeout_seconds"),integer(value,"memory_limit_bytes"),policy);
    }

    private void authorize() throws Exception {
        bindingRef.verify();
        require(MACHINE.equals(request.machineId()) && MACHINE.equals(WindowsJobProcess.currentMachineId()),"native machine mismatch");
        equalRef(request.standingRef(),STANDING); STANDING.verify();
        require(path(request.launcherSourceRef().path()).equals(SOURCE),"single shared launcher source required");
        equalRef(request.launcherSourceRef(),binding.launcherSourceRef()); request.launcherSourceRef().verify();
        require(request.owner().matches("/root/[a-z0-9_/-]+"),"canonical Root task owner required");
        JsonNode standing=parse(path(STANDING.path()));
        SharedOwnedCommandBinding.verifyAuthority(standing,binding.standingExpectation(),MACHINE);
        require(path(text(standing,"native_tmp_root")).equals(binding.nativeTemporaryRoot()),"exact approved native tmp root required");
        require(path(text(standing,"private_temporary_aggregate_root")).equals(binding.privateTemporaryAggregateRoot()),"exact standing private temporary aggregate root required");
        deadline=Instant.parse(text(standing,"review_at_utc")); require(Instant.now().isBefore(deadline),"standing runtime expired");
        ref(object(standing,"source_grant_ref")).verify(); ref(object(standing,"capacity_release_ref")).verify();
        require(request.operationCardRef()==null && request.temporaryPolicy()==TemporaryPolicy.SLOT_PRIVATE,
                "packaged ordinary caller requires null operation card and SLOT_PRIVATE");
        primary=findSlot(standing,request.slotId());
        long allowedMemory=primary.workerMemoryLimitBytes();
        if(request.borrowedSlotId()!=null) {
            require(request.coordinator().equals("/root/g2_java_delivery"),"only delivery coordinates a common slot loan");
            require(request.borrowedSlotId().matches("common-[0-3]") && !request.borrowedSlotId().equals(request.slotId()),"one distinct common slot loan required");
            borrowed=findSlot(standing,request.borrowedSlotId());
            allowedMemory=Math.addExact(allowedMemory,Math.addExact(borrowed.workerMemoryLimitBytes(),borrowed.outerMemoryBudgetBytes()));
        }
        require(request.memoryLimitBytes()>0 && request.memoryLimitBytes()<=allowedMemory,"worker memory exceeds its standing slot(s)");
        require(request.timeoutSeconds()>0 && request.timeoutSeconds()<=primary.timeoutSeconds(),"finite timeout exceeds group allowance");
        require(primary.outerMemoryBudgetBytes()==(256L<<20),"expected 256MiB outer reservation");
        require(request.outputRoot().startsWith(primary.outputRoot()) && !request.outputRoot().equals(primary.outputRoot()),"output outside exact slot build root");
        Path relative=primary.outputRoot().relativize(request.outputRoot());
        String ownerStem=request.owner().substring(6).replace('/','_');
        require(relative.getNameCount()==2 && relative.getName(0).toString().equals(ownerStem)
                && relative.getName(1).toString().equals(request.runId())
                && request.runId().matches("[a-z0-9][a-z0-9_-]{0,79}"),"output must be slot/owner/unique run_id");
        SharedSourceFiles.plainAncestors(request.cwd()); require(Files.isDirectory(request.cwd(),LinkOption.NOFOLLOW_LINKS),"ordinary existing cwd required");
        String executableName=path(request.executable().path()).getFileName().toString().toLowerCase(java.util.Locale.ROOT);
        require(!Set.of("powershell.exe","pwsh.exe","cmd.exe","bash.exe","sh.exe","wscript.exe","cscript.exe").contains(executableName),"shell launch is outside mechanical argv scope");
        boolean allowed=false;
        for(JsonNode entry:array(standing,"allowed_executables")) { FileRef pin=ref(entry); if(sameRef(request.executable(),pin)) { pin.verify(); allowed=true; } }
        require(allowed,"exact fresh standing executable required");
        ref(object(standing,"qualified_tools_ref")).verify(); ref(object(standing,"qualified_own_readback_ref")).verify();
        DELIVERY.verify(); JsonNode delivery=parse(path(DELIVERY.path()));
        SharedOwnedCommandBinding.verifyAuthority(delivery,binding.deliveryExpectation(),MACHINE);
        verifyPackagedSource(ref(object(standing,"qualified_tools_ref")));
        List<FileRef> expected=new ArrayList<>();
        for(JsonNode entry:array(standing,"runtime_closure")) { FileRef pin=ref(entry); pin.verify(); expected.add(pin); }
        List<FileRef> delivered=new ArrayList<>();
        for(JsonNode entry:array(delivery,"complete_runtime")) delivered.add(ref(entry));
        expected.sort(Comparator.comparing(FileRef::path)); delivered.sort(Comparator.comparing(FileRef::path));
        require(expected.size()==6 && expected.equals(delivered) && expected.equals(ControlBuild.producerClosure()),"complete exact six-piece accepted runtime required");
        runtime=List.copyOf(expected);
    }

    /** Historical build evidence identifies the archive; the exact fresh standing grants this execution window. */
    private void verifyPackagedSource(FileRef actualRef) throws Exception {
        actualRef.verify();
        Path own=Path.of(SharedOwnedCommand.class.getProtectionDomain().getCodeSource().getLocation().toURI()).toAbsolutePath().normalize();
        Path api=Path.of(ControlBuild.class.getProtectionDomain().getCodeSource().getLocation().toURI()).toAbsolutePath().normalize();
        Path config=Path.of(SharedOwnedCommandBinding.class.getProtectionDomain().getCodeSource().getLocation().toURI()).toAbsolutePath().normalize();
        require(Files.isRegularFile(own) && own.equals(api) && own.equals(config),"shared caller and binding must be in the complete packaged tools runtime");
        // The shared completed reader below enforces its recorded profile: legacy 2 MiB or explicit R2 4 MiB.
        ControlBuild.BuildReceipt actual=ControlBuild.verifiedCompletedReceipt(actualRef);
        require(actual.machineId().equals(MACHINE),"qualified package must match bound machine");
        require(actual.targetKind()==ControlBuild.TargetKind.BUILD_TOOLS_RUNTIME,"qualified build-tools runtime required");
        boolean sourceMatched=false;
        for(FileRef pin:actual.sourcePins()) if(sameRef(pin,binding.launcherSourceRef())) sourceMatched=true;
        require(sourceMatched,"bound launcher source must belong to the accepted complete build source graph");
        require(SOURCE.getFileName().toString().equals("SharedOwnedCommand.java"),"packaged shared source identity required");
        require(Set.copyOf(actual.completeDeployment()).equals(Set.copyOf(ControlBuild.producerClosure())),"accepted package must be this loaded complete runtime");
    }

    private static Slot findSlot(JsonNode standing,String id) throws IOException {
        Slot found=null;
        for(JsonNode value:array(standing,"slots")) if(text(value,"slot_id").equals(id)) {
            require(found==null && bool(value,"serial"),"unique serial slot required");
            found=new Slot(id,path(text(value,"output_root")),integer(value,"output_cap_bytes"),
                    integer(value,"worker_memory_limit_bytes"),integer(value,"outer_memory_budget_bytes"),integer(value,"timeout_seconds"));
        }
        require(found!=null,"unassigned slot id"); return found;
    }

    private Outcome run() throws Exception {
        Path out=request.outputRoot(); SharedSourceFiles.plainAncestors(out);
        require(!Files.exists(out,LinkOption.NOFOLLOW_LINKS),"fresh attempt output required; unknown/finished attempt cannot be replayed");
        Files.createDirectories(out.getParent()); Files.createDirectory(out);
        Path terminalReserve=out.resolve("terminal-reserve.bin"); writeNew(terminalReserve,new byte[65536]);
        writeNew(out.resolve("binding-ref.json"),JSON.writeValueAsBytes(new BindingEvidence("xar.shared-owned-command-binding-evidence/v1",MACHINE,bindingRef)));
        Path temporary=nativeTemporary(); SharedSourceFiles.plainAncestors(temporary); Files.createDirectories(temporary);
        WindowsJobProcess.CommandResult result=null; WindowsJobProcess.JobDiagnosticOutcome diagnostic=null;
        String failure=null; boolean started=false; Check inputPre=Check.NOT_REACHED,inputPost=Check.NOT_REACHED,runtimePost=Check.NOT_REACHED;
        List<String> effectiveArguments=effectiveArguments(temporary);
        Path stdout=out.resolve("stdout.log"),stderr=out.resolve("stderr.log");
        try {
            SharedSourceFiles.assertUnchanged(bindingBefore); inputBefore.add(bindingBefore);
            request.executable().verify(); inputBefore.add(SharedSourceFiles.observe(path(request.executable().path())));
            Set<Path> seen=new HashSet<>(); seen.add(path(request.executable().path()));
            for(FileRef pin:request.inputs()) {
                Path input=path(pin.path()); require(!input.startsWith(out),"input cannot be written inside fresh output");
                require(seen.add(input),"duplicate input ref"); pin.verify(); inputBefore.add(SharedSourceFiles.observe(input));
            }
            inputPre=Check.MATCH; guard();
            Map<String,String> environment=new TreeMap<>(String.CASE_INSENSITIVE_ORDER); environment.putAll(System.getenv());
            environment.remove("JAVA_TOOL_OPTIONS"); environment.remove("JDK_JAVA_OPTIONS"); environment.remove("_JAVA_OPTIONS"); environment.remove("JDK_JAVAC_OPTIONS");
            for(String key:request.environment().keySet()) require(!Set.of("JAVA_TOOL_OPTIONS","JDK_JAVA_OPTIONS","_JAVA_OPTIONS","JDK_JAVAC_OPTIONS").contains(key.toUpperCase(java.util.Locale.ROOT)),"JVM option environment is controlled by shared caller");
            environment.putAll(request.environment()); environment.put("TEMP",temporary.toString()); environment.put("TMP",temporary.toString());
            environment.put("PYTHONDONTWRITEBYTECODE","1");
            var command=new WindowsJobProcess.CommandSpec(path(request.executable().path()),effectiveArguments,request.cwd(),environment,stdout,stderr,request.memoryLimitBytes());
            try(var child=WindowsJobProcess.start(command)) {
                started=true;
                var awaited=child.await(Duration.ofSeconds(request.timeoutSeconds()),deadline,this::periodic,
                        out.resolve("before-cleanup.json"),request.rootExitDrainPolicy());
                result=awaited.commandResult(); diagnostic=awaited.diagnostic();
            }
        } catch(Exception error) { failure=describe(error); if(inputPre!=Check.MATCH) inputPre=Check.FAILED; }
        try { if(inputPre==Check.MATCH) { for(Witness pin:inputBefore) SharedSourceFiles.assertUnchanged(pin); inputPost=Check.MATCH; } }
        catch(Exception error) { inputPost=Check.FAILED; failure=append(failure,"input_postcheck: "+describe(error)); }
        try {
            bindingRef.verify(); requestRef.verify(); request.launcherSourceRef().verify(); STANDING.verify(); DELIVERY.verify();
            for(FileRef pin:runtime) pin.verify(); runtimePost=Check.MATCH;
        } catch(Exception error) { runtimePost=Check.FAILED; failure=append(failure,"runtime_postcheck: "+describe(error)); }
        long outputBytes=-1;
        try { outputBytes=slotAllocated(); require(outputBytes<=primary.outputCapBytes()-65536,"output cap/terminal reserve exceeded"); }
        catch(Exception error) { failure=append(failure,"output_postcheck: "+describe(error)); }
        FileRef stdoutRef=null,stderrRef=null;
        try { if(Files.isRegularFile(stdout)) stdoutRef=FileRef.measure(stdout); if(Files.isRegularFile(stderr)) stderrRef=FileRef.measure(stderr); }
        catch(Exception error) { failure=append(failure,"log_postcheck: "+describe(error)); }
        Instant completedAt=Instant.now();
        if(!completedAt.isBefore(deadline)) { runtimePost=Check.FAILED; failure=append(failure,"standing runtime expired at command completion"); }
        Status status=!started?Status.REJECTED:result!=null && result.passed() && failure==null?Status.PASS:Status.RED;
        Terminal terminal=new Terminal("xar.shared-owned-command-terminal/v2",MACHINE,completedAt.toString(),status,
                request.owner(),request.slotId(),request.borrowedSlotId(),requestRef,STANDING,request.launcherSourceRef(),runtime,
                new Outer(Long.toString(ProcessHandle.current().pid()),primary.outerMemoryBudgetBytes(),false,
                        "Packaged outer JVM is a conservative reservation; no outer hard Job is claimed. Child and descendants are in the hard Job."),
                started,result,diagnostic,inputPre,inputPost,runtimePost,failure,List.copyOf(inputBefore),effectiveArguments,
                stdoutRef,stderrRef,outputBytes,0,0);
        byte[] terminalBytes=JSON.writerWithDefaultPrettyPrinter().writeValueAsBytes(terminal);
        long now=0; boolean censusOk=true;
        try { now=slotAllocated(); } catch(Exception error) { censusOk=false; failure=append(failure,"terminal_census: "+describe(error)); }
        long growth=roundAllocation(terminalBytes.length);
        if(!censusOk || now+growth>primary.outputCapBytes()) {
            terminal=new Terminal(terminal.schema(),terminal.machineId(),terminal.observedAtUtc(),Status.RED,terminal.owner(),terminal.slotId(),
                    terminal.borrowedSlotId(),terminal.requestRef(),terminal.standingRef(),terminal.launcherSourceRef(),terminal.completeRuntime(),
                    terminal.outer(),terminal.childStarted(),terminal.child(),terminal.diagnostic(),terminal.inputPrecheck(),terminal.inputPostcheck(),
                    terminal.runtimePostcheck(),append(terminal.failure(),"full terminal snapshot exceeds output cap; actual child retained in compact terminal"),
                    List.of(),List.of(),terminal.stdoutRef(),terminal.stderrRef(),censusOk?now:-1,0,0);
            terminalBytes=JSON.writeValueAsBytes(terminal); status=Status.RED;
            require(terminalBytes.length<=65536,"compact actual-child terminal exceeds its preallocated64KiB reservation");
        }
        if(!censusOk || now+roundAllocation(terminalBytes.length)>primary.outputCapBytes()) {
            try(FileChannel channel=FileChannel.open(terminalReserve,StandardOpenOption.WRITE)) {
                ByteBuffer buffer=ByteBuffer.wrap(terminalBytes); while(buffer.hasRemaining()) channel.write(buffer);
                channel.truncate(terminalBytes.length); channel.force(true);
            }
            Files.move(terminalReserve,out.resolve("terminal.json"),java.nio.file.StandardCopyOption.ATOMIC_MOVE);
        } else { writeNew(out.resolve("terminal.json"),terminalBytes); }
        try { require(slotAllocated()<=primary.outputCapBytes(),"actual terminal allocation exceeds output cap"); }
        catch(IOException error) {
            status=Status.RED;
            if(Files.exists(terminalReserve,LinkOption.NOFOLLOW_LINKS)) {
                Terminal compact=new Terminal(terminal.schema(),terminal.machineId(),terminal.observedAtUtc(),Status.RED,terminal.owner(),terminal.slotId(),
                        terminal.borrowedSlotId(),terminal.requestRef(),terminal.standingRef(),terminal.launcherSourceRef(),terminal.completeRuntime(),
                        terminal.outer(),terminal.childStarted(),terminal.child(),terminal.diagnostic(),terminal.inputPrecheck(),terminal.inputPostcheck(),
                        terminal.runtimePostcheck(),append(terminal.failure(),"final_cap_observation: "+describe(error)),List.of(),List.of(),
                        terminal.stdoutRef(),terminal.stderrRef(),-1,0,0);
                replaceFromTerminalReserve(terminalReserve,out.resolve("terminal.json"),JSON.writeValueAsBytes(compact));
            }
            System.err.println("FINAL_CAP_OBSERVATION_FAILED actual RED terminal retained: "+describe(error));
        }
        if(Files.exists(terminalReserve,LinkOption.NOFOLLOW_LINKS)) Files.delete(terminalReserve);
        System.out.println("SHARED_COMMAND "+status+" child="+(result==null?"UNAVAILABLE":result.exitCode())+" Job="+(result==null?"UNAVAILABLE":result.accounting().activeProcesses())+" terminal="+out.resolve("terminal.json"));
        return new Outcome(status,FileRef.measure(out.resolve("terminal.json")));
    }

    private List<String> effectiveArguments(Path temporary) throws IOException {
        List<String> result=new ArrayList<>();
        String name=path(request.executable().path()).getFileName().toString().toLowerCase(java.util.Locale.ROOT);
        String prefix=name.equals("javac.exe")?"-J-":name.equals("java.exe")?"-":"";
        if(!prefix.isEmpty()) {
            result.add(prefix+"Djava.io.tmpdir="+temporary); result.add(prefix+"Djna.tmpdir="+binding.nativeTemporaryRoot());
            String xx=prefix+"XX:"; result.add(xx+"ErrorFile="+request.outputRoot().resolve("hs_err_pid%p.log"));
            result.add(xx+"ReplayDataFile="+request.outputRoot().resolve("replay_pid%p.log"));
            result.add(xx+"HeapDumpPath="+request.outputRoot());
        }
        for(String argument:request.arguments()) {
            require(argument.indexOf('\0')<0,"NUL in argv");
            require(!argument.startsWith("-Djava.io.tmpdir=") && !argument.startsWith("-Djna.tmpdir=")
                    && !argument.startsWith("-J-Djava.io.tmpdir=") && !argument.startsWith("-J-Djna.tmpdir="),"temporary roots are bound by the shared caller");
            require(!argument.matches("-J?-?XX:(ErrorFile|ReplayDataFile|HeapDumpPath)=.*"),"JVM crash outputs are bound by the shared caller");
            result.add(argument);
        }
        return List.copyOf(result);
    }
    private void guard() throws Exception {
        require(Instant.now().isBefore(deadline),"standing runtime expired"); bindingRef.verify(); requestRef.verify(); request.launcherSourceRef().verify(); STANDING.verify(); DELIVERY.verify();
        for(Witness pin:inputBefore) SharedSourceFiles.assertUnchanged(pin);
        require(slotAllocated()<=primary.outputCapBytes()-65536,"slot output cap or terminal reserve exceeded");
    }
    private void periodic() { try { guard(); } catch(Exception error) { throw new IllegalStateException(describe(error),error); } }
    private Path nativeTemporary() { return binding.privateTemporaryAggregateRoot().resolve(request.slotId().replace('/','_')).resolve(request.owner().substring(6).replace('/','_')).resolve(request.runId()); }
    private long slotAllocated() throws IOException { return Math.addExact(allocated(primary.outputRoot()),allocated(binding.privateTemporaryAggregateRoot().resolve(request.slotId().replace('/','_')))); }
    static long allocated(Path root) throws IOException {
        if(Files.notExists(root,LinkOption.NOFOLLOW_LINKS)) return 0;
        require(Files.exists(root,LinkOption.NOFOLLOW_LINKS),"owned output root existence unavailable: "+root);
        final long[] measured={0};
        Files.walkFileTree(root,new java.nio.file.SimpleFileVisitor<Path>() {
            @Override public java.nio.file.FileVisitResult preVisitDirectory(Path dir,java.nio.file.attribute.BasicFileAttributes attrs) throws IOException {
                try {
                    if(!plainMutableAncestors(dir)) return java.nio.file.FileVisitResult.SKIP_SUBTREE; require(!attrs.isSymbolicLink() && !attrs.isOther(),"plain owned output directory required: "+dir);
                } catch(IOException error) {
                    if(!dir.equals(root) && Files.notExists(dir,LinkOption.NOFOLLOW_LINKS)) return java.nio.file.FileVisitResult.SKIP_SUBTREE;
                    throw new IOException("owned mutable-output directory metadata failed: "+dir,error);
                }
                measured[0]=Math.addExact(measured[0],4096); return java.nio.file.FileVisitResult.CONTINUE;
            }
            @Override public java.nio.file.FileVisitResult visitFile(Path file,java.nio.file.attribute.BasicFileAttributes attrs) throws IOException {
                try {
                    require(attrs.isRegularFile() && !attrs.isSymbolicLink() && !attrs.isOther(),"plain owned output file required: "+file);
                    measured[0]=Math.addExact(measured[0],mutableFileAllocation(file));
                } catch(IOException error) {
                    if(!Files.notExists(file,LinkOption.NOFOLLOW_LINKS)) throw new IOException("owned mutable-output metadata failed: "+file,error);
                }
                return java.nio.file.FileVisitResult.CONTINUE;
            }
            @Override public java.nio.file.FileVisitResult visitFileFailed(Path file,IOException error) throws IOException {
                if(!file.equals(root) && error instanceof java.nio.file.NoSuchFileException) return java.nio.file.FileVisitResult.CONTINUE;
                throw new IOException("owned output walk failed: "+file,error);
            }
            @Override public java.nio.file.FileVisitResult postVisitDirectory(Path dir,IOException error) throws IOException {
                if(error!=null && (dir.equals(root) || !(error instanceof java.nio.file.NoSuchFileException))) throw new IOException("owned directory walk failed: "+dir,error);
                return java.nio.file.FileVisitResult.CONTINUE;
            }
        });
        return measured[0];
    }
    private static JsonNode parse(Path path) throws IOException { JsonNode value=JSON.readTree(Files.readAllBytes(path)); require(value!=null && value.isObject(),"JSON object required"); return value; }
    private static JsonNode field(JsonNode value,String key) throws IOException { require(value.isObject() && value.has(key),"missing field: "+key); return value.get(key); }
    private static JsonNode object(JsonNode value,String key) throws IOException { JsonNode result=field(value,key); require(result.isObject(),"object required: "+key); return result; }
    private static JsonNode array(JsonNode value,String key) throws IOException { JsonNode result=field(value,key); require(result.isArray(),"array required: "+key); return result; }
    private static String text(JsonNode value,String key) throws IOException { JsonNode result=field(value,key); require(result.isTextual(),"string required: "+key); return result.textValue(); }
    private static String nullableText(JsonNode value,String key) throws IOException { JsonNode result=field(value,key); require(result.isNull() || result.isTextual(),"explicit null/string required: "+key); return result.isNull()?null:result.textValue(); }
    private static long integer(JsonNode value,String key) throws IOException { JsonNode result=field(value,key); require(result.isIntegralNumber() && result.canConvertToLong(),"exact integer required: "+key); return result.longValue(); }
    private static boolean bool(JsonNode value,String key) throws IOException { JsonNode result=field(value,key); require(result.isBoolean(),"boolean required: "+key); return result.booleanValue(); }
    private static List<String> texts(JsonNode array) throws IOException { List<String> result=new ArrayList<>(); for(JsonNode value:array) { require(value.isTextual(),"string argv required"); result.add(value.textValue()); } return List.copyOf(result); }
    private static FileRef ref(JsonNode value) throws IOException { exactKeys(value,Set.of("path","bytes","sha256")); return new FileRef(path(text(value,"path")).toString(),integer(value,"bytes"),text(value,"sha256")); }
    private static Path path(String value) throws IOException { Path path=Path.of(value); require(path.isAbsolute(),"absolute path required"); return path.toAbsolutePath().normalize(); }
    private static void equalRef(FileRef left,FileRef right) throws IOException { require(path(left.path()).equals(path(right.path())) && left.bytes()==right.bytes() && left.sha256().equals(right.sha256()),"exact reference mismatch"); }
    private static void exactKeys(JsonNode value,Set<String> keys) throws IOException { require(value.isObject() && value.size()==keys.size(),"exact object fields required"); for(var item:value.properties()) require(keys.contains(item.getKey()),"unknown field: "+item.getKey()); }
    private static void writeNew(Path target,byte[] data) throws IOException { SharedSourceFiles.plainAncestors(target); try(FileChannel out=FileChannel.open(target,StandardOpenOption.CREATE_NEW,StandardOpenOption.WRITE)) { ByteBuffer bytes=ByteBuffer.wrap(data); while(bytes.hasRemaining()) out.write(bytes); out.force(true); } }
    private static long roundAllocation(long bytes) { return Math.multiplyExact(Math.addExact(bytes,4095)/4096,4096); }
    private static String describe(Exception error) { return error.getClass().getSimpleName()+": "+error.getMessage(); }
    private static String append(String first,String next) { return first==null?next:first+"; "+next; }
    private static void require(boolean condition,String message) throws IOException { if(!condition) throw new IOException(message); }

    private static FileRef nullableRef(JsonNode value,String key) throws IOException { JsonNode item=field(value,key); return item.isNull()?null:ref(item); }
    private static TemporaryPolicy temporaryPolicy(JsonNode value) throws IOException { try { return TemporaryPolicy.valueOf(text(value,"temporary_policy")); } catch(IllegalArgumentException error) { throw new IOException("unknown typed temporary policy",error); } }
    private static boolean sameRef(FileRef a,FileRef b) throws IOException { return path(a.path()).equals(path(b.path())) && a.bytes()==b.bytes() && a.sha256().equals(b.sha256()); }

    /** Mutable output only: native missing2/3 can race CREATE_NEW/replace; reparse and access failures remain fatal. */
    private static boolean plainMutableAncestors(Path path) throws IOException {
        Path current=path.toAbsolutePath().normalize();
        while(current!=null) {
            int attrs=com.sun.jna.platform.win32.Kernel32.INSTANCE.GetFileAttributes(extendedWindowsPath(current));
            if(attrs==-1) {
                int error=com.sun.jna.Native.getLastError();
                if(error==2 || error==3) return false;
                throw new IOException("mutable path attribute Win32="+error+" path="+current);
            }
            require((attrs&0x400)==0,"mutable output reparse path rejected: "+current);
            current=current.getParent();
        }
        return true;
    }
    private static long mutableFileAllocation(Path file) throws IOException {
        IOException last=null;
        for(int attempt=0;attempt<4;attempt++) {
            if(!plainMutableAncestors(file)) return 0;
            try { return nativeMutableAllocation(file); }
            catch(IOException error) { last=error; if(!plainMutableAncestors(file)) return 0; }
        }
        throw new IOException("bounded mutable metadata retries exhausted: "+file,last);
    }


    private static final class MutableApi {
        private static final SharedSourceFiles.AttributeApi VALUE=com.sun.jna.Native.load("kernel32",SharedSourceFiles.AttributeApi.class);
    }
    private static String extendedWindowsPath(Path path) throws IOException {
        require(path.isAbsolute(),"absolute mutable Windows path required"); String value=path.toAbsolutePath().normalize().toString();
        if(value.startsWith("\\\\?\\")) return value;
        if(value.startsWith("\\\\")) return "\\\\?\\UNC\\"+value.substring(2);
        require(value.matches("[A-Za-z]:\\\\.*"),"canonical Windows drive or UNC path required");
        return "\\\\?\\"+value;
    }
    private static long nativeMutableAllocation(Path file) throws IOException {
        var handle=com.sun.jna.platform.win32.Kernel32.INSTANCE.CreateFile(extendedWindowsPath(file),0x80,7,null,3,0x00200000,null);
        if(com.sun.jna.platform.win32.WinBase.INVALID_HANDLE_VALUE.equals(handle)) {
            int error=com.sun.jna.Native.getLastError(); if(error==2 || error==3) return 0;
            throw new IOException("mutable extended metadata open Win32="+error+" path="+file);
        }
        try(com.sun.jna.Memory basic=new com.sun.jna.Memory(40); com.sun.jna.Memory standard=new com.sun.jna.Memory(24)) {
            require(MutableApi.VALUE.GetFileInformationByHandleEx(handle,0,basic,40)
                    && MutableApi.VALUE.GetFileInformationByHandleEx(handle,1,standard,24),"mutable extended metadata query failed: "+file);
            require((basic.getInt(32)&0x400)==0 && standard.getByte(21)==0,"mutable native regular non-reparse file required: "+file);
            long allocated=standard.getLong(0); require(allocated>=0,"nonnegative native allocation required: "+file); return allocated;
        } finally { require(com.sun.jna.platform.win32.Kernel32.INSTANCE.CloseHandle(handle),"mutable metadata handle close failed: "+file); }
    }


    private static void replaceFromTerminalReserve(Path reserve,Path target,byte[] bytes) throws IOException {
        require(bytes.length<=65536,"compact actual terminal exceeds preallocated64KiB");
        try(FileChannel channel=FileChannel.open(reserve,StandardOpenOption.WRITE)) {
            ByteBuffer buffer=ByteBuffer.wrap(bytes); while(buffer.hasRemaining()) channel.write(buffer);
            channel.truncate(bytes.length); channel.force(true);
        }
        Files.move(reserve,target,java.nio.file.StandardCopyOption.ATOMIC_MOVE,java.nio.file.StandardCopyOption.REPLACE_EXISTING);
    }

}
