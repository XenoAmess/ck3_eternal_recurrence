package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.File;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.HashSet;
import java.util.Properties;
import java.util.Set;
import java.util.jar.JarFile;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.regex.Pattern;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.CiBootstrap;
import org.xar.ck3.control.build.RootBootstrapSessionScope;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.service.root.RootBootstrapProtocol.*;

/** Real Java/Win32 Job pipes exercise the shared production exchange. Test frames grant no profile or build qualification.
 * The separate genuine producer/Guard regression verifies the physical writer; postqualification must still run Session CLI. */
class RootBootstrapDuplexTest {
    @TempDir Path root;
    private final List<RootBootstrapSessionScope.ChildLaunch> launches=new ArrayList<>();
    @AfterEach void releaseNativeHolds()throws Exception {for(var launch:launches)launch.close();}
    public enum Behavior { NORMAL,EOF_AFTER_SEND,WRONG_PHASE }
    public record PeerInput(Behavior behavior,Mode mode,FileRef original,FileRef settingsSnapshot,List<FileRef> bindings) {public PeerInput {bindings=List.copyOf(bindings);}}
    private record Fixture(WindowsJobProcess.CommandSpec command,WindowsJobProcess.OwnedStdioSpec stdio,List<FileRef> bindings,RootBootstrapSessionScope.ChildLaunch launch,CiBootstrap.JavaUtf8Invocation.ClassCarrier carrier) { }
    private enum ArchiveRole { MAIN,TEST }
    private record ArchiveRuntime(CiBootstrap.JavaUtf8Invocation.ClasspathPin peerOrigin,CiBootstrap.JavaUtf8Invocation.ClassCarrier carrier) { }
    private static ArchiveRuntime archives;

    /** Import the complete current Maven MAIN/TEST artifacts; never create a fixture runtime or omit dependencies. */
    private static synchronized ArchiveRuntime archiveRuntime()throws Exception {
        if(archives!=null)return archives;
        String classpath=System.getProperty("surefire.test.class.path",System.getProperty("java.class.path"));
        Path peerOrigin=Path.of(Peer.class.getProtectionDomain().getCodeSource().getLocation().toURI()).toRealPath();
        var entries=new ArrayList<CiBootstrap.JavaUtf8Invocation.ClasspathPin>();
        CiBootstrap.JavaUtf8Invocation.ClasspathPin main=null;
        for(String entry:classpath.split(Pattern.quote(File.pathSeparator))) {
            Path original=Path.of(entry);var archive=originalArchive(original);entries.add(archive);
            if(original.toRealPath().equals(peerOrigin)) {if(main!=null)throw new IOException("duplicate original Peer origin");main=archive;}
        }
        if(main==null)throw new IOException("original Peer MAIN/TEST artifact is missing");
        archives=new ArchiveRuntime(main,new CiBootstrap.JavaUtf8Invocation.ClassCarrier(entries));return archives;
    }

