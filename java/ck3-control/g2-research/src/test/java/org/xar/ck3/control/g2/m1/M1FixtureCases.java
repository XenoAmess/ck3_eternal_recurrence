package org.xar.ck3.control.g2.m1;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.Instant;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.g2.common.G2Request;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.common.Milestone;
import org.xar.ck3.control.wave2.finance.rawcash.SdkProjectionJson;

/** Original producer captures shared by the finite exporter and its regression tests. */
public final class M1FixtureCases {
    public record Fixture(M1Operation operation, G2Source source, ProjectionJson input, ProjectionJson expected) {
        public Fixture {
            Objects.requireNonNull(operation); Objects.requireNonNull(source);
            Objects.requireNonNull(input); Objects.requireNonNull(expected);
        }
        public G2Request request() {
            return new G2Request("m1-fixture-" + operation.wire(), Milestone.M1, source,
                    operation.payload(input.bytes()));
        }
    }
    private record Corpus(JsonNode json, G2Source source) { }
    private M1FixtureCases() { }

    public static List<Fixture> all() throws IOException {
        Corpus realm = corpus("realm-membership.json", "21fd8f8bd03a822add8bb67321549e8b35e50cefcd547042e483bc7c76dbb253");
        JsonNode realmInput = realm.json().path("bases").path("first");
        JsonNode feedback = named(realm.json(), "name", "complete-first-observation").get("expected");
        Corpus month = corpus("monthly-observation.json", "53cdbca5439bdc3911f57908c018029e6c31caab4812b5fa070b345003ab78ae");
        JsonNode baseline = named(month.json(), "id", "sample-baseline");
        byte[] savedRaw = resource("saved-membership.jsonl", "da6297b603c7f2388b350eb8214a66911ba7761fff642d5e3a3de3145bea9e96");
        List<String> savedLines = new String(savedRaw, StandardCharsets.UTF_8).lines().toList();
        JsonNode savedHeader = parse(utf8(savedLines.getFirst()));
        JsonNode saved = parse(utf8(savedLines.get(1)));
        G2Source savedSource = source("saved-membership.jsonl", savedRaw, savedHeader.path("machine_id").textValue(),
                savedHeader.path("observed_at_utc").textValue(),
                savedHeader.path("source_sha256").path("ck3_autonomous_player/src/xar_autoplayer/campaign_score_save_reader.py").textValue());
        Corpus summary = corpus("dated-summary.json", "7bc6d62177f58fe3f7763d302cfab9d739f7821ae37937485bd088d5622418fc");
        JsonNode currentLoss = named(summary.json(), "id", "current-loss");
        List<Fixture> fixtures = new ArrayList<>();
        fixtures.add(fixture(M1Operation.REALM_FEEDBACK, realm.source(), write(realmInput), write(feedback)));
        ObjectNode nativePair = StrictJson.object();
        nativePair.set("cached", feedback.get("observation")); nativePair.set("current", feedback.get("observation"));
        fixtures.add(fixture(M1Operation.NATIVE_CACHE, realm.source(), write(nativePair),
                utf8("{\"status\":\"current\",\"reason\":null}")));
        ObjectNode difference = StrictJson.object(); difference.putNull("previous");
        difference.set("observation", feedback.get("observation"));
        fixtures.add(fixture(M1Operation.NATIVE_DIFFERENCE, realm.source(), write(difference),
                utf8("{\"status\":\"unavailable\",\"lost_county_title_ids\":null,\"gained_county_title_ids\":null,\"unavailable_reason\":\"previous_complete_observation_missing\"}")));
        fixtures.add(fixture(M1Operation.MONTHLY_OBSERVATION, month.source(), write(baseline.get("request")),
                write(baseline.path("expected").get("value"))));
        ObjectNode monthlyPair = StrictJson.object();
        monthlyPair.set("cached", baseline.get("request")); monthlyPair.set("current", baseline.get("request"));
        fixtures.add(fixture(M1Operation.MONTHLY_CACHE, month.source(), write(monthlyPair),
                utf8("{\"status\":\"current\",\"reason\":null}")));
        byte[] savedInput = utf8(saved.path("input_json").textValue());
        fixtures.add(fixture(M1Operation.SAVED_MEMBERSHIP, savedSource, savedInput, write(saved.get("expected"))));
        ObjectNode savedPair = StrictJson.object(); savedPair.set("previous", parse(savedInput));
        savedPair.set("current", parse(savedInput)); savedPair.put("scope", "realm");
        fixtures.add(fixture(M1Operation.SAVED_DIFFERENCE, savedSource, write(savedPair),
                utf8("{\"scope\":\"realm\",\"cause\":null,\"status\":\"unavailable\",\"unavailable_reason\":\"DATE_NOT_STRICTLY_EARLIER\",\"lost_title_ids\":null,\"gained_title_ids\":null}")));
        fixtures.add(fixture(M1Operation.DATED_SUMMARY, summary.source(), write(currentLoss.get("request")),
                write(currentLoss.path("expected").get("value"))));
        return List.copyOf(fixtures);
    }

