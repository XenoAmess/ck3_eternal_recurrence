package org.xar.ck3.control.g2.m7.producer;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.security.MessageDigest;
import java.time.Instant;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.List;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.governance.government.GovernmentContextCodec;

/** Finite producer differential and strict persisted-result negative regression. */
public final class M7GovernmentProducerVerification {
    private static int checks;
    private M7GovernmentProducerVerification() { }

    public static void main(String[] arguments) throws Exception {
        if (arguments.length != 3) { throw new IllegalArgumentException("old-original-golden fresh-original-golden new-actual"); }
        JsonNode original = StrictJson.parse(Files.readAllBytes(Path.of(arguments[0])));
        JsonNode fresh = StrictJson.parse(Files.readAllBytes(Path.of(arguments[1])), StrictJson.EXPLICIT_MAX_BYTES);
        require(fresh.path("source_refs_unchanged").booleanValue(), "fresh source pins unchanged");
        require(fresh.path("original_inputs_unchanged").booleanValue(), "original goal input immutable");
        require(original.path("cases").size() == 15 && original.path("wire_rejections").size() == 5,
                "all original government vectors required");
        for (JsonNode row : original.path("cases")) {
            ObjectNode request = (ObjectNode) original.path("base_request").deepCopy();
            for (JsonNode patch : row.path("request_patch")) {
                String pointer = patch.path("path").textValue(); int last = pointer.lastIndexOf('/');
                JsonNode parent = last == 0 ? request : request.at(pointer.substring(0, last));
                require(parent.isObject(), "original patch parent");
                String field = pointer.substring(last + 1).replace("~1", "/").replace("~0", "~");
                if (patch.path("op").asText().equals("remove")) { ((ObjectNode) parent).remove(field); }
                else { require(patch.path("op").asText().equals("set"), "original patch operation");
                    ((ObjectNode) parent).set(field, patch.path("value").deepCopy()); }
            }
            ObjectNode expected = (ObjectNode) row.path("expected").deepCopy();
            JsonNode observedSha = row.path("expected_observation_sha256");
            if (observedSha.isNull()) { expected.putNull("government_runtime_adapter"); }
            else {
                JsonNode observed = request.get("government_observation");
                require(observedSha.textValue().equals(sha(StrictJson.canonical(observed))), "captured native observation digest");
                expected.set("government_runtime_adapter", observed);
            }
            compareAndRoundtrip(request, expected, row.path("name").asText());
        }
        for (JsonNode row : original.path("wire_rejections")) {
            reject(() -> GovernmentContextCodec.compose(row.path("raw_request_json").textValue().getBytes(StandardCharsets.UTF_8)),
                    row.path("name").asText());
        }
        require(fresh.path("government_cases").size() == 4, "all fresh government cases");
        for (JsonNode row : fresh.path("government_cases")) {
            compareAndRoundtrip(row.path("input"), row.path("expected"), row.path("name").asText());
        }
        JsonNode feudal = fresh.path("government_cases").get(0).path("expected");
        JsonNode clan = fresh.path("government_cases").get(1).path("expected");
        require(!feudal.path("government_key").equals(clan.path("government_key")), "government keys remain distinct");
        require(feudal.path("adapter_family").equals(clan.path("adapter_family")), "same family does not erase a government key");
        var nativePlayerContext = GovernmentContextCodec.decodeContext(bytes(feudal));
        java.math.BigInteger nativePlayer = feudal.get("government_runtime_adapter").get("player_character_id").bigIntegerValue();
        GovernmentContextCodec.requireCurrentPlayerBinding(nativePlayerContext, nativePlayer); checks++;
        reject(() -> GovernmentContextCodec.requireCurrentPlayerBinding(nativePlayerContext, nativePlayer.add(java.math.BigInteger.ONE)),
                "consumer binds the actual native player");
        var mismatchedGoal = GovernmentContextCodec.decodeContext(bytes(fresh.path("government_cases").get(3).path("expected")));
        reject(() -> GovernmentContextCodec.requireCurrentPlayerBinding(mismatchedGoal, java.math.BigInteger.valueOf(100)),
                "valid mismatch diagnostic is not another player's consumed profile");
        var absentProfile = GovernmentContextCodec.decodeContext(bytes(fresh.path("government_cases").get(2).path("expected")));
        GovernmentContextCodec.requireCurrentPlayerBinding(absentProfile, nativePlayer); checks++;
        ObjectNode valid = (ObjectNode) StrictJson.parse(GovernmentContextCodec.compose(bytes(original.path("base_request"))));
        List<String> fields = new ArrayList<>(); valid.fieldNames().forEachRemaining(fields::add);
        require(fields.size() == 16, "complete result field inventory");
        for (String field : fields) {
            ObjectNode missing = valid.deepCopy(); missing.remove(field);
            reject(() -> GovernmentContextCodec.decodeContext(bytes(missing)), "missing persisted " + field);
        }
        for (String field : List.of("schema", "schema_version", "status", "query_permitted", "identity_observation_ready",
                "core_adapter_ready", "ordinary_goal_context_ready", "campaign_id", "current_character_id", "snapshot_revision",
                "date_raw", "government_key", "adapter_family", "adapter_status", "government_runtime_adapter")) {
            ObjectNode nulled = valid.deepCopy(); nulled.putNull(field);
            reject(() -> GovernmentContextCodec.decodeContext(bytes(nulled)), "null persisted known " + field);
        }
        ObjectNode unknown = valid.deepCopy(); unknown.put("fresh_readiness_issued", true);
        reject(() -> GovernmentContextCodec.decodeContext(bytes(unknown)), "unknown result field");
        for (String field : List.of("schema_version", "current_character_id", "snapshot_revision", "date_raw")) {
            for (String token : List.of("true", "1.0", "\"1\"")) {
                byte[] wrong = bytesWithRawTopLevelToken(valid, field, token);
                if (token.equals("1.0")) {
                    require(StrictJson.parse(wrong).get(field).isFloatingPointNumber(), "raw float token retained " + field);
                }
                reject(() -> GovernmentContextCodec.decodeContext(wrong), "integer token " + field + token);
            }
        }
        for (String field : Set.of("government_key", "adapter_family", "adapter_status", "status")) {
            ObjectNode changed = valid.deepCopy(); changed.put(field, "fixture-mismatch");
            reject(() -> GovernmentContextCodec.decodeContext(bytes(changed)), "result/native mismatch " + field);
        }
        for (String field : List.of("identity_observation_ready", "core_adapter_ready", "ordinary_goal_context_ready")) {
            ObjectNode changed = valid.deepCopy(); changed.put(field, false);
            reject(() -> GovernmentContextCodec.decodeContext(bytes(changed)), "readiness mismatch " + field);
            ObjectNode wrongToken = valid.deepCopy(); wrongToken.put(field, 1);
            reject(() -> GovernmentContextCodec.decodeContext(bytes(wrongToken)), "readiness integer " + field);
        }
        ObjectNode revision = valid.deepCopy(); revision.put("snapshot_revision", 99);
        reject(() -> GovernmentContextCodec.decodeContext(bytes(revision)), "persisted native revision binding");
        ObjectNode date = valid.deepCopy(); date.put("date_raw", 99);
        reject(() -> GovernmentContextCodec.decodeContext(bytes(date)), "persisted native date binding");
        for (String field : List.of("schema_version", "snapshot_revision", "player_character_id", "date_raw")) {
            ObjectNode changed = valid.deepCopy(); ObjectNode observed = (ObjectNode) changed.get("government_runtime_adapter");
            observed.put(field, observed.get(field).doubleValue()); byte[] originalFloat = bytes(changed);
            reject(() -> GovernmentContextCodec.decodeContext(originalFloat), "retained native float " + field);
            JsonNode nested = StrictJson.parse(originalFloat);
            reject(() -> GovernmentContextCodec.parseContext(nested), "parsed retained native float " + field);
        }
        ObjectNode featureCount = valid.deepCopy();
        ((ObjectNode) featureCount.get("government_runtime_adapter").get("effective_feature_flags")).put("native_count", 44.0);
        reject(() -> GovernmentContextCodec.parseContext(StrictJson.parse(bytes(featureCount))), "parsed retained feature count float");
        ObjectNode featureIndex = valid.deepCopy();
        ((ObjectNode) featureIndex.get("government_runtime_adapter").get("effective_feature_flags").get("items").get(0)).put("native_index", 0.0);
        reject(() -> GovernmentContextCodec.parseContext(StrictJson.parse(bytes(featureIndex))), "parsed retained feature index float");
        String text = valid.toString();
        reject(() -> GovernmentContextCodec.decodeContext((text + "{}").getBytes(StandardCharsets.UTF_8)), "trailing result JSON");
        reject(() -> GovernmentContextCodec.decodeContext((text.substring(0, text.length() - 1) + ",\"schema_version\":1}").getBytes(StandardCharsets.UTF_8)), "duplicate result field");
        reject(() -> GovernmentContextCodec.decodeContext(new byte[] {(byte) 0xff}), "invalid result UTF8");
        ObjectNode actual = StrictJson.object();
        actual.put("schema", "xar.g2-m7-government-producer-verification/v1");
        actual.put("machine_id", fresh.path("machine_id").textValue()); actual.put("observed_at_utc", Instant.now().toString());
        actual.put("status", "PASS"); actual.put("checks", checks); actual.put("original_government_vectors", 15);
        actual.put("original_raw_token_rejections", 5); actual.put("fresh_government_vectors", 4);
        actual.put("fresh_goal_vectors_available", fresh.path("goal_cases").size());
        actual.put("goal_domain_differential_executed_by_this_class", false);
        actual.put("game_calls", 0); actual.put("true_driver_or_save_body_reads", 0);
        actual.put("qualification_scope", "pure original producer differential and typed persistence; no native/action/recovery/business qualification");
        Files.write(Path.of(arguments[2]), StrictJson.canonical(actual), StandardOpenOption.CREATE_NEW);
        System.out.println("M7 government producer and persisted-result checks PASS: " + checks);
    }

