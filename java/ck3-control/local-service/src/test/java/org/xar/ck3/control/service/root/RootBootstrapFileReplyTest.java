package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.service.root.RootBootstrapOutputContract.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.PipedInputStream;
import java.io.PipedOutputStream;
import java.io.PrintStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.Arrays;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.FutureTask;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.Timeout;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.checkpoint.NativeCheckpointFiles;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.service.root.RootBootstrapProtocol.FileReply;
import org.xar.ck3.control.service.root.RootBootstrapProtocol.FileReplyChannel;
import org.xar.ck3.control.service.root.RootBootstrapProtocol.OrdinaryQuote;
import org.xar.ck3.control.service.root.RootBootstrapProtocol.Quote;
import org.xar.ck3.control.service.root.RootProfileBootstrapCommand.Mode;

/** Real Windows files, the original issuer/Guard and one retained Prepared. Financial cards here are
 * explicitly software fixtures; this class grants no deployment, live runtime, Session or Game credit. */
final class RootBootstrapFileReplyTest {
    @TempDir Path root;
    private record Scene(Path asset,Path control,Clock clock,String machine,String review,
            RootOriginalDriverRunProfileProducer.Prepared producer,RootProfileBootstrapInputs.Prepared prepared,
            FileRef outer,FileRef channelRef,FileReplyChannel channel) { }

    @Test @Timeout(150)
    void actualEmittedQuoteIndependentIssuerFileReplyAndTheSamePreparedReachOriginalGuardAndReadback()throws Exception {
        Scene scene=scene(root,Clock.systemUTC());
        var reader=RootBootstrapFileReply.open(scene.channelRef(),Mode.ORIGINAL_DRIVER_RUN_PROFILE,
                SharedSourceFiles.observe(Path.of(scene.outer().path())),scene.clock());
        try(var input=new PipedInputStream(RootBootstrapProtocol.FRAME_BYTES);
                var output=new PipedOutputStream(input);var capture=new PrintStream(output,true,StandardCharsets.UTF_8)){
            var issuer=new FutureTask<RootProfileBootstrapCommand.IssuerPublication>(()->{
                byte[] frame=line(input);
                FileRef quote=write(RootBootstrapFileReply.quotePath(scene.channel(),0),frame);
                FileRef binding=issueBinding(scene,quote);
                return RootProfileBootstrapCommand.publishIssuedFileReply(issuerRequest(scene,quote,binding),scene.clock());
            });
            Thread issuerThread=Thread.ofVirtual().start(issuer);
            var phase=new FutureTask<List<RootProfileBootstrapInputs.Created>>(() ->
                    RootProfileBootstrapCommand.phase(reader,"ORIGINAL_DRIVER_RUN_PROFILE",scene.prepared(),
                            scene.review(),scene.clock(),SharedSourceFiles.observe(Path.of(scene.outer().path()))));
            Thread phaseThread=Thread.ofVirtual().unstarted(phase);
            PrintStream previous=System.out;
            List<RootProfileBootstrapInputs.Created> created;
            RootProfileBootstrapCommand.IssuerPublication reply;
            try{
                System.setOut(capture);phaseThread.start();
                reply=issuer.get(10,TimeUnit.SECONDS);created=phase.get(10,TimeUnit.SECONDS);
            }finally{
                phase.cancel(true);issuer.cancel(true);
                try{
                    phaseThread.join(5000);issuerThread.join(5000);
                    assertFalse(phaseThread.isAlive()||issuerThread.isAlive(),"actual fixture threads must terminate after failure or completion");
                }finally{System.setOut(previous);}
            }
            assertEquals(RootBootstrapFileReply.replyPath(scene.channel(),0).toString(),reply.original().path());
            assertEquals(SharedSourceFiles.nativeFile(Path.of(reply.original().path())),reply.nativeFile());
            assertEquals(1,reply.nativeFile().linkCount());
            assertFalse(Files.exists(scene.control().resolve("phase-0-reply.pending")));
            assertEquals(1,created.size());scene.producer().verifyCreated();
            assertArrayEquals(scene.producer().bytes(),Files.readAllBytes(Path.of(created.getFirst().original().path())));
            assertEquals(SharedSourceFiles.nativeFile(Path.of(created.getFirst().original().path())),created.getFirst().nativeFile());
            var pin=new RootRuntimeDefinitionModel.DataPin(RootRuntimeDefinitionModel.DataRole.ORIGINAL_DRIVER_RUN_PROFILE,created.getFirst().original());
            assertArrayEquals(scene.producer().bytes(),RootRuntimeDefinitions.readData(pin));
            assertThrows(IOException.class,()->reader.await(quote(scene),scene.review()),"one accepted phase cannot replay");
            var before=SharedSourceFiles.observe(Path.of(reply.original().path()));
            assertThrows(IOException.class,()->RootProfileBootstrapCommand.publishIssuedFileReply(
                    issuerRequest(scene,FileRef.measure(RootBootstrapFileReply.quotePath(scene.channel(),0)),
                            RootBootstrapFileReply.decode(reply.original(),FileReply.class).binding()),scene.clock()));
            SharedSourceFiles.assertUnchanged(before);
        }
    }

