package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.capabilities.CapabilitySessionPresentation;
import org.xar.ck3.control.application.capabilities.DynamicCapabilities;
import org.xar.ck3.control.application.driver.InitialEpisodePolicy;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRulesData;
import org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRulesEffects;
import org.xar.ck3.control.platform.NativeLaunchPlan;
import org.xar.ck3.control.platform.NativeLaunchPlanCodec;

/** Uses archived public plan/policy DATA only. It opens no Game, writer, Context or frontend authority. */
final class RootSavedFrontendLifecycleTest {
    private static ExactRef required(String kind) {
        String base="xar.saved.frontend."+kind+".";
        return new ExactRef(System.getProperty(base+"path"),Long.parseLong(System.getProperty(base+"bytes")),System.getProperty(base+"sha256"));
    }
    private static NativeLaunchPlan plan()throws Exception {
        var ref=required("plan");byte[] raw;
        try(var input=Files.newInputStream(Path.of(ref.path()))) {raw=input.readNBytes(NativeLaunchPlanCodec.MAXIMUM_BYTES+1);}
        assertEquals(ref.bytes(),raw.length);assertEquals(ref.sha256(),java.util.HexFormat.of().formatHex(java.security.MessageDigest.getInstance("SHA-256").digest(raw)));
        var row=StrictJson.parse(raw,NativeLaunchPlanCodec.MAXIMUM_BYTES);
        return NativeLaunchPlanCodec.fromJson(row.has("configuration")?row.get("configuration"):row).accept();
    }
    private static ExactRef implementation(Class<?> actual)throws Exception {
        var ref=ControlBuild.FileRef.measure(Path.of(actual.getProtectionDomain().getCodeSource().getLocation().toURI()));
        return new ExactRef(ref.path(),ref.bytes(),ref.sha256());
    }
    private static RootRuntimeSourceProducts.FrontendConfiguration configuration(InitialEpisodePolicy policy,ExactRef nativeDriver)throws Exception {
        var presentation=new CapabilitySessionPresentation(false,Optional.empty(),Optional.empty(),CapabilitySessionPresentation.BindingState.UNBOUND,
                Optional.empty(),Optional.empty(),Optional.empty(),Optional.empty());
        return new RootRuntimeSourceProducts.FrontendConfiguration(FrontendRulesData.Build.CK3_1210_STEAM_26757580,nativeDriver,
                implementation(FrontendRulesEffects.class),implementation(FrontendRulesData.class),policy,
                new DynamicCapabilities.Configuration(Optional.empty(),Optional.empty(),3,3,false,false),presentation,
                Duration.ofSeconds(60),Duration.ofSeconds(60),64,128,"saved-frontend-data-regression");
    }
    @Test void publicMappedSavedPolicyCanPrepareTheOrdinarySourceWithoutInventingLifecycleOrMenuStart()throws Exception {
        var plan=plan();var policy=InitialEpisodePolicy.readExactSaved(required("policy"),plan);policy.requireSavedHistory(plan);
        var dll=plan.sources().review().bridgeDll();
        var selected=configuration(policy,new ExactRef(dll.path(),dll.bytes(),dll.sha256())).sources();
        assertSame(policy,selected.initialPolicy());assertEquals(InitialEpisodePolicy.Lifecycle.NATIVE_CAMPAIGN_SAVED,selected.initialPolicy().kind());
        assertArrayEquals(new byte[]{'n','u','l','l'},selected.initialPolicy().lifecycle().bytes());
        assertEquals(required("policy"),selected.initialPolicy().source());
        assertTrue(selected.menuStart().isEmpty());assertTrue(selected.optionalOriginalDriverImport().isEmpty());
        assertTrue(selected.fixtureSources().isEmpty());assertThrows(IllegalStateException.class,selected::entryAuthority);
    }
    @Test void originalBusinessLifecyclesStillPrepareWithoutMenuStart()throws Exception {
        for(var kind:new InitialEpisodePolicy.Lifecycle[]{InitialEpisodePolicy.Lifecycle.ROGUE_ONE_LIFE,InitialEpisodePolicy.Lifecycle.ORDINARY_CAMPAIGN_SUCCESSION}) {
            var binding=StrictJson.object().put("schema","xar.ck3.succession-lifecycle-binding/v1")
                    .put("lifecycle",kind==InitialEpisodePolicy.Lifecycle.ROGUE_ONE_LIFE?"rogue_one_life":"ordinary_campaign_succession")
                    .putNull("xar_enabled").put("pact_contract","source-data-only").put("source","source-data-only").putNull("environment_sha256");
            var policy=InitialEpisodePolicy.ordinary(kind,new RawJson(StrictJson.canonical(binding)));
            var selected=configuration(policy,implementation(FrontendRulesEffects.class)).sources();
            assertSame(policy,selected.initialPolicy());assertTrue(selected.menuStart().isEmpty());assertEquals(kind,selected.initialPolicy().kind());
        }
    }
    @Test void savedConfigurationCannotGrantUnmigratedFrontendLayoutsOrManufactureFixturePolicies() {
        var build=FrontendRulesData.Build.CK3_1210_STEAM_26757580;
        assertThrows(IllegalArgumentException.class,build::requireRules);assertThrows(IllegalArgumentException.class,build::requireFrontend);
        assertThrows(IllegalArgumentException.class,build::requireLoadedFeatures);
        assertThrows(IllegalArgumentException.class,()->new FrontendRulesData.Source(new FrontendRulesData.Binding(1,BigInteger.ONE),build));
        for(var kind:new InitialEpisodePolicy.Lifecycle[]{InitialEpisodePolicy.Lifecycle.NATIVE_CAMPAIGN_SAVED,InitialEpisodePolicy.Lifecycle.NATIVE_CAMPAIGN_FIXTURE})
            assertThrows(IllegalArgumentException.class,()->InitialEpisodePolicy.ordinary(kind,new RawJson(new byte[]{'n','u','l','l'})));
    }
}
