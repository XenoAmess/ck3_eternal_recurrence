package org.xar.ck3.control.g2.context;

import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.JsonParser;
import com.fasterxml.jackson.core.JsonToken;
import com.fasterxml.jackson.core.StreamReadFeature;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.charset.CharacterCodingException;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;
import java.util.HashSet;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.g2.common.G2Exception;
import org.xar.ck3.control.g2.common.G2HttpError;
import org.xar.ck3.control.g2.common.G2Wire;
import org.xar.ck3.control.g2.common.Milestone;

/** Exact transport only; source paths and capabilities are absent from request fields. */
public final class G2CallContextWire {
    public static final String HTTP_PATH = "/v1/g2-research/context";
    public static final String SCHEMA = "xar.g2-call-context/v1";
    public static final String PRODUCER = "java-quarkus-g2-call-context/v1";
    public static final String PRODUCER_VERSION = "0.1.0";
    public static final int MAX_INPUT_BYTES = G2Wire.MAX_REQUEST_BYTES;
    public static final int MAX_CONTEXT_BYTES = 65_536;
    private static final JsonFactory FACTORY = JsonFactory.builder()
            .enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION).build();
    private G2CallContextWire() { }
    public record Input(Milestone milestone, ProjectionJson payload) {
        public Input {
            Objects.requireNonNull(milestone); Objects.requireNonNull(payload);
            G2CallContextProducer.requirePayloadToken(payload);
        }
    }
    public static Input decodeInput(byte[] raw) {
        if (raw == null || raw.length == 0) { throw malformed("nonempty context request required"); }
        if (raw.length > MAX_INPUT_BYTES) { throw new G2Exception(G2HttpError.Code.PAYLOAD_TOO_LARGE, "context request role budget"); }
        if (raw.length >= 3 && raw[0] == (byte) 0xef && raw[1] == (byte) 0xbb && raw[2] == (byte) 0xbf) {
            throw malformed("context UTF8 BOM rejected");
        }
        for (byte value : raw) { if (value == 0) { throw malformed("context raw NUL rejected"); } }
        try { StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT)
                .onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(raw)); }
        catch (CharacterCodingException error) { throw malformed("invalid context UTF8"); }
        Set<String> seen = new HashSet<>(); Milestone milestone = null; ProjectionJson payload = null;
        try (JsonParser parser = FACTORY.createParser(raw)) {
            if (parser.nextToken() != JsonToken.START_OBJECT) { throw malformed("context object required"); }
            while (parser.nextToken() != JsonToken.END_OBJECT) {
                if (parser.currentToken() != JsonToken.FIELD_NAME) { throw malformed("context field required"); }
                String field = parser.currentName();
                if (!Set.of("milestone", "payload").contains(field) || !seen.add(field)) { throw malformed("exact context fields required"); }
                JsonToken token = parser.nextToken();
                if (field.equals("milestone")) {
                    if (token != JsonToken.VALUE_STRING) { throw malformed("text milestone required"); }
                    milestone = Milestone.fromWire(parser.getText());
                } else {
                    if (token != JsonToken.START_OBJECT) { throw malformed("original context payload object required"); }
                    int start = Math.toIntExact(parser.currentTokenLocation().getByteOffset());
                    parser.skipChildren(); parser.finishToken(); int end = Math.toIntExact(parser.currentLocation().getByteOffset());
                    if (start < 0 || end < start || end > raw.length) { throw malformed("context payload span invalid"); }
                    payload = ProjectionJson.object(Arrays.copyOfRange(raw, start, end), ProjectionJson.MAX_BYTES);
                }
            }
            if (!seen.equals(Set.of("milestone", "payload")) || parser.nextToken() != null
                    || milestone == null || payload == null) { throw malformed("complete exact context request required"); }
            return new Input(milestone, payload);
        } catch (G2Exception error) { throw error; }
        catch (IOException | IllegalArgumentException error) { throw malformed("invalid context request"); }
    }
    public static byte[] encodeContext(G2CallContextProducer.Context context) {
        Objects.requireNonNull(context);
        ObjectNode row = StrictJson.object(); row.put("schema", SCHEMA);
        row.set("source", StrictJson.parse(G2Wire.sourceBytes(context.source()), MAX_CONTEXT_BYTES));
        row.put("request_id", context.requestId()); row.put("payload_sha256", context.payloadSha256());
        return StrictJson.canonical(row, MAX_CONTEXT_BYTES);
    }
    public static G2CallContextProducer.Context decodeContext(byte[] raw) {
        ObjectNode row = StrictJson.object(StrictJson.parse(raw, MAX_CONTEXT_BYTES),
                Set.of("schema", "source", "request_id", "payload_sha256"));
        StrictJson.require(SCHEMA.equals(StrictJson.text(row.get("schema"))), "exact context schema required");
        return new G2CallContextProducer.Context(G2Wire.source(row.get("source")),
                StrictJson.text(row.get("request_id")), StrictJson.text(row.get("payload_sha256")));
    }
    private static G2Exception malformed(String message) { return new G2Exception(G2HttpError.Code.MALFORMED_REQUEST, message); }
}