    @Test @Timeout(150)
    void actualWindowsNulStdinCommandMainCompletesThroughIndependentFileReplyWithoutAnySession()throws Exception {
        Scene scene=scene(root,Clock.systemUTC());
        Path java=Path.of(System.getProperty("java.home"),"bin","java.exe"),stdout=root.resolve("command-stdout.log"),stderr=root.resolve("command-stderr.log");
        String classpath=System.getProperty("surefire.test.class.path",System.getProperty("java.class.path"));
        var arguments=new ArrayList<String>(List.of("-Xms16m","-Xmx128m","-XX:MaxMetaspaceSize=128m","-XX:ReservedCodeCacheSize=48m",
                "-Djava.io.tmpdir="+root,"-Djna.tmpdir="+root,"-XX:ErrorFile="+root.resolve("command-hs-%p.log"),
                "-XX:ReplayDataFile="+root.resolve("command-replay-%p.log"),"-XX:HeapDumpPath="+root.resolve("command-heap.hprof"),
                "-XX:-HeapDumpOnOutOfMemoryError","-cp",classpath,RootProfileBootstrapCommand.class.getName(),
                "ORIGINAL_DRIVER_RUN_PROFILE",scene.outer().path(),Long.toString(scene.outer().bytes()),scene.outer().sha256(),
                "FILE_REPLY",scene.channelRef().path(),Long.toString(scene.channelRef().bytes()),scene.channelRef().sha256()));
        var environment=new java.util.TreeMap<String,String>(String.CASE_INSENSITIVE_ORDER);environment.putAll(System.getenv());
        for(String name:List.of("JAVA_TOOL_OPTIONS","JDK_JAVA_OPTIONS","_JAVA_OPTIONS","JDK_JAVAC_OPTIONS","CLASSPATH"))environment.remove(name);
        for(String name:List.of("TEMP","TMP","TMPDIR","RUNNER_TEMP"))environment.put(name,root.toString());
        var command=new WindowsJobProcess.CommandSpec(java,arguments,root,environment,stdout,stderr,512L<<20);
        // The original start(CommandSpec) path sets hStdInput to its actual NUL handle.
        try(var process=WindowsJobProcess.start(command)){
            var identity=process.identity();
            FileRef captured=write(RootBootstrapFileReply.quotePath(scene.channel(),0),line(stdout,stderr,process,Instant.parse(scene.review())));
            assertArrayEquals(RootBootstrapProtocol.quoteLine(quote(scene)),Files.readAllBytes(Path.of(captured.path())));
            FileRef binding=issueBinding(scene,captured);
            RootProfileBootstrapCommand.publishIssuedFileReply(issuerRequest(scene,captured,binding),scene.clock());
            var terminal=process.await(Duration.ofSeconds(60),Instant.parse(scene.review()),()->{
                if(size(stdout)>(2L<<20)||size(stderr)>(1L<<20))throw new IllegalStateException("finite software child logs exceeded their original bound");
            });
            assertEquals(identity,terminal.identity());assertTrue(terminal.passed(),Files.readString(stderr));
            assertEquals(0,terminal.accounting().activeProcesses());
        }
        scene.producer().verifyCreated();
        var actual=SharedSourceFiles.observe(scene.producer().target());
        assertArrayEquals(scene.producer().bytes(),RootRuntimeDefinitions.readData(new RootRuntimeDefinitionModel.DataPin(
                RootRuntimeDefinitionModel.DataRole.ORIGINAL_DRIVER_RUN_PROFILE,actual.source())));
        String emitted=Files.readString(stdout);
        assertTrue(emitted.contains("STAGE_CREATED_NO_GAME_ADMISSION"));
        assertTrue(emitted.contains("ORIGINAL_DRIVER_RUN_PROFILE_CREATED_NO_GAME_ADMISSION"));
        assertFalse(emitted.contains("session_nonce"));
    }

