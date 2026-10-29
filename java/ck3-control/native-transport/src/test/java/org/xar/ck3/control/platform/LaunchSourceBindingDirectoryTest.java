package org.xar.ck3.control.platform;

import static org.junit.jupiter.api.Assertions.*;

import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Ordinary configuration regressions. No Native proof, process or Game result is fabricated. */
final class LaunchSourceBindingDirectoryTest {
    @TempDir Path temporary;

    private ControlBuild.FileRef ref(String name) {
        return new ControlBuild.FileRef(temporary.resolve(name).toAbsolutePath().toString(),1,"a".repeat(64));
    }
    private NativeLaunchPlanCodec.Configuration configuration() {
        var review=new LaunchSourceBinding.Review(null,null,ref("ck3.exe"),ref("xar_ck3_bridge.dll"),
                ref("xar_ck3_bridge_injector.exe"),null,null,List.of());
        var prepared=new NativeLaunchPlan.PreparedProfile(ref("environment.json"),temporary.resolve("mod"),
                "mod/example.mod",List.of(),List.of());
        return new NativeLaunchPlanCodec.Configuration("request","session",review,temporary,
                temporary.resolve("state"),temporary.resolve("evidence"),"\\\\.\\pipe\\ordinary",
                "bridge","adapter",new NativeLaunchPlan.NewGame(),false,
                NativeLaunchPlan.WindowPolicy.MINIMIZED_NO_ACTIVATE,Map.of(),1,1,
                Instant.parse("2100-01-01T00:00:00Z"),Duration.ofMinutes(2),Duration.ofMinutes(20),
                new SteamOfflineProbe.Plan("software-only",ref("steam.exe"),Instant.EPOCH),prepared,1);
    }
    @Test void ordinaryConfigurationConstructsWithoutNativeReaderOrHistoricalFiles() throws Exception {
        var configured=configuration();
        var plan=configured.accept(expected->{throw new AssertionError("Launch must not request a Native proof");});
        assertEquals(configured.review().gameExecutable(),plan.sources().review().gameExecutable());
        assertEquals(configured.review().bridgeDll(),plan.sources().review().bridgeDll());
        assertEquals(configured.review().injector(),plan.sources().review().injector());
        assertEquals(configured.review().nativeEvidence(),plan.sources().review().nativeEvidence());
        assertEquals(configured.review().nativeSourceRoot(),plan.sources().review().nativeSourceRoot());
        assertEquals(configured.review().completeRuntimeSources(),plan.sources().review().completeRuntimeSources());
        assertEquals(configured.steam().machineId(),plan.sources().review().machineId());
        assertNull(configured.review().machineId());
        assertEquals(configured.review().expiresAt(),plan.sources().review().expiresAt());
        assertEquals(List.of("-gdpr-compliant","-userdir="+temporary),plan.gameArguments());
        assertFalse(Files.exists(Path.of(configured.review().gameExecutable().path())));
        assertNull(plan.sources().review().nativeEvidence());
        assertThrows(IllegalStateException.class,plan.sources()::nativeProof);
        plan.sources().verify();
        plan.sources().requireLoadedClass(LaunchSourceBindingDirectoryTest.class);
        plan.preparedProfile().verify(plan);
    }
    @Test void optionalHistoricalMetadataRoundTripsWithoutCreatingQualification() throws Exception {
        var configured=configuration();
        byte[] bytes=StrictJson.canonical(NativeLaunchPlanCodec.toJson(configured),NativeLaunchPlanCodec.MAXIMUM_BYTES);
        var decoded=NativeLaunchPlanCodec.fromJson(StrictJson.parse(bytes,NativeLaunchPlanCodec.MAXIMUM_BYTES));
        assertEquals(configured,decoded);
        assertNotNull(decoded.accept());
    }
    @Test void readingConfigurationDoesNotHashOldSourcePinsOrInvokeTheHistoricalReader() throws Exception {
        var configured=configuration();
        Path file=temporary.resolve("launch.json");
        Files.write(file,StrictJson.canonical(NativeLaunchPlanCodec.toJson(configured),NativeLaunchPlanCodec.MAXIMUM_BYTES));
        // Deliberately stale metadata: the current configuration body supplies the actual launch values.
        var metadata=new ExactRef(file.toString(),1,"b".repeat(64));
        var actual=NativeLaunchPlanCodec.readExact(metadata,expected->{throw new AssertionError("Historical reader invoked");});
        assertEquals("request",actual.requestId());
        assertEquals(configured.gameMemoryBytes(),actual.gameMemoryBytes());
    }
    @Test void acceptedMachineReachesTheActualEndpointAndOwnerForAbsentAndNullMetadata() throws Exception {
        for(boolean explicitNull:List.of(false,true)) {
            var wire=NativeLaunchPlanCodec.toJson(configuration());
            wire.put("schema","xar.java-game-launch-plan/v4");wire.remove("prepared_profile");
            var metadata=(com.fasterxml.jackson.databind.node.ObjectNode)wire.get("review");
            if(explicitNull)metadata.putNull("machine_id");else metadata.remove("machine_id");
            metadata.put("expires_at",Instant.EPOCH.toString());
            var configured=NativeLaunchPlanCodec.fromJson(wire);
            var unchanged=NativeLaunchPlanCodec.toJson(configured);
            var plan=configured.accept(expected->{throw new AssertionError("Configuration must not request Native proof");});
            assertNull(configured.review().machineId());
            var identity=new org.xar.ck3.control.build.WindowsJobProcess.ProcessIdentity(
                    42,"134376718582643410",temporary.resolve("software.exe").toString());
            var endpoint=new org.xar.ck3.control.nativebridge.NativePipeEndpoint.Config(
                    plan.pipeName(),plan.sources().review().machineId(),ManagedGameSession.generation(identity),
                    plan.sessionId(),plan.bridgeVersion(),plan.sources().review().gameExecutable().sha256(),plan.adapterId());
            assertEquals(configured.steam().machineId(),endpoint.machineId());
            assertEquals(Instant.EPOCH,plan.sources().review().expiresAt());
            var effective=NativeLaunchPlanCodec.describe(plan);
            byte[] encoded=StrictJson.canonical(NativeLaunchPlanCodec.toJson(effective),NativeLaunchPlanCodec.MAXIMUM_BYTES);
            assertEquals(effective,NativeLaunchPlanCodec.fromJson(StrictJson.parse(encoded,NativeLaunchPlanCodec.MAXIMUM_BYTES)));
            var descriptor=new GameSupervisorControl.Descriptor(endpoint.machineId(),plan.sessionId(),
                    identity,identity,effective,new ExactRef(ref("hello.json").path(),1,"a".repeat(64)),
                    new ExactRef(ref("launch.json").path(),1,"b".repeat(64)),
                    temporary.resolve(GameSupervisorControl.STOP_FILE),temporary.resolve(GameSupervisorControl.TERMINAL_FILE));
            Path owner=temporary.resolve(explicitNull?"owner-null.json":"owner-absent.json");
            GameSupervisorControl.writeDescriptor(owner,descriptor);
            assertEquals(descriptor,GameSupervisorControl.readDescriptor(owner));
            assertEquals(unchanged,NativeLaunchPlanCodec.toJson(configured));
            assertNull(plan.sources().review().nativeEvidence());
            assertThrows(IllegalStateException.class,plan.sources()::nativeProof);
            assertFalse(Files.exists(Path.of(configured.review().gameExecutable().path())));
        }
        var explicit=NativeLaunchPlanCodec.toJson(configuration());
        ((com.fasterxml.jackson.databind.node.ObjectNode)explicit.get("review")).put("machine_id","configured-host");
        var configured=NativeLaunchPlanCodec.fromJson(explicit);
        assertSame(configured.review(),configured.accept().sources().review());
    }
    @Test void ordinaryNewNoModsLaunchRejectsSystemVolumeBeforeAnyStateMutation() throws Exception {
        assertInitialNoModsVolumeRejection(false);
    }
    @Test void ordinarySavedNoModsLaunchRejectsSystemVolumeBeforeAnyStateMutation() throws Exception {
        assertInitialNoModsVolumeRejection(true);
    }
    private void assertInitialNoModsVolumeRejection(boolean saved) throws Exception {
        String systemRoot=System.getenv("SystemRoot");
        if(systemRoot==null||!System.getProperty("os.name","").startsWith("Windows"))
            throw new IllegalStateException("Physical-volume regression requires Windows SystemRoot");
        String before=System.getProperty(org.xar.ck3.control.build.ProjectStoragePolicy.FORBID_SYSTEM_VOLUME_BULK);
        String beforeRoot=System.getProperty(org.xar.ck3.control.build.ProjectStoragePolicy.PROJECT_STORAGE_ROOT);
        Path forbidden=Path.of(systemRoot).resolve("xar-sdk-current-no-create-"+java.util.UUID.randomUUID());
        Path state=temporary.resolve(saved?"saved-state":"new-state");
        Path evidence=temporary.resolve(saved?"saved-evidence":"new-evidence");
        try {
            System.setProperty(org.xar.ck3.control.build.ProjectStoragePolicy.FORBID_SYSTEM_VOLUME_BULK,"true");
            System.setProperty(org.xar.ck3.control.build.ProjectStoragePolicy.PROJECT_STORAGE_ROOT,temporary.toString());
            var wire=NativeLaunchPlanCodec.toJson(configuration());
            wire.put("schema","xar.java-game-launch-plan/v4");wire.remove("prepared_profile");
            wire.put("profile_directory",forbidden.toString());wire.put("state_directory",state.toString());
            wire.put("evidence_root",evidence.toString());wire.put("deadline",Instant.now().plusSeconds(60).toString());
            var environment=(com.fasterxml.jackson.databind.node.ObjectNode)wire.get("environment");
            environment.put("TEMP",temporary.toString());environment.put("TMP",temporary.toString());
            if(saved) {
                var load=StrictJson.object().put("kind","SAVED_GAME").put("basename","software-save");
                load.set("save",new ExactRef(forbidden.resolve("save games/software-save.ck3").toString(),1,"a".repeat(64)).toJson());
                wire.set("load",load);
            }
            var plan=NativeLaunchPlanCodec.fromJson(wire).accept();
            assertFalse(Files.exists(Path.of(plan.sources().review().gameExecutable().path())),
                    "Absent software EXE guarantees this regression cannot start a Game even before the fix");
            var lifecycle=new JavaGameLifecycle(List.of());
            java.io.IOException failure=assertThrows(java.io.IOException.class,
                    ()->{if(saved)lifecycle.launchSaved(plan);else lifecycle.launchNew(plan);});
            assertAll("Initial current launch policy must reject before mutation",
                    ()->assertTrue(failure.getMessage().contains("system volume"),failure.toString()),
                    ()->assertFalse(Files.exists(state),"state directory must remain absent"),
                    ()->assertFalse(Files.exists(evidence),"evidence directory must remain absent"),
                    ()->assertFalse(Files.exists(forbidden),"forbidden profile must remain absent"));
        } finally {
            if(before==null)System.clearProperty(org.xar.ck3.control.build.ProjectStoragePolicy.FORBID_SYSTEM_VOLUME_BULK);
            else System.setProperty(org.xar.ck3.control.build.ProjectStoragePolicy.FORBID_SYSTEM_VOLUME_BULK,before);
            if(beforeRoot==null)System.clearProperty(org.xar.ck3.control.build.ProjectStoragePolicy.PROJECT_STORAGE_ROOT);
            else System.setProperty(org.xar.ck3.control.build.ProjectStoragePolicy.PROJECT_STORAGE_ROOT,beforeRoot);
        }
    }
    @Test void missingActualArgumentsAndWrongJsonTypesStillReject() {
        var configured=configuration();
        var missing=NativeLaunchPlanCodec.toJson(configured);
        ((com.fasterxml.jackson.databind.node.ObjectNode)missing.get("review")).remove("bridge_dll");
        assertThrows(IllegalArgumentException.class,()->NativeLaunchPlanCodec.fromJson(missing));
        var wrong=NativeLaunchPlanCodec.toJson(configured);wrong.put("game_memory_bytes",true);
        assertThrows(IllegalArgumentException.class,()->NativeLaunchPlanCodec.fromJson(wrong));
        assertThrows(IllegalArgumentException.class,()->new NativeLaunchPlan("request","session",
                LaunchSourceBinding.accept(configured.review()),temporary,temporary,temporary,"invalid",
                "bridge","adapter",new NativeLaunchPlan.NewGame(),false,configured.windowPolicy(),Map.of(),
                1,1,configured.deadline(),configured.injectorTimeout(),configured.startupTimeout(),configured.steam(),
                configured.preparedProfile(),1));
    }
}
