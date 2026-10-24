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
        var command = command("natural"); var dll = reference(Path.of(System.getProperty("java.home"), "bin/server/jvm.dll"));
        var retained = new AtomicReference<WindowsPreloadCustody.Lease>();
        var token = new AtomicReference<WindowsJobProcess.SuspendedTarget>();
        try (var owner = WindowsJobProcess.start(command, WindowsJobProcess.ConsoleMode.NO_WINDOW, target -> {
            token.set(target); assertEquals(0, Files.size(command.stdout()));
            var lease = WindowsPreloadCustody.prepare(target, dll); retained.set(lease);
            assertEquals(target.identity(), lease.targetIdentity()); assertFalse(lease.preloadImages().isEmpty());
            return lease;
        })) {
            assertThrows(IOException.class, () -> token.get().identity());
            Instant until = Instant.now().plusSeconds(4);
            while (Files.size(command.stdout()) == 0 && Instant.now().isBefore(until)) Thread.sleep(10);
            assertEquals("SOFTWARE_READY\n", Files.readString(command.stdout()));
            var loaded = retained.get().observeLoaded();
            assertEquals(owner.identity(), loaded.targetIdentity());
            assertEquals(loaded.dll().nativeFile().identityKey(), loaded.matchingDll().heldFile().orElseThrow().identityKey());
            assertTrue(loaded.modules().size() > 1);
            assertTrue(owner.await(Duration.ofSeconds(4), dll.deadline(), () -> { }).passed());
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
    @Test void badPinnedHashAbortsBeforeResumeAndReleasesActualFileLease() throws Exception {
        Path file = temporary.resolve("wrong.dll"); Files.writeString(file, "wrong-hash");
        var good = ControlBuild.FileRef.measure(file);
        var bad = new WindowsPreloadCustody.DllRef(new ControlBuild.FileRef(good.path(), good.bytes(), "0".repeat(64)),
                Instant.now().plusSeconds(5), () -> { });
        var command = command("bad-hash");
        assertThrows(IOException.class, () -> WindowsJobProcess.start(command, WindowsJobProcess.ConsoleMode.NO_WINDOW,
                target -> WindowsPreloadCustody.prepare(target, bad)));
        assertEquals(0, Files.size(command.stdout())); Files.writeString(file, "released");
    }
    @Test void completeInitialImageWalkRejectsAlreadyMappedTargetImage() throws Exception {
        var command = command("already-mapped"); var reference = reference(javaExe());
        assertThrows(IOException.class, () -> WindowsJobProcess.start(command, WindowsJobProcess.ConsoleMode.NO_WINDOW,
                target -> WindowsPreloadCustody.prepare(target, reference)));
        assertEquals(0, Files.size(command.stdout()));
    }
}
