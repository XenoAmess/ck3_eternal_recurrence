package org.xar.ck3.control.build;

import static org.junit.jupiter.api.Assertions.*;
import com.sun.jna.Native;
import com.sun.jna.platform.win32.Kernel32;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.TreeMap;
import java.util.UUID;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

/** Real original software pipes and original Job resources. Never Native/Game qualification. */
final class NativeServerLocatorTest {
    @TempDir Path temporary;
    private static ControlBuild.FileRef classRef(Class<?> type) throws Exception {
        Path root = Path.of(type.getProtectionDomain().getCodeSource().getLocation().toURI());
        return ControlBuild.FileRef.measure(Files.isDirectory(root)
                ? root.resolve(type.getName().replace('.', '/') + ".class") : root);
    }
    private final class Fixture implements AutoCloseable {
        final Path root, source, dll;
        final String name, auxiliary;
        final Instant deadline;
        final WindowsJobProcess.CommandSpec serverCommand;
        final WindowsJobProcess.OwnedStdio server;
        WindowsJobProcess target;
        WindowsPreloadCustody.Lease lease;
        Fixture(String mode) throws Exception {
            root = Files.createDirectory(temporary.resolve(UUID.randomUUID().toString()));
            source = root.resolve("source.txt"); Files.writeString(source, "pinned");
            dll = root.resolve("software-held.dll"); Files.writeString(dll, "software-file");
            name = "\\\\.\\pipe\\xar-java-locator-" + UUID.randomUUID();
            auxiliary = name + "-aux"; deadline = Instant.now().plusSeconds(10);
            serverCommand = command("server", mode, name, auxiliary);
            var refs = List.of(classRef(PreloadEndpointSoftwarePeer.class), classRef(NativeServerLocator.class),
                    classRef(WindowsPreloadCustody.class), classRef(WindowsPreloadCustody.Api.class),
                    classRef(WindowsJobProcess.JobKernel32.class), classRef(Native.class), classRef(Kernel32.class),
                    ControlBuild.FileRef.measure(source));
            server = WindowsJobProcess.startOwnedStdio(new WindowsJobProcess.OwnedStdioSpec(
                    serverCommand, WindowsJobProcess.ConsoleMode.NO_WINDOW,
                    ControlBuild.FileRef.measure(serverCommand.executable()), refs, deadline,
                    8192, 8192, 32768, () -> { }));
        }
        WindowsJobProcess.CommandSpec command(String directory, String mode, String... operands) throws Exception {
            Path cwd = Files.createDirectory(root.resolve(directory));
            var arguments = new ArrayList<>(List.of("-Xms8m", "-Xmx16m", "-XX:+UseSerialGC",
                    "-XX:ActiveProcessorCount=1", "-XX:MaxMetaspaceSize=32m", "-XX:ReservedCodeCacheSize=16m",
                    "-XX:MaxDirectMemorySize=8m", "-Xss256k", "-Dfile.encoding=UTF-8",
                    "-Djava.io.tmpdir=" + System.getProperty("java.io.tmpdir"),
                    "-Djna.tmpdir=" + System.getProperty("jna.tmpdir", System.getProperty("java.io.tmpdir")),
                    "-cp", System.getProperty("java.class.path"), PreloadEndpointSoftwarePeer.class.getName(), mode));
            arguments.addAll(List.of(operands));
            var environment = new TreeMap<String, String>(String.CASE_INSENSITIVE_ORDER);
            environment.putAll(System.getenv()); environment.remove("JAVA_TOOL_OPTIONS");
            return new WindowsJobProcess.CommandSpec(Path.of(System.getProperty("java.home"), "bin/java.exe"),
                    arguments, cwd, environment, cwd.resolve("stdout.raw"), cwd.resolve("stderr.raw"), 128L << 20);
        }
        NativeServerLocator.Received receive() throws Exception {
            return NativeServerLocator.receive(server, name, deadline);
        }
        void startTarget(NativeServerLocator.Received received, boolean invalidResource) throws Exception {
            var command = command("target", "client-locator", name);
            target = WindowsJobProcess.start(command, WindowsJobProcess.ConsoleMode.NO_WINDOW, suspended -> {
                var acquired = WindowsPreloadCustody.prepare(suspended, new WindowsPreloadCustody.DllRef(
                        ControlBuild.FileRef.measure(dll), deadline, () -> { }));
                lease = acquired;
                try {
                    if (invalidResource) {
                        IOException failure = assertThrows(IOException.class, () -> received.retain(acquired));
                        assertFalse(failure instanceof WindowsPreloadCustody.PipeNotConnected);
                        assertThrows(IOException.class, () -> received.retain(acquired));
                    } else {
                        var waiting = assertThrows(WindowsPreloadCustody.PipeNotConnected.class,
                                () -> received.retain(acquired));
                        assertTrue(waiting.win32Error() == 233 || waiting.win32Error() == 1168);
                    }
                    return acquired;
                } catch (RuntimeException | AssertionError failure) {
                    try { acquired.close(); } catch (IOException cleanup) { failure.addSuppressed(cleanup); }
                    throw new IOException("software locator pre-resume failure", failure);
                }
            });
            assertEquals("SOFTWARE_CONNECTED\n",
                    new String(server.readLine(deadline).rawBytes(), StandardCharsets.US_ASCII));
        }
        @Override public void close() throws IOException {
            try { closeActual(); }
            catch (InterruptedException interrupted) {
                Thread.currentThread().interrupt(); throw new IOException("software resource cleanup interrupted", interrupted);
            }
        }
        private void closeActual() throws IOException, InterruptedException {
            try {
                server.closeInput();
                var actual = server.awaitExit(null).commandResult();
                assertEquals(0, actual.accounting().activeProcesses(), actual.toString());
                if (!actual.passed()) assertNotNull(actual.stopReason(), actual.toString());
            } finally {
                try { server.close(); }
                finally {
                    if (target != null) try {
                        var actual = target.await(Duration.ofSeconds(6), Instant.now().plusSeconds(7), () -> { });
                        assertTrue(actual.passed(), actual.toString());
                        assertEquals(0, actual.accounting().activeProcesses());
                    } finally { target.close(); }
                }
            }
        }
    }

