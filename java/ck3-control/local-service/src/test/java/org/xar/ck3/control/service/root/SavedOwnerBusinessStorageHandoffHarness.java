package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.io.InputStream;
import java.nio.channels.FileChannel;
import java.nio.channels.FileLock;
import java.nio.channels.OverlappingFileLockException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.UUID;
import java.util.concurrent.atomic.AtomicReference;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.ProjectStoragePolicy;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.build.runtime.HostMode;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.FreshContinuityGenesis;
import org.xar.ck3.control.continuity.OriginalWindowReducer;
import org.xar.ck3.control.continuity.writer.ContinuityWriter;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;

/**
 * Independent, finite, no-Game target for the JDK Attach storage-only rehearsal.
 * Uses the normal initializer, ordinary storage guard and public Core producer.
 * The external attach command/agent supplies its own exact grant and immutable receipt.
 * This target never loads an agent, constructs a Prepared/ManagedGameSession, or publishes a business edge.
 */
public final class SavedOwnerBusinessStorageHandoffHarness {
    private static final int MAXIMUM_PROPERTIES_BYTES=128*1024;
    private static final long FIXTURE_STORAGE_CAP=8L*1024*1024;
    private static final Set<String> MODES=Set.of("positive","wrong-head","ambiguous","expired","no-close");
    private static final List<RootApplicationAssembly.Core> RETAINED_CORES=new ArrayList<>();
    private static RootRuntimeStorageGuard retainedGuard;
    private SavedOwnerBusinessStorageHandoffHarness(){ }

    private record Original(SharedSourceFiles.Witness witness,byte[] bytes){
        private Original {bytes=bytes.clone();}
        private void verify()throws IOException {
            SharedSourceFiles.assertUnchanged(witness);
            require(Arrays.equals(bytes,Files.readAllBytes(Path.of(witness.source().path()))),"original fixture bytes changed");
            SharedSourceFiles.assertUnchanged(witness);
        }
    }
    /** Byte-range-locked empty files permit metadata queries; zero logical length uniquely fixes their empty body. */
    private record EmptyLock(Path path,SharedSourceFiles.NativeFile original){
        private void verify()throws IOException {
            require(original.logicalBytes()==0&&original.linkCount()==1&&original.equals(SharedSourceFiles.nativeFile(path)),
                    "original empty lock native identity, metadata or unique empty body changed");
        }
    }
    private record Fixture(RootApplicationConfiguration configuration,RootRuntimeStorageGuard guard,
            RootApplicationAssembly.Core core,WriterContracts.Head head,Path allocationLock,
            List<Original> originals,List<EmptyLock> emptyLocks,SharedSourceFiles.DirectoryIdentity eventsIdentity){ }

