package org.xar.ck3.control.platform;

import static org.junit.jupiter.api.Assertions.*;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.ControlBuild;

/** Exercises the saved-plan producer with an expired real launch deadline; no process is created. */
final class NativeLaunchPlanReplacementDeadlineTest {
    private static final Instant ORIGINAL_DEADLINE=Instant.parse("2026-10-30T13:31:03.956251Z");
    @TempDir Path root;

    @Test void restoreAfterTheOriginalStartupUsesItsOwnOperationDeadline()throws IOException {
        var template=template(ORIGINAL_DEADLINE);
        Instant requested=Instant.now().plusSeconds(120);
        var child=template.savedReplacement("later-restore",save(template),requested);
        assertEquals(requested,child.deadline());
        assertDoesNotThrow(()->Win32Host.deadline(child.deadline()));
        assertEquals(ORIGINAL_DEADLINE,template.deadline());
        assertInstanceOf(NativeLaunchPlan.SavedGame.class,child.load());
        assertSame(template.sources(),child.sources());
        assertSame(template.preparedProfile(),child.preparedProfile());
    }

    @Test void replacementSteamObservationUsesTheNewOperationDeadline()throws IOException {
        var template=template(ORIGINAL_DEADLINE);
        Instant requested=Instant.now().plusSeconds(120);
        var child=template.savedReplacement("later-steam-observation",save(template),requested);
        assertEquals(requested,child.steam().deadline());
        assertDoesNotThrow(()->Win32Host.deadline(child.steam().deadline()));
        assertEquals(template.steam().machineId(),child.steam().machineId());
        assertEquals(template.steam().steamExecutable(),child.steam().steamExecutable());
        assertEquals(ORIGINAL_DEADLINE,template.steam().deadline());
    }

    @Test void shorterRequestedDeadlineStillBoundsTheWholeReplacement()throws IOException {
        var template=template(Instant.now().plusSeconds(300));
        Instant requested=Instant.now().plusSeconds(60);
        var child=template.savedReplacement("shorter-operation",save(template),requested);
        assertEquals(requested,child.deadline());
        assertEquals(requested,child.steam().deadline());
    }

    @Test void expiredReplacementRequestIsNotExtendedByTheTemplate()throws IOException {
        var template=template(Instant.now().plusSeconds(300));
        Instant requested=Instant.EPOCH;
        var child=template.savedReplacement("expired-operation",save(template),requested);
        assertEquals(requested,child.deadline());
        assertThrows(IOException.class,()->Win32Host.deadline(child.deadline()));
        assertThrows(IOException.class,()->Win32Host.deadline(child.steam().deadline()));
    }

    private NativeLaunchPlan template(Instant deadline)throws IOException {
        Path profile=Files.createDirectories(root.resolve("profile"));
        Path state=Files.createDirectories(root.resolve("state"));
        String machine="xenoamess-full-tower-eb9d2c1186";
        var sources=LaunchSourceBinding.accept(new LaunchSourceBinding.Review(machine,deadline,
                metadata("ck3.exe"),metadata("bridge.dll"),metadata("injector.exe"),
                new NativeLaunchEvidence.Inputs(metadata("environment.json"),metadata("build.json"),metadata("registration.json")),
                root,List.of()));
        return new NativeLaunchPlan("original-start","original-session",sources,profile,state,
                root.resolve("evidence/original-start"),"\\\\.\\pipe\\saved-deadline-fixture","bridge-fixture","adapter-fixture",
                new NativeLaunchPlan.NewGame(),false,NativeLaunchPlan.WindowPolicy.MINIMIZED_NO_ACTIVATE,
                Map.of(),1L<<30,64L<<20,deadline,Duration.ofSeconds(5),Duration.ofSeconds(30),
                new SteamOfflineProbe.Plan(machine,metadata("steam.exe"),deadline),NativeLaunchPlan.PreparedProfile.vanilla(),32);
    }

    private ControlBuild.FileRef save(NativeLaunchPlan template)throws IOException {
        Path saves=Files.createDirectories(template.profileDirectory().resolve("save games"));
        Path source=saves.resolve("native-checkpoint.ck3");
        Files.writeString(source,"software fixture only; no Game SAVE or RESTORE performed");
        return ControlBuild.FileRef.measure(source);
    }

    private ControlBuild.FileRef metadata(String name) {
        return new ControlBuild.FileRef(root.resolve(name).toString(),1,"c".repeat(64));
    }
}
