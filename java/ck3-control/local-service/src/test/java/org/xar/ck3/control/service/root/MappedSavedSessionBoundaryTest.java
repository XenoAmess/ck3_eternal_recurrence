package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.service.root.RootBootstrapProtocol.*;

import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.PrintStream;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.checkpoint.CheckpointPair;
import org.xar.ck3.control.application.checkpoint.CheckpointPairCodec;
import org.xar.ck3.control.application.checkpoint.NativeCheckpointFiles;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.NativeRunProfileManifest.ProfileKind;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.platform.*;

/** Genuine temporary Native files and public producer/consumer methods. Runtime metadata in the
 * Session DTO is explicit unqualified DATA: no Session launch, Game, token or financial card is faked.
 * System streams are isolated for the actual EOF regression; no child process is started. */
@org.junit.jupiter.api.parallel.Isolated
final class MappedSavedSessionBoundaryTest {
    @TempDir Path root;
    private final NativeCheckpointFiles files=new NativeCheckpointFiles();
    private record Scene(Path asset,Path control,Path replies,String machine,String review,FileRef bootstrap,
            RootProfileBootstrapCommand.SavedMaterializedPolicyRequest policyRequest) { }
    private FileRef write(Path target,byte[] bytes)throws IOException {
        Files.write(target,bytes);return FileRef.measure(target);
    }
    private FileRef data(String name)throws IOException {return write(root.resolve(name),new byte[]{'{','}'});}
    private static ExactRef exact(FileRef ref){return new ExactRef(ref.path(),ref.bytes(),ref.sha256());}
    private Scene scene()throws Exception {
        Path asset=Files.createDirectory(root.resolve("asset")),control=Files.createDirectory(root.resolve("shared"));
        Path replies=Files.createDirectory(root.resolve("replies"));String machine=WindowsJobProcess.currentMachineId();
        String review=Instant.now().plusSeconds(240).toString();
        var request=new RootProfileBootstrapCommand.SavedMaterializedPolicyRequest(
                "xar.java-root-initial-saved-native-policy-bootstrap/v2",machine,review,data("ENV-DATA.json"),
                write(root.resolve("old-source.ck3"),new byte[]{1,2,3}),exact(data("plan-DATA.json")),
                asset.resolve("policy.json").toString(),exact(data("pair-DATA.json")));
        FileRef bootstrap=write(root.resolve("mapped-request.json"),ControlBuild.strictMapper().writeValueAsBytes(request));
        return new Scene(asset,control,replies,machine,review,bootstrap,request);
    }
    private RootProfileBootstrapSession.Request session(Scene scene,String deadline)throws Exception {
        FileRef placeholder=data("UNQUALIFIED-runtime-metadata.json");
        var runtime=new RootBootstrapRuntime.Request(placeholder,placeholder,placeholder,List.of(placeholder),List.of());
        return new RootProfileBootstrapSession.Request("xar.java-root-bootstrap-session/v1",scene.machine(),deadline,
                Mode.INITIAL_SAVED_MATERIALIZED_POLICY,scene.bootstrap(),runtime,scene.control().resolve("session").toString(),
                scene.replies().toString(),SharedSourceFiles.nativeDirectory(scene.replies()));
    }
    private OrdinaryQuote quote(Scene scene,RootBootstrapOutputContract.Kind kind,String name)throws Exception {
        FileRef body=write(scene.asset().resolve(name),"software-policy-DATA".getBytes(StandardCharsets.UTF_8));
        var output=new RootBootstrapOutputContract.Output(kind,name,body.bytes(),body.sha256());
        return new OrdinaryQuote("xar.java-root-bootstrap-phase-quote/v1","INITIAL_SAVED_MATERIALIZED_POLICY",
                scene.machine(),scene.review(),scene.asset().toString(),List.of(output),List.of(),List.of(),
                "AWAITING_REAL_INDEPENDENT_ISSUER_BINDING");
    }

    @Test void actualMappedFinalConsumerAcceptsOnlyItsExactCreatedAndNewStatus()throws Exception {
        Scene scene=scene();var request=session(scene,scene.review());var quote=quote(scene,RootBootstrapOutputContract.Kind.INITIAL_POLICY,"policy.json");
        Path target=scene.asset().resolve("policy.json");FileRef original=FileRef.measure(target);
        var created=new RootProfileBootstrapInputs.Created(RootBootstrapOutputContract.Kind.INITIAL_POLICY,original,SharedSourceFiles.nativeFile(target));
        var stage=new Stage(List.of(created),new RootBootstrapOutputGuard.Accounting(RootBootstrapOutputGuard.Status.ADMITTED,0,0,0,1,0));
        RootProfileBootstrapSession.verifyQuote(request,quote.phase(),quote);RootProfileBootstrapSession.verifyStage(quote,stage);
        var progress=List.of(new RootProfileBootstrapSession.Progress(quote.phase(),RootProfileBootstrapSession.PhaseState.CREATED,
                data("quote-ref-DATA.json"),null,List.of(created)));
        String status="INITIAL_SAVED_MATERIALIZED_POLICY_CREATED_NO_GAME_ADMISSION";
        byte[] finalFrame=line(new Emission<>(status,scene.machine(),Instant.now().toString(),created));
        RootProfileBootstrapSession.verifyFinal(request,progress,finalFrame);
        assertThrows(IOException.class,()->RootProfileBootstrapSession.verifyFinal(request,progress,
                line(new Emission<>("INITIAL_SAVED_NATIVE_POLICY_CREATED_NO_GAME_ADMISSION",scene.machine(),Instant.now().toString(),created))));
        var swapped=new RootProfileBootstrapInputs.Created(RootBootstrapOutputContract.Kind.ORIGINAL_DRIVER_RUN_PROFILE,original,created.nativeFile());
        assertThrows(IOException.class,()->RootProfileBootstrapSession.verifyFinal(request,progress,
                line(new Emission<>(status,scene.machine(),Instant.now().toString(),swapped))));
    }

