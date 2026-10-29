package org.xar.ck3.control.wave2.runtime.clockreader;

import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.JsonParser;
import com.fasterxml.jackson.core.JsonToken;
import com.fasterxml.jackson.core.StreamReadFeature;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.CharBuffer;
import java.nio.charset.CharacterCodingException;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;

/** Local legacy-container reader. Raw subtree slices retain 1.0/1e0 token types. */
final class ClockRawJson {
    private static final JsonFactory FACTORY = JsonFactory.builder().enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION).build();
    private static final ObjectMapper MAPPER = new ObjectMapper(FACTORY)
            .enable(DeserializationFeature.USE_BIG_INTEGER_FOR_INTS)
            .enable(DeserializationFeature.USE_BIG_DECIMAL_FOR_FLOATS)
            .enable(DeserializationFeature.FAIL_ON_TRAILING_TOKENS);
    private ClockRawJson() { }
    static JsonNode parse(byte[] raw, int maximum) {
        StrictJson.require(raw != null && raw.length >= 1 && raw.length <= maximum && maximum <= 32 * 1024 * 1024, "bounded legacy JSON");
        try {
            StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT).onUnmappableCharacter(CodingErrorAction.REPORT)
                    .decode(ByteBuffer.wrap(raw));
            JsonNode root = MAPPER.readTree(raw); StrictJson.require(root != null, "JSON value required"); return root;
        } catch (IOException error) { throw new ContractViolationException("invalid, duplicate or trailing legacy JSON", error); }
    }
    static byte[] textJson(JsonNode node, int maximum) {
        StrictJson.require(node != null && node.isTextual(), "actual MCP text content required");
        try {
            ByteBuffer encoded = StandardCharsets.UTF_8.newEncoder().onMalformedInput(CodingErrorAction.REPORT)
                    .onUnmappableCharacter(CodingErrorAction.REPORT).encode(CharBuffer.wrap(node.textValue()));
            StrictJson.require(encoded.remaining() >= 1 && encoded.remaining() <= maximum, "native text body exceeds byte budget");
            byte[] raw = new byte[encoded.remaining()]; encoded.get(raw); return raw;
        } catch (CharacterCodingException error) { throw new ContractViolationException("unpaired Unicode in MCP body", error); }
    }
    static byte[] subtree(byte[] raw, String... objectPath) {
        try (JsonParser parser = FACTORY.createParser(raw)) {
            StrictJson.require(parser.nextToken() == JsonToken.START_OBJECT, "object root required");
            byte[] result = find(parser, raw, objectPath, 0);
            StrictJson.require(result != null, "required raw JSON path missing"); return result;
        } catch (IOException error) { throw new ContractViolationException("invalid raw JSON subtree", error); }
    }
    private static byte[] find(JsonParser parser, byte[] raw, String[] path, int depth) throws IOException {
        StrictJson.require(parser.currentToken() == JsonToken.START_OBJECT, "object required along raw JSON path");
        while (parser.nextToken() != JsonToken.END_OBJECT) {
            StrictJson.require(parser.currentToken() == JsonToken.FIELD_NAME, "JSON field required");
            String name = parser.currentName(); parser.nextToken();
            if (name.equals(path[depth])) {
                if (depth + 1 < path.length) { return find(parser, raw, path, depth + 1); }
                long start = parser.currentTokenLocation().getByteOffset(); parser.skipChildren();
                long end = parser.currentLocation().getByteOffset();
                StrictJson.require(start >= 0 && end > start && end <= raw.length, "raw subtree byte locations");
                return Arrays.copyOfRange(raw, (int) start, (int) end);
            }
            parser.skipChildren();
        }
        return null;
    }
}
