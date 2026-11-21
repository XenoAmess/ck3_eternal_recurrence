package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import java.nio.file.*;
import java.time.Clock;
import java.util.*;
import java.io.IOException;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.platform.*;
import org.xar.ck3.control.build.runtime.HostMode;
import org.xar.ck3.control.application.checkpoint.NativeCheckpointFiles;
import org.xar.ck3.control.continuity.FreshContinuityGenesis;
import org.xar.ck3.control.continuity.OriginalWindowReducer;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.governance.council.CouncilCodec;
import org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionModels;

/** Preparation DATA only. There is deliberately no ManagedGameSession or NativePacketPort. */
class Current125PlainPreparationDataTest {
    static final String VERSION="1.21.0.3";
    static final String SHA="859f0d380098adcb130eb9d453458222749fcdf6d46126ad0ed99d78f9a0aa28";
    @TempDir Path temporary;
    static Path originalConfig(){return Path.of(System.getProperty("plain.original.config"));}
    static RootOrdinaryRuntimeConfiguration actualConfig()throws Exception {
        var document=StrictJson.parse(Files.readAllBytes(originalConfig()),StrictJson.EXPLICIT_MAX_BYTES);
        var plan=NativeLaunchPlanCodec.fromJson(StrictJson.parse(Files.readAllBytes(Path.of(document.get("launch_plan_file").textValue())),NativeLaunchPlanCodec.MAXIMUM_BYTES)).accept();
        return RootOrdinaryRuntimeConfiguration.readSaved(originalConfig(),plan);
    }
    @Test void currentGovernanceIsUnavailableWithoutCouncilQualification() {
        var config=new GovernanceRuntimeInstaller.Config(VERSION,SHA,"data-only",Set.of(),64,64);
        assertFalse(config.nativeQualified());assertTrue(config.unavailableReason().isPresent());
        assertThrows(org.xar.ck3.control.service.mcp.PublicServiceFailure.class,()->GovernanceRuntimeInstaller.requirePublicAvailable(VERSION,SHA));
        assertThrows(IllegalArgumentException.class,()->CouncilCodec.requireBuild(VERSION,SHA));
    }
    @Test void mismatchedGovernanceIdentityRemainsRejected() {
        assertThrows(IllegalArgumentException.class,()->GovernanceRuntimeInstaller.qualifiedBuild("1.21.0",SHA));
        assertThrows(IllegalArgumentException.class,()->GovernanceRuntimeInstaller.qualifiedBuild(VERSION,"0".repeat(64)));
    }
    @Test void currentInteractionsKeepTheirUnavailableContract() {
        var build=KnownInteractionsRuntimeInstaller.ConfiguredBuild.select(VERSION,SHA);
        assertEquals(VERSION,build.version());assertEquals(SHA,build.executableSha256());assertFalse(build.qualified());
        assertEquals(Optional.of(KnownInteractionsRuntimeInstaller.ConfiguredBuild.UNMIGRATED_REASON),build.unavailableReason());
        assertThrows(IllegalStateException.class,build::requireQualified);
    }
    @Test void mixedInteractionsAndLegacyGovernanceRemainDistinct() {
        assertThrows(IllegalArgumentException.class,()->KnownInteractionsRuntimeInstaller.ConfiguredBuild.select("1.21.0",SHA));
        assertThrows(IllegalArgumentException.class,()->KnownInteractionsRuntimeInstaller.ConfiguredBuild.select(VERSION,"0".repeat(64)));
        var old=ExactCk3Build.CK3_12004;
        assertTrue(GovernanceRuntimeInstaller.qualifiedBuild(old.version(),old.executableSha256()));
        for(var legacy:InteractionModels.Build.values())assertSame(legacy,KnownInteractionsRuntimeInstaller.ConfiguredBuild.select(legacy.version(),legacy.sha256()).requireQualified());
        for(var prior:List.of(ExactCk3Build.CK3_1210,ExactCk3Build.CK3_1210_STEAM_26757580)) {
            assertFalse(GovernanceRuntimeInstaller.qualifiedBuild(prior.version(),prior.executableSha256()));
            assertFalse(KnownInteractionsRuntimeInstaller.ConfiguredBuild.select(prior.version(),prior.executableSha256()).qualified());
        }
    }
    @org.junit.jupiter.api.condition.EnabledIfSystemProperty(named="plain.actual.jar",matches=".+")
    @Test void actualSourceOwnersAreTheNewNormalJar()throws Exception {
        Path expected=Path.of(System.getProperty("plain.actual.jar")).toRealPath();
        for(Class<?> owner:List.of(GovernanceRuntimeInstaller.class,KnownInteractionsRuntimeInstaller.class,RootOrdinaryPlainProducts.class,RootOrdinaryRuntimeAssembly.class))
            assertEquals(expected,Path.of(owner.getProtectionDomain().getCodeSource().getLocation().toURI()).toRealPath());
    }
    @org.junit.jupiter.api.condition.EnabledIfSystemProperty(named="plain.original.config",matches=".+")
    @Test void actual51InputsAndRealLayoutPrepareReadOnlyWithoutCore()throws Exception {
        var config=actualConfig();assertEquals(VERSION,config.configuredBuild().version());
        try(var graph=RootOrdinaryRuntimeAssembly.prepareReadOnlySavedSource(config,Clock.systemUTC())) {
            assertSame(config,graph.configuration());assertEquals(SHA,graph.configuration().configuredBuild().sha256().toLowerCase(Locale.ROOT));
            assertSame(config.initialPolicy(),graph.initialPolicy());
            assertThrows(IllegalStateException.class,graph::privatePermissions);
            assertThrows(IllegalStateException.class,graph::catalogs);
            assertThrows(IllegalStateException.class,graph::lifecycle);
            assertTrue(graph.publicDefinitionsProduction().isEmpty());
        }
    }
    @org.junit.jupiter.api.condition.EnabledIfSystemProperty(named="plain.original.config",matches=".+")
    @Test void actual51ConfigurationComposesAllPlainProductsOnOwnedRealLayout()throws Exception {
        var original=actualConfig();var raw=StrictJson.parse(Files.readAllBytes(originalConfig()),StrictJson.EXPLICIT_MAX_BYTES).deepCopy();
        var object=(com.fasterxml.jackson.databind.node.ObjectNode)raw;
        Path root=temporary.resolve("plain-owned").toAbsolutePath(),state=root.resolve("state"),continuity=root.resolve("continuity"),archive=continuity.resolve("artifacts");
        for(Path p:List.of(state,continuity,archive,root.resolve("checkpoints"),root.resolve("receipts"),root.resolve("artifacts")))Files.createDirectories(p);
        object.put("state_dir",state.toString());object.put("stop_path",root.resolve("never-created.stop").toString());
        Path cfg=root.resolve("derived-actual51-data.json");Files.writeString(cfg,object.toString(),java.nio.charset.StandardCharsets.UTF_8);
        var plan=NativeLaunchPlanCodec.fromJson(StrictJson.parse(Files.readAllBytes(original.launchPlanFile()),NativeLaunchPlanCodec.MAXIMUM_BYTES)).accept();
        var config=RootOrdinaryRuntimeConfiguration.readSaved(cfg,plan);var clock=Clock.systemUTC();var metadata=new RootOrdinaryImplementationMetadata();
        var initial=new WriterContracts.InitialLayout(continuity.resolve("continuity.json"),continuity.resolve("genesis-anchor.json"),config.machineId());
        var genesis=new FreshContinuityGenesis.Plan(config.machineId(),Math.max(1,clock.millis()),OriginalWindowReducer.TARGET_DAYS);
        Path request=continuity.resolve("genesis-request.json");Files.write(request,FreshContinuityGenesis.encode(genesis));
        try(var storage=RootRuntimeStorageGuard.ordinary(initial,archive,()->{throw new IOException("NoGame fixture has no open writer");},List.of(root),config.maximumStorageBytes(),clock)) {
            var layout=ContinuityWriter.initializeFresh(genesis,metadata.file(request),initial,storage).layout();
            var anchor=metadata.file(initial.anchor());assertEquals(layout.anchor(),anchor);assertTrue(anchor.bytes()>0);
            var app=new RootApplicationConfiguration(config.machineId(),HostMode.COMPLETE_MIGRATION,clock.instant(),metadata.file(config.launchPlanFile()),layout,List.of(metadata.implementation(RootOrdinaryRuntimeAssembly.class)),archive,config.maximumStorageBytes());
            var core=new RootCoreBoundPorts(app);
            var ports=new RootRuntimeSourceProducts.OrdinaryRuntimePorts(core,storage.checkpointFiles(new NativeCheckpointFiles()),storage,OriginalRuntimeHandoffProof.unavailable(),RootOperatorCharacterAuthority.prepareOrdinary(metadata.file(config.nativeImplementation()),metadata),metadata,clock);
            var graph=RootOrdinaryPlainProducts.prepare(config,app,ports,config.initialPolicy(),plan);
            for(Object product:List.of(graph.runtime(),graph.domains(),graph.family(),graph.army(),graph.governance(),graph.finance(),graph.crossRun(),graph.additionalDomains()))assertNotNull(product);
            assertSame(graph.runtime().sources(),graph.runtime().catalogs().sources());
            assertTrue(graph.runtime().sources().historicalPackage().isEmpty());
            assertFalse(graph.runtime().sources().nativeGovernance().nativeQualified());
            assertFalse(graph.runtime().sources().interactions().configuredBuild().qualified());
            assertFalse(graph.runtime().catalogs().domainRegistrations().isEmpty());
            assertThrows(IOException.class,core::requireWriter);
            assertFalse(Files.exists(root.resolve("never-created.stop")));
            assertEquals(anchor,metadata.file(initial.anchor()));
        }
    }
}
