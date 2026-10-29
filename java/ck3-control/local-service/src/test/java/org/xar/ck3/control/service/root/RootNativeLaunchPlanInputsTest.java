package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.platform.LaunchSourceBinding;
import org.xar.ck3.control.platform.NativeBridgeLaunchEvidence;
import org.xar.ck3.control.platform.NativeLaunchEvidence;
import org.xar.ck3.control.platform.NativeLaunchPlan;
import org.xar.ck3.control.platform.NativeLaunchPlanCodec;
import org.xar.ck3.control.platform.SteamOfflineProbe;

/** DATA cases never mint a source binding. The final case requires actual Native originals and a real output card. */
final class RootNativeLaunchPlanInputsTest {
    private static final String FIXTURE="xar.root.nativePlan.publication.fixture";
    @TempDir Path temporary;

    private FileRef data(String name) {
        return new FileRef(temporary.resolve(name).toAbsolutePath().normalize().toString(),1,"a".repeat(64));
    }
    private NativeLaunchPlanCodec.Configuration configuration(NativeLaunchPlan.Load load,Map<String,String> environment) {
        Instant deadline=Instant.now().plus(Duration.ofMinutes(20));
        var review=new LaunchSourceBinding.Review("software-data-only",deadline,data("ck3.exe"),
                data("xar_ck3_bridge.dll"),data("xar_ck3_bridge_injector.exe"),
                new NativeLaunchEvidence.Inputs(data("native-env.json"),data("native-build.json"),data("native-register.json")),
                temporary,List.of(data("classes.jar")));
        var profile=new NativeLaunchPlan.PreparedProfile(data("profile-environment.json"),temporary.resolve("production"),
                "mod/xar_autoplayer.mod",List.of(data("actual-profile-input")),List.of(data("production/descriptor.mod")));
        return new NativeLaunchPlanCodec.Configuration("first-plan","session-first-plan",review,temporary.resolve("profile"),
                temporary.resolve("state"),temporary.resolve("evidence"),"\\\\.\\pipe\\first-plan-data","explicit-bridge",
                "explicit-adapter",load,false,NativeLaunchPlan.WindowPolicy.MINIMIZED_NO_ACTIVATE,environment,
                8L<<30,128L<<20,deadline,Duration.ofSeconds(10),Duration.ofMinutes(2),
                new SteamOfflineProbe.Plan("software-data-only",data("steam.exe"),deadline),profile,128);
    }
    private RootNativeLaunchPlanInputs.Request request(NativeLaunchPlanCodec.Configuration data) {
        return new RootNativeLaunchPlanInputs.Request(data,temporary.resolve(RootNativeLaunchPlanInputs.FILE_NAME),
                data.deadline().minusSeconds(1));
    }

