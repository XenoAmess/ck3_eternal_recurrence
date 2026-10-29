package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.lang.reflect.Modifier;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

/** Real existing owned Java software peer, not a forged legacy Python proof. */
final class WindowsOriginalRetirementTest {
    @TempDir Path temporary;
    private WindowsJobProcess.OwnedStdioSpec spec(String mode, AtomicInteger guardCalls,
            List<ControlBuild.FileRef> extra) throws Exception {
        Path classes = Path.of(OwnedStdioSoftwarePeer.class.getProtectionDomain().getCodeSource().getLocation().toURI());
        Path run = Files.createDirectory(temporary.resolve("run-" + java.util.UUID.randomUUID()));
        Path executable = Path.of(System.getProperty("java.home"), "bin", "java.exe");
        var arguments = List.of("-Xms8m", "-Xmx16m", "-XX:+UseSerialGC", "-XX:ActiveProcessorCount=1",
                "-XX:MaxMetaspaceSize=24m", "-XX:ReservedCodeCacheSize=16m", "-XX:MaxDirectMemorySize=8m", "-Xss256k",
                "-Dfile.encoding=UTF-8", "-Djava.io.tmpdir=" + System.getProperty("java.io.tmpdir"),
                "-Djna.tmpdir=" + System.getProperty("jna.tmpdir", System.getProperty("java.io.tmpdir")),
                "-cp", classes.toString(), OwnedStdioSoftwarePeer.class.getName(), mode);
        var environment = new java.util.TreeMap<String, String>(String.CASE_INSENSITIVE_ORDER);
        environment.putAll(System.getenv()); environment.remove("JAVA_TOOL_OPTIONS");
        var command = new WindowsJobProcess.CommandSpec(executable, arguments, run, environment,
                run.resolve("stdout.raw"), run.resolve("stderr.raw"), 128L << 20);
        var sources = new ArrayList<ControlBuild.FileRef>();
        sources.add(ControlBuild.FileRef.measure(classes.resolve("org/xar/ck3/control/build/OwnedStdioSoftwarePeer.class")));
        sources.addAll(extra);
        return new WindowsJobProcess.OwnedStdioSpec(command, WindowsJobProcess.ConsoleMode.NO_WINDOW,
                ControlBuild.FileRef.measure(executable), sources, Instant.now().plusSeconds(15), 4096, 4096, 4096,
                guardCalls::incrementAndGet);
    }
    private static WindowsJobProcess.RetiredCustody retired(WindowsJobProcess.OwnedStdio original) throws Exception {
        long until = System.nanoTime() + 5_000_000_000L;
        IOException last = null;
        do {
            try { return original.observeRetiredCustody(); }
            catch (IOException waiting) { last = waiting; Thread.sleep(10); }
        } while (System.nanoTime() < until);
        throw new IOException("Actual software child retirement was not observed", last);
    }
    // Deliberate mid-scope closure exercises closed-state refusal; the enclosing resource scope still owns final cleanup.
    private static void closeRetiredToken(WindowsJobProcess.RetiredCustody actual) { actual.close(); }
    private static void closeOriginalOwner(WindowsJobProcess.OwnedStdio actual) { actual.close(); }
    @Test void liveRefusalDoesNotCallGuardFailOrTerminateAndTokenCloseLeavesOwnerUsable() throws Exception {
        var guard = new AtomicInteger();
        try (var original = WindowsJobProcess.startOwnedStdio(spec("echo", guard, List.of()))) {
            int before = guard.get();
            assertThrows(IOException.class, original::observeRetiredCustody);
            assertEquals(before, guard.get(), "retirement query must never invoke mutable launch guard");
            byte[] raw = new byte[]{111, 107, 10};
            original.write(raw, Instant.now().plusSeconds(3));
            assertArrayEquals(raw, original.readLine(Instant.now().plusSeconds(3)).rawBytes());
            original.closeInput(); // Explicit fixture lifecycle; the proof API itself never closes input.
            try (var token = retired(original)) {
                int afterLaunch = guard.get();
                var first = token.observation();
                assertEquals(original.identity(), first.identity());
                assertEquals(original.sessionNonce(), first.sessionNonce());
                assertEquals(0, first.exitCode()); assertEquals(0, first.accounting().activeProcesses());
                token.requireCurrent();
                assertEquals(afterLaunch, guard.get());
                var mapper = ControlBuild.strictMapper();
                assertEquals(first, mapper.readValue(mapper.writeValueAsBytes(first), WindowsJobProcess.RetirementObservation.class));
                assertEquals(first.observedAtUtc(), Instant.parse(first.observedAtUtc()).toString());
                var encoded = assertInstanceOf(com.fasterxml.jackson.databind.node.ObjectNode.class,
                        mapper.readTree(mapper.writeValueAsBytes(first)));
                for (String invalid : List.of("2026-10-24T03:00:00+00:00", "not-a-time", "2026-10-24T03:00:00.000Z")) {
                    var wrong = encoded.deepCopy();
                    wrong.put("observed_at_utc", invalid);
                    assertThrows(IOException.class, () -> mapper.readValue(mapper.writeValueAsBytes(wrong),
                            WindowsJobProcess.RetirementObservation.class));
                }
                var wrongType = encoded.deepCopy();
                wrongType.put("observed_at_utc", 9007199254740991L);
                assertThrows(IOException.class, () -> mapper.readValue(mapper.writeValueAsBytes(wrongType),
                        WindowsJobProcess.RetirementObservation.class));
                var missing = encoded.deepCopy();
                missing.remove("observed_at_utc");
                assertThrows(IOException.class, () -> mapper.readValue(mapper.writeValueAsBytes(missing),
                        WindowsJobProcess.RetirementObservation.class));
                var unknown = encoded.deepCopy();
                unknown.put("caller_retired", true);
                assertThrows(IOException.class, () -> mapper.readValue(mapper.writeValueAsBytes(unknown),
                        WindowsJobProcess.RetirementObservation.class));
                closeRetiredToken(token);
                assertThrows(IOException.class, token::requireCurrent);
            }
            try (var again = original.observeRetiredCustody()) {
                again.requireCurrent();
                var terminal = original.awaitExit(null);
                assertTrue(terminal.commandResult().passed(), terminal.toString());
                again.requireOriginal(original, terminal.commandResult());
            }
        }
    }
    @Test void nonzeroNaturalExitIsRetirementDataAndSourceDriftNeverMutatesTheLaunchGuard() throws Exception {
        Path source = temporary.resolve("witness.txt"); Files.writeString(source, "original");
        var guard = new AtomicInteger();
        try (var original = WindowsJobProcess.startOwnedStdio(spec("exit7-after-eof", guard,
                List.of(ControlBuild.FileRef.measure(source))));
                var read = WindowsJobProcess.retainReadOnlyProcess(original.identity().pid())) {
            assertEquals(258, read.waitZero()); // Acquire image/birth from the live blocked peer.
            assertEquals(original.identity(), read.identity());
            original.closeInput();
            try (var token = retired(original)) {
                assertEquals(7, token.observation().exitCode());
                int before = guard.get();
                Files.writeString(source, "different");
                assertThrows(IOException.class, token::requireCurrent);
                assertEquals(before, guard.get());
                assertEquals(0, read.waitZero()); assertEquals(7, read.exitCode());
                assertEquals(original.identity(), read.identity());
            }
        }
    }
    @Test void originalOwnerCloseInvalidatesOutstandingReadOnlyCustodyAndNoPublicMintExists() throws Exception {
        var guard = new AtomicInteger();
        try (var original = WindowsJobProcess.startOwnedStdio(spec("exit7", guard, List.of())); var token = retired(original)) {
            closeOriginalOwner(original);
            assertThrows(IOException.class, token::requireCurrent);
            closeRetiredToken(token);
            assertThrows(IOException.class, token::observation);
        }
        assertTrue(Modifier.isFinal(WindowsJobProcess.RetiredCustody.class.getModifiers()));
        assertEquals(0, WindowsJobProcess.RetiredCustody.class.getConstructors().length);
        for (var constructor : WindowsJobProcess.RetiredCustody.class.getDeclaredConstructors())
            assertTrue(Modifier.isPrivate(constructor.getModifiers()));
    }
}