    @Test void exactReplyRejectsWrongPhaseOuterRequestNativeIdentityQuoteBytesAndDeadlineBeforeAnyAssetWrite()throws Exception {
        for(String defect:List.of("phase","outer","native","quote","noncanonical","deadline")){
            Scene scene=scene(Files.createDirectory(root.resolve(defect)),Clock.systemUTC());
            Quote expected=quote(scene),captured=expected;
            if(defect.equals("quote")){
                var original=expected.outputs().getFirst();
                captured=new OrdinaryQuote(expected.schema(),expected.phase(),expected.machineId(),expected.reviewAtUtc(),expected.assetRoot(),
                        List.of(new Output(original.kind(),original.fileName(),original.bytes(),"1".repeat(64))),List.of(),List.of(),expected.authority());
            }
            byte[] frame=RootBootstrapProtocol.quoteLine(captured);
            if(defect.equals("noncanonical")){
                byte[] changed=Arrays.copyOf(frame,frame.length+1);changed[frame.length-1]=' ';changed[frame.length]='\n';frame=changed;
            }
            FileRef quoteRef=write(RootBootstrapFileReply.quotePath(scene.channel(),0),frame);
            FileRef binding=write(scene.control().resolve("not-yet-read-binding.json"),new byte[]{'{','}'});
            var nativeQuote=SharedSourceFiles.nativeFile(Path.of(quoteRef.path()));
            if(defect.equals("native"))nativeQuote=SharedSourceFiles.nativeFile(Path.of(binding.path()));
            var reply=new FileReply("xar.java-root-bootstrap-file-reply/v1",scene.channelRef(),scene.outer(),
                    Mode.ORIGINAL_DRIVER_RUN_PROFILE,expected.phase(),0,scene.review(),quoteRef,nativeQuote,binding);
            ObjectNode value=(ObjectNode)ControlBuild.strictMapper().valueToTree(reply);
            switch(defect){
                case "phase"->value.put("phase","NORMAL_EXIT_TARGET_BINDING");
                case "outer"->{var other=write(scene.control().resolve("other-request.json"),Files.readAllBytes(Path.of(scene.outer().path())));
                    value.set("bootstrap_request",ControlBuild.strictMapper().valueToTree(other));}
                case "deadline"->value.put("deadline",Instant.parse(scene.review()).minusSeconds(1).toString());
                default->{ }
            }
            write(RootBootstrapFileReply.replyPath(scene.channel(),0),StrictJson.canonical(value));
            var reader=RootBootstrapFileReply.open(scene.channelRef(),Mode.ORIGINAL_DRIVER_RUN_PROFILE,
                    SharedSourceFiles.observe(Path.of(scene.outer().path())),scene.clock());
            assertThrows(IOException.class,()->reader.await(expected,scene.review()),defect);
            assertFalse(Files.exists(scene.producer().target()),defect);
        }
    }

