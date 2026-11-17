package org.xar.ck3.control.platform;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.function.Consumer;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.NativeRunProfileManifest.ProfileKind;
import org.xar.ck3.control.contracts.StrictJson;

/** Public DATA contracts only: no source qualification, Native custody or Game launch. */
final class NativeLaunchPlanSettingsSeedCodecTest {
    @TempDir Path temporary;
    private static final String V5="xar.java-game-launch-plan/v5";
    private static final String SEED="pdx_settings_seed";

    private ControlBuild.FileRef ref(String name) {
        return new ControlBuild.FileRef(temporary.resolve(name).toAbsolutePath().toString(),1,"a".repeat(64));
    }
    private NativeLaunchPlanCodec.Configuration configuration(NativeLaunchPlan.Load load,NativeLaunchPlan.PreparedProfile profile) {
        Instant deadline=Instant.parse("2030-01-01T00:00:00Z");
        var review=new LaunchSourceBinding.Review("software-only",deadline,ref("ck3.exe"),ref("bridge.dll"),ref("injector.exe"),
                new NativeLaunchEvidence.Inputs(ref("environment-actual.json"),ref("build-actual.json"),ref("registration-actual.json")),
                temporary,List.of(ref("classes.jar")));
        return new NativeLaunchPlanCodec.Configuration("request","session",review,temporary,temporary.resolve("state"),temporary.resolve("evidence"),
                "\\\\.\\pipe\\software-only","bridge-v1","adapter-v1",load,false,NativeLaunchPlan.WindowPolicy.MINIMIZED_NO_ACTIVATE,
                Map.of("SOFTWARE_TEST","a=b"),9L<<30,128L<<20,deadline,Duration.ofSeconds(10),Duration.ofMinutes(2),
                new SteamOfflineProbe.Plan("software-only",ref("steam.exe"),deadline),profile,128);
    }
    private ObjectNode v5() {
        return NativeLaunchPlanCodec.toJson(configuration(new NativeLaunchPlan.NewGame(),NativeLaunchPlan.PreparedProfile.vanilla(ref("settings.txt"))));
    }
    private void reject(Consumer<ObjectNode> change) {
        ObjectNode value=v5();change.accept(value);
        assertThrows(IllegalArgumentException.class,()->NativeLaunchPlanCodec.fromJson(value));
    }
    private void rejectSeed(Consumer<ObjectNode> change) {
        reject(value->change.accept((ObjectNode)value.get(SEED)));
    }

    @Test void explicitSeedRoundTripsBothLoadModesWithOnlyItsSingleInput() {
        var seed=ref("settings.txt");
        for(var load:List.of(new NativeLaunchPlan.NewGame(),new NativeLaunchPlan.SavedGame("save",ref("save.ck3")))) {
            var profile=NativeLaunchPlan.PreparedProfile.vanilla(seed);
            var original=configuration(load,profile);
            ObjectNode wire=NativeLaunchPlanCodec.toJson(original);
            assertEquals(V5,wire.path("schema").textValue());
            assertFalse(wire.has("prepared_profile"));assertEquals(3,wire.path(SEED).size());
            assertEquals(seed.path(),wire.path(SEED).path("path").textValue());
            assertEquals(seed.bytes(),wire.path(SEED).path("bytes").longValue());
            assertEquals(seed.sha256(),wire.path(SEED).path("sha256").textValue());
            byte[] bytes=StrictJson.canonical(wire,NativeLaunchPlanCodec.MAXIMUM_BYTES);
            var decoded=NativeLaunchPlanCodec.fromJson(StrictJson.parse(bytes,NativeLaunchPlanCodec.MAXIMUM_BYTES));
            assertEquals(original,decoded);assertEquals(wire,NativeLaunchPlanCodec.toJson(decoded));
            var actual=decoded.preparedProfile();
            assertEquals(Optional.of(seed),actual.settingsSeed());assertEquals(List.of(seed),actual.preparedInputs());
            assertEquals(new NativeLaunchPlan.PreparedProfile.NoMods(),actual.declaration());
            assertTrue(actual.optionalEnvironmentManifest().isEmpty());assertTrue(actual.productionRoots().isEmpty());
            assertTrue(actual.ordinary().isEmpty());assertTrue(actual.explicit().isEmpty());assertTrue(actual.noMods().isPresent());
            assertThrows(IllegalStateException.class,actual::environmentManifest);assertThrows(IllegalStateException.class,actual::kind);
            assertThrows(IllegalStateException.class,actual::productionRoot);assertThrows(UnsupportedOperationException.class,()->actual.preparedInputs().clear());
            assertEquals(Objects.hash(Optional.empty(),List.of(seed),new NativeLaunchPlan.PreparedProfile.NoMods()),actual.hashCode());
            assertEquals(profile,NativeLaunchPlan.PreparedProfile.vanilla(seed));
            assertNotEquals(profile,NativeLaunchPlan.PreparedProfile.vanilla(ref("other-settings.txt")));
            assertEquals(original.review(),decoded.review());assertEquals(original.environment(),decoded.environment());
        }
    }

