package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

/** Real retained Windows resources with ordinary Java loader; no Game, injector or Native admission. */
final class WindowsPreloadCustodyTest {
    @TempDir Path temporary;
    private Path javaExe() { return Path.of(System.getProperty("java.home"), "bin/java.exe"); }
    private WindowsJobProcess.CommandSpec command(String name) throws Exception {
        Path root = Files.createDirectory(temporary.resolve(name));
        Path classes = Path.of(PreloadSoftwarePeer.class.getProtectionDomain().getCodeSource().getLocation().toURI());
        return new WindowsJobProcess.CommandSpec(javaExe(), List.of("-Xms8m", "-Xmx16m", "-XX:+UseSerialGC",
                "-XX:ActiveProcessorCount=1", "-XX:MaxMetaspaceSize=24m", "-XX:ReservedCodeCacheSize=16m",
                "-cp", classes.toString(), PreloadSoftwarePeer.class.getName()), root, Map.of(),
                root.resolve("stdout"), root.resolve("stderr"), 128L << 20);
    }
    private WindowsPreloadCustody.DllRef reference(Path path) throws Exception {
        return new WindowsPreloadCustody.DllRef(ControlBuild.FileRef.measure(path), Instant.now().plusSeconds(12), () -> { });
    }
    @Test void originalSuspendedJavaChildNaturallyLoadsSameHeldJvmFile() throws Exception {
        var command = command("natural");
        var dll = reference(Path.of(System.getProperty("java.home"), "bin/server/jvm.dll"));
        var retained = new AtomicReference<WindowsPreloadCustody.Lease>();
        var token = new AtomicReference<WindowsJobProcess.SuspendedTarget>();
        var suspendedStdoutBytes = new AtomicReference<Long>();

        try (var owner = WindowsJobProcess.start(command, WindowsJobProcess.ConsoleMode.NO_WINDOW, target -> {
            token.set(target);
            suspendedStdoutBytes.set(Files.size(command.stdout()));
            var lease = WindowsPreloadCustody.prepare(target, dll);
            retained.set(lease);
            return lease;
        })) {
            assertEquals(0L, suspendedStdoutBytes.get().longValue());
            assertThrows(IOException.class, () -> token.get().identity());
            assertEquals(owner.identity(), retained.get().targetIdentity());
            assertTrue(retained.get().preloadImages().isEmpty());
            Instant until = Instant.now().plusSeconds(4);
            while (Files.size(command.stdout()) == 0 && Instant.now().isBefore(until)) Thread.sleep(10);
            assertEquals("SOFTWARE_READY\n", Files.readString(command.stdout()));

            var loaded = retained.get().observeLoaded();
            assertEquals(owner.identity(), loaded.targetIdentity());
            assertEquals(loaded.dll().nativeFile().identityKey(), loaded.matchingDll().heldFile().orElseThrow().identityKey());
            // Current enumeration returns only the requested DLL match.
            assertEquals(1, loaded.modules().size());
            assertEquals(loaded.dll().fullDosPath(), loaded.modules().getFirst().fullDosPath());

            var result = owner.await(Duration.ofSeconds(4), dll.deadline(), () -> { });
            assertTrue(result.passed(), result.toString());
            assertEquals(0, result.accounting().activeProcesses());
        }
        assertThrows(IOException.class, () -> retained.get().verify());
    }
    @Test void continuouslyHeldReadLeaseBlocksMutationAndRenameUntilOwnerClose() throws Exception {
        Path file = temporary.resolve("software-only.dll"); Files.writeString(file, "software-file");
        var command = command("sharing"); var dll = reference(file); var retained = new AtomicReference<WindowsPreloadCustody.Lease>();
        try (var owner = WindowsJobProcess.start(command, WindowsJobProcess.ConsoleMode.NO_WINDOW, target -> {
            var lease = WindowsPreloadCustody.prepare(target, dll); retained.set(lease); return lease;
        })) {
            assertThrows(IOException.class, () -> Files.writeString(file, "drift"));
            assertThrows(IOException.class, () -> Files.move(file, temporary.resolve("moved.dll")));
            retained.get().verify();
            assertTrue(owner.await(Duration.ofSeconds(4), dll.deadline(), () -> { }).passed());
            assertThrows(IOException.class, () -> Files.writeString(file, "after-exit-still-held"));
        }
        Files.writeString(file, "after-close");
        assertThrows(IOException.class, () -> retained.get().verify());
    }
    @Test void descriptorOnlyHashMetadataDoesNotBlockPreparation() throws Exception {
        Path file = temporary.resolve("wrong.dll");
        Files.writeString(file, "wrong-hash");
        var good = ControlBuild.FileRef.measure(file);
        var bad = new WindowsPreloadCustody.DllRef(new ControlBuild.FileRef(good.path(), good.bytes(), "0".repeat(64)),
                Instant.now().plusSeconds(5), () -> { });
        var command = command("bad-hash");
        var retained = new AtomicReference<WindowsPreloadCustody.Lease>();

        try (var owner = WindowsJobProcess.start(command, WindowsJobProcess.ConsoleMode.NO_WINDOW, target -> {
            var lease = WindowsPreloadCustody.prepare(target, bad);
            retained.set(lease);
            return lease;
        })) {
            assertNotNull(retained.get());
            var readback = retained.get().dllReadback();
            assertEquals("", readback.sha256());
            assertEquals(bad.file().path(), readback.originalRef().path());

            Instant until = Instant.now().plusSeconds(4);
            while (Files.size(command.stdout()) == 0 && Instant.now().isBefore(until)) Thread.sleep(10);
            assertEquals("SOFTWARE_READY\n", Files.readString(command.stdout()));

            var result = owner.await(Duration.ofSeconds(4), bad.deadline(), () -> { });
            assertTrue(result.passed());
            assertEquals(0, result.accounting().activeProcesses());
        }
        assertThrows(IOException.class, () -> retained.get().verify());
    }
    @Test void alreadyMappedImageDoesNotBlockPreparation() throws Exception {
        var command = command("already-mapped");
        var reference = reference(javaExe());
        var retained = new AtomicReference<WindowsPreloadCustody.Lease>();

        try (var owner = WindowsJobProcess.start(command, WindowsJobProcess.ConsoleMode.NO_WINDOW, target -> {
            var lease = WindowsPreloadCustody.prepare(target, reference);
            retained.set(lease);
            return lease;
        })) {
            assertNotNull(retained.get());
            var readback = retained.get().dllReadback();
            assertEquals(reference.file().path(), readback.originalRef().path());

            Instant until = Instant.now().plusSeconds(4);
            while (Files.size(command.stdout()) == 0 && Instant.now().isBefore(until)) Thread.sleep(10);
            assertEquals("SOFTWARE_READY\n", Files.readString(command.stdout()));

            var result = owner.await(Duration.ofSeconds(4), reference.deadline(), () -> { });
            assertTrue(result.passed());
            assertEquals(0, result.accounting().activeProcesses());
        }
        assertThrows(IOException.class, () -> retained.get().verify());
    }
}