    @Test void soleProducerDataEncodingReachesTheStrictConsumerForBothLoadBranches() throws Exception {
        for (var load:List.of(new NativeLaunchPlan.NewGame(),
                new NativeLaunchPlan.SavedGame("罗贝尔 1066",data("罗贝尔 1066.ck3")))) {
            var original=configuration(load,Map.of("EXPLICIT_DATA","a=b"));
            byte[] bytes=RootNativeLaunchPlanInputs.encodeConfiguration(original);
            assertEquals(original,NativeLaunchPlanCodec.fromJson(StrictJson.parse(bytes,NativeLaunchPlanCodec.MAXIMUM_BYTES)));
            assertFalse(Files.exists(request(original).target()));
        }
    }
    @Test void firstTargetAndReviewAreExplicitAndCannotExtendTheNativeReview() {
        var data=configuration(new NativeLaunchPlan.NewGame(),Map.of());
        assertThrows(IllegalArgumentException.class,()->new RootNativeLaunchPlanInputs.Request(
                data,Path.of("native-launch-plan.json"),data.deadline()));
        assertThrows(IllegalArgumentException.class,()->new RootNativeLaunchPlanInputs.Request(
                data,temporary.resolve("another.json"),data.deadline()));
        assertThrows(IllegalArgumentException.class,()->new RootNativeLaunchPlanInputs.Request(
                data,temporary.resolve(RootNativeLaunchPlanInputs.FILE_NAME),data.deadline().plusSeconds(1)));
    }
    @Test void expiredPublicationRefusesBeforeAnyMissingNativeInputOrOutput() {
        var data=configuration(new NativeLaunchPlan.NewGame(),Map.of());
        var request=request(data);
        IOException failure=assertThrows(IOException.class,()->RootNativeLaunchPlanInputs.prepare(
                request,Clock.fixed(request.reviewAt(),ZoneOffset.UTC)));
        assertTrue(failure.getMessage().contains("expired"));
        assertFalse(Files.exists(request.target()));
    }
    @Test void existingOriginalIsNeverOverwrittenOrReplayed() throws Exception {
        var request=request(configuration(new NativeLaunchPlan.NewGame(),Map.of()));
        byte[] original="original unknown publication".getBytes(java.nio.charset.StandardCharsets.UTF_8);
        Files.write(request.target(),original);
        IOException failure=assertThrows(IOException.class,()->RootNativeLaunchPlanInputs.prepare(request,Clock.systemUTC()));
        assertTrue(failure.getMessage().contains("already exists"));
        assertArrayEquals(original,Files.readAllBytes(request.target()));
    }
    @Test void absentActualProfileCannotProduceAQuoteOrPlan() {
        var request=request(configuration(new NativeLaunchPlan.NewGame(),Map.of()));
        assertThrows(IOException.class,()->RootNativeLaunchPlanInputs.prepare(request,Clock.systemUTC()));
        assertFalse(Files.exists(request.target()));
    }
    @Test void explicitDebugCannotContradictTheCurrentProductionProfile() {
        var tree=NativeLaunchPlanCodec.toJson(configuration(new NativeLaunchPlan.NewGame(),Map.of()));
        tree.put("debug_mode",true);
        var request=request(NativeLaunchPlanCodec.fromJson(tree));
        IOException failure=assertThrows(IOException.class,()->RootNativeLaunchPlanInputs.prepare(request,Clock.systemUTC()));
        assertTrue(failure.getMessage().contains("production profile"));
        assertFalse(Files.exists(request.target()));
    }
    @Test void legacyProfileDataCannotAcquireCurrentJavaPreparedInputs() throws Exception {
        Path old=temporary.resolve("old-python-environment.json");
        Files.writeString(old,"{\"format_version\":1,\"prepared\":true}");
        FileRef actual=FileRef.measure(old);
        assertThrows(IOException.class,()->RootNativeLaunchPlanInputs.preparedProfile(actual));
        assertFalse(Files.exists(temporary.resolve(RootNativeLaunchPlanInputs.FILE_NAME)));
    }
    @Test void malformedNativeReviewAndCoercedNumbersRejectInTheSoleCodec() {
        var valid=NativeLaunchPlanCodec.toJson(configuration(new NativeLaunchPlan.NewGame(),Map.of()));
        var number=valid.deepCopy();number.put("game_memory_bytes",1.0);
        assertThrows(IllegalArgumentException.class,()->NativeLaunchPlanCodec.fromJson(number));
        var missing=valid.deepCopy();
        ((com.fasterxml.jackson.databind.node.ObjectNode)missing.path("review").path("native_evidence")).remove("registration_actual");
        assertThrows(IllegalArgumentException.class,()->NativeLaunchPlanCodec.fromJson(missing));
        var old=valid.deepCopy();old.put("schema","xar.java-game-launch-plan/v1");
        assertThrows(IllegalArgumentException.class,()->NativeLaunchPlanCodec.fromJson(old));
        var extra=valid.deepCopy();extra.put("ready",true);
        assertThrows(IllegalArgumentException.class,()->NativeLaunchPlanCodec.fromJson(extra));
    }
    @Test void oversizedOrInvalidEnvironmentDataCannotBypassTheFinitePlanCodec() {
        Map<String,String> tooMany=new HashMap<>();
        for (int i=0;i<257;i++) tooMany.put("K"+i,"v");
        assertThrows(IOException.class,()->RootNativeLaunchPlanInputs.encodeConfiguration(
                configuration(new NativeLaunchPlan.NewGame(),tooMany)));
        assertThrows(IllegalArgumentException.class,()->configuration(
                new NativeLaunchPlan.NewGame(),Map.of("K","a\0b")));
        Map<String,String> tooLarge=new HashMap<>();
        for (int i=0;i<64;i++) tooLarge.put("K"+i,"x".repeat(32768));
        assertThrows(IOException.class,()->RootNativeLaunchPlanInputs.encodeConfiguration(
                configuration(new NativeLaunchPlan.NewGame(),tooLarge)));
    }

