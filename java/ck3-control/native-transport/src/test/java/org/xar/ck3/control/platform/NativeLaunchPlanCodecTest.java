package org.xar.ck3.control.platform;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

final class NativeLaunchPlanCodecTest {
    @TempDir Path temporary;
    private ControlBuild.FileRef ref(String name){return new ControlBuild.FileRef(temporary.resolve(name).toAbsolutePath().toString(),1,"a".repeat(64));}
    private NativeLaunchPlanCodec.Configuration configuration(NativeLaunchPlan.Load load){
        Instant deadline=Instant.parse("2030-01-01T00:00:00Z");
        var review=new LaunchSourceBinding.Review("software-only",deadline,ref("ck3.exe"),ref("xar_ck3_bridge.dll"),ref("xar_ck3_bridge_injector.exe"),
                new NativeLaunchEvidence.Inputs(ref("environment-actual.json"),ref("build-actual.json"),ref("registration-actual.json")),temporary,List.of(ref("classes.jar")));
        var prepared=new NativeLaunchPlan.PreparedProfile(ref("manifest.json"),temporary.resolve("mod"),"mod/example.mod",List.of(ref("prepared-input")),List.of(ref("mod/descriptor.mod")));
        return new NativeLaunchPlanCodec.Configuration("request","session",review,temporary,temporary.resolve("state"),temporary.resolve("evidence"),"\\\\.\\pipe\\software-only","bridge-v1","adapter-v1",load,false,
                NativeLaunchPlan.WindowPolicy.MINIMIZED_NO_ACTIVATE,Map.of("SOFTWARE_TEST","a=b"),9L<<30,128L<<20,deadline,Duration.ofSeconds(10),Duration.ofMinutes(2),
                new SteamOfflineProbe.Plan("software-only",ref("steam.exe"),deadline),prepared,128);
    }
    @Test void producerAndStrictConsumerRoundTripBothLoadBranchesWithoutMintingAdmission(){
        for(var load:List.of(new NativeLaunchPlan.NewGame(),new NativeLaunchPlan.SavedGame("罗贝尔 1066",ref("罗贝尔 1066.ck3")))){
            var original=configuration(load);byte[] raw=StrictJson.canonical(NativeLaunchPlanCodec.toJson(original),NativeLaunchPlanCodec.MAXIMUM_BYTES);
            assertEquals(original,NativeLaunchPlanCodec.fromJson(StrictJson.parse(raw,NativeLaunchPlanCodec.MAXIMUM_BYTES)));
        }
    }
    @Test void malformedConfigurationAndChangedExactBytesRejectBeforeAnyAdmission()throws Exception{
        var valid=NativeLaunchPlanCodec.toJson(configuration(new NativeLaunchPlan.NewGame()));
        var wrong=valid.deepCopy();wrong.put("game_memory_bytes",1.0);assertThrows(IllegalArgumentException.class,()->NativeLaunchPlanCodec.fromJson(wrong));
        var missing=valid.deepCopy();missing.remove("review");assertThrows(IllegalArgumentException.class,()->NativeLaunchPlanCodec.fromJson(missing));
        var extra=valid.deepCopy();extra.put("ready",true);assertThrows(IllegalArgumentException.class,()->NativeLaunchPlanCodec.fromJson(extra));
        var bool=valid.deepCopy();bool.put("injector_timeout_millis",true);assertThrows(IllegalArgumentException.class,()->NativeLaunchPlanCodec.fromJson(bool));
        var duplicate=StrictJson.canonical(valid,NativeLaunchPlanCodec.MAXIMUM_BYTES);
        Path file=temporary.resolve("plan.json");Files.write(file,duplicate);var measured=ControlBuild.FileRef.measure(file);Files.writeString(file,"{}");
        assertThrows(java.io.IOException.class,()->NativeLaunchPlan.readExact(new ExactRef(measured.path(),measured.bytes(),measured.sha256()),expected->{throw new AssertionError("Changed config must reject before Native reader");}));
    }
    @Test void legacyReadyBuildAndMissingActualRegistrationCannotRoundTripAsCurrentQualification(){
        var valid=NativeLaunchPlanCodec.toJson(configuration(new NativeLaunchPlan.NewGame()));
        var old=valid.deepCopy();old.put("schema","xar.java-game-launch-plan/v1");
        assertThrows(IllegalArgumentException.class,()->NativeLaunchPlanCodec.fromJson(old));
        var legacy=valid.deepCopy();var review=(com.fasterxml.jackson.databind.node.ObjectNode)legacy.get("review");
        review.remove("native_evidence");review.set("native_build_result",valid.path("review").path("native_evidence").path("build_actual"));
        assertThrows(IllegalArgumentException.class,()->NativeLaunchPlanCodec.fromJson(legacy));
        var missing=valid.deepCopy();((com.fasterxml.jackson.databind.node.ObjectNode)missing.path("review").path("native_evidence")).remove("registration_actual");
        assertThrows(IllegalArgumentException.class,()->NativeLaunchPlanCodec.fromJson(missing));
    }
    @Test void partialNativeEvidenceCannotSatisfyTheBridgeSourceAndOutputClosure(){
        var config=configuration(new NativeLaunchPlan.NewGame());var review=config.review();
        var expected=new NativeLaunchEvidence.Expected(review.machineId(),review.nativeSourceRoot(),List.of(ref("src/bridge.cpp")),
                review.bridgeDll(),review.injector(),review.nativeEvidence());
        assertThrows(IllegalArgumentException.class,()->new NativeLaunchEvidence.Proof(expected,review.nativeEvidence().references()));
        var closure=new java.util.ArrayList<>(review.nativeEvidence().references());closure.addAll(expected.completeSources());closure.add(expected.bridgeDll());closure.add(expected.injector());
        assertEquals(expected,new NativeLaunchEvidence.Proof(expected,closure).expected());
        closure.add(expected.injector());assertThrows(IllegalArgumentException.class,()->new NativeLaunchEvidence.Proof(expected,closure));
    }
    @Test void vanillaNeedsNoPreparedEnvironmentForNewOrSavedGame() throws Exception {
        for(var load:List.of(new NativeLaunchPlan.NewGame(),new NativeLaunchPlan.SavedGame("save",ref("save.ck3")))) {
            var json=NativeLaunchPlanCodec.toJson(configuration(load));
            json.put("schema","xar.java-game-launch-plan/v4");json.remove("prepared_profile");
            var review=(com.fasterxml.jackson.databind.node.ObjectNode)json.get("review");
            for(String name:List.of("machine_id","expires_at","native_evidence","native_source_root","complete_runtime_sources"))review.remove(name);
            var decoded=NativeLaunchPlanCodec.fromJson(json);
            var profile=decoded.preparedProfile();
            assertInstanceOf(NativeLaunchPlan.PreparedProfile.NoMods.class,profile.declaration());
            assertTrue(profile.optionalEnvironmentManifest().isEmpty());
            assertTrue(profile.productionRoots().isEmpty());assertTrue(profile.preparedInputs().isEmpty());
            assertThrows(IllegalStateException.class,profile::environmentManifest);
            assertThrows(IllegalStateException.class,profile::kind);
            var plan=decoded.accept(expected->{throw new AssertionError("vanilla configuration must not qualify historical Native evidence");});
            assertEquals("-userdir="+temporary,plan.gameArguments().get(1));
            var encoded=NativeLaunchPlanCodec.toJson(decoded);
            assertEquals("xar.java-game-launch-plan/v4",encoded.path("schema").textValue());
            assertFalse(encoded.has("prepared_profile"));
            byte[] raw=StrictJson.canonical(encoded,NativeLaunchPlanCodec.MAXIMUM_BYTES);
            assertEquals(decoded,NativeLaunchPlanCodec.fromJson(StrictJson.parse(raw,NativeLaunchPlanCodec.MAXIMUM_BYTES)));
        }
    }
    @Test void vanillaRejectsNullOrFakePreparedProfileAndRetainsRequiredBusinessFields() {
        var json=NativeLaunchPlanCodec.toJson(configuration(new NativeLaunchPlan.NewGame()));
        json.put("schema","xar.java-game-launch-plan/v4");json.remove("prepared_profile");
        var nullable=json.deepCopy();nullable.putNull("prepared_profile");
        assertThrows(IllegalArgumentException.class,()->NativeLaunchPlanCodec.fromJson(nullable));
        var empty=json.deepCopy();empty.set("prepared_profile",StrictJson.object());
        assertThrows(IllegalArgumentException.class,()->NativeLaunchPlanCodec.fromJson(empty));
        var legacy=json.deepCopy();legacy.put("schema","xar.java-game-launch-plan/v2");
        assertThrows(IllegalArgumentException.class,()->NativeLaunchPlanCodec.fromJson(legacy));
        var missing=json.deepCopy();missing.remove("review");
        assertThrows(IllegalArgumentException.class,()->NativeLaunchPlanCodec.fromJson(missing));
        var wrong=json.deepCopy();wrong.put("debug_mode",1);
        assertThrows(IllegalArgumentException.class,()->NativeLaunchPlanCodec.fromJson(wrong));
    }
    @Test void legacySavedVanillaKeepsItsActualEnvironmentMetadataAndV3Wire() {
        var json=NativeLaunchPlanCodec.toJson(configuration(new NativeLaunchPlan.SavedGame("save",ref("save.ck3"))));
        var old=json.get("prepared_profile");var profile=StrictJson.object();
        profile.put("kind","SAVED_VANILLA");profile.set("environment_manifest",old.get("environment_manifest"));
        profile.putArray("production_roots");profile.set("prepared_inputs",old.get("prepared_inputs"));
        json.put("schema","xar.java-game-launch-plan/v3");json.set("prepared_profile",profile);
        var decoded=NativeLaunchPlanCodec.fromJson(json);
        assertEquals(org.xar.ck3.control.build.NativeRunProfileManifest.ProfileKind.SAVED_VANILLA,decoded.preparedProfile().kind());
        assertTrue(decoded.preparedProfile().optionalEnvironmentManifest().isPresent());
        assertEquals(json,NativeLaunchPlanCodec.toJson(decoded));
    }
    @Test void nativeBackendAndScopedTemporaryPathsRoundTripThroughTheActualProducerAndConsumer(){
        var valid=NativeLaunchPlanCodec.toJson(configuration(new NativeLaunchPlan.NewGame()));
        var environment=(com.fasterxml.jackson.databind.node.ObjectNode)valid.get("environment");
        environment.put("TEMP",temporary.resolve("temp").toString());
        environment.put("TMP",temporary.resolve("tmp").toString());
        environment.put("XAR_CK3_BRIDGE_MODE","native-headless");
        environment.put("XAR_CK3_BRIDGE_PIPE","\\\\.\\pipe\\software-only");
        var decoded=NativeLaunchPlanCodec.fromJson(valid);
        byte[] raw=StrictJson.canonical(NativeLaunchPlanCodec.toJson(decoded),NativeLaunchPlanCodec.MAXIMUM_BYTES);
        assertEquals(decoded,NativeLaunchPlanCodec.fromJson(StrictJson.parse(raw,NativeLaunchPlanCodec.MAXIMUM_BYTES)));
        assertEquals(temporary.resolve("tmp").toString(),decoded.environment().get("TMP"));
        var hybrid=valid.deepCopy();((com.fasterxml.jackson.databind.node.ObjectNode)hybrid.get("environment")).put("XAR_CK3_BRIDGE_MODE","hybrid-fallback");
        assertThrows(IllegalArgumentException.class,()->NativeLaunchPlanCodec.fromJson(hybrid));
        var wrongPipe=valid.deepCopy();((com.fasterxml.jackson.databind.node.ObjectNode)wrongPipe.get("environment")).put("XAR_CK3_BRIDGE_PIPE","\\\\.\\pipe\\different");
        assertThrows(IllegalArgumentException.class,()->NativeLaunchPlanCodec.fromJson(wrongPipe));
        var duplicate=valid.deepCopy();((com.fasterxml.jackson.databind.node.ObjectNode)duplicate.get("environment")).put("tmp",temporary.resolve("tmp").toString());
        assertThrows(IllegalArgumentException.class,()->NativeLaunchPlanCodec.fromJson(duplicate));
    }
}
