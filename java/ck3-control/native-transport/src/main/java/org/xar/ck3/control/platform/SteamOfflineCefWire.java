package org.xar.ck3.control.platform;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.InetSocketAddress;
import java.net.Proxy;
import java.net.Socket;
import java.net.URI;
import java.net.URISyntaxException;
import java.nio.ByteBuffer;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Base64;
import java.util.HashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;

/** Original fixed read-only App getter protocol; never enables CDP or accepts caller JavaScript. */
final class SteamOfflineCefWire {
    static final int MAXIMUM_BYTES = 256 * 1024;
    record Target(String id, String url, String webSocketUrl) { }
    private SteamOfflineCefWire() { }

    static String getterExpression(String nonce) {
        if (nonce == null || !nonce.matches("[A-Za-z0-9_-]{1,128}")) throw new IllegalArgumentException("Fresh bounded nonce required");
        return "(() => {\nconst app = globalThis.App;\nif (!app || typeof app.GetCurrentUser !== \"function\" ||\n"
                + "    typeof app.BIsOfflineMode !== \"function\") throw Error(\"no Steam App\");\n"
                + "const user = app.GetCurrentUser();\nif (!user) throw Error(\"no current Steam user\");\n"
                + "return {nonce: \"" + nonce + "\",\n direct: user.bIsOfflineMode, method: app.BIsOfflineMode()};\n})()";
    }
    static boolean parseGetter(JsonNode node, String nonce) {
        ObjectNode value = StrictJson.object(node, Set.of("nonce", "direct", "method"));
        StrictJson.require(StrictJson.text(value.get("nonce")).equals(nonce) && value.get("direct").isBoolean()
                && value.get("method").isBoolean() && value.get("direct").booleanValue() == value.get("method").booleanValue(),
                "Both original App getters must be actual equal booleans bound to this nonce");
        return value.get("direct").booleanValue();
    }
    static List<Target> targets(JsonNode version, JsonNode list) {
        StrictJson.require(version != null && version.isObject(), "Chromium discovery object required");
        String browser = StrictJson.text(version.get("Browser")).toLowerCase(Locale.ROOT);
        StrictJson.require((browser.startsWith("chrome/") || browser.startsWith("chromium/"))
                && StrictJson.text(version.get("Protocol-Version")).startsWith("1."), "Qualified Chromium debugger required");
        StrictJson.require(list != null && list.isArray() && list.size() <= 128, "Bounded CEF target list required");
        List<Target> result = new ArrayList<>();
        for (JsonNode node : list) {
            StrictJson.require(node.isObject(), "CEF target object required");
            if (!node.path("type").isTextual() || !node.path("type").textValue().equals("page")) continue;
            String url = StrictJson.text(node.get("url"));
            boolean shared = url.equals("about:blank") && node.path("title").isTextual()
                    && node.path("title").textValue().equals("SharedJSContext");
            URI target = uri(url);
            if (!shared && !("https".equalsIgnoreCase(target.getScheme()) && "steamloopback.host".equalsIgnoreCase(target.getHost())
                    && target.getRawQuery() == null && target.getRawFragment() == null && target.getRawUserInfo() == null)) continue;
            String id = StrictJson.text(node.get("id")), socket = StrictJson.text(node.get("webSocketDebuggerUrl"));
            if (!("/devtools/page/" + id).equals(uri(socket).getRawPath())) continue;
            result.add(new Target(id, url, socket));
        }
        return List.copyOf(result);
    }
    static URI endpoint(String value, int port) {
        URI uri = uri(value);
        StrictJson.require("ws".equalsIgnoreCase(uri.getScheme()) && uri.getHost() != null && Set.of("localhost", "127.0.0.1").contains(uri.getHost().toLowerCase(Locale.ROOT))
                && uri.getPort() == port && uri.getRawUserInfo() == null && uri.getRawQuery() == null && uri.getRawFragment() == null
                && uri.getRawPath() != null && uri.getRawPath().matches("/devtools/page/[A-Za-z0-9_-]{1,128}"), "Owned loopback CEF websocket required");
        return uri;
    }
    static List<Target> discover(int port, Instant deadline) throws IOException {
        try { return targets(http(port, "/json/version", deadline), http(port, "/json/list", deadline)); }
        catch (IllegalArgumentException invalid) { throw new IOException("CEF discovery rejected", invalid); }
    }
    private static JsonNode http(int port, String path, Instant deadline) throws IOException {
        if (port < 1 || port > 65535 || !Set.of("/json/version", "/json/list").contains(path)) throw new IOException("Fixed owned CDP discovery required");
        HttpURLConnection connection = (HttpURLConnection) URI.create("http://127.0.0.1:" + port + path).toURL().openConnection(Proxy.NO_PROXY);
        connection.setConnectTimeout(remainingMillis(deadline)); connection.setReadTimeout(remainingMillis(deadline));
        connection.setInstanceFollowRedirects(false); connection.setRequestMethod("GET");
        try {
            if (connection.getResponseCode() != 200) throw new IOException("CDP discovery unavailable");
            try (InputStream input = connection.getInputStream(); ByteArrayOutputStream data = new ByteArrayOutputStream()) {
                byte[] block = new byte[8192];
                while (true) {
                    remainingMillis(deadline); int count = input.read(block);
                    if (count < 0) break;
                    if (count == 0) throw new IOException("CEF HTTP input made no progress");
                    if (data.size() > MAXIMUM_BYTES - count) throw new IOException("CDP discovery response limit exceeded");
                    data.write(block, 0, count);
                }
                remainingMillis(deadline); return StrictJson.parse(data.toByteArray(), MAXIMUM_BYTES);
            }
        } finally { connection.disconnect(); }
    }
    static boolean evaluate(Target target, int port, String nonce, Instant deadline) throws IOException {
        final URI endpoint;
        try { endpoint = endpoint(target.webSocketUrl(), port); }
        catch (IllegalArgumentException invalid) { throw new IOException("Untrusted CEF endpoint", invalid); }
        try (Socket socket = new Socket(Proxy.NO_PROXY)) {
            socket.connect(new InetSocketAddress("127.0.0.1", port), remainingMillis(deadline));
            String key = Base64.getEncoder().encodeToString(SteamOfflineProbe.randomBytes(16));
            String request = "GET " + endpoint.getRawPath() + " HTTP/1.1\r\nHost: 127.0.0.1:" + port
                    + "\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Key: " + key + "\r\nSec-WebSocket-Version: 13\r\n\r\n";
            socket.getOutputStream().write(request.getBytes(StandardCharsets.US_ASCII));
            ByteArrayOutputStream header = new ByteArrayOutputStream();
            while (true) {
                if (header.size() > 8192) throw new IOException("CDP handshake limit exceeded");
                header.write(read(socket, 1, deadline));
                byte[] bytes = header.toByteArray(); int n = bytes.length;
                if (n >= 4 && bytes[n - 4] == '\r' && bytes[n - 3] == '\n' && bytes[n - 2] == '\r' && bytes[n - 1] == '\n') break;
            }
            String[] lines = header.toString(StandardCharsets.ISO_8859_1).split("\r\n");
            Map<String, String> fields = new HashMap<>();
            for (int index = 1; index < lines.length; index++) {
                int colon = lines[index].indexOf(':');
                if (colon >= 0) fields.put(lines[index].substring(0, colon).toLowerCase(Locale.ROOT), lines[index].substring(colon + 1).trim());
            }
            if (!lines[0].startsWith("HTTP/1.1 101 ") || !accept(key).equals(fields.get("sec-websocket-accept"))
                    || !"websocket".equalsIgnoreCase(fields.get("upgrade"))) throw new IOException("CDP handshake rejected");
            ObjectNode message = StrictJson.object(); message.put("id", 1); message.put("method", "Runtime.evaluate");
            ObjectNode parameters = message.putObject("params"); parameters.put("expression", getterExpression(nonce));
            parameters.put("returnByValue", true); parameters.put("throwOnSideEffect", true); parameters.put("disableBreaks", true);
            parameters.put("timeout", remainingMillis(deadline)); send(socket, StrictJson.canonical(message, MAXIMUM_BYTES), 1);
            for (int index = 0; index < 32; index++) {
                byte[] first = read(socket, 2, deadline); int flags = Byte.toUnsignedInt(first[0]), second = Byte.toUnsignedInt(first[1]);
                if ((flags & 0x70) != 0 || (flags & 0x80) == 0 || (second & 0x80) != 0) throw new IOException("Unsupported CDP websocket frame");
                int opcode = flags & 15; long count = second & 127;
                if (count == 126) count = Short.toUnsignedInt(ByteBuffer.wrap(read(socket, 2, deadline)).getShort());
                else if (count == 127) count = ByteBuffer.wrap(read(socket, 8, deadline)).getLong();
                if (count < 0 || count > MAXIMUM_BYTES) throw new IOException("CDP response limit exceeded");
                byte[] body = read(socket, (int) count, deadline);
                if (opcode == 9) { send(socket, body, 10); continue; }
                if (opcode != 1) throw new IOException("CDP response is not text");
                JsonNode response = StrictJson.parse(body, MAXIMUM_BYTES);
                if (response == null || !response.isObject()) throw new IOException("CDP response object required");
                if (!response.has("id")) continue;
                try {
                    StrictJson.require(StrictJson.integer(response.get("id"), 1, 1) == 1 && !response.has("error"), "Expected one successful CDP request ID");
                    JsonNode result = response.get("result");
                    StrictJson.require(result != null && result.isObject() && !result.has("exceptionDetails"), "Steam App getter unavailable");
                    JsonNode remote = result.get("result");
                    StrictJson.require(remote != null && remote.isObject() && remote.path("type").isTextual()
                            && remote.path("type").textValue().equals("object") && remote.has("value"), "Getter JSON object required");
                    return parseGetter(remote.get("value"), nonce);
                } catch (IllegalArgumentException invalid) { throw new IOException("CEF getter result rejected", invalid); }
            }
            throw new IOException("CDP event limit exceeded");
        }
    }
    private static byte[] read(Socket socket, int count, Instant deadline) throws IOException {
        byte[] data = new byte[count]; int offset = 0;
        while (offset < count) {
            socket.setSoTimeout(remainingMillis(deadline)); int read = socket.getInputStream().read(data, offset, count - offset);
            if (read <= 0) throw new IOException("CDP connection ended"); offset += read;
        }
        return data;
    }
    private static void send(Socket socket, byte[] data, int opcode) throws IOException {
        if (data.length > MAXIMUM_BYTES) throw new IOException("CDP request limit exceeded");
        ByteArrayOutputStream body = new ByteArrayOutputStream(); body.write(0x80 | opcode);
        if (data.length < 126) body.write(0x80 | data.length);
        else if (data.length < 65536) { body.write(0xfe); body.writeBytes(ByteBuffer.allocate(2).putShort((short) data.length).array()); }
        else { body.write(0xff); body.writeBytes(ByteBuffer.allocate(8).putLong(data.length).array()); }
        byte[] mask = SteamOfflineProbe.randomBytes(4); body.writeBytes(mask);
        for (int index = 0; index < data.length; index++) body.write(data[index] ^ mask[index % 4]);
        socket.getOutputStream().write(body.toByteArray());
    }
    private static String accept(String key) {
        try { return Base64.getEncoder().encodeToString(MessageDigest.getInstance("SHA-1")
                .digest((key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11").getBytes(StandardCharsets.US_ASCII))); }
        catch (NoSuchAlgorithmException impossible) { throw new IllegalStateException(impossible); }
    }
    static int remainingMillis(Instant deadline) throws IOException {
        long remaining = Duration.between(Instant.now(), deadline).toMillis();
        if (remaining <= 0) throw new IOException("CEF observation deadline expired");
        return (int) Math.min(Integer.MAX_VALUE, Math.max(1, remaining));
    }
    private static URI uri(String value) {
        try { return new URI(value); }
        catch (URISyntaxException invalid) { throw new IllegalArgumentException("Invalid CEF endpoint URI", invalid); }
    }
}
