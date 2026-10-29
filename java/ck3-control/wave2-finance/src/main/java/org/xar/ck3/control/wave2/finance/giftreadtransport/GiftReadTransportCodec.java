package org.xar.ck3.control.wave2.finance.giftreadtransport;

import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.StreamReadConstraints;
import com.fasterxml.jackson.core.StreamReadFeature;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.cfg.JsonNodeFeature;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigDecimal;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.util.Set;
import java.util.TreeSet;
import java.util.function.Function;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.finance.factioncandidate.FactionCandidateCodec;
import org.xar.ck3.control.wave2.finance.giftreadtransport.GiftReadTransport.Binding;
import org.xar.ck3.control.wave2.finance.giftreadtransport.GiftReadTransport.Candidate;
import org.xar.ck3.control.wave2.finance.giftreadtransport.GiftReadTransport.Command;
import org.xar.ck3.control.wave2.finance.giftreadtransport.GiftReadTransport.Diagnostics;
import org.xar.ck3.control.wave2.finance.giftreadtransport.GiftReadTransport.Envelope;
import org.xar.ck3.control.wave2.finance.giftreadtransport.GiftReadTransport.ObjectDocument;
import org.xar.ck3.control.wave2.finance.giftreadtransport.GiftReadTransport.OpaqueValue;
import org.xar.ck3.control.wave2.finance.giftreadtransport.GiftReadTransport.Presence;
import org.xar.ck3.control.wave2.finance.giftreadtransport.GiftReadTransport.Read;
import org.xar.ck3.control.wave2.finance.giftreadtransport.GiftReadTransport.Request;
import org.xar.ck3.control.wave2.finance.giftreadtransport.GiftReadTransport.Result;
import org.xar.ck3.control.wave2.finance.giftreadtransport.GiftReadTransport.Snapshot;
import org.xar.ck3.control.wave2.finance.giftreadtransport.GiftReadTransport.Timeout;

