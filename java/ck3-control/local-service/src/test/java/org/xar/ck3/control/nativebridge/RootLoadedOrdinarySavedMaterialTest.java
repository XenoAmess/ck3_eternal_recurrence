package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.condition.EnabledOnOs;
import org.junit.jupiter.api.condition.OS;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.checkpoint.*;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.service.root.*;
import org.xar.ck3.control.wave3.governance.lifecycle.SuccessionLifecycleCodec;

/** Real ordinary software SAVE and private Store provenance; produced metadata grants no Game or loaded role. */
@EnabledOnOs(OS.WINDOWS)
final class RootLoadedOrdinarySavedMaterialTest {
    @TempDir Path temporary;
    @Test void genuineOrdinarySavedMaterialProducesExactPolicyCopyAndRejectsWrongBindingOrUnheldRole()throws Exception {
        byte[] policy=("\r\n"+new String(RootLoadedOrdinaryProfileContractTest.policy(),StandardCharsets.UTF_8)+"\r\n").getBytes(StandardCharsets.UTF_8);
        Path originalPolicy=temporary.resolve("original-policy.json");Files.write(originalPolicy,policy);
        Path root=temporary.resolve("ordinary-source");
        try(var f=new CheckpointSourceCompositionTest.Fixture(root,false,Clock.systemUTC(),Optional.empty(),Optional.empty(),List.of(),
                Duration.ofSeconds(90),root.resolve("profile"),Optional.empty(),
                Optional.of(CheckpointSourceCompositionTest.freshReconciliationReads()),false,true,1,
                Optional.of(RootLoadedOrdinaryProfileContractTest.lifecycle()))) {
            byte[] command=ActionCodec.encodeCommand(f.request.saveCommand());Instant deadline=f.request.saveCommand().deadline();
            var result=f.service.checkpoint(f.request);
            if(result instanceof CheckpointResult.Unknown unknown) {
                var action=unknown.action().orElseThrow();assertTrue(action.ack().orElseThrow().nativeOk(),result::toString);
                result=f.service.queryOriginal(unknown.actionId(),Instant.now().plusSeconds(30));
            }
            var confirmed=assertInstanceOf(CheckpointResult.Confirmed.class,result,result.toString());
            assertArrayEquals(command,ActionCodec.encodeCommand(confirmed.action().command()));assertEquals(deadline,confirmed.action().command().deadline());
            f.saveBoundary(confirmed.pair());
            var material=f.actual.writer.locked(same->{
                var actual=f.sources.load(confirmed.pair());String head=same.head().digest();
                assertEquals(3,actual.sourceSemantic().frame().observationVersion());
                assertInstanceOf(DriverStateSnapshot.Value.class,actual.savedDriver().successionLifecycle());
                assertArrayEquals(SuccessionLifecycleCodec.normalize(RootLoadedOrdinaryProfileContractTest.lifecycle().bytes()),
                        RootLoadedOrdinaryProfile.requireMaterial(same,actual,policy).bytes());
                var wrong=(com.fasterxml.jackson.databind.node.ObjectNode)StrictJson.parse(policy,1<<20);
                ((com.fasterxml.jackson.databind.node.ObjectNode)wrong.get("succession_lifecycle")).put("source","another-producer");
                assertThrows(Exception.class,()->RootLoadedOrdinaryProfile.requireMaterial(same,actual,StrictJson.canonical(wrong)));
                var nativePolicy=StrictJson.object().put("schema","xar.java.initial-episode-saved-native-projection/v1");nativePolicy.putNull("succession_lifecycle");
                assertThrows(Exception.class,()->RootLoadedOrdinaryProfile.requireMaterial(same,actual,StrictJson.canonical(nativePolicy)));
                assertEquals(head,same.head().digest());return actual;
            });
            Path pairFile=temporary.resolve("pair.json");Files.write(pairFile,CheckpointPairCodec.encode(confirmed.pair()));
            Path environment=temporary.resolve("environment.json");Files.writeString(environment,"{}");
            Path owner=temporary.resolve("unqualified-owner-data.json");Files.writeString(owner,"{}");
            Path output=Files.createDirectory(temporary.resolve("outputs"));Path target=output.resolve("ordinary-profile.json");
            Instant now=Instant.now();var environmentRef=RootLoadedOrdinaryProfileContractTest.ref(environment);
            var ownerRef=RootLoadedOrdinaryProfileContractTest.ref(owner);
            // These are honest source-only fixture records. No private LoadedReplacement is fabricated.
            var profile=new RootFrozenRunProfile.Request(WindowsJobProcess.currentMachineId(),now.minusSeconds(1),now.plusSeconds(90),
                    "ordinary-software-request","ordinary-software-session",environmentRef,
                    RootFrozenRunProfile.LifecycleMode.ORDINARY_CAMPAIGN_SUCCESSION,true,new RootFrozenRunProfile.Enabled(root));
            var request=new RootLoadedOrdinaryProfile.Request(profile,ownerRef,ownerRef,ownerRef,
                    RootLoadedOrdinaryProfileContractTest.ref(pairFile),material.witness(),
                    RootLoadedOrdinaryProfileContractTest.ref(originalPolicy),output.resolve("ordinary-policy.json"));
            Path producerInput=temporary.resolve("producer-v3.json");Files.write(producerInput,RootLoadedOrdinaryProfile.encodeRequest(request));
            var prepared=RootOriginalDriverRunProfileProducer.prepare(ControlBuild.FileRef.measure(producerInput),target,Clock.systemUTC());
            assertArrayEquals(policy,prepared.ordinaryPolicyCopy().orElseThrow().bytes());
            var body=RootProfileBootstrapInputs.originalDriverRunProfile(prepared);
            assertEquals(2,body.quote().size());
            assertEquals(RootBootstrapOutputContract.Kind.ORIGINAL_DRIVER_RUN_PROFILE,body.quote().get(0).kind());
            assertEquals(RootBootstrapOutputContract.Kind.INITIAL_POLICY,body.quote().get(1).kind());
            assertFalse(Files.exists(target));assertFalse(Files.exists(request.policyTarget()),"preparation and quote have zero output writes");
            // Readback checks on controlled test bytes; no bootstrap permit, loaded role or admission is claimed.
            Files.write(target,prepared.bytes());Files.write(request.policyTarget(),prepared.ordinaryPolicyCopy().orElseThrow().bytes());
            prepared.verifyCreated();
            assertArrayEquals(Files.readAllBytes(originalPolicy),Files.readAllBytes(request.policyTarget()));
            assertThrows(Exception.class,()->RootLoadedOrdinaryProfile.readExact(RootLoadedOrdinaryProfileContractTest.ref(target),
                    RootLoadedOrdinaryProfileContractTest.ref(request.policyTarget()),ownerRef,null,null,null,material,null,Clock.systemUTC()));
            Files.writeString(request.policyTarget(),"null");assertThrows(Exception.class,prepared::verifyCreated);
            assertEquals(1,f.actual.nativeActionWrites(),"one original software SAVE, no replay or Game action");
        }
    }
}
