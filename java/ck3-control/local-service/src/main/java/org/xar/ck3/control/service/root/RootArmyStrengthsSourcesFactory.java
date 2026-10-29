package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.time.Duration;
import java.util.Objects;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.application.history.DriverReadHistoryRichMaterial;
import org.xar.ck3.control.nativebridge.capabilities.army.*;
import org.xar.ck3.control.nativebridge.history.OriginalDriverQueryHistorySettings;
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
import static org.xar.ck3.control.service.root.RootRuntimeDefinitionModel.DataRole.NATIVE_DOMAIN_ORIGINALS;

/** Pure source wiring for the actual 23-field Strengths closure. No army input, Native permit or Core is created. */
public final class RootArmyStrengthsSourcesFactory {
    private RootArmyStrengthsSourcesFactory() { }
    public static RootArmyStrengthsRuntimeFactory.Prepared prepare(RootRuntimeDefinitions.Inputs inputs,
            RootRuntimeSelectedSources selected,RootRuntimeNativeOriginals.Bound originals,
            OriginalDriverQueryHistorySettings.Bound sameQueryHistory)throws IOException {
        Objects.requireNonNull(inputs);Objects.requireNonNull(selected);Objects.requireNonNull(originals);Objects.requireNonNull(sameQueryHistory);
        if(!inputs.data(NATIVE_DOMAIN_ORIGINALS).equals(originals.original())
                ||!inputs.application().machineId().equals(originals.configuration().machineId()))
            throw new IOException("Strengths original provenance is not the identical configured Root original");
        var dispatcher=originals.configuration().source(RootRuntimeNativeOriginals.Role.NATIVE_DISPATCHER);
        ExactRef nativeDefinition=selected.original(dispatcher.original(),dispatcher.role().kind());
        var actual=sources(selected,nativeDefinition);
        var configuration=configuration(inputs.configuration().army().commandReadTimeoutMs());
        selected.requireCurrent();return new RootArmyStrengthsRuntimeFactory.Prepared(actual,configuration,sameQueryHistory);
    }
    static RootArmyStrengthsRuntimeFactory.Configuration configuration(long actualTimeoutMillis) {
        return new RootArmyStrengthsRuntimeFactory.Configuration(Duration.ofMillis(actualTimeoutMillis));
    }
    /** The same actual source constructor used by prepare; source-only regression entry creates no Runtime Inputs. */
    static RootArmyStrengthsRuntimeFactory.Sources sources(RootRuntimeSelectedSources selected,ExactRef nativeDefinition)throws IOException {
        Objects.requireNonNull(selected);Objects.requireNonNull(nativeDefinition);
        selected.javaSource(LOCAL_SERVICE,RootArmyStrengthsSourcesFactory.class);
        selected.javaSource(LOCAL_SERVICE,RootArmyStrengthsRuntimeFactory.class);
        selected.javaSource(NATIVE_TRANSPORT,ArmyStrengthsInstallation.class);
        selected.javaSource(NATIVE_TRANSPORT,ArmyStrengthsExistingFamilies.class);
        selected.javaSource(NATIVE_TRANSPORT,ArmyStrengthsDriverResult.class);
        selected.javaSource(APPLICATION,DriverReadHistoryRichMaterial.class);
        selected.javaSource(NATIVE_TRANSPORT,OriginalDriverQueryHistorySettings.class);
        var nativeFields=new ArmyStrengthsNativeFields.Sources(selected.javaSource(NATIVE_TRANSPORT,ArmyStrengthsNativeFields.class),
                selected.javaSource(WAVE2_MILITARY,CurrentMovementCodec.class),selected.javaSource(WAVE2_MILITARY,ArmyUpdateClockCodec.class));
        var existing=new ArmyStrengthsExistingFamilies.Sources(selected.javaSource(WAVE2_MILITARY,MonthlyLossCodec.class),
                selected.javaSource(WAVE2_MILITARY,ArmyDailyQueueInputsCodec.class),selected.javaSource(WAVE2_MILITARY,CountyEntryCodec.class),
                selected.javaSource(WAVE2_MILITARY,SourceNextFrameCodec.class),selected.javaSource(WAVE2_MILITARY,FleetSupplyCodec.class),
                selected.javaSource(WAVE2_MILITARY,CurrentSupplyDispatchCodec.class),selected.javaSource(WAVE2_MILITARY,FutureDailySupplyScheduleCodec.class),
                selected.javaSource(WAVE2_MILITARY,CombatRolesCodec.class));
        var normalization=new ArmyStrengthsInstallation.Sources(nativeFields,existing,
                selected.javaSource(NATIVE_TRANSPORT,ArmyStrengthsStages.class),selected.javaSource(NATIVE_TRANSPORT,ArmyStrengthsBaselinePublicRules.class),
                selected.javaSource(NATIVE_TRANSPORT,ArmyStrengthsRefill.class),selected.javaSource(NATIVE_TRANSPORT,ArmyStrengthsAssaultInstaller.class),
                selected.javaSource(NATIVE_TRANSPORT,ArmyStrengthsPhases.class),selected.javaSource(NATIVE_TRANSPORT,ArmyStrengthsSupply.class),
                selected.javaSource(NATIVE_TRANSPORT,ArmyStrengthsMonthly.class),selected.javaSource(NATIVE_TRANSPORT,ArmyStrengthsMovement.class),
                selected.javaSource(NATIVE_TRANSPORT,ArmyStrengthsManagers.class),selected.javaSource(NATIVE_TRANSPORT,ArmyStrengthsDetachment.class),
                selected.javaSource(NATIVE_TRANSPORT,ArmyDetachmentDataProjection.class),selected.javaSource(NATIVE_TRANSPORT,ArmyStrengthsLossAllocation.class));
        var result=new RootArmyStrengthsRuntimeFactory.Sources(normalization,nativeDefinition,
                selected.javaSource(NATIVE_TRANSPORT,ArmyStrengthsCodec.class),selected.javaSource(NATIVE_TRANSPORT,ArmyStrengthsDriverResult.class),
                selected.javaSource(APPLICATION,DriverReadHistoryRichMaterial.class),
                selected.javaSource(NATIVE_TRANSPORT,ArmyQueryHistoryStore.class),selected.javaSource(NATIVE_TRANSPORT,ArmyQueryHistoryReference.class),
                selected.javaSource(NATIVE_TRANSPORT,OriginalDriverQueryHistorySettings.class));
        selected.requireCurrent();return result;
    }
}