    /** All responses must traverse their production typed consumer before export. */
    public static void consume(M1Operation operation, byte[] raw) {
        switch (operation) {
            case SAVED_MEMBERSHIP -> M1ResultConsumers.savedMembership(raw);
            case REALM_FEEDBACK -> M1ResultConsumers.realmFeedback(raw);
            case MONTHLY_OBSERVATION -> M1ResultConsumers.monthlyObservation(raw);
            case NATIVE_DIFFERENCE -> M1ResultConsumers.nativeDifference(raw);
            case NATIVE_CACHE, MONTHLY_CACHE -> M1ResultConsumers.cache(raw);
            case SAVED_DIFFERENCE -> M1ResultConsumers.savedDifference(raw);
            case DATED_SUMMARY -> M1ResultConsumers.datedSummary(raw);
        }
    }
    private static Fixture fixture(M1Operation operation, G2Source source, byte[] input, byte[] expected) {
        return new Fixture(operation, source, ProjectionJson.object(input, M1Research.MAX_BYTES),
                ProjectionJson.value(expected, M1Research.MAX_BYTES));
    }
    private static Corpus corpus(String name, String sha256) throws IOException {
        byte[] raw = resource(name, sha256); JsonNode json = parse(raw);
        boolean realm = name.equals("realm-membership.json");
        JsonNode metadata = realm ? json.path("capture") : json;
        String producer = realm ? producerSha(json, "ck3_autonomous_player/src/xar_autoplayer/realm_membership_feedback_v1.py")
                : json.path("producer").path("sha256").textValue();
        return new Corpus(json, source(name, raw, metadata.path("machine_id").textValue(),
                metadata.path("observed_at_utc").textValue(), producer));
    }
    private static String producerSha(JsonNode corpus, String path) throws IOException {
        for (JsonNode row : corpus.path("sources")) {
            if (path.equals(row.path("path").textValue())) { return row.path("sha256").textValue(); }
        }
        throw new IOException("original producer source pin missing: " + path);
    }
    private static G2Source source(String name, byte[] raw, String machine, String observed, String producerSha) {
        StrictJson.require(producerSha != null && producerSha.matches("[0-9a-f]{64}"), "actual original producer pin required");
        // These captures use original synthetic DTOs. Their build identity names the pure producer only.
        return new G2Source(machine, Instant.parse(observed).toString(), "pure-producer:" + producerSha,
                new ExactRef("classpath:/m1/" + name, raw.length, sha256(raw)));
    }
    private static JsonNode named(JsonNode corpus, String field, String name) throws IOException {
        for (JsonNode row : corpus.path("cases")) {
            if (name.equals(row.path(field).textValue())) { return row; }
        }
        throw new IOException("original producer case missing: " + name);
    }
    private static byte[] resource(String name, String sha256) throws IOException {
        try (InputStream input = M1FixtureCases.class.getResourceAsStream("/m1/" + name)) {
            if (input == null) { throw new IOException("original producer corpus missing: " + name); }
            byte[] raw = input.readNBytes(M1ResultConsumers.MAX_BYTES + 1);
            if (raw.length > M1ResultConsumers.MAX_BYTES || !sha256(raw).equals(sha256)) {
                throw new IOException("original producer corpus bytes changed: " + name);
            }
            return raw;
        }
    }
    public static String sha256(byte[] raw) {
        try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)); }
        catch (NoSuchAlgorithmException impossible) { throw new IllegalStateException(impossible); }
    }
    private static JsonNode parse(byte[] raw) { return StrictJson.parse(raw, M1ResultConsumers.MAX_BYTES); }
    private static byte[] write(JsonNode node) { return SdkProjectionJson.encode(node, M1ResultConsumers.MAX_BYTES); }
    private static byte[] utf8(String text) { return text.getBytes(StandardCharsets.UTF_8); }
}
