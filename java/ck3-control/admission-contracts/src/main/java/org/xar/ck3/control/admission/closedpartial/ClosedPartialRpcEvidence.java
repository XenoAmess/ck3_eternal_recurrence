package org.xar.ck3.control.admission.closedpartial;

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
import java.util.Objects;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.recovery.RecoveryEvidence;

/** Existing AUTO envelopes can exceed one MiB. This distinct boundary is not a metadata cap change. */
public record ClosedPartialRpcEvidence(ExactRef reference, byte[] raw) {
    public static final int MAX_BYTES = 2 * 1024 * 1024;
    private static final ObjectMapper MAPPER = new ObjectMapper(JsonFactory.builder()
            .enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION).build())
            .enable(DeserializationFeature.USE_BIG_INTEGER_FOR_INTS)
            .enable(DeserializationFeature.USE_BIG_DECIMAL_FOR_FLOATS)
            .enable(DeserializationFeature.FAIL_ON_TRAILING_TOKENS);
    public ClosedPartialRpcEvidence {
        Objects.requireNonNull(reference); Objects.requireNonNull(raw);
        StrictJson.require(raw.length > 0 && raw.length <= MAX_BYTES && reference.bytes() == raw.length
                && reference.sha256().equals(RecoveryEvidence.sha256(raw)), "exact bounded original RPC bytes");
        raw = raw.clone();
        parse(raw);
    }
    @Override public byte[] raw() { return raw.clone(); }
    public ObjectNode object() { return parse(raw); }
    private static ObjectNode parse(byte[] raw) {
        try {
            String text = StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT)
                    .onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(raw)).toString();
            JsonNode node = MAPPER.readTree(text);
            StrictJson.require(node instanceof ObjectNode, "original RPC object required");
            return (ObjectNode) node;
        } catch (IOException error) {
            throw new ContractViolationException("strict original RPC UTF-8/JSON boundary", error);
        }
    }
}
