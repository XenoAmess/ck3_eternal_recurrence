package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.condition.EnabledOnOs;
import org.junit.jupiter.api.condition.OS;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.checkpoint.NativeCheckpointFiles;
import org.xar.ck3.control.application.driver.InitialEpisodePolicy;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.service.root.*;
import org.xar.ck3.control.wave3.governance.lifecycle.*;

/** Explicit metadata versions grant no loaded role or SavedMaterial. */
@EnabledOnOs(OS.WINDOWS)
final class RootLoadedOrdinaryProfileContractTest {
    @TempDir Path temporary;
    static RawJson lifecycle() {
        var binding=new SuccessionLifecycleBinding(SuccessionLifecycleBinding.Profile.ORDINARY_VANILLA_CONFIGURATION,
                "ordinary_vanilla_configuration",null);
        return InitialEpisodePolicy.ordinary(InitialEpisodePolicy.Lifecycle.ORDINARY_CAMPAIGN_SUCCESSION,
                new RawJson(SuccessionLifecycleCodec.encode(binding))).lifecycle();
    }
    static byte[] policy() {
        var row=StrictJson.object().put("schema","xar.java.initial-episode-policy/v1");
        row.set("succession_lifecycle",StrictJson.parse(lifecycle().bytes(),1<<20));return StrictJson.canonical(row);
    }
    static ExactRef ref(Path path)throws Exception {
        var f=ControlBuild.FileRef.measure(path);return new ExactRef(f.path(),f.bytes(),f.sha256());
    }
    @Test void explicitOrdinaryVersionsRoundTripAndCannotEnterLegacyNativeOrIssuePrivateRoles()throws Exception {
        Path source=temporary.resolve("source.json");Files.writeString(source,"{}");var ref=ref(source);
        var witness=new NativeCheckpointFiles().observe(source).orElseThrow();Instant now=Instant.now();
        var profile=new RootFrozenRunProfile.Request(WindowsJobProcess.currentMachineId(),now.minusSeconds(1),now.plusSeconds(90),
                "ordinary-request","ordinary-session",ref,RootFrozenRunProfile.LifecycleMode.ORDINARY_CAMPAIGN_SUCCESSION,
                true,new RootFrozenRunProfile.Enabled(temporary));
        var request=new RootLoadedOrdinaryProfile.Request(profile,ref,ref,ref,ref,witness,ref,temporary.resolve("new-policy.json"));
        byte[] encoded=RootLoadedOrdinaryProfile.encodeRequest(request);
        assertEquals(request,RootLoadedOrdinaryProfile.decodeRequest(encoded));
        assertThrows(IllegalArgumentException.class,()->RootOriginalDriverRunProfileProducer.decodeLoaded(encoded));
        assertThrows(IllegalArgumentException.class,()->new RootFrozenRunProfile.LoadedRequest(profile,ref,ref,ref,ref));
        var nativeProfile=new RootFrozenRunProfile.Request(profile.machineId(),profile.observedAt(),profile.reviewAt(),
                profile.requestId(),profile.sessionId(),ref,RootFrozenRunProfile.LifecycleMode.NATIVE_CAMPAIGN,false,
                new RootFrozenRunProfile.EnabledNativeCampaign(temporary));
        assertThrows(IllegalArgumentException.class,()->new RootLoadedOrdinaryProfile.Request(nativeProfile,ref,ref,ref,ref,witness,ref,request.policyTarget()));
        var nativeInput=new RootLoadedReplacementRecoveryInputs.Request(profile.machineId(),profile.observedAt(),profile.reviewAt(),
                ref,ref,ref,ref,ref,ref,ref,temporary.resolve("evidence"),"a".repeat(64));
        assertEquals(RootLoadedReplacementRecoveryInputs.Mode.NATIVE_CAMPAIGN,
                RootLoadedReplacementRecoveryInputs.decode(RootLoadedReplacementRecoveryInputs.encode(nativeInput)).mode());
        var ordinary=new RootLoadedReplacementRecoveryInputs.Request(nativeInput.machineId(),nativeInput.issuedAt(),nativeInput.deadline(),
                ref,ref,ref,ref,ref,ref,ref,nativeInput.evidenceDirectory(),nativeInput.expectedHeadDigest(),RootLoadedReplacementRecoveryInputs.Mode.ORDINARY_PROFILE3);
        byte[] ordinaryBytes=RootLoadedReplacementRecoveryInputs.encode(ordinary);
        assertEquals(ordinary,RootLoadedReplacementRecoveryInputs.decode(ordinaryBytes));
        var wrong=StrictJson.parse(ordinaryBytes,65536).deepCopy();
        ((com.fasterxml.jackson.databind.node.ObjectNode)wrong).put("recovery_mode","native_campaign");
        assertThrows(IllegalArgumentException.class,()->RootLoadedReplacementRecoveryInputs.decode(StrictJson.canonical(wrong)));
        assertThrows(Exception.class,()->RootLoadedOrdinaryProfile.requireMaterial(null,null,policy()));
        assertThrows(Exception.class,()->RootLoadedOrdinaryProfile.readExact(ref,ref,ref,null,null,null,null,null,java.time.Clock.systemUTC()));
    }
}