    /** Arguments: positive|wrong-head|ambiguous|expired|no-close, absent fixture root, timeout seconds 1..120. */
    public static void main(String... arguments)throws Exception {
        if(arguments.length!=3||!MODES.contains(arguments[0]))throw new IllegalArgumentException(
                "mode, absent no-Game fixture root and finite timeout seconds 1..120 required");
        if(!com.sun.jna.Platform.isWindows())throw new IOException("actual Windows allocation lock and old Core/JNA are required");
        String mode=arguments[0];Path root=Path.of(arguments[1]);
        require(root.isAbsolute()&&root.normalize().equals(root)&&root.getParent()!=null,"canonical fresh fixture root required");
        long seconds=Long.parseLong(arguments[2]);require(seconds>=1&&seconds<=120,"finite rehearsal timeout 1..120 seconds required");
        ProjectStoragePolicy.requireBulkOutput(root);SharedSourceFiles.plainAncestors(root);
        require(!Files.exists(root,LinkOption.NOFOLLOW_LINKS),"rehearsal fixture root must be absent");
        Files.createDirectory(root);
        Instant started=Instant.now(),deadline=started.plusSeconds(seconds);String operation="rehearsal-"+UUID.randomUUID();
        Path ready=root.resolve("ready.properties"),receipt=root.resolve("agent-receipt.properties"),result=root.resolve("harness-result.properties");
        Throwable primary=null;Fixture fixture=null;
        try {
            fixture=create(root,mode.equals("ambiguous"));requireBefore(deadline);
            Fixture actual=fixture;assertLock(actual.allocationLock(),false);
            actual.guard().requireCompleteAdmission();assertOriginals(actual);
            Map<String,String> fields=ready(operation,mode,started,deadline,actual,receipt);
            publish(ready,fields);
            System.out.println("READY "+ready);System.out.flush();
            awaitReceipt(receipt,deadline);
            Map<String,String> returned=readProperties(receipt);
            require(operation.equals(returned.get("operation_id")),"agent receipt belongs to another operation");
            require(Long.toString(ProcessHandle.current().pid()).equals(returned.get("target_pid")),"agent receipt belongs to another JVM");
            boolean expectedClosed=mode.equals("positive");
            require((expectedClosed?"GUARD_RELEASED_OWNER_RETAINED":"REJECTED_NO_CLOSE").equals(returned.get("status")),"agent did not report the expected exact terminal");
            require((expectedClosed?"1":"0").equals(returned.get("close_called")),"agent close invocation count differs from the expected exact terminal");
            verifyOutcome(actual,expectedClosed);
            var completed=new LinkedHashMap<String,String>();completed.put("schema","xar.java-storage-handoff-rehearsal-result/v1");
            completed.put("purpose","NO_GAME_REHEARSAL");completed.put("operation_id",operation);completed.put("mode",mode);
            completed.put("status","VERIFIED");completed.put("target_pid",Long.toString(ProcessHandle.current().pid()));
            completed.put("expected_guard_closed",Boolean.toString(expectedClosed));completed.put("allocation_lock_available",Boolean.toString(expectedClosed));
            completed.put("strong_real_core_count",Integer.toString(RETAINED_CORES.size()));
            completed.put("canonical_head_sequence",Long.toString(actual.head().state().sequence()));completed.put("canonical_head_digest",actual.head().digest());
            completed.put("canonical_originals_unchanged","true");completed.put("canonical_events_empty","true");
            completed.put("game_objects_created","0");completed.put("business_edges_published","0");
            completed.put("observed_at_utc",Instant.now().toString());completed.put("elapsed_millis",Long.toString(Duration.between(started,Instant.now()).toMillis()));
            addFile(completed,"agent_receipt",receipt);publish(result,completed);
            System.out.println("VERIFIED "+result);System.out.flush();
        }catch(Exception|Error failure){
            primary=failure;
            var failed=new LinkedHashMap<String,String>();failed.put("schema","xar.java-storage-handoff-rehearsal-result/v1");
            failed.put("purpose","NO_GAME_REHEARSAL");failed.put("operation_id",operation);failed.put("mode",mode);failed.put("status","FAILED");
            failed.put("exception",failure.getClass().getName());failed.put("detail",singleLine(failure.toString()));failed.put("observed_at_utc",Instant.now().toString());
            try{publish(result,failed);}catch(IOException|RuntimeException recording){failure.addSuppressed(recording);}
            throw failure;
        }finally {
            Throwable closing=null;
            for(int index=RETAINED_CORES.size()-1;index>=0;index--){
                var core=RETAINED_CORES.get(index);
                try{core.close();core.closeCompletion().toCompletableFuture().join();}
                catch(RuntimeException|Error failure){if(closing==null)closing=failure;else if(closing!=failure)closing.addSuppressed(failure);}
            }
            if(retainedGuard!=null)try{retainedGuard.close();}catch(IOException|RuntimeException failure){if(closing==null)closing=failure;else if(closing!=failure)closing.addSuppressed(failure);}
            if(closing!=null){if(primary!=null)primary.addSuppressed(closing);else if(closing instanceof Exception exception)throw exception;else throw (Error)closing;}
        }
    }