    @Test void actualChannelFileRejectsMissingAndWrongTypesForeignDirectoryAndExpiredOrExtendedWindow()throws Exception {
        for(String defect:List.of("missing","numeric-mode","float-bytes","boolean-bytes","directory","expired","extended")){
            Scene scene=scene(Files.createDirectory(root.resolve(defect)),Clock.systemUTC());
            ObjectNode value=(ObjectNode)ControlBuild.strictMapper().valueToTree(scene.channel());
            Clock clock=scene.clock();
            switch(defect){
                case "missing"->value.remove("issuer_reply_directory");
                case "numeric-mode"->value.put("mode",1);
                case "float-bytes"->((ObjectNode)value.get("bootstrap_request")).put("bytes",scene.outer().bytes()+0.0);
                case "boolean-bytes"->((ObjectNode)value.get("bootstrap_request")).put("bytes",true);
                case "directory"->{Path other=Files.createDirectory(root.resolve("other-native-directory"));
                    value.set("issuer_reply_directory",ControlBuild.strictMapper().valueToTree(SharedSourceFiles.nativeDirectory(other)));}
                case "expired"->clock=Clock.fixed(Instant.parse(scene.review()),ZoneOffset.UTC);
                case "extended"->value.put("deadline",Instant.parse(scene.review()).plusSeconds(1).toString());
                default->throw new AssertionError(defect);
            }
            FileRef modified=write(scene.control().resolve("modified-channel.json"),ControlBuild.strictMapper().writeValueAsBytes(value));Clock observed=clock;
            if(defect.equals("extended")){
                var reader=RootBootstrapFileReply.open(modified,Mode.ORIGINAL_DRIVER_RUN_PROFILE,
                        SharedSourceFiles.observe(Path.of(scene.outer().path())),observed);
                assertThrows(IOException.class,()->reader.await(quote(scene),scene.review()));
            }else assertThrows(IOException.class,()->RootBootstrapFileReply.open(modified,Mode.ORIGINAL_DRIVER_RUN_PROFILE,
                    SharedSourceFiles.observe(Path.of(scene.outer().path())),observed),defect);
            assertFalse(Files.exists(scene.producer().target()));
        }
    }

    @Test void acceptedReplyRetainsQuoteAndDirectoryWitnessesAndCannotAuthorizeAReplacedOriginal()throws Exception {
        Scene scene=scene(root,Clock.systemUTC());Quote expected=quote(scene);
        FileRef quote=write(RootBootstrapFileReply.quotePath(scene.channel(),0),RootBootstrapProtocol.quoteLine(expected));
        FileRef binding=issueBinding(scene,quote);
        var published=RootProfileBootstrapCommand.publishIssuedFileReply(issuerRequest(scene,quote,binding),scene.clock());
        var reader=RootBootstrapFileReply.open(scene.channelRef(),Mode.ORIGINAL_DRIVER_RUN_PROFILE,
                SharedSourceFiles.observe(Path.of(scene.outer().path())),scene.clock());
        var accepted=reader.await(expected,scene.review());accepted.verify();
        Path old=Path.of(quote.path()),replacement=scene.control().resolve("quote-replacement.jsonl");
        Files.copy(old,replacement);Files.setLastModifiedTime(replacement,Files.getLastModifiedTime(old));
        Files.move(replacement,old,java.nio.file.StandardCopyOption.REPLACE_EXISTING);
        assertThrows(IOException.class,accepted::verify);
        assertFalse(Files.exists(scene.producer().target()));
        published.original().verify();
    }

    @Test @Timeout(5)
    void capturedMonotonicBudgetExpiresEvenWhenTheSuppliedClockDoesNotAdvance()throws Exception {
        Scene scene=scene(root,Clock.fixed(Instant.now(),ZoneOffset.UTC));
        var channel=new FileReplyChannel(scene.channel().schema(),scene.machine(),scene.clock().instant().plusMillis(100).toString(),
                scene.channel().mode(),scene.outer(),scene.control().toString(),scene.channel().issuerReplyDirectory());
        FileRef original=write(root.resolve("finite-clock-channel.json"),RootBootstrapProtocol.encode(channel,65536));
        var reader=RootBootstrapFileReply.open(original,Mode.ORIGINAL_DRIVER_RUN_PROFILE,
                SharedSourceFiles.observe(Path.of(scene.outer().path())),scene.clock());
        assertThrows(IOException.class,()->reader.await(quote(scene),scene.review()));
        assertFalse(Files.exists(scene.producer().target()));
    }

