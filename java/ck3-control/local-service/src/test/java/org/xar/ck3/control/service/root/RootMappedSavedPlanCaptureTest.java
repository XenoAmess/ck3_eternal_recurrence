package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Duration;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.NativeRunProfileManifest.ProfileKind;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.platform.LaunchSourceBinding;
import org.xar.ck3.control.platform.NativeLaunchPlan;
import org.xar.ck3.control.platform.NativeLaunchPlanCodec;
import org.xar.ck3.control.platform.SteamOfflineProbe;

/** Real small files and the mapped Command consumer; no Game, issuer, clone or Native proof is fabricated. */
final class RootMappedSavedPlanCaptureTest {
    private static final Instant GAME_CAP=Instant.parse("2026-11-18T08:02:00.000000001Z");
    private static final Instant STEAM_CAP=Instant.parse("2026-11-18T08:01:00.000000001Z");
    private static final Instant SOURCE_REVIEW=Instant.parse("2026-11-18T08:03:00.000000001Z");
    @TempDir Path root;

    private FileRef data(String name)throws IOException {
        Path target=root.resolve(name);
        Files.writeString(target,"software DATA only: "+name,StandardOpenOption.CREATE_NEW);
        return FileRef.measure(target);
    }
    private NativeLaunchPlanCodec.Configuration configuration()throws IOException {
        var executable=data("game-data.bin");var bridge=data("bridge-data.bin");
        var injector=data("injector-data.bin");var steam=data("steam.exe");
        var environment=data("environment-data.json");var save=data("checkpoint.ck3");
        var review=new LaunchSourceBinding.Review("software-data-only",SOURCE_REVIEW,
                executable,bridge,injector,null,null,List.of());
        return new NativeLaunchPlanCodec.Configuration("mapped-exact-data","mapped-exact-session",review,
                root.resolve("profile"),root.resolve("state"),root.resolve("evidence"),
                "\\\\.\\pipe\\mapped-exact-data","software-bridge","software-adapter",
                new NativeLaunchPlan.SavedGame("checkpoint",save),false,
                NativeLaunchPlan.WindowPolicy.MINIMIZED_NO_ACTIVATE,Map.of(),1L<<30,64L<<20,
                GAME_CAP,Duration.ofSeconds(5),Duration.ofSeconds(30),
                new SteamOfflineProbe.Plan("software-data-only",steam,STEAM_CAP),
                NativeLaunchPlan.PreparedProfile.explicit(environment,ProfileKind.SAVED_VANILLA,List.of(),List.of(environment)),32);
    }
    private static byte[] encode(NativeLaunchPlanCodec.Configuration configuration) {
        return StrictJson.canonical(NativeLaunchPlanCodec.toJson(configuration),NativeLaunchPlanCodec.MAXIMUM_BYTES);
    }
    private ExactRef writePlan(byte[] raw)throws IOException {
        Path path=root.resolve("mapped-plan.json");Files.write(path,raw,StandardOpenOption.CREATE_NEW);
        var ref=FileRef.measure(path);return new ExactRef(ref.path(),ref.bytes(),ref.sha256());
    }
    private static FileRef file(ExactRef ref){return new FileRef(ref.path(),ref.bytes(),ref.sha256());}
    private static void requireOriginalCaps(NativeLaunchPlan plan) {
        assertEquals(GAME_CAP,plan.deadline());
        assertEquals(STEAM_CAP,plan.steam().deadline());
        assertEquals(SOURCE_REVIEW,plan.sources().review().expiresAt());
        assertThrows(IllegalStateException.class,()->plan.sources().nativeProof());
    }

    @Test void actualMappedCommandConsumerKeepsTheOriginalDistinctCapsAndSavedSource()throws Exception {
        var original=configuration();var ref=writePlan(encode(original));
        var plan=RootProfileBootstrapCommand.readMappedSavedPlan(ref);
        assertEquals(original,NativeLaunchPlanCodec.describe(plan));
        requireOriginalCaps(plan);
        assertInstanceOf(NativeLaunchPlan.SavedGame.class,plan.load());
        assertEquals(original.load(),plan.load());
    }

    @Test void equalLengthBThenRestoredAVerifiesThePathButCannotAuthorizeAnExtendedPlan()throws Exception {
        var original=configuration();byte[] rawA=encode(original);var refA=writePlan(rawA);
        var changed=NativeLaunchPlanCodec.toJson(original);
        changed.put("deadline",GAME_CAP.plusNanos(1).toString());
        ((com.fasterxml.jackson.databind.node.ObjectNode)changed.get("steam")).put("deadline",STEAM_CAP.plusNanos(1).toString());
        ((com.fasterxml.jackson.databind.node.ObjectNode)changed.get("review")).put("expires_at",SOURCE_REVIEW.plusNanos(1).toString());
        byte[] rawB=StrictJson.canonical(changed,NativeLaunchPlanCodec.MAXIMUM_BYTES);
        assertEquals(rawA.length,rawB.length,"same length isolates the missing captured SHA check");
        Path path=Path.of(refA.path());Files.write(path,rawB);

        // This is the old Command's path-only decode, using the real codec against physical B.
        var alreadyDecodedB=NativeLaunchPlanCodec.read(path);
        assertEquals(GAME_CAP.plusNanos(1),alreadyDecodedB.deadline());
        assertThrows(IOException.class,()->RootProfileBootstrapCommand.readMappedSavedPlan(refA));

        // Restoring A makes subsequent original/pin verification succeed; it cannot repair decoded B.
        Files.write(path,rawA);file(refA).verify();
        assertEquals(STEAM_CAP.plusNanos(1),alreadyDecodedB.steam().deadline());
        assertEquals(SOURCE_REVIEW.plusNanos(1),alreadyDecodedB.sources().review().expiresAt());
        var current=RootProfileBootstrapCommand.readMappedSavedPlan(refA);
        requireOriginalCaps(current);
        assertEquals(original,NativeLaunchPlanCodec.describe(current));
    }

    @Test void differingCapturedLengthCannotReachTheMappedPlanDecoder()throws Exception {
        byte[] raw=encode(configuration());var ref=writePlan(raw);
        Files.writeString(Path.of(ref.path())," ",StandardOpenOption.APPEND);
        assertThrows(IOException.class,()->RootProfileBootstrapCommand.readMappedSavedPlan(ref));
        assertEquals(raw.length+1,Files.size(Path.of(ref.path())));
    }

    @Test void fixedCodecCapRejectsAnOversizedDeclaredSourceBeforeOpeningAnAbsentPath() {
        var ref=new ExactRef(root.resolve("absent-plan.json").toString(),
                (long)NativeLaunchPlanCodec.MAXIMUM_BYTES+1,"a".repeat(64));
        assertThrows(IOException.class,()->RootProfileBootstrapCommand.readMappedSavedPlan(ref));
        assertFalse(Files.exists(Path.of(ref.path())));
    }

    @Test void matchingPhysicalHashCannotMakeMalformedPlanDataAcceptable()throws Exception {
        var ref=writePlan("{}".getBytes(java.nio.charset.StandardCharsets.UTF_8));
        file(ref).verify();
        assertThrows(IOException.class,()->RootProfileBootstrapCommand.readMappedSavedPlan(ref));
    }
}
