package org.xar.ck3.control.platform;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.time.Duration;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.checkpoint.CheckpointPairCodec;
import org.xar.ck3.control.application.checkpoint.NativeCheckpointFiles;
import org.xar.ck3.control.build.ControlBuild;

/** Tiny physical-file DATA tests; no Game, process, Steam, Ready or canonical writer is created. */
final class NativeSavedGameCloneTest {
    @TempDir Path temporary;
    private final NativeCheckpointFiles files=new NativeCheckpointFiles();
    private ControlBuild.FileRef metadata(String name) {
        return new ControlBuild.FileRef(temporary.resolve(name).toString(),1,"c".repeat(64));
    }
    private NativeLaunchPlan plan(Path profile,NativeLaunchPlan.SavedGame saved)throws IOException {
        Instant deadline=Instant.now().plusSeconds(60);String machine="xenoamess-full-tower-eb9d2c1186";
        var sources=LaunchSourceBinding.accept(new LaunchSourceBinding.Review(machine,deadline,
                metadata("ck3.exe"),metadata("bridge.dll"),metadata("injector.exe"),
                new NativeLaunchEvidence.Inputs(metadata("environment.json"),metadata("build.json"),metadata("registration.json")),
                temporary,List.of()));
        return new NativeLaunchPlan("source-clone-fixture","fixture-session",sources,profile,temporary.resolve("state"),
                temporary.resolve("evidence"),"\\\\.\\pipe\\source-clone-fixture","fixture-bridge","fixture-adapter",saved,false,
                NativeLaunchPlan.WindowPolicy.MINIMIZED_NO_ACTIVATE,Map.of(),1L<<30,64L<<20,deadline,
                Duration.ofSeconds(5),Duration.ofSeconds(30),new SteamOfflineProbe.Plan(machine,metadata("steam.exe"),deadline),
                NativeLaunchPlan.PreparedProfile.vanilla(),32);
    }
    private NativeLaunchPlan external()throws IOException {
        Path source=temporary.resolve("original/checkpoint.ck3");Files.createDirectories(source.getParent());
        Files.writeString(source,"SAV0100\nmeta_data={original_fixture=yes}\n");
        Path profile=Files.createDirectory(temporary.resolve("new-profile"));
        return plan(profile,new NativeLaunchPlan.SavedGame("checkpoint",ControlBuild.FileRef.measure(source)));
    }
    private static void replaceEqualBytes(Path target,Path replacement)throws IOException {
        Files.copy(target,replacement);Files.setLastModifiedTime(replacement,Files.getLastModifiedTime(target));
        Files.move(target,target.resolveSibling("retained-"+target.getFileName()),StandardCopyOption.ATOMIC_MOVE);
        Files.move(replacement,target,StandardCopyOption.ATOMIC_MOVE);
    }

    @Test void actualProfileCloneKeepsTheOriginalSourceWitnessAndBothNativeIdentities()throws Exception {
        var plan=external();var saved=(NativeLaunchPlan.SavedGame)plan.load();
        var original=files.observe(Path.of(saved.save().path())).orElseThrow();
        byte[] before=CheckpointPairCodec.fileWitnessToJson(original).toString().getBytes(java.nio.charset.StandardCharsets.UTF_8);
        NativeSavedGameFiles.materialize(plan.profileDirectory(),saved);
        var mapping=NativeSavedGameClone.observe(plan,original);
        assertEquals(original,mapping.originalSave());assertFalse(mapping.inPlace());
        assertThrows(IOException.class,()->NativeSavedGameClone.observe(plan,mapping.actualSave()));
        assertThrows(IOException.class,()->mapping.requireCurrent(plan,mapping.actualSave()));
        assertEquals(plan.profileDirectory().resolve("save games/checkpoint.ck3").toString(),mapping.actualSave().reference().path());
        assertEquals(original.reference().sha256(),mapping.actualSave().reference().sha256());
        assertNotEquals(original.identity().fileId(),mapping.actualSave().identity().fileId());
        mapping.requireCurrent(plan,original);files.verify(original);
        var wire=mapping.toJson();assertEquals(NativeSavedGameClone.SCHEMA,wire.get("schema").textValue());
        assertEquals(original,CheckpointPairCodec.fileWitnessFromJson(wire.get("original_save")));
        assertEquals(mapping.actualSave(),CheckpointPairCodec.fileWitnessFromJson(wire.get("actual_save")));
        assertTrue(wire.get("original_native_identity").get("file_id_decimal").isTextual());
        assertTrue(wire.get("actual_native_identity").get("volume_serial_decimal").isTextual());
        assertArrayEquals(before,CheckpointPairCodec.fileWitnessToJson(original).toString().getBytes(java.nio.charset.StandardCharsets.UTF_8));
        assertSame(saved,plan.load());assertSame(saved.save(),((NativeLaunchPlan.SavedGame)plan.load()).save());
    }