    private static void compareAndRoundtrip(JsonNode request, JsonNode expected, String label) {
        String before = request.toString();
        byte[] produced = GovernmentContextCodec.compose(bytes(request));
        require(StrictJson.parse(produced).equals(expected), "actual original producer differential " + label);
        byte[] restored = GovernmentContextCodec.encode(GovernmentContextCodec.decodeContext(produced));
        require(StrictJson.parse(restored).equals(expected), "typed persisted result roundtrip " + label);
        byte[] repeated = GovernmentContextCodec.encode(GovernmentContextCodec.decodeContext(restored));
        require(java.util.Arrays.equals(restored, repeated), "stable result bytes " + label);
        require(before.equals(request.toString()), "producer input unchanged " + label);
    }
    private static void reject(Runnable call, String label) {
        try { call.run(); } catch (IllegalArgumentException expected) { checks++; return; }
        throw new IllegalStateException("expected actual rejection: " + label);
    }
    private static void require(boolean condition, String label) {
        if (!condition) { throw new IllegalStateException(label); } checks++;
    }
    private static byte[] bytes(JsonNode value) { return value.toString().getBytes(StandardCharsets.UTF_8); }
    /** Build the wire bytes directly: parsing 1.0 and reserializing its DecimalNode can erase its token type. */
    private static byte[] bytesWithRawTopLevelToken(ObjectNode value, String field, String rawToken) {
        if (!value.has(field)) { throw new IllegalArgumentException("missing field for raw-token fixture"); }
        StringBuilder wire = new StringBuilder("{");
        var entries = value.properties().iterator();
        boolean first = true;
        while (entries.hasNext()) {
            var entry = entries.next();
            if (!first) { wire.append(','); }
            first = false;
            wire.append(com.fasterxml.jackson.databind.node.TextNode.valueOf(entry.getKey()).toString()).append(':');
            wire.append(entry.getKey().equals(field) ? rawToken : entry.getValue().toString());
        }
        return wire.append('}').toString().getBytes(StandardCharsets.UTF_8);
    }
    private static String sha(byte[] raw) throws Exception {
        return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw));
    }
}