    @Test void issuerPreservesAnExistingReplyRatherThanOverwritingOrStagingAnotherAttempt()throws Exception {
        Scene scene=scene(root,Clock.systemUTC());Quote expected=quote(scene);
        FileRef quote=write(RootBootstrapFileReply.quotePath(scene.channel(),0),RootBootstrapProtocol.quoteLine(expected));
        FileRef binding=issueBinding(scene,quote);
        Path target=RootBootstrapFileReply.replyPath(scene.channel(),0);
        FileRef existing=write(target,new byte[]{'{','}'});
        assertThrows(IOException.class,()->RootProfileBootstrapCommand.publishIssuedFileReply(issuerRequest(scene,quote,binding),scene.clock()));
        existing.verify();assertFalse(Files.exists(scene.control().resolve("phase-0-reply.pending")));
        assertFalse(Files.exists(scene.producer().target()));
    }

    @Test void independentBindingForDifferentActualBytesCannotPublishAReplyForThisPreparedPlan()throws Exception {
        Scene scene=scene(root,Clock.systemUTC());Quote expected=quote(scene);var output=expected.outputs().getFirst();
        var wrong=new OrdinaryQuote(expected.schema(),expected.phase(),expected.machineId(),expected.reviewAtUtc(),expected.assetRoot(),
                List.of(new Output(output.kind(),output.fileName(),output.bytes(),"1".repeat(64))),List.of(),List.of(),expected.authority());
        FileRef wrongOriginal=write(root.resolve("other-phase-quote.jsonl"),RootBootstrapProtocol.quoteLine(wrong));
        FileRef binding=issueBinding(scene,wrongOriginal);
        FileRef actual=write(RootBootstrapFileReply.quotePath(scene.channel(),0),RootBootstrapProtocol.quoteLine(expected));
        assertThrows(IOException.class,()->RootProfileBootstrapCommand.publishIssuedFileReply(issuerRequest(scene,actual,binding),scene.clock()));
        assertFalse(Files.exists(RootBootstrapFileReply.replyPath(scene.channel(),0)));
        assertFalse(Files.exists(scene.control().resolve("phase-0-reply.pending")));
        assertFalse(Files.exists(scene.producer().target()));
    }

    @Test void completeTwoNameMetadataPeakMustFitOriginalControlBudgetBeforeAnyStagingWrite()throws Exception {
        Scene scene=scene(root,Clock.systemUTC());Quote expected=quote(scene);
        FileRef quote=write(RootBootstrapFileReply.quotePath(scene.channel(),0),RootBootstrapProtocol.quoteLine(expected));
        FileRef binding=issueBinding(scene,quote);
        var reply=new FileReply("xar.java-root-bootstrap-file-reply/v1",scene.channelRef(),scene.outer(),Mode.ORIGINAL_DRIVER_RUN_PROFILE,
                expected.phase(),0,scene.review(),quote,SharedSourceFiles.nativeFile(Path.of(quote.path())),binding);
        long one=RootBootstrapOutputGuard.fileQuote(RootBootstrapProtocol.encode(reply,65536).length,scene.control());
        long charged=RootBootstrapAssetTree.directoryQuote(scene.control());
        try(var stream=Files.newDirectoryStream(scene.control())){for(Path path:stream)charged+=SharedSourceFiles.nativeFile(path).allocatedBytes();}
        long unit=org.xar.ck3.control.build.NativeStorageGeometry.read(scene.control()).clusterBytes();
        long filler=((512L*1024-charged-one)/unit)*unit;
        assertTrue(filler>0&&filler<Integer.MAX_VALUE);
        write(scene.control().resolve("software-control-budget-fixture.bin"),new byte[(int)filler]);
        assertThrows(IOException.class,()->RootProfileBootstrapCommand.publishIssuedFileReply(issuerRequest(scene,quote,binding),scene.clock()));
        assertFalse(Files.exists(RootBootstrapFileReply.replyPath(scene.channel(),0)));
        assertFalse(Files.exists(scene.control().resolve("phase-0-reply.pending")));
        assertFalse(Files.exists(scene.producer().target()));
    }

