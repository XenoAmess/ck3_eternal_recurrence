package org.xar.ck3.control.wave2.military.prestore;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HexFormat;
import java.util.Set;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.military.countyentry.CountyEntryCodec;
import org.xar.ck3.control.wave2.military.disembark.DisembarkCodec;

/** Test-only typed byte transport to the existing original-consumer harness. */
public final class MovementConsumerTransport {
    public static final int MAX_RAW_BYTES = 32_768;
    public static final int MAX_FRAME_BYTES = 131_072;
    public enum Operation { COUNTY_NORMALIZE, MOVEMENT_NORMALIZE, PRESTORE_PROJECT, DISEMBARK_NORMALIZE, DISEMBARK_PROJECT }
    public enum Status { ACCEPTED, REJECTED }
    public record Request(int sequence, Operation operation, String inputJson, String inputSha256) {
        public Request {
            StrictJson.require(sequence >= 1 && sequence <= 4_096 && operation != null
                    && inputJson != null && inputSha256 != null, "typed finite request required");
            StrictJson.text(inputJson);
            byte[] raw = inputJson.getBytes(StandardCharsets.UTF_8);
            StrictJson.require(raw.length > 0 && raw.length <= MAX_RAW_BYTES && sha256(raw).equals(inputSha256), "raw request binding required");
        }
    }
    public record Reply(int sequence, Operation operation, String inputSha256, Status status,
                        String resultJson, String resultSha256, String errorCode) {
        public Reply {
            StrictJson.require(sequence >= 1 && sequence <= 4_096 && operation != null && status != null
                    && inputSha256 != null && inputSha256.matches("[0-9a-f]{64}"), "typed return binding required");
            if (status == Status.ACCEPTED) {
                StrictJson.require(resultJson != null && errorCode == null
                        && sha256(resultJson.getBytes(StandardCharsets.UTF_8)).equals(resultSha256), "accepted return bytes/SHA required");
            } else {
                StrictJson.require(resultJson == null && resultSha256 == null && "CONTRACT_REJECTED".equals(errorCode), "refusal has no result bytes");
            }
        }
    }
    private MovementConsumerTransport() { }

    public static Request decode(byte[] frame, int expectedSequence) {
        ObjectNode node = StrictJson.object(StrictJson.parse(frame, MAX_FRAME_BYTES),
                Set.of("sequence", "operation", "input_json", "input_sha256"));
        int sequence = (int) StrictJson.integer(node.get("sequence"), 1, 4_096);
        StrictJson.require(sequence == expectedSequence, "request sequence drift");
        Operation operation;
        try { operation = Operation.valueOf(StrictJson.text(node.get("operation"))); }
        catch (IllegalArgumentException failure) { throw new ContractViolationException("unknown movement transport operation", failure); }
        String raw = StrictJson.text(node.get("input_json"));
        byte[] input = raw.getBytes(StandardCharsets.UTF_8);
        StrictJson.require(input.length <= MAX_RAW_BYTES, "bounded original token bytes required");
        String digest = StrictJson.text(node.get("input_sha256"));
        StrictJson.require(digest.matches("[0-9a-f]{64}") && digest.equals(sha256(input)), "original input token SHA mismatch");
        return new Request(sequence, operation, raw, digest);
    }

    public static Reply evaluate(Request request) {
        byte[] input = request.inputJson().getBytes(StandardCharsets.UTF_8);
        StrictJson.require(input.length > 0 && input.length <= MAX_RAW_BYTES
                && request.inputSha256().equals(sha256(input)), "validated raw request required");
        byte[] result;
        try {
            result = switch (request.operation()) {
                case COUNTY_NORMALIZE -> county(input);
                case MOVEMENT_NORMALIZE -> CurrentMovementCodec.encode(CurrentMovementCodec.normalize(input));
                case PRESTORE_PROJECT -> PrestoreCodec.project(input);
                case DISEMBARK_NORMALIZE -> DisembarkCodec.encodeObservation(DisembarkCodec.normalize(input));
                case DISEMBARK_PROJECT -> DisembarkCodec.encodeProjection(DisembarkCodec.decodeProjectionRequest(input));
            };
        } catch (IllegalArgumentException failure) {
            return new Reply(request.sequence(), request.operation(), request.inputSha256(), Status.REJECTED,
                    null, null, "CONTRACT_REJECTED");
        }
        StrictJson.require(result.length > 0 && result.length <= MAX_RAW_BYTES, "bounded actual Java return required");
        return new Reply(request.sequence(), request.operation(), request.inputSha256(), Status.ACCEPTED,
                new String(result, StandardCharsets.UTF_8), sha256(result), null);
    }

    private static byte[] county(byte[] raw) {
        ObjectNode node = StrictJson.object(StrictJson.parse(raw), Set.of("value", "current_soldiers"));
        int current = (int) StrictJson.integer(node.get("current_soldiers"), 0, Integer.MAX_VALUE);
        return CountyEntryCodec.encode(CountyEntryCodec.decode(node.get("value"), current));
    }

    public static byte[] encode(Reply reply) {
        ObjectNode node = StrictJson.object(); node.put("sequence", reply.sequence());
        node.put("operation", reply.operation().name()); node.put("input_sha256", reply.inputSha256());
        node.put("status", reply.status().name());
        if (reply.resultJson() == null) { node.putNull("result_json"); node.putNull("result_sha256"); }
        else { node.put("result_json", reply.resultJson()); node.put("result_sha256", reply.resultSha256()); }
        if (reply.errorCode() == null) { node.putNull("error_code"); } else { node.put("error_code", reply.errorCode()); }
        return StrictJson.canonical(node, MAX_FRAME_BYTES);
    }

    public static String sha256(byte[] raw) {
        try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)); }
        catch (NoSuchAlgorithmException failure) { throw new IllegalStateException("SHA-256 unavailable", failure); }
    }
}