    @Test void actualNoticeBindsRawArrivalAndOriginalOwnerTargetEndpoint() throws Exception {
        try (var fixture = new Fixture("notice-good")) {
            var received = fixture.receive();
            assertEquals(fixture.server.identity(), received.ownerIdentity());
            assertEquals(fixture.server.sessionNonce(), received.sessionNonce());
            assertEquals(1, received.sequence());
            assertEquals(fixture.name, received.pipeName());
            assertTrue(received.handleDecimal().matches("[1-9][0-9]{0,19}"));
            assertArrayEquals(received.arrival().rawBytes(), received.rawBytes());
            assertArrayEquals(received.rawBytes(), Files.readAllBytes(fixture.serverCommand.stdout()));
            var json = ControlBuild.strictMapper().readTree(received.rawBytes());
            assertEquals(received.handleDecimal(), json.path("params").path("handle_decimal").textValue());
            fixture.startTarget(received, false);
            var endpoint = received.retain(fixture.lease);
            assertSame(endpoint, received.retain(fixture.lease));
            endpoint.verify();
            assertEquals(fixture.server.identity(), endpoint.ownerIdentity());
            assertEquals(fixture.target.identity(), endpoint.targetIdentity());
            assertEquals(fixture.name, endpoint.pipeName());
        }
    }

    @Test void actualMalformedFramesRejectSchemaFieldsTypesAndDecimalDrift() throws Exception {
        for (String mode : List.of("notice-number", "notice-bool", "notice-float", "notice-zero",
                "notice-leading-zero", "notice-overflow", "notice-extra", "notice-missing",
                "notice-schema", "notice-rpc-id", "notice-duplicate")) {
            try (var fixture = new Fixture(mode)) {
                assertThrows(IOException.class, fixture::receive, mode);
                assertTrue(Files.size(fixture.serverCommand.stdout()) > 0, mode);
                IOException replay = assertThrows(IOException.class, fixture::receive, mode);
                assertTrue(replay.getMessage().contains("already attempted"), replay.toString());
            }
        }
    }