/** Typed codec for existing owned-port data. No pipe, Game access or source-qualification shortcut. */
public final class GiftReadTransportCodec {
    public static final String SCHEMA = "xar.gift-read-transport-input.v1";
    public static final int MAX_SDK_CONTAINER_BYTES = 1_048_576;
    private static final ObjectMapper JSON = new ObjectMapper(JsonFactory.builder()
            .enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION)
            .streamReadConstraints(StreamReadConstraints.builder().maxNestingDepth(64)
                    .maxStringLength(MAX_SDK_CONTAINER_BYTES).maxNumberLength(1024).build()).build())
            .enable(DeserializationFeature.USE_BIG_INTEGER_FOR_INTS)
            .enable(DeserializationFeature.USE_BIG_DECIMAL_FOR_FLOATS)
            .enable(DeserializationFeature.FAIL_ON_TRAILING_TOKENS)
            .configure(JsonNodeFeature.STRIP_TRAILING_BIGDECIMAL_ZEROES, false);
    private GiftReadTransportCodec() { }

    public static Request decodeRequest(byte[] bytes) {
        ObjectNode input = StrictJson.object(parse(bytes), Set.of("schema", "snapshot", "root", "minimum_gold_reserve_raw", "timeout_seconds"));
        StrictJson.require(SCHEMA.equals(text(input.get("schema"))), "gift read schema required");
        return new Request(decodeSnapshot(encodeObject(input.get("snapshot"))),
                FactionCandidateCodec.decodeRootProjection(encodeObject(input.get("root"))),
                integer(input.get("minimum_gold_reserve_raw")), timeout(input.get("timeout_seconds")));
    }

    public static Snapshot decodeSnapshot(byte[] bytes) {
        JsonNode node = object(parse(bytes)); JsonNode actor = objectPart(node, "played_character");
        Binding binding = new Binding(read(node, "snapshot_id", GiftReadTransportCodec::text),
                read(node, "revision", GiftReadTransportCodec::integer), read(node, "native_revision", GiftReadTransportCodec::integer),
                read(node, "date_raw", GiftReadTransportCodec::integer), read(node, "paused", GiftReadTransportCodec::bool),
                read(node, "map_ready", GiftReadTransportCodec::bool), read(actor, "character_id", GiftReadTransportCodec::integer),
                read(actor, "alive", GiftReadTransportCodec::bool), read(node, "active_event", GiftReadTransportCodec::opaque),
                read(node, "pending_character_interaction", GiftReadTransportCodec::opaque));
        return new Snapshot(new ObjectDocument(encodeObject(node)), binding,
                read(node, "one_life_terminal_reason", GiftReadTransportCodec::opaque));
    }

    public static Diagnostics decodeDiagnostics(byte[] bytes) {
        JsonNode node = object(parse(bytes));
        JsonNode route = objectPart(objectPart(node, "last_heartbeat"), "g2_faction_gift_mitigation_async_glue_v1");
        return new Diagnostics(read(route, "private_build", GiftReadTransportCodec::bool));
    }

    public static Envelope decodeEnvelope(byte[] bytes) {
        JsonNode node = object(parse(bytes));
        return new Envelope(read(node, "type", GiftReadTransportCodec::text),
                read(node, "protocol_version", GiftReadTransportCodec::integer),
                read(node, "request_id", GiftReadTransportCodec::text), read(node, "ok", GiftReadTransportCodec::bool),
                read(node, "result", value -> new ObjectDocument(encodeObject(value))),
                read(node, "error", value -> value.isTextual() ? text(value) : opaque(value).canonicalJson()));
    }

    public static byte[] encodeCommand(Command command) {
        ObjectNode result = StrictJson.object(); result.put("type", "execute_step"); result.put("protocol_version", 1);
        result.put("request_id", command.requestId().value()); result.put("step", "private-query-faction-gift-member-v1");
        result.put("expected_revision", command.expectedRevision()); result.put("expected_date_raw", command.expectedDateRaw());
        result.put("expected_player_character_id", command.expectedPlayerCharacterId());
        return StrictJson.canonical(result, 16_384);
    }

    public static byte[] encodeResult(Result result) {
        if (result instanceof Candidate candidate) { return FactionCandidateCodec.encodeCandidateResult(candidate.candidate()); }
        if (result instanceof GiftReadTransport.PrivateRouteOff) {
            ObjectNode node = StrictJson.object(); node.put("status", "private_route_off");
            node.put("public_capability_advertised", false); node.put("gift_submission_enabled", false);
            return StrictJson.canonical(node);
        }
        throw new IllegalArgumentException("typed query result required");
    }

    /** Shared SDK/application object projection; preserves float token domain for downstream strict readers. */
    public static byte[] encodeObjectProjection(JsonNode node) { return encodeObject(node); }

    private static Timeout timeout(JsonNode node) {
        StrictJson.require(node != null && node.isNumber(), "timeout must be positive numeric seconds, never boolean/string");
        BigDecimal seconds = node.isIntegralNumber() ? new BigDecimal(node.bigIntegerValue()) : node.decimalValue();
        return new Timeout(seconds);
    }
    private static JsonNode parse(byte[] bytes) {
        StrictJson.require(bytes != null && bytes.length > 0 && bytes.length <= MAX_SDK_CONTAINER_BYTES, "bounded SDK JSON required");
        try {
            String utf8 = StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT)
                    .onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(bytes)).toString();
            JsonNode result = JSON.readTree(utf8); StrictJson.require(result != null, "JSON value required"); return result;
        } catch (IOException error) { throw new ContractViolationException("invalid UTF-8/duplicate/trailing SDK JSON", error); }
    }
    private static byte[] encodeObject(JsonNode node) {
        object(node);
        byte[] bytes = sorted(node).getBytes(StandardCharsets.UTF_8);
        StrictJson.require(bytes.length <= MAX_SDK_CONTAINER_BYTES, "SDK projection exceeds its bound"); return bytes;
    }
    private static JsonNode object(JsonNode node) {
        StrictJson.require(node != null && node.isObject(), "SDK object required"); return node;
    }
    private static JsonNode objectPart(JsonNode node, String name) {
        if (node == null) { return null; } JsonNode value = node.get(name);
        return value != null && value.isObject() ? value : null;
    }
    private static BigInteger integer(JsonNode node) {
        StrictJson.require(node != null && node.isIntegralNumber(), "exact JSON integer token required; bool/float/string rejected");
        return node.bigIntegerValue();
    }
    private static Boolean bool(JsonNode node) {
        StrictJson.require(node != null && node.isBoolean(), "actual boolean token required"); return node.booleanValue();
    }
    private static String text(JsonNode node) {
        StrictJson.require(node != null && node.isTextual(), "string token required");
        if (!node.textValue().isEmpty()) { StrictJson.text(node.textValue()); } return node.textValue();
    }
    private static <T> Read<T> read(JsonNode node, String name, Function<JsonNode, T> parser) {
        JsonNode value = node == null ? null : node.get(name);
        return value == null ? Read.missing() : value.isNull() ? Read.nil() : Read.of(parser.apply(value));
    }
    private static OpaqueValue opaque(JsonNode node) { return new OpaqueValue(sorted(node)); }
    private static String sorted(JsonNode node) {
        if (node.isObject()) {
            TreeSet<String> keys = new TreeSet<>(); node.properties().forEach(entry -> keys.add(entry.getKey()));
            StringBuilder out = new StringBuilder("{"); boolean first = true;
            for (String key : keys) {
                if (!first) { out.append(','); } first = false;
                out.append(JSON.getNodeFactory().textNode(key)).append(':').append(sorted(node.get(key)));
            }
            return out.append('}').toString();
        }
        if (node.isArray()) {
            StringBuilder out = new StringBuilder("["); boolean first = true;
            for (JsonNode item : node) { if (!first) { out.append(','); } first = false; out.append(sorted(item)); }
            return out.append(']').toString();
        }
        if (node.isFloatingPointNumber()) {
            String number = node.decimalValue().toString();
            // Even exponent-zero floating tokens must not become integer tokens in the next consumer.
            return number.indexOf('.') >= 0 || number.indexOf('e') >= 0 || number.indexOf('E') >= 0 ? number : number + ".0";
        }
        return node.toString();
    }
}
