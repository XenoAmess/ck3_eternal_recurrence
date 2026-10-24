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
import java.util.UUID;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.AfterAll;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.MethodOrderer;
import org.junit.jupiter.api.Order;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestInstance;
import org.junit.jupiter.api.TestMethodOrder;
import org.junit.jupiter.api.io.TempDir;

/** Actual retained pipe resources with Java peers only. Endpoint success grants no Native authority. */
@TestInstance(TestInstance.Lifecycle.PER_CLASS)
@TestMethodOrder(MethodOrderer.OrderAnnotation.class)
final class WindowsPreloadEndpointTest {
    @TempDir static Path temporary;
    private WindowsJobProcess.OwnedStdio server;
    private WindowsJobProcess target;
    private WindowsPreloadCustody.Lease lease;
    private WindowsPreloadCustody.Endpoint endpoint, continuousEndpoint;
    private String primaryName, auxiliaryName, primaryLocator, auxiliaryLocator, clientLocator, waitingLocator;
    private Path sourcePin;
    private Instant deadline;

    private List<String> command(String mode, String... names) {
        List<String> result = new ArrayList<>(List.of("-Xms8m", "-Xmx16m", "-XX:+UseSerialGC",
                "-XX:ActiveProcessorCount=1", "-XX:MaxMetaspaceSize=32m",
                "-XX:ReservedCodeCacheSize=16m", "-Xss256k", "-Dfile.encoding=UTF-8",
                "-Djna.tmpdir=" + System.getProperty("jna.tmpdir", System.getProperty("java.io.tmpdir")),
                "-cp", System.getProperty("java.class.path"), PreloadEndpointSoftwarePeer.class.getName(), mode));
        result.addAll(List.of(names)); return List.copyOf(result);
    }
    private WindowsJobProcess.CommandSpec spec(Path directory, List<String> args) {
        return new WindowsJobProcess.CommandSpec(Path.of(System.getProperty("java.home"), "bin/java.exe"),
                args, directory, System.getenv(), directory.resolve("stdout.raw"),
                directory.resolve("stderr.raw"), 128L << 20);
    }
    private static ControlBuild.FileRef classRef(Class<?> type) throws Exception {
        Path root = Path.of(type.getProtectionDomain().getCodeSource().getLocation().toURI());
        return ControlBuild.FileRef.measure(Files.isDirectory(root)
                ? root.resolve(type.getName().replace('.', '/') + ".class") : root);
    }
    private byte[] read() throws IOException, InterruptedException { return server.readLine(deadline).rawBytes(); }
    @BeforeAll void acquireRealSoftwareResources() throws Exception {
        deadline = Instant.now().plusSeconds(30);
        String nonce = UUID.randomUUID().toString();
        primaryName = "\\\\.\\pipe\\xar-java-software-primary-" + nonce;
        auxiliaryName = "\\\\.\\pipe\\xar-java-software-aux-" + nonce;
        sourcePin = temporary.resolve("software-owner-source.txt"); Files.writeString(sourcePin, "pinned");
        Path dll = temporary.resolve("software-only-held.dll"); Files.writeString(dll, "software-held-file");
        Path serverDirectory = Files.createDirectory(temporary.resolve("server"));
        Path targetDirectory = Files.createDirectory(temporary.resolve("target"));
        var serverCommand = spec(serverDirectory, command("server", primaryName, auxiliaryName));
        List<ControlBuild.FileRef> refs = List.of(classRef(PreloadEndpointSoftwarePeer.class),
                classRef(WindowsPreloadCustody.class), classRef(WindowsPreloadCustody.Api.class),
                classRef(WindowsJobProcess.JobKernel32.class), classRef(Native.class), classRef(Kernel32.class),
                ControlBuild.FileRef.measure(sourcePin));
        var stdio = new WindowsJobProcess.OwnedStdioSpec(serverCommand, WindowsJobProcess.ConsoleMode.NO_WINDOW,
                ControlBuild.FileRef.measure(serverCommand.executable()), refs, deadline, 4096, 4096, 16384, () -> { });
        server = WindowsJobProcess.startOwnedStdio(stdio);
        String[] locators = new String(read(), StandardCharsets.US_ASCII).strip().split(" ");
        assertEquals(4, locators.length);
        primaryLocator = locators[0]; auxiliaryLocator = locators[1]; clientLocator = locators[2];
        waitingLocator = locators[3];
        for (String locator : locators) assertTrue(locator.matches("[1-9][0-9]*"));
        var retained = new AtomicReference<WindowsPreloadCustody.Lease>();
        var targetCommand = spec(targetDirectory, command("client", primaryName));
        target = WindowsJobProcess.start(targetCommand, WindowsJobProcess.ConsoleMode.NO_WINDOW, suspended -> {
            var acquired = WindowsPreloadCustody.prepare(suspended, new WindowsPreloadCustody.DllRef(
                    ControlBuild.FileRef.measure(dll), deadline, () -> { }));
            try {
                var waiting = assertThrows(WindowsPreloadCustody.PipeNotConnected.class,
                        () -> acquired.retainOwnerServer(server, primaryLocator, primaryName));
                assertTrue(waiting.win32Error() == 233 || waiting.win32Error() == 1168);
                retained.set(acquired); return acquired;
            } catch (RuntimeException | AssertionError failure) {
                try { acquired.close(); } catch (IOException cleanup) { failure.addSuppressed(cleanup); }
                throw new IOException("Software pre-resume assertion failed; original owner must clean up", failure);
            }
        });
        lease = retained.get();
        assertEquals("SOFTWARE_CONNECTED\n", new String(read(), StandardCharsets.US_ASCII));
        Instant readyDeadline = Instant.now().plusSeconds(4);
        while (Files.size(targetCommand.stdout()) == 0 && Instant.now().isBefore(readyDeadline)) Thread.sleep(10);
        assertEquals("SOFTWARE_CLIENT_READY\n", Files.readString(targetCommand.stdout()));
    }
    @Test @Order(1) void actualKernelNameAndBothPeerPidsMatchContinuousResources() throws Exception {
        endpoint = lease.retainOwnerServer(server, primaryLocator, primaryName);
        continuousEndpoint = lease.retainOwnerServer(server, primaryLocator, primaryName);
        endpoint.verify();
        assertEquals(server.identity(), endpoint.ownerIdentity());
        assertEquals(target.identity(), endpoint.targetIdentity());
        assertEquals(primaryName, endpoint.pipeName());
    }
    @Test @Order(2) void wrongExactPipeNameRejectsOtherwiseMatchingServerHandle() {
        assertThrows(IOException.class, () -> lease.retainOwnerServer(server, primaryLocator, primaryName + "-wrong"));
    }
    @Test @Order(3) void actualWrongClientPidRejectsRealServerEnd() {
        assertThrows(IOException.class, () -> lease.retainOwnerServer(server, auxiliaryLocator, auxiliaryName));
    }
    @Test @Order(4) void actualClientHandleAndWaitingModeCannotBecomeEligibleServerEndpoint() {
        assertThrows(IOException.class, () -> lease.retainOwnerServer(server, clientLocator, auxiliaryName));
        IOException mode = assertThrows(IOException.class,
                () -> lease.retainOwnerServer(server, waitingLocator, auxiliaryName + "-wait"));
        assertTrue(mode.getMessage().contains("PIPE_NOWAIT"), mode.toString());
    }
    @Test @Order(5) void closedDuplicateAndClosedOriginalHandleAreRejected() throws Exception {
        assertNotNull(endpoint); endpoint.close(); assertThrows(IOException.class, endpoint::verify);
        server.write("CLOSE_PRIMARY\n".getBytes(StandardCharsets.US_ASCII), deadline);
        assertEquals("SOFTWARE_CLOSED\n", new String(read(), StandardCharsets.US_ASCII));
        assertThrows(IOException.class, () -> lease.retainOwnerServer(server, primaryLocator, primaryName));
        continuousEndpoint.verify();
    }
    @Test @Order(6) void ownerSourceDriftRevokesLiveEndpointAndLatchesUnknown() throws Exception {
        Files.writeString(sourcePin, "drift!");
        IOException failure = assertThrows(IOException.class, continuousEndpoint::verify);
        assertFalse(failure.getMessage().contains("endpoint closed"), failure.toString());
        assertThrows(IOException.class, server::verifyActualIdentityAndSources);
        assertThrows(IOException.class, () -> server.write("STOP\n".getBytes(StandardCharsets.US_ASCII), deadline));
    }
    @AfterAll void consumeActualTerminalsAndReleaseResources() throws Exception {
        Exception failure = null;
        WindowsJobProcess.CommandResult serverResult = null, targetResult = null;
        if (endpoint != null) try { endpoint.close(); } catch (Exception error) { failure = error; }
        if (continuousEndpoint != null) try { continuousEndpoint.close(); } catch (Exception error) { failure = error; }
        if (server != null) {
            try {
                server.closeInput();
                serverResult = server.awaitExit(null).commandResult();
            } catch (Exception error) { failure = error; }
            finally { try { server.close(); } catch (Exception error) { failure = error; } }
        }
        if (target != null) {
            try {
                targetResult = target.await(Duration.ofSeconds(14), deadline, () -> { });
            } catch (Exception error) { failure = error; }
            finally { try { target.close(); } catch (Exception error) { failure = error; } }
        }
        if (failure != null) throw failure;
        assertNotNull(serverResult); assertEquals(0, serverResult.accounting().activeProcesses());
        assertFalse(serverResult.passed()); assertNotNull(serverResult.stopReason());
        assertNotNull(targetResult); assertTrue(targetResult.passed(), targetResult.toString());
        assertEquals(0, targetResult.accounting().activeProcesses());
    }
}