    @Test void legacyConstructorsAndVanillaKeepTheirV4AndEnvironmentSemantics() throws Exception {
        assertNotNull(NativeLaunchPlan.PreparedProfile.class.getDeclaredConstructor(Optional.class,List.class,NativeLaunchPlan.PreparedProfile.Declaration.class));
        assertNotNull(NativeLaunchPlan.PreparedProfile.class.getDeclaredConstructor(ControlBuild.FileRef.class,List.class,NativeLaunchPlan.PreparedProfile.Declaration.class));
        assertEquals(0,NativeLaunchPlan.PreparedProfile.NoMods.class.getRecordComponents().length);
        var empty=NativeLaunchPlan.PreparedProfile.vanilla();
        assertTrue(empty.settingsSeed().isEmpty());assertTrue(empty.preparedInputs().isEmpty());
        assertTrue(empty.optionalEnvironmentManifest().isEmpty());assertTrue(empty.productionRoots().isEmpty());
        assertEquals(empty,NativeLaunchPlan.PreparedProfile.vanilla());
        assertEquals(Objects.hash(Optional.empty(),List.of(),new NativeLaunchPlan.PreparedProfile.NoMods()),empty.hashCode());
        var ordinary=new NativeLaunchPlan.PreparedProfile(ref("manifest.json"),temporary.resolve("mod"),"mod/example.mod",
                List.of(ref("input")),List.of(ref("mod/descriptor.mod")));
        var explicit=NativeLaunchPlan.PreparedProfile.explicit(ref("saved-manifest.json"),ProfileKind.SAVED_VANILLA,List.of(),List.of(ref("input")));
        var profiles=List.of(empty,ordinary,explicit);
        var schemas=List.of("xar.java-game-launch-plan/v4","xar.java-game-launch-plan/v2","xar.java-game-launch-plan/v3");
        for(int i=0;i<profiles.size();i++) {
            var profile=profiles.get(i);
            NativeLaunchPlan.Load load=i==2?new NativeLaunchPlan.SavedGame("save",ref("save.ck3")):new NativeLaunchPlan.NewGame();
            var original=configuration(load,profile);var encoded=NativeLaunchPlanCodec.toJson(original);
            assertEquals(schemas.get(i),encoded.path("schema").textValue());assertFalse(encoded.has(SEED));
            assertEquals(i!=0,encoded.has("prepared_profile"));assertTrue(profile.settingsSeed().isEmpty());
            assertEquals(original,NativeLaunchPlanCodec.fromJson(encoded));
        }
        assertNotEquals(empty,NativeLaunchPlan.PreparedProfile.vanilla(ref("settings.txt")));
    }

    @Test void v5RequiresClosedPositiveBoundedSeedAndNeverAcceptsPreparedProfile() {
        reject(value->value.remove(SEED));reject(value->value.putNull(SEED));reject(value->value.put(SEED,"settings.txt"));
        reject(value->value.putArray(SEED));reject(value->value.putNull("prepared_profile"));
        reject(value->value.set("prepared_profile",StrictJson.object()));
        reject(value->value.put("settings_ready",true));
        for(String field:List.of("path","bytes","sha256"))rejectSeed(seed->seed.remove(field));
        rejectSeed(seed->seed.put("witness",true));rejectSeed(seed->seed.putNull("path"));
        rejectSeed(seed->seed.put("path",true));rejectSeed(seed->seed.put("path","relative/settings.txt"));
        rejectSeed(seed->seed.put("path",temporary.resolve("nested").resolve("..").resolve("settings.txt").toString()));
        rejectSeed(seed->seed.put("sha256","A".repeat(64)));rejectSeed(seed->seed.put("sha256","a".repeat(63)));
        rejectSeed(seed->seed.put("sha256",false));rejectSeed(seed->seed.putNull("sha256"));
        rejectSeed(seed->seed.put("bytes",0));rejectSeed(seed->seed.put("bytes",-1));
        rejectSeed(seed->seed.put("bytes",1048577));rejectSeed(seed->seed.put("bytes",1.0));
        rejectSeed(seed->seed.put("bytes","1"));rejectSeed(seed->seed.put("bytes",true));
        rejectSeed(seed->seed.putNull("bytes"));rejectSeed(seed->seed.put("bytes",BigInteger.ONE.shiftLeft(64)));
        for(long length:List.of(1L,1048576L)) {
            var valid=v5();((ObjectNode)valid.get(SEED)).put("bytes",length);
            assertEquals(length,NativeLaunchPlanCodec.fromJson(valid).preparedProfile().settingsSeed().orElseThrow().bytes());
        }
        assertThrows(NullPointerException.class,()->NativeLaunchPlan.PreparedProfile.vanilla(null));
        var path=temporary.resolve("settings.txt").toString();
        for(long length:List.of(0L,1048577L))
            assertThrows(IllegalArgumentException.class,()->NativeLaunchPlan.PreparedProfile.vanilla(new ControlBuild.FileRef(path,length,"a".repeat(64))));
        assertThrows(IllegalArgumentException.class,()->NativeLaunchPlan.PreparedProfile.vanilla(
                new ControlBuild.FileRef(temporary.resolve("nested").resolve("..").resolve("settings.txt").toString(),1,"a".repeat(64))));
    }