    private static Fixture create(Path root,boolean ambiguous)throws Exception {
        require(RETAINED_CORES.isEmpty()&&retainedGuard==null,"one fresh child JVM per rehearsal case required");
        Path control=Files.createDirectory(root.resolve("control")),managed=Files.createDirectory(root.resolve("managed"));
        Path ledger=Files.createDirectory(managed.resolve("continuity")),archive=Files.createDirectory(ledger.resolve("archive"));
        String machine=WindowsJobProcess.currentMachineId();
        var plan=new FreshContinuityGenesis.Plan(machine,1,OriginalWindowReducer.TARGET_DAYS);
        byte[] planBytes=FreshContinuityGenesis.encode(plan);Path originalPlan=control.resolve("fresh-genesis-request.json");
        Files.write(originalPlan,planBytes,StandardOpenOption.CREATE_NEW);ExactRef planRef=exact(originalPlan);
        var initial=new WriterContracts.InitialLayout(ledger.resolve("ROOT-CONTINUITY-WINDOW.json"),ledger.resolve("anchor.json"),machine);
        var bound=new AtomicReference<RootApplicationAssembly.Core>();
        RootRuntimeStorageGuard.WriterAccess access=()->{
            var core=bound.get();if(core==null)throw new IOException("no writer exists before normal genesis/Core construction");return core.writer();
        };
        RootRuntimeStorageGuard guard=RootRuntimeStorageGuard.ordinary(initial,archive,access,List.of(managed),FIXTURE_STORAGE_CAP,Clock.systemUTC());
        retainedGuard=guard;
        var initialized=ContinuityWriter.initializeFresh(plan,planRef,initial,guard);
        require(initialized.initialHead().state().sequence()==0&&initialized.initialHead().state().status()==ContinuityState.Status.AWAITING_INITIAL_ENTRY,
                "sole fresh initializer did not produce an empty awaiting-initial-entry ledger");
        require(!initialized.initialHead().state().toJson().has("game_binding"),"no-Game genesis unexpectedly contains a Game binding");
        Path noLaunch=control.resolve("no-game-launch-data.json");
        Files.writeString(noLaunch,"{\"purpose\":\"NO_GAME_REHEARSAL\",\"launch_permission\":false}",StandardCharsets.UTF_8,StandardOpenOption.CREATE_NEW);
        var configuration=new RootApplicationConfiguration(machine,HostMode.MCP_STDIO,Instant.now().plusSeconds(120),exact(noLaunch),
                initialized.layout(),List.of(planRef),archive,FIXTURE_STORAGE_CAP);
        var core=RootApplicationAssembly.open(configuration,Clock.systemUTC(),List.of(),Optional.empty(),guard);
        RETAINED_CORES.add(core);bound.set(core);guard.requireCompleteAdmission();
        WriterContracts.Head head=core.writer().locked(same->same.head());
        require(head.digest().equals(initialized.initialHead().digest())&&head.state().sequence()==0,"normal Core changed the sole initializer head");
        if(ambiguous){
            var second=RootApplicationAssembly.open(configuration,Clock.systemUTC(),List.of(),Optional.empty(),guard);
            RETAINED_CORES.add(second);
            require(second!=core&&second.writer()!=core.writer()&&second.storageGuard()==guard,"ambiguous case needs two normally constructed real Cores");
            var other=second.writer().locked(same->same.head());
            require(other.digest().equals(head.digest())&&other.state().sequence()==head.state().sequence(),"ambiguous Cores do not match the actual same canonical head");
        }
        List<Path> allocation;
        try(var files=Files.list(ledger)){
            allocation=files.filter(path->path.getFileName().toString().startsWith(".runtime-storage-")&&path.getFileName().toString().endsWith(".lock")).toList();
        }
        require(allocation.size()==1,"normal storage producer must have exactly one allocation owner file");
        Path allocationLock=allocation.getFirst();require(Files.size(allocationLock)==0,"original allocation owner file must remain empty");
        var originals=new ArrayList<Original>();
        for(Path path:List.of(initial.snapshot(),initial.anchor(),originalPlan,noLaunch)){
            var witness=SharedSourceFiles.observe(path);byte[] bytes=Files.readAllBytes(path);SharedSourceFiles.assertUnchanged(witness);originals.add(new Original(witness,bytes));
        }
        var emptyLocks=new ArrayList<EmptyLock>();
        for(Path path:List.of(initial.lock(),allocationLock)){
            var original=new EmptyLock(path,SharedSourceFiles.nativeFile(path));original.verify();emptyLocks.add(original);
        }
        assertEmpty(initialized.layout().events());
        return new Fixture(configuration,guard,core,head,allocationLock,List.copyOf(originals),List.copyOf(emptyLocks),SharedSourceFiles.nativeDirectory(initialized.layout().events()));
    }

