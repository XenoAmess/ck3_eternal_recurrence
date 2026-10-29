package org.xar.ck3.control.platform;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.file.Path;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.NativeRunProfileManifest.ProfileKind;
import org.xar.ck3.control.contracts.StrictJson;

/** DATA contract and the actual output guard; no source, Steam, process or Game admission is minted. */
final class NativeProfileDomainContractTest {
    @TempDir Path output;
    private FileRef ref(String name){return new FileRef(output.resolve(name).toString(),1,"a".repeat(64));}
    private NativeLaunchPlanCodec.Configuration data(ProfileKind kind) {
        var end=Instant.parse("2030-01-01T00:00:00Z");
        var review=new LaunchSourceBinding.Review("software-only",end,ref("ck3.exe"),ref("bridge.dll"),ref("injector.exe"),
                new NativeLaunchEvidence.Inputs(ref("environment-actual.json"),ref("build-actual.json"),ref("registration-actual.json")),
                output,List.of(ref("runtime.jar")));
        var roots=kind==ProfileKind.SAVED_VANILLA?List.<Path>of():List.of(output.resolve("product-b"),output.resolve("product-a"));
        var profile=NativeLaunchPlan.PreparedProfile.explicit(ref("ENV.json"),kind,roots,List.of(ref("prepared"),ref("later-request")));
        NativeLaunchPlan.Load load=kind==ProfileKind.FRESH_FRONTEND_FIXTURE?new NativeLaunchPlan.NewGame():new NativeLaunchPlan.SavedGame("restored_campaign",ref("restored_campaign.ck3"));
        return new NativeLaunchPlanCodec.Configuration("request","session",review,output,output.resolve("state"),output.resolve("evidence"),
                "\\\\.\\pipe\\software-only","bridge","adapter",load,kind==ProfileKind.SAVED_VANILLA,
                NativeLaunchPlan.WindowPolicy.MINIMIZED_NO_ACTIVATE,Map.of(),9L<<30,128L<<20,end,Duration.ofSeconds(10),Duration.ofMinutes(2),
                new SteamOfflineProbe.Plan("software-only",ref("steam.exe"),end),profile,128);
    }
    @Test void soleCodecKeepsAllExplicitKindsRootOrderAndLateOriginalsWithoutAnOrdinaryAlias() {
        for(var kind:List.of(ProfileKind.SAVED_VANILLA,ProfileKind.SAVED_PRODUCT_ONLY,ProfileKind.FRESH_FRONTEND_FIXTURE)) {
            var original=data(kind);var wire=NativeLaunchPlanCodec.toJson(original);
            assertEquals("xar.java-game-launch-plan/v3",wire.path("schema").textValue());
            assertFalse(wire.path("prepared_profile").has("production_root"));assertFalse(wire.path("prepared_profile").has("enabled_outer_descriptor_ref"));
            var decoded=NativeLaunchPlanCodec.fromJson(StrictJson.parse(StrictJson.canonical(wire,NativeLaunchPlanCodec.MAXIMUM_BYTES),NativeLaunchPlanCodec.MAXIMUM_BYTES));
            assertEquals(original,decoded);assertEquals(original.preparedProfile().productionRoots(),decoded.preparedProfile().productionRoots());
            assertEquals(original.preparedProfile().preparedInputs(),decoded.preparedProfile().preparedInputs());
            assertThrows(IllegalStateException.class,decoded.preparedProfile()::productionRoot);
            assertThrows(IllegalStateException.class,decoded.preparedProfile()::completeProductionFiles);
            var crossed=wire.deepCopy();crossed.put("schema","xar.java-game-launch-plan/v2");
            assertThrows(IllegalArgumentException.class,()->NativeLaunchPlanCodec.fromJson(crossed));
        }
    }
    @Test void strictExplicitWireRejectsMissingNullWrongTypesDomainAndInventedSingletonFields() {
        var actual=NativeLaunchPlanCodec.toJson(data(ProfileKind.SAVED_PRODUCT_ONLY));
        for(String field:List.of("kind","environment_manifest","production_roots","prepared_inputs")) {
            var missing=actual.deepCopy();((ObjectNode)missing.get("prepared_profile")).remove(field);
            assertThrows(IllegalArgumentException.class,()->NativeLaunchPlanCodec.fromJson(missing));
            var nul=actual.deepCopy();((ObjectNode)nul.get("prepared_profile")).putNull(field);
            assertThrows(IllegalArgumentException.class,()->NativeLaunchPlanCodec.fromJson(nul));
        }
        var ordinary=actual.deepCopy();((ObjectNode)ordinary.get("prepared_profile")).put("kind","ORDINARY_PRODUCTION");
        assertThrows(IllegalArgumentException.class,()->NativeLaunchPlanCodec.fromJson(ordinary));
        var alias=actual.deepCopy();((ObjectNode)alias.get("prepared_profile")).put("production_root",output.toString());
        assertThrows(IllegalArgumentException.class,()->NativeLaunchPlanCodec.fromJson(alias));
        for(var wrong:List.of(com.fasterxml.jackson.databind.node.JsonNodeFactory.instance.booleanNode(true),com.fasterxml.jackson.databind.node.JsonNodeFactory.instance.numberNode(3.0))) {
            var input=actual.deepCopy();((ObjectNode)input.path("prepared_profile").path("prepared_inputs").get(0)).set("bytes",wrong);
            assertThrows(IllegalArgumentException.class,()->NativeLaunchPlanCodec.fromJson(input));
        }
        var mismatch=actual.deepCopy();((ObjectNode)mismatch.get("load")).removeAll().put("kind","NEW_GAME");
        assertThrows(IllegalArgumentException.class,()->NativeLaunchPlanCodec.fromJson(mismatch));
        var vanilla=actual.deepCopy();((ObjectNode)vanilla.get("prepared_profile")).put("kind","SAVED_VANILLA");
        assertThrows(IllegalArgumentException.class,()->NativeLaunchPlanCodec.fromJson(vanilla));
    }
    @Test void actualGuardChecksVanillaAndEveryOneOf128ProductionRootsPlusScopedTemporaryPaths()throws Exception {
        var env=Map.of("TEMP",output.resolve("temp").toString(),"TMP",output.resolve("tmp").toString());
        var checked=new ArrayList<Path>();NativeLaunchPolicy.requireOutputs(output,output.resolve("state"),output.resolve("evidence"),List.of(),env,true,checked::add);
        assertEquals(List.of(output,output.resolve("state"),output.resolve("evidence"),output.resolve("temp"),output.resolve("tmp")),checked);
        var roots=new ArrayList<Path>();for(int i=0;i<128;i++)roots.add(output.resolve("product-"+i));
        checked.clear();NativeLaunchPolicy.requireOutputs(output,output.resolve("state"),output.resolve("evidence"),roots,env,true,checked::add);
        assertTrue(checked.containsAll(roots));assertEquals(128,checked.stream().filter(roots::contains).count());
        assertThrows(java.io.IOException.class,()->NativeLaunchPolicy.requireOutputs(output,output.resolve("state"),output.resolve("evidence"),roots,Map.of(),true,checked::add));
        var escaped=new ArrayList<>(roots);escaped.set(127,Path.of("relative"));
        assertThrows(java.io.IOException.class,()->NativeLaunchPolicy.requireOutputs(output,output.resolve("state"),output.resolve("evidence"),escaped,env,true,checked::add));
    }
}