    @Test void actualV4ProducerOutputJoinsOrdinaryInputsAndSurvivesThePlanCodec()throws Exception {
        FileRef environment=actualFile("environment.json","{}");
        var run=RootOriginalDriverRunProfileProducerTest.profile(Path.of(environment.path()));
        FileRef producer=actualFile("producer.json",new String(RootOriginalDriverRunProfileProducer.encode(
                new RootOriginalDriverRunProfileProducer.Request(run)),java.nio.charset.StandardCharsets.UTF_8));
        Path target=temporary.resolve("original-run-profile.json");
        var prepared=RootOriginalDriverRunProfileProducer.prepare(producer,target,RootOriginalDriverRunProfileProducerTest.CLOCK);
        Files.write(target,prepared.bytes());prepared.verifyCreated();FileRef actual=FileRef.measure(target);
        FileRef first=actualFile("first.json","first"),second=actualFile("second.json","second");
        var ordinary=ordinaryProfile(environment,List.of(first,second));
        var merged=RootNativeLaunchPlanInputs.ordinaryPreparedProfile(ordinary,List.of(actual,second,first));
        assertEquals(List.of(first,second,actual),merged.preparedInputs());
        assertEquals(merged,RootNativeLaunchPlanInputs.ordinaryPreparedProfile(ordinary,List.of(first,actual,second,actual)));
        var tree=NativeLaunchPlanCodec.toJson(configuration(new NativeLaunchPlan.NewGame(),Map.of()));
        var profile=(com.fasterxml.jackson.databind.node.ObjectNode)tree.get("prepared_profile");
        profile.set("prepared_inputs",ControlBuild.strictMapper().valueToTree(merged.preparedInputs()));
        var decoded=NativeLaunchPlanCodec.fromJson(tree);
        assertEquals(merged.preparedInputs(),decoded.preparedProfile().preparedInputs());
        assertTrue(decoded.preparedProfile().preparedInputs().contains(actual));
        assertEquals(run,RootFrozenRunProfile.decode(RootRuntimeDefinitions.read(actual,65536)));
        assertFalse(Files.exists(temporary.resolve(RootNativeLaunchPlanInputs.FILE_NAME)));
    }
    @Test void ordinaryAdditionalInputsRejectMissingChangedAndConflictingExactSources()throws Exception {
        FileRef environment=actualFile("environment.json","{}"),base=actualFile("base.json","base");
        var ordinary=ordinaryProfile(environment,List.of(base));
        assertThrows(IOException.class,()->RootNativeLaunchPlanInputs.ordinaryPreparedProfile(ordinary,List.of(data("missing.json"))));
        var falseRef=new FileRef(base.path(),base.bytes(), "b".repeat(64));
        assertThrows(IOException.class,()->RootNativeLaunchPlanInputs.ordinaryPreparedProfile(ordinary,List.of(falseRef)));
        Files.writeString(Path.of(base.path()),"changed");
        assertThrows(IOException.class,()->RootNativeLaunchPlanInputs.ordinaryPreparedProfile(ordinary,List.of()));
    }
    @Test void ordinaryInputMergePreservesBaseOrderAndSortsOnlyIndependentOriginals()throws Exception {
        FileRef environment=actualFile("environment.json","{}"),base=actualFile("base.json","base"),
                a=actualFile("a.json","a"),z=actualFile("z.json","z");
        var ordinary=ordinaryProfile(environment,List.of(base));
        assertEquals(List.of(base,a,z),RootNativeLaunchPlanInputs.ordinaryPreparedProfile(ordinary,List.of(z,a)).preparedInputs());
        assertEquals(ordinary,RootNativeLaunchPlanInputs.ordinaryPreparedProfile(ordinary,List.of(base)));
    }
    private NativeLaunchPlan.PreparedProfile ordinaryProfile(FileRef environment,List<FileRef> inputs)throws IOException {
        Path production=Files.createDirectory(temporary.resolve("production"));
        Path descriptor=production.resolve("descriptor.mod");Files.writeString(descriptor,"name=\"software-data-only\"\n");
        return new NativeLaunchPlan.PreparedProfile(environment,production,"mod/xar_autoplayer.mod",inputs,
                List.of(SharedSourceFiles.observe(descriptor).source()));
    }
    private FileRef actualFile(String name,String text)throws IOException {
        Path file=temporary.resolve(name);Files.writeString(file,text);return SharedSourceFiles.observe(file).source();
    }

