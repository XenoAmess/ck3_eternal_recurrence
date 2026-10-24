package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotEquals;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.xar.ck3.control.build.ProjectionArtifactAuthority.*;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.nio.file.attribute.BasicFileAttributes;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

/** Real Windows filesystem/process/writer lifecycle; accepted build is a package-only fixture, not build or HTTP qualification. */
final class ProjectionArtifactOwnerNativeLifecycleTest {
    @TempDir Path temporary;

    @Test void windowsNullFileKeyStillPreparesPublishesOneLeaseAndClosesTheActualWriter() throws Exception {
        Fixture fixture = new Fixture(temporary);
        assertNull(Files.readAttributes(fixture.slot, BasicFileAttributes.class, LinkOption.NOFOLLOW_LINKS).fileKey(),
                "exercise the original Windows provider failure instead of replacing it with a fake key");
        ProjectionArtifactInputOwner.Prepared prepared = fixture.prepare();
        try {
            assertEquals(prepared.scope(), decodeScope(Files.readAllBytes(Path.of(prepared.scopeRef().path()))));
            prepared.publishLease(fixture.host);
            prepared.verifyCurrent(fixture.host); prepared.requireLive(fixture.host);
            assertEquals(prepared.scopeRef(), decodeLease(Files.readAllBytes(fixture.lease)).scopeRef());
            assertThrows(IOException.class, () -> prepared.publishLease(fixture.host));
        } finally { prepared.close(); }
        prepared.close();
        assertThrows(IOException.class, () -> prepared.requireLive(fixture.host));
        assertTrue(Files.isRegularFile(fixture.lease));
        assertTrue(Files.isRegularFile(Path.of(fixture.scope + ".writer.lock")));
    }

    @Test void replacingTheEmptySlotBeforeLeaseRejectsItsNewGenerationAndConsumesTheAttempt() throws Exception {
        Fixture fixture = new Fixture(temporary);
        try (var prepared = fixture.prepare()) {
            var original = SharedSourceFiles.nativeDirectory(fixture.slot);
            Files.move(fixture.slot, fixture.slot.resolveSibling("original-slot"));
            Files.createDirectory(fixture.slot);
            assertNotEquals(original, SharedSourceFiles.nativeDirectory(fixture.slot));
            IOException rejected = assertThrows(IOException.class, () -> prepared.publishLease(fixture.host));
            assertTrue(rejected.getMessage().contains("directory identity changed"));
            assertFalse(Files.exists(fixture.lease));
            assertTrue(assertThrows(IOException.class, () -> prepared.publishLease(fixture.host)).getMessage().contains("already attempted"));
        }
    }

    @Test void replacingAnAncestorAfterLeaseRejectsEvenWhenTheOriginalSlotInodeIsRestored() throws Exception {
        Fixture fixture = new Fixture(temporary);
        try (var prepared = fixture.prepare()) {
            prepared.publishLease(fixture.host);
            Path parent = fixture.slot.getParent(), oldParent = parent.resolveSibling("original-inputs");
            var originalSlot = SharedSourceFiles.nativeDirectory(fixture.slot);
            var originalParent = SharedSourceFiles.nativeDirectory(parent);
            Files.move(parent, oldParent); Files.createDirectory(parent);
            Files.move(oldParent.resolve(fixture.slot.getFileName()), fixture.slot);
            assertEquals(originalSlot, SharedSourceFiles.nativeDirectory(fixture.slot));
            assertNotEquals(originalParent, SharedSourceFiles.nativeDirectory(parent));
            IOException rejected = assertThrows(IOException.class, () -> prepared.verifyCurrent(fixture.host));
            assertTrue(rejected.getMessage().contains("directory identity changed"));
        }
    }