    @Test void mappedSessionRejectsWrongRoleOrTargetAtTheActualQuoteConsumer()throws Exception {
        Scene scene=scene();var request=session(scene,scene.review());
        var wrong=quote(scene,RootBootstrapOutputContract.Kind.PROFILE_ENVIRONMENT,"xar-autoplayer-environment.json");
        assertThrows(IOException.class,()->RootProfileBootstrapSession.verifyQuote(request,wrong.phase(),wrong));
        var crossed=quote(scene,RootBootstrapOutputContract.Kind.INITIAL_POLICY,"other-policy.json");
        assertThrows(IOException.class,()->RootProfileBootstrapSession.verifyQuote(request,crossed.phase(),crossed));
        var valid=quote(scene,RootBootstrapOutputContract.Kind.INITIAL_POLICY,"policy.json");
        var alias=new OrdinaryQuote(valid.schema(),"INITIAL_SAVED_NATIVE_POLICY",valid.machineId(),valid.reviewAtUtc(),
                valid.assetRoot(),valid.outputs(),valid.outputDirectories(),valid.retainedInputs(),valid.authority());
        assertThrows(IOException.class,()->RootProfileBootstrapSession.verifyQuote(request,alias.phase(),alias));
    }

    @Test void mappedProducerInputsRejectWindowMismatchBeforeReadingUnqualifiedPlanData()throws Exception {
        Scene scene=scene();var request=session(scene,Instant.parse(scene.review()).plusSeconds(1).toString());
        IOException refused=assertThrows(IOException.class,()->RootProfileBootstrapSession.producerInputs(request));
        assertTrue(refused.getMessage().contains("exact machine/deadline"));
        assertFalse(Files.exists(scene.asset().resolve("policy.json")));
    }

    @Test void actualCapturedMappedLfReachesPublicDeclarationAndColdQuoteReadback()throws Exception {
        Scene scene=scene();var quote=quote(scene,RootBootstrapOutputContract.Kind.INITIAL_POLICY,"policy.json");
        byte[] frame=RootBootstrapProtocol.quoteLine(quote);
        byte[] original=RootProfileBootstrapSession.issuerQuoteOriginal(Mode.INITIAL_SAVED_MATERIALIZED_POLICY,frame);
        assertArrayEquals(frame,original);FileRef exactQuote=write(root.resolve("captured-issuer-quote.json"),original);
        var request=new RootProfileBootstrapCommand.IssuerDeclarationRequest(
                "xar.java-root-bootstrap-issuer-declaration-request/v1",scene.machine(),scene.review(),"mapped-public-issuer",
                exactQuote,scene.replies().toString(),scene.replies().resolve("declaration.json").toString(),65536,262144,65536,64);
        var actual=RootProfileBootstrapCommand.declareOutput(request,Clock.systemUTC());
        var declaration=RootBootstrapOutputContract.decode(Files.readAllBytes(Path.of(actual.declaration().original().path())),RootBootstrapOutputContract.Declaration.class);
        assertEquals(quote.outputs(),declaration.outputs());assertEquals(quote.assetRoot(),declaration.assetRoot());
        assertEquals(quote,RootProfileBootstrapSession.read(exactQuote,RootBootstrapProtocol.FRAME_BYTES-1,Quote.class));
        assertThrows(IOException.class,()->RootProfileBootstrapSession.issuerQuoteOriginal(Mode.INITIAL_SAVED_MATERIALIZED_POLICY,
                java.util.Arrays.copyOf(frame,frame.length-1)));
        assertArrayEquals(RootBootstrapProtocol.trim(frame),RootProfileBootstrapSession.issuerQuoteOriginal(Mode.ORIGINAL_DRIVER_RUN_PROFILE,frame));
    }

