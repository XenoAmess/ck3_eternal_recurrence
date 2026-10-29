package org.xar.ck3.control.g2.context;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;

/** Test-only Java MCP peer; its messages deliberately contain no Game, Native or fixture-authority fields. */
public final class RootMcpSoftwarePeer {
    private RootMcpSoftwarePeer() { }
    public static void main(String[] arguments) throws Exception {
        if (arguments.length != 1) { throw new IllegalArgumentException("one software peer mode required"); }
        String mode = arguments[0]; ObjectMapper json = new ObjectMapper();
        try (BufferedReader input = new BufferedReader(new InputStreamReader(System.in, StandardCharsets.UTF_8))) {
            String line;
            while ((line = input.readLine()) != null) {
                JsonNode request = json.readTree(line); String method = request.path("method").asText();
                if (method.equals("notifications/initialized")) { continue; }
                JsonNode idNode = request.get("id");
                if (idNode == null || !idNode.isIntegralNumber() || !idNode.canConvertToLong() || idNode.longValue() < 1) {
                    throw new IllegalArgumentException("exact software client id required");
                }
                long id = idNode.longValue();
                if (method.equals("initialize")) {
                    emit("{\"jsonrpc\":\"2.0\",\"id\":" + id + ",\"result\":{\"protocolVersion\":\"2025-11-25\",\"capabilities\":{\"tools\":{}},\"serverInfo\":{\"name\":\"software-mcp-peer\",\"version\":\"1\"}}}\n");
                } else if (method.equals("tools/call")) {
                    if (!request.path("params").path("name").asText().equals("ck3_take_semantic_snapshot_private_v1")
                            || !request.path("params").path("arguments").isObject() || !request.path("params").path("arguments").isEmpty()) {
                        throw new IllegalArgumentException("only the fixed software semantic request is supported");
                    }
                    System.err.println("software-mcp-stderr-is-separate"); System.err.flush();
                    if (mode.equals("stall")) { Thread.sleep(10_000); }
                    if (mode.equals("wrong-id")) { id++; }
                    emit("{\"jsonrpc\":\"2.0\",\"id\":" + id + ",\"result\":{\"content\":[{\"type\":\"text\",\"text\":\"软件回显\"}],\"structuredContent\":{\"software_only\":true,\"unsigned\":18446744073709551615,\"decimal\":1.2300e-17,\"negative_zero\":-0.0}}}\n");
                } else { throw new IllegalArgumentException("unsupported software peer method"); }
            }
        }
    }
    private static void emit(String line) throws Exception {
        byte[] raw = line.getBytes(StandardCharsets.UTF_8);
        for (int offset = 0; offset < raw.length; offset += 3) {
            System.out.write(raw, offset, Math.min(3, raw.length - offset)); System.out.flush(); Thread.sleep(1);
        }
    }
}
