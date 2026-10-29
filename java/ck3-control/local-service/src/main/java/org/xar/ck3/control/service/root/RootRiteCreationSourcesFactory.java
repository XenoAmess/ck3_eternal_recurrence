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
public final class RootRiteCreationSourcesFactory {
    private RootRiteCreationSourcesFactory(){ }
    public static RootRiteCreationRuntimeFactory.Prepared prepare(RootRuntimeDefinitions.Inputs inputs,RootRuntimeSelectedSources selected,
            RootRuntimeNativeOriginals.Bound originals,RootSelectedRegistrationConfiguration.Bound registration,
            RootCoreBoundPorts ports,Duration freshness,Clock clock)throws IOException {
        registration.requireCurrent(inputs,clock);originals.requireCurrent(clock);selected.requireCurrent();
        selected.javaSource(LOCAL_SERVICE,RootRiteCreationSourcesFactory.class);
        // The sole selected-configuration codec requires all 79 ordinary flags to be explicit true. Consume that real typed wire,
        // rather than introducing a second flag parser or a disabled default in this source composer.
        var encoded=StrictJson.parse(RootSelectedRegistrationConfiguration.encode(registration.configuration()));
        var flag=encoded.get("registration_attributes").get(RootSelectedRegistrationConfiguration.RegistrationFlag.PLAYER_RITE_CREATION_ACTIONS.wire());
        if(flag==null||!flag.isBoolean()||!flag.booleanValue())throw new IOException("actual all-ordinary Rite registration flag is absent or disabled");
        var nativeClosure=new ArrayList<ExactRef>();
        for(var role:RootRuntimeNativeOriginals.Role.values())if(role.name().startsWith("RITE_CREATION_")||role==RootRuntimeNativeOriginals.Role.NATIVE_DISPATCHER)
            nativeClosure.add(originals.source(role));
        var nativeSources=new RiteCreationNative.Sources(originals.source(RootRuntimeNativeOriginals.Role.RITE_CREATION_NATIVE_MAILBOX),
                originals.source(RootRuntimeNativeOriginals.Role.RITE_CREATION_NATIVE_WIRE),nativeClosure);
        var closure=new ArrayList<ExactRef>(nativeClosure);
        for(var target:List.of("application/src/main/java/org/xar/ck3/control/application/ritecreation/RiteCreationContract.java",
                "application/src/main/java/org/xar/ck3/control/application/ritecreation/RiteCreationCodec.java",
                "application/src/main/java/org/xar/ck3/control/application/ritecreation/RiteCreationState.java",
                "application/src/main/java/org/xar/ck3/control/application/ritecreation/RiteCreationDomainState.java",
                "application/src/main/java/org/xar/ck3/control/application/ritecreation/RiteCreationLegacyStore.java",
                "local-service/src/main/java/org/xar/ck3/control/service/root/RootRiteCreationLegacyImport.java",
                "local-service/src/main/java/org/xar/ck3/control/service/root/RootRiteCreationLegacyArchive.java",
                "contracts/src/main/java/org/xar/ck3/control/contracts/ManagedCampaignRunBinding.java",
                "contracts/src/main/java/org/xar/ck3/control/contracts/LegacyWindowsPathCanonicalizer.java",
                "local-service/src/main/java/org/xar/ck3/control/service/root/RootRiteCreationDomain.java"))closure.add(selected.javaTarget(target));
        closure.add(selected.javaSource(NATIVE_TRANSPORT,RiteCreationNative.class));
        var runtime=selected.javaSource(LOCAL_SERVICE,RootRiteCreationRuntimeFactory.class);closure.add(runtime);
        closure.add(selected.javaSource(NATIVE_TRANSPORT,OriginalRuntimeHandoffProof.class));
        closure.add(selected.javaSource(NATIVE_TRANSPORT,WindowsOriginalRuntimeHandoff.class));
        // No original owned Python producer object is retained by this Java startup. The sole OS factory
        // therefore supplies actual Unavailable; plan/profile/Game PID are not original-producer custody.
        var legacyRuntime=WindowsOriginalRuntimeHandoff.originalOwnedLaunch(Optional.empty());
        return new RootRiteCreationRuntimeFactory.Prepared(new RootRiteCreationRuntimeFactory.Sources(nativeSources,runtime,
                closure.stream().distinct().toList(),flag.booleanValue(),new RootRiteCreationScopeAuthority(ports,freshness,clock),legacyRuntime));
    }
}