    @Test @org.junit.jupiter.api.Timeout(30)
    void actualMappedPhaseEofProducesNoStageAndLexicalOwnerReleasesItsRealCloneCustody()throws Exception {
        Path profile=Files.createDirectories(root.resolve("profile/save games")).getParent(),state=Files.createDirectory(root.resolve("state"));
        Path source=Files.createDirectory(root.resolve("old")).resolve("checkpoint.ck3");Files.writeString(source,"original-software-SAVE");
        var original=files.observe(source).orElseThrow();Path actual=profile.resolve("save games/checkpoint.ck3");files.copyNew(original,actual);
        var manifest=StrictJson.object().put("environment_sha256","e".repeat(64)).put("profile_dir",profile.toString()).put("state_dir",state.toString());
        manifest.putObject("rules").putArray("profile");manifest.putObject("load_profile").putArray("enabled_mods");
        FileRef env=write(root.resolve("ENV-DATA.json"),StrictJson.canonical(manifest));
        Instant now=Instant.now(),deadline=now.plusSeconds(240);Clock clock=Clock.fixed(now,java.time.ZoneOffset.UTC);
        String machine=WindowsJobProcess.currentMachineId();FileRef meta=data("plan-metadata-DATA.json");
        FileRef nativeEnvironment=data("native-environment-DATA.json"),nativeBuild=data("native-build-DATA.json"),
                nativeRegistration=data("native-registration-DATA.json");
        var sources=LaunchSourceBinding.accept(new LaunchSourceBinding.Review(machine,deadline,meta,meta,meta,
                new NativeLaunchEvidence.Inputs(nativeEnvironment,nativeBuild,nativeRegistration),root,List.of()));
        var plan=new NativeLaunchPlan("mapped-eof-fixture","mapped-eof-session",sources,profile,state,root.resolve("evidence"),
                "\\\\.\\pipe\\mapped-eof-fixture","fixture-bridge","fixture-adapter",new NativeLaunchPlan.SavedGame("checkpoint",FileRef.measure(source)),
                false,NativeLaunchPlan.WindowPolicy.MINIMIZED_NO_ACTIVATE,Map.of(),1L<<30,64L<<20,deadline,Duration.ofSeconds(5),Duration.ofSeconds(30),
                new SteamOfflineProbe.Plan(machine,data("steam.exe"),deadline),NativeLaunchPlan.PreparedProfile.explicit(env,ProfileKind.SAVED_VANILLA,List.of(),List.of(env)),32);
        var frame=new ProposalLifecycle.ObservationIdentity(machine,new GameGeneration(123,new PythonOnlyUInt64(BigInteger.valueOf(100))),
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(29829),BigInteger.ONE,BigInteger.valueOf(240)),
                        "native:1",BigInteger.ONE,"episode-1"),1);
        FileRef driver=data("Driver-DATA.json"),ack=data("ack-DATA.json");
        var pair=new CheckpointPair(original,files.observe(Path.of(driver.path())).orElseThrow(),frame,"lineage-1",1,"save-1",exact(ack),now);
        FileRef pairRef=write(root.resolve("pair.json"),CheckpointPairCodec.encode(pair));
        FileRef planRef=write(root.resolve("plan-DATA.json"),NativeLaunchPlanCodec.toJson(NativeLaunchPlanCodec.describe(plan)).toString().getBytes(StandardCharsets.UTF_8));
        FileRef outer=data("outer-request-DATA.json");Path target=Files.createDirectory(root.resolve("policy-assets")).resolve("policy.json");
        var existing=NativeSavedGamePreparation.requirePrepared(plan,original,clock);
        RootProfileBootstrapInputs.Prepared prepared;var output=new ByteArrayOutputStream();
        try(var held=NativeSavedGameClone.qualify(plan,original)) {
            prepared=RootProfileBootstrapInputs.initialSavedMaterializedPolicy(env,plan,pair,exact(planRef),exact(pairRef),held,target)
                    .withExistingAllocatedInput(existing);
            var previousIn=System.in;var previousOut=System.out;
            try(var capture=new PrintStream(output,true,StandardCharsets.UTF_8)) {
                System.setIn(new ByteArrayInputStream(new byte[0]));System.setOut(capture);
                Exception refused=assertThrows(Exception.class,()->RootProfileBootstrapCommand.phase(null,
                        "INITIAL_SAVED_MATERIALIZED_POLICY",prepared,deadline.toString(),clock,SharedSourceFiles.observe(Path.of(outer.path()))));
                Throwable cause=refused;while(cause.getCause()!=null)cause=cause.getCause();
                assertTrue(cause instanceof IOException);assertTrue(cause.getMessage().contains("input ended before this phase"));
            } finally {System.setIn(previousIn);System.setOut(previousOut);}
            held.requireCurrent(plan,original);assertFalse(Files.exists(target));
        }
        var quote=RootBootstrapProtocol.line(output.toByteArray(),Quote.class);
        assertEquals("INITIAL_SAVED_MATERIALIZED_POLICY",quote.phase());assertEquals(1,quote.outputs().size());
        assertEquals(RootBootstrapOutputContract.Kind.INITIAL_POLICY,quote.outputs().getFirst().kind());
        assertThrows(UncheckedIOException.class,prepared::quote);
        Files.writeString(actual,"clone is writable after the failed phase owner closes");files.verify(original);
        assertFalse(Files.exists(target));
    }
    private static byte[] line(Object value)throws IOException {
        byte[] bytes=RootBootstrapProtocol.encode(value,RootBootstrapProtocol.FRAME_BYTES-1);
        byte[] result=java.util.Arrays.copyOf(bytes,bytes.length+1);result[result.length-1]='\n';return result;
    }
}