    @Test void replacingAPopulatedSlotRejectsDespitePreservedInputIdentityContentAndMtime() throws Exception {
        Fixture fixture = new Fixture(temporary);
        try (var prepared = fixture.prepare()) {
            prepared.publishLease(fixture.host);
            Path input = fixture.slot.resolve(INPUT_NAME);
            Files.writeString(input, "original finite fixture input", StandardOpenOption.CREATE_NEW);
            var inputBefore = SharedSourceFiles.observe(input);
            Path oldSlot = fixture.slot.resolveSibling("original-slot");
            Files.move(fixture.slot, oldSlot); Files.createDirectory(fixture.slot);
            Files.move(oldSlot.resolve(INPUT_NAME), input);
            var inputAfter = SharedSourceFiles.observe(input);
            assertEquals(inputBefore.nativeFile().identityKey(), inputAfter.nativeFile().identityKey());
            assertEquals(inputBefore.nativeFile().lastWriteFiletimeDecimal(), inputAfter.nativeFile().lastWriteFiletimeDecimal());
            assertEquals(inputBefore.source(), inputAfter.source());
            assertTrue(assertThrows(IOException.class, () -> prepared.verifyCurrent(fixture.host)).getMessage().contains("directory identity changed"));
        }
    }

    @Test void ordinaryInputPublicationKeepsDirectoryIdentityAndTheOriginalLeaseCurrent() throws Exception {
        Fixture fixture = new Fixture(temporary);
        try (var prepared = fixture.prepare()) {
            prepared.publishLease(fixture.host);
            var original = SharedSourceFiles.nativeDirectory(fixture.slot);
            Files.writeString(fixture.slot.resolve(INPUT_NAME), "original finite fixture input", StandardOpenOption.CREATE_NEW);
            assertEquals(original, SharedSourceFiles.nativeDirectory(fixture.slot));
            prepared.verifyCurrent(fixture.host); prepared.requireLive(fixture.host);
        }
    }

    @Test void anUnknownCreateNewLeasePublicationIsNeverRetriedOrReplaced() throws Exception {
        Fixture fixture = new Fixture(temporary);
        try (var prepared = fixture.prepare()) {
            byte[] unknown = "retained UNKNOWN publication".getBytes(java.nio.charset.StandardCharsets.UTF_8);
            Files.write(fixture.lease, unknown, StandardOpenOption.CREATE_NEW);
            assertThrows(IOException.class, () -> prepared.publishLease(fixture.host));
            assertTrue(assertThrows(IOException.class, () -> prepared.publishLease(fixture.host)).getMessage().contains("already attempted"));
            assertEquals(new String(unknown, java.nio.charset.StandardCharsets.UTF_8), Files.readString(fixture.lease));
        }
    }

    private static final class Fixture implements ProjectionArtifactInputOwner.Environment {
        private final Path slot, work, scope, lease;
        private final Instant deadline;
        private final String machine;
        private final WindowsJobProcess.ProcessIdentity host;
        private final ProjectionArtifactInputOwner.Config config;
        private final ControlBuild.BuildReceipt build;
        private final ControlBuild.FileRef buildRef, ownerRuntime;

