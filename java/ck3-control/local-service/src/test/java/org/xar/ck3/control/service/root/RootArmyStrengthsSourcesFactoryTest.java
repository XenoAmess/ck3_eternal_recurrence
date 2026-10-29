package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.time.Duration;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import java.nio.file.Path;
import java.nio.file.Files;
import java.util.Optional;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.nativebridge.history.OriginalDriverQueryHistorySettings;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.application.history.DriverReadHistoryRichMaterial;
import org.xar.ck3.control.nativebridge.capabilities.army.*;
import org.xar.ck3.control.wave2.military.armyqueue.ArmyDailyQueueInputsCodec;
import org.xar.ck3.control.wave2.military.callbackrisk.CurrentSupplyDispatchCodec;
import org.xar.ck3.control.wave2.military.combatroles.CombatRolesCodec;
import org.xar.ck3.control.wave2.military.countyentry.CountyEntryCodec;
import org.xar.ck3.control.wave2.military.fleetsupply.FleetSupplyCodec;
import org.xar.ck3.control.wave2.military.monthlyloss.MonthlyLossCodec;
import org.xar.ck3.control.wave2.military.prestore.CurrentMovementCodec;
import org.xar.ck3.control.wave2.military.supplyschedule.FutureDailySupplyScheduleCodec;
import org.xar.ck3.control.wave2.military.updaterwrites.SourceNextFrameCodec;
import org.xar.ck3.control.wave2.military.zerostockclock.ArmyUpdateClockCodec;
import static org.xar.ck3.control.service.root.RootRuntimeSelectedSources.Module.*;

