package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.NativeObservationPort.TransportSession;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.platform.LaunchSourceBinding;
import org.xar.ck3.control.platform.NativeLaunchEvidence;
import org.xar.ck3.control.platform.NativeLaunchPlan;
import org.xar.ck3.control.platform.NativeLaunchPlanCodec;
import org.xar.ck3.control.platform.SteamOfflineProbe;


/** Shared DATA projections only; these values create no Managed, RestoreBinding or admission. */
class RootRestoredDriverSessionTest {
    private static final String MACHINE="session-projection-fixture",PIPE="actual-restored-pipe",EPISODE="restored-episode";
    private static final BigInteger ACTOR=BigInteger.valueOf(1066);
    private static final GameGeneration GAME=new GameGeneration(120,new PythonOnlyUInt64(BigInteger.valueOf(10001)));
    private static final TransportSession TRANSPORT=new TransportSession(MACHINE,GAME,BigInteger.valueOf(3),"session-a");
    private static final SessionIdentity ADMITTED=new SessionIdentity(MACHINE,GAME,"session-a");
    private static final DriverStateSnapshot.Session DRIVER=new DriverStateSnapshot.Session(PIPE,GAME.pid(),ACTOR,EPISODE);
    @Test void driverProjectionMatchesItsDifferentTransportContractType()throws IOException {
        assertNotEquals(DRIVER,TRANSPORT);
        RootPostAdoptionCollector.requireDriverSession(DRIVER,TRANSPORT,ADMITTED,PIPE,ACTOR,EPISODE);
    }
    @Test void samePidDifferentBirthAndEveryDriverProjectionMismatchAreRejected() {
        var differentBirth=new GameGeneration(GAME.pid(),new PythonOnlyUInt64(BigInteger.valueOf(10002)));
        assertThrows(IOException.class,()->RootPostAdoptionCollector.requireDriverSession(DRIVER,TRANSPORT,
                new SessionIdentity(MACHINE,differentBirth,"session-a"),PIPE,ACTOR,EPISODE));
        assertThrows(IOException.class,()->RootPostAdoptionCollector.requireDriverSession(DRIVER,TRANSPORT,
                new SessionIdentity("other-machine",GAME,"session-a"),PIPE,ACTOR,EPISODE));
        assertThrows(IOException.class,()->RootPostAdoptionCollector.requireDriverSession(DRIVER,TRANSPORT,
                new SessionIdentity(MACHINE,GAME,"other-session"),PIPE,ACTOR,EPISODE));
        for(var wrong:java.util.List.of(new DriverStateSnapshot.Session(PIPE,121,ACTOR,EPISODE),
                new DriverStateSnapshot.Session(PIPE+"-other",120,ACTOR,EPISODE),
                new DriverStateSnapshot.Session(PIPE,120,ACTOR.add(BigInteger.ONE),EPISODE),
                new DriverStateSnapshot.Session(PIPE,120,ACTOR,EPISODE+"-other")))
            assertThrows(IOException.class,()->RootPostAdoptionCollector.requireDriverSession(wrong,TRANSPORT,ADMITTED,PIPE,ACTOR,EPISODE));
    }

    @TempDir Path temp;

    private ControlBuild.FileRef fileRef(String name) {
        return new ControlBuild.FileRef(temp.resolve(name).toAbsolutePath().toString(), 1, "a".repeat(64));
    }

