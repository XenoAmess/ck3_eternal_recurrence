package org.xar.ck3.control.contracts.projection;

import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.JsonParser;
import com.fasterxml.jackson.core.JsonToken;
import com.fasterxml.jackson.core.StreamReadFeature;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.charset.CharacterCodingException;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;

/** Validated original JSON bytes. Domain codecs, rather than this transport, interpret numbers. */
public final class ProjectionJson {
    public static final int MAX_BYTES = 8 * 1024 * 1024;
    static final JsonFactory FACTORY = JsonFactory.builder().enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION).build();
    private final byte[] raw;
    private final boolean object;
    private ProjectionJson(byte[] raw, boolean object) { this.raw = raw.clone(); this.object = object; }

    public static ProjectionJson object(byte[] raw, int maximumBytes) { return validate(raw, maximumBytes, true); }
    public static ProjectionJson value(byte[] raw, int maximumBytes) { return validate(raw, maximumBytes, false); }
    public byte[] bytes() { return raw.clone(); }
    public int size() { return raw.length; }
    public boolean isObject() { return object; }

    static void requireUtf8(byte[] raw) {
        if (raw.length >= 3 && raw[0] == (byte) 0xef && raw[1] == (byte) 0xbb && raw[2] == (byte) 0xbf) {
            throw invalid("UTF-8 BOM is not permitted in projection JSON values");
        }
        // A literal NUL is invalid JSON. Reject it before Jackson's byte parser can auto-detect UTF-16/32.
        for (byte value : raw) {
            if (value == 0) { throw invalid("raw NUL is not permitted in UTF-8 projection JSON"); }
        }
        try {
            StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT)
                    .onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(raw));
        } catch (CharacterCodingException error) { throw invalid("invalid projection UTF-8"); }
    }

    private static ProjectionJson validate(byte[] raw, int maximumBytes, boolean object) {
        if (maximumBytes < 1 || maximumBytes > MAX_BYTES || raw == null || raw.length == 0 || raw.length > maximumBytes) {
            throw invalid("projection JSON exceeds explicit role budget");
        }
        requireUtf8(raw);
        try (JsonParser parser = FACTORY.createParser(raw)) {
            JsonToken first = parser.nextToken();
            if (first == null || (object && first != JsonToken.START_OBJECT)) { throw invalid("projection object required"); }
            validateString(parser);
            if (first.isStructStart()) {
                int depth = 1;
                while (depth > 0) {
                    JsonToken token = parser.nextToken();
                    if (token == null) { throw invalid("incomplete projection JSON"); }
                    validateString(parser);
                    if (token.isStructStart()) { depth++; }
                    else if (token.isStructEnd()) { depth--; }
                }
            }
            if (parser.nextToken() != null) { throw invalid("trailing projection JSON"); }
            return new ProjectionJson(raw, first == JsonToken.START_OBJECT);
        } catch (IOException error) { throw invalid("invalid or duplicate projection JSON"); }
    }

    private static void validateString(JsonParser parser) throws IOException {
        if (parser.currentToken() == JsonToken.FIELD_NAME || parser.currentToken() == JsonToken.VALUE_STRING) {
            String text = parser.getText();
            for (int i = 0; i < text.length(); i++) {
                char c = text.charAt(i);
                if (Character.isHighSurrogate(c)) {
                    if (i + 1 >= text.length() || !Character.isLowSurrogate(text.charAt(++i))) { throw invalid("unpaired projection Unicode surrogate"); }
                } else if (Character.isLowSurrogate(c)) { throw invalid("unpaired projection Unicode surrogate"); }
            }
        }
    }

    static ProjectionProtocolException invalid(String message) {
        return new ProjectionProtocolException(ProjectionError.Code.INVALID_ENVELOPE, message);
    }
}
