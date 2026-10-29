package org.xar.ck3.control.contracts.semantic;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.JsonNodeFactory;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.HashSet;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;

/** Sole semantic wire contract. Unavailable native metadata may carry signed/absent actor values; no Game qualification. */
public final class NativePlayerEventTraitMembership {
    public static final String SCHEMA = "xar.ck3.player-event-trait-membership/v1";
    public static final String GAME_VERSION = "1.20.0.4";
    public static final String EXECUTABLE_SHA256 = "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
    private static final Set<String> FIELDS = Set.of("schema", "game_version", "executable_sha256", "status",
            "snapshot_revision", "date_raw", "played_character_id", "traits", "unavailable_reason");
    private static final Set<String> TRAITS = Set.of("lifestyle_poet", "journaller");
    private NativePlayerEventTraitMembership() { }

    /** Retain original positive integer DATA and actual native signed-int32 unavailable metadata, including absent -1. */
    public record Frame(BigInteger nativeRevision, BigInteger dateRaw, BigInteger playedCharacterId) {
        public Frame {
            Objects.requireNonNull(nativeRevision); Objects.requireNonNull(dateRaw); Objects.requireNonNull(playedCharacterId);
            need(nativeRevision.signum() > 0, "positive original trait native revision required");
            need(playedCharacterId.signum() > 0 || playedCharacterId.compareTo(BigInteger.valueOf(Integer.MIN_VALUE)) >= 0,
                    "original positive trait actor or signed-int32 unavailable actor metadata required");
        }
    }
    public record Traits(boolean lifestylePoet, boolean journaller) { }
    public sealed interface Observation permits Available, Unavailable { Frame frame(); }
    public record Available(Frame frame, Traits traits) implements Observation {
        public Available {
            Objects.requireNonNull(frame); Objects.requireNonNull(traits);
            need(frame.playedCharacterId().signum() > 0, "available traits require the independently positive actor");
        }
    }
    public record Unavailable(Frame frame, String reason) implements Observation {
        public Unavailable {
            Objects.requireNonNull(frame);
            need(reason != null && !reason.isEmpty(), "nonempty original trait unavailable reason required");
        }
    }

    /** Original general positive DATA remains unchanged; only unavailable metadata admits native nonpositive signed-int32 values. */
    public static Observation read(JsonNode original, BigInteger expectedCharacterId,
            BigInteger expectedNativeRevision, JsonNode expectedDateRaw) {
        Objects.requireNonNull(original); Objects.requireNonNull(expectedCharacterId);
        Objects.requireNonNull(expectedNativeRevision); Objects.requireNonNull(expectedDateRaw);
        ObjectNode row = object(original); fields(row, FIELDS);
        equalText(row.get("schema"), SCHEMA); equalText(row.get("game_version"), GAME_VERSION);
        equalText(row.get("executable_sha256"), EXECUTABLE_SHA256);
        var expected = new Frame(expectedNativeRevision, integer(expectedDateRaw), expectedCharacterId);
        var actual = new Frame(integer(row.get("snapshot_revision")), integer(row.get("date_raw")),
                integer(row.get("played_character_id")));
        need(actual.equals(expected), "original event-trait current-player binding differs");
        JsonNode status = row.get("status");
        if (isText(status, "available")) {
            need(row.get("unavailable_reason").isNull(), "available original trait reason must be null");
            ObjectNode values = object(row.get("traits")); fields(values, TRAITS);
            return new Available(actual, new Traits(bool(values.get("lifestyle_poet")), bool(values.get("journaller"))));
        }
        need(isText(status, "unavailable") && row.get("traits").isNull(),
                "unavailable original traits require explicit null values");
        JsonNode reason = row.get("unavailable_reason");
        need(reason.isTextual() && !reason.textValue().isEmpty(), "nonempty original trait unavailable reason required");
        return new Unavailable(actual, reason.textValue());
    }

    public static ObjectNode normalize(JsonNode original, BigInteger expectedCharacterId,
            BigInteger expectedNativeRevision, JsonNode expectedDateRaw) {
        return toJson(read(original, expectedCharacterId, expectedNativeRevision, expectedDateRaw));
    }

    /** One serializer shared by receive normalization and the existing higher bounded business codec. */
    public static ObjectNode toJson(Observation observation) {
        Objects.requireNonNull(observation);
        ObjectNode row = JsonNodeFactory.instance.objectNode();
        row.put("schema", SCHEMA).put("game_version", GAME_VERSION).put("executable_sha256", EXECUTABLE_SHA256)
                .put("snapshot_revision", observation.frame().nativeRevision()).put("date_raw", observation.frame().dateRaw())
                .put("played_character_id", observation.frame().playedCharacterId());
        if (observation instanceof Available available) {
            row.put("status", "available").putNull("unavailable_reason");
            row.putObject("traits").put("lifestyle_poet", available.traits().lifestylePoet())
                    .put("journaller", available.traits().journaller());
        } else if (observation instanceof Unavailable unavailable) {
            row.put("status", "unavailable").putNull("traits").put("unavailable_reason", unavailable.reason());
        }
        return row;
    }

    private static ObjectNode object(JsonNode value) {
        need(value instanceof ObjectNode, "original event-trait JSON object required"); return (ObjectNode) value;
    }
    private static BigInteger integer(JsonNode value) {
        need(value != null && value.isIntegralNumber(), "original trait integer token required; no bool/float/string");
        return value.bigIntegerValue();
    }
    private static boolean bool(JsonNode value) {
        need(value != null && value.isBoolean(), "original trait boolean token required"); return value.booleanValue();
    }
    private static void fields(ObjectNode value, Set<String> expected) {
        Set<String> actual = new HashSet<>(); value.fieldNames().forEachRemaining(actual::add);
        need(actual.equals(expected), "exact original trait fields required");
    }
    private static boolean isText(JsonNode value, String expected) {
        return value != null && value.isTextual() && expected.equals(value.textValue());
    }
    private static void equalText(JsonNode value, String expected) { need(isText(value, expected), "original trait schema/build identity differs"); }
    private static void need(boolean value, String message) { StrictJson.require(value, message); }
}
