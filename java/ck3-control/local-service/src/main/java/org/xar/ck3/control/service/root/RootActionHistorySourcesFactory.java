package org.xar.ck3.control.service.root;

import static org.xar.ck3.control.service.root.RootRuntimeSelectedSources.Module.*;
import static org.xar.ck3.control.service.root.RootRuntimeDefinitionModel.DataRole.*;
import java.io.IOException;
import java.time.Clock;
import java.time.Duration;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.platform.OriginalRuntimeHandoffProof;
import org.xar.ck3.control.platform.WindowsOriginalRuntimeHandoff;
import org.xar.ck3.control.application.advance.*;
import org.xar.ck3.control.application.checkpoint.CheckpointFiles;
import org.xar.ck3.control.application.effects.NativeEventEffects;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.application.planning.campaign.M7CampaignPolicies;
import org.xar.ck3.control.application.planning.events.*;
import org.xar.ck3.control.application.planning.military.*;
import org.xar.ck3.control.application.planning.warexit.WarExitPolicies;
import org.xar.ck3.control.build.runtime.JavaRuntimePackageModel.Request;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.army.*;
import org.xar.ck3.control.nativebridge.capabilities.aub.*;
import org.xar.ck3.control.nativebridge.capabilities.events.*;
import org.xar.ck3.control.nativebridge.capabilities.religion.PlayerReligionContextRead;
import org.xar.ck3.control.nativebridge.capabilities.ritecreation.RiteCreationNative;
import org.xar.ck3.control.platform.NativeLaunchPlan;
import org.xar.ck3.control.wave2.military.exitcomparison.DefenderExitObservationCodec;

/** Sole concrete source wiring; constructs actual typed owner products and grants no Game/read/write admission. */
public final class RootActionHistorySourcesFactory {
    private RootActionHistorySourcesFactory(){ }
    /** Actual metadata wiring only; construction neither reads a source file nor grants an action. */
    public static RootActionHistoryMaterialSourceFactory.Sources ordinary(
            java.util.Map<RootActionHistoryMaterialSourceFactory.RecordingRole,ExactRef> actualDeclaredRecordings,
            RootAdditionalDomains.ImplementationMetadata metadata) {
        Objects.requireNonNull(metadata);
        var readers=new java.util.EnumMap<RootActionHistoryMaterialSourceFactory.ReaderRole,ExactRef>(
                RootActionHistoryMaterialSourceFactory.ReaderRole.class);
        for(var role:RootActionHistoryMaterialSourceFactory.ReaderRole.values())
            readers.put(role,metadata.implementation(role.implementationType()));
        return RootActionHistoryMaterialSourceFactory.Sources.ordinary(
                metadata.implementation(RootActionHistoryMaterialSourceFactory.class),
                metadata.implementation(org.xar.ck3.control.application.driver.DriverActionHistoryCodec.class),
                metadata.implementation(org.xar.ck3.control.application.driver.DriverActionHistoryPublisher.class),
                actualDeclaredRecordings,readers);
    }
    public static RootActionHistoryMaterialSourceFactory.Prepared prepare(RootRuntimeDefinitions.Inputs inputs,
            RootRuntimeSelectedSources selected,RootRuntimeNativeOriginals.Bound originals,Clock clock)throws IOException {
        originals.requireCurrent(clock);selected.requireInputs(inputs);selected.requireCurrent();
        selected.javaSource(LOCAL_SERVICE,RootActionHistorySourcesFactory.class);
        var readers=new ArrayList<ExactRef>();
        for(Class<?> actual:List.of(org.xar.ck3.control.application.effects.NativeEffectEvidence.class,
                org.xar.ck3.control.application.effects.NativeEffectRegistry.class,
                org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier.class,
                org.xar.ck3.control.application.effects.RootGuardEvidence.class,LifeAdvanceEvidence.class,LifeAdvanceRootReplay.class,
                org.xar.ck3.control.application.routecontact.RouteContactEvidenceArchive.class,
                org.xar.ck3.control.application.routecontact.RouteContactSteps.class,
                org.xar.ck3.control.application.effects.family.FamilySendObservation.class,WarHistorySteps.class,
                org.xar.ck3.control.application.effects.DriverFrameEvidenceLoader.class,
                org.xar.ck3.control.application.driver.DriverJson.class))readers.add(selected.javaSource(APPLICATION,actual));
        readers.add(selected.javaSource(LOCAL_SERVICE,org.xar.ck3.control.service.sway.SwayRuntimeInstaller.class));
        readers.add(selected.javaSource(LOCAL_SERVICE,RootFamilySendRecordingMaterial.class));
        readers.add(selected.javaSource(LOCAL_SERVICE,RootDriverTransportRuntimeFactory.class));
        readers.add(selected.javaSource(NATIVE_TRANSPORT,ArmyObserverSampling.class));
        readers.add(selected.javaSource(APPLICATION,org.xar.ck3.control.application.planning.finance.GiftActionHistoryEvidence.class));
        readers.add(selected.javaSource(APPLICATION,org.xar.ck3.control.application.action.PhysicalActionCodec.class));
        readers.add(selected.javaSource(APPLICATION,org.xar.ck3.control.application.planning.finance.FinanceReadContracts.class));
        readers.add(selected.javaSource(APPLICATION,org.xar.ck3.control.application.effects.NativeFinanceEffects.class));
        readers.add(selected.javaSource(LOCAL_SERVICE,RootGuiPresentation.class));
        readers.add(selected.javaSource(LOCAL_SERVICE,RootReligionPilgrimage.class));
        readers.add(selected.javaSource(LOCAL_SERVICE,RootNaturalTimeline.class));
        readers.add(selected.javaSource(LOCAL_SERVICE,RootPendingUiRuntime.class));
        readers.add(selected.javaSource(LOCAL_SERVICE,RootLifecycleRuntimeFactory.class));
        readers.add(selected.javaSource(NATIVE_TRANSPORT,org.xar.ck3.control.nativebridge.capabilities.publicmethods.religion.ReligionService.class));
        readers.add(selected.javaSource(NATIVE_TRANSPORT,org.xar.ck3.control.nativebridge.capabilities.publicmethods.religion.extensions.ReligionPilgrimage.class));
        var policy=new RootActionHistoryMaterialSourceFactory.RecordingPolicySources(
                inputs.source(RootRuntimeDefinitionModel.SourceRole.FRONTEND_ORIGINAL_DRIVER),
                originals.source(RootRuntimeNativeOriginals.Role.WAR_DECLARED_OVERVIEW_POLICY),
                originals.source(RootRuntimeNativeOriginals.Role.WAR_RECORDING_POLICY),
                originals.source(RootRuntimeNativeOriginals.Role.BATTLE_RECORDING_POLICY));
        return new RootActionHistoryMaterialSourceFactory.Prepared(new RootActionHistoryMaterialSourceFactory.Sources(
                selected.javaSource(LOCAL_SERVICE,RootActionHistoryMaterialSourceFactory.class),
                selected.javaSource(APPLICATION,org.xar.ck3.control.application.driver.DriverActionHistoryCodec.class),
                selected.javaSource(APPLICATION,org.xar.ck3.control.application.driver.DriverActionHistoryPublisher.class),policy,
                readers.stream().distinct().toList()));
    }
}