        private Fixture(Path root) throws IOException {
            assertTrue(com.sun.jna.Platform.isWindows(), "real Windows native provider is required; unavailable is not skipped PASS");
            root = root.toRealPath();
            machine = WindowsJobProcess.currentMachineId();
            host = WindowsJobProcess.observeLiveProcess(ProcessHandle.current().pid()).identity();
            Instant now = Instant.now().minusSeconds(1); deadline = now.plusSeconds(300);
            work = Files.createDirectories(root.resolve("work")); Files.createDirectory(work.resolve("logs"));
            slot = Files.createDirectories(root.resolve("inputs/slot"));
            scope = work.resolve("logs/scope.json"); lease = work.resolve("logs/lease.json");
            Path source = Files.createDirectory(root.resolve("source")), compiled = Files.createDirectory(root.resolve("compiled"));
            Path deployment = Files.createDirectory(root.resolve("deployment"));
            List<ControlBuild.FileRef> sources = new ArrayList<>(), compiledSources = new ArrayList<>();
            for (String name : List.of("ProjectionArtifactAuthority.java", "ProjectionArtifactInputOwner.java", "MapAdmissionServiceOwner.java")) {
                String relative = "build-tools/src/main/java/org/xar/ck3/control/build/" + name;
                sources.add(write(source.resolve(relative), "fixture source " + name));
                compiledSources.add(write(compiled.resolve(relative), "fixture source " + name));
            }
            ControlBuild.FileRef producer = write(deployment.resolve("military.jar"), "fixture producer artifact");
            ownerRuntime = write(root.resolve("owner.jar"), "fixture accepted Owner runtime");
            ControlBuild.FileRef policy = write(root.resolve("policy.json"), """
                    {"schema":"xar-storage-retention-policy-v1","policy_version":"1.0.0","capacity":{
                    "safety_floor_bytes":1,"safety_ceiling_bytes":1,"safety_volume_fraction":0.00000001,
                    "default_project_quota_ceiling_bytes":1000000000000,"default_project_quota_volume_fraction":0.99,
                    "quota_override_max_hours":168}}
                    """);
            var store = Files.getFileStore(slot);
            var volume = CiBootstrap.calculate(CiBootstrap.readPolicy(Files.readAllBytes(Path.of(policy.path()))),
                    store.getTotalSpace(), store.getUsableSpace(), 65536, 0, 1, 65536);
            var release = new ControlBuild.CapacityRelease("xar.java-control.capacity-release/v1", machine, now.toString(), deadline.toString(),
                    "RELEASED", "owner-native-fixture", policy, List.of(slot.toString()), root.toString(), Map.of("projection_input", 65536L),
                    Map.of(slot.getRoot().toString(), volume), Map.of(), ProjectionArtifactInputOwner.JOB_MEMORY_BYTES, 256L << 20);
            ControlBuild.FileRef capacity = write(root.resolve("capacity.json"), ControlBuild.strictMapper().writeValueAsBytes(release));
            build = new ControlBuild.BuildReceipt(ControlBuild.SCHEMA, machine, now.toString(), "PASS", source.toString(), compiled.toString(), deployment.toString(),
                    new ControlBuild.SourcePostcheck(ControlBuild.SourceState.MATCH, null), new ControlBuild.SourcePostcheck(ControlBuild.SourceState.MATCH, null),
                    ControlBuild.TargetKind.SERVICE_FAST_JAR, ControlBuild.SourceLimitProfile.EXISTING_MIGRATION_20261022, sources, compiledSources,
                    List.of(producer), List.of(ownerRuntime), capacity, null, ControlBuild.FileRef.measure(Path.of(host.executable())), null, null, Map.of(), null);
            buildRef = write(root.resolve("build.json"), ControlBuild.strictMapper().writeValueAsBytes(build));
            var grant = new ProjectionArtifactInputOwner.RootGrant(ProjectionArtifactInputOwner.GRANT_SCHEMA, machine, "owner-native-fixture", now.toString(), deadline.toString(),
                    slot.toString(), scope.toString(), lease.toString(), work.resolve("logs/source.json").toString(), work.resolve("logs/runtime.json").toString(),
                    65536, ProjectionArtifactInputOwner.JOB_MEMORY_BYTES, producer, policy, capacity);
            config = new ProjectionArtifactInputOwner.Config(write(root.resolve("grant.json"), ControlBuild.strictMapper().writeValueAsBytes(grant)), "native-fixture-scope", "native-fixture-owner");
        }
        private ProjectionArtifactInputOwner.Prepared prepare() throws IOException {
            return ProjectionArtifactInputOwner.prepare(config, build, buildRef, work, deadline, machine, List.of(), this);
        }
        @Override public ControlBuild.BuildReceipt acceptedBuild(Path receipt) throws IOException {
            buildRef.verify(); assertEquals(Path.of(buildRef.path()), receipt);
            return ControlBuild.strictMapper().readValue(Files.readAllBytes(receipt), ControlBuild.BuildReceipt.class);
        }
        @Override public List<ControlBuild.FileRef> runtimeClosure() throws IOException { ownerRuntime.verify(); return List.of(ownerRuntime); }
        @Override public ControlBuild.FileRef ownerCodeSource() throws IOException { ownerRuntime.verify(); return ownerRuntime; }
        private static ControlBuild.FileRef write(Path path, String text) throws IOException {
            return write(path, text.getBytes(java.nio.charset.StandardCharsets.UTF_8));
        }
        private static ControlBuild.FileRef write(Path path, byte[] raw) throws IOException {
            Files.createDirectories(path.getParent()); Files.write(path, raw, StandardOpenOption.CREATE_NEW); return ControlBuild.FileRef.measure(path);
        }
    }
}