    @Test void actualWrongPipeNotificationRejectsBeforeAnyTargetExists() throws Exception {
        try (var fixture = new Fixture("notice-wrong-pipe")) {
            assertNull(fixture.target);
            assertThrows(IOException.class, fixture::receive);
            assertThrows(IOException.class, fixture::receive);
            assertNull(fixture.target);
        }
    }

    @Test void locatorStringCannotAuthorizeInvalidActualResourceAndUnknownCannotRetry() throws Exception {
        try (var fixture = new Fixture("notice-bad-resource")) {
            var received = fixture.receive();
            assertEquals("1", received.handleDecimal());
            fixture.startTarget(received, true);
            assertThrows(IOException.class, () -> received.retain(fixture.lease));
        }
    }

    @Test void receivedLocatorCannotTransferToAnotherActualHeldLease() throws Exception {
        try (var fixture = new Fixture("notice-good")) {
            var received = fixture.receive(); fixture.startTarget(received, false);
            received.retain(fixture.lease);
            var otherCommand = fixture.command("other-target", "idle");
            try (var other = WindowsJobProcess.start(otherCommand, WindowsJobProcess.ConsoleMode.NO_WINDOW, suspended -> {
                var otherLease = WindowsPreloadCustody.prepare(suspended, new WindowsPreloadCustody.DllRef(
                        ControlBuild.FileRef.measure(fixture.dll), fixture.deadline, () -> { }));
                try {
                    IOException failure = assertThrows(IOException.class, () -> received.retain(otherLease));
                    assertTrue(failure.getMessage().contains("same lease"), failure.toString());
                    assertThrows(IOException.class, () -> received.retain(fixture.lease));
                    return otherLease;
                } catch (RuntimeException | AssertionError failure) {
                    try { otherLease.close(); } catch (IOException cleanup) { failure.addSuppressed(cleanup); }
                    throw new IOException("software same-lease assertion", failure);
                }
            })) {
                assertTrue(other.await(Duration.ofSeconds(4), fixture.deadline, () -> { }).passed());
            }
        }
    }

    @Test void sourceDriftAndActualReadTimeoutRevokeReceiptWithoutReplay() throws Exception {
        try (var fixture = new Fixture("notice-good")) {
            var received = fixture.receive(); fixture.startTarget(received, false);
            received.retain(fixture.lease);
            Files.writeString(fixture.source, "drift!");
            assertThrows(IOException.class, () -> received.retain(fixture.lease));
            assertThrows(IOException.class, () -> received.retain(fixture.lease));
            assertThrows(IOException.class, fixture.server::verifyActualIdentityAndSources);
        }
        try (var fixture = new Fixture("notice-delay")) {
            IOException timeout = assertThrows(IOException.class, () -> NativeServerLocator.receive(
                    fixture.server, fixture.name, Instant.now().plusMillis(500)));
            var actual = fixture.server.awaitExit(null).commandResult();
            assertEquals(124, actual.exitCode(), actual.toString());
            assertEquals(0, actual.accounting().activeProcesses(), actual.toString());
            assertFalse(actual.passed(), actual.toString());
            assertNotNull(actual.stopReason(), actual.toString());
            String latched = "IOException: " + timeout.getMessage();
            assertTrue(actual.stopReason().equals("periodic_guard: " + latched)
                    || actual.stopReason().equals("owned_stdio_unknown: " + latched), actual.toString());
            assertThrows(IOException.class, fixture.server::verifyLiveOwner);
            assertFalse(Files.readString(fixture.serverCommand.stderr()).contains("SOFTWARE_NOTICE_EMITTED"));
            assertEquals(0, Files.size(fixture.serverCommand.stdout()));
            IOException replay = assertThrows(IOException.class, fixture::receive);
            assertTrue(replay.getMessage().contains("already attempted"), replay.toString());
            assertEquals(0, Files.size(fixture.serverCommand.stdout()));
        }
    }
}
