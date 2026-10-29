package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

/** Tuple-only fixtures never run Python or qualify resources, producer deployment, SDK imports or Game. */
final class ControlCiCanonicalThirtyTest {
    @TempDir Path temporary;
    private static final long MIB = 1L << 20;
    private record Fixture(CiBootstrap.Plan resources, ControlBuild.CapacityRelease release,
            ControlBuild.FileRef releaseRef, ControlBuild.FileRef python, ControlBuild.FileRef git,
            ControlBuild.FileRef workflow, Path repository, Path output, Path dependencies) {
        CanonicalColdWarmStage.Config config(CanonicalColdWarmStage.BootstrapMode mode,
                ControlBuild.FileRef card, Path work) {
            return new CanonicalColdWarmStage.Config(CanonicalColdWarmStage.SCHEMA, resources.machineId(),
                    resources.reviewAtUtc(), repository.toString(), work.toString(), python, git, workflow, workflow,
                    List.of(workflow), List.of(dependencies.toString()), List.of(python), card, mode,
                    mode == CanonicalColdWarmStage.BootstrapMode.NONE ? null : workflow, 128 * MIB, 900);
        }
        CanonicalColdWarmStage.Config config() {
            return config(CanonicalColdWarmStage.BootstrapMode.NONE, releaseRef, output);
        }
    }
    private Fixture fixture() throws IOException {
        Path repository = Files.createDirectories(temporary.resolve("repository/.github/workflows")).getParent().getParent();
        Path workflow = repository.resolve(".github/workflows/static-ci.yml");
        Files.writeString(workflow, "tuple fixture only; not an executable workflow");
        Path work = Files.createDirectories(temporary.resolve("work"));
        Path artifacts = Files.createDirectory(work.resolve("artifacts"));
        Path dependencies = Files.createDirectory(temporary.resolve("dependencies"));
        Path python = Files.writeString(dependencies.resolve("python.exe"), "not an interpreter");
        Path git = Files.writeString(dependencies.resolve("git.exe"), "not git");
        Path policy = Files.writeString(temporary.resolve("policy.json"), "not a resource policy");
        Path card = Files.writeString(temporary.resolve("release.json"), "not an execution release");
        var pythonRef = ControlBuild.FileRef.measure(python); var workflowRef = ControlBuild.FileRef.measure(workflow);
        var policyRef = ControlBuild.FileRef.measure(policy);
        var policyPin = new CiBootstrap.FilePin(policyRef.path(), policyRef.bytes(), policyRef.sha256());
        String observed = Instant.now().toString(), review = Instant.now().plusSeconds(3600).toString();
        Map<String,Long> parts = Map.of("m2",4096L,"build",4096L,"tools",4096L,"scratch",4096L,"metadata_logs",4096L,"artifacts",1L << 20);
        var volumes = Map.of(temporary.getRoot().toString(), new CiBootstrap.VolumeBudget(1,1,1,1,1,1,1,1,1));
        var resources = new CiBootstrap.Plan(CiBootstrap.PLAN_SCHEMA, "tuple-fixture-machine", observed, review,
                repository.toString(), work.toString(), temporary.toString(), "mvn", python.toString(), "/root/sdk",
                policyPin, volumes, Map.of(), parts, List.of(policyPin), List.of(policyPin), false, false);
        var release = new ControlBuild.CapacityRelease("xar.java-control.capacity-release/v1", resources.machineId(),
                observed, review, "RELEASED", resources.ownerTask(), policyRef, List.of(work.toString(), repository.toString()),
                work.resolve("scratch").toString(), parts, volumes, Map.of(), 256 * MIB, 32 * MIB);
        return new Fixture(resources, release, ControlBuild.FileRef.measure(card), pythonRef,
                ControlBuild.FileRef.measure(git), workflowRef, repository, artifacts.resolve("canonical30"), dependencies);
    }
    @Test void cliRejectsMissingOrWrongRefGroupsBeforeAnyIo() {
        assertThrows(IllegalArgumentException.class, () -> ControlCi.main(new String[]{"--canonical-thirty"}));
        assertThrows(IllegalArgumentException.class, () -> ControlCi.main(new String[]{"--canonical-thirty","x","1","a",
                "--wrong","x","1","a","--capacity-release","x","1","a"}));
    }
    @Test void oneExactTupleCannotChangeCardOutputOrChildMemory() throws Exception {
        var f = fixture();
        assertDoesNotThrow(() -> ControlCi.requireCanonicalThirtyBindings(f.config(), f.resources(), f.release(), f.releaseRef()));
        assertFalse(Files.exists(f.output()));
        assertThrows(IOException.class, () -> ControlCi.requireCanonicalThirtyBindings(
                f.config(CanonicalColdWarmStage.BootstrapMode.NONE, f.workflow(), f.output()), f.resources(), f.release(), f.releaseRef()));
        Path foreignArtifacts = Files.createDirectory(temporary.resolve("foreign-artifacts"));
        var foreign = f.config(CanonicalColdWarmStage.BootstrapMode.NONE, f.releaseRef(), foreignArtifacts.resolve("canonical30"));
        assertEquals(foreignArtifacts.toRealPath(), Path.of(foreign.workRoot()).getParent().toRealPath());
        assertNotEquals(Path.of(f.resources().workRoot()).resolve("artifacts").toRealPath(), foreignArtifacts.toRealPath());
        IOException rejectedOutput = assertThrows(IOException.class, () -> ControlCi.requireCanonicalThirtyBindings(
                foreign, f.resources(), f.release(), f.releaseRef()));
        assertEquals("Canonical-only scope requires NONE and the same exact machine, clock, inputs and admitted resources", rejectedOutput.getMessage());
        assertFalse(Files.exists(Path.of(foreign.workRoot())));
        var r = f.release();
        var smaller = new ControlBuild.CapacityRelease(r.schema(),r.machineId(),r.observedAtUtc(),r.reviewAtUtc(),r.status(),
                r.ownerTask(),r.policyRef(),r.approvedOutputRoots(),r.temporaryRoot(),r.parts(),r.volumes(),r.quotaOverrides(),64 * MIB,32 * MIB);
        assertThrows(IOException.class, () -> ControlCi.requireCanonicalThirtyBindings(f.config(), f.resources(), smaller, f.releaseRef()));
        assertFalse(Files.exists(f.output()));
    }
    @Test void standaloneCannotMasqueradeAsRootSoftwareFixture() throws Exception {
        var f = fixture();
        assertThrows(IOException.class, () -> ControlCi.requireCanonicalThirtyBindings(
                f.config(CanonicalColdWarmStage.BootstrapMode.ROOT_SOFTWARE_FIXTURE, f.releaseRef(), f.output()),
                f.resources(), f.release(), f.releaseRef()));
        assertFalse(Files.exists(f.output()));
    }
}
