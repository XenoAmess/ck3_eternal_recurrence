package org.xar.ck3.control.g2.m0;

import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.StreamReadFeature;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;

/** Finite NDJSON test transport to the actual production codec; no host or game authority. */
public final class WarExitCodecProbe {
    static final int LIMIT = 1_048_576;
    static final ObjectMapper MAPPER = new ObjectMapper(JsonFactory.builder()
            .enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION).build())
            .enable(DeserializationFeature.USE_BIG_INTEGER_FOR_INTS)
            .enable(DeserializationFeature.FAIL_ON_TRAILING_TOKENS);
    private WarExitCodecProbe() { }
    public static void main(String[] args) throws IOException {
        if (args.length != 0) throw new IllegalArgumentException("stdin only");
        for (int count = 0; ; count++) {
            byte[] line = readLine();
            if (line == null) return;
            if (count >= 2048) throw new IllegalArgumentException("finite request count exceeded");
            ObjectNode output;
            try { output = execute(parse(line)); }
            catch (IllegalArgumentException rejected) {
                output = MAPPER.createObjectNode().put("accepted", false).put("error", rejected.getMessage());
            }
            byte[] raw = MAPPER.writeValueAsBytes(output);
            if (raw.length > LIMIT) throw new IllegalArgumentException("output limit exceeded");
            System.out.write(raw); System.out.write('\n'); System.out.flush();
        }
    }
    public static ObjectNode execute(JsonNode request) {
        ObjectNode response = MAPPER.createObjectNode().put("accepted", true);
        try {
            response.set("result", parse(RaiktorExitObservationCodec.execute(MAPPER.writeValueAsBytes(request)))); return response;
        } catch (IOException error) { throw new IllegalArgumentException("normalization wire roundtrip failed", error); }
    }
    static JsonNode parse(byte[] raw) throws IOException {
        if (raw.length > LIMIT) throw new IllegalArgumentException("input limit exceeded");
        String text = StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT)
                .onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(raw)).toString();
        JsonNode result = MAPPER.readTree(text);
        if (result == null) throw new IllegalArgumentException("JSON value required");
        finite(result); return result;
    }
    private static void finite(JsonNode node) {
        if (node.isFloatingPointNumber() && !Double.isFinite(node.doubleValue()))
            throw new IllegalArgumentException("finite JSON numbers required");
        if (node.isContainerNode()) for (JsonNode child : node) finite(child);
    }
    private static byte[] readLine() throws IOException {
        ByteArrayOutputStream line = new ByteArrayOutputStream();
        for (int value; (value = System.in.read()) != -1;) {
            if (value == '\n') return line.toByteArray();
            if (line.size() >= LIMIT) throw new IllegalArgumentException("input limit exceeded");
            line.write(value);
        }
        return line.size() == 0 ? null : line.toByteArray();
    }
}