    @Test void olderSchemaVersionsRejectTheNewTopLevelField() {
        var ordinary=new NativeLaunchPlan.PreparedProfile(ref("manifest.json"),temporary.resolve("mod"),"mod/example.mod",
                List.of(ref("input")),List.of(ref("mod/descriptor.mod")));
        var explicit=NativeLaunchPlan.PreparedProfile.explicit(ref("saved-manifest.json"),ProfileKind.SAVED_VANILLA,List.of(),List.of(ref("input")));
        var validOld=List.of(
                NativeLaunchPlanCodec.toJson(configuration(new NativeLaunchPlan.NewGame(),ordinary)),
                NativeLaunchPlanCodec.toJson(configuration(new NativeLaunchPlan.SavedGame("save",ref("save.ck3")),explicit)),
                NativeLaunchPlanCodec.toJson(configuration(new NativeLaunchPlan.NewGame(),NativeLaunchPlan.PreparedProfile.vanilla())));
        for(ObjectNode original:validOld) {
            assertDoesNotThrow(()->NativeLaunchPlanCodec.fromJson(original));
            var extra=original.deepCopy();extra.set(SEED,v5().get(SEED));
            assertThrows(IllegalArgumentException.class,()->NativeLaunchPlanCodec.fromJson(extra));
        }
        var unsupported=validOld.getFirst().deepCopy();unsupported.put("schema","xar.java-game-launch-plan/v1");
        unsupported.set(SEED,v5().get(SEED));
        assertThrows(IllegalArgumentException.class,()->NativeLaunchPlanCodec.fromJson(unsupported));
        var v5WithOrdinary=validOld.getFirst().deepCopy();v5WithOrdinary.put("schema",V5);v5WithOrdinary.set(SEED,v5().get(SEED));
        assertThrows(IllegalArgumentException.class,()->NativeLaunchPlanCodec.fromJson(v5WithOrdinary));
    }

    @Test void seedStaysMetadataAndSurvivesSavedChildPlanWithoutNativeQualification() throws Exception {
        var seed=ref("not-created-settings.txt");assertFalse(Files.exists(Path.of(seed.path())));
        var config=configuration(new NativeLaunchPlan.NewGame(),NativeLaunchPlan.PreparedProfile.vanilla(seed));
        var plan=config.accept(expected->{throw new AssertionError("DATA settings must not qualify Native evidence");});
        assertFalse(Files.exists(Path.of(seed.path())));
        assertThrows(IllegalStateException.class,()->plan.sources().nativeProof());
        var save=ref("save games/child.ck3");
        var child=plan.savedReplacement("original-parent",save,config.deadline());
        assertSame(plan.preparedProfile(),child.preparedProfile());assertSame(plan.sources(),child.sources());
        assertEquals(Optional.of(seed),child.preparedProfile().settingsSeed());
        assertEquals(List.of(seed),child.preparedProfile().preparedInputs());
        assertEquals(new NativeLaunchPlan.SavedGame("child",save),child.load());
        assertEquals(V5,NativeLaunchPlanCodec.toJson(NativeLaunchPlanCodec.describe(child)).path("schema").textValue());
        assertFalse(Files.exists(Path.of(seed.path())));assertFalse(Files.exists(Path.of(save.path())));
        var legacy=NativeLaunchPlanCodec.toJson(configuration(new NativeLaunchPlan.NewGame(),NativeLaunchPlan.PreparedProfile.vanilla()));
        assertEquals("xar.java-game-launch-plan/v4",legacy.path("schema").textValue());assertFalse(legacy.has(SEED));
    }
}