/** Actual source files -> selected ref guard -> typed 23-leaf Sources -> original full consumer. No Game/read permit. */
final class RootArmyStrengthsSourcesFactoryTest {
    @TempDir Path temporary;
    private static final List<Class<?>> ARMY=List.of(ArmyStrengthsInstallation.class,ArmyStrengthsExistingFamilies.class,
            ArmyStrengthsNativeFields.class,ArmyStrengthsStages.class,ArmyStrengthsBaselinePublicRules.class,ArmyStrengthsRefill.class,
            ArmyStrengthsAssaultInstaller.class,ArmyStrengthsPhases.class,ArmyStrengthsSupply.class,ArmyStrengthsMonthly.class,
            ArmyStrengthsMovement.class,ArmyStrengthsManagers.class,ArmyStrengthsDetachment.class,ArmyDetachmentDataProjection.class,
            ArmyStrengthsLossAllocation.class,ArmyStrengthsCodec.class,ArmyStrengthsDriverResult.class,
            ArmyQueryHistoryStore.class,ArmyQueryHistoryReference.class,OriginalDriverQueryHistorySettings.class);
    private static final List<Class<?>> MILITARY=List.of(CurrentMovementCodec.class,ArmyUpdateClockCodec.class,MonthlyLossCodec.class,
            ArmyDailyQueueInputsCodec.class,CountyEntryCodec.class,SourceNextFrameCodec.class,FleetSupplyCodec.class,
            CurrentSupplyDispatchCodec.class,FutureDailySupplyScheduleCodec.class,CombatRolesCodec.class);
    private static List<RootRuntimeDefinitionModel.SelectedSource> rows()throws Exception {
        var rows=new ArrayList<>(RootSourceHelperFiles.java(ARMY,NATIVE_TRANSPORT));
        rows.addAll(RootSourceHelperFiles.java(MILITARY,WAVE2_MILITARY));
        rows.addAll(RootSourceHelperFiles.java(List.of(DriverReadHistoryRichMaterial.class),APPLICATION));
        rows.addAll(RootSourceHelperFiles.java(List.of(RootArmyStrengthsSourcesFactory.class,RootArmyStrengthsRuntimeFactory.class),LOCAL_SERVICE));
        return List.copyOf(rows);
    }
    @Test void actualCompleteSourcesReachTheSameFullNormalizerRegistryAndPreserveExactReferences()throws Exception {
        var selected=new RootRuntimeSelectedSources(rows());
        ExactRef nativeDefinition=RootSourceHelperFiles.original("ck3_autonomous_player/native_bridge/src/bridge.cpp");
        var sources=RootArmyStrengthsSourcesFactory.sources(selected,nativeDefinition);
        assertEquals(23,sources.normalizationAndStages().sourceRefs().size());assertSame(nativeDefinition,sources.nativeDefinition());
        assertEquals(selected.javaSource(NATIVE_TRANSPORT,ArmyStrengthsDriverResult.class),sources.driverResult());
        assertTrue(sources.sourceRefs().contains(sources.driverResult()));
        assertEquals(selected.javaSource(APPLICATION,DriverReadHistoryRichMaterial.class),sources.richMaterial());
        assertTrue(sources.sourceRefs().contains(sources.richMaterial()));
        for(ExactRef actual:sources.sourceRefs())assertEquals(actual,ExactRef.fromJson(actual.toJson()));
        var actualSettings=historySettingsData();
        var actualClosure=new ArrayList<>(sources.sourceRefs());actualClosure.add(actualSettings);
        assertTrue(actualClosure.contains(selected.javaSource(NATIVE_TRANSPORT,OriginalDriverQueryHistorySettings.class)));
        var definitions=RootArmyStrengthsRuntimeFactory.definitions(sources,Optional.empty(),actualSettings,List.copyOf(actualClosure));
        assertTrue(definitions.contracts().sidecarStore().isEmpty());
        assertEquals(actualSettings,definitions.contracts().historySettingsOriginal());
        assertEquals(selected.javaSource(NATIVE_TRANSPORT,ArmyQueryHistoryStore.class),sources.historyStore());
        assertEquals(selected.javaSource(NATIVE_TRANSPORT,ArmyQueryHistoryReference.class),sources.historyReference());
        assertEquals(selected.javaSource(NATIVE_TRANSPORT,OriginalDriverQueryHistorySettings.class),sources.historySettingsCodec());
        definitions.contracts().requireCompleteRich();definitions.pipeline().requireComplete();
        assertEquals(definitions.contracts().families(),definitions.installation().readFamilies());selected.requireCurrent();
        assertTrue(definitions.installation().actions().isEmpty());assertTrue(definitions.installation().composites().isEmpty());
    }
    @Test void aMissingActualLeafCannotBecomeAPartialSourceClosure()throws Exception {
        var complete=rows();var missing=complete.stream().filter(row->!row.targetRelative().endsWith("/MonthlyLossCodec.java")).toList();
        var selected=new RootRuntimeSelectedSources(missing);
        ExactRef nativeDefinition=RootSourceHelperFiles.original("ck3_autonomous_player/native_bridge/src/bridge.cpp");
        assertThrows(IOException.class,()->RootArmyStrengthsSourcesFactory.sources(selected,nativeDefinition));
        var missingDriver=complete.stream().filter(row->!row.targetRelative().endsWith("/ArmyStrengthsDriverResult.java")).toList();
        assertThrows(IOException.class,()->RootArmyStrengthsSourcesFactory.sources(new RootRuntimeSelectedSources(missingDriver),nativeDefinition));
        var missingMaterial=complete.stream().filter(row->!row.targetRelative().endsWith("/DriverReadHistoryRichMaterial.java")).toList();
        assertThrows(IOException.class,()->RootArmyStrengthsSourcesFactory.sources(new RootRuntimeSelectedSources(missingMaterial),nativeDefinition));
        for(String required:List.of("ArmyQueryHistoryStore.java","ArmyQueryHistoryReference.java","OriginalDriverQueryHistorySettings.java")) {
            var absent=complete.stream().filter(row->!row.targetRelative().endsWith("/"+required)).toList();
            assertThrows(IOException.class,()->RootArmyStrengthsSourcesFactory.sources(new RootRuntimeSelectedSources(absent),nativeDefinition));
        }
        var after=RootArmyStrengthsSourcesFactory.sources(new RootRuntimeSelectedSources(complete),nativeDefinition);
        assertEquals(23,after.normalizationAndStages().sourceRefs().size());
    }
    @Test void actualReadTimeoutPreservesMillisecondsAndRejectsTheOriginalConsumersBoundary() {
        assertEquals(Duration.ofMillis(1),RootArmyStrengthsSourcesFactory.configuration(1).commandReadTimeout());
        assertEquals(Duration.ofMillis(59999),RootArmyStrengthsSourcesFactory.configuration(59999).commandReadTimeout());
        assertEquals(Duration.ofMinutes(1),RootArmyStrengthsSourcesFactory.configuration(60000).commandReadTimeout());
        for(long invalid:new long[]{0,-1,60001,3600000,Long.MAX_VALUE})
            assertThrows(IllegalArgumentException.class,()->RootArmyStrengthsSourcesFactory.configuration(invalid));
    }

    /** Actual typed settings encoder -> original file/ref -> pure definitions consumer. No Bound/Root qualification. */
    private ExactRef historySettingsData()throws Exception {
        byte[] raw=OriginalDriverQueryHistorySettings.encodeRequest(new OriginalDriverQueryHistorySettings.Request(
                "controlled-strengths-settings",java.time.Instant.EPOCH,java.time.Instant.EPOCH.plusSeconds(3600),
                new OriginalDriverQueryHistorySettings.JavaConfigured(new OriginalDriverQueryHistorySettings.Disabled(),0,
                        OriginalDriverQueryHistorySettings.Admission.ROOT_STORAGE)));
        Path original=temporary.resolve("explicit-inline-query-history-request.json");Files.write(original,raw);
        assertEquals(OriginalDriverQueryHistorySettings.decodeRequest(raw),OriginalDriverQueryHistorySettings.decodeRequest(Files.readAllBytes(original)));
        return new ExactRef(original.toAbsolutePath().toString(),raw.length,ActionCodec.sha256(raw));
    }
}
