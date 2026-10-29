package org.xar.ck3.control.g2.context;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertInstanceOf;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.WindowsJobProcess;

/** Real Job-owned Java child and fragmented stdio; SOFTWARE only, never a Native completion or live Game result. */
final class RootMcpOwnedTransportTest {
    @TempDir Path temporary;
    private static final RootMcpWire.Handshake HANDSHAKE = new RootMcpWire.Handshake("2025-11-25", Set.of("2025-11-25"),
            "java-root-owned-software-test", "1", "software-mcp-peer", "1");
    private static final RootMcpWire.Limits LIMITS = new RootMcpWire.Limits(65536, 8);

    @Test void actualOwnedChildCompletesInitializeAndFragmentedUtf8SemanticReply() throws Exception {
        Path root = Files.createDirectory(temporary.resolve("success"));
        try (var channel = open(root, "success")) {
            var pins = new RootMcpSemanticClient.SourceRefs(channel.spec().programSourceRefs().getFirst(),
                    channel.spec().executableRef(), ControlBuild.FileRef.measure(Path.of(RootMcpOwnedTransportTest.class.getResource("RootMcpOwnedTransportTest.class").toURI())));
            var rejected = assertInstanceOf(RootMcpSemanticClient.Unavailable.class,
                    RootMcpSemanticClient.open(channel, Optional.of(pins), HANDSHAKE, LIMITS, deadline()));
            assertEquals(RootMcpSemanticClient.Reason.ACCEPTED_NATIVE_RUNTIME_UNAVAILABLE, rejected.reason());
            var session = assertInstanceOf(RootMcpSemanticClient.SoftwareSession.class,
                    RootMcpSemanticClient.openSoftware(channel, HANDSHAKE, LIMITS, deadline()));
            var result = assertInstanceOf(RootMcpSemanticClient.SoftwareSnapshot.class, session.snapshot(1, deadline())).completion();
            String projection = new String(result.ownerRow().bytes().bytes(), java.nio.charset.StandardCharsets.UTF_8);
            assertTrue(projection.contains("软件回显")); assertTrue(projection.contains("18446744073709551615"));
            assertTrue(projection.contains("1.2300e-17")); assertTrue(projection.contains("-0.0"));
            assertFalse(result.isError()); assertEquals(channel.identity(), result.child()); assertEquals(channel.sessionNonce(), result.sessionNonce());
            assertEquals(channel.spec().programSourceRefs(), result.programSources()); assertEquals(2, result.arrivalSequence());
            session.close(); var exit = channel.awaitExit(root.resolve("before-cleanup.json"));
            assertEquals(0, exit.commandResult().exitCode()); assertEquals(0, exit.commandResult().accounting().activeProcesses());
            assertTrue(Files.readString(root.resolve("stderr.log")).contains("software-mcp-stderr-is-separate"));
            assertFalse(new String(result.originalRpcLine().bytes(), java.nio.charset.StandardCharsets.UTF_8).contains("stderr-is-separate"));
        }
    }

    @Test void wrongIdFromActualOwnedPipeIsRetainedAndNeverResubmitted() throws Exception {
        Path root = Files.createDirectory(temporary.resolve("wrong-id"));
        try (var channel = open(root, "wrong-id")) {
            var session = assertInstanceOf(RootMcpSemanticClient.SoftwareSession.class,
                    RootMcpSemanticClient.openSoftware(channel, HANDSHAKE, LIMITS, deadline()));
            var unknown = assertInstanceOf(RootMcpSemanticClient.Unknown.class, session.snapshot(2, deadline()));
            assertFalse(unknown.replayAllowed());
            assertTrue(new String(unknown.lastFrame().bytes(), java.nio.charset.StandardCharsets.UTF_8).contains("\"id\":3"));
            assertEquals(RootMcpSemanticClient.Reason.CLOSED,
                    assertInstanceOf(RootMcpSemanticClient.Unavailable.class, session.snapshot(3, deadline())).reason());
            session.close(); var exit = channel.awaitExit(root.resolve("before-cleanup.json"));
            assertEquals(0, exit.commandResult().exitCode()); assertEquals(0, exit.commandResult().accounting().activeProcesses());
        }
    }

    @Test void actualReadTimeoutKillsOriginalJobAndDoesNotReplayTheToolCall() throws Exception {
        Path root = Files.createDirectory(temporary.resolve("timeout"));
        try (var channel = open(root, "stall")) {
            var session = assertInstanceOf(RootMcpSemanticClient.SoftwareSession.class,
                    RootMcpSemanticClient.openSoftware(channel, HANDSHAKE, LIMITS, deadline()));
            var unknown = assertInstanceOf(RootMcpSemanticClient.Unknown.class, session.snapshot(4, Instant.now().plusMillis(250)));
            assertEquals(IOException.class.getName(), unknown.exceptionType()); assertFalse(unknown.replayAllowed());
            assertEquals(RootMcpSemanticClient.Reason.CLOSED,
                    assertInstanceOf(RootMcpSemanticClient.Unavailable.class, session.snapshot(5, deadline())).reason());
            var exit = channel.awaitExit(root.resolve("before-cleanup.json"));
            assertEquals(0, exit.commandResult().accounting().activeProcesses());
            assertFalse(exit.commandResult().passed());
        }
    }

    private static WindowsJobProcess.OwnedStdio open(Path root, String mode) throws Exception {
        Path java = Path.of(System.getProperty("java.home")).resolve("bin/java.exe").toRealPath();
        var resource = RootMcpSoftwarePeer.class.getResource("RootMcpSoftwarePeer.class");
        if (resource == null || !resource.getProtocol().equals("file")) { throw new IOException("actual compiled software peer class file required; do not skip"); }
        ControlBuild.FileRef peer = ControlBuild.FileRef.measure(Path.of(resource.toURI()).toRealPath());
        var command = new WindowsJobProcess.CommandSpec(java, List.of("-Xms8m", "-Xmx16m", "-XX:MaxMetaspaceSize=24m", "-XX:ReservedCodeCacheSize=16m", "-Xss256k", "-XX:ActiveProcessorCount=1", "-XX:+UseSerialGC",
                "-cp", System.getProperty("java.class.path"), RootMcpSoftwarePeer.class.getName(), mode), root,
                Map.of(), root.resolve("stdout.jsonl"), root.resolve("stderr.log"), 128L << 20);
        return WindowsJobProcess.startOwnedStdio(new WindowsJobProcess.OwnedStdioSpec(command, WindowsJobProcess.ConsoleMode.NO_WINDOW,
                ControlBuild.FileRef.measure(java), List.of(peer), Instant.now().plusSeconds(15), 65536, 131072, 262144, () -> { }));
    }
    private static Instant deadline() { return Instant.now().plusSeconds(10); }
}
