package org.xar.ck3.control.g2.context;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;

/** Test-only streaming software peer. No Game/Native tuple, custody token or fixture Native authority is emitted. */
public final class RootMcpEnvelopePeer {
    static final String BODY_PREFIX = "{\"software_only\":true,\"u64\":18446744073709551615,\"decimal\":1.2300e-17,\"negative_zero\":-0.0,\"value\":\"";
    static final String BODY_SUFFIX = "\"}";
    private static final ObjectMapper JSON = new ObjectMapper();
    private RootMcpEnvelopePeer() { }

    public static void main(String[] arguments) throws Exception {
        if (arguments.length != 1 || !java.util.Set.of("large", "overflow").contains(arguments[0])) {
            throw new IllegalArgumentException("explicit finite software envelope mode required");
        }
        try (BufferedReader input = new BufferedReader(new InputStreamReader(System.in, StandardCharsets.UTF_8))) {
            String line;
            while ((line = input.readLine()) != null) {
                JsonNode request = JSON.readTree(line); String method = request.path("method").asText();
                if (method.equals("notifications/initialized")) { continue; }
                JsonNode id = request.get("id");
                if (id == null || !id.isIntegralNumber() || !id.canConvertToLong() || id.longValue() < 1) {
                    throw new IllegalArgumentException("positive exact software request ID required");
                }
                if (method.equals("initialize")) {
                    text("{\"jsonrpc\":\"2.0\",\"id\":" + id.longValue()
                            + ",\"result\":{\"protocolVersion\":\"2025-11-25\",\"capabilities\":{\"tools\":{}},\"serverInfo\":{\"name\":\"software-envelope-peer\",\"version\":\"1\"}}}\n");
                } else if (method.equals("tools/call") && request.path("params").path("name").asText().equals(RootMcpWire.SEMANTIC_TOOL)
                        && request.path("params").path("arguments").isObject() && request.path("params").path("arguments").isEmpty()) {
                    System.err.println("SOFTWARE_ENVELOPE_" + arguments[0]); System.err.flush();
                    if (arguments[0].equals("large")) { large(id.longValue()); } else { overflow(id.longValue()); }
                } else { throw new IllegalArgumentException("only fixed software semantic request supported"); }
                System.out.flush();
            }
        }
    }
    private static void large(long id) throws Exception {
        int payload = RootMcpEnvelope.SEMANTIC_BODY_MAX_BYTES - BODY_PREFIX.getBytes(StandardCharsets.UTF_8).length
                - BODY_SUFFIX.getBytes(StandardCharsets.UTF_8).length;
        text("{\"jsonrpc\":\"2.0\",\"id\":" + id + ",\"result\":{\"content\":[{\"type\":\"text\",\"text\":\"");
        text(escaped(BODY_PREFIX)); repeat(payload); text(escaped(BODY_SUFFIX));
        text("\"}],\"structuredContent\":"); text(BODY_PREFIX); repeat(payload); text(BODY_SUFFIX); text("}}\n");
    }
    private static void overflow(long id) throws Exception {
        text("{\"jsonrpc\":\"2.0\",\"id\":" + id + ",\"result\":{\"content\":[{\"type\":\"text\",\"text\":\"");
        repeat(RootMcpEnvelope.RPC_LINE_MAX_BYTES); text("\"}]}}\n");
    }
    private static void repeat(int length) throws Exception {
        byte[] chunk = new byte[4093]; Arrays.fill(chunk, (byte) 'A');
        for (int offset = 0; offset < length; offset += chunk.length) {
            System.out.write(chunk, 0, Math.min(chunk.length, length - offset));
        }
    }
    private static String escaped(String value) throws Exception {
        String quoted = JSON.writeValueAsString(value); return quoted.substring(1, quoted.length() - 1);
    }
    private static void text(String value) throws Exception { System.out.write(value.getBytes(StandardCharsets.UTF_8)); }
}