    private static Scene scene(Path root,Clock clock)throws Exception {
        Path asset=Files.createDirectory(root.resolve("asset")),control=Files.createDirectory(root.resolve("control"));
        String machine=WindowsJobProcess.currentMachineId();Instant now=clock.instant();String review=now.plusSeconds(120).toString();
        FileRef environment=write(root.resolve("environment.json"),"{\"software_environment_only\":true}".getBytes(StandardCharsets.UTF_8));
        var profile=new RootFrozenRunProfile.Request(machine,now.minusSeconds(1),Instant.parse(review),"file-reply-software-request",
                "file-reply-software-session",new ExactRef(environment.path(),environment.bytes(),environment.sha256()),
                RootFrozenRunProfile.LifecycleMode.ROGUE_ONE_LIFE,false,new RootFrozenRunProfile.DisabledFreshRobert());
        FileRef producerRef=write(root.resolve("producer.json"),RootOriginalDriverRunProfileProducer.encode(new RootOriginalDriverRunProfileProducer.Request(profile)));
        Path target=asset.resolve("original-driver-run-profile.json");
        var producer=RootOriginalDriverRunProfileProducer.prepare(producerRef,target,clock);
        var request=new RootProfileBootstrapCommand.OriginalDriverRequest("xar.java-root-original-driver-bootstrap/v1",machine,review,producerRef,target.toString());
        FileRef outer=write(root.resolve("bootstrap-request.json"),RootBootstrapProtocol.encode(request,65536));
        var channel=new FileReplyChannel("xar.java-root-bootstrap-file-reply-channel/v1",machine,review,
                Mode.ORIGINAL_DRIVER_RUN_PROFILE,outer,control.toString(),SharedSourceFiles.nativeDirectory(control));
        FileRef channelRef=write(root.resolve("channel.json"),RootBootstrapProtocol.encode(channel,65536));
        return new Scene(asset,control,clock,machine,review,producer,RootProfileBootstrapInputs.originalDriverRunProfile(producer),outer,channelRef,channel);
    }
    private static Quote quote(Scene scene){return new OrdinaryQuote("xar.java-root-bootstrap-phase-quote/v1","ORIGINAL_DRIVER_RUN_PROFILE",
            scene.machine(),scene.review(),scene.asset().toString(),scene.prepared().quote(),List.of(),List.of(),"AWAITING_REAL_INDEPENDENT_ISSUER_BINDING");}
    private static RootProfileBootstrapCommand.IssuerFileReplyRequest issuerRequest(Scene scene,FileRef quote,FileRef binding){
        return new RootProfileBootstrapCommand.IssuerFileReplyRequest("xar.java-root-bootstrap-issuer-file-reply-request/v1",
                scene.machine(),scene.review(),scene.channelRef(),0,quote,binding);
    }
    private static FileRef issueBinding(Scene scene,FileRef quote)throws Exception {
        var declaration=RootProfileBootstrapCommand.declareOutput(new RootProfileBootstrapCommand.IssuerDeclarationRequest(
                "xar.java-root-bootstrap-issuer-declaration-request/v1",scene.machine(),scene.review(),"file-reply-software-fixture",
                quote,scene.control().toString(),scene.control().resolve("declaration.json").toString(),1536L*1024,512L*1024,1<<20,64),scene.clock());
        var census=RootProfileBootstrapCommand.observeOutputCensus(new RootProfileBootstrapCommand.IssuerCensusRequest(
                "xar.java-root-bootstrap-issuer-census-request/v1",scene.machine(),scene.review(),declaration.declaration().original(),
                scene.control().resolve("census.json").toString()),scene.clock());
        var policy=StrictJson.object().put("policy_version","1.0.0");var rules=policy.putObject("capacity");
        rules.put("safety_floor_bytes",2L<<30);rules.put("safety_ceiling_bytes",20L<<30);
        rules.put("default_project_quota_ceiling_bytes",100L<<30);rules.put("safety_volume_fraction",new java.math.BigDecimal("0.05"));
        rules.put("default_project_quota_volume_fraction",new java.math.BigDecimal("0.10"));
        FileRef policyRef=write(scene.control().resolve("policy.json"),ControlBuild.strictMapper().writeValueAsBytes(policy));
        Path volume=scene.asset().getRoot();long total=Files.getFileStore(volume).getTotalSpace(),free=Files.getFileStore(volume).getUsableSpace();
        var financial=StrictJson.object().put("scope","software-fixture-actual-volume-observation").put("machine_id",scene.machine())
                .put("total_bytes",total).put("usable_bytes",free).put("old_workpackage_actual_is_unknown",true);
        FileRef head=write(scene.control().resolve("financial.json"),StrictJson.canonical(financial));
        var usage=new RootRuntimeStorageContract.ExistingUsage(RootRuntimeStorageContract.ExistingUsageKind.UNKNOWN_WITH_CONSERVATIVE_UPPER,
                null,Math.subtractExact(total,free),head);
        var release=new CapacityRelease(CAPACITY,PURPOSE,scene.machine(),"/root",ISSUER,"file-reply-software-fixture",scene.clock().instant().toString(),
                scene.review(),policyRef,declaration.declaration().original(),census.original(),head,2L<<20,
                List.of(new Volume(volume.toString(),2L<<20,0,0,total,scene.review(),usage,List.of(),0)),List.of());
        FileRef capacity=write(scene.control().resolve("capacity.json"),RootBootstrapOutputContract.encode(release));
        return RootProfileBootstrapCommand.bindIssuedCapacity(new RootProfileBootstrapCommand.IssuerBindingRequest(
                "xar.java-root-bootstrap-issuer-binding-request/v1",scene.machine(),scene.review(),capacity,
                scene.control().resolve("binding.json").toString()),scene.clock()).binding().original();
    }
    private static FileRef write(Path target,byte[] bytes)throws IOException {
        var files=new NativeCheckpointFiles();var actual=files.createNew(target,bytes);files.verify(actual);
        var ref=actual.reference();return new FileRef(ref.path(),ref.bytes(),ref.sha256());
    }
    private static byte[] line(PipedInputStream input)throws IOException {
        var bytes=new ByteArrayOutputStream();int value;
        while((value=input.read())>=0){if(bytes.size()>=RootBootstrapProtocol.FRAME_BYTES)throw new IOException("fixture phase frame exceeds bound");
            bytes.write(value);if(value=='\n')return bytes.toByteArray();}
        throw new IOException("actual Command quote stream ended before LF");
    }
    private static byte[] line(Path stdout,Path stderr,WindowsJobProcess process,Instant deadline)throws Exception {
        long started=System.nanoTime();
        while(Instant.now().isBefore(deadline)&&System.nanoTime()-started<TimeUnit.SECONDS.toNanos(60)){
            if(size(stdout)>RootBootstrapProtocol.FRAME_BYTES||size(stderr)>(1L<<20))throw new IOException("actual child quote/log byte bound exceeded");
            if(Files.exists(stdout)){
                byte[] bytes=Files.readAllBytes(stdout);
                for(int i=0;i<bytes.length;i++)if(bytes[i]=='\n')return Arrays.copyOf(bytes,i+1);
            }
            if(!process.isRunning())throw new IOException("actual NUL child exited before quote: "+(Files.exists(stderr)?Files.readString(stderr):"stderr missing"));
            Thread.sleep(25);
        }
        throw new IOException("actual NUL child did not produce its complete LF quote within the finite window");
    }
    private static long size(Path path){try{return Files.exists(path)?Files.size(path):0;}catch(IOException unavailable){throw new IllegalStateException(unavailable);}}
}
