package org.xar.ck3.control.service.root;

import static org.xar.ck3.control.service.root.RootBootstrapProtocol.*;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.TreeMap;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.CiBootstrap;
import org.xar.ck3.control.build.ProjectStoragePolicy;
import org.xar.ck3.control.build.RootBootstrapSessionScope;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.service.root.RootBootstrapProtocol.*;
import org.xar.ck3.control.service.root.RootProfileBootstrapInputs.Created;

/** Finite Shared-owned duplex controller. The independent issuer and the original phase writer keep their authority.
 * An attempted issuer write is never repeated, including when no completion was observed. No Game admission is granted. */
public final class RootProfileBootstrapSession {
    private RootProfileBootstrapSession(){ }
    static final int SESSION_REQUEST_BYTES=1<<20;
    public record Request(String schema,String machineId,String deadline,Mode mode,FileRef bootstrapRequest,
            RootBootstrapRuntime.Request runtime,String controlRoot,String issuerReplyRoot,
            SharedSourceFiles.DirectoryIdentity issuerReplyDirectory) {
        public Request {
            require("xar.java-root-bootstrap-session/v1".equals(schema),"session schema");instant(deadline);
            Objects.requireNonNull(machineId);Objects.requireNonNull(mode);Objects.requireNonNull(bootstrapRequest);Objects.requireNonNull(runtime);
            Objects.requireNonNull(issuerReplyDirectory);absolute(controlRoot);absolute(issuerReplyRoot);
            require(bootstrapRequest.bytes()>0&&bootstrapRequest.bytes()<=65536,"bounded actual bootstrap request required");
        }
        public long controlCap(){return mode==Mode.NORMAL_EXIT?48L<<20:mode==Mode.PROFILE?36L<<20:24L<<20;}
    }
    public enum Status { COMPLETE_NO_GAME_ADMISSION,REJECTED_BEFORE_SEND,UNKNOWN }
    private record StorageConfiguration(String forbidSystemVolumeBulk,String preferredRoot) { }
    public enum PhaseState { AWAITING_QUOTE,AWAITING_ISSUER,SEND_ATTEMPTED,REPLY_SENT,CREATED }
    public record WriteObservation(long bytesWritten,WindowsJobProcess.ProcessIdentity identity,String sessionNonce) {
        public WriteObservation {Objects.requireNonNull(identity);require(bytesWritten>0&&sessionNonce!=null&&sessionNonce.matches("[0-9a-f]{64}"),"actual pipe write observation required");}
    }
    public record Progress(String phase,PhaseState state,FileRef quote,WriteObservation writeReceipt,List<Created> created) {
        public Progress {created=List.copyOf(created);}
    }
    public record PhaseEvidence(String phase,PhaseState state,FileRef quote,WriteObservation writeReceipt,FileRef createdEvidence) { }
    public record Terminal(String schema,String machineId,Status status,FileRef sessionRequest,String deadline,
            WindowsJobProcess.ProcessIdentity child,String sessionNonce,List<PhaseEvidence> phases,
            WindowsJobProcess.AwaitResult actualExit,RootBootstrapSessionScope.ChildCompletion childCompletion,String failure) {
        public Terminal {
            require("xar.java-root-bootstrap-session-terminal/v1".equals(schema),"terminal schema");
            Objects.requireNonNull(machineId);Objects.requireNonNull(status);Objects.requireNonNull(sessionRequest);instant(deadline);phases=List.copyOf(phases);
            require((child==null)==(sessionNonce==null),"child identity and nonce must be present together");
            if(sessionNonce!=null)require(sessionNonce.matches("[0-9a-f]{64}"),"actual child nonce required");
            if(status==Status.COMPLETE_NO_GAME_ADMISSION)require(child!=null&&actualExit!=null&&actualExit.commandResult().passed()&&childCompletion!=null&&failure==null&&!phases.isEmpty(),"completed actual child and readback required");
        }
    }
    @FunctionalInterface public interface Issuer {IssuerReply await(IssuerQuote original,Instant deadline)throws Exception;}

