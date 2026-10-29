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

/** Actual Job-owned software stdout: a full8MiB body is duplicated into an MCP envelope, then a real line overflow is refused. */
final class RootMcpLargeEnvelopeTest {
    @TempDir Path temporary;
    private static final RootMcpWire.Handshake HANDSHAKE = new RootMcpWire.Handshake("2025-11-25", Set.of("2025-11-25"),
            "java-root-envelope-test", "1", "software-envelope-peer", "1");
    private static final RootMcpWire.Limits LIMITS = new RootMcpWire.Limits(RootMcpEnvelope.RPC_LINE_MAX_BYTES, 8);

    @Test void actualEightMiBBodyAndDuplicatedMcpEnvelopeKeepSeparateBudgetsAndSoftwareScope() throws Exception {
        Path root = Files.createDirectory(temporary.resolve("full-body"));
        try (var channel = open(root, "large")) {
            var unavailable = assertInstanceOf(RootMcpSemanticClient.Unavailable.class,
                    RootMcpSemanticClient.openNative(channel, Optional.empty(), HANDSHAKE, LIMITS, deadline()));
            assertEquals(RootMcpSemanticClient.Reason.ACCEPTED_NATIVE_RUNTIME_UNAVAILABLE, unavailable.reason());
            var session = assertInstanceOf(RootMcpSemanticClient.SoftwareSession.class,
                    RootMcpSemanticClient.openSoftware(channel, HANDSHAKE, LIMITS, deadline()));
            var completion = assertInstanceOf(RootMcpSemanticClient.SoftwareSnapshot.class, session.snapshot(1, deadline())).completion();
            assertEquals(RootMcpEnvelope.SEMANTIC_BODY_MAX_BYTES, completion.semanticBody().byteLength());
            assertTrue(completion.originalRpcLine().byteLength() > 8 * 1024 * 1024 + 4096,
                    "the actual whole MCP line must exceed the old lower hard cap");
            assertTrue(completion.originalRpcLine().byteLength() <= RootMcpEnvelope.RPC_LINE_MAX_BYTES);
            assertTrue(completion.ownerRow().bytes().byteLength() <= RootMcpEnvelope.OWNER_ROW_MAX_BYTES);
            assertFalse(completion.isError()); assertEquals(channel.identity(), completion.child());
            assertEquals(channel.sessionNonce(), completion.sessionNonce()); assertEquals(2, completion.arrivalSequence());
            session.close(); var terminal = channel.awaitExit(root.resolve("before-cleanup.json"));
            assertEquals(0, terminal.commandResult().exitCode()); assertEquals(0, terminal.commandResult().accounting().activeProcesses());
            assertTrue(Files.size(root.resolve("rpc.audit.jsonl")) > completion.originalRpcLine().byteLength());
            assertTrue(Files.size(root.resolve("rpc.audit.jsonl")) < completion.originalRpcLine().byteLength() + 1024L);
            assertTrue(Files.readString(root.resolve("stderr.log")).contains("SOFTWARE_ENVELOPE_large"));
        }
    }

    @Test void actualWholeLineOverflowTerminatesOriginalJobAndCannotReplay() throws Exception {
        Path root = Files.createDirectory(temporary.resolve("overflow"));
        try (var channel = open(root, "overflow")) {
            var session = assertInstanceOf(RootMcpSemanticClient.SoftwareSession.class,
                    RootMcpSemanticClient.openSoftware(channel, HANDSHAKE, LIMITS, deadline()));
            var unknown = assertInstanceOf(RootMcpSemanticClient.Unknown.class, session.snapshot(2, deadline()));
            assertEquals(IOException.class.getName(), unknown.exceptionType()); assertFalse(unknown.replayAllowed());
            assertEquals(RootMcpSemanticClient.Reason.CLOSED,
                    assertInstanceOf(RootMcpSemanticClient.Unavailable.class, session.snapshot(3, deadline())).reason());
            var terminal = channel.awaitExit(root.resolve("before-cleanup.json"));
            assertEquals(0, terminal.commandResult().accounting().activeProcesses()); assertFalse(terminal.commandResult().passed());
            long retained = Files.size(root.resolve("rpc.audit.jsonl"));
            assertTrue(retained >= RootMcpEnvelope.RPC_LINE_MAX_BYTES);
            assertTrue(retained <= RootMcpEnvelope.RPC_LINE_MAX_BYTES + (1L << 20));
        }
    }

    private static WindowsJobProcess.OwnedStdio open(Path root, String mode) throws Exception {
        Path java = Path.of(System.getProperty("java.home")).resolve("bin/java.exe").toRealPath();
        var resource = RootMcpEnvelopePeer.class.getResource("RootMcpEnvelopePeer.class");
        if (resource == null || !resource.getProtocol().equals("file")) { throw new IOException("actual software peer class required; do not skip"); }
        var peer = ControlBuild.FileRef.measure(Path.of(resource.toURI()).toRealPath());
        var command = new WindowsJobProcess.CommandSpec(java, List.of("-Xms8m", "-Xmx16m", "-XX:MaxMetaspaceSize=24m",
                "-XX:ReservedCodeCacheSize=16m", "-Xss256k", "-XX:ActiveProcessorCount=1", "-XX:+UseSerialGC",
                "-cp", System.getProperty("java.class.path"), RootMcpEnvelopePeer.class.getName(), mode), root, Map.of(),
                root.resolve("rpc.audit.jsonl"), root.resolve("stderr.log"), 128L << 20);
        return WindowsJobProcess.startOwnedStdio(new WindowsJobProcess.OwnedStdioSpec(command, WindowsJobProcess.ConsoleMode.NO_WINDOW,
                ControlBuild.FileRef.measure(java), List.of(peer), Instant.now().plusSeconds(90), RootMcpEnvelope.RPC_LINE_MAX_BYTES,
                131072, RootMcpEnvelope.SESSION_RECEIVED_MAX_BYTES, () -> { }));
    }
    private static Instant deadline() { return Instant.now().plusSeconds(60); }
}
