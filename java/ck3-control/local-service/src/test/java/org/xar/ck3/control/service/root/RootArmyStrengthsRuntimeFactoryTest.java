package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.file.Files;
import java.io.IOException;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyQueryHistoryStore;
import org.xar.ck3.control.nativebridge.history.OriginalDriverQueryHistorySettings;
import java.nio.file.Path;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyStrengthsExistingFamilies;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyStrengthsInstallation;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyStrengthsNativeFields;

/** Full actual selected Java normalizer/stage closure; source assembly never mints a Game or ReadPermit. */
final class RootArmyStrengthsRuntimeFactoryTest {
    @TempDir Path temporary;
    @Test void completeDefinitionsPublishTheIdenticalFullFamilyAndPipelineBeforeAnyAdoptedDriverExists() throws Exception {
        var sources = sources();
        var definitions = definitions(sources,Optional.empty());
        definitions.contracts().requireCompleteRich(); definitions.pipeline().requireComplete();
        assertTrue(definitions.contracts().normalizationCoverage().complete()); assertTrue(definitions.pipeline().coverage().complete());
        assertEquals(definitions.contracts().families(), definitions.installation().readFamilies());
        assertSame(definitions.contracts().families().getFirst(), definitions.installation().readFamilies().getFirst());
        assertTrue(definitions.installation().actions().isEmpty()); assertTrue(definitions.installation().composites().isEmpty());
        assertTrue(definitions.installation().domainRegistrations().isEmpty());
    }
    @Test void changedDefinitionOrDecoderCannotCreateAnAdvertisablePartialStrengthsInstallation() throws Exception {
        var sources = sources(); ExactRef decoder = sources.decoder();
        var changed = new RootArmyStrengthsRuntimeFactory.Sources(sources.normalizationAndStages(), sources.nativeDefinition(),
                new ExactRef(decoder.path(), decoder.bytes(), "0".repeat(64)),sources.driverResult(),sources.richMaterial(),sources.historyStore(),sources.historyReference(),sources.historySettingsCodec());
        assertThrows(IllegalArgumentException.class, () -> definitions(changed,Optional.empty()));
        var after = definitions(sources,Optional.empty());
        after.contracts().requireCompleteRich(); after.pipeline().requireComplete();
    }
    @Test void explicitZeroStoreIsRetainedAndIsNeverConfusedWithTheNoStateDirectoryBranch() throws Exception {
        var sources=sources();var settings=settings();var store=new ArmyQueryHistoryStore(
                new ArmyQueryHistoryStore.Settings(temporary.resolve("native-session/army-query-history-results"),0),
                ()->{throw new IOException("DATA-only installation must not request live admission");},new ArmyQueryHistoryStore.ArtifactIO(){
                    @Override public long existingFlatBytes(Path folder){throw new AssertionError("definitions cannot scan storage");}
                    @Override public ArmyQueryHistoryStore.StoredFile writeExclusive(Path target,long maximumLogicalBytes,ArmyQueryHistoryStore.WriteBody body){throw new AssertionError("definitions cannot create storage");}
                });
        var actual=RootArmyStrengthsRuntimeFactory.definitions(sources,Optional.of(store),settings,List.of(settings));
        assertSame(store,actual.contracts().sidecarStore().orElseThrow());assertSame(settings,actual.contracts().historySettingsOriginal());
        assertTrue(RootArmyStrengthsRuntimeFactory.definitions(sources,Optional.empty(),settings,List.of(settings)).contracts().sidecarStore().isEmpty());
        assertFalse(Files.exists(store.settings().evidenceDirectory()));
    }
    @Test void everyNewSourceAndActualSettingsOriginalIsPartOfTheCheckedFixedProjectionClosure() throws Exception {
        var actual=sources();var settings=settings();
        for(ExactRef role:List.of(actual.driverResult(),actual.richMaterial(),actual.historyStore(),actual.historyReference(),actual.historySettingsCodec())) {
            var changed=new RootArmyStrengthsRuntimeFactory.Sources(actual.normalizationAndStages(),actual.nativeDefinition(),actual.decoder(),
                    bad(actual.driverResult(),role),bad(actual.richMaterial(),role),bad(actual.historyStore(),role),bad(actual.historyReference(),role),bad(actual.historySettingsCodec(),role));
            assertThrows(IllegalArgumentException.class,()->RootArmyStrengthsRuntimeFactory.definitions(changed,Optional.empty(),settings,List.of(settings)));
        }
        assertThrows(IllegalArgumentException.class,()->RootArmyStrengthsRuntimeFactory.definitions(actual,Optional.empty(),settings,List.of()));
        Files.writeString(Path.of(settings.path()),"changed original settings");
        assertThrows(IllegalArgumentException.class,()->RootArmyStrengthsRuntimeFactory.definitions(actual,Optional.empty(),settings,List.of(settings)));
    }
    private static ExactRef bad(ExactRef actual,ExactRef selected){return actual.equals(selected)?new ExactRef(actual.path(),actual.bytes(),"0".repeat(64)):actual;}
    private RootArmyStrengthsRuntimeFactory.Definitions definitions(RootArmyStrengthsRuntimeFactory.Sources actual,Optional<ArmyQueryHistoryStore> store)throws Exception {
        var settings=settings();return RootArmyStrengthsRuntimeFactory.definitions(actual,store,settings,List.of(settings));
    }
    /** Typed original request DATA only; it is not a private Bound or current Root authority. */
    private ExactRef settings()throws Exception {
        byte[] bytes=OriginalDriverQueryHistorySettings.encodeRequest(new OriginalDriverQueryHistorySettings.Request("factory-data-settings",Instant.EPOCH,Instant.EPOCH.plusSeconds(3600),
                new OriginalDriverQueryHistorySettings.JavaConfigured(new OriginalDriverQueryHistorySettings.Disabled(),0,OriginalDriverQueryHistorySettings.Admission.ROOT_STORAGE)));
        Path file=Files.createTempFile(temporary,"settings-",".json");Files.write(file,bytes);
        assertEquals(OriginalDriverQueryHistorySettings.decodeRequest(bytes),OriginalDriverQueryHistorySettings.decodeRequest(Files.readAllBytes(file)));
        return new ExactRef(file.toAbsolutePath().toString(),bytes.length,ActionCodec.sha256(bytes));
    }
    private static RootArmyStrengthsRuntimeFactory.Sources sources() throws Exception {
        var normalization = new ArmyStrengthsInstallation.Sources(
                new ArmyStrengthsNativeFields.Sources(army("ArmyStrengthsNativeFields"), military("prestore/CurrentMovementCodec"), military("zerostockclock/ArmyUpdateClockCodec")),
                new ArmyStrengthsExistingFamilies.Sources(military("monthlyloss/MonthlyLossCodec"), military("armyqueue/ArmyDailyQueueInputsCodec"),
                        military("countyentry/CountyEntryCodec"), military("updaterwrites/SourceNextFrameCodec"), military("fleetsupply/FleetSupplyCodec"),
                        military("callbackrisk/CurrentSupplyDispatchCodec"), military("supplyschedule/FutureDailySupplyScheduleCodec"), military("combatroles/CombatRolesCodec")),
                army("ArmyStrengthsStages"), army("ArmyStrengthsBaselinePublicRules"), army("ArmyStrengthsRefill"), army("ArmyStrengthsAssaultInstaller"),
                army("ArmyStrengthsPhases"), army("ArmyStrengthsSupply"), army("ArmyStrengthsMonthly"), army("ArmyStrengthsMovement"), army("ArmyStrengthsManagers"),
                army("ArmyStrengthsDetachment"), army("ArmyDetachmentDataProjection"), army("ArmyStrengthsLossAllocation"));
        // The definition is controlled source data in this closure test. Actual Root installation
        // receives the exact native definition ref and separately qualifies its physical producer.
        return new RootArmyStrengthsRuntimeFactory.Sources(normalization, army("ArmyStrengthsContracts"), army("ArmyStrengthsCodec"),
                army("ArmyStrengthsDriverResult"),source("application/src/main/java/org/xar/ck3/control/application/history/DriverReadHistoryRichMaterial.java"),
                army("ArmyQueryHistoryStore"),army("ArmyQueryHistoryReference"),
                source("native-transport/src/main/java/org/xar/ck3/control/nativebridge/history/OriginalDriverQueryHistorySettings.java"));
    }
    private static ExactRef army(String name) throws Exception { return source("native-transport/src/main/java/org/xar/ck3/control/nativebridge/capabilities/army/" + name + ".java"); }
    private static ExactRef military(String name) throws Exception { return source("wave2-military/src/main/java/org/xar/ck3/control/wave2/military/" + name + ".java"); }
    private static ExactRef source(String relative) throws Exception {
        Path module = Path.of(RootArmyStrengthsRuntimeFactory.class.getProtectionDomain().getCodeSource().getLocation().toURI()).toAbsolutePath();
        for (Path cursor = module; cursor != null; cursor = cursor.getParent()) {
            Path selected = cursor.resolve(relative);
            if (Files.isRegularFile(selected)) {
                byte[] actual = Files.readAllBytes(selected);
                return new ExactRef(selected.toRealPath().toString(), actual.length, ActionCodec.sha256(actual));
            }
        }
        throw new IllegalStateException("NOT EXECUTED: required actual selected Java source unavailable: " + relative);
    }
}