    /** Exact eight-argument parent route or four-argument child route. Only the parent delegates to OwnedStdio. */
    public static void main(String[] args){
        try{
            if(args.length==4&&args[0].equals("child")){child(cliRef(args,1));return;}
            if(args.length!=8||!args[0].equals("run"))throw new IOException("run SESSION_PATH BYTES SHA BINDING_PATH BYTES SHA SHARED_SPEC_PATH | child SESSION_PATH BYTES SHA");
            FileRef original=cliRef(args,1),binding=cliRef(args,4);Request request=read(original,SESSION_REQUEST_BYTES,Request.class);
            RootBootstrapRuntime.verifyParent(request.runtime());
            var retained=new ArrayList<>(RootBootstrapRuntime.retained(request.runtime()));retained.add(request.bootstrapRequest());
            retained.addAll(producerInputs(request));
            var scope=RootBootstrapSessionScope.open(original,binding,Path.of(args[7]).toAbsolutePath().normalize(),
                    Path.of(request.controlRoot()),Instant.parse(request.deadline()),retained,List.of(args),request.runtime().serviceBuild());
            Terminal terminal=run(original,request,scope,fileIssuer(request));
            RootBootstrapProtocol.emit(terminal);if(terminal.status()!=Status.COMPLETE_NO_GAME_ADMISSION)System.exit(2);
        }catch(Exception failure){System.err.println("BOOTSTRAP_SESSION_UNAVAILABLE: "+failure);System.exit(2);}
    }
    private static void child(FileRef original)throws Exception {
        Request request=read(original,SESSION_REQUEST_BYTES,Request.class);current(request);
        var held=SharedSourceFiles.observe(Path.of(original.path()));
        var origins=RootBootstrapRuntime.observeInChild(request.runtime(),request.mode());
        original.verify();SharedSourceFiles.assertUnchanged(held);
        RootBootstrapProtocol.emit(new Origin("xar.java-root-bootstrap-child-origins/v1",request.mode(),request.machineId(),original,origins,RootBootstrapRuntime.observeCarrier(request.runtime())));
        FileRef bootstrap=request.bootstrapRequest();
        RootProfileBootstrapCommand.main(new String[]{request.mode().name(),bootstrap.path(),Long.toString(bootstrap.bytes()),bootstrap.sha256()});
    }
    static Terminal run(FileRef original,Request request,WindowsJobProcess.StdioGuard outerScope,Issuer issuer)throws Exception {
        Objects.requireNonNull(outerScope);Objects.requireNonNull(issuer);current(request);
        if(!read(original,SESSION_REQUEST_BYTES,Request.class).equals(request))throw new IOException("session request differs from exact original");
        RootBootstrapRuntime.verify(request.runtime(),request.mode());outerScope.verify();
        Path root=Path.of(request.controlRoot());SharedSourceFiles.plainAncestors(root);
        if(Files.exists(root,LinkOption.NOFOLLOW_LINKS))throw new IOException("Session output already exists; UNKNOWN or completed sessions cannot replay");
        StorageConfiguration storage=storageConfiguration();storage(root);Files.createDirectory(root);prepareGitRoot(request,root,outerScope);Path scratch=root.resolve("scratch");Files.createDirectory(scratch);
        Path nativeTmp=scratch.resolve("native");Files.createDirectory(nativeTmp);
        var held=new ArrayList<SharedSourceFiles.Witness>();
        var pins=new java.util.LinkedHashSet<>(RootBootstrapRuntime.retained(request.runtime()));pins.add(original);pins.add(request.bootstrapRequest());pins.addAll(producerInputs(request));
        for(FileRef ref:pins){var witness=SharedSourceFiles.observe(Path.of(ref.path()));if(!witness.source().equals(ref))throw new IOException("Session retained input drift");held.add(witness);}
        Path stderr=root.resolve("stderr.log");
        WindowsJobProcess.StdioGuard guard=()->{
            outerScope.verify();current(request);storage(root);
            if(!storage.equals(storageConfiguration()))throw new IOException("captured explicit project storage configuration drifted");
            for(var witness:held)SharedSourceFiles.assertUnchanged(witness);
            if(!SharedSourceFiles.nativeDirectory(Path.of(request.issuerReplyRoot())).equals(request.issuerReplyDirectory()))throw new IOException("independent issuer reply directory identity drift");
            if(size(stderr)>(1L<<20)||RootBootstrapSessionScope.allocated(root,scratch)>(2L<<20)||allocated(root)>request.controlCap()-65536)
                throw new IOException("Session stderr, scratch or native control sub-budget exceeded");
        };
        guard.verify();
        var launch=prepareChild(request,original,root,scratch,nativeTmp,guard);
        try(launch){
        for(FileRef ref:launch.inputs())if(pins.add(ref)){
            var witness=SharedSourceFiles.observe(Path.of(ref.path()));if(!witness.source().equals(ref))throw new IOException("sole engine input drift");held.add(witness);
        }
        WindowsJobProcess.StdioGuard ownedGuard=()->{launch.requireCurrent();guard.verify();};
        Map<String,String> environment=new TreeMap<>(String.CASE_INSENSITIVE_ORDER);environment.putAll(System.getenv());
        for(String name:List.of("JAVA_TOOL_OPTIONS","JDK_JAVA_OPTIONS","_JAVA_OPTIONS","JDK_JAVAC_OPTIONS","CLASSPATH"))environment.remove(name);
        for(String name:List.of("TEMP","TMP","TMPDIR","RUNNER_TEMP"))environment.put(name,scratch.toString());
        var command=new WindowsJobProcess.CommandSpec(Path.of(request.runtime().javaExecutable().path()),launch.arguments(),root,environment,
                root.resolve("stdout.log"),stderr,1L<<30);
        var spec=new WindowsJobProcess.OwnedStdioSpec(command,WindowsJobProcess.ConsoleMode.NO_WINDOW,request.runtime().javaExecutable(),
                List.copyOf(pins),Instant.parse(request.deadline()),FRAME_BYTES,request.mode().sentBytes(),request.mode().receivedBytes(),ownedGuard);
        var progress=new ArrayList<Progress>();WindowsJobProcess.AwaitResult exit=null;
        WindowsJobProcess.ProcessIdentity identity=null;String nonce=null,failure=null;boolean attempted=false;Status status=Status.REJECTED_BEFORE_SEND;
        RootBootstrapSessionScope.ChildCompletion completion=null;
        RootBootstrapDuplex duplex=null;
        try(var io=WindowsJobProcess.startOwnedStdio(spec)){
            launch.attach(io);
            identity=io.identity();nonce=io.sessionNonce();long sequence=0;
            try{
                var arrival=io.readLine(spec.deadline());sequence=arrival(arrival,io,sequence);
                Origin origin=line(arrival.rawBytes(),Origin.class);
                if(origin.mode()!=request.mode()||!origin.machineId().equals(request.machineId())||!origin.request().equals(original))throw new IOException("actual child origin header mismatch");
                RootBootstrapRuntime.verifyObservation(request.runtime(),request.mode(),origin.classes());
                RootBootstrapRuntime.verifyCarrier(request.runtime(),origin.carrier());
                writeNew(root.resolve("child-origins.json"),encode(origin,65536),guard,request);
                duplex=new RootBootstrapDuplex(request.mode(),io,ownedGuard,sequence);
                duplex.exchange(new RootBootstrapDuplex.Handler(){
                    @Override public FileRef authorize(String phase,WindowsJobProcess.Arrival frame,Quote quote)throws Exception {
                        verifyQuote(request,phase,quote);int index=progress.size();
                        Path quotePath=root.resolve("phase-"+index+"-quote.json");writeNew(quotePath,trim(frame.rawBytes()),guard,request);
                        FileRef quoteRef=FileRef.measure(quotePath);progress.add(new Progress(phase,PhaseState.AWAITING_ISSUER,quoteRef,null,List.of()));
                        IssuerQuote envelope=new IssuerQuote("xar.java-root-bootstrap-issuer-quote/v1",request.mode(),phase,original,quoteRef,
                                io.identity(),io.sessionNonce(),frame.sequence(),request.deadline());
                        writeNew(root.resolve("phase-"+index+"-issuer-quote.json"),encode(envelope,65536),guard,request);
                        IssuerReply reply=awaitIssuer(issuer,envelope,spec.deadline(),ownedGuard);ownedGuard.verify();
                        if(!reply.original().equals(envelope))throw new IOException("issuer reply is not for this original mode/phase/arrival");
                        reply.binding().verify();writeNew(root.resolve("phase-"+index+"-issuer-reply.json"),encode(reply,65536),guard,request);
                        return reply.binding();
                    }
                    @Override public void beforeSend(String phase,FileRef binding)throws Exception {
                        int index=progress.size()-1;var prior=progress.get(index);
                        progress.set(index,new Progress(phase,PhaseState.SEND_ATTEMPTED,prior.quote(),null,List.of()));
                        writeNew(root.resolve("phase-"+index+"-send-attempt.json"),encode(progress.get(index),65536),guard,request);
                    }
                    @Override public void sent(String phase,WindowsJobProcess.WriteReceipt receipt)throws Exception {
                        int index=progress.size()-1;var prior=progress.get(index);
                        progress.set(index,new Progress(phase,PhaseState.REPLY_SENT,prior.quote(),
                                new WriteObservation(receipt.bytesWritten(),receipt.identity(),receipt.sessionNonce()),List.of()));
                        writeNew(root.resolve("phase-"+index+"-write-receipt.json"),encode(progress.get(index),65536),guard,request);
                    }
                    @Override public void created(String phase,WindowsJobProcess.Arrival frame,Quote quote,Stage created)throws Exception {
                        verifyStage(quote,created);int index=progress.size()-1;var prior=progress.get(index);
                        progress.set(index,new Progress(phase,PhaseState.CREATED,prior.quote(),prior.writeReceipt(),created.created()));
                        writeNew(root.resolve("phase-"+index+"-created.json"),trim(frame.rawBytes()),guard,request);
                    }
                });
                attempted=duplex.sendAttempted();arrival=duplex.next();verifyFinal(request,progress,arrival.rawBytes());
                writeNew(root.resolve("final-originals.json"),trim(arrival.rawBytes()),guard,request);
                exit=io.awaitExit(root.resolve("job-diagnostic.json"));guard.verify();
                if(!exit.commandResult().passed())throw new IOException("original child exit/Job settlement failed");
                completion=launch.completed(io,exit);ownedGuard.verify();
                status=Status.COMPLETE_NO_GAME_ADMISSION;
            }catch(Exception invalid){attempted=attempted||(duplex!=null&&duplex.sendAttempted());failure=invalid.toString();status=attempted?Status.UNKNOWN:Status.REJECTED_BEFORE_SEND;
                try{if(exit==null)exit=io.awaitExit(root.resolve("job-diagnostic.json"));}catch(Exception settlement){failure+="; settlement="+settlement;}
                if(exit==null)status=Status.UNKNOWN;
            }
        }catch(Exception invalid){failure=invalid.toString();status=attempted||identity!=null?Status.UNKNOWN:Status.REJECTED_BEFORE_SEND;}
        var evidence=new ArrayList<PhaseEvidence>();
        for(int i=0;i<progress.size();i++){
            var phase=progress.get(i);Path path=root.resolve("phase-"+i+"-created.json");FileRef created=null;
            if(Files.isRegularFile(path,LinkOption.NOFOLLOW_LINKS))created=FileRef.measure(path);
            evidence.add(new PhaseEvidence(phase.phase(),phase.state(),phase.quote(),phase.writeReceipt(),created));
        }
        var terminal=new Terminal("xar.java-root-bootstrap-session-terminal/v1",request.machineId(),status,original,request.deadline(),identity,nonce,evidence,exit,completion,failure);
        // Preserve the terminal even when the operational deadline/guard expired. The original Shared cap retains its reserved 64KiB.
        byte[] bytes=encode(terminal,65536);if(allocated(root)+rounded(bytes.length)>request.controlCap())throw new IOException("terminal reserve unavailable; retain original audit as UNKNOWN");
        Files.write(root.resolve("terminal.json"),bytes,StandardOpenOption.CREATE_NEW);return terminal;
        }
    }
    static List<String> startupOptions(Path scratch,Path nativeTmp)throws IOException {
        var storage=storageConfiguration();
        var args=new ArrayList<String>(List.of("-Xms32m","-Xmx512m","-XX:MaxMetaspaceSize=192m","-XX:ReservedCodeCacheSize=96m",
                "-DXAR_PROJECT_FORBID_SYSTEM_VOLUME_BULK="+storage.forbidSystemVolumeBulk(),"-DXAR_PROJECT_STORAGE_ROOT="+storage.preferredRoot(),
                "-Djava.io.tmpdir="+scratch,"-Djna.tmpdir="+nativeTmp,"-XX:ErrorFile="+scratch.resolve("hs-error-%p.log"),
                "-XX:ReplayDataFile="+scratch.resolve("replay-%p.log"),"-XX:HeapDumpPath="+scratch.resolve("heap.hprof"),
                "-XX:-HeapDumpOnOutOfMemoryError"));
        for(String argument:args)if(argument.chars().anyMatch(c->c<32||c>126))throw new IOException("this direct pinned Java stdio route requires ASCII argv; non-ASCII needs the existing sole UTF8 engine");
        return List.copyOf(args);
    }
    private static RootBootstrapSessionScope.ChildLaunch prepareChild(Request request,FileRef original,Path root,
            Path scratch,Path nativeTmp,WindowsJobProcess.StdioGuard guard)throws IOException {
        var classpath=new ArrayList<CiBootstrap.JavaUtf8Invocation.ClasspathPin>();
        for(FileRef ref:request.runtime().classpath())classpath.add(CiBootstrap.JavaUtf8Invocation.captureClasspath(Path.of(ref.path())));
        FileRef main=RootBootstrapRuntime.provider(request.runtime().classpath(),RootProfileBootstrapSession.class.getName());
        var origin=classpath.stream().filter(pin->Path.of(pin.path()).equals(Path.of(main.path()))).findFirst().orElseThrow(()->new IOException("actual Session main archive absent from qualified target roots"));
        var target=new CiBootstrap.JavaUtf8Invocation.ClassTarget(RootProfileBootstrapSession.class.getName(),origin,classpath);
        return RootBootstrapSessionScope.prepareChild(target,carrier(request.runtime()),startupOptions(scratch,nativeTmp),
                 List.of("child",original.path(),Long.toString(original.bytes()),original.sha256()),root,Path.of(request.runtime().javaExecutable().path()),guard,request.controlCap());
    }
    static CiBootstrap.JavaUtf8Invocation.ClassCarrier carrier(RootBootstrapRuntime.Request runtime)throws IOException {
        var roots=new ArrayList<CiBootstrap.JavaUtf8Invocation.ClasspathPin>();
        for(FileRef ref:ControlBuild.verifiedCompletedReceipt(runtime.toolsBuild()).completeDeployment())if(ref.path().endsWith(".jar"))roots.add(CiBootstrap.JavaUtf8Invocation.captureClasspath(Path.of(ref.path())));
        return new CiBootstrap.JavaUtf8Invocation.ClassCarrier(roots);
    }
    static void verifyChildCompletion(FileRef original,Request request,Terminal terminal)throws IOException {
        var completion=terminal.childCompletion();Path root=Path.of(request.controlRoot()).resolve("child-engine");
        if(completion==null||!Path.of(completion.envelope().path()).equals(root.resolve("child-invocation.bin"))
                ||!Path.of(completion.preparation().path()).equals(root.resolve("java-utf8-prepared.bin"))
                ||!Path.of(completion.nativeEvidence().path()).equals(root.resolve("native-sources.json"))
                ||!completion.retirement().identity().equals(terminal.child())||!completion.retirement().sessionNonce().equals(terminal.sessionNonce())
                ||!completion.retirement().machineId().equals(request.machineId()))throw new IOException("actual original child engine/evidence/retirement binding differs");
        var publication=new CiBootstrap.JavaUtf8Invocation.Publication(CiBootstrap.JavaUtf8Invocation.captureFile(Path.of(completion.envelope().path())));
        var logical=CiBootstrap.JavaUtf8Invocation.read(publication);
        if(!(logical.target() instanceof CiBootstrap.JavaUtf8Invocation.ClassTarget target)
                ||!target.mainClass().equals(RootProfileBootstrapSession.class.getName())||!logical.properties().isEmpty()
                ||!logical.arguments().equals(List.of("child",original.path(),Long.toString(original.bytes()),original.sha256()))
                ||!Path.of(logical.evidenceRoot().path()).equals(root))throw new IOException("actual child envelope selects another logical target/request");
        var expected=new ArrayList<CiBootstrap.JavaUtf8Invocation.ClasspathPin>();
        for(FileRef archive:request.runtime().classpath())expected.add(CiBootstrap.JavaUtf8Invocation.captureClasspath(Path.of(archive.path())));
        FileRef main=RootBootstrapRuntime.provider(request.runtime().classpath(),RootProfileBootstrapSession.class.getName());
        if(!target.classpath().equals(expected)||!Path.of(target.mainOrigin().path()).equals(Path.of(main.path())))throw new IOException("actual child envelope differs from qualified complete target deployment");
        var nativeEvidence=RootBootstrapSessionScope.verifyChildCompletion(completion,carrier(request.runtime()));
        if(!nativeEvidence.terminal().equals(terminal.actualExit().commandResult()))throw new IOException("actual native source evidence differs from original Session exit");
    }
    private static IssuerReply awaitIssuer(Issuer issuer,IssuerQuote original,Instant deadline,WindowsJobProcess.StdioGuard guard)throws Exception {
        var future=new java.util.concurrent.FutureTask<IssuerReply>(()->issuer.await(original,deadline));Thread.ofVirtual().start(future);
        try{while(true){guard.verify();long remaining=java.time.Duration.between(Instant.now(),deadline).toMillis();
            if(remaining<=0)throw new IOException("independent issuer deadline expired");
            try{return future.get(Math.min(25,remaining),java.util.concurrent.TimeUnit.MILLISECONDS);}
            catch(java.util.concurrent.TimeoutException pending){/* Keep original resource guards live while the issuer works. */}
        }}finally{future.cancel(true);}
    }
    static void verifyQuote(Request request,String phase,Quote quote)throws IOException {
        if(!quote.phase().equals(phase)||!quote.machineId().equals(request.machineId())||Instant.parse(quote.reviewAtUtc()).isAfter(Instant.parse(request.deadline()))
                ||(request.mode()==Mode.FORMAL_RELEASE)!=quote.schema().equals("xar.java-root-bootstrap-formal-release-phase-quote/v2"))throw new IOException("child phase quote differs from fixed mode/order/window");
        Path asset=Path.of(quote.assetRoot()),controls=Path.of(request.controlRoot()).getParent(),replies=Path.of(request.issuerReplyRoot());
        if(overlap(asset,controls)||overlap(asset,replies)||overlap(controls,replies))throw new IOException("assets, original Shared controls and independent replies must be disjoint");
    }
    static void verifyStage(Quote quote,Stage stage)throws IOException {
        // Both plans retain earlier profile assets; the current writer creates only its explicit new outputs.
        var writes=switch(quote.phase()){
            case "PROFILE_ENVIRONMENT"->quote.outputs().stream().filter(output->output.kind()==RootBootstrapOutputContract.Kind.PROFILE_ENVIRONMENT).toList();
            case "NORMAL_EXIT_INVENTORY_AND_PROJECTION"->quote.outputs().stream().filter(output->output.kind()==RootBootstrapOutputContract.Kind.NORMAL_EXIT_SOURCE_INVENTORY
                    ||output.kind()==RootBootstrapOutputContract.Kind.NORMAL_EXIT_PROFILE_PROJECTION).toList();
            default->quote.outputs();
        };
        if(writes.isEmpty()||stage.created().size()!=writes.size()||stage.accounting().status()!=RootBootstrapOutputGuard.Status.ADMITTED
                ||stage.accounting().unresolvedPeakBytes()!=0||stage.accounting().completedOutputs()!=quote.outputs().size())throw new IOException("original writer did not confirm complete bounded stage");
        for(var output:quote.outputs())new FileRef(Path.of(quote.assetRoot()).resolve(output.fileName()).toString(),output.bytes(),output.sha256()).verify();
        for(int i=0;i<stage.created().size();i++){
            var output=writes.get(i);var created=stage.created().get(i);var ref=created.original();
            if(created.kind()!=output.kind()||!Path.of(ref.path()).equals(Path.of(quote.assetRoot()).resolve(output.fileName()))
                    ||ref.bytes()!=output.bytes()||!ref.sha256().equals(output.sha256())||!SharedSourceFiles.nativeFile(Path.of(ref.path())).equals(created.nativeFile()))throw new IOException("created original differs from actual producer quote");ref.verify();
        }
    }
    static void verifyFinal(Request request,List<Progress> progress,byte[] raw)throws IOException {
        var node=org.xar.ck3.control.contracts.StrictJson.parse(trim(raw),FRAME_BYTES-1);
        String expected=switch(request.mode()){
            case PROFILE->"PROFILE_INPUTS_CREATED_NO_GAME_ADMISSION";
            case FORMAL_RELEASE->"FORMAL_RELEASE_STAGING_CREATED_NO_UPLOAD_OR_GAME_ADMISSION";
            case ORIGINAL_DRIVER_RUN_PROFILE->"ORIGINAL_DRIVER_RUN_PROFILE_CREATED_NO_GAME_ADMISSION";
            case NORMAL_EXIT->"NORMAL_EXIT_ORIGINALS_CREATED_NO_MANAGED_ADMISSION";
        };
        if(!node.path("status").isTextual()||!node.path("status").textValue().equals(expected)
                ||!node.path("machine_id").asText().equals(request.machineId()))throw new IOException("original writer final status differs");
        Object originals;
        if(request.mode()==Mode.NORMAL_EXIT){
            var input=new org.xar.ck3.control.platform.NormalExitSourceInventory.Input(
                    created(progress,RootBootstrapOutputContract.Kind.NORMAL_EXIT_SOURCE_INVENTORY).exact(),
                    created(progress,RootBootstrapOutputContract.Kind.NORMAL_EXIT_MANAGED_PROFILE).exact(),
                    created(progress,RootBootstrapOutputContract.Kind.ORIGINAL_SETTINGS_SNAPSHOT).exact());
            org.xar.ck3.control.platform.NormalExitSourceInventory.inspect(input);originals=input;
        }else originals=request.mode()==Mode.FORMAL_RELEASE?progress.getLast().created():progress.getLast().created().getFirst();
        var wanted=new Emission<>(expected,request.machineId(),node.path("observed_at_utc").textValue(),originals);
        if(!org.xar.ck3.control.contracts.StrictJson.parse(encode(wanted,FRAME_BYTES-1),FRAME_BYTES-1).equals(node))throw new IOException("final original set differs from confirmed stage");
    }
    private static Created created(List<Progress> progress,RootBootstrapOutputContract.Kind kind)throws IOException {
        var matches=progress.stream().flatMap(phase->phase.created().stream()).filter(row->row.kind()==kind).toList();
        if(matches.size()!=1)throw new IOException("one actual created original required for normal-exit role: "+kind);
        return matches.getFirst();
    }
    static long arrival(WindowsJobProcess.Arrival value,WindowsJobProcess.OwnedStdio io,long previous)throws IOException {
        if(value.sequence()!=previous+1||!value.identity().equals(io.identity())||!value.sessionNonce().equals(io.sessionNonce())||!value.deadline().equals(io.deadline()))throw new IOException("opaque original arrival identity/order/deadline differs");return value.sequence();
    }
    private static Issuer fileIssuer(Request request){return (quote,deadline)->{
        int index=request.mode().phases().indexOf(quote.phase());Path target=Path.of(request.issuerReplyRoot()).resolve("phase-"+index+"-reply.json");
        while(Instant.now().isBefore(deadline)){
            if(!SharedSourceFiles.nativeDirectory(Path.of(request.issuerReplyRoot())).equals(request.issuerReplyDirectory()))throw new IOException("issuer reply directory changed");
            if(Files.exists(target,LinkOption.NOFOLLOW_LINKS)){FileRef ref=FileRef.measure(target);return read(ref,65536,IssuerReply.class);}
            Thread.sleep(25);
        }throw new IOException("independent issuer reply deadline expired");};}
    private static FileRef producerRequest(Request request)throws IOException {
        return switch(request.mode()){
            case PROFILE->read(request.bootstrapRequest(),65536,RootProfileBootstrapCommand.ProfileRequest.class).producerRequest();
            case FORMAL_RELEASE->read(request.bootstrapRequest(),65536,RootProfileBootstrapCommand.FormalReleaseRequest.class).producerRequest();
            case ORIGINAL_DRIVER_RUN_PROFILE->read(request.bootstrapRequest(),65536,RootProfileBootstrapCommand.OriginalDriverRequest.class).producerRequest();
            case NORMAL_EXIT->{var source=read(request.bootstrapRequest(),65536,RootProfileBootstrapCommand.NormalExitRequest.class).nativePlan();yield new FileRef(source.path(),source.bytes(),source.sha256());}
        };
    }
    private static List<FileRef> producerInputs(Request request)throws IOException {
        if(request.mode()==Mode.NORMAL_EXIT){
            var bootstrap=read(request.bootstrapRequest(),65536,RootProfileBootstrapCommand.NormalExitRequest.class);
            bootstrapWindow(request,bootstrap.machineId(),bootstrap.reviewAtUtc());
            var plan=org.xar.ck3.control.platform.NativeLaunchPlan.readExact(bootstrap.nativePlan(),new org.xar.ck3.control.platform.NativeBridgeLaunchEvidence());
            if(!plan.sources().review().machineId().equals(request.machineId())||plan.deadline().isBefore(Instant.parse(request.deadline())))
                throw new IOException("normal-exit native plan machine/window differs from this finite Session");
            var pins=new java.util.LinkedHashSet<FileRef>();pins.add(producerRequest(request));pins.add(bootstrap.productionInventory());
            pins.add(plan.preparedProfile().environmentManifest());pins.addAll(plan.preparedProfile().preparedInputs());return List.copyOf(pins);
        }
        var result=new ArrayList<FileRef>();FileRef producer=producerRequest(request);result.add(producer);
        if(request.mode()==Mode.FORMAL_RELEASE){
            var formal=read(request.bootstrapRequest(),65536,RootProfileBootstrapCommand.FormalReleaseRequest.class);
            bootstrapWindow(request,formal.machineId(),formal.reviewAtUtc());
            result.add(formal.execution().gitExecutable());
            var source=org.xar.ck3.control.build.FormalReleaseProducer.readRequest(producer);
            if(!source.machineId().equals(request.machineId())||Instant.parse(source.reviewAtUtc()).isBefore(Instant.parse(request.deadline()))
                    ||Instant.parse(formal.execution().reviewAtUtc()).isBefore(Instant.parse(request.deadline())))throw new IOException("formal producer/Git validity must cover the original Session deadline");
        }else if(request.mode()==Mode.PROFILE){
            var bootstrap=read(request.bootstrapRequest(),65536,RootProfileBootstrapCommand.ProfileRequest.class);
            bootstrapWindow(request,bootstrap.machineId(),bootstrap.reviewAtUtc());
            var source=org.xar.ck3.control.build.NativeRunProfileProducer.readRequest(producer);
            if(!source.qualifiedToolsBuild().equals(request.runtime().toolsBuild())||!source.machineId().equals(request.machineId())
                    ||Instant.parse(source.reviewAtUtc()).isBefore(Instant.parse(request.deadline())))throw new IOException("PROFILE producer and child runtime/machine/window differ");
            result.addAll(List.of(source.qualifiedToolsBuild(),source.gameExecutable(),source.vanillaRules(),source.launcherSettings(),source.productionManifest()));
        }else{
            var bootstrap=read(request.bootstrapRequest(),65536,RootProfileBootstrapCommand.OriginalDriverRequest.class);
            bootstrapWindow(request,bootstrap.machineId(),bootstrap.reviewAtUtc());
            var source=RootOriginalDriverRunProfileProducer.readRequest(producer).profile();
            if(!source.machineId().equals(request.machineId())||source.reviewAt().isBefore(Instant.parse(request.deadline())))throw new IOException("typed Driver configuration validity must cover the original Session deadline");
            var environment=source.environmentManifest();result.add(new FileRef(environment.path(),environment.bytes(),environment.sha256()));
        }return List.copyOf(result);
    }
    private static void bootstrapWindow(Request request,String machine,String review)throws IOException {
        if(!machine.equals(request.machineId())||!review.equals(request.deadline()))throw new IOException("inner bootstrap and original Session must share the exact machine/deadline");
    }
    private static void prepareGitRoot(Request request,Path root,WindowsJobProcess.StdioGuard scope)throws Exception {
        if(request.mode()!=Mode.FORMAL_RELEASE)return;
        var source=read(request.bootstrapRequest(),65536,RootProfileBootstrapCommand.FormalReleaseRequest.class);
        var producer=org.xar.ck3.control.build.FormalReleaseProducer.readRequest(source.producerRequest());
        Path captures=root.getParent().resolve("git-captures");
        if(!source.execution().commandRoot().equals(captures)||source.execution().memoryLimitBytes()>(128L<<20)
                ||Instant.parse(source.execution().reviewAtUtc()).isBefore(Instant.parse(request.deadline()))
                ||overlap(producer.outputRoot(),root.getParent())||overlap(producer.outputRoot(),Path.of(request.issuerReplyRoot())))
            throw new IOException("formal Git captures must use this original Shared output sibling and <=128MiB nested Job/window");
        scope.verify();storage(captures);SharedSourceFiles.plainAncestors(captures);
        Files.createDirectory(captures);scope.verify();
    }
    private static void current(Request request)throws IOException {
        long remaining=java.time.Duration.between(Instant.now(),Instant.parse(request.deadline())).toMillis();
        if(!request.machineId().equals(WindowsJobProcess.currentMachineId())||remaining<=0||remaining>(request.mode()==Mode.FORMAL_RELEASE?1200000:480000))throw new IOException("Session machine/deadline exceeds its original finite mode window");
    }
    private static boolean overlap(Path left,Path right){return left.startsWith(right)||right.startsWith(left);}
    static <T>T read(FileRef ref,int maximum,Class<T> type)throws IOException {
        if(ref.bytes()<1||ref.bytes()>maximum)throw new IOException("bounded exact original required");var held=SharedSourceFiles.observe(Path.of(ref.path()));
        if(!held.source().equals(ref))throw new IOException("exact original differs");T value=decode(Files.readAllBytes(Path.of(ref.path())),maximum,type);SharedSourceFiles.assertUnchanged(held);return value;
    }
    private static FileRef cliRef(String[] args,int index)throws IOException {
        long size=Long.parseLong(args[index+1]);if(!Long.toString(size).equals(args[index+1]))throw new IOException("canonical decimal byte count required");
        return new FileRef(Path.of(args[index]).toAbsolutePath().normalize().toString(),size,args[index+2]);
    }
    private static void storage(Path root)throws IOException {
        storageConfiguration();ProjectStoragePolicy.requireBulkOutput(root);
    }
    private static StorageConfiguration storageConfiguration()throws IOException {
        String flag=System.getProperty("XAR_PROJECT_FORBID_SYSTEM_VOLUME_BULK",System.getenv("XAR_PROJECT_FORBID_SYSTEM_VOLUME_BULK"));
        String preferred=System.getProperty("XAR_PROJECT_STORAGE_ROOT",System.getenv("XAR_PROJECT_STORAGE_ROOT"));
        if(!"true".equals(flag)||preferred==null||preferred.isBlank())throw new IOException("explicit data-volume project configuration required, no repository fallback");
        return new StorageConfiguration(flag,preferred);
    }
    private static Path absolute(String value){Path path=Path.of(value);require(path.isAbsolute()&&path.normalize().equals(path),"canonical absolute path required");return path;}
    private static long size(Path path)throws IOException {return Files.exists(path,LinkOption.NOFOLLOW_LINKS)?Files.size(path):0;}
    private static long rounded(long size){return Math.addExact(4096,Math.multiplyExact(Math.max(1,(size+4095)/4096),4096));}
    static long allocated(Path root)throws IOException {
        return RootBootstrapSessionScope.allocated(root,root);
    }
    private static void writeNew(Path path,byte[] bytes,WindowsJobProcess.StdioGuard guard,Request request)throws IOException {
        guard.verify();if(allocated(Path.of(request.controlRoot()))+rounded(bytes.length)>request.controlCap()-65536)throw new IOException("bounded Session metadata would consume terminal reserve");
        SharedSourceFiles.plainAncestors(path);Files.write(path,bytes,StandardOpenOption.CREATE_NEW);guard.verify();
    }
}
