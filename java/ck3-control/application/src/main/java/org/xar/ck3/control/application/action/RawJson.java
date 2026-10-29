package org.xar.ck3.control.application.action;

import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.JsonParser;
import com.fasterxml.jackson.core.JsonToken;
import com.fasterxml.jackson.core.StreamReadConstraints;
import com.fasterxml.jackson.core.StreamReadFeature;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;
import java.util.HashSet;
import java.util.Set;

/** Original JSON bytes. Native defaults retain 4300 digits; explicit complete material retains its 64 MiB domain. */
public final class RawJson {
    public static final int MAXIMUM_BYTES = 64 * 1024 * 1024;
    private static final JsonFactory FACTORY = factory(4300);
    private static final JsonFactory MATERIAL_FACTORY = factory(MAXIMUM_BYTES);
    private static JsonFactory factory(int maximumNumberLength) {
        return JsonFactory.builder().enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION)
                .streamReadConstraints(StreamReadConstraints.builder().maxStringLength(MAXIMUM_BYTES)
                        .maxNumberLength(maximumNumberLength).maxNestingDepth(1000).build()).build();
    }
    private final byte[] bytes;
    private final JsonFactory factory;
    /** Original Native/public token lane; its existing 4300 digit bound is unchanged. */
    public RawJson(byte[] input) { this(input,FACTORY); }
    /** Complete Driver/auxiliary material only. Role-specific decoding and source qualification remain mandatory. */
    public static RawJson fullMaterial(byte[] input) { return new RawJson(input,MATERIAL_FACTORY); }
    private RawJson(byte[] input,JsonFactory actualFactory) {
        factory=actualFactory;
        if (input == null || input.length < 1 || input.length > MAXIMUM_BYTES) throw new IllegalArgumentException("bounded original Native token required");
        bytes = input.clone();
        try {
            StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT)
                    .onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(bytes));
            validateDocument(factory);
        } catch (IOException error) { throw new IllegalArgumentException("invalid UTF-8/duplicate/token Native JSON", error); }
    }
    public byte[] bytes() { return bytes.clone(); }
    /** Explicit complete material cannot bypass the original Native/public protocol number bound. */
    public void requireProtocolBound() {
        if(factory==FACTORY)return;
        try { validateDocument(FACTORY); }
        catch(IOException error) { throw new IllegalArgumentException("complete material exceeds the original Native token contract",error); }
    }
    private void validateDocument(JsonFactory actualFactory)throws IOException {
        try(JsonParser parser=actualFactory.createParser(bytes)) {
            if(parser.nextToken()==null)throw new IOException("JSON value required");
            validate(parser);
            if(parser.nextToken()!=null)throw new IOException("trailing Native JSON value");
        }
    }
    /** Validates object shape without exposing an untyped Java map to producers or consumers. */
    public Set<String> objectFieldNames() {
        try (JsonParser parser = factory.createParser(bytes)) {
            if (parser.nextToken() != JsonToken.START_OBJECT) throw new IllegalArgumentException("Native additional fields must be an object");
            Set<String> fields = new HashSet<>();
            while (parser.nextToken() != JsonToken.END_OBJECT) {
                fields.add(parser.currentName()); parser.nextToken(); parser.skipChildren();
            }
            return Set.copyOf(fields);
        } catch (IOException error) { throw new IllegalArgumentException("invalid Native object token", error); }
    }
    private static void validate(JsonParser parser) throws IOException {
        JsonToken token = parser.currentToken();
        if (token == JsonToken.START_OBJECT) {
            while (parser.nextToken() != JsonToken.END_OBJECT) {
                if (parser.currentToken() != JsonToken.FIELD_NAME) throw new IOException("JSON object field required");
                unicode(parser.currentName()); parser.nextToken(); validate(parser);
            }
        } else if (token == JsonToken.START_ARRAY) {
            while (parser.nextToken() != JsonToken.END_ARRAY) validate(parser);
        } else if (token == JsonToken.VALUE_STRING) unicode(parser.getText());
        else if (token == null || !token.isScalarValue()) throw new IOException("JSON scalar value required");
    }
    private static void unicode(String value) throws IOException {
        for (int index = 0; index < value.length(); index++) {
            char current = value.charAt(index);
            if (Character.isHighSurrogate(current)) {
                if (index + 1 >= value.length() || !Character.isLowSurrogate(value.charAt(++index))) throw new IOException("unpaired JSON surrogate");
            } else if (Character.isLowSurrogate(current)) throw new IOException("unpaired JSON surrogate");
        }
    }
    @Override public boolean equals(Object other) { return other instanceof RawJson raw && Arrays.equals(bytes, raw.bytes); }
    @Override public int hashCode() { return Arrays.hashCode(bytes); }
}
