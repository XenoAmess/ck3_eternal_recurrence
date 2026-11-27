package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

import java.io.IOException;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.condition.EnabledOnOs;
import org.junit.jupiter.api.condition.OS;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.checkpoint.CheckpointPair;
import org.xar.ck3.control.application.checkpoint.NativeCheckpointFiles;
import org.xar.ck3.control.application.readiness.NativeReadiness;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.continuity.OriginalWindowReducer;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.platform.LaunchSourceBinding;
import org.xar.ck3.control.platform.NativeLaunchEvidence;
import org.xar.ck3.control.platform.NativeLaunchPlan;
import org.xar.ck3.control.platform.NativeLaunchPlanCodec;
import org.xar.ck3.control.platform.SteamOfflineProbe;

@EnabledOnOs(OS.WINDOWS)
final class RootImportedCheckpointPathsTest {
    @TempDir Path root;
    private final NativeCheckpointFiles files = new NativeCheckpointFiles();
    private static final Instant NOW = Instant.parse("2026-11-27T01:30:00Z");

    @Test void successorCanReuseItsOwnConfirmedOutputWhileKeepingTheImportedLineage() throws Exception {
        var profile = Files.createDirectory(root.resolve("profile"));
        var output = Files.createDirectories(profile.resolve("save games")).resolve("xar_checkpoint.ck3");
        var imported = pair(root.resolve("imported.ck3"),"lineage",100);
        var latest = pair(output,"lineage",200);
        var base = configuration();
        var actual = RootOrdinaryRuntimeAssembly.retainImportedCheckpointPaths(base,launch(profile),imported,latest,files);

        assertEquals(output,actual.checkpoints().save());
        assertEquals(imported.lineageId(),actual.checkpoints().lineageId());
        assertEquals(base.checkpoints().driverCheckpoint(),actual.checkpoints().driverCheckpoint());
        assertEquals(base.deadline(),actual.deadline());
        assertEquals("save-100",Files.readString(Path.of(imported.save().reference().path())));
        assertEquals("save-200",Files.readString(output));
    }

    @Test void rejectsDifferentLineageAndAnOutputLinkedToTheOldImportedSave() throws Exception {
        var profile = Files.createDirectory(root.resolve("profile"));
        var output = Files.createDirectories(profile.resolve("save games")).resolve("xar_checkpoint.ck3");
        var imported = pair(root.resolve("imported.ck3"),"lineage",100);
        var foreign = pair(root.resolve("foreign.ck3"),"foreign-lineage",200);
        var game = launch(profile);
        var base = configuration();

        assertThrows(IOException.class,() ->
                RootOrdinaryRuntimeAssembly.retainImportedCheckpointPaths(base,game,imported,foreign,files));
        Files.createLink(output,Path.of(imported.save().reference().path()));
        assertThrows(IOException.class,() ->
                RootOrdinaryRuntimeAssembly.retainImportedCheckpointPaths(base,game,imported,imported,files));
    }

    @Test void onlyTheLatestConfirmedPairMustMatchTheCurrentOnDiskFiles() throws Exception {
        var profile = Files.createDirectory(root.resolve("profile"));
        var output = Files.createDirectories(profile.resolve("save games")).resolve("xar_checkpoint.ck3");
        var imported = pair(root.resolve("imported.ck3"),"lineage",100);
        var first = pair(output,"lineage",200);
        var game = launch(profile);
        var base = configuration();
        RootOrdinaryRuntimeAssembly.retainImportedCheckpointPaths(base,game,imported,first,files);

        var latest = pair(output,"lineage",300);
        assertThrows(IOException.class,() ->
                RootOrdinaryRuntimeAssembly.retainImportedCheckpointPaths(base,game,imported,first,files));
        assertEquals(output,RootOrdinaryRuntimeAssembly
                .retainImportedCheckpointPaths(base,game,imported,latest,files).checkpoints().save());
        Files.delete(output);
        assertThrows(IOException.class,() ->
                RootOrdinaryRuntimeAssembly.retainImportedCheckpointPaths(base,game,imported,latest,files));
    }

    private RootApplicationAssembly.FreshSessionConfiguration configuration() {
        var paths = new RootStartupConfiguration.CheckpointPaths(root.resolve("driver"),root.resolve("evidence"),
                root.resolve("attachments"),"configured-lineage",root.resolve("configured.ck3"));
        return new RootApplicationAssembly.FreshSessionConfiguration("fixture",
                new NativeReadiness.Policy(false,false,Optional.empty(),Duration.ofMillis(25),true),
                Duration.ofSeconds(30),paths,new OriginalWindowReducer.Policy(10958),NOW.plusSeconds(30));
    }

    private NativeLaunchPlan launch(Path profile) throws IOException {
        var inputs = new NativeLaunchEvidence.Inputs(configured("env.json"),configured("build.json"),configured("register.json"));
        var review = new LaunchSourceBinding.Review("fixture-machine",NOW,configured("game.exe"),configured("bridge.dll"),
                configured("injector.exe"),inputs,root,List.of(configured("runtime.jar")));
        var steam = new SteamOfflineProbe.Plan("fixture-machine",configured("steam.exe"),NOW.plusSeconds(60));
        return new NativeLaunchPlanCodec.Configuration("fixture-launch","fixture-session",review,profile,root.resolve("state"),
                root.resolve("runtime-evidence"),"\\\\.\\pipe\\checkpoint-paths","bridge",
                "ck3-1.20.0.4-msvc-x64",new NativeLaunchPlan.NewGame(),false,NativeLaunchPlan.WindowPolicy.MINIMIZED_NO_ACTIVATE,
                Map.of(),128L<<20,32L<<20,NOW.plusSeconds(60),Duration.ofSeconds(1),Duration.ofSeconds(2),
                steam,NativeLaunchPlan.PreparedProfile.vanilla(),128).accept();
    }

    private ControlBuild.FileRef configured(String name) {
        return new ControlBuild.FileRef(root.resolve(name).toString(),1,"a".repeat(64));
    }

    private CheckpointPair pair(Path save, String lineage, int pid) throws IOException {
        var game = new GameGeneration(pid,new PythonOnlyUInt64(BigInteger.valueOf(pid)));
        var frame = new JointBudgetSelector.ProposalFrame(
                new JointBudgetSelector.Frame(BigInteger.ONE,BigInteger.ONE,BigInteger.valueOf(100)),
                "snapshot",BigInteger.ONE,"episode");
        var observed = new ObservationIdentity("fixture-machine",game,frame,1);
        var ack = write(root.resolve("ack-" + pid),"ack-" + pid);
        return new CheckpointPair(witness(write(save,"save-" + pid)),
                witness(write(root.resolve("driver-" + pid),"driver-" + pid)),observed,lineage,1,
                "save-" + pid,ack,NOW);
    }

    private CheckpointPair.FileWitness witness(ExactRef ref) throws IOException {
        var actual = files.observe(Path.of(ref.path())).orElseThrow();
        assertEquals(ref,actual.reference());
        return actual;
    }

    private static ExactRef write(Path path, String content) throws IOException {
        Files.writeString(path,content);
        byte[] actual = Files.readAllBytes(path);
        return new ExactRef(path.toString(),actual.length,ActionCodec.sha256(actual));
    }
}