    private static Map<String,String> ready(String operation,String mode,Instant started,Instant deadline,Fixture actual,Path output)throws Exception {
        var fields=new LinkedHashMap<String,String>();fields.put("schema","xar.java-storage-handoff-rehearsal-ready/v1");
        fields.put("purpose","NO_GAME_REHEARSAL");fields.put("operation_id",operation);fields.put("mode",mode);
        fields.put("issued_at_utc",started.toString());fields.put("deadline_utc",deadline.toString());
        var self=WindowsJobProcess.exactProcess(ProcessHandle.current().pid());
        fields.put("target_pid",Long.toString(self.pid()));fields.put("target_birth_filetime",self.creationFiletimeDecimal());
        fields.put("java_executable",self.executable());
        fields.put("java_home",Path.of(System.getProperty("java.home")).toAbsolutePath().normalize().toString());
        fields.put("java_runtime_version",System.getProperty("java.runtime.version"));
        fields.put("expected_sequence",Long.toString(actual.head().state().sequence()));fields.put("expected_digest",actual.head().digest());
        fields.put("writer_lock",actual.configuration().ledger().lock().toString());fields.put("allocation_lock",actual.allocationLock().toString());
        fields.put("output",output.toString());fields.put("rehearsal_main",SavedOwnerBusinessStorageHandoffHarness.class.getName());
        fields.put("strong_real_core_count",Integer.toString(RETAINED_CORES.size()));fields.put("game_objects_created","0");
        addFile(fields,"snapshot",actual.configuration().ledger().snapshot());
        addFile(fields,"anchor",Path.of(actual.configuration().ledger().anchor().path()));
        for(Class<?> type:List.of(RootApplicationAssembly.Core.class,RootRuntimeStorageGuard.class,ContinuityWriter.class,
                WindowsJobProcess.class,com.sun.jna.Native.class,SavedOwnerBusinessStorageHandoffHarness.class))
            addClass(fields,"class."+type.getName(),type);
        return fields;
    }
    private static void verifyOutcome(Fixture fixture,boolean closed)throws Exception {
        boolean admitted;
        try{fixture.guard().requireCompleteAdmission();admitted=true;}
        catch(IOException denied){admitted=false;if(!closed)throw denied;}
        require(admitted!=closed,"public original guard admission does not match the expected storage-only close");
        assertLock(fixture.allocationLock(),closed);assertOriginals(fixture);
        WriterContracts.Head after=fixture.core().writer().locked(same->same.head());
        require(after.state().sequence()==fixture.head().state().sequence()&&after.digest().equals(fixture.head().digest()),"attach changed the canonical no-Game head");
    }
    private static void assertOriginals(Fixture actual)throws IOException {
        for(Original original:actual.originals())original.verify();
        for(EmptyLock lock:actual.emptyLocks())lock.verify();
        require(actual.eventsIdentity().equals(SharedSourceFiles.nativeDirectory(actual.configuration().ledger().events())),"canonical events directory identity changed");
        assertEmpty(actual.configuration().ledger().events());
    }
    private static void assertEmpty(Path directory)throws IOException {
        try(var children=Files.list(directory)){require(children.findAny().isEmpty(),"no-Game rehearsal published a canonical event");}
    }
    /** Real original allocation region; OPEN_EXISTING/WRITE/tryLock never writes a byte. */
    private static void assertLock(Path path,boolean available)throws IOException {
        boolean actual=false;
        try(var channel=FileChannel.open(path,StandardOpenOption.WRITE)){
            try(FileLock lock=channel.tryLock()){actual=lock!=null;}
            catch(OverlappingFileLockException held){actual=false;}
        }
        require(actual==available,"actual allocation lock availability differs from the expected guard lifetime");
    }
    private static void awaitReceipt(Path path,Instant deadline)throws IOException,InterruptedException {
        while(!Files.exists(path,LinkOption.NOFOLLOW_LINKS)){
            requireBefore(deadline);Thread.sleep(Math.min(50,Math.max(1,Duration.between(Instant.now(),deadline).toMillis())));
        }
        requireBefore(deadline);SharedSourceFiles.plainAncestors(path);
    }
    private static Map<String,String> readProperties(Path path)throws IOException {
        byte[] bytes=readBounded(path,MAXIMUM_PROPERTIES_BYTES);String text=new String(bytes,StandardCharsets.UTF_8);
        require(Arrays.equals(bytes,text.getBytes(StandardCharsets.UTF_8)),"receipt is not exact UTF-8");
        var values=new LinkedHashMap<String,String>();
        for(String line:text.split("\\n",-1)){
            if(line.isEmpty())continue;require(!line.endsWith("\r"),"canonical LF properties required");int split=line.indexOf('=');
            require(split>0,"agent receipt requires explicit key=value fields");String key=line.substring(0,split),value=line.substring(split+1);
            require(key.matches("[A-Za-z][A-Za-z0-9_.$]*")&&values.putIfAbsent(key,value)==null,"agent receipt field is invalid or duplicated");
        }
        require(!values.isEmpty(),"empty agent receipt cannot complete the rehearsal");return Map.copyOf(values);
    }
    private static void addFile(Map<String,String> fields,String name,Path path)throws IOException {
        ControlBuild.FileRef file=ControlBuild.FileRef.measure(path);fields.put(name+".path",file.path());
        fields.put(name+".bytes",Long.toString(file.bytes()));fields.put(name+".sha256",file.sha256());
    }
    private static void addClass(Map<String,String> fields,String name,Class<?> type)throws Exception {
        var source=type.getProtectionDomain().getCodeSource();require(source!=null,"actual qualified class has no CodeSource");
        String resource="/"+type.getName().replace('.','/')+".class";byte[] bytes;
        try(InputStream input=type.getResourceAsStream(resource)){
            require(input!=null,"actual qualified class resource is absent");bytes=input.readNBytes(2*1024*1024+1);
        }
        require(bytes.length>0&&bytes.length<=2*1024*1024,"bounded actual qualified class resource required");
        fields.put(name+".location",source.getLocation().toURI().toString());fields.put(name+".bytes",Integer.toString(bytes.length));
        fields.put(name+".sha256",org.xar.ck3.control.application.driver.DriverJson.sha256(bytes));
    }
    private static ExactRef exact(Path path)throws IOException {var ref=ControlBuild.FileRef.measure(path);return new ExactRef(ref.path(),ref.bytes(),ref.sha256());}
    private static byte[] readBounded(Path path,int maximum)throws IOException {
        byte[] bytes;try(InputStream input=Files.newInputStream(path)){bytes=input.readNBytes(maximum+1);}
        require(bytes.length>0&&bytes.length<=maximum,"bounded nonempty receipt required");return bytes;
    }
    private static void publish(Path path,Map<String,String> values)throws IOException {
        var body=new StringBuilder();for(var field:values.entrySet()){
            require(field.getKey().matches("[A-Za-z][A-Za-z0-9_.$]*")&&!field.getValue().contains("\n")&&!field.getValue().contains("\r"),"single-line canonical properties required");
            body.append(field.getKey()).append('=').append(field.getValue()).append('\n');
        }
        byte[] bytes=body.toString().getBytes(StandardCharsets.UTF_8);require(bytes.length<=MAXIMUM_PROPERTIES_BYTES,"bounded rehearsal receipt required");
        Files.write(path,bytes,StandardOpenOption.CREATE_NEW);
    }
    private static String singleLine(String value){String text=value.replace('\n',' ').replace('\r',' ');return text.substring(0,Math.min(4096,text.length()));}
    private static void requireBefore(Instant deadline)throws IOException {require(Instant.now().isBefore(deadline),"finite no-Game rehearsal deadline expired");}
    private static void require(boolean condition,String message)throws IOException {if(!condition)throw new IOException(message);}
}