    private static CiBootstrap.JavaUtf8Invocation.JarClasspath originalArchive(Path inputPath)throws Exception {
        var source=CiBootstrap.JavaUtf8Invocation.captureClasspath(inputPath);Path original=Path.of(source.path());
        if(source instanceof CiBootstrap.JavaUtf8Invocation.JarClasspath jar) {archiveOnly(jar);return jar;}
        if(!(source instanceof CiBootstrap.JavaUtf8Invocation.DirectoryClasspath directory))
            throw new IOException("Maven runtime entry is neither a complete class directory nor an original JAR");
        ArchiveRole role=switch(original.getFileName().toString()) {
            case "classes"->ArchiveRole.MAIN;case "test-classes"->ArchiveRole.TEST;
            default->throw new IOException("unrecognized Maven MAIN/TEST output directory");
        };
        Path module=original.getParent();var coordinates=new Properties();
        try(var input=Files.newInputStream(module.resolve("maven-archiver/pom.properties"))) {coordinates.load(input);}
        if(!coordinates.keySet().equals(Set.of("groupId","artifactId","version"))
                ||!"org.xar.ck3.control".equals(coordinates.getProperty("groupId"))
                ||!module.getFileName().toString().equals(coordinates.getProperty("artifactId"))
                ||!coordinates.getProperty("version").matches("[A-Za-z0-9][A-Za-z0-9._-]*"))
            throw new IOException("exact original Maven module coordinates are required");
        String artifact=coordinates.getProperty("artifactId"),version=coordinates.getProperty("version");
        Path archive=module.resolve(artifact+"-"+version+(role==ArchiveRole.TEST?"-tests":"")+".jar");
        if(!Files.isRegularFile(archive))throw new IOException("MISSING_ACTUAL_MAVEN_"+role+"_JAR: "+archive);
        var before=CiBootstrap.JavaUtf8Invocation.captureFile(archive);
        String metadata="META-INF/maven/org.xar.ck3.control/"+artifact+"/";
        var expected=new HashSet<String>();
        try(var jar=new JarFile(archive.toFile(),true,JarFile.OPEN_READ,Runtime.version())) {
            var packaged=new Properties();var properties=jar.getJarEntry(metadata+"pom.properties");
            if(properties==null)throw new IOException("original Maven artifact metadata is missing");
            try(var input=jar.getInputStream(properties)) {packaged.load(input);}
            if(!coordinates.equals(packaged))throw new IOException("original Maven artifact coordinates differ");
            for(var file:directory.files()) {
                String relative=original.relativize(Path.of(file.path())).toString().replace('\\','/');
                expected.add(relative);var entry=jar.getJarEntry(relative);
                if(entry==null||entry.isDirectory()||entry.getSize()!=file.bytes())
                    throw new IOException("complete original Maven artifact entry is missing: "+relative);
                var digest=java.security.MessageDigest.getInstance("SHA-256");
                try(var input=jar.getInputStream(entry)) {byte[] buffer=new byte[65536];for(int count;(count=input.read(buffer))!=-1;)digest.update(buffer,0,count);}
                if(!file.sha256().equals(java.util.HexFormat.of().formatHex(digest.digest())))
                    throw new IOException("Maven artifact differs from current complete output: "+relative);
            }
            var generated=Set.of("META-INF/MANIFEST.MF",metadata+"pom.xml",metadata+"pom.properties");
            var seen=new HashSet<String>();var entries=jar.entries();
            while(entries.hasMoreElements()) {var entry=entries.nextElement();if(!seen.add(entry.getName()))throw new IOException("duplicate original JAR member");
                if(!entry.isDirectory()&&!expected.contains(entry.getName())&&!generated.contains(entry.getName()))
                    throw new IOException("unexpected original Maven artifact member: "+entry.getName());}
        }
        if(!source.equals(CiBootstrap.JavaUtf8Invocation.captureClasspath(original)))
            throw new IOException("complete Maven output changed during original artifact import");
        var captured=CiBootstrap.JavaUtf8Invocation.captureClasspath(archive);
        if(!(captured instanceof CiBootstrap.JavaUtf8Invocation.JarClasspath jar)||!before.equals(jar.jar()))
            throw new IOException("original Maven artifact changed during complete import");
        archiveOnly(jar);return jar;
    }
    private static void archiveOnly(CiBootstrap.JavaUtf8Invocation.JarClasspath jar)throws IOException {
        for(var entry:jar.manifestClasspath())if(!(entry instanceof CiBootstrap.JavaUtf8Invocation.FileClasspath))
            throw new IOException("complete bootstrap test runtime requires original archive-only manifest dependencies");
    }
    private Fixture fixture(Behavior behavior)throws Exception {
        return fixture(behavior,Mode.PROFILE);
    }
    private Fixture fixture(Behavior behavior,Mode mode)throws Exception {
        Path original=root.resolve("tools.json");Files.writeString(original,"x");var bindings=new ArrayList<FileRef>();
        Path settings=root.resolve("original-settings.txt");Files.write(settings,new byte[0]);
        for(int i=0;i<mode.phases().size();i++){Path path=root.resolve("binding-"+i+".json");Files.writeString(path,"independent issuer "+i);bindings.add(FileRef.measure(path));}
        Path input=root.resolve("peer-input.json");Files.write(input,RootBootstrapProtocol.encode(new PeerInput(behavior,mode,FileRef.measure(original),FileRef.measure(settings),bindings),65536));
        Path java=Path.of(System.getProperty("java.home"),"bin","java.exe");FileRef executable=FileRef.measure(java);
        var runtime=archiveRuntime();var carrier=runtime.carrier();
        Path session=root.resolve("session");Files.createDirectory(session);
        var launch=RootBootstrapSessionScope.prepareChild(new CiBootstrap.JavaUtf8Invocation.ClassTarget(Peer.class.getName(),runtime.peerOrigin(),carrier.classpath()),
                carrier,
                List.of("-Xms16m","-Xmx128m","-Djava.io.tmpdir="+root,"-Djna.tmpdir="+root,"-XX:ErrorFile="+root.resolve("hs-%p.log"),"-XX:-HeapDumpOnOutOfMemoryError"),
                List.of(input.toString()),session,java,()->{},16L<<20);
        launches.add(launch);
        var env=new java.util.TreeMap<String,String>(String.CASE_INSENSITIVE_ORDER);env.putAll(System.getenv());
        for(String name:List.of("JAVA_TOOL_OPTIONS","JDK_JAVA_OPTIONS","_JAVA_OPTIONS","JDK_JAVAC_OPTIONS","CLASSPATH"))env.remove(name);
        for(String name:List.of("TEMP","TMP","TMPDIR","RUNNER_TEMP"))env.put(name,root.toString());
        var command=new WindowsJobProcess.CommandSpec(java,launch.arguments(),root,env,root.resolve("stdout.log"),root.resolve("stderr.log"),256L<<20);
        var refs=new ArrayList<FileRef>();refs.add(FileRef.measure(input));refs.add(FileRef.measure(original));refs.add(FileRef.measure(settings));refs.addAll(bindings);
        for(Class<?> type:List.of(RootBootstrapDuplexTest.class,Peer.class,PeerInput.class,RootBootstrapDuplex.class,RootBootstrapProtocol.class)){
            Path source=Path.of(type.getProtectionDomain().getCodeSource().getLocation().toURI());
            if(Files.isDirectory(source))source=source.resolve(type.getName().replace('.','/')+".class");
            FileRef ref=FileRef.measure(source);if(!refs.contains(ref))refs.add(ref);
        }
        refs.addAll(launch.inputs());
        var spec=new WindowsJobProcess.OwnedStdioSpec(command,WindowsJobProcess.ConsoleMode.NO_WINDOW,executable,refs,
                Instant.now().plusSeconds(60),RootBootstrapProtocol.FRAME_BYTES,mode.sentBytes(),mode.receivedBytes(),launch::requireCurrent);
        return new Fixture(command,spec,List.copyOf(bindings),launch,carrier);
    }
    private WindowsJobProcess.AwaitResult settle(Fixture fixture,WindowsJobProcess.OwnedStdio io)throws Exception {
        var result=io.awaitExit(root.resolve("job.json"));
        var completion=fixture.launch().completed(io,result);
        var evidence=RootBootstrapSessionScope.verifyChildCompletion(completion,fixture.carrier());
        assertEquals(result.commandResult(),evidence.terminal());assertEquals(io.sessionNonce(),completion.retirement().sessionNonce());
        assertTrue(Files.size(Path.of(completion.nativeEvidence().path()))>0);return result;
    }
    private static RootBootstrapDuplex.Handler handler(Fixture f,AtomicInteger authorized,AtomicInteger created){return new RootBootstrapDuplex.Handler(){
        @Override public FileRef authorize(String phase,WindowsJobProcess.Arrival arrival,Quote quote){return f.bindings().get(authorized.getAndIncrement());}
        @Override public void beforeSend(String phase,FileRef binding){ }
        @Override public void sent(String phase,WindowsJobProcess.WriteReceipt receipt){assertTrue(receipt.bytesWritten()>0);}
        @Override public void created(String phase,WindowsJobProcess.Arrival arrival,Quote quote,Stage stage){assertEquals(1,stage.created().size());created.incrementAndGet();}
    };}
    @Test void actualOwnedPipeRelaysThreeDistinctIssuerLinesOnceInOrder()throws Exception {
        Fixture f=fixture(Behavior.NORMAL);var authorized=new AtomicInteger();var created=new AtomicInteger();
        try(var io=WindowsJobProcess.startOwnedStdio(f.stdio())){
            f.launch().attach(io);
            var exchange=new RootBootstrapDuplex(Mode.PROFILE,io,()->{},0);var handler=handler(f,authorized,created);
            exchange.exchange(handler);assertTrue(exchange.sendAttempted());assertEquals(3,authorized.get());assertEquals(3,created.get());
            assertThrows(IOException.class,()->exchange.exchange(handler));assertEquals(3,authorized.get());
            assertTrue(settle(f,io).commandResult().passed());
        }
    }
    @Test void actualEofAfterIssuerSendLatchesUnknownBoundaryAndCannotReplay()throws Exception {
        Fixture f=fixture(Behavior.EOF_AFTER_SEND);var authorized=new AtomicInteger();var created=new AtomicInteger();
        try(var io=WindowsJobProcess.startOwnedStdio(f.stdio())){
            var exchange=new RootBootstrapDuplex(Mode.PROFILE,io,()->{},0);var handler=handler(f,authorized,created);
            assertThrows(IOException.class,()->exchange.exchange(handler));assertTrue(exchange.sendAttempted());
            assertEquals(1,authorized.get());assertEquals(0,created.get());assertThrows(IOException.class,()->exchange.exchange(handler));
            assertFalse(io.awaitExit(root.resolve("job.json")).commandResult().passed());
        }
    }
    @Test void actualNormalExitFourPhasesRetainZeroByteSettingsAndOriginalEngineCustody()throws Exception {
        Fixture f=fixture(Behavior.NORMAL,Mode.NORMAL_EXIT);var authorized=new AtomicInteger();var created=new AtomicInteger();
        try(var io=WindowsJobProcess.startOwnedStdio(f.stdio())){
            f.launch().attach(io);var exchange=new RootBootstrapDuplex(Mode.NORMAL_EXIT,io,()->{},0);
            exchange.exchange(handler(f,authorized,created));assertEquals(4,authorized.get());assertEquals(4,created.get());
            assertTrue(settle(f,io).commandResult().passed());assertEquals(0,Files.size(root.resolve("original-settings.txt")));
        }
    }
    @Test void actualWrongPhaseRejectsBeforeAnyIssuerLine()throws Exception {
        Fixture f=fixture(Behavior.WRONG_PHASE);var authorized=new AtomicInteger();var created=new AtomicInteger();
        try(var io=WindowsJobProcess.startOwnedStdio(f.stdio())){
            var exchange=new RootBootstrapDuplex(Mode.PROFILE,io,()->{},0);
            assertThrows(IOException.class,()->exchange.exchange(handler(f,authorized,created)));assertFalse(exchange.sendAttempted());assertEquals(0,authorized.get());
            io.closeInput();io.awaitExit(root.resolve("job.json"));
        }
    }
    @Test void actualRetainedSourceDriftAfterFirstSendPreventsAnySecondIssuer()throws Exception {
        Fixture f=fixture(Behavior.NORMAL);var authorized=new AtomicInteger();var created=new AtomicInteger();
        try(var io=WindowsJobProcess.startOwnedStdio(f.stdio())){
            var exchange=new RootBootstrapDuplex(Mode.PROFILE,io,()->{},0);var delegate=handler(f,authorized,created);
            var handler=new RootBootstrapDuplex.Handler(){
                @Override public FileRef authorize(String phase,WindowsJobProcess.Arrival arrival,Quote quote)throws Exception {return delegate.authorize(phase,arrival,quote);}
                @Override public void beforeSend(String phase,FileRef binding)throws Exception {delegate.beforeSend(phase,binding);}
                @Override public void sent(String phase,WindowsJobProcess.WriteReceipt receipt)throws Exception {Files.writeString(Path.of(f.bindings().getFirst().path()),"drift after actual first pipe write");}
                @Override public void created(String phase,WindowsJobProcess.Arrival arrival,Quote quote,Stage stage)throws Exception {delegate.created(phase,arrival,quote,stage);}
            };
            assertThrows(IOException.class,()->exchange.exchange(handler));assertTrue(exchange.sendAttempted());assertEquals(1,authorized.get());assertEquals(0,created.get());
            assertThrows(IOException.class,()->exchange.exchange(handler));
            assertFalse(io.awaitExit(root.resolve("job.json")).commandResult().passed());
        }
    }
    @Test void oldActualNulStdinRouteExitsTwoWithoutStageCompletion()throws Exception {
        Fixture f=fixture(Behavior.NORMAL);
        try(var process=WindowsJobProcess.start(f.command())){
            var terminal=process.await(Duration.ofSeconds(30),f.stdio().deadline(),()->{});
            assertEquals(2,terminal.exitCode());assertEquals(0,terminal.accounting().activeProcesses());
        }
        assertFalse(Files.readString(f.command().stdout()).contains("STAGE_CREATED_NO_GAME_ADMISSION"));
    }
    @Test void wrongWireTypesMissingBindingAndOversizedLineReject()throws Exception {
        Fixture f=fixture(Behavior.NORMAL);String machine=WindowsJobProcess.currentMachineId();
        var original=new IssuerQuote("xar.java-root-bootstrap-issuer-quote/v1",Mode.PROFILE,"PROFILE_ASSETS",f.bindings().get(0),f.bindings().get(1),
                new WindowsJobProcess.ProcessIdentity(1,"1",f.command().executable().toString()),"1".repeat(64),1,Instant.now().plusSeconds(60).toString());
        byte[] wire=RootBootstrapProtocol.encode(new IssuerReply("xar.java-root-bootstrap-issuer-reply/v1",original,f.bindings().get(2)),65536);
        assertEquals(f.bindings().get(2),RootBootstrapProtocol.decode(wire,65536,IssuerReply.class).binding());
        var node=(com.fasterxml.jackson.databind.node.ObjectNode)org.xar.ck3.control.contracts.StrictJson.parse(wire);
        ((com.fasterxml.jackson.databind.node.ObjectNode)node.path("original")).put("arrival_sequence",true);
        assertThrows(IOException.class,()->RootBootstrapProtocol.decode(RootBootstrapProtocol.encode(node,65536),65536,IssuerReply.class));
        node.remove("binding");assertThrows(IOException.class,()->RootBootstrapProtocol.decode(RootBootstrapProtocol.encode(node,65536),65536,IssuerReply.class));
        assertThrows(IOException.class,()->RootBootstrapProtocol.line(new byte[RootBootstrapProtocol.FRAME_BYTES+1],Origin.class));
        assertFalse(machine.isBlank());
    }
    @Test void environmentReadbackValidatesExistingAssetsWithoutClaimingTheyWereRecreated()throws Exception {
        Path existing=root.resolve("pdx_settings.txt"),environment=root.resolve("xar-autoplayer-environment.json");
        Files.writeString(existing,"existing profile asset");Files.writeString(environment,"new environment");
        FileRef first=FileRef.measure(existing),second=FileRef.measure(environment);
        var outputs=List.of(new RootBootstrapOutputContract.Output(RootBootstrapOutputContract.Kind.PROFILE_SETTINGS,existing.getFileName().toString(),first.bytes(),first.sha256()),
                new RootBootstrapOutputContract.Output(RootBootstrapOutputContract.Kind.PROFILE_ENVIRONMENT,environment.getFileName().toString(),second.bytes(),second.sha256()));
        var quote=new OrdinaryQuote("xar.java-root-bootstrap-phase-quote/v1","PROFILE_ENVIRONMENT",WindowsJobProcess.currentMachineId(),Instant.now().plusSeconds(60).toString(),root.toString(),
                outputs,List.of(),List.of(),"AWAITING_REAL_INDEPENDENT_ISSUER_BINDING");
        var created=new RootProfileBootstrapInputs.Created(RootBootstrapOutputContract.Kind.PROFILE_ENVIRONMENT,second,SharedSourceFiles.nativeFile(environment));
        var stage=new Stage(List.of(created),new RootBootstrapOutputGuard.Accounting(RootBootstrapOutputGuard.Status.ADMITTED,0,0,0,2,0));
        RootProfileBootstrapSession.verifyStage(quote,stage);
        Files.writeString(existing,"asset drift");assertThrows(IOException.class,()->RootProfileBootstrapSession.verifyStage(quote,stage));
    }
    @Test void normalExitInventoryReadbackCountsOnlyItsTwoNewOutputsAndStillChecksRetainedProfile()throws Exception {
        Path settings=root.resolve("pdx_settings.txt"),inventory=root.resolve("normal-exit-source-inventory-v1.json"),projection=root.resolve("normal-exit-profile-binding-projection-v1.json");
        Files.writeString(settings,"retained profile settings");Files.writeString(inventory,"actual test inventory");Files.writeString(projection,"actual test projection");
        var outputs=new ArrayList<RootBootstrapOutputContract.Output>();var created=new ArrayList<RootProfileBootstrapInputs.Created>();
        var kinds=List.of(RootBootstrapOutputContract.Kind.PROFILE_SETTINGS,RootBootstrapOutputContract.Kind.NORMAL_EXIT_SOURCE_INVENTORY,RootBootstrapOutputContract.Kind.NORMAL_EXIT_PROFILE_PROJECTION);
        var paths=List.of(settings,inventory,projection);
        for(int i=0;i<paths.size();i++){
            FileRef ref=FileRef.measure(paths.get(i));outputs.add(new RootBootstrapOutputContract.Output(kinds.get(i),paths.get(i).getFileName().toString(),ref.bytes(),ref.sha256()));
            if(i>0)created.add(new RootProfileBootstrapInputs.Created(kinds.get(i),ref,SharedSourceFiles.nativeFile(paths.get(i))));
        }
        var quote=new OrdinaryQuote("xar.java-root-bootstrap-phase-quote/v1","NORMAL_EXIT_INVENTORY_AND_PROJECTION",WindowsJobProcess.currentMachineId(),Instant.now().plusSeconds(60).toString(),root.toString(),outputs,List.of(),List.of(),"AWAITING_REAL_INDEPENDENT_ISSUER_BINDING");
        var stage=new Stage(created,new RootBootstrapOutputGuard.Accounting(RootBootstrapOutputGuard.Status.ADMITTED,0,0,0,3,0));
        RootProfileBootstrapSession.verifyStage(quote,stage);Files.writeString(settings,"retained settings changed");
        assertThrows(IOException.class,()->RootProfileBootstrapSession.verifyStage(quote,stage));
    }
    /** Mechanical fixture peer, not an alternative profile producer, writer or capacity issuer. */
    public static final class Peer {
        private Peer(){ }
        public static void main(String[] args)throws Exception {
            PeerInput input=RootBootstrapProtocol.decode(Files.readAllBytes(Path.of(args[0])),65536,PeerInput.class);
            var reader=new BufferedReader(new InputStreamReader(System.in,StandardCharsets.UTF_8));String machine=WindowsJobProcess.currentMachineId();
            for(int i=0;i<input.mode().phases().size();i++){
                String phase=input.mode().phases().get(i);if(input.behavior()==Behavior.WRONG_PHASE)phase=input.mode().phases().getLast();
                boolean settings=input.mode()==Mode.NORMAL_EXIT&&i==0;
                var ref=settings?input.settingsSnapshot():input.original();var kind=settings?RootBootstrapOutputContract.Kind.ORIGINAL_SETTINGS_SNAPSHOT:RootBootstrapOutputContract.Kind.MCP_TOOLS;
                var output=new RootBootstrapOutputContract.Output(kind,Path.of(ref.path()).getFileName().toString(),ref.bytes(),ref.sha256());
                RootBootstrapProtocol.emit(new OrdinaryQuote("xar.java-root-bootstrap-phase-quote/v1",phase,machine,Instant.now().plusSeconds(30).toString(),
                        Path.of(ref.path()).getParent().toString(),List.of(output),List.of(),List.of(),"AWAITING_REAL_INDEPENDENT_ISSUER_BINDING"));
                String line=reader.readLine();if(line==null){System.exit(2);return;}
                var binding=RootBootstrapProtocol.decode(line.getBytes(StandardCharsets.UTF_8),65536,FileRef.class);
                if(!binding.equals(input.bindings().get(i)))throw new IOException("wrong issuer original for phase "+i);
                if(input.behavior()==Behavior.EOF_AFTER_SEND){System.exit(2);return;}
                var created=new RootProfileBootstrapInputs.Created(kind,ref,SharedSourceFiles.nativeFile(Path.of(ref.path())));
                RootBootstrapProtocol.emit(new Emission<>("STAGE_CREATED_NO_GAME_ADMISSION",machine,Instant.now().toString(),new Stage(List.of(created),
                        new RootBootstrapOutputGuard.Accounting(RootBootstrapOutputGuard.Status.ADMITTED,0,0,0,1,0))));
            }
        }
    }
}
