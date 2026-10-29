package org.xar.ck3.control.wave2.runtime.providerchain;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.runtime.providerchain.OriginReadbackValues.Body;
import org.xar.ck3.control.wave2.runtime.providerchain.OriginReadbackValues.DllFileKey;
import org.xar.ck3.control.wave2.runtime.providerchain.OriginReadbackValues.ProcessKey;
import org.xar.ck3.control.wave2.runtime.providerchain.OriginReadbackValues.Reply;
import org.xar.ck3.control.wave2.runtime.providerchain.OriginReadbackValues.SourceEpoch;

/** Exact opaque Python-private tuple wire. OS liveness, peer/revoke and issuer checks stay with the reader. */
public final class OriginReadbackCodec {
    public static final String REPLY_KIND = "original_preload_live";
    public static final int PRIVATE_MESSAGE_MAX_BYTES = 16_384;
    private OriginReadbackCodec() { }

    public static Reply decodeReply(byte[] raw) { return parseReply(StrictJson.parse(raw, PRIVATE_MESSAGE_MAX_BYTES)); }

    public static Reply parseReply(JsonNode value) {
        ObjectNode row = StrictJson.object(value, Set.of("kind", "sequence", "nonce", "body"));
        StrictJson.require(row.get("kind").isTextual() && REPLY_KIND.equals(row.get("kind").textValue()),
                "exact original private reply kind required");
        return new Reply(positive(row.get("sequence")), StrictJson.text(row.get("nonce")), parseBody(row.get("body")));
    }

    public static Body parseBody(JsonNode value) {
        ObjectNode row = StrictJson.object(value, Set.of("epoch", "creator", "target", "file", "origin", "app"));
        return new Body(new SourceEpoch(StrictJson.text(row.get("epoch"))), new SourceSha256(StrictJson.text(row.get("creator"))),
                parseProcessKey(row.get("target")), parseFileKey(row.get("file")),
                parseProcessKey(row.get("origin")), parseProcessKey(row.get("app")));
    }

    public static ProcessKey parseProcessKey(JsonNode value) {
        StrictJson.require(value != null && value.isArray() && value.size() == 3, "exact original process key required");
        return new ProcessKey(positive(value.get(0)), StrictJson.text(value.get(1)), StrictJson.text(value.get(2)));
    }

    public static DllFileKey parseFileKey(JsonNode value) {
        StrictJson.require(value != null && value.isArray() && value.size() == 5, "exact original held file key required");
        return new DllFileKey(StrictJson.text(value.get(0)), StrictJson.text(value.get(1)), positive(value.get(2)),
                new SourceSha256(StrictJson.text(value.get(3))), StrictJson.text(value.get(4)));
    }

    public static byte[] encodeReply(Reply value) {
        StrictJson.require(value != null, "original reply values required");
        StringBuilder json = new StringBuilder("{\"kind\":\"original_preload_live\",\"sequence\":");
        json.append(value.sequence()).append(",\"nonce\":"); CreatorSourceManifest.asciiQuote(value.nonce(), json);
        Body body = value.body(); json.append(",\"body\":{\"epoch\":");
        CreatorSourceManifest.asciiQuote(body.epoch().value(), json);
        json.append(",\"creator\":"); CreatorSourceManifest.asciiQuote(body.creator().value(), json);
        json.append(",\"target\":"); appendProcess(body.target(), json);
        json.append(",\"file\":"); appendFile(body.file(), json);
        json.append(",\"origin\":"); appendProcess(body.origin(), json);
        json.append(",\"app\":"); appendProcess(body.app(), json);
        json.append("}}\n");
        byte[] raw = json.toString().getBytes(StandardCharsets.UTF_8);
        StrictJson.require(raw.length <= PRIVATE_MESSAGE_MAX_BYTES, "private message exceeds bound");
        return raw;
    }

    public static ObjectNode bodyJson(Body value) {
        StrictJson.require(value != null, "original origin body values required");
        ObjectNode row = StrictJson.object(); row.put("epoch", value.epoch().value()); row.put("creator", value.creator().value());
        row.set("target", processJson(value.target())); row.set("file", fileJson(value.file()));
        row.set("origin", processJson(value.origin())); row.set("app", processJson(value.app()));
        return row;
    }

    public static ArrayNode processJson(ProcessKey value) {
        StrictJson.require(value != null, "original process key required");
        ArrayNode row = StrictJson.object().putArray("key");
        row.add(value.pid()); row.add(value.creationFiletimeDecimal()); row.add(value.normalizedExecutable()); return row;
    }

    public static ArrayNode fileJson(DllFileKey value) {
        StrictJson.require(value != null, "original file key required");
        ArrayNode row = StrictJson.object().putArray("key");
        row.add(value.volumeSerialDecimal()); row.add(value.fileIdHex()); row.add(value.size());
        row.add(value.sha256().value()); row.add(value.normalizedFinalPath()); return row;
    }

    private static BigInteger positive(JsonNode value) {
        StrictJson.require(value != null && value.isIntegralNumber() && value.bigIntegerValue().signum() > 0,
                "exact positive original JSON integer required");
        return value.bigIntegerValue();
    }

    private static void appendProcess(ProcessKey value, StringBuilder json) {
        json.append('[').append(value.pid()).append(',');
        CreatorSourceManifest.asciiQuote(value.creationFiletimeDecimal(), json); json.append(',');
        CreatorSourceManifest.asciiQuote(value.normalizedExecutable(), json); json.append(']');
    }

    private static void appendFile(DllFileKey value, StringBuilder json) {
        json.append('['); CreatorSourceManifest.asciiQuote(value.volumeSerialDecimal(), json); json.append(',');
        CreatorSourceManifest.asciiQuote(value.fileIdHex(), json); json.append(',').append(value.size()).append(',');
        CreatorSourceManifest.asciiQuote(value.sha256().value(), json); json.append(',');
        CreatorSourceManifest.asciiQuote(value.normalizedFinalPath(), json); json.append(']');
    }
}