    @Test void absentOrDifferentActualCloneCannotBeQualifiedFromTheOriginalSourceAlone()throws Exception {
        var plan=external();var saved=(NativeLaunchPlan.SavedGame)plan.load();
        var original=files.observe(Path.of(saved.save().path())).orElseThrow();
        assertThrows(IOException.class,()->NativeSavedGameClone.observe(plan,original));
        Path target=NativeSavedGameClone.actualPath(plan);Files.createDirectories(target.getParent());Files.writeString(target,"different");
        assertThrows(IOException.class,()->NativeSavedGameClone.observe(plan,original));files.verify(original);
    }

    @Test void sameBytesAndMtimeAtActualPathCannotReplaceAnObservedCloneFileId()throws Exception {
        var plan=external();var saved=(NativeLaunchPlan.SavedGame)plan.load();
        var original=files.observe(Path.of(saved.save().path())).orElseThrow();NativeSavedGameFiles.materialize(plan.profileDirectory(),saved);
        var mapping=NativeSavedGameClone.observe(plan,original);Path target=NativeSavedGameClone.actualPath(plan);
        replaceEqualBytes(target,target.resolveSibling("replacement.ck3"));
        var replaced=files.observe(target).orElseThrow();assertEquals(mapping.actualSave().reference(),replaced.reference());
        assertNotEquals(mapping.actualSave().identity().fileId(),replaced.identity().fileId());
        assertThrows(IOException.class,()->mapping.requireCurrent(plan,original));files.verify(original);
    }

    @Test void sameBytesAndMtimeAtOriginalPathCannotRefreshTheOriginalPairWitness()throws Exception {
        var plan=external();var saved=(NativeLaunchPlan.SavedGame)plan.load();Path source=Path.of(saved.save().path());
        var original=files.observe(source).orElseThrow();NativeSavedGameFiles.materialize(plan.profileDirectory(),saved);
        var mapping=NativeSavedGameClone.observe(plan,original);replaceEqualBytes(source,source.resolveSibling("replacement.ck3"));
        assertThrows(IOException.class,()->mapping.requireCurrent(plan,original));
        assertThrows(IOException.class,()->NativeSavedGameClone.observe(plan,original));
        assertEquals(original.reference(),files.observe(source).orElseThrow().reference());
    }

    @Test void externalHardLinkCannotBeAnIndependentIsolatedClone()throws Exception {
        var plan=external();var saved=(NativeLaunchPlan.SavedGame)plan.load();Path source=Path.of(saved.save().path());
        var original=files.observe(source).orElseThrow();Path target=NativeSavedGameClone.actualPath(plan);
        Files.createDirectories(target.getParent());Files.createLink(target,source);
        assertThrows(IOException.class,()->NativeSavedGameClone.observe(plan,original));
        assertArrayEquals(Files.readAllBytes(source),Files.readAllBytes(target));
    }

    @Test void identicalPlanIdentityCannotBeReplacedByAnEqualDecodedPlan()throws Exception {
        var plan=external();var saved=(NativeLaunchPlan.SavedGame)plan.load();
        var original=files.observe(Path.of(saved.save().path())).orElseThrow();NativeSavedGameFiles.materialize(plan.profileDirectory(),saved);
        var mapping=NativeSavedGameClone.observe(plan,original);
        var equal=NativeLaunchPlanCodec.fromJson(NativeLaunchPlanCodec.toJson(NativeLaunchPlanCodec.describe(plan))).accept();
        assertNotSame(plan,equal);assertThrows(IOException.class,()->mapping.requireCurrent(equal,original));
        mapping.requireCurrent(plan,original);
    }

    @Test void legacySourceAlreadyAtActualLoadPathKeepsItsOriginalIdentity()throws Exception {
        Path profile=Files.createDirectory(temporary.resolve("in-place-profile"));
        Path saves=Files.createDirectory(profile.resolve("save games"));Path source=saves.resolve("checkpoint.ck3");
        Files.writeString(source,"software-only in-place legacy source");
        var saved=new NativeLaunchPlan.SavedGame("checkpoint",ControlBuild.FileRef.measure(source));var plan=plan(profile,saved);
        var original=files.observe(source).orElseThrow();var mapping=NativeSavedGameClone.observe(plan,original);
        assertTrue(mapping.inPlace());assertEquals(original,mapping.originalSave());assertEquals(original,mapping.actualSave());
        mapping.requireCurrent(plan,original);files.verify(original);
    }
}
