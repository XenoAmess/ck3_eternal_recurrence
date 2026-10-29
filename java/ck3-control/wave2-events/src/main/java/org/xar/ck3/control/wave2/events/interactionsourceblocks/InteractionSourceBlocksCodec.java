package org.xar.ck3.control.wave2.events.interactionsourceblocks;

import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.StreamReadFeature;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.util.Set;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;
import static org.xar.ck3.control.wave2.events.interactionsourceblocks.InteractionSourceBlocks.*;

/** UTF-8/JSON adapter for source extraction. No flags here grant registry qualification. */
public final class InteractionSourceBlocksCodec {
    public static final int MAX_JSON_BYTES = 12 * 1024 * 1024 + 4096;
    private static final ObjectMapper JSON = new ObjectMapper(JsonFactory.builder().enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION).build())
            .enable(DeserializationFeature.FAIL_ON_TRAILING_TOKENS);
    public record Request(String text, String key) { public Request { validText(text); InteractionSourceBlocks.key(key); } }
    private InteractionSourceBlocksCodec() { }
    public static Request parseRequest(byte[] raw) {
        StrictJson.require(raw != null && raw.length > 0 && raw.length <= MAX_JSON_BYTES, "bounded source projection required");
        try {
            String decoded = StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT).onUnmappableCharacter(CodingErrorAction.REPORT)
                    .decode(ByteBuffer.wrap(raw)).toString();
            ObjectNode root = StrictJson.object(JSON.readTree(decoded), Set.of("schema", "text", "key"));
            StrictJson.require(root.get("schema").isTextual() && root.get("schema").textValue().equals("xar.interaction-source-block-request/v1"), "unsupported source block schema");
            JsonNode text = root.get("text"); StrictJson.require(text.isTextual(), "source text string required");
            return new Request(text.textValue(), StrictJson.text(root.get("key")));
        } catch (IOException error) { throw new ContractViolationException("invalid UTF-8 or JSON source request", error); }
    }
    public static byte[] encodeRequest(Request value) {
        ObjectNode row = JSON.createObjectNode(); row.put("schema", "xar.interaction-source-block-request/v1"); row.put("text", value.text()); row.put("key", value.key());
        return encode(row);
    }
    public static byte[] encodeBlock(Block value) {
        ObjectNode row = JSON.createObjectNode(); row.put("schema", "xar.interaction-source-block/v1");
        if (value instanceof Found found) { row.put("status", "found"); row.put("text", found.text()); }
        else { java.util.Objects.requireNonNull(value); row.put("status", "absent"); row.putNull("text"); }
        row.put("material_effects_verified", false); return encode(row);
    }
    private static byte[] encode(JsonNode value) {
        try { byte[] raw = JSON.writeValueAsBytes(value); StrictJson.require(raw.length <= MAX_JSON_BYTES, "source projection output too large"); return raw; }
        catch (IOException error) { throw new ContractViolationException("source projection serialization failed", error); }
    }
}
