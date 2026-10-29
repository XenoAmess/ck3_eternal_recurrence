package org.xar.ck3.control.g2.client;

import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.StreamReadFeature;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.net.URI;
import java.nio.ByteBuffer;
import java.nio.charset.CharacterCodingException;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.Instant;
import java.util.Base64;
import java.util.HexFormat;
import java.util.Objects;
import java.util.Optional;
import java.util.OptionalInt;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2HttpError;
import org.xar.ck3.control.g2.common.G2Wire;

/** Persistence of original HTTP bytes and measured outcomes, never a domain result re-encoding. */
public final class G2ClientOutcomeWire {
    public static final String SCHEMA = "xar.g2-client-outcome/v1";
    public static final int MAX_BYTES = ((G2Wire.MAX_RESPONSE_BYTES + 2) / 3) * 4 + 16_384;
    private static final ObjectMapper JSON = new ObjectMapper(JsonFactory.builder()
            .enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION).build())
            .enable(DeserializationFeature.FAIL_ON_TRAILING_TOKENS);
    private static final Set<String> EVIDENCE_FIELDS = Set.of("endpoint", "request_id", "started_at_utc",
            "completed_at_utc", "elapsed_nanos", "request_bytes", "request_sha256", "observed_response_bytes",
            "retained_response_bytes", "retained_response_sha256", "http_status", "response_complete", "actual_http_invoked");
    private G2ClientOutcomeWire() { }

    public static byte[] encode(G2ClientOutcome outcome) {
        Objects.requireNonNull(outcome, "outcome");
        ObjectNode row = StrictJson.object();
        row.put("schema", SCHEMA);
        switch (outcome) {
            case G2ClientOutcome.Success success -> {
                row.put("status", "SUCCESS");
                row.set("evidence", evidence(success.evaluation().evidence()));
                row.put("response_bytes_base64", Base64.getEncoder().encodeToString(success.evaluation().responseBytes()));
            }
            case G2ClientOutcome.Unavailable unavailable -> {
                row.put("status", "UNAVAILABLE");
                row.put("reason", unavailable.reason().name());
                row.put("message", unavailable.message());
                if (unavailable.failure().isPresent()) row.set("failure", failure(unavailable.failure().orElseThrow()));
                else row.putNull("failure");
            }
            case G2ClientOutcome.Failed failed -> {
                row.put("status", "FAILED");
                row.set("failure", failure(failed.failure()));
            }
        }
        try {
            byte[] raw = JSON.writeValueAsBytes(row);
            require(raw.length <= MAX_BYTES, "outcome exceeds explicit role budget");
            return raw;
        } catch (IOException error) {
            throw new IllegalArgumentException("outcome encoding failed", error);
        }
    }

    public static G2ClientOutcome decode(byte[] raw) {
        require(raw != null && raw.length > 0 && raw.length <= MAX_BYTES, "bounded nonempty outcome required");
        require(!(raw.length >= 3 && raw[0] == (byte) 0xef && raw[1] == (byte) 0xbb && raw[2] == (byte) 0xbf), "outcome BOM rejected");
        for (byte value : raw) require(value != 0, "outcome raw NUL rejected");
        try {
            String text = StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT)
                    .onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(raw)).toString();
            JsonNode value = JSON.readTree(text);
            require(value != null && value.isObject(), "outcome object required");
            require(SCHEMA.equals(StrictJson.text(value.get("schema"))), "exact outcome schema required");
            return switch (StrictJson.text(value.get("status"))) {
                case "SUCCESS" -> {
                    ObjectNode row = StrictJson.object(value, Set.of("schema", "status", "evidence", "response_bytes_base64"));
                    G2CallEvidence measured = evidence(row.get("evidence"));
                    byte[] response = original(row.get("response_bytes_base64"), measured);
                    yield new G2ClientOutcome.Success(new G2Evaluation(G2Wire.decodeResponse(response), measured, response));
                }
                case "UNAVAILABLE" -> {
                    ObjectNode row = StrictJson.object(value, Set.of("schema", "status", "reason", "message", "failure"));
                    yield new G2ClientOutcome.Unavailable(G2ClientOutcome.UnavailableReason.valueOf(StrictJson.text(row.get("reason"))),
                            StrictJson.text(row.get("message")), row.get("failure").isNull()
                                    ? Optional.empty() : Optional.of(failure(row.get("failure"))));
                }
                case "FAILED" -> {
                    ObjectNode row = StrictJson.object(value, Set.of("schema", "status", "failure"));
                    yield new G2ClientOutcome.Failed(failure(row.get("failure")));
                }
                default -> throw new IllegalArgumentException("exact outcome status required");
            };
        } catch (CharacterCodingException error) {
            throw new IllegalArgumentException("invalid outcome UTF-8", error);
        } catch (IOException error) {
            throw new IllegalArgumentException("invalid or duplicate outcome JSON", error);
        }
    }

    private static ObjectNode failure(G2ClientException failure) {
        G2ClientOutcome.requireMessage(failure.getMessage());
        ObjectNode row = StrictJson.object();
        row.put("reason", failure.reason().name());
        row.put("message", failure.getMessage());
        row.set("evidence", evidence(failure.evidence()));
        row.put("response_bytes_base64", Base64.getEncoder().encodeToString(failure.responseBytes()));
        original(row.get("response_bytes_base64"), failure.evidence());
        return row;
    }

    private static G2ClientException failure(JsonNode value) {
        ObjectNode row = StrictJson.object(value, Set.of("reason", "message", "evidence", "response_bytes_base64"));
        G2ClientException.Reason reason = G2ClientException.Reason.valueOf(StrictJson.text(row.get("reason")));
        String message = StrictJson.text(row.get("message"));
        G2ClientOutcome.requireMessage(message);
        G2CallEvidence measured = evidence(row.get("evidence"));
        byte[] response = original(row.get("response_bytes_base64"), measured);
        G2HttpError error = reason == G2ClientException.Reason.HTTP_REJECTED ? G2Wire.decodeError(response) : null;
        require(error == null || message.equals(error.message()), "verified refusal retains its original message");
        return new G2ClientException(reason, message, measured, error, response, null);
    }

    private static ObjectNode evidence(G2CallEvidence value) {
        ObjectNode row = StrictJson.object();
        row.put("endpoint", value.endpoint().toString());
        row.put("request_id", value.requestId());
        row.put("started_at_utc", value.startedAtUtc().toString());
        row.put("completed_at_utc", value.completedAtUtc().toString());
        row.put("elapsed_nanos", Long.toString(value.elapsedNanos()));
        row.put("request_bytes", Long.toString(value.requestBytes()));
        row.put("request_sha256", value.requestSha256());
        row.put("observed_response_bytes", Long.toString(value.observedResponseBytes()));
        row.put("retained_response_bytes", value.retainedResponseBytes());
        row.put("retained_response_sha256", value.retainedResponseSha256());
        if (value.httpStatus().isPresent()) row.put("http_status", value.httpStatus().orElseThrow());
        else row.putNull("http_status");
        row.put("response_complete", value.responseComplete());
        row.put("actual_http_invoked", value.actualHttpInvoked());
        return row;
    }

    private static G2CallEvidence evidence(JsonNode value) {
        ObjectNode row = StrictJson.object(value, EVIDENCE_FIELDS);
        JsonNode status = row.get("http_status");
        return new G2CallEvidence(URI.create(StrictJson.text(row.get("endpoint"))), StrictJson.text(row.get("request_id")),
                Instant.parse(StrictJson.text(row.get("started_at_utc"))), Instant.parse(StrictJson.text(row.get("completed_at_utc"))),
                decimal(row.get("elapsed_nanos")), decimal(row.get("request_bytes")), StrictJson.text(row.get("request_sha256")),
                decimal(row.get("observed_response_bytes")), Math.toIntExact(StrictJson.integer(row.get("retained_response_bytes"), 0, G2Wire.MAX_RESPONSE_BYTES)),
                StrictJson.text(row.get("retained_response_sha256")), status.isNull() ? OptionalInt.empty()
                        : OptionalInt.of(Math.toIntExact(StrictJson.integer(status, 100, 599))),
                bool(row.get("response_complete")), bool(row.get("actual_http_invoked")));
    }

    private static byte[] original(JsonNode value, G2CallEvidence evidence) {
        require(value != null && value.isTextual(), "original response base64 string required");
        String encoded = value.textValue();
        require(encoded.length() <= ((G2Wire.MAX_RESPONSE_BYTES + 2) / 3) * 4, "bounded original response required");
        byte[] raw = Base64.getDecoder().decode(encoded);
        require(Base64.getEncoder().encodeToString(raw).equals(encoded), "canonical base64 required");
        require(raw.length == evidence.retainedResponseBytes(), "retained original response length differs");
        try {
            require(HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw))
                    .equals(evidence.retainedResponseSha256()), "retained original response digest differs");
        } catch (NoSuchAlgorithmException error) {
            throw new IllegalStateException("required SHA-256 unavailable", error);
        }
        return raw;
    }

    private static long decimal(JsonNode value) {
        String text = StrictJson.text(value);
        require(text.matches("0|[1-9][0-9]{0,18}"), "canonical nonnegative decimal string required");
        return Long.parseLong(text);
    }

    private static boolean bool(JsonNode value) {
        require(value != null && value.isBoolean(), "exact outcome boolean required");
        return value.booleanValue();
    }

    private static void require(boolean condition, String message) {
        if (!condition) throw new IllegalArgumentException(message);
    }
}
