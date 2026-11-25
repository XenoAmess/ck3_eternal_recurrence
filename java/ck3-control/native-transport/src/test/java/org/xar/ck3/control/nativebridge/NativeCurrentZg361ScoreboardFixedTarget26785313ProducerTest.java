package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.GuiWindowFrame;
import org.xar.ck3.control.nativebridge.capabilities.registry.GuiWindowFramePublicCodec;

/** Actual current C++ serializer/parser originals. No Game, tree synthesis or action qualification. */
final class NativeCurrentZg361ScoreboardFixedTarget26785313ProducerTest {
    private static final String ROOT = "/current267-zg361-fixed-scoreboard-cpp-a1731/";
    private static final String TARGET = "zg361_scoreboard_window";
    private static final String ID = "root-fixed-scoreboard-DATA-1";

    private static byte[] original(String name, int bytes, String sha) throws Exception {
        byte[] body;
        try (var stream = NativeCurrentZg361ScoreboardFixedTarget26785313ProducerTest.class.getResourceAsStream(ROOT + name)) {
            if (stream == null) throw new IOException("actual C++ original is required: " + name);
            body = stream.readNBytes(16385);
        }
        assertEquals(bytes, body.length);
        assertEquals(sha, sha(body));
        return body;
    }

    private static byte[] response() throws Exception {
        return original("cpp-fixed-scoreboard-response.body.json", 2186,
                "e82f8e76f8cd4569ad0cf7efef5f2052f141c90b08c317a74cfc1ea238068789");
    }

    private static byte[] request() throws Exception {
        return original("cpp-fixed-scoreboard-request.body.json", 698,
                "26b1970268dbaa7341cddeec27c08b22caf90b6a873b817603d95898470931e0");
    }

    private static String sha(byte[] body) throws Exception {
        return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(body));
    }

    @Test void actualCppCompleteTargetProjectionRoundTripsWithoutMiddleOrFullGameClaims() throws Exception {
        var original = StrictJson.parse(response());
        var frame = assertInstanceOf(GuiWindowFrame.Partial.class,
                GuiWindowFramePublicCodec.decodePacket(new RawJson(response()), ID));
        assertEquals(TARGET, frame.requestedWindow());
        assertTrue(frame.windowAvailable());
        assertEquals(1, frame.topLevel().size());
        assertEquals(TARGET, frame.topLevel().getFirst().name());
        var nodes = frame.window().orElseThrow().nodes();
        assertEquals(4, nodes.size());
        assertEquals(List.of(TARGET, "scoreboard_body", "score_text", "zg361_scoreboard_close"),
                nodes.stream().map(GuiWindowFrame.Node::name).toList());
        assertEquals(0, nodes.getFirst().nodeId());
        assertTrue(nodes.getFirst().parentId().isEmpty());
        assertEquals(0, nodes.getFirst().depth());
        assertEquals(0, nodes.getFirst().siblingIndex());
        assertEquals(2, nodes.getFirst().childCount());
        assertEquals(1, nodes.get(1).childCount());
        assertEquals(0, nodes.get(2).childCount());
        assertEquals(0, nodes.get(3).childCount());
        var encoded = GuiWindowFramePublicCodec.encode(frame);
        assertEquals(frame, GuiWindowFrame.decode(encoded));
        assertEquals(original.get("result"), StrictJson.parse(encoded.bytes()));
        for (String key : List.of("complete_gui_tree", "complete_snapshot", "native_findtop_semantics_verified",
                "activation_available", "control_actions_available")) {
            assertFalse(original.get("result").get(key).booleanValue());
        }
        assertTrue(original.get("result").get("complete_window_tree").booleanValue());
    }

    @Test void actualCppNamedRequestUsesProductionFactoryAndExportsOneImmutableParserInput() throws Exception {
        byte[] cppBody = request();
        var cpp = StrictJson.parse(cppBody);
        var actual = GuiWindowFramePublicCodec.decodeRequestPacket(NativeWire.packet(cppBody));
        assertEquals(TARGET, actual.windowName());
        assertEquals(new BigInteger("4102444800000"), actual.deadlineUnixMs());
        var response = assertInstanceOf(GuiWindowFrame.Partial.class,
                GuiWindowFramePublicCodec.decodePacket(new RawJson(response()), ID));
        assertEquals(response.coreFrame(), actual.expectedCore());
        // This is exactly NativeGameTransport's named-window production packet factory.
        byte[] packet = NativeWire.execute(ID, GuiWindowFrame.STEP, BigInteger.ZERO,
                GuiWindowFramePublicCodec.additionalFields(actual).bytes());
        assertEquals(packet.length - 4, ByteBuffer.wrap(packet, 0, 4).order(ByteOrder.LITTLE_ENDIAN).getInt());
        byte[] body = java.util.Arrays.copyOfRange(packet, 4, packet.length);
        assertEquals(cpp, StrictJson.parse(body));
        assertEquals(actual, GuiWindowFramePublicCodec.decodeRequestPacket(packet));
        var outer = NativeWire.decodeExecuteRequest(packet);
        assertEquals(ID, outer.requestId());
        assertEquals(java.util.Optional.of(BigInteger.ZERO), outer.expectedRevision());
        assertTrue(outer.expectedSnapshotRevision().isEmpty());

        String output = System.getProperty("xar.zg361.fixed.scoreboard.java.requests.output.directory");
        assertNotNull(output, "actual once parser export directory is required");
        Path directory = Path.of(output);
        assertTrue(directory.isAbsolute());
        Files.createDirectories(directory);
        Path bodyPath = directory.resolve("java-fixed-scoreboard-request.body.json");
        Path packetPath = directory.resolve("java-fixed-scoreboard-request.packet.bin");
        Files.write(bodyPath, body, StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE);
        Files.write(packetPath, packet, StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE);
        var index = StrictJson.object().put("schema", "xar.zg361.fixed-scoreboard.actual-Java1-factory.v1")
                .put("request_id", ID).put("deadline_unix_ms", actual.deadlineUnixMs())
                .put("window_name", TARGET).put("actual_factory_count", 1)
                .put("production_factory", "GuiWindowFramePublicCodec.additionalFields + NativeWire.execute");
        addPin(index.putObject("body"), bodyPath, body);
        addPin(index.putObject("packet"), packetPath, packet);
        Files.write(directory.resolve("java-fixed-scoreboard-requests-index.json"), StrictJson.canonical(index),
                StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE);
    }

    private static void addPin(com.fasterxml.jackson.databind.node.ObjectNode row, Path path, byte[] body) throws Exception {
        row.put("path", path.toString()).put("bytes", body.length).put("sha256", sha(body));
    }
}