    /** A separate exact fixture contains actual source/review fields and the independent card, never a plan template. */
    private record ActualPublicationFixture(String schema,String machineId,String requestId,String sessionId,LaunchSourceBinding.Review review,
            FileRef profileEnvironment,Path evidenceRoot,String pipeName,String bridgeVersion,String adapterId,
            NativeLaunchPlan.WindowPolicy windowPolicy,Map<String,String> environment,long gameMemoryBytes,
            long injectorMemoryBytes,Instant deadline,Duration injectorTimeout,Duration startupTimeout,
            SteamOfflineProbe.Plan steam,int maximumEvidenceRows,Instant publicationReviewAt,Path target,FileRef bootstrapBinding) {
        private ActualPublicationFixture {
            if (!"xar.root-native-launch-plan-publication-fixture/v1".equals(schema)
                    || review==null || !review.machineId().equals(machineId))
                throw new IllegalArgumentException("Exact first-publication fixture and explicit reviewed machine required");
        }
        private NativeLaunchPlanCodec.Configuration configuration() throws IOException {
            var prepared=RootNativeLaunchPlanInputs.preparedProfile(profileEnvironment);
            var manifest=org.xar.ck3.control.build.NativeRunProfileProducer.readVerified(profileEnvironment);
            return new NativeLaunchPlanCodec.Configuration(requestId,sessionId,review,Path.of(manifest.profileDir()),
                    Path.of(manifest.stateDir()),evidenceRoot,pipeName,bridgeVersion,adapterId,new NativeLaunchPlan.NewGame(),
                    false,windowPolicy,environment,gameMemoryBytes,injectorMemoryBytes,deadline,injectorTimeout,startupTimeout,
                    steam,prepared,maximumEvidenceRows);
        }
    }
    @Test void actualNativeInputsProduceTheFirstGuardedOriginalAndBothPhysicalReaders() throws Exception {
        String path=System.getProperty(FIXTURE+".path");
        String count=System.getProperty(FIXTURE+".bytes");
        String sha=System.getProperty(FIXTURE+".sha256");
        assertNotNull(path,"NOT_RUN_REQUIRED: actual Native/profile/publication fixture path");
        assertNotNull(count,"NOT_RUN_REQUIRED: actual fixture bytes");
        assertNotNull(sha,"NOT_RUN_REQUIRED: actual fixture sha256");
        assertTrue(count.matches("[1-9][0-9]*"),"exact positive fixture size");
        FileRef original=new FileRef(path,Long.parseLong(count),sha);
        assertTrue(original.bytes()<=1<<20,"bounded first-publication fixture");
        original.verify();var source=SharedSourceFiles.observe(Path.of(path));
        byte[] bytes;
        try (var input=Files.newInputStream(Path.of(path))) { bytes=input.readNBytes((1<<20)+1); }
        assertEquals(original.bytes(),bytes.length);
        StrictJson.parse(bytes,1<<20);
        var fixture=ControlBuild.strictMapper().readValue(bytes,ActualPublicationFixture.class);
        assertEquals(org.xar.ck3.control.build.WindowsJobProcess.currentMachineId(),fixture.machineId());
        var configuration=fixture.configuration(); Clock clock=Clock.systemUTC();
        var request=new RootNativeLaunchPlanInputs.Request(configuration,fixture.target(),fixture.publicationReviewAt());
        var prepared=RootNativeLaunchPlanInputs.prepare(request,clock);
        assertEquals(RootBootstrapOutputContract.Kind.NATIVE_LAUNCH_PLAN,prepared.quote().kind());
        assertFalse(Files.exists(fixture.target()),"quote/prepare never writes");
        try (var authority=RootBootstrapOutputGuard.readExact(fixture.bootstrapBinding(),clock)) {
            var published=prepared.createNew(authority,clock);
            assertEquals(configuration,NativeLaunchPlanCodec.describe(published.requireCurrent(clock)));
            var cold=NativeLaunchPlan.readExact(published.original(),new NativeBridgeLaunchEvidence());
            assertEquals(configuration,NativeLaunchPlanCodec.describe(cold));
            org.xar.ck3.control.platform.NativePrelaunchInputs.requireCurrent(cold,clock);
            assertEquals(1,authority.accounting().completedOutputs());
            assertThrows(IOException.class,()->prepared.createNew(authority,clock));
        }
        SharedSourceFiles.assertUnchanged(source);original.verify();
    }
}