    private NativeLaunchPlanCodec.Configuration baseConfig() {
        Instant deadline = Instant.parse("2030-01-01T00:00:00Z");
        var review = new LaunchSourceBinding.Review("software-only", deadline, fileRef("ck3.exe"), fileRef("xar_ck3_bridge.dll"), fileRef("xar_ck3_bridge_injector.exe"),
                new NativeLaunchEvidence.Inputs(fileRef("environment-actual.json"), fileRef("build-actual.json"), fileRef("registration-actual.json")), temp, List.of(fileRef("classes.jar")));
        var prepared = new NativeLaunchPlan.PreparedProfile(fileRef("manifest.json"), temp.resolve("mod"), "mod/example.mod", List.of(fileRef("prepared-input")), List.of(fileRef("mod/descriptor.mod")));
        return new NativeLaunchPlanCodec.Configuration("request", "session", review, temp, temp.resolve("state"), temp.resolve("evidence"), "\\\\.\\pipe\\software-only", "bridge-v1", "adapter-v1", new NativeLaunchPlan.NewGame(), false,
                NativeLaunchPlan.WindowPolicy.MINIMIZED_NO_ACTIVATE, Map.of("SOFTWARE_TEST", "a=b"), 9L << 30, 128L << 20, deadline, Duration.ofSeconds(10), Duration.ofMinutes(2),
                new SteamOfflineProbe.Plan("software-only", fileRef("steam.exe"), deadline), prepared, 128);
    }

    @Test void ordinaryLaunchConfigurationFeedsFactoryBeforeSaveAndRetainsGenuineSavedChild() throws IOException {
        var config=baseConfig();
        byte[] json=StrictJson.canonical(NativeLaunchPlanCodec.toJson(config),NativeLaunchPlanCodec.MAXIMUM_BYTES);
        var decoded=NativeLaunchPlanCodec.fromJson(StrictJson.parse(json,NativeLaunchPlanCodec.MAXIMUM_BYTES));
        assertEquals(config,decoded);
        NativeLaunchPlan plan=decoded.accept();
        Path savePath=plan.profileDirectory().resolve("save games").resolve("test-save.ck3");
        assertInstanceOf(NativeLaunchPlan.NewGame.class,plan.load());
        assertFalse(Files.exists(savePath));
        RootRestoreMaterialFactory.requireOrdinaryConfiguration(plan,plan);
        Files.createDirectories(savePath.getParent());Files.write(savePath,new byte[]{1,2,3});
        var saveRef=ControlBuild.FileRef.measure(savePath);
        NativeLaunchPlan child=plan.savedReplacement("parent-intent",saveRef,plan.deadline().minusSeconds(1));
        assertSame(plan.sources(),child.sources());
        assertEquals(saveRef,assertInstanceOf(NativeLaunchPlan.SavedGame.class,child.load()).save());
        assertNotEquals(plan.requestId(),child.requestId());assertNotEquals(plan.sessionId(),child.sessionId());
        RootRestoreMaterialFactory.requireOrdinaryConfiguration(plan,child);
        // Equal serialized configuration cannot replace this actual retained binding instance.
        assertThrows(IOException.class,()->RootRestoreMaterialFactory.requireOrdinaryConfiguration(plan,decoded.accept()));
        for(String field:List.of("profile","state","pipe","bridge","adapter","environment","prepared"))
            assertThrows(IOException.class,()->RootRestoreMaterialFactory.requireOrdinaryConfiguration(plan,changed(plan,field)),field);
    }

    private NativeLaunchPlan changed(NativeLaunchPlan plan,String field) {
        var prepared=field.equals("prepared")
                ?new NativeLaunchPlan.PreparedProfile(fileRef("other-manifest.json"),temp.resolve("other-mod"),
                        "mod/other.mod",List.of(fileRef("other-input")),List.of(fileRef("other/descriptor.mod")))
                :plan.preparedProfile();
        return new NativeLaunchPlan(plan.requestId(),plan.sessionId(),plan.sources(),
                field.equals("profile")?temp.resolve("other-profile"):plan.profileDirectory(),
                field.equals("state")?temp.resolve("other-state"):plan.stateDirectory(),plan.evidenceRoot(),
                field.equals("pipe")?"\\\\.\\pipe\\other":plan.pipeName(),
                field.equals("bridge")?"other-bridge":plan.bridgeVersion(),
                field.equals("adapter")?"other-adapter":plan.adapterId(),plan.load(),plan.debugMode(),plan.windowPolicy(),
                field.equals("environment")?Map.of("OTHER","value"):plan.environment(),plan.gameMemoryBytes(),
                plan.injectorMemoryBytes(),plan.deadline(),plan.injectorTimeout(),plan.startupTimeout(),plan.steam(),prepared,
                plan.maximumEvidenceRows());
    }
}


