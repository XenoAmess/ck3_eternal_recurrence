package org.xar.ck3.control.platform;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.net.InetAddress;
import java.net.ServerSocket;
import java.net.Socket;
import java.nio.ByteBuffer;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.time.Instant;
import java.util.Base64;
import java.util.List;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;

/** Actual production RFC6455 producer against a bounded local fixture, never a Steam endpoint. */
final class SteamOfflineCefSocketTest {
    private static final String NONCE = "0123456789abcdef0123456789abcdef";
    @Test void realLoopbackPreservesBothOriginalGetterStatesAndExactMaskedRequest() throws Exception {
        for (boolean offline : List.of(true, false)) {
            try (ServerSocket listener = new ServerSocket(0, 1, InetAddress.getByName("127.0.0.1"))) {
                listener.setSoTimeout(3000); ExecutorService executor = Executors.newSingleThreadExecutor();
                try {
                    Future<JsonNode> request = executor.submit(() -> serve(listener, offline, false));
                    int port = listener.getLocalPort();
                    var target = new SteamOfflineCefWire.Target("Shared", "about:blank", "ws://127.0.0.1:" + port + "/devtools/page/Shared");
                    assertEquals(offline, SteamOfflineCefWire.evaluate(target, port, NONCE, Instant.now().plusSeconds(2)));
                    JsonNode actual = request.get(4, TimeUnit.SECONDS);
                    assertEquals(1, StrictJson.integer(actual.get("id"), 1, 1));
                    assertEquals("Runtime.evaluate", actual.path("method").textValue());
                    JsonNode params = actual.path("params");
                    assertEquals(SteamOfflineCefWire.getterExpression(NONCE), params.path("expression").textValue());
                    assertTrue(params.path("throwOnSideEffect").isBoolean() && params.path("throwOnSideEffect").booleanValue());
                    assertTrue(params.path("returnByValue").isBoolean() && params.path("returnByValue").booleanValue());
                    assertTrue(params.path("disableBreaks").booleanValue());
                    assertTrue(StrictJson.integer(params.get("timeout"), 1, 2000) > 0);
                } finally { executor.shutdownNow(); assertTrue(executor.awaitTermination(5, TimeUnit.SECONDS)); }
            }
        }
    }
    @Test void aRealSocketWithNumericGetterDoesNotBecomeFalseOnline() throws Exception {
        try (ServerSocket listener = new ServerSocket(0, 1, InetAddress.getByName("127.0.0.1"))) {
            listener.setSoTimeout(3000); ExecutorService executor = Executors.newSingleThreadExecutor();
            try {
                Future<JsonNode> request = executor.submit(() -> serve(listener, false, true));
                int port = listener.getLocalPort();
                var target = new SteamOfflineCefWire.Target("Shared", "about:blank", "ws://127.0.0.1:" + port + "/devtools/page/Shared");
                assertThrows(IOException.class, () -> SteamOfflineCefWire.evaluate(target, port, NONCE, Instant.now().plusSeconds(2)));
                assertNotNull(request.get(4, TimeUnit.SECONDS));
            } finally { executor.shutdownNow(); assertTrue(executor.awaitTermination(5, TimeUnit.SECONDS)); }
        }
    }
    private static JsonNode serve(ServerSocket listener, boolean offline, boolean numeric) throws Exception {
        try (Socket stream = listener.accept()) {
            stream.setSoTimeout(3000); ByteArrayOutputStream header = new ByteArrayOutputStream();
            while (true) {
                if (header.size() > 8192) throw new IOException("Fixture request header exceeded limit");
                header.write(read(stream.getInputStream(), 1)); byte[] bytes = header.toByteArray(); int n = bytes.length;
                if (n >= 4 && bytes[n - 4] == '\r' && bytes[n - 3] == '\n' && bytes[n - 2] == '\r' && bytes[n - 1] == '\n') break;
            }
            String key = null;
            for (String line : header.toString(StandardCharsets.US_ASCII).split("\r\n")) if (line.startsWith("Sec-WebSocket-Key: ")) key = line.substring("Sec-WebSocket-Key: ".length());
            if (key == null) throw new IOException("Fixture did not receive a websocket key");
            String accept = Base64.getEncoder().encodeToString(MessageDigest.getInstance("SHA-1")
                    .digest((key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11").getBytes(StandardCharsets.US_ASCII)));
            stream.getOutputStream().write(("HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Accept: "
                    + accept + "\r\n\r\n").getBytes(StandardCharsets.US_ASCII));
            byte[] first = read(stream.getInputStream(), 2); int second = Byte.toUnsignedInt(first[1]);
            if (Byte.toUnsignedInt(first[0]) != 0x81 || (second & 128) == 0) throw new IOException("Client must send masked text");
            long length = second & 127;
            if (length == 126) length = Short.toUnsignedInt(ByteBuffer.wrap(read(stream.getInputStream(), 2)).getShort());
            else if (length == 127) length = ByteBuffer.wrap(read(stream.getInputStream(), 8)).getLong();
            if (length < 0 || length > SteamOfflineCefWire.MAXIMUM_BYTES) throw new IOException("Fixture client frame too large");
            byte[] mask = read(stream.getInputStream(), 4), body = read(stream.getInputStream(), (int) length);
            for (int index = 0; index < body.length; index++) body[index] ^= mask[index % 4];
            JsonNode request = StrictJson.parse(body, SteamOfflineCefWire.MAXIMUM_BYTES);
            ObjectNode response = StrictJson.object(); response.put("id", 1);
            ObjectNode remote = response.putObject("result").putObject("result"); remote.put("type", "object");
            ObjectNode value = remote.putObject("value"); value.put("nonce", NONCE);
            if (numeric) value.put("direct", 0); else value.put("direct", offline);
            value.put("method", offline); byte[] raw = StrictJson.canonical(response);
            ByteArrayOutputStream frame = new ByteArrayOutputStream(); frame.write(0x81);
            if (raw.length < 126) frame.write(raw.length);
            else { frame.write(126); frame.writeBytes(ByteBuffer.allocate(2).putShort((short) raw.length).array()); }
            frame.writeBytes(raw); stream.getOutputStream().write(frame.toByteArray()); return request;
        }
    }
    private static byte[] read(InputStream stream, int count) throws IOException {
        byte[] result = stream.readNBytes(count); if (result.length != count) throw new IOException("Fixture disconnected"); return result;
    }
}
